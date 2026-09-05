"""Exertion segments and the transition-counting frequency: H2a's cross-check.

`docs/RUBRIC.md` fixes the boundary rule this path needs and the spectral path does not:

- an exertion **begins** at the first frame of a run of `true` and **ends** at the last frame
  before a run of `false`;
- **debounce is 0.5 s in both directions**, and a run shorter than that is absorbed into its
  neighbours -- at 4 Hz, two frames, the shortest interruption distinguishable from a
  labelling flicker;
- the debounce is recorded on every `ExertionSegment`, because the segment count is a
  function of it and a reader must be able to see that.

**Nulls are not absorbed.** An unreadable frame is neither an exertion nor a gap between two,
so it ends whatever run it interrupts and starts nothing. Absorbing it would be gap-filling
by another name: it would join two bouts across an interval nobody scored, and the join would
lower the count in the flattering direction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from cyclegraph.models import DEBOUNCE_S, ClipRef, ExertionSegment, FrequencyEstimate, LabelSource

Label = bool | None


@dataclass(frozen=True, slots=True)
class Run:
    """A maximal stretch of one label value, in frame indices `[start, end)`."""

    value: Label
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start

    def seconds(self, fps: float) -> float:
        return self.length / fps


def runs(series: Sequence[Label]) -> list[Run]:
    out: list[Run] = []
    for i, value in enumerate(series):
        if out and out[-1].value is value:
            out[-1] = Run(value, out[-1].start, i + 1)
        else:
            out.append(Run(value, i, i + 1))
    return out


def debounce(series: Sequence[Label], *, fps: float,
             min_duration_s: float = DEBOUNCE_S) -> list[Label]:
    """Absorb runs shorter than the debounce into their neighbours, repeatedly until stable.

    Repeating matters: absorbing one short run merges its neighbours into a longer run, which
    can leave a *different* short run adjacent to it. A single pass would leave flicker behind
    in exactly the noisy series the debounce exists for.
    """
    if fps <= 0:
        raise ValueError("fps is positive")
    if min_duration_s <= 0:
        raise ValueError("the debounce is positive")
    current = list(series)
    while True:
        blocks = runs(current)
        victim = next(
            (i for i, r in enumerate(blocks)
             if r.value is not None and r.seconds(fps) < min_duration_s
             and (i > 0 or len(blocks) > 1)),
            None,
        )
        if victim is None:
            return current
        neighbours = [blocks[j] for j in (victim - 1, victim + 1)
                      if 0 <= j < len(blocks) and blocks[j].value is not None]
        if not neighbours:
            return current
        into = max(neighbours, key=lambda r: r.length)
        block = blocks[victim]
        for i in range(block.start, block.end):
            current[i] = into.value


def exertion_segments(
    clip: ClipRef, series: Sequence[Label], *, fps: float, label_source: LabelSource,
    min_duration_s: float = DEBOUNCE_S,
) -> list[ExertionSegment]:
    """Every bounded exertion in a debounced series. Never produced by the primary path."""
    debounced = debounce(series, fps=fps, min_duration_s=min_duration_s)
    out: list[ExertionSegment] = []
    for run in runs(debounced):
        if run.value is not True:
            continue
        start_s, end_s = run.start / fps, run.end / fps
        if end_s - start_s < min_duration_s:
            continue  # an edge run the debounce could not absorb
        out.append(ExertionSegment(
            clip_id=clip.clip_id, corpus_rev=clip.corpus_rev,
            start_s=start_s, end_s=end_s, method="transitions",
            min_duration_s=min_duration_s, label_source=label_source,
        ))
    return out


def transition_frequency(
    clip: ClipRef, series: Sequence[Label], *, fps: float, label_source: LabelSource,
) -> FrequencyEstimate:
    """Bout frequency by counting exertions over the clip's duration.

    A clip with no exertion at all is `no_peak` with `hz: null`, not a frequency of zero:
    "no detectable cycle" and "no repetition" are different claims and conflating them is the
    single most consequential way this pipeline could understate exposure (`docs/RUBRIC.md`).
    """
    segments = exertion_segments(clip, series, fps=fps, label_source=label_source)
    nyquist = fps / 2.0
    if not segments:
        return FrequencyEstimate(
            clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, label_source=label_source,
            hz=None, method="transitions", peak_power_ratio=None,
            resolvability_floor=None, resolvable=False,
            hz_ci95=None, nyquist_hz=nyquist, status="no_peak",
        )
    hz = len(segments) / clip.duration_s
    if hz >= nyquist:
        return FrequencyEstimate(
            clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, label_source=label_source,
            hz=None, method="transitions", peak_power_ratio=None,
            resolvability_floor=None, resolvable=False,
            hz_ci95=None, nyquist_hz=nyquist, status="aliased",
        )
    return FrequencyEstimate(
        clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, label_source=label_source,
        hz=hz, method="transitions", peak_power_ratio=None,
        resolvability_floor=None, resolvable=True,
        hz_ci95=None, nyquist_hz=nyquist, status="ok",
    )


def relative_difference(a: float, b: float) -> float:
    """H2a's statistic: |a - b| over their mean, so neither estimator is the denominator."""
    if a <= 0 or b <= 0:
        raise ValueError("a relative difference between frequencies needs two positive values")
    return abs(a - b) / ((a + b) / 2.0)


H2A_RELATIVE_DIFFERENCE: Final[float] = 0.20
"""`docs/PRE-REGISTRATION.md` H2a: spectral and transition-counting agree to within this."""
