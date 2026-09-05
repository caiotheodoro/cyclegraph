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


def test_private_material_is_not_stageable() -> None:
    assert validate.gate_privacy() == []


def test_the_gates_pass_with_no_source_code_at_all() -> None:
    """W0's actual claim: the gate set works on documentation alone.

    If this test needed `src/` to exist, the documentation-before-code ordering would be
    unverifiable, and the ordering is the whole reason the ordering rule exists.
    """
    src = ROOT / "src" / "cyclegraph"
    modules = list(src.rglob("*.py")) if src.exists() else []
    assert modules == [], "W0 is documentation only; a .py under src/ means W2 has started"
    assert validate.gate_docs_before_code() == []
