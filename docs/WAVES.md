# Waves

The plan, and the review loop. Each wave ends: build → **fresh-context** review → fix
fan-out → re-verify. A re-read in the same context is not a review.

## Ordering constraints that are not negotiable

- **W0 before `src/`.** Git history is the evidence, and `docs/PRE-REGISTRATION.sha256` pins
  the frozen text.
- **`docs/SURVEY.md`'s novelty gate before W1.** If egocentric hand-activity assessment is
  already published, re-scope. A redundant result is worth less than the honesty of noticing.
- **S3 before E6.** The HAL scale mapping must come from the primary standard. `make hal`
  fails loudly rather than approximating.
- **H1 before the main draw.** If duty cycle is not stable across label sources, the cheap
  labeller cannot carry 30 million frames and scaling it anyway would be knowingly building
  on a biased estimate. H1 failing selects Arm B of the pre-registered two-arm draw
  (`docs/DECISIONS.md` D018); it is not a stop, and it is not an improvised re-plan.
- **The pilot factory is nameable.** Its gates publish pass or fail only; no pilot value
  leaves `results/`.
- **The negative control before H3.** A pipeline that cannot separate factory work from
  kitchen work has not measured repetition, and its distribution is not worth comparing to
  published values.
- **No published number at an identifiable unit, ever.** Not a wave gate — a standing
  constraint, enforced in `CONTRACTS.md` and reviewed at every seam.

## Waves

| | Wave | Exit condition |
|---|---|---|
| **W0** | Frozen docs, no `src/` | `make validate` green on docs gates; `PRE-REGISTRATION.sha256` committed; every cited path resolves or is declared |
| **W1** | Novelty gate | `docs/SURVEY.md` S1–S6 answered, every `[S]` opened and re-tagged, verdict recorded |
| **W2** | `CONTRACTS.md` in code | `src/cyclegraph/models.py` implements every record as a frozen pydantic model with `extra="forbid"`; fixtures generated; `mypy --strict` clean |
| **W3** | `corpus` + `signal` | Pilot factory manifest reconciles against published counts; decode failure rate <1%; `FrameSignal` written for the pilot |
| **W4** | H1 | Duty cycle stable across label sources and sampling rates → Arm A; or H1 reported FAILED and Arm B (judge-only, 200 clips) runs, with H4/H5 `UNTESTED` |
| **W5** | `cycles` + H2 | Spectral and counting agree within 20%; ≥70% resolvable |
| **W6** | Negative control | Median HAL separates factory from non-repetitive corpus by ≥1.0 |
| **W7** | `exposure` + `estimation` | H3, H4, H5 measured with clustered intervals and the design effect published beside them |
| **W8** | The card | `make card` regenerates; verdict `NOT_VERIFIED` with `docs/COVERAGE.md`'s gaps enumerated |

## Per-unit review checklist

Every unit is reviewed against the seams in `docs/ARCHITECTURE.md`:

| Row | Bar |
|---|---|
| Contract fidelity | Emits exactly the record in `CONTRACTS.md`, no extra fields, no silent nulls |
| Test quality | Behavioural or golden-case, not schema-only, for every statistical unit. A spectral estimator gets a synthetic signal with a known frequency; a bootstrap gets synthetic clustered data with a known design effect. `pytest` passing is not sufficient acceptance on its own |
| Isolation | `git diff --name-only` touches only the unit's files and its test file |
| Seam discipline | The unit's named seam is honoured, and the review says how it was checked rather than that it was |
| Aggregation floor | No code path emits an identifiable unit. Checked by reading, on every unit, every wave |

## Acceptance, mechanical

The unit's tests pass offline with no network; `mypy --strict` clean on its files; no
`NotImplementedError` in its public functions; every test runs against committed fixtures,
never live data.
