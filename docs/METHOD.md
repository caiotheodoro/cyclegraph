# Method

The protocol, stage by stage, with the cost of each. Cost is published because a check
nobody can afford is not a check — the convention is inherited from `../assay/docs/METHOD.md`.

**Every figure in the cost column is an estimate under stated assumptions, not a
measurement.** They are replaced with measured values as each stage runs, and the assumption
is named so a reader can see which way an error would run.

## Scale, first, because it determines the method

One factory is roughly 2,270 clips (192,903 ÷ 85). At a mean clip duration near 187 s and
the pre-registered 4 Hz analysis rate, that is **~1.7 million frames for the pilot factory
alone**. The 40,000-clip main draw is **~30 million frames**.

This rules out labelling every frame with a VLM judge, at any price. The method that follows
is shaped by that arithmetic rather than by preference, and the consequence is a real
weakness recorded in `docs/RED-TEAM.md` A1.

## E1 — Clip manifest

Enumerate clips for the pilot factory from the shard index and the per-clip metadata the
release ships. No decode. Emits `ClipRef`.

**Cost:** negligible; HTTP range reads of shard indices only.
**Gate:** clip count and total duration reconcile against the published per-factory figures.

## E2 — Frame extraction

Decode at 4 Hz via ffmpeg's `subfile` protocol over HTTP range requests — a frame out of an
mp4 inside a tar without downloading the shard, established in `../vernier/docs/DECISIONS.md`.

**Cost:** ~1.7M frames for the pilot. Estimated 2–4 hours wall-clock at a few hundred frames
per second, network-bound rather than compute-bound.
**Gate:** decode failure rate below 1%, and failures recorded as `decode_failed` rather than
dropped.

## E3 — Labelling, two sources

The primary label source is a **cheap probe** — frozen backbone features plus a linear head,
the shape `vernier` built and published as a negative result at 0.693 fidelity against a
0.8 target. That number is a warning, not a licence: it is why H1 exists.

The **judge** runs on a stratified calibration subset only, sized so that H1's cross-source
comparison is powered, not on the full corpus.

**Cost:** probe ~1.7M frames at ~100 frames/s ≈ 5 GPU-hours for the pilot. Judge on a
calibration subset of ~20,000 frames, on the order of tens of dollars at the rates
`../vernier/docs/METHOD.md` records.
**Gate:** H1. If duty cycle is not stable across the two sources within 0.05 mean absolute
difference, the probe cannot carry the corpus and the method stops here rather than scaling
a known-biased labeller to 30M frames.

## E4 — Duty cycle

Mean of the manipulation series over scored frames, per clip. No smoothing.

**Cost:** negligible.
**Gate:** H1's sampling-rate arm — 4 Hz against 8 Hz on a subsample, within 0.02.

## E5 — Exertion frequency

Spectral estimation over the manipulation series, primary. Transition-counting with the
0.5 s debounce, as cross-check.

**Cost:** negligible.
**Gate:** H2, both bounds — 20% relative agreement *and* ≥70% of clips resolvable. The
second bound is the one that usually goes unreported and it is a stopping condition here.

## E6 — Hand Activity Level

Map (frequency, duty cycle) onto the published 0–10 scale.

**Blocked.** The exact mapping and its edition are an open question with a resolving trigger
in `docs/RUBRIC.md`: the ACGIH TLV documentation must be obtained and transcribed. `make hal`
fails loudly rather than approximating, because an approximate mapping would produce numbers
that look like HAL, compare against published HAL in E8, and be wrong by an offset E8 could
not detect.

**Cost:** the standard's purchase price, plus an afternoon.

## E7 — Negative control

The same pipeline on a non-repetitive egocentric corpus — Ego4D and EPIC-KITCHENS-100.

**Cost:** small; both are already accessible to the sibling project, subject to
EPIC-KITCHENS' institutional-email requirement, which `../vernier/docs/COVERAGE.md` records
as unmet. If it stays unmet, Ego4D alone carries the control and that is a weaker control,
reported as such.
**Gate:** median HAL separates by ≥1.0 on the 0–10 scale. **This runs before E8.** A
pipeline that cannot distinguish factory work from kitchen work has not measured repetition,
and its distribution is not worth comparing to anything.

## E8 — Aggregation and the design effect

Cluster bootstrap over `worker_id`, B = 10,000, with the iid interval beside it for
contrast. Variance decomposition for H4. Comparison against published HAL distributions for
H3.

**Cost:** minutes.
**Gate:** H3, H4, H5. H3 is labelled a plausibility check in every place it appears.

## E9 — The card

`make card` regenerates `MEASUREMENT_CARD.json` from `results/`. Verdict is `NOT_VERIFIED`
while any gap in `docs/COVERAGE.md` is open, which in v1 is by construction.

## What is not in the protocol

No rendering, no synthetic data, no pose estimation, no per-cycle metric, no force, no
per-worker or per-factory number, and no full-corpus decode.
