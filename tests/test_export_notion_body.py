"""Tests for `scripts/export_notion_body.py`.

The bug this script exists to fix shipped to a published article: `ntn pages create` makes one
Notion block per **source line**, so the repository's 95-character hard wrap became a paragraph
break every ninety characters, and a sentence ending near the margin left a block holding one
word. Nothing in the publish path could see it, because the markdown was valid and every number
in it was right.

So the tests hold the two halves apart: prose must be joined, and everything that is
line-structured -- headings, tables, fenced code, list items -- must not be.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from export_notion_body import strip_title, unwrap  # noqa: E402

ESSAY = ROOT / "writing" / "flow-is-not-hand-speed.md"


def test_a_hard_wrapped_paragraph_becomes_one_line() -> None:
    src = "The project is cyclegraph. It reads a per-frame flag\nas duty cycle, one of two\ninputs.\n"
    assert unwrap(src) == "The project is cyclegraph. It reads a per-frame flag as duty cycle, one of two inputs.\n"


def test_a_blank_line_still_separates_paragraphs() -> None:
    out = unwrap("One sentence\nwrapped here.\n\nA second\nparagraph.\n")
    assert out == "One sentence wrapped here.\n\nA second paragraph.\n"


def test_headings_and_table_rows_are_left_alone() -> None:
    src = "## A heading\nProse under it\nwrapped.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
    out = unwrap(src)
    assert "## A heading" in out.split("\n")
    assert "| a | b |" in out.split("\n")
    assert "| 1 | 2 |" in out.split("\n")
    assert "Prose under it wrapped." in out


def test_fenced_code_survives_its_own_line_breaks() -> None:
    """Joining a code block would destroy it, and the chart block is JSON on its own line."""
    src = '```json\n// cv-chart\n{"type":"bars"}\n```\nProse after\nthe fence.\n'
    out = unwrap(src)
    assert '```json\n// cv-chart\n{"type":"bars"}\n```' in out
    assert "Prose after the fence." in out


def test_list_items_stay_separate_and_absorb_their_continuations() -> None:
    src = "- First item that is\n  wrapped over two lines\n- Second item\n"
    lines = [ln for ln in unwrap(src).split("\n") if ln.strip()]
    assert len(lines) == 2
    assert lines[0] == "- First item that is wrapped over two lines"
    assert lines[1] == "- Second item"


def test_the_h1_is_dropped_because_the_title_property_carries_it() -> None:
    assert strip_title("# A title\n\nBody text.\n") == "Body text.\n"
    assert strip_title("No title here.\n") == "No title here.\n"


def test_the_real_essay_produces_no_continuation_block() -> None:
    """The regression, defined properly.

    A short paragraph is not a bug -- the essay deliberately opens a section with the single
    line "0.18." What shipped was a *continuation* block: the tail of a sentence broken at the
    wrap column, which starts mid-sentence and therefore in lowercase. The raw source is full of
    them by construction; the unwrapped body must have none.
    """
    raw = strip_title(ESSAY.read_text())
    body = unwrap(raw)

    def continuations(text: str) -> list[str]:
        out, in_fence = [], False
        for line in text.split("\n"):
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line.strip():
                continue
            if line.startswith(("#", "|", "-", "`", ">")):
                continue
            if line.lstrip()[:1].islower():
                out.append(line.strip()[:40])
        return out

    assert continuations(raw), "the source must still be hard-wrapped, or this proves nothing"
    assert continuations(body) == [], f"continuation blocks would ship: {continuations(body)}"


def test_a_deliberate_short_paragraph_survives() -> None:
    """`0.18.` is a one-line beat in the essay and must not be joined into its neighbours."""
    body = unwrap(strip_title(ESSAY.read_text()))
    assert "\n0.18.\n" in body


def test_the_real_essay_keeps_its_structure_through_the_unwrap() -> None:
    src = ESSAY.read_text()
    body = unwrap(strip_title(src))
    for pattern in (r"^## ", r"^\|", r"^```", r"^- "):
        assert len(re.findall(pattern, body, re.M)) == len(re.findall(pattern, src, re.M)), pattern
    assert len(re.findall(r"^### ", body, re.M)) == 0
    # and no word is lost or duplicated by the joining
    assert len(body.split()) == len(strip_title(src).split())
