# Handoff

The resume point. A fresh session should be able to continue from this file without
re-deriving anything.

**Last updated: 2026-09-05 — pre-registration v1.4.0; contracts v1.2; W2 landed and
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
| `PRE-REGISTRATION.md` | v1.5.0, D013–D055, hashed; the version gate walks the chain of prior versions |
| `CONTRACTS.md` | v1.5: three fields that could not say "not measured" now can — `HALScore.duty_cycle`, `FrequencyEstimate.resolvability_floor`, `HandSpeedEstimate.flow_null_rate` (D054). v1.3: `FrameSignal.status` gains `not_attempted` with null provenance (D032); v1.2: provenance on every record, `HALScore` recomputed from its mapping, `pilot_gate`, split dominance shares |
| Code | W2 and W3 landed: `models.py`, `exposure/hal.py`, `estimation/bootstrap.py`, `corpus/` (ports, manifest, sampling, shards, decode), `signal/` (ports, frames, speed, synthetic with a renderer, flow_farneback, stores), `cycles/`, `exposure/`, `estimation/`; 444 tests; `mypy --strict` clean |
| Novelty gate | **Cleared 2026-09-05, narrowly.** `docs/SURVEY.md` S1–S6 answered |
| Corpus access | HF token in `.env` on the author's machine (gitignored, `chmod 600`); rotate after use |
| Compute | Measured, not estimated. The **labeller is not a GPU stage** — the A10G idled at 0% while the work was decode-bound, and a laptop's MPS matched four paid workers. The **detector is** — 10 frames/s per worker, 30 with three. `docs/METHOD.md` E3 |
| HAL scale | **Resolved.** Radwin 2015 and Akkas 2015, open access, residuals published |
| Expert anchor | **None, and none expected.** `docs/DECISIONS.md` D009 |
| Reviews | Every wave ends with a fresh-context review; findings land as a DECISIONS entry. W3's stalled twice before returning a report; what worked was a narrow scope and a hard tool-call budget (D030). The 2026-09-06 review returned 14 findings, all closed (D052–D055) — including a gate that could not fail, a hypothesis confirmed by data that could not bear on it, and a debounce whose output depended on where the unreadable frames fell |

## The next three things

1. **Finish the speed path's first real run.** EgoHOS is adopted (D047) and its boxes are the
   bounding box of a hand mask's largest connected component (D048); the adapter is written and
   its box logic is tested offline. What remains is running it over the pilot, then
   `scripts/build_signal.py` for real `FrameSignal` and `HandSpeedEstimate` records, then H2c.
   Every `HandSpeedEstimate` written so far is `status: "no_detector"` and carries no
   measurement.
2. **Close the flow-estimator decision.** D024's rule is fixed and only the synthetic arm is
   measured. Both real-pair arms must now be re-run, because D045 changed what a pair *is* —
   any stored `flow_benchmark.json` without a `pair_baseline` field was measured over the
   0.25 s baseline and is not comparable. RAFT's gain curve is measured
   (`results/flow_gain_raft.json`) and does **not** rescue D044's collapse, so the A14 column
   separates the arms over a range the pilot's speeds do not sit in.
3. **The negative control, before H3.** Ego4D and EPIC-KITCHENS-100, unchanged and still
   non-negotiable in that order.

**The five failure shapes this project keeps producing.** Four fresh-context reviews found 42
defects between them, and every round found its defects inside the previous round's *fixes*.
Density rose per line each time — 14 in ~6,200 lines, 12 in ~1,200, 8 in ~500, 8 in ~330 —
because a fix is denser in risk than the code it repairs. Grep for these before writing new
ones:

1. **A gate that cannot fail.** `conflicts_total >= 0`; a sum of three branches compared to
   their own total; `total == 0 or rate < bound`. Ask of every gate: what input makes this FAIL?
2. **A check over absent data.** A rate with an empty denominator; H4 confirmed by a corpus with
   no within-factory information; a `corpus_rev` set built from a field no row carries. An
   unevaluable gate is not a satisfied one.
3. **A rule fixed at one of its consumers.** D043's resume left in the detector; D034's H2b
   guard left out of H4; D054's absence-as-zero left in a third field; D022's drop applied to
   `FrameSignal` and not to the speed path. When an entry names a mechanism, grep for it.
4. **A claim the artifact does not support.** Measured hypotheses reading UNTESTED because
   nothing wrote the verdict; a fitted range quoted from tabulation points; a `corpus_rev`
   check reported as passing; and this very sentence, which claimed all five shapes were here
   when two were (D065, corrected 2026-09-07).
5. **A repair that reads its own diagnosis too narrowly.** D064 fixed "wrote nothing in their
   place" and left "deleted the records", turning a loud crash into a silent overwrite that
   published a false verdict. Only a second look at a fix finds this one.

And the sixth, which is not a defect in code but in reading it: **an absent or constant signal
taken as confirmation.** A `make validate` failure read as success because the signal was a
missing line; a permanently-failing H2c gate read as "no detector has run"; a decode hung for
eleven hours looking exactly like slow work. A false refusal is equally a defect — a guard that
blocks correct work is not conservative, it is broken.

**Read `docs/DECISIONS.md` D044 first if you touch the speed path.** At the baseline the
pipeline used until 2026-09-06, both flow estimators recovered 0.18 of a working hand's motion
— the ratio of the two plane distances — because they report the background inside the hand box
and the rubric then subtracts the background. D045 amended the pair; nothing has been run at the
amended definition yet.

## Open questions, each with its resolving trigger

| Question | Resolves when |
|---|---|
| Whether EPIC-KITCHENS-100 is reachable for the frequency control | Its institutional-email requirement is met, or the control is reported `UNTESTED` |
| Whether the pilot factory is degenerate | **Closed.** The manifest is built and D012's gates pass; the verdict is pass/fail only and the values stay in `results/` |
| Whether the vendor's manipulation label and the TLV's duty cycle are the same construct | Largely answered by the TLV's own definition of exertion (`docs/SURVEY.md` S3); closed when the pilot's judge labels are read against that sentence. `docs/RED-TEAM.md` A3 |
| Whether the A14 floor is within budget | **Half closed.** The floor is measured and published as a motion budget (D026): 23–37 °/s of rotation or 2.6–4.2 cm/s of translation consumes the whole 0.25 HAL bound. Whether the corpus's real ego-motion sits inside that is not knowable until frames are decoded with a real detector, and the bound is evaluated at W7 |
| Who resolves S2's abstract-only rows | Anyone who opens the six Radwin-lab papers in full and re-tags them; nothing downstream needs it |
| Whether a mask's box width is a usable hand-breadth proxy on fisheye | **Encouraging, not settled.** The smoke run's median box is 105 px at 960 wide against ~96 px predicted by the lens geometry for a hand at 0.45 m — two independent routes, 9% apart. Settled by H2c coverage and the hand-breadth sensitivity row at W7 |
| How far a mask box sits from the detector box the rubric was written against | **Never, with these artifacts.** 100DOH cannot be run, so the offset cannot be measured. It is arithmetically a change in `hand_breadth_mm`, so the ±6% sensitivity rows bound it that far and no further. D047, `docs/COVERAGE.md` |
