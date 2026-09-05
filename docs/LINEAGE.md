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
standards' own vocabulary, and `docs/SURVEY.md` records that every claim about them is
currently `[S]`.

The reframe that makes this viewpoint workable — hand-and-wrist standards instead of
whole-body RULA/REBA — is a choice, not a discovery. It is available to anyone who notices
that a head-mounted camera cannot see a trunk.

## From `vernier` — the corpus, the machinery, and two limits

`../vernier` is the sibling that audits the same vendor's quality claim on the same corpus.

| From | What | Where it lands |
|---|---|---|
| `../vernier/docs/DECISIONS.md` | The raw-corpus access path: one frame out of an mp4 inside a tar over HTTP range requests, via ffmpeg's `subfile` protocol | `corpus` module, E2 |
| `../vernier/docs/UPSTREAM-FINDINGS.md` | That the evaluation release's `frame_id` carries no clip linkage, so only the raw release can support this | D011 |
| `../vernier/src/vernier/estimation/bootstrap.py` | Cluster bootstrap over a grouping variable | `estimation` module, H5 |
| `../vernier/docs/DECISIONS.md` | The design-effect threshold ambiguity — "a design effect of 2" versus "twice the width" — which made that project's equivalent hypothesis unfalsifiable as written | H5 states both readings in one sentence |
| `../vernier/docs/COVERAGE.md` | That the vendor's manipulation figure reproduced within tolerance while its 2-hands figure did not | `docs/RED-TEAM.md` A1 |
| `../vernier/docs/DECISIONS.md` | The rung-1 probe and its published failure at 0.693 fidelity against a 0.8 target | E3's choice of labeller, and the reason H1 exists |
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
follows from the observation. `docs/SURVEY.md` gates whether even that survives contact with
the literature, and it has not yet been run.

## Ideas checked and abandoned before arriving here

Recorded so the route is visible, and so nobody repeats the search. All findings `[S]`.

| Idea | Why abandoned |
|---|---|
| Blender-rendered synthetic egocentric hands for judge auditing | HOI-Synth (ECCV 2024), BEDLAM, RenderIH, AnyHand |
| Human→robot embodiment retargeting of the corpus | Ego2Robot: 18,561 hours across 15 morphologies, ~1 month old at time of search |
| Metamorphic counterfactual testing of the judge | MetaRA, and DeepBackground for the background arm |
| Virtual camera rotation as an exact counterfactual | Fisheye sphere-rotation reprojection already published as segmentation augmentation |
| 85 factories as a natural domain-generalization benchmark | Not abandoned — deferred. Cheap, and orthogonal to this |
