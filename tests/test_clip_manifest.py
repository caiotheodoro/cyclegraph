"""Behavioural tests for `src/cyclegraph/corpus/manifest.py`.

The tar walk's golden case is Python's own `tarfile`. A hand-computed expectation would just
re-implement the same offset arithmetic and would agree with a bug in it; `tarfile` reads the
whole file locally and is an independent oracle for exactly this format.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Callable

import pytest

from cyclegraph.corpus.manifest import (
    MetadataRow,
    PublishedCounts,
    clip_id,
    clip_records_from_shard,
    clip_refs,
    is_too_short,
    parse_clip_id,
    pilot_factory,
    reconcile,
    walk_tar_members,
)

REV = "3e5f87c8"


def _sidecar(factory: str, worker: str, index: int, duration: float) -> bytes:
    return json.dumps({
        "factory_id": factory, "worker_id": worker, "video_index": index,
        "duration_sec": duration, "width": 1920, "height": 1080,
        "fps": 30.0, "size_bytes": 123, "codec": "h265",
    }).encode()


def _build_tar(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w") as tar:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))


def _reader(path: Path) -> Callable[[int, int], bytes]:
    def read_range(start: int, end_inclusive: int) -> bytes:
        with path.open("rb") as handle:
            handle.seek(start)
            return handle.read(end_inclusive - start + 1)
    return read_range


def _shard(tmp_path: Path, clips: int = 3) -> Path:
    members: dict[str, bytes] = {}
    for i in range(clips):
        stem = f"factory001_worker001_{i:05d}"
        members[f"{stem}.mp4"] = b"\x00" * (1000 + i)
        members[f"{stem}.json"] = _sidecar("factory_001", "worker_001", i, 180.0 + i)
    path = tmp_path / "shard.tar"
    _build_tar(path, members)
    return path


def test_the_walk_recovers_what_tarfile_recovers(tmp_path: Path) -> None:
    """Golden case against an independent oracle."""
    path = _shard(tmp_path, clips=4)
    walked = {name: (off, size) for name, off, size in walk_tar_members(_reader(path))}
    with tarfile.open(path) as tar:
        expected = {m.name: (m.offset_data, m.size) for m in tar.getmembers() if m.isfile()}
    assert walked == expected


def test_the_walk_reads_only_headers_not_payloads(tmp_path: Path) -> None:
    """The property that makes indexing a 16 TB corpus cost ~150 MB."""
    path = _shard(tmp_path, clips=4)
    read_bytes = 0
    inner = _reader(path)

    def counting(start: int, end_inclusive: int) -> bytes:
        nonlocal read_bytes
        read_bytes += end_inclusive - start + 1
        return inner(start, end_inclusive)

    list(walk_tar_members(counting))
    assert read_bytes < path.stat().st_size / 2


def test_clip_records_pair_sidecars_with_their_media(tmp_path: Path) -> None:
    path = _shard(tmp_path, clips=3)
    rows = clip_records_from_shard("factory_001/workers/worker_001/part00.tar", _reader(path))
    assert len(rows) == 3
    assert [r.clip_index for r in sorted(rows, key=lambda r: r.clip_index)] == [0, 1, 2]
    row = sorted(rows, key=lambda r: r.clip_index)[1]
    assert row.byte_end - row.byte_start == 1001  # the mp4's real payload size
    assert row.codec == "h265" and row.duration_s == 181.0


def test_the_release_clip_name_is_translated_not_copied() -> None:
    """The sidecar names a clip `factory001_worker001_00007`; the contract does not."""
    assert clip_id("factory_001", "worker_001", 7) == "factory_001/worker_001/000007"
    assert parse_clip_id("factory_001/worker_001/000007") == ("factory_001", "worker_001", 7)
    with pytest.raises(ValueError):
        parse_clip_id("factory001_worker001_00007")


def _rows(n_workers: int, per_worker: int, duration: float = 200.0) -> list[MetadataRow]:
    return [
        MetadataRow(factory_id="factory_001", worker_id=f"worker_{w:03d}", clip_index=c,
                    shard="s.tar", byte_start=512, byte_end=512 + 1000,
                    duration_s=duration, fps=30.0, width=1920, height=1080, codec="h265")
        for w in range(1, n_workers + 1) for c in range(per_worker)
    ]


def test_a_duplicate_clip_raises_rather_than_being_kept_once() -> None:
    rows = _rows(1, 2)
    with pytest.raises(ValueError, match="duplicate clip"):
        clip_refs(rows + rows[:1], corpus_rev=REV)


def test_reconciliation_passes_on_a_matching_claim() -> None:
    refs = clip_refs(_rows(3, 7), corpus_rev=REV)
    published = PublishedCounts(source="synthetic", n_factories=1, n_clips=21, n_workers=3,
                                total_duration_s=21 * 200.0)
    result = reconcile(refs, published)
    assert result.reconciles and result.mismatches == ()


def test_a_dropped_clip_and_a_duration_drift_each_fail_with_a_named_mismatch() -> None:
    refs = clip_refs(_rows(3, 7), corpus_rev=REV)
    missing = reconcile(refs, PublishedCounts(source="vendor", n_clips=22))
    assert not missing.reconciles
    assert "n_clips" in missing.mismatches[0] and "vendor" in missing.mismatches[0]

    drift = reconcile(refs, PublishedCounts(source="vendor", total_duration_s=21 * 200.0 * 1.02))
    assert not drift.reconciles and "total_duration_s" in drift.mismatches[0]


def test_a_tolerance_lets_a_known_gap_through_while_still_reporting_it() -> None:
    """F12's -9 worker gap is inherited, not rediscovered: it must be expressible."""
    refs = clip_refs(_rows(3, 7), corpus_rev=REV)
    assert reconcile(refs, PublishedCounts(source="vendor", n_workers=5),
                     worker_tolerance=2).reconciles
    assert not reconcile(refs, PublishedCounts(source="vendor", n_workers=5)).reconciles


def test_the_pilot_factory_is_the_first_sorted_and_not_the_first_seen() -> None:
    ids = ["factory_007", "factory_001", "factory_042"]
    assert pilot_factory(ids) == "factory_001"
    assert pilot_factory(reversed(ids)) == "factory_001"
    with pytest.raises(ValueError):
        pilot_factory([])


def test_the_clip_length_floor_comes_from_the_frozen_constant() -> None:
    short = clip_refs(_rows(1, 1, duration=59.9), corpus_rev=REV)[0]
    long = clip_refs(_rows(1, 1, duration=60.1), corpus_rev=REV)[0]
    assert is_too_short(short) and not is_too_short(long)


def test_the_module_does_not_retype_the_frozen_threshold() -> None:
    body = (Path(__file__).resolve().parent.parent
            / "src" / "cyclegraph" / "corpus" / "manifest.py").read_text()
    assert "MIN_CLIP_S" in body
    assert "60.0" not in body and "60 " not in body
