# Benchmark

The results table. Its structure is fixed before any experiment runs, specifically so
results land in a shape decided before anyone saw them.

**No experiment has run. Every cell is `—`.** This file is committed empty on purpose; a
results table written after the results are known is a presentation, not a protocol.

## Primary

| Hypothesis | Statement | Threshold | Observed | Interval | Holds |
|---|---|---|---|---|---|
| H1a | Duty cycle stable across label sources | ≤0.05 mean abs. diff | — | — | — |
| H1b | Duty cycle stable across sampling rates | ≤0.02 mean abs. diff | — | — | — |
| H2a | Spectral vs. transition frequency | ≤20% relative diff | — | — | — |
| H2b | Fraction of clips resolvable | ≥70% | — | — | — |
| H3 | HAL distribution plausible vs. literature | median inside published range | — | — | — |
| H4 | Between-factory variance > between-worker | ratio >1 | — | — | — |
| H5 | Design effect on HAL, clustered by worker | >1 | — | — | — |
| NC | Factory vs. non-repetitive corpus | ≥1.0 median HAL gap | — | — | — |

Intervals are cluster bootstrap over `worker_id`, B = 10,000. The iid interval appears in
the row below each clustered one, labelled, for contrast only.

## Design effect, reported as a result in its own right

| Figure | Clustered CI width | iid CI width | Design effect (variance ratio) | Width ratio (√) |
|---|---|---|---|---|
| HAL mean | — | — | — | — |
| Duty cycle mean | — | — | — | — |
| Frequency mean | — | — | — | — |

Both readings are printed because a threshold stated as "a design effect of 2" and one
stated as "twice the width" are different claims, and conflating them made a sibling
project's equivalent hypothesis unfalsifiable as written.

## Exclusions, which are part of the result

| Reason | Clips | % of drawn |
|---|---|---|
| `too_short` | — | — |
| `decode_failed` | — | — |
| `no_labels` | — | — |
| `no_peak` (unresolvable frequency) | — | — |
| `aliased` | — | — |

The `no_peak` row is the one to read first. The reported distribution is conditional on
resolvability, and `docs/RED-TEAM.md` A5 is the attack that row answers or concedes.

## What is not in this table, and will not be

The TLV. The force axis. Any per-worker or per-factory figure. An agreement statistic
against expert assessment — there is no expert.
