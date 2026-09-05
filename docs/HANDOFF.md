# Handoff

The resume point. A fresh session should be able to continue from this file without
re-deriving anything.

**Last updated: 2026-09-05 — W1 cleared, pre-registration at v1.1.0, contracts at v1.1,
W2 in progress. The next thing is W2's three isolated commits, then W3.**

## Do not do

- **Do not edit `docs/PRE-REGISTRATION.md` silently.** It is hashed in
  `docs/PRE-REGISTRATION.sha256` and `scripts/validate.py` checks that every amendment
  cites a decision with a reversal clause and quotes a real prior version. Supersede with
  a dated `docs/DECISIONS.md` entry, apply in place, append to `## Amendments`, re-hash.
- **Do not map HAL by anything but the two published equations.** `mapping` is a closed
  enum; `scale_rev` is required. An approximation of this project's own would be wrong by
  an offset H3 could not detect.
- **Do not treat an unresolvable clip, a missing hand, or a failed flow as zero.** Each is
  `null` with a reason, counted and excluded. Zero is the flattering direction.
- **Do not build a `HandSpeedEstimate` from a region prior.** No detector box, no speed.
- **Do not emit a per-worker, per-factory, sub-floor or pilot number,** in code, in a
  notebook, or in a message. `CONTRACTS.md`'s `ExposureAggregate` cannot carry one; do not
  work around it.
- **Do not cluster over bare `worker_id`.** It is numbered within factory. The unit is
  `factory_id/worker_id`.
- **Do not scale the cheap labeller past the pilot before H1 passes.** If it fails, Arm B is
  pre-registered; take it and report H1 FAILED.
- **Do not cite a paper tagged `[S]`** as though it were established. Two remain, both
  reviews, both non-load-bearing.

## State

| | |
|---|---|
| Docs | 19 files under `docs/`, spine complete, tightened after W1 |
| `PRE-REGISTRATION.md` | v1.1.0, D013–D019, hashed, amendment gate green |
| `CONTRACTS.md` | v1.1: `HandSpeedEstimate`, mapping-conditional `HALScore`, strata + k-floor on `ExposureAggregate` |
| Code | W2 in progress: `models.py`, `exposure/hal.py`, `estimation/bootstrap.py` as isolated commits |
| Novelty gate | **Cleared 2026-09-05, narrowly.** `docs/SURVEY.md` S1–S6 answered |
| Corpus access | Inherited from `../vernier`; a gated HF token with accepted terms is required |
| HAL scale | **Resolved.** Radwin 2015 and Akkas 2015, open access, residuals published |
| Expert anchor | **None, and none expected.** `docs/DECISIONS.md` D009 |
| Reviews | Every wave ends with a fresh-context review; findings land as a DECISIONS entry |

## The next three things

1. **Finish W2.** `src/cyclegraph/models.py` with every validator `CONTRACTS.md` names
   (mapping-conditional nulls, k-floor, identifier-pattern rejection); fixtures; golden tests
   for both equations against Radwin 2015 Table 3 and for the bootstrap against synthetic
   clustered data. `mypy --strict` clean.
2. **W3.** `make manifest FACTORY=<first in sorted manifest>`; decode pairs at 4 Hz; run
   100DOH; write `FrameSignal` and `HandSpeedEstimate` for the pilot; A14 synthetics.
3. **Decide the flow estimator by measurement, not preference.** Farneback CPU vs RAFT-small
   GPU on 1,000 pairs; the one that meets H2c's null-rate bound at lower cost wins, recorded
   as a DECISIONS entry with the measured rates.

## Open questions, each with its resolving trigger

| Question | Resolves when |
|---|---|
| Whether EPIC-KITCHENS-100 is reachable for the frequency control | Its institutional-email requirement is met, or the control is reported `UNTESTED` |
| Whether the pilot factory is degenerate | The manifest is built and its task and worker spread inspected (D012) |
| Whether the vendor's manipulation label and the TLV's duty cycle are the same construct | Largely answered by the TLV's own definition of exertion (`docs/SURVEY.md` S3); closed when the pilot's judge labels are read against that sentence. `docs/RED-TEAM.md` A3 |
| The A14 translation floor | The synthetic runs at W3 and the residual is measured |
| Whether 100DOH's box width is a usable hand-breadth proxy on fisheye | H2c coverage and the hand-breadth sensitivity row at W7 |
