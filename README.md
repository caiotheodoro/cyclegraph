# cyclegraph

**A dataset vendor's quality metric is, dimensionally, an occupational-exposure metric.
This measures what happens when you read it that way.** The corpus measurement is blocked on
cost; what has shipped is the instrument check, and it found that dense optical flow inside a
hand box stops reporting the hand well before anyone would notice — the
[flow-gain result](writing/flow-is-not-hand-speed.md), reproducible with no corpus, no token
and no GPU.

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
it, and HAL specifically has been recovered from video by one lab since 2013. Every system
that could be opened is **third-person**. That is not an accident of fashion: RULA and REBA
— the whole-body indices — score trunk, neck and legs, and a head-mounted camera never sees
a trunk. Egocentric ergonomics is empty because the standard instruments are ill-posed from
that viewpoint.

The hand-and-wrist standards are not. HAL, the Strain Index and OCRA were built for
repetitive manufacturing work and score what an egocentric camera does see. `docs/SURVEY.md`
ran the novelty gate on this claim on 2026-09-05 and it cleared, narrowly: the instrument is
not new, the reading of the vendor's number is.

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
| **The instrument** | Borrowed, not built: the Radwin lab's published speed–duty-cycle and frequency–duty-cycle HAL equations, fed from egocentric video with no new annotation. Hand speed from optical flow inside detected hand boxes, ego-motion subtracted; spectral bout frequency as a cross-check and a stated lower bound. |
| **The distribution** | HAL across 85 factories and 2,144 workers (2,153 published; `../vernier/docs/UPSTREAM-FINDINGS.md` F12). Reported at corpus level and, where a k-anonymity floor is cleared, by factory-size tercile. Nothing finer. |
| **The verifiable results** | Two label sources against each other; two sampling rates; spectral frequency against transition-counting; hand-box coverage and flow-failure rates; two negative controls on two corpora; variance decomposition; the design effect on clustered estimates. None needs external ground truth, and the evals card says so. |

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

**Pre-registration v1.5.0; rubric v1.5.0; contracts v1.5; W2 landed and reviewed (D020);
W3's code landed and its corpus gates passed; W9 published the synthetic instrument work
(D071).** The clip manifest reconciles against two independent scans and
confirms the vendor's published worker count is nine too high (`docs/DECISIONS.md` D027); the
A14 residual floor is measured and published as a motion budget that is tighter than ordinary
head movement (D026). No exposure number exists yet: the hand detector and the manipulation
labeller have not run, and nothing substitutes for them. `docs/PRE-REGISTRATION.md` and
`docs/RUBRIC.md` were committed before `src/` existed, and git history is the evidence of that
ordering — checked by ancestry in `scripts/validate.py`, not by timestamp. Every amendment
since quotes the sentence it replaced and cites a decision with a reversal clause; the gate
checks that too. A project built on the argument that unvalidated measurements get published
without protocols does not get to improvise its own.

`docs/SURVEY.md`'s novelty gate ran on 2026-09-05 and cleared, narrowly: HAL from video is
published since 2013, always third-person; no egocentric system scores it. Two reviews could
not be opened and stay `[S]`; nothing rests on them.

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
| What is blocked, and on what | `docs/BLOCKED.md` |
| The flow-gain benchmark, and what it cannot tell you | `docs/BENCHMARK_CARD.md` |
| The essay | `writing/flow-is-not-hand-speed.md` |
| The published dataset and harness | [huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain](https://huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain) |
| The Space, with the quiver panels and the gain curve | [huggingface.co/spaces/caiotheodoro/cyclegraph](https://huggingface.co/spaces/caiotheodoro/cyclegraph) |

**What the release deliberately withholds**, and each for its own reason: every pilot value
(D018); `results/decode_probe.json`, whose rates are over pilot-factory clips; and the
manipulation probe, because `docs/MODEL_CARD.md` says no model ships and because nothing in
either repository states whether `../vernier`'s judge labels may be redistributed. No
permission and no prohibition is an open question, not a licence. `docs/DECISIONS.md` D071.

Apache-2.0.
