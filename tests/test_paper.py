"""The short paper's numbers, citations and rendered text must trace to the repository.

paper/cyclegraph.tex holds no artifact number. Each is a macro that
scripts/export_paper_tables.py writes from results/*.json, the measurement card or a code
constant. These tests fail when

  * a generated file differs from what the script writes now (a stale table);
  * the prose contains a bare number that is not on a short, justified allowlist;
  * a citation key has no bibliography entry, or an entry is never cited;
  * a macro is used and not defined, or a backslash was doubled so that LaTeX silently
    swallowed a command (vernier's paper lost an abstract to this while its build and CI
    stayed green);
  * the committed PDF's extracted text has lost a number, a citation, a table or a figure.

The PDF test needs `pdftotext` and skips without it. The rest are stdlib only.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import export_paper_tables as ept  # noqa: E402

PAPER = ROOT / "paper"
TEX = PAPER / "cyclegraph.tex"
BIB = PAPER / "refs.bib"
PDF = PAPER / "cyclegraph.pdf"
GEN = PAPER / "generated"
PREREG = ROOT / "docs" / "PRE-REGISTRATION.md"

MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
          "November|December")


def _read_json(name: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((ROOT / name).read_text())
    return out


def _macros() -> dict[str, str]:
    text = (GEN / "numbers.tex").read_text()
    return dict(re.findall(r"\\newcommand\{\\(cg\w+)\}\{(.*)\}", text))


def _strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def _prose(text: str) -> str:
    """The tex with everything that is not a claim removed: comments, macro calls (their value
    is checked at the source), citations, labels, file names, URLs, and the generated inputs."""
    t = _strip_comments(text)
    t = re.sub(r"\\cg[A-Za-z]+\{\}", " ", t)
    t = re.sub(r"\\(?:citep|citet|cite|ref|label|input|bibliography|bibliographystyle|url)"
               r"(?:\[[^\]]*\])?\{[^}]*\}", " ", t)
    t = re.sub(r"\\texttt\{(?:[^{}]|\{[^{}]*\})*\}", " ", t)
    t = re.sub(r"\\(?:usepackage|usetikzlibrary|usepgfplotslibrary|pgfplotsset|documentclass"
               r"|setlength)(?:\[[^\]]*\])?\{[^}]*\}(?:\{[^}]*\})?", " ", t)
    t = re.sub(r"\\resizebox\{[^}]*\}\{[^}]*\}", " ", t)
    t = re.sub(rf"\b\d{{1,2}} (?:{MONTHS}) \d{{4}}\b", " ", t)       # dates
    t = t.replace("{,}", ",")
    # Names that contain digits: licences and products, not measurements.
    for name in ("Apache-2.0", "CC BY 4.0", "gemini-2.5-flash", "EPIC-KITCHENS-100", "SHA-256"):
        t = t.replace(name, " ")
    return t


def _numbers(text: str) -> list[str]:
    return re.findall(r"(?<![\w.\\])\d+(?:[.,]\d+)*(?![\w])", text)


def _allowed_numbers() -> set[str]:
    """Numbers the prose may state without a macro, each with the reason it is safe."""
    allowed: set[str] = set()
    # Structural integers: section-sized counts, the 0 to 10 HAL scale, the two-arm design.
    allowed |= {str(i) for i in range(0, 13)}
    # Years of citations and of the standard's table edition.
    allowed |= {"2001", "2013", "2026"}
    # Decode sizes: they must be frames the seeded sweep actually used.
    seeds = _read_json("results/flow_gain_seeds.json")
    sizes = {n for a in seeds["farneback_by_width"].values() for n in a["frame_size"]}
    assert sizes == {480, 270, 960, 540, 1440, 810, 1920, 1080}
    allowed |= {str(n) for n in sizes}
    # The equation's constants, from the code that implements it.
    from cyclegraph.exposure import hal
    allowed |= {f"{abs(hal._A_B0)}", f"{hal._A_BD}", f"{hal._A_BS}"}
    # The two thresholds the harness itself uses.
    from cyclegraph.signal import gain
    allowed |= {str(gain.KNEE_GAIN), str(gain.COLLAPSE_GAIN)}
    # Pre-registered literals: each must be in the frozen text.
    prereg = PREREG.read_text()
    for literal, needle in (("40,000", "40,000"), ("200", "200 clips"), ("50", "50 workers"),
                            ("40", "40%"), ("4", "4 Hz"), ("5", "5 factories")):
        assert needle in prereg, f"{needle!r} is not in the frozen pre-registration"
        allowed.add(literal)
    # The band the budget is quoted across: the keys of the committed floor file.
    floor = _read_json("results/a14_translation_floor.json")
    assert {"400.0", "800.0"} <= set(floor["hal_budget_mm_s_at_assumed_median"])
    allowed |= {"400", "800"}
    # Rotation rate used as the worked example: a row of the committed table.
    assert 10.0 in {r["rotation_deg_per_s"] for r in floor["rotation_only_corpus_lens"]}
    return allowed


# ---------------------------------------------------------------------------------------------
# generated files and the numbers


def test_generated_files_are_current() -> None:
    files = ept.build()
    stale = [n for n, t in files.items()
             if not (GEN / n).exists() or (GEN / n).read_text() != t]
    assert stale == [], f"run scripts/export_paper_tables.py: {stale}"
    extra = {p.name for p in GEN.iterdir()} - set(files)
    assert extra == set(), f"files in paper/generated/ that nothing writes: {extra}"


def test_the_prose_states_no_number_that_is_not_a_macro_or_allowlisted() -> None:
    bad = sorted({n for n in _numbers(_prose(TEX.read_text())) if n not in _allowed_numbers()})
    assert bad == [], f"bare numbers in the paper's prose; make them macros: {bad}"


def test_the_allowlist_can_fail() -> None:
    """A gate that cannot fail is the first failure shape in docs/HANDOFF.md."""
    planted = _prose(TEX.read_text()) + " and the gain was 0.77 here"
    assert "0.77" in {n for n in _numbers(planted) if n not in _allowed_numbers()}


def test_every_macro_used_is_defined() -> None:
    used = set(re.findall(r"\\(cg[A-Za-z]+)\{\}", _strip_comments(TEX.read_text())))
    for f in GEN.glob("*.tex"):
        used |= set(re.findall(r"\\(cg[A-Za-z]+)\{\}", f.read_text()))
    missing = used - set(_macros())
    assert missing == set(), f"macros used but not defined: {sorted(missing)}"


def test_no_doubled_backslash_has_eaten_a_command() -> None:
    """vernier's paper once read `\\\\citep` and lost its abstract's citations and a result's
    intervals; the build was green. A double backslash directly before a letter is never what
    the author meant outside a tabular, and the prose has no tabular."""
    prose = _strip_comments(TEX.read_text())
    hits = re.findall(r"\\\\[A-Za-z]+", prose)
    assert hits == [], f"doubled backslashes in cyclegraph.tex: {hits[:5]}"


def test_seed_eleven_is_the_published_curve() -> None:
    """The seed arm is only a spread around the published number if it reproduces it."""
    seeds = _read_json("results/flow_gain_seeds.json")
    published = _read_json("results/flow_gain_by_resolution.json")
    for scale in published["scales"]:
        w = str(scale["frame_size"][0])
        got = next(p for p in seeds["farneback_by_width"][w]["per_seed"]
                   if p["seed"] == seeds["published_seed"])["gains"]
        assert got == [r["gain"] for r in scale["rows"]], w


def test_the_cpu_raft_arm_reproduces_the_published_gpu_curve() -> None:
    seeds = _read_json("results/flow_gain_seeds.json")
    raft = _read_json("results/flow_gain_raft.json")
    pub = next(s for s in raft["scales"] if s["frame_size"][0] == 960)
    got = next(p for p in seeds["raft"]["by_width"]["960"]["per_seed"]
               if p["seed"] == seeds["published_seed"])["gains"]
    assert max(abs(a - b["gain"]) for a, b in zip(got, pub["rows"])) < 5e-3


def test_the_shelf_is_the_depth_ratio_for_both_estimators() -> None:
    """The paper's mechanism claim. If a rerun moved the shelf off the ratio, the sentence
    that explains it would be wrong while every number stayed right."""
    seeds = _read_json("results/flow_gain_seeds.json")
    ratio = seeds["floor_ratio_expected"]
    far = seeds["farneback_by_width"]["960"]["floor_gain"]["mean"]
    raft = seeds["raft"]["by_width"]["960"]["floor_gain"]["mean"]
    assert abs(far - ratio) < 0.03
    assert abs(raft - ratio) < 0.03


def test_the_published_seed_is_not_the_mean_and_the_paper_says_so() -> None:
    """The single seed that was published reads 0.99 where the mean is 0.88. If the two ever
    agreed, the paragraph saying they do not would be stale."""
    m = _macros()
    assert m["cgGainAtKneePub"] != m["cgGainAtKneeMean"]


# ---------------------------------------------------------------------------------------------
# citations


def _bib_keys() -> set[str]:
    return set(re.findall(r"^@\w+\{([^,\s]+),", BIB.read_text(), re.M))


def _cited_keys() -> set[str]:
    keys: set[str] = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]*)\}", _strip_comments(TEX.read_text())):
        keys |= {k.strip() for k in group.split(",")}
    return keys


def test_every_citation_has_an_entry_and_every_entry_is_cited() -> None:
    assert _cited_keys() - _bib_keys() == set()
    assert _bib_keys() - _cited_keys() == set(), "an uncited reference is a reference nobody read"


def test_the_bbl_matches_the_bib() -> None:
    bbl = (PAPER / "cyclegraph.bbl").read_text()
    assert len(re.findall(r"\\bibitem", bbl)) == len(_bib_keys())


# ---------------------------------------------------------------------------------------------
# what the paper is allowed to claim


def test_the_abstract_and_first_section_state_the_limits() -> None:
    text = _strip_comments(TEX.read_text())
    abstract = text.split("\\begin{abstract}", 1)[1].split("\\end{abstract}", 1)[0]
    assert "Not peer reviewed" in abstract
    assert "no\nergonomist" in abstract or "no ergonomist" in abstract
    assert "makes no claim about the corpus" in abstract
    first = text.split("\\section{What this note does not show}", 1)[1].split("\\section", 1)[0]
    for phrase in ("No ergonomist", "no agreement statistic", "has not run"):
        assert phrase in first, phrase


def test_the_title_and_abstract_do_not_claim_a_corpus_result() -> None:
    text = TEX.read_text()
    head = text.split("\\maketitle", 1)[0]
    for banned in ("we measure", "we show that the corpus", "accurately", "validated"):
        assert banned not in head.lower(), banned


def test_no_word_about_the_vendor_that_the_artifacts_cannot_support() -> None:
    text = _strip_comments(TEX.read_text()).lower()
    for word in ("misleading", "inflated", "deceptive", "fraud", "dishonest", "lied", "overstat"):
        assert re.search(rf"\b{word}", text) is None, word


def test_the_pre_registration_hash_the_paper_relies_on_is_the_committed_one() -> None:
    import hashlib
    digest = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    pinned = (ROOT / "docs" / "PRE-REGISTRATION.sha256").read_text().split()[0]
    assert digest == pinned


def test_the_vendor_statements_are_the_ones_on_file() -> None:
    v = _read_json("results/vendor_claim.json")
    assert v["frames_sampled"] == 10000
    assert v["published_percent"]["egocentric_10k"] == pytest.approx(91.66)
    assert "actively manipulating" in v["prompt_task"]
    assert v["labeller"] == "gemini-2.5-flash"


# ---------------------------------------------------------------------------------------------
# the rendered PDF


def _pdf_text() -> str:
    out = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True,
                         text=True, check=True)
    return out.stdout


needs_pdf = pytest.mark.skipif(
    shutil.which("pdftotext") is None or not PDF.exists(),
    reason="pdftotext or the committed PDF is missing")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u2019", "'").replace("\u2013", "-")
                  .replace("\u2212", "-").replace("\ufb01", "fi").replace("\u00ad", ""))


@needs_pdf
def test_the_pdf_has_no_unresolved_reference_or_empty_citation() -> None:
    text = _pdf_text()
    assert "??" not in text
    assert "[?]" not in text
    assert "(?)" not in text
    assert "Table ?" not in text


@needs_pdf
def test_the_pdf_abstract_survived_the_build() -> None:
    flat = _flat(_pdf_text())
    abstract = _flat(_strip_comments(TEX.read_text()).split("\\begin{abstract}", 1)[1]
                     .split("\\end{abstract}", 1)[0])
    # the abstract's first and last sentences, with macros stripped, are in the PDF
    assert "Build AI publishes that" in flat
    assert "Not peer reviewed." in flat
    assert "makes no claim about the corpus" in flat
    assert abstract.count("\\cg") > 5


@needs_pdf
def test_every_macro_used_in_the_prose_shows_up_with_its_value_in_the_pdf() -> None:
    flat = _flat(_pdf_text())
    macros = _macros()
    used = set(re.findall(r"\\(cg[A-Za-z]+)\{\}", _strip_comments(TEX.read_text())))
    missing = []
    for name in sorted(used):
        value = _flat(macros[name].replace("\\_", "_").replace("{,}", ","))
        if value not in flat:
            missing.append((name, value))
    assert missing == [], f"numbers the PDF does not show: {missing}"


@needs_pdf
def test_every_citation_is_a_resolved_number_and_every_float_is_present() -> None:
    flat = _flat(_pdf_text())
    n_refs = len(_bib_keys())
    assert f"[{n_refs}]" in flat, "the last reference is not in the PDF"
    for label in ("Figure 1", "Figure 2", "Figure 3", "Table 1", "Table 2", "Table 3",
                  "Table 4", "Table 5"):
        assert f"{label}:" in flat, f"{label} has no caption in the PDF"
    assert re.search(r"\[\d+(?:[,\u2013-]\d+)*\]", flat), "no numeric citation survived"


@needs_pdf
def test_the_pdf_is_within_the_length_the_note_was_scoped_to() -> None:
    out = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", out.stdout).group(1))  # type: ignore[union-attr]
    assert 6 <= pages <= 14


# ---------------------------------------------------------------------------------------------
# the documents that carry the correction quote the same artifact


def test_the_correction_in_the_card_and_the_retraction_log_quotes_the_seed_file() -> None:
    seeds = _read_json("results/flow_gain_seeds.json")
    m = _macros()
    card = (ROOT / "docs" / "BENCHMARK_CARD.md").read_text()
    log = (ROOT / "docs" / "RETRACTIONS.md").read_text()
    raft = {c["hand_displacement_px"]: c for c in
            seeds["raft"]["by_width"]["960"]["by_displacement"]}[34.181]
    rtext = f"{raft['mean']:.2f} (range {raft['min']:.2f} to {raft['max']:.2f})"
    assert f"mean there is {rtext}" in card
    assert f"{m['cgHalfRaftMean']} px against {m['cgWidthHalfB']} px" in card
    for tag, w in (("A", "480x270"), ("B", "960x540")):
        text = (f"{m['cgWidthGain' + tag]} (range {m['cgWidthGainMin' + tag]} to "
                f"{m['cgWidthGainMax' + tag]}) at {w}")
        assert text in card, text
    assert f"{m['cgShelfMean']} (sd {m['cgShelfSd']})" in card
    assert f"{m['cgShelfRaftMean']} (sd {m['cgShelfRaftSd']})" in card
    assert f"{m['cgBelowNinety']} of {m['cgNSeeds']} seeds" in log
    assert f"RAFT-small's mean gain there is {raft['mean']:.2f}" in log
    assert f"the published seed reads {m['cgGainAtKneePub']}" in log
