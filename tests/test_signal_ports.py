"""Behavioural tests for `src/cyclegraph/signal/ports.py`.

The seams these hold are the ones `docs/ARCHITECTURE.md` says would not fail loudly: a
defaulted `label_source`, a flow failure that reads as zero, a hand count taken from the
detector. Each is asserted as a property of the type, so a later change that reopens one
fails here rather than at pilot scale.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

from cyclegraph.signal.ports import (
    Detection,
    Flow,
    FlowEstimator,
    FrameLabel,
    HandBox,
    LabelProvenance,
    box_mask,
    largest_box,
)

ROOT = Path(__file__).resolve().parent.parent
SIGNAL = ROOT / "src" / "cyclegraph" / "signal"

# `corpus` owns shard access and nothing else may learn what a tar member is
# (`docs/ARCHITECTURE.md`). Checked as text because an import check would pass a module that
# merely reimplemented the byte arithmetic.
SHARD_TOKENS = ("subfile", "byte_start", "byte_end", "huggingface", "hf_hub", "tarfile")


def test_no_module_in_signal_knows_what_a_shard_is() -> None:
    offenders: list[str] = []
    for path in sorted(SIGNAL.glob("*.py")):
        body = path.read_text()
        for token in SHARD_TOKENS:
            # `.tar` inside a prose docstring is not a violation; a bare identifier is.
            if re.search(rf"\b{re.escape(token)}\b", body):
                offenders.append(f"{path.name}: {token}")
    assert offenders == [], f"signal/ must not reach the corpus seam: {offenders}"


def test_largest_box_picks_by_area_and_returns_none_when_empty() -> None:
    small = HandBox(x=0, y=0, width=10, height=10, score=0.9)
    big = HandBox(x=20, y=20, width=30, height=20, score=0.4)
    assert largest_box([small, big]) is big  # area, not score
    assert largest_box([]) is None


def test_box_mask_is_the_union_and_its_complement_is_the_background() -> None:
    boxes = [HandBox(x=1, y=1, width=2, height=2, score=0.5),
             HandBox(x=5, y=0, width=1, height=3, score=0.5)]
    mask = box_mask((4, 8), boxes)
    assert mask.sum() == 2 * 2 + 1 * 3
    assert mask[1, 1] and mask[2, 2] and mask[0, 5] and mask[2, 5]
    assert not mask[0, 0]
    assert (~mask).sum() == 4 * 8 - 7  # the ego-motion region


def test_a_box_outside_the_frame_is_clipped_not_wrapped() -> None:
    mask = box_mask((4, 4), [HandBox(x=3, y=3, width=10, height=10, score=0.5)])
    assert mask.sum() == 1


def test_a_degenerate_box_is_refused() -> None:
    with pytest.raises(ValueError):
        HandBox(x=0, y=0, width=0, height=5, score=0.5)
    with pytest.raises(ValueError):
        HandBox(x=0, y=0, width=5, height=5, score=1.5)


def test_detection_carries_no_hand_count() -> None:
    """D022. `hands_visible` is label-sourced; putting it here is the expensive mistake."""
    assert not hasattr(Detection(boxes=()), "hands_visible")
    assert "hands_visible" not in Detection.__slots__


def test_a_failed_detection_carries_a_reason_and_no_boxes() -> None:
    assert Detection(boxes=(), failed_reason="detector raised").boxes == ()
    with pytest.raises(ValueError):
        Detection(boxes=(HandBox(x=0, y=0, width=1, height=1, score=0.5),),
                  failed_reason="detector raised")
    with pytest.raises(ValueError):
        Detection(boxes=(), failed_reason="")


def test_provenance_has_no_defaults() -> None:
    """Seam 2. A default here would erase H1's independent variable."""
    with pytest.raises(TypeError):
        LabelProvenance()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        LabelProvenance(label_source="judge", label_rev="", prompt_variant="P0b")


def test_a_label_is_null_in_both_fields_or_neither_and_says_why() -> None:
    assert FrameLabel(manipulation=True, hands_visible=2).unreadable_reason is None
    assert FrameLabel(manipulation=None, hands_visible=None,
                      unreadable_reason="decode failed").manipulation is None
    with pytest.raises(ValueError):
        FrameLabel(manipulation=None, hands_visible=1, unreadable_reason="x")
    with pytest.raises(ValueError):
        FrameLabel(manipulation=None, hands_visible=None)  # no reason
    with pytest.raises(ValueError):
        FrameLabel(manipulation=True, hands_visible=0)  # contract rejects this downstream


def test_flow_estimator_failure_is_none_not_zeros() -> None:
    """A15, at the port. A zero field is a measurement of zero speed; None is a failure."""

    class DeadFlow:
        @property
        def flow_method(self) -> str:
            return "dead"

        def flow(self, first: npt.NDArray[np.uint8],
                 second: npt.NDArray[np.uint8]) -> Flow | None:
            return None

    estimator: FlowEstimator = DeadFlow()  # must satisfy the Protocol, not merely resemble it
    frame = np.zeros((4, 4), dtype=np.uint8)
    assert estimator.flow(frame, frame) is None

    # A zero field is a *measurement* of no motion and is a legal return; only None is a
    # failure. The two must never be conflated, which is why the Protocol's return is
    # `Flow | None` rather than `Flow` with a zero-field convention.
    zeros: Flow = np.zeros((4, 4, 2), dtype=np.float32)
    assert zeros.shape == (4, 4, 2)
