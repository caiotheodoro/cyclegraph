"""Tests for `scripts/run_labeller.py` and `scripts/labellers/probe.py`.

The backbone is the untestable part. What is tested is the join, the fidelity arithmetic, and
the rule for what happens when the two heads contradict each other -- which is where a
labeller quietly invents a field to satisfy a schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from labellers.probe import (  # noqa: E402
    FEATURE_DIM,
    ManipulationProbe,
    cross_validated_fidelity,
    inherited_training_set,
)
from run_labeller import CONFLICT_REASON, label_rows  # noqa: E402

from cyclegraph.models import ClipRef  # noqa: E402
from cyclegraph.signal.stores import JsonlLabelStore  # noqa: E402
from tests import fixtures  # noqa: E402


def _clip() -> ClipRef:
    return ClipRef.model_validate(fixtures.CLIP_REF)


def test_a_contradiction_between_the_heads_is_unreadable_not_repaired() -> None:
    """`manipulation: true` with `hands_visible: 0` is what the contract rejects, and it is a
    real disagreement rather than a schema inconvenience. Repairing it toward either answer
    would be choosing which head to believe, silently, per frame."""
    rows, conflicts = label_rows(_clip(), [0.0, 0.25, 0.5],
                                 manipulation=[True, True, False],
                                 hands_visible=[2, 0, 0],
                                 label_rev="r", prompt_variant="none")
    assert conflicts == 1
    assert rows[0]["manipulation"] is True and rows[0]["hands_visible"] == 2
    assert rows[1]["manipulation"] is None and rows[1]["hands_visible"] is None
    assert rows[1]["unreadable_reason"] == CONFLICT_REASON
    assert rows[2]["manipulation"] is False and rows[2]["hands_visible"] == 0


def test_the_rows_round_trip_through_the_store_that_consumes_them(tmp_path: Path) -> None:
    """The contract between this script and `signal/stores.py`, and with it the contract's
    own rule that manipulation and hands_visible are null together."""
    rows, _ = label_rows(_clip(), [0.0, 0.25], manipulation=[True, True],
                         hands_visible=[2, 0], label_rev="r", prompt_variant="none")
    path = tmp_path / "labels.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    store = JsonlLabelStore.from_path(path)
    assert store.provenance.label_source == "probe"
    assert store.label(_clip().clip_id, 0.0).manipulation is True
    conflicted = store.label(_clip().clip_id, 0.25)
    assert conflicted.manipulation is None and conflicted.unreadable_reason


def test_every_instant_gets_a_row() -> None:
    rows, _ = label_rows(_clip(), [0.0, 0.25, 0.5, 0.75],
                         manipulation=[True, False, True, False],
                         hands_visible=[1, 0, 2, 1], label_rev="r", prompt_variant="none")
    assert len(rows) == 4
    assert all(r["label_source"] == "probe" for r in rows)


def test_mismatched_series_lengths_raise_rather_than_truncating() -> None:
    with pytest.raises(ValueError):
        label_rows(_clip(), [0.0, 0.25], manipulation=[True], hands_visible=[1],
                   label_rev="r", prompt_variant="none")


def _synthetic(n: int = 200, seed: int = 3) -> tuple[list[list[float]], list[bool]]:
    rng = np.random.default_rng(seed)
    y = rng.random(n) < 0.75
    direction = rng.normal(size=FEATURE_DIM)
    x = rng.normal(size=(n, FEATURE_DIM)) + np.outer(y.astype(float), direction) * 1.5
    return [[float(v) for v in row] for row in x], [bool(v) for v in y]


def test_the_probe_learns_a_separable_signal_and_reports_its_baseline() -> None:
    """Fidelity is never reported without the baseline it has to beat: on a 75/25 problem a
    probe that always said yes would score 0.75 and look respectable."""
    features, manipulation = _synthetic()
    fidelity = cross_validated_fidelity(features, manipulation)
    assert fidelity.majority_baseline == pytest.approx(
        max(np.mean(manipulation), 1 - np.mean(manipulation)))
    assert fidelity.beats_baseline
    assert fidelity.balanced_accuracy > 0.5


def test_a_probe_cannot_be_fitted_on_one_class() -> None:
    features, _ = _synthetic()
    with pytest.raises(ValueError, match="one class"):
        ManipulationProbe.fit(features, [True] * len(features))


def test_a_head_refuses_features_of_the_wrong_width() -> None:
    with pytest.raises(ValueError, match="dimensional"):
        ManipulationProbe.fit([[0.0] * 8] * 10, [True, False] * 5)


def test_an_unfitted_probe_refuses_to_be_saved(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        ManipulationProbe().save(tmp_path / "p.joblib")


def test_a_saved_head_round_trips_and_names_its_backbone(tmp_path: Path) -> None:
    features, manipulation = _synthetic()
    probe = ManipulationProbe.fit(features, manipulation)
    path = tmp_path / "p.joblib"
    probe.save(path)
    assert ManipulationProbe.load(path).predict(features[:5]) == probe.predict(features[:5])


def test_a_head_fitted_to_other_features_is_refused(tmp_path: Path) -> None:
    """A linear head is meaningless without the exact features it was fitted to, and neither
    travels with the other."""
    import joblib

    path = tmp_path / "wrong.joblib"
    joblib.dump({"model": object(), "backbone": "something-else", "target": "manipulation"},
                path)
    with pytest.raises(ValueError, match="meaningless without"):
        ManipulationProbe.load(path)


def test_the_inherited_join_is_by_id_and_not_by_position(tmp_path: Path) -> None:
    """The two files were written by different runs. A positional join would pair a frame's
    features with another frame's label and nothing downstream would notice."""
    (tmp_path / "f.json").write_text(json.dumps({"b": [0.0] * FEATURE_DIM,
                                                 "a": [1.0] * FEATURE_DIM}))
    (tmp_path / "l.json").write_text(json.dumps([
        {"frame_id": "a", "manipulation": True, "status": "ok"},
        {"frame_id": "b", "manipulation": False, "status": "ok"},
        {"frame_id": "c", "manipulation": True, "status": "ok"},
    ]))
    ids, features, manipulation = inherited_training_set(tmp_path / "f.json", tmp_path / "l.json")
    assert ids == ["a", "b"]
    assert features[0][0] == 1.0 and manipulation[0] is True
    assert features[1][0] == 0.0 and manipulation[1] is False


def test_a_non_ok_judge_response_is_not_trained_on(tmp_path: Path) -> None:
    (tmp_path / "f.json").write_text(json.dumps({"a": [1.0] * FEATURE_DIM}))
    (tmp_path / "l.json").write_text(json.dumps([
        {"frame_id": "a", "manipulation": True, "status": "error"}]))
    with pytest.raises(ValueError, match="no frame appears in both"):
        inherited_training_set(tmp_path / "f.json", tmp_path / "l.json")
