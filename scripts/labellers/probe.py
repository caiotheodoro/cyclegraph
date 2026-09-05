"""The cheap manipulation labeller: frozen DINOv2 features and a linear head.

`docs/METHOD.md` E3 makes a probe of this shape the primary label source, because the
arithmetic rules out a VLM judge on every frame at any price. The design -- frozen backbone,
linear head, judge labels as the training target -- is inherited from `../vernier`, and so are
the labels it trains on (`docs/LINEAGE.md`).

**What is inherited and what is not.** Vernier's *trained* probe predicts `hands_visible`,
because that was its own hypothesis; it is not reusable here and is not reused. What carries
over is its 29,400 stored judge labels, which record `manipulation` alongside the hand count,
its cached DINOv2 features, and the shape of the method. This module trains a new head on the
same features against the `manipulation` column.

**The backbone is `facebook/dinov2-small` and the pooling is mean over patch tokens.** Neither
travels with a saved head, so both are named here: a linear head is meaningless without the
exact features it was fitted to, and a caller who changed either would get a probe that
silently scored a different quantity.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

import numpy as np

BACKBONE: Final[str] = "facebook/dinov2-small"
FEATURE_DIM: Final[int] = 384
IMAGE_MEAN: Final[tuple[float, float, float]] = (0.485, 0.456, 0.406)
IMAGE_STD: Final[tuple[float, float, float]] = (0.229, 0.224, 0.225)
IMAGE_SIZE: Final[int] = 224
SEED: Final[int] = 777


@dataclass(frozen=True, slots=True)
class Fidelity:
    """How well the head reproduces the judge it was distilled from, held out.

    `accuracy` alone is not evidence on a class-imbalanced problem -- a probe that answered
    "manipulating" every time would score the base rate -- so the baseline it must beat is
    reported beside it and `balanced_accuracy` is reported at all.
    """

    n: int
    accuracy: float
    majority_baseline: float
    balanced_accuracy: float
    aggregate_prevalence_judge: float
    aggregate_prevalence_probe: float

    @property
    def beats_baseline(self) -> bool:
        return self.accuracy > self.majority_baseline


class ManipulationProbe:
    """A linear head over frozen features, predicting the manipulation label."""

    def __init__(self, model: Any = None) -> None:
        self._model = model

    @classmethod
    def fit(cls, features: Sequence[Sequence[float]],
            manipulation: Sequence[bool]) -> ManipulationProbe:
        from sklearn.linear_model import LogisticRegression

        x = np.asarray(features, dtype=np.float32)
        y = np.asarray([int(bool(v)) for v in manipulation])
        if x.shape[1] != FEATURE_DIM:
            raise ValueError(f"features must be {FEATURE_DIM}-dimensional, got {x.shape[1]}")
        if len(set(y.tolist())) < 2:
            raise ValueError("a probe cannot be fitted on one class")
        model = LogisticRegression(max_iter=1000, random_state=SEED)
        model.fit(x, y)
        return cls(model)

    def predict(self, features: Sequence[Sequence[float]]) -> list[bool]:
        if self._model is None:
            raise RuntimeError("the probe has no fitted head")
        return [bool(v) for v in self._model.predict(np.asarray(features, dtype=np.float32))]

    def save(self, path: Path) -> None:
        import joblib

        if self._model is None:
            raise RuntimeError("refusing to save an unfitted probe")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self._model, "backbone": BACKBONE,
                     "feature_dim": FEATURE_DIM, "target": "manipulation"}, path)

    @classmethod
    def load(cls, path: Path) -> ManipulationProbe:
        import joblib

        blob = joblib.load(path)
        if blob.get("backbone") != BACKBONE or blob.get("target") != "manipulation":
            raise ValueError(
                f"this head was fitted to {blob.get('backbone')!r} for "
                f"{blob.get('target')!r}; a head is meaningless without the exact features "
                f"it was fitted to"
            )
        return cls(blob["model"])


def cross_validated_fidelity(features: Sequence[Sequence[float]],
                             manipulation: Sequence[bool], *, folds: int = 5) -> Fidelity:
    """Held-out fidelity by stratified cross-validation, with its own baseline beside it."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    x = np.asarray(features, dtype=np.float32)
    y = np.asarray([int(bool(v)) for v in manipulation])
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED)
    predicted = cross_val_predict(LogisticRegression(max_iter=1000, random_state=SEED), x, y, cv=cv)
    return Fidelity(
        n=int(y.size),
        accuracy=float((predicted == y).mean()),
        majority_baseline=float(max(y.mean(), 1.0 - y.mean())),
        balanced_accuracy=float(balanced_accuracy_score(y, predicted)),
        aggregate_prevalence_judge=float(y.mean()),
        aggregate_prevalence_probe=float(predicted.mean()),
    )


class HandCountProbe:
    """`../vernier`'s trained head, predicting `hands_visible` over the same features.

    This one **is** reused as-is: it is the head vernier fitted for its own hypothesis, its
    fidelity is published as a negative result (0.6933 teacher fidelity against a
    pre-registered 0.90), and `CONTRACTS.md` requires a hand count alongside every
    manipulation label. Refitting it here would be rebuilding something already measured and
    already disclosed, and the disclosure is the more valuable half.
    """

    def __init__(self, model: Any) -> None:
        self._model = model

    @classmethod
    def load(cls, path: Path) -> HandCountProbe:
        import joblib

        model = joblib.load(path)
        if not hasattr(model, "predict") or getattr(model, "n_features_in_", None) != FEATURE_DIM:
            raise ValueError(
                f"{path} is not a {FEATURE_DIM}-dimensional head; a head is meaningless "
                f"without the exact features it was fitted to"
            )
        return cls(model)

    def predict(self, features: Sequence[Sequence[float]]) -> list[int]:
        return [int(v) for v in self._model.predict(np.asarray(features, dtype=np.float32))]


def inherited_training_set(features_path: Path, labels_path: Path
                           ) -> tuple[list[str], list[list[float]], list[bool]]:
    """Vernier's cached DINOv2 features joined to its stored judge labels, by frame id.

    Only frames present in both are returned, and the join is by id rather than by position:
    the two files were written by different runs and a positional join would silently pair a
    frame's features with another frame's label.
    """
    features: dict[str, list[float]] = json.loads(features_path.read_text())
    labels = {r["frame_id"]: r for r in json.loads(labels_path.read_text())
              if r.get("status") == "ok"}
    ids = sorted(set(features) & set(labels))
    if not ids:
        raise ValueError("no frame appears in both the feature cache and the label store")
    return (ids,
            [features[i] for i in ids],
            [bool(labels[i]["manipulation"]) for i in ids])
