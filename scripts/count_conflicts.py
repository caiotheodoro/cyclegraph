"""How often the detector and the labeller contradict each other, over the whole pilot.

`docs/DECISIONS.md` D022 drops a detector box on a frame the labeller called
`hands_visible: 0`, and `docs/BENCHMARK.md` publishes that count as its own row so a reader can
tell a detector miss from a labeller miss. `scripts/build_signal.py` counts it and **prints**
it, per invocation; nothing writes it down, and sharding the pilot across processes gives each
one a fraction of it. So the number `docs/BENCHMARK.md` promises did not exist anywhere.

This recomputes it from the two inputs, which is cheap and needs no decode: the join is on
`(clip_id, t_s)` and the rule is one boolean. Values stay in `results/` (D018).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import sample_times  # noqa: E402
from cyclegraph.signal.frames import box_is_contradicted  # noqa: E402
from cyclegraph.signal.ports import FrameLabel  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default="results/pilot/labels.jsonl")
    parser.add_argument("--detections", default="results/pilot/detections.jsonl")
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--corpus-rev",
                        default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    parser.add_argument("--out", default="results/pilot/conflicts.json")
    args = parser.parse_args(argv)

    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)

    labels: dict[tuple[str, float], FrameLabel] = {}
    for line in (ROOT / args.labels).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        labels[(row["clip_id"], round(float(row["t_s"]), 3))] = FrameLabel(
            manipulation=row.get("manipulation"),
            hands_visible=row.get("hands_visible"),
            unreadable_reason=row.get("unreadable_reason"),
        )

    tally: Counter[str] = Counter()
    for line in (ROOT / args.detections).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        tally["samples"] += 1
        label = labels.get((row["clip_id"], round(float(row["t_s"]), 3)))
        if label is None:
            tally["no_label_at_this_instant"] += 1
            continue
        if not row["boxes"]:
            tally["detector_found_no_box"] += 1
            continue
        tally["detector_found_a_box"] += 1
        if label.hands_visible is None:
            tally["box_on_unreadable_frame"] += 1
        elif box_is_contradicted(label):
            tally["box_dropped_labeller_says_no_hand"] += 1
        else:
            tally["box_kept"] += 1

    samples = tally["samples"]
    # Every category is written explicitly, including the ones that did not occur: `Counter`
    # does not insert on lookup, so a measured zero would have been *absent* from the JSON --
    # the inverse of this project's own rule (D064).
    for key in ("no_label_at_this_instant", "detector_found_no_box", "detector_found_a_box",
                "box_on_unreadable_frame", "box_dropped_labeller_says_no_hand", "box_kept"):
        tally.setdefault(key, 0)
    # BENCHMARK's row is the labeller-says-no-hand drop. The unreadable-frame drop is a
    # different cause and is reported separately rather than summed into it.
    dropped = tally["box_dropped_labeller_says_no_hand"]
    planned = sum(len(sample_times(c.duration_s)) for c in refs)
    complete = samples == planned
    payload = {
        "what_this_is": (
            "docs/BENCHMARK.md's 'box dropped: labeller reported no visible hand' row, over the "
            "whole pilot. Recomputed from labels and detections; build_signal only prints it, "
            "per invocation. Values stay in results/ (D018)."),
        "rule": "docs/DECISIONS.md D022 and D056; one definition in signal/frames.py",
        **dict(tally),
        "planned_samples": planned,
        "covers_the_plan": complete,
        "dropped_rate_of_samples": round(dropped / samples, 6) if samples else None,
        "dropped_rate_of_boxed": (round(dropped / tally["detector_found_a_box"], 6)
                                  if tally["detector_found_a_box"] else None),
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.out}")
    # Counts stay in the file. What is printed is the shape of the answer, not the numbers.
    # The old check summed the three branches and compared them to their own total, which is
    # an identity: it could not fail on any input. What can fail is whether the detections
    # cover the manifest's sample plan -- the thing this file is a denominator for (D064).
    print(f"  {'PASS' if complete else 'FAIL'}  detections cover the manifest's sample plan "
          f"({samples} rows against {planned} planned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
