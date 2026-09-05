"""Tests for `src/cyclegraph/exposure/score.py`.

The equations themselves are golden-tested against the papers in `tests/test_hal_mapping.py`.
What is tested here is the wiring: that the mapping names its input, that absence propagates
as a status rather than a number, and that the force axis cannot be populated.
"""

from __future__ import annotations

import pytest

from cyclegraph.exposure.hal import SCALE_REV, hal_akkas_2015, hal_radwin_2015
from cyclegraph.exposure.score import score_spectral_path, score_speed_path
from cyclegraph.models import DutyCycleEstimate, FrequencyEstimate, HandSpeedEstimate
from tests import fixtures

CLIP = "factory_001/worker_001/000123"


def _duty(duty_cycle: float | None, status: str = "ok") -> DutyCycleEstimate:
    n = 100
    exerting = 0 if duty_cycle is None else round(duty_cycle * n)
    return DutyCycleEstimate.model_validate({
        **fixtures.DUTY_CYCLE, "clip_id": CLIP, "duty_cycle": duty_cycle,
        "n_frames_scored": n if status == "ok" else n, "n_frames_exerting": exerting,
        "n_frames_excluded": 0, "status": status,
    })


def _speed(rms: float | None, status: str = "ok") -> HandSpeedEstimate:
    base = fixtures.HAND_SPEED if status == "ok" else fixtures.HAND_SPEED_LOW_COVERAGE
    return HandSpeedEstimate.model_validate({**base, "clip_id": CLIP, "rms_speed_mm_s": rms})


def _frequency(hz: float | None, status: str = "ok") -> FrequencyEstimate:
    base = fixtures.FREQUENCY if status == "ok" else fixtures.FREQUENCY_NO_PEAK
    return FrequencyEstimate.model_validate({**base, "clip_id": CLIP, "hz": hz,
                                             "hz_ci95": None})


def test_the_speed_path_is_the_akkas_equation_of_its_own_inputs() -> None:
    """Golden: the record's `hal` must equal the published equation at one decimal, and the
    record's own validator recomputes it, so a transcribed value cannot survive."""
    score = score_speed_path(_duty(0.68), _speed(612.4))
    assert score.status == "ok"
    assert score.mapping == "akkas-2015-speed-dc"
    assert score.scale_rev == SCALE_REV["akkas-2015-speed-dc"]
    assert score.hal == pytest.approx(round(hal_akkas_2015(612.4, 68.0), 1))
    assert score.rms_speed_mm_s == 612.4 and score.hz is None


def test_the_spectral_path_is_the_radwin_equation_of_its_own_inputs() -> None:
    score = score_spectral_path(_duty(0.68), _frequency(0.42))
    assert score.mapping == "radwin-2015-freq-dc"
    assert score.hal == pytest.approx(round(hal_radwin_2015(0.42, 68.0), 1))
    assert score.hz == 0.42 and score.rms_speed_mm_s is None


def test_the_force_axis_cannot_be_populated_by_any_path() -> None:
    for score in (score_speed_path(_duty(0.68), _speed(612.4)),
                  score_spectral_path(_duty(0.68), _frequency(0.42))):
        assert score.force_axis is None
        assert score.tlv_evaluable is False
        assert "not observable" in score.force_axis_reason


def test_a_zero_duty_cycle_is_a_status_and_not_a_hal_of_zero() -> None:
    """Both equations take ln D. A worker whose hands never engaged is outside the
    instrument's domain, not at hand-activity level zero."""
    score = score_speed_path(_duty(0.0), _speed(612.4))
    assert score.status == "zero_duty_cycle"
    assert score.hal is None and score.hal != 0.0


def test_an_excluded_input_produces_no_input_rather_than_a_number() -> None:
    assert score_speed_path(_duty(None, "no_labels"), _speed(612.4)).status == "no_input"
    assert score_speed_path(_duty(0.68), _speed(None, "low_coverage")).status == "no_input"
    assert score_spectral_path(_duty(0.68), _frequency(None, "no_peak")).status == "no_input"


def test_out_of_range_is_derived_and_not_hidden() -> None:
    """`docs/RUBRIC.md`: inputs outside the fitted range are mapped and flagged, and their
    share reported. Extrapolation is disclosed, never clamped away."""
    inside = score_speed_path(_duty(0.68), _speed(612.4))
    outside = score_speed_path(_duty(0.68), _speed(2000.0))
    assert not inside.out_of_range
    assert outside.out_of_range and outside.hal is not None


def test_a_score_joins_one_clip_to_its_own_inputs() -> None:
    other = HandSpeedEstimate.model_validate({**fixtures.HAND_SPEED,
                                              "clip_id": "factory_001/worker_002/000001"})
    with pytest.raises(ValueError, match="its own speed"):
        score_speed_path(_duty(0.68), other)


def test_the_mapping_never_reads_the_other_path_s_input() -> None:
    """`mapping = akkas` requires a speed and `mapping = radwin` requires a frequency; a
    record with the wrong one present and the right one null is invalid rather than silently
    mapped from the other (`docs/ARCHITECTURE.md`)."""
    score = score_speed_path(_duty(0.68), _speed(612.4))
    assert score.hz is None
    spectral = score_spectral_path(_duty(0.68), _frequency(0.42))
    assert spectral.rms_speed_mm_s is None
