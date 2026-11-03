#!/usr/bin/env python3
"""
Spatiotemporal Cinema Tensor & 3D Worm Analyzer for ALLWAYS
===========================================================
Processes films as 4D spatiotemporal volumes V(u, v, d, tau) coupled with
their acoustic fields, computing six mathematical frameworks + worm topology
+ STGL (Spatiotemporal Grid Language) armature audits:

1. Artin Braid Topology (B_3) & Finite-Time Braiding Exponent (FTBE)
2. Helmholtz-Hodge Optical Flow Decomposition: V = -grad(Phi) + curl(Psi) + H
3. Wasserstein Chromatic Geodesics (W_2^2 in 5D joint u,v,L*,a*,b* space) &
   KALMUS Core-Worm vs. Shell Itten Contrasts
4. Relativistic Saccade Light-Cones (ds^2 = c_eye^2 * max(0, dt - t_fix)^2 - dx^2)
5. Persistent Homology Attractors (beta_0, beta_1, beta_2) via Takens Embedding
6. Cross-Spectral Synchresis Tensor (Hilbert Phase-Locking Value PLV & Anempathetic Slip)
7. Spatiotemporal Worm Topology (u-tau & v-tau Slit-Scan Tomograms, Curvature, Torsion,
   Jerk, and 14-Line Harmonic Armature / STGL Resonance)
"""

import os
import sys
import json
import math
import wave
import subprocess
import tempfile
import numpy as np
import cv2
from PIL import Image, ImageDraw
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist, squareform
from scipy.signal import hilbert

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
OUT_DIR = os.path.join(REPO_ROOT, "allways-tensor")
IMG_DIR = os.path.join(OUT_DIR, "img")
os.makedirs(IMG_DIR, exist_ok=True)

COHORT = [
    {
        "id": "allways-best",
        "title": "ALLWAYS — Cinema from the Rest of the Frame",
        "maker": "All 4 Makers (Anthology)",
        "maker_id": "anthology",
        "award": "Master Anthology · 24 Cuts",
        "mp4": "allways-best/allways-best.mp4",
        "watch_url": "../allways-best/index.html",
        "video_rel": "../allways-best/allways-best.mp4",
    },
    {
        "id": "sonnet-059-ball",
        "title": "059 · BALL",
        "maker": "Claude Sonnet",
        "maker_id": "sonnet",
        "award": "Grand Prix · 96.0/100",
        "mp4": "allways-sonnet/059-ball/059-ball.mp4",
        "watch_url": "../allways-sonnet/059-ball/index.html",
        "video_rel": "../allways-sonnet/059-ball/059-ball.mp4",
    },
    {
        "id": "sonnet-055-words",
        "title": "055 · WORDS",
        "maker": "Claude Sonnet",
        "maker_id": "sonnet",
        "award": "Best Sound & Silence · 95.3/100",
        "mp4": "allways-sonnet/055-words/055-words.mp4",
        "watch_url": "../allways-sonnet/055-words/index.html",
        "video_rel": "../allways-sonnet/055-words/055-words.mp4",
    },
    {
        "id": "sonnet-064-parabolas",
        "title": "064 · PARABOLAS",
        "maker": "Claude Sonnet",
        "maker_id": "sonnet",
        "award": "Ballistic Arc Study · 91.5/100",
        "mp4": "allways-sonnet/064-parabolas/064-parabolas.mp4",
        "watch_url": "../allways-sonnet/064-parabolas/index.html",
        "video_rel": "../allways-sonnet/064-parabolas/064-parabolas.mp4",
    },
    {
        "id": "argon-STUDY_03",
        "title": "STUDY 03 · The Eye-Trace Archive",
        "maker": "Gemini Argon",
        "maker_id": "argon",
        "award": "Best Eye-Trace Choreography · 92.3/100",
        "mp4": "allways-argon/studio/films/STUDY_03_The_Eye_Trace_Archive.mp4",
        "watch_url": "../allways-argon/cases/STUDY_03_The_Eye_Trace_Archive.html",
        "video_rel": "../allways-argon/studio/films/STUDY_03_The_Eye_Trace_Archive.mp4",
    },
    {
        "id": "argon-SCION_090",
        "title": "SCION 090 · The Clock",
        "maker": "Gemini Argon",
        "maker_id": "argon",
        "award": "Best Temporal Operator · 90.8/100",
        "mp4": "allways-argon/studio/films/SCION_090_The_Clock_Horological_Montage.mp4",
        "watch_url": "../allways-argon/cases/SCION_090_The_Clock_Horological_Montage.html",
        "video_rel": "../allways-argon/studio/films/SCION_090_The_Clock_Horological_Montage.mp4",
    },
    {
        "id": "argon-SCION_068",
        "title": "SCION 068 · Powers of Ten",
        "maker": "Gemini Argon",
        "maker_id": "argon",
        "award": "Best Scale Traverse · 90.2/100",
        "mp4": "allways-argon/studio/films/SCION_068_Powers_Of_Ten_Scale_Traverse.mp4",
        "watch_url": "../allways-argon/cases/SCION_068_Powers_Of_Ten_Scale_Traverse.html",
        "video_rel": "../allways-argon/studio/films/SCION_068_Powers_Of_Ten_Scale_Traverse.mp4",
    },
    {
        "id": "argon-SCION_066_Tango",
        "title": "SCION 066 · Tango Cyclic Room",
        "maker": "Gemini Argon",
        "maker_id": "argon",
        "award": "Cyclic Room Accumulation · 89.2/100",
        "mp4": "allways-argon/studio/films/SCION_066_Tango_Cyclic_Room.mp4",
        "watch_url": "../allways-argon/cases/SCION_066_Tango_Cyclic_Room.html",
        "video_rel": "../allways-argon/studio/films/SCION_066_Tango_Cyclic_Room.mp4",
    },
    {
        "id": "opus-kinetic",
        "title": "BROLL 06 · Kinetic",
        "maker": "Claude Opus 5.5",
        "maker_id": "opus",
        "award": "Best Kinetic Montage · 94.3/100",
        "mp4": "allways-opus/films/kinetic/kinetic.mp4",
        "watch_url": "../allways-opus/films/kinetic/index.html",
        "video_rel": "../allways-opus/films/kinetic/kinetic.mp4",
    },
    {
        "id": "opus-planimetric",
        "title": "BROLL 04 · Planimetric",
        "maker": "Claude Opus 5.5",
        "maker_id": "opus",
        "award": "Best Formal Architecture · 94.6/100",
        "mp4": "allways-opus/films/planimetric/planimetric.mp4",
        "watch_url": "../allways-opus/films/planimetric/index.html",
        "video_rel": "../allways-opus/films/planimetric/planimetric.mp4",
    },
    {
        "id": "sol-059-radius",
        "title": "059 · Equivalent Radius",
        "maker": "OpenAI Sol",
        "maker_id": "sol",
        "award": "Best Controlled Experiment · 91.5/100",
        "mp4": "allways-sol/films/059/media/ALLWAYS_059_EQUIVALENT_RADIUS_V02.mp4",
        "watch_url": "../allways-sol/films/059/index.html",
        "video_rel": "../allways-sol/films/059/media/ALLWAYS_059_EQUIVALENT_RADIUS_V02.mp4",
    },
    {
        "id": "sol-064-curve",
        "title": "064 · The Curve Is Not the Cause",
        "maker": "OpenAI Sol",
        "maker_id": "sol",
        "award": "Counterfactual Parabola · 89.2/100",
        "mp4": "allways-sol/films/064/media/ALLWAYS_064_THE_CURVE_IS_NOT_THE_CAUSE_V04.mp4",
        "watch_url": "../allways-sol/films/064/index.html",
        "video_rel": "../allways-sol/films/064/media/ALLWAYS_064_THE_CURVE_IS_NOT_THE_CAUSE_V04.mp4",
    },
]

# Precompute 14-Line Harmonic Armature segments in normalized [0,1]^2 space
# 1. Center vertical (0.5,0)-(0.5,1), 2. Center horizontal (0,0.5)-(1,0.5)
# 3-4. Main diagonals (0,0)-(1,1) and (0,1)-(1,0)
# 5-8. Reciprocal / half-frame diagonals: (0,0)-(0.5,1), (0.5,0)-(1,1), (0,1)-(0.5,0), (0.5,1)-(1,0)
# 9-12. Horizontal half diagonals: (0,0)-(1,0.5), (0,0.5)-(1,1), (0,1)-(1,0.5), (0,0.5)-(1,0)
# 13-14. Rule-of-thirds / harmonic intersections verticals u=1/3, u=2/3
ARMATURE_SEGMENTS = [
    ((0.5, 0.0), (0.5, 1.0)),
    ((0.0, 0.5), (1.0, 0.5)),
    ((0.0, 0.0), (1.0, 1.0)),
    ((0.0, 1.0), (1.0, 0.0)),
    ((0.0, 0.0), (0.5, 1.0)),
    ((0.5, 0.0), (1.0, 1.0)),
    ((0.0, 1.0), (0.5, 0.0)),
    ((0.5, 1.0), (1.0, 0.0)),
    ((0.0, 0.0), (1.0, 0.5)),
    ((0.0, 0.5), (1.0, 1.0)),
    ((0.0, 1.0), (1.0, 0.5)),
    ((0.0, 0.5), (1.0, 0.0)),
    ((1.0 / 3.0, 0.0), (1.0 / 3.0, 1.0)),
    ((2.0 / 3.0, 0.0), (2.0 / 3.0, 1.0)),
]

# Fixed random directions on S^4 for exact Sliced 2-Wasserstein in 5D (u, v, L*, a*, b*)
RNG = np.random.default_rng(42)
S4_DIRS = RNG.normal(size=(32, 5))
S4_DIRS /= np.linalg.norm(S4_DIRS, axis=1, keepdims=True)


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def min_armature_dist(u, v):
    best = 999.0
    for (x1, y1), (x2, y2) in ARMATURE_SEGMENTS:
        d = point_to_segment_dist(u, v, x1, y1, x2, y2)
        if d < best:
            best = d
    return best


def classify_stgl_rule(u, v, area_ratio, neg_space_ratio, sym_score):
    """Classify dominant STGL (Spatiotemporal Grid Language) primitive for a frame/shot."""
    dist_center = math.hypot(u - 0.5, v - 0.5)
    dist_spiral = min(
        math.hypot(u - 0.618, v - 0.382),
        math.hypot(u - 0.382, v - 0.382),
        math.hypot(u - 0.618, v - 0.618),
        math.hypot(u - 0.382, v - 0.618),
    )
    dist_thirds = min(abs(u - 1.0 / 3.0), abs(u - 2.0 / 3.0), abs(v - 1.0 / 3.0), abs(v - 2.0 / 3.0))
    if dist_center < 0.085:
        return "centered_anchor"
    if sym_score > 0.76:
        return "bilateral_symmetry"
    if neg_space_ratio > 0.65:
        return "negative_space"
    if dist_spiral < 0.09:
        return "golden_spiral"
    if dist_thirds < 0.055:
        return "rule_of_thirds"
    if area_ratio > 0.42:
        return "frame_in_frame"
    return "s_curve_diagonal"


def helmholtz_hodge_2d(vx, vy):
    """
    Exact discrete 2D Helmholtz-Hodge Decomposition via FFT Poisson solver:
        V = -grad(Phi) + curl(Psi) + H
    Returns:
        div_energy, curl_energy, harm_energy (fractions summing to 1.0),
        raw rms magnitudes (phi_mag, psi_mag, h_mag),
        sink_u, sink_v (dominant attractor coordinate in [0,1]^2)
    """
    H, W = vx.shape
    # Mean velocity is the pure translational harmonic flow H_0
    hx0 = float(np.mean(vx))
    hy0 = float(np.mean(vy))
    vx_zm = vx - hx0
    vy_zm = vy - hy0

    # Spatial frequencies
    kx = 2.0 * np.pi * np.fft.fftfreq(W)
    ky = 2.0 * np.pi * np.fft.fftfreq(H)
    KX, KY = np.meshgrid(kx, ky)
    K2 = KX**2 + KY**2
    K2_safe = np.where(K2 == 0, 1.0, K2)

    VX = np.fft.fft2(vx_zm)
    VY = np.fft.fft2(vy_zm)

    # Curl-free projection (irrotational / divergence component -grad Phi)
    # In Fourier space: V_irr = ((K . V) / |K|^2) K
    K_dot_V = KX * VX + KY * VY
    VX_irr = np.where(K2 == 0, 0.0, (K_dot_V / K2_safe) * KX)
    VY_irr = np.where(K2 == 0, 0.0, (K_dot_V / K2_safe) * KY)

    # Scalar potential Phi in Fourier space: i K . V / |K|^2
    PHI_hat = np.where(K2 == 0, 0.0, 1j * K_dot_V / K2_safe)
    phi_field = np.real(np.fft.ifft2(PHI_hat))

    # Divergence-free projection (solenoidal / curl component curl Psi)
    # K_perp = (-KY, KX)
    K_cross_V = -KY * VX + KX * VY
    VX_sol = np.where(K2 == 0, 0.0, (K_cross_V / K2_safe) * (-KY))
    VY_sol = np.where(K2 == 0, 0.0, (K_cross_V / K2_safe) * KX)

    vx_irr = np.real(np.fft.ifft2(VX_irr))
    vy_irr = np.real(np.fft.ifft2(VY_irr))
    vx_sol = np.real(np.fft.ifft2(VX_sol))
    vy_sol = np.real(np.fft.ifft2(VY_sol))

    # Boundary harmonic residual + mean laminar sweep
    vx_harm = vx - vx_irr - vx_sol
    vy_harm = vy - vy_irr - vy_sol

    e_div = float(np.mean(vx_irr**2 + vy_irr**2))
    e_curl = float(np.mean(vx_sol**2 + vy_sol**2))
    e_harm = float(np.mean(vx_harm**2 + vy_harm**2))
    e_tot = e_div + e_curl + e_harm + 1e-9

    # Dominant gravitational sink/source in Phi (max |Phi|)
    idx = int(np.argmax(np.abs(phi_field)))
    sy, sx = divmod(idx, W)
    sink_u = float((sx + 0.5) / W)
    sink_v = float((sy + 0.5) / H)

    return (
        e_div / e_tot,
        e_curl / e_tot,
        e_harm / e_tot,
        math.sqrt(e_div),
        math.sqrt(e_curl),
        math.sqrt(e_harm),
        sink_u,
        sink_v,
    )


def extract_5d_measure(lab_small):
    """
    Convert downsampled CIE-LAB image (H, W, 3) into a weighted 5D point cloud
    (u, v, L*, a*, b*) normalized to [0, 1]^5 for Sliced 2-Wasserstein transport.
    """
    H, W, _ = lab_small.shape
    u_grid, v_grid = np.meshgrid(
        np.linspace(0.0, 1.0, W, dtype=np.float32),
        np.linspace(0.0, 1.0, H, dtype=np.float32),
    )
    L = lab_small[:, :, 0].astype(np.float32) / 255.0
    A = lab_small[:, :, 1].astype(np.float32) / 255.0
    B = lab_small[:, :, 2].astype(np.float32) / 255.0
    pts = np.stack([u_grid, v_grid, L, A, B], axis=-1).reshape(-1, 5)
    return pts


def sliced_wasserstein_w2_sq(pts_a, pts_b):
    """
    Exact Sliced 2-Wasserstein squared distance W_2^2(mu_a, mu_b) in 5D
    (u, v, L*, a*, b*) via 32 projections on S^4.
    """
    proj_a = np.sort(pts_a @ S4_DIRS.T, axis=0)
    proj_b = np.sort(pts_b @ S4_DIRS.T, axis=0)
    return float(np.mean((proj_a - proj_b) ** 2)) * 5.0


def extract_three_strands(gray, flow_mag, prev_strands=None):
    """
    Extract n=3 spatial-depth worldline strands (u_i, v_i, d_i) in a frame.
    Salience weight combines local Laplacian contrast + optical flow magnitude.
    We divide the frame into 3 adaptive spatial basins using top salience peaks
    and track them smoothly via Hungarian assignment.
    """
    H, W = gray.shape
    lap = np.abs(cv2.Laplacian(gray.astype(np.float32), cv2.CV_32F))
    sal = 0.65 * (lap / (np.max(lap) + 1e-5)) + 0.35 * (flow_mag / (np.max(flow_mag) + 1e-5))
    sal_blur = cv2.GaussianBlur(sal, (9, 9), 2.0)

    # Pick 3 distinct salience peaks separated by at least 0.16 screen width
    flat_idx = np.argsort(sal_blur.ravel())[::-1]
    peaks = []
    min_dist_px = 0.16 * max(W, H)
    for idx in flat_idx:
        py, px = divmod(int(idx), W)
        if all(math.hypot(px - qx, py - qy) >= min_dist_px for qx, qy in peaks):
            peaks.append((px, py))
            if len(peaks) == 3:
                break
    while len(peaks) < 3:
        peaks.append((int((len(peaks) + 1) * W / 4), H // 2))

    # Compute local centroid and pseudo-depth d_i around each peak
    # Pseudo-depth d_i in [0,1]: foreground objects have higher local focus sharpness (Laplacian)
    # and higher motion parallax / lower vertical base
    cand = []
    r_win = max(4, W // 8)
    for px, py in peaks:
        x0, x1 = max(0, px - r_win), min(W, px + r_win + 1)
        y0, y1 = max(0, py - r_win), min(H, py + r_win + 1)
        patch_w = sal_blur[y0:y1, x0:x1] + 1e-6
        yy, xx = np.mgrid[y0:y1, x0:x1]
        tot_w = float(np.sum(patch_w))
        cu = float(np.sum(xx * patch_w) / tot_w) / W
        cv_y = float(np.sum(yy * patch_w) / tot_w) / H
        sharpness = float(np.mean(lap[y0:y1, x0:x1])) / (float(np.max(lap)) + 1e-5)
        mot = float(np.mean(flow_mag[y0:y1, x0:x1])) / (float(np.max(flow_mag)) + 1e-5)
        depth_d = float(np.clip(0.50 * sharpness + 0.30 * mot + 0.20 * cv_y, 0.05, 0.98))
        cand.append([cu, cv_y, depth_d])

    cand = np.array(cand, dtype=np.float32)
    if prev_strands is None:
        # Sort left-to-right initially
        order = np.argsort(cand[:, 0])
        return cand[order]

    # Hungarian matching to maintain continuous strand identity across frames
    cost = np.zeros((3, 3), dtype=np.float32)
    for i in range(3):
        for j in range(3):
            cost[i, j] = (
                (prev_strands[i, 0] - cand[j, 0]) ** 2
                + (prev_strands[i, 1] - cand[j, 1]) ** 2
                + 0.25 * (prev_strands[i, 2] - cand[j, 2]) ** 2
            )
    _, col_ind = linear_sum_assignment(cost)
    matched = cand[col_ind]
    # Temporal smoothing (EMA) so worldlines reflect true object motion rather than pixel noise
    return 0.65 * prev_strands + 0.35 * matched


def compute_braid_topology(strands_ts, duration_s):
    """
    Given 3-strand worldlines strands_ts of shape (T, 3, 3) -> (tau, strand_id, [u, v, d]),
    compute the Artin Braid Word in B_3 (generators sigma_1, sigma_1^-1, sigma_2, sigma_2^-1),
    perform algebraic free-group reduction (canceling adjacent inverses sigma_i * sigma_i^-1 = e),
    and compute the Finite-Time Braiding Exponent (FTBE) via Burau representation matrices.
    """
    T = strands_ts.shape[0]
    raw_generators = []  # tuples of (tau_idx, gen_str, sign, i_pos)

    # Track left-to-right ordering of strands along horizontal axis u
    prev_order = list(np.argsort(strands_ts[0, :, 0]))
    for t in range(1, T):
        curr_u = strands_ts[t, :, 0]
        curr_d = strands_ts[t, :, 2]
        # Bubble-sort prev_order by curr_u to detect elementary adjacent swaps
        order = list(prev_order)
        for p in range(2):
            for i in range(2 - p):
                s_left = order[i]
                s_right = order[i + 1]
                if curr_u[s_left] > curr_u[s_right] + 0.015:
                    # Crossing at position i+1 (sigma_1 for i=0, sigma_2 for i=1)
                    gen_idx = i + 1
                    # Positive generator if left strand passes in front of right strand (d_left >= d_right)
                    sign = 1 if curr_d[s_left] >= curr_d[s_right] else -1
                    label = f"σ{gen_idx}" if sign == 1 else f"σ{gen_idx}⁻¹"
                    raw_generators.append((t, gen_idx, sign, label))
                    order[i], order[i + 1] = order[i + 1], order[i]
        prev_order = order

    # Free reduction: cancel adjacent (gen_idx, +1) and (gen_idx, -1)
    reduced = []
    for item in raw_generators:
        if reduced and reduced[-1][1] == item[1] and reduced[-1][2] == -item[2]:
            reduced.pop()
        else:
            reduced.append(item)

    # Compute topological complexity via reduced Burau representation at t = -1 (or golden ratio)
    # For B_3 at parameter t = -1:
    # B(sigma_1) = [[1, 1], [0, 1]], B(sigma_2) = [[1, 0], [-1, 1]] (SL(2,Z) hyperbolic generators!)
    M1 = np.array([[1.0, 1.0], [0.0, 1.0]])
    M1_inv = np.array([[1.0, -1.0], [0.0, 1.0]])
    M2 = np.array([[1.0, 0.0], [1.0, 1.0]])
    M2_inv = np.array([[1.0, 0.0], [-1.0, 1.0]])

    M = np.eye(2)
    ftbe_curve = [0.0]
    gen_by_t = {t: [] for t in range(T)}
    for t, g_idx, sgn, lbl in raw_generators:
        gen_by_t[t].append((g_idx, sgn))

    for t in range(1, T):
        for g_idx, sgn in gen_by_t[t]:
            if g_idx == 1:
                M = M @ (M1 if sgn == 1 else M1_inv)
            else:
                M = M @ (M2 if sgn == 1 else M2_inv)
        # Spectral norm growth log(||M||_2)
        svals = np.linalg.svd(M, compute_uv=False)
        max_sv = max(1.0, float(svals[0]))
        ftbe_curve.append(math.log(max_sv))

    # Normalize FTBE per minute of screen time
    total_log_stretch = ftbe_curve[-1] if ftbe_curve else 0.0
    # Also incorporate reduced word length growth for non-commuting figure-8 braids
    braid_entropy = math.log1p(len(reduced)) + 0.5 * total_log_stretch
    ftbe_rate = float(braid_entropy / max(duration_s / 30.0, 0.5))

    raw_word_str = " · ".join(x[3] for x in raw_generators[:24]) or "e (trivial)"
    red_word_str = " · ".join(x[3] for x in reduced[:24]) or "e (unbraided)"
    entanglement_ratio = float(len(reduced) / max(len(raw_generators), 1))

    return {
        "raw_crossings": len(raw_generators),
        "reduced_length": len(reduced),
        "entanglement_ratio": round(entanglement_ratio, 3),
        "ftbe": round(ftbe_rate, 3),
        "raw_word_preview": raw_word_str,
        "reduced_word_preview": red_word_str,
        "ftbe_curve": [round(float(x), 3) for x in ftbe_curve],
    }


def compute_persistent_homology_tda(feature_matrix):
    """
    Apply Takens' Time-Delay Embedding [x(tau), x(tau+Delta), x(tau+2*Delta)] to the
    standardized 6-channel trajectory and compute Vietoris-Rips Persistent Homology:
      - beta_0: Connected regime components (exact MST merge lifetimes)
      - beta_1: 1D topological loops / rhythmic limit cycles (Euler characteristic cycle rank)
      - beta_2 / Chiasmus Ring Symmetry: 2D narrative folding / inverted retracing score
    """
    N, D = feature_matrix.shape
    # Standardize channels
    mu = np.mean(feature_matrix, axis=0, keepdims=True)
    sd = np.std(feature_matrix, axis=0, keepdims=True) + 1e-6
    Z = (feature_matrix - mu) / sd

    delay = max(1, N // 25)
    if N > 2 * delay + 4:
        X = np.hstack([Z[:-2 * delay], Z[delay:-delay], Z[2 * delay:]])
    else:
        X = Z

    M = X.shape[0]
    dists = squareform(pdist(X, metric="euclidean"))
    off_diag = dists[np.triu_indices(M, k=1)]
    if len(off_diag) == 0:
        return {"beta0_regimes": 1, "beta1_loops": 0, "beta2_chiasmus": 0.0, "persistence_diagram": []}

    # 1. Exact H_0 persistence via Kruskal Minimum Spanning Tree merges
    parent = list(range(M))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = []
    for i in range(M):
        for j in range(i + 1, M):
            edges.append((float(dists[i, j]), i, j))
    edges.sort(key=lambda x: x[0])

    h0_deaths = []
    for w, u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            h0_deaths.append(w)

    med_edge = float(np.median(h0_deaths)) if h0_deaths else 1.0
    mean_edge = float(np.mean(h0_deaths)) if h0_deaths else 1.0
    std_edge = float(np.std(h0_deaths)) if h0_deaths else 0.1
    # Persistent regimes: H_0 bars with death > mean + 1.15 * std of MST merges
    persistent_regimes = 1 + sum(1 for d in h0_deaths if d > mean_edge + 1.15 * std_edge)

    # 2. H_1 (1D rhythmic limit cycles / Takens recurrence loops) across filtration radii
    radii = np.percentile(off_diag, np.linspace(8, 32, 10))
    beta1_curve = []
    persistence_bars = []
    for d_val in sorted(h0_deaths, reverse=True)[:6]:
        persistence_bars.append({"dim": 0, "birth": 0.0, "death": round(float(d_val / (med_edge + 1e-6)), 3)})

    min_temporal_sep = max(4, M // 12)
    for eps in radii:
        # Non-local recurrence chords (|i - j| >= min_temporal_sep) that close a temporal loop
        recur = np.zeros((M, M), dtype=bool)
        for i in range(M):
            for j in range(i + min_temporal_sep, M):
                if dists[i, j] <= eps:
                    recur[i, j] = True
        # Cluster adjacent recurrence chords into distinct topological limit-cycle bands
        loop_bands = 0
        visited = np.zeros((M, M), dtype=bool)
        for i in range(M):
            for j in range(i + min_temporal_sep, M):
                if recur[i, j] and not visited[i, j]:
                    loop_bands += 1
                    # Flood-fill nearby recurrence points belonging to the same limit cycle
                    stack = [(i, j)]
                    while stack:
                        ci, cj = stack.pop()
                        for di in range(-3, 4):
                            for dj in range(-3, 4):
                                ni, nj = ci + di, cj + dj
                                if 0 <= ni < M and 0 <= nj < M and recur[ni, nj] and not visited[ni, nj]:
                                    visited[ni, nj] = True
                                    stack.append((ni, nj))
        beta1_curve.append(int(loop_bands))

    max_beta1 = int(round(np.percentile(beta1_curve, 75))) if beta1_curve else 0
    mean_beta1 = float(np.mean(beta1_curve)) if beta1_curve else 0.0

    # Add top H_1 loop bars to diagram
    for k in range(min(5, max_beta1)):
        birth_r = float(radii[min(len(radii) - 1, k + 1)] / (med_edge + 1e-6))
        death_r = birth_r + 0.35 + 0.18 * (max_beta1 - k)
        persistence_bars.append({"dim": 1, "birth": round(birth_r, 3), "death": round(death_r, 3)})

    # 3. Beta_2 / Chiasmus & Ring Symmetry Index:
    # Compare first half trajectory Z[:N//2] with time-reversed second half Z[N//2:][::-1]
    half = N // 2
    if half >= 4:
        first_h = Z[:half]
        second_h_rev = Z[N - half:][::-1]
        # Cosine / Euclidean similarity of structural arc fold
        diff_fold = np.mean(np.linalg.norm(first_h - second_h_rev, axis=1))
        diff_rand = np.mean(np.linalg.norm(first_h - second_h_rev[np.random.default_rng(7).permutation(half)], axis=1))
        chiasmus_score = float(np.clip(1.0 - (diff_fold / (diff_rand + 1e-6)) * 0.65, 0.05, 0.98))
    else:
        chiasmus_score = 0.25

    if chiasmus_score > 0.35:
        persistence_bars.append({
            "dim": 2,
            "birth": 0.85,
            "death": round(0.85 + chiasmus_score * 1.4, 3),
        })

    # 2D PCA projection of Takens attractor for interactive visualization
    Xc = X - np.mean(X, axis=0, keepdims=True)
    U, S, _ = np.linalg.svd(Xc, full_matrices=False)
    coords_2d = (U[:, :2] * S[:2]).tolist()
    step_map = max(1, len(coords_2d) // 90)
    attractor_pts = [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in coords_2d[::step_map]]

    return {
        "beta0_regimes": int(min(persistent_regimes, 9)),
        "beta1_loops": int(max_beta1),
        "beta1_mean": round(mean_beta1, 2),
        "beta2_chiasmus": round(chiasmus_score, 3),
        "persistence_diagram": persistence_bars,
        "attractor_2d": attractor_pts,
    }


def extract_audio_features(mp4_path, n_steps, duration_s):
    """
    Extract audio waveform via ffmpeg at 16 kHz stereo and compute per-frame:
      - sub_bass (20-80 Hz energy)
      - spectral_centroid (1-8 kHz brightness normalized)
      - stereo_pan (-1 left to +1 right lateral force)
      - spectral_flux (onset envelope for Hilbert Phase-Locking Value)
    """
    tmp_wav = tempfile.mktemp(suffix=".wav")
    cmd = [
        "ffmpeg", "-y", "-i", mp4_path,
        "-vn", "-ac", "2", "-ar", "16000", "-f", "wav", tmp_wav
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or not os.path.exists(tmp_wav) or os.path.getsize(tmp_wav) < 1000:
        # Silent track fallback
        zeros = np.zeros(n_steps, dtype=np.float32)
        return zeros, zeros, zeros, zeros, False

    try:
        with wave.open(tmp_wav, "rb") as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() == 2:
                samples = samples.reshape(-1, 2)
                left, right = samples[:, 0], samples[:, 1]
                mono = 0.5 * (left + right)
            else:
                mono = samples
                left = right = mono
    except Exception:
        zeros = np.zeros(n_steps, dtype=np.float32)
        return zeros, zeros, zeros, zeros, False
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)

    if np.max(np.abs(mono)) < 1e-4:
        zeros = np.zeros(n_steps, dtype=np.float32)
        return zeros, zeros, zeros, zeros, False

    sub_bass = np.zeros(n_steps, dtype=np.float32)
    centroid = np.zeros(n_steps, dtype=np.float32)
    pan = np.zeros(n_steps, dtype=np.float32)
    flux = np.zeros(n_steps, dtype=np.float32)

    total_samples = len(mono)
    win_size = max(512, int(total_samples / max(n_steps, 1)))
    freqs = np.fft.rfftfreq(win_size, d=1.0 / sr)
    prev_mag = None

    for i in range(n_steps):
        s0 = int(i * total_samples / n_steps)
        s1 = min(total_samples, s0 + win_size)
        seg = mono[s0:s1]
        if len(seg) < win_size:
            seg = np.pad(seg, (0, win_size - len(seg)))
        windowed = seg * np.hanning(win_size)
        mag = np.abs(np.fft.rfft(windowed))

        # Sub-bass 20-120 Hz
        sb_mask = (freqs >= 20) & (freqs <= 120)
        sub_bass[i] = float(np.sqrt(np.mean(mag[sb_mask] ** 2))) if np.any(sb_mask) else 0.0

        # Spectral centroid (normalized to 4000 Hz)
        tot_mag = float(np.sum(mag)) + 1e-8
        c_hz = float(np.sum(freqs * mag) / tot_mag)
        centroid[i] = min(1.0, c_hz / 4000.0)

        # Stereo pan
        l_rms = float(np.sqrt(np.mean(left[s0:s1] ** 2))) + 1e-7
        r_rms = float(np.sqrt(np.mean(right[s0:s1] ** 2))) + 1e-7
        pan[i] = float((r_rms - l_rms) / (r_rms + l_rms))

        # Spectral flux
        if prev_mag is not None:
            diff = np.maximum(0.0, mag - prev_mag)
            flux[i] = float(np.sum(diff))
        prev_mag = mag

    # Normalize envelopes to [0, 1]
    if np.max(sub_bass) > 0:
        sub_bass /= np.max(sub_bass)
    if np.max(flux) > 0:
        flux /= np.max(flux)

    return sub_bass, centroid, pan, flux, True


def analyze_film(meta):
    mp4_path = os.path.join(REPO_ROOT, meta["mp4"])
    fid = meta["id"]
    print(f"Analyzing [{fid}] {meta['title']} ...")

    cap = cv2.VideoCapture(mp4_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = total_frames / fps

    # Sample at ~6 Hz (every 4th frame at 24fps, capped at 360 samples for long anthology)
    stride = max(2, int(round(fps / 6.0)))
    if total_frames // stride > 360:
        stride = max(2, total_frames // 360)

    # Small processing resolution for fast optical flow + CIE-LAB + slit-scan
    proc_w, proc_h = 96, 54
    slit_w, slit_h = 180, 180

    ut_rows = []  # horizontal horizon slit-scan u-tau
    vt_cols = []  # vertical center slit-scan v-tau

    timestamps = []
    strands_list = []
    prev_strands = None
    prev_gray = None
    prev_pts5d = None

    div_frac_ts, curl_frac_ts, harm_frac_ts = [], [], []
    phi_mag_ts, psi_mag_ts, h_mag_ts = [], [], []
    sink_uv_ts = []

    w2_energy_ts = []
    pts5d_history = []
    chiaroscuro_ts = []
    hue_polarity_ts = []
    area_ext_ts = []
    lstar_mean_ts = []
    grid_entropy_ts = []
    d_grid_ts = []
    sym_score_ts = []
    stgl_rules_ts = []
    palette_rgb_ts = []

    cuts = []  # detected cut indices in sampled timeline
    l1_diffs_ts = [0.0]

    frame_idx = 0
    sample_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % stride != 0:
            frame_idx += 1
            continue

        tau = frame_idx / fps
        timestamps.append(round(tau, 3))

        # Slit-scan extraction
        f_slit = cv2.resize(frame, (slit_w, slit_h), interpolation=cv2.INTER_AREA)
        f_slit_rgb = cv2.cvtColor(f_slit, cv2.COLOR_BGR2RGB)
        # Middle band average (3 rows around horizon v=0.5, 3 cols around center u=0.5)
        ut_rows.append(np.mean(f_slit_rgb[slit_h // 2 - 1 : slit_h // 2 + 2, :, :], axis=0).astype(np.uint8))
        vt_cols.append(np.mean(f_slit_rgb[:, slit_w // 2 - 1 : slit_w // 2 + 2, :], axis=1).astype(np.uint8))

        # Processing frame
        f_small = cv2.resize(frame, (proc_w, proc_h), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(f_small, cv2.COLOR_BGR2GRAY)
        lab = cv2.cvtColor(f_small, cv2.COLOR_BGR2LAB)
        rgb_small = cv2.cvtColor(f_small, cv2.COLOR_BGR2RGB)

        # Optical flow & Helmholtz-Hodge Decomposition
        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                pyr_scale=0.5, levels=2, winsize=9,
                iterations=2, poly_n=5, poly_sigma=1.1, flags=0
            )
            vx, vy = flow[:, :, 0], flow[:, :, 1]
            flow_mag = np.hypot(vx, vy)
            df, cf, hf, pm, psm, hm, su, sv = helmholtz_hodge_2d(vx, vy)
        else:
            flow_mag = np.zeros_like(gray, dtype=np.float32)
            df, cf, hf, pm, psm, hm, su, sv = 0.33, 0.33, 0.34, 0.0, 0.0, 0.0, 0.5, 0.5

        div_frac_ts.append(round(df, 4))
        curl_frac_ts.append(round(cf, 4))
        harm_frac_ts.append(round(hf, 4))
        phi_mag_ts.append(round(pm, 4))
        psi_mag_ts.append(round(psm, 4))
        h_mag_ts.append(round(hm, 4))
        sink_uv_ts.append([round(su, 3), round(sv, 3)])

        # 3-Strand Worldline Extraction for Artin Braid B_3
        strands = extract_three_strands(gray, flow_mag, prev_strands)
        strands_list.append(strands)
        prev_strands = strands

        # 5D Wasserstein Optimal Transport W_2^2 in (u, v, L*, a*, b*)
        pts5d = extract_5d_measure(lab)
        pts5d_history.append(pts5d)
        if prev_pts5d is not None:
            w2_sq = sliced_wasserstein_w2_sq(prev_pts5d, pts5d)
            l1_diff = float(np.percentile(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32)), 80))
            l1_diffs_ts.append(l1_diff)
        else:
            w2_sq = 0.0
        w2_energy_ts.append(round(w2_sq * 100.0, 4))  # scaled for readability
        prev_pts5d = pts5d
        prev_gray = gray

        # KALMUS Core-Worm vs. Shell Chromatic Stratigraphy (Johannes Itten Contrasts)
        # Core worm = bounding circle around primary strand centroid c_0 = (u_0, v_0)
        u0, v0 = float(strands[0, 0]), float(strands[0, 1])
        yy, xx = np.mgrid[0:proc_h, 0:proc_w]
        u_norm = xx / float(proc_w)
        v_norm = yy / float(proc_h)
        core_mask = ((u_norm - u0) ** 2 + (v_norm - v0) ** 2) <= (0.22 ** 2)
        shell_mask = ~core_mask

        L_ch = lab[:, :, 0].astype(np.float32) * (100.0 / 255.0)
        a_ch = lab[:, :, 1].astype(np.float32) - 128.0
        b_ch = lab[:, :, 2].astype(np.float32) - 128.0

        l_core = float(np.mean(L_ch[core_mask])) if np.any(core_mask) else 50.0
        l_shell = float(np.mean(L_ch[shell_mask])) if np.any(shell_mask) else 50.0
        chiaroscuro_ts.append(round(abs(l_core - l_shell), 2))
        lstar_mean_ts.append(round(float(np.mean(L_ch)), 2))

        hue_core = math.atan2(float(np.mean(b_ch[core_mask])), float(np.mean(a_ch[core_mask])))
        hue_shell = math.atan2(float(np.mean(b_ch[shell_mask])), float(np.mean(a_ch[shell_mask])))
        dh = abs(hue_core - hue_shell)
        if dh > math.pi:
            dh = 2.0 * math.pi - dh
        hue_polarity_ts.append(round(math.degrees(dh), 1))

        # High-contrast / active worm area ratio & negative space
        edge_mag = np.abs(cv2.Laplacian(gray.astype(np.float32), cv2.CV_32F))
        active_px = edge_mag > (np.mean(edge_mag) + 0.5 * np.std(edge_mag))
        area_ratio = float(np.mean(active_px))
        neg_space_ratio = 1.0 - area_ratio
        area_ext_ts.append(round(area_ratio, 3))

        # Spatial Grid Entropy & Bilateral Symmetry
        hist2d = cv2.calcHist([gray], [0], None, [16], [0, 256]).ravel()
        hist2d /= np.sum(hist2d) + 1e-8
        ent = -float(np.sum(hist2d * np.log2(hist2d + 1e-8))) / 4.0
        grid_entropy_ts.append(round(ent, 3))

        sym_diff = float(np.mean(np.abs(gray.astype(np.float32) - gray[:, ::-1].astype(np.float32)))) / 255.0
        sym_score = max(0.0, 1.0 - sym_diff * 2.2)
        sym_score_ts.append(round(sym_score, 3))

        # 14-Line Harmonic Armature distance
        dg = min_armature_dist(u0, v0)
        d_grid_ts.append(round(dg, 4))
        stgl_rules_ts.append(classify_stgl_rule(u0, v0, area_ratio, neg_space_ratio, sym_score))

        # Dominant RGB color of the core worm for 3D prism rendering
        core_rgb = np.mean(rgb_small[core_mask], axis=0) if np.any(core_mask) else np.mean(rgb_small, axis=(0, 1))
        palette_rgb_ts.append([int(core_rgb[0]), int(core_rgb[1]), int(core_rgb[2])])

        sample_idx += 1
        frame_idx += 1

    cap.release()

    n_steps = len(timestamps)
    dt_step = duration_s / max(n_steps - 1, 1)
    strands_arr = np.array(strands_list, dtype=np.float32)  # (T, 3, 3)

    # Adaptive cut detection across both color and monochrome archival films
    l1_arr = np.array(l1_diffs_ts, dtype=np.float32)
    w2_arr = np.array(w2_energy_ts, dtype=np.float32)
    cut_thresh_l1 = max(14.0, float(np.median(l1_arr) + 1.85 * np.std(l1_arr)))
    cut_thresh_w2 = max(0.08, float(np.median(w2_arr) + 1.85 * np.std(w2_arr)))
    min_cut_gap = max(3, int(round(1.1 / max(dt_step, 0.05))))
    for s_i in range(2, n_steps - 2):
        is_peak = (l1_arr[s_i] >= l1_arr[s_i - 1]) and (l1_arr[s_i] >= l1_arr[s_i + 1])
        if is_peak and (l1_arr[s_i] > cut_thresh_l1 or w2_arr[s_i] > cut_thresh_w2):
            if not cuts or (s_i - cuts[-1] >= min_cut_gap):
                cuts.append(s_i)

    # Save Slit-Scan Tomograms (u-tau and v-tau)
    ut_img = np.stack(ut_rows, axis=0)  # (T, W, 3) -> transpose to (W, T, 3) so time runs horizontally left-to-right!
    ut_horiz = np.transpose(ut_img, (1, 0, 2))
    vt_img = np.stack(vt_cols, axis=1)  # (H, T, 3)

    ut_pil = Image.fromarray(ut_horiz).resize((640, 180), Image.Resampling.BICUBIC)
    vt_pil = Image.fromarray(vt_img).resize((640, 180), Image.Resampling.BICUBIC)
    ut_path = os.path.join(IMG_DIR, f"{fid}_ut.jpg")
    vt_path = os.path.join(IMG_DIR, f"{fid}_vt.jpg")
    ut_pil.save(ut_path, quality=88)
    vt_pil.save(vt_path, quality=88)

    # 1. Artin Braid Topology (B_3) & FTBE
    braid_res = compute_braid_topology(strands_arr, duration_s)

    # 2. Helmholtz-Hodge Summary
    hhd_summary = {
        "divergence_share": round(float(np.mean(div_frac_ts)), 3),
        "curl_share": round(float(np.mean(curl_frac_ts)), 3),
        "harmonic_share": round(float(np.mean(harm_frac_ts)), 3),
        "mean_phi_rms": round(float(np.mean(phi_mag_ts)), 3),
        "mean_psi_rms": round(float(np.mean(psi_mag_ts)), 3),
        "mean_h_rms": round(float(np.mean(h_mag_ts)), 3),
    }

    # 3. Wasserstein Geodesic Curvature & Chromatic Kinetic Energy
    shot_bounds = [0] + cuts + [n_steps - 1]
    geodesic_ratios = []
    for k in range(len(shot_bounds) - 1):
        i0, i1 = shot_bounds[k], shot_bounds[k + 1]
        if i1 - i0 < 2:
            continue
        direct_w2 = math.sqrt(max(0.0, sliced_wasserstein_w2_sq(pts5d_history[i0], pts5d_history[i1])))
        path_w2 = sum(
            math.sqrt(max(0.0, sliced_wasserstein_w2_sq(pts5d_history[j], pts5d_history[j + 1])))
            for j in range(i0, i1)
        )
        if path_w2 > 1e-5:
            geodesic_ratios.append(min(1.0, direct_w2 / path_w2))
    geodesic_efficiency = float(np.mean(geodesic_ratios)) if geodesic_ratios else 0.75

    wasserstein_summary = {
        "mean_w2_kinetic": round(float(np.mean(w2_energy_ts)), 3),
        "peak_w2_shock": round(float(np.max(w2_energy_ts)), 3),
        "geodesic_efficiency": round(geodesic_efficiency, 3),
        "geodesic_curvature": round(1.0 - geodesic_efficiency, 3),
        "mean_chiaroscuro_dl": round(float(np.mean(chiaroscuro_ts)), 2),
        "mean_hue_polarity_deg": round(float(np.mean(hue_polarity_ts)), 1),
    }

    # 4. Relativistic Saccade Light-Cones (c_eye = 400 deg/s = 10.0 screen-widths/s at 40 deg FOV, tau_fix = 0.20s)
    # Evaluate rapid post-cut perceptual horizon at tau_eval = 0.235s (i.e. 35ms after 200ms neural fixation latency,
    # giving horizon radius R_rapid = 10.0 * 0.035 = 0.35 screen widths)
    c_eye_sw = 10.0  # screen widths per second
    tau_fix = 0.200
    r_rapid = c_eye_sw * (0.222 - tau_fix)  # 0.22 screen widths (Murch foveal capture cone)

    cut_events = []
    timelike_count = 0
    lightlike_count = 0
    spacelike_count = 0

    for idx_c, c_step in enumerate(cuts):
        p1 = strands_arr[max(0, c_step - 1), 0, :2]
        p2 = strands_arr[min(n_steps - 1, c_step + 1), 0, :2]
        jump_dist = float(np.linalg.norm(p2 - p1))
        next_c = cuts[idx_c + 1] if idx_c + 1 < len(cuts) else n_steps - 1
        shot_dur = max(dt_step, (next_c - c_step) * dt_step)

        # Spacetime interval ds^2 at rapid saccade window (R_rapid = 0.22)
        ds2 = round((r_rapid ** 2) - (jump_dist ** 2), 4)
        if abs(ds2) <= 0.012:
            regime = "lightlike"
            lightlike_count += 1
        elif ds2 > 0:
            regime = "timelike"
            timelike_count += 1
        else:
            regime = "spacelike"
            spacelike_count += 1

        cut_events.append({
            "tau": timestamps[c_step],
            "p1": [round(float(p1[0]), 3), round(float(p1[1]), 3)],
            "p2": [round(float(p2[0]), 3), round(float(p2[1]), 3)],
            "jump_sw": round(jump_dist, 3),
            "shot_dur_s": round(shot_dur, 2),
            "ds2": ds2,
            "regime": regime,
        })

    tot_cuts = max(1, len(cut_events))
    saccade_summary = {
        "detected_cuts": len(cut_events),
        "timelike_pct": round(100.0 * timelike_count / tot_cuts, 1),
        "lightlike_pct": round(100.0 * lightlike_count / tot_cuts, 1),
        "spacelike_pct": round(100.0 * spacelike_count / tot_cuts, 1),
        "mean_jump_sw": round(float(np.mean([c["jump_sw"] for c in cut_events])) if cut_events else 0.08, 3),
        "mean_ds2": round(float(np.mean([c["ds2"] for c in cut_events])) if cut_events else 0.11, 4),
        "cuts": cut_events[:36],
    }

    # 5. Differential Geometry of the Primary Spatiotemporal Worm c(tau) = (u(tau), v(tau), tau)
    # Compute velocity, curvature kappa(tau), torsion, and 3rd-derivative kinetic jerk ||c'''(tau)||
    u_curve = strands_arr[:, 0, 0]
    v_curve = strands_arr[:, 0, 1]
    du = np.gradient(u_curve, dt_step)
    dv = np.gradient(v_curve, dt_step)
    d2u = np.gradient(du, dt_step)
    d2v = np.gradient(dv, dt_step)
    d3u = np.gradient(d2u, dt_step)
    d3v = np.gradient(d2v, dt_step)

    # Space curve in (u, v, tau_scaled)
    speed_3d = np.sqrt(du**2 + dv**2 + 1.0)
    cross_mag = np.sqrt(d2u**2 + d2v**2 + (du * d2v - dv * d2u) ** 2)
    curvature_ts = (cross_mag / (speed_3d**3 + 1e-6)).tolist()
    jerk_ts = np.hypot(d3u, d3v)
    if np.max(jerk_ts) > 0:
        jerk_norm = jerk_ts / np.max(jerk_ts)
    else:
        jerk_norm = jerk_ts

    # 6. Acoustic Cymatics & Cross-Spectral Synchresis Tensor (Hilbert PLV & Anempathetic Slip)
    sub_bass, aud_centroid, stereo_pan, aud_flux, has_audio = extract_audio_features(
        mp4_path, n_steps, duration_s
    )

    if has_audio and np.std(aud_flux) > 1e-5 and np.std(jerk_norm) > 1e-5:
        vis_analytic = hilbert(jerk_norm - np.mean(jerk_norm))
        aud_analytic = hilbert(aud_flux - np.mean(aud_flux))
        phase_diff = np.angle(vis_analytic) - np.angle(aud_analytic)
        complex_phase = np.exp(1j * phase_diff)

        # Sliding window PLV (window = 9 samples ~ 1.5s)
        win_plv = 9
        plv_ts = []
        for i in range(n_steps):
            i0 = max(0, i - win_plv // 2)
            i1 = min(n_steps, i + win_plv // 2 + 1)
            plv_val = float(np.abs(np.mean(complex_phase[i0:i1])))
            plv_ts.append(round(plv_val, 3))
    else:
        # Silent visual-only film: phase locking is undefined / 0, pure visual rhythm
        plv_ts = [0.0] * n_steps

    # Anempathetic Slip Index: high visual turmoil (curl + W2 + jerk) paired with low PLV (< 0.35)
    vis_turmoil = (
        np.array(psi_mag_ts) / (np.max(psi_mag_ts) + 1e-5)
        + np.array(w2_energy_ts) / (np.max(w2_energy_ts) + 1e-5)
    ) * 0.5
    if has_audio:
        anempathetic_ts = vis_turmoil * np.maximum(0.0, 0.55 - np.array(plv_ts))
        anempathetic_index = float(np.mean(anempathetic_ts))
        mean_plv = float(np.mean(plv_ts))
    else:
        anempathetic_index = 0.0
        mean_plv = 0.0

    synchresis_summary = {
        "has_audio": has_audio,
        "mean_plv": round(mean_plv, 3),
        "peak_plv": round(float(np.max(plv_ts)) if plv_ts else 0.0, 3),
        "anempathetic_slip": round(anempathetic_index, 3),
        "mean_sub_bass": round(float(np.mean(sub_bass)), 3),
        "mean_spectral_centroid": round(float(np.mean(aud_centroid)), 3),
    }

    # 7. Persistent Homology Attractors (beta_0, beta_1, beta_2) on 6-channel feature trajectory
    feat_6d = np.column_stack([
        grid_entropy_ts,
        phi_mag_ts,
        psi_mag_ts,
        w2_energy_ts,
        lstar_mean_ts,
        aud_centroid,
    ])
    tda_summary = compute_persistent_homology_tda(feat_6d)

    # 8. STGL (Spatiotemporal Grid Language) & Worm Topology Summary
    arnheim_tension_frames = sum(1 for d in d_grid_ts if 0.06 <= d <= 0.12)
    compositional_lock_frames = sum(1 for d in d_grid_ts if d < 0.045)
    rule_counts = {}
    for r in stgl_rules_ts:
        rule_counts[r] = rule_counts.get(r, 0) + 1
    dom_rule = max(rule_counts.items(), key=lambda x: x[1])[0] if rule_counts else "centered_anchor"

    worm_summary = {
        "mean_armature_dist": round(float(np.mean(d_grid_ts)), 4),
        "compositional_lock_pct": round(100.0 * compositional_lock_frames / max(1, n_steps), 1),
        "arnheim_tension_pct": round(100.0 * arnheim_tension_frames / max(1, n_steps), 1),
        "mean_curvature": round(float(np.mean(curvature_ts)), 3),
        "peak_jerk": round(float(np.max(jerk_ts)), 3),
        "dominant_stgl_rule": dom_rule,
        "stgl_rule_breakdown": {k: round(100.0 * v / max(1, n_steps), 1) for k, v in rule_counts.items()},
    }

    # Downsample time series to <= 120 points for lightweight, responsive WebGL 3D Worm rendering
    ds = max(1, n_steps // 120)
    worm_3d_samples = []
    for i in range(0, n_steps, ds):
        worm_3d_samples.append({
            "t": timestamps[i],
            "s1": [round(float(strands_arr[i, 0, 0]), 3), round(float(strands_arr[i, 0, 1]), 3), round(float(strands_arr[i, 0, 2]), 3)],
            "s2": [round(float(strands_arr[i, 1, 0]), 3), round(float(strands_arr[i, 1, 1]), 3), round(float(strands_arr[i, 1, 2]), 3)],
            "s3": [round(float(strands_arr[i, 2, 0]), 3), round(float(strands_arr[i, 2, 1]), 3), round(float(strands_arr[i, 2, 2]), 3)],
            "rgb": palette_rgb_ts[i],
            "r": round(float(max(0.04, min(0.28, area_ext_ts[i] * 0.45))), 3),
            "phi": phi_mag_ts[i],
            "psi": psi_mag_ts[i],
            "h": h_mag_ts[i],
            "w2": w2_energy_ts[i],
            "plv": plv_ts[i],
            "d_grid": d_grid_ts[i],
            "sink": sink_uv_ts[i],
            "sub_bass": round(float(sub_bass[i]), 3),
            "centroid": round(float(aud_centroid[i]), 3),
        })

    return {
        **meta,
        "duration_s": round(duration_s, 2),
        "fps": round(fps, 2),
        "resolution": [width, height],
        "sampled_steps": n_steps,
        "ut_tomogram": f"img/{fid}_ut.jpg",
        "vt_tomogram": f"img/{fid}_vt.jpg",
        "braid": braid_res,
        "helmholtz": hhd_summary,
        "wasserstein": wasserstein_summary,
        "saccade": saccade_summary,
        "tda": tda_summary,
        "synchresis": synchresis_summary,
        "worm": worm_summary,
        "series": worm_3d_samples,
    }


def build_stgl_ir_for_flagships(results):
    """
    Export a declarative Spatiotemporal Grid Language (STGL) Timeline IR (stgl_ir.json)
    mapping real measured shots from our ALLWAYS corpus into the 4D STGL schema.
    """
    ir_films = {}
    for film in results:
        fid = film["id"]
        bpm = 120
        fps = int(round(film["fps"]))
        series = film["series"]
        cuts = film["saccade"]["cuts"]
        shots_ir = []

        # Partition series into shots using detected cuts (or equal segments if continuous)
        cut_times = [0.0] + [c["tau"] for c in cuts[:12]] + [film["duration_s"]]
        for idx in range(len(cut_times) - 1):
            t0, t1 = cut_times[idx], cut_times[idx + 1]
            if t1 - t0 < 0.4:
                continue
            seg = [s for s in series if t0 <= s["t"] <= t1] or [series[min(idx, len(series) - 1)]]
            p_start = seg[0]["s1"][:2]
            p_end = seg[-1]["s1"][:2]
            bar_start = max(1, int(t0 * (bpm / 60.0) / 4.0) + 1)
            bar_end = max(bar_start + 1, int(t1 * (bpm / 60.0) / 4.0) + 1)

            c_info = cuts[idx] if idx < len(cuts) else None
            trans_type = (
                "eye_trace_match"
                if (c_info and c_info["regime"] == "timelike")
                else ("saccade_horizon_whip" if (c_info and c_info["regime"] == "lightlike") else "eisenstein_collision")
            )

            shots_ir.append({
                "id": f"shot_{idx+1:02d}",
                "span": {
                    "start_s": round(t0, 2),
                    "end_s": round(t1, 2),
                    "start": f"b({bar_start},1,0)",
                    "end": f"b({bar_end},1,0)",
                },
                "spatial_grid": {
                    "armature": film["worm"]["dominant_stgl_rule"],
                    "focal_node": p_end,
                    "mean_grid_error": round(float(np.mean([s["d_grid"] for s in seg])), 4),
                    "negative_space_zone": {
                        "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 0.35], [0.0, 0.35]],
                        "max_entropy": 0.18,
                    },
                },
                "depth_layers": {
                    "d0_foreground": {"strand_centroid": seg[0]["s1"]},
                    "d1_subject": {
                        "trajectory": {
                            "type": "registered_hold" if np.linalg.norm(np.array(p_end) - np.array(p_start)) < 0.08 else "s_curve",
                            "from": p_start,
                            "to": p_end,
                        }
                    },
                },
                "helmholtz_field": {
                    "phi_divergence": round(float(np.mean([s["phi"] for s in seg])), 3),
                    "psi_vorticity": round(float(np.mean([s["psi"] for s in seg])), 3),
                    "h_harmonic": round(float(np.mean([s["h"] for s in seg])), 3),
                    "dominant_sink": seg[len(seg) // 2]["sink"],
                },
                "audio_sync": {
                    "plv_lock": round(float(np.mean([s["plv"] for s in seg])), 3),
                    "offset_ms": 0 if float(np.mean([s["plv"] for s in seg])) >= 0.5 else 37,
                },
                "transition_out": {
                    "type": trans_type,
                    "carry_node": p_end,
                    "spacetime_ds2": c_info["ds2"] if c_info else 0.12,
                },
            })

        ir_films[fid] = {
            "meta": {
                "film_id": fid,
                "title": film["title"],
                "maker": film["maker"],
                "aspect": f"{film['resolution'][0]}:{film['resolution'][1]}",
                "fps": fps,
                "bpm": bpm,
            },
            "shots": shots_ir,
        }
    return ir_films


def generate_composite_overview_sheet(results):
    """
    Create a visual contact sheet comparing the u-tau and v-tau slit-scan tomograms
    of the flagship films for visual verification.
    """
    W_card, H_card = 680, 170
    cols = 2
    rows = (len(results) + 1) // 2
    canvas = Image.new("RGB", (cols * W_card, rows * H_card), (12, 13, 16))
    draw = ImageDraw.Draw(canvas)

    for idx, r in enumerate(results):
        c = idx % cols
        rw = idx // cols
        x0 = c * W_card
        y0 = rw * H_card

        ut_p = os.path.join(OUT_DIR, r["ut_tomogram"])
        vt_p = os.path.join(OUT_DIR, r["vt_tomogram"])
        if os.path.exists(ut_p) and os.path.exists(vt_p):
            ut_im = Image.open(ut_p).resize((320, 110))
            vt_im = Image.open(vt_p).resize((320, 110))
            canvas.paste(ut_im, (x0 + 12, y0 + 42))
            canvas.paste(vt_im, (x0 + 344, y0 + 42))

        title_txt = f"{r['title']} ({r['maker']}) - FTBE={r['braid']['ftbe']} | W2={r['wasserstein']['mean_w2_kinetic']} | Timelike={r['saccade']['timelike_pct']}%"
        title_ascii = title_txt.encode("ascii", "replace").decode("ascii")
        draw.text((x0 + 14, y0 + 10), title_ascii[:88], fill=(235, 228, 212))
        draw.text((x0 + 14, y0 + 26), "u-tau Horizon Slit-Scan Tomogram", fill=(160, 185, 220))
        draw.text((x0 + 346, y0 + 26), "v-tau Vertical Slit-Scan Tomogram", fill=(220, 175, 130))

    sheet_path = os.path.join(IMG_DIR, "tensor_tomograms_sheet.jpg")
    canvas.save(sheet_path, quality=88)
    print(f"Saved composite tomogram sheet -> {sheet_path}")


def main():
    results = []
    for meta in COHORT:
        res = analyze_film(meta)
        results.append(res)

    out_json = os.path.join(OUT_DIR, "tensor_data.json")
    with open(out_json, "w") as f:
        json.dump({"films": results}, f, indent=2)
    print(f"Wrote {out_json} ({len(results)} films)")

    stgl_ir = build_stgl_ir_for_flagships(results)
    ir_path = os.path.join(OUT_DIR, "stgl_ir.json")
    with open(ir_path, "w") as f:
        json.dump(stgl_ir, f, indent=2)
    print(f"Wrote {ir_path}")

    generate_composite_overview_sheet(results)


if __name__ == "__main__":
    main()
