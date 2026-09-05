#!/usr/bin/env python3
"""Fit the manipulation probe on inherited judge labels. `docs/METHOD.md` E3.

Trains a linear head over frozen DINOv2 features against the `manipulation` column of
`../vernier`'s stored judge labels, and writes the head with a held-out fidelity report beside
it. Nothing is bought: the labels and the features were already paid for by the sibling
(`docs/LINEAGE.md`, `docs/DECISIONS.md` D038).

**The fidelity report is the point, not the head.** A probe distilled from a judge inherits
the judge's errors and adds its own, and `docs/RED-TEAM.md` A1 is exactly that objection. So
accuracy is never reported without the majority-class baseline it has to beat -- on a corpus
where three frames in four are manipulating, a probe that always answered "yes" would look
respectable -- and balanced accuracy is reported at all.

**What this cannot tell you.** H1a's statistic is the *per-clip* mean absolute difference in
duty cycle between two label sources. These frames come from the evaluation release, whose
`frame_id` carries no clip linkage (`docs/DECISIONS.md` D011), so no per-clip quantity can be
computed from them at all. The aggregate prevalence gap printed here is a much weaker thing --
errors cancel across a pool in a way they do not within a clip -- and it is labelled as such.
H1a is answerable only by running two labellers over raw-release pilot clips.

Usage:
    python3 scripts/train_probe.py
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from labellers.probe import (  # noqa: E402
    BACKBONE,
    ManipulationProbe,
    cross_validated_fidelity,
    inherited_training_set,
)

VERNIER = ROOT.parent / "vernier"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", default=str(VERNIER / "data" / "dinov2_features.json"))
    parser.add_argument("--labels", default=str(VERNIER / "data" / "rung1_stored_labels.json"))
    parser.add_argument("--out", default="results/probe_manipulation.joblib")
    parser.add_argument("--report", default="results/probe_fidelity.json")
    args = parser.parse_args(argv)

    features_path, labels_path = Path(args.features), Path(args.labels)
    for path in (features_path, labels_path):
        if not path.exists():
            print(f"REFUSING: {path} not found.", file=sys.stderr)
            print("These are ../vernier's assets; docs/LINEAGE.md records what is inherited "
                  "and this stage does not regenerate them.", file=sys.stderr)
            return 2

    ids, features, manipulation = inherited_training_set(features_path, labels_path)
    fidelity = cross_validated_fidelity(features, manipulation)
    probe = ManipulationProbe.fit(features, manipulation)
    probe.save(ROOT / args.out)

    report = {
        "backbone": BACKBONE,
        "target": "manipulation",
        "n_frames": len(ids),
        "source": "../vernier stored judge labels (gemini-2.5-flash, prompt variant P0b)",
        "fidelity": asdict(fidelity),
        "what_this_is_not": (
            "H1a's statistic. That is a per-clip mean absolute difference in duty cycle, and "
            "these frames are from the evaluation release, whose frame_id carries no clip "
            "linkage (docs/DECISIONS.md D011). The aggregate prevalence gap below is weaker: "
            "errors cancel across a pool in a way they do not within a clip."
        ),
    }
    (ROOT / args.report).write_text(json.dumps(report, indent=2) + "\n")

    print(f"trained on {fidelity.n} frames from {BACKBONE} features")
    print(f"  accuracy          {fidelity.accuracy:.4f}")
    print(f"  majority baseline {fidelity.majority_baseline:.4f}  "
          f"{'BEATS' if fidelity.beats_baseline else 'DOES NOT BEAT'} it")
    print(f"  balanced accuracy {fidelity.balanced_accuracy:.4f}")
    print(f"  aggregate prevalence: judge {fidelity.aggregate_prevalence_judge:.4f} "
          f"vs probe {fidelity.aggregate_prevalence_probe:.4f}  "
          f"(NOT H1a; see {args.report})")
    print(f"\nwrote {args.out} and {args.report}")
    return 0 if fidelity.beats_baseline else 1


if __name__ == "__main__":
    raise SystemExit(main())
