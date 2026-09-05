"""Tests for `src/cyclegraph/signal/frames.py`.

The golden case rebuilds `tests.fixtures.FRAME_SIGNAL` field for field from a hand-written
sample list. That ties the builder to the frozen contract fixture without editing it: if the
contract changes, this fails, and if the builder drifts, this fails.
"""

from __future__ import annotations

import pytest

from cyclegraph.models import ClipRef, FrameSignal
from cyclegraph.signal.frames import FrameSample, build_frame_signal, resolve_conflicts
from cyclegraph.signal.ports import FrameLabel, LabelProvenance
from tests import fixtures

PROVENANCE = LabelProvenance(label_source="judge", label_rev="qwen3vl@abc", prompt_variant="P0b")


def _clip(**over: object) -> ClipRef:
    return ClipRef.model_validate({**fixtures.CLIP_REF, **over})


def _label(manipulation: bool | None, hands: int | None) -> FrameLabel:
    return FrameLabel(manipulation=manipulation, hands_visible=hands,  # type: ignore[arg-type]
                      unreadable_reason=None if manipulation is not None else "unreadable")


def test_it_rebuilds_the_contract_fixture_exactly() -> None:
    """Golden case against the frozen fixture."""
    expected = FrameSignal.model_validate(fixtures.FRAME_SIGNAL)
    samples = [
        FrameSample(t_s=i * 0.25, label=_label(m, h), hand_box_width_px=w)
        for i, (m, h, w) in enumerate(zip(
            fixtures.FRAME_SIGNAL["manipulation"],
            fixtures.FRAME_SIGNAL["hands_visible"],
            fixtures.FRAME_SIGNAL["hand_box_width_px"],
            strict=True,
        ))
    ]
    built = build_frame_signal(
        _clip(clip_id=expected.clip_id, corpus_rev=expected.corpus_rev),
        samples, provenance=PROVENANCE, hand_mask_source="100doh",
        flow_method="farneback", fps_sampled=4.0,
    )
    assert built == expected


def _series(n: int, unreadable: int) -> list[FrameSample]:
    return [
        FrameSample(t_s=i * 0.25,
                    label=_label(None, None) if i < unreadable else _label(True, 2),
                    hand_box_width_px=None if i < unreadable else 209.0)
        for i in range(n)
    ]


def test_the_unreadable_ceiling_is_where_the_rubric_puts_it() -> None:
    ok = build_frame_signal(_clip(), _series(100, 10), provenance=PROVENANCE,
                            hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)
    assert ok.status == "ok" and ok.n_unreadable == 10
    over = build_frame_signal(_clip(), _series(100, 11), provenance=PROVENANCE,
                              hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)
    assert over.status == "no_labels"


def test_a_clip_under_the_floor_is_too_short_whatever_its_labels_say() -> None:
    signal = build_frame_signal(_clip(duration_s=59.9), _series(100, 0), provenance=PROVENANCE,
                                hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)
    assert signal.status == "too_short"


def test_a_clip_whose_every_sample_failed_to_decode_is_decode_failed() -> None:
    samples = [FrameSample(t_s=i * 0.25, label=_label(None, None), decode_reason="no frame")
               for i in range(20)]
    signal = build_frame_signal(_clip(), samples, provenance=PROVENANCE,
                                hand_mask_source="none", flow_method="f", fps_sampled=4.0)
    assert signal.status == "decode_failed" and signal.n_unreadable == 20


def test_a_box_the_labeller_contradicts_raises_rather_than_being_repaired() -> None:
    """The builder never fixes anything silently; repair is an explicit call."""
    samples = [FrameSample(t_s=0.0, label=_label(False, 0), hand_box_width_px=200.0)]
    with pytest.raises(ValueError, match="resolve_conflicts"):
        build_frame_signal(_clip(), samples, provenance=PROVENANCE,
                           hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)


def test_resolve_conflicts_drops_the_box_and_counts_it_by_cause() -> None:
    """D022. The count is the part of a coverage miss owed to the labeller, and H2c is
    otherwise read as a statement about the detector alone."""
    samples = [
        FrameSample(t_s=0.00, label=_label(True, 2), hand_box_width_px=209.0),
        FrameSample(t_s=0.25, label=_label(False, 0), hand_box_width_px=200.0),
        FrameSample(t_s=0.50, label=_label(None, None), hand_box_width_px=198.0),
        FrameSample(t_s=0.75, label=_label(True, 1), hand_box_width_px=None),
    ]
    resolved, conflicts = resolve_conflicts(samples)
    assert conflicts.box_without_visible_hand == 1
    assert conflicts.box_on_unreadable_frame == 1
    assert conflicts.total == 2
    assert [s.hand_box_width_px for s in resolved] == [209.0, None, None, None]
    built = build_frame_signal(_clip(), resolved, provenance=PROVENANCE,
                               hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)
    assert built.n_frames == 4


def test_a_mask_source_of_none_carries_no_box_widths() -> None:
    signal = build_frame_signal(_clip(), _series(20, 0), provenance=PROVENANCE,
                                hand_mask_source="none", flow_method="f", fps_sampled=4.0)
    assert all(w is None for w in signal.hand_box_width_px)


def test_the_label_source_reaches_the_record_from_provenance_not_a_default() -> None:
    probe = LabelProvenance(label_source="probe", label_rev="r1", prompt_variant="P0a")
    signal = build_frame_signal(_clip(), _series(20, 0), provenance=probe,
                                hand_mask_source="100doh", flow_method="f", fps_sampled=4.0)
    assert signal.label_source == "probe" and signal.label_rev == "r1"
