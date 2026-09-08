"""Tests for `scripts/export_hf_dataset.py`.

Two properties carry the release. Rows must equal their sources, because a flattening bug would
publish numbers that no longer match the files they cite. And the generated card must transcribe
nothing by hand -- the rule `MEASUREMENT_CARD.json` is built under, applied to prose, because a
card whose numbers drifted from its data is exactly the failure this project exists to describe.

Identifier hygiene on the built tree is checked here only for filenames and literal identifier
strings. The pilot-value question is a different and harder one -- a number measured over decoded
pilot frames carries nothing to grep for -- and it lives in `tests/test_release_leakage.py`,
which names the fields and figures that are known to be pilot-derived and checks both release
trees. This file does not establish that no pilot value ships, and it used to say it did.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import export_hf_dataset as ex  # noqa: E402

# `scripts/validate.py`'s identifier gate, applied to the built tree rather than to `results/`.
IDENTIFIER = re.compile(r"factory[_-]?\d|worker[_-]?\d", re.I)

SOURCES = ("flow_displacement_gain.json", "flow_gain_raft.json", "flow_gain_by_resolution.json",
           "flow_benchmark.json", "a14_translation_floor.json")


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, int]]:
    out = tmp_path_factory.mktemp("hf")
    counts = ex.export(out)
    return out, counts


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_row_counts_equal_the_sources(built: tuple[Path, dict[str, int]]) -> None:
    out, counts = built
    expected = {}
    for cfg, name in (("displacement_gain", "flow_displacement_gain.json"),
                      ("displacement_gain_raft", "flow_gain_raft.json"),
                      ("gain_by_resolution", "flow_gain_by_resolution.json")):
        doc = json.loads((ROOT / "results" / name).read_text())
        expected[cfg] = sum(len(s["rows"]) for s in doc["scales"])
    expected["estimator_benchmark"] = len(
        json.loads((ROOT / "results" / "flow_benchmark.json").read_text())["arms"])
    floor = json.loads((ROOT / "results" / "a14_translation_floor.json").read_text())
    expected["geometry_floor"] = sum(len(floor[k]) for k in (
        "rotation_only_corpus_lens", "rotation_only_narrow_lens_control",
        "translation_only_corpus_lens"))

    assert counts == expected
    for cfg, n in counts.items():
        assert len(_jsonl(out / "data" / f"{cfg}.jsonl")) == n


def test_every_gain_row_equals_its_source(built: tuple[Path, dict[str, int]]) -> None:
    out, _ = built
    for cfg, name in (("displacement_gain", "flow_displacement_gain.json"),
                      ("displacement_gain_raft", "flow_gain_raft.json"),
                      ("gain_by_resolution", "flow_gain_by_resolution.json")):
        doc = json.loads((ROOT / "results" / name).read_text())
        source = [(s["frame_size"][0], r["hand_displacement_px"], r["gain"])
                  for s in doc["scales"] for r in s["rows"]]
        built_rows = [(r["frame_width"], r["hand_displacement_px"], r["gain"])
                      for r in _jsonl(out / "data" / f"{cfg}.jsonl")]
        assert built_rows == source, cfg


def test_every_row_carries_its_own_pair_interval(built: tuple[Path, dict[str, int]]) -> None:
    """D071: the two baselines are only comparable on displacement, so the column travels."""
    out, _ = built
    for cfg in ("displacement_gain", "displacement_gain_raft", "gain_by_resolution"):
        rows = _jsonl(out / "data" / f"{cfg}.jsonl")
        assert all("pair_interval_s" in r for r in rows), cfg
    fb = {r["pair_interval_s"] for r in _jsonl(out / "data" / "displacement_gain.jsonl")}
    raft = {r["pair_interval_s"] for r in _jsonl(out / "data" / "displacement_gain_raft.jsonl")}
    byres = {r["pair_interval_s"] for r in _jsonl(out / "data" / "gain_by_resolution.jsonl")}
    assert fb == raft, "the two compared estimators must share a baseline"
    assert fb != byres, "the resolution sweep is on the other baseline and must say so"


def test_the_card_transcribes_no_number(built: tuple[Path, dict[str, int]]) -> None:
    """Every measured figure in the README must appear in a file under `results/`.

    Structural numbers -- row counts, the shipped worker count, the depth ratio -- are allowed
    by name and nothing else is. A card figure that is neither in the data nor on that list is
    a transcription, which is how a card and its numbers drift apart.
    """
    out, counts = built
    readme = (out / "README.md").read_text()
    # The pool is everything the release ships, not only the raw results: a figure the card
    # derives (displacement over box width, say) must still appear in a published column, so a
    # reader can find it rather than having to recompute it.
    pool = " ".join((ROOT / "results" / n).read_text() for n in SOURCES)
    pool += " " + " ".join(p.read_text() for p in sorted((out / "data").glob("*.jsonl")))

    allowed = {str(n) for n in counts.values()}
    allowed |= {"2", "4", "10", "76", "0.18", "2,144", "1.0", "0.5", "12.0", "960", "2.0"}

    body = readme.split("---", 2)[-1]
    body = re.sub(r"```.*?```", "", body, flags=re.S)          # the usage snippet
    body = re.sub(r"https?://\S+", "", body)                    # URLs carry no measurements
    numbers = set(re.findall(r"(?<![\w.])\d+\.\d{2,}(?![\w])", body))

    missing = sorted(n for n in numbers if n not in pool and n not in allowed)
    assert missing == [], f"README numbers not traceable to results/: {missing}"


def test_the_consent_quote_is_a_whole_sentence(built: tuple[Path, dict[str, int]]) -> None:
    """ETHICS.md hard-wraps; quoting one line truncates it mid-clause."""
    out, _ = built
    quote = next(ln for ln in (out / "README.md").read_text().splitlines()
                 if ln.startswith("> "))
    assert quote.rstrip().endswith(".")
    assert "consent instrument is unknown" in quote


def test_no_identifier_and_no_pilot_file_ships(built: tuple[Path, dict[str, int]]) -> None:
    out, _ = built
    offenders = []
    for path in sorted(out.rglob("*")):
        if not path.is_file():
            continue
        assert "pilot" not in path.name, f"a pilot file reached the release: {path}"
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for hit in IDENTIFIER.findall(text):
            offenders.append(f"{path.relative_to(out)}: {hit}")
    assert offenders == [], f"identifier-shaped strings in the release: {offenders}"


def test_the_vendored_harness_runs_on_numpy_alone(built: tuple[Path, dict[str, int]]) -> None:
    """The release's central promise: a stranger runs this without the repo and without a GPU.

    Run in a subprocess with the repo's `src/` off the path, so an accidental fallback to the
    installed package would fail rather than silently pass.
    """
    out, _ = built
    script = """
import sys, numpy as np
sys.path.insert(0, %r)
try:
    import cyclegraph
    raise SystemExit("repo package was importable; this test proves nothing")
except ModuleNotFoundError:
    pass
from cyclegraph_flow_gain import gain_curve

class BackgroundTracker:
    def flow(self, first, second):
        f = np.zeros((first.shape[0], first.shape[1], 2), dtype=np.float32)
        f[..., 0] = 2.0
        return f

c = gain_curve(BackgroundTracker(), width=480)
assert c.knee_px is None, c.knee_px
assert c.tracks_background is True, (c.floor_gain, c.floor_ratio_expected)
assert c.verdict(5.0) == "FAIL"
for m in ("pydantic", "cv2", "torch"):
    assert m not in sys.modules, m
print("ok")
""" % str(out)
    env_root = str(ROOT)
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          cwd=str(out), env={"PATH": "/usr/bin:/bin", "HOME": env_root})
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout


def test_the_harness_source_has_no_repo_imports_left(built: tuple[Path, dict[str, int]]) -> None:
    out, _ = built
    for path in (out / "cyclegraph_flow_gain").glob("*.py"):
        assert "from cyclegraph." not in path.read_text(), path.name
