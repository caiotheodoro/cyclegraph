"""File-backed detections and labels: the seam where the models sit outside this package.

100DOH needs torch and a judge needs an HTTP client, and the `signal` extra declares neither.
`pyproject.toml` says an extra that does not name a module, or a module with no extra, is
drift -- so rather than widening the extra to fit a runtime, the runtimes stay in `scripts/`
and this package consumes what they wrote. Three things follow, and the third is the reason:

- the extras map stays honest;
- the pilot is re-runnable offline once detections exist, so a 24 GPU-hour stage is a
  resumable batch job rather than an inline dependency of `make signal`;
- **every estimator in this repository is testable with no model installed at all.**

The seam is also where two of `docs/ARCHITECTURE.md`'s rules are enforced mechanically rather
than by discipline. A detections file whose `mask_source` is not a detector the contract knows
is refused on load, so a region prior cannot become a `HandSpeedEstimate` by being written to
a file first. A labels file carrying two different `label_source` values is refused on load,
because pooling label sources inside one estimate is what would make H1 unanswerable.

An instant with no row is **not** a negative. It comes back `manipulation: None` with a
reason, because "the labeller did not score this frame" and "the labeller saw no
manipulation" are different facts and only one of them is evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from cyclegraph.signal.ports import (
    Detection,
    FrameLabel,
    HandBox,
    LabelProvenance,
    LabelSource,
    MaskSource,
)

_QUANTUM: Final[float] = 1e-4
"""Instants are constructed as `i/fps` and round-trip through JSON, so keys are quantised
rather than compared as floats."""

_MASK_SOURCES: Final[frozenset[str]] = frozenset({"100doh", "egohos"})
_LABEL_SOURCES: Final[frozenset[str]] = frozenset({"judge", "probe", "human"})

NO_ROW_REASON: Final[str] = "no label was written for this instant"


def _key(clip_id: str, t_s: float) -> tuple[str, int]:
    return clip_id, int(round(t_s / _QUANTUM))


@dataclass(frozen=True, slots=True)
class JsonlDetectionStore:
    """Hand boxes written by `scripts/run_detector.py`. Implements `HandDetector`."""

    _rows: dict[tuple[str, int], Detection]
    _mask_source: MaskSource

    @property
    def mask_source(self) -> MaskSource:
        return self._mask_source

    @classmethod
    def from_path(cls, path: Path) -> JsonlDetectionStore:
        rows: dict[tuple[str, int], Detection] = {}
        sources: set[str] = set()
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            source = str(payload["mask_source"])
            if source not in _MASK_SOURCES:
                raise ValueError(
                    f"{source!r} is not a detector this contract knows. A hand box never comes "
                    f"from a region prior (docs/RUBRIC.md, docs/HANDOFF.md)"
                )
            sources.add(source)
            boxes = tuple(
                HandBox(x=float(b["x"]), y=float(b["y"]), width=float(b["width"]),
                        height=float(b["height"]), score=float(b["score"]))
                for b in payload.get("boxes", [])
            )
            reason = payload.get("failed_reason")
            rows[_key(str(payload["clip_id"]), float(payload["t_s"]))] = Detection(
                boxes=boxes, failed_reason=str(reason) if reason else None)
        if len(sources) > 1:
            raise ValueError(f"one detector per file; found {sorted(sources)}")
        if not sources:
            raise ValueError("an empty detections file names no detector")
        source_name = sources.pop()
        assert source_name in _MASK_SOURCES
        return cls(_rows=rows, _mask_source=source_name)  # type: ignore[arg-type]

    def detect(self, clip_id: str, t_s: float) -> Detection:
        """An unwritten instant is a detector that did not run, not a frame with no hands."""
        found = self._rows.get(_key(clip_id, t_s))
        if found is None:
            return Detection(boxes=(), failed_reason="no detection was written for this instant")
        return found


@dataclass(frozen=True, slots=True)
class JsonlLabelStore:
    """Manipulation labels written by a judge or a probe. Implements `ManipulationLabeller`."""

    _rows: dict[tuple[str, int], FrameLabel]
    _provenance: LabelProvenance

    @property
    def provenance(self) -> LabelProvenance:
        return self._provenance

    @classmethod
    def from_path(cls, path: Path) -> JsonlLabelStore:
        rows: dict[tuple[str, int], FrameLabel] = {}
        provenances: set[tuple[str, str, str]] = set()
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            for field in ("label_source", "label_rev", "prompt_variant"):
                if not payload.get(field):
                    raise ValueError(
                        f"every label row carries {field}; it is never defaulted "
                        f"(docs/ARCHITECTURE.md, seam 2)"
                    )
            source = str(payload["label_source"])
            if source not in _LABEL_SOURCES:
                raise ValueError(f"{source!r} is not a label source this contract knows")
            provenances.add((source, str(payload["label_rev"]), str(payload["prompt_variant"])))
            manipulation = payload.get("manipulation")
            hands = payload.get("hands_visible")
            reason = payload.get("unreadable_reason")
            rows[_key(str(payload["clip_id"]), float(payload["t_s"]))] = FrameLabel(
                manipulation=None if manipulation is None else bool(manipulation),
                hands_visible=None if hands is None else int(hands),  # type: ignore[arg-type]
                unreadable_reason=str(reason) if reason else None,
            )
        if len(provenances) > 1:
            raise ValueError(
                f"one label source per file; found {sorted(provenances)}. Judge, probe and "
                f"human labels have different error structures and H1 exists to measure the "
                f"difference, so they are never pooled inside one estimate"
            )
        if not provenances:
            raise ValueError("an empty labels file names no label source")
        source, rev, variant = provenances.pop()
        assert source in _LABEL_SOURCES
        label_source: LabelSource = source  # type: ignore[assignment]
        return cls(_rows=rows,
                   _provenance=LabelProvenance(label_source=label_source, label_rev=rev,
                                               prompt_variant=variant))

    def label(self, clip_id: str, t_s: float) -> FrameLabel:
        """An unwritten instant is unreadable, never `False`. Zero is the flattering direction."""
        found = self._rows.get(_key(clip_id, t_s))
        if found is None:
            return FrameLabel(manipulation=None, hands_visible=None,
                              unreadable_reason=NO_ROW_REASON)
        return found
