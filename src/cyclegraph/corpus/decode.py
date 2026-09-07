"""One clip's frames at the analysis rate, out of an mp4 inside a tar, over HTTP ranges.

`../vernier/docs/DECISIONS.md` D071 established the access path: ffmpeg's `subfile` protocol
presents a byte window of another URL as a seekable file, so a frame comes out of a shard
without downloading it. Two details are load-bearing and both are asserted by tests rather
than trusted:

**`-ss` goes before `-i`.** Before, it is an input seek: ffmpeg consults the moov index and
range-requests the GOP it needs. After, it decodes from the start and discards, which turns a
two-second seek into a full sequential read of an 800 MB shard.

**The protocol whitelist is not optional.** `subfile` is not enabled by default, and the list
must also carry `https`, `tls`, `tcp` and `crypto` for a signed CDN URL. Dropping the flag
does not fail loudly -- it re-enables `file:` as a side effect, and ffmpeg will then happily
open a local path a URL happens to look like.

**Whole clips, not seeks per sample.** `docs/METHOD.md` E2 decodes sequentially: one ffmpeg
per clip at the analysis rate, not one seek per instant. A cold seek costs ~1.9 s, and the
pilot plans on the order of a million instants, so per-instant seeking is not a slower plan --
it is an impossible one. Consecutive decoded frames are exactly the pairs `corpus/sampling.py`
plans, because pair `i` is `(t_i, t_i + 1/fps)` and `t_{i+1} = t_i + 1/fps`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Final, Iterator, Literal

import numpy as np
import numpy.typing as npt

from cyclegraph.models import ClipRef

PROTOCOL_WHITELIST: Final[str] = "file,http,https,tls,tcp,crypto,subfile"
FFMPEG: Final[str] = "ffmpeg"

Gray = npt.NDArray[np.uint8]


def subfile_url(url: str, byte_start: int, byte_end: int) -> str:
    """The `subfile` wrapper naming the byte window one clip's mp4 occupies in its shard."""
    if byte_end <= byte_start:
        raise ValueError("byte_end must exceed byte_start")
    return f"subfile,,start,{byte_start},end,{byte_end},,:{url}"


def ffmpeg_clip_argv(url: str, clip: ClipRef, *, fps_sampled: float,
                     width: int, height: int, start_s: float = 0.0,
                     max_frames: int | None = None, pix_fmt: str = "gray",
                     threads: int | None = None,
                     rw_timeout_s: float = 120.0) -> list[str]:
    """Decode one clip to raw 8-bit frames on stdout, at the analysis rate.

    `pix_fmt` defaults to grey because the flow path and the box-width scale are luminance
    only and grey is a third of the bytes. It is a **parameter** rather than a constant
    because the labeller is not luminance-only: its head was fitted on colour frames, and
    feeding it grey silently moves the feature distribution the head was trained against
    (`docs/DECISIONS.md` D040). A consumer that needs colour asks for `rgb24`.
    """
    if fps_sampled <= 0:
        raise ValueError("the analysis rate is positive")
    argv = [
        FFMPEG, "-hide_banner", "-loglevel", "error",
        "-protocol_whitelist", PROTOCOL_WHITELIST,
    ]
    if threads is not None:
        if threads < 1:
            raise ValueError("threads must be positive")
        argv += ["-threads", str(threads)]
    if rw_timeout_s > 0:
        # microseconds, and before -i so it applies to reading the input
        argv += ["-rw_timeout", str(int(rw_timeout_s * 1_000_000))]
    if start_s > 0:
        argv += ["-ss", f"{start_s:.3f}"]  # before -i: an input seek
    argv += [
        "-i", subfile_url(url, clip.byte_start, clip.byte_end),
        "-vf", f"fps={fps_sampled},scale={width}:{height}",
        "-pix_fmt", pix_fmt, "-f", "rawvideo",
    ]
    if max_frames is not None:
        argv += ["-frames:v", str(max_frames)]
    argv += ["-"]
    return argv


@dataclass(frozen=True, slots=True)
class DecodeOutcome:
    """What one clip's decode produced. A failure is a value with a reason, never an absence."""

    clip_id: str
    n_frames: int
    n_pairs_planned: int
    status: Literal["ok", "decode_failed"]
    reason: str | None
    seconds: float

    @property
    def n_pairs_decoded(self) -> int:
        return max(self.n_frames - 1, 0)

    @property
    def pair_failures(self) -> int:
        """Pairs planned that no decoded frame pair covers. The E2 gate's numerator."""
        return max(self.n_pairs_planned - self.n_pairs_decoded, 0)


def decode_gray_frames(argv: list[str], width: int, height: int, *,
                       timeout_s: float = 900.0, channels: int = 1) -> Iterator[Gray]:
    """Raw frames off ffmpeg's stdout. Raises with ffmpeg's own stderr on a non-zero exit.

    `channels` must match the `pix_fmt` the argv asked for: 1 for `gray`, 3 for `rgb24`. A
    mismatch would not error -- it would silently reinterpret the byte stream as frames of the
    wrong shape.
    """
    frame_bytes = width * height * channels
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    try:
        while True:
            buffer = process.stdout.read(frame_bytes)
            if not buffer or len(buffer) < frame_bytes:
                break
            shape = (height, width) if channels == 1 else (height, width, channels)
            yield np.frombuffer(buffer, dtype=np.uint8).reshape(shape)
    finally:
        process.stdout.close()
        try:
            _, err = process.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            process.kill()
            raise
        if process.returncode not in (0, None):
            raise RuntimeError(err.decode("utf-8", "replace").strip()[:400] or "ffmpeg failed")
