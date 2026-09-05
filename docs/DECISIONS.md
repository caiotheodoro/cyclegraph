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
moves HAL by **0.85 at 400 mm/s, 1.22 at 612 mm/s and 1.22 at 800 mm/s** — recomputed from
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
