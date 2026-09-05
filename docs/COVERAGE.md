# Coverage

What cyclegraph measures, and — the half that matters — what it does not.

Written in the **standards' own vocabulary**, not this project's. Stating a coverage gap in
categories we invented would let us define the gap out of existence. The rows below are the
input variables of the ACGIH TLV for Hand Activity Level and of the Strain Index, in their
order, because those are the instruments a reader will compare this against.

Every claim about what a standard contains is tagged `[S]` — taken from secondary sources,
not from the primary documentation — and is **not load-bearing** until the standard is
obtained and the tag becomes `[V]`. `docs/RUBRIC.md` records the resolving trigger.

## ACGIH TLV for Hand Activity Level `[S]`

The TLV is a two-axis criterion: Hand Activity Level against Normalized Peak Force.

| Input | Status | Why |
|---|---|---|
| **Exertion frequency** | **Observable.** | Recovered spectrally from the per-frame manipulation series. H2 tests it against transition-counting. Bounded above by Nyquist at the 4 Hz analysis rate — 120 exertions/min. |
| **Duty cycle** | **Observable.** | The fraction of scored frames labelled as manipulating. This is the input the whole project turns on: it is what the vendor already publishes, under a different name. |
| **Hand Activity Level (0–10)** | **Derived, pending the scale.** | A function of the two above. The exact published mapping is an open question with a stated resolving trigger (`docs/RUBRIC.md`); no `HALScore` is written until it is resolved. |
| **Normalized Peak Force (0–10)** | **Unobservable. Full stop.** | Force cannot be read from a monocular image of a hand. It is never imputed. `HALScore.force_axis` is `null` on every record with a reason string. |
| **The TLV itself** | **Never evaluated.** | The criterion is a curve in the (HAL, force) plane. With one axis absent, no point can be placed on it. `tlv_evaluable` is `false` on every record in v1. |

**So: one axis of two.** Any summary of this project claiming it "applies the TLV" is wrong,
and this table exists to make that hard to do by accident.

## Strain Index `[S]`

| Task variable | Status | Why |
|---|---|---|
| **Intensity of exertion** | **Unobservable.** | A force judgement. Same wall as Normalized Peak Force. |
| **Duration of exertion per cycle** | **Unobservable.** | Requires locating cycle boundaries. `docs/RUBRIC.md` refuses to locate them: any boundary would be inferred from the same signal whose period is being estimated. cyclegraph reports rates, never per-cycle quantities. |
| **Efforts per minute** | **Observable.** | This is exertion frequency in other units. |
| **Hand/wrist posture** | **Partially observable, not attempted in v1.** | Wrist deviation is in principle recoverable from egocentric hand pose. It needs a pose estimator on fisheye imagery, which vision foundation models handle badly `[S]`, and it is out of scope. Named here so its absence is a decision rather than an oversight. |
| **Speed of work** | **Not attempted.** | A subjective observer rating with no video-derivable definition this project is willing to invent. |
| **Duration of task per day** | **Unobservable.** | The corpus has clips, not shifts. Mean ~7 hours per worker is published for the 100K release, but nothing links clips into a working day. |

**One of six.**

## OCRA `[S]`

Not attempted at all. It requires recovery periods, additional factors and daily duration —
none reconstructible from a clip corpus with no shift structure. Listed so that the reader
who knows the field can see it was considered.

## Within what is measured, what is and is not tested

| | Status |
|---|---|
| Is duty cycle stable across label sources | Tested — H1 |
| Is duty cycle stable across sampling rates | Tested — H1 |
| Does spectral frequency agree with counting exertions | Tested — H2 |
| How often does the spectrum resolve at all | Tested — H2's second bound, and it is the half that usually gets omitted |
| Is the resulting distribution plausible against the literature | Tested — H3, and it is plausibility, not agreement |
| Is exposure structured by site or by person | Tested — H4 |
| Are clips independent observations | Tested — H5 |
| Does the pipeline respond to repetition or merely to hands | Tested — the negative control |
| **Does the pipeline agree with a certified ergonomist** | **Not tested, and this is the largest gap in the project.** No expert scored any sample. There is no agreement statistic. Everything above is internal consistency or literature comparison, and neither is validation. |
| **Is the HAL scale mapping correct** | **Not verified.** Blocked on obtaining the primary standard. Until then `make hal` refuses to run rather than approximating. |
| **Is the vendor's manipulation label itself accurate** | **Not tested here.** It is measured in `../vernier/docs/COVERAGE.md`, on the same corpus, and that project found the judge's 2-hands figure off by ~6pp against its published value while manipulation reproduced within tolerance. cyclegraph inherits that limitation and does not re-measure it. |
| **Is the corpus representative of factory work** | **Not testable.** No published population definition or site-selection method. |
| **Peak force, and therefore injury risk itself** | **Not measured.** HAL is an exposure axis, not a risk prediction. A high HAL at low force is not the same finding as a high HAL at high force, and cyclegraph cannot tell them apart. |

## What a clean result would and would not license

If every hypothesis holds, the licensed conclusion is narrow: *under one sampling design, on
one corpus, at one revision, hand-activity exposure can be recovered from egocentric video
without new annotation, and its distribution is internally consistent and not implausible
against published values.*

It would not license "this corpus shows workers at risk", "the TLV is exceeded", or "this
measures injury risk." Those are three different claims and cyclegraph tests none of them.
