"""Behavioural tests for `src/cyclegraph/signal/speed.py`.

Carries `docs/WAVES.md`'s speed-path golden row. The residual arithmetic is checked against a
field whose answer is exact by construction, and the A14 cases are checked against the
synthetic geometry rather than against a recorded number.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cyclegraph.models import ClipRef, HandSpeedEstimate
from cyclegraph.signal.ports import HandBox, box_mask
from cyclegraph.signal.speed import (
    HAND_BREADTH_MM,
    ZERO_RESIDUAL_REASON,
    SpeedSample,
    ego_motion,
    hand_speed_estimate,
    residual_rms_px,
    speed_sample,
)
from cyclegraph.signal.synthetic import (
    CORPUS_CAMERA,
    NARROW_CAMERA,
    Scene,
    analytic_flow,
    hand_box_for,
)
from tests import fixtures

# A long lens makes rotational flow nearly uniform, so the rubric's scalar ego-motion estimate
# cancels it and the residual is a rounding artefact. One percent of the raw flow is the
# geometric bound from sec^2 over a 26-degree field, not a tuned number.
ROTATION_NULL_FRACTION = 0.01

# Under the corpus lens the same rotation leaves an order of magnitude more. The measured
# fraction is ~13%; 5% is the floor a near-uniform field could not clear.
CORPUS_ROTATION_FRACTION = 0.05

DT_S = 0.25  # the 4 Hz pair interval


def _clip() -> ClipRef:
    return ClipRef.model_validate(fixtures.CLIP_REF)


def _uniform_flow(shape: tuple[int, int], ego: tuple[float, float],
                  box: HandBox, inside: tuple[float, float]) -> np.ndarray:
    flow = np.zeros((*shape, 2), dtype=np.float32)
    flow[..., 0], flow[..., 1] = ego
    mask = box_mask(shape, [box])
    flow[mask] = np.asarray([ego[0] + inside[0], ego[1] + inside[1]], dtype=np.float32)
    return flow


def test_ego_motion_is_the_background_median_and_ignores_unreadable_pixels() -> None:
    flow = np.zeros((10, 10, 2), dtype=np.float32)
    flow[..., 0] = 3.0
    flow[..., 1] = -1.0
    flow[0, :] = np.nan  # a row outside the image circle
    mask = np.zeros((10, 10), dtype=np.bool_)
    mask[5:7, 5:7] = True
    assert ego_motion(flow, mask) == (3.0, -1.0)


def test_ego_motion_refuses_a_full_frame_mask() -> None:
    """No background is a failure, not an ego-motion of zero."""
    flow = np.zeros((4, 4, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="no background"):
        ego_motion(flow, np.ones((4, 4), dtype=np.bool_))


def test_residual_is_hand_computable_on_a_constructed_field() -> None:
    """Ego-motion (7, -2) everywhere, hand moving (3, 4) relative to it. The residual is
    sqrt(3^2 + 4^2) = 5 exactly, whatever the ego-motion happens to be."""
    box = HandBox(x=4, y=4, width=4, height=4, score=1.0)
    flow = _uniform_flow((20, 20), ego=(7.0, -2.0), box=box, inside=(3.0, 4.0))
    ego = ego_motion(flow, box_mask((20, 20), [box]))
    assert ego == (7.0, -2.0)
    assert residual_rms_px(flow, box, ego) == pytest.approx(5.0, abs=1e-6)


def test_a_zero_residual_is_a_flow_null_not_a_speed_of_zero() -> None:
    """D023. Without this the clip below has no legal record at all."""
    box = HandBox(x=4, y=4, width=4, height=4, score=1.0)
    flow = _uniform_flow((20, 20), ego=(2.0, 2.0), box=box, inside=(0.0, 0.0))
    sample = speed_sample(flow, [box], t_s=0.0, dt_s=DT_S)
    assert sample.px_per_s is None
    assert sample.null_reason == ZERO_RESIDUAL_REASON
    assert sample.is_flow_null


def test_a_missing_box_is_not_a_flow_null() -> None:
    """The denominators differ: coverage is over samples, the null rate over boxed samples."""
    sample = speed_sample(None, [], t_s=0.0, dt_s=DT_S)
    assert sample.px_per_s is None
    assert not sample.has_box
    assert not sample.is_flow_null


def test_a_failed_flow_with_a_box_is_a_flow_null_with_its_reason() -> None:
    box = HandBox(x=1, y=1, width=2, height=2, score=1.0)
    sample = speed_sample(None, [box], t_s=0.0, dt_s=DT_S, flow_reason="blur")
    assert sample.is_flow_null and sample.null_reason == "blur"


def test_a_sample_can_never_carry_a_non_positive_speed() -> None:
    with pytest.raises(ValueError):
        SpeedSample(t_s=0.0, px_per_s=0.0, box_width_px=10.0, null_reason=None)
    with pytest.raises(ValueError):
        SpeedSample(t_s=0.0, px_per_s=5.0, box_width_px=10.0, null_reason="both")


def _estimate(n: int, boxed: int, nulls: int, **kw: object) -> HandSpeedEstimate:
    samples: list[SpeedSample] = []
    for i in range(n):
        if i >= boxed:
            samples.append(SpeedSample(t_s=i * DT_S, px_per_s=None, box_width_px=None,
                                       null_reason="no detected hand box; never a region prior"))
        elif i < nulls:
            samples.append(SpeedSample(t_s=i * DT_S, px_per_s=None, box_width_px=209.0,
                                       null_reason="blur"))
        else:
            samples.append(SpeedSample(t_s=i * DT_S, px_per_s=1500.0, box_width_px=209.0,
                                       null_reason=None))
    return hand_speed_estimate(_clip(), samples, mask_source="100doh",
                               flow_method="farneback", **kw)  # type: ignore[arg-type]


def test_the_rates_use_their_own_denominators() -> None:
    est = _estimate(1000, boxed=700, nulls=70)
    assert est.coverage == pytest.approx(0.70)
    assert est.flow_null_rate == pytest.approx(70 / 700)
    assert est.status == "ok"


def test_the_coverage_boundary_is_where_the_contract_puts_it() -> None:
    assert _estimate(1000, boxed=599, nulls=0).status == "low_coverage"
    assert _estimate(1000, boxed=600, nulls=0).status == "ok"


def test_the_flow_null_boundary_is_where_the_contract_puts_it() -> None:
    assert _estimate(1000, boxed=1000, nulls=100).status == "ok"
    assert _estimate(1000, boxed=1000, nulls=101).status == "flow_failed"


def test_status_precedence_is_fixed_when_two_conditions_hold() -> None:
    """D023: no_detector > too_short > low_coverage > flow_failed > ok."""
    both = _estimate(1000, boxed=500, nulls=400)  # low coverage AND a high null rate
    assert both.status == "low_coverage"
    est = hand_speed_estimate(_clip(), [SpeedSample(0.0, None, None, "no box")],
                              mask_source=None, flow_method="farneback")
    assert est.status == "no_detector" and est.mask_source is None


def test_a_too_short_clip_still_carries_a_positive_sample_count() -> None:
    est = hand_speed_estimate(
        _clip(), [SpeedSample(i * DT_S, None, None, "never decoded") for i in range(120)],
        mask_source="100doh", flow_method="farneback", too_short=True)
    assert est.status == "too_short" and est.n_samples == 120 and est.n_with_box == 0


def test_an_entirely_dead_flow_field_produces_a_constructible_record() -> None:
    """The hole D023 closes: boxes everywhere, flow dead, and the record must still exist."""
    est = _estimate(100, boxed=100, nulls=100)
    assert est.status == "flow_failed"
    assert est.rms_speed_mm_s is None
    assert est.flow_null_rate == 1.0


def test_it_reproduces_the_contract_example_counts() -> None:
    """`CONTRACTS.md`'s own HandSpeedEstimate example, rebuilt from samples."""
    est = _estimate(749, boxed=688, nulls=9)
    assert (est.n_samples, est.n_with_box, est.n_flow_null) == (749, 688, 9)
    assert est.coverage == pytest.approx(fixtures.HAND_SPEED["coverage"])
    assert est.flow_null_rate == pytest.approx(fixtures.HAND_SPEED["flow_null_rate"])
    assert est.status == "ok"


def _rotation_residual_fraction(camera: object, deg_per_s: float) -> tuple[float, float]:
    scene = Scene(camera=camera, hand_box=hand_box_for(camera))  # type: ignore[arg-type]
    flow = analytic_flow(scene, rotation_rad=math.radians(deg_per_s * DT_S))
    box = scene.hand_box
    ego = ego_motion(flow, box_mask(flow.shape[:2], [box]))
    residual = residual_rms_px(flow, box, ego)
    inside = flow[box_mask(flow.shape[:2], [box])]
    raw = float(np.sqrt(np.nanmean((inside**2).sum(axis=-1))))
    return residual, raw


def test_rotation_only_with_a_static_hand_yields_no_residual_under_a_long_lens() -> None:
    """`docs/WAVES.md`'s speed-path golden row, in the geometry where it is a statement about
    the estimator's arithmetic."""
    residual, raw = _rotation_residual_fraction(NARROW_CAMERA, 30.0)
    assert residual / raw < ROTATION_NULL_FRACTION


def test_rotation_only_leaves_real_residual_under_the_corpus_lens() -> None:
    """The same sequence, the same static hand, the corpus's own lens: the scalar ego-motion
    estimate no longer cancels, and what survives is A14 (`docs/DECISIONS.md` D021)."""
    residual, raw = _rotation_residual_fraction(CORPUS_CAMERA, 30.0)
    assert residual / raw > CORPUS_ROTATION_FRACTION


def test_the_hand_breadth_scale_is_the_rubric_value() -> None:
    assert HAND_BREADTH_MM == 85.0
