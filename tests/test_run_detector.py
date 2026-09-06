"""Tests for `scripts/run_detector.py`.

The model is the untestable part; everything around it is not, and it is where a GPU run's
work gets silently lost -- a resume that re-detects nothing, boxes written in the wrong
coordinate space, an instant with no row where the detector actually ran. Those are tested
here with a fake detector, offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from run_detector import (  # noqa: E402
    ClipFrames,
    build_detector,
    drop_partial_clips,
    rows_per_clip,
    detections_for_clip,
    scale_box,
)

from cyclegraph.corpus.sampling import sample_times
from cyclegraph.models import ClipRef  # noqa: E402
from cyclegraph.signal.ports import HandBox, MaskSource  # noqa: E402
from cyclegraph.signal.stores import JsonlDetectionStore  # noqa: E402
from tests import fixtures  # noqa: E402


class _Fake:
    """A detector that finds one box in the middle of whatever it is given."""

    mask_source: MaskSource = "100doh"

    def __init__(self, raise_on: int | None = None) -> None:
        self.calls = 0
        self._raise_on = raise_on

    def boxes(self, frame: np.ndarray) -> list[HandBox]:
        self.calls += 1
        if self._raise_on is not None and self.calls == self._raise_on:
            raise RuntimeError("cuda oom")
        h, w = frame.shape
        return [HandBox(x=w / 4, y=h / 4, width=w / 2, height=h / 2, score=0.9)]


def _clip() -> ClipRef:
    return ClipRef.model_validate({**fixtures.CLIP_REF, "width": 1920, "height": 1080})


def _frames(n: int, size: tuple[int, int] = (540, 960)) -> ClipFrames:
    return ClipFrames(clip=_clip(), times=[i * 0.25 for i in range(n)],
                      frames=[np.zeros(size, dtype=np.uint8) for _ in range(n)])


def test_boxes_are_written_in_native_clip_pixels() -> None:
    """`hand_box_width_px` is the hand-breadth scale. A consumer must not have to know this
    script's decode size to interpret it, so the scaling happens before the write."""
    rows = detections_for_clip(_frames(1), _Fake())
    box = rows[0]["boxes"][0]  # type: ignore[index]
    assert box["width"] == pytest.approx(1920 / 2)  # half of native, not half of 960
    assert box["height"] == pytest.approx(1080 / 2)


def test_scale_box_is_the_identity_when_the_sizes_match() -> None:
    box = HandBox(x=10, y=20, width=30, height=40, score=0.5)
    same = scale_box(box, from_width=960, from_height=540, to_width=960, to_height=540)
    assert (same.x, same.y, same.width, same.height) == (10, 20, 30, 40)


def test_every_decoded_instant_gets_a_row_even_with_no_box() -> None:
    """An instant with no row means 'the detector did not run here' to the store that reads
    this. An instant where it ran and found nothing is a different fact."""

    class _Empty(_Fake):
        def boxes(self, frame: np.ndarray) -> list[HandBox]:
            return []

    rows = detections_for_clip(_frames(5), _Empty())
    assert len(rows) == 5
    assert all(r["boxes"] == [] for r in rows)


def test_a_frame_the_model_cannot_process_is_a_value_not_a_crash() -> None:
    """A CUDA OOM on frame 3 of 200,000 must not lose the other 199,999."""
    rows = detections_for_clip(_frames(5), _Fake(raise_on=3))
    assert len(rows) == 5
    assert rows[2]["failed_reason"]
    assert rows[2]["boxes"] == []
    assert not rows[3].get("failed_reason")


def test_the_rows_round_trip_through_the_store_that_consumes_them(tmp_path: Path) -> None:
    """The contract between this script and `signal/stores.py`, asserted rather than assumed."""
    rows = detections_for_clip(_frames(3), _Fake())
    path = tmp_path / "detections.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    store = JsonlDetectionStore.from_path(path)
    assert store.mask_source == "100doh"
    found = store.detect(_clip().clip_id, 0.25)
    assert len(found.boxes) == 1
    assert found.boxes[0].width == pytest.approx(960.0)


def test_resume_counts_rows_rather_than_trusting_that_any_exist(tmp_path: Path) -> None:
    """A spot instance is interrupted, not asked, so work already bought is not re-bought --
    but a clip it was interrupted *inside* has rows and is not finished.

    This asserted that two rows made a clip complete, which is the defect
    `docs/DECISIONS.md` D043 names and D052 found still here: a done-set resumes past the part
    of a clip that was never written, and the hole reaches H2c's coverage as no-box samples.
    """
    path = tmp_path / "detections.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in detections_for_clip(_frames(2), _Fake())))
    counts = rows_per_clip(path)
    assert counts == {_clip().clip_id: 2}
    assert rows_per_clip(tmp_path / "absent.jsonl") == {}

    # Two rows is not a finished clip: the plan for this clip is far longer, so a caller
    # comparing against the sample plan sees it as partial.
    assert len(sample_times(_clip().duration_s)) > 2


def test_a_partly_written_clip_is_dropped_so_the_rerun_appends_a_whole_one(
        tmp_path: Path) -> None:
    """Without this the re-run appends a second copy of the clip's rows and the file carries a
    clip that is both short and duplicated."""
    path = tmp_path / "detections.jsonl"
    rows = detections_for_clip(_frames(3), _Fake())
    other = [{**r, "clip_id": "factory_002/worker_009/000004"} for r in rows[:2]]
    path.write_text("\n".join(json.dumps(r) for r in rows + other) + "\n")

    kept = drop_partial_clips(path, {_clip().clip_id})
    assert kept == 2
    remaining = rows_per_clip(path)
    assert _clip().clip_id not in remaining
    assert remaining == {"factory_002/worker_009/000004": 2}
    assert drop_partial_clips(path, set()) == 0  # nothing to do is not a rewrite


def test_an_unknown_detector_is_refused_by_name() -> None:
    """`CONTRACTS.md`'s `mask_source` is a closed enum and this is where a third one would
    otherwise sneak in."""
    with pytest.raises(ValueError, match="not a detector this contract knows"):
        build_detector("mediapipe")
