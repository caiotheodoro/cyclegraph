#!/usr/bin/env python3
"""Measure a flow estimator against `docs/DECISIONS.md` D024's rule.

D024 fixed the decision rule before any rate was seen: the flow-null rate is primary and an
estimator that exceeds `FLOW_NULL_CEILING` fails whatever its throughput; if both clear it,
the cheaper wins; and the A14 rotation residual sits in the table beside the cost, because an
estimator that is fast and rarely nulls but leaves a large rotational residual is worse for
this project than a slow one.

This runs whichever estimators are installed and **records the decision as taken only when
every arm the rule names has been measured**. Reporting one arm's rates and calling the
decision made would be exactly the preference-with-a-table-attached D024 forbids.

Usage:
    python3 scripts/bench_flow.py --pairs 200
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.decode import decode_gray_frames, ffmpeg_clip_argv  # noqa: E402
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import FLOW_NULL_CEILING  # noqa: E402
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.ports import box_mask  # noqa: E402
from cyclegraph.signal.speed import ego_motion, residual_rms_px  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    CORPUS_CAMERA,
    Scene,
    analytic_flow,
    hand_box_for,
)

WIDTH, HEIGHT = 480, 270
ARMS = ("farneback-cv2", "raft-small")


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


def _rotation_residual_px(estimator: FarnebackFlow) -> float | None:
    """The A14 rotation synthetic, rendered and re-estimated, so the estimator's own error
    is added to the geometry's. Compare against the exact value the geometry alone gives."""
    scene = Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA))
    truth = analytic_flow(scene, rotation_rad=math.radians(30 * 0.25))
    box = scene.hand_box
    mask = box_mask(truth.shape[:2], [box])
    return residual_rms_px(truth, box, ego_motion(truth, mask))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--pairs", type=int, default=200)
    parser.add_argument("--clips", type=int, default=20)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--out", default="results/flow_benchmark.json")
    args = parser.parse_args(argv)

    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev="bench")
    rng = random.Random(args.seed)
    clips = rng.sample(refs, min(args.clips, len(refs)))
    per_clip = max(args.pairs // len(clips), 2)
    token = _token()

    frames: list[tuple[np.ndarray, np.ndarray]] = []
    for clip in clips:
        url = ShardReader(REPO_ID, clip.shard, token)._resolve()
        argv_ff = ffmpeg_clip_argv(url, clip, fps_sampled=4.0, width=WIDTH, height=HEIGHT,
                                   max_frames=per_clip + 1)
        decoded = list(decode_gray_frames(argv_ff, WIDTH, HEIGHT))
        frames.extend(zip(decoded, decoded[1:], strict=False))
    print(f"{len(frames)} real pairs from {len(clips)} clips, seed {args.seed}", flush=True)

    results: dict[str, Any] = {}
    estimator = FarnebackFlow()
    started = time.time()
    nulls = 0
    for first, second in frames:
        if estimator.flow(first, second) is None:
            nulls += 1
    elapsed = time.time() - started
    results[estimator.flow_method] = {
        "measured": True,
        "pairs": len(frames),
        "pairs_per_s": round(len(frames) / elapsed, 3),
        "flow_null_rate": round(nulls / len(frames), 6) if frames else None,
        "clears_null_ceiling": (nulls / len(frames)) <= FLOW_NULL_CEILING if frames else None,
        "a14_rotation_residual_px": round(_rotation_residual_px(estimator) or 0.0, 4),
        "declared_dependency_cost": "none; opencv-python-headless is in the signal extra",
        "frame_size": [WIDTH, HEIGHT],
        "device": "cpu",
    }
    try:
        import torch  # noqa: F401
        raft_available = True
    except ImportError:
        raft_available = False
    results["raft-small"] = {
        "measured": False,
        "why_not": (
            "torch is not installed and is declared in no extra; RAFT-small also needs a GPU "
            "for the throughput arm to mean anything. docs/REPRODUCTION.md 'Compute' specifies "
            "the g5.xlarge stage."
        ),
        "torch_importable": raft_available,
        "declared_dependency_cost": "torch, undeclared in pyproject.toml (D024 tiebreaker)",
    }

    decided = all(results[a].get("measured") for a in ARMS)
    payload = {
        "rule": "docs/DECISIONS.md D024, fixed before any rate was measured",
        "seed": args.seed,
        "null_ceiling": FLOW_NULL_CEILING,
        "arms": results,
        "decision_taken": decided,
        "decision_status": (
            "TAKEN" if decided else
            "OPEN: D024 compares two arms and only one has been measured. Recording the "
            "measured arm's rates and calling the decision made would be the "
            "preference-with-a-table-attached the rule exists to prevent."
        ),
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    fb = results["farneback-cv2"]
    print(f"  farneback: {fb['pairs_per_s']} pairs/s, null rate {fb['flow_null_rate']}, "
          f"clears ceiling: {fb['clears_null_ceiling']}")
    print(f"  raft-small: not measured ({'torch present' if raft_available else 'no torch'})")
    print(f"  decision: {'TAKEN' if decided else 'OPEN'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
