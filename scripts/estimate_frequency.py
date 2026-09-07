#!/usr/bin/env python3
"""Bout frequency by both methods, for every clip in a manifest. `docs/METHOD.md` E5.

Reads the manipulation series a labeller wrote and produces a `FrequencyEstimate` per clip on
each path: spectral (the cross-check that never segments) and transition-counting (the
cross-check's own cross-check, which H2a compares it against).

Refuses without labels rather than substituting anything. An unwritten instant read as a
negative would shorten every bout and raise the count, which is the flattering direction.

**H2b's floor was fixed before this ran** (`docs/DECISIONS.md` D034): the resolvability
threshold is now the ratio white noise of the same length would exceed 5% of the time, so
clearing it is evidence rather than arithmetic. What it is *not* evidence of is that the peak
sits at a bout frequency -- resolvability says a peak is tall, not that it is in the right
band, and D039 records what that turned out to mean here.

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
    exertion_segments,
    null_bounded_segments,
    scored_seconds,
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
    # D042's disclosure. A null landing inside a bout ends it and starts another, so part of
    # the segment count is where the labels ran out rather than what the hands did. Written
    # per clip beside the estimates, never subtracted from them, and never printed: these are
    # pilot values and D018 keeps them in `results/`.
    boundaries = (out_dir / "bout_boundaries.jsonl").open("w")

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
            boundaries.write(json.dumps({
                "clip_id": clip.clip_id,
                "corpus_rev": clip.corpus_rev,
                "n_segments": len(exertion_segments(
                    clip, series, fps=ANALYSIS_HZ,
                    label_source=store.provenance.label_source)),
                "n_null_bounded": null_bounded_segments(series, fps=ANALYSIS_HZ),
                "scored_s": scored_seconds(series, fps=ANALYSIS_HZ),
                "duration_s": clip.duration_s,
            }) + "\n")
            if spectral.hz is not None and counted.hz is not None:
                agreements.append(relative_difference(spectral.hz, counted.hz))
    boundaries.close()

    print(f"  bout boundaries written to {args.out_dir}/bout_boundaries.jsonl (D042); "
          f"docs/BENCHMARK.md publishes them beside the segment count")
    print(f"pilot gates (values stay in {args.out_dir}, D018):")
    h2a_holds = bool(agreements) and (sum(agreements) / len(agreements)) <= H2A_RELATIVE_DIFFERENCE
    if agreements:
        print(f"  {'PASS' if h2a_holds else 'FAIL'}  "
              f"H2a: spectral and transition-counting agree")
    else:
        print("  FAIL  H2a: no clip resolved on both paths")
    fraction = resolvable_fraction(spectral_all)
    h2b_holds = fraction >= H2B_RESOLVABLE_FRACTION
    print(f"  {'PASS' if h2b_holds else 'FAIL'}  "
          f"H2b: resolvable fraction clears the pre-registered bound")

    # The card reads a verdict per claim from `results/`; it does not parse stdout, and a claim
    # with no file is UNTESTED -- which is what H2a and H2b were reporting as, long after they
    # had been measured, because the gates printed and persisted nothing
    # (`docs/DECISIONS.md` D062). H2 is the conjunction: it is recoverable only if both halves
    # hold, and H2c is written by `scripts/score_hal.py` from the records it reads.
    def _verdict(name: str, holds: bool, note: str) -> None:
        (out_dir / f"{name}.json").write_text(json.dumps({
            "claim": name, "status": "HOLDS" if holds else "FAILED",
            "corpus_rev": args.corpus_rev, "note": note,
        }, indent=2) + "\n")

    _verdict("h2a", h2a_holds,
             "mean relative difference between the spectral and transition-counting "
             "frequencies, over clips both paths resolved")
    _verdict("h2b", h2b_holds,
             "fraction of clips carrying a resolvable dominant cycle, against the "
             "length-dependent floor D034 derived")
    below = sum(1 for e in spectral_all if e.hz is not None and e.hz < 0.05)
    resolved = sum(1 for e in spectral_all if e.hz is not None)
    if resolved:
        print(f"  READ WITH D039  {below}/{resolved} resolved peaks sit below 0.05 Hz, the "
              f"slowest cycle docs/RUBRIC.md's own 60 s floor contemplates. A tall peak in "
              f"the wrong band still clears H2b.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
