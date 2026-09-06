"""How much of a hand's motion the flow estimator actually recovers, against displacement.

`docs/RUBRIC.md` takes a speed sample "from the frame pair (t, t + 1/fps)", and
`src/cyclegraph/corpus/sampling.py` reads `fps` there as the 4 Hz analysis rate, so the two
frames a speed sample is computed from are **0.25 s apart**. That is a long baseline for dense
optical flow, and this script measures what it costs.

The quantity is **gain**: the median recovered flow magnitude inside the hand box over the
median true magnitude there. Gain 1.0 recovers the motion; gain 0.2 reports a fifth of it. It
is measured on `signal/synthetic.py`'s rendered pairs, where the true field is known exactly,
under the corpus's own lens and the workstation distances `results/a14_translation_floor.json`
already fixes.

This is not an A15 flow *failure*: the estimator returns a finite, plausible, non-zero field
and nothing in the contract can tell that it is small for the wrong reason. It is the same
shape as `docs/DECISIONS.md` D039 and D040 -- a gate that passes quietly.

Writes `results/flow_displacement_gain.json`. No corpus access, no token, no GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.sampling import ANALYSIS_HZ, pair_offset_s  # noqa: E402
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.ports import FlowEstimator, box_mask  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    CORPUS_CAMERA,
    Camera,
    Scene,
    analytic_flow,
    hand_box_for,
    render_pair,
)

HAND_BREADTH_MM = 85.0
SEED = 11
# Camera translations, in metres per pair interval, chosen to sweep the hand-box displacement
# through and past the range a working hand produces. Translating the camera is how a static
# scene is given relative hand motion here; the hand plane is nearer than the background, so
# the box moves further than its surroundings, which is also what makes the depth
# discontinuity this measures.
TRANSLATIONS_M = (0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.12, 0.15)


def _scaled_camera(width: int) -> Camera:
    c = CORPUS_CAMERA
    s = width / c.width
    return Camera(width=int(c.width * s), height=int(c.height * s), fx=c.fx * s, fy=c.fy * s,
                  cx=c.cx * s, cy=c.cy * s, k=c.k)


def measure(width: int, estimator: FlowEstimator) -> dict[str, Any]:
    cam = _scaled_camera(width)
    scene = Scene(camera=cam, hand_box=hand_box_for(cam))
    mask = box_mask((cam.height, cam.width), [scene.hand_box])
    mm_per_px = HAND_BREADTH_MM / scene.hand_box.width
    dt = pair_offset_s(ANALYSIS_HZ)
    rows = []
    for metres in TRANSLATIONS_M:
        truth = analytic_flow(scene, translation_m=(metres, 0.0, 0.0))
        first, second = render_pair(scene, translation_m=(metres, 0.0, 0.0), seed=SEED)
        field = estimator.flow(first, second)
        true_px = float(np.median(np.linalg.norm(truth[mask], axis=-1)))
        got_px = (float(np.median(np.linalg.norm(field[mask], axis=-1)))
                  if field is not None else None)
        rows.append({
            "translation_m_per_pair": metres,
            "hand_displacement_px": round(true_px, 3),
            "true_speed_mm_s": round(true_px * mm_per_px / dt, 1),
            "recovered_px": None if got_px is None else round(got_px, 3),
            "gain": None if got_px is None else round(got_px / true_px, 4),
            "flow_returned_none": field is None,
        })
    return {
        "frame_size": [cam.width, cam.height],
        "hand_box_width_px": round(scene.hand_box.width, 3),
        "mm_per_px": round(mm_per_px, 5),
        "pair_interval_s": dt,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/flow_displacement_gain.json")
    parser.add_argument("--estimator", choices=("farneback", "raft"), default="farneback",
                        help="raft needs a CUDA device and torchvision; it is the arm that "
                             "decides whether D044's collapse is a property of Farneback or "
                             "of the 0.25 s pair the rubric specifies")
    args = parser.parse_args(argv)

    estimator: FlowEstimator
    parameters: dict[str, Any]
    if args.estimator == "raft":
        sys.path.insert(0, str(ROOT / "scripts"))
        from bench_flow import load_raft
        raft, why_not = load_raft()
        if raft is None:
            print(f"REFUSING: {why_not}", file=sys.stderr)
            return 2
        estimator, parameters = raft, {"weights": "Raft_Small_Weights.DEFAULT"}
    else:
        farneback = FarnebackFlow()
        estimator, parameters = farneback, asdict(farneback)

    scales = [measure(480, estimator), measure(960, estimator)]
    payload: dict[str, Any] = {
        "what_this_is": (
            "Median recovered flow magnitude over median true magnitude, inside the hand box, "
            "against hand displacement. Gain 1.0 recovers the motion; gain 0.2 reports a "
            "fifth of it. Rendered synthetics under the corpus lens; no corpus access."),
        "estimator": estimator.flow_method,
        "estimator_parameters": parameters,
        "seed": SEED,
        "deterministic": True,
        "pair_interval_s": pair_offset_s(ANALYSIS_HZ),
        "pair_interval_note": (
            "docs/RUBRIC.md's pair is (t, t + 1/fps) and src/cyclegraph/corpus/sampling.py "
            "reads fps as the 4 Hz analysis rate. The interval is the independent variable "
            "this measurement is about."),
        "scales": scales,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.out}")
    for scale in scales:
        w, h = scale["frame_size"]
        print(f"  {w}x{h}:")
        for row in scale["rows"]:
            print(f"    {row['hand_displacement_px']:7.1f} px "
                  f"({row['true_speed_mm_s']:7.1f} mm/s)  gain {row['gain']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
