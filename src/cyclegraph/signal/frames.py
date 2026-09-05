"""One clip's per-frame series, assembled into a `FrameSignal`.

The record's own validator enforces the contract; this module's job is to decide `status` and
to count what the record has no field for.

**`hands_visible` is the labeller's, `hand_box_width_px` is the detector's**
(`docs/DECISIONS.md` D022). They are never crossed, and where they disagree the box is
dropped and counted rather than reconciled: the contract rejects a box on a frame with no
visible hand, and H2c permits the detector to miss 40% of frames, so a pipeline that took the
hand count from the detector would make ~40% of manipulating frames unconstructible and would
only discover it after the detector run.

The drop count has nowhere to live on the record, so `resolve_conflicts` returns it and the
caller writes it beside the record. It is a reported quantity, not a log line: it is the part
of a coverage miss attributable to the labeller rather than the detector, and H2c is otherwise
read as a statement about the detector alone.

`build_frame_signal` **raises** on an internally inconsistent sample rather than repairing it.
Repair is `resolve_conflicts`' job and is called explicitly, so nothing is silently fixed on
the way into a record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from cyclegraph.models import MIN_CLIP_S, UNREADABLE_CEILING, ClipRef, FrameSignal
from cyclegraph.signal.ports import FrameLabel, LabelProvenance

MaskSourceField = Literal["100doh", "egohos", "none"]


@dataclass(frozen=True, slots=True)
class FrameSample:
    """One sampled instant, before it becomes a column of a series."""

    t_s: float
    label: FrameLabel
    hand_box_width_px: float | None = None
    decode_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SignalConflicts:
    """What had to be dropped to make the series constructible, and why."""

    box_without_visible_hand: int
    box_on_unreadable_frame: int

    @property
    def total(self) -> int:
        return self.box_without_visible_hand + self.box_on_unreadable_frame


def resolve_conflicts(samples: Sequence[FrameSample]) -> tuple[list[FrameSample], SignalConflicts]:
    """Drop detector boxes the labeller contradicts, and count them. D022."""
    out: list[FrameSample] = []
    no_hand = 0
    unreadable = 0
    for sample in samples:
        if sample.hand_box_width_px is None:
            out.append(sample)
            continue
        if sample.label.hands_visible is None:
            unreadable += 1
            out.append(FrameSample(sample.t_s, sample.label, None, sample.decode_reason))
        elif sample.label.hands_visible == 0:
            no_hand += 1
            out.append(FrameSample(sample.t_s, sample.label, None, sample.decode_reason))
        else:
            out.append(sample)
    return out, SignalConflicts(box_without_visible_hand=no_hand,
                                box_on_unreadable_frame=unreadable)


def build_frame_signal(
    clip: ClipRef,
    samples: Sequence[FrameSample],
    *,
    provenance: LabelProvenance,
    hand_mask_source: MaskSourceField,
    flow_method: str,
    fps_sampled: float,
) -> FrameSignal:
    """Assemble the record, choosing `status` from the rubric rather than taking it."""
    manipulation: list[bool | None] = []
    hands_visible: list[Literal[0, 1, 2] | None] = []
    widths: list[float | None] = []
    for sample in samples:
        manipulation.append(sample.label.manipulation)
        hands_visible.append(sample.label.hands_visible)
        widths.append(sample.hand_box_width_px)
        if sample.hand_box_width_px is not None and (
            sample.label.hands_visible is None or sample.label.hands_visible == 0
        ):
            raise ValueError(
                "a box on a frame the labeller says has no visible hand; call "
                "resolve_conflicts first so the drop is counted rather than hidden (D022)"
            )

    n_frames = len(samples)
    unreadable = sum(1 for m in manipulation if m is None)

    status: Literal["ok", "too_short", "no_labels", "decode_failed"]
    if clip.duration_s < MIN_CLIP_S:
        status = "too_short"
    elif n_frames and all(s.decode_reason is not None for s in samples):
        status = "decode_failed"
    elif n_frames == 0 or unreadable / n_frames > UNREADABLE_CEILING:
        status = "no_labels"
    else:
        status = "ok"

    if hand_mask_source == "none":
        widths = [None] * n_frames

    return FrameSignal(
        clip_id=clip.clip_id,
        corpus_rev=clip.corpus_rev,
        fps_sampled=fps_sampled,
        n_frames=n_frames,
        manipulation=manipulation,
        hands_visible=hands_visible,
        hand_box_width_px=widths,
        hand_mask_source=hand_mask_source,
        flow_method=flow_method,
        label_source=provenance.label_source,
        label_rev=provenance.label_rev,
        prompt_variant=provenance.prompt_variant,
        status=status,
        n_unreadable=unreadable,
    )
