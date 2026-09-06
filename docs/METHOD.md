# Method

The protocol, stage by stage, with the cost of each. Cost is published because a check
nobody can afford is not a check — the convention is inherited from `../assay/docs/METHOD.md`.

**Every figure in the cost column is an estimate under stated assumptions, not a
measurement**, except where it cites a sibling's measured rate. They are replaced with
measured values as each stage runs, and the assumption is named so a reader can see which
way an error would run.

## Scale, first, because it determines the method

One factory is roughly 2,270 clips (192,903 ÷ 85). At a mean clip duration near 187 s and
the pre-registered 4 Hz analysis rate, that is **~1.7 million sample instants for the pilot
factory alone**, each a frame pair. The 40,000-clip Arm A main draw is **~30 million**.

This rules out labelling every frame with a VLM judge, at any price. The method that follows
is shaped by that arithmetic rather than by preference, and the consequence is a real
weakness recorded in `docs/RED-TEAM.md` A1.

## E1 — Clip manifest

Enumerate clips for the pilot factory from the shard index and the per-clip metadata the
release ships. No decode. Emits `ClipRef`.

**Cost:** negligible; HTTP range reads of shard indices only. `vernier` indexed the whole
16 TB corpus moving ~150 MB.
**Gate:** clip count and total duration reconcile against the published per-factory figures.

## E2 — Frame extraction

Decode at 4 Hz via ffmpeg's `subfile` protocol over HTTP range requests — a frame out of an
mp4 inside a tar without downloading the shard, established in `../vernier/docs/DECISIONS.md`.
Each sample is a **pair** (t, t + 1/fps) so the speed path has a flow baseline; decode is
sequential either way, so the pair roughly doubles frames written, not frames decoded.

**Cost:** ~1.7M pairs for the pilot, network-bound rather than compute-bound. `vernier`
measured 1.93 s for a cold single-frame seek, which is the per-clip overhead and the reason
this stage decodes whole clips sequentially rather than seeking per instant
(`docs/DECISIONS.md` D023 and `src/cyclegraph/corpus/decode.py`). The 3–6 hour estimate stands
and is not yet replaced by a measured full-pilot figure.
**Gate:** decode failure rate below 1% **per pair**, with the per-clip rate reported beside it
(`docs/DECISIONS.md` D023), and failures recorded as `decode_failed` rather than dropped.
**Measured:** the open-failure rate over every clip in the pilot manifest is 0.0000% per pair
and per clip, and truncation over a seeded full-decode sample is 0.0069% per pair
(`results/decode_probe.json`). The gate passes.

## E3 — Labelling and hand localisation

**Manipulation label, two sources.** The primary label source is a **cheap probe** — frozen
backbone features plus a linear head, the shape `vernier` built and published as a negative
result: teacher fidelity 0.6933 against a pre-registered ≥0.90, with the agreement floor met
(0.8421 against ≥0.80) only by abstaining on 60% of frames (`../vernier/docs/DECISIONS.md`,
D061 result table). An earlier version of this sentence conflated the two rows as "0.693
against 0.8"; corrected 2026-09-05. Those numbers are a warning, not a licence: they are why
H1 exists. The **judge** runs on a stratified calibration subset only, sized so that H1's
cross-source comparison is powered, not on the full corpus.

**Hand boxes.** **EgoHOS** (Zhang et al., ECCV 2022) on every sampled frame; box width
recorded. It replaces 100DOH, which this section named until 2026-09-06 and which cannot be
run by anyone: both Google Drive links its authors publish return 404 and no mirror exists
(`docs/DECISIONS.md` D037, re-probed against a live EgoHOS control). That is **not** the
trigger this section anticipated — EgoHOS was named the fallback "if 100DOH's coverage fails
H2c", and coverage has never been measured — so the switch is its own decision, D047, with its
own cost. EgoHOS is a segmenter, so `docs/RUBRIC.md` v1.4.0 defines the box: the axis-aligned
bounding box of a hand's mask pixels, hand classes only. The offset between that and a
human-annotated detector box is systematic, linear in mm/s, and unmeasurable while 100DOH
cannot be run; it is arithmetically identical to a change in `hand_breadth_mm`, so
`docs/BENCHMARK.md`'s 79.5/90.4 rows already bound it to about ±6%, and `docs/COVERAGE.md`
carries the remainder as a gap.

Frames reach the detector in **colour**. This stage decoded grey and the adapter replicated it
across three channels, which is a grey image in a colour tensor — the same substitution D040
measured on the labeller, latent here because no detector had ever run.

**Hand speed.** Dense optical flow on each pair (Farneback on CPU, or RAFT-small on GPU if
the CPU rate is too slow); ego-motion as the median flow over the mask complement;
residual RMS inside the box; scaled by the clip's median box width against 85 mm
(`docs/RUBRIC.md`). Emits `HandSpeedEstimate`.

**Cost:** **measured 2026-09-06.** The pilot factory is **97 clips and 462,437 sampled
instants** — the ~1.7M frames this line previously estimated was high by roughly a factor of
four. The probe ran at **13.2–13.6 frames/s per worker**, four workers on one `g5.2xlarge`
(A10G, 8 vCPU, 32 GB), so ~53 frames/s aggregate.

**The GPU was idle at 0% throughout, and that is the finding.** The stage is bounded by ffmpeg
decode and per-frame preprocessing, not by the backbone: DINOv2-small over a 384-dim head is
negligible beside decoding colour frames at 960×540. The same labeller on an Apple Silicon
laptop's MPS ran at **45–49 frames/s in a single process** — comparable to four workers on the
paid instance, at no cost. `docs/REPRODUCTION.md` names a GPU stage for E3; for the *labeller*
that is the wrong shape of machine, and a reader reproducing this should not rent one for it.
The detector, when there is one, is a different question and unmeasured.

Two costs that are not throughput. Colour frames are three times grey, and a 1200 s clip
buffered whole is **7.5 GB**; four workers of that exhausted 32 GB, drove the box into swap and
had two workers OOM-killed before the decode was streamed (`docs/DECISIONS.md` D043). And the
first full pass lost **1.1385%** of planned samples to three clips whose HTTPS reads ended
mid-stream while ffmpeg still exited 0 — above E2's 1% ceiling, invisible to every check until
one was written for it. Re-decoding those three brought the run to 462,437 of 462,437. Judge on a
calibration subset of ~20,000 frames: `vernier` paid **$9.06** and ~10–11 h for 10,000
frames with two prompt variants (D066's estimate was $8.56; the real invoice is the number
that counts), so ~$9 and ~10 h for one variant here. Detector ~1.7M
frames at ~20 frames/s on one GPU ≈ 24 GPU-hours, the largest single cost in the pilot.
Flow: **decided, both arms measured** (`docs/DECISIONS.md` D059). At the pair D045 defines and
the 960x540 D050 chose, over 200 real pilot pairs: Farneback **7.57 pairs/s** on CPU, RAFT-small
**21.5 pairs/s** on an A10G, both with a flow-null rate of 0.000. **Farneback is chosen**, on
D024's cost rule — it needs no GPU and parallelises across processes, pricing the pilot at
roughly $2 against RAFT's $6 — and on the A14 column, where RAFT's residual falls *below* the
exact-geometry floor and Farneback's sits above it. The earlier 116.9 pairs/s figure was
measured at 480x270 over the 0.25 s pair both of those decisions replaced and is not comparable.
**Gate:** H1. If duty cycle is not stable across the two sources within 0.05 mean absolute
difference, the probe cannot carry the corpus. The method does not scale a known-biased
labeller to 30M frames; it takes **Arm B** of the pre-registered two-arm draw — judge-only,
200 clips (≈150,000 frames, ≈$68 at `vernier`'s paid rate; D020 corrects D018's $65), with H4 and H5 reported
`UNTESTED` (`docs/DECISIONS.md` D018). And H2c: detector coverage ≥60%, flow-null ≤10%.

## E4 — Duty cycle

Mean of the manipulation series over scored frames, per clip. No smoothing.

**Cost:** negligible.
**Gate:** H1's sampling-rate arm — 4 Hz against 8 Hz on a subsample, within 0.02.

## E5 — Frequency axis

**Primary: RMS hand speed** from E3. **Cross-check: spectral bout frequency** over the
manipulation series, with transition-counting at the 0.5 s debounce as its own cross-check.
Bout frequency is a lower bound on exertion frequency and every record says so
(`docs/DECISIONS.md` D014).

**Cost:** negligible.
**Gate:** H2a and H2b on the spectral path — 20% relative agreement *and* ≥70% resolvable.
The second bound is the one that usually goes unreported and it is a stopping condition for
the cross-check, not for the project: the speed path does not depend on resolvability.

## E6 — Hand Activity Level

Map (speed, duty cycle) by `akkas-2015-speed-dc` and (bout frequency, duty cycle) by
`radwin-2015-freq-dc`, each to one decimal, each with `scale_rev` set, each flagged when
its inputs fall outside the fitted range. Both are peer-reviewed regression fits to the
ACGIH 2001 table with published residuals (`docs/SURVEY.md` S3). No approximation of this
project's own is ever used; `make hal` refuses any mapping not in the enum.

**Cost:** negligible.
**Gate:** golden tests against the papers' Table 3 cells pass within the residual.

## E7 — Negative control

The same pipeline on two non-factory egocentric corpora, each testing a different axis
because their manipulation prevalences differ (`docs/DECISIONS.md` D016).

**Ego4D — duty-cycle control:** factory − Ego4D duty-cycle gap ≥0.25 and HAL gap ≥1.0.
**EPIC-KITCHENS-100 — frequency control:** factory − EPIC speed-path HAL gap ≥0.5, spectral
gap reported beside it. This is the test of `docs/RED-TEAM.md` A4 and A11: kitchens have
head motion too.

**Cost:** small; both are already accessible to the sibling project, subject to
EPIC-KITCHENS' institutional-email requirement, which `../vernier/docs/COVERAGE.md` records
as unmet. If it stays unmet, the frequency control is `UNTESTED` in those words and A4/A11
stay OPEN.
**Gate:** every pre-committed gap. **This runs before E8.** A pipeline that cannot
distinguish factory work from kitchen work has not measured repetition, and its
distribution is not worth comparing to anything.

## E8 — Aggregation, strata and the design effect

Cluster bootstrap over `factory_id/worker_id`, B = 10,000, seeded, with the iid interval
beside it for contrast and both design-effect readings printed. Variance decomposition for
H4. Comparison against [2.4, 6.2] for H3. Size-tercile strata computed and published only
above the D019 floor, suppressed rows printed as suppressed. Sensitivity table for hand
breadth, ego-motion subtraction and the A14 translation floor.

**Cost:** minutes.
**Gate:** H3, H4, H5. H3 is labelled a plausibility check in every place it appears. H4 and
H5 read `UNTESTED` under Arm B.

## E9 — The card

`make card` regenerates `MEASUREMENT_CARD.json` from `results/`. Verdict is `NOT_VERIFIED`
while any gap in `docs/COVERAGE.md` is open, which in v1 is by construction. No pilot value
and no identifier reaches it; `scripts/validate.py` checks the second.

## What is not in the protocol

No rendering, no synthetic data beyond the A14 golden sequences, no body-pose estimation
(hand *detection* yes, pose no), no per-cycle metric, no force, no per-worker or
per-factory number, no pilot value, no site self-run tool, and no full-corpus decode.
