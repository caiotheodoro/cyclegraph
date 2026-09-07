#!/usr/bin/env python3
"""`FrameSignal` and `HandSpeedEstimate` for every clip in a manifest. `docs/METHOD.md` E2-E3.

Decodes each clip once, sequentially, at the analysis rate, and reads its hand boxes and
manipulation labels from files that earlier stages wrote. The models themselves live in
`scripts/`, not in `src/cyclegraph/signal/`, so this stage is CPU-only and re-runnable offline
once those files exist (`docs/DECISIONS.md` D022, and `signal/stores.py`).

**It refuses to run without them, by design.** A pipeline that substituted a region prior for
a detector, or an unwritten instant for a negative label, would produce records that satisfy
every schema and mean nothing. `docs/HANDOFF.md`: no detector box, no speed.

Pilot output is pass/fail; the records go to a gitignored path under `results/`.

Usage:
    python3 scripts/build_signal.py --manifest results/pilot/clips_factory_001.jsonl \\
        --detections results/pilot/detections.jsonl --labels results/pilot/labels.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Iterator

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.decode import (  # noqa: E402
    Gray,
    decode_gray_frames,
    ffmpeg_clip_argv,
)
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import (  # noqa: E402
    ANALYSIS_HZ,
    n_samples,
    pair_offset_s,
    sample_times,
)
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import (  # noqa: E402
    COVERAGE_FLOOR,
    FLOW_NULL_CEILING,
    ClipRef,
    FrameSignal,
    HandSpeedEstimate,
)
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.frames import (  # noqa: E402
    FrameSample,
    box_is_contradicted,
    contradiction_reason,
    build_frame_signal,
    resolve_conflicts,
)
from cyclegraph.signal.ports import Flow, HandBox, largest_box  # noqa: E402
from cyclegraph.signal.speed import (  # noqa: E402
    HAND_BREADTH_MM,
    SpeedSample,
    hand_speed_estimate,
    speed_sample,
)
from cyclegraph.signal.stores import JsonlDetectionStore, JsonlLabelStore  # noqa: E402

WIDTH, HEIGHT = 960, 540
"""Flow and the box-width scale are both ratios of pixels, so a uniform downscale cancels in
mm/s. It does not cancel in the detector's coordinates, which is why boxes are scaled below.

**It also does not cancel in what the estimator can recover**, which is why this is 960 and not
the 480 it was. Measured at the pair D045 defines (`results/flow_gain_by_resolution.json`), a
hand at 602 mm/s is recovered with gain **0.77 at 480x270 and 0.99 at 960x540**. The knee is
not monotone in resolution and 960 is a measured optimum, not a maximum: at 1440 and 1920 the
same motion spans more pixels than the estimator's search range and the gain falls back to
0.20 (`docs/DECISIONS.md` D050)."""


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


def _scaled(box: HandBox, sx: float, sy: float) -> HandBox:
    return HandBox(x=box.x * sx, y=box.y * sy, width=box.width * sx,
                   height=box.height * sy, score=box.score)


def _refuse_to_overwrite(out_dir: Path) -> str | None:
    """Why writing placeholders here would destroy something, or None if it would not.

    `--record-not-attempted` opens both outputs in mode `"w"`. Before D064 it then died on the
    validator, leaving two empty files and an obvious incident. D064 fixed the record and left
    the truncation, so at the default `--out-dir` the flag now *succeeds* at replacing the
    pilot's measured records with placeholders -- and `score_hal` then reads 97 records with no
    boxes and publishes H2c as **FAILED**: a pre-registered hypothesis falsified by a stage
    that never ran. A silent success is worse than the crash it replaced (D065).
    """
    for name in ("frame_signal.jsonl", "hand_speed.jsonl"):
        path = out_dir / name
        if path.exists() and path.stat().st_size > 0:
            return (f"{path} already holds records. This flag writes placeholders that say no "
                    f"stage ran, and would overwrite them. Use a different --out-dir.")
    return None


def _record_not_attempted(args: argparse.Namespace) -> int:
    """Write what is true of a pilot whose signal stage has not run.

    Every field is either measured from the manifest or explicitly null. `not_attempted` is
    the status `CONTRACTS.md` v1.3 added for exactly this, because the alternative was to
    assert that labelling ran and failed, or that decoding failed, neither of which happened
    (`docs/DECISIONS.md` D031). Nothing is decoded and no exposure value is produced.

    `too_short` is deliberately not used here even where the duration would justify it: it is
    a determination the signal stage makes when it runs, and this stage has not run.
    """
    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    refusal = _refuse_to_overwrite(out_dir)
    if refusal is not None:
        print(f"REFUSING: {refusal}", file=sys.stderr)
        return 2

    written = 0
    with (out_dir / "frame_signal.jsonl").open("w") as signals, \
         (out_dir / "hand_speed.jsonl").open("w") as speeds:
        for clip in refs:
            planned = n_samples(clip.duration_s)
            signal = FrameSignal(
                clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, fps_sampled=ANALYSIS_HZ,
                n_frames=planned, manipulation=[None] * planned,
                hands_visible=[None] * planned, hand_box_width_px=[None] * planned,
                hand_mask_source="none", flow_method="none",
                label_source=None, label_rev=None, prompt_variant=None,
                status="not_attempted", n_unreadable=planned,
            )
            speed = HandSpeedEstimate(
                clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, rms_speed_mm_s=None,
                n_samples=planned, n_with_box=0, n_flow_null=0, coverage=0.0,
                # Null, not 0.0: D054 made this null exactly when nothing was boxed, and this
                # writer kept the zero. The validator then refused the first record -- after
                # the `with` above had already truncated both output files -- so the flag
                # deleted the pilot's records and wrote nothing in their place (D064).
                flow_null_rate=None, hand_breadth_mm=HAND_BREADTH_MM,
                median_box_width_px=None, mask_source=None, flow_method="none",
                ego_motion="mask_complement_median", status="no_detector",
                status_reason="no detector ran on this clip",
            )
            signals.write(signal.model_dump_json() + "\n")
            speeds.write(speed.model_dump_json() + "\n")
            written += 1

    print(f"pilot gates (values stay in {args.out_dir}, D018):")
    print(f"  {'PASS' if written == len(refs) else 'FAIL'}  both records written for every clip")
    print("  PASS  every record states the stage has not run; none carries an exposure value")
    return 0 if written == len(refs) else 1


def stream_pairs(clip: ClipRef, token: str | None, *, width: int, height: int,
                 ) -> Iterator[tuple[int, float, Gray, Gray]]:
    """`(k, t_s, first, second)` for each 4 Hz instant that has a pair.

    The two frames are **one frame of the source video apart** (`docs/DECISIONS.md` D045), not
    one analysis period. Getting that requires decoding at the clip's own rate: ffmpeg's `fps`
    filter resamples to 4 Hz and cannot emit the frame that follows one of its outputs.

    Decoding at the native rate costs no extra *network* -- the mp4 bytes fetched are the same
    either way, because H.264 has to be decoded sequentially regardless of how many frames are
    emitted. What grows is the local pipe, and only the two frames of the current pair are ever
    held, so it does not grow memory (D049).

    Instants whose pair falls off the end of the decode are simply not yielded; the caller
    records them as absent with a reason rather than inventing a pair.

    **This trusts the sidecar's `fps` to be the stream's real rate**, because the index of the
    frame at `t` is `round(t * fps)` and `ffmpeg`'s `fps` filter resamples to whatever it is
    told. A sidecar claiming 30 over a 29.97 stream would have the filter duplicate about one
    frame in a thousand, and the mapping would drift by a second or so by the end of a 20-minute
    clip -- pairing late instants with frames from elsewhere, silently. Checked rather than
    assumed, 2026-09-06: every clip in the pilot manifest declares 30.0, and `ffprobe` on the
    streams themselves reports `r_frame_rate` and `avg_frame_rate` of exactly `30/1`, with
    `nb_frames / duration` agreeing (35998 / 1199.933). The filter is a no-op here. On a corpus
    where it is not, this needs the filter dropped rather than the rate trusted.
    """
    times = sample_times(clip.duration_s)
    if not times:
        return
    # Which native frame index each instant starts at, and how far to decode for the last pair.
    # Half-up, not `round`. At 4 Hz over a 30 fps source every odd instant lands on a
    # half-integer frame index, and Python's banker's rounding then alternates between the
    # frame before and the frame after by the instant's *parity* -- k=1 to frame 8, k=3 to
    # frame 22, k=5 to frame 38. Which source frame an instant means should not depend on
    # whether its index is odd.
    #
    # This does not remove the underlying ambiguity, and nothing here can: the box and the
    # label at the same instant come from a separate `-vf fps=4` decode whose frame selection
    # is ffmpeg's, so box and flow can still differ by one source frame -- 33 ms, about 21 px
    # of hand travel at 600 mm/s against a ~96 px box. `docs/COVERAGE.md` carries that bound.
    first_index: dict[int, int] = {}
    for k, t_s in enumerate(times):
        first_index.setdefault(int(t_s * clip.fps + 0.5), k)
    limit = int(times[-1] * clip.fps + 0.5) + 2

    url = ShardReader(REPO_ID, clip.shard, token)._resolve()
    argv = ffmpeg_clip_argv(url, clip, fps_sampled=clip.fps, width=width, height=height,
                            max_frames=limit)
    previous: Gray | None = None
    for n, frame in enumerate(decode_gray_frames(argv, width, height)):
        index = first_index.get(n - 1)
        if previous is not None and index is not None:
            yield index, times[index], previous, frame
        previous = frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--detections", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--out-dir", default="results/pilot")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--corpus-rev", default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    parser.add_argument(
        "--record-not-attempted", action="store_true",
        help="write truthful records for a pilot whose signal stage has not run: "
             "FrameSignal at not_attempted, HandSpeedEstimate at no_detector. Decodes "
             "nothing and claims nothing (CONTRACTS v1.3, docs/DECISIONS.md D031).",
    )
    args = parser.parse_args(argv)

    if args.record_not_attempted:
        return _record_not_attempted(args)

    detections_path = ROOT / args.detections
    labels_path = ROOT / args.labels
    missing = [str(p) for p in (detections_path, labels_path) if not p.exists()]
    if missing:
        print("REFUSING: this stage consumes files earlier stages write.", file=sys.stderr)
        for path in missing:
            print(f"  missing: {path}", file=sys.stderr)
        print(
            "\nHand boxes come from 100DOH on GPU (docs/METHOD.md E3, ~24 GPU-hours for the\n"
            "pilot on a g5.xlarge; docs/REPRODUCTION.md 'Compute'). Manipulation labels come\n"
            "from the probe or the judge on a calibration subset. Neither is substitutable:\n"
            "a HandSpeedEstimate built from a region prior is a contract violation, and an\n"
            "unwritten instant read as a negative biases duty cycle in the flattering\n"
            "direction (docs/HANDOFF.md).",
            file=sys.stderr,
        )
        return 2

    detections = JsonlDetectionStore.from_path(detections_path)
    labels = JsonlLabelStore.from_path(labels_path)
    flow_estimator = FarnebackFlow()
    token = _token()

    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs: list[ClipRef] = clip_refs(rows, corpus_rev=args.corpus_rev)
    if args.limit:
        refs = refs[: args.limit]

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    signals = (out_dir / "frame_signal.jsonl").open("w")
    speeds = (out_dir / "hand_speed.jsonl").open("w")
    conflicts_total = 0
    built = 0
    estimates: list[HandSpeedEstimate] = []

    failed_clips: list[dict[str, object]] = []
    for clip in refs:
        started = time.time()
        times = sample_times(clip.duration_s)
        sx, sy = WIDTH / clip.width, HEIGHT / clip.height
        # The pair spans one source frame, so this is what a pixel of displacement is worth in
        # seconds. Using the analysis period here instead -- which this did -- divides every
        # speed by the wrong number, by the ratio of the two baselines (D045).
        dt_s = pair_offset_s(clip.fps)
        no_pair = "no decoded pair at this instant"

        def _sample(k: int, t_s: float, field: Flow | None, reason: str | None
                    ) -> tuple[FrameSample, SpeedSample]:
            detection = detections.detect(clip.clip_id, t_s)
            boxes = [_scaled(b, sx, sy) for b in detection.boxes]
            biggest = largest_box(boxes)
            label = labels.label(clip.clip_id, t_s)
            frame_sample = FrameSample(
                t_s=t_s, label=label,
                hand_box_width_px=None if biggest is None else biggest.width / sx,
                decode_reason=reason,
            )
            # D022's drop applies to *both* records. `resolve_conflicts` below nulls the box on
            # the FrameSignal and counts it; the speed path was still handed the unresolved
            # boxes, so a box the contract had discarded was counted in `n_with_box` and an RMS
            # was taken inside it (D056). The raw width stays on `frame_sample` so the conflict
            # is still counted where it is reported.
            dropped_because = contradiction_reason(label)
            for_speed = [] if dropped_because is not None else boxes
            return frame_sample, speed_sample(
                field, for_speed, t_s=t_s, dt_s=dt_s, flow_reason=reason,
                no_box_reason=dropped_because if boxes else None)

        built_samples: list[FrameSample | None] = [None] * len(times)
        built_speeds: list[SpeedSample | None] = [None] * len(times)
        try:
            for k, t_s, first, second in stream_pairs(clip, token, width=WIDTH, height=HEIGHT):
                # Dense flow costs 0.13 s a pair at 960x540 and is 83% of this stage's wall-clock.
                # A pair with no usable box produces a "no detected hand box" sample whatever the
                # field is -- `speed_sample` tests the box before the flow -- so computing one is
                # work whose result is discarded. Skipping it is not an approximation: the sample
                # is identical either way, and on the pilot's coverage it is a sixth of the run.
                usable = detections.detect(clip.clip_id, t_s).boxes and not box_is_contradicted(
                    labels.label(clip.clip_id, t_s))
                if not usable:
                    built_samples[k], built_speeds[k] = _sample(k, t_s, None, None)
                    continue
                if np.array_equal(first, second):
                    # The same frame twice. `docs/RED-TEAM.md` A15 and D023 make a dead flow a null
                    # with a reason and never a zero, but the exact-zero rule they rely on does not
                    # fire here: Farneback on identical frames returns a *tiny non-zero* field, so
                    # the residual is ~1e-07 rather than 0.0 and passes through as a real
                    # measurement of almost no motion -- the flattering direction. Frame equality
                    # is exact, needs no threshold, and catches the case D023 names (D051).
                    built_samples[k], built_speeds[k] = _sample(
                        k, t_s, None, "the two frames of this pair are identical")
                    continue
                built_samples[k], built_speeds[k] = _sample(
                    k, t_s, flow_estimator.flow(first, second), None)
        except Exception as exc:  # a clip that cannot be read through is a value, not a stop
            # A decode that dies mid-stream used to raise out of the worker, taking every
            # clip still queued behind it. Two workers died that way and six clips of the
            # pilot were simply absent from the output (`docs/DECISIONS.md` D060). What
            # decoded is kept; the instants that did not are marked absent with a reason
            # by the loop below, which is what the rubric asks for.
            failed_clips.append({"clip_id": clip.clip_id,
                                 "error": f"{type(exc).__name__}: {str(exc)[:160]}"})
            print(f"  decode failed mid-clip, continuing: {type(exc).__name__}", flush=True)
        for k, t_s in enumerate(times):
            if built_samples[k] is None:
                built_samples[k], built_speeds[k] = _sample(k, t_s, None, no_pair)

        samples: list[FrameSample] = [s for s in built_samples if s is not None]
        speed_samples = [s for s in built_speeds if s is not None]

        resolved, conflicts = resolve_conflicts(samples)
        conflicts_total += conflicts.total
        signal = build_frame_signal(
            clip, resolved, provenance=labels.provenance,
            hand_mask_source=detections.mask_source, flow_method=flow_estimator.flow_method,
            fps_sampled=ANALYSIS_HZ,
        )
        speed = hand_speed_estimate(
            clip, speed_samples, mask_source=detections.mask_source,
            flow_method=flow_estimator.flow_method,
            too_short=signal.status == "too_short",
        )
        signals.write(signal.model_dump_json() + "\n")
        speeds.write(speed.model_dump_json() + "\n")
        # Per clip, like the labeller and the detector. Without it a clip's records sit in the
        # stdio buffer until the process exits, so a worker killed after two hours has written
        # nothing and there is nothing to resume from -- the shape `docs/DECISIONS.md` D043
        # records, in the one stage that had neither a flush nor a resume.
        signals.flush()
        speeds.flush()
        estimates.append(speed)
        built += 1
        print(f"  {built}/{len(refs)} clips  ({time.time() - started:.1f}s)", flush=True)

    signals.close()
    speeds.close()
    if failed_clips:
        path = out_dir / "signal_failures.jsonl"
        with path.open("a") as handle:
            for row in failed_clips:
                handle.write(json.dumps(row) + "\n")
        print(f"\n{len(failed_clips)} clips failed mid-decode; recorded in {path}")

    # H2c, pre-registered: "Detector hand-box coverage is at least 60% of scored frames on the
    # pilot" with a flow-null rate at or under 10% of boxed samples. Aggregated over the pilot
    # in the same shape the per-clip fields use, so the gate and the record agree on what the
    # denominators are: coverage is boxes over samples, and the null rate is nulls over
    # *boxed* samples, not over samples. Those differ by 1/coverage -- at 60% that is 1.67x,
    # enough to straddle the ceiling in both directions.
    total_samples = sum(e.n_samples for e in estimates)
    boxed = sum(e.n_with_box for e in estimates)
    nulls = sum(e.n_flow_null for e in estimates)
    coverage = boxed / total_samples if total_samples else 0.0
    # A rate over no boxed samples is 0.0, which would print PASS on no data at all. An
    # unevaluable gate is not a satisfied one; it reports FAIL and says which it is.
    null_rate = nulls / boxed if boxed else 0.0
    null_evaluable = boxed > 0

    print(f"\npilot gates (values stay in {args.out_dir}, D018):")
    print(f"  {'PASS' if built == len(refs) else 'FAIL'}  every clip produced both records")
    # Not `>= 0`, which is what this checked and which no run could ever fail. A gate that
    # cannot fail is not a gate; the labeller's equivalent bound is 10% of frames (D038).
    conflict_rate = conflicts_total / total_samples if total_samples else 0.0
    print(f"  {'PASS' if conflict_rate < 0.10 else 'FAIL'}  "
          f"detector and labeller contradict each other on under 10% of samples")
    print(f"  {'PASS' if coverage >= COVERAGE_FLOOR else 'FAIL'}  "
          f"H2c: hand-box coverage clears the pre-registered {COVERAGE_FLOOR:.0%} floor")
    print(f"  {'PASS' if null_evaluable and null_rate <= FLOW_NULL_CEILING else 'FAIL'}  "
          f"H2c: flow-null rate within the pre-registered {FLOW_NULL_CEILING:.0%} ceiling"
          f"{'' if null_evaluable else ' (no boxed sample: not evaluable, not satisfied)'}")
    return 0 if built == len(refs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
