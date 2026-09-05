#!/usr/bin/env python3
"""Bout frequency by both methods, for every clip in a manifest. `docs/METHOD.md` E5.

Reads the manipulation series a labeller wrote and produces a `FrequencyEstimate` per clip on
each path: spectral (the cross-check that never segments) and transition-counting (the
cross-check's own cross-check, which H2a compares it against).

Refuses without labels rather than substituting anything. An unwritten instant read as a
negative would shorten every bout and raise the count, which is the flattering direction.

**H2b is not evaluable as specified.** `docs/DECISIONS.md` D033 measured that white noise
clears the rubric's 6x peak-power floor at every clip duration in this corpus, so a resolvable
fraction computed here would be satisfiable by a corpus with no repetition in it. The script
computes and prints it, labelled, and does not treat clearing 70% as evidence of anything.

Usage:
    python3 scripts/estimate_frequency.py --labels results/pilot/labels.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402
from cyclegraph.cycles.spectral import (  # noqa: E402
    H2B_RESOLVABLE_FRACTION,
    resolvable_fraction,
    spectral_frequency,
)
from cyclegraph.cycles.transitions import (  # noqa: E402
    H2A_RELATIVE_DIFFERENCE,
    relative_difference,
    transition_frequency,
)
from cyclegraph.signal.stores import JsonlLabelStore  # noqa: E402

PILOT_REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--out-dir", default="results/pilot")
    parser.add_argument("--corpus-rev", default=PILOT_REV)
    args = parser.parse_args(argv)

    labels_path = ROOT / args.labels
    if not labels_path.exists():
        print(f"REFUSING: no labels at {labels_path}", file=sys.stderr)
        print(
            "\nThe frequency axis reads a manipulation series that a labeller produced. An\n"
            "instant nobody scored is not a negative, and reading it as one would shorten\n"
            "every bout and raise the count -- the flattering direction. docs/HANDOFF.md\n"
            "names the labeller as one of W3's two blocking dependencies.",
            file=sys.stderr,
        )
        return 2

    store = JsonlLabelStore.from_path(labels_path)
    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    spectral_all = []
    agreements: list[float] = []

    with (out_dir / "frequency.jsonl").open("w") as handle:
        for clip in refs:
            series = [store.label(clip.clip_id, t).manipulation
                      for t in sample_times(clip.duration_s)]
            spectral = spectral_frequency(clip, series, fps=ANALYSIS_HZ,
                                          label_source=store.provenance.label_source)
            counted = transition_frequency(clip, series, fps=ANALYSIS_HZ,
                                           label_source=store.provenance.label_source)
            handle.write(spectral.model_dump_json() + "\n")
            handle.write(counted.model_dump_json() + "\n")
            spectral_all.append(spectral)
            if spectral.hz is not None and counted.hz is not None:
                agreements.append(relative_difference(spectral.hz, counted.hz))

    print(f"pilot gates (values stay in {args.out_dir}, D018):")
    if agreements:
        mean_rel = sum(agreements) / len(agreements)
        print(f"  {'PASS' if mean_rel <= H2A_RELATIVE_DIFFERENCE else 'FAIL'}  "
              f"H2a: spectral and transition-counting agree")
    else:
        print("  FAIL  H2a: no clip resolved on both paths")
    fraction = resolvable_fraction(spectral_all)
    print(f"  {'PASS' if fraction >= H2B_RESOLVABLE_FRACTION else 'FAIL'}  "
          f"H2b: resolvable fraction clears the pre-registered bound")
    print("  NOT EVIDENCE  the 6x peak floor does not separate signal from noise at these"
          " clip lengths (docs/DECISIONS.md D033); read H2b's verdict as untrustworthy until"
          " that is amended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
