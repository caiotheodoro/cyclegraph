# Benchmark

The results table. Its structure is fixed before any experiment runs, specifically so
results land in a shape decided before anyone saw them.

**No experiment has run. Every cell is `—`.** A results table written after the results are
known is a presentation, not a protocol.

## Primary

| Hypothesis | Statement | Threshold | Observed | Interval | Holds |
|---|---|---|---|---|---|
| H1a | Duty cycle stable across label sources | ≤0.05 mean abs. diff | — | — | — |
| H1b | Duty cycle stable across sampling rates | ≤0.02 mean abs. diff | — | — | — |
| H2a | Spectral bout frequency vs. transition counting | ≤20% relative diff | — | — | — |
| H2b | Fraction of clips spectrally resolvable | ≥70% | — | — | — |
| H2c | Hand-box coverage / flow-null rate | ≥60% / ≤10% | — | — | — |
| NC-dc | Factory − Ego4D duty cycle; HAL | ≥0.25; ≥1.0 | — | — | — |
| NC-f | Factory − EPIC-KITCHENS HAL, speed path | ≥0.5 | — | — | — |
| H3 | Median HAL, primary path | inside [2.4, 6.2] | — | — | — |
| H4 | Between-factory variance > between-worker | ratio >1 | — | — | — |
| H5 | Design effect on HAL, clustered by `factory_id/worker_id` | ≥1.2 | — | — | — |

Intervals are cluster bootstrap over `factory_id/worker_id`, B = 10,000. The iid interval
appears in the row below each clustered one, labelled, for contrast only. Under Arm B
(`docs/DECISIONS.md` D018) the H4 and H5 rows read `UNTESTED` and say so.

## Both paths, side by side

| Figure | Speed path (primary) | Spectral path (lower bound) |
|---|---|---|
| HAL median | — | — |
| HAL p10 / p90 | — | — |
| Clips contributing | — | — |
| Clips excluded (`low_coverage` / `flow_failed` · `no_peak` / `aliased`) | — | — |

## Design effect, reported as a result in its own right

| Figure | Clustered CI width | iid CI width | Design effect (variance ratio) | Width ratio (√) |
|---|---|---|---|---|
| HAL mean | — | — | — | — |
| Duty cycle mean | — | — | — | — |
| RMS speed mean | — | — | — | — |

Both readings are printed because a threshold stated as "a design effect of 2" and one
stated as "twice the width" are different claims, and conflating them made a sibling
project's equivalent hypothesis unfalsifiable as written.

## Strata

| Stratum | n factories | n workers | max share (workers / clips) | HAL mean | CI95 |
|---|---|---|---|---|---|
| corpus | — | — | — | — | — |
| size tercile 1 | — | — | — | — | — |
| size tercile 2 | — | — | — | — | — |
| size tercile 3 | — | — | — | — | — |

A stratum row below the floor (`docs/DECISIONS.md` D019) is printed as `SUPPRESSED`, not
omitted, so the suppression is visible.

## Sensitivity

| Choice | Alternatives run | Effect on HAL median |
|---|---|---|
| Hand breadth 85 mm | 79.5, 90.4 | — |
| Ego-motion from mask complement | none subtracted (upper bound) | — |
| Translation floor (A14) | subtracted / not | — |

## Exclusions, which are part of the result

| Reason | Clips | % of drawn |
|---|---|---|
| `too_short` | — | — |
| `decode_failed` | — | — |
| `no_labels` | — | — |
| `no_peak` (spectral unresolvable) | — | — |
| `aliased` | — | — |
| `low_coverage` (speed path) | — | — |
| `flow_failed` (speed path) | — | — |

The `no_peak` and `low_coverage` rows are the ones to read first. Each path's distribution
is conditional on its own exclusions, and `docs/RED-TEAM.md` A5, A12 and A15 are the attacks
those rows answer or concede.

## What is not in this table, and will not be

The TLV. The force axis. Any per-worker or per-factory figure, including any pilot value.
An agreement statistic against expert assessment — there is no expert.
