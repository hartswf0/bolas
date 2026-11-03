#!/usr/bin/env python3
"""
Builds the Zero-Lag, Deterministic Geometric Cinema Studio at:
  /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html

Fixes all lag and randomness:
  1. ZERO LAG:
     - No requestAnimationFrame loop, no offscreen canvas getImageData() GPU-to-CPU stalls,
       and no 60fps DOM innerHTML mutations.
     - No inline base64 image bloat (uses external img/*.jpg with loading="lazy"),
       dropping index.html from 2.7 MB to ~140 KB.
  2. ZERO RANDOMNESS:
     - No noisy 0.5-second shape jumping or jittering dots on top of pre-annotated videos.
     - Every film is segmented into deterministic, human-legible Cuts / Chapters / Parts:
       * 8 SCION Shape Films (SCION 114–121, 24s): 8 exact 3.0s Cuts across the 4 Phases
         (Phase I: Raw Observation, Phase II: Viewfinder Lock, Phase III: Rupture/Break,
         Phase IV: Unannotated Return).
       * 8-Rule Perspective Reel (eight-perspectives.mp4, 28s): 8 exact 3.5s Rule Chapters
         (#1 Golden Spiral through #8 Negative Space).
       * All 133 Other ALLWAYS Films: 4 Structural Parts (Part 1 Opening -> Part 4 Resolution)
         with one stable dominant geometric guide and camera movement per Part.
"""

import os
import json
import math

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
TENSOR_DIR = os.path.join(REPO_ROOT, "allways-tensor")


RULE_META = {
    "golden_spiral": {
        "num": 1,
        "name": "Golden Spiral (1:1.618)",
        "short": "1 · Golden Spiral",
        "what_to_look_for": "Outer curving foliage, shadow, or arm sweeps across the 1:1.618 Golden Rectangles into the upper-right focal eye at (0.68, 0.44).",
    },
    "frame_in_frame": {
        "num": 2,
        "name": "Frame in a Frame",
        "short": "2 · Frame in Frame",
        "what_to_look_for": "A physical doorway, window, arch, or mirror border encloses the inner rectangular threshold [0.16..0.84, 0.14..0.88].",
    },
    "s_curve": {
        "num": 3,
        "name": "S-Curve (Leading Curve)",
        "short": "3 · S-Curve",
        "what_to_look_for": "A winding path, river delta, or rail track curves from the bottom-left foreground through the center inflection into the upper-right background.",
    },
    "symmetry": {
        "num": 4,
        "name": "Symmetry (50/50 Split)",
        "short": "4 · Symmetry",
        "what_to_look_for": "The vertical center line (u = 0.50) splits twin architectural halves, doorways, or frontal faces into mirror-image balance.",
    },
    "rule_of_thirds": {
        "num": 5,
        "name": "Rule of Thirds (3×3 Grid)",
        "short": "5 · Rule of Thirds",
        "what_to_look_for": "Horizon lines lock to the 1/3 or 2/3 horizontal lines while primary subjects anchor on the four 1/3 power-point intersections.",
    },
    "centered": {
        "num": 6,
        "name": "Centered (Corridor + Horizon)",
        "short": "6 · Centered",
        "what_to_look_for": "Two vertical center corridor rails (u = 0.43, 0.57) and a lower third baseline (v = 0.67) lock a lone subject dead-center.",
    },
    "v_shape": {
        "num": 7,
        "name": "V-Shape (Converging Wedge)",
        "short": "7 · V-Shape",
        "what_to_look_for": "Two upper diagonal sightlines or architectural rafters converge downward into a single bottom-center apex at (0.50, 0.88).",
    },
    "negative_space": {
        "num": 8,
        "name": "Negative Space (Upper Sky)",
        "short": "8 · Negative Space",
        "what_to_look_for": "Open sky, mist, or wall occupies the upper two-thirds above v = 0.62 while the silhouette or subject is compressed along the lower ground band.",
    },
}

TOPO_PLAIN = {
    "VERTICAL_PILLAR": "Locked Tripod (Subject holds steady inside a vertical column)",
    "SHEARED_DIAGONAL_RIBBON": "Lateral Pan / Track (Subject sweeps horizontally across the frame)",
    "EXPANDING_CONE": "Approaching Zoom / Dolly (Subject expands or recedes in depth)",
    "HELICAL_CORKSCREW": "Curved / Spiral Motion (Subject curves across both X and Y axes)",
    "DOUBLE_HELIX_BRAID": "Two-Shot Counterbalance (Left and right subjects balance each other)",
}


def pick_part_shape(part, series_slice_list):
    """
    Deterministically select ONE stable geometric rule and fit % for a film Part
    so the guide never flickers randomly inside a shot.
    """
    t0 = part.get("t_start", 0.0)
    t1 = part.get("t_end", 999.0)
    sub = [s for s in series_slice_list if t0 - 0.5 <= s.get("t", 0.0) <= t1 + 0.5]
    if not sub:
        sub = series_slice_list[:4] if series_slice_list else []

    if not sub:
        return "rule_of_thirds", 85

    avg_u = sum(s["c"][0] for s in sub) / len(sub)
    avg_v = sum(s["c"][1] for s in sub) / len(sub)
    avg_r = sum(s["r"] for s in sub) / len(sub)
    avg_lr = sum(s.get("lr_balance", 0.8) for s in sub) / len(sub)
    avg_th = sum(s.get("d_thirds", 0.09) for s in sub) / len(sub)
    avg_gold = sum(s.get("d_golden", 0.16) for s in sub) / len(sub)
    avg_arm = sum(s.get("d_armature", 0.02) for s in sub) / len(sub)
    avg_area = sum(s.get("area_ratio", 0.28) for s in sub) / len(sub)
    topo = part.get("topology", "VERTICAL_PILLAR")

    scores = {
        "symmetry": int(max(55, min(98, avg_lr * 100 - abs(avg_u - 0.5) * 120))),
        "rule_of_thirds": int(max(55, min(97, 100 - avg_th * 420))),
        "golden_spiral": int(max(55, min(96, 100 - avg_gold * 260 + (6 if topo == "HELICAL_CORKSCREW" else 0)))),
        "centered": int(max(55, min(97, 96 - abs(avg_u - 0.5) * 210 - abs(avg_v - 0.56) * 110))),
        "frame_in_frame": int(max(55, min(95, 92 - abs(avg_r - 0.31) * 220 - avg_arm * 220))),
        "s_curve": int(max(55, min(95, (89 if topo in ("HELICAL_CORKSCREW", "SHEARED_DIAGONAL_RIBBON") else 74) - avg_arm * 160))),
        "v_shape": int(max(55, min(94, (88 if topo == "EXPANDING_CONE" else 75) - abs(avg_u - 0.5) * 150))),
        "negative_space": int(max(55, min(96, 92 - abs(avg_area - 0.24) * 180 + (avg_v - 0.5) * 80))),
    }
    best_id = max(scores.items(), key=lambda kv: kv[1])[0]
    return best_id, scores[best_id]


def build_phase_how_to_test(phase_str, rule_id, cut_num, score_pct):
    rm = RULE_META.get(rule_id, RULE_META["golden_spiral"])
    if "I ·" in phase_str:
        return (
            f"PHASE I (RAW OBSERVATION — NO GRID OVERLAY YET): Watch the unannotated archival shot first. "
            f"{rm['what_to_look_for']} Toggle 'Force Guide On' above if you want to check the gold overlay early."
        )
    if "II ·" in phase_str:
        return (
            f"PHASE II (VIEWFINDER LOCK — GOLD GRID SNAPS ON AT +0.6s): "
            f"0.6 seconds into this cut, the gold {rm['name']} viewfinder locks directly onto the video frame "
            f"({score_pct}% geometric fit). Verify how the real physical edges align with the gold lines."
        )
    if "III ·" in phase_str:
        return (
            f"PHASE III (DELIBERATE RUPTURE / BREAK — {score_pct}% FIT): "
            f"This cut tests what happens when a shot breaks out of {rm['name']}—notice the directional exit "
            f"and the sudden drop in the audio pulse."
        )
    return (
        f"PHASE IV (UNANNOTATED RETURN — {score_pct}% FIT): "
        f"We return to the #1 archival exemplar from Cut 4 and dissolve the gold viewfinder away so your eye "
        f"holds the {rm['name']} structure in the raw cinema frame."
    )


def main():
    grids_path = os.path.join(TENSOR_DIR, "eight_grids_archive.json")
    scion_shapes_path = os.path.join(TENSOR_DIR, "scion_shapes.json")
    worms_140_path = os.path.join(TENSOR_DIR, "allways_worms_140.json")

    with open(grids_path) as f:
        grids_data = json.load(f)
    with open(scion_shapes_path) as f:
        scion_shapes_data = json.load(f)
    with open(worms_140_path) as f:
        worms_140_data = json.load(f)

    shape_ops_by_id = {}
    for op in scion_shapes_data.get("operators", []):
        shape_ops_by_id[f"shape-{op['scion_id']}"] = op

    rules_list = grids_data.get("rules", [])

    # Build deterministic, lightweight film objects with steps[] (8 Cuts or 4 Parts)
    films_catalog = []
    for wf in worms_140_data.get("films", []):
        fid = wf["id"]
        dur = float(wf.get("duration_s", 24.0))
        op_info = shape_ops_by_id.get(fid)
        raw_ser = wf.get("series", [])

        # Sample up to 12 color pairs for a tiny, zero-bloat color timeline bar
        color_bar = []
        if raw_ser:
            step_n = max(1, len(raw_ser) // 12)
            for s in raw_ser[::step_n][:12]:
                color_bar.append([s.get("rgb_core", [80, 80, 80]), s.get("rgb_shell", [30, 30, 30])])

        steps = []
        has_burned_in_grid = False
        pinned_rule = None
        theorem = ""

        if op_info:
            # One of the 8 SCION Shape Films (shape-114 .. shape-121) -> 8 exact 3.0s cuts
            has_burned_in_grid = True
            pinned_rule = op_info["rule_id"]
            theorem = op_info["theorem"]
            for c in op_info.get("cuts", []):
                cnum = int(c["cut_num"])
                t_start = round((cnum - 1) * 3.0, 1)
                t_end = round(cnum * 3.0, 1)
                sc_pct = int(round(float(c.get("score", 0.75)) * 100))
                yr = f" ({c['source_year']})" if c.get("source_year") else ""
                steps.append({
                    "num": cnum,
                    "label": f"Cut {cnum}",
                    "phase": c["phase"],
                    "t_start": t_start,
                    "t_end": t_end,
                    "rule_id": pinned_rule,
                    "fit_pct": sc_pct,
                    "source": f"{c['source_title']}{yr}",
                    "from_film": f"{c['film_title']} ({c['maker']})",
                    "what_happens": c["desc"],
                    "how_to_test": build_phase_how_to_test(c["phase"], pinned_rule, cnum, sc_pct),
                })

        elif fid == "shape-eight-reel":
            # The 28.0s 8-Perspective Grids Reel -> 8 exact 3.5s chapters (1 per rule)
            has_burned_in_grid = True
            pinned_rule = "golden_spiral"
            theorem = (
                "Sequential 28-second breakdown of all 8 composition rules from @gfxmotionbyahmar "
                "('Life Is All About Perspective! #shorts'). Each 3.5-second chapter plays 0.8s unannotated "
                "followed by 2.7s with the gold viewfinder locked onto the #1 ALLWAYS archival match."
            )
            for idx, r in enumerate(rules_list):
                cnum = idx + 1
                t_start = round(idx * 3.5, 1)
                t_end = round((idx + 1) * 3.5, 1)
                w = r["winner"]
                sc_pct = int(round(float(w.get("score", 0.8)) * 100))
                yr = f" ({w['source_year']})" if w.get("source_year") else ""
                rm = RULE_META.get(r["id"], RULE_META["golden_spiral"])
                steps.append({
                    "num": cnum,
                    "label": f"Rule #{cnum}",
                    "phase": f"Rule #{cnum} · {rm['short']}",
                    "t_start": t_start,
                    "t_end": t_end,
                    "rule_id": r["id"],
                    "fit_pct": sc_pct,
                    "source": f"{w['source_title']}{yr}",
                    "from_film": f"{w['film_title']} ({w['maker']})",
                    "what_happens": w["desc"],
                    "how_to_test": (
                        f"First 0.8s ({t_start:.1f}s–{t_start+0.8:.1f}s) is raw archival footage; "
                        f"at {t_start+0.8:.1f}s the gold {r['name']} guide locks on ({sc_pct}% fit). "
                        f"{rm['what_to_look_for']}"
                    ),
                })

        else:
            # Standard ALLWAYS film -> 4 deterministic Structural Parts
            has_burned_in_grid = False
            parts = wf.get("manovich_parts", [])
            part_names = ["Part 1 · Opening", "Part 2 · Development", "Part 3 · Turn", "Part 4 · Resolution"]
            for idx, p in enumerate(parts):
                pnum = idx + 1
                t_start = round(float(p.get("t_start", (idx * dur) / 4.0)), 1)
                t_end = round(float(p.get("t_end", ((idx + 1) * dur) / 4.0)), 1)
                if idx == len(parts) - 1 and t_end < dur:
                    t_end = round(dur, 1)
                rule_id, fit_pct = pick_part_shape(p, raw_ser)
                rm = RULE_META.get(rule_id, RULE_META["rule_of_thirds"])
                topo_code = p.get("topology", wf.get("dominant_topology", "VERTICAL_PILLAR"))
                topo_desc = TOPO_PLAIN.get(topo_code, topo_code)
                ec = p.get("entry_c", [0.5, 0.5])
                xc = p.get("exit_c", [0.5, 0.5])
                dx = xc[0] - ec[0]
                dy = xc[1] - ec[1]
                shift_str = (
                    f"Subject center holds steady near ({ec[0]:.2f}, {ec[1]:.2f})"
                    if math.hypot(dx, dy) < 0.04
                    else f"Subject center shifts from ({ec[0]:.2f}, {ec[1]:.2f}) to ({xc[0]:.2f}, {xc[1]:.2f})"
                )
                steps.append({
                    "num": pnum,
                    "label": f"Part {pnum}",
                    "phase": part_names[idx] if idx < 4 else f"Part {pnum}",
                    "t_start": t_start,
                    "t_end": t_end,
                    "rule_id": rule_id,
                    "fit_pct": fit_pct,
                    "source": topo_desc,
                    "from_film": f"{wf['title']} ({wf['maker']})",
                    "what_happens": (
                        f"{shift_str} · Contrast: {p.get('chiaroscuro', 18.0):.1f} · "
                        f"Subject area: {int(round(p.get('area_ratio', 0.3)*100))}% of frame."
                    ),
                    "how_to_test": (
                        f"Dominant geometry in Part {pnum}: {rm['name']} ({fit_pct}% alignment). "
                        f"{rm['what_to_look_for']}"
                    ),
                })

            if steps:
                pinned_rule = steps[0]["rule_id"]
            theorem = (
                f"4-Part Breakdown of '{wf['title']}' ({wf['maker']}): "
                f"{TOPO_PLAIN.get(wf.get('dominant_topology',''), wf.get('dominant_topology',''))} "
                f"({wf.get('compositional_lock_pct', 82.0):.1f}% geometric lock)."
            )

        films_catalog.append({
            "id": fid,
            "title": wf["title"],
            "maker": wf["maker"],
            "group": wf["group"],
            "video_rel": wf["video_rel"],
            "case_url": wf["case_url"],
            "duration_s": dur,
            "dominant_topology": wf.get("dominant_topology", "VERTICAL_PILLAR"),
            "lock_pct": wf.get("compositional_lock_pct", 82.0),
            "has_burned_in_grid": has_burned_in_grid,
            "pinned_rule": pinned_rule or "golden_spiral",
            "theorem": theorem,
            "steps": steps,
        })

    # Reorder so shape-114..121 and shape-eight-reel and allways-best are easy to find
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLWAYS — Shot-by-Shot Geometric Cinema Studio</title>
<style>
  :root {{
    --bg: #0b0d12;
    --panel: #131722;
    --panel-alt: #191e2c;
    --border: #283044;
    --fg: #f3f0ea;
    --muted: #9aa3b5;
    --gold: #f2bc57;
    --cyan: #5bc8eb;
    --green: #68d391;
    --rose: #f56565;
    --mono: "SFMono-Regular", ui-monospace, Consolas, monospace;
  }}
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  html, body {{
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.45;
  }}
  a {{ color: var(--gold); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Top Bar */
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 16px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .brand {{
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.03em;
  }}
  .brand span {{ color: var(--gold); }}
  .nav-links {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .nav-links a {{
    font-size: 12px;
    color: var(--muted);
    padding: 4px 9px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--panel-alt);
  }}
  .nav-links a:hover {{ color: var(--fg); border-color: var(--gold); text-decoration: none; }}

  .container {{
    max-width: 1180px;
    margin: 0 auto;
    padding: 12px;
  }}

  /* Quick Film Switcher Pills */
  .quick-film-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 8px;
    margin-bottom: 8px;
    scrollbar-width: thin;
  }}
  .quick-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--muted);
    white-space: nowrap;
    margin-right: 2px;
  }}
  .qf-btn {{
    background: var(--panel);
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }}
  .qf-btn:hover {{ color: var(--fg); border-color: #44506e; }}
  .qf-btn.active {{
    background: rgba(242, 188, 87, 0.16);
    color: var(--gold);
    border-color: var(--gold);
  }}

  /* Studio Card */
  .player-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 16px;
  }}

  /* Film Selector & Guide Toolbar */
  .player-toolbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 10px 12px;
    background: var(--panel-alt);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .film-select-group {{
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 240px;
  }}
  select.film-select {{
    flex: 1;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 600;
    max-width: 100%;
  }}
  .btn {{
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }}
  .btn:hover {{ border-color: var(--gold); color: var(--gold); }}
  .btn-gold {{
    background: var(--gold);
    color: #0b0d12;
    border-color: var(--gold);
    font-weight: 700;
  }}
  .btn-gold:hover {{ background: #ffd175; color: #0b0d12; }}

  /* Guide Overlay Selector Row */
  .guide-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    background: #0e121b;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: thin;
  }}
  .guide-pill {{
    background: var(--panel);
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }}
  .guide-pill.active {{
    background: rgba(242, 188, 87, 0.16);
    color: var(--gold);
    border-color: var(--gold);
  }}

  /* Video + Static SVG/Canvas Guide Stage */
  .video-stage {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    max-height: 60vh;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }}
  .video-stage video {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }}
  .video-stage canvas {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }}

  /* Transport + Segmented Cut Scrubber */
  .transport-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #0e121b;
    border-top: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .time-readout {{
    font-family: var(--mono);
    font-size: 12px;
    color: var(--gold);
    min-width: 95px;
  }}
  .seg-scrubber {{
    flex: 1;
    min-width: 180px;
    display: flex;
    gap: 3px;
    height: 22px;
    align-items: stretch;
  }}
  .seg-slot {{
    flex: 1;
    background: #1a2030;
    border: 1px solid #2b344b;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    user-select: none;
  }}
  .seg-slot:hover {{ border-color: var(--gold); color: var(--fg); }}
  .seg-slot.active {{
    border-color: var(--gold);
    color: var(--fg);
    font-weight: 700;
  }}
  .seg-fill {{
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 0%;
    background: rgba(242, 188, 87, 0.28);
    pointer-events: none;
  }}
  .seg-slot span {{ position: relative; z-index: 1; }}

  /* Deterministic Shot & Geometry Inspector */
  .shot-inspector {{
    padding: 14px;
    background: var(--panel-alt);
    border-top: 1px solid var(--border);
  }}
  .shot-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }}
  .phase-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 5px;
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    background: rgba(91, 200, 235, 0.14);
    color: var(--cyan);
    border: 1px solid rgba(91, 200, 235, 0.35);
  }}
  .phase-badge.lock {{
    background: rgba(242, 188, 87, 0.16);
    color: var(--gold);
    border-color: rgba(242, 188, 87, 0.45);
  }}
  .phase-badge.break {{
    background: rgba(245, 101, 101, 0.16);
    color: var(--rose);
    border-color: rgba(245, 101, 101, 0.45);
  }}
  .phase-badge.return {{
    background: rgba(104, 211, 145, 0.15);
    color: var(--green);
    border-color: rgba(104, 211, 145, 0.4);
  }}
  .fit-pill {{
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 5px;
    background: #0e121b;
    border: 1px solid var(--border);
    color: var(--gold);
  }}
  .shot-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  @media (max-width: 720px) {{
    .shot-grid {{ grid-template-columns: 1fr; }}
  }}
  .shot-box {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .shot-box-label {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 4px;
  }}
  .shot-box-title {{
    font-size: 13px;
    font-weight: 700;
    color: var(--fg);
    margin-bottom: 4px;
  }}
  .shot-box-body {{
    font-size: 12.5px;
    color: #d5d9e2;
  }}

  /* Interactive 8-Cut / 4-Part Storyboard Strip */
  .storyboard-section {{
    padding: 12px 14px 14px;
    background: var(--panel);
    border-top: 1px solid var(--border);
  }}
  .storyboard-title-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }}
  .storyboard-title {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
  }}
  .storyboard-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 8px;
  }}
  .sb-card {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 9px 10px;
    cursor: pointer;
    transition: border-color 0.12s;
  }}
  .sb-card:hover {{ border-color: #4b5778; }}
  .sb-card.active {{
    border-color: var(--gold);
    background: rgba(242, 188, 87, 0.08);
  }}
  .sb-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    margin-bottom: 4px;
  }}
  .sb-cut {{
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--gold);
  }}
  .sb-time {{
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
  }}
  .sb-phase {{
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 3px;
    color: var(--cyan);
  }}
  .sb-source {{
    font-size: 11.5px;
    font-weight: 600;
    color: var(--fg);
    margin-bottom: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .sb-desc {{
    font-size: 11px;
    color: var(--muted);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}

  /* Main Section Tabs */
  .tabs {{
    display: flex;
    gap: 6px;
    margin-bottom: 14px;
    overflow-x: auto;
    padding-bottom: 2px;
  }}
  .tab-btn {{
    background: var(--panel);
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }}
  .tab-btn.active {{
    background: var(--gold);
    color: #0b0d12;
    border-color: var(--gold);
    font-weight: 700;
  }}
  .tab-pane {{ display: none; }}
  .tab-pane.active {{ display: block; }}

  /* Grid Cards */
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
    gap: 12px;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .card-head {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
  }}
  .card-title {{ font-weight: 700; font-size: 14px; }}
  .badge {{
    font-family: var(--mono);
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(242, 188, 87, 0.15);
    color: var(--gold);
    white-space: nowrap;
  }}
  .card-thumb {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: #000;
  }}
  .card-desc {{
    font-size: 12px;
    color: var(--muted);
  }}
  .card-actions {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: auto;
  }}

  /* Search & Filter Bar */
  .filter-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }}
  .search-input {{
    flex: 1;
    min-width: 200px;
    background: var(--panel);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
  }}
  .table-wrap {{
    overflow-x: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  th, td {{
    padding: 9px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    background: var(--panel-alt);
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
  }}
  tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
  details summary {{
    cursor: pointer;
    font-size: 12px;
    color: var(--cyan);
    font-weight: 600;
  }}
  pre.prompt-pre {{
    background: #080a0e;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    font-family: var(--mono);
    font-size: 11px;
    max-height: 240px;
    overflow: auto;
    white-space: pre-wrap;
    color: #d6deeb;
    margin-top: 6px;
  }}
</style>
</head>
<body>

<header class="header">
  <div class="brand">ALLWAYS <span>// SHOT-BY-SHOT GEOMETRIC CINEMA STUDIO</span></div>
  <nav class="nav-links">
    <a href="worms.html" style="border-color:var(--gold);color:var(--gold);font-weight:700;">★ 108 Tracked 4D Time Worms (Secondhand Motion) →</a>
    <a href="../index.html">Hub</a>
    <a href="../allways-best/index.html">The One Film</a>
    <a href="../allways-Selects/index.html">Selects</a>
    <a href="../allways-argon/index.html">Argon</a>
    <a href="../allways-opus/index.html">Opus</a>
    <a href="../allways-gpt/index.html">GPT-5.4</a>
    <a href="../allways-sonnet/index.html">Sonnet</a>
  </nav>
</header>

<main class="container">

  <!-- 1-CLICK QUICK FILM SWITCHER -->
  <div class="quick-film-bar" id="quickFilmBar">
    <span class="quick-label">Quick Play:</span>
    <button class="qf-btn active" data-fid="shape-114">1 · Golden Spiral (24s)</button>
    <button class="qf-btn" data-fid="shape-115">2 · Frame in Frame (24s)</button>
    <button class="qf-btn" data-fid="shape-116">3 · S-Curve (24s)</button>
    <button class="qf-btn" data-fid="shape-117">4 · Symmetry (24s)</button>
    <button class="qf-btn" data-fid="shape-118">5 · Rule of Thirds (24s)</button>
    <button class="qf-btn" data-fid="shape-119">6 · Centered (24s)</button>
    <button class="qf-btn" data-fid="shape-120">7 · V-Shape (24s)</button>
    <button class="qf-btn" data-fid="shape-121">8 · Negative Space (24s)</button>
    <button class="qf-btn" data-fid="shape-eight-reel">★ All 8 Rules Reel (28s)</button>
    <button class="qf-btn" data-fid="allways-best">★ ALLWAYS Master (163s)</button>
  </div>

  <!-- ZERO-LAG, DETERMINISTIC VIDEO PLAYER & SHOT INSPECTOR -->
  <section class="player-card">
    <div class="player-toolbar">
      <div class="film-select-group">
        <button class="btn" id="prevFilmBtn" title="Previous Film">◀</button>
        <select class="film-select" id="filmSelect" aria-label="Select Film"></select>
        <button class="btn" id="nextFilmBtn" title="Next Film">▶</button>
      </div>
      <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
        <a class="btn" id="openCaseBtn" href="../allways-best/index.html" target="_blank">Source Dossier ↗</a>
      </div>
    </div>

    <!-- CLEAN STATIC VIEWFINDER GUIDE BAR -->
    <div class="guide-bar" id="guideBar">
      <span class="quick-label">Viewfinder Guide:</span>
      <button class="guide-pill active" data-guide="auto" id="guideAutoBtn">Smart Guide (1 Static Shape / Shot)</button>
      <button class="guide-pill" data-guide="off">Off (Raw Video Only)</button>
      <button class="guide-pill" data-guide="golden_spiral">1 · Golden Spiral</button>
      <button class="guide-pill" data-guide="frame_in_frame">2 · Frame in Frame</button>
      <button class="guide-pill" data-guide="s_curve">3 · S-Curve</button>
      <button class="guide-pill" data-guide="symmetry">4 · Symmetry</button>
      <button class="guide-pill" data-guide="rule_of_thirds">5 · Rule of Thirds</button>
      <button class="guide-pill" data-guide="centered">6 · Centered</button>
      <button class="guide-pill" data-guide="v_shape">7 · V-Shape</button>
      <button class="guide-pill" data-guide="negative_space">8 · Negative Space</button>
    </div>

    <!-- NATIVE HARDWARE VIDEO STAGE + STATIC GUIDE OVERLAY -->
    <div class="video-stage">
      <video id="mainVideo" controls playsinline preload="metadata"></video>
      <canvas id="guideCanvas" width="960" height="540"></canvas>
    </div>

    <!-- CUT-BY-CUT TRANSPORT & SEGMENTED SCRUBBER -->
    <div class="transport-bar">
      <button class="btn" id="prevStepBtn">◀ Prev Cut</button>
      <button class="btn btn-gold" id="playPauseBtn">▶ Play</button>
      <button class="btn" id="nextStepBtn">Next Cut ▶</button>
      <span class="time-readout" id="timeReadout">0.0s / 24.0s</span>
      <div class="seg-scrubber" id="segScrubber" title="Click any cut or part to jump directly to it"></div>
    </div>

    <!-- LIVE DETERMINISTIC SHOT & GEOMETRY INSPECTOR -->
    <div class="shot-inspector">
      <div class="shot-header">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span class="phase-badge" id="shotPhaseBadge">CUT 1 OF 8 · PHASE I: RAW OBSERVATION</span>
          <span style="font-weight:700;font-size:13px;color:var(--fg);" id="shotSourceTitle">Loading...</span>
        </div>
        <span class="fit-pill" id="shotFitPill">Golden Spiral · 73% Fit</span>
      </div>
      <div class="shot-grid">
        <div class="shot-box">
          <div class="shot-box-label">1. What Is Happening in This Shot</div>
          <div class="shot-box-title" id="shotWhatTitle">Archival Source</div>
          <div class="shot-box-body" id="shotWhatBody">—</div>
        </div>
        <div class="shot-box">
          <div class="shot-box-label">2. Geometric Claim &amp; How to Test It Right Now</div>
          <div class="shot-box-title" id="shotHowTitle">Active Geometry</div>
          <div class="shot-box-body" id="shotHowBody">—</div>
        </div>
      </div>
    </div>

    <!-- CLICKABLE 8-CUT / 4-PART STORYBOARD -->
    <div class="storyboard-section">
      <div class="storyboard-title-row">
        <span class="storyboard-title" id="storyboardHeading">ALL 8 CUTS IN THIS FILM — CLICK ANY CUT TO JUMP &amp; COMPARE PHASES</span>
        <span style="font-size:11px;color:var(--muted);" id="filmTheoremSummary"></span>
      </div>
      <div class="storyboard-grid" id="storyboardGrid"></div>
    </div>
  </section>

  <!-- 3 CLEAN EXPLORATION TABS -->
  <div class="tabs">
    <button class="tab-btn active" data-tab="tab-rules">1. The 8 Perspective Rules (With / Without Grid Proof Cards)</button>
    <button class="tab-btn" data-tab="tab-shapes">2. 8 Shape Prompts &amp; Films (SCION 114–121)</button>
    <button class="tab-btn" data-tab="tab-archive">3. All 142 Archive Films</button>
  </div>

  <!-- TAB 1: 8 PERSPECTIVE RULES -->
  <section class="tab-pane active" id="tab-rules">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;">
      <div>
        <h2 style="margin:0;font-size:16px;">8 Perspective Rules from <a href="https://www.youtube.com/watch?v=QNvK63WetSA" target="_blank">Life Is All About Perspective! #shorts ↗</a></h2>
        <p style="margin:3px 0 0;font-size:12px;color:var(--muted);">
          Toggle between the Gold Viewfinder Overlay and the Raw Frame below, or click <b>Play 24s Shape Film</b> to watch all 8 cuts in the player above.
        </p>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn" id="toggleRuleImgsBtn">Switch Cards to Raw Unannotated Frames</button>
        <button class="btn btn-gold" id="playEightReelBtn">▶ Play 28s All-8-Rules Reel</button>
      </div>
    </div>
    <div class="card-grid" id="rulesGrid"></div>
  </section>

  <!-- TAB 2: 8 SCION SHAPE FILMS & PROMPTS -->
  <section class="tab-pane" id="tab-shapes">
    <div style="margin-bottom:12px;">
      <h2 style="margin:0;font-size:16px;">8 Standalone SCION Shape Prompts &amp; 24-Second Archival Proof Films (SCION 114–121)</h2>
      <p style="margin:3px 0 0;font-size:12px;color:var(--muted);">
        Every shape film follows a strict 4-Phase structure: <b>Cuts 1–3 (0–9s)</b> Raw Observation → <b>Cuts 4–6 (9–18s)</b> Gold Viewfinder Lock (+0.6s snap) → <b>Cut 7 (18–21s)</b> Deliberate Rupture/Break → <b>Cut 8 (21–24s)</b> Unannotated Return.
      </p>
    </div>
    <div class="card-grid" id="shapesGrid"></div>
  </section>

  <!-- TAB 3: ALL 142 ARCHIVE FILMS -->
  <section class="tab-pane" id="tab-archive">
    <div class="filter-bar">
      <input type="search" class="search-input" id="archiveSearch" placeholder="Search 142 films by title, maker, or camera movement...">
      <select class="film-select" id="makerFilter" style="max-width:220px;">
        <option value="ALL">All Makers (142)</option>
        <option value="SCION Shape Studio">SCION Shape Studio (9)</option>
        <option value="Anthology Synthesis">Anthology / Featured (5)</option>
        <option value="Gemini Argon">Gemini Argon (51)</option>
        <option value="Claude Opus 5.5">Claude Opus 5.5 (20)</option>
        <option value="GPT-5.4">GPT-5.4 (24)</option>
        <option value="Claude Sonnet">Claude Sonnet (23)</option>
        <option value="Classic Reference">Classic Reference (10)</option>
      </select>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Film Title</th>
            <th>Maker</th>
            <th>Duration</th>
            <th>Dominant Camera / Blocking</th>
            <th>Part 1 → Part 4 Shapes</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="archiveTableBody"></tbody>
      </table>
    </div>
  </section>

</main>

<script>
const FILMS = {json.dumps(films_catalog, separators=(',', ':'))};
const RULES = {json.dumps(rules_list, separators=(',', ':'))};
const SCION_OPS = {json.dumps(scion_shapes_data.get("operators", []), separators=(',', ':'))};
const RULE_META = {json.dumps(RULE_META, separators=(',', ':'))};

let currentFilmIdx = 1; // Default to shape-114 (1 · Golden Spiral, 24s)
let currentGuideMode = "auto"; // "auto", "off", or one of the 8 rule_ids
let lastStepIdx = -1;
let showRuleOverlays = true;

const videoEl = document.getElementById("mainVideo");
const guideCanvas = document.getElementById("guideCanvas");
const ctx = guideCanvas.getContext("2d");
const filmSelect = document.getElementById("filmSelect");

function populateFilmDropdown() {{
  const groups = [
    {{ key: "shapes", label: "8 Perspective Shape Films (SCION 114–121 + 8-Rule Reel)" }},
    {{ key: "featured", label: "Featured Master Anthologies" }},
    {{ key: "argon", label: "Gemini Argon (51 Films)" }},
    {{ key: "opus", label: "Claude Opus 5.5 (20 Films)" }},
    {{ key: "gpt", label: "GPT-5.4 (24 Films)" }},
    {{ key: "sonnet", label: "Claude Sonnet (23 Films)" }},
    {{ key: "partials", label: "Classic Reference (10 Films)" }}
  ];
  filmSelect.innerHTML = "";
  groups.forEach(g => {{
    const og = document.createElement("optgroup");
    og.label = g.label;
    FILMS.forEach((f, idx) => {{
      if (f.group === g.key) {{
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${{f.title}} (${{f.maker}} · ${{f.duration_s.toFixed(0)}}s)`;
        og.appendChild(opt);
      }}
    }});
    if (og.children.length) filmSelect.appendChild(og);
  }});
}}

function getActiveStepIndex(film, t) {{
  if (!film.steps || !film.steps.length) return 0;
  for (let i = 0; i < film.steps.length; i++) {{
    const s = film.steps[i];
    if (t >= s.t_start && t < s.t_end) return i;
  }}
  if (t >= film.steps[film.steps.length - 1].t_start) return film.steps.length - 1;
  return 0;
}}

/* Draw a clean, static geometric guide on the overlay canvas ONLY when needed */
function drawStaticGuideOverlay(film, stepIdx) {{
  const W = guideCanvas.width;
  const H = guideCanvas.height;
  ctx.clearRect(0, 0, W, H);

  if (currentGuideMode === "off") return;

  // CRITICAL FIX FOR RANDOMNESS / DOUBLE-DRAWING:
  // In "auto" mode:
  // - eight-perspectives.mp4 (shape-eight-reel) already has burned-in gold guides on every chapter.
  // - SCION 114-121 films already have burned-in gold guides during Phase II (Cuts 4-6).
  // So we clear the canvas during those burned-in intervals (zero double-grids!),
  // and draw a clean, static guide (once per cut, zero 60fps redraws) on unannotated shots.
  const step = (film.steps && film.steps[stepIdx]) ? film.steps[stepIdx] : null;
  if (currentGuideMode === "auto") {{
    if (film.id === "shape-eight-reel") return;
    if (film.has_burned_in_grid && step && step.phase.includes("II ·")) return;
  }}

  const ruleId = (currentGuideMode === "auto")
    ? (step ? step.rule_id : film.pinned_rule)
    : currentGuideMode;

  if (!ruleId) return;

  ctx.save();
  ctx.strokeStyle = "rgba(242, 188, 87, 0.9)";
  ctx.fillStyle = "rgba(242, 188, 87, 0.9)";
  ctx.lineWidth = 2.5;

  if (ruleId === "golden_spiral") {{
    const gx = W * 0.618, gy = H * 0.618;
    ctx.strokeRect(12, 12, W - 24, H - 24);
    ctx.beginPath();
    ctx.moveTo(gx, 12); ctx.lineTo(gx, H - 12);
    ctx.moveTo(gx, gy); ctx.lineTo(W - 12, gy);
    ctx.stroke();

    const ex = W * 0.68, ey = H * 0.44;
    ctx.beginPath();
    for (let i = 0; i <= 90; i++) {{
      const t = (i / 90) * Math.PI * 2.5;
      const r = Math.max(W, H) * 0.52 * Math.exp(-0.34 * t);
      const x = ex - r * Math.cos(t);
      const y = ey + r * Math.sin(t) * 0.78;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }}
    ctx.stroke();
    ctx.beginPath(); ctx.arc(ex, ey, 6, 0, Math.PI * 2); ctx.fill();
  }} else if (ruleId === "frame_in_frame") {{
    const x0 = W * 0.16, x1 = W * 0.84, y0 = H * 0.14, y1 = H * 0.88;
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(x0, y0);
    ctx.moveTo(W, 0); ctx.lineTo(x1, y0);
    ctx.moveTo(0, H); ctx.lineTo(x0, y1);
    ctx.moveTo(W, H); ctx.lineTo(x1, y1);
    ctx.stroke();
  }} else if (ruleId === "s_curve") {{
    ctx.beginPath();
    for (let i = 0; i <= 60; i++) {{
      const s = i / 60;
      const y = H * (0.90 - 0.78 * s);
      const x = W * (0.50 + 0.24 * Math.sin((s - 0.5) * Math.PI * 2.0));
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }}
    ctx.stroke();
  }} else if (ruleId === "symmetry") {{
    ctx.beginPath();
    ctx.moveTo(W * 0.5, 0); ctx.lineTo(W * 0.5, H);
    ctx.stroke();
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(W * 0.25, H * 0.12); ctx.lineTo(W * 0.25, H * 0.88);
    ctx.moveTo(W * 0.75, H * 0.12); ctx.lineTo(W * 0.75, H * 0.88);
    ctx.stroke();
  }} else if (ruleId === "rule_of_thirds") {{
    ctx.beginPath();
    ctx.moveTo(W / 3, 0); ctx.lineTo(W / 3, H);
    ctx.moveTo((2 * W) / 3, 0); ctx.lineTo((2 * W) / 3, H);
    ctx.moveTo(0, H / 3); ctx.lineTo(W, H / 3);
    ctx.moveTo(0, (2 * H) / 3); ctx.lineTo(W, (2 * H) / 3);
    ctx.stroke();
    [[W/3, H/3], [2*W/3, H/3], [W/3, 2*H/3], [2*W/3, 2*H/3]].forEach(([px, py]) => {{
      ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2); ctx.fill();
    }});
  }} else if (ruleId === "centered") {{
    ctx.beginPath();
    ctx.moveTo(W * 0.43, 0); ctx.lineTo(W * 0.43, H);
    ctx.moveTo(W * 0.57, 0); ctx.lineTo(W * 0.57, H);
    ctx.moveTo(0, H * 0.67); ctx.lineTo(W, H * 0.67);
    ctx.stroke();
  }} else if (ruleId === "v_shape") {{
    ctx.beginPath();
    ctx.moveTo(W * 0.10, 0); ctx.lineTo(W * 0.50, H * 0.88);
    ctx.lineTo(W * 0.90, 0);
    ctx.stroke();
    ctx.beginPath(); ctx.arc(W * 0.50, H * 0.88, 6, 0, Math.PI * 2); ctx.fill();
  }} else if (ruleId === "negative_space") {{
    ctx.strokeRect(W * 0.05, H * 0.06, W * 0.90, H * 0.56);
    ctx.beginPath();
    ctx.moveTo(0, H * 0.62); ctx.lineTo(W, H * 0.62);
    ctx.stroke();
  }}

  // Top-left clean badge showing which static guide is drawn
  const rm = RULE_META[ruleId];
  if (rm) {{
    ctx.fillStyle = "rgba(11, 13, 18, 0.82)";
    ctx.fillRect(14, 14, 240, 28);
    ctx.strokeStyle = "rgba(242, 188, 87, 0.7)";
    ctx.lineWidth = 1;
    ctx.strokeRect(14, 14, 240, 28);
    ctx.fillStyle = "#f2bc57";
    ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, sans-serif";
    ctx.fillText("GUIDE: " + rm.name.toUpperCase(), 24, 32);
  }}
  ctx.restore();
}}

function buildSegmentedScrubber(film) {{
  const wrap = document.getElementById("segScrubber");
  wrap.innerHTML = "";
  (film.steps || []).forEach((s, idx) => {{
    const slot = document.createElement("div");
    slot.className = "seg-slot";
    slot.dataset.idx = idx;
    slot.innerHTML = `<div class="seg-fill" id="segFill_${{idx}}"></div><span>${{s.label}}</span>`;
    slot.addEventListener("click", () => {{
      videoEl.currentTime = s.t_start + 0.05;
      updateActiveStepUI(film, idx, true);
    }});
    wrap.appendChild(slot);
  }});
}}

function buildStoryboardCards(film) {{
  const grid = document.getElementById("storyboardGrid");
  const heading = document.getElementById("storyboardHeading");
  const thm = document.getElementById("filmTheoremSummary");

  if (film.id === "shape-eight-reel") {{
    heading.textContent = "ALL 8 PERSPECTIVE RULES IN THIS 28s REEL — CLICK ANY RULE CHAPTER TO JUMP";
  }} else if (film.has_burned_in_grid) {{
    heading.textContent = "ALL 8 CUTS IN THIS 24s SHAPE FILM — CLICK ANY CUT TO JUMP & COMPARE PHASES";
  }} else {{
    heading.textContent = "4 STRUCTURAL PARTS OF THIS FILM — CLICK ANY PART TO JUMP & TEST GEOMETRY";
  }}
  thm.textContent = film.theorem || "";

  grid.innerHTML = "";
  (film.steps || []).forEach((s, idx) => {{
    const card = document.createElement("div");
    card.className = "sb-card";
    card.id = `sbCard_${{idx}}`;
    card.innerHTML = `
      <div class="sb-top">
        <span class="sb-cut">${{s.label}} · ${{s.fit_pct}}% Fit</span>
        <span class="sb-time">${{s.t_start.toFixed(1)}}s–${{s.t_end.toFixed(1)}}s</span>
      </div>
      <div class="sb-phase">${{s.phase}}</div>
      <div class="sb-source" title="${{s.source}}">${{s.source}}</div>
      <div class="sb-desc">${{s.what_happens}}</div>
    `;
    card.addEventListener("click", () => {{
      videoEl.currentTime = s.t_start + 0.05;
      videoEl.play().catch(() => {{}});
      updateActiveStepUI(film, idx, true);
    }});
    grid.appendChild(card);
  }});
}}

/* Update the Inspector & Storyboard ONLY when the active Cut / Part changes! */
function updateActiveStepUI(film, stepIdx, forceRedraw) {{
  if (stepIdx === lastStepIdx && !forceRedraw) return;
  lastStepIdx = stepIdx;

  const steps = film.steps || [];
  const s = steps[stepIdx];
  if (!s) return;

  const badge = document.getElementById("shotPhaseBadge");
  badge.textContent = `${{s.label.toUpperCase()}} OF ${{steps.length}} (${{s.t_start.toFixed(1)}}s–${{s.t_end.toFixed(1)}}s) · ${{s.phase.toUpperCase()}}`;
  badge.className = "phase-badge";
  if (s.phase.includes("II ·") || s.phase.includes("Rule #")) badge.classList.add("lock");
  else if (s.phase.includes("III ·")) badge.classList.add("break");
  else if (s.phase.includes("IV ·")) badge.classList.add("return");

  document.getElementById("shotSourceTitle").textContent = `${{s.source}} — from ${{s.from_film}}`;

  const rm = RULE_META[s.rule_id] || RULE_META.golden_spiral;
  document.getElementById("shotFitPill").textContent = `${{rm.name}} · ${{s.fit_pct}}% Fit`;

  document.getElementById("shotWhatTitle").textContent = `${{s.source}} (${{s.from_film}})`;
  document.getElementById("shotWhatBody").textContent = s.what_happens;

  document.getElementById("shotHowTitle").textContent = `${{rm.name}} — ${{s.phase}}`;
  document.getElementById("shotHowBody").textContent = s.how_to_test;

  // Highlight active storyboard card & segment slot
  steps.forEach((_, i) => {{
    const card = document.getElementById(`sbCard_${{i}}`);
    if (card) card.classList.toggle("active", i === stepIdx);
  }});
  const slots = document.querySelectorAll("#segScrubber .seg-slot");
  slots.forEach((sl, i) => sl.classList.toggle("active", i === stepIdx));

  // Redraw static overlay canvas only when step changes
  drawStaticGuideOverlay(film, stepIdx);
}}

function updateProgressBarsOnly() {{
  const film = FILMS[currentFilmIdx];
  if (!film) return;
  const t = videoEl.currentTime || 0;
  const dur = film.duration_s || videoEl.duration || 24;
  document.getElementById("timeReadout").textContent = `${{t.toFixed(1)}}s / ${{dur.toFixed(1)}}s`;

  const stepIdx = getActiveStepIndex(film, t);
  if (stepIdx !== lastStepIdx) {{
    updateActiveStepUI(film, stepIdx, false);
  }}

  // Update lightweight fill width inside segmented scrubber
  const steps = film.steps || [];
  steps.forEach((s, i) => {{
    const fill = document.getElementById(`segFill_${{i}}`);
    if (!fill) return;
    if (t <= s.t_start) fill.style.width = "0%";
    else if (t >= s.t_end) fill.style.width = "100%";
    else {{
      const pct = Math.max(0, Math.min(100, ((t - s.t_start) / Math.max(0.1, s.t_end - s.t_start)) * 100));
      fill.style.width = pct.toFixed(1) + "%";
    }}
  }});
}}

function loadFilmByIndex(idx, seekTime = 0, autoPlay = false) {{
  if (idx < 0) idx = FILMS.length - 1;
  if (idx >= FILMS.length) idx = 0;
  currentFilmIdx = idx;
  filmSelect.value = idx;
  lastStepIdx = -1;

  const film = FILMS[idx];
  document.getElementById("openCaseBtn").href = film.case_url || "../index.html";

  // Update Quick Play bar active state
  document.querySelectorAll("#quickFilmBar .qf-btn").forEach(btn => {{
    btn.classList.toggle("active", btn.dataset.fid === film.id);
  }});

  // Update Smart Default label so user knows whether video has built-in gold guides
  const autoBtn = document.getElementById("guideAutoBtn");
  if (film.has_burned_in_grid) {{
    autoBtn.textContent = "Built-In Video Guide (No Extra Overlay)";
  }} else {{
    autoBtn.textContent = "Auto Part Guide (1 Stable Shape / Part)";
  }}

  buildSegmentedScrubber(film);
  buildStoryboardCards(film);

  videoEl.src = film.video_rel;
  videoEl.currentTime = seekTime || 0;

  const initStep = getActiveStepIndex(film, seekTime || 0);
  updateActiveStepUI(film, initStep, true);
  updateProgressBarsOnly();

  if (autoPlay) {{
    videoEl.play().catch(() => {{}});
  }}
}}

function loadFilmById(fid, seekTime = 0, autoPlay = true) {{
  const idx = FILMS.findIndex(f => f.id === fid);
  if (idx !== -1) {{
    loadFilmByIndex(idx, seekTime, autoPlay);
    window.scrollTo({{ top: 0, behavior: "smooth" }});
  }}
}}

/* Wire Player Controls */
filmSelect.addEventListener("change", () => loadFilmByIndex(parseInt(filmSelect.value, 10), 0, true));
document.getElementById("prevFilmBtn").addEventListener("click", () => loadFilmByIndex(currentFilmIdx - 1, 0, true));
document.getElementById("nextFilmBtn").addEventListener("click", () => loadFilmByIndex(currentFilmIdx + 1, 0, true));

document.querySelectorAll("#quickFilmBar .qf-btn").forEach(btn => {{
  btn.addEventListener("click", () => loadFilmById(btn.dataset.fid, 0, true));
}});

document.querySelectorAll("#guideBar .guide-pill").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll("#guideBar .guide-pill").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentGuideMode = btn.dataset.guide;
    const film = FILMS[currentFilmIdx];
    const stepIdx = getActiveStepIndex(film, videoEl.currentTime || 0);
    drawStaticGuideOverlay(film, stepIdx);
  }});
}});

document.getElementById("playPauseBtn").addEventListener("click", () => {{
  if (videoEl.paused) videoEl.play().catch(() => {{}});
  else videoEl.pause();
}});
videoEl.addEventListener("play", () => {{
  document.getElementById("playPauseBtn").textContent = "⏸ Pause";
}});
videoEl.addEventListener("pause", () => {{
  document.getElementById("playPauseBtn").textContent = "▶ Play";
}});

document.getElementById("prevStepBtn").addEventListener("click", () => {{
  const film = FILMS[currentFilmIdx];
  const cur = getActiveStepIndex(film, videoEl.currentTime || 0);
  const target = Math.max(0, cur - 1);
  if (film.steps && film.steps[target]) {{
    videoEl.currentTime = film.steps[target].t_start + 0.05;
    updateActiveStepUI(film, target, true);
  }}
}});
document.getElementById("nextStepBtn").addEventListener("click", () => {{
  const film = FILMS[currentFilmIdx];
  const cur = getActiveStepIndex(film, videoEl.currentTime || 0);
  const target = Math.min((film.steps ? film.steps.length : 1) - 1, cur + 1);
  if (film.steps && film.steps[target]) {{
    videoEl.currentTime = film.steps[target].t_start + 0.05;
    updateActiveStepUI(film, target, true);
  }}
}});

/* Native timeupdate event — zero 60fps polling lag! */
videoEl.addEventListener("timeupdate", updateProgressBarsOnly);
videoEl.addEventListener("seeked", updateProgressBarsOnly);

/* Populate Tab 1: 8 Perspective Rules */
function renderRulesTab() {{
  const grid = document.getElementById("rulesGrid");
  grid.innerHTML = "";
  RULES.forEach(r => {{
    const w = r.winner;
    const scionId = 113 + r.num;
    const imgSrc = showRuleOverlays ? r.overlay_img : r.clean_img;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-head">
        <span class="card-title">#${{r.num}} · ${{r.name}}</span>
        <span class="badge">${{Math.round(w.score * 100)}}% Fit</span>
      </div>
      <img class="card-thumb" src="${{imgSrc}}" loading="lazy" alt="${{r.name}}">
      <div class="card-desc">
        <strong style="color:var(--fg);">Geometry:</strong> ${{r.geometry}}<br>
        <strong style="color:var(--fg);">#1 Archive Winner:</strong> <em>${{w.source_title}}</em> in <b>${{w.film_title}}</b> (${{w.maker}} @ ${{w.timestamp_s.toFixed(1)}}s)<br>
        <span>${{w.desc}}</span>
      </div>
      <div class="card-actions">
        <button class="btn btn-gold" onclick="loadFilmById('shape-${{scionId}}', 0, true)">▶ Play 24s Shape Film (SCION ${{scionId}})</button>
        <button class="btn" onclick="loadFilmById('${{w.film_id}}', ${{w.start_s}}, true)">Jump to Source Shot @ ${{w.timestamp_s.toFixed(1)}}s</button>
      </div>
    `;
    grid.appendChild(card);
  }});
}}

document.getElementById("toggleRuleImgsBtn").addEventListener("click", (e) => {{
  showRuleOverlays = !showRuleOverlays;
  e.target.textContent = showRuleOverlays
    ? "Switch Cards to Raw Unannotated Frames"
    : "Switch Cards to Gold Viewfinder Overlays";
  renderRulesTab();
}});

document.getElementById("playEightReelBtn").addEventListener("click", () => {{
  loadFilmById("shape-eight-reel", 0, true);
}});

/* Populate Tab 2: 8 SCION Shape Prompts & Films */
function renderShapesTab() {{
  const grid = document.getElementById("shapesGrid");
  grid.innerHTML = "";
  SCION_OPS.forEach(op => {{
    const card = document.createElement("div");
    card.className = "card";
    const cutsHtml = (op.cuts || []).map(c =>
      `<div style="font-size:11px;padding:3px 0;border-bottom:1px solid #1e2436;">
        <b style="color:var(--gold);">Cut ${{c.cut_num}} (${{c.time_range}})</b> · <span style="color:var(--cyan);">${{c.phase}}</span>:
        <b>${{c.source_title}}</b> (${{Math.round(c.score * 100)}}% fit)
      </div>`
    ).join("");
    card.innerHTML = `
      <div class="card-head">
        <span class="card-title">${{op.short_title}}</span>
        <span class="badge">24.0s · 8 Cuts</span>
      </div>
      <div class="card-desc" style="color:var(--fg);">${{op.theorem}}</div>
      <div style="background:var(--panel-alt);padding:8px;border-radius:6px;border:1px solid var(--border);">
        ${{cutsHtml}}
      </div>
      <details>
        <summary>Read Full SCION ${{op.scion_id}} Markdown Prompt</summary>
        <pre class="prompt-pre">${{op.prompt_markdown.replace(/</g, "&lt;")}}</pre>
      </details>
      <div class="card-actions">
        <button class="btn btn-gold" onclick="loadFilmById('shape-${{op.scion_id}}', 0, true)">▶ Watch 24s Film &amp; Step Through 8 Cuts</button>
      </div>
    `;
    grid.appendChild(card);
  }});
}}

/* Populate Tab 3: All 142 Archive Films Table */
function renderArchiveTable() {{
  const q = (document.getElementById("archiveSearch").value || "").toLowerCase();
  const maker = document.getElementById("archiveTableBody") ? document.getElementById("makerFilter").value : "ALL";
  const tbody = document.getElementById("archiveTableBody");
  tbody.innerHTML = "";

  FILMS.forEach((f, idx) => {{
    if (maker !== "ALL" && f.maker !== maker) return;
    const hay = `${{f.title}} ${{f.maker}} ${{f.dominant_topology}}`.toLowerCase();
    if (q && !hay.includes(q)) return;

    const partShapes = (f.steps || []).slice(0, 4).map(s => {{
      const rm = RULE_META[s.rule_id];
      return rm ? rm.short : s.rule_id;
    }}).join(" → ");

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family:var(--mono);color:var(--muted);">${{idx + 1}}</td>
      <td><strong style="color:var(--fg);">${{f.title}}</strong></td>
      <td>${{f.maker}}</td>
      <td style="font-family:var(--mono);">${{f.duration_s.toFixed(1)}}s</td>
      <td>${{f.dominant_topology.replace(/_/g, " ")}}</td>
      <td style="font-size:11px;color:var(--cyan);">${{partShapes}}</td>
      <td><button class="btn btn-gold" style="padding:4px 9px;font-size:11px;" onclick="loadFilmByIndex(${{idx}}, 0, true);window.scrollTo({{top:0,behavior:'smooth'}});">▶ Load</button></td>
    `;
    tbody.appendChild(tr);
  }});
}}

document.getElementById("archiveSearch").addEventListener("input", renderArchiveTable);
document.getElementById("makerFilter").addEventListener("change", renderArchiveTable);

/* Tab Switching */
document.querySelectorAll(".tabs .tab-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".tabs .tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  }});
}});

/* Initialize */
populateFilmDropdown();
renderRulesTab();
renderShapesTab();
renderArchiveTable();
// Start on shape-114 (1 · Golden Spiral, 24s) so the 8-cut 4-phase structure is immediately clear
const startIdx = FILMS.findIndex(f => f.id === "shape-114");
loadFilmByIndex(startIdx !== -1 ? startIdx : 0, 0, false);
</script>
</body>
</html>
"""

    out_path = os.path.join(TENSOR_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Wrote {out_path} ({len(html) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
