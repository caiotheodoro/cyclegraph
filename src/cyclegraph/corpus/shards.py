"""Ranged reads over the corpus's shards. The only module that knows what a tar member is.

`docs/ARCHITECTURE.md`'s first seam: the pinned revision is a property of the record, not of
the process. Every function here takes `corpus_rev` explicitly and none reads it from
configuration, so two `ClipRef`s from different revisions cannot be produced by the same call
and silently pooled.

Two details earn their keep, both from `../vernier/docs/DECISIONS.md` D071:

**Block caching.** A member header is 512 bytes, but its sidecar sits immediately after its
mp4 and the next header immediately after that, so fetching an aligned window serves several
logical reads per request. Without it the scan makes roughly three times the requests.

**URL refresh.** Hugging Face hands back a CloudFront-signed URL with an `Expires` claim, and
a scan outlives it. A 403 part-way through is a stale signature, not a permissions failure,
and reporting it as one would send a reader looking for an access problem that does not exist.
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
from typing import Final

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

REPO_ID: Final[str] = "builddotai/Egocentric-10K"
_WINDOW: Final[int] = 8192
_ATTEMPTS: Final[int] = 4
_RETRYABLE: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})


class ShardReader:
    """A `read_range` over one shard's resolved CDN URL, with a block cache."""

    def __init__(self, repo_id: str, shard: str, token: str | None,
                 window: int = _WINDOW, timeout_s: float = 60.0) -> None:
        self._repo_id = repo_id
        self._shard = shard
        self._token = token
        self._window = window
        self._timeout_s = timeout_s
        self._url: str | None = None
        self._cache: dict[int, bytes] = {}
        self.requests = 0
        self.bytes_fetched = 0

    def _resolve(self) -> str:
        from huggingface_hub import get_hf_file_metadata, hf_hub_url

        url = hf_hub_url(self._repo_id, self._shard, repo_type="dataset")
        return str(get_hf_file_metadata(url, token=self._token).location)

    def _fetch(self, start: int, end: int) -> bytes:
        for attempt in range(_ATTEMPTS):
            if self._url is None:
                self._url = self._resolve()
            request = urllib.request.Request(self._url, headers={"Range": f"bytes={start}-{end}"})
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                    payload = bytes(response.read())
                self.requests += 1
                self.bytes_fetched += len(payload)
                return payload
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    self._url = None  # an expired signature, not a permissions failure
                elif exc.code == 416:
                    return b""  # past the end of the object
                elif exc.code not in _RETRYABLE:
                    raise
                time.sleep(2**attempt)
            except (TimeoutError, OSError):
                time.sleep(2**attempt)
        raise RuntimeError(f"range {start}-{end} of {self._shard} failed after {_ATTEMPTS} tries")

    def read_range(self, start: int, end_inclusive: int) -> bytes:
        out = bytearray()
        position = start
        while position <= end_inclusive:
            block_start = (position // self._window) * self._window
            block = self._cache.get(block_start)
            if block is None:
                block = self._fetch(block_start, block_start + self._window - 1)
                self._cache[block_start] = block
            chunk = block[position - block_start : end_inclusive - block_start + 1]
            if not chunk:
                break
            out += chunk
            position += len(chunk)
        return bytes(out)


def list_shards(repo_id: str = REPO_ID, token: str | None = None) -> tuple[list[str], str]:
    """Every `.tar` in the repository, sorted, with the revision they were listed at.

    The revision is returned rather than stored, so a caller cannot use the listing from one
    revision against reads from another (`docs/ARCHITECTURE.md`, seam 1).
    """
    from huggingface_hub import HfApi

    info = HfApi(token=token).dataset_info(repo_id)
    shards = sorted(s.rfilename for s in (info.siblings or []) if s.rfilename.endswith(".tar"))
    return shards, str(info.sha)


def shards_for_factory(shards: list[str], factory_id: str) -> list[str]:
    """The shards belonging to one factory, by path prefix."""
    return [s for s in shards if s.startswith(f"{factory_id}/")]


def factory_ids(shards: list[str]) -> list[str]:
    """Every factory the listing mentions, sorted. `pilot_factory` takes the first."""
    return sorted({s.split("/", 1)[0] for s in shards if "/" in s})
