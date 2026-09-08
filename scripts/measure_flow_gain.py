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

from cyclegraph.corpus.sampling import ANALYSIS_HZ  # noqa: E402
from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.ports import FlowEstimator, box_mask  # noqa: E402
from cyclegraph.signal.speed import HAND_BREADTH_MM  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    CORPUS_CAMERA,
    Camera,
    Scene,
    analytic_flow,
    hand_box_for,
    render_pair,
)

# The sweep itself lives in `src/cyclegraph/signal/gain.py` so this script and the published
# harness run the same code rather than two copies that can drift.
from cyclegraph.signal.gain import SEED, TRANSLATIONS_M, sweep  # noqa: E402,F401


def measure(width: int, estimator: FlowEstimator, pair_interval_s: float) -> dict[str, Any]:
    return sweep(width, estimator, pair_interval_s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/flow_displacement_gain.json")
    parser.add_argument("--widths", default="480,960",
                        help="decode widths to sweep. The knee is not monotone in resolution: "
                             "a dense estimator's search range is in pixels, so a higher "
                             "resolution spends the same physical motion on more of them.")
    parser.add_argument("--pair-interval-s", type=float, default=1.0 / ANALYSIS_HZ,
                        help="seconds between the two frames of a speed pair. The default is "
                             "the 4 Hz reading D045 replaced; it stays the default so this "
                             "curve remains comparable with the one D044 published. Pass "
                             "1/30 for the amended reading.")
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

    widths = [int(w) for w in args.widths.split(",") if w.strip()]
    scales = [measure(w, estimator, args.pair_interval_s) for w in widths]
    payload: dict[str, Any] = {
        "what_this_is": (
            "Median recovered flow magnitude over median true magnitude, inside the hand box, "
            "against hand displacement. Gain 1.0 recovers the motion; gain 0.2 reports a "
            "fifth of it. Rendered synthetics under the corpus lens; no corpus access."),
        "estimator": estimator.flow_method,
        "estimator_parameters": parameters,
        "seed": SEED,
        "deterministic": True,
        "pair_interval_s": args.pair_interval_s,
        "pair_interval_note": (
            "The interval is the independent variable this measurement is about. The 4 Hz "
            "reading of docs/RUBRIC.md's (t, t + 1/fps) gives 0.25 s; docs/DECISIONS.md D045 "
            "replaced it with the clip's own frame rate, about 0.033 s."),
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
