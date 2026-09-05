#!/usr/bin/env python3
"""Measure the speed path's residual floor and publish it. `docs/RED-TEAM.md` A14.

The floor is the apparent hand speed a *static* hand produces under camera motion alone,
after the rubric's ego-motion subtraction. It has two parts and this script measures both
(`docs/DECISIONS.md` D021):

- **rotation**, which survives because the rubric subtracts a scalar and the corpus lens makes
  rotational flow vary by a factor of two across the frame;
- **translation**, which survives because flow scales as `v/Z` and the hands are nearer than
  the background the scalar is taken from.

It runs on exact synthetic geometry with no optical-flow estimator in the loop, so what it
reports is a property of the rubric's rule and the corpus's lens rather than of any
estimator's error. An estimator's own contribution is measured separately by
`scripts/bench_flow.py`.

**The floor is not one number.** It is proportional to how much the camera moves, and the
corpus's ego-motion distribution is not known until frames are decoded. So this publishes the
floor as a function of camera motion, plus the motion budget at which it reaches the
pre-registered 0.25 HAL bound. When real ego-motion is measured, the floor is read off.

Deterministic by construction: no random number is drawn anywhere in it.

Usage:
    python3 scripts/measure_a14_floor.py [--out results/a14_translation_floor.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.exposure.hal import hal_akkas_2015  # noqa: E402
from cyclegraph.signal.ports import box_mask  # noqa: E402
from cyclegraph.signal.speed import HAND_BREADTH_MM, ego_motion, residual_rms_px  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    CORPUS_CAMERA,
    CORPUS_K,
    NARROW_CAMERA,
    Camera,
    Scene,
    analytic_flow,
    hand_box_for,
    image_circle_radius_px,
    max_theta,
    valid_mask,
)

DT_S = 0.25  # the pre-registered 4 Hz pair interval (docs/DECISIONS.md D010)
DUTY_CYCLE_PCT = 68.0  # CONTRACTS.md's own example, used only to price a floor in HAL
HAL_BUDGET = 0.25  # docs/PRE-REGISTRATION.md v1.3.0
ASSUMED_MEDIAN_SPEEDS_MM_S = (400.0, 612.4, 800.0)

ROTATION_DEG_PER_S = (0.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0)
TRANSLATION_M_PER_S = (0.0, 0.01, 0.02, 0.05, 0.10, 0.25)


def _floor_mm_s(camera: Camera, *, rotation_deg_s: float, translation_m_s: float) -> float:
    """Apparent speed of a static hand, in mm/s, after the rubric's ego-motion subtraction."""
    scene = Scene(camera=camera, hand_box=hand_box_for(camera))
    flow = analytic_flow(
        scene,
        rotation_rad=math.radians(rotation_deg_s * DT_S),
        translation_m=(translation_m_s * DT_S, 0.0, 0.0),
    )
    box = scene.hand_box
    mask = box_mask(flow.shape[:2], [box])
    if rotation_deg_s == 0.0 and translation_m_s == 0.0:
        return 0.0
    ego = ego_motion(flow, mask)
    px_per_frame = residual_rms_px(flow, box, ego)
    return (px_per_frame / DT_S) * HAND_BREADTH_MM / box.width


def _hal_cost(floor_mm_s: float, median_mm_s: float) -> float:
    """HAL a spurious floor adds: the measured median is the true one plus the floor."""
    true_speed = max(median_mm_s - floor_mm_s, 1e-6)
    return hal_akkas_2015(median_mm_s, DUTY_CYCLE_PCT) - hal_akkas_2015(true_speed, DUTY_CYCLE_PCT)


def _budget(median_mm_s: float) -> float:
    """The floor, in mm/s, that costs exactly HAL_BUDGET at this median. Bisection."""
    lo, hi = 0.0, median_mm_s * 0.999
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _hal_cost(mid, median_mm_s) < HAL_BUDGET:
            lo = mid
        else:
            hi = mid
    return lo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/a14_translation_floor.json")
    args = parser.parse_args(argv)

    box = hand_box_for(CORPUS_CAMERA)

    rotation_rows = [
        {"rotation_deg_per_s": d, "translation_m_per_s": 0.0,
         "floor_mm_s": round(_floor_mm_s(CORPUS_CAMERA, rotation_deg_s=d, translation_m_s=0.0), 4)}
        for d in ROTATION_DEG_PER_S
    ]
    translation_rows = [
        {"rotation_deg_per_s": 0.0, "translation_m_per_s": v,
         "floor_mm_s": round(_floor_mm_s(CORPUS_CAMERA, rotation_deg_s=0.0, translation_m_s=v), 4)}
        for v in TRANSLATION_M_PER_S
    ]
    narrow_control = [
        {"rotation_deg_per_s": d, "floor_mm_s": round(
            _floor_mm_s(NARROW_CAMERA, rotation_deg_s=d, translation_m_s=0.0), 4)}
        for d in ROTATION_DEG_PER_S
    ]

    budgets = {f"{s:.1f}": round(_budget(s), 4) for s in ASSUMED_MEDIAN_SPEEDS_MM_S}

    def motion_budget(rows: list[dict[str, Any]], key: str, floor_mm_s: float) -> float | None:
        """Linear interpolation: the floor is proportional to motion, so this inverts it."""
        pts = [(float(r[key]), float(r["floor_mm_s"])) for r in rows if float(r[key]) > 0]
        if not pts:
            return None
        m, f = pts[0]
        return round(floor_mm_s * m / f, 5) if f > 0 else None

    payload: dict[str, Any] = {
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "what_this_is": (
            "The apparent RMS hand speed a static hand produces under camera motion alone, "
            "after the ego-motion subtraction docs/RUBRIC.md specifies. Exact geometry; no "
            "optical-flow estimator is involved, so this is a property of the rule and the "
            "lens, not of an estimator."
        ),
        "deterministic": True,
        "seed": None,
        "seed_note": "No random number is drawn; the computation is closed-form geometry.",
        "pre_registered_bound_hal": HAL_BUDGET,
        "pre_registration_version": "1.3.0",
        "lens": {
            "source": "docs/DECISIONS.md D025; identical for all 2144 shipped workers",
            "model": "fisheye (Kannala-Brandt)",
            "k": list(CORPUS_K),
            "max_theta_rad": round(max_theta(CORPUS_CAMERA), 6),
            "max_half_angle_deg": round(math.degrees(max_theta(CORPUS_CAMERA)), 3),
            "image_circle_radius_px": round(image_circle_radius_px(CORPUS_CAMERA), 3),
            "fraction_of_frame_inside_image_circle": round(float(valid_mask(CORPUS_CAMERA).mean()), 5),
        },
        "assumptions": {
            "hand_distance_m": 0.45,
            "background_distance_m": 2.50,
            "hand_breadth_mm": HAND_BREADTH_MM,
            "hand_box_width_px": round(box.width, 3),
            "pair_interval_s": DT_S,
            "duty_cycle_pct_for_pricing": DUTY_CYCLE_PCT,
            "note": (
                "Distances are stated assumptions about workstation geometry, not measurements. "
                "They are part of the floor's definition."
            ),
        },
        "rotation_only_corpus_lens": rotation_rows,
        "rotation_only_narrow_lens_control": narrow_control,
        "translation_only_corpus_lens": translation_rows,
        "hal_budget_mm_s_at_assumed_median": budgets,
        "motion_budget_at_0.25_hal": {
            "note": (
                "The camera motion at which the floor alone reaches the pre-registered bound, "
                "at each assumed corpus median speed. Below these the floor is within budget."
            ),
            "rotation_deg_per_s": {
                k: motion_budget(rotation_rows, "rotation_deg_per_s", v) for k, v in budgets.items()
            },
            "translation_m_per_s": {
                k: motion_budget(translation_rows, "translation_m_per_s", v)
                for k, v in budgets.items()
            },
        },
        "what_is_not_settled": (
            "The corpus's own ego-motion distribution. Until frames are decoded and real "
            "head motion is measured, this table gives the floor for an assumed motion, not "
            "the floor. docs/PRE-REGISTRATION.md's bound is evaluated at W7 against the "
            "measured corpus median speed."
        ),
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.out}")
    print(f"  lens: half-angle {payload['lens']['max_half_angle_deg']}deg, "
          f"{100 * float(payload['lens']['fraction_of_frame_inside_image_circle']):.1f}% of frame usable")
    print(f"  hand box {box.width:.1f} px at {payload['assumptions']['hand_distance_m']} m")
    for row in rotation_rows:
        print(f"  rotation {row['rotation_deg_per_s']:5.1f} deg/s -> floor {row['floor_mm_s']:9.3f} mm/s")
    for row in translation_rows:
        print(f"  translation {row['translation_m_per_s']:5.2f} m/s -> floor {row['floor_mm_s']:9.3f} mm/s")
    print(f"  budget at 0.25 HAL: {budgets}")
    print(f"  motion budget: {json.dumps(payload['motion_budget_at_0.25_hal'], indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
