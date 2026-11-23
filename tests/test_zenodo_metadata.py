"""`.zenodo.json` and `CITATION.cff` are generated from, or held to, the paper."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import export_zenodo_metadata as ezm  # noqa: E402


def test_zenodo_json_is_what_the_paper_generates() -> None:
    assert json.loads((ROOT / ".zenodo.json").read_text()) == ezm.build()


def test_the_deposit_carries_the_owner_the_licence_and_the_limits() -> None:
    z = json.loads((ROOT / ".zenodo.json").read_text())
    assert z["creators"] == [
        {"name": "Theodoro, Caio", "affiliation": "Avenza Labs", "orcid": "0009-0005-7343-981X"},
        {"name": "Theodoro, Matheus", "affiliation": "Avenza Labs", "orcid": "0009-0001-4061-4117"},
    ]
    assert z["license"] == "cc-by-4.0"
    assert z["publication_date"] == "2026-09-08"
    assert z["version"] == "paper-v2.0"
    assert "8 September 2026" in z["notes"]
    assert "23 November 2026" in z["notes"]
    assert "Not peer reviewed" in z["description"]
    assert "no corpus exposure measurement" in z["description"]
    assert "\\" not in z["description"] and "cg" not in re.findall(r"\\cg\w+", z["description"])


def test_every_reference_is_present_and_readable() -> None:
    z = json.loads((ROOT / ".zenodo.json").read_text())
    bib = (ROOT / "paper" / "refs.bib").read_text()
    assert len(z["references"]) == len(re.findall(r"^@\w+\{", bib, re.M))
    for ref in z["references"]:
        assert "\\" not in ref and "{" not in ref and "}" not in ref, ref
        assert re.search(r"\b(19|20)\d\d[a-z]?\b", ref), ref


def test_every_arxiv_paper_cited_is_a_related_work() -> None:
    z = json.loads((ROOT / ".zenodo.json").read_text())
    cited = {r["identifier"] for r in z["related_identifiers"] if r["relation"] == "cites"}
    for i in ezm.arxiv_ids():
        assert f"arXiv:{i}" in cited


def test_citation_cff_names_the_same_paper() -> None:
    cff = (ROOT / "CITATION.cff").read_text()
    z = json.loads((ROOT / ".zenodo.json").read_text())
    assert z["title"] in cff
    assert "0009-0005-7343-981X" in cff
