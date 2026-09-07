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


def box_is_contradicted(label: FrameLabel) -> bool:
    """Whether the labeller contradicts a detector box on this frame. D022.

    One definition, because two consumers need it: `resolve_conflicts` nulls the box width on
    the `FrameSignal`, and the speed path must not measure a residual inside a box the labeller
    says holds no hand. The speed path was reading the *unresolved* boxes, so a box dropped from
    one record was still counted in the other's `n_with_box` -- inflating H2c's coverage with
    boxes the contract had already discarded, and taking an RMS inside them
    (`docs/DECISIONS.md` D056).
    """
    return label.hands_visible is None or label.hands_visible == 0


def contradiction_reason(label: FrameLabel) -> str | None:
    """Why a box on this frame is dropped, or None if it is kept.

    Two causes, and `docs/BENCHMARK.md` gives them separate rows so a reader need not guess:
    the labeller saw no hand, or the labeller could not read the frame at all. `resolve_conflicts`
    counts them apart and the speed path's reason string collapsed them, attributing a statement
    to the labeller it never made on 8,750 of the pilot's samples (`docs/DECISIONS.md` D065).
    """
    if label.hands_visible is None:
        return ("the detector's box was dropped: the labeller could not read this frame, so "
                "there is no hand count to corroborate it (D022)")
    if label.hands_visible == 0:
        return ("the detector's box was dropped: the labeller reports no visible hand on this "
                "frame (D022)")
    return None


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
        elif box_is_contradicted(sample.label):
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

    if hand_mask_source == "none" and any(w is not None for w in widths):
        raise ValueError(
            "hand_mask_source 'none' with detector box widths present. Nulling them here "
            "would void a whole series of real detector measurements with no count and no "
            "reason, and would understate H2c's coverage with no trace; this module repairs "
            "nothing silently (docs/DECISIONS.md D022)"
        )

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
