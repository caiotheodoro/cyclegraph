"""Tests for `src/cyclegraph/exposure/duty.py`.

The golden case is a series whose mean is known by construction, as `docs/EVALS_CARD.md`
requires for every statistical unit. The rest pin the rubric's two rules that would not fail
loudly if they were wrong: the denominator is scored frames rather than sampled ones, and
nothing is filled in.
"""

from __future__ import annotations

import pytest

from cyclegraph.exposure.duty import (
    H1A_LABEL_SOURCE_MAD,
    H1B_SAMPLING_RATE_MAD,
    agreement,
    duty_cycle_estimate,
    paired_duty_cycles,
)
from cyclegraph.models import UNREADABLE_CEILING, ClipRef, DutyCycleEstimate
from tests import fixtures


def _clip(**over: object) -> ClipRef:
    return ClipRef.model_validate({**fixtures.CLIP_REF, **over})


def test_the_duty_cycle_is_the_known_mean_of_its_series() -> None:
    """Golden case: 7 true, 3 false, no nulls. The answer is 0.7 by construction."""
    series = [True] * 7 + [False] * 3
    est = duty_cycle_estimate(_clip(), series, label_source="judge")
    assert est.status == "ok"
    assert est.duty_cycle == pytest.approx(0.7)
    assert (est.n_frames_scored, est.n_frames_exerting, est.n_frames_excluded) == (10, 7, 0)


def test_the_denominator_is_scored_frames_not_sampled_frames() -> None:
    """The rule that changes the answer. 7 true, 2 false, 1 null: the duty cycle is 7/9, not
    7/10. A null in the denominator would understate every clip that has one."""
    series: list[bool | None] = [True] * 7 + [False] * 2 + [None]
    est = duty_cycle_estimate(_clip(), series, label_source="judge")
    assert est.n_frames_scored == 9 and est.n_frames_excluded == 1
    assert est.duty_cycle == pytest.approx(7 / 9)
    assert est.duty_cycle != pytest.approx(7 / 10)


def test_nothing_is_filled_in() -> None:
    """A one-frame dropout stays a dropout. Both possible fills change the answer, so both
    are asserted against. The series is long enough that the single null stays under the 10%
    ceiling -- otherwise the clip would be `no_labels` and the point would not be testable."""
    series: list[bool | None] = [True] * 22 + [False] * 7 + [None]
    est = duty_cycle_estimate(_clip(), series, label_source="judge")
    assert est.status == "ok"
    assert est.duty_cycle == pytest.approx(22 / 29)
    assert est.duty_cycle != pytest.approx(23 / 30)  # the null filled as true
    assert est.duty_cycle != pytest.approx(22 / 30)  # the null filled as false


def test_the_unreadable_ceiling_is_where_the_rubric_puts_it() -> None:
    ok = duty_cycle_estimate(_clip(), [None] * 10 + [True] * 90, label_source="judge")
    assert ok.status == "ok" and ok.n_frames_excluded == 10
    over = duty_cycle_estimate(_clip(), [None] * 11 + [True] * 89, label_source="judge")
    assert over.status == "no_labels" and over.duty_cycle is None
    assert UNREADABLE_CEILING == 0.10


def test_a_short_clip_is_too_short_whatever_its_labels_say() -> None:
    est = duty_cycle_estimate(_clip(duration_s=59.9), [True] * 100, label_source="judge")
    assert est.status == "too_short" and est.duty_cycle is None


def test_a_failed_decode_is_not_a_duty_cycle_of_zero() -> None:
    est = duty_cycle_estimate(_clip(), [None] * 10, label_source="judge", decode_failed=True)
    assert est.status == "decode_failed" and est.duty_cycle is None


def test_an_all_false_clip_is_a_real_zero_and_not_an_absence() -> None:
    """Zero duty cycle is a measurement. `HALScore` handles it with `zero_duty_cycle`
    precisely because it is a value rather than a gap."""
    est = duty_cycle_estimate(_clip(), [False] * 50, label_source="judge")
    assert est.status == "ok" and est.duty_cycle == 0.0


def _estimates(values: dict[str, float], source: str) -> list[DutyCycleEstimate]:
    out = []
    for clip_id, value in values.items():
        n = 100
        exerting = round(value * n)
        out.append(DutyCycleEstimate(
            clip_id=clip_id, corpus_rev=fixtures.REV, duty_cycle=exerting / n,
            n_frames_scored=n, n_frames_exerting=exerting, n_frames_excluded=0,
            label_source=source,  # type: ignore[arg-type]
            status="ok",
        ))
    return out


def test_agreement_is_the_mean_absolute_difference_over_paired_clips() -> None:
    """Golden: differences of 0.02, 0.04 and 0.06 have a mean absolute difference of 0.04."""
    a = _estimates({"c1": 0.50, "c2": 0.60, "c3": 0.70}, "judge")
    b = _estimates({"c1": 0.52, "c2": 0.56, "c3": 0.76}, "probe")
    result = agreement(a, b, threshold=H1A_LABEL_SOURCE_MAD)
    assert result.n_pairs == 3
    assert result.mean_absolute_difference == pytest.approx(0.04)
    assert result.max_absolute_difference == pytest.approx(0.06)
    assert result.holds  # 0.04 <= 0.05


def test_the_threshold_is_the_pre_registered_one_and_a_miss_fails() -> None:
    a = _estimates({"c1": 0.50}, "judge")
    b = _estimates({"c1": 0.56}, "probe")
    assert not agreement(a, b, threshold=H1A_LABEL_SOURCE_MAD).holds
    assert H1A_LABEL_SOURCE_MAD == 0.05
    assert H1B_SAMPLING_RATE_MAD == 0.02


def test_only_clips_both_sides_scored_are_paired() -> None:
    """A clip one side excluded carries no information about whether they agree, and
    averaging over the union would let a coverage difference read as a duty-cycle one."""
    a = _estimates({"c1": 0.50, "c2": 0.90}, "judge")
    b = _estimates({"c1": 0.52}, "probe")
    assert [p[0] for p in paired_duty_cycles(a, b)] == ["c1"]
    assert agreement(a, b, threshold=H1A_LABEL_SOURCE_MAD).n_pairs == 1


def test_an_agreement_over_nothing_is_not_a_pass() -> None:
    a = _estimates({"c1": 0.5}, "judge")
    b = _estimates({"c2": 0.5}, "probe")
    with pytest.raises(ValueError, match="not a passing result"):
        agreement(a, b, threshold=H1A_LABEL_SOURCE_MAD)
