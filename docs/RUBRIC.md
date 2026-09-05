# Rubric

**Version:** 1.2.0. Frozen with `docs/PRE-REGISTRATION.md`; amended with it, with the
replaced text quoted at the end.

The operational definitions the standards leave open. Every one of these is a choice; the
standards state constructs, not procedures, and a procedure invented after seeing the data
is not a procedure. They are fixed here so a reader can disagree with a specific rule rather
than with a number.

## The unit

**A clip** is the unit of measurement. Not a frame, because exposure is a rate and a rate
needs duration. Not a shift, because the corpus does not reconstruct shifts.

**Clips shorter than 60 s are excluded** with `status: "too_short"`, counted, and reported.
The clip length bounds the *slowest* cycle the analysis can see; sixty seconds is three
cycles at 0.05 Hz, a 20 s period, and a duty cycle over fewer than three cycles is dominated
by where the clip happened to start. The analysis rate bounds the *fastest* (Nyquist,
2 Hz); the two limits are separate and this floor is about the first.

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

A `FrequencyEstimate` is `resolvable` when its spectral peak exceeds the ratio a white-noise
spectrum of the same length would exceed only **5%** of the time. That floor is
`−ln(1 − 0.95^(1/N)) / ln 2` for a periodogram of `N` bins, it rises with clip length, and it
is **recorded on every `FrequencyEstimate`** because `resolvable` is a function of it — the
same rule the debounce follows on `ExertionSegment`. A clip with no dominant cycle —
non-repetitive work, a break, a walk between stations — is recorded `status: "no_peak"` with
`hz: null`.

**Such clips are counted and excluded, never assigned zero.** Assigning zero would treat "no
detectable cycle" as "no repetition," which is the single most consequential way this
pipeline could understate exposure.

## Hand speed

The primary frequency-axis input (`docs/DECISIONS.md` D014). Defined so that a reader can
disagree with a rule rather than with a number.

- **A speed sample** is taken at each 4 Hz instant from the frame pair (t, t + 1/fps):
  dense optical flow, the **median flow over the complement of the hand mask** taken as the
  camera's ego-motion and subtracted, then the **RMS residual flow magnitude inside the
  largest detected hand box**. Pixels per second.
- **Scale.** Pixel speed is converted to mm/s by `hand_breadth_mm / median_box_width_px`,
  the clip's median detected box width standing in for hand breadth as Akkas 2015 requires.
  `hand_breadth_mm = 85`, the mean of the paper's male and female population means, because
  sex is not known per clip. The choice is disclosed on every `HandSpeedEstimate` and its
  effect on HAL is bounded by re-running with 79.5 and 90.4 in the sensitivity table.
- **Absence.** No box → `null` sample. Flow failure → `null` sample with reason, never zero
  (`docs/RED-TEAM.md` A15). A clip with box coverage below **60%** of scored frames is
  `status: "low_coverage"`; with a flow-null rate above **10%** of boxed samples it is
  `status: "flow_failed"`. Either carries `rms_speed_mm_s: null` and contributes no HAL on
  this path. Both rates are reported.
- **The clip's estimate** is the RMS over its valid samples. It is a sampled speed process,
  not a tracked trajectory; no hand is followed between samples and Nyquist does not apply.
- **Never from a region prior.** A "lower half of the frame" mask is not a hand mask; a
  record built from one is a contract violation.

## Mapping to the Hand Activity Level scale

HAL is a 0–10 scale. Two published regression fits to the ACGIH 2001 look-up table are used,
each with its residual on record (`docs/SURVEY.md` S3; `docs/DECISIONS.md` D013):

| `mapping` | Inputs | Equation | Fit |
|---|---|---|---|
| `radwin-2015-freq-dc` | F exertions/s, D % | `HAL = 6.56 · ln D · [F^1.31 / (1 + 3.18 F^1.31)]` | residual SD 1.18 on Latko's 33 jobs |
| `akkas-2015-speed-dc` | S mm/s, D % | `HAL = 10 · σ(−15.87 + 0.02 D + 2.25 ln S)` | R² 0.99, MSE 0.16 on 30 validation tasks |

- The speed mapping is primary; the frequency mapping runs on the spectral cross-check
  path with `F` understood as bout frequency, a lower bound.
- Values are reported to one decimal, as Radwin 2015 recommends for comparison and
  arithmetic, and rounded to integers only where a TLV category is named.
- Inputs outside the fitted range (F 0.125–1.67/s, D 11–100%, S 255–1288 mm/s) are mapped
  and flagged `out_of_range: true`; their share is reported. Extrapolation is not hidden.
- **No approximation of this project's own.** An approximate mapping would produce numbers
  that look like HAL, compare against published HAL in H3, and be wrong by an offset H3
  could not detect. The published fits carry their own residual, which is the point.
- `scale_rev` on every `HALScore` names the table edition and the fit. If ACGIH revises the
  table, a new `scale_rev` is added and old records keep theirs.

## What a rater would do, if there were one

There is no rater. There is no human-labelled sample in this project and therefore no
agreement statistic — `docs/COVERAGE.md` names it first and `README.md` names it above the
fold.

This section exists to record that the omission is known rather than overlooked, and to fix
what would happen if it changed: a certified ergonomist would score whole clips on HAL,
blind to the pipeline's output, on a stratified sample drawn before any score is seen, and
the resulting agreement would be reported whatever it said.

## Amendments

### v1.2.0 — D034

- **Resolvability** (D034). Prior: "A `FrequencyEstimate` is `resolvable` when its spectral
  peak exceeds **6×** the median power of the rest of the spectrum." Now: the floor is the
  ratio white noise of the same length would exceed 5% of the time, which rises with bin
  count and is recorded on the record. A fixed multiple gets *easier* to clear the longer the
  clip: measured over 40 seeded trials per duration, white noise cleared 6× on 72% of 60 s
  clips and **100%** of clips at 180 s, 433 s and 1200 s — the corpus's actual durations — so
  H2b was satisfiable by a corpus with no repetition in it. Amended before any corpus clip was
  scored spectrally.

### v1.1.0 — D013, D014, D020

- **Mapping to the Hand Activity Level scale** (D013). Prior: "The exact mapping — whether
  the published regression or the categorical table, and which edition — is **an open
  question, not a placeholder.** **Resolving trigger:** the ACGIH TLV documentation for Hand
  Activity Level is obtained and opened, and the mapping transcribed with its edition
  recorded in `scale_rev` on every `HALScore`. Until then no `HALScore` may be written;
  `make hal` fails loudly rather than using an approximation." Now: the two published
  equations, their fits, and their ranges.
- **Hand speed** (D014). New section. No prior text replaced.
- **The unit** (D020). Prior: "Sixty seconds is three cycles at the slowest frequency the
  analysis rate can resolve, and a duty cycle over fewer than three cycles is dominated by
  where the clip happened to start." Now: the clip length bounds the slowest cycle and the
  analysis rate the fastest; the sentence had conflated them.
