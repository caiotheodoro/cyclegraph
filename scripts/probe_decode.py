#!/usr/bin/env python3
"""Measure the decode failure rate for `docs/METHOD.md` E2's sub-1% gate.

The gate has two failure modes and they cost very different amounts to measure. A clip that
will not open at all is detectable from its first frames, so every clip in the manifest is
probed. A clip that opens and then truncates is only detectable by decoding it to the end,
which means pulling the whole mp4, so that is measured on a sample and reported as a sample.

`docs/DECISIONS.md` D023 fixes the denominator as **pairs**, with the per-clip rate beside it.
A clip that fails to open contributes all of its planned pairs to the numerator, which is why
the two rates differ and why both are printed.

Pilot output is pass/fail: the pilot factory is nameable, so its counts stay in `results/`.

Usage:
    python3 scripts/probe_decode.py --manifest results/pilot/clips_factory_001.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.decode import decode_gray_frames, ffmpeg_clip_argv  # noqa: E402
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import n_samples  # noqa: E402
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402

GATE = 0.01  # docs/METHOD.md E2
WIDTH, HEIGHT = 480, 270
PROBE_FRAMES = 8


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


@dataclass(frozen=True, slots=True)
class Probe:
    planned: int
    frames: int
    ok: bool
    reason: str | None
    seconds: float


def _probe(clip: ClipRef, token: str | None, max_frames: int | None) -> Probe:
    planned = n_samples(clip.duration_s)
    started = time.time()
    try:
        url = ShardReader(REPO_ID, clip.shard, token)._resolve()
        argv = ffmpeg_clip_argv(url, clip, fps_sampled=4.0, width=WIDTH, height=HEIGHT,
                                max_frames=max_frames)
        frames = sum(1 for _ in decode_gray_frames(argv, WIDTH, HEIGHT))
        return Probe(planned, frames, frames > 0,
                     None if frames > 0 else "no frames decoded",
                     round(time.time() - started, 2))
    except Exception as exc:
        return Probe(planned, 0, False, f"{type(exc).__name__}: {str(exc)[:200]}",
                     round(time.time() - started, 2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--full-sample", type=int, default=4,
                        help="clips decoded to the end, to detect truncation")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--out", default="results/decode_probe.json")
    args = parser.parse_args(argv)

    token = _token()
    rows = [MetadataRow(**json.loads(line))
            for line in (ROOT / args.manifest).read_text().splitlines() if line.strip()]
    refs = clip_refs(rows, corpus_rev="probe")
    print(f"probing {len(refs)} clips at {PROBE_FRAMES} frames each", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        opens = list(pool.map(lambda c: _probe(c, token, PROBE_FRAMES), refs))

    failed_clips = [r for r in opens if not r.ok]
    planned_total = sum(r.planned for r in opens)
    failed_pairs = sum(r.planned for r in failed_clips)

    rng = random.Random(args.seed)
    sample = rng.sample(list(refs), min(args.full_sample, len(refs)))
    print(f"decoding {len(sample)} clips to the end for truncation", flush=True)
    with ThreadPoolExecutor(max_workers=min(args.workers, len(sample))) as pool:
        fulls = list(pool.map(lambda c: _probe(c, token, None), sample))
    trunc_planned = sum(r.planned for r in fulls)
    trunc_decoded = sum(max(r.frames - 1, 0) for r in fulls)
    trunc_missing = max(trunc_planned - trunc_decoded, 0)

    open_pair_rate = failed_pairs / planned_total if planned_total else 0.0
    open_clip_rate = len(failed_clips) / len(opens) if opens else 0.0
    trunc_rate = trunc_missing / trunc_planned if trunc_planned else 0.0

    payload = {
        "gate": GATE,
        "denominator": "pairs (docs/DECISIONS.md D023), with the per-clip rate beside it",
        "open_failure_rate_per_pair": round(open_pair_rate, 6),
        "open_failure_rate_per_clip": round(open_clip_rate, 6),
        "clips_probed": len(opens),
        "truncation_sample_clips": len(fulls),
        "truncation_missing_rate_per_pair": round(trunc_rate, 6),
        "truncation_note": (
            "Measured on a seeded sample decoded to the end; opening every clip is cheap and "
            "finishing every clip is not. Reported as a sample, not as the pilot's rate."
        ),
        "seed": args.seed,
        "reasons": sorted({r.reason for r in failed_clips if r.reason}),
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nwrote {args.out}")
    print(f"  open failure, per pair : {open_pair_rate:.4%}")
    print(f"  open failure, per clip : {open_clip_rate:.4%}")
    print(f"  truncation, per pair   : {trunc_rate:.4%} (sample of {len(fulls)})")
    passed = open_pair_rate < GATE and trunc_rate < GATE
    print(f"\nE2 decode gate (<{GATE:.0%} per pair): {'PASS' if passed else 'FAIL'}")
    for reason in sorted({r.reason for r in failed_clips if r.reason}):
        print(f"    {reason}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
