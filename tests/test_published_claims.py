"""Published-claims gate: every structural promise this repository makes is still true.

Each test checks something the documentation says in prose against the artifact it claims to
come from. Ported in spirit from the sibling repos, where the equivalent suite exists because
a claim that nobody re-checks quietly stops being true.

These run offline, with no network and no dependencies beyond the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402


def test_the_spine_the_gate_requires_is_the_spine_on_disk() -> None:
    assert validate.gate_spine() == []


def test_no_placeholder_survives_in_any_tracked_document() -> None:
    assert validate.gate_no_placeholders() == []


def test_every_cited_path_resolves_or_is_declared() -> None:
    assert validate.gate_cited_paths() == []


def test_the_pre_registration_matches_its_committed_hash() -> None:
    assert validate.gate_prereg_frozen() == []


def test_every_amendment_cites_a_reversible_decision_and_quotes_a_real_prior() -> None:
    """A re-hash alone must not be enough to pass the freeze.

    Each amendment block names decisions that exist and carry a reversal clause, a prior
    hash that is a committed version, and quoted sentences that were really in it.
    """
    assert validate.gate_prereg_version() == []


def test_private_material_is_not_stageable() -> None:
    assert validate.gate_privacy() == []


def test_documentation_precedes_every_source_file_by_ancestry() -> None:
    """The ordering claim, checked by git ancestry rather than by timestamps or by `src/`
    happening to be empty."""
    assert validate.gate_docs_before_code() == []


def test_no_identifier_can_reach_a_published_number() -> None:
    assert validate.gate_no_identifier_in_results() == []


def test_the_identifier_pattern_matches_the_corpus_naming() -> None:
    for hit in ("hal for factory_007 was", "cluster over worker_001",
                "factory001_worker001_part00.tar", "Factory_007", "xworker-0012"):
        assert validate.IDENTIFIER.search(hit) is not None, hit
    assert validate.IDENTIFIER.search("cluster_unit factory_id/worker_id") is None
    assert validate.IDENTIFIER.search("85 factories, worker-hours") is None


def test_a_silent_body_edit_is_caught_even_after_a_rehash() -> None:
    """The scenario the gate exists for: change a threshold, re-hash, touch DECISIONS."""
    prior = validate._git("show", f"HEAD:{validate.PREREG}")
    current = (validate.ROOT / validate.PREREG).read_text()
    assert "[2.4, 6.2]" in current
    tampered = current.replace("[2.4, 6.2]", "[1.0, 9.0]")
    quotes = validate.PRIOR_QUOTE.findall(tampered[len(validate._body(tampered)):])
    survivors = validate._prior_sentences(validate._body(prior), quotes)
    missing = [s for s in survivors if s not in validate._squash(validate._body(tampered))]
    assert missing, "a changed H3 sentence must be detected as unquoted"


def test_a_short_sentence_cannot_be_silently_rewritten(tmp_path: Path) -> None:
    """`docs/DECISIONS.md` D041, exploit 1. "Bootstrap B = 10,000." is 21 characters and was
    editable while the gate's floor was 25. It is a live estimation parameter."""
    body = validate._body((validate.ROOT / validate.PREREG).read_text())
    sentences = validate._body_sentences(body)
    assert any("Bootstrap B = 10,000." in s for s in sentences), (
        "a 21-character pre-registered parameter must be a checked sentence")


def test_the_reporting_floor_closure_is_a_checked_sentence() -> None:
    """D041, exploit 2. "Nothing else." is 13 characters and is what stops any reporting unit
    below the D019 floor from being published."""
    body = validate._body((validate.ROOT / validate.PREREG).read_text())
    assert "Nothing else." in validate._body_sentences(body)


def test_the_banner_paragraph_prose_is_checked_not_skipped() -> None:
    """D041's third mechanism. The `**Amended:**` paragraph runs on into substantive prose
    about the amendment discipline; skipping the whole paragraph left that prose editable, and
    a real v1.2.0 change hid there for two versions."""
    body = validate._body((validate.ROOT / validate.PREREG).read_text())
    sentences = validate._body_sentences(body)
    assert any("refuses any change to the frozen body" in s for s in sentences)
    assert not any(s.startswith("**Version:**") for s in sentences)


def test_the_grandfathered_addition_count_is_pinned(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """D041. Pre-v1.5.0 history is exempt from the additions rule but frozen: the gate carries
    the exact count so that history cannot be edited under cover of the exemption.

    Asserting the constant equals its own literal is a tautology -- it cannot fail for the
    reason the test exists. What has to be true is that the count is *load-bearing*: move it,
    and the gate must notice. That is checked by moving it."""
    assert validate._ADDITIONS_RULE_FROM == (1, 5, 0)
    assert validate.gate_prereg_version() == []

    for wrong in (validate._GRANDFATHERED_ADDITIONS - 1,
                  validate._GRANDFATHERED_ADDITIONS + 1):
        monkeypatch.setattr(validate, "_GRANDFATHERED_ADDITIONS", wrong)
        failures = validate.gate_prereg_version()
        assert failures, f"the gate accepted a grandfathered count of {wrong}"
        assert any("grandfathered" in f or "unquoted additions" in f for f in failures)
