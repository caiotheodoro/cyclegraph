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
    assert int((duration - pair_offset_s()) * ANALYSIS_HZ) + 1 == 40

    times = sample_times(duration)
    assert times[-1] + pair_offset_s() < duration
    assert times[-1] + 2 * pair_offset_s() >= duration  # no further pair fits


def test_the_last_pair_always_ends_strictly_inside_the_clip() -> None:
    for duration in (60.0, 60.25, 61.0, 100.0, 187.4, 433.4, 1200.0):
        times = sample_times(duration)
        assert times, duration
        assert times[-1] + pair_offset_s() < duration, duration
        assert times[-1] + 2 * pair_offset_s() >= duration - 1e-9, duration


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


def test_pairs_are_offset_by_exactly_one_analysis_interval() -> None:
    clip = ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": 100.0})
    pairs = plan_pairs(clip)
    assert all(math.isclose(b - a, pair_offset_s()) for a, b in pairs)
    assert pairs[0][0] == 0.0


def test_nyquist_is_two_hertz_at_the_pre_registered_rate() -> None:
    assert ANALYSIS_HZ == 4.0
    assert nyquist_hz() == 2.0
    assert fixtures.FREQUENCY["nyquist_hz"] == nyquist_hz()


def test_the_rate_is_a_parameter_not_a_hard_coded_four() -> None:
    assert n_samples(10.0, fps_sampled=8.0) == 79
    assert nyquist_hz(8.0) == 4.0
