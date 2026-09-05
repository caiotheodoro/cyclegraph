# Coverage

What cyclegraph measures, and — the half that matters — what it does not.

Written in the **standards' own vocabulary**, not this project's. Stating a coverage gap in
categories we invented would let us define the gap out of existence. The rows below are the
input variables of the ACGIH TLV for Hand Activity Level and of the Strain Index, in their
order, because those are the instruments a reader will compare this against.

Claims about what a standard contains carry `[V]` when the primary or a peer-reviewed
reproduction of it was opened, and `[S]` with a reason when not. `docs/SURVEY.md` S3 records
what was opened on 2026-09-05.

## ACGIH TLV for Hand Activity Level `[V]`

Inputs and definitions from Radwin et al. 2015, which reproduces the ACGIH 2001 look-up table
and the TLV's operational definitions of exertion and recovery (`docs/SURVEY.md` S3). The
ACGIH document itself was not purchased; the reproduction is peer-reviewed and cites it.

The TLV is a two-axis criterion: Hand Activity Level against Normalized Peak Force.

| Input | Status | Why |
|---|---|---|
| **Exertion frequency** | **Observable.** | Recovered spectrally from the per-frame manipulation series. H2 tests it against transition-counting. Bounded above by Nyquist at the 4 Hz analysis rate — 120 exertions/min. |
| **Duty cycle** | **Observable.** | The fraction of scored frames labelled as manipulating. This is the input the whole project turns on: it is what the vendor already publishes, under a different name. |
| **Hand speed** | **Observable, as a proxy.** | Not a TLV input, but the input of the published speed–duty-cycle HAL equation (Akkas 2015). RMS residual optical flow inside detected hand boxes, scaled by hand breadth. Carries `docs/RED-TEAM.md` A11, A14, A15. |
| **Hand Activity Level (0–10)** | **Derived.** | From (frequency, duty cycle) by Radwin 2015 eq. 3, or from (hand speed, duty cycle) by Akkas 2015. Both are regression fits to the ACGIH table with published residuals; `scale_rev` names which. `docs/DECISIONS.md` D013. |
| **Normalized Peak Force (0–10)** | **Unobservable. Full stop.** | Force cannot be read from a monocular image of a hand. It is never imputed. `HALScore.force_axis` is `null` on every record with a reason string. |
| **The TLV itself** | **Never evaluated.** | The criterion is a curve in the (HAL, force) plane. With one axis absent, no point can be placed on it. `tlv_evaluable` is `false` on every record in v1. |

**So: one axis of two.** Any summary of this project claiming it "applies the TLV" is wrong,
and this table exists to make that hard to do by accident.

## Strain Index `[S]` — Moore & Garg 1995 not opened; the six variables are as named in every secondary source and nothing here depends on their exact definitions, because five of six are marked unobservable regardless

| Task variable | Status | Why |
|---|---|---|
| **Intensity of exertion** | **Unobservable.** | A force judgement. Same wall as Normalized Peak Force. |
| **Duration of exertion per cycle** | **Unobservable.** | Requires locating cycle boundaries. `docs/RUBRIC.md` refuses to locate them: any boundary would be inferred from the same signal whose period is being estimated. cyclegraph reports rates, never per-cycle quantities. |
| **Efforts per minute** | **Observable.** | This is exertion frequency in other units. |
| **Hand/wrist posture** | **Partially observable, not attempted in v1.** | Wrist deviation is in principle recoverable from egocentric hand pose. It needs a pose estimator on fisheye imagery, which vision foundation models handle badly `[S]`, and it is out of scope. Named here so its absence is a decision rather than an oversight. |
| **Speed of work** | **Not attempted.** | A subjective observer rating with no video-derivable definition this project is willing to invent. |
| **Duration of task per day** | **Unobservable.** | The corpus has clips, not shifts. Mean ~7 hours per worker is published for the 100K release (`../vernier/docs/ETHICS.md`), but nothing links clips into a working day. |

**One of six.**

## OCRA `[S]` — not opened; listed only to say it is not attempted

Not attempted at all. It requires recovery periods, additional factors and daily duration —
none reconstructible from a clip corpus with no shift structure. Listed so that the reader
who knows the field can see it was considered.

## A gap that is not about the instrument

**The primary detector's weights cannot be obtained.** 100DOH's two published checkpoints both
return 404 from the Google Drive links its paper and repository give, no mirror was found, and
the repository still advertises them without a deprecation notice (`docs/DECISIONS.md` D037).
The code builds and the training description is still `[V]`; the model those claims describe is
not downloadable.

This is listed here rather than in the red team because it is not an attack on a finding — it
is a hole in what `docs/REPRODUCTION.md` promises. A stranger cannot re-run the speed path as
specified, and that is true regardless of which detector this project ends up using or what
the numbers turn out to be.

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
| **Is the HAL scale mapping correct** | **Verified against the published table within its residual.** Golden tests hold the equations to Radwin 2015 Table 3 cells (`docs/SURVEY.md` S3). What is not verified is whether the ACGIH document has since revised the table; `scale_rev` pins the 2001 edition the fit was made to. |
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
