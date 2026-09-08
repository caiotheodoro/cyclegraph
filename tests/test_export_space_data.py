"""Tests for `scripts/export_space_data.py`.

The Space and the Hugging Face dataset publish the same measurements to two audiences. The
property that matters is that they cannot disagree: both read `results/`, and a figure that
appears on the page must be the figure in the data. A hand-edited chart constant is exactly how
two surfaces drift apart, and this project's whole argument is about published numbers whose
provenance nobody can check.

The quiver export also has to survive the fisheye's image circle, which covers 96% of the frame
and leaves the rest with no defined projection.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import export_hf_dataset as hf  # noqa: E402
import export_space_data as sp  # noqa: E402


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    return sp.build()


def test_the_payload_is_valid_json_with_no_non_finite_literal(payload: dict[str, Any]) -> None:
    """`analytic_flow` is NaN outside the image circle, and bare NaN is not valid JSON.

    Serialising it would make `JSON.parse` reject the whole file and the page render nothing,
    which is how this was found.
    """
    text = json.dumps(payload, allow_nan=False)
    assert "NaN" not in text and "Infinity" not in text
    assert json.loads(text) == payload


def test_every_sampled_vector_is_finite(payload: dict[str, Any]) -> None:
    for panel in payload["quivers"]:
        assert panel["vectors"], "a panel exported no vectors"
        assert panel["vectors_outside_image_circle"] > 0, (
            "no point fell outside the image circle, so the filter is untested here")
        for v in panel["vectors"]:
            for key in ("tx", "ty", "rx", "ry"):
                assert math.isfinite(v[key]), (panel["displacement_px"], key)


def test_the_space_and_the_dataset_report_the_same_gains(payload: dict[str, Any],
                                                         tmp_path: Path) -> None:
    """The verification that matters: two surfaces, one source, no divergence."""
    hf.export(tmp_path)
    rows = [json.loads(ln) for ln in
            (tmp_path / "data" / "displacement_gain.jsonl").read_text().splitlines() if ln]
    dataset = {(r["frame_width"], r["hand_displacement_px"]): r["gain"] for r in rows}

    space = {(s["frame_size"][0], r["displacement_px"]): r["gain"]
             for s in payload["sweeps"]["farneback_025"] for r in s["rows"]}

    assert space == dataset


def test_the_depth_ratio_on_the_page_is_the_generator_s(payload: dict[str, Any]) -> None:
    assert payload["depth_ratio"] == round(
        payload["hand_distance_m"] / payload["background_distance_m"], 4)
    assert payload["depth_ratio"] == 0.18


def test_the_quiver_panels_show_the_collapse(payload: dict[str, Any]) -> None:
    """The hero's argument, asserted rather than eyeballed.

    Below the knee the in-box recovered flow is several times the background's, because the hand
    is nearer. Past it the two are the same size, which is the whole finding.
    """
    ratios = []
    for panel in payload["quivers"]:
        inside = [v for v in panel["vectors"] if v["in_box"]]
        outside = [v for v in panel["vectors"] if not v["in_box"]]
        rec_in = sorted(math.hypot(v["rx"], v["ry"]) for v in inside)[len(inside) // 2]
        true_out = sorted(math.hypot(v["tx"], v["ty"]) for v in outside)[len(outside) // 2]
        ratios.append(rec_in / true_out)

    expected = 1.0 / payload["depth_ratio"]          # 5.56, the hand's advantage in pixels
    assert ratios[0] > 0.7 * expected, ratios        # following the hand
    assert ratios[-1] < 1.5, ratios                  # reporting the background
    assert ratios[0] > 3 * ratios[-1], ratios        # and the two panels are far apart


def test_the_page_reads_only_the_exported_payload() -> None:
    """No measured figure may be typed into the HTML; the page has to ask for it."""
    html = (ROOT / "space" / "index.html").read_text()
    body = html[html.index("<body>"):]
    for literal in ("0.9925", "0.2024", "34.181", "10.0916", "0.1801", "1.1461"):
        assert literal not in body, f"{literal} is hard-coded in the page"
    assert 'fetch("data.json")' in body


def test_the_page_classifies_with_the_harness_s_own_thresholds(payload: dict[str, Any]) -> None:
    """The page duplicates `gain.py`'s knee/floor rule in JavaScript, which can drift.

    Flagged by the W9 fresh-context review: the page had 0.9, 0.5 and 0.5 * ratio retyped as
    literals, so changing a constant in `gain.py` would have left the Space silently
    disagreeing with the harness a reader downloads. The thresholds now travel in the payload
    and the page must read them from there.
    """
    from cyclegraph.signal.gain import (
        BACKGROUND_TOLERANCE,
        COLLAPSE_GAIN,
        KNEE_GAIN,
        REGIME_TWO_FRACTION,
    )

    assert payload["thresholds"] == {
        "knee_gain": KNEE_GAIN,
        "collapse_gain": COLLAPSE_GAIN,
        "regime_two_fraction": REGIME_TWO_FRACTION,
        "background_tolerance": BACKGROUND_TOLERANCE,
    }

    body = (ROOT / "space" / "index.html").read_text()
    body = body[body.index("<body>"):]
    assert "const TH = D.thresholds" in body
    for literal in ("r.gain >= 0.9", "r.gain < 0.5", "0.5 * RATIO", "[0, 0.18,"):
        assert literal not in body, f"{literal} is retyped in the page"


def test_the_space_publishes_no_pilot_column(payload: dict[str, Any]) -> None:
    """`flow_benchmark.json`'s throughput and null-rate columns are pilot measurements (D059).

    They shipped in `space/data.json` under a `benchmark` key the page never referenced -- a
    leak with no reader. Only the synthetic A14 residuals remain.
    """
    import json as _json

    text = _json.dumps(payload)
    for field in ("pairs_per_s", "flow_null_rate", "pairs_per_s_batched_8"):
        assert field not in text, field
    assert set(payload["a14_residuals"]) == {"farneback-cv2", "raft-small"}
    for arm in payload["a14_residuals"].values():
        assert set(arm) == {"with_estimator_px", "geometry_only_px"}
