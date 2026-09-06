"""RMS residual hand speed for one clip: `docs/RUBRIC.md` "Hand speed", as code.

The rule, unchanged from the rubric: at each sampled instant take dense flow over the pair,
take the **median flow over the complement of the hand mask** as the camera's ego-motion,
subtract it, take the **RMS residual magnitude inside the largest detected hand box**, and
scale pixels to mm/s by `hand_breadth_mm / median_box_width_px`.

Three rules this module implements that the rubric states in prose and leaves unquantified
(`docs/DECISIONS.md` D023):

*An exactly-zero residual is a flow null, not a speed of zero.* Without it a clip with boxes
on every frame and a dead flow field has no legal record at all: `HandSpeedEstimate` bars a
non-positive speed under `ok` and bars `flow_failed` unless the null rate clears its ceiling.
The test is `== 0.0` exactly and not a threshold, because nulling small residuals would
discard real slow motion and bias the corpus upward. It follows that the null rate is a
**lower bound** on flow failure: blur and low light decay flow toward small non-zero values
that pass through as speed.

*Status precedence*, when more than one condition holds:
`no_detector` > `too_short` > `low_coverage` > `flow_failed` > `ok`.

*A no-box sample is not a flow null.* `coverage` is `n_with_box / n_samples` and
`flow_null_rate` is `n_flow_null / n_with_box`; the denominators differ, and at the 60%
coverage floor they differ by a factor of 1.67 in both directions.

Nothing here runs a flow estimator. It consumes fields, which is what lets the A14 floor be
measured from exact synthetic geometry with no estimator error in the loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Sequence

import numpy as np

from cyclegraph.models import COVERAGE_FLOOR, FLOW_NULL_CEILING, ClipRef, HandSpeedEstimate
from cyclegraph.signal.ports import Flow, HandBox, Mask, MaskSource, box_mask, largest_box

HAND_BREADTH_MM: Final[float] = 85.0
"""`docs/RUBRIC.md`: the mean of Akkas 2015's male and female population means, because sex
is not known per clip. The sensitivity table re-runs the two below."""

HAND_BREADTH_MM_SENSITIVITY: Final[tuple[float, float]] = (79.5, 90.4)

EGO_MOTION: Final[str] = "mask_complement_median"

ZERO_RESIDUAL_REASON: Final[str] = (
    "zero residual inside the box: a dead flow field, not a speed (docs/RED-TEAM.md A15, D023)"
)


def ego_motion(flow: Flow, hand_mask: Mask) -> tuple[float, float]:
    """The camera's motion, as the median flow over everything that is not a hand.

    Non-finite samples are excluded rather than treated as zero. On a fisheye the frame's
    corners lie outside the image circle and carry no flow at all; counting them as zero
    would drag this estimate toward zero and shrink every residual computed against it.
    """
    if flow.shape[:2] != hand_mask.shape:
        raise ValueError("flow and mask must cover the same frame")
    background = flow[~hand_mask]
    background = background[np.isfinite(background).all(axis=-1)]
    if background.size == 0:
        raise ValueError(
            "no background to estimate ego-motion from; a full-frame hand mask is a failure, "
            "not a zero ego-motion"
        )
    return float(np.median(background[:, 0])), float(np.median(background[:, 1]))


def residual_rms_px(flow: Flow, box: HandBox, ego: tuple[float, float]) -> float:
    """RMS residual flow magnitude inside one box, after subtracting the ego-motion vector."""
    mask = box_mask(flow.shape[:2], [box])
    inside = flow[mask]
    inside = inside[np.isfinite(inside).all(axis=-1)]
    if inside.size == 0:
        raise ValueError("the hand box covers no readable pixel")
    residual = inside - np.asarray(ego, dtype=np.float32)
    return float(np.sqrt((residual**2).sum(axis=-1).mean()))


@dataclass(frozen=True, slots=True)
class SpeedSample:
    """One 4 Hz instant. `px_per_s` is null with a reason, or positive; never zero."""

    t_s: float
    px_per_s: float | None
    box_width_px: float | None
    null_reason: str | None

    def __post_init__(self) -> None:
        if (self.px_per_s is None) != (self.null_reason is not None):
            raise ValueError("a null sample carries a reason and a measured one does not")
        if self.px_per_s is not None and self.px_per_s <= 0.0:
            raise ValueError("a non-positive speed is a failure, not a measurement")

    @property
    def has_box(self) -> bool:
        return self.box_width_px is not None

    @property
    def is_flow_null(self) -> bool:
        """A no-box sample is not a flow null: the denominators differ (D023)."""
        return self.has_box and self.px_per_s is None


def speed_sample(
    flow: Flow | None,
    boxes: Sequence[HandBox],
    *,
    t_s: float,
    dt_s: float,
    flow_reason: str | None = None,
) -> SpeedSample:
    """One sample from one frame pair. Every absence is a reason, never a zero."""
    if dt_s <= 0:
        raise ValueError("the pair interval is positive")
    box = largest_box(boxes)
    if box is None:
        return SpeedSample(t_s=t_s, px_per_s=None, box_width_px=None,
                           null_reason="no detected hand box; never a region prior")
    if flow is None:
        return SpeedSample(t_s=t_s, px_per_s=None, box_width_px=box.width,
                           null_reason=flow_reason or "the flow estimator returned no field")
    try:
        ego = ego_motion(flow, box_mask(flow.shape[:2], [box]))
        residual = residual_rms_px(flow, box, ego)
    except ValueError as exc:
        # `ego_motion` refuses a mask with no complement, and `residual_rms_px` refuses a box
        # covering no readable pixel. Both are right to refuse -- a full-frame hand mask is a
        # segmentation failure and not a measurement of zero camera motion. But refusing by
        # raising killed a worker mid-shard and cost every clip after it in that shard, and
        # `docs/RUBRIC.md`'s own rule for this is a null with a reason, not a stop
        # (`docs/DECISIONS.md` D060).
        return SpeedSample(t_s=t_s, px_per_s=None, box_width_px=box.width,
                           null_reason=f"ego-motion unavailable: {exc}"[:120])
    if residual == 0.0:
        return SpeedSample(t_s=t_s, px_per_s=None, box_width_px=box.width,
                           null_reason=ZERO_RESIDUAL_REASON)
    return SpeedSample(t_s=t_s, px_per_s=residual / dt_s, box_width_px=box.width,
                       null_reason=None)


def hand_speed_estimate(
    clip: ClipRef,
    samples: Sequence[SpeedSample],
    *,
    mask_source: MaskSource | None,
    flow_method: str,
    hand_breadth_mm: float = HAND_BREADTH_MM,
    too_short: bool = False,
) -> HandSpeedEstimate:
    """Assemble the record. Status follows D023's precedence, not the order of the checks."""
    n_samples = len(samples)
    if n_samples == 0:
        raise ValueError("a clip plans at least one sample; n_samples is positive on the record")
    with_box = [s for s in samples if s.has_box]
    n_with_box = len(with_box)
    n_flow_null = sum(1 for s in samples if s.is_flow_null)
    coverage = n_with_box / n_samples
    # Null, not zero, when nothing was boxed: the rate is nulls over *boxed* samples and that
    # ratio has no value with an empty denominator. Zero there reads as "flow never failed" on
    # a clip where flow was never attempted (`docs/DECISIONS.md` D054).
    flow_null_rate = (n_flow_null / n_with_box) if n_with_box else None
    widths = [s.box_width_px for s in with_box if s.box_width_px is not None]
    median_box_width_px = float(np.median(widths)) if widths else None

    status: Literal["ok", "low_coverage", "no_detector", "flow_failed", "too_short"]
    reason: str | None
    if mask_source is None:
        status, reason = "no_detector", "no detector ran on this clip"
    elif too_short:
        status, reason = "too_short", "clip shorter than the pre-registered 60 s floor"
    elif coverage < COVERAGE_FLOOR:
        status = "low_coverage"
        reason = f"detector coverage {coverage:.2f} below the {COVERAGE_FLOOR:.2f} floor"
    elif flow_null_rate is not None and flow_null_rate > FLOW_NULL_CEILING:
        status = "flow_failed"
        reason = f"flow-null rate {flow_null_rate:.2f} above the {FLOW_NULL_CEILING:.2f} ceiling"
    else:
        status, reason = "ok", None

    rms_speed_mm_s: float | None = None
    if status == "ok":
        valid = [s.px_per_s for s in with_box if s.px_per_s is not None]
        assert median_box_width_px is not None
        rms_px_s = float(np.sqrt(np.mean(np.square(valid))))
        rms_speed_mm_s = rms_px_s * hand_breadth_mm / median_box_width_px
        if rms_speed_mm_s <= 0.0:
            status, reason, rms_speed_mm_s = "flow_failed", ZERO_RESIDUAL_REASON, None

    return HandSpeedEstimate(
        clip_id=clip.clip_id,
        corpus_rev=clip.corpus_rev,
        rms_speed_mm_s=rms_speed_mm_s,
        n_samples=n_samples,
        n_with_box=n_with_box,
        n_flow_null=n_flow_null,
        coverage=coverage,
        flow_null_rate=flow_null_rate,
        hand_breadth_mm=hand_breadth_mm,
        median_box_width_px=median_box_width_px,
        mask_source=mask_source,
        flow_method=flow_method,
        ego_motion="mask_complement_median",
        status=status,
        status_reason=reason,
    )
