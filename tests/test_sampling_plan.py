"""Tests for `src/cyclegraph/corpus/sampling.py`."""

from __future__ import annotations

import math

import pytest

from cyclegraph.corpus.sampling import (
    ANALYSIS_HZ,
    n_samples,
    nyquist_hz,
    pair_offset_s,
    plan_pairs,
    sample_times,
)
from cyclegraph.models import ClipRef
from tests import fixtures

# `CONTRACTS.md`'s own HandSpeedEstimate example: 187.4 s at 4 Hz.
CONTRACT_EXAMPLE_DURATION_S = 187.4
CONTRACT_EXAMPLE_N_SAMPLES = 749

# The margin `n_samples` reserves at the end of a clip. Since D045 the speed pair spans one
# frame of the source video, not one analysis period, so this is deliberately larger than the
# pair needs -- see `n_samples`'s docstring for why it was not shrunk.
PLAN_MARGIN_S = 1.0 / ANALYSIS_HZ


def test_it_reproduces_the_contract_example() -> None:
    assert n_samples(CONTRACT_EXAMPLE_DURATION_S) == CONTRACT_EXAMPLE_N_SAMPLES


def test_the_contract_example_does_not_discriminate_so_a_boundary_case_is_pinned() -> None:
    """At 187.4 s every plausible formula agrees, so passing that alone proves nothing.

    At exactly 10 s and 4 Hz the pair at t = 9.75 ends at 10.0, which is the clip's end and
    not inside it, so 39 pairs fit and not 40. Both naive closed forms -- `floor(d*fps)` and
    `floor((d - 1/fps)*fps) + 1` -- return 40 here.
    """
    duration = 10.0
    assert n_samples(duration) == 39
    assert int(duration * ANALYSIS_HZ) == 40
    assert int((duration - PLAN_MARGIN_S) * ANALYSIS_HZ) + 1 == 40

    times = sample_times(duration)
    assert times[-1] + PLAN_MARGIN_S < duration
    assert times[-1] + 2 * PLAN_MARGIN_S >= duration  # no further sample fits


def test_the_last_pair_always_ends_strictly_inside_the_clip() -> None:
    for duration in (60.0, 60.25, 61.0, 100.0, 187.4, 433.4, 1200.0):
        times = sample_times(duration)
        assert times, duration
        assert times[-1] + PLAN_MARGIN_S < duration, duration
        assert times[-1] + 2 * PLAN_MARGIN_S >= duration - 1e-9, duration


def test_a_clip_shorter_than_one_pair_plans_nothing() -> None:
    assert n_samples(0.2) == 0
    assert sample_times(0.2) == []
    with pytest.raises(ValueError):
        n_samples(0.0)


def test_a_clip_below_the_rubric_floor_plans_no_pairs() -> None:
    short = ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": 59.9})
    long = ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": 60.1})
    assert plan_pairs(short) == []
    assert plan_pairs(long)


def test_pairs_are_offset_by_one_frame_of_the_clip_not_one_analysis_interval() -> None:
    """D045, and the regression that catches a revert to the 4 Hz reading. At that reading the
    two frames were 0.25 s apart, and neither flow estimator recovers a working hand's motion
    over that baseline (D044). The offset must come from the clip's own frame rate."""
    clip = ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": 100.0, "fps": 30.0})
    pairs = plan_pairs(clip)
    assert all(math.isclose(b - a, 1.0 / 30.0) for a, b in pairs)
    assert not math.isclose(1.0 / 30.0, PLAN_MARGIN_S)  # the two readings really do differ
    assert pairs[0][0] == 0.0
    # The instants themselves stay on the analysis grid; only the second frame moved.
    assert all(math.isclose(b - a, 1.0 / 60.0)
               for a, b in plan_pairs(ClipRef.model_validate(
                   {**fixtures.CLIP_REF, "duration_s": 100.0, "fps": 60.0})))
    assert [a for a, _ in pairs] == sample_times(100.0)


def test_the_pair_offset_refuses_to_default_to_the_analysis_rate() -> None:
    """The defaulted argument is how a 0.25 s flow baseline entered the pipeline without
    anyone choosing it. A caller has to name the rate now."""
    with pytest.raises(TypeError):
        pair_offset_s()  # type: ignore[call-arg]
    assert pair_offset_s(30.0) == pytest.approx(1.0 / 30.0)
    with pytest.raises(ValueError):
        pair_offset_s(0.0)


def test_nyquist_is_two_hertz_at_the_pre_registered_rate() -> None:
    assert ANALYSIS_HZ == 4.0
    assert nyquist_hz() == 2.0
    assert fixtures.FREQUENCY["nyquist_hz"] == nyquist_hz()


def test_the_rate_is_a_parameter_not_a_hard_coded_four() -> None:
    assert n_samples(10.0, fps_sampled=8.0) == 79
    assert nyquist_hz(8.0) == 4.0
