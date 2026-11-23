# Design: v2 real-video validation and corpus measurement

Status: **design, not a registration.** Written 2026-11-23 alongside the paper v2 revision.
Nothing here is frozen, nothing has been run, no paid call has been made, and every choice
marked **owner** is open. Any corpus-scale measurement remains governed by the frozen
`docs/PRE-REGISTRATION.md` (v1.5.0) and its k-anonymity and pilot-withholding rules
(`docs/ETHICS.md`, D018, D019).

## Why

The synthetic instrument check (v1 plus the D078 post-hoc suite in `results/flow_gain_v2.json`)
establishes the background-capture mechanism across four estimators and controlled sweeps of
depth ratio, box size, motion blur, and sensor noise, and cleanly separates ego-motion capture
from static-camera breakdown. Four questions remain open because they require real egocentric
footage, a richer renderer, or paid compute:

1. **Real inter-frame displacement distributions.** Synthetic scenes establish *where* each
   estimator crosses half gain in pixels, not *how often* real factory or kitchen hand motions
   reach 23–40 px per frame pair at 30 fps. No publishable real egocentric video clips are on
   disk locally, and pilot-factory values are withheld under D018.
2. **Realistic occlusion, disocclusion, rolling shutter, and 3D hand articulation.** The two-plane
   backward warp isolates the depth discontinuity cleanly without occlusion, foreground/background
   texture contrast, rolling shutter, or illumination change.
3. **Sparse tracking, global-matching transformers, and depth-aware alternatives.** The v2 suite
   tests four dense estimators (Farneback, DIS, RAFT-small, RAFT-large). Sparse keypoint/box
   tracking, global-matching flow (GMFlow), and monocular depth-conditioned or motion-segmented
   flow remain untested on the same harness.
4. **Corpus-scale exposure measurement and negative controls.** Blocked on budget (`docs/BLOCKED.md`)
   and dataset licences (Ego4D licence acceptance; EPIC-KITCHENS-100 institutional email).

## What stays

- The nominal Kannala--Brandt corpus lens (`CORPUS_CAMERA`, D025) and exact analytic ground truth.
- The privacy and ethics boundaries (`docs/ETHICS.md`, D018, D019): no per-worker, per-factory,
  sub-floor, or pilot-factory value ever leaves `results/`.
- The frozen pre-registration (`docs/PRE-REGISTRATION.md` v1.5.0) for any corpus-level HAL claim.

## Planned workstreams

### A. Real-clip displacement distribution check (no pilot leakage)

- **Source corpora (public, non-pilot):** Ego4D (after licence acceptance, `docs/BLOCKED.md`) and
  EPIC-KITCHENS-100 (if institutional access is obtained), or a multi-factory corpus draw clearing
  D019's k-anonymity floor (≥5 factories, ≥50 workers, max factory share ≤40%).
- **Measurement:** Sample consecutive frame pairs at native frame rate (30 fps), run hand
  detection plus sparse keypoint tracking (e.g. KLT / CoTracker) inside the hand mask to obtain a
  dense-flow-independent displacement reference, and report the empirical CDF of per-pair hand
  displacement (in px and in fractions of box width) alongside the background ego-motion
  distribution.
- **Outcome:** Directly answers what fraction of real working frames fall below, inside, and
  above each estimator's transition band (23–40+ px at 960×540).
- **Owner:** accept the Ego4D licence (~$8 estimated GPU/CPU cost per `docs/BLOCKED.md`) or fund
  a k-anonymous multi-factory sample.

### B. 3D / occlusion-aware synthetic renderer

- Replace the static-box first-order backward warp with a forward-rendered or ray-cast two-layer
  scene where the hand patch physically moves across the background, creating true occlusion and
  disocclusion strips, distinct foreground/background texture statistics, rolling-shutter scanline
  delay, and illumination shift.
- Re-run the four-estimator suite on both renderers to measure how much occlusion and distinct
  foreground texture shift the half-crossing displacement and background-capture fraction.

### C. Estimator and mitigation comparison

- Evaluate a global-matching transformer (GMFlow; Xu et al. 2022), a sparse point tracker inside
  the hand mask, and a parametric (homography or rotational) ego-motion model for the fisheye
  lens (which removes the 76× scalar-median rotation residual of `results/a14_translation_floor.json`).
- Any replacement of the ego-motion rule or speed estimator for the corpus study requires a formal
  amendment to `docs/RUBRIC.md` and `docs/PRE-REGISTRATION.md` before corpus decoding begins.

### D. Corpus HAL measurement and negative controls

- Follow the locked wave order in `docs/WAVES.md` and cost ledger in `docs/BLOCKED.md`:
  1. Ego4D negative control (NC-dc; ~$8 after licence acceptance).
  2. H1a cross-labeller agreement on ~30 stratified clips (~$5–$9, or self-hosted VLM).
  3. Main draw selected by H1a outcome (Arm A: 40,000 clips, ~$2,840; Arm B: 200 clips, ~$82).
  4. Aggregate-only reporting with k-anonymity enforcement (`MEASUREMENT_CARD.json`).

## What the owner decides before starting

1. Whether to unblock Ego4D first for workstream A (~$8) independently of the corpus draw.
2. Whether to amend `docs/RUBRIC.md` to replace scalar-median ego-motion subtraction and dense
   Farneback flow with parametric rotation compensation + sparse/global-matching tracking before
   running the main corpus draw.
3. Funding allocation for H1a and Arm A vs Arm B (`docs/BLOCKED.md`).
