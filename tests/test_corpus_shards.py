"""Tests for `src/cyclegraph/corpus/shards.py`.

The network paths are not tested -- `docs/WAVES.md` requires every test to run offline
against committed fixtures, and a test that reached the corpus would violate that and be
useless on a clone without a token. What is tested is the part that decides how many requests
a 19,495-shard scan makes, and the path arithmetic the pilot selection depends on.
"""

from __future__ import annotations

from cyclegraph.corpus.shards import ShardReader, factory_ids, shards_for_factory

SHARDS = [
    "factory_001/workers/worker_001/factory001_worker001_part00.tar",
    "factory_001/workers/worker_002/factory001_worker002_part00.tar",
    "factory_010/workers/worker_001/factory010_worker001_part00.tar",
    "factory_002/workers/worker_003/factory002_worker003_part07.tar",
]


class _FakeReader(ShardReader):
    """A reader over an in-memory archive, so the block cache can be counted."""

    def __init__(self, payload: bytes, window: int = 8192) -> None:
        super().__init__("repo", "shard.tar", None, window=window)
        self._payload = payload

    def _fetch(self, start: int, end: int) -> bytes:  # type: ignore[override]
        self.requests += 1
        chunk = self._payload[start : end + 1]
        self.bytes_fetched += len(chunk)
        return chunk


def test_factories_are_recovered_from_shard_paths_and_sorted() -> None:
    assert factory_ids(SHARDS) == ["factory_001", "factory_002", "factory_010"]


def test_a_factory_selects_only_its_own_shards() -> None:
    picked = shards_for_factory(SHARDS, "factory_001")
    assert len(picked) == 2
    assert all(s.startswith("factory_001/") for s in picked)
    # A prefix must not match a longer factory id.
    assert shards_for_factory(SHARDS, "factory_00") == []


def test_the_block_cache_serves_neighbouring_reads_from_one_request() -> None:
    """A header is 512 bytes but its sidecar and the next header follow immediately, so an
    aligned window serves several logical reads. This is the difference between a ~50-minute
    scan and a multi-hour one (`../vernier/docs/DECISIONS.md` D071)."""
    reader = _FakeReader(bytes(range(256)) * 128, window=4096)
    for start in range(0, 4096, 512):
        reader.read_range(start, start + 511)
    assert reader.requests == 1  # eight logical reads, one fetch


def test_a_read_past_the_end_stops_rather_than_looping() -> None:
    reader = _FakeReader(b"abcd", window=8)
    assert reader.read_range(0, 100) == b"abcd"


def test_reads_spanning_two_windows_fetch_both() -> None:
    reader = _FakeReader(bytes(4096), window=1024)
    assert len(reader.read_range(1000, 1100)) == 101
    assert reader.requests == 2
