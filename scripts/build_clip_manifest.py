#!/usr/bin/env python3
"""Build the clip manifest and reconcile it against every published count. `docs/METHOD.md` E1.

Never downloads a shard. A tar member header is 512 bytes at a computable offset, so the whole
corpus indexes with small ranged reads (`../vernier/docs/DECISIONS.md` D071).

Output is JSONL, appended per shard and resumable, because a scan that loses everything on
interruption gets re-spent.

The reconciliation is three-way on purpose. The vendor's dataset card and the corpus itself
disagree about how many workers shipped, and a gate against a single source would either
inherit the card's error or silently contradict the sibling that already measured it. Two
independent scans agreeing is the actual evidence.

Usage:
    python3 scripts/build_clip_manifest.py --factory factory_001
    python3 scripts/build_clip_manifest.py --all          # the corpus-level reconciliation
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.manifest import (  # noqa: E402
    MetadataRow,
    is_too_short,
    PublishedCounts,
    clip_refs,
    clip_records_from_shard,
    pilot_factory,
    reconcile,
)
from cyclegraph.corpus.shards import (  # noqa: E402
    REPO_ID,
    ShardReader,
    factory_ids,
    list_shards,
    shards_for_factory,
)

# The vendor's own dataset card, quoted in ../vernier/docs/ETHICS.md.
VENDOR = PublishedCounts(source="vendor dataset card", n_factories=85, n_clips=192_900,
                         n_workers=2_153, total_duration_s=10_000 * 3600.0)
# ../vernier/docs/UPSTREAM-FINDINGS.md F12, measured over all 19,495 shards.
VERNIER = PublishedCounts(source="vernier F12 scan", n_factories=85, n_clips=192_903,
                          n_workers=2_144)


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


def _scanned(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line)["shard"] for line in path.read_text().splitlines() if line.strip()}


def _scan_one(shard: str, token: str | None) -> tuple[str, list[MetadataRow], int, str | None]:
    try:
        reader = ShardReader(REPO_ID, shard, token)
        contents = clip_records_from_shard(shard, reader.read_range)
        return shard, contents.rows, contents.dropped, None
    except Exception as exc:  # a failed shard is recorded, never silently skipped
        return shard, [], 0, f"{type(exc).__name__}: {exc}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory", default=None, help="one factory; default is the pilot")
    parser.add_argument("--all", action="store_true", help="scan the whole corpus")
    parser.add_argument("--out", default=None)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args(argv)

    token = _token()
    shards, revision = list_shards(REPO_ID, token)
    print(f"repo {REPO_ID} at {revision}: {len(shards)} shards, "
          f"{len(factory_ids(shards))} factories", flush=True)

    if args.all:
        selected, label = shards, "corpus"
    else:
        factory = args.factory or pilot_factory(factory_ids(shards))
        selected = shards_for_factory(shards, factory)
        label = factory
        print(f"pilot factory (first in sorted manifest, D012): {factory}", flush=True)

    out = ROOT / (args.out or f"results/pilot/clips_{label}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = _scanned(out)
    todo = [s for s in selected if s not in done]
    print(f"{len(selected)} shards selected, {len(done)} already scanned, {len(todo)} to go",
          flush=True)

    failures: list[str] = []
    dropped_total = 0
    with out.open("a") as handle, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, (shard, rows, dropped, error) in enumerate(
            pool.map(lambda s: _scan_one(s, token), todo), 1
        ):
            if error is not None:
                failures.append(f"{shard}: {error}")
                continue
            dropped_total += dropped
            for row in rows:
                handle.write(json.dumps(asdict(row)) + "\n")
            handle.flush()
            if i % 250 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} shards", flush=True)

    rows = [MetadataRow(**json.loads(line))
            for line in out.read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev=revision)
    print(f"\nfailed shards: {len(failures)}")
    print(f"sidecars dropped (orphan or oversized): {dropped_total}")
    for f in failures[:10]:
        print(f"  {f}")

    n_workers = len({(r.factory_id, r.worker_id) for r in refs})
    n_clips = len(refs)
    if args.all:
        print(f"\n{label}: {n_clips} clips, {n_workers} workers, "
              f"{len({r.factory_id for r in refs})} factories, "
              f"{sum(r.duration_s for r in refs) / 3600:.2f} hours")
    else:
        # The pilot factory is nameable (D012), so any count of its clips or workers is a
        # per-factory number. docs/ETHICS.md and D018 allow the gate's verdict to leave
        # results/ and nothing else, so this prints pass/fail and writes the values to the
        # gitignored manifest. A script that printed them would be the leak the aggregation
        # floor exists to prevent, whatever the operator intended to do with the output.
        long_enough = sum(1 for r in refs if not is_too_short(r))
        gates = {
            "manifest built": n_clips > 0,
            "no failed shards": not failures,
            "clips clear the 60 s floor": long_enough == n_clips,
            "more than one worker (D012 degeneracy)": n_workers > 1,
            "enough workers to see within-factory spread (D012)": n_workers >= 5,
        }
        print(f"\n{label} pilot gates (values stay in results/, D018):")
        for name, ok in gates.items():
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not all(gates.values()):
            return 1

    if args.all:
        print("\nreconciliation, three ways:")
        overall = True
        for published in (VENDOR, VERNIER):
            result = reconcile(refs, published)
            print(f"  {published.source}: {'RECONCILES' if result.reconciles else 'MISMATCH'}")
            for m in result.mismatches:
                print(f"      {m}")
            overall = overall and result.reconciles
        print(f"\n  own scan is the third: {len(refs)} clips over {len(shards)} shards "
              f"at {revision}")
        if failures:
            print("  NOT AUTHORITATIVE: some shards failed to read")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
