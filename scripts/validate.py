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
PREREG = "docs/PRE-REGISTRATION.md"
PREREG_SHA = "docs/PRE-REGISTRATION.sha256"
DECISIONS = "docs/DECISIONS.md"

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
    PREREG,
    PREREG_SHA,
    DECISIONS,
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

# An identifier that must never reach a published number. Matches the corpus's own naming.
IDENTIFIER = re.compile(r"\b(factory_\d+|worker_\d+)\b")

VERSION_LINE = re.compile(r"^\*\*Version:\*\*\s+(\d+)\.(\d+)\.(\d+)\s*$", re.M)
AMENDMENT_HEADING = re.compile(
    r"^### v(\d+)\.(\d+)\.(\d+) — (.+?) · prior hash ([0-9a-f]{64})\s*$", re.M
)
DECISION_REF = re.compile(r"\bD(\d{3})\b")
PRIOR_QUOTE = re.compile(r'Prior:\s+"(.+?)"\s+Now:', re.S)
DECISION_HEADING = re.compile(r"^## (D\d{3}) — ", re.M)


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return proc.stdout


def _git_ok(*args: str) -> bool:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    return proc.returncode == 0


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


def _squash(s: str) -> str:
    return " ".join(s.split())


def gate_spine() -> list[str]:
    return [f"spine: missing {name}" for name in SPINE if not (ROOT / name).exists()]


def gate_privacy() -> list[str]:
    """docs/private/ must not be stageable. It never shapes a finding and never ships."""
    if "docs/private" in _git("add", "-A", "--dry-run"):
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
                bare = span.split("#", 1)[0].rstrip("/")
                if bare in declared or bare in external:
                    continue
                if (ROOT / bare).exists():
                    continue
                failures.append(f"cited path: {f.relative_to(ROOT)}:{i} -> {span}")
    return failures


def gate_prereg_frozen() -> list[str]:
    """The pre-registration matches its committed hash. Freezing is the whole argument."""
    doc = ROOT / PREREG
    sig = ROOT / PREREG_SHA
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


def _historical_versions() -> dict[str, str]:
    """sha256 -> commit for every committed version of the pre-registration."""
    out: dict[str, str] = {}
    for commit in _git("log", "--format=%H", "--", PREREG).split():
        blob = _git("show", f"{commit}:{PREREG}")
        if blob:
            out[hashlib.sha256(blob.encode()).hexdigest()] = commit
    return out


def gate_prereg_version() -> list[str]:
    """Every amendment is a decision with a reversal clause, quoting a real prior version.

    A re-hash on its own would let the frozen-hash gate pass for the wrong reason. This
    gate ties each amendment block to (a) a decision entry that exists and carries
    `**Reverses if:**`, (b) a prior version whose sha256 is in git history, and (c) quoted
    prior sentences that really were in that version. It also refuses any commit that
    touched the pre-registration without touching its hash and the decisions log.
    """
    doc = ROOT / PREREG
    dec = ROOT / DECISIONS
    if not doc.exists() or not dec.exists():
        return ["prereg-version: document or decisions missing"]
    text = doc.read_text()
    m = VERSION_LINE.search(text)
    if not m:
        return ["prereg-version: no **Version:** line"]
    minor = int(m.group(2))
    blocks = list(AMENDMENT_HEADING.finditer(text))
    failures: list[str] = []
    if len(blocks) != minor:
        failures.append(
            f"prereg-version: {len(blocks)} amendment block(s) but version minor is {minor}"
        )
    decisions_text = dec.read_text()
    entries: dict[str, str] = {}
    heads = list(DECISION_HEADING.finditer(decisions_text))
    for j, h in enumerate(heads):
        end = heads[j + 1].start() if j + 1 < len(heads) else len(decisions_text)
        entries[h.group(1)] = decisions_text[h.start() : end]
    history = _historical_versions()
    for j, b in enumerate(blocks):
        end = blocks[j + 1].start() if j + 1 < len(blocks) else len(text)
        body = text[b.start() : end]
        for ref in sorted(set(DECISION_REF.findall(b.group(4)) + DECISION_REF.findall(body))):
            key = f"D{ref}"
            entry = entries.get(key)
            if entry is None:
                failures.append(f"prereg-version: amendment cites {key}, not in DECISIONS.md")
            elif "**Reverses if:**" not in entry:
                failures.append(f"prereg-version: {key} has no reversal clause")
        prior_commit = history.get(b.group(5))
        if prior_commit is None:
            failures.append(
                f"prereg-version: prior hash {b.group(5)[:12]} matches no committed version"
            )
            continue
        prior = _squash(_git("show", f"{prior_commit}:{PREREG}"))
        for q in PRIOR_QUOTE.findall(body):
            if _squash(q) not in prior:
                failures.append(f"prereg-version: quoted prior text not in prior version: {q[:60]!r}")
    commits = _git("log", "--format=%H", "--", PREREG).split()
    if commits:
        for commit in commits[:-1]:  # everything after the add commit
            touched = set(_git("show", "--name-only", "--format=", commit).split())
            missing = {PREREG_SHA, DECISIONS} - touched
            if missing:
                failures.append(
                    f"prereg-version: commit {commit[:10]} changed {PREREG} "
                    f"without {', '.join(sorted(missing))}"
                )
    return failures


def gate_docs_before_code() -> list[str]:
    """No source file may predate the documentation. Ancestry, not timestamps.

    Timestamps are rewritten by rebase and squash. The check is that the commit adding the
    pre-registration is an ancestor of the commit adding every `src/**/*.py`, and is not the
    same commit.
    """
    src_files = [p for p in _git("ls-files", "src").split() if p.endswith(".py")]
    if not src_files:
        return []
    prereg_adds = _git("log", "--diff-filter=A", "--format=%H", "--", PREREG).split()
    if not prereg_adds:
        return ["ordering: PRE-REGISTRATION.md has no add commit; cannot prove ordering"]
    prereg_add = prereg_adds[-1]
    failures: list[str] = []
    for path in src_files:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", path).split()
        if not adds:
            failures.append(f"ordering: {path} is tracked but has no add commit (uncommitted?)")
            continue
        src_add = adds[-1]
        if src_add == prereg_add:
            failures.append(f"ordering: {path} was added in the same commit as {PREREG}")
        elif not _git_ok("merge-base", "--is-ancestor", prereg_add, src_add):
            failures.append(f"ordering: {PREREG}'s add commit is not an ancestor of {path}'s")
    return failures


def gate_no_identifier_in_results() -> list[str]:
    """No factory or worker identifier in anything that could be published."""
    tracked = _git("ls-files", "results", "MEASUREMENT_CARD.json").split()
    failures: list[str] = []
    for rel in tracked:
        p = ROOT / rel
        if not p.is_file() or p.suffix not in {".json", ".csv", ".md", ".txt", ".yaml"}:
            continue
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if IDENTIFIER.search(line):
                failures.append(f"identifier: {rel}:{i}")
                break
    return failures


GATES = (
    ("spine", gate_spine),
    ("privacy", gate_privacy),
    ("placeholders", gate_no_placeholders),
    ("cited-paths", gate_cited_paths),
    ("prereg-frozen", gate_prereg_frozen),
    ("prereg-version", gate_prereg_version),
    ("docs-before-code", gate_docs_before_code),
    ("no-identifier-in-results", gate_no_identifier_in_results),
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
