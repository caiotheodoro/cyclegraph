"""Tests for `scripts/bench_flow.py`'s A14 column.

The column exists so D024 can separate two flow estimators by the residual each leaves on the
rotation synthetic. It shipped taking an `estimator` argument and never calling it, computing
the residual from the analytic field alone -- so it would have returned the same number for
every arm, and the comparison it exists for could not have discriminated. These tests pin the
property the defect broke: the returned value must *depend on the estimator*.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bench_flow  # noqa: E402

from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.synthetic import CORPUS_CAMERA  # noqa: E402
from cyclegraph.signal.ports import Flow  # noqa: E402


class _DeadFlow:
    """An estimator that always fails. The A14 column must report its absence, not a zero."""

    @property
    def flow_method(self) -> str:
        return "dead"

    def flow(self, first: npt.NDArray[np.uint8],
             second: npt.NDArray[np.uint8]) -> Flow | None:
        return None


def test_the_geometry_residual_is_reported_without_an_estimator() -> None:
    geometry, estimated = bench_flow._a14_residuals(None)
    assert geometry > 0.0
    assert estimated is None


def test_the_residual_depends_on_the_estimator_that_was_passed() -> None:
    """The regression. Under the defect both values were the geometry's, so this failed by
    equality -- which is exactly how a comparison between two arms would have been silently
    reduced to a comparison between one arm and itself."""
    geometry, estimated = bench_flow._a14_residuals(FarnebackFlow())
    assert estimated is not None
    assert estimated != geometry
    # Same lens, same rotation: the geometry term must not move when the estimator changes.
    assert bench_flow._a14_residuals(None)[0] == geometry


def test_a_failing_estimator_reports_no_residual_rather_than_zero() -> None:
    """A15 at the benchmark: an estimator that returns nothing has not measured a residual of
    zero, and recording zero would make the worst arm look like the best one."""
    geometry, estimated = bench_flow._a14_residuals(_DeadFlow())
    assert geometry > 0.0
    assert estimated is None


def test_the_synthetic_is_evaluated_where_the_pipeline_actually_runs() -> None:
    """A dense estimator's error is a function of displacement in pixels, so the column has to
    be measured at the pipeline's own resolution *and* its own pair. Both were stale: the
    resolution was 480x270 after D050 moved flow to 960x540, and the rotation was priced over
    a 0.25 s pair after D045 made the pair one source frame. Measured over the old pair the
    displacement lands in the regime D050 shows both estimators collapse in -- so the column
    meant to separate them was measured where they are indistinguishable."""
    scene = bench_flow._bench_scene()
    assert scene.camera.width == bench_flow.WIDTH == 960
    assert scene.camera.height == bench_flow.HEIGHT == 540
    assert scene.camera.width < CORPUS_CAMERA.width
    # One frame of a 30 fps source, not a quarter second of it.
    assert bench_flow.A14_ROTATION_DEG == pytest.approx(1.0)
