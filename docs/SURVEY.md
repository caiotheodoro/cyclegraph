# Survey

**The novelty gate.** Nothing downstream runs until this file answers one question:

> *Has automated hand-activity-level assessment from egocentric video been published?*

## Verdict: CLEARS, NARROWLY — run 2026-09-05

Every source below was opened on 2026-09-05 and is tagged `[V]` (primary source read) or
left `[S]` with the reason it could not be opened. Two `[S]` entries remain and neither is
load-bearing: the gate is decided by the `[V]` rows and by two direct PubMed queries whose
result counts are recorded here.

**What the gate found.** HAL has been automated from video since 2013, by one lab, from a
fixed third-person camera, with a published frequency–duty-cycle equation and a published
hand-speed–duty-cycle equation. No published system scores HAL, duty cycle or exertion
frequency from a head-mounted camera. The nearest egocentric work measures "percentage of
time interacting" for rehabilitation and never mentions ergonomics.

**So the contribution is narrower than "egocentric ergonomics is empty", and it is stated
narrowly:** a per-frame data-quality statistic published by a dataset vendor is
dimensionally the duty-cycle input of a validated occupational-exposure index; reading it
that way, from the worker's own viewpoint, at corpus scale, without new annotation, is
unpublished. The instrument is not new. The observation is.

The tagging discipline is inherited from `../vernier/docs/SURVEY.md`, where a claim tagged
`[S]` dissolved on contact with the source. That happened here too, twice — see S1 and S4.

## S1 — Is any published automated ergonomic assessment system egocentric? **No.** `[V]`

Direct queries, run 2026-09-05 against PubMed via E-utilities:

| Query | Hits |
|---|---|
| `"hand activity level" AND (egocentric OR "first-person" OR "head-mounted" OR "wearable camera")` | **0** |
| `(egocentric OR "first-person" OR "head-mounted" OR "wearable camera") AND (ergonomic* OR musculoskeletal) AND video AND (hand OR wrist) AND (repetiti* OR "duty cycle" OR exertion)` | **1** — PMID 40890863, esports wrist-extensor fatigue by sEMG; not video, not HAL. Irrelevant. |
| `"hand activity level" AND (video OR "computer vision") AND (automat* OR tracking)` | **7** — all Radwin-lab, all third-person; listed under S2 |

Systems opened:

- Validation of computer-vision ergonomic risk assessment in real manufacturing
  (*Scientific Reports* 14:27785, 2024; PMC11561082). `[V]` Cameras "mounted on tripods,
  positioned behind and to the side of the monitored operators". REBA, RULA, OCRA. tf-pose +
  MediaPipe hands. Twelve workstations. No HAL, no duty cycle.
- ErgoExplorer (arXiv 2209.05252). `[V]` "Regular cameras"; REBA; joint angles. No HAL, no
  duty cycle. Viewpoint not stated, but REBA scores trunk/neck/legs, which a head-mounted
  camera cannot see.
- DULA/DEBA (arXiv 2205.03491). `[V]` Differentiable surrogates that replicate RULA/REBA
  from joint angles to >99%. They are score models, not vision systems, and viewpoint-
  agnostic by construction. Not a hand-activity instrument.
- mmWave-based automated REBA (arXiv 2607.02611). `[V]` Radar, not video. REBA. No HAL.
- Egocentric hand use after cervical SCI (Zariffa lab, *J NeuroEng Rehabil* 16:83, 2019;
  PMC6612110). `[V]` **Nearest prior art.** GoPro on a head strap; Faster R-CNN hand
  detection; random forest on optical flow + HOG + colour. Metrics: "amount of total
  interaction as a percentage of testing time", "average duration of individual
  interactions", "number of interactions per hour". Nine participants, activities of daily
  living. **No mention of ergonomics, occupational exposure or repetitive work.** The first
  metric is duty cycle by another name, which supports the argument that the construct is
  recoverable egocentrically — and confirms nobody has pointed it at a factory.
- *A systematic review of computer vision-based human pose estimation for occupational
  safety* (*Int J Ind Ergon*, 2026, DOI 10.1016/j.ergon.2026.103931). `[S]` — publisher
  returned 403 and Crossref carries no abstract. **Left `[S]` because it could not be
  opened; not load-bearing** — the direct queries above answer S1 without it.
- Iyer & Jeong, PRISMA review of pose estimation for ergonomic risk (*Proc HFES*, 2025).
  `[S]` — publisher returned 403; not indexed in PubMed under those authors. **Left `[S]`
  for the same reason; not load-bearing.**

The earlier claim that "every published system is third-person" survives for every system
that could be opened, and is restated with its evidence rather than as a slogan.

## S2 — Has HAL been automated from video at all? **Yes, third-person, since 2013.** `[V]`

One lab (Radwin, Hu, Chen, Akkas, Azari; University of Wisconsin), one viewpoint. Every
paper below was opened via its PubMed record.

| PMID | Year | What | Viewpoint | Agreement |
|---|---|---|---|---|
| 23691826 | 2013 | Automated video exposure assessment of repetitive HAL for a load-transfer task (*Hum Factors*). Cross-correlation template matching on one region of interest. | Fixed camera, 12 subjects, paced lab task | slopes 0.98 (R² .79) frequency, 1.27 (R² .63) duty cycle, 1.06 (R² .77) HAL |
| 25343278 | 2015 | Hand speed–duty cycle equation for HAL (*Ergonomics* 58(2):184–194; PMC4664886) | Latko's 33 job videos + 30 validation tasks | R² 0.99, MSE 0.16 on validation |
| 25978764 | 2015 | Accuracy of conventional 2D video for upper-limb kinematics in repetitive tasks | Fixed | median speed error 86.5 mm/s, "sufficient for HAL" |
| 26848051 | 2016 | Measuring elemental time and duty cycle using automated video processing (*Ergonomics*) | Fixed, marker-less | duty-cycle error 2.7–3.3%, HAL error 0.1 |
| 28640656 | 2017 | Exertion time, duty cycle and HAL for industrial tasks using computer vision (*Ergonomics*) | Fixed | HAL difference 0.3–0.5 |
| 28284701 | 2017 | Visualising stressful aspects of repetitive tasks (*Appl Ergon*) | Fixed | — |
| 36227226 | 2023 | Observer vs single-frame video vs computer-vision HAL (*Ergonomics*) | Fixed | 68% within ±1 HAL; R² 0.89 CV vs single-frame |
| 40811128 | 2026 | HAL from upper-limb pose trajectories, probabilistic regression (*Ergonomics*) | Third-person pose | RMSE 0.24 in-domain, 0.74 cross-domain |

**Consequence for this project.** The instrument — HAL from (frequency, duty cycle) or from
(hand speed, duty cycle) recovered by computer vision — is published, validated against
observer ratings, and has a cross-domain error of 0.74 HAL points in its best current form.
cyclegraph inherits that lineage rather than competing with it (`docs/LINEAGE.md`), and the
cross-domain figure is the honest prior for how far an unvalidated egocentric port could be
off.

## S3 — Exact HAL mapping and edition. **Resolved; two open equations.** `[V]`

Opened: Radwin, Azari, Lindstrom, Ulin, Armstrong, Rempel, *A frequency–duty cycle equation
for the ACGIH hand activity level*, *Ergonomics* 58(2):173–183, 2015. PMID 25343340. Open
PDF: `https://stacks.cdc.gov/view/cdc/200748` (and `ergo.wisc.edu`). Read in full.

- **Equation (3):** `HAL = 6.56 · ln(D) · [ F^1.31 / (1 + 3.18 · F^1.31) ]`, F in
  exertions/s, D in percent (`D = 100 · work / (work + rest)`). Nonlinear least squares on
  Latko et al. (1997)'s 33 jobs. Residual SD 1.18 (vs 1.31 for the linear model), AIC 109.3
  vs 116.2.
- **Fitted to** the ACGIH 2001 TLV look-up table (their Table 1), which was itself built by
  the ACGIH Physical Agents Committee from a linear regression on 31 of the same 33 jobs.
  The equation "closely follows the original TLV table" and captures the committee's manual
  upward adjustments at 90% duty cycle.
- **Data range:** F 0.125–1.67 exertions/s; D 11–100%; HAL 0.6–8.5; only two of 33 jobs
  above 1.5 exertions/s. The paper proposes the table's "2 exertions/s" row be read as 1.5.
- **Definitions used:** an exertion is the hand "holding, manipulating, triggering, pushing,
  pulling or otherwise handling an object"; recovery is "when the hand was completely idle,
  resting upon an object for voluntary support, moving freely or reaching for an object".
  **This is the sentence that decides `docs/RED-TEAM.md` A3**: the TLV's own operational
  definition of exertion is *handling an object*, which is what the vendor's "hands working
  on a workpiece" label approximates. Idle grip for support is recovery under both.
- **Golden cells** (their Table 3, one decimal): F=0.5, D 20–40 → 4.0; F=0.5, D 40–60 →
  4.5; F=0.5, D 60–80 → 4.9; F=0.5, D 80–100 → 5.2; F=1.0, D 60–80 → 6.7; F=1.0,
  D 80–100 → 7.1; F=1.5, D 60–80 → 7.4; F=1.5, D 80–100 → 7.8; F=0.25, D 20–40 → 2.4;
  F=0.125, D 0–20 → 0.8. Tests evaluate the equation at cell mid-points and must land
  within the paper's residual SD of the cell value.
- **`scale_rev = "radwin-2015-freq-dc"`**, and every `HALScore` records that it is a
  regression fit to the ACGIH 2001 table, not the table itself.

Also opened: Akkas, Azari, Chen, Hu, Ulin, Armstrong, Radwin, *A hand speed–duty cycle
equation for estimating the ACGIH hand activity level rating*, *Ergonomics* 58(2):184–194,
2015. PMID 25343278, PMC4664886. Read in full.

- **Equation:** `HAL = 10 · σ(−15.87 + 0.02·D + 2.25·ln S)`, σ the logistic function, S the
  RMS hand speed in **mm/s**, D in percent. Validation on 30 tasks: slope 0.99, R² 0.99,
  MSE 0.16. Data range S 255–1288 mm/s, D 11–100%.
- **Normalisation:** pixel speed is converted to mm/s using **hand breadth** as the scale
  (population means 90.4 mm male, 79.5 mm female; CoV 0.046/0.048). This is the scale
  cyclegraph must reproduce: a hand-box width in pixels against a hand breadth in mm.
- **`scale_rev = "akkas-2015-speed-dc"`.**

**The "purchase required" blocker in the prior RUBRIC and METHOD text was wrong.** The
ACGIH document remains the authority, but two peer-reviewed, open equations fitted to its
table exist, and the residual of each is published. `docs/DECISIONS.md` D013.

## S4 — Published HAL distributions for comparable work. **Resolved.** `[V]`

- Kapellusch et al., pooled prospective CTS cohort, six research groups, 2,751 workers from
  54 predominantly manufacturing and service companies in ten US states (PMC4251712).
  Baseline **HAL mean 4.3, SD 1.9, range 0–10**; peak force mean 2.9 (SD 1.7); TLV-for-HAL
  score mean 0.63. Categories: 55.3% below the Action Limit, 18.6% between AL and TLV,
  26.1% above TLV. Females 4.5 vs males 4.2.
- Latko et al. 1997's 33 rated jobs (reproduced in Radwin 2015 Table 2): HAL median 6.0,
  range 0.6–8.5, duty-cycle median 74%, frequency median 0.74/s. Appliance, auto
  components, fibre drum, glass, office furniture manufacturing.
- Garg et al. 2012 (PMID 22397385): 536 workers, 10 manufacturing facilities; abstract
  reports no HAL distribution. Contributes to the pooled cohort above.

**Number for H3, fixed here for the v1.1.0 amendment:** corpus median HAL inside
**[2.4, 6.2]** — the pooled-cohort mean ± 1 SD. Latko's range is too wide to falsify
anything. The pre-existing SURVEY claim that a range existed "in the literature" was `[S]`
and had no number in it; it now does.

## S5 — Do the patents read on this method? **No.** `[V]`

- **US 12,020,193 B1** (VelocityEHS, filed 2023-08-29, granted 2024-06-25), *Vision-based
  hand grip recognition method and system for industrial ergonomics risk identification*.
  Claim 1 requires: identify hand grips **and** wrist bending, **determine a hand grip type**,
  **obtain hand grip force information**, compute percent maximum strength, then frequency
  and duration of each grip and each wrist bend. Grip-type classification and force are
  mandatory elements. Duty cycle or exertion frequency from a per-frame binary manipulation
  label alone, with no grip type and no force, is not within the claim.
- **US 12,361,359** — continuation with the same title; same claim structure by inspection
  of the USPTO full-text listing. `[V]`
- **US 12,511,929 B1** (VelocityEHS, granted 2025-12-30), *Vision-based three-dimensional
  human pose estimation system and method for ergonomic risk assessment*. Claim 1 requires
  whole-body 2D→3D pose, joint angles, per-joint posture scores. No HAL, duty cycle or
  exertion frequency. Not camera-orientation constrained, but whole-body pose is not
  recoverable from a head-mounted camera in any case (D003).
- **US 12,380,392** (VelocityEHS), *Automated industrial ergonomics risk root cause
  identification and management* — multi-stage CNN over body regions with a colour-coded
  UI. Body-region posture; no hand-activity measure.

This is a disclosure, not legal advice. Nothing here is a freedom-to-operate opinion.

## S6 — Is "every published system is third-person" true? **For everything opened, yes.** `[V]`

S1 and S2 together. Every system that scores an ergonomic index from video and could be
opened uses a fixed, external camera, and the two indices they score (RULA/REBA) are
undefined from the egocentric viewpoint. The one egocentric hand-use system found is
rehabilitation, not ergonomics. Two reviews could not be opened and are not relied on.

## What the gate changed

| Claim before the gate | After |
|---|---|
| "The HAL mapping needs the purchased TLV" | Wrong. Two open equations with published residuals. D013 |
| "Every video-ergonomics system is third-person" | True for every system opened; stated with evidence, two reviews unopened |
| "Egocentric hand-activity is empty" | Egocentric *ergonomics* is empty; egocentric duty-cycle-like measurement exists in rehab |
| "HAL from video" as part of the contribution | Not the contribution. Published since 2013. The contribution is the reading of the vendor metric |
| H3 "published range" | Now a number: [2.4, 6.2] |
| A3 unresolved | Substantially answered: the TLV's own definition of exertion is "handling an object". Still carried as OPEN until the pilot's judge labels are read against it |

## Ideas checked and abandoned before arriving here

Recorded in `docs/LINEAGE.md` so the route is visible. All remain `[S]`; none is load-bearing
on anything in this project because none is a claim this project makes.

## Stop condition

Not triggered. If a later source shows egocentric HAL already published, the correct action
is to record it here, dated, and re-scope.
