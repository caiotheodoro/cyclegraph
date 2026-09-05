# cyclegraph — orientation for agents and reviewers

`README.md` is the argument. This file is the operating rules.

cyclegraph reads a dataset vendor's per-frame quality metric as an occupational-exposure
primitive, and measures the corpus that way. The corpus is `builddotai/Egocentric-10K`:
10,000 hours, 2,153 workers, 85 factories, 192,903 clips.

**Current state (2026-09-05):** documentation frozen, no code. `docs/SURVEY.md`'s novelty
gate has not been run to completion, and it gates everything. Every literature claim in this
repository is `[S]` — search summary, not opened — and load-bearing on nothing.

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

**3. Nothing is reported at an identifiable unit.** Worker and factory are variance units,
never reporting units. This is not a preference — `docs/ETHICS.md` is the reason, and
`docs/ARCHITECTURE.md` names the seam where it would leak. A module that can emit a
per-worker or per-factory number is a defect regardless of whether anything calls it.

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
- **One vendor, one corpus, one modality.**

## Order of work

`docs/SURVEY.md` gates everything. If automated hand-activity assessment from egocentric
video is already published, stop and re-scope — a redundant result is worth less than the
honesty of noticing.

Then: freeze `docs/PRE-REGISTRATION.md` → `make manifest` → `make signal` → `make cycles`
→ `make hal` → `make estimate` → `make card`.

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
