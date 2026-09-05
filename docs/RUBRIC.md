# Rubric

**Version:** 1.0.0. Frozen with `docs/PRE-REGISTRATION.md`.

The operational definitions the standards leave open. Every one of these is a choice; the
standards state constructs, not procedures, and a procedure invented after seeing the data
is not a procedure. They are fixed here so a reader can disagree with a specific rule rather
than with a number.

## The unit

**A clip** is the unit of measurement. Not a frame, because exposure is a rate and a rate
needs duration. Not a shift, because the corpus does not reconstruct shifts.

**Clips shorter than 60 s are excluded** with `status: "too_short"`, counted, and reported.
Sixty seconds is three cycles at the slowest frequency the analysis rate can resolve, and a
duty cycle over fewer than three cycles is dominated by where the clip happened to start.

## Duty cycle

**Duty cycle is the fraction of scored frames whose label is "actively manipulating."**

- The denominator is scored frames, not sampled frames. Unreadable frames are excluded and
  the exclusion count travels with the estimate.
- **No smoothing, no interpolation, no gap-filling.** A one-frame dropout stays a dropout.
  Filling it would import an assumption about exertion continuity that this project is
  partly trying to measure.
- A clip with more than **10%** unreadable frames is `status: "no_labels"` and contributes
  nothing. It is counted.

## Exertions and their boundaries

The primary frequency estimate **never segments exertions.** It reads the dominant frequency
out of the manipulation series spectrally, which is why no boundary rule is needed for it.

The transition-counting cross-check does need one, and it is:

- **An exertion begins** at the first frame of a run of `true` labels, and **ends** at the
  last frame before a run of `false` labels.
- **Debounce is 0.5 s** in both directions. A run shorter than that is absorbed into its
  neighbours. At 4 Hz that is two frames — the shortest interruption distinguishable from a
  labelling flicker.
- The debounce threshold is recorded on every `ExertionSegment`, because the segment count
  is a function of it and a reader must be able to see that.

## A cycle

**A cycle is the reciprocal of the dominant frequency.** It is not identified in time and no
cycle boundary is ever located. Factory work is cyclic but the corpus carries no task
annotation, so any cycle boundary would be inferred from the same signal whose period is
being estimated — circular, and it would silently smuggle the answer into the method.

Consequence, stated rather than discovered: cyclegraph reports exposure rates, never
per-cycle metrics. The Strain Index's "duration of exertion per cycle" is therefore
unobservable here, and `docs/COVERAGE.md` marks it so.

## Resolvability

A `FrequencyEstimate` is `resolvable` when its spectral peak exceeds **6×** the median power
of the rest of the spectrum. A clip with no dominant cycle — non-repetitive work, a break, a
walk between stations — is recorded `status: "no_peak"` with `hz: null`.

**Such clips are counted and excluded, never assigned zero.** Assigning zero would treat "no
detectable cycle" as "no repetition," which is the single most consequential way this
pipeline could understate exposure.

## Mapping to the Hand Activity Level scale

HAL is a 0–10 scale determined from exertion frequency and duty cycle. The exact mapping —
whether the published regression or the categorical table, and which edition — is **an open
question, not a placeholder.**

**Resolving trigger:** the ACGIH TLV documentation for Hand Activity Level is obtained and
opened, and the mapping transcribed with its edition recorded in `scale_rev` on every
`HALScore`. Until then no `HALScore` may be written; `make hal` fails loudly rather than
using an approximation.

This is deliberate. An approximate mapping would produce numbers that look like HAL, compare
against published HAL distributions in H3, and be wrong by an unknown offset that H3 could
not detect.

## What a rater would do, if there were one

There is no rater. There is no human-labelled sample in this project and therefore no
agreement statistic — `docs/COVERAGE.md` names it first and `README.md` names it above the
fold.

This section exists to record that the omission is known rather than overlooked, and to fix
what would happen if it changed: a certified ergonomist would score whole clips on HAL,
blind to the pipeline's output, on a stratified sample drawn before any score is seen, and
the resulting agreement would be reported whatever it said.
