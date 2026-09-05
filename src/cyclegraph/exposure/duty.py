"""Duty cycle for one clip, and the agreement statistic H1 tests it with.

`docs/RUBRIC.md`: *"Duty cycle is the fraction of scored frames whose label is 'actively
manipulating.'"* The denominator is **scored** frames, not sampled ones; unreadable frames
leave the denominator and their count travels with the estimate.

**No smoothing, no interpolation, no gap-filling.** A one-frame dropout stays a dropout. The
rubric's reason is that filling it imports an assumption about exertion continuity that this
project is partly trying to measure, so there is deliberately no window, no median filter and
no forward-fill anywhere in this module. A clip above the 10% unreadable ceiling is
`status: "no_labels"` and contributes nothing, counted rather than dropped.

H1 asks whether duty cycle is a property of the clip or of the labeller. Both of its arms are
a **mean absolute difference over clips measured both ways** -- across label sources within
0.05, and across sampling rates within 0.02 (`docs/PRE-REGISTRATION.md`). The comparison is
paired by `clip_id`: an unpaired mean would let a difference in which clips each source
happened to score masquerade as a difference between the sources.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal

from cyclegraph.models import (
    MIN_CLIP_S,
    UNREADABLE_CEILING,
    ClipRef,
    DutyCycleEstimate,
    LabelSource,
)


H1A_LABEL_SOURCE_MAD: Final[float] = 0.05
"""`docs/PRE-REGISTRATION.md` H1: duty cycle from two label sources on the same clips agrees
to within this mean absolute difference, or H1a is FAILED and Arm B runs (D018)."""

H1B_SAMPLING_RATE_MAD: Final[float] = 0.02
"""H1's second arm: 4 Hz against 8 Hz on a subsample."""


def duty_cycle_estimate(
    clip: ClipRef,
    manipulation: Sequence[bool | None],
    *,
    label_source: LabelSource,
    decode_failed: bool = False,
) -> DutyCycleEstimate:
    """One clip's duty cycle. `status` is decided here, not passed in."""
    n_excluded = sum(1 for m in manipulation if m is None)
    n_scored = len(manipulation) - n_excluded
    n_exerting = sum(1 for m in manipulation if m)
    total = len(manipulation)

    status: Literal["ok", "too_short", "no_labels", "decode_failed"]
    if clip.duration_s < MIN_CLIP_S:
        status = "too_short"
    elif decode_failed:
        status = "decode_failed"
    elif total == 0 or n_scored == 0 or n_excluded / total > UNREADABLE_CEILING:
        status = "no_labels"
    else:
        status = "ok"

    return DutyCycleEstimate(
        clip_id=clip.clip_id,
        corpus_rev=clip.corpus_rev,
        duty_cycle=(n_exerting / n_scored) if status == "ok" else None,
        n_frames_scored=n_scored,
        n_frames_exerting=n_exerting,
        n_frames_excluded=n_excluded,
        label_source=label_source,
        status=status,
    )


@dataclass(frozen=True, slots=True)
class Agreement:
    """One arm of H1. `mean_absolute_difference` is the quantity the threshold is on."""

    n_pairs: int
    mean_absolute_difference: float
    max_absolute_difference: float
    threshold: float

    @property
    def holds(self) -> bool:
        return self.mean_absolute_difference <= self.threshold


def paired_duty_cycles(
    left: Sequence[DutyCycleEstimate], right: Sequence[DutyCycleEstimate]
) -> list[tuple[str, float, float]]:
    """`(clip_id, left, right)` for clips both sides scored `ok`.

    Pairing is the point. A clip one side excluded and the other did not carries no
    information about whether the two agree, and averaging over the union would let a
    difference in coverage read as a difference in duty cycle.
    """
    by_id: Mapping[str, DutyCycleEstimate] = {e.clip_id: e for e in right if e.status == "ok"}
    out: list[tuple[str, float, float]] = []
    for estimate in left:
        other = by_id.get(estimate.clip_id)
        if estimate.status != "ok" or other is None:
            continue
        assert estimate.duty_cycle is not None and other.duty_cycle is not None
        out.append((estimate.clip_id, estimate.duty_cycle, other.duty_cycle))
    return out


def agreement(
    left: Sequence[DutyCycleEstimate], right: Sequence[DutyCycleEstimate], *, threshold: float
) -> Agreement:
    """Mean absolute difference over paired clips, against a pre-registered bound."""
    pairs = paired_duty_cycles(left, right)
    if not pairs:
        raise ValueError(
            "no clip was scored 'ok' by both sides; an agreement statistic over nothing is "
            "not a passing result"
        )
    diffs = [abs(a - b) for _, a, b in pairs]
    return Agreement(
        n_pairs=len(pairs),
        mean_absolute_difference=sum(diffs) / len(diffs),
        max_absolute_difference=max(diffs),
        threshold=threshold,
    )
