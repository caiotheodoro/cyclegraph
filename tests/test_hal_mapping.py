"""Golden cases for the two HAL mappings, against the papers themselves.

Radwin 2015 Table 3 prints the equation evaluated at the duty-cycle band mid-points (10, 30,
50, 70, 90 %) to one decimal. A transcription error in any constant moves several cells by
more than rounding. Akkas 2015 prints no table; its anchors are hand-computed from the
printed equation at the corners of its fitted range, and the test also checks the properties
a HAL scale must have.
"""

from __future__ import annotations

import math

import pytest

from cyclegraph.exposure import hal

ROUNDING = 0.06  # one decimal, plus a hair for the paper's own rounding of the constants

# (F exertions/s, D %, HAL) — Radwin et al. 2015, Table 3.
RADWIN_TABLE_3: list[tuple[float, float, float]] = [
    (0.125, 10.0, 0.8),
    (0.25, 30.0, 2.4),
    (0.25, 50.0, 2.8),
    (0.5, 30.0, 4.0),
    (0.5, 50.0, 4.5),
    (0.5, 70.0, 4.9),
    (0.5, 90.0, 5.2),
    (1.0, 70.0, 6.7),
    (1.0, 90.0, 7.1),
    (1.5, 70.0, 7.4),
    (1.5, 90.0, 7.8),
]


@pytest.mark.parametrize(("f", "d", "expected"), RADWIN_TABLE_3)
def test_radwin_2015_reproduces_its_own_table(f: float, d: float, expected: float) -> None:
    assert hal.hal_radwin_2015(f, d) == pytest.approx(expected, abs=ROUNDING)


def test_radwin_2015_matches_the_original_tlv_cells_it_kept() -> None:
    """Table 1 (ACGIH 2001) cells that Table 3 did not asterisk, at band mid-points."""
    assert round(hal.hal_radwin_2015(0.5, 30.0)) == 4
    assert round(hal.hal_radwin_2015(1.0, 90.0)) == 7


def test_radwin_2015_is_monotone_in_both_inputs() -> None:
    for d in (20.0, 50.0, 80.0):
        prev = -math.inf
        for f in (0.125, 0.25, 0.5, 1.0, 1.5, 2.0):
            v = hal.hal_radwin_2015(f, d)
            assert v > prev
            prev = v
    for f in (0.25, 0.5, 1.0):
        prev = -math.inf
        for d in (10.0, 30.0, 50.0, 70.0, 90.0, 100.0):
            v = hal.hal_radwin_2015(f, d)
            assert v > prev
            prev = v


def test_akkas_2015_anchors_at_the_corners_of_its_fitted_range() -> None:
    """Hand-computed from the printed equation: z = −15.87 + 0.02 D + 2.25 ln S."""
    lo = hal.hal_akkas_2015(255.3, 11.0)
    hi = hal.hal_akkas_2015(1288.0, 100.0)
    assert lo == pytest.approx(10.0 / (1.0 + math.exp(-(-15.87 + 0.22 + 2.25 * math.log(255.3)))), abs=1e-9)
    assert hi == pytest.approx(10.0 / (1.0 + math.exp(-(-15.87 + 2.0 + 2.25 * math.log(1288.0)))), abs=1e-9)
    # And they land where Latko's rated jobs land: roughly 0.4 and 9.0.
    assert 0.3 < lo < 0.5
    assert 8.9 < hi < 9.2


def test_akkas_2015_is_bounded_and_monotone() -> None:
    for s in (100.0, 255.3, 600.0, 1288.0, 3000.0):
        for d in (5.0, 11.0, 50.0, 100.0):
            assert 0.0 < hal.hal_akkas_2015(s, d) < 10.0
    for d in (20.0, 60.0, 100.0):
        prev = -math.inf
        for s in (200.0, 400.0, 800.0, 1600.0):
            v = hal.hal_akkas_2015(s, d)
            assert v > prev
            prev = v


def test_zero_is_refused_not_mapped() -> None:
    """A null estimate never reaches a mapping as zero (`docs/RED-TEAM.md` A15, RUBRIC)."""
    with pytest.raises(ValueError):
        hal.hal_radwin_2015(0.0, 50.0)
    with pytest.raises(ValueError):
        hal.hal_akkas_2015(0.0, 50.0)
    with pytest.raises(ValueError):
        hal.hal_radwin_2015(0.5, 0.0)


def test_fitted_ranges_are_the_papers_ranges() -> None:
    assert hal.RADWIN_2015_RANGE == (0.125, 1.67, 11.0, 100.0)
    assert hal.AKKAS_2015_RANGE == (255.3, 1288.0, 11.0, 100.0)
    assert hal.in_fitted_range("radwin-2015-freq-dc", 0.5, 50.0)
    assert not hal.in_fitted_range("radwin-2015-freq-dc", 2.0, 50.0)
    assert hal.in_fitted_range("akkas-2015-speed-dc", 600.0, 92.0)
    assert not hal.in_fitted_range("akkas-2015-speed-dc", 100.0, 92.0)


def test_scale_rev_names_the_table_and_the_fit() -> None:
    for rev in hal.SCALE_REV.values():
        assert rev.startswith("acgih-2001-table/")
        assert rev.endswith("-fit")
