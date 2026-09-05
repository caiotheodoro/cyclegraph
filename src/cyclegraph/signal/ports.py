"""The seams `signal` is built on: what a detector, a flow estimator and a labeller are.

Three `Protocol`s and the small value types they exchange. Nothing here runs a model, opens a
shard or touches the network -- that is what lets every estimator in this package be tested
against committed fixtures, and it is what `docs/WAVES.md`'s "tests pass offline with no
network" requires.

Two seams from `docs/ARCHITECTURE.md` are enforced by the shapes rather than by discipline:

*`label_source` is carried, never defaulted.* `LabelProvenance` has no default for any field.
H1 exists to measure how much the choice of labeller moves duty cycle, and a module that
defaulted the field would erase H1's independent variable.

*A missing hand or a failed flow is a value with a reason, never zero.* `FlowEstimator.flow`
returns `None` on failure rather than a zero field, so the A15 rule holds one level below
`HandSpeedEstimate`'s validator -- in code that never constructs a record at all.

`Detection` deliberately carries no hand count. `hands_visible` is label-sourced and
`hand_box_width_px` is detector-sourced (`docs/DECISIONS.md` D022); keeping the count off this
type makes crossing them a type error rather than a pilot-scale surprise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

import numpy as np
import numpy.typing as npt

LabelSource = Literal["judge", "probe", "human"]
MaskSource = Literal["100doh", "egohos"]

Flow = npt.NDArray[np.float32]
"""Dense optical flow, shape (h, w, 2), in pixels per frame interval."""

Mask = npt.NDArray[np.bool_]


@dataclass(frozen=True, slots=True)
class HandBox:
    """One detected hand, in pixels, origin top-left."""

    x: float
    y: float
    width: float
    height: float
    score: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("a hand box has positive extent")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score is a probability")

    @property
    def area(self) -> float:
        return self.width * self.height


def largest_box(boxes: Sequence[HandBox]) -> HandBox | None:
    """The largest box by area, or `None` when the detector found nothing.

    `docs/RUBRIC.md` takes the residual inside "the largest detected hand box"; when there is
    no box the sample is null, never a fallback region (`docs/HANDOFF.md`).
    """
    if not boxes:
        return None
    return max(boxes, key=lambda b: b.area)


def box_mask(shape: tuple[int, int], boxes: Sequence[HandBox]) -> Mask:
    """A boolean mask true inside any box. Its complement is where ego-motion is estimated."""
    height, width = shape
    if height <= 0 or width <= 0:
        raise ValueError("mask shape must be positive")
    mask: Mask = np.zeros((height, width), dtype=np.bool_)
    for box in boxes:
        x0 = max(0, int(np.floor(box.x)))
        y0 = max(0, int(np.floor(box.y)))
        x1 = min(width, int(np.ceil(box.x + box.width)))
        y1 = min(height, int(np.ceil(box.y + box.height)))
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = True
    return mask


@dataclass(frozen=True, slots=True)
class Detection:
    """What a hand detector returns for one sampled instant. Carries no hand count (D022)."""

    boxes: tuple[HandBox, ...]
    failed_reason: str | None = None

    def __post_init__(self) -> None:
        if self.failed_reason is not None and self.boxes:
            raise ValueError("a failed detection carries no boxes")
        if self.failed_reason is not None and not self.failed_reason:
            raise ValueError("a failure carries a reason, never an empty string")


@dataclass(frozen=True, slots=True)
class LabelProvenance:
    """Which labeller produced a manipulation series. No field has a default."""

    label_source: LabelSource
    label_rev: str
    prompt_variant: str

    def __post_init__(self) -> None:
        if not self.label_rev or not self.prompt_variant:
            raise ValueError("provenance fields are non-empty; nothing here is defaulted")


@dataclass(frozen=True, slots=True)
class FrameLabel:
    """One frame's label. `manipulation` and `hands_visible` are null together (contract)."""

    manipulation: bool | None
    hands_visible: Literal[0, 1, 2] | None
    unreadable_reason: str | None = None

    def __post_init__(self) -> None:
        if (self.manipulation is None) != (self.hands_visible is None):
            raise ValueError("manipulation and hands_visible are null together or not at all")
        if (self.manipulation is None) != (self.unreadable_reason is not None):
            raise ValueError("an unreadable frame carries a reason; a readable one does not")
        if self.manipulation and self.hands_visible == 0:
            raise ValueError("manipulation without a visible hand")


class HandDetector(Protocol):
    """Hand boxes for one sampled instant."""

    @property
    def mask_source(self) -> MaskSource: ...

    def detect(self, clip_id: str, t_s: float) -> Detection: ...


class FlowEstimator(Protocol):
    """Dense flow between a frame pair. `None` is failure, and is never a zero field (A15)."""

    @property
    def flow_method(self) -> str: ...

    def flow(self, first: npt.NDArray[np.uint8], second: npt.NDArray[np.uint8]) -> Flow | None: ...


class ManipulationLabeller(Protocol):
    """The manipulation label for one sampled instant, with its provenance."""

    @property
    def provenance(self) -> LabelProvenance: ...

    def label(self, clip_id: str, t_s: float) -> FrameLabel: ...
