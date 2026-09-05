"""Tests for `src/cyclegraph/signal/stores.py`.

Every rule here is one that would not fail loudly if it were wrong: a pooled label source
makes H1 unanswerable rather than raising, an unwritten instant read as `False` biases duty
cycle downward, and a region prior written to a file looks exactly like a detector's output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cyclegraph.signal.stores import NO_ROW_REASON, JsonlDetectionStore, JsonlLabelStore


def _write(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def _detection(t: float, boxes: int = 1, source: str = "100doh") -> dict[str, object]:
    return {
        "clip_id": "factory_001/worker_001/000123", "t_s": t, "mask_source": source,
        "boxes": [{"x": 10.0, "y": 20.0, "width": 200.0, "height": 190.0, "score": 0.9}] * boxes,
    }


def _label(t: float, manipulation: bool | None = True, source: str = "judge",
           hands: int | None = 2) -> dict[str, object]:
    row: dict[str, object] = {
        "clip_id": "factory_001/worker_001/000123", "t_s": t, "label_source": source,
        "label_rev": "qwen3vl@abc", "prompt_variant": "P0b",
        "manipulation": manipulation, "hands_visible": hands,
    }
    if manipulation is None:
        row["unreadable_reason"] = "frame unreadable"
    return row


def test_detections_round_trip_by_instant(tmp_path: Path) -> None:
    store = JsonlDetectionStore.from_path(
        _write(tmp_path / "d.jsonl", [_detection(0.0), _detection(0.25)]))
    assert store.mask_source == "100doh"
    assert len(store.detect("factory_001/worker_001/000123", 0.25).boxes) == 1
    assert store.detect("factory_001/worker_001/000123", 0.25).boxes[0].width == 200.0


def test_an_unwritten_instant_is_a_detector_that_did_not_run(tmp_path: Path) -> None:
    store = JsonlDetectionStore.from_path(_write(tmp_path / "d.jsonl", [_detection(0.0)]))
    missing = store.detect("factory_001/worker_001/000123", 99.0)
    assert missing.boxes == () and missing.failed_reason is not None


def test_a_region_prior_is_refused_on_load(tmp_path: Path) -> None:
    """`docs/HANDOFF.md`: no detector box, no speed. Writing it to a file first must not
    launder it into a record."""
    path = _write(tmp_path / "d.jsonl", [_detection(0.0, source="region")])
    with pytest.raises(ValueError, match="region prior"):
        JsonlDetectionStore.from_path(path)


def test_two_detectors_in_one_file_are_refused(tmp_path: Path) -> None:
    path = _write(tmp_path / "d.jsonl",
                  [_detection(0.0, source="100doh"), _detection(0.25, source="egohos")])
    with pytest.raises(ValueError, match="one detector per file"):
        JsonlDetectionStore.from_path(path)


def test_an_empty_detections_file_names_no_detector(tmp_path: Path) -> None:
    (tmp_path / "d.jsonl").write_text("")
    with pytest.raises(ValueError, match="names no detector"):
        JsonlDetectionStore.from_path(tmp_path / "d.jsonl")


def test_labels_round_trip_with_their_provenance(tmp_path: Path) -> None:
    store = JsonlLabelStore.from_path(_write(tmp_path / "l.jsonl", [_label(0.0), _label(0.25)]))
    assert store.provenance.label_source == "judge"
    assert store.provenance.label_rev == "qwen3vl@abc"
    assert store.label("factory_001/worker_001/000123", 0.0).manipulation is True


def test_two_label_sources_in_one_file_are_refused(tmp_path: Path) -> None:
    """Seam 2, mechanically. Pooling sources inside one estimate erases H1's independent
    variable, and it would not fail loudly anywhere else."""
    path = _write(tmp_path / "l.jsonl", [_label(0.0, source="judge"),
                                         _label(0.25, source="probe")])
    with pytest.raises(ValueError, match="one label source per file"):
        JsonlLabelStore.from_path(path)


def test_a_row_without_provenance_is_refused_rather_than_defaulted(tmp_path: Path) -> None:
    row = _label(0.0)
    del row["label_source"]
    with pytest.raises(ValueError, match="never defaulted"):
        JsonlLabelStore.from_path(_write(tmp_path / "l.jsonl", [row]))


def test_an_unwritten_instant_is_unreadable_and_never_false(tmp_path: Path) -> None:
    """The whole difference between 'not scored' and 'no manipulation'. Only one is evidence,
    and reading the first as the second biases duty cycle downward."""
    store = JsonlLabelStore.from_path(_write(tmp_path / "l.jsonl", [_label(0.0)]))
    missing = store.label("factory_001/worker_001/000123", 42.0)
    assert missing.manipulation is None
    assert missing.manipulation is not False
    assert missing.unreadable_reason == NO_ROW_REASON


def test_an_explicitly_unreadable_row_survives_the_round_trip(tmp_path: Path) -> None:
    store = JsonlLabelStore.from_path(
        _write(tmp_path / "l.jsonl", [_label(0.0, manipulation=None, hands=None)]))
    got = store.label("factory_001/worker_001/000123", 0.0)
    assert got.manipulation is None and got.hands_visible is None


def test_instants_match_despite_float_round_tripping(tmp_path: Path) -> None:
    """Instants are constructed as i/fps and pass through JSON, so lookup is quantised."""
    store = JsonlLabelStore.from_path(_write(tmp_path / "l.jsonl", [_label(3 / 4)]))
    assert store.label("factory_001/worker_001/000123", 0.75).manipulation is True
