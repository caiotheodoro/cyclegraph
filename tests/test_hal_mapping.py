"""Golden cases for the two HAL mappings, against the papers themselves.

Radwin 2015 Table 3 prints the equation evaluated inside each duty-cycle band (the paper says
"fitted values for duty cycles of 10, 30, 50, 70 and 90") to one decimal. Evaluated at those
mid-points the largest miss against a printed cell is 0.058 (at F=0.5, D=30: 3.942 vs 4.0),
so the assertion is one-decimal agreement within ±0.1, not a tolerance tuned to the worst
cell. A transcription error in any constant moves several cells by more than that.

Akkas 2015 prints no HAL table. Its Table 1 reproduces Latko's 33 rated jobs with the
measured hand speed and duty cycle, so the equation is held to four of those rows within
the band observers themselves agree to (Radwin 2015 cites 91% within one point) plus the
fit's own residual; the largest miss is 1.23 on "Fabric wrap". That is the honest golden
case for a regression, and it is not a tautology.
"""

from __future__ import annotations

import math

import pytest

from cyclegraph.exposure import hal

ROUNDING = 0.1  # one-decimal agreement; the largest mid-point miss in the paper is 0.058
RATER_BAND = 1.3  # observers agree within one point 91% of the time; plus the fit residual

# (F exertions/s, D %, HAL) — Radwin et al. 2015, Table 3, as transcribed in docs/SURVEY.md S3.
RADWIN_TABLE_3: list[tuple[float, float, float]] = [
    (0.125, 10.0, 0.8),
    (0.125, 30.0, 1.2),
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


# (S mm/s, D %, rated HAL) — Akkas et al. 2015, Table 1 (Latko's jobs), as in docs/SURVEY.md S3.
AKKAS_TABLE_1: list[tuple[str, float, float, float]] = [
    ("Inspection", 255.3, 26.0, 0.6),
    ("Line stack", 665.9, 31.0, 3.5),
    ("Fabric wrap", 574.0, 74.0, 5.98),
    ("Curler", 1055.0, 71.0, 8.13),
]


@pytest.mark.parametrize(("job", "s", "d", "rated"), AKKAS_TABLE_1)
def test_akkas_2015_predicts_latkos_rated_jobs_within_the_rater_band(
    job: str, s: float, d: float, rated: float
) -> None:
    assert hal.hal_akkas_2015(s, d) == pytest.approx(rated, abs=RATER_BAND), job


def test_akkas_2015_ranks_latkos_jobs_in_rated_order() -> None:
    preds = [hal.hal_akkas_2015(s, d) for _, s, d, _ in AKKAS_TABLE_1]
    rated = [r for _, _, _, r in AKKAS_TABLE_1]
    assert sorted(range(4), key=lambda i: preds[i]) == sorted(range(4), key=lambda i: rated[i])


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
