#!/usr/bin/env python3
"""HAL per clip, and the corpus aggregate. `docs/METHOD.md` E4, E6 and E8.

Reads the per-clip records earlier stages wrote, computes a duty cycle, maps it to HAL by the
published equations, and -- with `--aggregate` -- assembles the one publishable row plus the
bootstrap replicates that make its interval reproducible without a grouping key.

Refuses without the inputs. There is no default labeller and no fallback detector: a HAL
computed from a substituted input would look exactly like one computed from a real one.

**Pilot output is pass/fail.** The pilot factory is nameable, so its HAL distribution is a
per-factory number and stays in `results/` (D018). The aggregate path prints corpus-level
counts, which are not.

Usage:
    python3 scripts/score_hal.py --labels results/pilot/labels.jsonl
    python3 scripts/score_hal.py --labels results/pilot/labels.jsonl --aggregate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402
from cyclegraph.estimation.aggregate import (  # noqa: E402
    ClipObservation,
    build_aggregate,
    replicate_means,
    variance_components,
)
from cyclegraph.exposure.duty import duty_cycle_estimate  # noqa: E402
from cyclegraph.exposure.score import score_speed_path  # noqa: E402
from cyclegraph.models import (  # noqa: E402
    COVERAGE_FLOOR,
    FLOW_NULL_CEILING,
    HandSpeedEstimate,
)
from cyclegraph.signal.stores import JsonlLabelStore  # noqa: E402

PILOT_REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--speeds", default="results/pilot/hand_speed.jsonl")
    parser.add_argument("--out-dir", default="results/pilot")
    parser.add_argument("--corpus-rev", default=PILOT_REV)
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args(argv)

    labels_path, speeds_path = ROOT / args.labels, ROOT / args.speeds
    missing = [str(p) for p in (labels_path, speeds_path) if not p.exists()]
    if missing:
        print("REFUSING: this stage consumes records earlier stages wrote.", file=sys.stderr)
        for path in missing:
            print(f"  missing: {path}", file=sys.stderr)
        print(
            "\nDuty cycle needs a manipulation series and the speed path needs a\n"
            "HandSpeedEstimate with a real detector behind it. A HAL computed from a\n"
            "substituted input looks exactly like one computed from a real one, which is why\n"
            "there is no fallback here (docs/HANDOFF.md).",
            file=sys.stderr,
        )
        return 2

    store = JsonlLabelStore.from_path(labels_path)
    speeds = {
        s.clip_id: s for s in (
            HandSpeedEstimate.model_validate_json(line)
            for line in speeds_path.read_text().splitlines() if line.strip()
        )
    }
    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    observations: list[ClipObservation] = []
    scored = 0

    with (out_dir / "hal.jsonl").open("w") as handle:
        for clip in refs:
            series = [store.label(clip.clip_id, t).manipulation
                      for t in sample_times(clip.duration_s)]
            duty = duty_cycle_estimate(clip, series,
                                       label_source=store.provenance.label_source)
            speed = speeds.get(clip.clip_id)
            if speed is None:
                continue
            hal = score_speed_path(duty, speed)
            handle.write(hal.model_dump_json() + "\n")
            scored += 1
            if hal.status == "ok" and hal.hal is not None:
                observations.append(ClipObservation(clip.factory_id, clip.worker_id, hal.hal))

    # H2c over every speed record, whatever wrote them. `build_signal` reports the same gate
    # for the clips one invocation happened to see; sharding the pilot across processes gives
    # each of those a partial denominator, and a gate computed on part of the pilot is not the
    # pre-registered gate. This one reads the whole file.
    total_samples = sum(e.n_samples for e in speeds.values())
    boxed = sum(e.n_with_box for e in speeds.values())
    nulls = sum(e.n_flow_null for e in speeds.values())
    coverage = boxed / total_samples if total_samples else 0.0
    # A rate over no boxed samples is 0.0, which would print PASS on no data at all. An
    # unevaluable gate is not a satisfied one; it reports FAIL and says which it is.
    null_rate = nulls / boxed if boxed else 0.0
    null_evaluable = boxed > 0

    print(f"pilot gates (values stay in {args.out_dir}, D018):")
    print(f"  {'PASS' if scored else 'FAIL'}  every clip with a speed record produced a HAL")
    print(f"  {'PASS' if observations else 'FAIL'}  at least one clip scored on the speed path")
    print(f"  {'PASS' if coverage >= COVERAGE_FLOOR else 'FAIL'}  "
          f"H2c: hand-box coverage clears the pre-registered {COVERAGE_FLOOR:.0%} floor")
    print(f"  {'PASS' if null_evaluable and null_rate <= FLOW_NULL_CEILING else 'FAIL'}  "
          f"H2c: flow-null rate within the pre-registered {FLOW_NULL_CEILING:.0%} ceiling"
          f"{'' if null_evaluable else ' (no boxed sample: not evaluable, not satisfied)'}")

    if not args.aggregate:
        return 0 if scored else 1

    if len(observations) < 2:
        print("\nREFUSING to aggregate: nothing to aggregate.", file=sys.stderr)
        return 1

    outcome = build_aggregate(
        observations, stratum="corpus", stratum_definition="docs/DECISIONS.md#d019",
        mapping="akkas-2015-speed-dc", label_source=store.provenance.label_source,
        corpus_rev=args.corpus_rev, generated=datetime.now(timezone.utc),
    )
    if outcome.suppressed:
        print(f"\ncorpus: SUPPRESSED -- {outcome.suppressed_reason}")
        print("A stratum below the D019 floor is printed as suppressed, never omitted.")
        return 0

    aggregate = outcome.aggregate
    assert aggregate is not None
    (ROOT / "results" / "exposure_aggregate.json").write_text(
        aggregate.model_dump_json(indent=2) + "\n")
    (ROOT / "results" / "bootstrap_replicates.json").write_text(
        json.dumps({"seed": aggregate.seed, "b": aggregate.bootstrap_b,
                    "means": replicate_means(observations)}) + "\n")
    components = variance_components(observations)
    print(f"\ncorpus: {aggregate.n_clips} clips, {aggregate.n_workers} workers, "
          f"{aggregate.n_factories} factories")
    print(f"  H4 variance ratio: {'HOLDS' if components.holds else 'FAILED'}")
    print(f"  H5 design effect:  {aggregate.design_effect:.3f} "
          f"(width ratio {aggregate.design_effect_width_ratio:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
