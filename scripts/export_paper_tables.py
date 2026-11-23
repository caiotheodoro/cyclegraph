"""Write every figure, table and number in paper/cyclegraph.tex from the committed artifacts.

The paper's prose holds no artifact number. It names a macro (`\\cgHalfFineMean`) and this script
defines it, from `results/*.json`, `MEASUREMENT_CARD.json` or a code constant. `tests/test_paper.py`
regenerates the files in memory and fails if the committed copies differ, and fails if the prose
contains a bare number that is not on its short allowlist. A number cannot be typed into the
paper, only produced here.

    python3 scripts/export_paper_tables.py            # rewrite paper/generated/
    python3 scripts/export_paper_tables.py --check    # exit 1 if the committed files differ
"""

from __future__ import annotations

import argparse
import datetime as _dt
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
    CORPUS_CAMERA,
    HAND_DISTANCE_M,
)

OUT = ROOT / "paper" / "generated"
HAL_BOUND = 0.25


def _load(name: str) -> Any:
    return json.loads((ROOT / name).read_text())


def _f(x: float, nd: int) -> str:
    return f"{x:.{nd}f}"


def _pct(x: float, nd: int = 1) -> str:
    return f"{100.0 * x:.{nd}f}"


def _coords(rows: list[tuple[float, float]]) -> str:
    return " ".join(f"({d:.3f},{g:.4f})" for d, g in rows)


def _band(arm: dict[str, Any]) -> tuple[str, str, str]:
    mean = _coords([(c["hand_displacement_px"], c["mean"]) for c in arm["by_displacement"]])
    lo = _coords([(c["hand_displacement_px"], c["min"]) for c in arm["by_displacement"]])
    hi = _coords([(c["hand_displacement_px"], c["max"]) for c in arm["by_displacement"]])
    return mean, lo, hi


def _build_geometry_figure(ratio: float) -> str:
    """Pure vector TikZ schematic of the two-plane fisheye geometry and ego-motion disparity."""
    return (
        "\\begin{tikzpicture}[>=Latex,font=\\footnotesize]\n"
        "% Camera & fisheye optical axis\n"
        "\\draw[gray!50,dashed] (0,0) -- (11.9,0);\n"
        "\\node[anchor=south east,gray!70!black] at (11.9,0.06) {optical axis ($z$)};\n"
        "% Camera at t0 and t1 (draw C1 first so arrow and label stay clean)\n"
        "\\draw[dashed,blue!65!black,fill=blue!6] (-0.35,1.25) rectangle (0.35,1.85);\n"
        "\\node[anchor=south,blue!75!black] at (0.0,1.88) {$C_1$};\n"
        "\\draw[fill=black!8,thick] (-0.35,-0.32) rectangle (0.35,0.32);\n"
        "\\draw[thick] (0.35,-0.22) -- (0.62,-0.42) -- (0.62,0.42) -- (0.35,0.22);\n"
        "\\node[anchor=north,align=center] at (0.1,-0.45) {Camera $C_0$\\\\(fisheye, $67.9^\\circ$)};\n"
        "\\draw[->,very thick,blue!75!black] (0.0,0.40) -- (0.0,1.18);\n"
        "\\node[anchor=east,align=right,blue!75!black] at (-0.45,0.82) {ego-motion\\\\translation $t$};\n"
        "% Hand plane at Z_hand\n"
        "\\draw[ultra thick,red!75!black] (3.4,-1.05) -- (3.4,1.05);\n"
        "\\node[above,red!75!black,font=\\footnotesize\\bfseries] at (3.4,1.10) {Hand plane};\n"
        "\\node[below,red!75!black,align=center] at (3.4,-1.10) {$Z_{\\mathrm{hand}} = 0.45\\,\\mathrm{m}$\\\\(box width $\\approx 96.6\\,\\mathrm{px}$)};\n"
        "% Background plane at Z_bg\n"
        "\\draw[ultra thick,teal!70!black] (9.4,-2.25) -- (9.4,2.25);\n"
        "\\node[above,teal!70!black,font=\\footnotesize\\bfseries] at (9.4,2.30) {Background plane (workstation wall)};\n"
        "\\node[below,teal!70!black,align=center] at (9.4,-2.30) {$Z_{\\mathrm{bg}} = 2.50\\,\\mathrm{m}$\\\\(mask complement $\\to$ scalar ego-motion)};\n"
        "% Projection rays from C0\n"
        "\\draw[gray!65,thin] (0.62,0) -- (3.4,1.05) -- (9.4,2.25);\n"
        "\\draw[gray!65,thin] (0.62,0) -- (3.4,-1.05) -- (9.4,-2.25);\n"
        "% Apparent flow arrows on image plane\n"
        "\\draw[->,very thick,red!75!black] (3.65,-0.12) -- (3.65,-1.02)\n"
        "  node[midway,right,align=left] {hand flow $v_{\\mathrm{hand}}$\\\\($\\propto t/Z_{\\mathrm{hand}}$)};\n"
        "\\draw[->,very thick,teal!70!black] (9.65,-0.15) -- (9.65,-0.62)\n"
        "  node[midway,right,align=left] {background flow $v_{\\mathrm{bg}}$\\\\($\\approx "
        + f"{ratio:.2f}"
        + "\\,v_{\\mathrm{hand}}$)};\n"
        "% Depth ratio callout\n"
        "\\draw[<->,thick,black!70] (0.62,-2.85) -- (3.4,-2.85) node[midway,below] {$Z_{\\mathrm{hand}}$};\n"
        "\\draw[<->,thick,black!70] (0.62,-3.45) -- (9.4,-3.45) node[midway,below] {$Z_{\\mathrm{bg}}$\\quad(depth ratio $Z_{\\mathrm{hand}}/Z_{\\mathrm{bg}} = "
        + f"{ratio:.2f}"
        + "$)};\n"
        "\\end{tikzpicture}\n"
    )


def _build_flowfield_figure(v2: dict[str, Any]) -> str:
    """Figure 2: 1D centerline horizontal flow profiles (11.4 vs 68.0 px) + 2D quiver fields at 68.0 px."""
    snaps = {s["translation_m"]: s for s in v2["experiment_a_flow_field"]["snapshots_seed11"]}
    s_lo = snaps[0.01]
    s_hi = snaps[0.06]
    box = s_hi["box"]
    x0, x1 = box["x0"], box["x1"]
    y0, y1 = box["y0"], box["y1"]

    def prof_coords(snap: dict[str, Any], key: str) -> str:
        xs = snap["centerline_profile"]["x"]
        ys = snap["centerline_profile"][key]
        # Negate u_x so leftward camera-induced flow plots as positive speed along motion axis.
        return " ".join(f"({x:.0f},{-u:.2f})" for x, u in zip(xs, ys))

    est_styles = [
        ("true_ux", "black,very thick", "True flow"),
        ("farneback-cv2", "blue!80!black,thick", "Farneback"),
        ("dis-medium", "green!55!black,thick,densely dashed", "DIS"),
        ("raft-small", "orange!85!black,thick,densely dotted", "RAFT-small"),
        ("raft-large", "red!75!black,thick", "RAFT-large"),
    ]

    p_lo_plots = "\n".join(
        f"\\addplot[{st}] coordinates {{{prof_coords(s_lo, k)}}};\n\\addlegendentry{{{lbl}}}"
        for k, st, lbl in est_styles
    )
    p_hi_plots = "\n".join(
        f"\\addplot[{st}] coordinates {{{prof_coords(s_hi, k)}}};"
        for k, st, _ in est_styles
    )

    # 2D quiver panels at 68.0 px (Farneback vs RAFT-large) overlaid on true vectors.
    def quiver_panel(est_key: str, title: str, color: str) -> str:
        # Subsample every 2nd grid coordinate (32 px spacing -> ~64 clean readable arrows)
        # while keeping interior box arrows dense enough to read clearly.
        q_true = s_hi["quiver_true"]
        q_est = s_hi["quiver_estimated"][est_key]
        scale = 0.42
        xmin = x0 - 64.0
        xmax = x1 + 64.0
        ymin = y0 - 64.0
        ymax = y1 + 64.0
        lines = [
            "\\begin{tikzpicture}[x=0.024cm,y=-0.024cm,>={Latex[length=3pt,width=2pt]}]",
            f"\\draw[black!70,thin] ({xmin:.1f},{ymin:.1f}) rectangle ({xmax:.1f},{ymax:.1f});",
            f"\\fill[gray!10] ({x0:.1f},{y0:.1f}) rectangle ({x1:.1f},{y1:.1f});",
            f"\\draw[black,dashed,thick] ({x0:.1f},{y0:.1f}) rectangle ({x1:.1f},{y1:.1f});",
        ]
        # Pick every other row/col on the 16 px grid -> 32 px stride (zero overlap!)
        for idx, (pt, ev) in enumerate(zip(q_true, q_est)):
            x, y, tx, ty, _in_box = pt
            # Grid is 15x15 = 225 points; select even row & col indices (8x8 = 64 arrows)
            r_i, c_i = divmod(idx, 15)
            if (r_i % 2 != 0) or (c_i % 2 != 0):
                continue
            rx, ry = ev
            lines.append(
                f"\\draw[->,gray!55,line width=0.55pt] ({x:.1f},{y:.1f}) -- ({x + scale * tx:.1f},{y + scale * ty:.1f});"
            )
            lines.append(
                f"\\draw[->,{color},line width=0.75pt] ({x:.1f},{y:.1f}) -- ({x + scale * rx:.1f},{y + scale * ry:.1f});"
            )
        lines.append(
            f"\\node[anchor=south,font=\\footnotesize\\bfseries] at ({(xmin+xmax)/2:.1f},{ymin - 8:.1f}) {{{title}}};"
        )
        lines.append(
            f"\\node[anchor=north east,font=\\scriptsize,fill=white,inner sep=1.5pt] at ({xmax - 4:.1f},{ymax - 4:.1f}) {{dashed: hand box; gray: true; color: est.}};"
        )
        lines.append("\\end{tikzpicture}")
        return "\n".join(lines)

    q_far = quiver_panel("farneback-cv2", "(c) 2D flow at 68.0 px: Farneback", "blue!80!black")
    q_rl = quiver_panel("raft-large", "(d) 2D flow at 68.0 px: RAFT-large", "red!75!black")

    return (
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n"
        "\\begin{axis}[width=0.95\\linewidth,height=4.7cm,"
        "title={\\footnotesize\\textbf{(a) Centerline profile before knee (11.4 px)}},"
        "xlabel={\\footnotesize horizontal pixel $x$},"
        "ylabel={\\footnotesize $-u_x$ (px)},"
        f"xmin={s_lo['centerline_profile']['x'][0]:.0f},xmax={s_lo['centerline_profile']['x'][-1]:.0f},"
        "ymin=-2,ymax=14.5,"
        "legend style={at={(0.02,0.98)},anchor=north west,font=\\tiny,draw=none,fill=white,fill opacity=0.85,inner sep=1pt},"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        f"\\fill[gray!12] (axis cs:{x0:.1f},-2) rectangle (axis cs:{x1:.1f},14.5);\n"
        f"\\draw[gray!60,dashed] (axis cs:{x0:.1f},-2) -- (axis cs:{x0:.1f},14.5);\n"
        f"\\draw[gray!60,dashed] (axis cs:{x1:.1f},-2) -- (axis cs:{x1:.1f},14.5);\n"
        + p_lo_plots + "\n"
        "\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n"
        "\\begin{axis}[width=0.95\\linewidth,height=4.7cm,"
        "title={\\footnotesize\\textbf{(b) Centerline profile past knee (68.0 px)}},"
        "xlabel={\\footnotesize horizontal pixel $x$},"
        "ylabel={\\footnotesize $-u_x$ (px)},"
        f"xmin={s_hi['centerline_profile']['x'][0]:.0f},xmax={s_hi['centerline_profile']['x'][-1]:.0f},"
        "ymin=-20,ymax=76,"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        f"\\fill[gray!12] (axis cs:{x0:.1f},-20) rectangle (axis cs:{x1:.1f},76);\n"
        f"\\draw[gray!60,dashed] (axis cs:{x0:.1f},-20) -- (axis cs:{x0:.1f},76);\n"
        f"\\draw[gray!60,dashed] (axis cs:{x1:.1f},-20) -- (axis cs:{x1:.1f},76);\n"
        + p_hi_plots + "\n"
        "\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\n\n"
        "\\vspace{4pt}\n"
        "\\begin{minipage}{0.49\\linewidth}\\centering\n"
        + q_far + "\n"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\\centering\n"
        + q_rl + "\n"
        "\\end{minipage}\n"
    )


def _build_gain_v2_figure(seeds: dict[str, Any], v2: dict[str, Any], ratio: float) -> str:
    """Figure 3: Four-estimator gain vs displacement: (a) ego-motion, (b) static-camera control."""
    far_ego = seeds["farneback_by_width"]["960"]
    rafts_ego = seeds["raft"]["by_width"]["960"]
    dis_ego = v2["additional_estimators_ego_motion"]["dis-medium"]["grid_9pt"]
    raftl_ego = v2["additional_estimators_ego_motion"]["raft-large"]["grid_9pt"]

    st = v2["experiment_b_static_camera"]

    def panel(arms: list[tuple[dict[str, Any], str, str, str]], title: str, show_legend: bool,
              show_ratio: bool) -> str:
        body = []
        for idx, (arm, col, mark, lbl) in enumerate(arms):
            mean, lo, hi = _band(arm)
            body.append(f"\\addplot[name path=lo{idx},draw=none,forget plot] coordinates {{{lo}}};")
            body.append(f"\\addplot[name path=hi{idx},draw=none,forget plot] coordinates {{{hi}}};")
            body.append(f"\\addplot[{col}!18,forget plot] fill between[of=lo{idx} and hi{idx}];")
        for arm, col, mark, lbl in arms:
            mean, _, _ = _band(arm)
            body.append(
                f"\\addplot[{col},thick,mark={mark},mark size=1.4pt] coordinates {{{mean}}};"
            )
            if show_legend:
                body.append(f"\\addlegendentry{{{lbl}}}")
        if show_ratio:
            body.append(
                f"\\addplot[black!60,dotted,thick] coordinates {{(5,{ratio:.4f})(180,{ratio:.4f})}};"
            )
            if show_legend:
                body.append("\\addlegendentry{depth ratio (0.18)}")
        else:
            body.append("\\addplot[black!60,dotted,thick] coordinates {(5,0)(180,0)};")
        leg = (
            "legend style={at={(0.02,0.02)},anchor=south west,font=\\tiny,draw=none,fill=white,fill opacity=0.85,inner sep=1.5pt},"
            if show_legend else ""
        )
        return (
            "\\begin{tikzpicture}\n"
            "\\begin{axis}[width=0.95\\linewidth,height=5.6cm,xmode=log,"
            f"title={{\\footnotesize\\textbf{{{title}}}}},"
            "xlabel={\\footnotesize hand displacement (px)},"
            "ylabel={\\footnotesize gain (recovered / true)},"
            "ymin=-0.03,ymax=1.12,xmin=5,xmax=180,"
            + leg
            + "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
            + "\n".join(body) + "\n"
            "\\end{axis}\n\\end{tikzpicture}\n"
        )

    ego_arms = [
        (far_ego, "blue!80!black", "*", "Farneback (20 seeds)"),
        (dis_ego, "green!55!black", "triangle*", "DIS-medium (20 seeds)"),
        (rafts_ego, "orange!85!black", "square*", "RAFT-small (11 seeds)"),
        (raftl_ego, "red!75!black", "diamond*", "RAFT-large (11 seeds)"),
    ]
    stat_arms = [
        (st["farneback-cv2"], "blue!80!black", "*", "Farneback"),
        (st["dis-medium"], "green!55!black", "triangle*", "DIS-medium"),
        (st["raft-small"], "orange!85!black", "square*", "RAFT-small"),
        (st["raft-large"], "red!75!black", "diamond*", "RAFT-large"),
    ]
    return (
        "\\begin{minipage}{0.49\\linewidth}\n"
        + panel(ego_arms, "(a) Moving camera, static scene (ego-motion)", True, True)
        + "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        + panel(stat_arms, "(b) Static camera, moving hand (control)", False, False)
        + "\\end{minipage}\n"
    )


def _build_sweeps_figure(v2: dict[str, Any]) -> str:
    """Figure 5: Four-panel parameter sweeps (depth ratio, box size, motion blur, sensor noise)."""
    sw = v2["experiment_d_sweeps"]
    styles = [
        ("farneback-cv2", "blue!80!black", "*", "Farneback"),
        ("dis-medium", "green!55!black", "triangle*", "DIS"),
        ("raft-small", "orange!85!black", "square*", "RAFT-small"),
    ]

    # (a) Depth ratio: observed shelf vs true depth ratio
    p_depth = ["\\addplot[black!60,dashed,thin] coordinates {(0.08,0.08)(0.54,0.54)};\n\\addlegendentry{$y=x$ (depth ratio)}"]
    for key, col, mk, lbl in styles:
        pts = _coords([(r["depth_ratio"], r["floor_gain"]["mean"]) for r in sw["depth_ratio"][key]])
        p_depth.append(f"\\addplot[{col},thick,mark={mk},mark size=1.5pt] coordinates {{{pts}}};\n\\addlegendentry{{{lbl}}}")

    # (b) Box size: half-crossing vs box width
    p_box = []
    for key, col, mk, _ in styles:
        pts = _coords([(r["hand_box_width_px"], r["half_crossing_px"]["mean"]) for r in sw["box_size"][key]])
        p_box.append(f"\\addplot[{col},thick,mark={mk},mark size=1.5pt] coordinates {{{pts}}};")

    # (c) Motion blur: half-crossing vs blur kernel
    p_blur = []
    for key, col, mk, _ in styles:
        pts = _coords([(float(r["blur_kernel_px"]), r["half_crossing_px"]["mean"]) for r in sw["motion_blur"][key]])
        p_blur.append(f"\\addplot[{col},thick,mark={mk},mark size=1.5pt] coordinates {{{pts}}};")

    # (d) Sensor noise: half-crossing vs sigma
    p_noise = []
    for key, col, mk, _ in styles:
        pts = _coords([(float(r["noise_sigma"]), r["half_crossing_px"]["mean"]) for r in sw["sensor_noise"][key]])
        p_noise.append(f"\\addplot[{col},thick,mark={mk},mark size=1.5pt] coordinates {{{pts}}};")

    return (
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.95\\linewidth,height=4.5cm,"
        "title={\\footnotesize\\textbf{(a) Depth ratio vs.\\ post-knee shelf}},"
        "xlabel={\\footnotesize true depth ratio $Z_{\\mathrm{hand}}/Z_{\\mathrm{bg}}$},"
        "ylabel={\\footnotesize observed shelf gain},xmin=0.06,xmax=0.54,ymin=0.06,ymax=0.54,"
        "legend style={at={(0.02,0.98)},anchor=north west,font=\\tiny,draw=none,fill=white,fill opacity=0.85,inner sep=1pt},"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(p_depth) + "\n\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.95\\linewidth,height=4.5cm,"
        "title={\\footnotesize\\textbf{(b) Hand box width vs.\\ half-crossing}},"
        "xlabel={\\footnotesize hand box width (px)},"
        "ylabel={\\footnotesize half-crossing (px)},xmin=40,xmax=200,ymin=10,ymax=120,"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(p_box) + "\n\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\n\n"
        "\\vspace{4pt}\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.95\\linewidth,height=4.5cm,"
        "title={\\footnotesize\\textbf{(c) Horizontal motion blur vs.\\ crossing}},"
        "xlabel={\\footnotesize 1D blur kernel length (px)},"
        "ylabel={\\footnotesize half-crossing (px)},xmin=-1,xmax=22,ymin=20,ymax=90,"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(p_blur) + "\n\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.95\\linewidth,height=4.5cm,"
        "title={\\footnotesize\\textbf{(d) Gaussian sensor noise vs.\\ crossing}},"
        "xlabel={\\footnotesize noise $\\sigma$ (intensity levels, 0--255)},"
        "ylabel={\\footnotesize half-crossing (px)},xmin=-1,xmax=32,ymin=20,ymax=50,"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(p_noise) + "\n\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\n"
    )


def build() -> dict[str, str]:
    seeds = _load("results/flow_gain_seeds.json")
    v2 = _load("results/flow_gain_v2.json")
    floor = _load("results/a14_translation_floor.json")
    native = _load("results/flow_gain_by_resolution.json")
    bench = _load("results/flow_benchmark.json")
    card = _load("MEASUREMENT_CARD.json")
    vendor = _load("results/vendor_claim.json")
    prov = _load("results/provenance.json")
    raft480 = _load("results/flow_gain_raft.json")["scales"][0]["rows"][0]

    files: dict[str, str] = {}
    m: dict[str, str] = {}

    # ----- vendor & sibling context (Appendix A) -------------------------------------------------
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

    # ----- provenance of registration & novelty rerun (Appendix A) -------------------------------
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

    # ----- geometry and error budget -------------------------------------------------------------
    ratio = HAND_DISTANCE_M / BACKGROUND_DISTANCE_M
    m["Ratio"] = _f(ratio, 2)
    m["FxNom"] = _f(CORPUS_CAMERA.fx, 0)
    m["FyNom"] = _f(CORPUS_CAMERA.fy, 0)
    m["JumpFracEgo"] = _f(1.0 - ratio, 2)
    m["JumpRatioPct"] = _f(100.0 * (1.0 / (1.0 - ratio) - 1.0), 0)
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
    narrow = {
        r["rotation_deg_per_s"]: r["floor_mm_s"]
        for r in floor["rotation_only_narrow_lens_control"]
    }
    m["RotFisheye"] = _f(rot[10.0], 1)
    m["RotNarrow"] = _f(narrow[10.0], 2)
    m["RotRatio"] = _f(rot[10.0] / narrow[10.0], 0)
    lens = floor["lens"]
    m["HalfAngle"] = _f(lens["max_half_angle_deg"], 1)

    # ----- A14 floor table -----------------------------------------------------------------------
    rows = []
    for deg in (2.0, 10.0, 30.0, 60.0):
        rows.append(f"{deg:.0f} & {_f(rot[deg], 2)} & {_f(narrow[deg], 2)} \\\\")
    files["tab_floor.tex"] = (
        "\\begin{tabular}{@{}rrr@{}}\n\\toprule\n"
        "Head rotation (deg/s) & Corpus fisheye (mm/s) & Narrow lens (mm/s) \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    )
    trans = {r["translation_m_per_s"]: r["floor_mm_s"] for r in floor["translation_only_corpus_lens"]}
    m["TransFloorFive"] = _f(trans[0.05], 1)

    # ----- baseline seed spread (flow_gain_seeds.json) -------------------------------------------
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
    m["HalfFarMin"] = _f(far["half_crossing_px"]["min"], 1)
    m["HalfFarMax"] = _f(far["half_crossing_px"]["max"], 1)
    lc = prov["lens_check"]
    m["LensChecked"] = str(lc["calibration_files_compared"])
    m["LensShipped"] = f"{lc['workers_shipped']:,}".replace(",", "{,}")

    # Verify every measurement returned a finite field (baseline + v2)
    published_rows = [
        r
        for f in ("flow_displacement_gain", "flow_gain_raft", "flow_gain_by_resolution")
        for sc in _load(f"results/{f}.json")["scales"]
        for r in sc["rows"]
    ]
    assert not any(r["flow_returned_none"] for r in published_rows)
    seed_gains = [
        g
        for arm in list(seeds["farneback_by_width"].values())
        + [seeds["farneback_fine_960"]]
        + list(seeds["raft"]["by_width"].values())
        for ps in arm["per_seed"]
        for g in ps["gains"]
    ]
    assert all(g is not None for g in seed_gains)
    m["PublishedRows"] = str(len(published_rows))
    m["SeedMeasurements"] = f"{len(seed_gains):,}".replace(",", "{,}")

    # Count total v2 measurements and assert all finite
    v2_count = 0
    for block in v2["additional_estimators_ego_motion"].values():
        for arm in block.values():
            assert arm["all_finite"]
            v2_count += sum(len(ps["gains"]) for ps in arm["per_seed"])
    for arm in v2["experiment_b_static_camera"].values():
        assert arm["all_finite"]
        v2_count += sum(len(ps["gains"]) for ps in arm["per_seed"])
    for est_rows in v2["experiment_a_flow_field"]["metrics_by_estimator"].values():
        v2_count += sum(r["n_seeds"] for r in est_rows)
    v2_count += len(v2["a14_rotation_residuals"]["by_estimator"]) * len(
        v2["a14_rotation_residuals"]["seeds"]
    )
    for sdict in v2["experiment_d_sweeps"].values():
        for est_name, est_rows in sdict.items():
            assert all(r["all_finite"] for r in est_rows)
            n_s = 10 if est_name in ("farneback-cv2", "dis-medium") else 5
            v2_count += len(est_rows) * n_s * 9
    m["VTwoMeasurements"] = f"{v2_count:,}".replace(",", "{,}")
    m["TotalMeasurements"] = f"{len(seed_gains) + v2_count:,}".replace(",", "{,}")

    rp = next(
        sc for sc in _load("results/flow_gain_raft.json")["scales"] if sc["frame_size"][0] == 960
    )
    rs = next(x for x in raft["per_seed"] if x["seed"] == seeds["published_seed"])
    m["RaftDevGap"] = _f(max(abs(r["gain"] - g) for r, g in zip(rp["rows"], rs["gains"])), 4)
    m["RaftMpsGap"] = _f(v2["device_parity"]["raft_small_max_abs_gain_diff"], 6)
    m["HalfRaftMean"] = _f(raft["half_crossing_px"]["mean"], 1)
    m["HalfRaftSd"] = _f(raft["half_crossing_px"]["sd"], 1)
    m["HalfRaftMin"] = _f(raft["half_crossing_px"]["min"], 1)
    m["HalfRaftMax"] = _f(raft["half_crossing_px"]["max"], 1)

    def by_disp(arm: dict[str, Any]) -> dict[float, dict[str, Any]]:
        return {c["hand_displacement_px"]: c for c in arm["by_displacement"]}

    f960, r960 = by_disp(far), by_disp(raft)
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
    m["DispShelfProbe"] = _f(68.025, 1)
    m["DispPreKnee"] = _f(11.399, 1)
    m["DispMax"] = _f(disp[-1], 1)
    m["RaftAfterMean"] = _f(r960[34.181]["mean"], 2)
    m["RaftGainSmallMean"] = _f(r960[disp[0]]["mean"], 2)
    m["RaftGainSmallSd"] = _f(r960[disp[0]]["sd"], 2)

    nat960 = next(s for s in native["scales"] if s["frame_size"][0] == 960)
    speed_at = {r["hand_displacement_px"]: r["true_speed_mm_s"] for r in nat960["rows"]}
    m["SpeedAtKnee"] = _f(speed_at[22.794], 0)
    m["SpeedAfter"] = _f(speed_at[34.181], 0)
    m["PairInterval"] = _f(1000 * native["pair_interval_s"], 0)
    m["MmPerPx"] = _f(nat960["mm_per_px"], 2)
    m["BoxWidthNom"] = _f(nat960["hand_box_width_px"], 1)
    px_at_median = 612.4 * native["pair_interval_s"] / nat960["mm_per_px"]
    m["PxAtMedian"] = _f(px_at_median, 0)

    # ----- v2 Estimator & static-camera macros + Table 2 -----------------------------------------
    dis_ego = v2["additional_estimators_ego_motion"]["dis-medium"]["grid_9pt"]
    rl_ego = v2["additional_estimators_ego_motion"]["raft-large"]["grid_9pt"]
    st = v2["experiment_b_static_camera"]
    a14 = v2["a14_rotation_residuals"]

    m["HalfDisMean"] = _f(dis_ego["half_crossing_px"]["mean"], 1)
    m["HalfDisSd"] = _f(dis_ego["half_crossing_px"]["sd"], 1)
    m["ShelfDisMean"] = _f(dis_ego["floor_gain"]["mean"], 2)
    m["ShelfDisSd"] = _f(dis_ego["floor_gain"]["sd"], 2)
    m["HalfRaftLargeMean"] = _f(rl_ego["half_crossing_px"]["mean"], 1)
    m["HalfRaftLargeSd"] = _f(rl_ego["half_crossing_px"]["sd"], 1)
    m["ShelfRaftLargeMean"] = _f(rl_ego["floor_gain"]["mean"], 2)
    m["ShelfRaftLargeSd"] = _f(rl_ego["floor_gain"]["sd"], 3)
    m["DelayMinPx"] = _f(rl_ego["half_crossing_px"]["mean"] - far["half_crossing_px"]["mean"], 0)
    m["DelayMaxPx"] = _f(dis_ego["half_crossing_px"]["mean"] - far["half_crossing_px"]["mean"], 0)

    m["StaticHalfFar"] = _f(st["farneback-cv2"]["half_crossing_px"]["mean"], 1)
    m["StaticHalfDis"] = _f(st["dis-medium"]["half_crossing_px"]["mean"], 1)
    m["StaticHalfRaftS"] = _f(st["raft-small"]["half_crossing_px"]["mean"], 1)
    m["StaticHalfRaftL"] = _f(st["raft-large"]["half_crossing_px"]["mean"], 1)
    m["StaticFloorFar"] = _f(st["farneback-cv2"]["post_68px_median_gain"]["mean"], 3)
    m["StaticFloorDis"] = _f(st["dis-medium"]["post_68px_median_gain"]["mean"], 3)
    m["StaticFloorRaftS"] = _f(st["raft-small"]["post_68px_median_gain"]["mean"], 4)
    m["StaticFloorRaftL"] = _f(st["raft-large"]["post_68px_median_gain"]["mean"], 4)

    m["ShiftPctFar"] = _f(
        100.0 * (1.0 - st["farneback-cv2"]["half_crossing_px"]["mean"] / far["half_crossing_px"]["mean"]),
        0,
    )
    m["ShiftPctDis"] = _f(
        100.0 * (1.0 - st["dis-medium"]["half_crossing_px"]["mean"] / dis_ego["half_crossing_px"]["mean"]),
        0,
    )
    m["ShiftPctRaftS"] = _f(
        100.0 * (1.0 - st["raft-small"]["half_crossing_px"]["mean"] / raft["half_crossing_px"]["mean"]),
        0,
    )
    m["ShiftPctRaftL"] = _f(
        100.0 * (1.0 - st["raft-large"]["half_crossing_px"]["mean"] / rl_ego["half_crossing_px"]["mean"]),
        0,
    )

    m["AOneFourGeom"] = _f(a14["geometry_only_px"], 2)
    m["AOneFourFar"] = _f(a14["by_estimator"]["farneback-cv2"]["mean"], 2)
    m["AOneFourDis"] = _f(a14["by_estimator"]["dis-medium"]["mean"], 2)
    m["AOneFourRaftS"] = _f(a14["by_estimator"]["raft-small"]["mean"], 2)
    m["AOneFourRaftSSd"] = _f(a14["by_estimator"]["raft-small"]["sd"], 3)
    m["AOneFourRaftL"] = _f(a14["by_estimator"]["raft-large"]["mean"], 2)

    est_rows = []
    for label, ego_arm, key in (
        ("Farneback", far, "farneback-cv2"),
        ("DIS-medium", dis_ego, "dis-medium"),
        ("RAFT-small", raft, "raft-small"),
        ("RAFT-large", rl_ego, "raft-large"),
    ):
        sa = st[key]
        a14e = a14["by_estimator"][key]
        eh = ego_arm["half_crossing_px"]
        ef = ego_arm["floor_gain"]
        sh = sa["half_crossing_px"]
        sf = sa["post_68px_median_gain"]
        est_rows.append(
            f"{label} & {ego_arm['n_seeds']} & "
            f"{_f(eh['mean'], 1)} $\\pm$ {_f(eh['sd'], 1)} & "
            f"{_f(ef['mean'], 2)} $\\pm$ {_f(ef['sd'], 2)} & "
            f"{_f(sh['mean'], 1)} $\\pm$ {_f(sh['sd'], 1)} & "
            f"{_f(sf['mean'], 3)} & "
            f"{_f(a14e['mean'], 2)} $\\pm$ {_f(a14e['sd'], 2)} \\\\"
        )
    files["tab_estimators.tex"] = (
        "\\begin{tabular}{@{}lrccccc@{}}\n\\toprule\n"
        " & & \\multicolumn{2}{c}{Ego-motion (depth ratio 0.18)} & "
        "\\multicolumn{2}{c}{Static camera (bg $= 0$)} & A14 rot. \\\\\n"
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\n"
        "Estimator & Seeds & $d_{0.5}$ (px) & Shelf gain & $d_{0.5}$ (px) & Post-68 px gain & resid. (px) \\\\\n\\midrule\n"
        + "\n".join(est_rows)
        + f"\n\\midrule\nExact geometry & --- & --- & 0.18 & --- & 0.000 & {_f(a14['geometry_only_px'], 2)} \\\\\n"
        "\\bottomrule\n\\end{tabular}\n"
    )

    # ----- Experiment A: pixel-level flow-field macros + Table 1 ---------------------------------
    exp_a = v2["experiment_a_flow_field"]["metrics_by_estimator"]
    a_by = {
        k: {r["translation_m"]: r for r in rows_list} for k, rows_list in exp_a.items()
    }
    m["FieldCloserBgMin"] = _pct(min(a_by[k][0.06]["frac_closer_to_bg"]["mean"] for k in a_by))
    m["FieldCloserBgMax"] = _pct(max(a_by[k][0.06]["frac_closer_to_bg"]["mean"] for k in a_by))
    m["FieldLockedBgMin"] = _pct(min(a_by[k][0.06]["frac_locked_bg"]["mean"] for k in a_by))
    m["FieldLockedBgMax"] = _pct(max(a_by[k][0.06]["frac_locked_bg"]["mean"] for k in a_by))
    m["FieldLockedHandPreMin"] = _pct(min(a_by[k][0.01]["frac_locked_hand"]["mean"] for k in a_by))
    m["FieldLockedHandPreMax"] = _pct(max(a_by[k][0.01]["frac_locked_hand"]["mean"] for k in a_by))
    m["FieldPreEpeMin"] = _f(min(a_by[k][0.01]["epe_hand_px"]["mean"] for k in a_by), 1)
    m["FieldPreEpeMax"] = _f(max(a_by[k][0.01]["epe_hand_px"]["mean"] for k in a_by), 1)
    m["FieldFarCloserBg"] = _pct(a_by["farneback-cv2"][0.06]["frac_closer_to_bg"]["mean"])
    m["FieldFarLockedBg"] = _pct(a_by["farneback-cv2"][0.06]["frac_locked_bg"]["mean"])
    m["FieldFarRecPct"] = _pct(a_by["farneback-cv2"][0.06]["residual_recovery_ratio"]["mean"])
    m["FieldRaftLCloserBg"] = _pct(a_by["raft-large"][0.06]["frac_closer_to_bg"]["mean"])
    m["FieldRaftLLockedBg"] = _pct(a_by["raft-large"][0.06]["frac_locked_bg"]["mean"])
    m["FieldRaftLEpeBg"] = _f(a_by["raft-large"][0.06]["epe_bg_px"]["mean"], 1)
    m["FieldRaftLEpeHand"] = _f(a_by["raft-large"][0.06]["epe_hand_px"]["mean"], 1)
    m["FieldRaftLResPx"] = _f(a_by["raft-large"][0.06]["pipeline_residual_px"]["mean"], 2)
    m["FieldTrueResHi"] = _f(a_by["raft-large"][0.06]["true_residual_px"], 2)
    m["FieldRecMinPct"] = _pct(min(a_by[k][0.06]["residual_recovery_ratio"]["mean"] for k in a_by))
    m["FieldRecMaxPct"] = _pct(max(a_by[k][0.06]["residual_recovery_ratio"]["mean"] for k in a_by))
    m["FieldPreRecMinPct"] = _pct(min(a_by[k][0.01]["residual_recovery_ratio"]["mean"] for k in a_by))
    m["FieldPreRecMaxPct"] = _pct(max(a_by[k][0.01]["residual_recovery_ratio"]["mean"] for k in a_by))
    m["FieldKneeCloserMin"] = _pct(min(a_by[k][0.02]["frac_closer_to_bg"]["mean"] for k in a_by))
    m["FieldKneeCloserMax"] = _pct(max(a_by[k][0.02]["frac_closer_to_bg"]["mean"] for k in a_by))

    f_rows = []
    for t_m, label_d in ((0.01, "11.4"), (0.02, "22.8"), (0.03, "34.2"), (0.06, "68.0")):
        for idx, (est_lbl, key) in enumerate(
            (
                ("Farneback", "farneback-cv2"),
                ("DIS-medium", "dis-medium"),
                ("RAFT-small", "raft-small"),
                ("RAFT-large", "raft-large"),
            )
        ):
            r = a_by[key][t_m]
            d_col = label_d if idx == 0 else ""
            f_rows.append(
                f"{d_col} & {est_lbl} & {_f(r['gain']['mean'], 2)} & "
                f"{_pct(r['frac_closer_to_bg']['mean'])}\\% & "
                f"{_pct(r['frac_locked_bg']['mean'])}\\% & "
                f"{_f(r['epe_hand_px']['mean'], 1)} & {_f(r['epe_bg_px']['mean'], 1)} & "
                f"{_f(r['cos_sim_hand']['mean'], 2)} & "
                f"{_pct(r['residual_recovery_ratio']['mean'])}\\% \\\\"
            )
        if t_m != 0.06:
            f_rows.append("\\midrule")
    files["tab_field.tex"] = (
        "\\begin{tabular}{@{}rlrrrrrrr@{}}\n\\toprule\n"
        "Disp.\\ (px) & Estimator & Gain & Closer bg & Locked bg & EPE$_{\\mathrm{hand}}$ & "
        "EPE$_{\\mathrm{bg}}$ & $\\cos\\theta$ & Resid.\\ rec. \\\\\n\\midrule\n"
        + "\n".join(f_rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )

    # ----- Experiment D: Parameter sweep macros + Table 3 ----------------------------------------
    sw = v2["experiment_d_sweeps"]
    # Depth ratio macros
    dr_r = {r["depth_ratio"]: r for r in sw["depth_ratio"]["raft-small"]}
    dr_f = {r["depth_ratio"]: r for r in sw["depth_ratio"]["farneback-cv2"]}
    dr_d = {r["depth_ratio"]: r for r in sw["depth_ratio"]["dis-medium"]}
    m["DepthShelfRaftTen"] = _f(dr_r[0.1]["floor_gain"]["mean"], 3)
    m["DepthShelfRaftFifty"] = _f(dr_r[0.5]["floor_gain"]["mean"], 3)
    m["DepthMaxErr"] = _f(
        max(abs(r["floor_gain"]["mean"] - r["depth_ratio"]) for r in sw["depth_ratio"]["raft-small"]),
        2,
    )
    m["DepthHalfFarTen"] = _f(dr_f[0.1]["half_crossing_px"]["mean"], 1)
    m["DepthHalfFarFifty"] = _f(dr_f[0.5]["half_crossing_px"]["mean"], 1)
    m["DepthHalfDisFifty"] = _f(dr_d[0.5]["half_crossing_px"]["mean"], 1)
    m["DepthHalfRaftFifty"] = _f(dr_r[0.5]["half_crossing_px"]["mean"], 1)

    # Box size macros
    bx_f = {r["box_scale"]: r for r in sw["box_size"]["farneback-cv2"]}
    bx_d = {r["box_scale"]: r for r in sw["box_size"]["dis-medium"]}
    bx_r = {r["box_scale"]: r for r in sw["box_size"]["raft-small"]}
    m["BoxWidthSmall"] = _f(bx_f[0.5]["hand_box_width_px"], 1)
    m["BoxWidthLarge"] = _f(bx_f[2.0]["hand_box_width_px"], 1)
    m["BoxHalfFarSmall"] = _f(bx_f[0.5]["half_crossing_px"]["mean"], 1)
    m["BoxHalfFarLarge"] = _f(bx_f[2.0]["half_crossing_px"]["mean"], 1)
    m["BoxHalfDisSmall"] = _f(bx_d[0.5]["half_crossing_px"]["mean"], 1)
    m["BoxHalfDisLarge"] = _f(bx_d[2.0]["half_crossing_px"]["mean"], 1)
    m["BoxHalfRaftSmall"] = _f(bx_r[0.5]["half_crossing_px"]["mean"], 1)
    m["BoxHalfRaftLarge"] = _f(bx_r[2.0]["half_crossing_px"]["mean"], 1)
    box_ratios = [
        r["half_crossing_px"]["mean"] / r["hand_box_width_px"] for r in sw["box_size"]["raft-small"]
    ]
    m["BoxRatioLo"] = _f(min(box_ratios), 2)
    m["BoxRatioHi"] = _f(max(box_ratios), 2)

    # Blur macros
    bl_f = {r["blur_kernel_px"]: r for r in sw["motion_blur"]["farneback-cv2"]}
    bl_d = {r["blur_kernel_px"]: r for r in sw["motion_blur"]["dis-medium"]}
    bl_r = {r["blur_kernel_px"]: r for r in sw["motion_blur"]["raft-small"]}
    m["BlurFarGainZero"] = _f(bl_f[0]["gain_at_5_7px"]["mean"], 2)
    m["BlurFarGainMax"] = _f(bl_f[21]["gain_at_5_7px"]["mean"], 2)
    m["BlurFarHalfZero"] = _f(bl_f[0]["half_crossing_px"]["mean"], 1)
    m["BlurFarHalfMax"] = _f(bl_f[21]["half_crossing_px"]["mean"], 1)
    m["BlurDisHalfMax"] = _f(bl_d[21]["half_crossing_px"]["mean"], 1)
    m["BlurRaftHalfMid"] = _f(bl_r[11]["half_crossing_px"]["mean"], 1)
    m["BlurRaftHalfMax"] = _f(bl_r[21]["half_crossing_px"]["mean"], 1)
    m["BlurRaftGainMax"] = _f(bl_r[21]["gain_at_5_7px"]["mean"], 2)
    blur_shelves = [
        r["floor_gain"]["mean"] for rows_b in sw["motion_blur"].values() for r in rows_b
    ]
    m["BlurShelfMin"] = _f(min(blur_shelves), 2)
    m["BlurShelfMax"] = _f(max(blur_shelves), 2)

    # Noise macros
    ns_f = {r["noise_sigma"]: r for r in sw["sensor_noise"]["farneback-cv2"]}
    ns_d = {r["noise_sigma"]: r for r in sw["sensor_noise"]["dis-medium"]}
    ns_r = {r["noise_sigma"]: r for r in sw["sensor_noise"]["raft-small"]}
    m["NoiseFarGainMax"] = _f(ns_f[30.0]["gain_at_5_7px"]["mean"], 2)
    m["NoiseFarHalfMax"] = _f(ns_f[30.0]["half_crossing_px"]["mean"], 1)
    m["NoiseDisHalfMax"] = _f(ns_d[30.0]["half_crossing_px"]["mean"], 1)
    m["NoiseRaftGainMax"] = _f(ns_r[30.0]["gain_at_5_7px"]["mean"], 2)
    m["NoiseRaftHalfZero"] = _f(ns_r[0.0]["half_crossing_px"]["mean"], 1)
    m["NoiseRaftHalfMax"] = _f(ns_r[30.0]["half_crossing_px"]["mean"], 1)

    sw_rows = []
    # Depth ratio rows
    for idx, rat in enumerate((0.50, 0.30, 0.18, 0.10)):
        cat = "Depth ratio" if idx == 0 else ""
        sw_rows.append(
            f"{cat} & {rat:.2f} & "
            f"{_f(dr_f[rat]['half_crossing_px']['mean'], 1)} & {_f(dr_f[rat]['floor_gain']['mean'], 2)} & "
            f"{_f(dr_d[rat]['half_crossing_px']['mean'], 1)} & {_f(dr_d[rat]['floor_gain']['mean'], 2)} & "
            f"{_f(dr_r[rat]['half_crossing_px']['mean'], 1)} & {_f(dr_r[rat]['floor_gain']['mean'], 2)} \\\\"
        )
    sw_rows.append("\\midrule")
    # Box size rows
    for idx, sc_v in enumerate((0.5, 0.75, 1.0, 1.5, 2.0)):
        cat = "Box width" if idx == 0 else ""
        w_px = _f(bx_f[sc_v]["hand_box_width_px"], 1)
        sw_rows.append(
            f"{cat} & {w_px} px & "
            f"{_f(bx_f[sc_v]['half_crossing_px']['mean'], 1)} & {_f(bx_f[sc_v]['floor_gain']['mean'], 2)} & "
            f"{_f(bx_d[sc_v]['half_crossing_px']['mean'], 1)} & {_f(bx_d[sc_v]['floor_gain']['mean'], 2)} & "
            f"{_f(bx_r[sc_v]['half_crossing_px']['mean'], 1)} & {_f(bx_r[sc_v]['floor_gain']['mean'], 2)} \\\\"
        )
    sw_rows.append("\\midrule")
    # Motion blur rows
    for idx, klen in enumerate((0, 5, 11, 21)):
        cat = "Motion blur" if idx == 0 else ""
        sw_rows.append(
            f"{cat} & {klen} px & "
            f"{_f(bl_f[klen]['half_crossing_px']['mean'], 1)} & {_f(bl_f[klen]['floor_gain']['mean'], 2)} & "
            f"{_f(bl_d[klen]['half_crossing_px']['mean'], 1)} & {_f(bl_d[klen]['floor_gain']['mean'], 2)} & "
            f"{_f(bl_r[klen]['half_crossing_px']['mean'], 1)} & {_f(bl_r[klen]['floor_gain']['mean'], 2)} \\\\"
        )
    sw_rows.append("\\midrule")
    # Sensor noise rows
    for idx, sig in enumerate((0.0, 5.0, 15.0, 30.0)):
        cat = "Sensor noise" if idx == 0 else ""
        sw_rows.append(
            f"{cat} & $\\sigma={sig:.0f}$ & "
            f"{_f(ns_f[sig]['half_crossing_px']['mean'], 1)} & {_f(ns_f[sig]['floor_gain']['mean'], 2)} & "
            f"{_f(ns_d[sig]['half_crossing_px']['mean'], 1)} & {_f(ns_d[sig]['floor_gain']['mean'], 2)} & "
            f"{_f(ns_r[sig]['half_crossing_px']['mean'], 1)} & {_f(ns_r[sig]['floor_gain']['mean'], 2)} \\\\"
        )
    files["tab_sweeps.tex"] = (
        "\\begin{tabular}{@{}llrrrrrr@{}}\n\\toprule\n"
        " & & \\multicolumn{2}{c}{Farneback (10)} & \\multicolumn{2}{c}{DIS (10)} & "
        "\\multicolumn{2}{c}{RAFT-small (5)} \\\\\n"
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\\cmidrule(lr){7-8}\n"
        "Factor & Setting & $d_{0.5}$ & Shelf & $d_{0.5}$ & Shelf & $d_{0.5}$ & Shelf \\\\\n\\midrule\n"
        + "\n".join(sw_rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )

    # ----- decode width table --------------------------------------------------------------------
    rows = []
    dt = native["pair_interval_s"]
    for w, tag in (("480", "A"), ("960", "B"), ("1440", "C"), ("1920", "D")):
        a = seeds["farneback_by_width"][w]
        sc = next(x for x in native["scales"] if x["frame_size"][0] == int(w))
        col = next(c for c in a["by_displacement"] if c["translation_m"] == 0.02)
        per = [
            s["gains"][[c["translation_m"] for c in a["by_displacement"]].index(0.02)]
            for s in a["per_seed"]
        ]
        hc = a["half_crossing_px"]
        speed_half = hc["mean"] * sc["mm_per_px"] / dt
        speed_here = col["hand_displacement_px"] * sc["mm_per_px"] / dt
        rows.append(
            f"{w}$\\times${round(int(w) * 9 / 16)} & {_f(sc['mm_per_px'], 2)} & "
            f"{_f(col['hand_displacement_px'], 1)} & "
            f"{_f(col['mean'], 2)} ({_f(col['min'], 2)}--{_f(col['max'], 2)}) & "
            f"{_f(hc['mean'], 1)} & {_f(hc['sd'], 1)} & {_f(speed_half, 0)} \\\\"
        )
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
        "Decode & mm/px & px moved & Gain at $\\approx 602$ mm/s & "
        "Crossing (px) & sd (px) & Crossing (mm/s) \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )

    # ----- A14 single-seed residual (preserved for provenance compatibility) ---------------------
    fb = bench["arms"]["farneback-cv2"]
    rf = bench["arms"]["raft-small"]
    m["ResGeom"] = _f(fb["a14_rotation_residual_geometry_only_px"], 2)
    m["ResFarneback"] = _f(fb["a14_rotation_residual_px"], 2)
    m["ResRaft"] = _f(rf["a14_rotation_residual_px"], 2)

    # ----- HAL propagation table -----------------------------------------------------------------
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
            f"{_f(h_true - h_mean, 2)} \\\\"
        )
        key = {11.399: "Lo", 22.794: "Mid", 34.181: "Hi"}[speed_disp]
        m[f"HalTrue{key}"] = _f(h_true, 1)
        m[f"HalLossMean{key}"] = _f(h_true - h_mean, 1)
        m[f"HalLossSmall{key}"] = _f(h_true - h_hi, 1)
        m[f"HalLossLarge{key}"] = _f(h_true - h_lo, 1)
        m[f"SpeedRow{key}"] = _f(s_true, 0)
    files["tab_hal.tex"] = (
        "\\begin{tabular}{@{}rrrrcr@{}}\n\\toprule\n"
        "True speed (mm/s) & Mean gain & HAL, true & HAL, recovered & "
        "HAL, seed range & Loss (mean) \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )

    # ----- measurement card (Appendix A) ---------------------------------------------------------
    rows = []
    status_count: dict[str, int] = {}
    for c in card["claims"]:
        st_lbl = c["status"]
        status_count[st_lbl] = status_count.get(st_lbl, 0) + 1
        rows.append(f"{c['id']} & {st_lbl.lower()} & {c['statement']} \\\\")
    m["CardVerdict"] = card["verdict"].replace("_", "\\_")
    m["CardUntested"] = str(status_count.get("UNTESTED", 0))
    m["CardHolds"] = str(status_count.get("HOLDS", 0))
    m["CardFailed"] = str(status_count.get("FAILED", 0))
    m["CardClaims"] = str(len(card["claims"]))
    files["tab_card.tex"] = (
        "\\begin{tabular}{@{}llp{9.2cm}@{}}\n\\toprule\n"
        "Claim & Status & Statement \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )

    # ----- figures -------------------------------------------------------------------------------
    files["fig_geometry.tex"] = _build_geometry_figure(ratio)
    files["fig_flowfield.tex"] = _build_flowfield_figure(v2)
    files["fig_gain_v2.tex"] = _build_gain_v2_figure(seeds, v2, ratio)
    files["fig_sweeps.tex"] = _build_sweeps_figure(v2)

    # Combined fine-grid texture spread + decode-width figure
    fine_lines = []
    for s in fine["per_seed"]:
        pts = _coords(
            [(c["hand_displacement_px"], g) for c, g in zip(fine["by_displacement"], s["gains"])]
        )
        fine_lines.append(f"\\addplot[gray!50,thin] coordinates {{{pts}}};")
    fmean = _coords([(c["hand_displacement_px"], c["mean"]) for c in fine["by_displacement"]])

    colours = {
        "480": "red!70!black",
        "960": "blue!80!black",
        "1440": "green!50!black",
        "1920": "violet",
    }
    w_parts = []
    for w, col in colours.items():
        a = seeds["farneback_by_width"][w]
        pts = _coords([(c["hand_displacement_px"], c["mean"]) for c in a["by_displacement"]])
        w_parts.append(
            f"\\addplot[{col},thick,mark=*,mark size=1.2pt] coordinates {{{pts}}};\n"
            f"\\addlegendentry{{{w} wide}}"
        )

    files["fig_fine_width.tex"] = (
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.94\\linewidth,height=4.8cm,"
        "title={\\footnotesize\\textbf{(a) Fine-grid texture spread (960$\\times$540, 20 seeds)}},"
        "xlabel={\\footnotesize hand displacement (px)},"
        "ylabel={\\footnotesize gain},ymin=0,ymax=1.12,"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(fine_lines)
        + f"\n\\addplot[blue!80!black,very thick] coordinates {{{fmean}}};\n"
        "\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}{0.49\\linewidth}\n"
        "\\begin{tikzpicture}\n\\begin{axis}[width=0.94\\linewidth,height=4.8cm,xmode=log,"
        "title={\\footnotesize\\textbf{(b) Farneback gain by decode width (20 seeds)}},"
        "xlabel={\\footnotesize hand displacement (px)},"
        "ylabel={\\footnotesize mean gain},ymin=0,ymax=1.12,"
        "legend style={at={(0.98,0.98)},anchor=north east,font=\\tiny,draw=none,fill=white,fill opacity=0.85,inner sep=1pt},"
        "grid=both,grid style={gray!15},tick label style={font=\\scriptsize}]\n"
        + "\n".join(w_parts)
        + "\n\\end{axis}\n\\end{tikzpicture}\n"
        "\\end{minipage}\n"
    )

    # ----- macros --------------------------------------------------------------------------------
    files["numbers.tex"] = (
        "% generated by scripts/export_paper_tables.py; do not edit\n"
        + "".join(f"\\newcommand{{\\cg{k}}}{{{v}}}\n" for k, v in sorted(m.items()))
    )
    return files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    files = build()
    if args.check:
        bad = [
            n
            for n, t in files.items()
            if not (OUT / n).exists() or (OUT / n).read_text() != t
        ]
        extra = [p.name for p in OUT.iterdir() if p.name not in files] if OUT.exists() else []
        for n in bad:
            print(f"stale or missing: paper/generated/{n}", file=sys.stderr)
        for n in extra:
            print(f"extra generated file: paper/generated/{n}", file=sys.stderr)
        return 1 if (bad or extra) else 0
    OUT.mkdir(parents=True, exist_ok=True)
    # Remove stale files no longer produced by v2.
    for existing in list(OUT.iterdir()):
        if existing.name not in files:
            existing.unlink()
    for n, t in files.items():
        (OUT / n).write_text(t)
    print(f"wrote {len(files)} files to paper/generated/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
