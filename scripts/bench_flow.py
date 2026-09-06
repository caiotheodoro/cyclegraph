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
from cyclegraph.signal.ports import Flow, FlowEstimator, box_mask  # noqa: E402
from cyclegraph.signal.speed import ego_motion, residual_rms_px  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    CORPUS_CAMERA,
    Camera,
    Scene,
    analytic_flow,
    hand_box_for,
    render_pair,
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


# The corpus's own motion budget (`docs/DECISIONS.md` D026, 23-37 deg/s) at the 4 Hz pair
# baseline: 30 deg/s over 0.25 s. The synthetic is evaluated at the resolution the pipeline
# decodes flow at, not the camera's native one -- a dense estimator's error is a function of
# the displacement in *pixels*, and the same rotation is 29 px at 480x270 and 118 px at
# 1920x1080. Measuring it at native resolution would report a number no pipeline pair ever sees.
A14_ROTATION_DEG = 30.0 * 0.25
FLOW_SCALE = WIDTH / CORPUS_CAMERA.width


def _bench_scene() -> Scene:
    c = CORPUS_CAMERA
    cam = Camera(width=int(c.width * FLOW_SCALE), height=int(c.height * FLOW_SCALE),
                 fx=c.fx * FLOW_SCALE, fy=c.fy * FLOW_SCALE,
                 cx=c.cx * FLOW_SCALE, cy=c.cy * FLOW_SCALE, k=c.k)
    return Scene(camera=cam, hand_box=hand_box_for(cam))


def _a14_residuals(estimator: FlowEstimator | None) -> tuple[float, float | None]:
    """`(geometry_only, with_estimator)` RMS residual in the hand box, in pixels.

    The first is what the rubric's scalar-median ego-motion leaves behind on a fisheye when
    the flow field is exact -- a property of the lens, identical for every estimator, and
    therefore useless on its own for choosing between them. The second runs the estimator on
    rendered frames carrying that same motion, so its own error is added to the geometry's.
    D024's A14 column is the second; the first is printed beside it as the floor it cannot
    go below.

    This function previously took an estimator and never called it, and so reported the
    geometry for both arms.
    """
    scene = _bench_scene()
    truth = analytic_flow(scene, rotation_rad=math.radians(A14_ROTATION_DEG))
    box = scene.hand_box
    mask = box_mask(truth.shape[:2], [box])
    geometry = residual_rms_px(truth, box, ego_motion(truth, mask))
    if estimator is None:
        return geometry, None
    first, second = render_pair(scene, rotation_rad=math.radians(A14_ROTATION_DEG), seed=11)
    field = estimator.flow(first, second)
    if field is None:
        return geometry, None
    return geometry, residual_rms_px(field, box, ego_motion(field, mask))


class RaftFlow:
    """RAFT-small behind the `FlowEstimator` port, with torch imported lazily.

    It lives in a script and not in `src/cyclegraph/signal/` on purpose: `pyproject.toml`'s
    extras map is the module boundary, torch is declared in no extra, and putting a model
    runtime inside `signal/` would make the extras a lie. D024's tiebreaker prices that -- if
    this arm wins, the declared dependency is part of the cost of choosing it.
    """

    def __init__(self, model: Any, device: str, torch_mod: Any) -> None:
        self._model = model
        self._device = device
        self._torch = torch_mod

    @property
    def flow_method(self) -> str:
        return "raft-small"

    def _batch(self, frames: list[np.ndarray]) -> Any:
        torch = self._torch
        stacked = np.stack(frames).astype(np.float32) / 255.0
        tensor = torch.from_numpy(stacked)[:, None, :, :].repeat(1, 3, 1, 1)
        tensor = (tensor * 2.0) - 1.0            # RAFT's expected [-1, 1] range
        return tensor.to(self._device)

    def flow_batch(self, firsts: list[np.ndarray], seconds: list[np.ndarray]) -> list[Flow]:
        torch = self._torch
        h, w = firsts[0].shape
        # RAFT downsamples by 8; a size that is not a multiple of 8 is padded and cropped back
        # rather than resized, so the field stays in the input's own pixel units.
        ph, pw = (-h) % 8, (-w) % 8
        a, b = self._batch(firsts), self._batch(seconds)
        if ph or pw:
            a = torch.nn.functional.pad(a, (0, pw, 0, ph), mode="replicate")
            b = torch.nn.functional.pad(b, (0, pw, 0, ph), mode="replicate")
        with torch.no_grad():
            predicted = self._model(a, b)[-1]
        field = predicted[:, :, :h, :w].permute(0, 2, 3, 1).cpu().numpy()
        return [f.astype(np.float32) for f in field]

    def flow(self, first: np.ndarray, second: np.ndarray) -> Flow | None:
        if first.shape != second.shape:
            return None
        field = self.flow_batch([first], [second])[0]
        if not np.isfinite(field).all():
            return None
        if not field.any():
            return None
        return field


def load_raft() -> tuple[RaftFlow | None, str]:
    """`(estimator, why_not)`. The one place RAFT-small is constructed, so the benchmark and
    `scripts/measure_flow_gain.py` measure the same weights and the same preprocessing."""
    try:
        import torch
        from torchvision.models.optical_flow import Raft_Small_Weights, raft_small
    except ImportError as exc:
        return None, f"torch/torchvision not importable: {exc}"
    if not torch.cuda.is_available():
        return None, ("no CUDA device. A CPU throughput number for RAFT would decide D024's "
                      "cost rule on a configuration nobody would run.")
    model = raft_small(weights=Raft_Small_Weights.DEFAULT).to("cuda").eval()
    return RaftFlow(model, "cuda", torch), ""


def _raft_arm(frames: list[tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    """Measure RAFT-small on the same pairs, or say precisely why it was not measured."""
    unmeasured = {
        "measured": False,
        "declared_dependency_cost": "torch, undeclared in pyproject.toml (D024 tiebreaker)",
    }
    estimator, why_not = load_raft()
    if estimator is None:
        return {**unmeasured, "why_not": why_not}
    import torch
    geometry, estimated = _a14_residuals(estimator)

    firsts = [a for a, _ in frames]
    seconds = [b for _, b in frames]
    nulls = sum(1 for a, b in frames if estimator.flow(a, b) is None)
    # Two throughput readings. Per-pair matches how Farneback is measured; batched is what a
    # GPU arm would actually be run at, and reporting only the first would price RAFT on a
    # configuration nobody would choose. The cost rule uses the better of the two.
    torch.cuda.synchronize()
    started = time.time()
    for a, b in frames:
        estimator.flow_batch([a], [b])
    torch.cuda.synchronize()
    per_pair = len(frames) / (time.time() - started)
    batch = 8
    torch.cuda.synchronize()
    started = time.time()
    for i in range(0, len(frames), batch):
        estimator.flow_batch(firsts[i:i + batch], seconds[i:i + batch])
    torch.cuda.synchronize()
    batched = len(frames) / (time.time() - started)
    return {
        "measured": True,
        "pairs": len(frames),
        "pairs_per_s": round(max(per_pair, batched), 3),
        "pairs_per_s_unbatched": round(per_pair, 3),
        "pairs_per_s_batched_8": round(batched, 3),
        "flow_null_rate": round(nulls / len(frames), 6) if frames else None,
        "clears_null_ceiling": (nulls / len(frames)) <= FLOW_NULL_CEILING if frames else None,
        "a14_rotation_residual_px": round(estimated, 4) if estimated is not None else None,
        "a14_rotation_residual_geometry_only_px": round(geometry, 4),
        "declared_dependency_cost": "torch, undeclared in pyproject.toml (D024 tiebreaker)",
        "frame_size": [WIDTH, HEIGHT],
        "device": torch.cuda.get_device_name(0),
    }


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
    fb_geometry, fb_estimated = _a14_residuals(estimator)
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
        "a14_rotation_residual_px": round(fb_estimated, 4) if fb_estimated is not None
        else None,
        "a14_rotation_residual_geometry_only_px": round(fb_geometry, 4),
        "declared_dependency_cost": "none; opencv-python-headless is in the signal extra",
        "frame_size": [WIDTH, HEIGHT],
        "device": "cpu",
    }
    results["raft-small"] = _raft_arm(frames)

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
    rf = results["raft-small"]
    if rf.get("measured"):
        print(f"  raft-small: {rf['pairs_per_s']} pairs/s, null rate {rf['flow_null_rate']}, "
              f"clears ceiling: {rf['clears_null_ceiling']}")
    else:
        print(f"  raft-small: not measured ({rf['why_not']})")
    print(f"  decision: {'TAKEN' if decided else 'OPEN'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
