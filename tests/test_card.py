"""Tests for `src/cyclegraph/card/build.py`.

The card is the artifact a reader is most likely to take at face value, so these test the
three properties that protect it: it is generated, its verdict is a consequence, and a
pilot-gated claim never carries a value.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cyclegraph.card.build import ClaimSource, build_card, known_gaps, read_claim

ROOT = Path(__file__).resolve().parent.parent
GENERATED = datetime(2026, 9, 5, tzinfo=timezone.utc)

CLAIMS = (
    ClaimSource("H3", "the corpus median HAL is plausible", "results/h3_plausibility.json"),
    ClaimSource("H1", "duty cycle is a property of the clip", "results/pilot/h1.json"),
)


def _card(tmp_path: Path, **kw: object):  # type: ignore[no-untyped-def]
    return build_card(CLAIMS, results_root=tmp_path,
                      coverage_md=ROOT / "docs" / "COVERAGE.md",
                      corpus_rev="3e5f87c8", generated=GENERATED, **kw)  # type: ignore[arg-type]


def test_the_gaps_come_from_the_coverage_table_not_from_this_file() -> None:
    """A gap list written as a literal would drift from the document it claims to summarise,
    which is the transcription problem one level up."""
    gaps = known_gaps(ROOT / "docs" / "COVERAGE.md")
    assert "Normalized Peak Force (0–10)" in gaps
    assert len(gaps) >= 4


def test_a_coverage_table_with_no_gaps_raises_rather_than_reading_as_complete(
    tmp_path: Path,
) -> None:
    """An empty gap list would render as a project with nothing missing, which is the one
    thing this card must never say by accident."""
    empty = tmp_path / "COVERAGE.md"
    empty.write_text("# Coverage\n\n| Input | Status | Why |\n|---|---|---|\n")
    with pytest.raises(ValueError, match="nothing missing"):
        known_gaps(empty)


def test_a_missing_result_file_is_untested_and_not_an_error(tmp_path: Path) -> None:
    """Most of this card is untested for most of the project's life, and that is its normal
    state rather than a failure."""
    claim = read_claim(CLAIMS[0], tmp_path)
    assert claim.status == "UNTESTED" and claim.interval is None


def test_the_verdict_is_a_consequence_of_the_gaps_not_a_setting(tmp_path: Path) -> None:
    """Even with every claim holding, an open coverage gap keeps the verdict NOT_VERIFIED."""
    (tmp_path / "pilot").mkdir()
    (tmp_path / "h3_plausibility.json").write_text(json.dumps({"status": "HOLDS"}))
    (tmp_path / "pilot" / "h1.json").write_text(json.dumps({"status": "HOLDS"}))
    card = _card(tmp_path)
    assert all(c.status == "HOLDS" for c in card.claims)
    assert card.known_gaps
    assert card.verdict == "NOT_VERIFIED"


def test_a_pilot_gated_claim_never_carries_an_interval(tmp_path: Path) -> None:
    """D018: the pilot factory is nameable, so an H1 figure is a per-factory number. The
    reader gets the verdict and not the value, even when the file offers one."""
    (tmp_path / "pilot").mkdir()
    (tmp_path / "pilot" / "h1.json").write_text(
        json.dumps({"status": "HOLDS", "interval": [0.03, 0.04]}))
    (tmp_path / "h3_plausibility.json").write_text(
        json.dumps({"status": "HOLDS", "interval": [3.9, 4.4]}))
    card = _card(tmp_path)
    pilot = next(c for c in card.claims if c.id == "H1")
    corpus = next(c for c in card.claims if c.id == "H3")
    assert pilot.pilot_gate and pilot.interval is None
    assert not corpus.pilot_gate and corpus.interval == [3.9, 4.4]


def test_an_unknown_status_in_a_result_file_raises(tmp_path: Path) -> None:
    (tmp_path / "h3_plausibility.json").write_text(json.dumps({"status": "PASSED"}))
    with pytest.raises(ValueError, match="unknown claim status"):
        read_claim(CLAIMS[0], tmp_path)


def test_the_card_carries_no_identifier(tmp_path: Path) -> None:
    card = _card(tmp_path)
    dumped = card.model_dump_json()
    assert "factory_0" not in dumped and "worker_0" not in dumped


def test_the_committed_card_is_not_verified_and_says_why() -> None:
    """The repository's own card. Its verdict is NOT_VERIFIED by construction, and the wave
    that produces it exits nonzero on purpose."""
    card = json.loads((ROOT / "MEASUREMENT_CARD.json").read_text())
    assert card["verdict"] == "NOT_VERIFIED"
    assert card["known_gaps"]
    assert all(c["interval"] is None for c in card["claims"] if c["pilot_gate"])
