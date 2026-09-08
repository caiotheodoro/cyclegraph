"""Build `space/data.json`, the only thing the Space renders.

The page holds no numbers of its own. Everything it draws is read out of `results/` here, so a
figure on the Space and the same figure in the Hugging Face dataset cannot drift apart -- which
is the failure mode a hand-edited chart constant produces, and the one this project spends its
whole argument objecting to.

Two things are exported. The published sweeps, flattened the same way
`scripts/export_hf_dataset.py` flattens them. And quiver fields: a downsampled grid of true and
recovered flow vectors at three displacements, computed here with the real estimator, because
the moment the recovered arrows inside the hand box swing away from the true ones and line up
with the background is the finding, and it is worth showing rather than asserting.

No corpus access, no token. The quiver arm needs opencv, which the `signal` extra declares.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.gain import (  # noqa: E402
    BACKGROUND_TOLERANCE,
    COLLAPSE_GAIN,
    KNEE_GAIN,
    REGIME_TWO_FRACTION,
    scaled_camera,
)
from cyclegraph.signal.ports import box_mask  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    BACKGROUND_DISTANCE_M,
    HAND_DISTANCE_M,
    Scene,
    analytic_flow,
    hand_box_for,
    render_pair,
)

RESULTS = ROOT / "results"
SEED = 11

# One displacement below the knee, one at it, one well past. Picked from the published sweep's
# own translations so the quiver panels line up with rows a reader can look up.
QUIVER_TRANSLATIONS_M = (0.01, 0.03, 0.08)
QUIVER_WIDTH = 960
QUIVER_STRIDE = 30      # px between sampled vectors over the frame
QUIVER_BOX_STRIDE = 14  # finer inside the hand box, where the whole argument happens: at the
                        # frame stride the box holds 16 arrows, too few to read as a field


def _load(name: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((RESULTS / name).read_text())
    return doc


def _sweep(doc: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for scale in doc["scales"]:
        out.append({
            "estimator": doc["estimator"],
            "frame_size": scale["frame_size"],
            "hand_box_width_px": scale["hand_box_width_px"],
            "pair_interval_s": scale["pair_interval_s"],
            "rows": [{
                "displacement_px": r["hand_displacement_px"],
                "over_box": round(r["hand_displacement_px"] / scale["hand_box_width_px"], 4),
                "gain": r["gain"],
                "true_speed_mm_s": r["true_speed_mm_s"],
            } for r in scale["rows"]],
        })
    return out


def _quivers() -> list[dict[str, Any]]:
    cam = scaled_camera(QUIVER_WIDTH)
    scene = Scene(camera=cam, hand_box=hand_box_for(cam))
    box = scene.hand_box
    mask = box_mask((cam.height, cam.width), [box])
    estimator = FarnebackFlow()

    coarse = [(int(x), int(y))
              for y in np.arange(QUIVER_STRIDE // 2, cam.height, QUIVER_STRIDE)
              for x in np.arange(QUIVER_STRIDE // 2, cam.width, QUIVER_STRIDE)
              if not mask[int(y), int(x)]]
    # A margin either side of the box, so the reader sees the discontinuity the estimator
    # smooths across rather than only the two sides of it.
    pad = QUIVER_STRIDE
    fine = [(int(x), int(y))
            for y in np.arange(max(0, int(box.y) - pad),
                               min(cam.height, int(box.y + box.height) + pad), QUIVER_BOX_STRIDE)
            for x in np.arange(max(0, int(box.x) - pad),
                               min(cam.width, int(box.x + box.width) + pad), QUIVER_BOX_STRIDE)]
    points = sorted(set(coarse) | set(fine))

    panels = []
    for metres in QUIVER_TRANSLATIONS_M:
        truth = analytic_flow(scene, translation_m=(metres, 0.0, 0.0))
        first, second = render_pair(scene, translation_m=(metres, 0.0, 0.0), seed=SEED)
        got = estimator.flow(first, second)
        assert got is not None, "the reference estimator returned no field"

        vectors = []
        dropped = 0
        for x, y in points:
            v = (float(truth[y, x, 0]), float(truth[y, x, 1]),
                 float(got[y, x, 0]), float(got[y, x, 1]))
            # The fisheye's image circle covers 96% of the frame; outside it there is no
            # defined projection and `analytic_flow` is NaN. Those points carry no measurement,
            # so they are dropped rather than serialised -- bare NaN is not valid JSON and
            # `JSON.parse` rejects the whole payload.
            if not all(np.isfinite(c) for c in v):
                dropped += 1
                continue
            vectors.append({
                "x": x, "y": y,
                "tx": round(v[0], 2), "ty": round(v[1], 2),
                "rx": round(v[2], 2), "ry": round(v[3], 2),
                "in_box": bool(mask[y, x]),
            })
        assert vectors, "every sampled point fell outside the image circle"
        true_px = float(np.median(np.linalg.norm(truth[mask], axis=-1)))
        got_px = float(np.median(np.linalg.norm(got[mask], axis=-1)))
        panels.append({
            "translation_m_per_pair": metres,
            "vectors_outside_image_circle": dropped,
            "displacement_px": round(true_px, 3),
            "gain": round(got_px / true_px, 4),
            "vectors": vectors,
        })
    return panels


def build() -> dict[str, Any]:
    floor = _load("a14_translation_floor.json")
    bench = _load("flow_benchmark.json")
    a = floor["assumptions"]
    cam = scaled_camera(QUIVER_WIDTH)
    scene = Scene(camera=cam, hand_box=hand_box_for(cam))

    return {
        "generated_from": "results/, by scripts/export_space_data.py",
        "depth_ratio": round(HAND_DISTANCE_M / BACKGROUND_DISTANCE_M, 4),
        "hand_distance_m": HAND_DISTANCE_M,
        "background_distance_m": BACKGROUND_DISTANCE_M,
        "lens": floor["lens"],
        "frame": {"width": cam.width, "height": cam.height},
        "hand_box": {"x": round(scene.hand_box.x, 1), "y": round(scene.hand_box.y, 1),
                     "width": round(scene.hand_box.width, 1),
                     "height": round(scene.hand_box.height, 1)},
        "sweeps": {
            "farneback_025": _sweep(_load("flow_displacement_gain.json")),
            "raft_025": _sweep(_load("flow_gain_raft.json")),
            "farneback_native": _sweep(_load("flow_gain_by_resolution.json")),
        },
        # `flow_benchmark.json`'s throughput and null-rate columns are measured over decoded
        # pilot pairs (D059) and must not be published; only the A14 residuals are synthetic.
        # The page never referenced the rest, so it was a leak with no reader.
        "a14_residuals": {
            name: {
                "with_estimator_px": arm["a14_rotation_residual_px"],
                "geometry_only_px": arm["a14_rotation_residual_geometry_only_px"],
            } for name, arm in bench["arms"].items()
        },
        # The page classifies knee and floor with the same thresholds `signal/gain.py` uses.
        # They travel in the payload so the two cannot drift; the page must not re-type them.
        "thresholds": {
            "knee_gain": KNEE_GAIN,
            "collapse_gain": COLLAPSE_GAIN,
            "regime_two_fraction": REGIME_TWO_FRACTION,
            "background_tolerance": BACKGROUND_TOLERANCE,
        },
        "geometry_floor": {
            "rotation_corpus": floor["rotation_only_corpus_lens"],
            "rotation_narrow": floor["rotation_only_narrow_lens_control"],
            "translation_corpus": floor["translation_only_corpus_lens"],
            "hal_budget": floor["hal_budget_mm_s_at_assumed_median"],
            "pre_registered_bound_hal": floor["pre_registered_bound_hal"],
        },
        "quivers": _quivers(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="space/data.json")
    args = parser.parse_args(argv)

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = build()
    out.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({kb:.0f} kB, {len(payload['quivers'])} quiver panels, "
          f"{len(payload['quivers'][0]['vectors'])} vectors each)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
