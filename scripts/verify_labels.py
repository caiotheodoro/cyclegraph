"""Every clip in the manifest has exactly the rows its sample plan calls for.

`docs/DECISIONS.md` D043: a worker killed mid-clip leaves rows behind, and a resume that
treats their existence as proof of completion skips past the hole. The labeller's own resume
now checks this, but a resume check is a statement about what the labeller believed while it
ran. This is a statement about the artifact that came out, made by a different piece of code,
and it is what the pilot's completeness claim rests on.

Counts only. `docs/DECISIONS.md` D018 keeps pilot values in `results/`; nothing here prints a
duty cycle, a per-worker figure or a per-factory one. Exits non-zero if any clip is short,
long, absent or unknown to the manifest.
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--labels", default="results/pilot/labels.jsonl")
    parser.add_argument("--corpus-rev",
                        default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    args = parser.parse_args(argv)

    labels = ROOT / args.labels
    if not labels.exists():
        print(f"REFUSING: no labels at {labels}", file=sys.stderr)
        return 2

    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=args.corpus_rev)
    expected = {c.clip_id: len(sample_times(c.duration_s)) for c in refs}

    counted: Counter[str] = Counter()
    revisions: set[str] = set()
    for line in labels.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            counted[row["clip_id"]] += 1
            revisions.add(row.get("corpus_rev", ""))

    short = [c for c, n in expected.items() if counted.get(c, 0) < n]
    over = [c for c, n in expected.items() if counted.get(c, 0) > n]
    missing = [c for c in expected if c not in counted]
    unknown = [c for c in counted if c not in expected]

    print(f"clips in manifest: {len(expected)}")
    print(f"clips with labels: {len(counted)}")
    print(f"rows: {sum(counted.values())} of {sum(expected.values())} planned")
    print(f"corpus revisions present: {len(revisions)}")

    ok = True
    for name, group in (("absent", missing), ("short", short), ("over-long", over),
                        ("not in the manifest", unknown)):
        # A clip id is a factory/worker identifier, so the ids themselves are not printed --
        # only how many there are (docs/HANDOFF.md's reporting floor).
        if group:
            ok = False
            print(f"  FAIL  {len(group)} clips {name}")
    if len(revisions) > 1:
        ok = False
        print("  FAIL  rows from more than one corpus revision; they are never pooled")
    if ok:
        print("  PASS  every clip has exactly the rows its sample plan calls for")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
