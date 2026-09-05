# Handoff

The resume point. A fresh session should be able to continue from this file without
re-deriving anything.

**Last updated: 2026-09-05 — pre-registration v1.3.0; contracts v1.2; W2 landed and
reviewed (D020). W3's code is landed and its corpus gates pass: the manifest reconciles
three ways (D027), the decode gate passes (D023, `results/decode_probe.json`), and the A14
floor is measured and published (D026), and the fresh-context review is complete with all five
findings addressed (D030, superseding D029). W3 is not closed: it has two external
dependencies, the hand detector and the manipulation labeller, and neither has run. Both
records are written for the pilot and every one of them says so: `FrameSignal` at
`not_attempted`, `HandSpeedEstimate` at `no_detector` (D032). No exposure number exists.**

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
| `PRE-REGISTRATION.md` | v1.3.0, D013–D021, hashed; the version gate walks the chain of prior versions |
| `CONTRACTS.md` | v1.3: `FrameSignal.status` gains `not_attempted` with null provenance (D032); v1.2: provenance on every record, `HALScore` recomputed from its mapping, `pilot_gate`, split dominance shares |
| Code | W2 and W3 landed: `models.py`, `exposure/hal.py`, `estimation/bootstrap.py`, `corpus/` (ports, manifest, sampling, shards, decode), `signal/` (ports, frames, speed, synthetic, flow_farneback, stores); 282 tests; `mypy --strict` clean |
| Novelty gate | **Cleared 2026-09-05, narrowly.** `docs/SURVEY.md` S1–S6 answered |
| Corpus access | HF token in `.env` on the author's machine (gitignored, `chmod 600`); rotate after use |
| Compute | GPU stages on AWS via the CLI, `g5.xlarge` spot; `docs/REPRODUCTION.md` "Compute". The author is not the builder; the stages are specified for whoever runs them |
| HAL scale | **Resolved.** Radwin 2015 and Akkas 2015, open access, residuals published |
| Expert anchor | **None, and none expected.** `docs/DECISIONS.md` D009 |
| Reviews | Every wave ends with a fresh-context review; findings land as a DECISIONS entry. W3's stalled twice before returning a report; what worked was a narrow scope and a hard tool-call budget (D030) |

## The next three things

1. **Obtain the 100DOH checkpoint.** `faster_rcnn_1_8_132028.pth` is published only through
   a Google Drive link that refuses automated download, and no mirror was found (D035). The
   build itself is solved: the ops compile on a current AMI with
   `scripts/detectors/doh100-torch2.patch`, measured on real hardware. **This file is now W3's
   blocking dependency, and it is a distribution problem rather than a compute one** — a
   browser download by a human, or a mirror, unblocks it. The GPU cost that follows is roughly
   6 GPU-hours for the pilot, well under an hour of wall-clock at ~$0.50/h.
2. **Run a manipulation labeller** on the same instants, writing `results/pilot/labels.jsonl`.
   The judge is ~$9 for a calibration subset and needs an OpenAI-compatible endpoint; the
   probe does not exist in this repository yet. Until one runs, H1 is `UNTESTED` — which is
   W4's gate, not W3's.
3. **Close the flow-estimator decision.** Farneback is measured at 116.9 pairs/s with a 0.000
   null rate (D028); RAFT-small is unmeasured, so D024's comparison is incomplete and
   `decision_taken` is `false`. One `g5.xlarge` run over the same 192 seeded pairs closes it.

## Open questions, each with its resolving trigger

| Question | Resolves when |
|---|---|
| Whether EPIC-KITCHENS-100 is reachable for the frequency control | Its institutional-email requirement is met, or the control is reported `UNTESTED` |
| Whether the pilot factory is degenerate | **Closed.** The manifest is built and D012's gates pass; the verdict is pass/fail only and the values stay in `results/` |
| Whether the vendor's manipulation label and the TLV's duty cycle are the same construct | Largely answered by the TLV's own definition of exertion (`docs/SURVEY.md` S3); closed when the pilot's judge labels are read against that sentence. `docs/RED-TEAM.md` A3 |
| Whether the A14 floor is within budget | **Half closed.** The floor is measured and published as a motion budget (D026): 23–37 °/s of rotation or 2.6–4.2 cm/s of translation consumes the whole 0.25 HAL bound. Whether the corpus's real ego-motion sits inside that is not knowable until frames are decoded with a real detector, and the bound is evaluated at W7 |
| Who resolves S2's abstract-only rows | Anyone who opens the six Radwin-lab papers in full and re-tags them; nothing downstream needs it |
| Whether 100DOH's box width is a usable hand-breadth proxy on fisheye | H2c coverage and the hand-breadth sensitivity row at W7 |
