# Ethics

This measures recordings of identifiable people at work, in order to say something about
their working conditions. That is a different act from measuring a dataset, and it needs its
own basis rather than an inherited one.

## Why `vernier`'s basis does not extend to here

`../vernier/docs/ETHICS.md` states: *"No claim about consent, compensation, or labour
practice. vernier has no evidence either way and will not infer from absence."* Its entire
posture is that it measures the dataset, not the people.

**cyclegraph measures the people.** A statement about hand-activity exposure is a statement
about labour practice — precisely the category `vernier` disclaims. Quietly widening that
document to cover this work would damage the credibility of both. This is a new basis,
stated here, and it is narrower in what it permits than what it replaces.

## What is knowable, and what is not

From the public release: 10,000 hours from 2,153 workers across 85 factories, captured on
the vendor's head-mounted devices in production environments, released under Apache-2.0,
gated on contact details.

Not stated, and therefore not knowable: the consent instrument or its language; whether
workers were compensated for downstream commercial use; whether declining carried
consequence; retention, deletion or withdrawal policy; how the 85 sites were selected.

## The basis

**Consent to be recorded for AI-training data collection is not consent to occupational
health assessment.** Even a fully informed consent to the first does not reach the second,
because the second produces a claim about the person's body and their employer's process
that the first gives no reason to anticipate.

Apache-2.0 is the vendor's licence to grant. It is not a worker's consent, and section 2
records that the consent instrument is unknown.

**Therefore: nothing is reported at a unit any person or site could be identified by.**

## What that forbids, concretely

- **No per-worker result, ever.** `worker_id` is load-bearing for every interval — clips
  from one person are not independent observations — and appears in no published number.
- **No per-factory result either, and no stratum below the floor.** This goes further than
  `vernier`. Factory-level aggregation protects individuals while exposing *sites*: "this
  plant shows exposure above the action limit" is a finding about an identifiable workplace
  whose operators never participated, and the people most exposed to the consequences are
  the workers there. Eighty-five sites are not meaningfully anonymous, and the corpus
  metadata carries no sector field that would let a sector be named either. The only unit
  between corpus and nothing is a **factory-size tercile** that clears ≥5 factories, ≥50
  workers and no factory above 40% of its workers or clips, with one `corpus_rev` per
  release so no two published aggregates can be differenced (`docs/DECISIONS.md` D019).
  A stratum that fails the floor is printed as suppressed, not omitted.
- **No pilot value.** The pilot factory is nameable by construction; its gates publish pass
  or fail only.
- **No ranking of anything.** Not workers, not sites, not shifts.
- **No re-identification of any kind.** No face recognition, no cross-clip linkage, no
  linkage to any external source.

`CONTRACTS.md`'s `ExposureAggregate` has no field that can carry an identifier, and
`docs/ARCHITECTURE.md` names the seam where this would otherwise leak. The rule is enforced
in the schema because a rule enforced by intention survives exactly as long as attention
does.

## The dual-use problem, named

The pipeline that computes hand-activity exposure computes, with no modification, a
per-worker productivity signal. Duty cycle is how much of the time someone's hands are
working. An employer wanting to rank workers by that number needs nothing this project would
not hand them.

The aggregation floor is the mitigation and it is the only one. It is worth being explicit
that it is a *design* mitigation, not a technical impossibility: anyone with the corpus and
this repository's method can compute the per-worker number. What this project controls is
what it publishes and what its own code will emit, and it controls both.

For the same reason this project does **not** ship a "run it on your own site" tool. An
instrument a site runs on its own footage is worker surveillance unless the workers, not
the site, consented to that use; nothing here can inspect that consent, so nothing here
offers the path. The finding is aggregate, and the way to make it actionable is a study
run with the participation of the people concerned — a different study with a different
document.

## The argument against not doing this

Suppression is not the neutral option and should not be treated as one.

Occupational health research uses observational data about workers precisely because the
alternative is that injury patterns stay invisible until they present as injuries. If a
corpus of factory hand work shows exposure above recognised action limits, that is
information with a claim on being known — by the people exposed most of all.

The position this project takes is that the finding should exist and the individuals should
not be identifiable in it. That is a real trade and it is not costless: aggregate-only
reporting means a site with a genuine problem cannot be told it has one. That cost is
accepted here, with the reason, rather than left implicit.

## What this project does not say

It takes no position on Build AI's collection practices. It draws no conclusion the public
artifacts support. Reporting on egocentric data collection elsewhere in the industry exists
and is not evidence about this vendor.

## Conflict of interest

The author has an interest in this work being noticed. That interest is disclosed, and
structurally contained: hypotheses, thresholds and stopping rules are frozen in
`docs/PRE-REGISTRATION.md` before any clip is decoded, so no finding can be shaped by how it
would be received. `docs/RED-TEAM.md` states the containment and its limits.
