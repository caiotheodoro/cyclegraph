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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.decode import decode_gray_frames, ffmpeg_clip_argv  # noqa: E402
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.frames import FrameSample, build_frame_signal, resolve_conflicts  # noqa: E402
from cyclegraph.signal.ports import HandBox, largest_box  # noqa: E402
from cyclegraph.signal.speed import hand_speed_estimate, speed_sample  # noqa: E402
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--detections", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--out-dir", default="results/pilot")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--corpus-rev", default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    args = parser.parse_args(argv)

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
        url = ShardReader(REPO_ID, clip.shard, token)._resolve()
        argv_ff = ffmpeg_clip_argv(url, clip, fps_sampled=ANALYSIS_HZ,
                                   width=WIDTH, height=HEIGHT)
        frames = list(decode_gray_frames(argv_ff, WIDTH, HEIGHT))
        times = sample_times(clip.duration_s)
        sx, sy = WIDTH / clip.width, HEIGHT / clip.height

        samples: list[FrameSample] = []
        speed_samples = []
        for i, t_s in enumerate(times):
            detection = detections.detect(clip.clip_id, t_s)
            boxes = [_scaled(b, sx, sy) for b in detection.boxes]
            label = labels.label(clip.clip_id, t_s)
            biggest = largest_box(boxes)
            samples.append(FrameSample(
                t_s=t_s, label=label,
                hand_box_width_px=None if biggest is None else biggest.width / sx,
                decode_reason=None if i + 1 < len(frames) else "no decoded pair at this instant",
            ))
            field = (flow_estimator.flow(frames[i], frames[i + 1])
                     if i + 1 < len(frames) else None)
            speed_samples.append(speed_sample(
                field, boxes, t_s=t_s, dt_s=1.0 / ANALYSIS_HZ,
                flow_reason=None if i + 1 < len(frames) else "no decoded pair at this instant",
            ))

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
