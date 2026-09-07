# Decisions

Append-only. Each entry: the decision, its reason, and what would reverse it. Entries are
never edited; a change is a later entry naming what it supersedes.

Seeded 2026-09-05 from the scoping session that created this repository.

## D001 — Documentation before code

`docs/PRE-REGISTRATION.md`, `docs/RUBRIC.md` and `CONTRACTS.md` freeze before `src/` exists.
The project's argument is that a measurement was published without a stated protocol.
Improvising this one would be self-refuting, and git history is the only evidence of
ordering that cannot be reconstructed after the fact.

**Reverses if:** nothing.

## D002 — Repository named `cyclegraph`

Frank Gilbreth's c.1913 instrument: a small lamp fixed to a worker's hand, photographed at
long exposure, the developed plate showing the path of one work cycle. This is the same
measurement from the hand's own point of view, a century later and at 10,000 hours.
Consistent with the sibling naming line — `vernier`, `assay`, `plumb`, `titer`, `sonar` —
where the name is the instrument the project is.

**Reverses if:** nothing.

## D003 — HAL is the index; RULA and REBA are not

**Decision.** The Hand Activity Level axis of the ACGIH TLV is the index. RULA and REBA are
not used.

**Rationale.** RULA and REBA score trunk, neck, legs and upper arm. A head-mounted camera
never sees a trunk. Every published video-ergonomics system is third-person for this reason,
and building on RULA/REBA from an egocentric viewpoint would be building on an ill-posed
foundation. HAL, the Strain Index and OCRA are hand-and-wrist instruments designed for
repetitive manufacturing work and score what this viewpoint does see.

**Evidence.** `docs/COVERAGE.md` maps every input of the TLV and of the Strain Index against
what is observable here. `docs/SURVEY.md` records the third-person finding; it is `[S]` and
gates the project until opened.

**Alternatives rejected.** RULA/REBA on the observable distal subset — a partial score
against a whole-body scale is not interpretable. A new video-native index — invites "why
should I believe your index" and forfeits decades of occupational-health validation.

**Reverses if:** egocentric whole-body pose estimation becomes reliable enough on fisheye
imagery that the proximal segments RULA/REBA need are recoverable. The camera motion carries
some trunk information in principle; nothing here depends on that.

## D004 — Unobservable inputs are reported absent, never estimated

Peak force cannot be read from video. It is recorded `null` with a reason string, and the
TLV is never evaluated.

An imputed force would look plausible, propagate into every downstream number, and be wrong
by an offset no internal check could detect — while converting a gap a reader can see into
an error they cannot.

**Reverses if:** nothing. An instrumented subset with measured force would be a different
study, not an amendment to this one.

## D005 — Spectral frequency is primary; transition-counting is the cross-check

**Decision.** Exertion frequency is estimated spectrally from the manipulation series.
Transition-counting runs on the same clips as a cross-check and is the subject of H2.

**Rationale.** Counting exertions requires deciding where one ends and the next begins,
which is where label noise concentrates and where an arbitrary debounce threshold silently
sets the answer. Spectral estimation never locates a boundary. Cyclic work has a dominant
frequency; recovering it is a well-posed signal problem rather than an annotation problem.

**Evidence.** `docs/RUBRIC.md` fixes the debounce at 0.5 s and records it on every segment,
precisely because the count is a function of it.

**Alternatives rejected.** A learned temporal segmenter — needs labels this project does not
have. Duty cycle only, no frequency — HAL needs both, and duty cycle alone cannot
distinguish slow heavy work from fast light work.

**Reverses if:** H2 fails and the disagreement traces to the spectral side.

## D006 — Corpus-level reporting only; worker *and* factory are variance units

Both identifiers are load-bearing for interval estimation and appear in no published number.
This goes further than `../vernier/docs/ETHICS.md`, which protects individuals but reports
nothing at site level either way.

Factory-level aggregation would expose sites: a finding about an identifiable workplace
whose operators never participated, where the people carrying the consequences are the
workers there. 85 sites with published client sectors are not meaningfully anonymous.

Enforced in `CONTRACTS.md` — `ExposureAggregate` has no field able to carry an identifier —
rather than by convention, because a rule enforced by intention survives as long as
attention does.

**Reverses if:** nothing, at this consent basis. A study run with the participation of the
sites concerned would be a different study with a different document.

## D007 — A new ethics basis, not an extension of `vernier`'s

`../vernier/docs/ETHICS.md` explicitly disclaims claims about labour practice. cyclegraph
makes one. Widening that document to cover this work would damage the credibility of both;
`docs/ETHICS.md` states its own basis and is narrower in what it permits.

**Reverses if:** nothing.

## D008 — Self-documented ethics, no external review, and that is a disclosed weakness

**Decision.** The ethics basis is self-documented. No IRB or equivalent review is sought
before v1.

**Rationale.** No institutional affiliation is available to route a review through, and the
alternative — proceeding while claiming review is forthcoming — would be worse than
proceeding while saying plainly that there is none.

**Evidence.** The aggregation floor is enforced schema-side rather than by policy, which is
the strongest mitigation available without a reviewer.

**Alternatives rejected.** Seeking review first — weeks, and it needs an affiliation.
Proceeding silently — the failure mode this repository exists to criticise.

**Reverses if:** an affiliation becomes available, or any finding moves toward a
site-identifiable claim. The second is a hard trigger, not a preference.

## D009 — No expert anchor, and the claim is downgraded to match

**Decision.** No certified ergonomist scores a sample. v1 does not claim to measure HAL
accurately.

**Rationale.** None is available. The honest consequence is a downgrade, not a
reinterpretation of what the remaining evidence shows: internal consistency and literature
plausibility are not validation, and the README says so above the fold rather than in a
limitations section.

**Evidence.** H3 is labelled a plausibility check wherever it appears. `docs/COVERAGE.md`
names the missing agreement statistic as the project's largest gap.

**Alternatives rejected.** Treating agreement with the vendor's own labels as validation —
that measures agreement with a judge whose 2-hands figure `vernier` found off by ~6pp.
Self-rating by the author — not an independent context, and not a qualification.

**Reverses if:** an ergonomist becomes available. `docs/RUBRIC.md` fixes the protocol in
advance so the result would be reportable whatever it said.

## D010 — Analysis rate is 4 Hz

Nyquist is then 2 Hz, or 120 exertions per minute, spanning the range the HAL scale is
defined over. A lower rate would alias fast repetitive work into a plausible slow frequency,
and the aliasing would bias exposure *downward* — the direction that flatters the corpus,
which is the direction an unforced error should never run.

**Reverses if:** H1's sampling-rate bound fails between 4 Hz and 8 Hz, which would mean 4 Hz
is already too coarse for duty cycle, not only for frequency.

## D011 — The raw release only; the evaluation release cannot support this

`builddotai/Egocentric-10K-Evaluation`'s `frame_id` is a bare UUID carrying no factory,
worker, clip or timestamp (`../vernier/docs/UPSTREAM-FINDINGS.md`). No clip can be
reconstructed from it and no duty cycle computed. The raw corpus is 19,495 h265 WebDataset
shards, reachable a frame at a time over HTTP range requests via ffmpeg's `subfile`
protocol, established in `../vernier/docs/DECISIONS.md`.

**Reverses if:** a release ships clip-linked frame identifiers.

## D012 — One factory end to end before any stratified draw

The pilot is every clip in a single factory, fixed as the first in the pinned revision's
sorted manifest rather than chosen after inspection. It exercises decode, labelling, duty
cycle, spectral frequency and aggregation at a scale that can be inspected by eye. The
stratified draw follows only if the pilot's gates pass.

**Reverses if:** the pilot factory turns out to be degenerate — a single task, or too few
workers to estimate a design effect. That would be a documented re-draw with the reason, not
a silent one.

## D013 — HAL mapping from the published equations; `scale_rev` names the fit

**Decision.** `HALScore` is computed by one of two peer-reviewed regression fits to the ACGIH
2001 look-up table, and `scale_rev` records which: `radwin-2015-freq-dc` (Radwin et al.
2015, `HAL = 6.56 ln D [F^1.31 / (1 + 3.18 F^1.31)]`, residual SD 1.18) or
`akkas-2015-speed-dc` (Akkas et al. 2015, `HAL = 10 σ(−15.87 + 0.02 D + 2.25 ln S)`, S in
mm/s, validation R² 0.99, MSE 0.16). Supersedes `docs/RUBRIC.md`'s "the ACGIH TLV
documentation must be obtained" and `docs/METHOD.md` E6's "the standard's purchase price".

**Rationale.** `docs/SURVEY.md` S3 opened both papers on 2026-09-05. The prior text asserted
a blocker that did not exist; a project whose argument is that measurements get published
without protocols does not get to keep a false blocker in its own protocol once it is known
to be false. The ACGIH document remains the authority, and every record says the number is a
fit to its table, not the table.

**Evidence.** Golden tests hold each equation to the paper's Table 3 cells within the paper's
residual (`tests/test_hal_mapping.py`, W2).

**Alternatives rejected.** Purchasing the ACGIH document anyway — it adds the table the
papers already reproduce and does not add a validation. Using the 2001 linear model the
committee used — Radwin 2015 shows it under-predicts both tails and is not a continuous
function.

**Reverses if:** ACGIH publishes a revised HAL table whose cells differ from the 2001 table
by more than the fitted residual, in which case a new `scale_rev` is added and the old one is
kept for records already written.

## D014 — Two frequency-axis paths; hand speed is primary, spectral is the cross-check

**Decision.** The manipulation-series spectral peak measures manipulation-*bout* frequency,
which is a lower bound on exertion frequency: a hand stays "manipulating" through ten
consecutive screw turns that the TLV counts as ten exertions. It is retained as the
cross-check and reported as a lower bound. **Primary HAL comes from the speed–duty-cycle
path:** RMS hand speed from optical flow inside detector hand boxes (100DOH, MIT; EgoHOS as
fallback segmenter), with camera ego-motion estimated from the **complement** of the hand
mask and subtracted, sampled at the pre-registered 4 Hz using a frame pair (t, t + 1/fps) at
each sample. Pixel speed is scaled to mm/s by the clip's median hand-box width against a
population hand breadth of 85 mm (the mean of Akkas 2015's 90.4 male / 79.5 female, sex
unknown per clip, disclosed). If no detector box is available the speed sample is `null`
with a reason; if fewer than 60% of a clip's scored frames have a box, the clip's speed
estimate is `status: "low_coverage"` and its speed-path HAL is `null`. **Never mapped from a
region prior.**

**The only pre-registered switch to spectral-primary** fires on a speed-path failure that
does not reference H3: (a) detector coverage below 60% of scored frames on the pilot in
aggregate, or (b) the EPIC-KITCHENS frequency control (D016) fails on the speed path. A switch
is reported as a failure of the speed path, in those words.

**Rationale.** Speed–duty-cycle is the validated automated-HAL lineage (`docs/SURVEY.md` S2);
it needs no exertion boundary and no spectral peak, and it is the input the ACGIH table's
own authors chose when they automated the measurement. Bout frequency would have made every
HAL a systematic under-statement in the direction that flatters the corpus.

**Evidence.** `docs/RED-TEAM.md` A10 (the construct gap), A11, A14, A15 (what the speed path
can get wrong). The rotation-only synthetic in `docs/WAVES.md`'s checklist is the golden test.

**Alternatives rejected.** Letting the pilot choose the path by which HAL median lands
nearer the literature — selects the estimator on H3's own outcome and makes H3 unfalsifiable.
Spectral on the hand-count series — same saturation problem. A learned exertion segmenter —
no labels.

**Reverses if:** an exertion-level label source becomes available, at which point counted
exertion frequency is the direct input and both proxies are demoted.

## D015 — The cluster unit is the composite `factory_id/worker_id`

`worker_id` is numbered *within* factory: `worker_001` exists in all 85 factories
(`../vernier/docs/DECISIONS.md` D072 found this the hard way — a partial manifest held 37
bare ids across 216 real pairs). Clustering over the bare id would pool up to 85 different
people as one cluster and shrink every interval. `cluster_unit` is the literal string
`factory_id/worker_id` and nothing else is accepted.

**Reverses if:** the corpus re-issues globally unique worker identifiers.

## D016 — The negative control is split by corpus and by axis

`vernier` measured manipulation prevalence at Ego4D 0.50–0.53 and EPIC-KITCHENS-100
0.86–0.89 against the factory's 0.92. A single "HAL gap ≥ 1.0" is therefore decided by duty
cycle alone on Ego4D and cannot pass on EPIC at all; it tests the corpus mix, not the
pipeline, and does not test `docs/RED-TEAM.md` A4.

**Decision.** Ego4D is the **duty-cycle control**: factory − Ego4D duty-cycle gap ≥ 0.25 and
HAL gap ≥ 1.0. EPIC-KITCHENS-100 is the **frequency control**: factory − EPIC speed-path HAL
gap ≥ 0.5; the spectral-path gap is reported beside it. The control fails if any
pre-committed gap fails. If EPIC access stays unmet, the frequency control is `UNTESTED` in
those words and A4 stays OPEN.

**Reverses if:** nothing at this corpus set. A third control corpus would be an addition.

## D017 — H5's threshold is a design effect of at least 1.2

`> 1` is near-tautological; `vernier` measured 1.25–1.66 on the same corpus at the same
cluster unit. The prior from the sibling is used, and the threshold is placed where the
sibling's lowest measurement would still clear it by a margin small enough to be a real
test.

**Reverses if:** nothing; a failure is a finding.

## D018 — The main draw is a two-arm conditional design, fixed before the pilot

**Decision.** **Arm A** (H1a passes on the pilot): probe labels, N = 40,000 clips as before.
**Arm B** (H1a fails): H1 is reported FAILED; the main draw is judge-only on **N_B = 200
clips ≈ 150,000 frames** (~750 frames per clip at 4 Hz over ~187 s), stratified over
factories then workers. Arm B supports H2, the negative control and H3. **H4 and H5 are
`UNTESTED` under Arm B**, in those words: 200 clips cannot estimate a between-factory
variance component. The stopping rule names both arms so neither N is chosen after an
interval is seen.

**Cost, from measured sibling rates** (`../vernier/docs/DECISIONS.md` D072 region: $8.56
per 10,000 frames for both prompt variants, ~0.47 frames/s on one container): Arm B ≈ $65
and ~4 days single-container, less with concurrency. An earlier draft of this entry put Arm B
at 8,000 clips; that is ~6 million frames, ~$2,600 and months, and it was not affordable.
The number was corrected before it was pre-registered.

**Pilot gates publish pass/fail only.** The pilot factory is nameable (first in sorted
manifest), so any pilot *value* — an H1 mean absolute difference, an H2 agreement figure —
is a per-factory number and stays in `results/` unpublished. The card carries the verdict.

**Reverses if:** the probe is replaced by a labeller whose fidelity is measured ≥ 0.90, at
which point Arm B is unnecessary and is removed by amendment.

## D019 — Reporting strata with a k-anonymity floor; size terciles only in this version

**Decision.** In addition to the corpus-level aggregate, an `ExposureAggregate` may be
published for a **stratum** iff: ≥ 5 factories, ≥ 50 workers, no single factory contributes
more than 40% of the stratum's workers **or** of its clips, and stratum estimates are
worker-weighted. The only strata defined in v1.1.0 are **factory-size terciles by worker
count**. Sector strata are **not** defined: the per-clip metadata carries no sector field
(`docs/SURVEY.md` found none; `README.md`'s earlier "published client sectors" was
unsupported and is corrected), and a sector with exactly five public clients would name
five companies. A future sector amendment needs a published taxonomy and k ≥ 10.

**Differencing.** One `corpus_rev` per release. Strata are re-derived on any re-pin and
every prior stratum aggregate is withdrawn from the release, never published alongside, so
no two published aggregates differ by fewer than the floor.

**Enforcement.** Schema, not policy: `ExposureAggregate.stratum` is a closed enum, the
definition field may hold only a path under `docs/`, `k_factories`/`k_workers`/
`max_factory_share` are required, and the validator rejects any string anywhere in the
record matching `factory_\d+|worker_\d+`. `docs/ETHICS.md`'s "no per-factory result" becomes
"no result below the floor", which is stricter in the case that matters and permits one
stratum level that a site cannot be identified from.

**Reverses if:** any published stratum is shown to identify a site, at which point strata
are withdrawn and the corpus-level aggregate is the only reporting unit again.

## D020 — Fresh-context review of the W1–W2 branch: 32 findings, and what changed

**Decision.** The review `docs/WAVES.md` requires at the end of every wave ran on
2026-09-05 in a fresh context against the whole branch (`333b167..1f5c2d6`). It returned 32
findings, three blocking. Every one is addressed in the commit that carries this entry, and
the ones that change a frozen document or a schema are listed here so the record is
complete. This entry also names two supersessions the file's own header requires and that
D014 and D019 omitted: **D014 supersedes D005** (spectral is no longer primary) and **D019
supersedes D006** (corpus-level is no longer the only reporting unit).

**Blocking, and fixed.**

1. `scripts/validate.py`'s pre-registration version gate bound the amendment blocks and the
   hash, not the frozen body: a simulated silent edit of H3 with a re-hash and a one-line
   DECISIONS touch passed both gates. The gate now walks the chain — every sentence of each
   prior version that its amendment block does not quote as replaced must still be present
   in the next version — and a test performs the tampering and asserts it is caught. Running
   the new gate on v1.1.0 found **four sentences its own amendment record did not quote**
   (the reporting-unit enforcement sentence, H2's "second half" sentence, and two negative-
   control sentences). They are added to the v1.1.0 block now; the quotes are checked
   against the v1.0.0 blob so the correction cannot itself be wrong.
2. A pilot value could reach the card through `MeasurementClaim.interval` on an H1/H2 claim.
   `pilot_gate` is now a required field, must be `true` exactly for the pilot-gated claim
   ids, and a gated claim with an interval is rejected.
3. The identifier pattern missed the corpus's shard naming (`factory001_worker001_part00`)
   and any capitalisation. It is now `(factory|worker)[_-]?\d{2,}`, case-insensitive, in
   both `models.py` and `validate.py`, and dictionary keys are walked as well as values.

**Schema changes, `contracts/v1.2`.** `corpus_rev` on every record and `label_source` on
every estimate at or above `HALScore` (seams 1 and 2 were prose above the frame level).
`HALScore.hal` is recomputed from the named mapping on construction, `scale_rev` must equal
the mapping's, `out_of_range` is derived, and a zero duty cycle is `status:
"zero_duty_cycle"` rather than mapped through `ln D`. `ExposureAggregate` drops the
redundant `k_*` fields — the floor is on `n_factories`/`n_workers` directly — and splits the
dominance rule into `max_factory_share_workers` and `max_factory_share_clips` because D019
says "or"; the design effect must equal the squared width ratio of the record's own two
intervals within `design_effect_mc_band`; `bootstrap_b` is the literal 10,000; timestamps
must be UTC. The rubric's frozen thresholds — 60 s clip floor, 10% unreadable ceiling, 0.5 s
debounce, 6× peak-power floor — are constants in `models.py` and a status that contradicts
them is rejected. `HandSpeedEstimate.mask_source` is null exactly when no detector ran.
Zero speed or zero frequency is refused on the record, as it already was in the mapping.

**Record corrections.** D015 attributed the "37 bare ids across 216 pairs" finding to
vernier D072; it is in vernier **D071**. D018 and `docs/METHOD.md` called $8.56 "measured";
vernier D066 records $8.56 as the *estimate* and **$9.06** as the real cost, so Arm B is
≈$68, not $65. The README, AGENTS and ETHICS said 2,153 workers; the corpus ships **2,144**
(`../vernier/docs/UPSTREAM-FINDINGS.md` F12) and the published figure is 2,153. LINEAGE
still carried the 0.693/0.8 conflation METHOD had corrected, and said the standards were
`[S]` after SURVEY had opened them. `docs/RUBRIC.md` had been rewritten without a version
bump; it is now v1.1.0 with an amendments list. The EVALS card promised ±10% on the
bootstrap golden test where the test uses 12%; the card now says 12%.

**Pre-registration v1.2.0.** Two substantive changes, each with its reversal here: a
switch to spectral-primary under D014 makes the frequency control `FAILED` and H3 `UNTESTED`
for v1, because the destination path has no thresholded control of its own (the review's
finding 22); and the A14 translation floor is pre-committed at 20% of the corpus median RMS
speed rather than living only in the red team. **Reverses if:** a spectral-path frequency
control is pre-registered with its own threshold in a later amendment.

**Tagging.** `docs/SURVEY.md` S2 rows opened only through their PubMed abstract are
re-tagged `[S]`; the two papers read in full stay `[V]`. The Radwin 2026 cross-domain RMSE
of 0.74 is abstract-sourced and is now cited as such. 100DOH is `[V]` from its repository.

**What the review did not find, and is still true.** No commit on the branch carries an AI
attribution trailer; the ordering holds by ancestry and survives both `--no-ff` and squash
merges; no aggregate can be built with an identifier field, a sub-floor stratum, or a bare
`worker_id` cluster unit.

**Reverses if:** nothing; this is a record.

## D021 — The A14 floor is bounded in HAL, not as a fraction of speed

**Decision.** `docs/PRE-REGISTRATION.md` v1.3.0 replaces "at most **20%** of the corpus
median RMS speed" with "at most **0.25 HAL** at the corpus median RMS speed", and widens what
the floor comprises: the residual left by a **rotation-only** synthetic under the corpus's own
fisheye intrinsics counts toward it alongside the translation-only residual. Supersedes the
A14 pre-commitment D020 added.

**Rationale.** The 20% bound was set without checking what it costs on the mapping it feeds.
It costs a lot. On `akkas-2015-speed-dc` at a 68% duty cycle, a floor at exactly 20% of speed
moves HAL by **0.85 at 400 mm/s and 1.08 at 1000 mm/s, peaking at 1.25 near 700 mm/s** — recomputed from
`src/cyclegraph/exposure/hal.py`, not transcribed. `docs/EVALS_CARD.md` names 0.74 HAL, the
best published third-person system's cross-domain RMSE against observers, as "the honest
prior for how far this port could be off". A pre-committed systematic floor larger than the
instrument's own honest prior bounds nothing: the path could pass A14 and still be wrong by
more than the whole port's expected error. 0.25 HAL corresponds to 4.4–5.8% of speed across
the same band, and is stated in the unit the hypothesis is actually about.

The rotation term is added because the rubric subtracts a **scalar** — the median flow over
the mask complement. Under pure camera rotation optical flow is depth-independent, so a
correct model cancels it exactly; a scalar does not, on a wide lens, because rotational flow
varies radially. That variation is exactly the residual A14 alleges, and a floor defined from
translation alone would omit it. `docs/WAVES.md`'s checklist row ("a rotation-only synthetic
with a static hand yields zero residual within tolerance") remains true only in narrow-field
geometry, where it is a test of the estimator's arithmetic rather than of the attack.

**Timing, which is the point.** This lands before `src/cyclegraph/signal/synthetic.py` exists
and before any residual has been computed. Changing a threshold after measuring the quantity
it bounds is post-hoc; changing it while the quantity is unknown is not. A project whose
argument is that measurements get published without protocols does not get to loosen its own
after seeing the number.

**Evidence.** The HAL costs above are recomputed by `hal_akkas_2015`; the 0.74 prior is
`docs/EVALS_CARD.md`, abstract-sourced and `[S]`, and is not load-bearing for the decision —
any prior in that region gives the same conclusion.

**Alternatives rejected.** Keeping 20% and disclosing the cost: the disclosure would say the
bound admits an error larger than the instrument's stated accuracy, which is a reason to
change the bound, not to annotate it. Bounding in percent-of-speed at a tighter value: the
harm of a speed offset depends on where on the logistic the corpus median sits, so a fixed
percentage is not a fixed amount of harm; HAL is.

**Reverses if:** the corpus median RMS speed lands far enough onto a tail of the Akkas
logistic that 0.25 HAL corresponds to a speed fraction the flow estimator cannot resolve, in
which case the bound is restated with the resolution floor named and the amendment quotes
this one.

## D022 — `hands_visible` is label-sourced; `hand_box_width_px` is detector-sourced

**Decision.** On `FrameSignal`, `hands_visible[i]` comes from the label source and
`hand_box_width_px[i]` from the hand detector. They are never crossed. A detector box on a
frame whose labeller reported `hands_visible: 0` is **dropped and counted**; the count is
published in `docs/BENCHMARK.md`, split by cause.

**Rationale.** `models.py`'s `FrameSignal` validator rejects `manipulation: true` with
`hands_visible: 0`, and rejects a box width where no hand is visible. H2c pre-registers
detector coverage as low as **60%**. If `hands_visible` were derived from the detector, up to
40% of pilot frames would carry `hands_visible: 0`, and every one of those the labeller called
manipulating would be an unconstructible record. The validator permits the reverse — a visible
hand with `hand_box_width_px: null` — which is exactly the shape of a labeller that sees hands
and a detector that misses them. The failure only appears at pilot scale, after the detector
run, which is the most expensive place in W3 to discover it.

**The cost, stated rather than discovered.** Dropping boxes on labeller-says-no-hands frames
makes H2c's coverage depend on label quality. If the probe misses hands, the speed path loses
samples it actually had, and H2c can fail for the labeller's error rather than the detector's
— which would trigger D014's switch to spectral-primary on a false signal. That is why the
drop count is a reported quantity and not a run-log detail: a reader must be able to separate
the two before reading H2c as a statement about the detector. `Detection` carries no
`hands_visible` field, so crossing the two is a type error rather than a runtime surprise.

**Reverses if:** a label source is adopted that does not report a hand count, in which case
`hands_visible` has no source and the field's meaning is re-decided rather than back-filled
from the detector.

## D023 — What absence looks like numerically: zero residual, status precedence, decode denominator

**Decision.** Three operational rules that `docs/RUBRIC.md` states in prose and leaves
unquantified.

1. **An exactly-zero residual inside the hand box is a flow null**, with a reason, not a
   speed of zero. It raises `n_flow_null`.
2. **Status precedence** on `HandSpeedEstimate`, when more than one condition holds:
   `no_detector` > `too_short` > `low_coverage` > `flow_failed` > `ok`.
3. **The decode-failure gate is per pair**, with the per-clip rate reported beside it. A clip
   that fails entirely is `status: "decode_failed"`, counted, never dropped.

**Rationale.** (1) closes a hole in the contract: the validator bars `rms_speed_mm_s <= 0`
under `ok` and bars `flow_failed` unless the null rate exceeds its ceiling, so a clip with
boxes everywhere and a dead flow field had **no legal representation** at all. Reading the
zero as the failure it is gives it one, and is what `docs/RUBRIC.md`'s "flow failure → null
with reason, never zero" already required. The test is `== 0.0` exactly, not a threshold:
nulling small residuals would discard real slow motion and bias the corpus upward.

(2) matters because both `low_coverage` and `flow_failed` can be true at once and the schema
accepts either. Without a fixed order, two runs over the same data disagree about why a clip
was dropped, and the reason is a published quantity.

(3) `docs/METHOD.md` E2 states "below 1%" without a denominator, and per-pair and per-clip
rates differ by the number of pairs in a clip. Choosing after seeing the rate is exactly the
flexibility the pre-registration exists to remove.

**What (1) does not catch, stated because the null rate will be read as a failure rate.**
An exact zero arises from identical or degenerate frames. Motion blur and low light — the
causes `docs/RED-TEAM.md` A15 actually names — make dense flow decay toward small *non-zero*
values, which this rule passes through as real speed. The reported `flow_null_rate` is
therefore a **lower bound on flow failure**, and H2c's 10% ceiling is correspondingly
permissive. A15 stays MITIGATED rather than closed.

**Reverses if:** a flow estimator is adopted that reports its own confidence, at which point
the null test is that confidence rather than an exact zero, and the lower-bound caveat is
replaced by the estimator's own false-negative rate.

## D024 — How the flow estimator will be chosen, fixed before the rates are measured

**Decision.** Farneback on CPU against RAFT-small on GPU, on the **same** 1,000 pilot pairs,
drawn deterministically by seed and spanning at least 20 clips so one dark clip cannot decide
it. The rule, in order:

1. Flow-null rate is primary. An estimator whose null rate exceeds `FLOW_NULL_CEILING` on the
   sample **fails**, whatever its throughput.
2. If both clear it, the lower total pilot cost wins — wall-clock times the instance rate, so
   spot pricing and CPU hours sit on one axis.
3. If neither clears it, that is H2c failing on the flow arm. The spectral path becomes
   primary under D014 and **the switch is reported as a failure of the speed path**.
4. **A tiebreaker that is not a rate.** RAFT-small needs torch, which the `signal` extra does
   not declare; choosing it costs either a declared `pyproject.toml` change with its own
   decision entry or a file-backed flow store and a runner script. Farneback costs nothing
   extra because `opencv-python-headless` is already declared. That asymmetry is written down
   now so it cannot be discovered later as a convenient reason.

The measured table lands in `results/flow_benchmark.json` and in the entry that records the
choice, and carries the median residual each estimator leaves on the A14 rotation synthetic
beside its throughput: an estimator that is fast and rarely nulls but leaves a large
rotational residual is worse for this project, because A14 is the open attack.

**Rationale.** `docs/HANDOFF.md` says to decide this "by measurement, not preference". A
measurement whose decision rule is written afterwards is a preference with a table attached.

**Reverses if:** the chosen estimator's null rate on the full pilot exceeds 10%, which is H2c
and is a re-run against this same rule, not a re-argument of it.

## D025 — The corpus ships one camera calibration, not 2,144; the A14 synthetic uses it

**Decision.** The A14 synthetics are built on the corpus's own lens model rather than an
invented one. The model is recorded here as a corpus constant, and the fact that it *is* a
constant is recorded as a limitation.

**What was found.** `builddotai/Egocentric-10K` at revision
`3e5f87c88c54ce8343865d8e2a8c171f18385a05` ships 2,144 `intrinsics.json` files, one per
worker directory — the same count as the shipped workers (`../vernier/docs/UPSTREAM-FINDINGS.md`
F12). Sixteen of them were drawn at an even stride across the sorted list, landing in sixteen
different factories, and **all sixteen are byte-identical**: 302 bytes, one sha256. The
per-worker calibration is a single calibration replicated.

| Field | Value |
|---|---|
| `model` | `fisheye` |
| `image_width` × `image_height` | 1920 × 1080 |
| `fx`, `fy` | 1030.587009, 1032.815725 |
| `cx`, `cy` | 966.691189, 539.687801 |
| `k1` … `k4` | −0.116554, −0.023589, +0.069364, −0.046334 |

Four radial coefficients, no tangential terms, and the field names and `model` string are
OpenCV's fisheye convention, which is Kannala–Brandt on an equidistant base. That is now `[V]`
from the shipped files rather than inferred from the coefficient count.

**Why it matters twice.** First, it settles the privacy question the synthetic would otherwise
raise: a lens model that is identical for every worker is a property of the corpus, not of a
person, so embedding it in a committed test emits no per-worker value. Second, and less
comfortably, **the corpus has no real per-camera calibration**. Whatever lens-to-lens variation
exists across 2,144 physical cameras is unmodelled and unmeasurable from the release, so the
A14 floor computed from this model is a floor for *the nominal lens*, not for the fleet.
`../vernier/docs/COVERAGE.md` describes the release as shipping "per-worker fisheye
intrinsics"; that is what the files are named and not what they contain, and cyclegraph records
the correction rather than inheriting the phrasing.

**Consequence for A14.** The lens is wide enough for the attack to be real: at `fx` ≈ 1030 on a
1920-pixel width, the horizontal half-angle is on the order of a radian, so rotational flow
varies substantially between image centre and edge and a scalar ego-motion subtraction cannot
cancel it. The rotation residual is therefore measured under this model and counted toward the
floor (D021), and the narrow-field rotation case is retained only as a test of the estimator's
arithmetic.

**Reverses if:** a later release ships genuinely per-worker calibrations, at which point the
floor is recomputed per calibration and its spread reported, or a wider sample of the current
release finds a worker whose `intrinsics.json` differs from these sixteen.

## D026 — The A14 floor, measured: it is a motion budget, not a number, and the budget is tight

**Result.** `scripts/measure_a14_floor.py` computes the apparent RMS hand speed a *static*
hand produces under camera motion alone, after `docs/RUBRIC.md`'s ego-motion subtraction, on
exact geometry under the corpus lens (D025). No optical-flow estimator is in the loop, so this
is a property of the rubric's rule and the lens rather than of any estimator. It is
deterministic: no random number is drawn. The table is `results/a14_translation_floor.json`.

The floor is **linear in camera motion**, so it is not a single number. What is publishable
is the floor per unit of motion, and the motion at which it consumes the whole 0.25 HAL bound
the pre-registration now sets (D021):

| Assumed corpus median speed | Floor budget | Rotation budget | Translation budget |
|---|---|---|---|
| 400 mm/s | 23.0 mm/s | 22.8 °/s | 0.026 m/s |
| 612 mm/s | 26.7 mm/s | 26.5 °/s | 0.031 m/s |
| 800 mm/s | 36.8 mm/s | 36.4 °/s | 0.042 m/s |

**This is uncomfortably tight and is reported as such.** A translation budget of 2.6–4.2 cm/s
is less than ordinary head sway at a workstation, and a rotation budget of 23–36 °/s is less
than an ordinary glance between a bin and a fixture. If the corpus's real ego-motion is
anywhere near those magnitudes for a material share of samples, the floor alone consumes the
pre-registered bound and A14 **lands**: the speed path would then be reported with the floor
subtracted and the subtraction disclosed, exactly as the red-team entry says.

**Both terms are real, and a translation-only test would have found only one.** At 30 °/s the
rotation floor is 29.9 mm/s — the same order as the translation floor at 3 cm/s — because the
scalar ego-motion estimate cannot cancel a rotational field that varies by a factor of two
across this lens. Under the long-lens control the same rotation leaves under 1% of raw flow.
D021 widened the floor to include this term before it was measured; the measurement is why
that mattered.

**What is not settled, and cannot be at W3.** The corpus's own ego-motion distribution. This
table gives the floor for an assumed motion, not the floor, and the pre-registered bound is
evaluated at W7 against the measured corpus median speed. The honest W3 claim is that the
floor is characterised and its budget published, not that A14 is retired.

**Reverses if:** measured corpus ego-motion turns out to sit well inside the budget, in which
case the floor is a disclosed limitation rather than a correction; or the ego-motion rule is
replaced by a fitted rotational model, which would cancel the rotation term and is a change to
`docs/RUBRIC.md` requiring its own amendment.

## D027 — E1 gate: the manifest reconciles, and the vendor's worker count is wrong by nine

**Result.** `scripts/build_clip_manifest.py --all` indexed all 19,495 shards at revision
`3e5f87c88c54ce8343865d8e2a8c171f18385a05` by ranged header reads, downloading no shard, and
found **192,903 clips, 2,144 distinct `factory_id/worker_id` pairs, 85 factories and 10,000.13
recorded hours**.

| Source | Factories | Clips | Workers | Verdict |
|---|---|---|---|---|
| Vendor dataset card | 85 | 192,900 | 2,153 | clips +3, **workers −9** |
| `../vernier` F12 scan | 85 | 192,903 | 2,144 | **reconciles exactly** |
| cyclegraph, this scan | 85 | 192,903 | 2,144 | — |

**Why three sources and not one.** A gate against the vendor's card alone would have failed on
a discrepancy the card itself is wrong about. A gate against the sibling alone would have
inherited whatever the sibling got wrong. Two independently written scans, in different
repositories, agreeing to the clip is the actual evidence; the vendor gap is then a finding
rather than a scan defect. `../vernier/docs/UPSTREAM-FINDINGS.md` F12 reported the −9 gap from
its own scan and this confirms it rather than repeating it.

The duration reconciles to 0.001% of the published "10,000 hours", which is what makes the
worker gap legible: a scan that had missed workers would have missed their hours too.

**Consequence.** 2,144 is the cluster count every interval in this project is computed over,
and 2,153 is the number the vendor's card and much of the surrounding literature would use.
`README.md` already carries 2,144 with F12 cited; this entry is the independent confirmation.

**A note on the scan itself.** Eleven shards failed on the first pass with connection resets
and read timeouts, and the run reported itself `NOT AUTHORITATIVE` rather than publishing a
short count. Re-running picked up exactly those eleven and the totals closed. A scan that had
silently dropped them would have reported 192,794 clips and disagreed with both sources for a
reason having nothing to do with the corpus.

**Reverses if:** the corpus is re-pinned, at which point every count is recomputed and every
stored record's `corpus_rev` makes the old ones unpoolable rather than merely stale.

## D028 — The flow benchmark: Farneback measured, and the decision stays OPEN

**Result.** `scripts/bench_flow.py` ran Farneback over 192 real pilot pairs drawn from 12
clips at seed 777, decoded at 480×270: **116.9 pairs/s on CPU, flow-null rate 0.000**, which
clears `FLOW_NULL_CEILING` with the whole margin. `results/flow_benchmark.json` carries the
table. The measured throughput is more than twice `docs/METHOD.md` E3's ~50 pairs/s estimate,
at this frame size.

**The decision is not taken, and that is the rule working rather than failing.** D024 fixed a
comparison between two arms before either was measured, and RAFT-small has not been measured:
torch is importable on this machine but is declared in no extra, no RAFT weights are present,
and the throughput arm is meaningless without the GPU `docs/REPRODUCTION.md` specifies. So
`decision_taken` is `false` in the artifact and `flow_method` on every record produced so far
names Farneback as *what ran*, not as *what was chosen*.

Recording one arm's rates and calling the decision made is precisely the
preference-with-a-table-attached D024 exists to prevent. The temptation is real: Farneback's
null rate is zero, its dependency is already declared, and the tiebreaker in D024(5) favours
it. That is an argument for expecting it to win, not for recording that it did.

**What would close it.** RAFT-small on a `g5.xlarge` over the same 192 seeded pairs, giving
the null rate and the pairs/s that D024(2) and D024(3) compare. Until then the speed path runs
on Farneback and says so.

**One thing the benchmark did settle.** A zero null rate over 192 real pairs is evidence that
the `== 0.0` detector almost never fires on real footage, which is the limitation D023 already
stated in the abstract: real frames are textured enough that even a bad estimate returns
something. The null rate is a lower bound on flow failure, and on this evidence a loose one.

**Reverses if:** RAFT-small is measured and either fails the null-rate bound or wins on cost,
at which point this entry is superseded by the one that records the comparison.

## D029 — W3's fresh-context review: what it covered, and what it did not

**Status: partial, and recorded as partial.** `docs/WAVES.md` requires a fresh-context review
at the end of every wave and says "a re-read in the same context is not a review". A fresh
context was given the branch diff, `CONTRACTS.md`, `docs/ARCHITECTURE.md`'s seams,
`docs/RUBRIC.md` and the checklist, and deliberately not the author's account. It returned two
findings and then stalled before writing a full report; a second, tighter pass stalled the
same way. The remainder was checked by the author, which is **weaker by construction** and is
labelled so rather than presented as an independent result.

**Found independently, and both real.**

1. **`make typecheck` was failing, and had been for several commits.** Three `mypy --strict`
   errors in the test suite: two `type: ignore` comments made unused when
   `opencv-python-headless` brought cv2's own stubs with it, and a `func-returns-value` on a
   `DeadFlow` stub annotated `-> None`. Fixed. **Worth recording is how it stayed hidden:**
   the author verified each commit with `make validate 2>&1 | grep -E "…|Success"`, and
   mypy's failure prints no line matching that filter, so the signal was the *absence* of a
   line rather than the presence of one. A filter that can only show success is not a check.
2. **The A14 generator survives mutation.** The reviewer built its own mutation harness and
   confirmed that a generator which loses the fisheye, or loses the two-plane depth split, is
   caught by the existing tests. That was the question the A14 design most needed answered
   from outside, since a degenerate generator would have made the speed path look clean.

**Checked by the author afterwards, and therefore weaker evidence.**

- *Numbers against artifacts.* Every figure quoted in D026, D027 and D028 was re-read from
  `results/a14_translation_floor.json`, `results/decode_probe.json` and
  `results/flow_benchmark.json`. They match.
- *Fabrication paths.* Six adversarial probes: a region prior in a detections file is refused
  on load; an unwritten instant returns `manipulation: None`, never `False`; a failed flow and
  an exactly-zero residual both return `None` with a reason; a null `mask_source` yields
  `no_detector` with no speed; a label row without `label_source` is refused. All closed.
- *Sampling arithmetic.* Brute-forced against a loop over 8,572 `(duration, fps)` pairs: zero
  mismatches, and the naive `floor(duration·fps)` is confirmed off by one at every exact
  integer boundary.
- *Pilot leakage.* Every `print` in `scripts/` was audited. Counts are printed only inside the
  corpus-level branch; the pilot branch prints gate verdicts. Failed **shard paths** are
  printed as operational diagnostics so a scan can be retried — those name a worker directory,
  and the judgement recorded here is that a path needed to resume a read is not a measurement
  and not a published number. A reviewer who disagrees should say so.

**A finding the author raises against the author's own work.** Two test thresholds --
`CORPUS_NONUNIFORMITY_CV = 0.10` against a measured 0.19, and `CORPUS_ROTATION_FRACTION = 0.05`
against a measured 0.127 -- are stated as "the floor a near-uniform field could not clear"
rather than derived from an independent bound the way their narrow-lens counterparts are. They
discriminate correctly, because a degenerate generator gives approximately zero, but the
specific value is a choice and not a derivation. They should be re-derived from the lens
geometry.

**What is still owed before W3 closes.** A completed fresh-context review covering contract
fidelity and test quality across the whole branch. The two items above are not that.

**Reverses if:** a completed independent review finds anything the author's own pass missed,
which is the outcome this entry exists to leave room for.

## D030 — W3's fresh-context review, completed: five findings, two blocking, all addressed

**Supersedes D029's "partial" status.** A third fresh context, given a narrow scope (contract
fidelity and test quality), a hard budget of 15 tool calls and an instruction to report rather
than keep investigating, returned a complete report in 11 calls. The two earlier attempts had
stalled by investigating without reporting; the fix was scope and a budget, which is worth
recording because the review step is otherwise easy to declare done on an empty result.

**Finding 1, blocking: the speed path's only statistical output had no golden case.**
`rms_speed_mm_s` is the number `HandSpeedEstimate` exists to carry and nothing asserted a value
for it — the only assertion on the field was that it was `None`. The reviewer proved it by
mutation rather than by inspection: deleting the pixel-to-millimetre scaling outright left
`tests/test_hand_speed.py` at **17 passed**, and swapping `np.median` for `np.mean` in
`ego_motion` and in the box-width statistic left **26 passed** across two files. The cause was
a fixture that gave every sample the same speed and the same box width, where RMS, mean, median
and max all coincide.

Fixed with a hand-computable case: speeds `(300, 400, 1200)` px/s and widths `(100, 209, 400)`
px give a median width of 209, an RMS of 750.5553 px/s and therefore
`750.5553 x 85 / 209 = 305.2498` mm/s. Three further tests separate RMS from mean, median from
mean in the ego-motion estimate (on a deliberately skewed background, which is the fisheye case
the rubric's median exists to defend against), and median from first-or-largest in the width.
Re-run under the same mutations: **A now fails 2 tests, B fails 3, C — substituting a mean for
the RMS — fails 2.** The reviewer's own worked example gave 741.62 px/s and 301.6 mm/s; those
figures are wrong and the values above are recomputed here.

**Finding 2, blocking: `build_frame_signal` silently voided detector measurements.** Under
`hand_mask_source="none"` it replaced every `hand_box_width_px` with `None`, in a module whose
own docstring promises it repairs nothing silently. A caller that mis-wired the mask source
while a detection store was loaded would have produced a record that validated, kept
`status: "ok"`, and understated H2c's detector coverage with no trace anywhere. It now raises.

**Finding 3, non-blocking: the manifest dropped rows with no count and no reason.** A sidecar
with no sibling media, or one too large to be a sidecar, was skipped silently; a truncated or
corrupt tar header ended the walk with a bare `return`, making a partial member list
indistinguishable from a complete one. `clip_records_from_shard` now returns `ShardContents`
carrying `orphan_sidecars` and `oversized_sidecars`, and a malformed header raises
`ShardReadError` — which is what the eleven shards that failed the first corpus pass should
have done rather than quietly shortening the manifest (D027).

**Finding 4, non-blocking:** a dead conditional in the `HandSpeedEstimate` constructor whose
branches were identical. Collapsed.

**Finding 5: the reviewer disputed the author's own self-report, and was right.** D029 flagged
`CORPUS_NONUNIFORMITY_CV = 0.10` and `CORPUS_ROTATION_FRACTION = 0.05` as possibly tuned. Measured,
they sit 1.9x and 2.5x clear of their observations (0.1909 and 0.1266) while their long-lens
controls sit 59x and 24x the other way, so neither is an observation rounded — they survive a
2x shift in either direction and still separate the two lenses. What was actually wrong was the
**provenance claimed in the comments**: one derived a sec^2 bound of ~5% and then asserted 1%,
another cited a grid spacing of 0.06 px and asserted 1e-3, and both used O(h) reasoning for an
O(h^2) interpolation error. Four comments are rewritten to state what these constants are —
one-sided separation bounds with their measured margins — rather than asserting derivations
that do not produce them.

**Reverses if:** a later review finds the speed path's golden case still admits a mutation the
three above do not cover, in which case the fixture is extended rather than the finding
re-argued.

## D031 — `FrameSignal` cannot say "this stage did not run", and that is why W3 writes no pilot records

**Found by trying to satisfy the requirement honestly rather than by argument.** W3's exit
condition asks for `FrameSignal` and `HandSpeedEstimate` written for the pilot factory. The
hand detector and the manipulation labeller have not run (`docs/HANDOFF.md`), so the question
is whether a truthful record can be written anyway. The two records differ, and the difference
is a contract defect.

**`HandSpeedEstimate` can.** `status: "no_detector"` with `mask_source: null`,
`rms_speed_mm_s: null` and a reason is exactly the shape for "no detector ran on this clip",
and it constructs. The contract anticipated this case.

**`FrameSignal` cannot.** Its status is `Literal["ok", "too_short", "no_labels",
"decode_failed"]` and none of them is true of a clip whose signal stage was never attempted:

| Status | What writing it would assert | True here |
|---|---|---|
| `no_labels` | labelling ran and more than 10% of frames were unreadable | No — nothing ran |
| `decode_failed` | the decoder was run and failed | No — it was not run |
| `too_short` | the clip is under the 60 s floor | No |
| `ok` | the series is usable | Rejected by the validator |

Three of the four construct without complaint, which is the dangerous part: a pipeline that
wanted to report progress could write `no_labels` across the pilot and every record would
validate, while asserting that a labeller ran and found nothing. That is the same class of
error as reading an unwritten instant as a negative (D022) — an absence dressed as a
measurement — one level up, at the record rather than the field.

**Consequence, and it is the reason the wave ends where it does.** W3 writes no pilot records.
Writing only the half that can be honest would be worse than writing none, because a directory
holding `hand_speed.jsonl` and no `frame_signal.jsonl` reads as a pipeline that partly
succeeded rather than one that has not been run. `scripts/build_signal.py` exits 2 and names
the missing stages instead.

**What would fix the contract.** A fifth status — `not_attempted`, or a nullable `status` with
a required reason — so that "this stage has not run" is a value like every other absence in
this schema. That is a `CONTRACTS.md` change with a version bump and it is deliberately **not**
made here: it should land with the labeller work that makes it exercisable, not be added
speculatively at the end of a wave to make an unmet condition look met.

**Reverses if:** the labeller and detector run, at which point the pilot's records carry real
statuses and this entry describes a gap that no longer blocks anything — though the missing
status remains a real defect for any future stage that has not yet run.

## D032 — `not_attempted` lands after all, and the pilot's records are written

**Supersedes D031's decision not to change the contract.** D031 identified that `FrameSignal`
could not express "this stage has not run" and declined to add the status, on the grounds that
widening a schema at a wave boundary to make an unmet condition look met is the move this
project exists to argue against. That reasoning was about doing it unilaterally to clear a
gate. Asked directly, with the gap and its cost stated, the author of the project decided the
status should land. Recorded here because the reversal is a decision, not a drift.

**What changed.** `CONTRACTS.md` is at `contracts/v1.3`. `FrameSignal.status` gains
`not_attempted`, and `label_source`, `label_rev` and `prompt_variant` become null **exactly**
under that status — a second gap D031 did not name, since an un-run stage has no true value
for any of the three either. The validator enforces the biconditional in both directions, so
seam 2 is preserved rather than relaxed: a record claiming any label still carries full
provenance, and this is the one shape that claims none. Under `not_attempted` every series
entry is null, `n_unreadable` equals `n_frames`, and `hand_mask_source` and `flow_method` are
`"none"`.

**What was written.** `scripts/build_signal.py --record-not-attempted` writes both records for
every clip in the pilot manifest, from the manifest alone. It decodes nothing, runs no model,
and produces no exposure value. `FrameSignal` carries `not_attempted`; `HandSpeedEstimate`
carries `no_detector`, which the contract already had. `n_frames` and `n_samples` are the
instant counts `corpus/sampling.py` plans, which are facts about the clip's duration rather
than measurements of it.

**One judgement inside it.** `too_short` is *not* used for short clips in this mode, even
though the duration alone would justify it. `too_short` is a determination the signal stage
makes when it runs; this stage has not run, and asserting a determination nobody made is the
error D031 was about. Every un-run clip is `not_attempted` regardless of duration.

**What this does not do.** It produces no hand box, no label, no duty cycle, no speed and no
HAL. The detector and the labeller remain W3's blocking dependencies and `make signal` without
the flag still exits 2 rather than substituting anything. The records say the pipeline has been
built and pointed at the pilot, and nothing more than that.

**Reverses if:** the status is ever used to carry a value — a record at `not_attempted` with
anything non-null beyond its identity and counts — at which point the validator's biconditional
has been weakened and the entry that weakens it supersedes this one.

## D033 — The 6x peak-power floor does not discriminate: white noise clears it

**Found by running the estimator on noise before running it on the corpus.** `docs/RUBRIC.md`
makes a `FrequencyEstimate` `resolvable` when its spectral peak exceeds **6x the median power
of the rest of the spectrum**. Measured against synthetic white noise at 4 Hz, with 40 seeded
trials per duration:

| Clip duration | Periodogram bins | Predicted noise ratio, ln(N)/ln 2 | Measured median | Share reported `resolvable` |
|---|---|---|---|---|
| 60 s | 120 | 6.91 | 7.81 | **72%** |
| 180 s | 360 | 8.49 | 8.89 | **100%** |
| 433 s | 866 | 9.76 | 9.89 | **100%** |
| 1200 s | 2400 | 11.23 | 11.96 | **100%** |

The corpus's observed clip durations are 180, 433 and 1200 s
(`../vernier/docs/DECISIONS.md` D071), so **an unstructured series is reported resolvable
essentially always**, and H2b — "at least 70% of pilot clips are `resolvable`" — can be
satisfied by a corpus containing no repetition whatever.

**Why, and why it was predictable.** The periodogram of white noise is exponentially
distributed per bin, so the ratio of the maximum to the median grows like `ln(N)/ln 2` in the
number of bins `N`, and `N` grows with clip length. A fixed multiplicative floor therefore
gets *easier* to clear the longer the clip. The measurement tracks the prediction to within
about 13% at every duration, which is what makes this a property of the statistic rather than
an artefact of one implementation.

**What this is not.** It is not a defect in `src/cyclegraph/cycles/spectral.py`, which
implements the rubric's sentence faithfully, and it is not `docs/RED-TEAM.md` A12. A12
anticipated H2b **failing** by construction on a saturated series; this is the opposite and
worse failure — H2b **passing** by construction, which would look like a result.

It is the same class of error as the design-effect ambiguity that made a sibling project's
equivalent hypothesis unfalsifiable and that `docs/PRE-REGISTRATION.md` H5 was written to
avoid: a threshold stated in units that do not mean what the sentence assumes they mean.

**Timing.** This is measured on synthetic noise, before any corpus clip has been scored
spectrally, which is the only point at which the threshold can be changed without it being
post-hoc — the same position D021 was in for the A14 floor.

**Status: OPEN, and deliberately not fixed here.** `PEAK_POWER_FLOOR` is frozen in
`docs/RUBRIC.md` and referenced by `docs/PRE-REGISTRATION.md` H2b, so changing it is an
amendment to both and is the project author's decision rather than the implementer's. The
estimator keeps the rubric's rule, `tests/test_cycles.py` pins the defect with an assertion
that a later amendment must deliberately change, and no corpus spectral estimate has been
produced.

**Candidate fixes, for whoever takes the decision.** A floor that scales with bin count
(`c · ln(N)`); the Lomb-Scargle false-alarm probability, which is the standard significance
test for exactly this and is bin-count aware by construction; or a fixed frequency grid so `N`
does not vary with clip length, which makes a constant floor meaningful again but discards
resolution on long clips.

**Reverses if:** nothing — this is a measurement. The amendment that acts on it supersedes it.

## D034 — The resolvability floor is derived from the noise null, not chosen

**Acts on D033**, which measured that the rubric's fixed 6× peak-power floor was cleared by
white noise on 72% of 60 s clips and 100% of clips at every duration the corpus actually
contains. `docs/RUBRIC.md` is at v1.2.0 and `docs/PRE-REGISTRATION.md` at v1.4.0.

**The rule.** A `FrequencyEstimate` is `resolvable` when its peak-to-median ratio exceeds the
value white noise of the same length would exceed only **5%** of the time:

    floor(N) = −ln(1 − 0.95^(1/N)) / ln 2

for a periodogram of `N` bins. Periodogram bins of noise are exponentially distributed, so the
median is `ln 2` and the maximum of `N` of them satisfies `P(max < x) = (1 − e^−x)^N`;
inverting at the 95th percentile and dividing by the median gives the floor. Nothing here is
fitted or chosen except the false-alarm rate, which is one interpretable number rather than a
multiplier whose meaning changed with clip length.

| Clip duration | Bins | Old floor | Derived floor | Noise reported `resolvable`, old → new |
|---|---|---|---|---|
| 60 s | 120 | 6.0 | 11.19 | 72% → 13% |
| 180 s | 360 | 6.0 | 12.78 | 100% → 5% |
| 433 s | 866 | 6.0 | 14.04 | 100% → 5% |
| 1200 s | 2400 | 6.0 | 15.51 | — |

**It rejects noise without rejecting signal.** A 0.25 Hz square wave clears its own floor by
more than three orders of magnitude at every corpus clip length, so the correction costs no
real detection.

**Where it is still loose, stated rather than found later.** At 60 s the measured false-alarm
rate is 13% against a nominal 5%: the exponential null is optimistic for the shortest series,
where there are fewer independent bins and the binary signal is furthest from the Gaussian
assumption behind it. The corpus's shortest clip is 62.3 s and **0.67% of its 192,903 clips
are under 180 s**, so this affects a fraction of a percent of the corpus and is disclosed
rather than corrected with a second fudge.

**The floor is recorded on every record.** It varies with clip length, so `FrequencyEstimate`
gains `resolvability_floor` (`contracts/v1.4`) and the validator checks the peak against the
record's own floor rather than a global. This is the rule `ExertionSegment.min_duration_s`
already followed and for the same reason: `resolvable` is a function of the floor and a reader
must be able to see which one was applied. `PEAK_POWER_FLOOR = 6.0` stays in `models.py`,
superseded but not deleted, because it is what any record written under rubric v1.1.0 was
judged against.

**Timing.** Amended after running the estimator on synthetic noise and before running it on a
single corpus clip — the same position D021 took for the A14 bound. The test that pinned
D033's defect now asserts the fix, so the amendment had to change it deliberately rather than
silently passing.

**Reverses if:** the false-alarm rate is shown to be materially wrong for binary series at
these lengths, in which case the null is calibrated by simulation per bin count rather than
taken from the exponential approximation, and the floor is recomputed from that.

## D035 — 100DOH builds on current hardware; the weights are what block the pilot

**The question this answers.** `docs/METHOD.md` E3 names 100DOH as the detector and
`scripts/detectors/doh100.py` called it the project's single largest unverified dependency:
the released model is a Faster R-CNN with custom CUDA ops written against torch 1.x, and no
current GPU AMI ships a torch that old. Whether it builds at all decided whether W3's remaining
cost was hours or weeks, so it was measured rather than argued about.

**Measured, on a real instance.** `g5.xlarge` (A10G 23 GB, driver 580.126.09), Deep Learning
OSS Nvidia Driver AMI GPU PyTorch 2.7 Ubuntu 22.04 (`ami-012ba162b9cd2729c`), torch 2.7.0+cu128,
torchvision 0.22.0, CUDA 12.8. **The ops compile**, producing `model/_C.*.so` linked against
`libtorch_cuda`, after an eight-file patch now committed as
`scripts/detectors/patch_doh100.py`.

The patch is entirely one deprecation: `Tensor.type()` used to return a
`DeprecatedTypeProperties` that could be passed to `AT_DISPATCH_FLOATING_TYPES` and asked
`.is_cuda()`. Torch 2 wants `scalar_type()` for the first and `is_cuda()` on the tensor for the
second. Without it the build stops at `cannot convert 'const at::DeprecatedTypeProperties' to
'c10::ScalarType'`. **No model logic and no numerics change**, which matters: a port that
altered the detector would make `mask_source: "100doh"` a claim about a model nobody published.

The upstream repository had already commented out its `THC/*` includes, so that generation of
breakage was fixed by its maintainers and only the dispatch API remained.

**What now blocks the pilot is distribution, not compute.** `faster_rcnn_1_8_132028.pth` is
published through a Google Drive link that refuses automated download — `gdown` reports the
file cannot be fetched — the lab's own host returns nothing for the obvious paths, and a
Hugging Face search for a mirror returns no models. The build is solved and the weights are
not, which is the opposite of the risk this entry set out to test.

**Cost of finding out.** One on-demand `g5.xlarge` for about 41 minutes, roughly $0.70. Spot
was attempted first and had no capacity in two availability zones; for a probe this short the
on-demand premium was smaller than another round of capacity hunting. The instance carried a
`shutdown -h +90` from first boot so that a forgotten session could not outlive the experiment,
and it was terminated explicitly along with its security group.

**Not measured, and still an estimate.** The detector's frame rate. `docs/METHOD.md` E3's
~20 frames/s is unverified because inference needs the weights; `scripts/run_detector.py --smoke`
exists to measure it in the same session that first loads them.

**Reverses if:** a maintained fork or a mirrored checkpoint appears, at which point the patch
may be unnecessary and this entry's build instructions are superseded rather than merely dated.

## D036 — The torch 2 fix ships as a script, not a diff, and D035's citation was corrected

**Decision.** The change D035 measured is committed as `scripts/detectors/patch_doh100.py`, a
substitution script, rather than as the `git diff` it was originally captured as.

**Why not a diff.** Two reasons, and the second is the one that decided it. A diff carries line
numbers and context, so it rots as soon as upstream moves a line, whereas the change here is two
mechanical string substitutions that are version-independent and idempotent — a half-finished
instance can simply re-run it. And the captured diff carried upstream's own
placeholder comments through as unchanged context lines, which `make check-placeholders`
correctly refused: the gate exists to stop
this project shipping placeholders, and the honest fix is not to add a third exclusion to a list
whose own comment warns that a third exclusion would be the loophole.

**The correction, stated rather than made silently.** D035 cited the artifact by its original
filename in two places and those citations were edited to the new one. `docs/DECISIONS.md`'s
header says entries are never edited, and this is the exception being declared rather than
taken: what changed is a filename in a record of a measurement, not the measurement, the
reasoning, or the conclusion. The cited-path gate would otherwise fail on a file that no longer
exists, which is the gate working. No other word of D035 is touched.

**Reverses if:** upstream adopts the fix, at which point the script prints "nothing to patch"
and both it and D035's build instructions become historical.

## D037 — 100DOH's published weights are gone; EgoHOS's are not

**Checked, not assumed.** `docs/METHOD.md` E3 names 100DOH as the detector and
`docs/SURVEY.md` tags it `[V]` from its repository. The code is still there and, per D035,
still builds. **The weights are not.**

| Artifact | Source the paper publishes | Result |
|---|---|---|
| `faster_rcnn_1_8_132028.pth` (handobj_100K+ego) | Google Drive `1H2tWsZkS7tDF8q1-jdjx6V9XrK25EDbE` | **HTTP 404** |
| `faster_rcnn_1_8_89999.pth` (handobj_100K) | Google Drive `166IM6CXA32f9L6V7-EMd9m8gin6TFpim` | **HTTP 404** |
| EgoHOS checkpoints | Google Drive `1DEJBeQ3cR1q7cjjzwDUIQVSoptT-y9U7`, via `download_checkpoints.sh` | **HTTP 200** |

Both 100DOH ids fail, so this is not one broken link. The upstream README still advertises
them unchanged and carries no deprecation notice, so the loss is silent rather than announced.
No mirror was found: Hugging Face has no copy of either checkpoint — its one near hit,
`ThompsonC21/100DOH-TinyExplorer-Tuned-hand-detection`, is a fine-tune on infant head-camera
data and is a **different model**, so using it and writing `mask_source: "100doh"` would be a
claim about weights nobody published. Two downstream repositories that use 100DOH
(`idejie/ego_hand_detecor`, `nripstein/Thesis-100-DOH`) both redirect to the same dead links.

**The `[V]` tag stays true and is now narrower.** `docs/SURVEY.md` verified the *repository*
and its training description; both still hold. What has changed is that a reader cannot obtain
the model those claims are about.

**This breaks a promise `docs/REPRODUCTION.md` makes**, independently of which detector the
project ends up using: "if this document does not let a stranger obtain commensurable numbers,
the project has failed on its own terms." A pipeline whose primary detector cannot be
downloaded does not let a stranger do anything. That is now true of 100DOH whatever else is
decided, and it is a coverage gap rather than a task.

**The fallback exists but its trigger has not fired.** `docs/METHOD.md` names EgoHOS as the
fallback "if 100DOH's coverage fails H2c", and `CONTRACTS.md` already admits
`mask_source: "egohos"`. Coverage has not failed H2c; nothing has been measured at all. So
switching is a different decision from the one METHOD anticipated and needs its own reason on
the record rather than borrowing that one.

**And it is not a drop-in.** EgoHOS is *segmentation*, and `docs/RUBRIC.md` scales pixel speed
to mm/s by "the clip's median detected **box** width". A width derived from a mask is not the
same quantity as a detector's box width — masks trace the hand's outline where a box bounds
it, so the two differ by a factor that depends on hand pose. Adopting EgoHOS therefore
requires deciding what `hand_box_width_px` means for a mask and saying so in the rubric, not
just changing an enum value.

**Correction, 2026-09-06.** The table above calls
`1DEJBeQ3cR1q7cjjzwDUIQVSoptT-y9U7` a folder. It is a **file** id -- EgoHOS's
`download_checkpoints.sh` passes it to `gdown` as `drive.google.com/file/d/<id>`, and it is a
single `work_dirs.zip`. Probed as a folder it returns 404, which is a property of the URL form
and not of the artifact; a later reader re-checking availability that way would wrongly
conclude EgoHOS had gone the same way as 100DOH. Re-probed 2026-09-06 in the file form, with
the 100DOH ids as a control on the identical probe: EgoHOS returns Drive's large-file
confirmation page, both 100DOH ids return **404**. The entry's finding is unchanged; only the
link's description was wrong.

**Reverses if:** the authors restore the files, a mirror surfaces, or the weights arrive by
another route, at which point 100DOH is used as `docs/METHOD.md` specifies and this entry
records an outage rather than a redirection.

## D038 — The labeller is two linear heads over one frozen backbone, and one of them is inherited

**Decision.** `docs/METHOD.md` E3's cheap probe is implemented as a `facebook/dinov2-small`
backbone, frozen, with two linear heads over the same features: a **manipulation** head fitted
here, and `../vernier`'s trained **hand-count** head reused unchanged. The training labels are
vernier's 29,400 stored `gemini-2.5-flash` P0b judge responses. No judge call is re-paid and no
backbone is fine-tuned.

**Why two heads and not one.** `CONTRACTS.md` makes `manipulation` and `hands_visible` null
together or not at all, and rejects `manipulation: true` with `hands_visible: 0`. A
manipulation-only probe therefore cannot write a legal record without inventing a hand count,
and inventing one to satisfy a schema is the failure this project keeps naming. Vernier's head
already predicts exactly that field, for exactly that corpus, with its fidelity published as a
negative result — reusing it costs one matrix multiply per frame and re-fitting it would be
rebuilding something already measured and already disclosed.

**Vernier's *trained* probe is not reused for manipulation, and that was checked rather than
assumed.** It predicts `hands_visible` — a three-class head, 384 inputs — because that was
vernier's own hypothesis. Its weights carry no information about the manipulation column. What
is inherited is the labels, the features, and the shape of the method.

**Measured fidelity of the manipulation head**, five-fold stratified cross-validation over the
750 frames that have both features and labels (`results/probe_fidelity.json`):

| | |
|---|---|
| Accuracy | **0.8547** |
| Majority-class baseline | 0.7747 |
| Balanced accuracy | 0.7845 |
| Aggregate prevalence, judge vs probe | 0.7747 vs 0.7840 |

Accuracy is never reported here without the baseline beside it: on a corpus where three frames
in four are manipulating, a head that always answered "yes" would score 0.775 and look
respectable. It beats that, and by less than it first appears.

**What the last row is not.** It is **not** H1a. H1a's statistic is the *per-clip* mean
absolute difference in duty cycle between two label sources, and errors cancel across a pooled
sample in a way they do not within a clip, so a 0.009 aggregate gap says almost nothing about a
per-clip one. It cannot be computed from these frames at all: they are evaluation-release
frames, whose `frame_id` carries no clip linkage (D011). **H1a is answerable only by running
two labellers over raw-release pilot clips**, which is what W4 is.

**Where the two heads contradict each other, the frame is unreadable.** `manipulation: true`
with `hands_visible: 0` is a real disagreement between two heads, not a schema inconvenience.
Those frames are written `null` with a reason and counted, never repaired toward whichever
answer would keep them — the rule D022 sets for a detector and a labeller disagreeing, applied
to two heads of one labeller. The rate is a reported gate.

**The domain step, stated.** The heads are fitted on evaluation-release frames and applied to
raw-release clips. Same corpus, same cameras, same vendor pipeline, but not the same frames,
and nothing here measures the gap. It is a disclosed assumption rather than a validated one.

**Reverses if:** H1a fails on the pilot, which selects Arm B and the judge-only draw (D018) —
this probe is then reported as the biased labeller H1 was written to catch, not patched.

## D039 — H2 is reported FAILED: the spectral path finds drift, not bouts

**Result, on the pilot, with the probe as the label source.** H2a **FAILED** and H2b passed.
The verdicts are the publishable part; the values stay in `results/pilot/` (D018).

**What failed.** Spectral bout frequency and transition-counting disagree by far more than
H2a's 20% relative bound, on almost every clip where both resolve, and in one direction:
spectral is roughly a sixtieth of transition-counting. The spectral estimate is not a noisy
version of the same quantity — it is a different quantity.

**Why, diagnosed rather than guessed.** The great majority of resolved spectral peaks sit
**below 0.05 Hz** — slower than the slowest cycle `docs/RUBRIC.md`'s own reasoning
contemplates, since its 60 s clip floor is justified as "three cycles at 0.05 Hz, a 20 s
period". Those peaks clear the resolvability floor comfortably. They are tall and they are in
the wrong band: on a manipulation series that is mostly `true`, the dominant spectral content
is the slow drift of gap density across the clip, not the rate of bouts.

**This is `docs/RED-TEAM.md` A12's mechanism with a different symptom, and the difference
matters.** A12 predicted that a saturated series would have *no* spectral peak and that H2b
would fail by construction. What happened is worse: the saturated series has a perfectly good
peak, H2b **passes**, and the number is meaningless. A12 anticipated a gate that would fail
loudly; the real failure mode was a gate that succeeds quietly. **Resolvability tests whether
a peak is tall, never whether it is where a bout could be.**

**H2a is what caught it.** `docs/DECISIONS.md` D005 introduced transition-counting as the
cross-check and D014 demoted the spectral path beneath it; H2a exists precisely to compare two
estimators of one quantity. It did its job on the first real data it saw. A project that had
run only the spectral path would have published a bout frequency two orders of magnitude too
low, with a resolvability flag saying it was fine.

**Not amended, deliberately.** The obvious fix — restrict the search grid to frequencies at or
above the rubric's own 0.05 Hz, or three cycles per clip — follows the rubric's stated logic
and would very likely rescue H2a. **It is not being applied, because the result has now been
seen.** D021 and D034 changed thresholds while the quantities they bound were still unmeasured;
this one is measured, and changing the method now to make a failed hypothesis pass is the exact
move the pre-registration exists to prevent. H2 stands FAILED and the fix, if it is made, is a
new pre-registration for a later version, applied to data this one did not decide.

**What this does not touch.** The speed path. D014 makes hand speed primary and this concerns
the cross-check; H2c is unmeasured because the detector's weights are gone (D037). The duty
cycle these labels produce is unaffected — it does not depend on frequency at all.

**Reverses if:** the search band is re-specified in a later pre-registration and the comparison
re-run on data not used to choose it.

## D040 — The pilot labels were scored on the wrong feature distribution, and are withdrawn

**Found by the fresh-context review of W4, not by the author.** The manipulation head was
fitted on `../vernier`'s cached DINOv2 features and applied to features this project extracted
differently, in two independent ways. `scripts/labellers/probe.py`'s own docstring claimed the
pipeline was "vernier's, reproduced rather than re-derived". It was not.

**Defect 1 — pooling.** Vernier pools **every** token (`last_hidden_state.mean(dim=1)`,
`../vernier/scripts/distill_rung1.py`). This project pooled patch tokens only, discarding CLS.
The origin is instructive: vernier's *docstring* says "mean-pooled patch tokens" and its *code*
does not, and this project reproduced the docstring. **Measured impact: none.** Across 60
frames not one prediction changed, and the duty cycle moved by 0.000 — CLS is one token of 257,
so the perturbation is far smaller than the head's margin.

**Defect 2 — colour.** Vernier's frames are colour JPEGs; `ffmpeg_extract_argv` sets no pixel
format. This project decoded `-pix_fmt gray` and replicated the single channel three times, a
choice `src/cyclegraph/corpus/decode.py` justified on the grounds that "every consumer of these
frames is luminance only" — true when written, false once the labeller became a consumer.
**Measured impact, and it decides the matter:**

| | |
|---|---|
| Predictions changed | **6 of 120 (5.0%)** |
| Duty-cycle shift | **0.033** |
| Feature cosine, colour vs grey | 0.951 |

**0.033 against H1a's bound of 0.05.** A preprocessing choice nobody had measured was consuming
two-thirds of the tolerance of the hypothesis it feeds, in a fixed direction. H1a is the test
that selects Arm A or Arm B for the whole main draw.

**The fix is verified, not assumed.** With both defects corrected, features extracted here
reproduce vernier's stored vectors at **cosine 1.000000, max absolute difference 1e-5**, on
three frames drawn from three different source datasets. That is the strongest available check
and it also proves the previous pipeline could not have matched.

**Consequence.** The 462,437 labels in `results/pilot/labels.jsonl` and every derived artifact
— `duty_cycle.jsonl`, `frequency.jsonl` — are **withdrawn** and re-scored. `docs/DECISIONS.md`
D039's H2 verdict rests on those labels and is **provisional** until it is recomputed; the
factor-60 disagreement is far larger than a 0.033 duty-cycle shift could explain, so the
verdict is unlikely to move, but "unlikely to move" is not "re-checked".

**What this says about the process.** Three defences failed silently and one worked. The
contract, the tests and the gates all passed: nothing they check was violated, because a
feature distribution is not a schema. `zip(strict=True)` caught a timestamp misalignment
earlier in the same file, and nothing analogous exists for "these features are not the ones the
model was fitted to". The fresh-context review caught it. That is the argument for the review
step, made concrete.

**Reverses if:** nothing. This is a defect record.

## D041 — The pre-registration gate did not check what it claimed; three exploits, now closed

**Found by the fresh-context review of the amendments.** `scripts/validate.py`'s docstring and
`docs/PRE-REGISTRATION.md`'s own banner both claimed that no sentence of the frozen body could
change without an amendment block quoting it. The reviewer defeated that claim three ways, each
run against the real gate with the hash recomputed, each returning exit 0.

| Exploit | Why it worked |
|---|---|
| Rewrite "Bootstrap B = 10,000." to `B = 200` | 21 characters; the gate skipped sentences under 25 |
| Delete "Nothing else." | 13 characters — and it is the closure that stops any reporting unit below the D019 floor |
| Insert a new sentence into the frozen Clustering paragraph | **additions were never checked at all** |

The third is the serious one. The gate tested only that prior sentences *survived*, so an
insertion passed by construction: nothing was removed, so nothing was missed. The frozen body
is a closed set, and adding to it changes what was pre-registered exactly as much as deleting
from it. A hypothesis could have been added, or a bound loosened by appending an exception, and
every gate would have gone green.

**Three fixes.** The sentence floor is 10 rather than 25, chosen because real pre-registered
sentences are short — the two exploited above are 21 and 13 characters. The version banner is
skipped by *line* rather than by paragraph: the `**Amended:**` paragraph runs on into
substantive prose about the amendment discipline, and skipping the whole paragraph left that
prose unchecked. And the chain check now runs in both directions.

**Turning it on immediately found a real historical violation.** v1.2.0 changed the banner
sentence "The amendment block at the end quotes every prior sentence it replaced" into the
plural and added a clause, without quoting it — in exactly the region the paragraph-skip had
hidden. The quote is added to the v1.2.0 block now, marked with the date and this entry.
D020 did the same thing at v1.1.0 when it strengthened the gate; that this keeps happening is
the argument for strengthening it rather than against.

**The additions rule starts at v1.5.0, and the history behind it is pinned, not excused.**
Versions 1.1.0 through 1.4.0 were written under the weaker rule and their blocks paraphrase new
text in `Now:` rather than quoting it, so they cannot satisfy the check — there are **45** such
additions, 38 of them in v1.1.0. Rewriting those blocks to carry all 45 verbatim would roughly
double the amendments section and would misrepresent what they said at the time. So they are
exempt, and the exemption is **bounded by a pinned count**: if the number of unquoted additions
in that history changes in either direction, the gate fails. The history is frozen rather than
merely forgiven, and every amendment from v1.5.0 on must carry its own additions.

**What this says about the gates generally.** This is the second defect this week found in a
check that was passing (`make typecheck` was the first, D030). Both were invisible for the same
reason: a green gate is evidence only about what it tests, and neither the author nor the gate
can tell you what it does not test. That is the whole argument for an independent context, and
it is the second time it has paid for itself.

**Reverses if:** nothing. This is a defect record.

## D042 — The transition count's denominator was wall-clock; its numerator is fragmented by nulls

2026-09-06.

The H2 review's first finding: unreadable frames do not only sit *between* exertions, they sit
*inside* them, and `docs/RUBRIC.md`'s boundary rule ends a run at every one. A bout interrupted
by a null is counted twice. On the withdrawn pilot labels the reviewer put the inflation at
**2.4–3.7x**, which makes D039's "roughly a sixtieth" closer to a twenty-fifth.

Reading the module against that finding turned up a second thing the reviewer did not name: the
**denominator**. `exertion_segments` finds exertions only where frames were scored, and
`transition_frequency` divided that count by `clip.duration_s` -- the whole clip, unreadable
stretches included. A restricted numerator over an unrestricted denominator imputes *no
exertion* to every span nobody scored. `docs/RUBRIC.md` already fixes duty cycle's denominator
as scored frames and is silent on this one, so the two halves of the same pipeline were using
two conventions on the same series.

**The denominator is changed to scored time. The fragmentation is not repaired.** They are
different kinds of problem and get different answers:

- The denominator is an implementation choice the pre-registration never constrained, and one
  convention is already blessed for the neighbouring quantity. Changing it is consistency, and
  it moves H2a's disagreement **in the unflattering direction** -- scored time is shorter than
  the clip, so transition-counting gets *faster* and the gap to the spectral estimate *widens*.
  A change that makes a failed hypothesis fail harder is not one this project needs to be
  suspicious of, but the direction is stated so nobody has to take that on trust.
- The fragmentation cannot be repaired without joining two bouts across an interval nobody
  scored, which is the gap-filling `docs/RUBRIC.md` forbids and which would move the count in
  the flattering direction. So it is **counted instead**: `null_bounded_segments` reports how
  many segments have an unreadable frame against a boundary, and that number is published
  beside the segment count in `docs/BENCHMARK.md`. A reader can then see how much of the count
  is the work and how much is where the labels ran out. It is never subtracted.

**What this does to D039.** D039's H2 verdict was already provisional under D040, because the
labels it rests on are withdrawn. This entry adds a second reason to re-derive rather than
re-quote it: the *magnitude* it reports is confounded by fragmentation the entry did not
measure, and the recomputation must carry the null-bounded count beside it. The FAILED verdict
itself is not disturbed here -- both effects identified so far move the disagreement the same
way or leave it far outside H2a's 20% bound -- but "not disturbed" is a prediction until the
re-scored labels are in, and it is recorded as one.

Neither change is a pre-registration amendment. H2a bounds the relative difference between two
estimators; it does not define either estimator's denominator, and `docs/RUBRIC.md`'s boundary
rule is untouched.

**Reverses if:** a later pre-registration re-specifies the transition estimator's support, in
which case the denominator follows that specification instead of duty cycle's.

## D043 — The colour re-run held whole clips in memory, and its resume trusted a row's existence

2026-09-06.

D040's fix moved the labeller from grey to colour frames. Nothing else changed, and the run
fell over: two of four workers were OOM-killed, the survivors dropped to 4.8 frames/s against
the ~44 the grey path managed on one stream, and the GPU sat at **0%** while `kswapd` burned a
core. The cause is arithmetic that the change made load-bearing without anyone noticing it was
there: `run_labeller.py` materialised a clip's frames with `list(...)`, and a 1200 s clip at
4 Hz and 960x540 is 4,799 frames -- 2.5 GB in grey, **7.5 GB in colour**. Four workers of that
do not fit in 30 GB, so the box went to swap and stopped being a GPU machine at all.

Three things follow, and the third is the one that matters.

1. **Frames are streamed in batches**, never accumulated. The decoder was already a generator;
   only the consumer was wrong. The decode is capped at the sample plan's length with ffmpeg's
   own `-frames:v` rather than by breaking out of the generator, because closing the pipe early
   makes ffmpeg exit non-zero and the reader raises on it.
2. **ffmpeg's decoder thread pool is capped.** Uncapped it sizes itself to the host and two
   concurrent colour decodes took 6.6 of 8 vCPUs between them, starving the Python side that
   consumes their output. Capping changes no pixel; H.264 slice threading is deterministic.
3. **Resume no longer treats a clip as finished because rows exist for it.** It compares the
   row count against the clip's sample plan, and rewrites the file without any clip that falls
   short before appending. The old set-of-seen-`clip_id`s would have resumed *past* the clip a
   worker was killed in the middle of, leaving a hole that nothing downstream could see -- a
   clip with a plausible duty cycle computed over the fraction of it that happened to be
   written before the kill. Two workers were killed mid-clip, so this is not hypothetical.

The third is the reason this is a decision and not a commit message. The first two are a
performance bug; the third is a **silent data defect that the performance bug exposed**, of
exactly the shape `docs/ARCHITECTURE.md` calls a seam that does not fail loudly. A resume that
cannot distinguish "finished" from "interrupted" produces short clips indistinguishable from
real ones, and the pilot's own gates -- which check that labels exist for every clip -- would
have passed on them.

**Reverses if:** nothing. This is a defect record.

## D044 — Above ~100 mm/s the flow estimator reports the background's motion inside the hand box

2026-09-06.

Fixing a defect in `scripts/bench_flow.py` turned this up. Its `_rotation_residual_px` took an
estimator and **never called it**: it computed the A14 residual from `analytic_flow` alone, so
both arms of D024's comparison would have reported the identical geometry number and the column
meant to separate them could not. The module offered no way to do better -- `signal/synthetic.py`
produced an exact flow field and no frames -- so `render_pair` was added, and with it the
ability to ask what an estimator actually recovers.

**The measurement.** `scripts/measure_flow_gain.py` sweeps hand displacement and reports
*gain*: median recovered flow magnitude inside the hand box over the median true magnitude
there. Published in `results/flow_displacement_gain.json`, seeded and closed-form; no corpus
access. At the pipeline's 480x270 flow resolution:

| Hand speed | Displacement over the pair | Gain |
|---|---|---|
| 20 mm/s | 2.8 px | 0.94 |
| 80 mm/s | 11.4 px | 0.77 |
| 120 mm/s | 17.1 px | 0.22 |
| 320 mm/s | 45.0 px | 0.19 |
| 570 mm/s | 81.5 px | 0.18 |

**The plateau is not noise, and it identifies the mechanism.** It sits at 0.18, which is
`hand_distance_m / background_distance_m` = 0.45 / 2.5 = 0.18. Once the hand's displacement
exceeds what the estimator's pyramid can search, Farneback stops tracking the hand and smooths
the surrounding field across the depth discontinuity -- so inside the hand box it reports **the
background's** motion. `docs/RUBRIC.md` then subtracts the median flow over the mask complement,
which is that same background motion, and the residual the hand speed is read from collapses
toward zero. The estimator and the rubric fail in the same direction, and the second failure
hides the first.

**Why this is worse than a wrong number.** `docs/RED-TEAM.md` A15 and `docs/DECISIONS.md` D023
make a flow failure a null with a reason and never a zero. This is not a failure by that
definition: the field is finite, non-zero, spatially smooth and entirely plausible. `n_flow_null`
does not move, H2c's 10% ceiling is untouched, and no contract validator can see it. It is the
same shape as D039 (a tall peak in the wrong band clears resolvability) and D040 (a probe scored
on features it was not fitted on) -- **a gate that passes quietly**. Three now, from three
different directions.

**Scale.** The speed path is primary under D014, and hand speeds the HAL equations are fitted
over run **255.3-1288.0 mm/s** (Akkas 2015 Table 1, as `exposure/hal.py` records it).
Every speed above about 120 mm/s sits on the plateau. Doubling the decode to 960x540
moves the knee by nothing in mm/s -- the knee is a fixed *pixel* displacement and finer pixels
buy proportionally more of them, so the two curves agree.

**What is not concluded here.** Not that the estimator is wrong for this job, and not that the
pre-registration must change. The pair interval is the independent variable and it is
pre-registered: `docs/RUBRIC.md` and `docs/PRE-REGISTRATION.md` both say the sample is taken
"from the frame pair (t, t + 1/fps)", and `src/cyclegraph/corpus/sampling.py` reads `fps` there
as the 4 Hz analysis rate, giving a **0.25 s** baseline. The corpus also ships a per-clip `fps`,
under which the same sentence would mean consecutive video frames and a ~0.033 s baseline --
about 11 px at 570 mm/s, comfortably inside the tracked region. Which reading was meant is a
question about the pre-registration's own words, and RAFT-small, whose whole design claim is
large-displacement matching, is the other half of D024 and is still unmeasured. **Both are open
and are not being settled by the author's preference after seeing this curve.** The options and
their costs go to the record and to the project's owner, not into a quiet edit.

**Resolved, same day, on the GPU already running: RAFT-small does not rescue it.**
`results/flow_gain_raft.json`, measured with `--estimator raft` on an A10G, the identical
synthetics and seed. RAFT is the better estimator over the middle of the range -- at 960x540 it
holds gain 0.97 out to 34 px where Farneback has already broken -- and it is *worse* at the
smallest displacements, where a 2.8 px field returns gain 0.30. But above the knee the two are
indistinguishable:

| Estimator | Gain at 320 mm/s | Gain at 570 mm/s | Plateau (mean of last three) |
|---|---|---|---|
| farneback-cv2 | 0.19 | 0.18 | 0.176 (480x270) |
| raft-small | 0.17 | 0.18 | 0.180 (960x540) |

Both land on `hand_distance / background_distance`. **So the collapse is not a property of
Farneback and no estimator choice fixes it** -- an estimator that cannot separate the hand
plane from the background at that displacement reports the background, and the rubric then
subtracts the background. D024's A14 column now separates the two arms, but it separates them
over a range the pilot's hand speeds do not sit in.

**What does move it is the baseline.** At 570 mm/s over a ~0.033 s pair -- the reading of
"(t, t + 1/fps)" in which `fps` is the clip's own frame rate, which the corpus ships per clip --
the displacement is about 21 px at 960x540, where Farneback measures 0.99 and RAFT 0.99. The
question D044 declined to settle is therefore the only one left, and it is a question about
what the pre-registration's sentence means, not about tooling.

**Reverses if:** the pair interval is re-specified, in which case the curve is re-measured at
the new baseline; or a hand-only mask (rather than a box) is used for the residual, which would
change what "smoothing across the discontinuity" costs and is not tested here.

## D045 — The speed path's frame pair is the clip's own frame rate, not the analysis rate

2026-09-06. Pre-registration **v1.4.0 → v1.5.0**.

`docs/PRE-REGISTRATION.md` and `docs/RUBRIC.md` both say the speed sample is taken "from a
frame pair (t, t + 1/fps)". `fps` was never defined in that sentence, and
`src/cyclegraph/corpus/sampling.py` read it as the 4 Hz analysis rate, making the two frames a
speed sample is computed from **0.25 s apart**. The release ships a per-clip `fps` under which
the same sentence means consecutive video frames, about 0.033 s apart. Both readings are
available in the words; only one of them works.

**Prior:** "The hand-speed path samples instantaneous speed from a frame pair (t, t + 1/fps) at
each of the same 4 Hz instants".
**Now:** the same, with `fps` named as the clip's own frame rate and explicitly not the
analysis rate.

**Why, measured rather than argued.** D044 swept hand displacement against what a dense
estimator recovers, on rendered synthetics under the corpus lens. At a 0.25 s baseline, hand
speeds across the fitted range 255.3-1288.0 mm/s move the hand 29-167 px, past what either
estimator can match above the low end; both
Farneback and RAFT-small then smooth across the depth discontinuity and report **the
background's** motion inside the hand box, at a gain of 0.18 — which is exactly
`hand_distance / background_distance`. The rubric then subtracts the background's motion, so
the residual the speed is read from collapses. At the clip's own frame rate the same 570 mm/s
is about 21 px, where Farneback measures 0.99 and RAFT 0.99. The defect is the baseline, and
no estimator choice reaches it: `results/flow_gain_raft.json` is the arm that establishes that.

**Why this is not post-hoc, stated plainly because the distinction is the whole point.** No
pilot speed number exists and none can: 100DOH's weights are unobtainable (D037), so no
`HandSpeedEstimate` has ever carried a measurement — every one written so far is
`status: "no_detector"`. H2c is unmeasured, the corpus median speed is unmeasured, and A14's
floor has never been compared against anything. The quantity this sentence governs is
**unobserved**, which is the same position D021 and D034 amended from and the opposite of
D039's, where the result was in hand and the method was therefore left alone. The evidence
that forced this is a synthetic sweep of a known geometry, not a pilot statistic.

**What it costs.** Decode currently resamples to 4 Hz with ffmpeg's `fps` filter, which cannot
produce two adjacent native frames; the speed path needs a seek to `t` and two consecutive
frames at the clip's own rate. That roughly doubles frames *decoded* while leaving frames
*written* unchanged, and `docs/METHOD.md` E2's decode figures must be re-measured at the new
shape rather than carried over. The manipulation series is untouched: it is sampled at 4 Hz and
this sentence governs only the speed path's second frame.

**Reverses if:** a later reading establishes that the corpus's per-clip `fps` is unreliable for
the pairs actually decoded, in which case the baseline is set explicitly in seconds rather than
by reference to a shipped field.

## D046 — D039's H2 verdict is confirmed on the rescored labels, and D040's withdrawal is discharged

2026-09-06.

D040 withdrew the pilot labels and every artifact derived from them, and marked D039's H2
verdict **provisional** until it was recomputed: *"'unlikely to move' is not 're-checked'."*
It has now been re-checked.

**What was re-run.** All 97 pilot clips were re-labelled from scratch with the corrected
feature pipeline — colour frames, all tokens pooled — on the same probe and the same inherited
hand-count head. `scripts/verify_labels.py` reports every clip carrying exactly the rows its
sample plan calls for, from one corpus revision. Duty cycle and the frequency axis were then
recomputed from those labels alone; nothing was carried over.

**The verdicts do not move.** H2a FAILED and H2b passed, as in D039, and the mechanism is the
same one: the great majority of resolved spectral peaks still sit below 0.05 Hz, slower than
the slowest cycle `docs/RUBRIC.md`'s own 60 s floor contemplates. D040 predicted this — a
0.033 duty-cycle shift cannot explain a two-order-of-magnitude disagreement — and recorded the
prediction rather than acting on it. The prediction held, which is worth exactly as much as it
is worth: it is now a measurement instead of an expectation.

**Three things changed underneath the verdict and none of them rescued it.** The transition
estimator's denominator became scored time (D042), which widens the disagreement rather than
narrowing it. The bout count's null-boundary confound is now measured and published beside it
(D042) rather than sitting unquantified inside H2a. And three clips that the first run wrote
short — 12%, 32% and 66% of their frames missing, from HTTPS reads that ended mid-stream while
ffmpeg still exited 0 — were caught by the new completeness check, dropped and re-decoded
(D043). The first run's aggregate shortfall was 1.1385% of planned samples, above
`docs/METHOD.md` E2's 1% ceiling; the completed run is at zero and the labeller now gates on it.

**What is still not measured.** The speed path. `make hal`'s speed gate FAILs because no
`HandSpeedEstimate` carries a measurement — 100DOH's weights are unobtainable (D037) and every
such record is `status: "no_detector"`. H2c is unmeasured, and D045 changed the pair the speed
path is computed from, so the speed axis is not merely unmeasured but unmeasured *at a
definition nothing has ever been run against*.

**Reverses if:** the labels are withdrawn again, on the same standard D040 set.

## D047 — EgoHOS replaces 100DOH, and a mask's hand box is its axis-aligned bounding box

2026-09-06. Rubric **v1.3.0 → v1.4.0**. No pre-registration amendment: it says "detector hand
boxes" and "the clip's median box width" and defines neither's source, so a box derived from a
mask satisfies it as written.

**Why now, and not under the trigger `docs/METHOD.md` anticipated.** METHOD names EgoHOS as
the fallback "if 100DOH's coverage fails H2c". That trigger has not fired and cannot: coverage
has never been measured, because 100DOH's weights are unobtainable (D037, re-probed 2026-09-06
against a live EgoHOS control). Switching is therefore a different decision from the one METHOD
anticipated, taken for a different reason — the primary detector cannot be downloaded, by
anyone, which breaks `docs/REPRODUCTION.md`'s promise independently of what this project does
next.

**The definition.** `hand_box_width_px` from a segmentation mask is the width of the
**axis-aligned bounding box of the mask's hand pixels**, per hand, and `docs/RUBRIC.md`'s
"largest detected hand box" then selects among those by area, unchanged. EgoHOS segments left
hand, right hand and interacting objects; only the two hand classes are read, and an object
touching a hand is not part of it.

**Why the axis-aligned box, argued rather than assumed.** Three candidates: the mask's
bounding box, the short side of its minimum-area rectangle, and the square root of its area.
The last two are better proxies for *hand breadth* in isolation, which is what the 85 mm
constant is. They are rejected anyway, because the rubric's rule is not "estimate hand breadth"
— it is "take the median detected box width and let it stand in for hand breadth". A bounding
box keeps the same functional form as the detector box it replaces, so the substitution changes
where the box comes from and not what quantity is being taken. Swapping in a different
estimator of a different quantity would change two things at once and make the change
unauditable.

**What it costs, stated because it is not zero and cannot be measured.** A human-annotated
detector box and a mask's tight bounding box do not agree: annotation conventions include
margin that a mask does not. The offset is systematic, and it enters mm/s **linearly** through
`hand_breadth_mm / median_box_width_px`. It cannot be bounded by running both on the same
frames, because 100DOH cannot be run at all.

**But it is not unquantified.** A box-convention offset of *x*% is arithmetically identical to
an *x*% change in `hand_breadth_mm`: both scale mm/px and nothing else. `docs/BENCHMARK.md`'s
sensitivity table already re-runs HAL at 79.5 and 90.4 mm against 85, which is −6.5% and
+6.4%, so the table's existing rows *are* the sensitivity to a box-convention offset of that
size, and a reader can read them as such. What is not covered is an offset materially larger
than 6%, and whether the real one is larger is unknown. `docs/COVERAGE.md` carries it as a gap,
not as a resolved question.

**Reverses if:** 100DOH's weights become obtainable, in which case both detectors run on the
same frames, the offset is measured rather than reasoned about, and the primary detector
returns to the one `docs/METHOD.md` pre-registered.

## D048 — A mask's hand box bounds its largest connected component, not every pixel of the class

2026-09-06. Rubric **v1.4.0 → v1.5.0**. This corrects D047, one day old, before any detection
was written.

D047 defined the box as "the axis-aligned bounding box of the mask's hand pixels". On real
frames that is wrong, and the smoke run said so. Measured over 120 pilot frames at 960x540,
where a hand at the assumed 0.45 m subtends about **96 px**: box widths came out at a median
of 132, a p90 of **484** and a maximum of **676** — 70% of the frame width. A segmenter emits
scattered false positives, and a bounding box over a disconnected mask spans the specks rather
than the hand.

**The direction matters more than the size.** `hand_breadth_mm / median_box_width_px` is a
**divisor**: an inflated box makes every pixel worth fewer millimetres, so every speed on the
clip comes out *lower*. The flattering direction, on the primary axis, from a definition this
project wrote itself.

**Now:** the box bounds the **largest connected component** of that hand's mask, and
`MIN_MASK_PIXELS` applies to that component rather than to the class total — otherwise a hand
made only of specks clears the floor by summing them and gets a box the size of the scatter.

**Why the tests did not catch it, which is the part worth keeping.** `boxes_from_labels` was
written as a pure function and tested offline precisely so a scale error could not first appear
on a rented GPU. That was right and it still missed this, because every fixture was a **clean
rectangle**: a synthetic mask has no false positives, so no test could distinguish "bounds the
class" from "bounds the hand". The gap was not too few tests but fixtures drawn from the
author's idea of the input rather than from the input. The smoke run's box-width percentiles
cost nothing and found it in one pass; they are now part of what a smoke run reports.

**Correction to this entry's own justification, 2026-09-06 (review finding 6).** The line
above — "Corrected before any detection was written" — and rubric v1.5.0's repetition of it are
a claim about the *output artifact*, not about the quantity. This project's test is whether the
quantity the amended sentence governs was still unmeasured, and it was not: the evidence for the
change is 120 pilot frames of `median_box_width_px`, and the change was made *because of* those
numbers. D045, two entries earlier, is scrupulous about exactly this distinction — "the evidence
that forced the change is a synthetic sweep of a known geometry, not a pilot statistic" — and
these two amendments were held to different standards one section apart.

The change still stands, on a ground that has to be stated rather than implied: the prior
definition **demonstrably did not measure the quantity it named**. A bounding box over a
disconnected mask is not "the hand's box" under any reading; 70% of the frame width is not a
hand. That is a different justification from "the quantity was unmeasured", and a weaker one —
it relies on the defect being visible without reference to whether the resulting numbers were
convenient. Two things make it checkable rather than a matter of trust: the direction is
**anti-flattering** (the box is a divisor, so the correction raises every speed), and the
finding is reproducible from the published percentiles without seeing any pilot value.

**Reverses if:** a later reading shows the largest component regularly drops a genuinely
detached part of one hand — a gloved finger segmented separately, say — in which case the rule
becomes a size-weighted union rather than a single component, measured rather than assumed.

## D049 — The same memory defect, in the sibling path, because only the path that fell over was fixed

2026-09-06.

D043 recorded that the labeller materialised a clip's frames and that colour made it fatal:
4,799 frames at 960x540 in RGB is 7.4 GB, four workers of that exhausted a 32 GB box, two were
OOM-killed. The fix streamed the decode.

`scripts/run_detector.py` had the identical defect and it was not fixed, because it had not yet
failed. The EgoHOS run was launched, three workers each began decoding a 1200 s clip whole, and
fifteen minutes later the run had written **zero rows** and was at 14 GB and climbing. It was
stopped before it repeated the OOM.

**The generalisation that was available and not taken.** D043 named the cause precisely — a
`list(...)` over a colour decode — and stopped at the file where it was found. Both scripts
decode the same corpus at the same resolution through the same helper; the second was one grep
away. A defect record that names a mechanism has said something about every place the mechanism
lives, and treating it as a fact about one file is how the same bug gets paid for twice.

**Fixed the same way**, plus a test. There is nothing to assert on in the output — the run
produces correct rows right up until the machine swaps — so `tests/test_detector_streaming.py`
pins the *shape*: `stream_clip` is a generator, and the pilot loop calls it rather than
`decode_clip`. That follows `tests/test_feature_fidelity.py`, which pins D040 the same way.
`decode_clip` stays for the smoke path, which is bounded by `--smoke` and small by construction.

**What it cost:** about 20 minutes of a `g5.2xlarge` and one restart. Nothing was corrupted --
the run wrote no rows, so there were no partial clips, and the resume logic had nothing to
clean up.

**Reverses if:** nothing. This is a defect record.

## D050 — Flow decodes at 960x540, a measured optimum, and the speed path still fails above ~900 mm/s

2026-09-06.

D045 moved the speed pair to one frame of the source video. That changes what displacement the
estimator sees, so the decode resolution — which nothing had ever chosen — became a live
parameter. Swept at the amended pair on the rendered synthetics
(`results/flow_gain_by_resolution.json`), gain inside the hand box:

| Decode | 301 mm/s | 602 mm/s | 903 mm/s |
|---|---|---|---|
| 480x270 | 0.96 | **0.77** | 0.22 |
| **960x540** | 1.00 | **0.99** | 0.20 |
| 1440x810 | 1.00 | 0.20 | 0.20 |
| 1920x1080 | 1.00 | 0.20 | 0.19 |

**The knee is not monotone in resolution, which is the part worth understanding.** A dense
estimator's search range is in *pixels*; a higher resolution spends the same physical motion on
more of them, so 1440 and 1920 fail at a speed 960 handles. And 480 is worse than 960 in the
other direction: the hand box is only 48 px there, so the depth discontinuity sits inside the
window and is smoothed across. 960x540 is a **measured optimum, not a maximum**, and the
pipeline moves to it from the 480x270 nothing had justified.

**Tuning the estimator does not extend it.** Raising the pyramid to 5 and 6 levels and the
window to 21 and 31 px, at 960x540: gain at 602 mm/s went 0.993, 0.993, 0.988, 0.241, 0.262.
Bigger windows are *worse*, which identifies the mechanism as the smoothness prior rather than
the search range — a wider window straddles the hand/background boundary and averages across
it. That is intrinsic to dense flow with a global smoothness assumption, and it is why neither
RAFT (D044) nor parameters reach it.

**What this leaves, stated rather than buried.** The speed path is faithful to about
**600-700 mm/s** and collapses above **~900 mm/s**, and the HAL equations are fitted over
**255.3-1288.0 mm/s** (Akkas 2015 Table 1). So the top of the band is not measured, it is
*under*-measured, in the flattering
direction, by a factor approaching five. This is not fixed here and is not fixable with a dense
estimator; it is a bound on what the speed path can say, and `docs/COVERAGE.md` carries it.

**Chosen before any pilot speed exists**, on synthetics whose ground truth is exact geometry.
No hypothesis is decided by it and no pilot number has ever been produced on this path.

**Reverses if:** a sparse or hand-masked estimator is measured on the same synthetics and holds
gain above 900 mm/s, in which case the resolution sweep is re-run for it and this optimum is
that estimator's, not the pipeline's.

## D051 — The exactly-zero flow rule does not fire on the case it was written for

2026-09-06.

`docs/RED-TEAM.md` A15 requires a flow failure to be a null with a reason and never a zero, and
D023 implements that at the sample level: an exactly-zero residual inside the box is the A15
signature, so it becomes a null. `== 0.0` exactly, deliberately — D023 argued that nulling
*small* residuals would bias the corpus upward, which is right.

**Measured, it does not fire.** Running the stage over pairs built from one frame twice — the
degenerate case D023 names — the record comes back `status: "ok"`, `n_flow_null: 0`, and
`rms_speed_mm_s: 3.5e-07`. Farneback on two identical frames returns a **tiny non-zero** field,
not a zero one, so neither the estimator's own `field.any()` guard nor D023's exact-zero rule
sees it. The sample is counted as a real measurement of almost no motion.

**The direction is the usual one.** A clip of such samples reports a speed near zero, which
maps to a low HAL. Flattering.

**The rule is not loosened.** A threshold would null real slow motion and bias upward, which is
exactly what D023 refused and still refuses. What is added instead is an **exact** check that
costs nothing and needs no threshold: if the two frames of a pair are byte-identical, that is
the same frame twice — a decode fact, not a measurement — and the sample is a null with that
reason. Real sensor noise means genuinely still footage never produces byte-identical frames;
duplicated frames from a decoder do.

**What this corrects in D023.** That entry says the exact-zero rule catches "identical or
degenerate frames". It catches neither, in floating point. The `flow_null_rate` is therefore an
even weaker lower bound on flow failure than D023 already warned it was, and the entry's
statement of what it does catch was wrong rather than merely incomplete.

**How it was found.** A mutation test. An integration test asserting `rms_speed_mm_s > 0`
passed when the pair was built from one frame twice, because 3.5e-07 is greater than zero. The
assertion was replaced with one that checks the value is the *right size* against a known hand
motion, and the mutation then failed as it should. An assertion that only checks a sign will
accept any bug that leaves the sign alone.

**Reverses if:** nothing. This is a defect record.

## D052 — Fresh-context review: a dead gate, and a debounce that stopped early on nulls

2026-09-06. `docs/WAVES.md` requires a review from a context that did not produce the work. This
one was given the session's diff, `CONTRACTS.md`, the seam list and the checklist, and
explicitly not the author's account. It returned fourteen findings. The two that change numbers
are here; the rest are tracked below and in the entries that follow.

**1. `debounce` stopped at the first short run it could not absorb.** A run flanked by nulls on
both sides has nothing to absorb it into, and the loop returned instead of moving on — so every
later flicker in the clip stayed. Reproduced directly: a single-frame gap between two 20-frame
bouts is absorbed on a series without nulls and left in place on one with them.

The consequence is the one this project cares about most: **the segment count became a function
of where the unreadable frames fell**, which is the confound D042 introduced `null_bounded_segments`
to keep *out* of the count. Re-run on the pilot's rescored labels, total exertion segments went
**18,075 → 12,042**, a third fewer. Every count D042 and D046 rest on was inflated by half.

**The H2 verdicts do not move.** H2a still FAILS, H2b still passes, and 75 of 93 resolved peaks
still sit below 0.05 Hz. Transition-counting got *smaller*, which narrows its disagreement with
the spectral path, and it is still far outside H2a's 20% bound. D046 stands; the magnitude it
was derived from was wrong, and is corrected here rather than left to be discovered.

**2. `build_signal`'s H2c gates summed a list nothing appended to.** `estimates` was declared
and read three times and never written. So coverage was always 0.0 and always FAILED, the
flow-null gate was never evaluable and always FAILED, and the conflict gate divided by zero
samples and **always PASSED**.

The comment directly above it reads: *"Not `>= 0`, which is what this checked and which no run
could ever fail. A gate that cannot fail is not a gate."* The replacement was unfalsifiable for
a different reason, three lines under a note about unfalsifiable gates.

**Worse, the failure was visible and misread.** The integration test's own output printed
`FAIL H2c: hand-box coverage` on a fixture where every instant carried a box, and it was read as
"correct, no detector has run". A permanent FAIL is as uninformative as a permanent PASS, and
this project has now made that mistake twice in one session — the other was reading a `make
validate` failure as success because the absent line was the signal.

**Both are now pinned by tests that fail on the defect**, and the integration test asserts the
gates can *pass* on a fixture where they should, which no test did before.

**Reverses if:** nothing. This is a defect record.

## D053 — H4 was confirmed by a corpus that carried no evidence about it

2026-09-06. Review finding 4.

H4 asks whether exposure is set by the site or by the individual, and compares between-factory
variance against between-worker-within-factory variance. The second is computed only over
factories that contributed **two or more workers**. Where none did, the list is empty, its mean
defaults to `0.0`, `ratio` short-circuits to infinity, and `holds` — defined as `ratio > 1` —
returned **True**.

Reproduced: three factories, one worker each, every HAL identical. Nothing varies anywhere.
`between_factory` 0.0, `within` 0.0, ratio infinity, **HOLDS**. `scripts/score_hal.py` printed
`H4 variance ratio: HOLDS` from it.

**This is D034's defect, one hypothesis over.** That entry corrected H2b because "H2b was
satisfiable by a corpus with no repetition in it" — a hypothesis confirmable by data that cannot
bear on it. The same shape sat in H4 and the correction was not carried across, exactly as D049
failed to carry D043's resume fix to the sibling script. Both times the general form of the
finding was available in the entry that recorded it, and both times only the instance was fixed.

**Now:** `VarianceComponents.evaluable` requires at least one factory with two workers **and**
non-zero between-factory variance, and `holds` requires `evaluable`. `score_hal` prints
`NOT EVALUABLE` rather than a verdict. An unevaluated hypothesis is neither confirmed nor
falsified, and saying so is not a failure of the pipeline — reporting HOLDS was.

**Reverses if:** nothing. This is a defect record.

## D054 — Two published fields could not say "not measured", so they said zero

2026-09-06. Contracts **v1.4 → v1.5**. Review findings 7 and 8.

`docs/ARCHITECTURE.md`'s seam is that absence is a value with a reason and never zero. Two
schema fields had no way to express absence, so the code supplied a number:

- **`HALScore.duty_cycle`** was non-nullable, and the caller wrote `duty.duty_cycle or 0.0`. A
  clip whose duty cycle could not be computed was published with the same `0.0` as a clip whose
  hands never engaged. The record has two statuses — `no_input` and `zero_duty_cycle` — that
  exist precisely to keep those apart, and the fabricated zero put them back together in the one
  field a reader averages. Now null, and null exactly under `no_input`.

- **`FrequencyEstimate.resolvability_floor`** was required whenever `method == "spectral"`, and
  `cycles/spectral.py` wrote **1.0** for clips it never transformed. 1.0 is below the smallest
  value the formula can produce — **5.30**, at the two-bin minimum — so it was a floor no clip
  could ever have had, on a field `docs/RUBRIC.md` v1.2.0 made load-bearing precisely so a
  reader could check `resolvable` against it.

  The rule is now that the floor accompanies a **judgement**: it is present exactly when
  `peak_power_ratio` is, because a floor without a ratio judged nothing and a ratio without a
  floor cannot be read. A constant series, whose periodogram *was* computed, now records a real
  ratio of 0.0 against a real floor instead of being lumped in with the unmeasured.

- **`HandSpeedEstimate.flow_null_rate`**, added 2026-09-06 for the same reason. It is nulls
  over *boxed* samples, so with nothing boxed the ratio has no value; it carried `0.0`, which
  reads as "the flow never failed" on a clip where flow was never attempted. The review rated
  this one MINOR because the status discloses it and both aggregate gates guard it. It is fixed
  anyway: leaving one instance of a mechanism after fixing two is what D049 and D053 did, and
  the review found both.

**The revision invalidates stored records, and that is the intended behaviour.** Every
`HandSpeedEstimate` on disk was written under v1.4 with `flow_null_rate: 0.0` and no boxes, so
`make hal` now refuses to load them instead of accepting them — the same rule `corpus_rev`
enforces, that records written under two definitions are never pooled. They are the placeholder
`no_detector` records and are regenerated from the real detections.

A reader hitting that refusal sees a pydantic error and not "this file predates the contract",
because records do not carry a `contracts_rev` the way they carry `corpus_rev`. That is a real
gap and it is not fixed here: adding the field would invalidate every stored record a second
time, for a message.

**All three were forced by the schema, which is the part worth keeping.** None was a careless
line: a non-nullable field leaves a caller no way to be honest, so the fix belongs in the
contract and not in a convention about what to write. The seven seams say absence must be
sayable; these are three places where it was not.

**Reverses if:** nothing. This is a defect record.


## D055 — Three entries quoted the wrong fitted range for the Akkas equation

2026-09-06. Review finding 13.

D044 and D050 both say "the HAL equations are fitted over 400-1000 mm/s". They are not.
`src/cyclegraph/exposure/hal.py` carries `AKKAS_2015_RANGE = FittedRange(255.3, 1288.0, 11.0,
100.0)` against a comment citing Akkas 2015 Table 1, and that constant is what `out_of_range`
is computed from — so the code and the prose disagreed, and the code is the one with a source.

**Where the wrong number came from.** D021 tabulated the cost of the A14 floor at 400, 612, 800
and 1000 mm/s — a set of evaluation points chosen to span a plausible working band. Those four
numbers were later quoted as though they were the equation's fitted range. A band someone chose
to tabulate and a range a paper fitted over are different things, and one became the other by
repetition across three entries.

**It matters in the direction that makes the earlier entries too kind.** D050 argued that the
speed path's collapse above ~900 mm/s leaves "the top of the band" unmeasured, with the band
ending at 1000. The real range runs to **1288 mm/s**, so the unmeasured portion is larger than
D050 said, not smaller. The correction is applied in place in D044, D050 and
`docs/COVERAGE.md`.

**Reverses if:** the Table 1 figures in `exposure/hal.py` are themselves wrong, which
`docs/SURVEY.md` S3's golden cells would show, since they are checked against the paper's own
table rows.

## D056 — D022's drop reached one record and not the other, and it inflated H2c

2026-09-06. Found while checking, before the speed path's first real run, that the rule the
original plan called "the highest-cost mistake available in W3" was actually implemented.

D022 makes `hands_visible` label-sourced and `hand_box_width_px` detector-sourced, and requires
that **a detector box on a frame the labeller called `hands_visible: 0` is dropped and counted**.
`signal/frames.py:resolve_conflicts` does exactly that — and it is applied only to the
`FrameSignal`. `scripts/build_signal.py` built the speed samples from the **unresolved** boxes,
so a box discarded from one record was still counted in the other's `n_with_box`, and an RMS
residual was taken inside it.

**What that costs.** `coverage = n_with_box / n_samples` is H2c's pre-registered gate, and the
inflation is in the direction that makes the gate **easier to pass** — on the number that decides
whether the speed path is reported at all, or whether D014's switch to spectral-primary fires.
It also puts a residual inside a box on a frame with no visible hand, which is background motion
scored as hand speed.

**Neither the fresh-context review nor any test caught it.** The review read the diff and the
contracts; this rule is satisfied in the file it looked at, and the omission is in a different
file's *use* of that file. Every test exercised a fixture where the labeller and the detector
agreed, so no test could tell the two paths apart. The fixture that finds it has the detector
seeing a hand at every instant and the labeller denying it in half of them.

**One definition, two call sites.** `box_is_contradicted(label)` is now the rule, used by
`resolve_conflicts` and by the speed path. The raw box width still reaches `FrameSignal` so the
conflict is counted where `docs/BENCHMARK.md` reports it — dropping it earlier would have made
the published "box dropped: labeller reported no visible hand" row read zero.

**Timing.** Caught before the detections were consumed, so nothing has to be withdrawn. Had the
signal pass run first, H2c would have been evaluated on an inflated coverage and the result
published as a pre-registered gate outcome.

**Reverses if:** nothing. This is a defect record.

## D057 — The spectral path carried its own copy of the clip floor

2026-09-06. Found by looking for more of D056's shape rather than waiting to be told.

D056 was a rule defined once and applied at one of its two consumers. That is a class, not an
incident, so the obvious next question is where else a rule has more than one home. The clip
floor is one: `exposure/duty.py` and `signal/frames.py` compare against `models.MIN_CLIP_S`,
and `cycles/spectral.py` compared against a literal `60.0`.

**Nothing is wrong today** — `MIN_CLIP_S` is 60.0, so every path agrees. What was wrong is that
they agreed by coincidence: changing the rubric's floor would have moved two paths and left the
spectral one silently on the old value, and the divergence would show up as a frequency estimate
existing for a clip that duty cycle refused to score. The original plan's acceptance criterion
for the manifest unit said "the module contains no literal 60"; the same criterion was never
applied to `cycles/`.

The test is textual, like `tests/test_signal_ports.py`'s shard-token check, because an import
check passes a module that imports the constant and then ignores it. It flags a `duration_s`
comparison against any non-zero literal and leaves positivity guards alone.

**The same sweep found a second, larger one: the hand breadth had three homes.** 85 mm is the
constant every reported speed is divided by. `signal/speed.py` defines `HAND_BREADTH_MM`,
`scripts/build_signal.py` and `scripts/measure_a14_floor.py` import it — and
`signal/synthetic.py` carried it as a literal default while `scripts/measure_flow_gain.py` kept
a private copy. `docs/BENCHMARK.md`'s sensitivity table re-runs HAL at 79.5 and 90.4 mm against
that constant, so a copy that did not move would have left the synthetic geometry describing a
hand the pipeline no longer assumes — and the A14 floor and the gain curves are both computed
from that geometry. All four now read one definition.

**Reverses if:** nothing. This is a defect record. It is recorded because the way it was found
is the point: D056 was a class, so the next move was to sweep for the class rather than wait
for the next instance to surface.

## D058 — The labels carried no `corpus_rev`, so the check for it passed on nothing

2026-09-06.

`scripts/verify_labels.py` reports "corpus revisions present: 1" and fails if there is more than
one, because `corpus_rev` is on every contract record for one reason: records from two corpus
revisions are never pooled. **The label rows never carried the field.** `row.get("corpus_rev",
"")` returned `""` for all 462,437 of them, the set had one element, and the check passed —
having read nothing.

**This corrects evidence already given.** D046's checkpoint cited "462,437 of 462,437 planned
rows, one corpus revision" as the basis for re-deriving H2's verdict. The row count was real.
The revision claim was not: there was no revision on any row to count. The verdict does not
depend on it — the labels came from a single run against a single pinned revision — but the
statement was of a check that had not happened, which is worse than not making it.

**Found the same way as D057**, by sweeping for a class rather than waiting: a check that cannot
fail is the same defect whether the condition is trivially true (D052's conflict gate), computed
over an empty denominator (D052's null gate, D053's H4), or — here — read from a field that does
not exist. That third form is the hardest to see, because the code looks like it is checking
something.

**Fixed in three parts.** The labeller writes `corpus_rev` on every row. `verify_labels.py` now
distinguishes "one revision" from "no revision recorded" and says which, instead of reporting
the second as the first. And the existing 462,437 rows are stamped with the revision they were
in fact produced at — disclosed here as a retro-stamp rather than a measurement, and safe only
because the run took `--corpus-rev` and read one pinned revision throughout.

**Detection rows still carry no `corpus_rev`**, and are not stamped: they were being written
while this was found, and rewriting a file three workers were appending to is how the partial
clips of D043 happen. `verify_labels.py` now reports that absence plainly instead of counting it
as agreement.

**Reverses if:** nothing. This is a defect record.

## D059 — The flow estimator is Farneback, decided by the rule D024 fixed beforehand

2026-09-06. `results/flow_benchmark.json`, both arms, 200 real pilot pairs from 20 clips,
seed 777, at the pair D045 defines and the resolution D050 chose.

| | pairs/s | flow-null | clears ceiling | A14 residual, px | declared cost |
|---|---|---|---|---|---|
| farneback-cv2 (CPU) | 7.57 | 0.000 | yes | **1.217** | none; cv2 is in the `signal` extra |
| raft-small (A10G) | 21.5 | 0.000 | yes | **1.014** | torch, undeclared |
| *geometry alone* | — | — | — | *1.146* | — |

**Rule 2, the primary one, does not separate them.** Both return a field on every pair.

**Rule 3 decides it: lower total pilot cost.** RAFT is 2.8x faster per pair and needs a GPU to
be so. Farneback needs no GPU and parallelises across processes — measured on this box, eight
workers reach about 20 pairs/s against one worker's 7.6, and cv2 does not thread a single call.
Pricing the pilot's ~388,000 flow calls: RAFT on the `g5.2xlarge` is ~5.0 h at $1.212, about
**$6**; Farneback on a CPU instance of the same generation is ~1.3 h at $1.428, about **$2**.
Rule 5's tiebreaker, written before any rate was seen, points the same way: RAFT costs a
declared torch dependency and Farneback costs nothing.

**The A14 column favours Farneback for a reason that is not speed.** It reports the residual an
estimator leaves on the rotation synthetic, against a geometry-only floor of 1.146 px — the
error the rubric's scalar ego-motion leaves when the field is *exact*. Farneback lands at 1.217,
above the floor: its own error adds to the geometry's, which is what an estimator's error does.
RAFT lands at **1.014, below the floor** — and a residual smaller than exact geometry allows can
only come from under-recovering the field. That is D044's mechanism in miniature and it points
the flattering way: an estimator that makes A14 look smaller than the geometry says it is has
not mitigated A14, it has hidden a little of it.

Had rule 3 gone the other way this column would have been the argument against taking it, which
is why D025's plan put it in the table.

**What this does not claim.** Farneback is not good here — D044 and D050 measure it recovering
0.18 of a working hand's motion above ~900 mm/s, and RAFT is no better there. The choice is
between two estimators that share a ceiling, on cost and on which of them is honest about the
residual below it.

**Reverses if:** the speed path moves to an estimator that does not smooth across the
hand/background boundary, in which case the comparison is re-run rather than inherited — the
rates here are for a 960x540 pair one source frame apart and nothing else.

## D060 — Two uncaught exceptions cost six clips of the pilot, and both had a rule already

2026-09-06. The signal pass wrote **91 of 97 clips**. The six missing were not skipped by any
rule; two workers raised and died, and every clip still queued behind them was never attempted.

**The two exceptions, and why both were right to refuse and wrong to raise.**

- `ego_motion` rejects a hand mask with no complement: *"a full-frame hand mask is a failure,
  not a zero ego-motion."* That is correct — with no background there is no camera motion to
  subtract, and returning zero would report the camera's motion as the hand's. It is D048's
  segmentation leak at its limit, where the box reaches the whole frame.
- `decode_gray_frames` raises `RuntimeError` on ffmpeg's non-zero exit, which is right too: a
  decode that dies mid-stream is not a short clip, it is a failure.

**Both are refusals the rubric already has an answer for**, and it is not `raise`: absence is a
value with a reason. A null sample carries the reason; a stack trace carries it out of the
process and takes the shard's remaining clips with it. All six lost clips are 1200 s — the
longest, so the most pairs and the most chances to meet either condition.

**Fixed at both levels.** `speed_sample` catches the ego-motion refusal and returns a null with
the reason attached, so a full-frame mask costs one sample rather than a run. `build_signal`
wraps the decode loop, so a clip that dies mid-stream keeps what it decoded, has the rest marked
absent-with-reason by the gap loop that already existed, and lets the shard continue. Failed
clips are written to `signal_failures.jsonl` rather than only printed.

**The gates on 91 clips are not the pilot's answer**, and were not read as one. H2c is
pre-registered "on the pilot", and a gate computed over 94% of it is the partial-denominator
mistake D052 corrected in a different file. The six were re-run before any verdict was recorded.

**Reverses if:** nothing. This is a defect record.

## D061 — W3's exit condition is met: H2c passes on the pilot, and the aggregate is suppressed

2026-09-06. `docs/WAVES.md`'s W3 gate, verbatim: *"Pilot factory manifest reconciles against
published counts; decode failure rate <1%; `FrameSignal` and `HandSpeedEstimate` written for the
pilot; A14 synthetics pass"*. All four hold. The verdicts are the publishable part; the values
stay in `results/pilot/` (D018).

**H2c PASSES, both halves.** Detector hand-box coverage clears the pre-registered 60% floor and
the flow-null rate is within the 10% ceiling, computed over all 97 clips from one file rather
than per shard (D052). Every clip with a speed record produced a HAL, and at least one clip
scored on the speed path — the first exposure values this project has computed from a
measurement rather than a placeholder. All 194 records validate against contracts v1.5, and
carry the provenance the decisions require: `mask_source: egohos` (D047) and
`flow_method: farneback-cv2` (D059).

**The corpus aggregate is SUPPRESSED, and that is the correct outcome, not a failure.** D019's
k-anonymity floor needs 5 factories and 50 workers; the pilot is one factory by D012. So **H3,
H4 and H5 are not answerable here at all** — not "failed", not "untested pending data", but
structurally outside what a single-site pilot may publish. The stratum prints as suppressed
rather than being omitted, which is the rule.

**What the pass does and does not license.** It says the detector finds hands often enough, and
the flow estimator returns a field often enough, for the speed path to be computed on this
factory. It says nothing about whether the speed is *right*: D050 measures the path collapsing
above ~900 mm/s against an equation fitted to 1288 mm/s, D047 records that the box-convention
offset against the pre-registered detector can never be measured, and `docs/COVERAGE.md` still
names the absent ergonomist as the largest gap. A gate that tests coverage has tested coverage.

**Six clips had to be re-run** after D060's uncaught exceptions, and the per-clip flush added in
the same hour is why they survived the instance's shutdown timer firing mid-re-run. The gates
were not computed until all 97 were present.

**Reverses if:** the labels are withdrawn again, on the standard D040 set, or the detector is
replaced — both would require the coverage number to be re-measured rather than inherited.

## D062 — Measured hypotheses were reporting as UNTESTED, because the gates printed and saved nothing

2026-09-07.

`MEASUREMENT_CARD.json` reads one verdict file per claim from `results/` and treats a missing
file as `UNTESTED` — which `card/build.py` defends as the truth: *"nothing has produced that
number"*. It was not the truth. H2a and H2b were measured on 2026-09-06 and re-derived after
D052; H2c passed on the full pilot the same day. All three read `UNTESTED` on the card, because
the scripts that evaluate them **print a PASS/FAIL line and persist nothing the card can read**.

So W8's artifact — the one thing in this project a reader is meant to consult — disagreed with
the project's own results, in the direction of understating what had been done. The card was
right about its rule and wrong about the world, and nothing connected the two.

**Fixed by writing the verdicts where the card looks.** `estimate_frequency.py` writes `h2a` and
`h2b`, `score_hal.py` writes `h2c`, `compare_rates.py` writes `h1b`. Each carries a status from
the closed set `card/build.py` already validates against, so an unknown string is refused rather
than silently treated as untested.

**H1 and H2 are conjunctions and are rolled up explicitly** by `scripts/roll_up_claims.py`,
not inferred by the card. The card generates and must compute no verdict of its own, or the
artifact would depend on logic no measurement produced. A parent whose parts are not all present
is **UNTESTED and never HOLDS**: a conjunction over an incomplete set is unevaluated, not
satisfied — the rule D052 and D053 arrived at for gates over absent data, applied to claims.

**The card now reads:** H2 FAILED, from H2a FAILED with H2b and H2c holding; H1 UNTESTED while
H1b is still running and H1a is unfunded; everything else UNTESTED. Verdict `NOT_VERIFIED`, exit
nonzero, which is the stage working.

**Reverses if:** nothing. This is a defect record.

## D063 — A stalled decode had no deadline anywhere, and looked exactly like slow work

2026-09-07.

The 8 Hz labelling run for H1b stopped at 50 of 97 clips and **sat for eleven hours**. The
Python process was at 0.0% CPU with an ffmpeg child holding an open HuggingFace CDN read. No
error, no exit, no log line. Nothing distinguished it from a long clip.

**There was no read deadline in the pipeline at all.** `decode_gray_frames` blocks in
`process.stdout.read(frame_bytes)`, and the `timeout_s` it carries applies to
`process.communicate()` in the `finally` block — reached only *after* stdout is exhausted, which
a hung ffmpeg never does. The guard that existed protected the path that could not hang.

**The expiring signed URL is a red herring**, and worth writing down so the next reader does not
chase it: the CDN URL expired at 06:37 UTC and the stall began around 01:37, five hours earlier.
The URL expiry is a consequence of the hang, not its cause.

**Fixed with ffmpeg's own `-rw_timeout`, on the input**, so a stalled read aborts and ffmpeg
exits non-zero — which `decode_gray_frames` already turns into a `RuntimeError` and which
D060's per-clip wrapper already catches. The fix is one argument because the machinery to
handle a failed decode was built the day before; what was missing was any way for the failure
to *occur*.

**This is the fourth shape of the same defect this project has produced**: a check that cannot
fail (D052's conflict gate), a check over an empty denominator (D052's null gate, D053's H4), a
check reading a field that does not exist (D058), and now a check on a path that cannot be
reached. In every case the code looked like it was checking something.

**It cost eleven hours of wall-clock and nothing else** — the labeller's resume (D043) keeps the
50 finished clips, so the re-run starts at 51.

**Reverses if:** nothing. This is a defect record.

## D064 — Second fresh-context review: the fixes needed fixing

2026-09-07. A second review, from a context that had not seen the first round, given the diff
since D052 and pointed specifically at **the fixes** rather than the original code. It returned
twelve findings. Every one is real; all are addressed. The pattern is the point: a fix is new
code, and this project's own defect classes reappeared inside the corrections for them.

**Destructive, and live.** `--record-not-attempted` still wrote `flow_null_rate=0.0` with no
boxes after D054 made that field null-when-nothing-was-boxed. The validator refused the first
record — *after* the enclosing `with` had opened both output files in mode `"w"` and truncated
them. At its default `--out-dir` the flag deleted the pilot's 194 records and wrote nothing.
448 tests and `mypy --strict` were green because nothing exercised the flag.

**The H4 guard was wrong in both directions.** D053 added `evaluable` to stop H4 being confirmed
by a corpus with no within-factory information, and tested `between_factory > 0` — the
*numerator*. H4 is a ratio, so what must exist is the denominator. A **measured** within-factory
variance of zero still gave ratio infinity and **H4 HOLDS**, which is D053's own defect one term
over; and a measured between-factory variance of zero — a clean falsification — reported NOT
EVALUABLE. The test that should have caught it built a corpus with identically-valued workers
and asserted H4 holds, encoding the defect.

**A guard that could not fire.** The new `--fps` flag made resume compute its plan at the
requested rate while `--out` still defaulted to the 4 Hz file, so `--fps 8` marked every clip
partial and `drop_partial_clips` kept nothing. The first fix read the `fps_sampled` field —
added in the same change that created the hazard, so absent from every label file written
before it. **Tested on a copy, which is the only reason this is a paragraph and not an
incident**: the copy went from 462,437 rows to 3,467. The rate is now derived from instant
spacing, which every row has ever carried.

**A verdict from a partial pilot.** `score_hal` wrote `h2c.json` as `HOLDS` over whatever speed
records it was handed. The 91-of-97 run would have published a pre-registered gate from 94% of
the pilot; that the six missing were noticed (D060) was operator discipline, not a check. It now
compares against the manifest and writes `UNTESTED` when short.

**And four more gates that could not fail**, in the same shapes this project keeps producing:
`count_conflicts`'s only check summed three branches and compared them to their own total — an
identity, in a file written to close exactly this class; two passes in the labeller spelled out
`or not clips` and `total == 0 or`; and `verify_labels`'s revision check tripped on
`len(revisions) > 1`, which an empty set never satisfies, so D058 made the printed line honest
and left the verdict passing on nothing.

**Also fixed:** the detector's `expected` set was built from one invocation's manifest slice
rather than the whole manifest, so sharded onto a shared `--out` it would delete other shards'
completed clips; `CONTRACTS.md` had no v1.5 changelog row and its header claimed a freeze date
that v1.5 does not have; the validator forbade a transitions estimate's floor but not its peak
ratio, though the contract forbids both; a `Counter` lookup meant a measured zero was absent
from the conflicts artifact rather than recorded as zero; and a box dropped under D022 was
reported as "no detected hand box", attributing a labeller disagreement to the detector.

**What the review found clean, and checked rather than assumed:** the debounce fix (exhaustive
over every series up to length 9), the unit arithmetic end to end, D056's fix visible in the
data, and D059/D061/D062 against their artifacts.

**Reverses if:** nothing. This is a defect record.

## D065 — Third review: one of D064's fixes was worse than the defect it replaced

2026-09-07. A third fresh-context review, scoped to D064's ~500 lines and pointed at the fixes.
Eight findings. Three of the ten claimed fixes were wrong or incomplete, and **one made the
situation worse**. The empirical result across three rounds is now unambiguous: in this
codebase, a fix is where the next defect is.

**The one that got worse.** D064 diagnosed `--record-not-attempted` as *"deleted the pilot's 194
records **and wrote nothing in their place**"* and fixed only the second clause. The truncation
was untouched. So at its default `--out-dir` the flag went from crashing on record one — leaving
two empty files and an obvious incident — to **succeeding**: it now replaces the pilot's measured
records with placeholders, and the next `score_hal` reads 97 records with no boxes and publishes
H2c as **FAILED**. A pre-registered hypothesis falsified by a stage that never ran, written to
the file the card reads. A silent success is worse than the crash it replaced, and D064's own
wording contained the clue it did not follow.

Fixed twice over: the writer refuses a non-empty target, and `score_hal` treats an all-
`no_detector` speeds file as UNTESTED, because a stage that did not run cannot falsify anything.

**The one that did nothing.** D064 claimed to rebuild the detector's `expected` set "from the
whole manifest, not this invocation's slice". Both lines are `list(iter_clips(ROOT /
args.manifest, args.corpus_rev))` — the same call with the same arguments. The manifest was
parsed twice and nothing changed. `run_detector` has no shard flag, so a "slice" does not exist;
sharding is by passing a different `--manifest`. **The real hazard was the clip the manifest does
not name**: `expected.get(cid)` returns None for a clip another shard wrote into a shared
`--out`, so it never matched, landed in `partial`, and had its rows deleted. That is now fixed —
in both scripts, because `run_labeller` had it too.

**The one that recreated the error it was fixing.** The new `no_box_reason` used
`box_is_contradicted`, which is true for `hands_visible is None` as well as `0`. So a frame the
labeller could not read got a reason claiming the labeller *reported no hand* — 8,750 of the
pilot's samples, 43% of the drops. `resolve_conflicts` counts those two apart twelve lines below
the function that conflates them, and `docs/BENCHMARK.md` gives them separate rows for exactly
this reason.

**A false refusal is a defect too.** D064 made `verify_labels` fail when no row carries
`corpus_rev` — and detections, by D058's explicit decision, carry none and never will. A
complete, correct artifact could no longer pass. The requirement now keys on what the file is.

**Also fixed:** `score_hal` compared record *counts* to manifest counts, so a file missing one
clip and carrying one foreign clip read as complete; `rate_of` inferred from the first two
instants and failed three ways (a single-row first clip returned None and left the original
hazard open, a gap doubled the inferred rate, disorder gave nonsense) and now takes the modal
spacing, refusing outright when the rate is undecidable; the new refusal test asserted only an
exit code that `main` also returns for a missing probe; and `count_conflicts`'s docstring claimed
equivalence with a number it had deliberately narrowed.

**What three reviews have established about this project's failure modes**, all now in HANDOFF:
a gate that cannot fail; a check over absent data; a rule fixed at one of its consumers; a claim
the artifact does not support; and — the one only a second look at a fix can find — **a repair
that reads its own diagnosis too narrowly**.

**Reverses if:** nothing. This is a defect record.
