# Handoff

The resume point. A fresh session should be able to continue from this file without
re-deriving anything.

**Last updated: 2026-09-05 — W1 cleared; pre-registration v1.2.0; contracts v1.2; W2
landed as three isolated commits and reviewed in a fresh context (D020, 32 findings, all
addressed). The next thing is W3.**

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
| `PRE-REGISTRATION.md` | v1.2.0, D013–D020, hashed; the version gate walks the chain of prior versions |
| `CONTRACTS.md` | v1.2: provenance on every record, `HALScore` recomputed from its mapping, `pilot_gate`, split dominance shares |
| Code | W2 landed: `models.py`, `exposure/hal.py`, `estimation/bootstrap.py`; 190+ tests; `mypy --strict` clean |
| Novelty gate | **Cleared 2026-09-05, narrowly.** `docs/SURVEY.md` S1–S6 answered |
| Corpus access | HF token in `.env` on the author's machine (gitignored, `chmod 600`); rotate after use |
| Compute | GPU stages on AWS via the CLI, `g5.xlarge` spot; `docs/REPRODUCTION.md` "Compute". The author is not the builder; the stages are specified for whoever runs them |
| HAL scale | **Resolved.** Radwin 2015 and Akkas 2015, open access, residuals published |
| Expert anchor | **None, and none expected.** `docs/DECISIONS.md` D009 |
| Reviews | Every wave ends with a fresh-context review; findings land as a DECISIONS entry |

## The next three things

1. **W3.** `make manifest FACTORY=<first in sorted manifest>`; decode pairs at 4 Hz; run
   100DOH; write `FrameSignal` and `HandSpeedEstimate` for the pilot; A14 synthetics.
2. **Decide the flow estimator by measurement, not preference.** Farneback CPU vs RAFT-small
   GPU on 1,000 pairs; the one that meets H2c's null-rate bound at lower cost wins, recorded
   as a DECISIONS entry with the measured rates.

## Open questions, each with its resolving trigger

| Question | Resolves when |
|---|---|
| Whether EPIC-KITCHENS-100 is reachable for the frequency control | Its institutional-email requirement is met, or the control is reported `UNTESTED` |
| Whether the pilot factory is degenerate | The manifest is built and its task and worker spread inspected (D012) |
| Whether the vendor's manipulation label and the TLV's duty cycle are the same construct | Largely answered by the TLV's own definition of exertion (`docs/SURVEY.md` S3); closed when the pilot's judge labels are read against that sentence. `docs/RED-TEAM.md` A3 |
| The A14 translation floor | The synthetic runs at W3 and the residual is measured; the 20% pre-commitment is in the pre-registration (v1.2.0) |
| Who resolves S2's abstract-only rows | Anyone who opens the six Radwin-lab papers in full and re-tags them; nothing downstream needs it |
| Whether 100DOH's box width is a usable hand-breadth proxy on fisheye | H2c coverage and the hand-breadth sensitivity row at W7 |
