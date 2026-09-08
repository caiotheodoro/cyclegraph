# Benchmark card

The flow-gain benchmark: what it measures, what it found, and what it cannot tell you.

This is **not** `docs/DATASET_CARD.md`. That document describes the corpus-derived exposure
records cyclegraph would publish if the measurement ran. This one describes an instrument check
that needs no corpus at all — no token, no GPU, no network. The two are separate releases and
the numbers never mix (`docs/DECISIONS.md` D071).

## What is measured

One quantity, swept: **gain**, the median recovered flow magnitude over the median true flow
magnitude, inside the hand box.

Gain 1.0 recovers the hand's motion. Gain 0.2 reports a fifth of it. The frames are rendered
synthetics under the corpus's own published fisheye — Kannala-Brandt, `k = [-0.116554,
-0.023589, 0.069364, -0.046334]`, 67.892 degrees half-angle — so the true flow field is known
exactly. Knowing it exactly is what makes a gain measurable at all.

A static hand sits at 0.45 m and the background at 2.5 m. Those distances are stated assumptions
about workstation geometry, not measurements, and they are part of the result's definition.

## What it found

**Gain does not decay. It falls off a knee and lands on a floor.**

The floor is `0.45 / 2.5 = 0.18`, the ratio of the two depths. Past the knee the estimator has
stopped reporting the hand and started reporting the background, scaled by how much further away
the background is.

| estimator | decode | last displacement above 0.97 | first displacement below 0.25 |
|---|---|---|---|
| farneback-cv2 | 960x540 | 22.794 px | 34.181 px |
| raft-small | 960x540 | 34.181 px | 45.539 px |

**The knee belongs to the estimator. The floor belongs to the geometry.** RAFT-small holds gain
0.9738 at a displacement where Farneback has already collapsed to 0.2024 — roughly one more
doubling of usable range. It buys a later knee and it does not move the floor: RAFT's collapsed
gains at 960x540 are 0.172, 0.177, 0.180, 0.184, and Farneback's across scales sit in the same
band. Swapping estimators is a real improvement to where the cliff is and no improvement at all
to what is below it.

**Higher decode resolution is not better, and past a point it is worse.** At the same
box-relative displacement — 0.236 of the hand box width — gain runs:

| decode | 480x270 | 960x540 | 1440x810 | 1920x1080 |
|---|---|---|---|---|
| gain | 0.7656 | 0.9925 | 0.2036 | 0.1978 |

960x540 is a measured optimum, not a compromise. 1920x1080 does worse than 480x270.

**Far past the knee there is a second regime.** Gain falls below the depth ratio toward zero,
once displacement exceeds the estimator's search range outright and it tracks nothing. The
0.18 plateau is a stage, not an asymptote (`docs/DECISIONS.md` D070), and the two regimes must
not be averaged together.

## Why the error is hard to see

`docs/RUBRIC.md` subtracts ego-motion as the median flow over the complement of the hand mask.
Past the knee, the hand box already contains the background's flow. The correction then removes
the signal it was meant to clean, and the residual comes out small and plausible instead of
obviously wrong. Two failures pointing the same way cancel into a believable number.

The exact-geometry floor is the control that separates them. It is computed closed-form, with no
estimator involved, so it is a property of the rule and the lens alone
(`results/a14_translation_floor.json`). Against it:

| A14 rotation residual | px |
|---|---|
| exact geometry, no estimator | 1.1461 |
| farneback-cv2 | 1.2171 |
| raft-small | 1.014 |

RAFT lands **below** the floor an ideal estimator would leave. That is under-recovery, not
accuracy — a wrong answer in the direction that looks like a good one.

The lens is doing most of this work. Under pure rotation at 10 deg/s the corpus fisheye leaves a
10.0916 mm/s apparent hand speed where a narrow lens leaves 0.1328 mm/s. Seventy-six times more,
from the same rule, because a scalar median cannot cancel a field that varies radially.

## Which files share a baseline

`flow_displacement_gain.json` and `flow_gain_raft.json` were measured on the 0.25 s pair interval
that `docs/DECISIONS.md` D045 replaced. `flow_gain_by_resolution.json` uses the clip's own frame
rate, about 0.0333 s.

The pixel displacements and the gains are identical either way. The interval only rescales the
`true_speed_mm_s` column, by 7.5x. So:

- **Compare estimators on `hand_displacement_px`.** Farneback and RAFT share the 0.25 s baseline
  and are directly comparable there.
- **Never compare any of it on mm/s across files.** `flow_benchmark.json` already states that a
  result carrying no `pair_baseline` field is not comparable to one that does.

Every published row carries its own `pair_interval_s` so this cannot be got wrong by accident.

## What this benchmark cannot tell you

- **Whether a real hand moves far enough between frames to cross the knee.** That depends on the
  frame rate and the work. The harness reports the knee for your geometry; it does not know your
  job.
- **Anything about the corpus.** No corpus frame was decoded for any number here. The
  measurement cyclegraph exists to make is blocked on cost and on one human step
  (`docs/BLOCKED.md`), and none of it has run.
- **Whether the ergonomic instrument is valid.** No ergonomist scored anything. `docs/COVERAGE.md`
  states what is untested, and this benchmark does not narrow it.
- **What the corpus's own ego-motion distribution is.** The floor table is computed for an
  assumed camera motion. Until frames are decoded it gives the floor for an assumption, not the
  floor.
- **Whether synthetic texture behaves like factory video.** The rendered scene has the corpus's
  lens and not its content.

## Reproduction

```
pip install -e ".[dev,signal]"
python3 scripts/measure_flow_gain.py --estimator farneback --widths 480,960,1440,1920
```

Seed 11, deterministic. The RAFT arm needs `torch` and a GPU is optional. The Farneback arm needs
neither a GPU nor a network nor a corpus token, which is the point: every claim on this card is
checkable by a stranger for nothing.

## Provenance and terms

The lens calibration is the corpus's published per-worker `intrinsics.json`, identical for all
2,144 shipped workers (`docs/DECISIONS.md` D025). It is the only corpus-derived input anywhere in
this release. Everything else is rendered.

`builddotai/Egocentric-10K` is released by its vendor under Apache-2.0, and this repository is
Apache-2.0. `docs/ETHICS.md` records the limit of what that settles:

> Apache-2.0 is the vendor's licence to grant. It is not a worker's consent, and section 2
> records that the consent instrument is unknown.

No frame, no worker, no factory and no pilot value appears in this release, and none ever will
at a unit any person or site could be identified by (`docs/DECISIONS.md` D018, D019).
