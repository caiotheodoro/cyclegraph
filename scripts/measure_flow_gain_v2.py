#!/usr/bin/env python3
"""Post-hoc v2 instrument-check experiments (docs/DECISIONS.md D078).

Extends `results/flow_gain_seeds.json` with five controlled, synthetic, zero-corpus experiments
at 960x540 under the corpus's nominal Kannala-Brandt fisheye lens:

  A. Direct flow-field observation inside and around the hand box (pixel-level background
     capture fractions, direction cosine similarity, endpoint errors against hand and
     background truth, actual pipeline ego-motion-subtracted residual, and seed-11 spatial
     snapshots for plotting).
  B. Moving-hand, static-camera arm (matched backward-warped pairs with stationary background)
     to separate ego-motion background capture from generic large-displacement breakdown.
  C. Additional estimators: OpenCV DIS (medium preset) and torchvision RAFT-large alongside
     Farneback and RAFT-small, plus multi-seed A14 rotation residuals for all four.
  D. Controlled parameter sweeps over depth ratio, hand bounding-box size, horizontal motion
     blur, and additive Gaussian sensor noise.

Writes `results/flow_gain_v2.json`. Deterministic, offline once torchvision weights are cached,
and touches no corpus frame or pilot artifact.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import cv2
import numpy as np
import numpy.typing as npt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cyclegraph.signal.flow_farneback import FarnebackFlow  # noqa: E402
from cyclegraph.signal.gain import (  # noqa: E402
    SEED,
    TRANSLATIONS_M,
    EstimatorLike,
    curve_from_rows,
    scaled_camera,
)
from cyclegraph.signal.ports import Flow, box_mask  # noqa: E402
from cyclegraph.signal.speed import HAND_BREADTH_MM, ego_motion, residual_rms_px  # noqa: E402
from cyclegraph.signal.synthetic import (  # noqa: E402
    BACKGROUND_DISTANCE_M,
    HAND_DISTANCE_M,
    Scene,
    analytic_flow,
    hand_box_for,
    texture,
    valid_mask,
)

WIDTH = 960
PAIR_INTERVAL_S = 1.0 / 30.0
FLOOR_RATIO = HAND_DISTANCE_M / BACKGROUND_DISTANCE_M
FINE_M = tuple(round(0.020 + 0.001 * i, 4) for i in range(0, 11))
FIELD_TRANSLATIONS_M = (0.01, 0.02, 0.03, 0.06)
SNAPSHOT_TRANSLATIONS_M = (0.01, 0.03, 0.06)
A14_ROTATION_DEG = 1.0  # 30 deg/s over 1/30 s, matching scripts/bench_flow.py

DEPTH_BG_M = (0.90, 1.50, 2.50, 4.50)
BOX_SCALES = (0.5, 0.75, 1.0, 1.5, 2.0)
BLUR_KERNELS = (0, 5, 11, 21)
NOISE_SIGMAS = (0.0, 5.0, 15.0, 30.0)


def _ensure_lzma_stub() -> None:
    """Allow importing torchvision.models.optical_flow on Python builds lacking _lzma."""
    try:
        import lzma  # noqa: F401
    except ModuleNotFoundError:
        stub = types.ModuleType("lzma")
        stub.open = None  # type: ignore[attr-defined]
        sys.modules["lzma"] = stub


@dataclass(frozen=True, slots=True)
class DISFlow:
    """OpenCV Dense Inverse Search optical flow (Kroeger et al. 2016)."""

    preset: int = cv2.DISOPTICAL_FLOW_PRESET_MEDIUM

    @property
    def flow_method(self) -> str:
        return "dis-medium"

    def flow(self, first: npt.NDArray[np.uint8], second: npt.NDArray[np.uint8]) -> Flow | None:
        if first.shape != second.shape or first.ndim != 2 or first.size == 0:
            return None
        dis = cv2.DISOpticalFlow.create(self.preset)
        field = dis.calc(first, second, None)  # type: ignore[call-overload,unused-ignore]
        if not np.isfinite(field).all() or not field.any():
            return None
        out: Flow = field.astype(np.float32)
        return out


class TorchRaftFlow:
    """RAFT-small or RAFT-large wrapper supporting CPU or MPS without touching src/."""

    def __init__(self, name: str, model: Any, device: str, torch_mod: Any) -> None:
        self._name = name
        self._model = model
        self._device = device
        self._torch = torch_mod

    @property
    def flow_method(self) -> str:
        return self._name

    def flow(self, first: npt.NDArray[np.uint8], second: npt.NDArray[np.uint8]) -> Flow | None:
        if first.shape != second.shape:
            return None
        torch = self._torch
        h, w = first.shape
        ph, pw = (-h) % 8, (-w) % 8
        a_np = (first.astype(np.float32) / 255.0) * 2.0 - 1.0
        b_np = (second.astype(np.float32) / 255.0) * 2.0 - 1.0
        a = torch.from_numpy(a_np)[None, None, :, :].repeat(1, 3, 1, 1).to(self._device)
        b = torch.from_numpy(b_np)[None, None, :, :].repeat(1, 3, 1, 1).to(self._device)
        if ph or pw:
            a = torch.nn.functional.pad(a, (0, pw, 0, ph), mode="replicate")
            b = torch.nn.functional.pad(b, (0, pw, 0, ph), mode="replicate")
        with torch.no_grad():
            pred = self._model(a, b)[-1]
        field: Flow = pred[0, :, :h, :w].permute(1, 2, 0).cpu().numpy().astype(np.float32)
        if not np.isfinite(field).all() or not field.any():
            return None
        return field


def _load_raft(variant: Literal["small", "large"], device: str) -> TorchRaftFlow:
    _ensure_lzma_stub()
    import torch
    from torchvision.models.optical_flow import (
        Raft_Large_Weights,
        Raft_Small_Weights,
        raft_large,
        raft_small,
    )

    torch.manual_seed(0)
    if variant == "small":
        model = raft_small(weights=Raft_Small_Weights.DEFAULT).to(device).eval()
        return TorchRaftFlow("raft-small", model, device, torch)
    model = raft_large(weights=Raft_Large_Weights.DEFAULT).to(device).eval()
    return TorchRaftFlow("raft-large", model, device, torch)


def _bilinear(
    image: npt.NDArray[np.float64],
    xs: npt.NDArray[np.float64],
    ys: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """Bilinear sampling with border clamping, matching `cyclegraph.signal.synthetic`."""
    h, w = image.shape
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    fx, fy = xs - x0, ys - y0
    x0c, x1c = np.clip(x0, 0, w - 1), np.clip(x0 + 1, 0, w - 1)
    y0c, y1c = np.clip(y0, 0, h - 1), np.clip(y0 + 1, 0, h - 1)
    top = image[y0c, x0c] * (1.0 - fx) + image[y0c, x1c] * fx
    bottom = image[y1c, x0c] * (1.0 - fx) + image[y1c, x1c] * fx
    return top * (1.0 - fy) + bottom * fy


def _render_pair_custom(
    scene: Scene,
    *,
    translation_m: float = 0.0,
    rotation_rad: float = 0.0,
    seed: int = 0,
    mode: Literal["ego_motion", "static_camera"] = "ego_motion",
    blur_kernel: int = 0,
    noise_sigma: float = 0.0,
) -> tuple[npt.NDArray[np.uint8], npt.NDArray[np.uint8], Flow]:
    """Render a synthetic pair and return `(first, second, truth_flow)`."""
    cam = scene.camera
    truth_ego = analytic_flow(
        scene,
        rotation_rad=rotation_rad,
        translation_m=(translation_m, 0.0, 0.0),
    )
    mask = box_mask((cam.height, cam.width), [scene.hand_box])
    valid = valid_mask(cam)
    if mode == "ego_motion":
        truth = truth_ego
    else:
        truth = np.zeros_like(truth_ego)
        truth[mask] = truth_ego[mask]
        truth[~valid] = np.nan

    first_f = texture(cam.height, cam.width, seed=seed).astype(np.float64)
    ys, xs = np.mgrid[0 : cam.height, 0 : cam.width].astype(np.float64)
    finite = np.isfinite(truth).all(axis=-1)
    sx = np.where(finite, xs - truth[..., 0], xs)
    sy = np.where(finite, ys - truth[..., 1], ys)
    second_f = _bilinear(first_f, sx, sy)

    if blur_kernel > 1:
        k = np.ones((1, blur_kernel), dtype=np.float64) / float(blur_kernel)
        first_f = np.asarray(
            cv2.filter2D(first_f, -1, k, borderType=cv2.BORDER_REPLICATE), dtype=np.float64
        )
        second_f = np.asarray(
            cv2.filter2D(second_f, -1, k, borderType=cv2.BORDER_REPLICATE), dtype=np.float64
        )

    if noise_sigma > 0.0:
        rng0 = np.random.default_rng(100_000 + seed * 31 + 1)
        rng1 = np.random.default_rng(100_000 + seed * 31 + 2)
        first_f = np.clip(first_f + rng0.normal(0.0, noise_sigma, size=first_f.shape), 0.0, 255.0)
        second_f = np.clip(
            second_f + rng1.normal(0.0, noise_sigma, size=second_f.shape), 0.0, 255.0
        )

    first_f = np.where(finite, first_f, 0.0)
    second_f = np.where(finite, second_f, 0.0)
    return first_f.round().astype(np.uint8), second_f.round().astype(np.uint8), truth


def _spread(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.fmean(values), 4),
        "sd": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def _half_crossing_px(displacements: list[float], gains: list[float | None]) -> float | None:
    for (d0, g0), (d1, g1) in zip(zip(displacements, gains), zip(displacements[1:], gains[1:])):
        if g0 is None or g1 is None:
            continue
        if g0 >= 0.5 > g1:
            return round(d0 + (g0 - 0.5) * (d1 - d0) / (g0 - g1), 3)
    return None


def _run_sweep(
    estimator: EstimatorLike,
    scene: Scene,
    translations: tuple[float, ...],
    seeds: list[int],
    *,
    mode: Literal["ego_motion", "static_camera"] = "ego_motion",
    blur_kernel: int = 0,
    noise_sigma: float = 0.0,
) -> dict[str, Any]:
    cam = scene.camera
    mask = box_mask((cam.height, cam.width), [scene.hand_box])
    ratio = scene.hand_distance_m / scene.background_distance_m
    call = estimator.flow if hasattr(estimator, "flow") else estimator

    # Precompute analytic truth per translation once.
    truths: list[tuple[float, float]] = []
    for metres in translations:
        t_ego = analytic_flow(scene, translation_m=(metres, 0.0, 0.0))
        true_px = float(np.median(np.linalg.norm(t_ego[mask], axis=-1)))
        truths.append((metres, round(true_px, 3)))

    per_seed: list[dict[str, Any]] = []
    all_finite = True
    for seed in seeds:
        rows: list[dict[str, Any]] = []
        for metres, true_px in truths:
            first, second, _ = _render_pair_custom(
                scene,
                translation_m=metres,
                seed=seed,
                mode=mode,
                blur_kernel=blur_kernel,
                noise_sigma=noise_sigma,
            )
            field = call(first, second)
            if field is None:
                all_finite = False
                got_px = None
            else:
                got_px = float(np.median(np.linalg.norm(field[mask], axis=-1)))
            rows.append(
                {
                    "translation_m_per_pair": metres,
                    "hand_displacement_px": true_px,
                    "recovered_px": None if got_px is None else round(got_px, 3),
                    "gain": None if got_px is None else round(got_px / true_px, 4),
                    "flow_returned_none": field is None,
                }
            )
        curve = curve_from_rows(rows, ratio)
        gains = [r["gain"] for r in rows]
        disps = [r["hand_displacement_px"] for r in rows]
        post_gains = [
            float(r["gain"])
            for r in rows
            if r["gain"] is not None and float(r["translation_m_per_pair"]) >= 0.06
        ]
        per_seed.append(
            {
                "seed": seed,
                "gains": gains,
                "knee_px": curve.knee_px,
                "collapse_px": curve.collapse_px,
                "half_crossing_px": _half_crossing_px(disps, gains),
                "floor_gain": None if curve.floor_gain is None else round(curve.floor_gain, 4),
                "post_68px_median_gain": (
                    round(statistics.median(post_gains), 4) if post_gains else None
                ),
            }
        )

    columns = []
    for i, (metres, d) in enumerate(truths):
        gvals = [float(s["gains"][i]) for s in per_seed if s["gains"][i] is not None]
        columns.append(
            {
                "hand_displacement_px": d,
                "translation_m": metres,
                "n_valid": len(gvals),
                **(_spread(gvals) if gvals else {}),
            }
        )
    knees = [float(s["knee_px"]) for s in per_seed if s["knee_px"] is not None]
    floors = [float(s["floor_gain"]) for s in per_seed if s["floor_gain"] is not None]
    halves = [float(s["half_crossing_px"]) for s in per_seed if s["half_crossing_px"] is not None]
    post68 = [
        float(s["post_68px_median_gain"])
        for s in per_seed
        if s["post_68px_median_gain"] is not None
    ]
    return {
        "n_seeds": len(seeds),
        "all_finite": all_finite,
        "hand_box_width_px": round(scene.hand_box.width, 3),
        "depth_ratio": round(ratio, 4),
        "by_displacement": columns,
        "knee_px": {"n_with_knee": len(knees), **(_spread(knees) if knees else {})},
        "half_crossing_px": {"n_with_crossing": len(halves), **(_spread(halves) if halves else {})},
        "floor_gain": {"n_with_floor": len(floors), **(_spread(floors) if floors else {})},
        "post_68px_median_gain": {"n": len(post68), **(_spread(post68) if post68 else {})},
        "per_seed": per_seed,
    }


def _experiment_a_field_observation(
    estimators: dict[str, EstimatorLike],
    seeds_by_est: dict[str, list[int]],
    scene: Scene,
) -> dict[str, Any]:
    """Directly measure pixel-level flow fields inside the hand box and save plotting snapshots."""
    cam = scene.camera
    box = scene.hand_box
    mask = box_mask((cam.height, cam.width), [box])
    bg_only_scene = Scene(
        camera=cam,
        hand_box=box,
        hand_distance_m=scene.background_distance_m,
        background_distance_m=scene.background_distance_m,
    )

    metrics: dict[str, list[dict[str, Any]]] = {name: [] for name in estimators}
    for metres in FIELD_TRANSLATIONS_M:
        truth_hand = analytic_flow(scene, translation_m=(metres, 0.0, 0.0))
        truth_bg = analytic_flow(bg_only_scene, translation_m=(metres, 0.0, 0.0))
        vh = truth_hand[mask]
        vb = truth_bg[mask]
        vh_mag = np.linalg.norm(vh, axis=-1)
        diff_hb = np.linalg.norm(vh - vb, axis=-1)
        true_px = float(np.median(vh_mag))
        true_res = residual_rms_px(truth_hand, box, ego_motion(truth_hand, mask))

        for name, est in estimators.items():
            call = est.flow if hasattr(est, "flow") else est
            per: dict[str, list[float]] = {
                "gain": [],
                "frac_closer_to_bg": [],
                "frac_locked_bg": [],
                "frac_locked_hand": [],
                "cos_sim_hand": [],
                "epe_hand_px": [],
                "epe_bg_px": [],
                "pipeline_residual_px": [],
                "residual_recovery_ratio": [],
            }
            for seed in seeds_by_est[name]:
                first, second, _ = _render_pair_custom(scene, translation_m=metres, seed=seed)
                field = call(first, second)
                assert field is not None, f"{name} returned None on seed {seed}, t={metres}"
                ve = field[mask]
                ve_mag = np.linalg.norm(ve, axis=-1)
                d_hand = np.linalg.norm(ve - vh, axis=-1)
                d_bg = np.linalg.norm(ve - vb, axis=-1)

                dot = (ve * vh).sum(axis=-1)
                denom = np.maximum(ve_mag * vh_mag, 1e-8)
                cos_sim = dot / denom

                est_res = residual_rms_px(field, box, ego_motion(field, mask))

                per["gain"].append(float(np.median(ve_mag)) / true_px)
                per["frac_closer_to_bg"].append(float(np.mean(d_bg < d_hand)))
                per["frac_locked_bg"].append(float(np.mean(d_bg <= 0.25 * diff_hb)))
                per["frac_locked_hand"].append(float(np.mean(d_hand <= 0.25 * diff_hb)))
                per["cos_sim_hand"].append(float(np.median(cos_sim)))
                per["epe_hand_px"].append(float(np.median(d_hand)))
                per["epe_bg_px"].append(float(np.median(d_bg)))
                per["pipeline_residual_px"].append(est_res)
                per["residual_recovery_ratio"].append(est_res / true_res)

            metrics[name].append(
                {
                    "translation_m": metres,
                    "hand_displacement_px": round(true_px, 3),
                    "true_residual_px": round(true_res, 3),
                    "n_seeds": len(seeds_by_est[name]),
                    **{k: _spread(v) for k, v in per.items()},
                }
            )

    # Seed-11 spatial snapshots: 1D centerline profiles + 2D vector grids around the hand box.
    cy_idx = int(round(cam.cy))
    x_lo = max(0, int(box.x) - 96)
    x_hi = min(cam.width, int(box.x + box.width) + 96)
    xs_1d = list(range(x_lo, x_hi + 1, 4))

    gx_lo = max(0, int(box.x) - 64)
    gx_hi = min(cam.width, int(box.x + box.width) + 64)
    gy_lo = max(0, int(box.y) - 64)
    gy_hi = min(cam.height, int(box.y + box.height) + 64)
    grid_xs = list(range(gx_lo, gx_hi + 1, 16))
    grid_ys = list(range(gy_lo, gy_hi + 1, 16))

    snapshots: list[dict[str, Any]] = []
    for metres in SNAPSHOT_TRANSLATIONS_M:
        first, second, truth = _render_pair_custom(scene, translation_m=metres, seed=SEED)
        true_px = float(np.median(np.linalg.norm(truth[mask], axis=-1)))
        profile: dict[str, list[float]] = {
            "x": [float(x) for x in xs_1d],
            "true_ux": [round(float(truth[cy_idx, x, 0]), 2) for x in xs_1d],
        }
        quiver_est: dict[str, list[list[float]]] = {}
        true_grid = [
            [
                x,
                y,
                round(float(truth[y, x, 0]), 2),
                round(float(truth[y, x, 1]), 2),
                1 if bool(mask[y, x]) else 0,
            ]
            for y in grid_ys
            for x in grid_xs
        ]
        for name, est in estimators.items():
            call = est.flow if hasattr(est, "flow") else est
            field = call(first, second)
            assert field is not None
            profile[name] = [round(float(field[cy_idx, x, 0]), 2) for x in xs_1d]
            quiver_est[name] = [
                [round(float(field[y, x, 0]), 2), round(float(field[y, x, 1]), 2)]
                for y in grid_ys
                for x in grid_xs
            ]
        snapshots.append(
            {
                "seed": SEED,
                "translation_m": metres,
                "hand_displacement_px": round(true_px, 3),
                "box": {
                    "x0": round(box.x, 1),
                    "x1": round(box.x + box.width, 1),
                    "y0": round(box.y, 1),
                    "y1": round(box.y + box.height, 1),
                },
                "centerline_y": cy_idx,
                "centerline_profile": profile,
                "quiver_true": true_grid,
                "quiver_estimated": quiver_est,
            }
        )

    return {"metrics_by_estimator": metrics, "snapshots_seed11": snapshots}


def _experiment_a14_residuals(
    estimators: dict[str, EstimatorLike],
    seeds: list[int],
    scene: Scene,
) -> dict[str, Any]:
    """Multi-seed A14 1-degree rotation residual against exact geometry at 960x540."""
    mask = box_mask((scene.camera.height, scene.camera.width), [scene.hand_box])
    truth = analytic_flow(scene, rotation_rad=math.radians(A14_ROTATION_DEG))
    geom_px = residual_rms_px(truth, scene.hand_box, ego_motion(truth, mask))
    out: dict[str, Any] = {
        "rotation_deg": A14_ROTATION_DEG,
        "geometry_only_px": round(geom_px, 4),
        "seeds": seeds,
        "by_estimator": {},
    }
    for name, est in estimators.items():
        call = est.flow if hasattr(est, "flow") else est
        vals: list[float] = []
        seed11_val: float | None = None
        for seed in seeds:
            first, second, _ = _render_pair_custom(
                scene, rotation_rad=math.radians(A14_ROTATION_DEG), seed=seed
            )
            field = call(first, second)
            assert field is not None
            res = residual_rms_px(field, scene.hand_box, ego_motion(field, mask))
            vals.append(res)
            if seed == SEED:
                seed11_val = round(res, 4)
        out["by_estimator"][name] = {
            "seed11_px": seed11_val,
            **_spread(vals),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/flow_gain_v2.json")
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cpu", "mps"),
        help="Torch device for RAFT estimators (auto prefers mps if available).",
    )
    args = parser.parse_args(argv)

    _ensure_lzma_stub()
    import torch

    if args.device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    else:
        device = args.device

    print(f"Running v2 experiments at {WIDTH}x540 (RAFT device: {device})...", flush=True)

    cam = scaled_camera(WIDTH)
    nominal_scene = Scene(camera=cam, hand_box=hand_box_for(cam))

    farneback = FarnebackFlow()
    dis = DISFlow()
    raft_small_est = _load_raft("small", device)
    raft_large_est = _load_raft("large", device)

    # Verify RAFT-small device parity against CPU on seed 11 if running on MPS.
    parity: dict[str, Any] = {"device": device, "checked_against_cpu": False}
    if device != "cpu":
        raft_small_cpu = _load_raft("small", "cpu")
        dev_sweep = _run_sweep(raft_small_est, nominal_scene, TRANSLATIONS_M, [SEED])
        cpu_sweep = _run_sweep(raft_small_cpu, nominal_scene, TRANSLATIONS_M, [SEED])
        g_dev = dev_sweep["per_seed"][0]["gains"]
        g_cpu = cpu_sweep["per_seed"][0]["gains"]
        max_diff = max(abs(float(a) - float(b)) for a, b in zip(g_dev, g_cpu))
        parity = {
            "device": device,
            "checked_against_cpu": True,
            "seed": SEED,
            "raft_small_max_abs_gain_diff": round(max_diff, 6),
        }
        print(f"  RAFT-small {device} vs CPU max abs gain diff (seed {SEED}): {max_diff:.6f}", flush=True)

    seeds_20 = list(range(20))
    seeds_11 = sorted(set(range(10)) | {SEED})
    seeds_10 = list(range(10))
    seeds_5 = list(range(5))

    estimators: dict[str, EstimatorLike] = {
        "farneback-cv2": farneback,
        "dis-medium": dis,
        "raft-small": raft_small_est,
        "raft-large": raft_large_est,
    }
    seeds_primary = {
        "farneback-cv2": seeds_20,
        "dis-medium": seeds_20,
        "raft-small": seeds_11,
        "raft-large": seeds_11,
    }

    # --- Experiment C: Additional estimators (ego-motion 9-pt + DIS fine grid) ------------------
    print("  [C] Running DIS-medium (ego-motion 9-pt + fine) and RAFT-large (ego-motion 9-pt)...", flush=True)
    ego_dis_9pt = _run_sweep(dis, nominal_scene, TRANSLATIONS_M, seeds_20, mode="ego_motion")
    ego_dis_fine = _run_sweep(dis, nominal_scene, FINE_M, seeds_20, mode="ego_motion")
    ego_raft_large_9pt = _run_sweep(
        raft_large_est, nominal_scene, TRANSLATIONS_M, seeds_11, mode="ego_motion"
    )
    a14_residuals = _experiment_a14_residuals(estimators, seeds_11, nominal_scene)

    # --- Experiment A: Direct flow-field observation --------------------------------------------
    print("  [A] Running direct flow-field observation across all 4 estimators...", flush=True)
    exp_a = _experiment_a_field_observation(estimators, seeds_primary, nominal_scene)

    # --- Experiment B: Moving-hand, static-camera arm -------------------------------------------
    print("  [B] Running static-camera, moving-hand arm across all 4 estimators...", flush=True)
    static_arms = {
        name: _run_sweep(
            est, nominal_scene, TRANSLATIONS_M, seeds_primary[name], mode="static_camera"
        )
        for name, est in estimators.items()
    }

    # --- Experiment D: Parameter sweeps (depth ratio, box size, motion blur, sensor noise) ------
    print("  [D1] Running depth-ratio sweep...", flush=True)
    depth_sweep: dict[str, list[dict[str, Any]]] = {
        "farneback-cv2": [],
        "dis-medium": [],
        "raft-small": [],
    }
    for bg_m in DEPTH_BG_M:
        sc = Scene(
            camera=cam,
            hand_box=hand_box_for(cam),
            hand_distance_m=HAND_DISTANCE_M,
            background_distance_m=bg_m,
        )
        for name, est, sd in (
            ("farneback-cv2", farneback, seeds_10),
            ("dis-medium", dis, seeds_10),
            ("raft-small", raft_small_est, seeds_5),
        ):
            res = _run_sweep(est, sc, TRANSLATIONS_M, sd, mode="ego_motion")
            depth_sweep[name].append(
                {
                    "background_distance_m": bg_m,
                    "depth_ratio": round(HAND_DISTANCE_M / bg_m, 4),
                    "half_crossing_px": res["half_crossing_px"],
                    "floor_gain": res["floor_gain"],
                    "post_68px_median_gain": res["post_68px_median_gain"],
                    "all_finite": res["all_finite"],
                }
            )

    print("  [D2] Running hand bounding-box size sweep...", flush=True)
    box_sweep: dict[str, list[dict[str, Any]]] = {
        "farneback-cv2": [],
        "dis-medium": [],
        "raft-small": [],
    }
    for scale in BOX_SCALES:
        hb = hand_box_for(cam, hand_breadth_mm=HAND_BREADTH_MM * scale)
        sc = Scene(camera=cam, hand_box=hb)
        for name, est, sd in (
            ("farneback-cv2", farneback, seeds_10),
            ("dis-medium", dis, seeds_10),
            ("raft-small", raft_small_est, seeds_5),
        ):
            res = _run_sweep(est, sc, TRANSLATIONS_M, sd, mode="ego_motion")
            box_sweep[name].append(
                {
                    "box_scale": scale,
                    "hand_box_width_px": res["hand_box_width_px"],
                    "half_crossing_px": res["half_crossing_px"],
                    "floor_gain": res["floor_gain"],
                    "all_finite": res["all_finite"],
                }
            )

    print("  [D3] Running directional motion-blur sweep...", flush=True)
    blur_sweep: dict[str, list[dict[str, Any]]] = {
        "farneback-cv2": [],
        "dis-medium": [],
        "raft-small": [],
    }
    for klen in BLUR_KERNELS:
        for name, est, sd in (
            ("farneback-cv2", farneback, seeds_10),
            ("dis-medium", dis, seeds_10),
            ("raft-small", raft_small_est, seeds_5),
        ):
            res = _run_sweep(
                est, nominal_scene, TRANSLATIONS_M, sd, mode="ego_motion", blur_kernel=klen
            )
            g_low = res["by_displacement"][0]
            g_knee = res["by_displacement"][2]
            blur_sweep[name].append(
                {
                    "blur_kernel_px": klen,
                    "gain_at_5_7px": {k: g_low[k] for k in ("mean", "sd", "min", "max")},
                    "gain_at_22_8px": {k: g_knee[k] for k in ("mean", "sd", "min", "max")},
                    "half_crossing_px": res["half_crossing_px"],
                    "floor_gain": res["floor_gain"],
                    "all_finite": res["all_finite"],
                }
            )

    print("  [D4] Running additive Gaussian sensor-noise sweep...", flush=True)
    noise_sweep: dict[str, list[dict[str, Any]]] = {
        "farneback-cv2": [],
        "dis-medium": [],
        "raft-small": [],
    }
    for sigma in NOISE_SIGMAS:
        for name, est, sd in (
            ("farneback-cv2", farneback, seeds_10),
            ("dis-medium", dis, seeds_10),
            ("raft-small", raft_small_est, seeds_5),
        ):
            res = _run_sweep(
                est, nominal_scene, TRANSLATIONS_M, sd, mode="ego_motion", noise_sigma=sigma
            )
            g_low = res["by_displacement"][0]
            g_knee = res["by_displacement"][2]
            noise_sweep[name].append(
                {
                    "noise_sigma": sigma,
                    "gain_at_5_7px": {k: g_low[k] for k in ("mean", "sd", "min", "max")},
                    "gain_at_22_8px": {k: g_knee[k] for k in ("mean", "sd", "min", "max")},
                    "half_crossing_px": res["half_crossing_px"],
                    "floor_gain": res["floor_gain"],
                    "all_finite": res["all_finite"],
                }
            )

    payload: dict[str, Any] = {
        "what_this_is": (
            "Post-hoc v2 instrument-check experiments (docs/DECISIONS.md D078): direct flow-field "
            "observation, moving-hand static-camera arm, DIS-medium and RAFT-large estimators, "
            "multi-seed A14 rotation residuals, and controlled sweeps over depth ratio, box size, "
            "motion blur, and Gaussian sensor noise. Rendered synthetics at 960x540 under the "
            "nominal corpus lens; zero corpus frames, zero pilot values."
        ),
        "width": WIDTH,
        "height": cam.height,
        "pair_interval_s": PAIR_INTERVAL_S,
        "floor_ratio_expected": FLOOR_RATIO,
        "device_parity": parity,
        "additional_estimators_ego_motion": {
            "dis-medium": {"grid_9pt": ego_dis_9pt, "fine_960": ego_dis_fine},
            "raft-large": {"grid_9pt": ego_raft_large_9pt},
        },
        "a14_rotation_residuals": a14_residuals,
        "experiment_a_flow_field": exp_a,
        "experiment_b_static_camera": static_arms,
        "experiment_d_sweeps": {
            "depth_ratio": depth_sweep,
            "box_size": box_sweep,
            "motion_blur": blur_sweep,
            "sensor_noise": noise_sweep,
        },
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
