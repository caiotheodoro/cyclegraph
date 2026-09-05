# Dataset card

The narrative for what cyclegraph would publish. `hf/dataset/README.md` is the generated
release artifact that interpolates live numbers into this text; it is derived and
gitignored, and every number in it must trace to a file under `results/`.

**Nothing is published yet.** W0 is documentation only.

## What would be released

Derived exposure records — never frames, never clips, never media of any kind.

| Config | Contents |
|---|---|
| `clip_estimates` | One row per clip: duty cycle, spectral bout frequency, RMS hand speed, HAL on both paths, exclusion status. **No grouping key of any kind** — no worker, factory, or opaque surrogate |
| `bootstrap_replicates` | The B = 10,000 cluster-bootstrap replicate means for every published interval, so H5 and every CI are reproducible without a grouping key |
| `aggregates` | `ExposureAggregate` rows: corpus, and size-tercile strata above the D019 floor |
| `results` | The raw result JSONs each claim in the card cites |

Plus copies of `CONTRACTS.md`, `docs/PRE-REGISTRATION.md` and `docs/RUBRIC.md`, so the
release is self-describing.

## What would never be released

- Any frame or clip. The corpus is Build AI's to distribute and the workers' likeness is not
  Build AI's to license — the same argument `../vernier/docs/ETHICS.md` makes about
  republication, and it applies with more force here because these records are about bodies.
- Any real or surrogate `worker_id` or `factory_id`. An earlier draft proposed a salted
  opaque key; it was dropped because a stable grouping key, salted or not, lets anyone
  compute per-group means from `clip_estimates`. The rows ship with no key, and the
  clustered intervals are reproducible from `bootstrap_replicates` instead.
- Any per-worker, per-factory or sub-floor statistic, in any form.

## Provenance

Derived from `builddotai/Egocentric-10K`, raw release, at a pinned revision recorded in
`corpus_rev` on every record. Apache-2.0 upstream. `docs/ETHICS.md` states what the upstream
licence does and does not settle.

## Known limitations

Every entry in `docs/COVERAGE.md`, and above all: no expert agreement statistic, and no force
axis. A user of these records is measuring one axis of a two-axis criterion, computed by an
unvalidated instrument.
