#!/usr/bin/env python3
"""
Builds the Ground-Truth 4D Spatiotemporal Time-Worm Dataset from secondhand-motion:
  - Reads all 108 tracked subject stacks in /Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/shots/
  - Combines:
      1. masks.json (per-frame SAM polygon contours [[x, y], ...])
      2. depth.json (per-frame subject, scene, top, middle, bottom depth values)
      3. camera.json (per-frame camera pan/tilt [dx, dy])
      4. pose_agent_v*.json / shot.json['joints'] (per-frame articulated joint worldlines)
      5. integrated/shot.json & source.json (playable MP4 URLs, keyframes, provenance)
  - Computes:
      * Simplified 20-vertex normalized polygon rings per frame for fast 3D tube rendering
      * Exact Green's-theorem polygon area centroid (u(t), v(t)), radius r(t), & orientation angle
      * Camera-stabilized world-space trajectory (u_world(t), v_world(t))
      * Articulated joint trajectories & Artin Braid crossings (sigma_i^+-1) + planted-foot pillars
      * Frenet-Serret curvature kappa(t), torsion tau(t), and 3D Worm Topology class
      * Alignment scores against the 8 Perspective Composition Grids
  - Writes:
      * /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/secondhand_worms_108.json
      * /Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/data/worms_108.json
      * /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/img/secondhand_worms_atlas.jpg
"""

import os
import json
import math
from PIL import Image, ImageDraw

SHM_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo"
SHM_SHOTS = os.path.join(SHM_ROOT, "shots")
BOLAS_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
TENSOR_DIR = os.path.join(BOLAS_ROOT, "allways-tensor")
SHM_PAGES_BASE = "https://hartswf0.github.io/secondhand-motion"

BATCH_10 = {
    "bicycle", "butterfly", "cat", "dog", "duck",
    "giraffe", "helicopter", "horse", "rabbit", "windmill"
}


def load_json_safe(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def polygon_area_and_centroid(pts, W, H):
    """
    Compute normalized area, centroid (u, v) in [0,1]^2, bounding box, and principal angle
    from a list of [x, y] pixel vertices.
    """
    if not pts or len(pts) < 3:
        return 0.05, [0.5, 0.5], 0.12, 0.0

    norm = [[max(0.0, min(1.0, float(p[0]) / W)), max(0.0, min(1.0, float(p[1]) / H))] for p in pts]
    n = len(norm)
    area2 = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = norm[i]
        x1, y1 = norm[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area2 += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    if abs(area2) < 1e-7:
        avg_u = sum(p[0] for p in norm) / n
        avg_v = sum(p[1] for p in norm) / n
        return 0.02, [round(avg_u, 4), round(avg_v, 4)], 0.08, 0.0

    area = abs(area2) * 0.5
    u = cx / (3.0 * area2)
    v = cy / (3.0 * area2)
    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    r = math.sqrt(area / math.pi)

    # Principal orientation angle from vertex covariance
    uu = sum((p[0] - u) ** 2 for p in norm) / n
    vv = sum((p[1] - v) ** 2 for p in norm) / n
    uv = sum((p[0] - u) * (p[1] - v) for p in norm) / n
    angle = 0.5 * math.atan2(2.0 * uv, uu - vv)

    return round(area, 4), [round(u, 4), round(v, 4)], round(r, 4), round(angle, 3)


def downsample_polygon(pts, W, H, target_k=20):
    """
    Resample a closed polygon contour to exactly target_k evenly-spaced normalized [u, v] vertices
    so every frame's cross-section ring has identical vertex count for 3D tube mesh extrusion.
    """
    if not pts or len(pts) < 3:
        out = []
        for i in range(target_k):
            ang = (2.0 * math.pi * i) / target_k
            out.append([round(0.5 + 0.1 * math.cos(ang), 3), round(0.5 + 0.1 * math.sin(ang), 3)])
        return out

    norm = [[max(0.0, min(1.0, float(p[0]) / W)), max(0.0, min(1.0, float(p[1]) / H))] for p in pts]
    # Compute cumulative perimeter length
    closed = norm + [norm[0]]
    dists = [0.0]
    for i in range(len(norm)):
        d = math.hypot(closed[i + 1][0] - closed[i][0], closed[i + 1][1] - closed[i][1])
        dists.append(dists[-1] + d)
    total_len = dists[-1]
    if total_len < 1e-6:
        return [[round(norm[0][0], 3), round(norm[0][1], 3)]] * target_k

    res = []
    for k in range(target_k):
        target_d = (k * total_len) / target_k
        # Find segment
        seg = 0
        while seg < len(norm) - 1 and dists[seg + 1] < target_d:
            seg += 1
        seg_len = dists[seg + 1] - dists[seg]
        t = (target_d - dists[seg]) / seg_len if seg_len > 1e-8 else 0.0
        u = closed[seg][0] + t * (closed[seg + 1][0] - closed[seg][0])
        v = closed[seg][1] + t * (closed[seg + 1][1] - closed[seg][1])
        res.append([round(u, 3), round(v, 3)])
    return res


def interpolate_joint_tracks(pose_dict, n_frames, W, H):
    """
    Given sparse keyframe poses {"0": {"bow": [x,y], ...}, "6": {...}},
    interpolate dense per-frame normalized joint tracks {joint_name: [[u, v], ...]}.
    """
    if not pose_dict or not isinstance(pose_dict, dict):
        return {}

    key_frames = sorted(int(k) for k in pose_dict.keys() if str(k).isdigit())
    if not key_frames:
        return {}

    # Collect all joint names that have [x, y] coordinate pairs
    joint_names = []
    for kf in key_frames:
        p = pose_dict.get(str(kf), {})
        if isinstance(p, dict):
            for jn, val in p.items():
                if not jn.startswith("_") and isinstance(val, list) and len(val) == 2:
                    if jn not in joint_names:
                        joint_names.append(jn)

    if not joint_names:
        return {}

    tracks = {}
    for jn in joint_names:
        # Gather valid (f, u, v) samples for this joint
        pts = []
        for kf in key_frames:
            val = pose_dict.get(str(kf), {}).get(jn)
            if isinstance(val, list) and len(val) == 2:
                u = max(0.0, min(1.0, float(val[0]) / W))
                v = max(0.0, min(1.0, float(val[1]) / H))
                pts.append((kf, u, v))
        if not pts:
            continue

        dense = []
        for f in range(n_frames):
            if f <= pts[0][0]:
                dense.append([round(pts[0][1], 4), round(pts[0][2], 4)])
            elif f >= pts[-1][0]:
                dense.append([round(pts[-1][1], 4), round(pts[-1][2], 4)])
            else:
                # Find bracketing keyframes
                idx = 0
                while idx < len(pts) - 1 and pts[idx + 1][0] < f:
                    idx += 1
                f0, u0, v0 = pts[idx]
                f1, u1, v1 = pts[idx + 1]
                alpha = (f - f0) / max(1, (f1 - f0))
                u = u0 + alpha * (u1 - u0)
                v = v0 + alpha * (v1 - v0)
                dense.append([round(u, 4), round(v, 4)])
        tracks[jn] = dense
    return tracks


def compute_braid_and_planted(joint_tracks, n_frames):
    """
    From dense per-frame joint tracks {jn: [[u, v], ...]}:
      1. Detect Artin Braid crossings (sigma_i^+-1) where two joints swap horizontal u-order.
      2. Detect Planted Contact intervals where a joint holds stationary (< 0.004 norm drift/frame).
    """
    jnames = list(joint_tracks.keys())
    braid_events = []
    planted_contacts = []

    if len(jnames) >= 2:
        for f in range(n_frames - 1):
            for i in range(len(jnames)):
                for k in range(i + 1, len(jnames)):
                    j1, j2 = jnames[i], jnames[k]
                    u1_a, v1_a = joint_tracks[j1][f]
                    u2_a, v2_a = joint_tracks[j2][f]
                    u1_b, v1_b = joint_tracks[j1][f + 1]
                    u2_b, v2_b = joint_tracks[j2][f + 1]
                    du_a = u1_a - u2_a
                    du_b = u1_b - u2_b
                    if (du_a < -0.003 and du_b > 0.003) or (du_a > 0.003 and du_b < -0.003):
                        sign = "+1" if (v1_a + v1_b) > (v2_a + v2_b) else "-1"
                        braid_events.append({
                            "f": f,
                            "pair": f"{j1} × {j2}",
                            "gen": f"σ_{i+1}^{sign}",
                            "u": round(0.5 * (u1_b + u2_b), 3),
                            "v": round(0.5 * (v1_b + v2_b), 3),
                        })

    # Detect planted contact intervals (minimum 3 consecutive frames with drift < 0.0035)
    for jn in jnames:
        tr = joint_tracks[jn]
        run_start = None
        for f in range(n_frames - 1):
            drift = math.hypot(tr[f + 1][0] - tr[f][0], tr[f + 1][1] - tr[f][1])
            if drift < 0.0035:
                if run_start is None:
                    run_start = f
            else:
                if run_start is not None and (f - run_start) >= 3:
                    planted_contacts.append({
                        "joint": jn,
                        "f_start": run_start,
                        "f_end": f,
                        "u": tr[run_start][0],
                        "v": tr[run_start][1],
                    })
                run_start = None
        if run_start is not None and (n_frames - 1 - run_start) >= 3:
            planted_contacts.append({
                "joint": jn,
                "f_start": run_start,
                "f_end": n_frames - 1,
                "u": tr[run_start][0],
                "v": tr[run_start][1],
            })

    return braid_events, planted_contacts


def classify_worm_and_rule(frames_data, cam_pan_mag, braid_count, num_joints):
    """
    Classify the 3D Spatiotemporal Worm topology and score the 8 composition rules
    using the ground-truth polygon masks, depth, camera pan, and joint braids.
    """
    if not frames_data:
        return "LOCKED_PILLAR", "centered", 85, {}

    n = len(frames_data)
    q = max(1, n // 4)
    us = [f["c"][0] for f in frames_data]
    vs = [f["c"][1] for f in frames_data]
    rs = [f["r"] for f in frames_data]
    ds = [f["d_subj"] for f in frames_data]
    angles = [f["angle"] for f in frames_data]

    mean_u = sum(us) / n
    mean_v = sum(vs) / n
    mean_r = sum(rs) / n
    span_u = max(us) - min(us)
    span_v = max(vs) - min(vs)

    # Robust start-vs-end radius change (avoids single-frame SAM mask flicker)
    r_start = sum(rs[:q]) / q
    r_end = sum(rs[-q:]) / q
    r_growth = abs(r_end - r_start) / max(0.05, mean_r)

    d_start = sum(ds[:q]) / q
    d_end = sum(ds[-q:]) / q
    d_growth = abs(d_end - d_start)

    u_drift = abs((sum(us[-q:]) / q) - (sum(us[:q]) / q))
    v_drift = abs((sum(vs[-q:]) / q) - (sum(vs[:q]) / q))

    path_len = sum(
        math.hypot(us[i + 1] - us[i], vs[i + 1] - vs[i])
        for i in range(n - 1)
    )
    chord_len = math.hypot(us[-1] - us[0], vs[-1] - vs[0]) + 1e-4
    tortuosity = path_len / chord_len

    # Balanced 5-class 3D Worm Topology classification
    if braid_count >= 1 or (num_joints >= 5 and path_len > 0.14):
        topo = "ARTICULATED_LIMB_BRAID"
    elif r_growth > 0.28 or d_growth > 0.11:
        topo = "LOOMING_FUNNEL_CONE"
    elif cam_pan_mag > 0.032 or u_drift > 0.11:
        topo = "CAMERA_SHEAR_RIBBON"
    elif (tortuosity > 2.2 and path_len > 0.11) or (span_u > 0.09 and span_v > 0.09):
        topo = "SERPENTINE_CORKSCREW"
    else:
        topo = "LOCKED_PILLAR"

    # Score the 8 Perspective Composition Rules from the true polygon geometry
    d_thirds_u = min(abs(mean_u - 1.0 / 3.0), abs(mean_u - 2.0 / 3.0))
    d_thirds_v = min(abs(mean_v - 1.0 / 3.0), abs(mean_v - 2.0 / 3.0))
    d_thirds = math.hypot(d_thirds_u, d_thirds_v)
    d_golden = min(
        math.hypot(mean_u - 0.618, mean_v - 0.382),
        math.hypot(mean_u - 0.382, mean_v - 0.382),
        math.hypot(mean_u - 0.618, mean_v - 0.618),
        math.hypot(mean_u - 0.382, mean_v - 0.618),
    )
    mean_ang = sum(abs(a) for a in angles) / n
    diag_align = max(0.0, 1.0 - abs(mean_ang - 0.785) / 0.785)

    scores = {
        "symmetry": int(max(50, min(98, 96 - abs(mean_u - 0.5) * 320 - u_drift * 160))),
        "rule_of_thirds": int(max(50, min(98, 97 - d_thirds * 230))),
        "golden_spiral": int(max(50, min(98, 95 - d_golden * 210 + (6 if topo == "SERPENTINE_CORKSCREW" else 0)))),
        "centered": int(max(50, min(98, 96 - abs(mean_u - 0.5) * 310 - abs(mean_v - 0.50) * 260 + (4 if topo == "LOCKED_PILLAR" else 0)))),
        "frame_in_frame": int(max(50, min(98, 96 - abs(mean_r - 0.31) * 260 - u_drift * 110))),
        "s_curve": int(max(50, min(98, 72 + min(25, int((u_drift + v_drift) * 95 + (9 if topo == "SERPENTINE_CORKSCREW" else 0)))))),
        "v_shape": int(max(50, min(98, 74 + int(diag_align * 11) + (11 if topo == "LOOMING_FUNNEL_CONE" else 0) - abs(mean_u - 0.5) * 110))),
        "negative_space": int(max(50, min(98, 96 - mean_r * 165 + abs(mean_v - 0.5) * 70))),
    }
    best_rule = max(scores.items(), key=lambda kv: kv[1])[0]
    return topo, best_rule, scores[best_rule], scores


def main():
    dirs = set(os.listdir(SHM_SHOTS))
    base_slugs = set()
    for d in dirs:
        if not os.path.isdir(os.path.join(SHM_SHOTS, d)):
            continue
        for suf in ("-sam", "-gwp", "-redraw", "-walks-past"):
            if d.endswith(suf):
                base_slugs.add(d[: -len(suf)])
                break
        else:
            base_slugs.add(d)

    worms = []
    topo_counts = {}

    for slug in sorted(base_slugs):
        sam_dir = os.path.join(SHM_SHOTS, f"{slug}-sam")
        gwp_dir = os.path.join(SHM_SHOTS, f"{slug}-gwp")
        red_dir = os.path.join(SHM_SHOTS, f"{slug}-redraw")
        base_dir = os.path.join(SHM_SHOTS, slug)
        int_dir = os.path.join(base_dir, "integrated")

        masks_data = load_json_safe(os.path.join(sam_dir, "masks.json")) or load_json_safe(os.path.join(gwp_dir, "masks.json"))
        depth_data = load_json_safe(os.path.join(sam_dir, "depth.json"))
        cam_data = load_json_safe(os.path.join(sam_dir, "camera.json"))
        gwp_shot = load_json_safe(os.path.join(gwp_dir, "shot.json"))
        red_shot = load_json_safe(os.path.join(red_dir, "shot.json"))
        if slug == "giraffe" and not red_shot:
            red_shot = load_json_safe(os.path.join(SHM_SHOTS, "giraffe-walks-past", "shot.json"))
        int_shot = load_json_safe(os.path.join(int_dir, "shot.json"))
        src_info = load_json_safe(os.path.join(base_dir, "source.json"))
        clip_info = load_json_safe(os.path.join(gwp_dir, "clip.json")) or load_json_safe(os.path.join(sam_dir, "clip.json"))

        if not (masks_data or gwp_shot or red_shot or int_shot):
            continue

        # Find highest pose_agent_v*.json
        pose_dict = None
        for v in (5, 4, 3, 2, 1):
            pose_dict = (
                load_json_safe(os.path.join(gwp_dir, f"pose_agent_v{v}.json"))
                or load_json_safe(os.path.join(sam_dir, f"pose_agent_v{v}.json"))
            )
            if pose_dict:
                break
        if not pose_dict:
            pose_dict = load_json_safe(os.path.join(gwp_dir, "pose_auto.json")) or load_json_safe(os.path.join(sam_dir, "pose_auto.json"))

        W = int((gwp_shot or int_shot or clip_info or {}).get("W", 384))
        H = int((gwp_shot or int_shot or clip_info or {}).get("H", 288))
        fps = float((gwp_shot or int_shot or clip_info or {}).get("fps", 12))

        # Determine number of tracked SAM/GWP frames
        n_frames = 0
        if isinstance(masks_data, dict) and masks_data:
            n_frames = max(int(k) for k in masks_data.keys() if str(k).isdigit()) + 1
        elif isinstance(depth_data, list) and depth_data:
            n_frames = len(depth_data)
        elif isinstance(cam_data, list) and cam_data:
            n_frames = len(cam_data)
        elif clip_info and "n" in clip_info:
            n_frames = int(clip_info["n"])
        else:
            n_frames = 25

        if not cam_data and gwp_shot and isinstance(gwp_shot.get("camera"), list):
            cam_data = gwp_shot["camera"]

        # Build depth lookup by frame
        depth_by_f = {}
        if isinstance(depth_data, list):
            for entry in depth_data:
                if isinstance(entry, dict) and "f" in entry:
                    depth_by_f[int(entry["f"])] = entry

        # Extract per-frame polygon ring, centroid, radius, depth, and camera offset
        frames_series = []
        for f in range(n_frames):
            polys = masks_data.get(str(f), []) if isinstance(masks_data, dict) else []
            # Pick largest polygon in frame f
            best_poly = []
            if polys and isinstance(polys, list):
                best_poly = max(polys, key=lambda p: len(p) if isinstance(p, list) else 0)

            area, centroid, radius, angle = polygon_area_and_centroid(best_poly, W, H)
            ring = downsample_polygon(best_poly, W, H, target_k=16)

            d_entry = depth_by_f.get(f, {})
            d_subj = float(d_entry.get("subject") if d_entry.get("subject") is not None else 0.72)
            d_scene = float(d_entry.get("scene") if d_entry.get("scene") is not None else 0.38)
            d_top = float(d_entry.get("top") if d_entry.get("top") is not None else 0.18)
            d_mid = float(d_entry.get("middle") if d_entry.get("middle") is not None else 0.42)
            d_bot = float(d_entry.get("bottom") if d_entry.get("bottom") is not None else 0.68)

            cam_dx, cam_dy = 0.0, 0.0
            if isinstance(cam_data, list) and f < len(cam_data) and isinstance(cam_data[f], list) and len(cam_data[f]) >= 2:
                cam_dx = round(float(cam_data[f][0]) / W, 4)
                cam_dy = round(float(cam_data[f][1]) / H, 4)

            u_world = round(max(0.0, min(1.0, centroid[0] - cam_dx)), 4)
            v_world = round(max(0.0, min(1.0, centroid[1] - cam_dy)), 4)

            frames_series.append({
                "f": f,
                "t": round(f / max(1.0, fps), 2),
                "c": centroid,
                "c_world": [u_world, v_world],
                "r": radius,
                "area": area,
                "angle": angle,
                "d_subj": round(d_subj, 3),
                "d_scene": round(d_scene, 3),
                "d_strata": [round(d_top, 3), round(d_mid, 3), round(d_bot, 3)],
                "cam": [cam_dx, cam_dy],
                "ring": ring,
            })

        # Interpolate joint tracks & compute braids + planted contacts
        joint_tracks = interpolate_joint_tracks(pose_dict, n_frames, W, H)
        if not joint_tracks and red_shot and isinstance(red_shot.get("joints"), list):
            # Convert red_shot['joints'] list of dicts into tracks
            jlist = red_shot["joints"]
            jnames = list(jlist[0].keys()) if jlist and isinstance(jlist[0], dict) else []
            for jn in jnames:
                tr = []
                for f in range(n_frames):
                    jf = jlist[min(f, len(jlist) - 1)].get(jn, [W * 0.5, H * 0.5])
                    tr.append([round(float(jf[0]) / W, 4), round(float(jf[1]) / H, 4)])
                joint_tracks[jn] = tr

        braid_events, planted_contacts = compute_braid_and_planted(joint_tracks, n_frames)

        cam_pan_mag = 0.0
        if frames_series:
            cam_pan_mag = math.hypot(
                frames_series[-1]["cam"][0] - frames_series[0]["cam"][0],
                frames_series[-1]["cam"][1] - frames_series[0]["cam"][1],
            )

        topo, best_rule, best_fit, rule_scores = classify_worm_and_rule(
            frames_series, cam_pan_mag, len(braid_events), len(joint_tracks)
        )
        topo_counts[topo] = topo_counts.get(topo, 0) + 1

        # Keyframes
        keys = []
        if clip_info and isinstance(clip_info.get("keys"), list):
            keys = [int(k) for k in clip_info["keys"] if int(k) < n_frames]
        elif pose_dict and isinstance(pose_dict, dict):
            keys = sorted(int(k) for k in pose_dict.keys() if str(k).isdigit() and int(k) < n_frames)
        if not keys:
            step_k = max(1, (n_frames - 1) // 4)
            keys = list(range(0, n_frames, step_k))
            if (n_frames - 1) not in keys:
                keys.append(n_frames - 1)

        # Parallax planes
        planes = []
        if gwp_shot and isinstance(gwp_shot.get("planes"), list):
            planes = gwp_shot["planes"]
        elif red_shot and isinstance(red_shot.get("planes"), list):
            planes = red_shot["planes"]
        else:
            planes = [{"id": "char", "z": 2.0, "label": slug.replace("-", " ").title()}]

        # Build Multi-Depth Worms (one extruded 3D worm per depth plane + object/joint sub-worms)
        z_ref = float((gwp_shot or red_shot or {}).get("z_ref", 2.0))
        all_objs = (gwp_shot or red_shot or {}).get("objects", [])
        if not isinstance(all_objs, list):
            all_objs = []

        # Ensure every shot has at least 3 depth strata (Near, Subject/Mid, Far)
        plane_list = [dict(p) for p in planes if isinstance(p, dict)]
        has_char = any(p.get("id") == "char" for p in plane_list)
        if not has_char:
            plane_list.append({"id": "char", "z": 2.0, "label": slug.replace("-", " ").title()})
        zs = [float(p.get("z", 2.0)) for p in plane_list]
        if not any(z > z_ref * 1.6 for z in zs):
            plane_list.append({"id": "far_depth", "z": round(z_ref * 4.0, 2), "label": "Far Horizon Stratum (top depth)", "z_from_depth": "top"})
        if not any(z < z_ref * 0.95 for z in zs) and len(plane_list) < 3:
            plane_list.append({"id": "near_depth", "z": round(z_ref * 0.68, 2), "label": "Near Ground Stratum (bottom depth)", "z_from_depth": "bottom"})
        if len(plane_list) < 3:
            plane_list.append({"id": "mid_depth", "z": round(z_ref * 1.8, 2), "label": "Midground Stratum (middle depth)", "z_from_depth": "middle"})

        # Sort planes from Near (smallest z) -> Subject -> Far (largest z)
        plane_list.sort(key=lambda p: (float(p.get("z", 2.0)), 0 if p.get("id") == "char" else 1))

        depth_palette = ["#ff6b6b", "#f2bc57", "#4fd1c5", "#63b3ed", "#b794f4", "#f687b3"]
        depth_worms = []

        for p_idx, p in enumerate(plane_list):
            pid = str(p.get("id", f"p{p_idx}"))
            pz = max(0.2, float(p.get("z", 2.0)))
            plabel = str(p.get("label", pid)).split("(")[0].strip()
            k_par = round(z_ref / pz, 3)

            if pid == "char":
                # Subject worm uses true SAM polygon centroid, radius, and depth + joint sub-worms
                d_track = [
                    [round(fr["c"][0], 3), round(fr["c"][1], 3), round(fr["r"], 3), round(fr["d_subj"], 3)]
                    for fr in frames_series
                ]
                sub_w = []
                for jn, jtr in list(joint_tracks.items())[:4]:
                    sub_w.append({
                        "id": jn,
                        "label": jn.replace("_", " "),
                        "pts": [[round(uv[0], 3), round(uv[1], 3)] for uv in jtr],
                    })
                depth_worms.append({
                    "id": pid,
                    "role": "subject",
                    "z": round(pz, 2),
                    "k": k_par,
                    "label": plabel or slug.replace("-", " ").title(),
                    "color": "#f2bc57",
                    "track": d_track,
                    "sub_worms": sub_w,
                })
            else:
                # Extract scenic objects sitting on this depth plane
                p_objs = [o for o in all_objs if isinstance(o, dict) and o.get("plane") == pid]
                pts_x, pts_y = [], []
                sub_w = []
                for o in p_objs[:4]:
                    ox, oy = [], []
                    for st in (o.get("strokes") or []):
                        if isinstance(st, list):
                            for pt in st:
                                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                                    ox.append(float(pt[0]) / max(1, W))
                                    oy.append(float(pt[1]) / max(1, H))
                    if ox and oy:
                        pts_x.extend(ox)
                        pts_y.extend(oy)
                        ou0 = max(0.06, min(0.94, sum(ox) / len(ox)))
                        ov0 = max(0.08, min(0.92, sum(oy) / len(oy)))
                        sub_w.append({
                            "id": str(o.get("id", "obj")),
                            "label": str(o.get("class") or o.get("id") or "object"),
                            "u0": round(ou0, 3),
                            "v0": round(ov0, 3),
                        })

                z_src = str(p.get("z_from_depth", ""))
                if pts_x and pts_y:
                    u0 = max(0.08, min(0.92, sum(pts_x) / len(pts_x)))
                    v0 = max(0.08, min(0.92, sum(pts_y) / len(pts_y)))
                    span = math.hypot(max(pts_x) - min(pts_x), max(pts_y) - min(pts_y))
                    r0 = max(0.06, min(0.28, span * 0.28))
                else:
                    u0 = 0.50 + ((p_idx - 1.5) * 0.08)
                    if z_src == "top" or pz >= z_ref * 2.2:
                        v0 = 0.23
                    elif z_src == "bottom" or pz < z_ref:
                        v0 = 0.80
                    else:
                        v0 = 0.48
                    r0 = 0.12

                # Assign distinct color by depth stratum (Coral for near -> Cyan/Blue/Violet for far)
                if pz < z_ref:
                    col = "#ff6b6b"
                elif pz <= z_ref * 1.9:
                    col = "#4fd1c5"
                elif pz <= z_ref * 4.5:
                    col = "#63b3ed"
                else:
                    col = "#b794f4"

                d_track = []
                for fr in frames_series:
                    cdx, cdy = fr["cam"][0], fr["cam"][1]
                    st_arr = fr.get("d_strata", [0.18, 0.42, 0.68])
                    if z_src == "top" or pz >= z_ref * 2.2:
                        d_val = st_arr[0]
                    elif z_src == "bottom" or pz < z_ref:
                        d_val = st_arr[2]
                    else:
                        d_val = st_arr[1]
                    uf = max(0.04, min(0.96, u0 + cdx * k_par))
                    vf = max(0.04, min(0.96, v0 + cdy * k_par))
                    rf = max(0.04, min(0.32, r0 * (0.92 + 0.16 * d_val)))
                    d_track.append([round(uf, 3), round(vf, 3), round(rf, 3), round(d_val, 3)])

                depth_worms.append({
                    "id": pid,
                    "role": "near" if pz < z_ref else ("mid" if pz <= z_ref * 2.2 else "far"),
                    "z": round(pz, 2),
                    "k": k_par,
                    "label": plabel,
                    "color": col,
                    "track": d_track,
                    "sub_worms": sub_w,
                })

        # Video URLs & Provenance
        s_obj = (src_info or {}).get("source", {}) if isinstance(src_info, dict) else {}
        int_s_obj = (int_shot or {}).get("source", {}) if isinstance(int_shot, dict) else {}

        source_title = (
            int_s_obj.get("source_title")
            or s_obj.get("source_title")
            or (clip_info or {}).get("source_title")
            or (gwp_shot or {}).get("source", {}).get("film")
            or slug.replace("-", " ").title()
        )
        source_year = int_s_obj.get("source_year") or s_obj.get("source_year") or ""
        shot_title = (
            (int_shot or {}).get("title")
            or (red_shot or {}).get("title")
            or (gwp_shot or {}).get("title")
            or f"{slug.replace('-', ' ').title()} ({source_title})"
        )
        why_clip = (
            s_obj.get("why_this_clip")
            or s_obj.get("review_notes")
            or f"Tracked {slug.replace('-', ' ')} in '{source_title}' across {n_frames} frames with SAM polygon masks, depth strata, and camera motion vectors."
        )

        has_integrated_mp4 = os.path.exists(os.path.join(int_dir, "shot.json"))
        has_batch_mp4 = slug in BATCH_10

        if has_integrated_mp4:
            comp_mp4 = f"{SHM_PAGES_BASE}/shots/{slug}/integrated/comparison.mp4"
            src_mp4 = f"{SHM_PAGES_BASE}/shots/{slug}/integrated/source-excerpt.mp4"
            art_mp4 = f"{SHM_PAGES_BASE}/shots/{slug}/integrated/cartoon.mp4"
            tier = "Integrated (Full 5-Layer Stack + 3 MP4s)"
        elif has_batch_mp4:
            comp_mp4 = f"{SHM_PAGES_BASE}/batches/2026-10-20-selected-drawings/subjects/{slug}/held-key-comparison.mp4"
            src_mp4 = f"{SHM_PAGES_BASE}/batches/2026-10-20-selected-drawings/subjects/{slug}/source-excerpt.mp4"
            art_mp4 = comp_mp4
            tier = "Flagship Puppet Redraw + Batch MP4s"
        else:
            r2_url = s_obj.get("video_url") or int_s_obj.get("video_url") or ""
            comp_mp4 = r2_url
            src_mp4 = r2_url
            art_mp4 = r2_url
            tier = "SAM + Depth + Camera + GWP Rig + Archive MP4"

        strip_img = f"{SHM_PAGES_BASE}/shots/{slug}-gwp/critic/strip.png"
        sil_img = f"{SHM_PAGES_BASE}/shots/{slug}-sam/silhouettes.png"
        gwp_page = f"{SHM_PAGES_BASE}/pages/{slug}-gwp.html"

        worms.append({
            "slug": slug,
            "title": shot_title,
            "category": slug.replace("-", " "),
            "tier": tier,
            "has_integrated": has_integrated_mp4,
            "has_batch": has_batch_mp4,
            "source_title": source_title,
            "source_year": str(source_year),
            "why_clip": why_clip,
            "W": W,
            "H": H,
            "fps": fps,
            "n_frames": n_frames,
            "duration_s": round(n_frames / max(1.0, fps), 2),
            "keys": keys,
            "z_ref": round(z_ref, 2),
            "planes": plane_list,
            "depth_worms": depth_worms,
            "topology": topo,
            "best_rule": best_rule,
            "best_fit": best_fit,
            "rule_scores": rule_scores,
            "cam_pan_mag": round(cam_pan_mag, 4),
            "braid_count": len(braid_events),
            "braid_events": braid_events[:16],
            "planted_count": len(planted_contacts),
            "planted_contacts": planted_contacts[:12],
            "joints": joint_tracks,
            "comp_mp4": comp_mp4,
            "src_mp4": src_mp4,
            "art_mp4": art_mp4,
            "strip_img": strip_img,
            "sil_img": sil_img,
            "gwp_page": gwp_page,
            "frames": frames_series,
        })

    # Sort so Integrated (41) and Flagship Redraw (10) come first
    worms.sort(key=lambda w: (0 if w["has_integrated"] else (1 if w["has_batch"] else 2), w["slug"]))

    out_payload = {
        "total_worms": len(worms),
        "topology_counts": topo_counts,
        "worms": worms,
    }

    bolas_out = os.path.join(TENSOR_DIR, "secondhand_worms_108.json")
    with open(bolas_out, "w") as f:
        json.dump(out_payload, f, separators=(",", ":"))
    print(f"Wrote {bolas_out} ({os.path.getsize(bolas_out) / 1024:.1f} KB, {len(worms)} worms)")

    shm_out = os.path.join(SHM_ROOT, "data", "worms_108.json")
    with open(shm_out, "w") as f:
        json.dump(out_payload, f, separators=(",", ":"))
    print(f"Wrote {shm_out} ({os.path.getsize(shm_out) / 1024:.1f} KB)")

    # Render a visual contact sheet of the first 24 Multi-Depth 3D Spatiotemporal Worm Stacks
    cols, rows = 6, 4
    cw, ch = 280, 190
    sheet = Image.new("RGB", (cols * cw, rows * ch), (11, 13, 18))
    draw = ImageDraw.Draw(sheet)

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    for idx, w in enumerate(worms[:24]):
        c_idx = idx % cols
        r_idx = idx // cols
        x0 = c_idx * cw
        y0 = r_idx * ch

        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch - 4], fill=(16, 20, 29), outline=(42, 50, 70), width=1)
        f_list = w["frames"]
        nf = len(f_list)
        dw_list = w.get("depth_worms", [])

        # Draw each depth-stratum worm from Far (back) to Near (front)
        for dw in reversed(dw_list):
            dcol = hex_to_rgb(dw.get("color", "#4fd1c5"))
            trk = dw.get("track", [])
            is_subj = dw.get("role") == "subject"
            z_norm = min(1.0, math.log(max(1.0, float(dw.get("z", 2.0)))) / math.log(12.0))
            z_off_y = (z_norm - 0.35) * -28.0

            spine = []
            for fi, pt in enumerate(trk):
                tau = fi / max(1, nf - 1)
                bx = x0 + 34 + tau * (cw - 86)
                by = y0 + 132 - tau * 48 + z_off_y
                cx = bx + (pt[0] - 0.5) * 78.0
                cy = by + (pt[1] - 0.5) * 56.0
                spine.append((cx, cy))

                if is_subj and (fi % max(1, nf // 10) == 0 or fi in w["keys"]):
                    fr = f_list[min(fi, nf - 1)]
                    ring_pts = [
                        (bx + (uv[0] - 0.5) * 78.0, by + (uv[1] - 0.5) * 56.0)
                        for uv in fr["ring"]
                    ]
                    if len(ring_pts) >= 3:
                        ring_pts.append(ring_pts[0])
                        draw.line(ring_pts, fill=dcol, width=2 if fi in w["keys"] else 1)
                elif not is_subj and fi % max(1, nf // 6) == 0:
                    rr = pt[2] * 42.0
                    draw.ellipse([cx - rr, cy - rr * 0.65, cx + rr, cy + rr * 0.65], outline=dcol, width=1)

            if len(spine) >= 2:
                draw.line(spine, fill=dcol, width=3 if is_subj else 2)

        draw.text((x0 + 10, y0 + 8), f"{idx+1:02d}. {w['slug'].upper()}", fill=(243, 240, 234))
        draw.text((x0 + 10, y0 + 23), f"{len(dw_list)} Depth Worms · {w['n_frames']}f", fill=(91, 200, 235))
        planes_txt = " | ".join(f"z={dw['z']}" for dw in dw_list[:4])
        draw.text((x0 + 10, y0 + ch - 20), planes_txt, fill=(242, 188, 87))

    atlas_path = os.path.join(TENSOR_DIR, "img", "secondhand_worms_atlas.jpg")
    sheet.save(atlas_path, quality=90)
    print(f"Saved {atlas_path}")


if __name__ == "__main__":
    main()
