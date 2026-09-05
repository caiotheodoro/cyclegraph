# Pre-registration

**Version:** 1.2.0
**Frozen:** 2026-09-05, before `src/` exists and before a single clip is decoded.
**Amended:** 2026-09-05, v1.1.0 and v1.2.0, still before a single clip is decoded. The
amendment blocks at the end quote every prior sentence they replaced, and
`scripts/validate.py` refuses any change to the frozen body that a block does not quote.

> **FROZEN TEXT.** This file is never edited. A change to any threshold, rule or hypothesis
> below goes through a `docs/DECISIONS.md` entry stating the prior value, the new value, the
> rationale and the reversal clause; only then is it applied here in place, together with an
> `## Amendments` entry quoting the prior value and a bump of the version line above.

Git history is the evidence of the ordering. `docs/PRE-REGISTRATION.sha256` pins this file's
contents, and the hash is published so the ordering is provable without exposing the working
tree. `scripts/validate.py` checks that every amendment cites a decision that exists and
carries a reversal clause, that every quoted prior sentence really was in the prior
version, and that every unquoted sentence of the prior version survives into the next.

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
`FrequencyEstimate` at or above Nyquist is recorded `status: "aliased"` and excluded. The
hand-speed path samples instantaneous speed from a frame pair (t, t + 1/fps) at each of the
same 4 Hz instants; it samples a speed process and does not track a trajectory, so Nyquist
does not bound it and the RMS over samples is the estimate.

**Mapping.** HAL is computed by a published regression fit to the ACGIH 2001 look-up table,
never by an approximation of this project's own: `radwin-2015-freq-dc` for (frequency, duty
cycle) and `akkas-2015-speed-dc` for (hand speed, duty cycle). `scale_rev` on every
`HALScore` names which. `docs/DECISIONS.md` D013; `docs/SURVEY.md` S3 holds the equations,
the ranges and the golden cells.

**Frequency axis.** Two paths. **Primary: hand speed** — RMS residual optical flow inside
detector hand boxes, ego-motion from the mask complement subtracted, scaled to mm/s by the
clip's median box width against an 85 mm population hand breadth. **Cross-check: spectral
bout frequency** from the manipulation series, reported as a lower bound on exertion
frequency. The only switch to spectral-primary is a pre-registered speed-path failure:
detector coverage below 60% of scored frames on the pilot, or the frequency control (below)
failing on the speed path. A switch is reported as a failure of the speed path, and because
the spectral path has no thresholded frequency control of its own, a switch makes the
frequency control `FAILED` and H3 `UNTESTED` for v1. The speed path's translation floor —
the residual a translation-only synthetic with a static hand produces (`docs/RED-TEAM.md`
A14) — must be at most **20%** of the corpus median RMS speed; above that the path is
reported with the floor subtracted and the subtraction disclosed. `docs/DECISIONS.md` D014,
D020.

**Clustering.** Every interval clusters over the composite `factory_id/worker_id`;
`worker_id` alone is numbered within factory and would pool people across sites
(`docs/DECISIONS.md` D015). Clips from one worker share task, station, tooling and shift;
treating them as independent understates interval width. iid intervals are computed only to
sit beside the clustered ones, labelled, exhibiting the effect. Bootstrap B = 10,000.

**Reporting unit.** Corpus level, plus factory-size-tercile strata that clear a k-anonymity
floor: ≥ 5 factories, ≥ 50 workers, no factory above 40% of the stratum's workers or clips,
worker-weighted. Nothing else. `worker_id` and `factory_id` are variance units and appear in
no published number. `docs/ETHICS.md` is the reason; `CONTRACTS.md`'s `ExposureAggregate`
is the enforcement; `docs/DECISIONS.md` D019 is the rule.

**Pilot.** One factory, end to end, before any stratified draw. Its identity is fixed by the
first factory in the pinned revision's sorted manifest, not chosen after inspection. Because
that factory is nameable, **pilot gates publish pass or fail only, never a value**
(`docs/DECISIONS.md` D018).

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
measurement of the labeller, and every number downstream of it would inherit that. What
happens next is fixed below under *Sample sizes and stopping*: Arm B, not an improvised
re-plan.

### H2 — exertion frequency is recoverable without segmenting exertions

**H2a/H2b, spectral path.** On pilot clips where both estimators resolve, spectral frequency
and transition-counting frequency agree to within **20% relative difference**, and **at
least 70%** of pilot clips are `resolvable` under the pre-registered peak-power floor.

**H2c, speed path.** Detector hand-box coverage is **at least 60%** of scored frames on the
pilot in aggregate, and the flow-failure (`null`) rate is **at most 10%** of samples with a
box.

*Falsified if* any bound is exceeded. The coverage and resolvability bounds matter as much as
the agreement bound: an estimator that agrees beautifully on the 15% of clips where it works
has not solved the problem. H2c failing is the pre-registered trigger for the spectral path
to become primary (D014), and that switch is reported as a failure.

### H3 — the resulting distribution is plausible

The corpus median HAL, on the primary path, falls inside **[2.4, 6.2]** — the pooled
prospective-cohort mean of 4.3 ± one SD of 1.9 across 2,751 manufacturing and service
workers (`docs/SURVEY.md` S4).

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
assumes and would be worth reporting on its own. **Untested under Arm B**, in those words.

### H5 — clip observations are not independent

The design effect on HAL, clustered over `factory_id/worker_id`, is at least **1.2**. The
prior is the sibling project's measurement of 1.25–1.66 on the same corpus.

Stated with its reading, because this exact ambiguity made a sibling project's equivalent
hypothesis unfalsifiable as written (`../vernier/docs/DECISIONS.md`): **design effect here
means the ratio of variances.** A design effect of 2 corresponds to an interval √2 ≈ 1.41×
wider, not 2× wider. Both numbers are reported.

*Falsified if* the design effect is below 1.2. **Untested under Arm B**, in those words.

### Negative control — the pipeline measures repetitive hand work, not hands

Two corpora, two axes, because their manipulation prevalences differ (`docs/DECISIONS.md`
D016) and a single HAL gap would be decided by the corpus mix rather than the pipeline.

- **Duty-cycle control, Ego4D:** factory − Ego4D duty-cycle gap **≥ 0.25** and HAL gap
  **≥ 1.0** on the primary path.
- **Frequency control, EPIC-KITCHENS-100:** factory − EPIC HAL gap **≥ 0.5** on the speed
  path; the spectral-path gap is reported beside it and carries no threshold in v1, which
  is why a switch to spectral-primary makes this control `FAILED` (D020).

*Falsified if* any pre-committed gap is smaller. The pipeline would then be responding to
the presence of hands, or to head motion, rather than to the repetitive structure of the
work, and H3's plausibility would be meaningless. This control runs before H3 is reported.
If EPIC access stays unmet, the frequency control is `UNTESTED` in those words.

## Sample sizes and stopping

- **Pilot:** every clip in one factory. No stopping rule; it runs to completion or it fails.
- **Main draw, two arms, chosen by H1a on the pilot and by nothing else:**
  - **Arm A** (H1a holds): probe labels, stratified over factories then workers within
    factory, to a target of **40,000 clips**.
  - **Arm B** (H1a fails): H1 reported FAILED; judge labels only, stratified the same way,
    to a target of **200 clips (≈ 150,000 frames)**. Arm B tests H2, the negative control and
    H3; H4 and H5 are `UNTESTED`.
  Both targets are fixed here so neither can be adjusted after seeing an interval.
- **Stopping:** the analysis stops at the pre-registered N of whichever arm is running. It
  does not stop early on a satisfying interval, and it is not extended on an unsatisfying
  one.
- **Seeds:** every draw and every bootstrap is seeded, and the seed is recorded on the
  record. No result is published from a single seed where a spread is computable.

## What would make this project stop

`docs/SURVEY.md`'s novelty gate. It ran on 2026-09-05 and cleared, narrowly. If a later
source shows automated hand-activity-level assessment from egocentric video already
published, the correct action is to re-scope, and a redundant result is worth less than the
honesty of noticing.

## Amendments

### v1.1.0 — D013–D019 · prior hash 310dcfa68ae301d62065b0d3e1c50d1fe9edee88a9efbe5a8b323b9cd073e5b3

Applied 2026-09-05, before any clip was decoded and before `src/` existed. Each item quotes
the v1.0.0 sentence it replaced. Four items were added on 2026-09-05 under D020 when the
new chain gate found sentences this block had not quoted; they are marked.

- **Analysis rate** (D014). Added the speed-path sampling sentence. No prior sentence
  replaced.
- **Mapping** (D013). New section. No prior sentence replaced; the prior text carried the
  mapping as an open question in `docs/RUBRIC.md`.
- **Frequency axis** (D014). New section. No prior sentence replaced.
- **Clustering** (D015). Prior: "Every interval clusters over `worker_id`." Now: the
  composite `factory_id/worker_id`.
- **Reporting unit** (D019). Prior: "Corpus level. `worker_id` and `factory_id` are
  variance units and appear in no published number." Now: corpus level plus
  factory-size-tercile strata above a k-anonymity floor. *Added under D020:* Prior:
  "`docs/ETHICS.md` is the reason; `CONTRACTS.md`'s `ExposureAggregate` is the
  enforcement." Now: the same sentence with "`docs/DECISIONS.md` D019 is the rule" appended.
- **Pilot** (D018). Added: pilot gates publish pass or fail only. No prior sentence
  replaced.
- **H2** (D014). Prior heading text unchanged; added H2c. Prior falsification sentence:
  "*Falsified if* the agreement bound is exceeded, or if fewer than 70% of clips resolve."
  Now: any of the three bounds. *Added under D020:* Prior: "The second half matters as much
  as the first: an estimator that agrees beautifully on the 15% of clips where it works has
  not solved the problem." Now: "The coverage and resolvability bounds matter as much as the
  agreement bound", same example.
- **H3** (D013, S4). Prior: "The corpus median HAL falls inside the range published for
  comparable manufacturing tasks in the occupational-health literature." Now: inside
  [2.4, 6.2].
- **H4** (D018). Added: untested under Arm B. No prior sentence replaced.
- **H5** (D015, D017). Prior: "The design effect on HAL, clustered over `worker_id`,
  exceeds **1**." Now: clustered over `factory_id/worker_id`, at least 1.2. Prior:
  "*Falsified if* the design effect is at or below 1, which would mean the clustering
  assumption was unnecessary." Now: below 1.2.
- **Negative control** (D016). Prior: "Median HAL on the factory corpus exceeds median HAL
  on a non-repetitive egocentric corpus (Ego4D, EPIC-KITCHENS-100) by at least **1.0** on
  the 0–10 scale." Now: split into a duty-cycle control on Ego4D and a frequency control on
  EPIC-KITCHENS-100. *Added under D020:* Prior: "*Falsified if* the gap is smaller." Now:
  "*Falsified if* any pre-committed gap is smaller." *Added under D020:* Prior: "The pipeline
  would then be responding to the presence of hands rather than to the repetitive structure
  of the work, and H3's plausibility would be meaningless." Now: the same with "or to head
  motion" inserted.
- **Sample sizes and stopping** (D018). Prior: "**Main draw:** stratified over factories,
  then workers within factory, to a target of 40,000 clips. The target is fixed here so it
  cannot be adjusted after seeing an interval." Now: two arms, 40,000 or 200 clips, chosen
  by H1a. Prior: "**Stopping:** the analysis stops at the pre-registered N." Now: the
  pre-registered N of whichever arm is running.
- **What would make this project stop** (S1–S6). Prior: "`docs/SURVEY.md`'s novelty gate.
  If automated hand-activity-level assessment from egocentric video is already published,
  the correct action is to re-scope, and a redundant result is worth less than the honesty
  of noticing." Now: records that the gate ran and cleared, and keeps the re-scope rule for
  any later finding.

### v1.2.0 — D020 · prior hash 0457cc5d206eb2726997993a3788a910c4c5adaf8ec0fbcfbd12468b304fb145

Applied 2026-09-05 after the fresh-context review, before any clip was decoded. Each item
quotes the v1.1.0 sentence it replaced.

- **Header** (D020). Prior: "`scripts/validate.py` checks that every amendment
  cites a decision that exists and carries a reversal clause, and that every quoted prior
  sentence really was in the prior version." Now: the same, plus "and that every unquoted
  sentence of the prior version survives into the next". Prior: "**Amended:** 2026-09-05,
  v1.1.0, still before `src/` exists and before a single clip is decoded." Now: names both
  versions.
- **Frequency axis** (D020, review finding 22). Prior: "A switch is reported as a failure."
  Now: a switch is a failure of the speed path and makes the frequency control `FAILED` and
  H3 `UNTESTED` for v1. Added the A14 translation-floor pre-commitment at 20% of the corpus
  median RMS speed. Prior: "`docs/DECISIONS.md` D014." Now: "`docs/DECISIONS.md` D014,
  D020."
- **Negative control** (D020). Prior: "**Frequency control, EPIC-KITCHENS-100:** factory −
  EPIC HAL gap **≥ 0.5** on the speed path; the spectral-path gap is reported beside it,
  unthresholded." Now: the same gap, with the consequence of a switch stated.
