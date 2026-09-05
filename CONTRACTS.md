# Contracts

`contracts/v1.1`, frozen 2026-09-05, before any code exists. Schemas are the seam between the
modules described in `docs/ARCHITECTURE.md`; changing one is a decision and belongs in
`docs/DECISIONS.md`. The changelog at the end records what v1.1 changed and why.

Three rules apply to all of them.

1. **Every record carries its provenance.** Which shard, which clip, which revision, which
   label source, which method. A number whose origin cannot be reconstructed is not
   publishable.
2. **Absence is explicit.** A clip that failed to decode, a spectrum with no resolvable
   peak, a frame with no detected hand, a TLV input that cannot be observed — each is
   recorded as such, with its reason, and excluded from the denominator. Silently dropping
   it biases the distribution, and in this project the bias would run toward *understating*
   exposure.
3. **Identifiers exist in records and never in aggregates.** `factory_id` and `worker_id`
   are load-bearing on every per-clip record because clustering requires them.
   `ExposureAggregate` has no field that can carry one, and its validator rejects any string
   value anywhere in the record that looks like one. This is a schema-level guarantee, not
   a convention — see `docs/ETHICS.md` and the seam in `docs/ARCHITECTURE.md`.

## Notation

| Written | Means |
|---|---|
| `CI95` | two-element array `[lo, hi]` |
| `datetime` | ISO 8601 UTC, `Z`-suffixed |
| `Literal[a,b]` | closed enum; anything else is a contract violation, not a warning |
| `null` | explicitly absent, with a sibling `*_reason` field naming why |

## `ClipRef` — one clip in the raw corpus

```json
{ "clip_id": "factory_001/worker_001/000123", "factory_id": "factory_001",
  "worker_id": "worker_001", "clip_index": 123, "shard": "factory_001/worker_001/shard-00007.tar",
  "byte_start": 512, "byte_end": 8419328, "duration_s": 187.4, "fps": 30.0,
  "width": 1920, "height": 1080, "codec": "h265", "corpus_rev": "3e5f87c8" }
```

- `clip_id` is `factory_id/worker_id/clip_index`, zero-padded. It is the join key everywhere.
- `worker_id` is numbered **within** factory; `worker_001` exists in every factory. The
  cluster key is always the pair, never the bare `worker_id` (`docs/DECISIONS.md` D015).
- `corpus_rev` is the pinned dataset revision. Two records with different `corpus_rev` are
  never pooled.
- Sourced from the per-clip metadata the release ships (factory, worker, video index,
  duration, resolution, frame rate, codec), not inferred from the media. The metadata
  carries no sector or task field.

## `FrameSignal` — the per-frame series for one clip

```json
{ "clip_id": "...", "fps_sampled": 4.0, "n_frames": 750,
  "manipulation": [true, true, false, null], "hands_visible": [2, 2, 1, null],
  "hand_box_width_px": [212.0, 208.5, null, null],
  "hand_mask_source": "100doh", "flow_method": "farneback",
  "label_source": "judge", "label_rev": "qwen3vl@...", "prompt_variant": "P0b",
  "status": "ok", "n_unreadable": 1 }
```

- `manipulation[i] = null` means that frame could not be labelled. `n_unreadable` counts
  them and they are excluded from every denominator downstream.
- `hand_box_width_px[i]` is the width of the largest detected hand box at sample `i`, in
  pixels; `null` when no box was detected or the frame was unreadable. It is the
  hand-breadth scale for the speed path.
- `hand_mask_source` ∈ {`100doh`, `egohos`, `none`}. `none` means no detector ran; every
  `hand_box_width_px` is then `null` and the speed path cannot produce a value.
- `flow_method` names the optical-flow estimator used for the speed samples.
- `label_source` ∈ {`judge`, `probe`, `human`}. Never pooled across sources in one estimate.
- `fps_sampled` is the analysis rate, not the clip's native `fps`. It bounds the highest
  exertion frequency recoverable on the spectral path — see `docs/RUBRIC.md` on the Nyquist
  limit, which is a real constraint on H2 and is stated in `docs/PRE-REGISTRATION.md`
  rather than discovered.

## `ExertionSegment` — one bounded exertion

```json
{ "clip_id": "...", "start_s": 12.5, "end_s": 14.0, "method": "transitions",
  "min_duration_s": 0.5, "label_source": "judge" }
```

- `method` ∈ {`transitions`, `segmenter`}. Produced only by the cross-check path; the
  primary frequency estimate never segments. See `docs/DECISIONS.md` D005.
- `min_duration_s` is the debounce threshold applied, recorded because the segment count is
  a function of it.

## `DutyCycleEstimate` — one clip

```json
{ "clip_id": "...", "duty_cycle": 0.68, "n_frames_scored": 749, "n_frames_exerting": 509,
  "n_frames_excluded": 1, "label_source": "judge", "status": "ok" }
```

- `duty_cycle = n_frames_exerting / n_frames_scored`. `n_frames_scored` excludes unreadable
  frames; the exclusion count travels with the estimate so a reader can bound its effect.
- `status` ∈ {`ok`, `too_short`, `no_labels`, `decode_failed`}. Anything but `ok` carries
  `duty_cycle: null`.

## `FrequencyEstimate` — manipulation-bout frequency, one clip, spectral path

```json
{ "clip_id": "...", "hz": 0.42, "method": "spectral", "peak_power_ratio": 6.1,
  "resolvable": true, "hz_ci95": [0.38, 0.47], "nyquist_hz": 2.0, "status": "ok" }
```

- `method` ∈ {`spectral`, `transitions`}. Both are computed on every clip; `spectral` is
  primary *within this path* and `transitions` is the cross-check that H2a tests.
- **What `hz` is:** the dominant frequency of the manipulation on/off series — the rate of
  manipulation *bouts*. It is a lower bound on the TLV's exertion frequency, because a hand
  stays "manipulating" across consecutive exertions (`docs/DECISIONS.md` D014;
  `docs/RED-TEAM.md` A10). Every consumer labels it so.
- `resolvable` is false when no peak clears the pre-registered `peak_power_ratio` floor —
  a clip with no dominant cycle. `hz` is then `null` with `status: "no_peak"`, and such
  clips are counted, reported, and excluded rather than assigned a frequency of zero.
- `nyquist_hz = fps_sampled / 2`. An estimate at or above it is `status: "aliased"`.

## `HandSpeedEstimate` — RMS hand speed, one clip, speed path

```json
{ "clip_id": "...", "rms_speed_mm_s": 612.4, "n_samples": 749, "n_with_box": 688,
  "n_flow_null": 9, "coverage": 0.918, "flow_null_rate": 0.013,
  "hand_breadth_mm": 85.0, "median_box_width_px": 209.0,
  "mask_source": "100doh", "flow_method": "farneback", "ego_motion": "mask_complement_median",
  "status": "ok", "status_reason": null }
```

- `rms_speed_mm_s` is the RMS over samples that have a box and a valid flow, of the residual
  flow magnitude inside the hand box after subtracting the ego-motion estimate from the
  mask complement, scaled by `hand_breadth_mm / median_box_width_px`.
- `coverage = n_with_box / n_samples`; `flow_null_rate = n_flow_null / n_with_box`.
- `status` ∈ {`ok`, `low_coverage`, `no_detector`, `flow_failed`, `too_short`}.
  `low_coverage` fires below 0.60; `flow_failed` fires above a 0.10 null rate. Anything but
  `ok` carries `rms_speed_mm_s: null` and a non-null `status_reason`.
- `mask_source` is never `region`; a region prior is not a hand mask and this record cannot
  be built from one (`docs/DECISIONS.md` D014).

## `HALScore` — the Hand Activity Level axis, one clip

```json
{ "clip_id": "...", "hal": 6.1, "mapping": "akkas-2015-speed-dc",
  "scale_rev": "acgih-2001-table/akkas-2015-fit", "duty_cycle": 0.68,
  "hz": null, "rms_speed_mm_s": 612.4, "force_axis": null,
  "force_axis_reason": "peak force is not observable from video (docs/COVERAGE.md)",
  "tlv_evaluable": false, "status": "ok" }
```

- `hal` is on the published 0–10 Hand Activity Level scale, to one decimal, per Radwin
  2015's recommendation.
- `mapping` ∈ {`radwin-2015-freq-dc`, `akkas-2015-speed-dc`}. **`radwin` requires `hz`
  non-null; `akkas` requires `rms_speed_mm_s` non-null.** The other input may be present for
  the record and is not used. `scale_rev` names the table edition the fit was made to and
  the fit; a record whose `scale_rev` is unset is invalid.
- `force_axis` is **always** `null` and `tlv_evaluable` is **always** `false` in v1. They
  exist in the schema so that the absence is a value a reader can see, not an omission they
  have to notice. Rule 4 of `AGENTS.md`.

## `ExposureAggregate` — the published unit

```json
{ "aggregate_id": "corpus-v1", "stratum": "corpus",
  "stratum_definition": "docs/DECISIONS.md#d019",
  "n_clips": 41230, "n_workers": 2144, "n_factories": 85,
  "k_factories": 85, "k_workers": 2144, "max_factory_share": 0.04,
  "mapping": "akkas-2015-speed-dc",
  "hal_mean": 4.11, "hal_ci95": [3.94, 4.28], "hal_quantiles": {"p10": 2.1, "p50": 4.0, "p90": 6.7},
  "cluster_unit": "factory_id/worker_id", "weighting": "worker",
  "design_effect": 1.44, "design_effect_width_ratio": 1.20, "design_effect_mc_band": 0.05,
  "bootstrap_b": 10000, "seed": 777, "iid_ci95_for_contrast": [4.02, 4.20],
  "aggregation_reason": "corpus-level; docs/ETHICS.md forbids any unit below the floor",
  "corpus_rev": "3e5f87c8", "generated": "2026-09-05T00:00:00Z" }
```

- **There is no `factory_id` and no `worker_id` field, and there will not be one.** Only
  counts. The validator additionally rejects **any** string value in the record matching
  `factory_\d+|worker_\d+`, so a definition or reason string cannot smuggle one. This is the
  schema-level enforcement of `AGENTS.md` rule 3.
- `stratum` ∈ {`corpus`, `size_tercile_1`, `size_tercile_2`, `size_tercile_3`}.
  `stratum_definition` must be a path under `docs/`, optionally with an anchor. Free text is
  rejected.
- `k_factories ≥ 5`, `k_workers ≥ 50`, `max_factory_share ≤ 0.40` are enforced on every
  record, including `corpus`, where they hold trivially (`docs/DECISIONS.md` D019).
- `cluster_unit` is the literal `factory_id/worker_id` and nothing else. `weighting` is
  `worker` for strata and `clip` or `worker` for the corpus, stated.
- `design_effect` is the variance ratio; `design_effect_width_ratio` is its square root.
  Both are printed because the two readings have been confused before.
- `iid_ci95_for_contrast` appears only beside the clustered interval, labelled, to exhibit
  the design effect. It is never published alone.
- `aggregation_reason` is a required string. A caller that wants an aggregate must state
  why the aggregation is permissible; there is no default, because a silent default is how
  the ethics rule would eventually break.

## `MeasurementCard` — the published artifact

```json
{ "verdict": "NOT_VERIFIED", "generated": "...", "corpus_rev": "...", "arm": "A",
  "claims": [ { "id": "H1", "statement": "...", "status": "UNTESTED",
                "source": "results/h1_duty_cycle.json", "interval": null } ],
  "known_gaps": ["no expert agreement statistic", "peak force unobservable"] }
```

- Generated by `scripts/refresh_card.py`. Never hand-edited.
- `arm` ∈ {`A`, `B`, `null`} names which main-draw arm produced the results.
- `claims[].status` ∈ {`UNTESTED`, `HOLDS`, `FAILED`, `UNTESTED_ARM_B`}. `FAILED` is a value
  the enum must be able to say because the pre-registration says failures are reported in
  those words. `UNTESTED_ARM_B` is H4/H5 under Arm B.
- `verdict` ∈ {`NOT_VERIFIED`, `VERIFIED`}. It is `NOT_VERIFIED` while any claim is
  `UNTESTED` or any entry in `known_gaps` is unclosed, and `make card` exits nonzero unless
  it is `VERIFIED`. The gaps above are open by construction in v1, so v1's card is
  `NOT_VERIFIED` and that is the honest state, not a failure.
- Every `source` is a path that must exist and must contain the number the claim states,
  and no `source` file may contain a factory or worker identifier
  (`scripts/validate.py` `gate_no_identifier_in_results`).

## Changelog

| Rev | Date | Change | Decision |
|---|---|---|---|
| `contracts/v1` | 2026-09-05 | Initial freeze, before `src/` exists. | D001 |
| `contracts/v1.1` | 2026-09-05 | `FrameSignal` gains hand-box width, mask source, flow method. New `HandSpeedEstimate`. `FrequencyEstimate.hz` documented as bout frequency. `HALScore` gains `mapping` and `rms_speed_mm_s` with mapping-conditional null rules. `ExposureAggregate` gains `stratum`, k-floor fields, `weighting`, `seed`, width-ratio, identifier-pattern rejection; `cluster_unit` is the composite. `MeasurementCard` gains `arm`, `FAILED`, `UNTESTED_ARM_B`. Still before `src/` exists. | D013–D019 |
