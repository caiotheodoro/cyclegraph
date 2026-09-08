"""Flow gain as a test an estimator either passes or fails for a stated geometry.

`scripts/measure_flow_gain.py` measures gain -- median recovered flow magnitude over median
true magnitude inside the hand box -- against hand displacement. This module turns that sweep
into a verdict, so a third party can point it at their own estimator and get back the three
numbers that matter rather than a table to interpret.

The three numbers:

    knee_px               the last displacement above KNEE_GAIN before the first collapse
    floor_gain            the gain the estimator settles on once it has lost the hand
    floor_ratio_expected  hand distance over background distance

**What gain does not test.** It is a ratio of median magnitudes over the hand box, so it says
nothing about direction -- an estimator returning the exact field negated scores identically to
a perfect one -- nothing about endpoint error, and nothing about a field that is right in half
the box and wrong in the other half, because a median hides that. It is a test for one specific
failure: the estimator quietly swapping which object it reports. Use it alongside an endpoint
error, not instead of one.

**Passing is not gain near 1.0 everywhere.** No dense estimator does that. Passing is the knee
sitting outside the displacements the work actually produces, which is why `verdict()` takes
that displacement as an argument rather than assuming one.

`floor_gain` equalling `floor_ratio_expected` is the signature this exists to detect: the
estimator has smoothed across the depth discontinuity at the edge of the hand box, lost the
hand, and locked onto the background, which is further away by exactly that ratio. The number
it returns is then a correct measurement of the wrong object, and `docs/RUBRIC.md`'s ego-motion
subtraction removes it rather than flagging it (`docs/DECISIONS.md` D044).

Past the knee there are two regimes, not one (`docs/DECISIONS.md` D070): the estimator tracks
the background at the depth ratio, and then, once displacement exceeds its search range
outright, it tracks nothing and gain falls toward zero. Averaging the two understates the floor,
so the second regime is excluded by REGIME_TWO_FRACTION rather than silently included.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Callable, Final, Protocol

import numpy as np
import numpy.typing as npt

from cyclegraph.signal.ports import Flow

if False:  # typing-only, avoids importing numpy-heavy modules at import time
    from cyclegraph.signal.synthetic import Camera

# Above this the estimator is recovering the hand's motion. 0.90 rather than 0.95 because the
# rendered pairs carry the generator's own bilinear resampling error, which costs a few percent
# at every displacement and is not the estimator's fault.
KNEE_GAIN: Final[float] = 0.90

# Below this it is not recovering it. The band between the two is a transition and is
# deliberately left unclassified -- calling it either way would be a judgement the measurement
# does not support.
COLLAPSE_GAIN: Final[float] = 0.50

# A collapsed gain below this fraction of the depth ratio is regime two -- tracking nothing at
# all -- and is excluded from the floor. Half is chosen because the observed regime-one spread
# in `results/flow_gain_by_resolution.json` stays inside +/-30% of the ratio at every scale,
# so half leaves clear air below the plateau without reaching the regime-two points.
REGIME_TWO_FRACTION: Final[float] = 0.5

# Relative tolerance for calling the floor equal to the depth ratio. The observed regime-one
# medians sit within 10% of it across four decode scales and two estimators; 25% leaves room
# for a different generator seed without admitting an unrelated value.
BACKGROUND_TOLERANCE: Final[float] = 0.25

#: Seed and camera translations are the published sweep's, so a third party's curve is
#: comparable to `results/flow_gain_by_resolution.json` rather than merely similar in shape.
#:
#: These translate the **camera** over a static scene, which is how a static hand is given
#: relative motion here. Because the hand plane is nearer than the background, its projection
#: moves further, and that difference is the depth discontinuity the measurement is about. It
#: is also why `floor_ratio_expected` is the depth ratio: past the knee the estimator reports
#: the background, which under camera translation is moving at that fraction of the hand's
#: apparent speed. Under a static camera and an independently moving hand the background does
#: not move at all, the estimator falls back toward zero rather than toward the ratio, and
#: `tracks_background` will not fire. The knee is unaffected; the floor's value is not.
SEED: Final[int] = 11
TRANSLATIONS_M: Final[tuple[float, ...]] = (0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.12, 0.15)


class _Estimator(Protocol):
    def flow(self, first: npt.NDArray[np.uint8],
             second: npt.NDArray[np.uint8]) -> Flow | None: ...


#: Either the repo's `FlowEstimator` protocol or a bare callable, so a third party does not have
#: to implement a Protocol to run the test.
EstimatorLike = _Estimator | Callable[
    [npt.NDArray[np.uint8], npt.NDArray[np.uint8]], "Flow | None"]


@dataclass(frozen=True, slots=True)
class GainRow:
    hand_displacement_px: float
    gain: float | None
    flow_returned_none: bool


@dataclass(frozen=True, slots=True)
class GainCurve:
    """The sweep, plus what it says about the estimator."""

    rows: tuple[GainRow, ...]
    floor_ratio_expected: float
    knee_px: float | None
    collapse_px: float | None
    floor_gain: float | None

    @property
    def tracks_background(self) -> bool:
        """True when the floor sits on the depth ratio, which is the failure this detects."""
        if self.floor_gain is None:
            return False
        return (abs(self.floor_gain - self.floor_ratio_expected)
                <= BACKGROUND_TOLERANCE * self.floor_ratio_expected)

    def verdict(self, operating_displacement_px: float) -> str:
        """PASS, FAIL or UNTESTED for a stated working displacement.

        UNTESTED, never PASS, when the sweep does not bracket the displacement asked about --
        a test that has not seen a case does not get to clear it. That applies below the
        smallest displacement measured as well as above the largest: RAFT-small really does
        under-recover small motions, scoring gain 0.3019 at 2.849 px at 480x270 in
        `results/flow_gain_raft.json`, so a curve measured from 5.7 px upward says nothing
        about 1 px and must not pretend otherwise.
        """
        measured = [r.hand_displacement_px for r in self.rows]
        if not (min(measured) <= operating_displacement_px <= max(measured)):
            return "UNTESTED"
        if self.knee_px is None:
            return "FAIL"
        return "PASS" if operating_displacement_px <= self.knee_px else "FAIL"


def curve_from_rows(rows: list[dict[str, Any]], floor_ratio_expected: float) -> GainCurve:
    """Build a curve from `scripts/measure_flow_gain.py`'s row dicts, published or freshly run."""
    parsed = tuple(
        GainRow(
            hand_displacement_px=float(r["hand_displacement_px"]),
            gain=None if r["gain"] is None else float(r["gain"]),
            flow_returned_none=bool(r["flow_returned_none"]),
        )
        for r in sorted(rows, key=lambda r: float(r["hand_displacement_px"]))
    )
    scored = [r for r in parsed if r.gain is not None]

    # The knee is the last displacement above KNEE_GAIN *before the first collapse*, not the
    # largest anywhere in the sweep. Taking a plain max lets a curve that collapses at 20 px and
    # recovers at 60 px report a knee of 60 and PASS at 20 -- a real shape for a multi-scale
    # estimator whose pyramid levels disagree, and one the harness must not clear.
    first_collapse = next((r.hand_displacement_px for r in scored
                           if r.gain is not None and r.gain < COLLAPSE_GAIN), None)
    above = [r.hand_displacement_px for r in scored
             if r.gain is not None and r.gain >= KNEE_GAIN
             and (first_collapse is None or r.hand_displacement_px < first_collapse)]
    knee = max(above) if above else None
    collapse = first_collapse

    # Regime one only: collapsed, but not so far collapsed that the estimator has stopped
    # tracking anything (D070).
    regime_one = [r.gain for r in scored
                  if r.gain is not None
                  and r.gain < COLLAPSE_GAIN
                  and r.gain >= REGIME_TWO_FRACTION * floor_ratio_expected]
    floor = statistics.median(regime_one) if regime_one else None

    return GainCurve(rows=parsed, floor_ratio_expected=floor_ratio_expected,
                     knee_px=knee, collapse_px=collapse, floor_gain=floor)


def scaled_camera(width: int) -> "Camera":
    """The corpus camera at `width`, preserving its intrinsics ratio."""
    from cyclegraph.signal.synthetic import CORPUS_CAMERA, Camera
    c = CORPUS_CAMERA
    s = width / c.width
    return Camera(width=int(c.width * s), height=int(c.height * s), fx=c.fx * s, fy=c.fy * s,
                  cx=c.cx * s, cy=c.cy * s, k=c.k)


def sweep(width: int, estimator: EstimatorLike, pair_interval_s: float,
          *, translations_m: tuple[float, ...] = TRANSLATIONS_M,
          seed: int = SEED) -> dict[str, Any]:
    """One decode scale of the displacement sweep.

    Moved here from `scripts/measure_flow_gain.py` so the harness and the script run the same
    code. Behaviour is unchanged; `results/flow_gain_by_resolution.json` reproduces from it.
    """
    from cyclegraph.signal.ports import box_mask
    from cyclegraph.signal.speed import HAND_BREADTH_MM
    from cyclegraph.signal.synthetic import Scene, analytic_flow, hand_box_for, render_pair

    cam = scaled_camera(width)
    scene = Scene(camera=cam, hand_box=hand_box_for(cam))
    mask = box_mask((cam.height, cam.width), [scene.hand_box])
    mm_per_px = HAND_BREADTH_MM / scene.hand_box.width
    dt = pair_interval_s
    call = estimator.flow if hasattr(estimator, "flow") else estimator
    rows = []
    for metres in translations_m:
        truth = analytic_flow(scene, translation_m=(metres, 0.0, 0.0))
        first, second = render_pair(scene, translation_m=(metres, 0.0, 0.0), seed=seed)
        field = call(first, second)
        true_px = float(np.median(np.linalg.norm(truth[mask], axis=-1)))
        got_px = (float(np.median(np.linalg.norm(field[mask], axis=-1)))
                  if field is not None else None)
        rows.append({
            "translation_m_per_pair": metres,
            "hand_displacement_px": round(true_px, 3),
            "true_speed_mm_s": round(true_px * mm_per_px / dt, 1),
            "recovered_px": None if got_px is None else round(got_px, 3),
            "gain": None if got_px is None else round(got_px / true_px, 4),
            "flow_returned_none": field is None,
        })
    return {
        "frame_size": [cam.width, cam.height],
        "hand_box_width_px": round(scene.hand_box.width, 3),
        "mm_per_px": round(mm_per_px, 5),
        "pair_interval_s": dt,
        "rows": rows,
    }


def gain_curve(estimator: EstimatorLike, *, width: int = 960,
               pair_interval_s: float = 1.0 / 30.0) -> GainCurve:
    """Run the sweep against `estimator` and return the curve with its verdict inputs.

    Needs no corpus, no token and no network. `pair_interval_s` only rescales the reported
    speeds; it does not change the displacements or the gains, which is why the curve is keyed
    on displacement in pixels.
    """
    from cyclegraph.signal.synthetic import BACKGROUND_DISTANCE_M, HAND_DISTANCE_M

    scale = sweep(width, estimator, pair_interval_s)
    rows: list[dict[str, Any]] = scale["rows"]
    return curve_from_rows(rows, HAND_DISTANCE_M / BACKGROUND_DISTANCE_M)
