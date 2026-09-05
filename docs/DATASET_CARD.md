# Dataset card

The narrative for what cyclegraph would publish. `hf/dataset/README.md` is the generated
release artifact that interpolates live numbers into this text; it is derived and
gitignored, and every number in it must trace to a file under `results/`.

**Nothing is published yet.** W0 is documentation only.

## What would be released

Derived exposure records — never frames, never clips, never media of any kind.

| Config | Contents |
|---|---|
| `clip_estimates` | One row per clip: duty cycle, frequency by both methods, resolvability, exclusion status. **Identifiers replaced by a salted opaque key** that supports clustering and supports nothing else |
| `aggregates` | `ExposureAggregate` rows. Corpus level only |
| `results` | The raw result JSONs each claim in the card cites |

Plus copies of `CONTRACTS.md`, `docs/PRE-REGISTRATION.md` and `docs/RUBRIC.md`, so the
release is self-describing.

## What would never be released

- Any frame or clip. The corpus is Build AI's to distribute and the workers' likeness is not
  Build AI's to license — the same argument `../vernier/docs/ETHICS.md` makes about
  republication, and it applies with more force here because these records are about bodies.
- Any real `worker_id` or `factory_id`. The opaque key is one-way and per-release salted, so
  two releases cannot be joined to recover a worker.
- Any per-worker or per-factory statistic, in any form, including one a reader could
  reconstruct by grouping `clip_estimates`.

That last item is a genuine tension and it is not resolved by the salt: publishing per-clip
rows with a stable grouping key lets anyone compute per-group means, salted or not.
**Resolving trigger:** before any release, decide whether `clip_estimates` ships at all, or
ships without the grouping key and therefore without the ability to reproduce H5. Recorded
here rather than discovered at publication time.

## Provenance

Derived from `builddotai/Egocentric-10K`, raw release, at a pinned revision recorded in
`corpus_rev` on every record. Apache-2.0 upstream. `docs/ETHICS.md` states what the upstream
licence does and does not settle.

## Known limitations

Every entry in `docs/COVERAGE.md`, and above all: no expert agreement statistic, and no force
axis. A user of these records is measuring one axis of a two-axis criterion, computed by an
unvalidated instrument.
