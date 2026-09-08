"""Run the flow-gain test against an estimator and print its verdict.

Point it at your own estimator with `--estimator module:factory`, where `factory` is a callable
returning either an object with a `.flow(first, second)` method or a bare function taking two
uint8 frames and returning an `(H, W, 2)` float array, or `None` on failure.

    python3 run_gain_test.py --estimator mypkg.flow:build --operating-displacement-px 12

With no `--estimator` it runs the Farneback reference, which needs `opencv-python-headless`.
Nothing here touches a corpus, a token, a network or a GPU.

**Passing is not gain near 1.0 everywhere.** No dense estimator does that. Passing is the knee
sitting outside the displacements your work produces, which is the number you have to supply.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

_LOCAL_SRC = Path(__file__).resolve().parent.parent / "src"
if _LOCAL_SRC.is_dir():  # running from a cyclegraph clone rather than the released bundle
    sys.path.insert(0, str(_LOCAL_SRC))

try:
    from cyclegraph.signal.gain import gain_curve
except ModuleNotFoundError:  # the released bundle vendors the harness flat, with no package
    from cyclegraph_flow_gain import gain_curve  # type: ignore[import-not-found,no-redef]


def _load_estimator(spec: str) -> Any:
    module_name, _, factory_name = spec.partition(":")
    if not factory_name:
        raise SystemExit(f"--estimator wants 'module:factory', got {spec!r}")
    module = importlib.import_module(module_name)
    return getattr(module, factory_name)()


def _reference() -> Any:
    try:
        from cyclegraph.signal.flow_farneback import FarnebackFlow
    except ModuleNotFoundError:
        raise SystemExit(
            "The reference arm needs opencv (`pip install opencv-python-headless`) and a\n"
            "cyclegraph clone. Pass --estimator module:factory to test your own instead.")
    return FarnebackFlow()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--estimator", default=None,
                        help="module:factory returning your estimator; omit for Farneback")
    parser.add_argument("--width", type=int, default=960, help="decode width to test at")
    parser.add_argument("--operating-displacement-px", type=float, default=None,
                        help="the hand displacement your work actually produces")
    args = parser.parse_args(argv)

    estimator = _load_estimator(args.estimator) if args.estimator else _reference()
    curve = gain_curve(estimator, width=args.width)

    print(f"\n  displacement   gain")
    for row in curve.rows:
        flag = "  <- lost the hand" if row.gain is not None and row.gain < 0.5 else ""
        shown = "FAILED" if row.gain is None else f"{row.gain:.4f}"
        print(f"  {row.hand_displacement_px:9.3f} px   {shown}{flag}")

    print(f"\n  knee                 {curve.knee_px} px"
          if curve.knee_px is not None else
          "\n  knee                 none - gain never held above the threshold")
    print(f"  floor                {curve.floor_gain}")
    print(f"  depth ratio          {curve.floor_ratio_expected}")
    print(f"  tracks background    {curve.tracks_background}")
    if curve.tracks_background:
        print("\n  The floor sits on the depth ratio. Past the knee this estimator is\n"
              "  reporting the background, not the hand, and an ego-motion subtraction\n"
              "  will remove that rather than flag it.")

    if args.operating_displacement_px is not None:
        verdict = curve.verdict(args.operating_displacement_px)
        print(f"\n  VERDICT at {args.operating_displacement_px} px: {verdict}")
        return 0 if verdict == "PASS" else 1
    print("\n  No --operating-displacement-px given, so no verdict. The curve alone does not\n"
          "  say whether this estimator is adequate for your work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
