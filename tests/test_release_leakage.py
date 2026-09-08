"""One gate over every byte the W9 release ships, whichever surface it ships on.

`scripts/validate.py`'s identifier gate runs over git-tracked `results/` only. Both release
trees are gitignored because they are derived, so before this existed they were covered by
nothing at all -- while `docs/WAVES.md`'s W9 exit condition reads "every shipped byte passes the
identifier gate". The W9 fresh-context review found two pilot leaks in that blind spot.

Identifiers are the easy half and were never the problem. The hard half is a **pilot value**: a
number measured over decoded pilot-factory frames, which `docs/ETHICS.md` and D018 forbid
publishing and which carries no identifier to grep for. It is caught here by naming the fields
and the figures that are known to be pilot-derived, because they cannot be recognised by shape.
"""

from __future__ import annotations

import json
import re
import sys
import pathlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import export_hf_dataset as hf  # noqa: E402
import export_space_data as sp  # noqa: E402

IDENTIFIER = re.compile(r"factory[_-]?\d|worker[_-]?\d|clip_[0-9a-f]{4}", re.I)

# Fields of `results/flow_benchmark.json` measured over 200 decoded pilot pairs from 20 pilot
# clips (`docs/DECISIONS.md` D059). `clears_null_ceiling` is absent on purpose: a pass/fail is
# what ETHICS permits the pilot to publish. The A14 residual fields are absent because
# `bench_flow.py:_a14_residuals` computes them on a rendered scene with no corpus frame.
PILOT_FIELDS = ("pairs_per_s", "pairs_per_s_unbatched", "pairs_per_s_batched_8",
                "flow_null_rate", "clips_probed", "open_failure_rate", "truncation")

# Figures that are pilot measurements and would otherwise pass every structural check.
# 676 and 120 are `docs/RUBRIC.md`'s v1.5.0 amendment, which was being copied verbatim.
PILOT_FIGURES = ("7.568", "21.494", "676", "120 pilot")


@pytest.fixture(scope="module")
def trees(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    hf_dir = tmp_path_factory.mktemp("hf")
    hf.export(hf_dir)
    space_dir = tmp_path_factory.mktemp("space")
    (space_dir / "data.json").write_text(json.dumps(sp.build(), allow_nan=False))
    for name in ("index.html", "README.md"):
        (space_dir / name).write_text((ROOT / "space" / name).read_text())
    return [hf_dir, space_dir]


def _files(trees: list[Path]) -> list[Path]:
    return [p for tree in trees for p in sorted(tree.rglob("*")) if p.is_file()]


def test_no_identifier_in_any_shipped_byte(trees: list[Path]) -> None:
    offenders = []
    for path in _files(trees):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [f"{path.name}: {hit}" for hit in IDENTIFIER.findall(text)]
    assert offenders == [], offenders


def test_no_pilot_derived_field_ships(trees: list[Path]) -> None:
    offenders = []
    for path in _files(trees):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [f"{path.name}: {f}" for f in PILOT_FIELDS if f in text]
    assert offenders == [], f"pilot-derived fields in the release: {offenders}"


def test_no_pilot_figure_ships(trees: list[Path]) -> None:
    offenders = []
    for path in _files(trees):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [f"{path.name}: {v}" for v in PILOT_FIGURES if v in text]
    assert offenders == [], f"pilot figures in the release: {offenders}"


def test_no_pilot_file_and_no_rubric_copy_ships(trees: list[Path]) -> None:
    names = [p.name for p in _files(trees)]
    assert not any("pilot" in n for n in names), names
    assert "RUBRIC.md" not in names, (
        "docs/RUBRIC.md carries a 120-pilot-frame measurement in its v1.5.0 amendment and must "
        "not be copied into the release verbatim")
    assert "flow_benchmark.json" not in names, (
        "flow_benchmark.json's throughput and null-rate columns are pilot measurements (D059); "
        "only its synthetic A14 columns may be published, via _benchmark_rows")


def test_the_gate_can_fail() -> None:
    """A gate nobody has seen fail is not evidence. `docs/HANDOFF.md` names this failure shape."""
    assert IDENTIFIER.search("factory_001/workers/worker_002")
    assert IDENTIFIER.search("clip_a1b2c3")
    assert not IDENTIFIER.search("960x540 farneback-cv2 gain 0.9925")
    assert any(f in '{"pairs_per_s": 7.568}' for f in PILOT_FIELDS)


def test_the_release_claim_matches_what_the_gate_checks(trees: list[Path]) -> None:
    """The card asserts this in prose; the prose must not outrun the check."""
    readme = (trees[0] / "README.md").read_text()
    assert "No frame, no worker, no factory and no pilot value appears in this release" in readme


def test_a_rebuild_removes_what_a_previous_build_shipped(tmp_path: pathlib.Path) -> None:
    """The staging directory is rebuilt, not updated in place.

    Found by listing the real `hf/dataset/` after the review fixes landed: `RUBRIC.md` and
    `results/flow_benchmark.json` were still there, because the exporter only ever wrote files
    and never removed them. Every test built into a fresh directory, so none of them could see
    it. Publishing from that directory would have shipped both pilot leaks with the fix in
    place and the tests green.
    """
    stale_doc = tmp_path / "RUBRIC.md"
    stale_result = tmp_path / "results" / "flow_benchmark.json"
    stale_result.parent.mkdir(parents=True)
    stale_doc.write_text("measured on 120 pilot frames it reached 676 px")
    stale_result.write_text('{"arms": {"farneback-cv2": {"pairs_per_s": 7.568}}}')

    hf.export(tmp_path)

    assert not stale_doc.exists(), "a stale doc survived the rebuild"
    assert not stale_result.exists(), "a stale result survived the rebuild"
    assert not list(tmp_path.rglob("__pycache__")), "bytecode shipped"
