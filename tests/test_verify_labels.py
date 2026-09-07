"""Tests for `scripts/verify_labels.py`.

The script exists because D043's partly-written clip is invisible to every other check: the
rows are well formed, the clip id is real, and only the *count* is wrong. So the tests that
matter are the ones where nothing is malformed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify_labels  # noqa: E402

from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402

REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"
DURATION_S = 180.0


def _manifest(path: Path, clips: int = 2) -> None:
    rows = [{
        "factory_id": "factory_001", "worker_id": "worker_001", "clip_index": i,
        "shard": "factory_001/workers/worker_001/f1_w1_part00.tar",
        "byte_start": 1024 * (i + 1), "byte_end": 1024 * (i + 2), "duration_s": DURATION_S,
        "fps": 30.0, "width": 1920, "height": 1080, "codec": "h264",
    } for i in range(clips)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _labels(path: Path, counts: dict[int, int]) -> None:
    lines = []
    for index, n in counts.items():
        cid = f"factory_001/worker_001/{index:06d}"
        # The real sample plan's instants, not integer seconds: the verifier infers the
        # analysis rate from the spacing, and a fixture at 1 Hz described a file no run
        # produces (D070).
        # The over-long case writes past the plan, so the instants continue on the same grid
        # rather than being truncated to it.
        step = 1.0 / ANALYSIS_HZ
        lines += [json.dumps({"clip_id": cid, "corpus_rev": REV, "t_s": j * step})
                  for j in range(n)]
    path.write_text("".join(line + "\n" for line in lines))


def _run(tmp_path: Path, counts: dict[int, int], clips: int = 2) -> int:
    manifest, labels = tmp_path / "m.jsonl", tmp_path / "l.jsonl"
    _manifest(manifest, clips)
    _labels(labels, counts)
    return verify_labels.main(["--manifest", str(manifest), "--labels", str(labels),
                              "--corpus-rev", REV])


def test_every_clip_at_its_planned_count_passes(tmp_path: Path) -> None:
    full = len(sample_times(DURATION_S))
    assert _run(tmp_path, {0: full, 1: full}) == 0


def test_a_clip_one_row_short_fails(tmp_path: Path) -> None:
    """D043's defect, in its mildest form. Nothing is malformed; one clip stopped early."""
    full = len(sample_times(DURATION_S))
    assert _run(tmp_path, {0: full, 1: full - 1}) == 1


def test_a_clip_with_no_rows_at_all_fails(tmp_path: Path) -> None:
    full = len(sample_times(DURATION_S))
    assert _run(tmp_path, {0: full}) == 1


def test_duplicated_rows_fail_rather_than_passing_as_complete(tmp_path: Path) -> None:
    """A resume that appended without purging would land here, not on the short case."""
    full = len(sample_times(DURATION_S))
    assert _run(tmp_path, {0: full, 1: full + 3}) == 1


def test_rows_from_two_corpus_revisions_are_refused(tmp_path: Path) -> None:
    """`corpus_rev` is on the record so records from two revisions are never pooled."""
    full = len(sample_times(DURATION_S))
    manifest, labels = tmp_path / "m.jsonl", tmp_path / "l.jsonl"
    _manifest(manifest, 1)
    step = 1.0 / ANALYSIS_HZ
    rows = [{"clip_id": "factory_001/worker_001/000000",
             "corpus_rev": REV if j else "other", "t_s": j * step} for j in range(full)]
    labels.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert verify_labels.main(["--manifest", str(manifest), "--labels", str(labels),
                              "--corpus-rev", REV]) == 1
