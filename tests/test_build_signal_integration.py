"""End-to-end test of `scripts/build_signal.py` against stubbed frames.

This stage has never completed a real run: every `HandSpeedEstimate` in the repository is
`status: "no_detector"`, because 100DOH's weights are unobtainable (`docs/DECISIONS.md` D037).
So the first time it runs for real will be on a rented GPU after a five-hour detector run, and
a structural error there costs the whole batch. This runs the same code path offline against
frames whose motion is known, and asserts the records it writes are valid and say what the
inputs imply.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_signal  # noqa: E402

from cyclegraph.corpus.sampling import sample_times  # noqa: E402
from cyclegraph.models import FrameSignal, HandSpeedEstimate  # noqa: E402

FPS = 30.0
DURATION_S = 61.0
WIDTH, HEIGHT = 1920, 1080
REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"
CLIP_ID = "factory_001/worker_001/000000"
BACKGROUND_SHIFT_PX = 3   # the camera's own motion, per source frame, in 960-wide pixels
HAND_EXTRA_PX = 2         # what the hand does on top of it -- the only real signal here
BOX_NATIVE_PX = 200.0

# The rubric divides the residual by the clip's median box width and multiplies by 85 mm, and
# both are pixels at the same scale, so the ratio is what matters and the decode scale cancels.
# The stub shifts both axes equally, so the hand's motion relative to the background is
# (HAND_EXTRA_PX, HAND_EXTRA_PX) and its magnitude is the diagonal -- 2*sqrt(2) = 2.83 px, not
# 2. Getting that wrong is what the first version of this constant did, and the pipeline's
# answer was right where the constant was not:
#   85 mm * (2*sqrt(2) / 100) / (1/30 s) = 72.1 mm/s
EXPECTED_MM_S = (85.0 * (HAND_EXTRA_PX * math.sqrt(2.0) / (BOX_NATIVE_PX / 2))
                 / (1.0 / FPS))


def _write_inputs(tmp: Path) -> tuple[Path, Path, Path]:
    manifest = tmp / "manifest.jsonl"
    manifest.write_text(json.dumps({
        "factory_id": "factory_001", "worker_id": "worker_001", "clip_index": 0,
        "shard": "factory_001/workers/worker_001/f.tar", "byte_start": 1024,
        "byte_end": 4096, "duration_s": DURATION_S, "fps": FPS,
        "width": WIDTH, "height": HEIGHT, "codec": "h264",
    }) + "\n")

    times = sample_times(DURATION_S)
    detections = tmp / "detections.jsonl"
    detections.write_text("".join(json.dumps({
        "clip_id": CLIP_ID, "t_s": t, "mask_source": "egohos",
        "boxes": [{"x": 800.0, "y": 400.0, "width": BOX_NATIVE_PX,
                   "height": BOX_NATIVE_PX, "score": 1.0}],
    }) + "\n" for t in times))

    labels = tmp / "labels.jsonl"
    labels.write_text("".join(json.dumps({
        "clip_id": CLIP_ID, "t_s": t, "label_source": "probe", "label_rev": "stub@1",
        "prompt_variant": "none", "manipulation": True, "hands_visible": 2,
    }) + "\n" for t in times))
    return manifest, detections, labels


def _stub_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Textured frames that translate by a known amount each source frame."""
    rng = np.random.default_rng(0)
    base = rng.integers(0, 255, size=(HEIGHT // 2, WIDTH // 2), dtype=np.uint8)

    def fake_argv(url: str, clip: Any, **kw: Any) -> list[str]:
        fake_argv.limit = int(kw["max_frames"])  # type: ignore[attr-defined]
        fake_argv.size = (int(kw["width"]), int(kw["height"]))  # type: ignore[attr-defined]
        return ["ffmpeg"]

    def fake_decode(argv: list[str], width: int, height: int, **kw: Any) -> Iterator[Any]:
        big = np.array(Image_resize(base, width + 256, height + 256))
        # The hand box in flow coordinates: the detection is native, the decode is half of it.
        bx, by = 800 // 2, 400 // 2
        bw = bh = int(BOX_NATIVE_PX // 2)
        for n in range(fake_argv.limit):  # type: ignore[attr-defined]
            back = (n * BACKGROUND_SHIFT_PX) % 128
            frame = np.ascontiguousarray(big[back:back + height, back:back + width])
            # The hand moves faster than the scene it sits in. Without this the only motion is
            # the camera's, the ego-motion subtraction removes all of it, and any speed the
            # stage reports is numerical noise -- which is exactly what made an earlier version
            # of this test unable to tell a correct run from one pairing a frame with itself.
            hand = (n * (BACKGROUND_SHIFT_PX + HAND_EXTRA_PX)) % 128
            frame[by:by + bh, bx:bx + bw] = big[hand:hand + bh, hand:hand + bw]
            yield frame

    def Image_resize(a: np.ndarray, w: int, h: int) -> np.ndarray:
        ys = (np.arange(h) * a.shape[0] / h).astype(int)
        xs = (np.arange(w) * a.shape[1] / w).astype(int)
        return a[np.ix_(ys, xs)]

    class FakeReader:
        def __init__(self, *a: Any, **k: Any) -> None: ...
        def _resolve(self) -> str: return "url"

    monkeypatch.setattr(build_signal, "ffmpeg_clip_argv", fake_argv)
    monkeypatch.setattr(build_signal, "decode_gray_frames", fake_decode)
    monkeypatch.setattr(build_signal, "ShardReader", FakeReader)


def test_the_stage_writes_valid_records_for_a_clip_it_can_measure(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, detections, labels = _write_inputs(tmp_path)
    _stub_decode(monkeypatch)
    out = tmp_path / "out"

    code = build_signal.main([
        "--manifest", str(manifest), "--detections", str(detections),
        "--labels", str(labels), "--out-dir", str(out), "--corpus-rev", REV,
    ])
    assert code == 0

    signals = [FrameSignal.model_validate_json(line)
               for line in (out / "frame_signal.jsonl").read_text().splitlines() if line.strip()]
    speeds = [HandSpeedEstimate.model_validate_json(line)
              for line in (out / "hand_speed.jsonl").read_text().splitlines() if line.strip()]
    assert len(signals) == 1 and len(speeds) == 1

    signal, speed = signals[0], speeds[0]
    assert signal.status == "ok"
    assert signal.label_source == "probe"          # never defaulted (seam 2)
    assert signal.hand_mask_source == "egohos"
    assert signal.n_frames == len(sample_times(DURATION_S))

    # Every instant carried a box, so coverage is total and the status is not low_coverage.
    assert speed.n_with_box == speed.n_samples
    assert speed.coverage == pytest.approx(1.0)
    assert speed.status == "ok"
    # The hand's own motion, recovered. Asserting only "> 0" is not enough: with the pair
    # built from one frame twice the stage still reports 3.5e-07 mm/s, because Farneback on
    # identical frames returns a tiny non-zero field and neither its own `any()` guard nor
    # D023's exact-zero sample rule fires on it. A number this test would accept has to be the
    # right size, not merely positive.
    assert speed.rms_speed_mm_s is not None
    assert speed.rms_speed_mm_s == pytest.approx(EXPECTED_MM_S, rel=0.10)

    # Ego-motion really is subtracted: the background moves 3 px per frame and the hand 5, and
    # the reported speed is the difference, not the sum. A stage that forgot the subtraction
    # would report about 2.5x this -- `docs/RED-TEAM.md` A14's concern in its easiest case.
    assert speed.rms_speed_mm_s < EXPECTED_MM_S * 2.0


def test_a_pair_of_identical_frames_is_a_null_with_a_reason_not_a_speed_of_almost_zero(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """D051. `docs/RED-TEAM.md` A15 says a dead flow is a null with a reason and never a zero,
    and D023 implements that as an exactly-zero residual. Measured, that rule does not fire on
    the case it names: Farneback on two identical frames returns a tiny non-zero field, the
    residual comes out around 1e-07 mm/s, and the sample is counted as a real measurement of
    almost no motion. Frame equality is exact and catches it."""
    manifest, detections, labels = _write_inputs(tmp_path)
    _stub_decode(monkeypatch)

    def frozen(argv: list[str], width: int, height: int, **kw: Any) -> Iterator[Any]:
        rng = np.random.default_rng(1)
        still = rng.integers(0, 255, size=(height, width), dtype=np.uint8)
        for _ in range(int(build_signal.ffmpeg_clip_argv.limit)):  # type: ignore[attr-defined]
            yield still.copy()

    monkeypatch.setattr(build_signal, "decode_gray_frames", frozen)
    out = tmp_path / "out"
    build_signal.main([
        "--manifest", str(manifest), "--detections", str(detections),
        "--labels", str(labels), "--out-dir", str(out), "--corpus-rev", REV,
    ])
    speed = HandSpeedEstimate.model_validate_json(
        (out / "hand_speed.jsonl").read_text().splitlines()[0])
    assert speed.n_flow_null == speed.n_with_box   # every boxed sample is a null
    assert speed.status == "flow_failed"
    assert speed.rms_speed_mm_s is None            # not 3.5e-07
