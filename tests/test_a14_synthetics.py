"""Behavioural tests for `src/cyclegraph/signal/synthetic.py`.

These are stricter than a typical unit's, deliberately. The A14 floor is measured from this
generator, so a generator that quietly lost the fisheye or the depth split would make the
speed path look clean and would retire an attack it could not have detected
(`docs/DECISIONS.md` D021). Every test below fails on such a generator.

The oracle is the geometry itself: `project` and `unproject` must invert each other, rotation
must be depth-independent because that is what rotation *is*, and translation must produce
parallax in the ratio the two plane distances set. None of these is a number tuned until it
passed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cyclegraph.signal.ports import box_mask
from cyclegraph.signal.synthetic import (
    CORPUS_CAMERA,
    NARROW_CAMERA,
    Scene,
    analytic_flow,
    hand_box_for,
    image_circle_radius_px,
    max_theta,
    project,
    unproject,
    valid_mask,
)

# `project(unproject(p)) == p` is exact arithmetic; the only error is the 20,001-point table
# `unproject` interpolates on. Linear interpolation of a smooth function has error O(h^2), not
# O(h), so the grid spacing alone does not give the bound -- the round trip measures 1.87e-06 px
# and this is set ~500x above that, loose enough to survive a platform's float differences and
# still ~1000x tighter than any error that would matter to a residual in pixels.
ROUNDTRIP_TOLERANCE_PX = 1e-3

# Rotational flow under a long lens varies as sec^2(theta) across the field. NARROW_CAMERA's
# half-angle is ~13 deg, where sec^2 - 1 = 5.3%, so geometry bounds the coefficient of
# variation ABOVE by a few percent and says nothing tighter. The measured value is 0.0017.
# This is therefore a separation bound and not a derivation: it sits ~6x above the observation
# and ~100x below the corpus lens's, which is the gap it exists to assert.
NARROW_UNIFORMITY_CV = 0.01

# The corpus lens reaches 67.9 deg and its rotational flow at the edge of the image circle is
# less than half the value at the centre. Measured coefficient of variation: 0.1909, against
# 0.0017 for the long lens. This threshold is a one-sided separation bound at roughly half the
# observation -- not a derived quantity, and stated as such -- chosen so that it survives a 2x
# shift in either direction while still lying ~59x above the long lens's value. A generator
# that lost the fisheye produces a near-uniform field and fails it by two orders of magnitude.
CORPUS_NONUNIFORMITY_CV = 0.10


def _corpus_scene(**kw: float) -> Scene:
    return Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA), **kw)


def test_projection_inverts_inside_the_image_circle() -> None:
    cam = CORPUS_CAMERA
    ys, xs = np.mgrid[0 : cam.height : 53, 0 : cam.width : 53]
    pix = np.stack([xs.astype(np.float64), ys.astype(np.float64)], axis=-1)
    dirs = unproject(cam, pix)
    back = project(cam, dirs)
    finite = np.isfinite(dirs).all(axis=-1)
    assert finite.sum() > 500
    assert np.abs(back - pix)[finite].max() < ROUNDTRIP_TOLERANCE_PX


def test_the_corners_of_the_frame_are_outside_the_lens_and_say_so() -> None:
    """Kannala-Brandt with these coefficients turns over at ~1.18 rad, so the image circle
    does not reach the corners of a 16:9 sensor. Those pixels carry no ray and must be NaN,
    not a plausible-looking one -- they sit in the region ego-motion is estimated from."""
    cam = CORPUS_CAMERA
    assert 1.0 < max_theta(cam) < math.pi / 2
    assert image_circle_radius_px(cam) < math.hypot(cam.width - cam.cx, cam.height - cam.cy)
    vm = valid_mask(cam)
    assert not vm[0, 0] and not vm[-1, -1]
    assert vm[int(cam.cy), int(cam.cx)]
    assert 0.90 < vm.mean() < 0.99
    flow = analytic_flow(_corpus_scene(), rotation_rad=0.05)
    assert np.isnan(flow[0, 0]).all()
    assert np.isfinite(flow[int(cam.cy), int(cam.cx)]).all()


def test_rotation_is_depth_independent_because_that_is_what_rotation_is() -> None:
    """The physics the whole A14 argument rests on. If this fails, the generator is wrong and
    every residual measured from it is meaningless."""
    near = Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA),
                 hand_distance_m=0.45, background_distance_m=0.45)
    far = Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA),
                hand_distance_m=9.0, background_distance_m=9.0)
    a = analytic_flow(near, rotation_rad=math.radians(7.5))
    b = analytic_flow(far, rotation_rad=math.radians(7.5))
    assert np.nanmax(np.abs(a - b)) < 1e-6


def _uniformity_cv(camera: object, rotation_deg: float) -> float:
    scene = Scene(camera=camera, hand_box=hand_box_for(camera),  # type: ignore[arg-type]
                  hand_distance_m=5.0, background_distance_m=5.0)
    flow = analytic_flow(scene, rotation_rad=math.radians(rotation_deg))
    mag = np.linalg.norm(flow, axis=-1)
    valid = np.isfinite(mag)
    return float(mag[valid].std() / mag[valid].mean())


def test_a_long_lens_makes_rotational_flow_nearly_uniform() -> None:
    """The control. A scalar ego-motion estimate is a good model here, which is why the
    rubric's rule works at all -- and why testing A14 only in this geometry would pass for
    the wrong reason."""
    assert _uniformity_cv(NARROW_CAMERA, 7.5) < NARROW_UNIFORMITY_CV


def test_the_corpus_lens_makes_rotational_flow_strongly_non_uniform() -> None:
    """The attack. A scalar cannot cancel a field that varies by this much across the frame,
    so a rotation-only sequence leaves residual where the hands sit. A generator that dropped
    the fisheye would produce a near-uniform field and fail here."""
    assert _uniformity_cv(CORPUS_CAMERA, 7.5) > CORPUS_NONUNIFORMITY_CV


def test_translation_flow_scales_as_one_over_depth() -> None:
    """Parallax, isolated. Comparing the box against the background would confound depth with
    position -- the hand sits at the optical centre where a lateral translation produces the
    most flow, and the background average runs off-axis where the same lens compresses it, so
    that ratio exceeds the depth ratio for a reason that has nothing to do with depth. Holding
    the pixels fixed and moving only the plane gives 1/Z directly."""
    near = Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA),
                 hand_distance_m=0.45, background_distance_m=0.45)
    far = Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA),
                hand_distance_m=2.50, background_distance_m=2.50)
    step = (0.004, 0.0, 0.0)  # small enough that the first-order 1/Z relation holds
    mask = box_mask((CORPUS_CAMERA.height, CORPUS_CAMERA.width), [near.hand_box])
    a = np.linalg.norm(analytic_flow(near, translation_m=step)[mask], axis=-1).mean()
    b = np.linalg.norm(analytic_flow(far, translation_m=step)[mask], axis=-1).mean()
    assert a / b == pytest.approx(2.50 / 0.45, rel=0.02)


def test_the_hand_moves_more_than_the_background_under_translation() -> None:
    """The direction that makes the ego-motion subtraction leave a residual: whatever the
    scalar median over the background is, the hand's own flow is larger than it."""
    scene = _corpus_scene()
    flow = analytic_flow(scene, translation_m=(0.0625, 0.0, 0.0))
    mask = box_mask((CORPUS_CAMERA.height, CORPUS_CAMERA.width), [scene.hand_box])
    finite = np.isfinite(flow).all(axis=-1)
    hand = np.linalg.norm(flow[mask & finite], axis=-1).mean()
    background = np.linalg.norm(flow[(~mask) & finite], axis=-1).mean()
    assert hand > background * 2.0


def test_pure_rotation_over_a_two_plane_scene_still_shows_no_parallax() -> None:
    """The discriminator between the two mechanisms: rotation residual is a lens effect, and
    must not depend on the hand being nearer."""
    a = analytic_flow(_corpus_scene(), rotation_rad=math.radians(7.5))
    b = analytic_flow(Scene(camera=CORPUS_CAMERA, hand_box=hand_box_for(CORPUS_CAMERA),
                            hand_distance_m=2.5, background_distance_m=2.5),
                      rotation_rad=math.radians(7.5))
    assert np.nanmax(np.abs(a - b)) < 1e-6


def test_the_hand_box_is_the_size_the_geometry_implies() -> None:
    """An 85 mm hand at 0.45 m under the corpus lens. `CONTRACTS.md`'s own HandSpeedEstimate
    example carries a 209 px median box width, so the geometry and the contract agree on the
    order of the thing without either being fitted to the other."""
    box = hand_box_for(CORPUS_CAMERA)
    assert 150.0 < box.width < 250.0
    assert box.width == pytest.approx(box.height, rel=0.02)
