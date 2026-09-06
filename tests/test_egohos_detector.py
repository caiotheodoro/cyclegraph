"""Tests for `scripts/detectors/egohos.py`'s pure half.

The model itself needs mmsegmentation and a GPU. What is tested here is the part that turns a
label map into a box, which is the part that decides `hand_box_width_px` -- the number the
whole speed axis is divided by (`docs/RUBRIC.md` v1.4.0, `docs/DECISIONS.md` D047). Leaving it
untested until it runs on a rented GPU is how a scale error reaches a published number.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from detectors.egohos import (  # noqa: E402
    HAND_CLASSES,
    MIN_MASK_PIXELS,
    EgoHosDetector,
    boxes_from_labels,
)


def _labels(shape: tuple[int, int] = (60, 80)) -> np.ndarray:
    return np.zeros(shape, dtype=np.uint8)


def test_each_hand_becomes_one_box_at_the_masks_own_extent() -> None:
    """The golden case, computed by hand. A mask spanning columns 3..14 is 12 px wide, not 11:
    the extent is inclusive of both end pixels."""
    labels = _labels()
    labels[2:12, 3:15] = HAND_CLASSES[0]     # rows 2..11, cols 3..14
    labels[5:16, 20:29] = HAND_CLASSES[1]    # rows 5..15, cols 20..28
    boxes = boxes_from_labels(labels)
    assert len(boxes) == 2
    left, right = boxes
    assert (left.x, left.y, left.width, left.height) == (3.0, 2.0, 12.0, 10.0)
    assert (right.x, right.y, right.width, right.height) == (20.0, 5.0, 9.0, 11.0)


def test_a_one_pixel_wide_hand_has_width_one_not_zero() -> None:
    """Without the +1 this raises, because `HandBox` refuses a zero-width box -- so the defect
    would surface as a crash on a real frame rather than as a wrong number. Pinned anyway: the
    fix is arithmetic that a reader has to trust."""
    labels = _labels((MIN_MASK_PIXELS + 10, 80))
    labels[0:MIN_MASK_PIXELS, 7:8] = HAND_CLASSES[0]
    boxes = boxes_from_labels(labels)
    assert len(boxes) == 1
    assert boxes[0].width == 1.0
    assert boxes[0].height == float(MIN_MASK_PIXELS)


def test_a_speck_below_the_floor_is_not_a_hand() -> None:
    """A few stray pixels have a tiny bounding box, and `hand_breadth_mm / box_width_px` turns
    a tiny box into a very large mm/s. The floor is on region size, not on a confidence the
    segmenter does not emit."""
    labels = _labels()
    labels[0:4, 0:4] = HAND_CLASSES[0]  # 16 px, below the floor
    assert boxes_from_labels(labels) == []
    labels[0:9, 0:9] = HAND_CLASSES[0]  # 81 px, above it
    assert len(boxes_from_labels(labels)) == 1


def test_a_frame_with_no_hand_yields_no_box_rather_than_a_frame_sized_one() -> None:
    assert boxes_from_labels(_labels()) == []


def test_an_object_the_hand_is_holding_is_not_part_of_the_hand() -> None:
    """EgoHOS's object classes exist in the label map and are deliberately not read
    (`docs/RUBRIC.md` v1.4.0). A box drawn around hand-plus-object would inflate the box width
    and deflate every speed on the clip."""
    labels = _labels()
    labels[10:20, 10:20] = HAND_CLASSES[0]
    labels[10:20, 40:70] = 3  # an interacting object, far from the hand
    boxes = boxes_from_labels(labels)
    assert len(boxes) == 1
    assert boxes[0].x + boxes[0].width <= 40.0


def test_a_speck_across_the_frame_does_not_stretch_the_box_to_reach_it() -> None:
    """The defect real frames exposed and clean synthetic masks could not. A bounding box over
    every pixel of the class spans the segmenter's scattered false positives; measured on the
    corpus it produced boxes up to 676 px wide at 960x540 against a hand of about 96 px. The
    box is a *divisor* -- `hand_breadth_mm / box_width_px` -- so an inflated box deflates every
    speed on the clip, in the flattering direction. D048."""
    labels = _labels((60, 200))
    labels[10:26, 10:26] = HAND_CLASSES[0]        # the hand: 16x16 = 256 px
    labels[50:54, 190:196] = HAND_CLASSES[0]      # a speck at the far edge, 24 px
    boxes = boxes_from_labels(labels)
    assert len(boxes) == 1
    assert boxes[0].width == 16.0 and boxes[0].height == 16.0
    assert boxes[0].x + boxes[0].width < 50.0  # nowhere near the speck


def test_the_floor_applies_to_the_largest_component_not_the_class_total() -> None:
    """Otherwise a hand made only of specks passes the floor by adding them up, and its box is
    the extent of the scatter."""
    labels = _labels((60, 200))
    for i in range(6):
        labels[10:14, 10 + i * 30 : 14 + i * 30] = HAND_CLASSES[0]  # 6 specks, 16 px each
    assert int((labels == HAND_CLASSES[0]).sum()) > MIN_MASK_PIXELS
    assert boxes_from_labels(labels) == []


def test_the_score_is_not_a_confidence() -> None:
    """It is 1.0 and means "this hand was segmented". The model emits a label map and no
    per-region probability, so any other value would be a number nothing measured."""
    labels = _labels()
    labels[0:10, 0:10] = HAND_CLASSES[0]
    assert boxes_from_labels(labels)[0].score == 1.0


def test_a_grey_frame_is_refused_without_needing_the_model_installed() -> None:
    """D040's defect, in the detector path. The check runs before the mmsegmentation import so
    it fails on any machine, not only on one that could load the weights."""
    detector = object.__new__(EgoHosDetector)  # no EGOHOS_ROOT on this machine
    with pytest.raises(ValueError, match="colour"):
        detector.segment(np.zeros((16, 16), dtype=np.uint8))
    with pytest.raises(ValueError, match="colour"):
        detector.segment(np.zeros((16, 16, 1), dtype=np.uint8))
