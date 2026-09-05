# Handoff

The resume point. A fresh session should be able to continue from this file without
re-deriving anything.

**Last updated: 2026-09-05 — W0 complete. Documentation frozen, no code. W1's novelty gate
is the next thing and it blocks everything.**

## Do not do

- **Do not edit `docs/PRE-REGISTRATION.md`.** It is hashed in
  `docs/PRE-REGISTRATION.sha256`. Supersede with a dated `docs/DECISIONS.md` entry carrying
  a reversal clause, then apply in place and append an `## Amendments` entry.
- **Do not write a `HALScore`** until `docs/SURVEY.md` S3 resolves the scale mapping from
  the primary standard. `make hal` is meant to fail. An approximate mapping would produce
  numbers that look like HAL and are wrong by an offset nothing downstream could detect.
- **Do not treat an unresolvable clip as zero frequency.** It is `status: "no_peak"`,
  counted and excluded. This is the largest single way the pipeline could understate
  exposure.
- **Do not emit a per-worker or per-factory number,** in code, in a notebook, or in a
  message. `CONTRACTS.md`'s `ExposureAggregate` cannot carry one; do not work around it.
- **Do not scale the cheap labeller past the pilot before H1 passes.** 30 million frames of
  a known-biased label is not a dataset, it is a committed error.
- **Do not cite a paper tagged `[S]`** as though it were established. Open it, then re-tag.

## State

| | |
|---|---|
| Docs | Frozen. 19 files under `docs/`, spine complete |
| `PRE-REGISTRATION.sha256` | Committed |
| Code | None. `src/cyclegraph/` is a `.gitkeep` |
| Novelty gate | **Not run.** `docs/SURVEY.md` S1–S6 all open |
| Corpus access | Inherited from `../vernier`; a gated HF token with accepted terms is required |
| HAL scale | **Blocked** on obtaining the ACGIH TLV documentation. S3 |
| Expert anchor | **None, and none expected.** `docs/DECISIONS.md` D009 |

## The next three things

1. **Run `docs/SURVEY.md`.** S1, S2 and S6 decide whether the project exists. S3 and S4
   are inputs it cannot run without. One literature pass resolves all of them.
2. **Obtain the ACGIH TLV documentation.** Everything from E6 onward is blocked on it, and
   it is a purchase rather than a research problem.
3. **Write `scripts/validate.py`.** The gates are currently described and not enforced;
   `make check-claims` calls a script that does not exist yet, which is declared in
   `PLANNED-PATHS.txt` and is the first thing W2 closes.

## Open questions, each with its resolving trigger

| Question | Resolves when |
|---|---|
| Which HAL scale edition and mapping | The TLV documentation is obtained (S3) |
| What HAL distributions are published for comparable work | The occupational-health literature pass (S4) |
| Whether EPIC-KITCHENS-100 is reachable for the negative control | Its institutional-email requirement is met, or Ego4D carries the control alone and the weaker control is reported as such |
| Whether the pilot factory is degenerate | The manifest is built and its task and worker spread inspected (D012) |
| Whether the vendor's manipulation label and the TLV's duty cycle are the same construct | S2 and S3. This is `docs/RED-TEAM.md` A3 and it is fatal if it fails |
