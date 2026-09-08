"""Behavioural tests for `src/cyclegraph/signal/gain.py`.

The harness exists to be pointed at a stranger's flow estimator, so the property that matters
is that it can *fail*. A test that only shows it passing a good estimator would not establish
anything: the whole claim is that an estimator which has quietly switched to tracking the
background gets caught, and that claim needs the bad case.

The real-estimator cases read `results/`'s published rows rather than re-rendering, so they
assert against the same numbers the release publishes rather than a fresh approximation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from cyclegraph.signal.gain import (
    BACKGROUND_TOLERANCE,
    COLLAPSE_GAIN,
    KNEE_GAIN,
    REGIME_TWO_FRACTION,
    curve_from_rows,
    gain_curve,
)
from cyclegraph.signal.ports import Flow
from cyclegraph.signal.synthetic import BACKGROUND_DISTANCE_M, HAND_DISTANCE_M

ROOT = Path(__file__).resolve().parent.parent
RATIO = HAND_DISTANCE_M / BACKGROUND_DISTANCE_M  # 0.18


def _published(name: str, frame_size: list[int]) -> list[dict[str, Any]]:
    doc = json.loads((ROOT / "results" / name).read_text())
    for scale in doc["scales"]:
        if scale["frame_size"] == frame_size:
            rows: list[dict[str, Any]] = scale["rows"]
            return rows
    raise AssertionError(f"{name} has no {frame_size} scale")


def _rows(pairs: list[tuple[float, float | None]]) -> list[dict[str, Any]]:
    return [{"hand_displacement_px": d, "gain": g, "flow_returned_none": g is None}
            for d, g in pairs]


def test_the_depth_ratio_is_what_the_generator_says_it_is() -> None:
    """If this drifts, every floor comparison below is comparing against the wrong number."""
    assert RATIO == 0.18


def test_a_perfect_estimator_has_a_knee_at_the_end_and_no_floor() -> None:
    curve = curve_from_rows(_rows([(5.0, 0.99), (10.0, 0.99), (20.0, 0.99), (40.0, 0.98)]), RATIO)
    assert curve.knee_px == 40.0
    assert curve.collapse_px is None
    assert curve.floor_gain is None
    assert curve.tracks_background is False
    assert curve.verdict(operating_displacement_px=20.0) == "PASS"


def test_a_background_tracker_is_caught() -> None:
    """The case the harness exists for: plausible, finite, non-zero, and wrong.

    Gain never rises above the knee threshold because the estimator reports the background at
    every displacement, so there is no knee at all and the floor sits on the depth ratio.
    """
    curve = curve_from_rows(_rows([(5.0, 0.18), (10.0, 0.181), (20.0, 0.179),
                                   (40.0, 0.18), (80.0, 0.182)]), RATIO)
    assert curve.knee_px is None
    assert curve.floor_gain is not None
    assert abs(curve.floor_gain - RATIO) <= BACKGROUND_TOLERANCE * RATIO
    assert curve.tracks_background is True
    assert curve.verdict(operating_displacement_px=5.0) == "FAIL"


def test_regime_two_does_not_drag_the_floor_below_the_plateau() -> None:
    """`docs/DECISIONS.md` D070: past the knee there are two regimes, and averaging them lies.

    Uses the published 1920x1080 row, which is the scale where the second regime actually bites,
    rather than an invented example. Filtering it out recovers the depth ratio; not filtering it
    reports 0.1056 and the background signature is missed outright.
    """
    import statistics

    rows = _published("flow_gain_by_resolution.json", [1920, 1080])
    curve = curve_from_rows(rows, RATIO)

    assert curve.floor_gain is not None
    assert abs(curve.floor_gain - RATIO) <= BACKGROUND_TOLERANCE * RATIO
    assert curve.tracks_background is True

    collapsed = [r["gain"] for r in rows if r["gain"] < COLLAPSE_GAIN]
    naive = statistics.median(collapsed)
    assert naive == 0.1056
    assert abs(naive - RATIO) > BACKGROUND_TOLERANCE * RATIO, (
        "the unfiltered median must miss the ratio, or this test is not testing the filter")


def test_a_sweep_that_never_reaches_the_asked_displacement_is_untested_not_passed() -> None:
    curve = curve_from_rows(_rows([(5.0, 0.99), (10.0, 0.99)]), RATIO)
    assert curve.verdict(operating_displacement_px=200.0) == "UNTESTED"
    assert curve.verdict(operating_displacement_px=10.0) == "PASS"


def test_a_flow_failure_is_dropped_rather_than_scored_as_zero() -> None:
    """A15 at the harness: `None` is a failure, not a measurement of no motion."""
    curve = curve_from_rows(_rows([(5.0, 0.99), (20.0, None), (40.0, 0.19)]), RATIO)
    assert [r.flow_returned_none for r in curve.rows] == [False, True, False]
    assert curve.knee_px == 5.0
    assert curve.floor_gain == 0.19


def test_published_farneback_and_raft_share_a_floor_and_differ_on_the_knee() -> None:
    """The release's central claim, asserted mechanically rather than only written down.

    Both files are the 0.25 s baseline, so they are comparable to each other
    (`docs/DECISIONS.md` D071).
    """
    fb = curve_from_rows(_published("flow_displacement_gain.json", [960, 540]), RATIO)
    raft = curve_from_rows(_published("flow_gain_raft.json", [960, 540]), RATIO)

    assert fb.knee_px == 22.794
    assert raft.knee_px == 34.181          # one sweep step further out
    assert raft.knee_px > fb.knee_px       # the knee is an estimator property

    assert fb.tracks_background and raft.tracks_background
    assert fb.floor_gain is not None and raft.floor_gain is not None
    assert abs(fb.floor_gain - raft.floor_gain) < 0.05   # the floor is a geometry property


def test_every_published_scale_lands_on_the_depth_ratio() -> None:
    for name in ("flow_displacement_gain.json", "flow_gain_raft.json",
                 "flow_gain_by_resolution.json"):
        doc = json.loads((ROOT / "results" / name).read_text())
        for scale in doc["scales"]:
            curve = curve_from_rows(scale["rows"], RATIO)
            assert curve.tracks_background, f"{name} {scale['frame_size']} floor missed the ratio"


def test_thresholds_are_ordered_so_the_transition_band_is_never_empty() -> None:
    assert 0.0 < REGIME_TWO_FRACTION * RATIO < COLLAPSE_GAIN < KNEE_GAIN < 1.0


def test_gain_curve_runs_end_to_end_against_a_stub_estimator() -> None:
    """`gain_curve` renders real pairs; the stub keeps it fast while proving the wiring.

    Returning a zero field is a legal measurement of no motion, so gain is 0.0 at every
    displacement -- below the regime-two cut, which means no floor is claimed and the estimator
    is not accused of tracking the background. That distinction is the point of the test.
    """

    class ZeroFlow:
        def flow(self, first: npt.NDArray[np.uint8],
                 second: npt.NDArray[np.uint8]) -> Flow | None:
            return np.zeros((first.shape[0], first.shape[1], 2), dtype=np.float32)

    curve = gain_curve(ZeroFlow(), width=480)
    assert len(curve.rows) == 9
    assert all(r.gain == 0.0 for r in curve.rows)
    assert curve.knee_px is None
    assert curve.floor_gain is None
    assert curve.tracks_background is False
