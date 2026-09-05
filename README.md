# cyclegraph

**A dataset vendor's quality metric is, dimensionally, an occupational-exposure metric.
This measures what happens when you read it that way.**

Build AI sells 10,000 hours of egocentric factory video and publishes a per-frame quality
figure: what fraction of frames show *active manipulation* — hands visibly working on a
workpiece. The number is sold as data quality. Buyers read it as data quality. The
computer-vision literature reads it as data quality.

It is also **duty cycle**: the fraction of time a worker's hands are exerting. Duty cycle is
a primary input to the **ACGIH TLV for Hand Activity Level**, the occupational-health
standard for repetitive hand work — the standard whose whole purpose is predicting
musculoskeletal injury on exactly this kind of job.

Nobody has read it that way, because the two communities do not share a corpus.

## Why this viewpoint is empty, and it is not because nobody thought of it

Automated ergonomic assessment from video is a mature field with commercial patents behind
it. Every published system is **third-person**. That is not an accident of fashion: RULA and
REBA — the standard indices — score trunk, neck and legs, and a head-mounted camera never
sees a trunk. Egocentric ergonomics is empty because the standard instruments are ill-posed
from that viewpoint.

The hand-and-wrist standards are not. HAL, the Strain Index and OCRA were built for
repetitive manufacturing work and score what an egocentric camera does see: exertion
frequency, duty cycle, wrist posture. `docs/SURVEY.md` runs the novelty gate on this claim
and nothing downstream proceeds until it passes.

## What this cannot do, said first

**There is no certified ergonomist in this project.** No expert scored a sample, so there is
no agreement statistic, and cyclegraph cannot claim it measures Hand Activity Level
*accurately*. That gap is the largest thing wrong with this work and it is not closed by
anything below.

**Peak force is not observable from video.** The full TLV needs it. cyclegraph computes the
HAL axis and reports the force axis as absent, never estimated. `docs/COVERAGE.md`
enumerates every TLV input and marks each one.

So the honest description is: an argument, an instrument, a distribution at unprecedented
scale, and a set of internally verifiable results — not a validated occupational-health
finding. `MEASUREMENT_CARD.json` carries `verdict: NOT_VERIFIED` until that changes.

## What it does claim

| | |
|---|---|
| **The argument** | A published per-frame quality statistic is dimensionally an exposure primitive. Checkable by inspection, not by experiment. |
| **The instrument** | Duty cycle and exertion frequency recovered from egocentric video with no new annotation. Frequency comes from spectral estimation over the manipulation signal, so no exertion has to be hand-segmented. |
| **The distribution** | HAL across 85 factories and 2,153 workers. Reported at corpus level only. |
| **The verifiable results** | Spectral frequency against transition-counting; test-retest; variance decomposition; the design effect on clustered estimates. None needs external ground truth. |

## What is measured is people, and that decides the reporting

The corpus is recordings of identifiable workers whose consent instrument is not published.
Consent for AI-training data collection is not consent for occupational-health assessment.

**Nothing is reported at a unit any person or site could be identified by.** Worker and
factory identifiers are variance units — they are load-bearing for every interval, because
clips from one worker are not independent observations — and they never appear in a result.
The same pipeline that flags injury risk also yields worker-productivity surveillance; the
aggregation floor is what separates them, and it is enforced at a module seam rather than by
intention. `docs/ETHICS.md` states the basis, and states why suppressing the work would not
be neutral either.

## Status

**Documentation frozen; no code.** `docs/PRE-REGISTRATION.md` and `docs/RUBRIC.md` are
committed before `src/` exists, and git history is the evidence of that ordering. A project
built on the argument that unvalidated measurements get published without protocols does not
get to improvise its own.

`docs/SURVEY.md`'s novelty gate has not been run to completion. Every literature claim in
this repository is tagged `[S]` — sourced from a search summary, not from opening the paper
— and none of it is load-bearing until it is opened and re-tagged `[V]`.

## Map

| | |
|---|---|
| What is committed before any result is seen | `docs/PRE-REGISTRATION.md` |
| The literature, and the novelty gate that stops the project | `docs/SURVEY.md` |
| Operational definitions the standards leave open | `docs/RUBRIC.md` |
| The protocol, stage by stage, with its cost | `docs/METHOD.md` |
| Every TLV input, and which are unobservable | `docs/COVERAGE.md` |
| Attacks on cyclegraph's own findings | `docs/RED-TEAM.md` |
| Why this measures people, and what that forbids | `docs/ETHICS.md` |
| Module boundaries and their seams | `docs/ARCHITECTURE.md` |
| Every record schema | `CONTRACTS.md` |
| Reproducing all of it | `docs/REPRODUCTION.md` |
| What is inherited, and from where | `docs/LINEAGE.md` |
| Decisions and what would reverse them | `docs/DECISIONS.md` |
| Where the work stands | `docs/HANDOFF.md` |

Apache-2.0.
