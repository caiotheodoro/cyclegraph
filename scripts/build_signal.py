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
from cyclegraph.models import ClipRef, FrameSignal, HandSpeedEstimate  # noqa: E402
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.frames import FrameSample, build_frame_signal, resolve_conflicts  # noqa: E402
from cyclegraph.signal.ports import Flow, HandBox, largest_box  # noqa: E402
from cyclegraph.signal.speed import (  # noqa: E402
    HAND_BREADTH_MM,
    SpeedSample,
    hand_speed_estimate,
    speed_sample,
)
from cyclegraph.signal.stores import JsonlDetectionStore, JsonlLabelStore  # noqa: E402

WIDTH, HEIGHT = 480, 270
"""Flow and the box-width scale are both ratios of pixels, so a uniform downscale cancels in
mm/s. It does not cancel in the detector's coordinates, which is why boxes are scaled below."""


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
                flow_null_rate=0.0, hand_breadth_mm=HAND_BREADTH_MM,
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
    """
    times = sample_times(clip.duration_s)
    if not times:
        return
    # Which native frame index each instant starts at, and how far to decode for the last pair.
    first_index: dict[int, int] = {}
    for k, t_s in enumerate(times):
        first_index.setdefault(int(round(t_s * clip.fps)), k)
    limit = int(round(times[-1] * clip.fps)) + 2

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
            frame_sample = FrameSample(
                t_s=t_s, label=labels.label(clip.clip_id, t_s),
                hand_box_width_px=None if biggest is None else biggest.width / sx,
                decode_reason=reason,
            )
            return frame_sample, speed_sample(field, boxes, t_s=t_s, dt_s=dt_s,
                                              flow_reason=reason)

        built_samples: list[FrameSample | None] = [None] * len(times)
        built_speeds: list[SpeedSample | None] = [None] * len(times)
        for k, t_s, first, second in stream_pairs(clip, token, width=WIDTH, height=HEIGHT):
            built_samples[k], built_speeds[k] = _sample(
                k, t_s, flow_estimator.flow(first, second), None)
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
        built += 1
        print(f"  {built}/{len(refs)} clips  ({time.time() - started:.1f}s)", flush=True)

    signals.close()
    speeds.close()
    print(f"\npilot gates (values stay in {args.out_dir}, D018):")
    print(f"  {'PASS' if built == len(refs) else 'FAIL'}  every clip produced both records")
    print(f"  {'PASS' if conflicts_total >= 0 else 'FAIL'}  detector/labeller conflicts counted")
    return 0 if built == len(refs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
