# cyclegraph — orientation for agents and reviewers

`README.md` is the argument. This file is the operating rules.

cyclegraph reads a dataset vendor's per-frame quality metric as an occupational-exposure
primitive, and measures the corpus that way. The corpus is `builddotai/Egocentric-10K`:
10,000 hours, 2,153 workers published and 2,144 shipped (`../vernier/docs/UPSTREAM-FINDINGS.md`
F12), 85 factories, 192,903 clips.

**Current state (2026-09-05):** W1 cleared, pre-registration v1.2.0, contracts v1.2, W2
landed (models, the two HAL equations, the bootstrap), fresh-context review recorded as
D020. `docs/SURVEY.md`'s two unopened reviews stay `[S]` and load-bearing on nothing.

## The claim

Build AI's *active manipulation* figure is duty cycle. Duty cycle is a primary input to the
ACGIH TLV for Hand Activity Level. Read that way, the corpus is the largest automated
hand-activity dataset assembled — and no ergonomics work has read it, because every
published video-ergonomics system is third-person and RULA/REBA are ill-posed from a
head-mounted camera.

## Rules in force from the first commit

**1. Pre-registration is binding.** `docs/PRE-REGISTRATION.md` is never edited. A change
after the freeze is a dated `docs/DECISIONS.md` entry carrying a reversal clause, plus an
`## Amendments` entry quoting the prior value. A deviation recorded is a limitation; a
deviation unrecorded is misconduct.

**2. No transcribed numbers.** Every figure in prose cites the file that produces it. This
applies to `MEASUREMENT_CARD.json` and to any generated card equally.

**3. Nothing is reported at an identifiable unit or below the floor.** Worker and factory
are variance units, never reporting units; the only unit between corpus and nothing is a
factory-size tercile that clears the D019 k-anonymity floor. This is not a preference —
`docs/ETHICS.md` is the reason, and `docs/ARCHITECTURE.md` names the seam where it would
leak. A module that can emit a per-worker, per-factory or sub-floor number is a defect
regardless of whether anything calls it. Pilot values never leave `results/`.

**4. Unobservable inputs are reported absent, never estimated.** Peak force cannot be read
from video. A plausible-looking imputation would convert a stated gap into a hidden error,
and the TLV would then be wrong in a direction nobody could audit.

**5. Literature claims carry `[V]` or `[S]`.** `[V]` means the primary source was opened.
`[S]` means a search summary only, and `[S]` is never load-bearing. vernier's survey
recorded a claim that dissolved on contact with the paper; the tag is what caught it.

**6. `docs/private/` never leaves the machine.** Run `make privacy-gate` before any commit.

## What is deliberately published as a weakness

- **No expert agreement statistic.** No ergonomist scored a sample. The instrument is
  unvalidated against professional assessment and says so in the README, not a footnote.
- **Peak force absent**, so the full TLV is never computed — only its HAL axis.
- **Plausibility is not agreement.** Comparison against published HAL distributions is
  directional evidence and is labelled as such wherever it appears.
- **Both frequency-axis inputs are proxies.** Spectral frequency is bout frequency, a lower
  bound on exertion frequency; hand speed is optical flow after ego-motion subtraction, with
  the failure modes `docs/RED-TEAM.md` A11/A14/A15 name.
- **One vendor, one corpus, one modality.**

## Order of work

`docs/SURVEY.md` gated everything and cleared on 2026-09-05. `docs/PRE-REGISTRATION.md` is
at v1.1.0. Next: W2 (`CONTRACTS.md` in code, three isolated commits) → `make manifest` →
`make signal` → `make cycles` → `make hal` → `make estimate` → `make card`.

`docs/WAVES.md` carries the ordering constraints that are not negotiable.

## Verify

```
make validate
```

## Map

| | |
|---|---|
| What is committed before any result is seen | `docs/PRE-REGISTRATION.md` |
| The literature, and the novelty gate | `docs/SURVEY.md` |
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
