"""H1b: does duty cycle at 4 Hz agree with duty cycle at 8 Hz?

`docs/PRE-REGISTRATION.md` H1: *"duty cycle at 4 Hz agrees with duty cycle at 8 Hz to within
0.02 mean absolute difference"*, falsified on the pilot factory. This is the half of H1 that
needs no second label source -- the same probe scores both rates, so it isolates the sampling
rate from the labeller.

A clip counts only if **both** rates scored it `ok`. `exposure/duty.py`'s `agreement` refuses to
compute over an empty pairing rather than returning a passing zero, which is the behaviour that
matters here: a rate that scored nothing would otherwise agree with anything.

Reports pass/fail. Values stay in `results/pilot/` (D018).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import sample_times  # noqa: E402
from cyclegraph.exposure.duty import (  # noqa: E402
    H1B_SAMPLING_RATE_MAD,
    agreement,
    duty_cycle_estimate,
)
from cyclegraph.models import ClipRef, DutyCycleEstimate  # noqa: E402


def _estimates(labels_path: Path, refs: list[ClipRef],
               fps: float) -> list[DutyCycleEstimate]:
    by_clip: dict[str, dict[float, bool | None]] = {}
    for line in labels_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by_clip.setdefault(row["clip_id"], {})[round(float(row["t_s"]), 4)] = (
            row.get("manipulation"))
    out: list[DutyCycleEstimate] = []
    for clip in refs:
        series = [by_clip.get(clip.clip_id, {}).get(round(t, 4))
                  for t in sample_times(clip.duration_s, fps_sampled=fps)]
        out.append(duty_cycle_estimate(clip, series, label_source="probe"))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--labels-4hz", default="results/pilot/labels.jsonl")
    parser.add_argument("--labels-8hz", default="results/pilot/labels_8hz.jsonl")
    parser.add_argument("--corpus-rev", default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    parser.add_argument("--out", default="results/pilot/h1b.json")
    args = parser.parse_args(argv)

    for path in (args.labels_4hz, args.labels_8hz):
        if not (ROOT / path).exists():
            print(f"REFUSING: no labels at {path}", file=sys.stderr)
            return 2

    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)

    four = _estimates(ROOT / args.labels_4hz, refs, 4.0)
    eight = _estimates(ROOT / args.labels_8hz, refs, 8.0)
    result = agreement(four, eight, threshold=H1B_SAMPLING_RATE_MAD)

    (ROOT / args.out).write_text(json.dumps({
        "hypothesis": "H1b", "threshold_mad": H1B_SAMPLING_RATE_MAD,
        "n_pairs": result.n_pairs,
        "mean_absolute_difference": result.mean_absolute_difference,
        "holds": result.holds,
        "note": ("Both rates scored by the same probe, so this isolates the sampling rate from "
                 "the labeller. A clip counts only if both rates scored it ok."),
    }, indent=2) + "\n")
    print(f"pilot gates (values stay in {Path(args.out).parent}, D018):")
    print(f"  {'PASS' if result.holds else 'FAIL'}  H1b: duty cycle at 4 Hz agrees with 8 Hz "
          f"within the pre-registered {H1B_SAMPLING_RATE_MAD} mean absolute difference")
    print(f"  clips scored ok by both rates: {result.n_pairs} of {len(refs)}")
    return 0 if result.holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
