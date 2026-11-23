"""The flow-gain sweep repeated over texture seeds, so every gain has a spread beside it.

`results/flow_gain_by_resolution.json` and its siblings are one seed (11), and `AGENTS.md`
rule 2 / the home repo's rule 3 forbid quoting a single-run number where a spread is
computable. The only thing a seed changes here is the texture the scene is rendered from; the
geometry, lens, depths and displacements are fixed. So the spread is the texture's, and it is
the only spread this synthetic has. It says nothing about real factory video.

Three arms, all at the clip's own frame interval (1/30 s; the interval only rescales mm/s and
leaves displacement and gain untouched):

  grid     the published nine translations, Farneback, four decode widths
  fine     a fine grid across the Farneback knee at 960x540, to place the knee
  raft     RAFT-small at 960x540 on the published nine translations (needs torch; CPU)

Writes `results/flow_gain_seeds.json`. No corpus, no token, no GPU.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.gain import (  # noqa: E402
    SEED,
    TRANSLATIONS_M,
    curve_from_rows,
    sweep,
)
from cyclegraph.signal.synthetic import (  # noqa: E402
    BACKGROUND_DISTANCE_M,
    HAND_DISTANCE_M,
)

PAIR_INTERVAL_S = 1.0 / 30.0
WIDTHS = (480, 960, 1440, 1920)
# 0.020 m is the last published translation with gain above the knee at 960x540 and 0.030 m the
# first below it, so the fine grid covers the span between them.
FINE_M = tuple(round(0.020 + 0.001 * i, 4) for i in range(0, 11))
FLOOR_RATIO = HAND_DISTANCE_M / BACKGROUND_DISTANCE_M


def _spread(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.fmean(values), 4),
        "sd": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def _half_crossing_px(displacements: list[float], gains: list[float | None]) -> float | None:
    """Displacement where gain first falls through 0.5, linearly interpolated between the two
    grid points either side. None if gain never starts above 0.5 or never falls through it."""
    for (d0, g0), (d1, g1) in zip(zip(displacements, gains), zip(displacements[1:], gains[1:])):
        if g0 is None or g1 is None:
            continue
        if g0 >= 0.5 > g1:
            return round(d0 + (g0 - 0.5) * (d1 - d0) / (g0 - g1), 3)
    return None


def _arm(estimator: Any, width: int, translations: tuple[float, ...],
         seeds: list[int]) -> dict[str, Any]:
    per_seed: list[dict[str, Any]] = []
    for seed in seeds:
        scale = sweep(width, estimator, PAIR_INTERVAL_S, translations_m=translations, seed=seed)
        curve = curve_from_rows(scale["rows"], FLOOR_RATIO)
        per_seed.append({
            "seed": seed,
            "gains": [r["gain"] for r in scale["rows"]],
            "knee_px": curve.knee_px,
            "collapse_px": curve.collapse_px,
            "half_crossing_px": _half_crossing_px(
                [r["hand_displacement_px"] for r in scale["rows"]],
                [r["gain"] for r in scale["rows"]]),
            "floor_gain": None if curve.floor_gain is None else round(curve.floor_gain, 4),
        })
    displacements = [r["hand_displacement_px"] for r in scale["rows"]]
    columns = []
    for i, d in enumerate(displacements):
        gains = [s["gains"][i] for s in per_seed]
        columns.append({"hand_displacement_px": d, "translation_m": translations[i],
                        **_spread(gains)})
    knees = [s["knee_px"] for s in per_seed if s["knee_px"] is not None]
    floors = [s["floor_gain"] for s in per_seed if s["floor_gain"] is not None]
    halves = [s["half_crossing_px"] for s in per_seed if s["half_crossing_px"] is not None]
    return {
        "frame_size": scale["frame_size"],
        "hand_box_width_px": scale["hand_box_width_px"],
        "n_seeds": len(seeds),
        "by_displacement": columns,
        "knee_px": {"n_with_knee": len(knees), **(_spread(knees) if knees else {})},
        "half_crossing_px": {"n_with_crossing": len(halves),
                             **(_spread(halves) if halves else {})},
        "floor_gain": {"n_with_floor": len(floors), **(_spread(floors) if floors else {})},
        "per_seed": per_seed,
    }


def _load_raft_cpu() -> Any:
    import torch
    from bench_flow import RaftFlow
    from torchvision.models.optical_flow import Raft_Small_Weights, raft_small

    torch.manual_seed(0)
    model = raft_small(weights=Raft_Small_Weights.DEFAULT).eval()
    return RaftFlow(model, "cpu", torch)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=int, default=20, help="Farneback seeds, 0..n-1")
    p.add_argument("--raft-seeds", type=int, default=10, help="RAFT seeds, 0..n-1; 0 skips")
    p.add_argument("--out", default="results/flow_gain_seeds.json")
    p.add_argument("--only-raft", action="store_true",
                   help="keep the Farneback arms already in --out and redo the RAFT arm")
    args = p.parse_args(argv)

    seeds = list(range(args.seeds))
    farneback = FarnebackFlow()
    if args.only_raft:
        payload = json.loads((ROOT / args.out).read_text())
    else:
        payload = {
            "what_this_is": (
                "The flow-gain sweep over texture seeds. The seed changes only the rendered "
                "texture; geometry, lens and depths are fixed, so the spread is the texture's "
                "and nothing else. Rendered synthetics under the corpus lens; no corpus access."),
            "published_seed": SEED,
            "pair_interval_s": PAIR_INTERVAL_S,
            "floor_ratio_expected": FLOOR_RATIO,
            "farneback_parameters": {"pyr_scale": farneback.pyr_scale, "levels": farneback.levels,
                                     "winsize": farneback.winsize, "iterations": farneback.iterations,
                                     "poly_n": farneback.poly_n, "poly_sigma": farneback.poly_sigma},
            "seeds": seeds,
            "farneback_by_width": {
                str(w): _arm(farneback, w, TRANSLATIONS_M, seeds) for w in WIDTHS},
            "farneback_fine_960": _arm(farneback, 960, FINE_M, seeds),
        }
    if args.raft_seeds > 0:
        raft = _load_raft_cpu()
        # The published seed is always included, so the CPU arm can be checked against the
        # published curve, which was measured on a CUDA device.
        raft_seeds = sorted(set(range(args.raft_seeds)) | {SEED})
        payload["raft"] = {
            "estimator": "raft-small",
            "weights": "Raft_Small_Weights.DEFAULT",
            "device": "cpu",
            "seeds": raft_seeds,
            "by_width": {"960": _arm(raft, 960, TRANSLATIONS_M, raft_seeds)},
        }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
