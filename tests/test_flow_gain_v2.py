"""Invariants on the committed v2 post-hoc experiment artifact (`results/flow_gain_v2.json`)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _v2() -> dict[str, Any]:
    out: dict[str, Any] = json.loads((ROOT / "results" / "flow_gain_v2.json").read_text())
    return out


def _seeds() -> dict[str, Any]:
    out: dict[str, Any] = json.loads((ROOT / "results" / "flow_gain_seeds.json").read_text())
    return out


def test_device_parity_and_all_finite() -> None:
    v2 = _v2()
    assert v2["device_parity"]["raft_small_max_abs_gain_diff"] < 1e-4
    for block in v2["additional_estimators_ego_motion"].values():
        for arm in block.values():
            assert arm["all_finite"] is True
    for arm in v2["experiment_b_static_camera"].values():
        assert arm["all_finite"] is True
    for sdict in v2["experiment_d_sweeps"].values():
        for rows in sdict.values():
            assert all(r["all_finite"] is True for r in rows)


def test_direct_flow_field_shows_background_lock_at_68px() -> None:
    v2 = _v2()
    by_est = v2["experiment_a_flow_field"]["metrics_by_estimator"]
    assert set(by_est) == {"farneback-cv2", "dis-medium", "raft-small", "raft-large"}
    for name, rows in by_est.items():
        by_t = {r["translation_m"]: r for r in rows}
        # Below transition: locked onto hand
        assert by_t[0.01]["frac_locked_hand"]["mean"] > 0.70, name
        assert by_t[0.01]["residual_recovery_ratio"]["mean"] > 0.85, name
        # Past transition: locked onto background and pipeline residual collapses
        assert by_t[0.06]["frac_closer_to_bg"]["mean"] > 0.85, name
        assert by_t[0.06]["frac_locked_bg"]["mean"] > 0.70, name
        assert by_t[0.06]["residual_recovery_ratio"]["mean"] < 0.25, name


def test_static_camera_eliminates_shelf_and_shifts_crossings_earlier() -> None:
    v2 = _v2()
    seeds = _seeds()
    ego_crossings = {
        "farneback-cv2": seeds["farneback_by_width"]["960"]["half_crossing_px"]["mean"],
        "dis-medium": v2["additional_estimators_ego_motion"]["dis-medium"]["grid_9pt"][
            "half_crossing_px"
        ]["mean"],
        "raft-small": seeds["raft"]["by_width"]["960"]["half_crossing_px"]["mean"],
        "raft-large": v2["additional_estimators_ego_motion"]["raft-large"]["grid_9pt"][
            "half_crossing_px"
        ]["mean"],
    }
    for name, ego_d in ego_crossings.items():
        st = v2["experiment_b_static_camera"][name]
        assert st["post_68px_median_gain"]["mean"] < 0.12, name
        assert st["half_crossing_px"]["mean"] < ego_d, name


def test_additional_estimators_land_on_depth_ratio_shelf() -> None:
    v2 = _v2()
    ratio = v2["floor_ratio_expected"]
    for name in ("dis-medium", "raft-large"):
        shelf = v2["additional_estimators_ego_motion"][name]["grid_9pt"]["floor_gain"]["mean"]
        assert abs(shelf - ratio) < 0.03, (name, shelf, ratio)


def test_depth_ratio_and_box_size_monotonicity() -> None:
    v2 = _v2()
    # RAFT-small shelf tracks depth ratio within 0.02 across 0.10..0.50
    for r in v2["experiment_d_sweeps"]["depth_ratio"]["raft-small"]:
        assert abs(r["floor_gain"]["mean"] - r["depth_ratio"]) < 0.02, r
    # Larger box monotonically delays half-crossing for all three estimators
    for name, rows in v2["experiment_d_sweeps"]["box_size"].items():
        crossings = [r["half_crossing_px"]["mean"] for r in rows]
        assert crossings == sorted(crossings), (name, crossings)
