# Lineage

What cyclegraph inherits, from where, and what is new. Written so no idea here is presented
as more original than it is.

## From Gilbreth — the instrument and the name

Frank and Lillian Gilbreth's **cyclegraph** (c.1913) fixed a small lamp to a worker's hand
and photographed the work at long exposure; the developed plate showed the path of one work
cycle as a light trace. The **chronocyclegraph** interrupted the lamp at a known rate so the
trace carried timing as well as shape.

That is this project's ancestor, precisely: measurement of repetitive hand work in a factory
by recording the hand's own motion. cyclegraph does it from the hand's point of view rather
than from across the room, and at 10,000 hours rather than one operator, but the question is
the Gilbreths' question. The name is not decoration; `docs/DECISIONS.md` D002 records it.

## From occupational health — the index

The ACGIH TLV for Hand Activity Level, the Strain Index (Moore & Garg) and OCRA are not this
project's instruments and nothing about them is claimed as new. cyclegraph computes one axis
of the first and reports the rest as unobservable. `docs/COVERAGE.md` states which, in the
standards' own vocabulary; the TLV's inputs are `[V]` through Radwin 2015's reproduction,
the Strain Index and OCRA remain `[S]` with the reason stated there.

The reframe that makes this viewpoint workable — hand-and-wrist standards instead of
whole-body RULA/REBA — is a choice, not a discovery. It is available to anyone who notices
that a head-mounted camera cannot see a trunk.

## From the Radwin lab — the instrument, already built

HAL has been recovered from video by computer vision since 2013 (University of Wisconsin;
`docs/SURVEY.md` S2 lists eight papers). Two of them supply what cyclegraph runs on:

| From | What | Where it lands |
|---|---|---|
| Radwin et al. 2015, *Ergonomics* 58(2):173 | `HAL = 6.56 ln D [F^1.31/(1+3.18F^1.31)]`, fitted to the ACGIH 2001 table, residual SD 1.18 | `exposure` module, `scale_rev = radwin-2015-freq-dc` |
| Akkas et al. 2015, *Ergonomics* 58(2):184 | `HAL = 10 σ(−15.87 + 0.02D + 2.25 ln S)`, S in mm/s via hand breadth, R² 0.99 on validation | `exposure` module, `scale_rev = akkas-2015-speed-dc`; the reason the speed path exists (D014) |
| Radwin 2015 §2 | The TLV's operational definition of exertion — "holding, manipulating, triggering, pushing, pulling or otherwise handling an object" — and of recovery | `docs/RED-TEAM.md` A3's answer |
| Radwin et al. 2026, *Ergonomics* (PMID 40811128) `[S]` — abstract only | Cross-domain RMSE 0.74 HAL points for the best current third-person system | The honest prior for an unvalidated egocentric port; abstract-sourced, so a prior and not a load-bearing number |

Every one of these is a fixed third-person camera. cyclegraph ports the instrument to the
worker's viewpoint; it did not invent it.

## From `vernier` — the corpus, the machinery, and two limits

`../vernier` is the sibling that audits the same vendor's quality claim on the same corpus.

| From | What | Where it lands |
|---|---|---|
| `../vernier/docs/DECISIONS.md` | The raw-corpus access path: one frame out of an mp4 inside a tar over HTTP range requests, via ffmpeg's `subfile` protocol | `corpus` module, E2 |
| `../vernier/docs/UPSTREAM-FINDINGS.md` | That the evaluation release's `frame_id` carries no clip linkage, so only the raw release can support this | D011 |
| `../vernier/src/vernier/estimation/bootstrap.py` | Cluster bootstrap over a grouping variable | `estimation` module, H5 |
| `../vernier/docs/DECISIONS.md` | The design-effect threshold ambiguity — "a design effect of 2" versus "twice the width" — which made that project's equivalent hypothesis unfalsifiable as written | H5 states both readings in one sentence |
| `../vernier/docs/COVERAGE.md` | That the vendor's manipulation figure reproduced within tolerance while its 2-hands figure did not | `docs/RED-TEAM.md` A1 |
| `../vernier/docs/DECISIONS.md` D061 | The rung-1 probe and its published failure: teacher fidelity 0.6933 against ≥0.90, agreement floor 0.8421 against ≥0.80 met only by abstaining on 60% of frames | E3's choice of labeller, and the reason H1 exists |
| `../vernier/docs/ETHICS.md` | The worker-as-cluster-not-subject rule | Extended, and deliberately not inherited — see below |

**What is deliberately not inherited:** `vernier`'s ethics basis. That document disclaims
claims about labour practice, and cyclegraph makes one. `docs/DECISIONS.md` D007 records why
extending it would have damaged both.

## From the workspace — the documentation system

The doc spine, the pre-registration-before-code ordering, `[V]`/`[S]` source tagging, the
red team opened before results, coverage written in someone else's vocabulary, and the
generated-never-transcribed card are all house conventions, developed across `reconforge`,
`assay`, `vernier` and `titer`. None is invented here.

The one-line version those repos share: *a measurement is not a result until you know its
uncertainty.*

## What is new here

One observation, and what follows from it: **a per-frame data-quality statistic published by
a dataset vendor is dimensionally an occupational-exposure primitive.** The instrument
follows from the observation and is borrowed, not built. `docs/SURVEY.md` ran the gate on
2026-09-05 and it cleared, narrowly; the narrowing is recorded there.

## Ideas checked and abandoned before arriving here

Recorded so the route is visible, and so nobody repeats the search. All findings `[S]`.

| Idea | Why abandoned |
|---|---|
| Blender-rendered synthetic egocentric hands for judge auditing | HOI-Synth (ECCV 2024), BEDLAM, RenderIH, AnyHand |
| Human→robot embodiment retargeting of the corpus | Ego2Robot: 18,561 hours across 15 morphologies, ~1 month old at time of search |
| Metamorphic counterfactual testing of the judge | MetaRA, and DeepBackground for the background arm |
| Virtual camera rotation as an exact counterfactual | Fisheye sphere-rotation reprojection already published as segmentation augmentation |
| 85 factories as a natural domain-generalization benchmark | Not abandoned — deferred. Cheap, and orthogonal to this |
