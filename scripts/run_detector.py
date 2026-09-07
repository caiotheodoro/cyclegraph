#!/usr/bin/env python3
"""Hand boxes for every sampled instant in a manifest. `docs/METHOD.md` E3, the GPU stage.

Writes `detections.jsonl` in the shape `cyclegraph.signal.stores.JsonlDetectionStore` reads,
so everything downstream of it runs offline on CPU afterwards. That split is the reason this
stage is a script and not a module: 100DOH needs torch, the `signal` extra declares none, and
`docs/DECISIONS.md` D022 keeps model runtimes out of `src/cyclegraph/signal/`.

**Boxes are written in native clip pixels**, whatever resolution the frames were decoded at,
because `hand_box_width_px` is the hand-breadth scale and a consumer must not have to know
this script's decode size to interpret it.

**Resumable per clip.** A spot instance is interrupted, not asked. A run that lost its work on
preemption would have to be re-bought, so completed clips are skipped on restart and the
output is appended.

**`--smoke` measures throughput instead of guessing it.** `docs/METHOD.md` E3 estimates
100DOH at ~20 frames/s and that figure has never been measured; the smoke path runs a bounded
number of real frames and prints the rate, which is what `docs/REPRODUCTION.md` means by
"whoever runs a stage records its measured cost beside the estimate".

Usage:
    python3 scripts/run_detector.py --smoke 200          # measure the rate, write nothing
    python3 scripts/run_detector.py --detector 100doh    # the pilot run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.corpus.decode import decode_gray_frames, ffmpeg_clip_argv  # noqa: E402
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402
from cyclegraph.signal.ports import HandBox, MaskSource  # noqa: E402

DECODE_WIDTH, DECODE_HEIGHT = 960, 540
"""Large enough for a hand at arm's length to survive detection, small enough to decode at
network speed. Boxes are scaled back to native before they are written."""

DECODE_PIX_FMT = "rgb24"
"""**Colour, and this is load-bearing.** Every hand model in reach was trained on colour, and
skin is one of the cues they were fitted on. `docs/DECISIONS.md` D040 measured what feeding a
grey frame to a colour-trained model costs on the labeller -- a 0.033 duty-cycle shift against
H1a's 0.05 bound -- and the detector path had the identical defect waiting in it: this decoded
grey and the adapter replicated it to three channels, which is a grey image in a colour tensor,
not a colour image. No detector has ever run, so the defect is latent rather than realised."""


class FrameDetector(Protocol):
    """What this script needs of a model. Deliberately narrower than `HandDetector`."""

    @property
    def mask_source(self) -> MaskSource: ...

    def boxes(self, frame: np.ndarray) -> list[HandBox]: ...


@dataclass(frozen=True, slots=True)
class ClipFrames:
    """One clip's sampled instants and the frames at them, already decoded."""

    clip: ClipRef
    times: list[float]
    frames: list[np.ndarray]


def scale_box(box: HandBox, *, from_width: int, from_height: int,
              to_width: int, to_height: int) -> HandBox:
    """Detector coordinates to native clip pixels."""
    sx, sy = to_width / from_width, to_height / from_height
    return HandBox(x=box.x * sx, y=box.y * sy, width=box.width * sx,
                   height=box.height * sy, score=box.score)


def detections_for_clip(clip_frames: ClipFrames, detector: FrameDetector) -> list[dict[str, object]]:
    """One JSONL row per sampled instant, including the instants with no box.

    A row is written for every instant the decoder produced, because an instant with no row
    means "the detector did not run here" to the store that reads this, and an instant where
    the detector ran and found nothing is a different fact (`signal/stores.py`).
    """
    rows: list[dict[str, object]] = []
    clip = clip_frames.clip
    for t_s, frame in zip(clip_frames.times, clip_frames.frames, strict=False):
        try:
            found = detector.boxes(frame)
            failed: str | None = None
        except Exception as exc:  # a frame the model could not process is a value, not a crash
            found, failed = [], f"{type(exc).__name__}: {str(exc)[:120]}"
        native = [
            scale_box(b, from_width=frame.shape[1], from_height=frame.shape[0],
                      to_width=clip.width, to_height=clip.height)
            for b in found
        ]
        row: dict[str, object] = {
            "clip_id": clip.clip_id, "t_s": t_s, "mask_source": detector.mask_source,
            "boxes": [{"x": b.x, "y": b.y, "width": b.width, "height": b.height,
                       "score": b.score} for b in native],
        }
        if failed is not None:
            row["failed_reason"] = failed
        rows.append(row)
    return rows


def rows_per_clip(path: Path) -> dict[str, int]:
    """How many rows each clip already has, so a preempted run resumes without a hole.

    Not a set of seen clip ids. `docs/DECISIONS.md` D043 records why, for the labeller: a
    worker killed mid-clip leaves rows behind, and a done-set calls that clip finished and
    resumes past the part that was never written. D049 says a defect record that names a
    mechanism has said something about every place the mechanism lives -- and then carried only
    the memory half of D043 across to this file, leaving the half D043 called "the one that
    matters". Rows are flushed per clip *and* by the stdio buffer inside a 4,799-row clip, so a
    preempted spot instance produces exactly the partial clip this now detects.
    """
    if not path.exists():
        return {}
    counts: dict[str, int] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            cid = json.loads(line)["clip_id"]
            counts[cid] = counts.get(cid, 0) + 1
    return counts


def drop_partial_clips(path: Path, partial: set[str]) -> int:
    """Remove every row of a clip short of its sample plan, so the re-run appends a whole clip
    rather than duplicating the part that survived."""
    if not partial or not path.exists():
        return 0
    kept = [line for line in path.read_text().splitlines()
            if line.strip() and json.loads(line)["clip_id"] not in partial]
    path.write_text("".join(line + "\n" for line in kept))
    return len(kept)


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


def stream_clip(clip: ClipRef, token: str | None) -> Iterator[tuple[float, np.ndarray]]:
    """`(t_s, frame)` one at a time, so a clip is never held whole.

    `decode_clip` below materialises every frame, which at 960x540 in colour is 1.55 MB each
    and 7.4 GB for a 1200 s clip. Three of those exhausted the box and had a run killed before
    it wrote a row -- the identical defect `docs/DECISIONS.md` D043 records in the labeller,
    left in the sibling path because the labeller was the one that fell over first. The smoke
    path still uses `decode_clip`: it is bounded by `--smoke` and small by construction.
    """
    url = ShardReader(REPO_ID, clip.shard, token)._resolve()
    times = sample_times(clip.duration_s)
    argv = ffmpeg_clip_argv(url, clip, fps_sampled=ANALYSIS_HZ,
                            width=DECODE_WIDTH, height=DECODE_HEIGHT,
                            max_frames=len(times), pix_fmt=DECODE_PIX_FMT)
    frames = decode_gray_frames(argv, DECODE_WIDTH, DECODE_HEIGHT, channels=3)
    yield from zip(times, frames, strict=False)


def decode_clip(clip: ClipRef, token: str | None, *, limit: int | None = None) -> ClipFrames:
    url = ShardReader(REPO_ID, clip.shard, token)._resolve()
    argv = ffmpeg_clip_argv(url, clip, fps_sampled=ANALYSIS_HZ,
                            width=DECODE_WIDTH, height=DECODE_HEIGHT, max_frames=limit,
                            pix_fmt=DECODE_PIX_FMT)
    frames = list(decode_gray_frames(argv, DECODE_WIDTH, DECODE_HEIGHT, channels=3))
    times = sample_times(clip.duration_s)[: len(frames)]
    return ClipFrames(clip=clip, times=times, frames=frames)


def build_detector(name: str) -> FrameDetector:
    """Construct the real model. Imported lazily so the rest of this file runs without torch."""
    if name == "100doh":
        from detectors.doh100 import Doh100Detector

        return Doh100Detector()
    if name == "egohos":
        from detectors.egohos import EgoHosDetector

        return EgoHosDetector()
    raise ValueError(
        f"{name!r} is not a detector this contract knows. CONTRACTS.md's mask_source is "
        f"'100doh' or 'egohos'; a hand box never comes from anything else."
    )


def iter_clips(manifest: Path, corpus_rev: str) -> Iterator[ClipRef]:
    rows = [MetadataRow(**json.loads(line))
            for line in manifest.read_text().splitlines() if line.strip()]
    yield from clip_refs(rows, corpus_rev=corpus_rev)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--out", default="results/pilot/detections.jsonl")
    parser.add_argument("--detector", default="100doh", choices=["100doh", "egohos"])
    parser.add_argument("--corpus-rev", default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    parser.add_argument("--smoke", type=int, default=None,
                        help="decode and detect this many frames, measure the rate, write nothing")
    args = parser.parse_args(list(argv) if argv is not None else None)

    token = _token()
    clips = list(iter_clips(ROOT / args.manifest, args.corpus_rev))
    detector = build_detector(args.detector)

    if args.smoke:
        remaining = args.smoke
        decoded = 0
        started = time.time()
        with_box = 0
        failed = 0
        widths: list[float] = []
        for clip in clips:
            if remaining <= 0:
                break
            batch = decode_clip(clip, token, limit=remaining)
            rows = detections_for_clip(batch, detector)
            with_box += sum(1 for r in rows if r["boxes"])
            for r in rows:
                found = r["boxes"]
                assert isinstance(found, list)
                widths.extend(float(b["width"]) for b in found)
            failed += sum(1 for r in rows if "failed_reason" in r)
            decoded += len(batch.frames)
            remaining -= len(batch.frames)
        elapsed = time.time() - started
        rate = decoded / elapsed if elapsed else 0.0
        print(f"smoke: {decoded} frames in {elapsed:.1f}s -> {rate:.1f} frames/s "
              f"(decode + detect, end to end)")
        print(f"  docs/METHOD.md E3 estimates ~20 frames/s for the detector alone")
        # The install-sanity signal. An mmcv-full that does not match the installed torch can
        # import cleanly and then produce empty or nonsense output; a box coverage near zero
        # means a broken install far more often than it means a corpus without hands. It is
        # deliberately *not* compared against H2c's 60% here -- that is a pre-registered gate
        # on the full pilot, and reading a smoke sample as though it settled one would be
        # exactly the shortcut docs/PRE-REGISTRATION.md exists to prevent.
        print(f"  box coverage on this sample: {with_box}/{decoded} frames; "
              f"{failed} frames the model raised on")
        # Box widths, because a plausible *count* of boxes says nothing about their size and
        # the size is what the whole speed axis is divided by. This is the check that caught
        # `docs/DECISIONS.md` D048: boxes reaching 70% of the frame width, from a bounding box
        # drawn over a disconnected mask. It costs one line and it runs before the money does.
        if widths:
            q = np.percentile(np.asarray(widths), [10, 50, 90, 100])
            print(f"  box width px, **native clip coordinates**: p10 {q[0]:.0f} "
                  f"median {q[1]:.0f} p90 {q[2]:.0f} max {q[3]:.0f}")
            print("  boxes are scaled to native before they are written, so these are not in "
                  "the detector's own pixels; at 1920 wide a hand at the assumed 0.45 m is "
                  "~193 px (results/a14_translation_floor.json). A median far above that is a "
                  "mask defect, not a large hand.")
        if decoded and with_box == 0:
            print("  WARNING: no frame produced a box. Check the install before buying the "
                  "pilot run; a mismatched mmcv-full imports cleanly and segments nothing.")
        print(f"  at this rate the pilot's {sum(1 for _ in clips)} clips need "
              f"{sum(len(sample_times(c.duration_s)) for c in clips) / rate / 3600:.2f} h"
              if rate else "  rate unavailable")
        return 0

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    have = rows_per_clip(out)
    # From the **whole** manifest, not this invocation's slice. Sharded onto one `--out`, a
    # clip completed by another shard has no entry here, lands in `partial`, and is deleted.
    # `run_labeller.py` builds it from every clip for exactly this reason; D049 said a named
    # mechanism speaks to every place it lives and this half was not carried across (D064).
    every = list(iter_clips(ROOT / args.manifest, args.corpus_rev))
    expected = {c.clip_id: len(sample_times(c.duration_s)) for c in every}
    complete = {cid for cid, n in have.items() if n == expected.get(cid)}
    partial = set(have) - complete
    if partial:
        kept = drop_partial_clips(out, partial)
        print(f"dropped {len(partial)} partly-written clips, {kept} rows kept", flush=True)
    done = complete
    todo = [c for c in clips if c.clip_id not in complete]
    print(f"{len(clips)} clips, {len(done)} already detected, {len(todo)} to go", flush=True)

    started = time.time()
    frames_total = 0
    with out.open("a") as handle:
        for i, clip in enumerate(todo, 1):
            n_frames = 0
            for t_s, frame in stream_clip(clip, token):
                one = ClipFrames(clip=clip, times=[t_s], frames=[frame])
                for row in detections_for_clip(one, detector):
                    handle.write(json.dumps(row) + "\n")
                n_frames += 1
            handle.flush()  # a preemption after this loses at most one clip
            frames_total += n_frames
            elapsed = time.time() - started
            print(f"  {i}/{len(todo)} clips, {frames_total} frames, "
                  f"{frames_total / elapsed:.1f} frames/s", flush=True)

    print(f"\npilot gates (values stay in {out.parent}, D018):")
    print(f"  {'PASS' if not todo or frames_total else 'FAIL'}  detections written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
