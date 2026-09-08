"""Turn a hard-wrapped repository essay into the body the Notion CMS expects.

`writing/*.md` is hard-wrapped at about 95 characters, which is right for a file that lives in
git and gets reviewed as a diff. It is wrong for `ntn pages create`, which treats **every source
line as its own block**: a paragraph wrapped over four lines becomes four Notion paragraphs, and
a sentence ending near the margin leaves an orphan block holding one word. The published article
then has a paragraph break every ninety characters.

So the wrap is undone here rather than removed from the source. Paragraphs are joined into one
line each; headings, table rows, list items and fenced code survive untouched, because each of
those is line-structured and joining them would destroy it.

The H1 is dropped: the Blog data source's `Title` property carries it, and leaving it in the body
prints the title twice.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FENCE = re.compile(r"^```")
HEADING = re.compile(r"^#{1,6}\s")
TABLE_ROW = re.compile(r"^\s*\|")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]\s|\d+\.\s)")
BLOCKQUOTE = re.compile(r"^\s*>")


def unwrap(markdown: str) -> str:
    """Join hard-wrapped prose into one line per block, leaving line-structured blocks alone."""
    out: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        if buffer:
            out.append(" ".join(part.strip() for part in buffer))
            buffer.clear()

    for line in markdown.split("\n"):
        if FENCE.match(line):
            flush()
            out.append(line)
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(line)          # code is verbatim, including its own line breaks
            continue
        if not line.strip():
            flush()
            out.append("")
            continue
        if HEADING.match(line) or TABLE_ROW.match(line):
            flush()
            out.append(line.rstrip())
            continue
        if LIST_ITEM.match(line) or BLOCKQUOTE.match(line):
            # A new item ends the previous one; its own continuation lines fold into it below.
            flush()
            buffer.append(line.rstrip())
            continue
        buffer.append(line)

    flush()
    # Collapse runs of blank lines, which the joining can leave behind.
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def strip_title(markdown: str) -> str:
    lines = markdown.split("\n")
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip("\n")
    return markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="the repository essay, e.g. writing/<name>.md")
    parser.add_argument("--out", required=True, help="where to write the Notion body")
    parser.add_argument("--keep-title", action="store_true",
                        help="keep the H1; by default it is dropped for the Title property")
    parser.add_argument("--insert-after", default=None,
                        help="a heading line; a file given by --insert is placed before it")
    parser.add_argument("--insert", default=None, help="markdown to splice in, e.g. a TL;DR table")
    args = parser.parse_args(argv)

    text = Path(args.source).read_text()
    if not args.keep_title:
        text = strip_title(text)
    if args.insert and args.insert_after:
        block = Path(args.insert).read_text().strip()
        idx = text.index(args.insert_after)
        text = text[:idx] + block + "\n\n" + text[idx:]

    body = unwrap(text)
    Path(args.out).write_text(body)

    blocks = sum(1 for ln in body.split("\n") if ln.strip())
    print(f"wrote {args.out}  ({len(body.split())} words, {blocks} non-empty lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
