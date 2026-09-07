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

    # H1b is pre-registered "on the pilot factory", so the statistic is not computed from part
    # of it. A clip *present* and scored `no_labels` is a legitimate exclusion; a clip whose
    # rows are simply absent means the run has not finished, and averaging over what happens to
    # be there is the partial-denominator mistake D064 and D065 removed from `score_hal`. Put
    # in before H1b's number existed, so it cannot have been shaped by the answer (D067).
    for label, path, rate in (("4 Hz", ROOT / args.labels_4hz, 4.0),
                              ("8 Hz", ROOT / args.labels_8hz, 8.0)):
        counts: dict[str, int] = {}
        for line in path.read_text().splitlines():
            if line.strip():
                cid = json.loads(line)["clip_id"]
                counts[cid] = counts.get(cid, 0) + 1
        short = [c.clip_id for c in refs
                 if counts.get(c.clip_id, 0) != len(sample_times(c.duration_s,
                                                                 fps_sampled=rate))]
        if short:
            (ROOT / args.out).write_text(json.dumps({
                "claim": "H1b", "status": "UNTESTED",
                "reason": (f"the {label} labels cover {len(refs) - len(short)} of {len(refs)} "
                           f"clips; H1b is pre-registered on the pilot and is not computed "
                           f"from part of it"),
            }, indent=2) + "\n")
            print(f"  NOT EVALUABLE  the {label} labels cover "
                  f"{len(refs) - len(short)} of {len(refs)} clips; H1b is pre-registered on "
                  f"the pilot and is not computed from part of it")
            return 1

    four = _estimates(ROOT / args.labels_4hz, refs, 4.0)
    eight = _estimates(ROOT / args.labels_8hz, refs, 8.0)
    result = agreement(four, eight, threshold=H1B_SAMPLING_RATE_MAD)

    (ROOT / args.out).write_text(json.dumps({
        "claim": "H1b", "status": "HOLDS" if result.holds else "FAILED",
        "threshold_mad": H1B_SAMPLING_RATE_MAD,
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
