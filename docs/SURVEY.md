# Survey

**The novelty gate.** Nothing downstream runs until this file answers one question:

> *Has automated hand-activity-level assessment from egocentric video been published?*

## Verdict: NOT RUN

Opened 2026-09-05. The seeds below come from a scoping session and **every one is `[S]`** —
sourced from a search summary, not from opening the primary source. `[S]` claims are not
load-bearing anywhere in this project. The gate is not passed until each is opened and
re-tagged `[V]`, or replaced.

The tagging discipline is inherited from `../vernier/docs/SURVEY.md`, where a claim tagged
`[S]` — a paper reported as achieving 91.3% agreement with humans on egocentric video —
dissolved entirely on contact with the source. The base rate for search-summary
mis-attribution in that project was not zero, and there is no reason to think it is zero
here.

## What the scoping session found — all `[S]`, none load-bearing

**Video ergonomics is mature and commercially patented.**

- A systematic review of computer-vision human pose estimation for occupational safety
  (ScienceDirect, 2026). `[S]`
- Validation of computer-vision ergonomic risk assessment tools for real manufacturing
  environments (Scientific Reports, 2024). `[S]`
- Differentiable DULA/DEBA networks reported at >99% replication of RULA/REBA scores. `[S]`
- ErgoExplorer, interactive ergonomic risk assessment from video collections
  (arXiv 2209.05252). `[S]`
- Privacy-preserving mmWave-based automated REBA scoring (arXiv 2607.02611). `[S]`
- VelocityEHS Holdings: four active or pending patents filed 2024–25 covering vision-based
  3D pose estimation and multi-stage CNN risk classification. `[S]`
- Two USPTO patents on vision-based hand grip recognition for industrial ergonomics risk
  identification. `[S]`

**And every one of them is third-person.** That is the observation the project rests on, and
it is the single most important thing to verify: if any of the above operates from a
head-mounted or hand-mounted viewpoint, the gate has not cleared.

**Adjacent egocentric work, occupied.** Synthetic egocentric hand-object data (HOI-Synth,
ECCV 2024; BEDLAM, CVPR 2023; RenderIH; AnyHand). Human-to-robot embodiment retargeting
(Ego2Robot, 18,561 hours across 15 morphologies; EgoVerse; HumanScale). Metamorphic
robustness testing of multimodal LLMs (MetaRA). Fisheye sphere-rotation reprojection as
segmentation augmentation. All `[S]`, all checked during scoping, all found occupied — which
is why the project is here and not there. `docs/LINEAGE.md` records that history so the
route to this question is visible.

## What must be opened before the gate can pass

| # | Question | Resolves by |
|---|---|---|
| S1 | Is any published automated ergonomic assessment system egocentric? | Opening the 2026 systematic review and checking its viewpoint taxonomy |
| S2 | Has HAL, the Strain Index or OCRA been automated from video at all — from any viewpoint? | Direct search of the occupational-health literature, not the CV literature |
| S3 | What is the exact ACGIH HAL scale mapping, and which edition? | Obtaining the TLV documentation. Also the resolving trigger in `docs/RUBRIC.md`; `make hal` is blocked on it |
| S4 | What HAL distributions are published for comparable manufacturing tasks? | The occupational-health literature. H3 has no external comparison without this |
| S5 | Do the two USPTO hand-grip patents and the VelocityEHS filings claim anything this method would read on? | Reading the claims, not the abstracts |
| S6 | Is the "every published system is third-person" claim actually true? | S1 and S2 together |

S3 and S4 are not novelty questions — they are inputs the project cannot run without. They
are listed here because the same literature pass resolves all six.

## The narrowing this project should expect

If the gate clears, the contribution is **not** "we automated ergonomics from video." That
is done and patented. Nor is it "we built a hand-activity classifier."

It is narrower and should be stated narrowly: **a per-frame data-quality statistic published
by a dataset vendor is dimensionally an occupational-exposure primitive, and reading it that
way is possible at corpus scale without new annotation.** The instrument follows from the
observation; the observation is the contribution.

Presenting it as anything wider invites the easy rejection, and the sibling precedent is
explicit that a redundant result is worth less than the honesty of noticing.

## Stop condition

If S1, S2 or S6 shows that egocentric hand-activity assessment is already published, the
correct action is to re-scope, and to record here what was found and when.
