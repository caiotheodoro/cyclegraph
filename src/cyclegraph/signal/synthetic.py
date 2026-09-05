"""Synthetic camera motion over a static hand, for the `docs/RED-TEAM.md` A14 floor.

A14 says a scalar ego-motion subtraction leaves residual flow where the hands sit, for two
reasons that behave differently and are measured separately here.

**Rotation.** Optical flow under pure camera rotation is independent of depth, so a correct
model cancels it everywhere. `docs/RUBRIC.md` does not fit a model: it takes *the median flow
over the complement of the hand mask*, a single vector. On a narrow lens rotational flow is
nearly uniform and that vector cancels it; on a wide one it is not, and the difference between
the flow at the hand and the median over the background survives as apparent hand speed. This
is why the rotation case is run twice -- once narrow, where the answer is zero and the test is
of the estimator's arithmetic, and once under the corpus's own lens, where the answer is the
part of A14 that a translation-only test would miss entirely (`docs/DECISIONS.md` D021).

**Translation.** Flow scales as `v/Z`. The hands are at arm's length and the background the
median is taken from is several times further, so the hand's flow exceeds the subtracted
median by roughly the depth ratio, and the remainder reads as hand speed.

The lens is the corpus's, not an invention: `intrinsics.json` is byte-identical for all 2,144
workers, so these constants are a corpus property rather than a per-worker value
(`docs/DECISIONS.md` D025). The projection is Kannala-Brandt, which is what `model: "fisheye"`
with four radial coefficients and no tangential terms denotes.

Everything here is exact geometry. `analytic_flow` is ground truth, not an estimate, which is
what lets the floor be separated from any optical-flow estimator's own error -- the floor is a
property of the rubric's ego-motion rule, and is measured without a flow estimator in the loop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
import numpy.typing as npt

from cyclegraph.signal.ports import Flow, HandBox

# `docs/DECISIONS.md` D025: identical across all 2,144 shipped workers.
CORPUS_FX: Final[float] = 1030.587009
CORPUS_FY: Final[float] = 1032.815725
CORPUS_CX: Final[float] = 966.691189
CORPUS_CY: Final[float] = 539.687801
CORPUS_K: Final[tuple[float, float, float, float]] = (-0.116554, -0.023589, 0.069364, -0.046334)
CORPUS_WIDTH: Final[int] = 1920
CORPUS_HEIGHT: Final[int] = 1080

# Stated assumptions, not measurements. They are part of the published floor's definition, so
# they are named here rather than buried in a test.
HAND_DISTANCE_M: Final[float] = 0.45
"""Hand to head-mounted camera at a workstation. Gives an 85 mm hand a box near 195 px under
the corpus lens, which is the order of `CONTRACTS.md`'s own 209 px example."""

BACKGROUND_DISTANCE_M: Final[float] = 2.50
"""The scene the ego-motion median is taken from: the far side of a work cell."""


@dataclass(frozen=True, slots=True)
class Camera:
    """A projection model. `k` is Kannala-Brandt radial; all zero is the pinhole limit."""

    fx: float
    fy: float
    cx: float
    cy: float
    k: tuple[float, float, float, float]
    width: int
    height: int

    @property
    def is_pinhole(self) -> bool:
        return all(c == 0.0 for c in self.k)


CORPUS_CAMERA: Final[Camera] = Camera(
    fx=CORPUS_FX, fy=CORPUS_FY, cx=CORPUS_CX, cy=CORPUS_CY,
    k=CORPUS_K, width=CORPUS_WIDTH, height=CORPUS_HEIGHT,
)

NARROW_CAMERA: Final[Camera] = Camera(
    fx=4.0 * CORPUS_FX, fy=4.0 * CORPUS_FY, cx=CORPUS_CX, cy=CORPUS_CY,
    k=(0.0, 0.0, 0.0, 0.0), width=CORPUS_WIDTH, height=CORPUS_HEIGHT,
)
"""The control. Four times the focal length and no distortion: a long lens, where a scalar
ego-motion estimate is a good model of rotation and the residual should vanish."""


def _theta_d(theta: npt.NDArray[np.float64], k: tuple[float, float, float, float]) -> npt.NDArray[np.float64]:
    t2 = theta * theta
    return theta * (1.0 + k[0] * t2 + k[1] * t2**2 + k[2] * t2**3 + k[3] * t2**4)


def project(cam: Camera, points: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Camera-frame points (..., 3) to pixels (..., 2). Kannala-Brandt."""
    x, y, z = points[..., 0], points[..., 1], points[..., 2]
    z = np.where(np.abs(z) < 1e-12, 1e-12, z)
    a, b = x / z, y / z
    r = np.hypot(a, b)
    theta = np.arctan(r)
    td = _theta_d(theta, cam.k)
    scale = np.where(r < 1e-12, 1.0, td / np.where(r < 1e-12, 1.0, r))
    return np.stack([cam.fx * scale * a + cam.cx, cam.fy * scale * b + cam.cy], axis=-1)


def max_theta(cam: Camera) -> float:
    """The largest incidence angle the model still maps monotonically outward.

    Kannala-Brandt with these coefficients is **not** monotonic: `theta_d` peaks near 1.2 rad
    and falls after it, so beyond that angle the projection is not invertible and pixels there
    do not correspond to any ray. This is not a defect in the corpus lens -- it is the ordinary
    fact that a fisheye's image circle does not reach the corners of a rectangular sensor -- but
    a model that ignored it would silently return garbage rays for the corners, and those
    corners sit in the mask complement where ego-motion is estimated.
    """
    theta = np.linspace(0.0, math.pi / 2.0, 20001)
    td = _theta_d(theta, cam.k)
    return float(theta[int(np.argmax(td))])


def image_circle_radius_px(cam: Camera) -> float:
    """Radius of the projectable image circle, in pixels along x."""
    return float(cam.fx * _theta_d(np.array([max_theta(cam)]), cam.k)[0])


def valid_mask(cam: Camera) -> npt.NDArray[np.bool_]:
    """Pixels that correspond to a real ray. The corners of a 16:9 frame do not."""
    ys, xs = np.mgrid[0 : cam.height, 0 : cam.width]
    a = (xs - cam.cx) / cam.fx
    b = (ys - cam.cy) / cam.fy
    inside: npt.NDArray[np.bool_] = np.hypot(a, b) <= _theta_d(
        np.array([max_theta(cam)]), cam.k
    )[0]
    return inside


def unproject(cam: Camera, pixels: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Pixels (..., 2) to unit ray directions (..., 3).

    Inverted by interpolation on the monotonic branch rather than by Newton: Newton diverges
    past the polynomial's turning point, and diverging quietly is how a corner pixel becomes a
    plausible-looking ray. Pixels outside the image circle come back `NaN`.
    """
    a = (pixels[..., 0] - cam.cx) / cam.fx
    b = (pixels[..., 1] - cam.cy) / cam.fy
    td = np.hypot(a, b)
    tmax = max_theta(cam)
    grid = np.linspace(0.0, tmax, 20001)
    table = _theta_d(grid, cam.k)
    theta = np.interp(td, table, grid, left=0.0, right=np.nan)
    theta = np.where(td > table[-1], np.nan, theta)
    r = np.tan(theta)
    scale = np.where(td < 1e-12, 0.0, r / np.where(td < 1e-12, 1.0, td))
    dirs = np.stack([scale * a, scale * b, np.ones_like(a)], axis=-1)
    norm = np.linalg.norm(dirs, axis=-1, keepdims=True)
    unit: npt.NDArray[np.float64] = dirs / norm
    return unit


def _rotation(axis: Literal["yaw", "pitch", "roll"], radians: float) -> npt.NDArray[np.float64]:
    c, s = math.cos(radians), math.sin(radians)
    if axis == "yaw":
        return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    if axis == "pitch":
        return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


@dataclass(frozen=True, slots=True)
class Scene:
    """Two fronto-parallel planes and the box the hand occupies, under one camera."""

    camera: Camera
    hand_box: HandBox
    hand_distance_m: float = HAND_DISTANCE_M
    background_distance_m: float = BACKGROUND_DISTANCE_M

    def depth_map(self) -> npt.NDArray[np.float64]:
        """Per-pixel plane distance: the hand plane inside the box, background elsewhere."""
        depth = np.full((self.camera.height, self.camera.width), self.background_distance_m)
        b = self.hand_box
        x0, y0 = int(b.x), int(b.y)
        x1, y1 = int(b.x + b.width), int(b.y + b.height)
        depth[y0:y1, x0:x1] = self.hand_distance_m
        return depth


def hand_box_for(cam: Camera, hand_breadth_mm: float = 85.0,
                 distance_m: float = HAND_DISTANCE_M) -> HandBox:
    """The box an 85 mm hand subtends at the image centre, from the geometry rather than a guess."""
    half = (hand_breadth_mm / 1000.0) / 2.0
    p = project(cam, np.array([[half, half, distance_m], [-half, -half, distance_m]]))
    width = float(abs(p[0, 0] - p[1, 0]))
    height = float(abs(p[0, 1] - p[1, 1]))
    return HandBox(x=cam.cx - width / 2.0, y=cam.cy - height / 2.0,
                   width=width, height=height, score=1.0)


def analytic_flow(scene: Scene, *, rotation_rad: float = 0.0,
                  translation_m: tuple[float, float, float] = (0.0, 0.0, 0.0),
                  axis: Literal["yaw", "pitch", "roll"] = "yaw") -> Flow:
    """Exact flow, in pixels, for one camera motion over a static scene.

    The camera moves by `(R, t)`; a world point sitting at pixel `p` on its plane reappears at
    `project(R.T @ (P - t))`. Under pure rotation the depth cancels, which is the property the
    narrow-lens control checks.
    """
    cam = scene.camera
    ys, xs = np.mgrid[0:cam.height, 0:cam.width]
    pix = np.stack([xs.astype(np.float64), ys.astype(np.float64)], axis=-1)
    dirs = unproject(cam, pix)
    depth = scene.depth_map()
    points = dirs * (depth / dirs[..., 2])[..., None]
    rot = _rotation(axis, rotation_rad)
    moved = (points - np.asarray(translation_m)) @ rot
    reprojected = project(cam, moved)
    delta = reprojected - pix
    # Corners outside the image circle carry no ray, so they carry no flow. They are NaN
    # rather than zero: they sit in the mask complement, and a zero there would drag the
    # ego-motion median toward zero and flatter the residual.
    delta[~valid_mask(cam)] = np.nan
    flow: Flow = delta.astype(np.float32)
    return flow
