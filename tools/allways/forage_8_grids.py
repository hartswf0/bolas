#!/usr/bin/env python3
"""
forage_8_grids.py — Archival Forage & Computer Vision Detector for the 8 Composition Grids
==========================================================================================
Searches the ALLWAYS / Moving Image Archive corpus across all 4 makers (Opus 5.5, Argon,
Sol, Sonnet) for the 8 visual composition rules shown sequentially in:
  "Life Is All About Perspective! #shorts" (@gfxmotionbyahmar, YouTube QNvK63WetSA)

1. Golden Ratio / Fibonacci Spiral (1:1.618) — Logarithmic spiral + Golden Rectangles
2. Frame in a Frame (Sub-framing) — Three-sided / inner rectangular aperture boundary
3. S-Curve (Leading Curve) — Smooth S-shaped cubic Bezier curve from bottom-left to top-right
4. Symmetry (Vertical Bisector) — Single vertical center line (50/50 mirror split)
5. The Rule of Thirds (3x3 Grid) — Two horizontal + two vertical lines at 1/3 & 2/3 + 4 power nodes
6. Centered (Center Channel + Horizon) — Two narrow parallel center verticals + lower baseline
7. V-Shape (Converging Wedge / Triangle) — Two diagonals converging to bottom-center apex
8. Negative Space (Upper-Frame Boundary) — Wide U-shaped upper frame bracket (open sky/field)
"""

import os
import re
import glob
import json
import math
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
OUT_DIR = os.path.join(REPO_ROOT, "allways-tensor")
IMG_DIR = os.path.join(OUT_DIR, "img")
os.makedirs(IMG_DIR, exist_ok=True)

RULES_SPEC = [
    {
        "num": 1,
        "id": "golden_spiral",
        "name": "Golden Ratio / Fibonacci Spiral (1:1.618)",
        "short_ts": "00:00 – 00:06",
        "geometry": "Logarithmic spiral subdivided into Golden Rectangles (1 : 0.618 : 0.382)",
        "ref_scene": "Physical acrylic Golden Ratio Card framing a street cone & curved shadow (00:00), then rowboat & overhanging tree branches on a lake (00:03)",
        "keywords": r"\b(spiral|boat|rowboat|lake|water|branch|tree|shadow|cone|compass|curve|arc|orbit|shell|galaxy|vortex|wheel|circle|lens|dial)\b",
    },
    {
        "num": 2,
        "id": "frame_in_frame",
        "name": "Frame in a Frame (Sub-framing)",
        "short_ts": "00:07 – 00:08",
        "geometry": "Three-sided inner rectangular boundary enclosing interior depth vista",
        "ref_scene": "Graffiti-painted concrete balcony opening framing the Manhattan skyline and Brooklyn Bridge",
        "keywords": r"\b(window|door|doorway|arch|bridge|balcony|frame|tunnel|mirror|viewfinder|portal|corridor|opening|gate|threshold|porch|cab|windshield)\b",
    },
    {
        "num": 3,
        "id": "s_curve",
        "name": "S-Curve (Leading Curve)",
        "short_ts": "00:09 – 00:11",
        "geometry": "Smooth S-shaped cubic Bezier curve from bottom-left to top-right",
        "ref_scene": "Winding park pathway guiding the eye from foreground grass into background trees",
        "keywords": r"\b(path|pathway|road|winding|river|stream|track|tracks|highway|trail|coast|shore|ribbon|snake|meander|curve|hill|slope|parabola)\b",
    },
    {
        "num": 4,
        "id": "symmetry",
        "name": "Symmetry (Vertical Bisector)",
        "short_ts": "00:11 – 00:13",
        "geometry": "Single vertical center line (50/50 mirror split at u = 0.50)",
        "ref_scene": "Bisects the ribbed white arches of the World Trade Center Oculus into mirror-image halves",
        "keywords": r"\b(symmetry|symmetric|aisle|church|cathedral|arches|hall|corridor|twin|mirror|frontal|center|centered|columns|pillars|nave|oculus)\b",
    },
    {
        "num": 5,
        "id": "rule_of_thirds",
        "name": "The Rule of Thirds (3×3 Grid)",
        "short_ts": "00:14 – 00:15",
        "geometry": "Two horizontal lines and two vertical lines at 1/3 and 2/3 intervals (4 power-point intersections)",
        "ref_scene": "Places the river horizon on the lower horizontal line, a seated person on the left vertical line, and the bridge tower on the right vertical line",
        "keywords": r"\b(horizon|river|bridge|tower|seated|sitting|harbor|bay|shoreline|two|pair|conversation|bench|watching|looking|landscape)\b",
    },
    {
        "num": 6,
        "id": "centered",
        "name": "Centered (Center Channel + Horizon)",
        "short_ts": "00:16 – 00:17",
        "geometry": "Two narrow parallel vertical lines in the center (u = 0.42, 0.58) crossed by a lower horizontal baseline (v = 0.68)",
        "ref_scene": "Locks a lone subject sitting dead-center on a park bench along the lower third baseline",
        "keywords": r"\b(lone|alone|single|seated|sitting|bench|chair|standing|man|woman|worker|figure|statue|monument|post|desk|operator)\b",
    },
    {
        "num": 7,
        "id": "v_shape",
        "name": "V-Shape (Converging Wedge / Triangle)",
        "short_ts": "00:18 – 00:20",
        "geometry": "Two diagonal lines converging from upper corners toward a bottom-center apex (0.50, 0.84)",
        "ref_scene": "Frames the sunlit gap between two people seated in park chairs and the V-shaped opening in the tree canopy",
        "keywords": r"\b(valley|canyon|gorge|wedge|triangle|gap|between|two|flanking|trees|canopy|v-shape|converging|funnel|chute|prow|bow)\b",
    },
    {
        "num": 8,
        "id": "negative_space",
        "name": "Negative Space (Upper-Frame Boundary)",
        "short_ts": "00:21 – 00:23",
        "geometry": "Wide U-shaped upper frame bracket isolating open sky above lower-third silhouette",
        "ref_scene": "Isolates the open twilight sky across the upper two-thirds of the frame above the Empire State Building silhouette",
        "keywords": r"\b(sky|cloud|clouds|silhouette|skyline|tower|spire|horizon|vast|empty|air|breath|twilight|sunset|desert|ocean|plain|roof)\b",
    },
]


def harvest_candidate_shots():
    """
    Collect candidate archival shots across:
      1. allways-argon/studio/manifests/all_films_manifest.json (85 films)
      2. allways-sonnet/*/edl.json (11 films)
      3. allways-opus/films/*/edl.json (12 films)
      4. allways-best/edl.json (24 cuts)
    """
    candidates = []

    # 1. Argon 85-film manifest
    argon_manifest = os.path.join(REPO_ROOT, "allways-argon/studio/manifests/all_films_manifest.json")
    if os.path.exists(argon_manifest):
        films = json.load(open(argon_manifest))
        # Prioritize flagship diverse films so we don't extract 600 frames via ffmpeg
        priority_slugs = {
            "SCION_055_Words_Polysemic_Relay",
            "SCION_056_Symmetry_Imperfect_Pairing",
            "SCION_059_Ball_Graphic_Constancy",
            "SCION_063_Breath_Respired_Interval",
            "SCION_064_Parabolas_Different_Causes",
            "SCION_066_Tango_Cyclic_Room",
            "SCION_068_Powers_Of_Ten_Scale_Traverse",
            "SCION_073_Walk_Through_H_Cartographic_Passage",
            "SCION_074_The_Falls_Directory_Index",
            "SCION_075_High_School_Institutional_Routine",
            "SCION_076_Life_In_A_Day_Synchronized_Ordinary",
            "SCION_076_Sacred_Distributed_Ritual_Logic",
            "SCION_077_Baraka_Contemplative_Counterpoint",
            "SCION_079_Qatsi_Three_Technological_Regimes",
            "SCION_081_Human_Testimony_And_Aerial_Breathing_Room",
            "SCION_083_Berlin_City_Symphony",
            "SCION_086_Songs_Second_Floor_Tableau_Pressure",
            "SCION_088_Le_Quattro_Volte_Nonhuman_Relay",
            "SCION_089_Planimetric_Geometry_Times_Encounter",
            "SCION_090_The_Clock_Horological_Montage",
            "SCION_091_Watchtower_Momentum_Across_Discontinuity",
            "SCION_100_Short_History_Of_The_Highrise",
            "STUDY_03_The_Eye_Trace_Archive",
            "COLL_01_Equivalents",
            "BROLL_01_Nobody_Home",
            "BROLL_03_Terra_Incognita",
            "BROLL_05_Cut_To_The_Chase",
            "BROLL_06_Kinetic",
            "BROLL_09_Anybody_Anywhere",
            "BROLL_12_Planimetric",
        }
        for fm in films:
            slug = fm.get("slug", "")
            if slug not in priority_slugs:
                continue
            mp4_p = os.path.join(REPO_ROOT, "allways-argon/studio/films", f"{slug}.mp4")
            if not os.path.exists(mp4_p):
                continue
            for seg in fm.get("edl", []):
                if seg.get("type") != "shot":
                    continue
                mid_t = 0.5 * (float(seg.get("start_sec", 0.0)) + float(seg.get("end_sec", 2.0)))
                candidates.append({
                    "maker": "Gemini Argon",
                    "film_id": slug,
                    "film_title": fm.get("title", slug),
                    "case_url": f"../allways-argon/cases/{slug}.html",
                    "video_rel": f"../allways-argon/studio/films/{slug}.mp4",
                    "mp4_path": mp4_p,
                    "timestamp_s": round(mid_t, 2),
                    "start_s": float(seg.get("start_sec", 0.0)),
                    "dur_s": float(seg.get("dur_s", 3.0)),
                    "source_title": seg.get("source_title", "Archival Record"),
                    "source_year": seg.get("source_year", ""),
                    "clip_id": seg.get("clip_id", ""),
                    "desc": f"{seg.get('action', '')} {seg.get('nearmatch', '')} {fm.get('title', '')}",
                })

    # 2. Sonnet 11 films (already have pre-extracted frames or MP4s!)
    for edl_p in sorted(glob.glob(os.path.join(REPO_ROOT, "allways-sonnet/*/edl.json"))):
        folder = os.path.dirname(edl_p)
        slug = os.path.basename(folder)
        mp4_p = os.path.join(folder, f"{slug}.mp4")
        if not os.path.exists(mp4_p):
            continue
        d = json.load(open(edl_p))
        t_acc = 0.0
        for idx, ev in enumerate(d.get("events", [])):
            dur = float(ev.get("dur", 2.5))
            layers = ev.get("layers", [])
            if layers:
                lbl = ev.get("label", "")
                src_id = layers[0].get("src", "")
                candidates.append({
                    "maker": "Claude Sonnet",
                    "film_id": slug,
                    "film_title": d.get("title", slug),
                    "case_url": f"../allways-sonnet/{slug}/index.html",
                    "video_rel": f"../allways-sonnet/{slug}/{slug}.mp4",
                    "mp4_path": mp4_p,
                    "timestamp_s": round(t_acc + dur * 0.5, 2),
                    "start_s": round(t_acc, 2),
                    "dur_s": round(dur, 2),
                    "source_title": f"MIA {src_id[:8]}",
                    "source_year": "",
                    "clip_id": src_id,
                    "desc": lbl,
                })
            t_acc += dur

    # 3. Opus 12 films
    for edl_p in sorted(glob.glob(os.path.join(REPO_ROOT, "allways-opus/films/*/edl.json"))):
        folder = os.path.dirname(edl_p)
        slug = os.path.basename(folder)
        mp4_p = os.path.join(folder, f"{slug}.mp4")
        if not os.path.exists(mp4_p):
            continue
        d = json.load(open(edl_p))
        shots = d.get("shots") or d.get("segments") or (d if isinstance(d, list) else [])
        t_acc = 0.0
        for idx, s in enumerate(shots):
            if not isinstance(s, dict):
                continue
            dur = float(s.get("duration") or s.get("dur") or (float(s.get("out", 3)) - float(s.get("in", 0))) or 3.0)
            why = s.get("why") or s.get("note") or s.get("description") or s.get("action") or ""
            stitle = s.get("source_title") or s.get("title") or slug
            candidates.append({
                "maker": "Claude Opus 5.5",
                "film_id": f"opus-{slug}",
                "film_title": slug.replace("-", " ").title(),
                "case_url": f"../allways-opus/films/{slug}/index.html",
                "video_rel": f"../allways-opus/films/{slug}/{slug}.mp4",
                "mp4_path": mp4_p,
                "timestamp_s": round(t_acc + dur * 0.5, 2),
                "start_s": round(t_acc, 2),
                "dur_s": round(dur, 2),
                "source_title": stitle,
                "source_year": s.get("year", ""),
                "clip_id": str(s.get("clip_id") or s.get("id") or ""),
                "desc": f"{why} {stitle}",
            })
            t_acc += dur

    return candidates


def score_frame_eight_rules(bgr, desc_text):
    """
    Compute a geometric + semantic score in [0, 1] for each of the 8 composition rules
    on a single video frame (resized to 160x90).
    """
    H, W = 90, 160
    small = cv2.resize(bgr, (W, H), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    edges = cv2.Canny((gray * 255).astype(np.uint8), 50, 130).astype(np.float32) / 255.0

    # Gradient orientation
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gmag = np.hypot(gx, gy) + 1e-6

    yy, xx = np.mgrid[0:H, 0:W]
    u = xx / float(W)
    v = yy / float(H)

    scores = {}

    # 1. Golden Ratio / Fibonacci Spiral:
    # Salience density near Golden Eye (0.618, 0.382) or (0.382, 0.382) + curved arc gradient variance
    eye_mask = ((u - 0.618) ** 2 + (v - 0.382) ** 2 <= 0.16 ** 2) | ((u - 0.382) ** 2 + (v - 0.618) ** 2 <= 0.16 ** 2)
    spiral_sal = float(np.mean(gmag[eye_mask])) / (float(np.mean(gmag)) + 1e-4)
    scores["golden_spiral"] = np.clip(0.45 * min(1.0, spiral_sal / 1.8), 0.0, 0.75)

    # 2. Frame in a Frame (Sub-framing):
    # Darker or high-structure outer border frame (u<0.16 or u>0.84 or v<0.16) enclosing bright/active center window
    outer_ring = (u < 0.16) | (u > 0.84) | (v < 0.16)
    inner_win = (u >= 0.22) & (u <= 0.78) & (v >= 0.22) & (v <= 0.82)
    lum_contrast = max(0.0, float(np.mean(gray[inner_win]) - np.mean(gray[outer_ring])))
    edge_border = float(np.mean(edges[outer_ring])) / (float(np.mean(edges)) + 1e-4)
    scores["frame_in_frame"] = np.clip(0.55 * min(1.0, lum_contrast * 2.4 + 0.25 * edge_border), 0.0, 0.78)

    # 3. S-Curve (Leading Curve):
    # Edge support along S-shaped cubic locus u_s(v) = 0.5 + 0.28 * sin(2*pi*(v - 0.5))
    u_scurve = 0.5 - 0.28 * np.sin(np.pi * (v - 0.5) * 1.6)
    s_band = np.abs(u - u_scurve) <= 0.09
    s_support = float(np.mean(edges[s_band])) / (float(np.mean(edges)) + 1e-4)
    scores["s_curve"] = np.clip(0.48 * min(1.0, s_support / 1.75), 0.0, 0.75)

    # 4. Symmetry (Vertical Bisector u = 0.50):
    # Direct pixel & edge bilateral mirror correlation across u = 0.50
    mirror_diff = float(np.mean(np.abs(gray - gray[:, ::-1])))
    edge_sym = 1.0 - float(np.mean(np.abs(cv2.GaussianBlur(edges, (7, 7), 1.5) - cv2.GaussianBlur(edges[:, ::-1], (7, 7), 1.5))))
    scores["symmetry"] = np.clip(0.65 * (1.0 - mirror_diff * 2.1) + 0.15 * edge_sym, 0.0, 0.82)

    # 5. The Rule of Thirds (3x3 Grid):
    # Horizontal edge line near v=2/3 or v=1/3 + salience at (1/3, 2/3) and (2/3, 1/3) power points
    horiz_band = (np.abs(v - 0.667) <= 0.05) | (np.abs(v - 0.333) <= 0.05)
    h_energy = float(np.mean(np.abs(gy[horiz_band]))) / (float(np.mean(np.abs(gy))) + 1e-4)
    p_nodes = ((u - 0.333) ** 2 + (v - 0.667) ** 2 <= 0.11 ** 2) | ((u - 0.667) ** 2 + (v - 0.333) ** 2 <= 0.11 ** 2)
    node_sal = float(np.mean(gmag[p_nodes])) / (float(np.mean(gmag)) + 1e-4)
    scores["rule_of_thirds"] = np.clip(0.30 * min(1.0, h_energy / 1.6) + 0.35 * min(1.0, node_sal / 1.6), 0.0, 0.76)

    # 6. Centered (Center Channel u in [0.42, 0.58] + Horizon v = 0.68):
    center_chan = (u >= 0.41) & (u <= 0.59) & (v >= 0.25) & (v <= 0.82)
    flank_chan = ((u < 0.32) | (u > 0.68)) & (v >= 0.25) & (v <= 0.82)
    center_dom = float(np.mean(gmag[center_chan])) / (float(np.mean(gmag[flank_chan])) + 1e-4)
    scores["centered"] = np.clip(0.55 * min(1.0, center_dom / 2.1), 0.0, 0.76)

    # 7. V-Shape (Converging Wedge toward bottom-center apex (0.50, 0.85)):
    # Two diagonal arms: u_left(v) = 0.12 + 0.38*(v/0.85), u_right(v) = 0.88 - 0.38*(v/0.85)
    v_norm = np.clip(v / 0.85, 0.0, 1.0)
    v_arms = (np.abs(u - (0.12 + 0.38 * v_norm)) <= 0.07) | (np.abs(u - (0.88 - 0.38 * v_norm)) <= 0.07)
    wedge_sup = float(np.mean(edges[v_arms])) / (float(np.mean(edges)) + 1e-4)
    scores["v_shape"] = np.clip(0.50 * min(1.0, wedge_sup / 1.65), 0.0, 0.75)

    # 8. Negative Space (Upper-Frame Boundary v < 0.64 smooth/open, lower third v >= 0.64 high contrast):
    upper_zone = v < 0.62
    lower_zone = v >= 0.64
    upper_calm = 1.0 - min(1.0, float(np.mean(edges[upper_zone])) * 6.5)
    lower_detail = min(1.0, float(np.mean(gmag[lower_zone])) / (float(np.mean(gmag[upper_zone])) + 1e-4) / 2.4)
    scores["negative_space"] = np.clip(0.45 * upper_calm + 0.35 * lower_detail, 0.0, 0.80)

    # Boost with semantic keyword match from archival shot description
    is_split_screen = "056-symmetry" in desc_text.lower() or "p1a" in desc_text.lower() or "p2a" in desc_text.lower() or "p3a" in desc_text.lower()
    for spec in RULES_SPEC:
        rid = spec["id"]
        matches = re.findall(spec["keywords"], desc_text, flags=re.I)
        if matches:
            scores[rid] = min(0.99, scores[rid] + min(0.34, 0.14 * len(set(m.lower() for m in matches))))
        if is_split_screen and rid != "symmetry":
            scores[rid] *= 0.45

    if re.search(r"park path|winding|niagara|crop duster|curved trajectory|branching river", desc_text, re.I):
        scores["s_curve"] = min(0.99, scores["s_curve"] + 0.28)
    if re.search(r"compass line|lone cedar|tree.*branch|rowboat|spiral", desc_text, re.I):
        scores["golden_spiral"] = min(0.99, scores["golden_spiral"] + 0.36)
    if re.search(r"twin doorways|electric house|symmetric", desc_text, re.I):
        scores["symmetry"] = min(0.995, scores["symmetry"] + 0.25)
    if re.search(r"empty station platform|iron canopy|berlin.*station", desc_text, re.I):
        scores["v_shape"] = min(0.99, scores["v_shape"] + 0.38)
    if re.search(r"scatter radar|water beneath distant mountains|hi diddle diddle|shoreline", desc_text, re.I):
        scores["rule_of_thirds"] = min(0.99, scores["rule_of_thirds"] + 0.26)

    return {k: round(float(v), 4) for k, v in scores.items()}


def draw_rule_overlay_pil(pil_img, rule_id, rule_num, rule_name, short_ts, source_label):
    """
    Draw the exact yellow/gold geometric composition grid + physical acrylic card frame
    from 'Life Is All About Perspective! #shorts' (@gfxmotionbyahmar) onto a 640x360 PIL image.
    """
    img = pil_img.convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    gold = (242, 196, 92, 235)
    gold_dim = (242, 196, 92, 110)
    cyan = (86, 194, 230, 220)
    white = (255, 255, 255, 235)

    # Outer acrylic viewfinder card bevel
    pad = 14
    draw.rectangle([pad, pad, W - pad, H - pad], outline=(255, 255, 255, 90), width=1)

    if rule_id == "golden_spiral":
        # Subdivided Golden Rectangles + Fibonacci Spiral converging to (0.618, 0.382)
        x0, y0, x1, y1 = pad, pad, W - pad, H - pad
        gx = int(x0 + (x1 - x0) * 0.618)
        gy = int(y0 + (y1 - y0) * 0.618)
        draw.line([(gx, y0), (gx, y1)], fill=gold_dim, width=2)
        draw.line([(gx, gy), (x1, gy)], fill=gold_dim, width=2)
        gx2 = int(gx + (x1 - gx) * 0.382)
        draw.line([(gx2, gy), (gx2, y1)], fill=gold_dim, width=1)

        # Logarithmic spiral polyline converging to (0.68, 0.42)
        cx, cy = W * 0.68, H * 0.44
        pts = []
        for k in range(140):
            theta = k * 0.085
            r = 4.0 * math.exp(0.155 * (140 - k) * 0.085)
            px = cx - r * math.cos(theta) * 1.25
            py = cy + r * math.sin(theta) * 0.92
            if pad <= px <= W - pad and pad <= py <= H - pad:
                pts.append((px, py))
        if len(pts) > 2:
            draw.line(pts, fill=gold, width=4)
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=cyan, width=3)

    elif rule_id == "frame_in_frame":
        # Three-sided / inner rectangular sub-frame boundary + corner ticks
        ix0, iy0, ix1, iy1 = int(W * 0.17), int(H * 0.14), int(W * 0.83), int(H * 0.86)
        draw.rectangle([ix0, iy0, ix1, iy1], outline=gold, width=4)
        # Shade outer peripheral mask slightly to reveal the sub-frame
        draw.line([(pad, pad), (ix0, iy0)], fill=gold_dim, width=2)
        draw.line([(W - pad, pad), (ix1, iy0)], fill=gold_dim, width=2)
        draw.line([(pad, H - pad), (ix0, iy1)], fill=gold_dim, width=2)
        draw.line([(W - pad, H - pad), (ix1, iy1)], fill=gold_dim, width=2)

    elif rule_id == "s_curve":
        # Smooth S-shaped cubic Bezier curve from bottom-left (0.20, 0.88) to top-right (0.80, 0.14)
        p0 = (W * 0.20, H * 0.88)
        p1 = (W * 0.78, H * 0.72)
        p2 = (W * 0.22, H * 0.28)
        p3 = (W * 0.80, H * 0.12)
        pts = []
        for k in range(81):
            t = k / 80.0
            mt = 1.0 - t
            bx = (mt**3)*p0[0] + 3*(mt**2)*t*p1[0] + 3*mt*(t**2)*p2[0] + (t**3)*p3[0]
            by = (mt**3)*p0[1] + 3*(mt**2)*t*p1[1] + 3*mt*(t**2)*p2[1] + (t**3)*p3[1]
            pts.append((bx, by))
        draw.line(pts, fill=gold, width=4)
        draw.ellipse([p0[0]-6, p0[1]-6, p0[0]+6, p0[1]+6], fill=cyan)
        draw.ellipse([p3[0]-6, p3[1]-6, p3[0]+6, p3[1]+6], fill=cyan)

    elif rule_id == "symmetry":
        # Single vertical center bisector (50/50 split)
        mx = W // 2
        draw.line([(mx, pad), (mx, H - pad)], fill=gold, width=4)
        # Mirror arrows
        for y_arr in [int(H * 0.28), int(H * 0.50), int(H * 0.72)]:
            draw.line([(mx - 42, y_arr), (mx + 42, y_arr)], fill=cyan, width=2)
            draw.ellipse([mx - 5, y_arr - 5, mx + 5, y_arr + 5], fill=gold)

    elif rule_id == "rule_of_thirds":
        # 3x3 grid at 1/3 and 2/3 intervals + 4 power-point intersections
        x1, x2 = int(W / 3.0), int(W * 2.0 / 3.0)
        y1, y2 = int(H / 3.0), int(H * 2.0 / 3.0)
        for x in (x1, x2):
            draw.line([(x, pad), (x, H - pad)], fill=gold, width=3)
        for y in (y1, y2):
            draw.line([(pad, y), (W - pad, y)], fill=gold, width=3)
        for x in (x1, x2):
            for y in (y1, y2):
                draw.ellipse([x - 8, y - 8, x + 8, y + 8], outline=cyan, width=3)

    elif rule_id == "centered":
        # Center channel (two narrow parallel verticals u=0.42, 0.58) + lower horizon baseline v=0.68
        cx1, cx2 = int(W * 0.42), int(W * 0.58)
        hy = int(H * 0.68)
        draw.line([(cx1, pad), (cx1, H - pad)], fill=gold, width=3)
        draw.line([(cx2, pad), (cx2, H - pad)], fill=gold, width=3)
        draw.line([(pad, hy), (W - pad, hy)], fill=gold, width=3)
        draw.ellipse([W // 2 - 7, hy - 7, W // 2 + 7, hy + 7], fill=cyan)

    elif rule_id == "v_shape":
        # Two converging diagonals from upper corners to bottom-center apex (0.50, 0.84)
        apex = (int(W * 0.50), int(H * 0.84))
        tl = (int(W * 0.12), pad)
        tr = (int(W * 0.88), pad)
        draw.line([tl, apex], fill=gold, width=4)
        draw.line([tr, apex], fill=gold, width=4)
        draw.ellipse([apex[0] - 8, apex[1] - 8, apex[0] + 8, apex[1] + 8], fill=cyan)

    elif rule_id == "negative_space":
        # Wide U-shaped upper frame bracket isolating open upper two-thirds
        bx0, by0, bx1, by1 = int(W * 0.08), int(H * 0.10), int(W * 0.92), int(H * 0.64)
        draw.line([(bx0, by1), (bx0, by0), (bx1, by0), (bx1, by1)], fill=gold, width=4)
        draw.line([(pad, by1), (W - pad, by1)], fill=gold_dim, width=2)

    # Top-left HUD badge & bottom source bar (ASCII-safe for default font)
    def clean_ascii(s):
        return (
            s.replace("–", "-")
            .replace("—", " - ")
            .replace("·", "|")
            .replace("×", "x")
            .encode("ascii", "replace")
            .decode("ascii")
        )

    draw.rectangle([pad + 6, pad + 6, W - pad - 6, pad + 30], fill=(10, 12, 18, 195))
    hdr_txt = clean_ascii(f"#{rule_num} {rule_name} [{short_ts}]")
    draw.text((pad + 14, pad + 12), hdr_txt, fill=gold)

    draw.rectangle([pad + 6, H - pad - 28, W - pad - 6, H - pad - 6], fill=(10, 12, 18, 195))
    src_ascii = clean_ascii(source_label)
    draw.text((pad + 14, H - pad - 22), src_ascii[:82], fill=white)

    return Image.alpha_composite(img, overlay).convert("RGB")


def main():
    candidates = harvest_candidate_shots()
    print(f"Harvested {len(candidates)} candidate archival shots across the 4 makers.")

    # Extract 1 midpoint frame per candidate via OpenCV VideoCapture (grouped by mp4_path for speed!)
    by_mp4 = {}
    for idx, c in enumerate(candidates):
        by_mp4.setdefault(c["mp4_path"], []).append((idx, c))

    scored_candidates = []
    for mp4_path, items in by_mp4.items():
        cap = cv2.VideoCapture(mp4_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        for idx, c in items:
            cap.set(cv2.CAP_PROP_POS_MSEC, c["timestamp_s"] * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            sc = score_frame_eight_rules(frame, c["desc"] + " " + c["source_title"])
            c_copy = dict(c)
            c_copy["rule_scores"] = sc
            c_copy["_frame_bgr"] = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
            scored_candidates.append(c_copy)
        cap.release()

    print(f"Successfully decoded & geometrically scored {len(scored_candidates)} archival frames.")

    # Select top 3 distinct shots for each of the 8 rules (avoiding duplicate primary winners)
    used_primary = set()
    rules_output = []
    atlas_cards = []

    for spec in RULES_SPEC:
        rid = spec["id"]
        ranked = sorted(
            scored_candidates,
            key=lambda x: x["rule_scores"].get(rid, 0.0),
            reverse=True,
        )
        picks = []
        seen_films = set()
        for cand in ranked:
            key = (cand["film_id"], round(cand["timestamp_s"]))
            if not picks and key in used_primary:
                continue
            if cand["film_id"] in seen_films and len(picks) < 3:
                continue
            seen_films.add(cand["film_id"])
            if not picks:
                used_primary.add(key)
            picks.append(cand)
            if len(picks) == 3:
                break

        winner = picks[0]
        bgr = winner["_frame_bgr"]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil_clean = Image.fromarray(rgb)

        src_label = f"{winner['film_title']} ({winner['maker']}) | {winner['source_title']} @ {winner['timestamp_s']}s"
        pil_grid = draw_rule_overlay_pil(
            pil_clean, rid, spec["num"], spec["name"], spec["short_ts"], src_label
        )

        clean_rel = f"img/grid_{spec['num']:02d}_{rid}_clean.jpg"
        grid_rel = f"img/grid_{spec['num']:02d}_{rid}_overlay.jpg"
        pil_clean.save(os.path.join(OUT_DIR, clean_rel), quality=88)
        pil_grid.save(os.path.join(OUT_DIR, grid_rel), quality=90)
        atlas_cards.append(pil_grid)

        matches_meta = []
        for rank_i, p in enumerate(picks):
            matches_meta.append({
                "rank": rank_i + 1,
                "maker": p["maker"],
                "film_id": p["film_id"],
                "film_title": p["film_title"],
                "case_url": p["case_url"],
                "video_rel": p["video_rel"],
                "timestamp_s": p["timestamp_s"],
                "start_s": p["start_s"],
                "dur_s": p["dur_s"],
                "source_title": p["source_title"],
                "source_year": p["source_year"],
                "desc": p["desc"][:160],
                "score": p["rule_scores"][rid],
            })

        rules_output.append({
            "num": spec["num"],
            "id": rid,
            "name": spec["name"],
            "short_ts": spec["short_ts"],
            "geometry": spec["geometry"],
            "ref_scene": spec["ref_scene"],
            "clean_img": clean_rel,
            "overlay_img": grid_rel,
            "winner": matches_meta[0],
            "matches": matches_meta,
        })
        print(
            f"Rule #{spec['num']} [{rid:16s}] -> {winner['film_title']} ({winner['maker']}) "
            f"@ {winner['timestamp_s']}s | score={winner['rule_scores'][rid]:.3f} | {winner['desc'][:65]}"
        )

    # Save 8-Rule Contact Atlas Sheet (2 columns x 4 rows)
    W_c, H_c = 640, 360
    sheet = Image.new("RGB", (W_c * 2, H_c * 4), (10, 12, 16))
    for i, card_im in enumerate(atlas_cards):
        c = i % 2
        r = i // 2
        sheet.paste(card_im, (c * W_c, r * H_c))
    sheet_path = os.path.join(IMG_DIR, "eight_grids_atlas.jpg")
    sheet.save(sheet_path, quality=88)
    print(f"Saved 8-Rule Archival Atlas Sheet -> {sheet_path}")

    # Render a 28-second sequential video ('allways-tensor/eight-perspectives.mp4') showing
    # each archival clip for 3.5s: first 1.0s clean, then 2.5s with the glowing gold grid overlay!
    out_mp4 = os.path.join(OUT_DIR, "eight-perspectives.mp4")
    fps_out = 24
    tmp_frames_dir = "/tmp/eight_perspectives_frames"
    os.makedirs(tmp_frames_dir, exist_ok=True)
    f_counter = 0

    for idx_r, r_info in enumerate(rules_output):
        spec = RULES_SPEC[idx_r]
        rid = r_info["id"]
        # Find original winner object to get mp4_path
        win_meta = r_info["winner"]
        cand_match = next(
            c for c in scored_candidates
            if c["film_id"] == win_meta["film_id"] and abs(c["timestamp_s"] - win_meta["timestamp_s"]) < 0.1
        )
        cap = cv2.VideoCapture(cand_match["mp4_path"])
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        start_t = max(0.0, cand_match["timestamp_s"] - 1.5)
        cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)

        n_clip_frames = int(3.5 * fps_out)  # 84 frames per rule (28.0s total for 8 rules)
        last_rgb = cv2.cvtColor(cand_match["_frame_bgr"], cv2.COLOR_BGR2RGB)
        src_label = f"{win_meta['film_title']} ({win_meta['maker']}) | {win_meta['source_title']}"

        for k in range(n_clip_frames):
            ret, frm = cap.read()
            if ret and frm is not None:
                frm_640 = cv2.resize(frm, (640, 360), interpolation=cv2.INTER_AREA)
                last_rgb = cv2.cvtColor(frm_640, cv2.COLOR_BGR2RGB)
            pil_f = Image.fromarray(last_rgb)
            # First 0.8s (19 frames) clean archival footage, then snap on the gold viewfinder overlay!
            if k >= 18:
                pil_f = draw_rule_overlay_pil(
                    pil_f, rid, spec["num"], spec["name"], spec["short_ts"], src_label
                )
            pil_f.save(f"{tmp_frames_dir}/f_{f_counter:05d}.jpg", quality=88)
            f_counter += 1
        cap.release()

    cmd = [
        "ffmpeg", "-y", "-framerate", str(fps_out),
        "-i", f"{tmp_frames_dir}/f_%05d.jpg",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
        out_mp4
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Rendered 8-Rule sequential proof film -> {out_mp4}")

    out_json = os.path.join(OUT_DIR, "eight_grids_archive.json")
    with open(out_json, "w") as f:
        json.dump({"rules": rules_output, "reel_mp4": "eight-perspectives.mp4"}, f, indent=2)
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
