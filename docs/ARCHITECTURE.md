# Architecture

Module boundaries, fixed before code. Each unit has one purpose, a schema at its edge
(`CONTRACTS.md`), and no knowledge of its callers.

```
  raw shards (h265, gated)
        |
   [ corpus ]  ClipRef                   shard access, byte ranges, decode, 4 Hz frame pairs
        |
   [ signal ]  FrameSignal               per-frame manipulation, hand boxes, flow samples
        |
        +-------------------+--------------------------+
        |                   |                          |
   [ cycles ]          [ signal/speed ]           [ exposure ]
   FrequencyEstimate   HandSpeedEstimate          DutyCycleEstimate
   bout frequency,     RMS residual hand speed    fraction of scored frames
   lower bound         (primary)
        |                   |                          |
        +-------------------+--------------------------+
                            |
                     [ exposure ]  HALScore     mapping ∈ {radwin, akkas}, scale_rev
                            |
                     [ estimation ]  ExposureAggregate   cluster bootstrap over
                            |                           factory_id/worker_id; strata
                        [ card ]  MeasurementCard
```

## `corpus`

**Owns.** Locating a clip inside the WebDataset shards, decoding it, and sampling frames at
the analysis rate — as pairs (t, t + 1/fps) so the speed path has a flow baseline. Emits
`ClipRef` and raw frames. Nothing else in the repository knows what a tar shard is.

**Depends on.** A gated Hugging Face token and a pinned revision. Nothing internal.

**Seam:** *the pinned revision is a property of the record, not of the process.* Two
`ClipRef`s with different `corpus_rev` are never pooled, and the check lives on the record
rather than in a global. A module that read the revision from configuration would silently
mix corpora after a re-pin, and the mixing would be invisible in every number downstream.

## `signal`

**Owns.** Turning a clip's sampled frames into a `FrameSignal` — the per-frame manipulation
and hand-count series, the detected hand-box width, and the flow method — with unreadable
frames and undetected hands marked `null`. `signal/speed.py` turns the same frames into a
`HandSpeedEstimate`: ego-motion from the mask complement, residual flow inside the box, the
clip's RMS.

**Depends on.** `corpus`, a label source, a hand detector, a flow estimator.

**Seams:** *`label_source` is carried, never defaulted.* Judge, probe and human labels have
different error structures and are never pooled inside one estimate. H1 exists to measure
how much the choice matters; a module that defaulted the field would make H1 unanswerable by
erasing its independent variable. *A missing hand or a failed flow is `null` with a reason,
never zero.* Zero is the flattering direction (`docs/RED-TEAM.md` A15), and a
`HandSpeedEstimate` cannot be built from a region prior in place of a detector.

## `cycles`

**Owns.** `FrequencyEstimate` by both methods — spectral, and transition-counting as the
cross-check H2a tests. Both measure manipulation-*bout* frequency, a lower bound on exertion
frequency (`docs/DECISIONS.md` D014), and every record says so.

**Depends on.** `signal`. Not on `exposure`; frequency does not know what it will be used
for.

**Seam:** *unresolvable is a value, not an absence.* A clip with no dominant cycle carries
`hz: null` with `status: "no_peak"` and is counted. The tempting simplification — treat it
as zero frequency — would convert "no detectable cycle" into "no repetition" and is the
single largest way this path could understate exposure.

## `exposure`

**Owns.** `DutyCycleEstimate` and `HALScore`, and the two pure mapping functions
(`exposure/hal.py`) with golden tests against the papers' table cells.

**Depends on.** `signal` for duty cycle and speed, `cycles` for bout frequency.

**Seams:** *the force axis is structurally absent, not missing.* `HALScore.force_axis` is
`null` and `tlv_evaluable` is `false` on every record, with a reason string, so that a
reader sees the absence as a value rather than having to notice an omission. This module has
no code path that could ever populate it. *The mapping names its input.* `mapping = radwin`
requires `hz`, `mapping = akkas` requires `rms_speed_mm_s`, and a record with the wrong one
present and the right one null is invalid rather than silently mapped from the other.

## `estimation`

**Owns.** `ExposureAggregate`: cluster bootstrap over the composite `factory_id/worker_id`,
the design effect in both readings, the iid interval that sits beside it for contrast, and
the size-tercile strata.

**Depends on.** `exposure`. Inherits the bootstrap approach from
`../vernier/src/vernier/estimation/bootstrap.py`; `docs/LINEAGE.md` records what is reused
and what is rewritten.

**Seam, and it is the one that matters most in this repository:** *the aggregation floor is
a property of the report, not a default.* `cluster_unit`, `stratum`, `k_factories`,
`k_workers`, `max_factory_share` and `aggregation_reason` are required with no default
value. A module able to emit a per-worker, per-factory or sub-floor number is an ethics
failure whether or not anything calls it, so `ExposureAggregate` has no field that can
carry an identifier, its validator rejects any string that looks like one, and the k-floor
is checked on construction — the constraint is in the schema, not in this module's
discipline. `docs/ETHICS.md` is the reason; `docs/DECISIONS.md` D019 is the rule.

## `card`

**Owns.** `MeasurementCard`. Every claim cites a path under `results/` that must exist, must
contain the number the claim states, and must contain no identifier
(`scripts/validate.py`).

**Depends on.** Everything, and nothing depends on it.

**Seam:** *the card is generated, never written.* A hand-edited card is a transcribed
number, and transcribed numbers are how a claim quietly stops being true. `make card` exits
nonzero unless the verdict is `VERIFIED`, and v1's verdict is `NOT_VERIFIED` by construction
because `docs/COVERAGE.md`'s gaps are open.

## Known seams

1. `corpus_rev` on the record, not in config.
2. `label_source` carried, never defaulted.
3. Unresolvable frequency, missing hand, failed flow: values with reasons, never zero.
4. The force axis structurally absent.
5. The mapping names its input.
6. **The aggregation floor as required arguments and a validator.** The one that would
   cause real harm.
7. The card generated, never written, and identifier-free.

`docs/WAVES.md` turns each into a per-unit review checklist.
