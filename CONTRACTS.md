# Contracts

`contracts/v1`, frozen 2026-09-05, before any code exists. Schemas are the seam between the
modules described in `docs/ARCHITECTURE.md`; changing one is a decision and belongs in
`docs/DECISIONS.md`.

Three rules apply to all of them.

1. **Every record carries its provenance.** Which shard, which clip, which revision, which
   label source, which method. A number whose origin cannot be reconstructed is not
   publishable.
2. **Absence is explicit.** A clip that failed to decode, a spectrum with no resolvable
   peak, a TLV input that cannot be observed — each is recorded as such, with its reason,
   and excluded from the denominator. Silently dropping it biases the distribution, and in
   this project the bias would run toward *understating* exposure.
3. **Identifiers exist in records and never in aggregates.** `factory_id` and `worker_id`
   are load-bearing on every record because clustering requires them. `ExposureAggregate`
   has no field that can carry one. This is a schema-level guarantee, not a convention —
   see `docs/ETHICS.md` and the seam in `docs/ARCHITECTURE.md`.

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
- `corpus_rev` is the pinned dataset revision. Two records with different `corpus_rev` are
  never pooled.
- Sourced from the per-clip metadata the release ships (factory, worker, video index,
  duration, resolution, frame rate, codec), not inferred from the media.

## `FrameSignal` — the per-frame series for one clip

```json
{ "clip_id": "...", "fps_sampled": 2.0, "n_frames": 375,
  "manipulation": [true, true, false, null], "hands_visible": [2, 2, 1, null],
  "label_source": "judge", "label_rev": "qwen3vl@...", "prompt_variant": "P0b",
  "status": "ok", "n_unreadable": 1 }
```

- `manipulation[i] = null` means that frame could not be labelled. `n_unreadable` counts
  them and they are excluded from every denominator downstream.
- `label_source` ∈ {`judge`, `probe`, `human`}. Never pooled across sources in one estimate.
- `fps_sampled` is the analysis rate, not the clip's native `fps`. It bounds the highest
  exertion frequency recoverable — see `docs/RUBRIC.md` on the Nyquist limit, which is a
  real constraint on H2 and is stated in `docs/PRE-REGISTRATION.md` rather than discovered.

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
{ "clip_id": "...", "duty_cycle": 0.68, "n_frames_scored": 374, "n_frames_exerting": 254,
  "n_frames_excluded": 1, "label_source": "judge", "status": "ok" }
```

- `duty_cycle = n_frames_exerting / n_frames_scored`. `n_frames_scored` excludes unreadable
  frames; the exclusion count travels with the estimate so a reader can bound its effect.
- `status` ∈ {`ok`, `too_short`, `no_labels`, `decode_failed`}. Anything but `ok` carries
  `duty_cycle: null`.

## `FrequencyEstimate` — exertions per second, one clip

```json
{ "clip_id": "...", "hz": 0.42, "method": "spectral", "peak_power_ratio": 6.1,
  "resolvable": true, "hz_ci95": [0.38, 0.47], "nyquist_hz": 1.0, "status": "ok" }
```

- `method` ∈ {`spectral`, `transitions`}. Both are computed on every clip; `spectral` is
  primary and `transitions` is the cross-check that H2 tests.
- `resolvable` is false when no peak clears the pre-registered `peak_power_ratio` floor —
  a clip with no dominant cycle. `hz` is then `null` with `status: "no_peak"`, and such
  clips are counted, reported, and excluded rather than assigned a frequency of zero.
- `nyquist_hz = fps_sampled / 2`. An estimate at or above it is `status: "aliased"`.

## `HALScore` — the Hand Activity Level axis, one clip

```json
{ "clip_id": "...", "hal": 4.6, "duty_cycle": 0.68, "hz": 0.42,
  "scale_rev": "acgih-tlv-hal/<edition>", "force_axis": null,
  "force_axis_reason": "peak force is not observable from video (docs/COVERAGE.md)",
  "tlv_evaluable": false, "status": "ok" }
```

- `hal` is on the published 0–10 Hand Activity Level scale. The exact mapping from
  (`hz`, `duty_cycle`) is fixed in `docs/RUBRIC.md` against the primary source, and
  `scale_rev` pins which edition was used. A record whose `scale_rev` is unset is invalid.
- `force_axis` is **always** `null` and `tlv_evaluable` is **always** `false` in v1. They
  exist in the schema so that the absence is a value a reader can see, not an omission they
  have to notice. Rule 4 of `AGENTS.md`.

## `ExposureAggregate` — the published unit

```json
{ "aggregate_id": "corpus-v1", "n_clips": 41230, "n_workers": 2144, "n_factories": 85,
  "hal_mean": 4.11, "hal_ci95": [3.94, 4.28], "hal_quantiles": {"p10": 2.1, "p50": 4.0, "p90": 6.7},
  "cluster_unit": "worker_id", "design_effect": 1.44, "design_effect_mc_band": 0.05,
  "bootstrap_b": 10000, "iid_ci95_for_contrast": [4.02, 4.20],
  "aggregation_reason": "corpus-level only; docs/ETHICS.md forbids any identifiable unit",
  "corpus_rev": "3e5f87c8", "generated": "2026-09-05T00:00:00Z" }
```

- **There is no `factory_id` and no `worker_id` field, and there will not be one.** Only
  counts. This is the schema-level enforcement of `AGENTS.md` rule 3.
- `cluster_unit` and `aggregation_reason` are required strings. A caller that wants an
  aggregate must state what it clustered over and why the aggregation is permissible; there
  is no default, because a silent default is how the ethics rule would eventually break.
- `iid_ci95_for_contrast` appears only beside the clustered interval, labelled, to exhibit
  the design effect. It is never published alone.

## `MeasurementCard` — the published artifact

```json
{ "verdict": "NOT_VERIFIED", "generated": "...", "corpus_rev": "...",
  "claims": [ { "id": "H1", "statement": "...", "status": "UNTESTED",
                "source": "results/h1_duty_cycle.json", "interval": null } ],
  "known_gaps": ["no expert agreement statistic", "peak force unobservable"] }
```

- Generated by `scripts/refresh_card.py`. Never hand-edited.
- `verdict` ∈ {`NOT_VERIFIED`, `VERIFIED`}. It is `NOT_VERIFIED` while any claim is
  `UNTESTED` or any entry in `known_gaps` is unclosed, and `make card` exits nonzero unless
  it is `VERIFIED`. The gaps above are open by construction in v1, so v1's card is
  `NOT_VERIFIED` and that is the honest state, not a failure.
- Every `source` is a path that must exist and must contain the number the claim states.

## Changelog

| Rev | Date | Change | Decision |
|---|---|---|---|
| `contracts/v1` | 2026-09-05 | Initial freeze, before `src/` exists. | D001 |
