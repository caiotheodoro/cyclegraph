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
    resolvability_floor,
    resolvable_fraction,
    spectral_frequency,
)
from cyclegraph.cycles.transitions import (
    H2A_RELATIVE_DIFFERENCE,
    debounce,
    exertion_segments,
    null_bounded_segments,
    relative_difference,
    runs,
    scored_seconds,
    transition_frequency,
)
from cyclegraph.models import (
    DEBOUNCE_S,
    PEAK_POWER_FLOOR,
    SPECTRAL_FALSE_ALARM_RATE,
    ClipRef,
)
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


def test_the_resolvability_floor_rises_with_bin_count() -> None:
    """The whole correction. A *fixed* multiple gets easier to clear the longer the clip,
    because a noise periodogram's peak-to-median ratio grows as ln(N)/ln 2 in bin count. The
    derived floor tracks that growth instead of ignoring it (`docs/DECISIONS.md` D034)."""
    floors = [resolvability_floor(n) for n in (120, 360, 866, 2400)]
    assert floors == sorted(floors)
    assert all(f > PEAK_POWER_FLOOR for f in floors)  # every one above the superseded 6x
    # The old floor was below the noise level at every corpus clip length; the new one is not.
    assert floors[0] == pytest.approx(11.19, abs=0.05)
    assert floors[-1] == pytest.approx(15.51, abs=0.05)


def test_white_noise_is_no_longer_reported_resolvable() -> None:
    """D033's defect, fixed. At 180 s -- below the corpus median clip length -- pure noise
    cleared the old 6x floor 100% of the time. Against its own derived floor it clears at
    about the nominal false-alarm rate instead, so H2b is a test again rather than something
    a corpus with no repetition in it would pass."""
    duration = 180.0
    resolved = 0
    trials = 40
    for seed in range(trials):
        rng = np.random.default_rng(1000 + seed)
        series: list[Label] = [bool(rng.random() < 0.5) for _ in range(int(duration * FPS))]
        est = spectral_frequency(_clip(duration), series, fps=FPS, label_source="judge")
        resolved += int(est.resolvable)
    assert resolved / trials <= 0.15  # nominal 5%; the bound leaves room for 40 trials


def test_a_real_signal_still_clears_the_stricter_floor_by_orders_of_magnitude() -> None:
    """The floor must reject noise without rejecting signal. A 0.25 Hz square wave clears its
    own floor by more than three orders of magnitude at every corpus clip length."""
    for duration in (180.0, 433.0):
        est = spectral_frequency(_clip(duration), _square(0.25, duration), fps=FPS,
                                 label_source="judge")
        assert est.status == "ok"
        assert est.peak_power_ratio is not None and est.resolvability_floor is not None
        assert est.peak_power_ratio > 1000 * est.resolvability_floor


def test_the_floor_is_recorded_on_the_record_and_transitions_carry_none() -> None:
    """`resolvable` is a function of the floor and the floor now varies by clip, so it is
    recorded -- the same rule `ExertionSegment.min_duration_s` follows."""
    spectral = spectral_frequency(_clip(300.0), _square(0.25, 300.0), fps=FPS,
                                  label_source="judge")
    counted = transition_frequency(_clip(300.0), _square(0.25, 300.0), fps=FPS,
                                   label_source="judge")
    assert spectral.resolvability_floor is not None
    assert counted.resolvability_floor is None


def test_the_false_alarm_rate_is_the_pre_registered_one() -> None:
    assert SPECTRAL_FALSE_ALARM_RATE == 0.05
    with pytest.raises(ValueError):
        resolvability_floor(1)
    with pytest.raises(ValueError):
        resolvability_floor(100, false_alarm=0.0)


# One 10 s block at 4 Hz, laid out so every run clears the 0.5 s debounce and nothing is
# absorbed. Four exertions, and a 2-frame unreadable gap sitting *inside* what would otherwise
# be one 14-frame exertion -- which is the case the frequency denominator and the null-boundary
# count exist for.
#   0-3   True    exertion 1
#   4-7   False
#   8-11  True    exertion 2, ends against the nulls
#   12-13 None
#   14-17 True    exertion 3, begins against the nulls
#   18-21 False
#   22-25 True    exertion 4
#   26-39 False
_BLOCK: list[Label] = (
    [True] * 4 + [False] * 4 + [True] * 4 + [None] * 2
    + [True] * 4 + [False] * 4 + [True] * 4 + [False] * 14
)
_BLOCKS = 10
_GAPPY: list[Label] = _BLOCK * _BLOCKS
_GAPPY_DURATION_S = 100.0          # 400 frames at 4 Hz
_GAPPY_SEGMENTS = 4 * _BLOCKS      # 40
_GAPPY_SCORED_S = 95.0             # 380 of 400 frames scored, at 4 Hz


def test_the_frequency_denominator_is_scored_time_not_the_clip_duration() -> None:
    """A count of exertions found only in scored frames, over the whole clip's wall-clock,
    would impute *no exertion* to every unreadable stretch. `docs/RUBRIC.md` already fixes duty
    cycle's denominator as scored frames; this is the same convention, and D042 records that
    it moves H2a's disagreement in the unflattering direction rather than the flattering one."""
    assert len(_GAPPY) == 400
    assert scored_seconds(_GAPPY, fps=FPS) == pytest.approx(_GAPPY_SCORED_S)
    estimate = transition_frequency(_clip(_GAPPY_DURATION_S), _GAPPY, fps=FPS,
                                    label_source="probe")
    assert estimate.status == "ok"
    assert estimate.hz is not None
    # 40 / 95.0, not 40 / 100.0 -- the two differ by the 5% that was unreadable.
    assert estimate.hz == pytest.approx(_GAPPY_SEGMENTS / _GAPPY_SCORED_S)
    assert estimate.hz != pytest.approx(_GAPPY_SEGMENTS / _GAPPY_DURATION_S)


def test_the_two_denominators_agree_exactly_when_nothing_is_unreadable() -> None:
    """The change is confined to clips with nulls; a fully scored clip is untouched."""
    series: list[Label] = [*(([True] * 4 + [False] * 4) * 50)]  # 400 frames, 50 exertions
    estimate = transition_frequency(_clip(100.0), series, fps=FPS, label_source="probe")
    assert estimate.hz is not None
    assert estimate.hz == pytest.approx(50 / 100.0)
    assert scored_seconds(series, fps=FPS) == pytest.approx(100.0)


def test_segments_whose_boundary_is_an_unreadable_frame_are_counted_not_repaired() -> None:
    """The disclosure D042 adds. Two of the four exertions per block end or begin against the
    nulls; the count says so, and the segment count is left alone."""
    assert null_bounded_segments(_GAPPY, fps=FPS) == 2 * _BLOCKS
    assert len(exertion_segments(_clip(_GAPPY_DURATION_S), _GAPPY, fps=FPS,
                                 label_source="probe")) == _GAPPY_SEGMENTS
    # A series with no nulls has no null-bounded segment, whatever its shape.
    assert null_bounded_segments(([True] * 4 + [False] * 4) * 50, fps=FPS) == 0


def test_a_wholly_unreadable_series_is_no_peak_rather_than_a_division_by_zero() -> None:
    estimate = transition_frequency(_clip(100.0), [None] * 400, fps=FPS, label_source="probe")
    assert estimate.status == "no_peak" and estimate.hz is None
    assert scored_seconds([None] * 400, fps=FPS) == 0.0


def test_an_unabsorbable_short_run_does_not_stop_the_debounce(fps: float = FPS) -> None:
    """A short run flanked by nulls on both sides has nothing to be absorbed into, and that is
    a fact about that run -- not a reason to leave every later flicker in the clip in place.

    `debounce` returned at the first such run, so a single-frame gap between two long bouts was
    absorbed on a series with no nulls and left alone on one with them. The segment count was
    therefore a function of where the unreadable frames fell, which is the confound
    `docs/DECISIONS.md` D042 exists to keep *out* of the count."""
    flicker: list[Label] = [*([True] * 20 + [False] + [True] * 20)]
    assert [(r.value, r.length) for r in runs(debounce(flicker, fps=fps))] == [(True, 41)]

    # The same flicker, behind a short run that cannot be absorbed. It must still be absorbed.
    blocked: list[Label] = [None, True, None] + flicker + [None] * 3
    shaped = [(r.value, r.length) for r in runs(debounce(blocked, fps=fps))]
    assert (True, 41) in shaped
    assert (False, 1) not in shaped
    # And the unabsorbable run survives rather than being silently rewritten.
    assert (True, 1) in shaped


def test_the_segment_count_does_not_depend_on_where_the_nulls_fell() -> None:
    """The property the defect broke, stated as the thing that matters: prefixing a clip with
    an unreadable stretch must not change how many exertions the rest of it contains."""
    body: list[Label] = [*(([True] * 8 + [False] + [True] * 8 + [False] * 8) * 3)]
    plain = len([r for r in runs(debounce(body, fps=FPS)) if r.value is True])
    prefixed = len([r for r in runs(debounce([None, True, None] + body, fps=FPS))
                    if r.value is True])
    assert prefixed == plain + 1  # only the prefix's own unabsorbable run is added
