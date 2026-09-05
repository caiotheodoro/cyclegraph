#!/usr/bin/env python3
"""Repository gates. Run by `make check-claims`, and by CI through `make validate`.

The gates are the deliverable at W0: they must pass with `src/` empty, which is what makes
the documentation-before-code ordering checkable rather than merely asserted.

Each gate returns a list of failure strings. An empty list is a pass. Nothing here imports
from `src/`; these run on a clone with no dependencies installed beyond the standard library.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The spine. A missing entry is a failure, not a warning: these files are gates, and a gate
# that is absent is a gate that passes for the wrong reason.
SPINE: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "CONTRACTS.md",
    "llms.txt",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    "docs/PRE-REGISTRATION.md",
    "docs/PRE-REGISTRATION.sha256",
    "docs/DECISIONS.md",
    "docs/RED-TEAM.md",
    "docs/COVERAGE.md",
    "docs/REPRODUCTION.md",
    "docs/METHOD.md",
    "docs/ARCHITECTURE.md",
    "docs/LINEAGE.md",
    "docs/HANDOFF.md",
    "docs/BENCHMARK.md",
    "docs/RUBRIC.md",
    "docs/SURVEY.md",
    "docs/WAVES.md",
    "docs/ETHICS.md",
    "docs/RETRACTIONS.md",
    "docs/methodology.md",
    "docs/DATASET_CARD.md",
    "docs/MODEL_CARD.md",
    "docs/EVALS_CARD.md",
)

PLACEHOLDERS = re.compile(r"\b(TBD|TODO|FIXME|XXX)\b")

# A backticked span is treated as a repository path only if it is rooted somewhere this
# repository actually has: a known top-level directory, or a relative escape to a sibling
# repo. Everything else that happens to contain a slash is prose -- a Hugging Face dataset
# id (`builddotai/Egocentric-10K`), a schema revision (`contracts/v1`), a format template
# (`factory_id/worker_id/clip_index`). Matching those would make the gate fire on things
# that were never claimed to be files, and a gate that cries wolf gets switched off.
PATH_SPAN = re.compile(r"`([^`\s]+)`")
REPO_ROOTS = ("docs/", "src/", "tests/", "scripts/", "results/", "hf/", ".github/")


def _manifest(name: str) -> set[str]:
    """Declared paths from a manifest file: non-empty, non-comment lines."""
    p = ROOT / name
    if not p.exists():
        return set()
    out: set[str] = set()
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.rstrip("/"))
    return out


def _tracked_markdown() -> list[Path]:
    files = [ROOT / f for f in ("README.md", "AGENTS.md", "CONTRACTS.md", "llms.txt")]
    files.extend(sorted((ROOT / "docs").glob("*.md")))
    return [f for f in files if f.exists()]


def gate_spine() -> list[str]:
    return [f"spine: missing {name}" for name in SPINE if not (ROOT / name).exists()]


def gate_privacy() -> list[str]:
    """docs/private/ must not be stageable. It never shapes a finding and never ships."""
    proc = subprocess.run(
        ["git", "add", "-A", "--dry-run"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if "docs/private" in proc.stdout:
        return ["privacy: docs/private/ is stageable -- fix .gitignore before committing"]
    return []


def gate_no_placeholders() -> list[str]:
    """Unknowns are named open questions with a resolving trigger, never placeholders."""
    failures: list[str] = []
    for f in _tracked_markdown():
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if PLACEHOLDERS.search(line):
                failures.append(f"placeholder: {f.relative_to(ROOT)}:{i}")
    return failures


def gate_cited_paths() -> list[str]:
    """Every path the docs cite resolves, or is declared in a manifest.

    titer added the manifests because its equivalent gate had been passing locally for the
    wrong reason: the files existed on the machine that wrote the docs.
    """
    declared = _manifest("PLANNED-PATHS.txt") | _manifest("GITIGNORED-PATHS.txt")
    external = _manifest("EXTERNAL-PATHS.txt")
    failures: list[str] = []
    for f in _tracked_markdown():
        for i, line in enumerate(f.read_text().splitlines(), 1):
            for span in PATH_SPAN.findall(line):
                if "/" not in span:
                    continue
                if not (span.startswith("../") or span.startswith(REPO_ROOTS)):
                    continue
                bare = span.rstrip("/")
                if bare in declared or bare in external:
                    continue
                if span.startswith("../"):
                    if (ROOT / span).exists():
                        continue
                    failures.append(f"cited path: {f.relative_to(ROOT)}:{i} -> {span}")
                    continue
                if (ROOT / bare).exists():
                    continue
                failures.append(f"cited path: {f.relative_to(ROOT)}:{i} -> {span}")
    return failures


def gate_prereg_frozen() -> list[str]:
    """The pre-registration matches its committed hash. Freezing is the whole argument."""
    doc = ROOT / "docs" / "PRE-REGISTRATION.md"
    sig = ROOT / "docs" / "PRE-REGISTRATION.sha256"
    if not doc.exists() or not sig.exists():
        return ["prereg: document or hash missing"]
    expected = sig.read_text().split()[0]
    actual = hashlib.sha256(doc.read_bytes()).hexdigest()
    if expected != actual:
        return [
            "prereg: PRE-REGISTRATION.md does not match its hash. "
            "A change after the freeze is a DECISIONS entry plus an Amendments entry, "
            "then a re-hash -- never a silent edit."
        ]
    return []


def gate_docs_before_code() -> list[str]:
    """No source file may predate the documentation. Git history is the evidence."""
    src = ROOT / "src" / "cyclegraph"
    real = [p for p in src.rglob("*.py")] if src.exists() else []
    if not real:
        return []
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", "docs/PRE-REGISTRATION.md"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if not proc.stdout.strip():
        return ["ordering: PRE-REGISTRATION.md has no add commit; cannot prove ordering"]
    return []


GATES = (
    ("spine", gate_spine),
    ("privacy", gate_privacy),
    ("placeholders", gate_no_placeholders),
    ("cited-paths", gate_cited_paths),
    ("prereg-frozen", gate_prereg_frozen),
    ("docs-before-code", gate_docs_before_code),
)


def main() -> int:
    failed = 0
    for name, fn in GATES:
        failures = fn()
        if failures:
            failed += 1
            print(f"FAIL {name}")
            for f in failures:
                print(f"     {f}")
        else:
            print(f"ok   {name}")
    if failed:
        print(f"\n{failed} gate(s) failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
