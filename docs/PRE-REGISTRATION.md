# Pre-registration

**Version:** 1.0.0
**Frozen:** 2026-09-05, before `src/` exists and before a single clip is decoded.

> **FROZEN TEXT.** This file is never edited. A change to any threshold, rule or hypothesis
> below goes through a `docs/DECISIONS.md` entry stating the prior value, the new value, the
> rationale and the reversal clause; only then is it applied here in place, together with an
> `## Amendments` entry quoting the prior value and a bump of the version line above.

Git history is the evidence of the ordering. `docs/PRE-REGISTRATION.sha256` pins this file's
contents, and the hash is published so the ordering is provable without exposing the working
tree.

A project whose argument is that a published measurement lacked a stated protocol does not
get to improvise its own.

## What is fixed before data

**Corpus.** `builddotai/Egocentric-10K`, raw release, at a single pinned revision. The
evaluation release is not usable: its `frame_id` is a bare UUID carrying no factory, worker,
clip or timestamp (`../vernier/docs/UPSTREAM-FINDINGS.md`), so no clip can be reconstructed
and no duty cycle computed.

**Analysis rate.** Frames are sampled at **4 Hz**. Nyquist is therefore 2 Hz, or 120
exertions per minute, which spans the range the Hand Activity Level scale is defined over.
A lower rate would alias fast repetitive work into a plausible-looking slow frequency, and
the aliasing would bias exposure *downward* — the direction that flatters the corpus. Any
`FrequencyEstimate` at or above Nyquist is recorded `status: "aliased"` and excluded.

**Clustering.** Every interval clusters over `worker_id`. Clips from one worker share task,
station, tooling and shift; treating them as independent understates interval width. iid
intervals are computed only to sit beside the clustered ones, labelled, exhibiting the
effect. Bootstrap B = 10,000.

**Reporting unit.** Corpus level. `worker_id` and `factory_id` are variance units and appear
in no published number. `docs/ETHICS.md` is the reason; `CONTRACTS.md`'s `ExposureAggregate`
is the enforcement.

**Pilot.** One factory, end to end, before any stratified draw. Its identity is fixed by the
first factory in the pinned revision's sorted manifest, not chosen after inspection.

**Force.** Peak force is not observable from video and is never imputed. Only the HAL axis
is computed. `tlv_evaluable` is `false` on every record in v1.

## Hypotheses

Each carries the condition that falsifies it. A hypothesis whose falsification condition
fires is reported as failed, in the README, in those words.

### H1 — duty cycle is a property of the clip, not of the labeller

Duty cycle computed from two different label sources on the same clips agrees to within
**0.05 mean absolute difference**, and duty cycle at 4 Hz agrees with duty cycle at 8 Hz to
within **0.02 mean absolute difference**.

*Falsified if* either bound is exceeded on the pilot factory. Duty cycle would then be a
measurement of the labeller, and every number downstream of it would inherit that.

### H2 — exertion frequency is recoverable without segmenting exertions

On pilot clips where both estimators resolve, spectral frequency and transition-counting
frequency agree to within **20% relative difference**, and **at least 70%** of pilot clips
are `resolvable` under the pre-registered peak-power floor.

*Falsified if* the agreement bound is exceeded, or if fewer than 70% of clips resolve. The
second half matters as much as the first: an estimator that agrees beautifully on the 15% of
clips where it works has not solved the problem.

### H3 — the resulting distribution is plausible

The corpus median HAL falls inside the range published for comparable manufacturing tasks in
the occupational-health literature.

*Falsified if* it falls outside. **This is a plausibility check and not an agreement
statistic**, and it is labelled as such wherever it appears. No certified ergonomist scored
this corpus, so H3 is the only external comparison available and it is weak by construction.
Passing H3 does not license "cyclegraph measures HAL accurately."

### H4 — exposure structure is between sites, not between people

The between-factory variance component of HAL exceeds the between-worker-within-factory
component.

*Falsified if* the ratio is at or below 1. That result would be substantive rather than a
nuisance: it would say hand-activity exposure is set by the individual rather than by how a
site is organised, which is the opposite of what the industrial-engineering literature
assumes and would be worth reporting on its own.

### H5 — clip observations are not independent

The design effect on HAL, clustered over `worker_id`, exceeds **1**.

Stated with its reading, because this exact ambiguity made a sibling project's equivalent
hypothesis unfalsifiable as written (`../vernier/docs/DECISIONS.md`): **design effect here
means the ratio of variances.** A design effect of 2 corresponds to an interval √2 ≈ 1.41×
wider, not 2× wider. Both numbers are reported.

*Falsified if* the design effect is at or below 1, which would mean the clustering
assumption was unnecessary.

### Negative control — the pipeline measures repetitive hand work, not hands

Median HAL on the factory corpus exceeds median HAL on a non-repetitive egocentric corpus
(Ego4D, EPIC-KITCHENS-100) by at least **1.0** on the 0–10 scale.

*Falsified if* the gap is smaller. The pipeline would then be responding to the presence of
hands rather than to the repetitive structure of the work, and H3's plausibility would be
meaningless. This control runs before H3 is reported.

## Sample sizes and stopping

- **Pilot:** every clip in one factory. No stopping rule; it runs to completion or it fails.
- **Main draw:** stratified over factories, then workers within factory, to a target of
  40,000 clips. The target is fixed here so it cannot be adjusted after seeing an interval.
- **Stopping:** the analysis stops at the pre-registered N. It does not stop early on a
  satisfying interval, and it is not extended on an unsatisfying one.
- **Seeds:** every draw and every bootstrap is seeded, and the seed is recorded on the
  record. No result is published from a single seed where a spread is computable.

## What would make this project stop

`docs/SURVEY.md`'s novelty gate. If automated hand-activity-level assessment from egocentric
video is already published, the correct action is to re-scope, and a redundant result is
worth less than the honesty of noticing.

## Amendments

None.
