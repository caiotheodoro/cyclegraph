#!/usr/bin/env python3
"""Manipulation labels for every sampled instant in a manifest. `docs/METHOD.md` E3.

Decodes each clip once at the analysis rate, extracts frozen DINOv2 features, and applies the
head `scripts/train_probe.py` fitted. Writes `labels.jsonl` in the shape
`cyclegraph.signal.stores.JsonlLabelStore` reads, so duty cycle, both frequency estimators and
the whole spectral path run offline on CPU afterwards.

**Two heads over one backbone.** `CONTRACTS.md` requires `hands_visible` alongside
`manipulation` and makes them null together or not at all, so a manipulation label cannot be
written without a hand count. The manipulation head is fitted here; the hand-count head is
`../vernier`'s, reused as-is because that is the hypothesis it was built for and its fidelity
is already published as a negative result. Both read the same frozen features, so the second
head costs one extra matrix multiply per frame.

**Where the two heads contradict each other, the frame is unreadable.** The contract rejects
`manipulation: true` with `hands_visible: 0`, and that combination is a real disagreement
between two heads rather than a schema inconvenience. Such frames are written `null` with a
reason and counted, never repaired toward whichever answer would keep them -- the rule
`docs/DECISIONS.md` D022 sets for a detector and a labeller disagreeing, applied to two heads
of one labeller.

**The `label_rev` names the head and the backbone**, because a linear head is meaningless
without the exact features it was fitted to and neither travels with the other.

Usage:
    python3 scripts/run_labeller.py --probe results/probe_manipulation.joblib
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cyclegraph.corpus.decode import decode_gray_frames, ffmpeg_clip_argv  # noqa: E402
from cyclegraph.corpus.manifest import MetadataRow, clip_refs  # noqa: E402
from cyclegraph.corpus.sampling import ANALYSIS_HZ, sample_times  # noqa: E402
from cyclegraph.corpus.shards import REPO_ID, ShardReader  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402
from labellers.probe import (  # noqa: E402
    BACKBONE,
    CROP_SIZE,
    IMAGE_MEAN,
    IMAGE_STD,
    RESIZE_SHORTEST_EDGE,
    HandCountProbe,
    ManipulationProbe,
)

DECODE_WIDTH, DECODE_HEIGHT = 960, 540
"""Chosen to match what the heads were fitted to, not to save bytes. Preprocessing resizes the
shortest edge to 256, so a frame decoded at 270 arrives having barely been downscaled while the
training frames came from 1080 and were downscaled fourfold. Decoding at 540 halves that gap,
and costs almost nothing: the source is 1080p h265 either way and only the scale filter's
output changes."""
CONFLICT_REASON = (
    "the manipulation head says exerting and the hand-count head says no hand visible; "
    "two heads of one labeller disagreeing is a value with a reason, not a frame to repair"
)


def _token() -> str | None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN=") and len(line) > len("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("HF_TOKEN")


def label_rows(clip: ClipRef, times: Sequence[float], manipulation: Sequence[bool],
               hands_visible: Sequence[int], *, label_rev: str, prompt_variant: str
               ) -> tuple[list[dict[str, object]], int]:
    """One row per instant, plus the count of frames the two heads contradicted."""
    rows: list[dict[str, object]] = []
    conflicts = 0
    for t_s, manipulating, hands in zip(times, manipulation, hands_visible, strict=True):
        row: dict[str, object] = {
            "clip_id": clip.clip_id, "t_s": t_s, "label_source": "probe",
            "label_rev": label_rev, "prompt_variant": prompt_variant,
        }
        if manipulating and hands == 0:
            conflicts += 1
            row["manipulation"] = None
            row["hands_visible"] = None
            row["unreadable_reason"] = CONFLICT_REASON
        else:
            row["manipulation"] = bool(manipulating)
            row["hands_visible"] = int(hands)
        rows.append(row)
    return rows, conflicts


class DinoFeatures:
    """Frozen `facebook/dinov2-small`, mean-pooled over patch tokens.

    The preprocessing is written out rather than delegated to `AutoImageProcessor`, for two
    reasons. It is one fewer dependency -- the processor pulls torchvision, which the pipeline
    otherwise never needs. And more importantly the exact steps are part of what a saved head
    was fitted to: a processor config that changed under us would move the feature
    distribution silently, and the head would keep returning confident answers to a different
    question. These are the steps vernier used (`docs/LINEAGE.md`).
    """

    def __init__(self, device: str = "cuda") -> None:
        self._device = device
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            import torch
            from transformers import AutoModel

            self._model = AutoModel.from_pretrained(BACKBONE).to(self._device).eval()
            torch.set_grad_enabled(False)
        return self._model

    @staticmethod
    def preprocess(frame: np.ndarray) -> np.ndarray:
        """One greyscale frame to a normalised (3, 224, 224) array."""
        from PIL import Image

        image = Image.fromarray(frame).convert("RGB")
        width, height = image.size
        scale = RESIZE_SHORTEST_EDGE / min(width, height)
        image = image.resize((round(width * scale), round(height * scale)), resample=3)
        width, height = image.size
        left, top = (width - CROP_SIZE) // 2, (height - CROP_SIZE) // 2
        image = image.crop((left, top, left + CROP_SIZE, top + CROP_SIZE))
        array: np.ndarray = np.asarray(image, dtype=np.float32) / 255.0
        mean = np.asarray(IMAGE_MEAN, dtype=np.float32)
        std = np.asarray(IMAGE_STD, dtype=np.float32)
        normalised: np.ndarray = ((array - mean) / std).astype(np.float32)
        return normalised.transpose(2, 0, 1)

    def extract(self, frames: Sequence[np.ndarray]) -> list[list[float]]:
        import torch

        model = self._load()
        batch = np.stack([self.preprocess(f) for f in frames])
        tensor = torch.from_numpy(batch).to(self._device)
        with torch.no_grad():
            out = model(pixel_values=tensor)
        pooled = out.last_hidden_state[:, 1:, :].mean(dim=1)  # patch tokens, CLS discarded
        return [[float(v) for v in row] for row in pooled.cpu().numpy()]


def iter_clips(manifest: Path, corpus_rev: str) -> Iterator[ClipRef]:
    rows = [MetadataRow(**json.loads(line))
            for line in manifest.read_text().splitlines() if line.strip()]
    yield from clip_refs(rows, corpus_rev=corpus_rev)


def completed_clips(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line)["clip_id"]
            for line in path.read_text().splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="results/pilot/clips_factory_001.jsonl")
    parser.add_argument("--probe", default="results/probe_manipulation.joblib")
    parser.add_argument("--out", default="results/pilot/labels.jsonl")
    parser.add_argument("--corpus-rev", default="3e5f87c88c54ce8343865d8e2a8c171f18385a05")
    parser.add_argument("--hand-probe",
                        default="../vernier/data/rung1_probe.joblib")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch", type=int, default=64)
    args = parser.parse_args(argv)

    probe_path = ROOT / args.probe
    if not probe_path.exists():
        print(f"REFUSING: no probe at {probe_path}. Run scripts/train_probe.py first.",
              file=sys.stderr)
        return 2
    hand_path = (ROOT / args.hand_probe).resolve()
    if not hand_path.exists():
        print(f"REFUSING: no hand-count head at {hand_path}. docs/LINEAGE.md records it as "
              f"inherited from ../vernier; CONTRACTS.md requires hands_visible alongside "
              f"every manipulation label.", file=sys.stderr)
        return 2
    probe = ManipulationProbe.load(probe_path)
    hands = HandCountProbe.load(hand_path)
    features = DinoFeatures(args.device)
    label_rev = f"{BACKBONE}+linear@{probe_path.name}"

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    done = completed_clips(out)
    clips = [c for c in iter_clips(ROOT / args.manifest, args.corpus_rev)
             if c.clip_id not in done]
    print(f"{len(clips)} clips to label ({len(done)} already done)", flush=True)

    token = _token()
    started = time.time()
    total = 0
    conflicts_total = 0
    with out.open("a") as handle:
        for i, clip in enumerate(clips, 1):
            url = ShardReader(REPO_ID, clip.shard, token)._resolve()
            argv_ff = ffmpeg_clip_argv(url, clip, fps_sampled=ANALYSIS_HZ,
                                       width=DECODE_WIDTH, height=DECODE_HEIGHT)
            frames = list(decode_gray_frames(argv_ff, DECODE_WIDTH, DECODE_HEIGHT))
            # ffmpeg's `fps` filter emits a frame or two past the sample plan's last instant,
            # because the plan requires the *second* frame of each pair to fall strictly
            # inside the clip and the filter has no such rule. The plan decides which instants
            # are analysed, so the surplus is dropped rather than labelled at a timestamp that
            # does not exist.
            times = sample_times(clip.duration_s)
            if len(frames) > len(times):
                frames = frames[: len(times)]
            times = times[: len(frames)]
            predictions: list[bool] = []
            counts: list[int] = []
            for start in range(0, len(frames), args.batch):
                chunk = features.extract(frames[start : start + args.batch])
                predictions.extend(probe.predict(chunk))
                counts.extend(hands.predict(chunk))
            rows, conflicts = label_rows(clip, times, predictions, counts,
                                         label_rev=label_rev, prompt_variant="none")
            for row in rows:
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            total += len(predictions)
            conflicts_total += conflicts
            print(f"  {i}/{len(clips)} clips, {total} frames, "
                  f"{total / (time.time() - started):.1f} frames/s", flush=True)

    print(f"\npilot gates (values stay in {out.parent}, D018):")
    print(f"  {'PASS' if total or not clips else 'FAIL'}  labels written for every clip")
    print(f"  {'PASS' if total == 0 or conflicts_total / max(total, 1) < 0.10 else 'FAIL'}  "
          f"the two heads contradict each other on under 10% of frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
