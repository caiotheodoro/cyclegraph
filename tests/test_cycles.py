"""Tests for `src/cyclegraph/cycles/`.

Golden cases are synthetic signals of known frequency, as `docs/EVALS_CARD.md` requires. The
last test in this file pins a defect rather than a behaviour, and says so.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cyclegraph.cycles.spectral import (
    H2B_RESOLVABLE_FRACTION,
    resolvable_fraction,
    spectral_frequency,
)
from cyclegraph.cycles.transitions import (
    H2A_RELATIVE_DIFFERENCE,
    debounce,
    exertion_segments,
    relative_difference,
    runs,
    transition_frequency,
)
from cyclegraph.models import DEBOUNCE_S, PEAK_POWER_FLOOR, ClipRef
from tests import fixtures

FPS = 4.0
Label = bool | None


def _clip(duration_s: float = 300.0) -> ClipRef:
    return ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": duration_s})


def _square(hz: float, duration_s: float, *, duty: float = 0.5,
            dropout: float = 0.0, seed: int = 0) -> list[Label]:
    """A square wave of exactly `hz`, sampled at 4 Hz, optionally with holes punched in it."""
    rng = np.random.default_rng(seed)
    out: list[Label] = []
    for i in range(int(duration_s * FPS)):
        value: Label = bool((((i / FPS) * hz) % 1.0) < duty)
        if dropout and rng.random() < dropout:
            value = None
        out.append(value)
    return out


# ---------------------------------------------------------------- transitions


def test_a_single_frame_flicker_is_absorbed_and_an_exact_debounce_is_not() -> None:
    """At 4 Hz the debounce is two frames. One frame is flicker; two is a real interruption,
    and the boundary is the whole point of stating the threshold in seconds."""
    assert debounce([True] * 4 + [False] + [True] * 4, fps=FPS) == [True] * 9
    exact = [True, True, False, False, True, True]
    assert debounce(exact, fps=FPS) == exact


def test_debounce_repeats_until_stable() -> None:
    """Absorbing one short run merges its neighbours, which can leave a different short run
    adjacent. A single pass would leave flicker behind in exactly the noisy series the
    debounce exists for."""
    series: list[Label] = [True, False, True, False, True, *([True] * 8)]
    out = debounce(series, fps=FPS)
    assert all(r.seconds(FPS) >= DEBOUNCE_S for r in runs(out) if r.value is not None)


def test_debounce_is_deterministic_on_a_fully_alternating_series() -> None:
    """Every run is flicker and nothing survives on its own merits. The outcome must at least
    be the same every time: ties absorb into the earlier neighbour."""
    series: list[Label] = [bool(i % 2 == 0) for i in range(8)]
    assert debounce(series, fps=FPS) == debounce(series, fps=FPS)
    assert len(set(debounce(series, fps=FPS))) == 1


def test_a_null_is_never_absorbed() -> None:
    """An unreadable frame is neither an exertion nor a gap between two. Absorbing it would
    join two bouts across an interval nobody scored, and the join lowers the count."""
    series: list[Label] = [True] * 4 + [None] + [True] * 4
    assert debounce(series, fps=FPS)[4] is None


def test_segments_carry_the_debounce_they_were_made_with() -> None:
    """The rubric requires it on every segment, because the count is a function of it."""
    segments = exertion_segments(_clip(), _square(0.25, 120.0), fps=FPS, label_source="judge")
    assert segments
    assert all(s.min_duration_s == DEBOUNCE_S for s in segments)
    assert all(s.end_s > s.start_s for s in segments)


def test_transition_frequency_recovers_a_known_rate() -> None:
    """Golden case: a 0.25 Hz square wave over 300 s is 75 bouts, so 0.25 bouts per second."""
    series = _square(0.25, 300.0)
    est = transition_frequency(_clip(300.0), series, fps=FPS, label_source="judge")
    assert est.status == "ok"
    assert est.hz == pytest.approx(0.25, rel=1e-9)
    assert est.method == "transitions"


def test_a_clip_with_no_exertion_is_no_peak_and_never_zero() -> None:
    """`docs/RUBRIC.md`: treating 'no detectable cycle' as 'no repetition' is the single most
    consequential way this pipeline could understate exposure."""
    est = transition_frequency(_clip(), [False] * 1200, fps=FPS, label_source="judge")
    assert est.status == "no_peak"
    assert est.hz is None
    assert est.hz != 0.0


def test_the_relative_difference_uses_the_mean_as_its_denominator() -> None:
    """So neither estimator is privileged: |a-b| over (a+b)/2 is symmetric, and dividing by
    one of them would make H2a's threshold depend on which was called the reference."""
    assert relative_difference(0.20, 0.25) == pytest.approx(relative_difference(0.25, 0.20))
    assert relative_difference(0.20, 0.25) == pytest.approx(0.05 / 0.225)
    assert H2A_RELATIVE_DIFFERENCE == 0.20


# ------------------------------------------------------------------ spectral


@pytest.mark.parametrize("hz", [0.1, 0.25, 0.5, 0.8])
def test_the_spectral_estimator_recovers_a_known_frequency(hz: float) -> None:
    """`docs/EVALS_CARD.md`: 'the spectral estimator against a synthetic signal of known
    frequency'. Tolerance is one periodogram bin, 1/span, which is the resolution of the
    method rather than a chosen number."""
    duration = 300.0
    est = spectral_frequency(_clip(duration), _square(hz, duration), fps=FPS,
                             label_source="judge")
    assert est.status == "ok" and est.hz is not None
    assert est.hz == pytest.approx(hz, abs=1.0 / duration)


def test_the_two_estimators_agree_within_H2a_on_a_clean_signal() -> None:
    series = _square(0.25, 300.0)
    spectral = spectral_frequency(_clip(300.0), series, fps=FPS, label_source="judge")
    counted = transition_frequency(_clip(300.0), series, fps=FPS, label_source="judge")
    assert spectral.hz is not None and counted.hz is not None
    assert relative_difference(spectral.hz, counted.hz) < H2A_RELATIVE_DIFFERENCE


def test_dropouts_are_analysed_not_repaired() -> None:
    """The reason this path uses Lomb-Scargle. An FFT would need the holes filled, which is
    the gap-filling the duty-cycle rule refuses; the frequency must survive without it."""
    est = spectral_frequency(_clip(300.0), _square(0.25, 300.0, dropout=0.08, seed=3),
                             fps=FPS, label_source="judge")
    assert est.status == "ok" and est.hz is not None
    assert est.hz == pytest.approx(0.25, abs=1.0 / 300.0)


def test_a_constant_series_has_no_dominant_cycle() -> None:
    est = spectral_frequency(_clip(), [True] * 1200, fps=FPS, label_source="judge")
    assert est.status == "no_peak" and est.hz is None


def test_too_many_unreadable_frames_is_no_labels() -> None:
    series: list[Label] = [None if i % 5 == 0 else True for i in range(1200)]
    est = spectral_frequency(_clip(), series, fps=FPS, label_source="judge")
    assert est.status == "no_labels"


def test_the_resolvable_fraction_is_over_every_clip_the_estimator_ran_on() -> None:
    clean = spectral_frequency(_clip(), _square(0.25, 300.0), fps=FPS, label_source="judge")
    flat = spectral_frequency(_clip(), [True] * 1200, fps=FPS, label_source="judge")
    assert resolvable_fraction([clean, flat]) == pytest.approx(0.5)
    assert H2B_RESOLVABLE_FRACTION == 0.70
    with pytest.raises(ValueError):
        resolvable_fraction([])


def test_white_noise_clears_the_pre_registered_peak_floor_which_is_a_defect() -> None:
    """**This pins a defect, not a behaviour.** `docs/DECISIONS.md` D033.

    A periodogram of white noise has peak-to-median ratio growing as ln(N)/ln(2) in the number
    of bins, and the bin count grows with clip length. At the corpus's clip durations that
    ratio exceeds the pre-registered 6x floor essentially always, so an unstructured series is
    reported `resolvable` and H2b can be satisfied by noise. The estimator is faithful to the
    rubric; the rubric's floor is what does not discriminate.

    The test asserts the defect so that a later amendment has to change it deliberately.
    """
    rng = np.random.default_rng(1)
    series: list[Label] = [bool(rng.random() < 0.5) for _ in range(1200)]
    est = spectral_frequency(_clip(300.0), series, fps=FPS, label_source="judge")
    assert est.peak_power_ratio is not None
    assert est.peak_power_ratio > PEAK_POWER_FLOOR
    assert est.resolvable  # and it should not be
    # The predicted noise ratio for this bin count, which the measurement tracks closely.
    n_bins = int(300.0 * FPS / 2)
    assert est.peak_power_ratio == pytest.approx(math.log(n_bins) / math.log(2), rel=0.35)
