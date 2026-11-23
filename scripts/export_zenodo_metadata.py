"""Write .zenodo.json from the paper itself, so the deposit cannot drift from the PDF.

The description is the paper's abstract with its macros expanded from paper/generated/numbers.tex,
followed by the preprint disclaimer and repository URL. The reference strings are the entries of
paper/cyclegraph.bbl with the LaTeX stripped. The related works are the repository, the Hugging
Face dataset, the blog essay, the Zenodo record of the sibling audit, and every arXiv paper the
bibliography cites.

    python3 scripts/export_zenodo_metadata.py          # rewrite .zenodo.json
    python3 scripts/export_zenodo_metadata.py --check  # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper"
OUT = ROOT / ".zenodo.json"
VERSION = "paper-v2.0"
PUBLICATION_DATE = "2026-09-08"
TITLE = (
    "When Dense Optical Flow Measures the Background Instead of the Hand: "
    "Silent Object Switching Under Egocentric Camera Motion"
)
REPO = "https://github.com/caiotheodoro/cyclegraph"
DATASET = "https://huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain"
ESSAY = "https://caio.theodoro.dev/blog/cyclegraph-flow-is-not-hand-speed"
SIBLING_DOI = "10.5281/zenodo.24453957"
NOTES = (
    f"First published on 8 September 2026 ({ESSAY}). "
    f"This version, {VERSION}, is of 23 November 2026."
)


def _macros() -> dict[str, str]:
    text = (PAPER / "generated" / "numbers.tex").read_text()
    return dict(re.findall(r"\\newcommand\{\\(cg\w+)\}\{(.*)\}", text))


def _detex(s: str, macros: dict[str, str]) -> str:
    s = re.sub(r"\\(cg[A-Za-z]+)\{\}", lambda m: macros[m.group(1)], s)
    s = s.replace("{,}", ",").replace("\\%", "%").replace("\\_", "_")
    s = re.sub(r"\\citep?\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:emph|texttt)\{([^}]*)\}", r"\1", s)
    s = s.replace("---", "\u2014").replace("--", "-").replace("~", " ")
    s = s.replace("``", '"').replace("''", '"').replace("$\\times$", "x")
    s = s.replace("$\\sigma$", "sigma").replace("$\\pm$", "+/-")
    s = re.sub(r"\$([^$]+)\$", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def abstract() -> str:
    tex = (PAPER / "cyclegraph.tex").read_text()
    tex = "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in tex.splitlines())
    body = tex.split("\\begin{abstract}", 1)[1].split("\\end{abstract}", 1)[0]
    return _detex(body.replace("\\noindent", ""), _macros())


_ACCENTS = {"'": "\u0301", '"': "\u0308", "v": "\u030c", "`": "\u0300", "^": "\u0302"}


def _accents(s: str) -> str:
    """{\\'a} -> a with a combining acute, composed; {\\v s} -> s with a caron."""

    def one(m: re.Match[str]) -> str:
        return unicodedata.normalize("NFC", (m.group(2) or m.group(3)) + _ACCENTS[m.group(1)])

    return re.sub(r"\{?\\(['\"v`^])\s*(?:\{(\w)\}|(\w))\}?", one, s)


def references() -> list[str]:
    bbl = (PAPER / "cyclegraph.bbl").read_text()
    refs = []
    for item in re.split(r"\\bibitem\[[^\]]*\]\{[^}]*\}", bbl)[1:]:
        item = item.split("\\end{thebibliography}")[0]
        item = re.sub(r"\\natexlab\{([a-z])\}", r"\1", item)
        item = _accents(item)
        item = re.sub(r"\\newblock", "", item)
        item = re.sub(r"\\penalty0", "", item)
        item = re.sub(r"\\emph\{([^}]*)\}", r"\1", item)
        item = re.sub(r"\{([^{}]*)\}", r"\1", item)
        item = item.replace("\\&", "&").replace("et~al.", "et al.")
        item = item.replace("--", "-").replace("~", " ")
        refs.append(re.sub(r"\s+", " ", item).strip())
    return refs


def arxiv_ids() -> list[str]:
    bib = (PAPER / "refs.bib").read_text()
    ids = re.findall(r"arXiv:(\d{4}\.\d{4,5})", bib)
    return list(dict.fromkeys(ids))


def build() -> dict[str, Any]:
    related: list[dict[str, str]] = [
        {"relation": "isSupplementedBy", "identifier": REPO, "resource_type": "software",
         "scheme": "url"},
        {"relation": "isSupplementedBy", "identifier": DATASET, "resource_type": "dataset",
         "scheme": "url"},
        {"relation": "isSupplementedBy", "identifier": ESSAY, "resource_type": "other",
         "scheme": "url"},
        {"relation": "cites", "identifier": SIBLING_DOI, "resource_type": "publication-preprint",
         "scheme": "doi"},
    ]
    related += [
        {"relation": "cites", "identifier": f"arXiv:{i}",
         "resource_type": "publication-preprint", "scheme": "arxiv"}
        for i in arxiv_ids()
    ]
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "preprint",
        "creators": [
            {"name": "Theodoro, Caio", "affiliation": "Avenza Labs", "orcid": "0009-0005-7343-981X"},
            {"name": "Theodoro, Matheus", "affiliation": "Avenza Labs", "orcid": "0009-0001-4061-4117"},
        ],
        "publication_date": PUBLICATION_DATE,
        "license": "cc-by-4.0",
        "description": abstract() + f" Not peer reviewed. Code and data: {REPO}",
        "notes": NOTES,
        "keywords": [
            "egocentric video",
            "optical flow",
            "hand speed",
            "background capture",
            "hand activity level",
            "occupational ergonomics",
        ],
        "language": "eng",
        "related_identifiers": related,
        "references": references(),
        "version": VERSION,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        return 0 if OUT.exists() and OUT.read_text() == text else 1
    OUT.write_text(text)
    print("wrote .zenodo.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
