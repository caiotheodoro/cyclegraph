"""Build the Hugging Face dataset release, `caiotheodoro/cyclegraph-flow-gain`, from the
committed `results/` JSONs and the generator that produced them.

Every published byte is synthetic. No corpus frame, no worker, no factory and no pilot value
appears here, and `docs/DECISIONS.md` D071 fixes that scope. The only corpus-derived input
anywhere in the release is the vendor's published lens calibration, which is identical for all
2,144 shipped workers (D025).

Regenerable and testable: `python3 scripts/export_hf_dataset.py` writes `hf/dataset/`
(gitignored, it is derived), and `tests/test_export_hf_dataset.py` asserts every row equals its
source and that the generated card transcribes no number by hand -- each figure in the README is
interpolated from a file under `results/`, the same rule `MEASUREMENT_CARD.json` is built under.

Configs, one `.jsonl` each and listed in the front matter so `load_dataset` finds them:

    displacement_gain       results/flow_displacement_gain.json    farneback, 0.25 s baseline
    displacement_gain_raft  results/flow_gain_raft.json            raft-small, 0.25 s baseline
    gain_by_resolution      results/flow_gain_by_resolution.json   farneback, native rate
    estimator_benchmark     results/flow_benchmark.json            one row per estimator
    geometry_floor          results/a14_translation_floor.json     closed form, no estimator

The two 0.25 s files are comparable to each other and not to the third on a mm/s axis; the
displacements and gains are identical either way. Every row carries its own `pair_interval_s`
so this cannot be got wrong by reading one column out of context.

Also vendors the harness as `cyclegraph_flow_gain/`, which needs numpy and nothing else.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

RESULTS = ROOT / "results"

DATASET_ID = "caiotheodoro/cyclegraph-flow-gain"
SPACE_URL = "https://huggingface.co/spaces/caiotheodoro/cyclegraph"
REPO_URL = "https://github.com/caiotheodoro/cyclegraph"

# Copied verbatim into the release so it is self-describing without a clone.
DOC_COPIES = {
    "docs/BENCHMARK_CARD.md": "BENCHMARK_CARD.md",
    "docs/ETHICS.md": "ETHICS.md",
}
# `docs/RUBRIC.md` is deliberately NOT copied. Its v1.5.0 amendment carries a measurement over
# 120 decoded pilot frames, and its D045 entry names the corpus's actual clip durations. Both
# are pilot values, which `docs/ETHICS.md` and D018 forbid publishing, and a verbatim copy
# would have carried them into a release whose own card says no pilot value appears in it.
# Found by the W9 fresh-context review.

# The harness, flattened out of the package. `speed.py` is not copied: it pulls pydantic in for
# contract records the harness never touches, and the only thing it contributes here is one
# number, which `_constants.py` carries with its provenance instead.
VENDORED = ("ports.py", "synthetic.py", "gain.py")
IMPORT_REWRITES = (
    (r"from cyclegraph\.signal\.speed import HAND_BREADTH_MM",
     "from ._constants import HAND_BREADTH_MM"),
    (r"from cyclegraph\.signal\.ports import", "from .ports import"),
    (r"from cyclegraph\.signal\.synthetic import", "from .synthetic import"),
    (r"from cyclegraph\.signal\.gain import", "from .gain import"),
)


def _load(name: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((RESULTS / name).read_text())
    return doc


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return len(rows)


def _gain_rows(doc: dict[str, Any], source: str) -> list[dict[str, Any]]:
    """Flatten a sweep file to one row per (decode scale, displacement)."""
    out: list[dict[str, Any]] = []
    for scale in doc["scales"]:
        width, height = scale["frame_size"]
        box = scale["hand_box_width_px"]
        for row in scale["rows"]:
            out.append({
                "estimator": doc["estimator"],
                "frame_width": width,
                "frame_height": height,
                "hand_box_width_px": box,
                "mm_per_px": scale["mm_per_px"],
                # Carried per row rather than per file: the two 0.25 s sweeps and the native-rate
                # one are only comparable on displacement, and a reader slicing one column out of
                # the merged table has to be able to see which baseline they hold.
                "pair_interval_s": scale["pair_interval_s"],
                "translation_m_per_pair": row["translation_m_per_pair"],
                "hand_displacement_px": row["hand_displacement_px"],
                "displacement_over_box_width": round(row["hand_displacement_px"] / box, 4),
                "true_speed_mm_s": row["true_speed_mm_s"],
                "recovered_px": row["recovered_px"],
                "gain": row["gain"],
                "flow_returned_none": row["flow_returned_none"],
                "seed": doc["seed"],
                "source_file": source,
            })
    return out


def _benchmark_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Only the synthetic columns of `flow_benchmark.json`.

    `scripts/bench_flow.py` measures throughput and the flow-null rate over 200 **decoded pilot
    pairs** from 20 pilot clips (`docs/DECISIONS.md` D059), so `pairs`, `pairs_per_s`,
    `pairs_per_s_unbatched`, `pairs_per_s_batched_8`, `flow_null_rate` and `device` are pilot
    values and none of them may be published (D018, `docs/ETHICS.md`). `clears_null_ceiling` is
    the pass/fail the ethics document does permit, and it is the only thing carried out of that
    group.

    The A14 residual columns are computed by `_a14_residuals` on a rendered scene with
    `analytic_flow` and `render_pair` at seed 11 -- no corpus frame is involved -- so they are
    publishable and are what the release's claim about under-recovery rests on.
    """
    out: list[dict[str, Any]] = []
    for name, arm in doc["arms"].items():
        width, height = arm["frame_size"]
        out.append({
            "estimator": name,
            "a14_rotation_residual_px": arm["a14_rotation_residual_px"],
            "a14_rotation_residual_geometry_only_px":
                arm["a14_rotation_residual_geometry_only_px"],
            "clears_null_ceiling": arm["clears_null_ceiling"],
            "frame_width": width,
            "frame_height": height,
            "declared_dependency_cost": arm["declared_dependency_cost"],
            "source_file": "flow_benchmark.json (synthetic columns only)",
        })
    return out


def _floor_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    cases = (
        ("corpus_fisheye", "rotation_only", "rotation_only_corpus_lens"),
        ("narrow_control", "rotation_only", "rotation_only_narrow_lens_control"),
        ("corpus_fisheye", "translation_only", "translation_only_corpus_lens"),
    )
    out: list[dict[str, Any]] = []
    for lens, motion, key in cases:
        for row in doc[key]:
            out.append({
                "lens": lens,
                "motion_case": motion,
                "rotation_deg_per_s": row.get("rotation_deg_per_s", 0.0),
                "translation_m_per_s": row.get("translation_m_per_s", 0.0),
                "floor_mm_s": row["floor_mm_s"],
                "hand_distance_m": doc["assumptions"]["hand_distance_m"],
                "background_distance_m": doc["assumptions"]["background_distance_m"],
                "pair_interval_s": doc["assumptions"]["pair_interval_s"],
                "source_file": "a14_translation_floor.json",
            })
    return out


def _scale(doc: dict[str, Any], frame_size: list[int]) -> dict[str, Any]:
    for s in doc["scales"]:
        if s["frame_size"] == frame_size:
            scale: dict[str, Any] = s
            return scale
    raise KeyError(f"no {frame_size} scale")


def _at(scale: dict[str, Any], displacement: float) -> dict[str, Any]:
    for row in scale["rows"]:
        if row["hand_displacement_px"] == displacement:
            found: dict[str, Any] = row
            return found
    raise KeyError(f"no row at {displacement} px")


def _readme(counts: dict[str, int]) -> str:
    """Generate the card. Every figure below is read out of `results/`, never typed."""
    fb = _load("flow_displacement_gain.json")
    raft = _load("flow_gain_raft.json")
    byres = _load("flow_gain_by_resolution.json")
    bench = _load("flow_benchmark.json")
    floor = _load("a14_translation_floor.json")

    a = floor["assumptions"]
    ratio = a["hand_distance_m"] / a["background_distance_m"]
    fb960, raft960 = _scale(fb, [960, 540]), _scale(raft, [960, 540])

    # The box-relative displacement the resolution comparison is made at, taken from the data
    # rather than chosen: the third sweep step, which every scale shares.
    res_cols = [_scale(byres, fs) for fs in ([480, 270], [960, 540], [1440, 810], [1920, 1080])]
    res_idx = 2
    over_box = round(res_cols[0]["rows"][res_idx]["hand_displacement_px"]
                     / res_cols[0]["hand_box_width_px"], 3)

    fisheye_deg = 10.0
    fisheye10 = next(r for r in floor["rotation_only_corpus_lens"]
                     if r["rotation_deg_per_s"] == fisheye_deg)["floor_mm_s"]
    narrow10 = next(r for r in floor["rotation_only_narrow_lens_control"]
                    if r["rotation_deg_per_s"] == fisheye_deg)["floor_mm_s"]

    # Pulled as a whole paragraph, not a line: ETHICS.md hard-wraps and taking one line
    # truncates the sentence mid-clause, which is a bad way to quote a consent statement.
    ethics = (ROOT / "docs" / "ETHICS.md").read_text()
    para = next(b for b in ethics.split("\n\n") if "is the vendor's licence to grant" in b)
    consent = " ".join(ln.strip() for ln in para.strip().splitlines())
    consent = consent.replace("**", "").strip()
    assert consent.endswith("."), f"consent quote is truncated: {consent!r}"

    fm = "\n".join([
        "---",
        "license: apache-2.0",
        "pretty_name: cyclegraph flow gain",
        "language:",
        "  - en",
        "size_categories:",
        "  - n<1K",
        "tags:",
        "  - optical-flow",
        "  - benchmark",
        "  - synthetic",
        "  - ergonomics",
        "  - egocentric",
        "  - fisheye",
        "configs:",
    ] + [f"  - config_name: {name}\n    data_files: data/{name}.jsonl"
         for name in ("displacement_gain", "displacement_gain_raft", "gain_by_resolution",
                      "estimator_benchmark", "geometry_floor")] + ["---", ""])

    body = f"""# cyclegraph flow gain

**How much of a hand's motion a dense optical flow estimator actually recovers, and what it
reports instead once it stops.** Rendered under the corpus's own fisheye, where the true flow
field is known exactly, which is the only reason a gain is measurable at all.

The finding, in one line: past a displacement knee the estimator reports the **background**,
at a gain equal to hand distance over background distance
({a['hand_distance_m']} / {a['background_distance_m']} = {ratio:.2f}) — and the ego-motion
correction that ought to catch this subtracts the background, so the error cancels into a small
plausible number rather than a loud one.

**Run it against your own estimator.** The harness ships in this repository, needs numpy and
nothing else, and needs no corpus, no token and no GPU.

```python
from cyclegraph_flow_gain import gain_curve

def my_estimator(first, second):   # -> (H, W, 2) float32, or None on failure
    ...

curve = gain_curve(my_estimator, width=960)
print(curve.knee_px, curve.floor_gain, curve.floor_ratio_expected)
print(curve.verdict(operating_displacement_px=12.0))
```

Passing is **not** gain near 1.0 everywhere; no dense estimator does that. Passing is your knee
sitting outside the displacements your work actually produces, which is why `verdict()` takes
that displacement instead of assuming one.

## The knee belongs to the estimator, the floor belongs to the geometry

Both files below share the {fb960['pair_interval_s']} s pair baseline, so they compare directly.

| hand displacement | farneback-cv2 | raft-small |
|---|---|---|
| {_at(fb960, 22.794)['hand_displacement_px']} px | {_at(fb960, 22.794)['gain']} | {_at(raft960, 22.794)['gain']} |
| {_at(fb960, 34.181)['hand_displacement_px']} px | {_at(fb960, 34.181)['gain']} | {_at(raft960, 34.181)['gain']} |
| {_at(fb960, 45.539)['hand_displacement_px']} px | {_at(fb960, 45.539)['gain']} | {_at(raft960, 45.539)['gain']} |
| {_at(fb960, 68.025)['hand_displacement_px']} px | {_at(fb960, 68.025)['gain']} | {_at(raft960, 68.025)['gain']} |

RAFT-small buys roughly one more doubling of usable displacement and lands on the same floor.
A better estimator moves where the cliff is and does not touch what is underneath it.

## Higher decode resolution is not better

At {over_box} of the hand box width, the same physical displacement at four decode sizes:

| decode | {' | '.join(f"{c['frame_size'][0]}x{c['frame_size'][1]}" for c in res_cols)} |
|---|{'---|' * len(res_cols)}
| gain | {' | '.join(str(c['rows'][res_idx]['gain']) for c in res_cols)} |

{res_cols[1]['frame_size'][0]}x{res_cols[1]['frame_size'][1]} is a measured optimum.
{res_cols[3]['frame_size'][0]}x{res_cols[3]['frame_size'][1]} does worse than
{res_cols[0]['frame_size'][0]}x{res_cols[0]['frame_size'][1]}.

## The lens does most of the work

`{list(DOC_COPIES.values())[0]}` carries the argument. Under pure rotation at {fisheye_deg:.0f} degrees per second the corpus fisheye leaves {fisheye10} mm/s of apparent hand speed, where a narrow lens leaves {narrow10} mm/s. That is {fisheye10 / narrow10:.0f} times more from the same scalar-median subtraction, because rotational flow on a fisheye varies with radius and a scalar cannot cancel a field that does.

The exact-geometry residual is the control: {bench['arms']['farneback-cv2']['a14_rotation_residual_geometry_only_px']} px,
computed closed-form with no estimator involved. `farneback-cv2` reports
{bench['arms']['farneback-cv2']['a14_rotation_residual_px']} px and `raft-small` reports
{bench['arms']['raft-small']['a14_rotation_residual_px']} px — **below** the floor an ideal
estimator would leave, which is under-recovery rather than accuracy.

## Configs

| config | rows | what one row is |
|---|---|---|
| `displacement_gain` | {counts['displacement_gain']} | farneback, one decode scale and displacement, {fb['pair_interval_s']} s baseline |
| `displacement_gain_raft` | {counts['displacement_gain_raft']} | raft-small, same sweep and baseline |
| `gain_by_resolution` | {counts['gain_by_resolution']} | farneback across four decode sizes, {byres['pair_interval_s']} s baseline |
| `estimator_benchmark` | {counts['estimator_benchmark']} | one estimator: its A14 rotation residual against the exact-geometry floor |
| `geometry_floor` | {counts['geometry_floor']} | closed-form apparent speed under one camera motion |

**On baselines.** `displacement_gain` and `displacement_gain_raft` use the
{fb['pair_interval_s']} s pair interval; `gain_by_resolution` uses the clip's own rate,
{byres['pair_interval_s']} s. Displacements and gains are identical either way — the interval
only rescales `true_speed_mm_s`. Compare estimators on `hand_displacement_px` and never across
files on mm/s. Every row carries its own `pair_interval_s`.

## What this cannot tell you

- **Whether a real hand crosses the knee.** That depends on your frame rate and your work. The
  harness reports the knee for your geometry; it does not know your job.
- **Anything about the corpus.** No corpus frame was decoded for any number here. The
  measurement cyclegraph exists to make is blocked on cost and one human step, and has not run.
- **Whether the ergonomic instrument is valid.** No ergonomist scored anything.
- **The corpus's real ego-motion distribution.** The floor table assumes a camera motion.
- **Whether synthetic texture behaves like factory video.** The lens is the corpus's. The
  content is not.

The depth planes — {a['hand_distance_m']} m and {a['background_distance_m']} m — are stated
assumptions about workstation geometry, not measurements, and the floor sits at their ratio, so
a different workstation gives a different floor. That is a prediction and it is untested.

## Provenance and terms

Apache-2.0, as is `builddotai/Egocentric-10K` itself. The lens calibration is the vendor's
published `intrinsics.json`, identical for all 2,144 shipped workers. `ETHICS.md` in this
repository records the limit of what the licence settles:

> {consent}

No frame, no worker, no factory and no pilot value appears in this release.

- Repository, including what is blocked and why: {REPO_URL}
- The data behind every table above, interactively: {SPACE_URL}
"""
    return fm + body


def _vendor_harness(out_dir: Path) -> list[str]:
    """Copy the harness into a flat package with numpy as its only dependency."""
    pkg = out_dir / "cyclegraph_flow_gain"
    pkg.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in VENDORED:
        src = (ROOT / "src" / "cyclegraph" / "signal" / name).read_text()
        for pattern, replacement in IMPORT_REWRITES:
            src = re.sub(pattern, replacement, src)
        (pkg / name).write_text(src)
        written.append(name)

    breadth = re.search(r"HAND_BREADTH_MM: Final\[float\] = ([\d.]+)",
                        (ROOT / "src" / "cyclegraph" / "signal" / "speed.py").read_text())
    assert breadth is not None, "speed.py no longer declares HAND_BREADTH_MM"
    (pkg / "_constants.py").write_text(
        '"""Constants the harness needs, lifted out of the package that defines them.\n\n'
        "`speed.py` owns this number but imports pydantic contract records the harness never\n"
        "touches, so it is carried here instead of vendoring that dependency.\n"
        '"""\n\nfrom typing import Final\n\n'
        "#: ANSUR II 50th-percentile male hand breadth, the scale that converts pixels to\n"
        "#: millimetres. Sensitivity to 79.5 and 90.4 is reported in the repository.\n"
        f"HAND_BREADTH_MM: Final[float] = {breadth.group(1)}\n")
    written.append("_constants.py")

    (pkg / "__init__.py").write_text(
        '"""The cyclegraph flow-gain test.\n\n'
        "Point `gain_curve` at your own estimator and it reports where your gain leaves 1.0,\n"
        "the floor it lands on, and the depth ratio that floor equals if the estimator has\n"
        "silently switched to tracking the background.\n"
        '"""\n\nfrom .gain import (\n'
        "    GainCurve,\n    GainRow,\n    curve_from_rows,\n    gain_curve,\n    sweep,\n)\n\n"
        '__all__ = ["GainCurve", "GainRow", "curve_from_rows", "gain_curve", "sweep"]\n')
    written.append("__init__.py")
    return written


def export(out_dir: Path) -> dict[str, int]:
    data = out_dir / "data"
    counts = {
        "displacement_gain": _write_jsonl(
            data / "displacement_gain.jsonl",
            _gain_rows(_load("flow_displacement_gain.json"), "flow_displacement_gain.json")),
        "displacement_gain_raft": _write_jsonl(
            data / "displacement_gain_raft.jsonl",
            _gain_rows(_load("flow_gain_raft.json"), "flow_gain_raft.json")),
        "gain_by_resolution": _write_jsonl(
            data / "gain_by_resolution.jsonl",
            _gain_rows(_load("flow_gain_by_resolution.json"), "flow_gain_by_resolution.json")),
        "estimator_benchmark": _write_jsonl(
            data / "estimator_benchmark.jsonl", _benchmark_rows(_load("flow_benchmark.json"))),
        "geometry_floor": _write_jsonl(
            data / "geometry_floor.jsonl", _floor_rows(_load("a14_translation_floor.json"))),
    }

    raw = out_dir / "results"
    raw.mkdir(parents=True, exist_ok=True)
    # `flow_benchmark.json` is not copied: its throughput and null-rate columns are measured
    # over decoded pilot pairs (D059). The synthetic A14 columns reach the release through
    # `_benchmark_rows` instead.
    for name in ("flow_displacement_gain.json", "flow_gain_raft.json",
                 "flow_gain_by_resolution.json", "a14_translation_floor.json"):
        shutil.copyfile(RESULTS / name, raw / name)

    for src, dst in DOC_COPIES.items():
        shutil.copyfile(ROOT / src, out_dir / dst)

    _vendor_harness(out_dir)
    shutil.copyfile(ROOT / "scripts" / "run_gain_test.py", out_dir / "run_gain_test.py")
    (out_dir / "README.md").write_text(_readme(counts))
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="hf/dataset", help="staging directory, gitignored")
    args = parser.parse_args(argv)

    out = ROOT / args.out
    counts = export(out)
    for name, n in counts.items():
        print(f"  {name:24s} {n:4d} rows")
    print(f"\nwrote {out}  ->  huggingface.co/datasets/{DATASET_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
