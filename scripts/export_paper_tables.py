"""Write every figure, table and number in paper/cyclegraph.tex from the committed artifacts.

The paper's prose holds no artifact number. It names a macro (`\\cgKneeMean`) and this script
defines it, from `results/*.json`, `MEASUREMENT_CARD.json` or a code constant. `tests/test_paper.py`
regenerates the files in memory and fails if the committed copies differ, and fails if the prose
contains a bare number that is not on its short allowlist. A number cannot be typed into the
paper, only produced here.

    python3 scripts/export_paper_tables.py            # rewrite paper/generated/
    python3 scripts/export_paper_tables.py --check    # exit 1 if the committed files differ
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.exposure.hal import AKKAS_2015_RANGE, hal_akkas_2015  # noqa: E402
from cyclegraph.signal.speed import HAND_BREADTH_MM  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    BACKGROUND_DISTANCE_M,
    HAND_DISTANCE_M,
)

OUT = ROOT / "paper" / "generated"
HAL_BOUND = 0.25


def _load(name: str) -> Any:
    return json.loads((ROOT / name).read_text())


def _f(x: float, nd: int) -> str:
    return f"{x:.{nd}f}"


def _tex_minus(s: str) -> str:
    return s.replace("-", "$-$")


def build() -> dict[str, str]:
    seeds = _load("results/flow_gain_seeds.json")
    floor = _load("results/a14_translation_floor.json")
    native = _load("results/flow_gain_by_resolution.json")
    bench = _load("results/flow_benchmark.json")
    card = _load("MEASUREMENT_CARD.json")
    vendor = _load("results/vendor_claim.json")
    prov = _load("results/provenance.json")
    raft480 = _load("results/flow_gain_raft.json")["scales"][0]["rows"][0]

    files: dict[str, str] = {}
    m: dict[str, str] = {}

    # ----- what the vendor's own page says ------------------------------------------------------
    m["VendorPct"] = _f(vendor["published_percent"]["egocentric_10k"], 2)
    m["VendorPctEgo"] = _f(vendor["published_percent"]["ego4d"], 2)
    m["VendorPctEpic"] = _f(vendor["published_percent"]["epic_kitchens"], 2)
    m["VendorFrames"] = f"{vendor['frames_sampled']:,}".replace(",", "{,}")
    m["CorpusHours"] = f"{vendor['corpus_hours']:,}".replace(",", "{,}")
    sib = vendor["sibling_audit"]
    m["SibOver"] = str(sib["manipulation_judge_over_calls"])
    m["SibOverOf"] = str(sib["manipulation_over_call_possible"])
    m["SibUnder"] = str(sib["manipulation_judge_under_calls"])
    m["SibUnderOf"] = str(sib["manipulation_under_call_possible"])
    m["SibLabels"] = str(sib["human_labels"])
    m["CorpusFactories"] = str(vendor["corpus_factories"])

    # ----- provenance of the registration and the novelty re-run ------------------------------
    import datetime as _dt
    created = _dt.datetime.strptime(prov["github"]["repository_created_utc"], "%Y-%m-%dT%H:%M:%SZ")
    m["RepoCreated"] = f"{created.day} {created.strftime('%B %Y')}"
    m["PreregVersion"] = prov["preregistration"]["current_version"]
    m["Amendments"] = str(prov["preregistration"]["amendments"])
    m["FreezeShort"] = prov["preregistration"]["freeze_commit"][:7]
    pm = prov["novelty_gate_rerun"]["pubmed"]
    m["PubmedA"] = str(pm[0]["hits_rerun"])
    m["PubmedB"] = str(pm[1]["hits_rerun"])
    m["PubmedC"] = str(pm[2]["hits_rerun"])
    m["ArxivA"] = str(prov["novelty_gate_rerun"]["arxiv"][0]["hits_rerun"])
    m["RaftSmall"] = _f(raft480["gain"], 2)
    m["RaftSmallPx"] = _f(raft480["hand_displacement_px"], 1)

    # ----- geometry and the pre-registered budget ------------------------------------------
    ratio = HAND_DISTANCE_M / BACKGROUND_DISTANCE_M
    m["Ratio"] = _f(ratio, 2)
    m["HandDist"] = _f(HAND_DISTANCE_M, 2)
    m["BgDist"] = _f(BACKGROUND_DISTANCE_M, 1)
    m["HandBreadth"] = _f(HAND_BREADTH_MM, 0)
    m["HalBound"] = _f(HAL_BOUND, 2)
    budget = floor["hal_budget_mm_s_at_assumed_median"]
    m["BudgetMmS"] = _f(budget["612.4"], 1)
    m["BudgetPct"] = _f(100 * budget["612.4"] / 612.4, 1)
    m["BudgetPctLo"] = _f(100 * budget["800.0"] / 800.0, 1)
    m["BudgetPctHi"] = _f(100 * budget["400.0"] / 400.0, 1)
    m["AssumedMedian"] = "612.4"
    m["SpeedLo"] = _f(AKKAS_2015_RANGE.x_lo, 1)
    m["SpeedHi"] = _f(AKKAS_2015_RANGE.x_hi, 1)
    m["DutyPricing"] = _f(floor["assumptions"]["duty_cycle_pct_for_pricing"], 0)
    mt = floor["motion_budget_at_0.25_hal"]
    m["RotBudget"] = _f(mt["rotation_deg_per_s"]["612.4"], 1)
    m["TransBudgetCm"] = _f(100 * mt["translation_m_per_s"]["612.4"], 1)

    rot = {r["rotation_deg_per_s"]: r["floor_mm_s"] for r in floor["rotation_only_corpus_lens"]}
    narrow = {r["rotation_deg_per_s"]: r["floor_mm_s"]
              for r in floor["rotation_only_narrow_lens_control"]}
    m["RotFisheye"] = _f(rot[10.0], 1)
    m["RotNarrow"] = _f(narrow[10.0], 2)
    m["RotRatio"] = _f(rot[10.0] / narrow[10.0], 0)
    lens = floor["lens"]
    m["HalfAngle"] = _f(lens["max_half_angle_deg"], 1)

    # ----- the A14 floor table -------------------------------------------------------------
    rows = []
    for deg in (2.0, 10.0, 30.0, 60.0):
        rows.append(f"{deg:.0f} & {_f(rot[deg], 2)} & {_f(narrow[deg], 2)} \\\\")
    files["tab_floor.tex"] = (
        "\\begin{tabular}{@{}rrr@{}}\n\\toprule\n"
        "Head rotation (deg/s) & corpus fisheye (mm/s) & narrow lens (mm/s) \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    trans = {r["translation_m_per_s"]: r["floor_mm_s"] for r in floor["translation_only_corpus_lens"]}
    m["TransFloorFive"] = _f(trans[0.05], 1)

    # ----- the seed spread -----------------------------------------------------------------
    n_seeds = len(seeds["seeds"])
    m["NSeeds"] = str(n_seeds)
    m["NSeedsRaft"] = str(len(seeds["raft"]["seeds"]))
    m["PubSeed"] = str(seeds["published_seed"])
    far = seeds["farneback_by_width"]["960"]
    fine = seeds["farneback_fine_960"]
    raft = seeds["raft"]["by_width"]["960"]
    m["DispLow"] = _f(far["by_displacement"][0]["hand_displacement_px"], 1)
    m["KneeFineMean"] = _f(fine["knee_px"]["mean"], 1)
    m["KneeFineSd"] = _f(fine["knee_px"]["sd"], 1)
    m["KneeFineMin"] = _f(fine["knee_px"]["min"], 1)
    m["KneeFineMax"] = _f(fine["knee_px"]["max"], 1)
    m["KneeFineN"] = str(fine["knee_px"]["n_with_knee"])
    m["HalfFineMean"] = _f(fine["half_crossing_px"]["mean"], 1)
    m["HalfFineSd"] = _f(fine["half_crossing_px"]["sd"], 1)
    m["HalfFineMin"] = _f(fine["half_crossing_px"]["min"], 1)
    m["HalfFineMax"] = _f(fine["half_crossing_px"]["max"], 1)
    m["HalfFineN"] = str(fine["half_crossing_px"]["n_with_crossing"])
    m["ShelfMean"] = _f(far["floor_gain"]["mean"], 2)
    m["ShelfSd"] = _f(far["floor_gain"]["sd"], 2)
    m["ShelfMin"] = _f(far["floor_gain"]["min"], 2)
    m["ShelfMax"] = _f(far["floor_gain"]["max"], 2)
    m["ShelfRaftMean"] = _f(raft["floor_gain"]["mean"], 2)
    m["ShelfRaftSd"] = _f(raft["floor_gain"]["sd"], 2)
    m["HalfFarMin"] = _f(seeds["farneback_by_width"]["960"]["half_crossing_px"]["min"], 1)
    m["HalfFarMax"] = _f(seeds["farneback_by_width"]["960"]["half_crossing_px"]["max"], 1)
    lc = prov["lens_check"]
    m["LensChecked"] = str(lc["calibration_files_compared"])
    m["LensShipped"] = f"{lc['workers_shipped']:,}".replace(",", "{,}")
    # every measurement in every published and seeded sweep returned a field
    published_rows = [r for f in ("flow_displacement_gain", "flow_gain_raft",
                                  "flow_gain_by_resolution")
                      for sc in _load(f"results/{f}.json")["scales"] for r in sc["rows"]]
    assert not any(r["flow_returned_none"] for r in published_rows)
    seed_gains = [g for arm in list(seeds["farneback_by_width"].values())
                  + [seeds["farneback_fine_960"]] + list(seeds["raft"]["by_width"].values())
                  for ps in arm["per_seed"] for g in ps["gains"]]
    assert all(g is not None for g in seed_gains)
    m["PublishedRows"] = str(len(published_rows))
    m["SeedMeasurements"] = f"{len(seed_gains):,}".replace(",", "{,}")
    # the CPU RAFT arm against the curve published from a CUDA device, on the shared seed
    rp = next(sc for sc in _load("results/flow_gain_raft.json")["scales"]
              if sc["frame_size"][0] == 960)
    rs = next(x for x in raft["per_seed"] if x["seed"] == seeds["published_seed"])
    m["RaftDevGap"] = _f(max(abs(r["gain"] - g) for r, g in zip(rp["rows"], rs["gains"])), 4)
    m["HalfRaftMean"] = _f(raft["half_crossing_px"]["mean"], 1)
    m["HalfRaftSd"] = _f(raft["half_crossing_px"]["sd"], 1)
    m["HalfRaftMin"] = _f(raft["half_crossing_px"]["min"], 1)
    m["HalfRaftMax"] = _f(raft["half_crossing_px"]["max"], 1)

    def by_disp(arm: dict[str, Any]) -> dict[float, dict[str, Any]]:
        return {c["hand_displacement_px"]: c for c in arm["by_displacement"]}

    f960, r960 = by_disp(far), by_disp(raft)
    # The single published seed, read from the seed arm's own per-seed record and checked
    # against the published file by tests/test_paper.py.
    pub = next(s for s in far["per_seed"] if s["seed"] == seeds["published_seed"])
    disp = [c["hand_displacement_px"] for c in far["by_displacement"]]
    i_knee = disp.index(22.794)
    i_after = disp.index(34.181)
    m["GainAtKneeMean"] = _f(f960[22.794]["mean"], 2)
    m["GainAtKneeSd"] = _f(f960[22.794]["sd"], 2)
    m["GainAtKneeMin"] = _f(f960[22.794]["min"], 2)
    m["GainAtKneeMax"] = _f(f960[22.794]["max"], 2)
    m["GainAtKneePub"] = _f(pub["gains"][i_knee], 2)
    m["GainAfterMean"] = _f(f960[34.181]["mean"], 2)
    m["GainAfterMin"] = _f(f960[34.181]["min"], 2)
    m["GainAfterMax"] = _f(f960[34.181]["max"], 2)
    m["GainAfterPub"] = _f(pub["gains"][i_after], 2)
    m["DispKnee"] = _f(22.794, 1)
    m["DispAfter"] = _f(34.181, 1)
    m["RaftAfterMean"] = _f(r960[34.181]["mean"], 2)
    m["RaftGainSmallMean"] = _f(r960[disp[0]]["mean"], 2)
    m["RaftGainSmallSd"] = _f(r960[disp[0]]["sd"], 2)

    # Speed at which the knee displacement is reached at the native pair interval, 960 wide.
    nat960 = next(s for s in native["scales"] if s["frame_size"][0] == 960)
    speed_at = {r["hand_displacement_px"]: r["true_speed_mm_s"] for r in nat960["rows"]}
    m["SpeedAtKnee"] = _f(speed_at[22.794], 0)
    m["SpeedAfter"] = _f(speed_at[34.181], 0)
    m["PairInterval"] = _f(1000 * native["pair_interval_s"], 0)
    m["MmPerPx"] = _f(nat960["mm_per_px"], 2)
    px_at_median = 612.4 * native["pair_interval_s"] / nat960["mm_per_px"]
    m["PxAtMedian"] = _f(px_at_median, 0)

    # ----- gain table: Farneback 960 and RAFT 960, mean, sd, range ---------------------------
    rows = []
    for d in disp:
        a, b = f960[d], r960[d]
        rows.append(
            f"{_f(d, 1)} & {_f(a['mean'], 2)} & {_f(a['sd'], 2)} & "
            f"{_f(a['min'], 2)}--{_f(a['max'], 2)} & {_f(b['mean'], 2)} & {_f(b['sd'], 2)} & "
            f"{_f(b['min'], 2)}--{_f(b['max'], 2)} \\\\")
    files["tab_gain.tex"] = (
        "\\begin{tabular}{@{}rrrcrrc@{}}\n\\toprule\n"
        " & \\multicolumn{3}{c}{Farneback} & \\multicolumn{3}{c}{RAFT-small} \\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n"
        "Displacement (px) & mean & sd & range & mean & sd & range \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ----- decode width table ----------------------------------------------------------------
    # translation 0.02 m is the same physical motion at every width (about 600 mm/s at the
    # native pair interval), so the four rows are compared at one speed, not one pixel count.
    rows = []
    dt = native["pair_interval_s"]
    for w, tag in (("480", "A"), ("960", "B"), ("1440", "C"), ("1920", "D")):
        a = seeds["farneback_by_width"][w]
        sc = next(x for x in native["scales"] if x["frame_size"][0] == int(w))
        col = next(c for c in a["by_displacement"] if c["translation_m"] == 0.02)
        per = [s["gains"][[c["translation_m"] for c in a["by_displacement"]].index(0.02)]
               for s in a["per_seed"]]
        hc = a["half_crossing_px"]
        speed_half = hc["mean"] * sc["mm_per_px"] / dt
        speed_here = col["hand_displacement_px"] * sc["mm_per_px"] / dt
        rows.append(
            f"{w}$\\times${round(int(w) * 9 / 16)} & {_f(sc['mm_per_px'], 2)} & "
            f"{_f(col['hand_displacement_px'], 1)} & "
            f"{_f(col['mean'], 2)} ({_f(col['min'], 2)}--{_f(col['max'], 2)}) & "
            f"{_f(hc['mean'], 1)} & {_f(hc['sd'], 1)} & {_f(speed_half, 0)} \\\\")
        m["WidthGain" + tag] = _f(col["mean"], 2)
        m["WidthGainMin" + tag] = _f(col["min"], 2)
        m["WidthGainMax" + tag] = _f(col["max"], 2)
        m["WidthHalf" + tag] = _f(hc["mean"], 1)
        m["WidthHalfSd" + tag] = _f(hc["sd"], 1)
        m["WidthHalfMmS" + tag] = _f(speed_half, 0)
        m["WidthSpeed" + tag] = _f(speed_here, 0)
        if w == "960":
            m["BelowNinety"] = str(sum(1 for g in per if g < 0.9))
    files["tab_width.tex"] = (
        "\\begin{tabular}{@{}lrrcrrr@{}}\n\\toprule\n"
        "Decode & mm/px & px moved & gain at about 600 mm/s & "
        "crossing (px) & sd (px) & crossing (mm/s) \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ----- A14 residual in pixels, single scene ------------------------------------------------
    fb = bench["arms"]["farneback-cv2"]
    rf = bench["arms"]["raft-small"]
    m["ResGeom"] = _f(fb["a14_rotation_residual_geometry_only_px"], 2)
    m["ResFarneback"] = _f(fb["a14_rotation_residual_px"], 2)
    m["ResRaft"] = _f(rf["a14_rotation_residual_px"], 2)

    # ----- what the shelf costs in HAL (illustrative propagation, not a measurement) ----------
    rows = []
    duty = floor["assumptions"]["duty_cycle_pct_for_pricing"]
    for speed_disp in (11.399, 22.794, 34.181):
        s_true = speed_at[speed_disp]
        g = f960[speed_disp]
        h_true = hal_akkas_2015(s_true, duty)
        h_mean = hal_akkas_2015(s_true * g["mean"], duty)
        h_lo = hal_akkas_2015(s_true * g["min"], duty)
        h_hi = hal_akkas_2015(s_true * g["max"], duty)
        tag = "in" if AKKAS_2015_RANGE.x_lo <= s_true <= AKKAS_2015_RANGE.x_hi else "out"
        rows.append(
            f"{_f(s_true, 0)}{'' if tag == 'in' else '$^{*}$'} & {_f(g['mean'], 2)} & "
            f"{_f(h_true, 2)} & {_f(h_mean, 2)} & {_f(h_lo, 2)}--{_f(h_hi, 2)} & "
            f"{_f(h_true - h_mean, 2)} \\\\")
        key = {11.399: "Lo", 22.794: "Mid", 34.181: "Hi"}[speed_disp]
        m[f"HalTrue{key}"] = _f(h_true, 1)
        m[f"HalLossMean{key}"] = _f(h_true - h_mean, 1)
        m[f"HalLossSmall{key}"] = _f(h_true - h_hi, 1)
        m[f"HalLossLarge{key}"] = _f(h_true - h_lo, 1)
        m[f"SpeedRow{key}"] = _f(s_true, 0)
    files["tab_hal.tex"] = (
        "\\begin{tabular}{@{}rrrrcr@{}}\n\\toprule\n"
        "True speed (mm/s) & mean gain & HAL, true & HAL, recovered & "
        "HAL, seed range & loss (mean) \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ----- the card -----------------------------------------------------------------------------
    rows = []
    status_count: dict[str, int] = {}
    for c in card["claims"]:
        st = c["status"]
        status_count[st] = status_count.get(st, 0) + 1
        rows.append(f"{c['id']} & {st.lower()} & {c['statement']} \\\\")
    m["CardVerdict"] = card["verdict"].replace("_", "\\_")
    m["CardUntested"] = str(status_count.get("UNTESTED", 0))
    m["CardClaims"] = str(len(card["claims"]))
    files["tab_card.tex"] = (
        "\\begin{tabular}{@{}llp{9.2cm}@{}}\n\\toprule\n"
        "Claim & status & statement \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ----- figures ------------------------------------------------------------------------------
    def coords(rows: list[tuple[float, float]]) -> str:
        return " ".join(f"({d},{g})" for d, g in rows)

    def band(arm: dict[str, Any]) -> tuple[str, str, str]:
        mean = coords([(c["hand_displacement_px"], c["mean"]) for c in arm["by_displacement"]])
        lo = coords([(c["hand_displacement_px"], c["min"]) for c in arm["by_displacement"]])
        hi = coords([(c["hand_displacement_px"], c["max"]) for c in arm["by_displacement"]])
        return mean, lo, hi

    fm, fl, fh = band(far)
    rm, rl, rh = band(raft)
    publine = coords([(d, g) for d, g in zip(disp, pub["gains"])])
    files["fig_gain.tex"] = (
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.92\\linewidth,height=6.4cm,xmode=log,"
        "xlabel={hand displacement between the two frames (px)},"
        "ylabel={gain: recovered / true flow},ymin=0,ymax=1.15,xmin=5,xmax=180,"
        "legend style={at={(0.02,0.02)},anchor=south west,font=\\small,draw=none,fill=none},"
        "grid=both,grid style={gray!15}]\n"
        f"\\addplot[name path=fl,draw=none,forget plot] coordinates {{{fl}}};\n"
        f"\\addplot[name path=fh,draw=none,forget plot] coordinates {{{fh}}};\n"
        "\\addplot[blue!25,forget plot] fill between[of=fl and fh];\n"
        f"\\addplot[name path=rl,draw=none,forget plot] coordinates {{{rl}}};\n"
        f"\\addplot[name path=rh,draw=none,forget plot] coordinates {{{rh}}};\n"
        "\\addplot[orange!30,forget plot] fill between[of=rl and rh];\n"
        f"\\addplot[blue!80!black,thick,mark=*,mark size=1.4pt] coordinates {{{fm}}};\n"
        "\\addlegendentry{Farneback, mean of seeds}\n"
        f"\\addplot[orange!85!black,thick,mark=square*,mark size=1.4pt] coordinates {{{rm}}};\n"
        "\\addlegendentry{RAFT-small, mean of seeds}\n"
        f"\\addplot[black,dashed,thin,mark=x,mark size=1.6pt] coordinates {{{publine}}};\n"
        "\\addlegendentry{Farneback, the one published seed}\n"
        f"\\addplot[gray,dotted,thick] coordinates {{(5,{ratio})(180,{ratio})}};\n"
        "\\addlegendentry{hand distance / background distance}\n"
        "\\end{axis}\n\\end{tikzpicture}\n")

    lines = []
    for s in fine["per_seed"]:
        pts = coords([(c["hand_displacement_px"], g)
                      for c, g in zip(fine["by_displacement"], s["gains"])])
        lines.append(f"\\addplot[gray!55,thin] coordinates {{{pts}}};")
    fmean = coords([(c["hand_displacement_px"], c["mean"]) for c in fine["by_displacement"]])
    files["fig_fine.tex"] = (
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.92\\linewidth,height=5.6cm,"
        "xlabel={hand displacement between the two frames (px)},"
        "ylabel={gain},ymin=0,ymax=1.15,"
        "grid=both,grid style={gray!15}]\n"
        + "\n".join(lines) + "\n"
        f"\\addplot[blue!80!black,very thick] coordinates {{{fmean}}};\n"
        "\\end{axis}\n\\end{tikzpicture}\n")

    colours = {"480": "red!70!black", "960": "blue!80!black", "1440": "green!50!black",
               "1920": "violet"}
    parts = []
    for w, col in colours.items():
        a = seeds["farneback_by_width"][w]
        pts = coords([(c["hand_displacement_px"], c["mean"]) for c in a["by_displacement"]])
        parts.append(f"\\addplot[{col},thick,mark=*,mark size=1.2pt] coordinates {{{pts}}};\n"
                     f"\\addlegendentry{{{w} wide}}")
    files["fig_width.tex"] = (
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.92\\linewidth,height=6cm,xmode=log,"
        "xlabel={hand displacement between the two frames (px)},"
        "ylabel={gain, mean of seeds},ymin=0,ymax=1.15,"
        "legend style={at={(0.98,0.98)},anchor=north east,font=\\small,draw=none,fill=none},"
        "grid=both,grid style={gray!15}]\n" + "\n".join(parts) + "\n"
        "\\end{axis}\n\\end{tikzpicture}\n")

    # ----- the macros ----------------------------------------------------------------------------
    files["numbers.tex"] = "% generated by scripts/export_paper_tables.py; do not edit\n" + "".join(
        f"\\newcommand{{\\cg{k}}}{{{v}}}\n" for k, v in sorted(m.items()))
    return files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    files = build()
    if args.check:
        bad = [n for n, t in files.items()
               if not (OUT / n).exists() or (OUT / n).read_text() != t]
        for n in bad:
            print(f"stale or missing: paper/generated/{n}", file=sys.stderr)
        return 1 if bad else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n, t in files.items():
        (OUT / n).write_text(t)
    print(f"wrote {len(files)} files to paper/generated/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
