"""The pilot factory's clip manifest: what is in the corpus, without decoding any of it.

A WebDataset `.tar` member header is 512 bytes at a computable offset, so the whole corpus
indexes with small ranged reads and no shard is ever downloaded -- the approach
`../vernier/docs/DECISIONS.md` D071 established and measured (~150 MB of reads over a ~16 TB
corpus). The walk is pure: it takes a `read_range(start, end_inclusive)` callable, so a
synthetic tar exercises it offline and everything network-facing lives in `corpus/shards.py`.

The release's own per-clip sidecar carries `factory_id`, `worker_id`, `video_index`,
`duration_sec`, `fps`, `width`, `height` and `codec`, and **no per-frame timestamp or index
of any kind** (`../vernier/docs/DECISIONS.md` D065). Sample instants are therefore constructed
by cyclegraph, and `corpus/sampling.py` says so where it constructs them.

`clip_id` here is *not* the sidecar's. The release names a clip `factory001_worker001_00007`;
`CONTRACTS.md` requires `factory_001/worker_001/000007`, because `worker_id` is numbered
within factory and the composite is the cluster unit (`docs/DECISIONS.md` D015). The
translation is a real function with a real test, not a rename.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import Callable, Final

from cyclegraph.models import MIN_CLIP_S, ClipRef

ReadRange = Callable[[int, int], bytes]
"""`(start, end_inclusive) -> bytes`. The seam: everything above this is pure."""

_BLOCK: Final[int] = 512
_NAME = slice(0, 100)
_SIZE = slice(124, 136)
_TYPEFLAG: Final[int] = 156
_PREFIX = slice(345, 500)
_REGULAR = {b"0", b"\x00"}
_MAX_SIDECAR_BYTES: Final[int] = 10_000


def _round_up_block(size: int) -> int:
    return ((size + _BLOCK - 1) // _BLOCK) * _BLOCK


def walk_tar_members(read_range: ReadRange) -> Iterator[tuple[str, int, int]]:
    """`(member name, payload offset, payload size)` for every regular file in a tar.

    Reads one 512-byte header per member and skips the payload by arithmetic. Stops at the
    end-of-archive marker or the first unreadable header.
    """
    offset = 0
    while True:
        header = read_range(offset, offset + _BLOCK - 1)
        if len(header) < _BLOCK or header[_NAME][:1] == b"\x00":
            return
        raw_size = header[_SIZE].rstrip(b"\x00 ").lstrip(b"0") or b"0"
        try:
            size = int(raw_size, 8)
        except ValueError:
            return
        name = header[_NAME].rstrip(b"\x00").decode("utf-8", "replace")
        prefix = header[_PREFIX].rstrip(b"\x00").decode("utf-8", "replace")
        if prefix:
            name = f"{prefix}/{name}"
        if header[_TYPEFLAG : _TYPEFLAG + 1] in _REGULAR and name:
            yield name, offset + _BLOCK, size
        offset += _BLOCK + _round_up_block(size)


@dataclass(frozen=True, slots=True)
class MetadataRow:
    """One clip, exactly as the release describes it, before any cyclegraph naming."""

    factory_id: str
    worker_id: str
    clip_index: int
    shard: str
    byte_start: int
    byte_end: int
    duration_s: float
    fps: float
    width: int
    height: int
    codec: str


def clip_id(factory_id: str, worker_id: str, clip_index: int) -> str:
    """`CONTRACTS.md`'s composite. The join key everywhere, and the cluster unit's prefix."""
    return f"{factory_id}/{worker_id}/{clip_index:06d}"


def parse_clip_id(cid: str) -> tuple[str, str, int]:
    parts = cid.split("/")
    if len(parts) != 3:
        raise ValueError(f"a clip id is factory/worker/index, got {cid!r}")
    return parts[0], parts[1], int(parts[2])


def clip_records_from_shard(shard: str, read_range: ReadRange) -> list[MetadataRow]:
    """Every clip in one shard, from its members' sidecars. No media is read."""
    members = list(walk_tar_members(read_range))
    media = {name.rsplit(".", 1)[0]: (off, size)
             for name, off, size in members if name.endswith(".mp4")}
    rows: list[MetadataRow] = []
    for name, off, size in members:
        if not name.endswith(".json"):
            continue
        stem = name.rsplit(".", 1)[0]
        if stem not in media or size > _MAX_SIDECAR_BYTES:
            continue
        payload = json.loads(read_range(off, off + size - 1).decode("utf-8"))
        mp4_off, mp4_size = media[stem]
        rows.append(MetadataRow(
            factory_id=str(payload["factory_id"]),
            worker_id=str(payload["worker_id"]),
            clip_index=int(payload["video_index"]),
            shard=shard,
            byte_start=mp4_off,
            byte_end=mp4_off + mp4_size,
            duration_s=float(payload["duration_sec"]),
            fps=float(payload["fps"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
            codec=str(payload["codec"]),
        ))
    return rows


def clip_refs(rows: Iterable[MetadataRow], *, corpus_rev: str) -> list[ClipRef]:
    """`MetadataRow` to `ClipRef`, refusing a duplicate clip rather than silently keeping one."""
    seen: set[tuple[str, str, int]] = set()
    out: list[ClipRef] = []
    for row in rows:
        key = (row.factory_id, row.worker_id, row.clip_index)
        if key in seen:
            raise ValueError(f"duplicate clip {clip_id(*key)!r} in the manifest")
        seen.add(key)
        out.append(ClipRef(
            clip_id=clip_id(row.factory_id, row.worker_id, row.clip_index),
            factory_id=row.factory_id, worker_id=row.worker_id, clip_index=row.clip_index,
            shard=row.shard, byte_start=row.byte_start, byte_end=row.byte_end,
            duration_s=row.duration_s, fps=row.fps, width=row.width, height=row.height,
            codec=row.codec, corpus_rev=corpus_rev,
        ))
    return out


@dataclass(frozen=True, slots=True)
class PublishedCounts:
    """What a source claims the corpus holds. Sources disagree; that is the point."""

    source: str
    n_factories: int | None = None
    n_clips: int | None = None
    n_workers: int | None = None
    total_duration_s: float | None = None


@dataclass(frozen=True, slots=True)
class Reconciliation:
    source: str
    reconciles: bool
    mismatches: tuple[str, ...]
    observed: dict[str, float]


def reconcile(refs: Sequence[ClipRef], published: PublishedCounts, *,
              clip_tolerance: int = 0, worker_tolerance: int = 0,
              duration_rel_tolerance: float = 0.01) -> Reconciliation:
    """Compare a scan against one published claim, naming each mismatch."""
    observed = {
        "n_clips": float(len(refs)),
        "n_workers": float(len({(r.factory_id, r.worker_id) for r in refs})),
        "n_factories": float(len({r.factory_id for r in refs})),
        "total_duration_s": float(sum(r.duration_s for r in refs)),
    }
    mismatches: list[str] = []
    for field, tol in (("n_clips", clip_tolerance), ("n_workers", worker_tolerance),
                       ("n_factories", 0)):
        claimed = getattr(published, field)
        if claimed is not None and abs(observed[field] - claimed) > tol:
            mismatches.append(
                f"{field}: scanned {int(observed[field])}, {published.source} claims {claimed}"
            )
    if published.total_duration_s is not None:
        rel = abs(observed["total_duration_s"] - published.total_duration_s) / published.total_duration_s
        if rel > duration_rel_tolerance:
            mismatches.append(
                f"total_duration_s: scanned {observed['total_duration_s']:.1f}, "
                f"{published.source} claims {published.total_duration_s:.1f} ({rel:.2%})"
            )
    return Reconciliation(source=published.source, reconciles=not mismatches,
                          mismatches=tuple(mismatches), observed=observed)


def pilot_factory(factory_ids: Iterable[str]) -> str:
    """`docs/DECISIONS.md` D012: the first in the pinned revision's sorted manifest, fixed
    rather than chosen after inspection."""
    ids = sorted(set(factory_ids))
    if not ids:
        raise ValueError("no factories in the manifest")
    return ids[0]


def is_too_short(ref: ClipRef) -> bool:
    """`docs/RUBRIC.md`: shorter than the floor is excluded, counted, and reported."""
    return ref.duration_s < MIN_CLIP_S
