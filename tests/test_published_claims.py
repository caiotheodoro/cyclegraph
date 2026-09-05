"""Published-claims gate: every structural promise this repository makes is still true.

Each test checks something the documentation says in prose against the artifact it claims to
come from. Ported in spirit from the sibling repos, where the equivalent suite exists because
a claim that nobody re-checks quietly stops being true.

These run offline, with no network and no dependencies beyond the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    assert validate.IDENTIFIER.search("hal for factory_007 was") is not None
    assert validate.IDENTIFIER.search("cluster over worker_001") is not None
    assert validate.IDENTIFIER.search("cluster_unit factory_id/worker_id") is None
