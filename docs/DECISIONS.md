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
