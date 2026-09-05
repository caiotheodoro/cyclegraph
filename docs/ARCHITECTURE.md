# Architecture

Module boundaries, fixed before code. Each unit has one purpose, a schema at its edge
(`CONTRACTS.md`), and no knowledge of its callers.

```
  raw shards (h265, gated)
        |
   [ corpus ]  ClipRef              shard access, byte ranges, decode, frame sampling
        |
   [ signal ]  FrameSignal          per-frame manipulation series at the fixed rate
        |
        +----------------------------+
        |                            |
   [ cycles ]  FrequencyEstimate     [ exposure ]  DutyCycleEstimate
        |         spectral + counting      |          fraction of scored frames
        +----------------------------+     |
                     |                     |
              [ exposure ]  HALScore  <----+
                     |
              [ estimation ]  ExposureAggregate    cluster bootstrap, design effect
                     |
                 [ card ]  MeasurementCard
```

## `corpus`

**Owns.** Locating a clip inside the WebDataset shards, decoding it, and sampling frames at
the analysis rate. Emits `ClipRef` and raw frames. Nothing else in the repository knows what
a tar shard is.

**Depends on.** A gated Hugging Face token and a pinned revision. Nothing internal.

**Seam:** *the pinned revision is a property of the record, not of the process.* Two
`ClipRef`s with different `corpus_rev` are never pooled, and the check lives on the record
rather than in a global. A module that read the revision from configuration would silently
mix corpora after a re-pin, and the mixing would be invisible in every number downstream.

## `signal`

**Owns.** Turning a clip's sampled frames into a `FrameSignal` — the per-frame manipulation
and hand-count series, with unreadable frames marked `null`.

**Depends on.** `corpus`, and a label source.

**Seam:** *`label_source` is carried, never defaulted.* Judge, probe and human labels have
different error structures and are never pooled inside one estimate. H1 exists to measure
how much the choice matters; a module that defaulted the field would make H1 unanswerable by
erasing its independent variable.

## `cycles`

**Owns.** `FrequencyEstimate` by both methods — spectral, which is primary, and
transition-counting, which is the cross-check H2 tests.

**Depends on.** `signal`. Not on `exposure`; frequency does not know what it will be used
for.

**Seam:** *unresolvable is a value, not an absence.* A clip with no dominant cycle carries
`hz: null` with `status: "no_peak"` and is counted. The tempting simplification — treat it
as zero frequency — would convert "no detectable cycle" into "no repetition" and is the
single largest way this pipeline could understate exposure.

## `exposure`

**Owns.** `DutyCycleEstimate` and `HALScore`.

**Depends on.** `signal` for duty cycle, `cycles` for frequency.

**Seam:** *the force axis is structurally absent, not missing.* `HALScore.force_axis` is
`null` and `tlv_evaluable` is `false` on every record, with a reason string, so that a
reader sees the absence as a value rather than having to notice an omission. This module has
no code path that could ever populate it.

## `estimation`

**Owns.** `ExposureAggregate`: cluster bootstrap over `worker_id`, the design effect, and
the iid interval that sits beside it for contrast.

**Depends on.** `exposure`. Inherits the bootstrap approach from
`../vernier/src/vernier/estimation/bootstrap.py`; `docs/LINEAGE.md` records what is reused
and what is rewritten.

**Seam, and it is the one that matters most in this repository:** *the aggregation floor is
a property of the report, not a default.* `cluster_unit` and `aggregation_reason` are
required arguments with no default value. A module able to emit a per-worker or per-factory
number is an ethics failure whether or not anything calls it, so `ExposureAggregate` has no
field that can carry an identifier — the constraint is in the schema, not in this module's
discipline. `docs/ETHICS.md` is the reason.

## `card`

**Owns.** `MeasurementCard`. Every claim cites a path under `results/` that must exist and
must contain the number the claim states.

**Depends on.** Everything, and nothing depends on it.

**Seam:** *the card is generated, never written.* A hand-edited card is a transcribed
number, and transcribed numbers are how a claim quietly stops being true. `make card` exits
nonzero unless the verdict is `VERIFIED`, and v1's verdict is `NOT_VERIFIED` by construction
because `docs/COVERAGE.md`'s gaps are open.

## Known seams

1. `corpus_rev` on the record, not in config.
2. `label_source` carried, never defaulted.
3. Unresolvable frequency as a value, not an absence.
4. The force axis structurally absent.
5. **The aggregation floor as a required argument.** The one that would cause real harm.
6. The card generated, never written.

`docs/WAVES.md` turns each into a per-unit review checklist.
