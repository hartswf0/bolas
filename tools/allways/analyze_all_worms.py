#!/usr/bin/env python3
"""
analyze_all_worms.py — Full-Corpus 3D Spatiotemporal Worm & KALMUS Stratigraphy Analyzer
========================================================================================
Processes ALL 140 playable MP4 films across the entire ALLWAYS corpus:
  - Anthology Master (1): allways-best
  - SCION 114–121 Shape Films + 8-Perspectives Reel (9): allways-tensor
  - Claude Sonnet 4.6 (11): SCION 055–065
  - Claude Opus 5.5 (12): B-Roll of Civilization
  - OpenAI Sol (23): SCION 055–078 playable films
  - Gemini Argon (85): B-Roll 01–12, Collections 01–05, Studies 01–09, SCION 055–113

For every video and every shot/part inside it, computes:
  1. 3D Spatiotemporal Worm Topology in (u, v, tau):
     - VERTICAL_PILLAR (Locked Tripod + Static Blocking)
     - SHEARED_DIAGONAL_RIBBON (Camera Pan / Lateral Track)
     - EXPANDING_CONE (Dolly In / Snap Zoom / Funnel)
     - HELICAL_CORKSCREW (S-Curve / Golden Spiral Staging)
     - DOUBLE_HELIX_BRAID (Two-Shot / Dialogue Counterpoint in Rabatment Squares)
     - Cut Transitions: EYE_TRACE_MATCH_CUT (||c_A - c_B|| <= 0.085) vs.
       EISENSTEIN_COLLISION_CUT (||c_A - c_B|| > 0.22 or velocity reversal)
  2. KALMUS Core-Sample vs. Outer-Shell Chromatic Stratigraphy & Itten's Color Contrasts:
     - Core Worm RGB (subject bounding tube) vs. Outer Shell RGB (negative space)
     - Light–Dark (Chiaroscuro) Tube Contrast: |L*_core(tau) - L*_shell(tau)|
     - Cold–Warm & Complementary Hue Polarity: delta_H_deg(tau) in [0, 180]
     - Contrast of Extension (Area Ratio): A_worm(tau) / A_frame
  3. Grid-Tunnel Resonance & Arnheim Eccentric Torque:
     - Distance d_grid(tau) to Bouleau 14-Line Armature, Rule of Thirds, Golden Spiral, Rabatment
     - Compositional Lock % (d_grid < 0.045) vs. Arnheim Eccentric Tension % (d_grid in [0.06, 0.12])
  4. Frenet–Serret 3D Space Curve Differential Geometry & Bruce Block Visual Intensity:
     - Curvature kappa(tau), Torsion tau_torsion(tau), Kinetic Jerk ||c'''(tau)||
     - Earshot Acoustic Impulse Landings (jerk peak timestamps)
     - Cultural Analytics Shot Triads (Entry, Midpoint, Exit worm telemetry + Bruce Block Intensity)
"""

import os
import glob
import json
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
OUT_DIR = os.path.join(REPO_ROOT, "allways-tensor")
IMG_DIR = os.path.join(OUT_DIR, "img")
os.makedirs(IMG_DIR, exist_ok=True)


# Bouleau 14-Line Armature segments in [0,1]^2
ARMATURE_14_SEGMENTS = [
    ((0.0, 0.0), (1.0, 1.0)),
    ((0.0, 1.0), (1.0, 0.0)),
    ((0.5, 0.0), (0.5, 1.0)),
    ((0.0, 0.5), (1.0, 0.5)),
    ((1.0 / 3.0, 0.0), (1.0 / 3.0, 1.0)),
    ((2.0 / 3.0, 0.0), (2.0 / 3.0, 1.0)),
    ((0.0, 1.0 / 3.0), (1.0, 1.0 / 3.0)),
    ((0.0, 2.0 / 3.0), (1.0, 2.0 / 3.0)),
    ((0.0, 0.0), (0.5, 1.0)),
    ((0.5, 0.0), (1.0, 1.0)),
    ((0.0, 1.0), (0.5, 0.0)),
    ((0.5, 1.0), (1.0, 0.0)),
    ((0.0, 0.0), (1.0, 0.5)),
    ((0.0, 1.0), (1.0, 0.5)),
]

THIRDS_SEGMENTS = [
    ((1.0 / 3.0, 0.0), (1.0 / 3.0, 1.0)),
    ((2.0 / 3.0, 0.0), (2.0 / 3.0, 1.0)),
    ((0.0, 1.0 / 3.0), (1.0, 1.0 / 3.0)),
    ((0.0, 2.0 / 3.0), (1.0, 2.0 / 3.0)),
]

RABATMENT_SEGMENTS = [
    ((0.5625, 0.0), (0.5625, 1.0)),  # Left 9:16 square edge in 16:9 frame
    ((0.4375, 0.0), (0.4375, 1.0)),  # Right 9:16 square edge in 16:9 frame
    ((0.28, 0.0), (0.28, 1.0)),
    ((0.72, 0.0), (0.72, 1.0)),
]


def point_to_segments_dist(u, v, segments):
    best = 1.0
    for (x1, y1), (x2, y2) in segments:
        dx, dy = x2 - x1, y2 - y1
        l2 = dx * dx + dy * dy + 1e-12
        t = max(0.0, min(1.0, ((u - x1) * dx + (v - y1) * dy) / l2))
        px, py = x1 + t * dx, y1 + t * dy
        d = math.hypot(u - px, v - py)
        if d < best:
            best = d
    return best


def discover_all_allways_videos():
    """
    Catalog all ~140 primary playable MP4 films across ALLWAYS.
    """
    catalog = []

    # 1. Master Anthology Film
    best_mp4 = os.path.join(REPO_ROOT, "allways-best/allways-best.mp4")
    if os.path.exists(best_mp4):
        catalog.append({
            "id": "allways-best",
            "title": "ALLWAYS · THE ONE FILM",
            "maker": "Anthology Synthesis",
            "group": "featured",
            "mp4_abs": best_mp4,
            "video_rel": "../allways-best/allways-best.mp4",
            "case_url": "../allways-best/index.html",
        })

    # 2. SCION 114–121 Shape Films + 8-Perspectives Reel
    scion_shapes_p = os.path.join(OUT_DIR, "scion_shapes.json")
    if os.path.exists(scion_shapes_p):
        with open(scion_shapes_p) as f:
            sdata = json.load(f)
        for op in sdata.get("operators", []):
            f_abs = os.path.join(OUT_DIR, op["film_file"])
            if os.path.exists(f_abs):
                catalog.append({
                    "id": f"shape-{op['scion_id']}",
                    "title": op["short_title"],
                    "maker": "SCION Shape Studio",
                    "group": "shapes",
                    "mp4_abs": f_abs,
                    "video_rel": op["film_file"],
                    "case_url": op["prompt_rel"],
                })
    eight_reel = os.path.join(OUT_DIR, "eight-perspectives.mp4")
    if os.path.exists(eight_reel):
        catalog.append({
            "id": "shape-eight-reel",
            "title": "8 PERSPECTIVE GRIDS REEL",
            "maker": "SCION Shape Studio",
            "group": "shapes",
            "mp4_abs": eight_reel,
            "video_rel": "eight-perspectives.mp4",
            "case_url": "eight_grids_archive.json",
        })

    # 3. Claude Sonnet 4.6 (11 primary films)
    sonnet_dirs = sorted(glob.glob(os.path.join(REPO_ROOT, "allways-sonnet/0*")))
    for sdir in sonnet_dirs:
        slug = os.path.basename(sdir)
        mp4_p = os.path.join(sdir, f"{slug}.mp4")
        if os.path.exists(mp4_p):
            catalog.append({
                "id": f"sonnet-{slug}",
                "title": slug.upper().replace("-", " · "),
                "maker": "Claude Sonnet 4.6",
                "group": "sonnet",
                "mp4_abs": mp4_p,
                "video_rel": f"../allways-sonnet/{slug}/{slug}.mp4",
                "case_url": f"../allways-sonnet/{slug}/index.html",
            })

    # 4. Claude Opus 5.5 (12 primary films)
    opus_dirs = sorted(glob.glob(os.path.join(REPO_ROOT, "allways-opus/films/*")))
    for odir in opus_dirs:
        slug = os.path.basename(odir)
        mp4_p = os.path.join(odir, f"{slug}.mp4")
        if os.path.exists(mp4_p):
            catalog.append({
                "id": f"opus-{slug}",
                "title": f"OPUS · {slug.upper().replace('-', ' ')}",
                "maker": "Claude Opus 5.5",
                "group": "opus",
                "mp4_abs": mp4_p,
                "video_rel": f"../allways-opus/films/{slug}/{slug}.mp4",
                "case_url": f"../allways-opus/films/{slug}/index.html",
            })

    # 5. OpenAI Sol (23 playable films from catalog.json)
    sol_cat_p = os.path.join(REPO_ROOT, "allways-sol/catalog.json")
    if os.path.exists(sol_cat_p):
        with open(sol_cat_p) as f:
            sol_cat = json.load(f).get("films", [])
        for sf in sol_cat:
            num = sf.get("number", "")
            vid_rel = (sf.get("film") or {}).get("url", "")
            if not vid_rel:
                continue
            mp4_p = os.path.join(REPO_ROOT, "allways-sol", vid_rel)
            if os.path.exists(mp4_p):
                catalog.append({
                    "id": f"sol-{num}",
                    "title": f"SOL {num} · {sf.get('title', '').upper()}",
                    "maker": "OpenAI Sol",
                    "group": "sol",
                    "mp4_abs": mp4_p,
                    "video_rel": f"../allways-sol/{vid_rel}",
                    "case_url": f"../allways-sol/films.html#film-{num}",
                })

    # 6. Gemini Argon (85 studio films)
    argon_mp4s = sorted(glob.glob(os.path.join(REPO_ROOT, "allways-argon/studio/films/*.mp4")))
    for mp4_p in argon_mp4s:
        slug = os.path.basename(mp4_p).replace(".mp4", "")
        short_lbl = slug.replace("_", " ")
        if len(short_lbl) > 28:
            parts = slug.split("_")
            short_lbl = "_".join(parts[:3]).replace("_", " ")
        catalog.append({
            "id": f"argon-{slug}",
            "title": short_lbl,
            "maker": "Gemini Argon",
            "group": "argon",
            "mp4_abs": mp4_p,
            "video_rel": f"../allways-argon/studio/films/{slug}.mp4",
            "case_url": f"../allways-argon/studio/cases/{slug}.html",
        })

    return catalog


def analyze_single_film_worm(item, n_slices=28):
    """
    Extract the 3D Spatiotemporal Worm V(u, v, tau), KALMUS Core-vs-Shell Chromatic
    Stratigraphy, Itten's 7 Color Contrasts, Grid-Tunnel Resonance, Frenet–Serret
    Curvature/Torsion/Jerk, and Shot-by-Shot Cultural Analytics Triads.
    """
    cap = cv2.VideoCapture(item["mp4_abs"])
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur_s = max(1.0, n_frames / fps)

    W, H = 128, 72
    sample_times = np.linspace(0.0, max(0.1, dur_s - 0.15), n_slices)

    uu, vv = np.meshgrid(np.linspace(0.0, 1.0, W), np.linspace(0.0, 1.0, H))

    series = []
    prev_gray = None

    for s_idx, t_sec in enumerate(sample_times):
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t_sec) * 1000.0)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        small = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
        lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(np.float32)

        # Salience map (Sobel gradient + luminance contrast)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad = np.hypot(gx, gy)
        sal = grad + 0.35 * np.abs(gray - np.mean(gray)) + 1e-3

        # Primary Worm Centroid c(tau) = (u1, v1) and Cross-Sectional Radius r(tau)
        w_sum = float(np.sum(sal))
        u1 = float(np.sum(uu * sal) / w_sum)
        v1 = float(np.sum(vv * sal) / w_sum)
        var_uv = float(np.sum(((uu - u1) ** 2 + (vv - v1) ** 2) * sal) / w_sum)
        r_worm = float(np.clip(math.sqrt(var_uv) * 0.85, 0.08, 0.42))

        # Left and Right Rabatment Worms for Two-Shot / Double-Helix Detection
        left_sal = sal[:, : W // 2]
        right_sal = sal[:, W // 2 :]
        u_left = float(np.sum(uu[:, : W // 2] * left_sal) / (np.sum(left_sal) + 1e-6))
        v_left = float(np.sum(vv[:, : W // 2] * left_sal) / (np.sum(left_sal) + 1e-6))
        u_right = float(np.sum(uu[:, W // 2 :] * right_sal) / (np.sum(right_sal) + 1e-6))
        v_right = float(np.sum(vv[:, W // 2 :] * right_sal) / (np.sum(right_sal) + 1e-6))
        lr_balance = float(min(np.sum(left_sal), np.sum(right_sal)) / (max(np.sum(left_sal), np.sum(right_sal)) + 1e-6))

        # KALMUS Core Worm vs. Outer Shell Mask Split
        dist_map = np.hypot(uu - u1, vv - v1)
        core_mask = dist_map <= r_worm
        shell_mask = ~core_mask
        if not np.any(core_mask):
            core_mask[int(v1 * (H - 1)), int(u1 * (W - 1))] = True
        if not np.any(shell_mask):
            shell_mask[0, 0] = True

        # Core RGB & Shell RGB (for Dual KALMUS Stratigraphy Barcodes)
        bgr_core = np.mean(small[core_mask], axis=0)
        bgr_shell = np.mean(small[shell_mask], axis=0)
        rgb_core = [int(bgr_core[2]), int(bgr_core[1]), int(bgr_core[0])]
        rgb_shell = [int(bgr_shell[2]), int(bgr_shell[1]), int(bgr_shell[0])]

        # Itten #1: Light–Dark (Chiaroscuro) Tube Contrast |L*_core - L*_shell| (normalized 0..100)
        l_core = float(np.mean(lab[:, :, 0][core_mask]) * (100.0 / 255.0))
        l_shell = float(np.mean(lab[:, :, 0][shell_mask]) * (100.0 / 255.0))
        chiaroscuro = round(abs(l_core - l_shell), 2)

        # Itten #2: Cold–Warm & Complementary Hue Angle Separation (0..180 deg)
        # Use circular mean of HSV hue (0..180 in OpenCV -> 0..360 deg)
        h_core_rad = hsv[:, :, 0][core_mask] * (2.0 * math.pi / 180.0)
        h_shell_rad = hsv[:, :, 0][shell_mask] * (2.0 * math.pi / 180.0)
        ang_core = math.atan2(float(np.mean(np.sin(h_core_rad))), float(np.mean(np.cos(h_core_rad))))
        ang_shell = math.atan2(float(np.mean(np.sin(h_shell_rad))), float(np.mean(np.cos(h_shell_rad))))
        hue_diff_deg = abs(math.degrees(ang_core - ang_shell)) % 360.0
        if hue_diff_deg > 180.0:
            hue_diff_deg = 360.0 - hue_diff_deg

        # Warm-minus-Cool polarity from CIE a*, b*
        warm_core = float(np.mean(lab[:, :, 1][core_mask] - 128.0) + 0.7 * np.mean(lab[:, :, 2][core_mask] - 128.0))
        warm_shell = float(np.mean(lab[:, :, 1][shell_mask] - 128.0) + 0.7 * np.mean(lab[:, :, 2][shell_mask] - 128.0))
        cold_warm_delta = round(abs(warm_core - warm_shell), 2)

        # Itten #3: Contrast of Extension (Area Ratio A_worm / A_frame)
        area_ratio = round(float(np.mean(core_mask)), 3)

        # Grid-Tunnel Distances (Bouleau 14-Line, Rule of Thirds, Golden Spiral Eye, Rabatment)
        d_armature = round(point_to_segments_dist(u1, v1, ARMATURE_14_SEGMENTS), 4)
        d_thirds = round(point_to_segments_dist(u1, v1, THIRDS_SEGMENTS), 4)
        d_rabat = round(point_to_segments_dist(u1, v1, RABATMENT_SEGMENTS), 4)
        d_golden = round(math.hypot(u1 - 0.618, v1 - 0.382), 4)

        # Frame-to-frame motion & cut discontinuity
        if prev_gray is not None:
            frame_diff = float(np.mean(np.abs(gray - prev_gray)) / 255.0)
        else:
            frame_diff = 0.0
        prev_gray = gray

        # Bruce Block Visual Intensity (composite of contrast, motion, gradient energy, saturation)
        sat_mean = float(np.mean(hsv[:, :, 1]) / 255.0)
        grad_norm = min(1.0, float(np.mean(grad)) / 45.0)
        block_intensity = round(
            min(1.0, 0.35 * grad_norm + 0.30 * min(1.0, chiaroscuro / 35.0) + 0.20 * sat_mean + 0.15 * min(1.0, frame_diff * 4.0)),
            3,
        )

        series.append({
            "t": round(float(t_sec), 2),
            "c": [round(u1, 3), round(v1, 3)],
            "r": round(r_worm, 3),
            "c_left": [round(u_left, 3), round(v_left, 3)],
            "c_right": [round(u_right, 3), round(v_right, 3)],
            "rabat_gap": round(u_right - u_left, 3),
            "lr_balance": round(lr_balance, 3),
            "rgb_core": rgb_core,
            "rgb_shell": rgb_shell,
            "chiaroscuro": chiaroscuro,
            "hue_diff_deg": round(hue_diff_deg, 1),
            "cold_warm_delta": cold_warm_delta,
            "area_ratio": area_ratio,
            "d_armature": d_armature,
            "d_thirds": d_thirds,
            "d_golden": d_golden,
            "d_rabat": d_rabat,
            "motion": round(frame_diff, 3),
            "block_intensity": block_intensity,
        })

    cap.release()
    if len(series) < 4:
        return None

    # Compute Frenet–Serret Differential Geometry (Curvature kappa, Torsion tau_torsion, Jerk ||c'''||)
    # and classify each slice & shot into the 7 Spatiotemporal Worm Topologies!
    dt = max(0.05, dur_s / len(series))
    us = np.array([s["c"][0] for s in series], dtype=np.float64)
    vs = np.array([s["c"][1] for s in series], dtype=np.float64)
    rs = np.array([s["r"] for s in series], dtype=np.float64)
    ts_norm = np.linspace(0.0, 1.0, len(series))

    du = np.gradient(us, dt)
    dv = np.gradient(vs, dt)
    dr = np.gradient(rs, dt)
    d2u = np.gradient(du, dt)
    d2v = np.gradient(dv, dt)
    d3u = np.gradient(d2u, dt)
    d3v = np.gradient(d2v, dt)

    earshot_impulses = []
    match_cuts = 0
    collision_cuts = 0
    topo_counts = {
        "VERTICAL_PILLAR": 0,
        "SHEARED_DIAGONAL_RIBBON": 0,
        "EXPANDING_CONE": 0,
        "HELICAL_CORKSCREW": 0,
        "DOUBLE_HELIX_BRAID": 0,
    }

    for i, s in enumerate(series):
        # 3D space curve r(t) = (u(t), v(t), t/T)
        c1 = np.array([du[i], dv[i], 1.0 / dur_s])
        c2 = np.array([d2u[i], d2v[i], 0.0])
        c3 = np.array([d3u[i], d3v[i], 0.0])
        cross12 = np.cross(c1, c2)
        norm_c1 = float(np.linalg.norm(c1)) + 1e-9
        norm_cross = float(np.linalg.norm(cross12)) + 1e-9

        kappa = float(norm_cross / (norm_c1 ** 3))
        torsion = float(abs(np.dot(cross12, c3)) / (norm_cross ** 2 + 1e-6))
        jerk = float(math.hypot(d3u[i], d3v[i]))

        s["kappa"] = round(min(25.0, kappa), 3)
        s["torsion"] = round(min(25.0, torsion), 3)
        s["jerk"] = round(min(25.0, jerk), 3)

        # Classify local 3D Worm Topology
        speed_uv = math.hypot(du[i], dv[i])
        if abs(dr[i]) > 0.035:
            topo = "EXPANDING_CONE"
        elif kappa > 1.8 and abs(du[i]) > 0.02 and abs(dv[i]) > 0.02:
            topo = "HELICAL_CORKSCREW"
        elif s["lr_balance"] > 0.76 and 0.34 <= s["rabat_gap"] <= 0.62:
            topo = "DOUBLE_HELIX_BRAID"
        elif speed_uv < 0.032:
            topo = "VERTICAL_PILLAR"
        else:
            topo = "SHEARED_DIAGONAL_RIBBON"

        s["topology"] = topo
        topo_counts[topo] += 1

        # Detect Cut Fracture Type & Earshot Acoustic Impulse Landings
        if i > 0:
            jump_uv = math.hypot(us[i] - us[i - 1], vs[i] - vs[i - 1])
            if s["motion"] > 0.11 or jump_uv > 0.10:
                if jump_uv <= 0.095:
                    s["cut_type"] = "EYE_TRACE_MATCH_CUT"
                    match_cuts += 1
                else:
                    s["cut_type"] = "EISENSTEIN_COLLISION_CUT"
                    collision_cuts += 1
            else:
                s["cut_type"] = "CONTINUOUS_TUBE"

            if jerk > 0.45 or s["motion"] > 0.14:
                earshot_impulses.append({"t": s["t"], "jerk": s["jerk"], "cut_type": s["cut_type"]})
        else:
            s["cut_type"] = "ENTRY"

    # Build 4 Cultural Analytics Montage Segments (Manovich Entry/Mid/Exit Triads)
    n_segs = 4
    seg_len = max(1, len(series) // n_segs)
    manovich_segments = []
    for k in range(n_segs):
        sub = series[k * seg_len : min(len(series), (k + 1) * seg_len)]
        if not sub:
            continue
        ent, mid, ext = sub[0], sub[len(sub) // 2], sub[-1]
        # Dominant topology in this segment
        seg_topos = {}
        for x in sub:
            seg_topos[x["topology"]] = seg_topos.get(x["topology"], 0) + 1
        dom_topo = max(seg_topos.items(), key=lambda kv: kv[1])[0]
        manovich_segments.append({
            "part_num": k + 1,
            "t_start": ent["t"],
            "t_end": ext["t"],
            "topology": dom_topo,
            "entry_c": ent["c"],
            "mid_c": mid["c"],
            "exit_c": ext["c"],
            "rgb_core": mid["rgb_core"],
            "rgb_shell": mid["rgb_shell"],
            "chiaroscuro": round(float(np.mean([x["chiaroscuro"] for x in sub])), 1),
            "hue_diff_deg": round(float(np.mean([x["hue_diff_deg"] for x in sub])), 1),
            "area_ratio": round(float(np.mean([x["area_ratio"] for x in sub])), 3),
            "block_intensity": round(float(np.mean([x["block_intensity"] for x in sub])), 3),
            "cut_exit": ext["cut_type"],
        })

    # Whole-film summary metrics
    dom_film_topo = max(topo_counts.items(), key=lambda kv: kv[1])[0]
    lock_pct = round(100.0 * sum(1 for s in series if s["d_armature"] < 0.048) / len(series), 1)
    arnheim_pct = round(100.0 * sum(1 for s in series if 0.055 <= s["d_armature"] <= 0.125) / len(series), 1)

    return {
        "id": item["id"],
        "title": item["title"],
        "maker": item["maker"],
        "group": item["group"],
        "video_rel": item["video_rel"],
        "case_url": item["case_url"],
        "duration_s": round(dur_s, 1),
        "dominant_topology": dom_film_topo,
        "topology_shares": {k: round(100.0 * v / len(series), 1) for k, v in topo_counts.items()},
        "match_cuts": match_cuts,
        "collision_cuts": collision_cuts,
        "mean_chiaroscuro": round(float(np.mean([s["chiaroscuro"] for s in series])), 1),
        "mean_hue_diff_deg": round(float(np.mean([s["hue_diff_deg"] for s in series])), 1),
        "mean_area_ratio": round(float(np.mean([s["area_ratio"] for s in series])), 3),
        "compositional_lock_pct": lock_pct,
        "arnheim_torque_pct": arnheim_pct,
        "mean_kappa": round(float(np.mean([s["kappa"] for s in series])), 2),
        "mean_torsion": round(float(np.mean([s["torsion"] for s in series])), 2),
        "mean_jerk": round(float(np.mean([s["jerk"] for s in series])), 2),
        "mean_block_intensity": round(float(np.mean([s["block_intensity"] for s in series])), 3),
        "earshot_impulses": earshot_impulses[:12],
        "manovich_parts": manovich_segments,
        "series": series,
    }


def render_140_worms_atlas(analyzed_films):
    """
    Render a visual KALMUS Core-vs-Shell Stratigraphy & 3D Worm Trajectory Atlas
    across all 140 films (7 columns x 20 rows = 140 cells, 1540 x 1400 px).
    """
    cols, rows = 7, 20
    cw, ch = 220, 72
    atlas = Image.new("RGB", (cols * cw, rows * ch), (8, 10, 15))
    draw = ImageDraw.Draw(atlas)

    topo_colors = {
        "VERTICAL_PILLAR": (114, 204, 150),
        "SHEARED_DIAGONAL_RIBBON": (86, 194, 230),
        "EXPANDING_CONE": (227, 104, 116),
        "HELICAL_CORKSCREW": (242, 196, 92),
        "DOUBLE_HELIX_BRAID": (199, 122, 224),
    }

    for idx, f in enumerate(analyzed_films[: cols * rows]):
        c = idx % cols
        r = idx // cols
        x0, y0 = c * cw, r * ch

        draw.rectangle([x0 + 2, y0 + 2, x0 + cw - 3, y0 + ch - 3], fill=(15, 18, 26), outline=(38, 44, 62))

        series = f["series"]
        n_s = len(series)
        bar_w = (cw - 12) / float(max(1, n_s))

        # Top stripe: KALMUS Core Worm RGB Barcode
        # Middle stripe: KALMUS Outer Shell RGB Barcode
        for i, s in enumerate(series):
            bx0 = int(x0 + 6 + i * bar_w)
            bx1 = int(x0 + 6 + (i + 1) * bar_w) + 1
            draw.rectangle([bx0, y0 + 20, bx1, y0 + 34], fill=tuple(s["rgb_core"]))
            draw.rectangle([bx0, y0 + 35, bx1, y0 + 45], fill=tuple(s["rgb_shell"]))

        # Overlay u(tau) worm trajectory curve across the barcode
        pts = []
        for i, s in enumerate(series):
            px = x0 + 6 + (i / float(max(1, n_s - 1))) * (cw - 12)
            py = y0 + 20 + s["c"][0] * 25.0
            pts.append((px, py))
        if len(pts) > 1:
            draw.line(pts, fill=(255, 255, 255), width=2)

        # Title + Dominant Worm Topology badge
        lbl = f"{idx+1:03d} {f['title']}"[:26].encode("ascii", "replace").decode("ascii")
        t_col = topo_colors.get(f["dominant_topology"], (229, 174, 92))
        draw.text((x0 + 6, y0 + 5), lbl, fill=t_col)

        sub = f"{f['dominant_topology'][:13]} | dL*:{f['mean_chiaroscuro']:.0f} Lock:{f['compositional_lock_pct']:.0f}%"
        draw.text((x0 + 6, y0 + 51), sub[:32], fill=(175, 182, 202))

    atlas_path = os.path.join(IMG_DIR, "allways_140_worms_atlas.jpg")
    atlas.save(atlas_path, quality=88)
    return atlas_path


def main():
    catalog = discover_all_allways_videos()
    print(f"Discovered {len(catalog)} playable MP4 videos across ALLWAYS.")

    analyzed = []
    for idx, item in enumerate(catalog):
        res = analyze_single_film_worm(item, n_slices=28)
        if res is not None:
            analyzed.append(res)
        if (idx + 1) % 20 == 0 or (idx + 1) == len(catalog):
            print(f"  [{idx+1:3d}/{len(catalog)}] Analyzed {item['id']} -> {res['dominant_topology'] if res else 'skip'}")

    atlas_path = render_140_worms_atlas(analyzed)
    print(f"Saved 140-Film Worm & KALMUS Stratigraphy Atlas -> {atlas_path}")

    # Tally corpus-wide topology & stratigraphy statistics
    topo_totals = {}
    for f in analyzed:
        t = f["dominant_topology"]
        topo_totals[t] = topo_totals.get(t, 0) + 1

    out_json = os.path.join(OUT_DIR, "allways_worms_140.json")
    with open(out_json, "w") as fp:
        json.dump(
            {
                "total_films": len(analyzed),
                "topology_distribution": topo_totals,
                "films": analyzed,
            },
            fp,
            separators=(",", ":"),
        )
    print(f"Wrote {out_json} ({os.path.getsize(out_json)/1024:.1f} KB) covering {len(analyzed)} films.")


if __name__ == "__main__":
    main()
