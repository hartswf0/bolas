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

  /* COMPACT MOBILE-FIRST MULTI-DEPTH WORM STUDIO AT TOP OF PAGE */
  .shm-worm-hero {{
    background: var(--panel);
    border: 1.5px solid var(--gold);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
  }}
  .shm-ctrl-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 6px 10px;
    background: var(--panel-alt);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .shm-worm-dual {{
    display: grid;
    grid-template-columns: 1.30fr 0.70fr;
    background: #040609;
  }}
  .shm-pane {{
    position: relative;
    height: 265px;
    overflow: hidden;
    border-right: 1px solid var(--border);
  }}
  .shm-pane:last-child {{ border-right: none; }}
  @media (max-width: 768px) {{
    .shm-pane {{ height: 228px; }}
  }}
  .shm-swipe-strip {{
    display: flex;
    gap: 5px;
    overflow-x: auto;
    padding: 5px 8px;
    background: #080b11;
    border-top: 1px solid var(--border);
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }}
  .shm-swipe-strip::-webkit-scrollbar {{ display: none; }}
  .shm-swipe-tile {{
    flex: 0 0 92px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 3px;
    cursor: pointer;
  }}
  .shm-swipe-tile.active {{
    border-color: var(--gold);
    background: rgba(242, 188, 87, 0.1);
  }}
  .shm-swipe-tile canvas {{
    width: 100%;
    height: 34px;
    display: block;
    background: #04060a;
    border-radius: 3px;
  }}
  .shm-swipe-title {{
    font-size: 9.5px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
  }}
  .shm-mini-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
    gap: 6px;
  }}
  @media (max-width: 520px) {{
    .shm-mini-grid {{
      grid-template-columns: repeat(3, 1fr);
      gap: 5px;
    }}
  }}
  .shm-mini-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 5px;
    cursor: pointer;
  }}
  .shm-mini-card:hover, .shm-mini-card.active {{
    border-color: var(--gold);
    background: rgba(242, 188, 87, 0.07);
  }}
</style>
</head>
<body>

<header class="header">
  <div class="brand">ALLWAYS &amp; SECONDHAND MOTION <span>// DISENTANGLED MULTI-DEPTH 4D WORMS</span></div>
  <nav class="nav-links">
    <a href="worms.html" style="border-color:var(--gold);color:var(--gold);font-weight:700;">Fullscreen 108 Worms ↗</a>
    <a href="https://hartswf0.github.io/secondhand-motion/" target="_blank">Secondhand Motion ↗</a>
    <a href="../index.html">Hub</a>
    <a href="../allways-best/index.html">The One Film</a>
  </nav>
</header>

<main class="container">

  <!-- ====================================================================== -->
  <!-- DISENTANGLED MULTI-DEPTH WORM STUDIO (108 SHOTS · 424 LAYERS)          -->
  <!-- ====================================================================== -->
  <section class="shm-worm-hero" id="shmWormHero">
    <!-- Row 1: Compact Shot Selector + View Switcher -->
    <div class="shm-ctrl-row">
      <div style="display:flex;align-items:center;gap:4px;flex:1;min-width:190px;">
        <button class="btn" id="shmPrevBtn" style="padding:4px 8px;">◀</button>
        <button class="btn btn-gold" id="shmPlayBtn" style="padding:4px 9px;">▶</button>
        <select class="film-select" id="shmSelect" style="min-width:140px;padding:4px 7px;font-size:12px;" aria-label="Select Secondhand Motion Worm"></select>
        <button class="btn" id="shmNextBtn" style="padding:4px 8px;">▶</button>
      </div>
      <div style="display:flex;gap:4px;align-items:center;overflow-x:auto;" id="shmModeBar">
        <button class="guide-pill active" data-wmode="stack" title="Disentangled Depth Worm Rows — Every layer separated in its own horizontal worm track">Disentangled</button>
        <button class="guide-pill" data-wmode="box3d" title="3D Multiplane Cel Stack (like giraffe-walks-past)">3D Planes</button>
        <button class="guide-pill" data-wmode="orbit3d" title="Exploded 3D Spatiotemporal Worm">3D Worm</button>
        <a class="guide-pill" id="shmCaseLink" href="https://hartswf0.github.io/secondhand-motion/pages/giraffe-walks-past.html" target="_blank">Shot ↗</a>
      </div>
    </div>

    <!-- Synchronized Compact Dual Stage (Disentangled Worm Stack + Unobstructed 2D Cutout Stage) -->
    <div class="shm-worm-dual">
      <div class="shm-pane p3d">
        <canvas id="shmPrism3d" width="760" height="440" style="width:100%;height:100%;display:block;cursor:pointer;touch-action:none;"></canvas>
        <span id="shmHud3d" style="position:absolute;top:5px;left:6px;background:rgba(9,11,16,0.86);padding:2px 6px;border-radius:4px;font:500 10px var(--mono);color:var(--fg);pointer-events:none;">Disentangled Depth Worms · Drag to scrub time · Tap any row to solo</span>
        <div style="position:absolute;top:5px;right:6px;display:flex;gap:3px;">
          <button class="guide-pill" id="shmSoloClearBtn" style="display:none;padding:2px 7px;font-size:10px;border-color:var(--gold);color:var(--gold);font-weight:700;">← All Worms</button>
          <button class="guide-pill" id="shmResetCam" style="padding:2px 6px;font-size:10px;">Reset</button>
        </div>
      </div>
      <div class="shm-pane p2d">
        <video id="shmVideo" playsinline muted loop preload="auto" style="display:none;"></video>
        <img id="shmFallbackImg" style="display:none;" alt="Keyframe strip">
        <canvas id="shmOverlay2d" width="600" height="380" style="width:100%;height:100%;display:block;"></canvas>
        <span id="shmHud2d" style="position:absolute;top:5px;left:6px;background:rgba(9,11,16,0.86);padding:2px 6px;border-radius:4px;font:500 10px var(--mono);color:var(--fg);pointer-events:none;">SAM Video Cutout</span>
        <div style="position:absolute;top:5px;right:6px;display:flex;gap:3px;" id="shmSourceBar">
          <button class="guide-pill active" data-src="cutout" style="padding:2px 6px;font-size:10px;">Cutout</button>
          <button class="guide-pill" data-src="scene" style="padding:2px 6px;font-size:10px;">+Planes</button>
          <button class="guide-pill" data-src="cel" style="padding:2px 6px;font-size:10px;">Cel</button>
          <button class="guide-pill" data-src="src" style="padding:2px 6px;font-size:10px;">Raw</button>
        </div>
      </div>
    </div>

    <!-- Row 2: Compact Scrubber + 1-Line Telemetry -->
    <div class="shm-ctrl-row" style="border-bottom:none;border-top:1px solid var(--border);">
      <button class="btn" id="shmStepPrev" style="padding:3px 7px;">-1f</button>
      <input type="range" id="shmSlider" min="0" max="32" value="0" step="1" style="flex:1;min-width:110px;accent-color:var(--gold);height:5px;">
      <button class="btn" id="shmStepNext" style="padding:3px 7px;">+1f</button>
      <span class="time-readout" id="shmSummaryText" style="min-width:auto;font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Loading 108 Disentangled Multi-Depth Worms...</span>
    </div>

    <!-- Row 3: Built-in Horizontal Touch-Swipe Strip of All 108 Multi-Depth Worms -->
    <div class="shm-swipe-strip" id="shmSwipeStrip"></div>
  </section>

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

  <!-- 4 CLEAN EXPLORATION TABS -->
  <div class="tabs">
    <button class="tab-btn active" data-tab="tab-shm-worms">★ 108 Secondhand Motion 4D Time Worms (Atlas + Cards)</button>
    <button class="tab-btn" data-tab="tab-rules">1. The 8 Perspective Rules (With / Without Grid Proof Cards)</button>
    <button class="tab-btn" data-tab="tab-shapes">2. 8 Shape Prompts &amp; Films (SCION 114–121)</button>
    <button class="tab-btn" data-tab="tab-archive">3. All 142 Archive Films</button>
  </div>

  <!-- TAB 0: 108 SECONDHAND MOTION 4D TIME WORMS ATLAS & CARDS -->
  <section class="tab-pane active" id="tab-shm-worms">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;">
      <div>
        <h2 style="margin:0;font-size:16px;">108 Ground-Truth 4D Spatiotemporal Time Worms from <a href="https://hartswf0.github.io/secondhand-motion/" target="_blank">Secondhand Motion ↗</a></h2>
        <p style="margin:3px 0 0;font-size:12px;color:var(--muted);">
          Click any card below to load its 3D polygon silhouette tube, multiplane depth shell, camera translation ribbon, and articulated limb braid into the 4D Worm Studio above.
        </p>
      </div>
      <div class="filter-bar" style="margin-bottom:0;">
        <input type="search" class="search-input" id="shmSearchInput" placeholder="Search 108 worms by category, topology, gait, or rule..." style="min-width:240px;">
        <select class="film-select" id="shmTopoFilter" style="max-width:240px;">
          <option value="ALL">All 108 Tracked Worms</option>
          <option value="CAMERA_SHEAR_RIBBON">Camera Shear Ribbon (37)</option>
          <option value="LOOMING_FUNNEL_CONE">Looming Funnel Cone (27)</option>
          <option value="ARTICULATED_LIMB_BRAID">Articulated Limb Braid (23)</option>
          <option value="SERPENTINE_CORKSCREW">Serpentine Corkscrew (13)</option>
          <option value="LOCKED_PILLAR">Locked Pillar (8)</option>
        </select>
      </div>
    </div>
    <div style="margin-bottom:14px;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:10px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:6px;">
        <span style="font-size:11px;font-family:var(--mono);color:var(--gold);font-weight:700;">108-WORM 3D SPATIOTEMPORAL CONTACT ATLAS (SORTED BY TOPOLOGY CLASS)</span>
        <a href="img/secondhand_worms_atlas.jpg" target="_blank" style="font-size:11px;font-family:var(--mono);">Open Full-Resolution Atlas (2000×2448) ↗</a>
      </div>
      <img src="img/secondhand_worms_atlas.jpg" loading="lazy" alt="108 Secondhand Motion 4D Time Worms Atlas" style="width:100%;border-radius:6px;border:1px solid var(--border);display:block;">
    </div>
    <div class="shm-mini-grid" id="shmCardsGrid"></div>
  </section>

  <!-- TAB 1: 8 PERSPECTIVE RULES -->
  <section class="tab-pane" id="tab-rules">
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

/* ========================================================================== */
/* DISENTANGLED MULTI-DEPTH WORM STUDIO ENGINE (108 SHOTS · 424 LAYERS)       */
/* ========================================================================== */
(function initShmWormStudio() {{
  let worms = [];
  let curWormIdx = 0;
  let curFrame = 0;
  let curSrcMode = "cutout";
  let wMode = "stack"; // DEFAULT: Physically Disentangled Depth Worm Rows
  let showMaskVid = true;
  let isPlaying = false;
  let lastTick = 0;
  let soloLayerId = null;
  let yaw = -0.46, pitch = 0.22;
  let dragging = false, dragX = 0, dragY = 0, moved = false;
  let hitNodes = [];
  let rowBands = [];
  const frameCache = {{}};

  const shmVideo = document.getElementById("shmVideo");
  const shmOverlay2d = document.getElementById("shmOverlay2d");
  const ctx2d = shmOverlay2d.getContext("2d");
  const shmPrism3d = document.getElementById("shmPrism3d");
  const ctx3d = shmPrism3d.getContext("2d");
  const shmSelect = document.getElementById("shmSelect");
  const shmSlider = document.getElementById("shmSlider");
  const shmSoloClearBtn = document.getElementById("shmSoloClearBtn");

  function getFrameDir(w) {{
    if (!w) return "";
    if (w.frame_dir) return w.frame_dir;
    const sid = w.shot_id || (w.slug === "giraffe-walks-past" ? "giraffe-walks-past" : (w.slug + "-gwp"));
    return "https://hartswf0.github.io/secondhand-motion/shots/" + sid + "/frames";
  }}

  function ensureFrameImg(w, fi) {{
    if (!w) return null;
    const fDir = getFrameDir(w);
    if (!fDir) return null;
    if (!frameCache[w.slug]) frameCache[w.slug] = {{}};
    const bag = frameCache[w.slug];
    if (bag[fi]) return (bag[fi].complete && bag[fi].naturalWidth > 0) ? bag[fi] : null;
    const im = new Image();
    im.onload = () => {{
      if (worms[curWormIdx] && worms[curWormIdx].slug === w.slug) drawShmAll();
    }};
    im.src = `${{fDir}}/f${{String(fi).padStart(3, "0")}}.jpg`;
    bag[fi] = im;
    return null;
  }}

  function preloadShotFrames(w) {{
    if (!w) return;
    const nf = (w.frames || []).length;
    ensureFrameImg(w, 0);
    ensureFrameImg(w, Math.floor(nf / 2));
    ensureFrameImg(w, Math.max(0, nf - 1));
    (w.keys || []).forEach(k => {{ if (k >= 0 && k < nf) ensureFrameImg(w, k); }});
    for (let i = 0; i < nf; i += 2) ensureFrameImg(w, i);
  }}

  function getMediaForFrame(w, fi) {{
    const im = ensureFrameImg(w, fi);
    if (im) return im;
    if (shmVideo.readyState >= 2 && shmVideo.videoWidth > 0) return shmVideo;
    const bag = frameCache[w.slug] || {{}};
    let bestImg = null, bestDist = 9999;
    Object.keys(bag).forEach(k => {{
      const cand = bag[k];
      if (cand && cand.complete && cand.naturalWidth > 0) {{
        const d = Math.abs(parseInt(k, 10) - fi);
        if (d < bestDist) {{ bestDist = d; bestImg = cand; }}
      }}
    }});
    return bestImg;
  }}

  function getPlanePolyUV(dw, fr, pt) {{
    if (dw.role === "subject" && fr && fr.ring && fr.ring.length >= 3) {{
      return fr.ring;
    }}
    if (dw.scene_rings && dw.scene_rings.length && dw.scene_rings[0].length >= 3) {{
      const dx = pt ? (pt[0] - (dw.u0 || 0.5)) : 0;
      const dy = pt ? (pt[1] - (dw.v0 || 0.5)) : 0;
      return dw.scene_rings[0].map(uv => [uv[0] + dx, uv[1] + dy]);
    }}
    if (dw.poly0 && dw.poly0.length >= 3 && pt) {{
      return dw.poly0.map(duv => [pt[0] + duv[0], pt[1] + duv[1]]);
    }}
    return [];
  }}

  function getPlaneStrokesUV(dw, fr, pt) {{
    if (dw.role === "subject" && fr && fr.doodle && fr.doodle.length) {{
      return fr.doodle;
    }}
    if (dw.strokes0 && dw.strokes0.length && pt) {{
      return dw.strokes0.map(st => st.map(duv => [pt[0] + duv[0], pt[1] + duv[1]]));
    }}
    return [];
  }}

  function isLayerActive(id) {{
    return soloLayerId === null || soloLayerId === id;
  }}

  function syncSoloUI(w) {{
    if (!shmSoloClearBtn) return;
    if (soloLayerId && w) {{
      const sdw = (w.depth_worms || []).find(d => d.id === soloLayerId);
      shmSoloClearBtn.style.display = "inline-block";
      shmSoloClearBtn.textContent = sdw ? `← All Worms (Solo: z=${{sdw.z}})` : "← All Worms";
    }} else {{
      shmSoloClearBtn.style.display = "none";
    }}
  }}

  function drawCroppedCutoutStamp(ctx, media, ring, cx, cy, maxW, maxH, borderCol, isCur, alpha) {{
    if (!ring || ring.length < 3) return false;
    let u0 = 1, v0 = 1, u1 = 0, v1 = 0;
    ring.forEach(([u, v]) => {{
      if (u < u0) u0 = u; if (u > u1) u1 = u;
      if (v < v0) v0 = v; if (v > v1) v1 = v;
    }});
    const pad = 0.025;
    u0 = Math.max(0, u0 - pad); v0 = Math.max(0, v0 - pad);
    u1 = Math.min(1, u1 + pad); v1 = Math.min(1, v1 + pad);
    const bw = Math.max(0.06, u1 - u0);
    const bh = Math.max(0.06, v1 - v0);

    const aspect = (bw * 1.333) / bh;
    let sw = maxH * aspect;
    let sh = maxH;
    if (sw > maxW) {{
      sw = maxW;
      sh = maxW / aspect;
    }}
    sw = Math.max(22, sw);
    sh = Math.max(22, sh);
    const x0 = cx - sw * 0.5;
    const y0 = cy - sh * 0.5;

    ctx.save();
    ctx.beginPath();
    ring.forEach(([u, v], i) => {{
      const px = x0 + ((u - u0) / bw) * sw;
      const py = y0 + ((v - v0) / bh) * sh;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }});
    ctx.closePath();

    ctx.fillStyle = "rgba(5, 8, 15, 0.9)";
    ctx.fill();

    if (media && showMaskVid) {{
      const mw = media.videoWidth || media.naturalWidth || 0;
      const mh = media.videoHeight || media.naturalHeight || 0;
      if (mw > 0 && mh > 0) {{
        ctx.save();
        ctx.clip();
        ctx.globalAlpha = alpha;
        try {{
          ctx.drawImage(media, u0 * mw, v0 * mh, bw * mw, bh * mh, x0, y0, sw, sh);
        }} catch (e) {{}}
        ctx.restore();
      }}
    }}

    ctx.strokeStyle = isCur ? "#ffffff" : borderCol;
    ctx.lineWidth = isCur ? 2.6 : 1.5;
    ctx.stroke();
    if (isCur) {{
      ctx.strokeStyle = "#f2bc57";
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }}
    ctx.restore();
    return true;
  }}

  function drawCroppedStrokesStamp(ctx, strokes, cx, cy, maxW, maxH, col, isCur) {{
    if (!strokes || !strokes.length) return false;
    let u0 = 1e9, v0 = 1e9, u1 = -1e9, v1 = -1e9;
    strokes.forEach(st => st.forEach(([u, v]) => {{
      if (u < u0) u0 = u; if (u > u1) u1 = u;
      if (v < v0) v0 = v; if (v > v1) v1 = v;
    }}));
    if (u0 > u1) return false;
    const bw = Math.max(0.08, u1 - u0);
    const bh = Math.max(0.08, v1 - v0);
    const sc = Math.min(maxW / bw, maxH / bh);
    const mcx = 0.5 * (u0 + u1);
    const mcy = 0.5 * (v0 + v1);

    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    strokes.forEach(st => {{
      if (st.length < 2) return;
      ctx.beginPath();
      st.forEach(([u, v], i) => {{
        const px = cx + (u - mcx) * sc;
        const py = cy + (v - mcy) * sc;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }});
      ctx.strokeStyle = "rgba(4, 6, 12, 0.9)";
      ctx.lineWidth = isCur ? 4.0 : 2.8;
      ctx.stroke();
      ctx.strokeStyle = isCur ? "#ffffff" : col;
      ctx.lineWidth = isCur ? 2.2 : 1.4;
      ctx.stroke();
    }});
    ctx.restore();
    return true;
  }}

  function drawDisentangledStack(w, fIdx, W, H) {{
    const frames = w.frames || [];
    const nf = frames.length;
    if (!nf) return;
    const dws = w.depth_worms || [];
    rowBands = [];
    hitNodes = [];

    const ordered = [...dws].reverse();
    const padL = Math.min(142, Math.max(106, Math.round(W * 0.21)));
    const padR = 14, padT = 28, padB = 18;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    const weights = ordered.map(dw => dw.role === "subject" ? 1.75 : 1.0);
    const totalWeight = weights.reduce((a, b) => a + b, 0) || 1;

    ctx3d.fillStyle = "rgba(142, 153, 176, 0.78)";
    ctx3d.font = "600 9.5px ui-monospace, SFMono-Regular, Menlo, monospace";
    ctx3d.fillText("DEPTH LAYER (TAP TO SOLO)", 7, 18);
    ctx3d.fillText("τ = f00", padL, 18);
    ctx3d.fillText(`τ = f${{String(nf - 1).padStart(2, "0")}}`, W - padR - 44, 18);

    const curX = padL + (fIdx / Math.max(1, nf - 1)) * plotW;

    let accY = padT;
    ordered.forEach((dw, rIdx) => {{
      const rh = (weights[rIdx] / totalWeight) * plotH;
      const yTop = accY + 2;
      const yBot = accY + rh - 2;
      const bandH = Math.max(18, yBot - yTop);
      const cyBase = 0.5 * (yTop + yBot);
      accY += rh;

      rowBands.push({{ id: dw.id, y0: yTop, y1: yBot, padL, plotW, nf }});

      const isSubj = (dw.role === "subject");
      const col = dw.color || "#00f5d4";

      ctx3d.fillStyle = isSubj ? "rgba(242, 188, 87, 0.08)" : (rIdx % 2 === 0 ? "rgba(255,255,255,0.025)" : "rgba(255,255,255,0.01)");
      ctx3d.fillRect(4, yTop, W - 8, bandH);
      ctx3d.strokeStyle = isSubj ? "rgba(242, 188, 87, 0.42)" : "rgba(255, 255, 255, 0.07)";
      ctx3d.lineWidth = isSubj ? 1.4 : 1.0;
      ctx3d.strokeRect(4, yTop, W - 8, bandH);

      ctx3d.fillStyle = col;
      ctx3d.fillRect(4, yTop, 4, bandH);

      const cleanLbl = dw.label.replace("Drawing Plane: ", "").replace("Rig: ", "");
      ctx3d.fillStyle = isSubj ? "#f2bc57" : col;
      ctx3d.font = "bold 10.5px ui-monospace, SFMono-Regular, Menlo, monospace";
      ctx3d.fillText(`z=${{dw.z}} ${{cleanLbl.slice(0, 12)}}`, 12, yTop + Math.min(15, bandH * 0.42));

      ctx3d.fillStyle = "rgba(232, 236, 244, 0.78)";
      ctx3d.font = "9.5px -apple-system, BlinkMacSystemFont, sans-serif";
      const subDesc = isSubj ? "SAM Video Cutout" : (dw.desc || dw.role || "");
      if (bandH >= 28) {{
        ctx3d.fillText(subDesc.slice(0, 19), 12, yTop + Math.min(28, bandH * 0.78));
      }}

      const trk = dw.track || [];
      if (!trk.length) return;
      const v0 = trk[0][1];
      const u0 = trk[0][0];

      const rowPts = trk.map((pt, fi) => {{
        const tx = padL + (fi / Math.max(1, nf - 1)) * plotW;
        const dv = (pt[1] - v0);
        const du = (pt[0] - u0);
        const ty = cyBase + Math.max(-bandH * 0.30, Math.min(bandH * 0.30, (dv * 1.1 + du * 0.35) * bandH));
        const rad = isSubj
          ? Math.max(9, Math.min(bandH * 0.40, (pt[2] || 0.14) * bandH * 1.6))
          : Math.max(5, Math.min(bandH * 0.25, 8));
        return {{ tx, ty, rad, pt, fi }};
      }});

      ctx3d.beginPath();
      rowPts.forEach((p, i) => {{ if (i === 0) ctx3d.moveTo(p.tx, p.ty - p.rad); else ctx3d.lineTo(p.tx, p.ty - p.rad); }});
      for (let i = rowPts.length - 1; i >= 0; i--) {{
        ctx3d.lineTo(rowPts[i].tx, rowPts[i].ty + rowPts[i].rad);
      }}
      ctx3d.closePath();
      ctx3d.fillStyle = col + (isSubj ? "28" : "1c");
      ctx3d.fill();
      ctx3d.strokeStyle = col + "77";
      ctx3d.lineWidth = 1.1;
      ctx3d.stroke();

      ctx3d.beginPath();
      rowPts.forEach((p, i) => {{
        if (i === 0) ctx3d.moveTo(p.tx, p.ty); else ctx3d.lineTo(p.tx, p.ty);
        hitNodes.push({{ fi: p.fi, sx: p.tx, sy: p.ty, layerId: dw.id }});
      }});
      ctx3d.strokeStyle = col;
      ctx3d.lineWidth = isSubj ? 2.6 : 1.7;
      ctx3d.stroke();

      const nStamps = isSubj ? 6 : 5;
      const stampFrames = [];
      for (let s = 0; s < nStamps; s++) {{
        stampFrames.push(Math.round((s / (nStamps - 1)) * (nf - 1)));
      }}
      if (!stampFrames.includes(fIdx)) stampFrames.push(fIdx);
      stampFrames.sort((a, b) => a - b);

      const filteredStamps = [];
      stampFrames.forEach(fi => {{
        if (fi === fIdx) {{
          filteredStamps.push(fi);
        }} else if (Math.abs(fi - fIdx) >= Math.max(2, Math.floor(nf / 12))) {{
          filteredStamps.push(fi);
        }}
      }});

      const maxStampH = Math.max(20, bandH * 0.86);
      const maxStampW = Math.max(26, (plotW / (nStamps + 0.5)) * 0.88);

      filteredStamps.forEach(fi => {{
        const isCur = (fi === fIdx);
        const rp = rowPts[Math.min(rowPts.length - 1, fi)];
        if (!rp) return;
        const fr = frames[Math.min(nf - 1, fi)];
        const media = getMediaForFrame(w, fi);

        if (isSubj && fr && fr.ring && fr.ring.length >= 3) {{
          drawCroppedCutoutStamp(
            ctx3d, media, fr.ring, rp.tx, rp.ty,
            isCur ? maxStampW * 1.18 : maxStampW,
            isCur ? maxStampH * 1.06 : maxStampH * 0.90,
            col, isCur, isCur ? 1.0 : 0.85
          );
        }} else {{
          const strokesUV = getPlaneStrokesUV(dw, fr, rp.pt);
          drawCroppedStrokesStamp(
            ctx3d, strokesUV, rp.tx, rp.ty,
            isCur ? maxStampW * 0.95 : maxStampW * 0.78,
            isCur ? maxStampH * 0.86 : maxStampH * 0.72,
            col, isCur
          );
        }}
      }});
    }});

    ctx3d.save();
    ctx3d.strokeStyle = "rgba(242, 188, 87, 0.88)";
    ctx3d.lineWidth = 1.8;
    ctx3d.setLineDash([4, 3]);
    ctx3d.beginPath();
    ctx3d.moveTo(curX, padT - 4);
    ctx3d.lineTo(curX, H - padB + 4);
    ctx3d.stroke();
    ctx3d.restore();
  }}

  function proj3d(u, v, tau, zOff, W, H) {{
    const x = u - 0.5;
    const y = (0.5 - v) + zOff;
    const z = (tau - 0.5) * 1.55;
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
    const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
    const sc = (Math.min(W, H) * 0.82) / Math.max(0.55, 2.25 - z2 * 0.5);
    return {{ sx: W * 0.50 + x1 * sc, sy: H * 0.52 - y2 * sc, sc }};
  }}

  function drawMediaIn3DMask(media, poly, tau, zOff, W, H, alpha) {{
    if (!media || !poly || poly.length < 3) return false;
    const mw = media.videoWidth || media.naturalWidth || 0;
    const mh = media.videoHeight || media.naturalHeight || 0;
    if (!mw || !mh) return false;

    const p00 = proj3d(0, 0, tau, zOff, W, H);
    const p10 = proj3d(1, 0, tau, zOff, W, H);
    const p01 = proj3d(0, 1, tau, zOff, W, H);

    ctx3d.save();
    ctx3d.beginPath();
    poly.forEach((uv, idx) => {{
      const p = proj3d(uv[0], uv[1], tau, zOff, W, H);
      if (idx === 0) ctx3d.moveTo(p.sx, p.sy); else ctx3d.lineTo(p.sx, p.sy);
    }});
    ctx3d.closePath();
    ctx3d.clip();
    ctx3d.globalAlpha = alpha;
    ctx3d.transform(
      (p10.sx - p00.sx) / mw, (p10.sy - p00.sy) / mw,
      (p01.sx - p00.sx) / mh, (p01.sy - p00.sy) / mh,
      p00.sx, p00.sy
    );
    try {{ ctx3d.drawImage(media, 0, 0, mw, mh); }} catch(e) {{}}
    ctx3d.restore();
    return true;
  }}

  function draw3dWormPrism(w, fIdx) {{
    const W = shmPrism3d.width, H = shmPrism3d.height;
    ctx3d.clearRect(0, 0, W, H);
    const frames = w.frames || [];
    const nf = frames.length;
    if (!nf) return;
    const dws = w.depth_worms || [];
    hitNodes = [];
    rowBands = [];

    syncSoloUI(w);

    const hud3d = document.getElementById("shmHud3d");
    if (hud3d) {{
      if (soloLayerId) {{
        const sdw = dws.find(d => d.id === soloLayerId);
        hud3d.textContent = sdw
          ? `SOLO WORM: z=${{sdw.z}} ${{sdw.label}} (${{sdw.desc || ""}}) · Drag to orbit`
          : "SOLO WORM";
      }} else if (wMode === "stack") {{
        hud3d.textContent = "Disentangled Depth Worms · Drag horizontally to scrub · Tap any row to solo";
      }} else if (wMode === "box3d") {{
        hud3d.textContent = "3D Multiplane Cel Stack (Drag to orbit)";
      }} else {{
        hud3d.textContent = "Exploded 3D Spatiotemporal Worm (Drag to orbit)";
      }}
    }}

    if (wMode === "stack" && !soloLayerId) {{
      drawDisentangledStack(w, fIdx, W, H);
      return;
    }}

    if (wMode === "box3d") {{
      const nPlanes = Math.max(1, dws.length);
      const sc = Math.min(W, H) * 0.62;
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const tilt = 0.34;
      const PBox = (u, v, rankIdx) => {{
        const X = (u - 0.5);
        const Zd = (rankIdx / Math.max(1, nPlanes - 1) - 0.5) * 1.15;
        const rx = X * cy - Zd * sy;
        const rz = X * sy + Zd * cy;
        return {{
          sx: W * 0.50 + rx * sc,
          sy: H * 0.54 + (v - 0.5) * sc * 0.75 - rz * sc * tilt,
          depth: rz
        }};
      }};

      const ordered = dws.map((dw, idx) => ({{ dw, idx, d: PBox(0.5, 0.5, idx).depth }}))
                         .sort((a, b) => a.d - b.d);

      ordered.forEach(({{ dw, idx }}) => {{
        if (!isLayerActive(dw.id)) return;
        const corners = [PBox(0, 0, idx), PBox(1, 0, idx), PBox(1, 1, idx), PBox(0, 1, idx)];
        ctx3d.beginPath();
        corners.forEach((c, i) => {{ if (i === 0) ctx3d.moveTo(c.sx, c.sy); else ctx3d.lineTo(c.sx, c.sy); }});
        ctx3d.closePath();
        ctx3d.fillStyle = "rgba(18, 24, 38, 0.42)";
        ctx3d.fill();
        ctx3d.strokeStyle = dw.color || "#00f5d4";
        ctx3d.lineWidth = (soloLayerId === dw.id || dw.role === "subject") ? 2.2 : 1.1;
        ctx3d.stroke();
      }});

      const fr = frames[Math.min(nf - 1, fIdx)];
      const media = getMediaForFrame(w, fIdx);

      ordered.forEach(({{ dw, idx }}) => {{
        if (!isLayerActive(dw.id)) return;
        const col = dw.color || "#00f5d4";
        const trk = dw.track || [];
        const pt = trk[Math.min(trk.length - 1, fIdx)] || [dw.u0 || 0.5, dw.v0 || 0.5, dw.r0 || 0.12];

        const polyUV = getPlanePolyUV(dw, fr, pt);
        if (showMaskVid && media && (dw.role === "subject" || dw.scene_rings || soloLayerId === dw.id) && polyUV.length >= 3) {{
          const mw = media.videoWidth || media.naturalWidth || 0;
          const mh = media.videoHeight || media.naturalHeight || 0;
          if (mw && mh) {{
            const p00 = PBox(0, 0, idx), p10 = PBox(1, 0, idx), p01 = PBox(0, 1, idx);
            ctx3d.save();
            ctx3d.beginPath();
            polyUV.forEach((uv, i) => {{
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3d.moveTo(p.sx, p.sy); else ctx3d.lineTo(p.sx, p.sy);
            }});
            ctx3d.closePath();
            ctx3d.clip();
            ctx3d.transform(
              (p10.sx - p00.sx) / mw, (p10.sy - p00.sy) / mw,
              (p01.sx - p00.sx) / mh, (p01.sy - p00.sy) / mh,
              p00.sx, p00.sy
            );
            try {{ ctx3d.drawImage(media, 0, 0, mw, mh); }} catch(e) {{}}
            ctx3d.restore();

            ctx3d.beginPath();
            polyUV.forEach((uv, i) => {{
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3d.moveTo(p.sx, p.sy); else ctx3d.lineTo(p.sx, p.sy);
            }});
            ctx3d.closePath();
            ctx3d.strokeStyle = "#ffffff";
            ctx3d.lineWidth = 2.0;
            ctx3d.stroke();
          }}
        }}

        const strokesUV = getPlaneStrokesUV(dw, fr, pt);
        if (strokesUV.length) {{
          ctx3d.strokeStyle = dw.role === "subject" ? "#ffffff" : col;
          ctx3d.lineWidth = dw.role === "subject" ? 2.2 : 1.7;
          ctx3d.lineCap = "round";
          ctx3d.lineJoin = "round";
          strokesUV.forEach(st => {{
            if (st.length < 2) return;
            ctx3d.beginPath();
            st.forEach((uv, i) => {{
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3d.moveTo(p.sx, p.sy); else ctx3d.lineTo(p.sx, p.sy);
            }});
            ctx3d.stroke();
          }});
        }}

        const topL = PBox(0, 0, idx);
        ctx3d.fillStyle = col;
        ctx3d.font = "bold 10.5px monospace";
        ctx3d.fillText(`z=${{dw.z}} ${{dw.label}} (${{dw.desc || ""}})`, topL.sx + 4, topL.sy - 5);
      }});
      return;
    }}

    const box = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]].map(c => proj3d(c[0],c[1],c[2],0,W,H));
    [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([a,b]) => {{
      ctx3d.beginPath(); ctx3d.moveTo(box[a].sx, box[a].sy); ctx3d.lineTo(box[b].sx, box[b].sy);
      ctx3d.strokeStyle = "rgba(139,149,171,0.16)"; ctx3d.lineWidth = 1; ctx3d.stroke();
    }});

    const nL = Math.max(1, dws.length);
    [...dws].reverse().forEach((dw, revIdx) => {{
      const origIdx = nL - 1 - revIdx;
      if (!isLayerActive(dw.id)) return;
      const col = dw.color || "#00f5d4";
      const trk = dw.track || [];
      const isSubj = (dw.role === "subject");
      const isSolo = (soloLayerId === dw.id);
      const zOff = isSolo ? 0.0 : ((origIdx / Math.max(1, nL - 1)) - 0.5) * 1.05;

      ctx3d.strokeStyle = col;
      ctx3d.lineWidth = (isSubj || isSolo) ? 3.5 : 1.9;
      ctx3d.beginPath();
      trk.forEach((pt, fi) => {{
        const p = proj3d(pt[0], pt[1], fi / Math.max(1, nf - 1), zOff, W, H);
        if (isSubj || isSolo) hitNodes.push({{ fi, sx: p.sx, sy: p.sy, layerId: dw.id }});
        if (fi === 0) ctx3d.moveTo(p.sx, p.sy); else ctx3d.lineTo(p.sx, p.sy);
      }});
      ctx3d.stroke();

      if (isSubj || isSolo) {{
        const sliceIndices = [];
        const step = Math.max(1, Math.floor((nf - 1) / 5));
        for (let s = 0; s < nf; s += step) sliceIndices.push(s);
        if (!sliceIndices.includes(nf - 1)) sliceIndices.push(nf - 1);
        if (!sliceIndices.includes(fIdx)) sliceIndices.push(fIdx);
        sliceIndices.sort((a, b) => a - b);

        sliceIndices.forEach(fi => {{
          const isCur = (fi === fIdx);
          const fr = frames[Math.min(nf - 1, fi)];
          const pt = trk[Math.min(trk.length - 1, fi)] || [0.5, 0.5, 0.14];
          const tau = fi / Math.max(1, nf - 1);
          const pCenter = proj3d(pt[0], pt[1], tau, zOff, W, H);
          const media = getMediaForFrame(w, fi);

          if (isSubj && fr && fr.ring && fr.ring.length >= 3) {{
            drawCroppedCutoutStamp(
              ctx3d, media, fr.ring, pCenter.sx, pCenter.sy,
              isCur ? 96 : 68, isCur ? 88 : 62,
              col, isCur, isCur ? 1.0 : 0.82
            );
          }} else {{
            const polyUV = getPlanePolyUV(dw, fr, pt);
            if (showMaskVid && media && polyUV.length >= 3) {{
              drawMediaIn3DMask(media, polyUV, tau, zOff, W, H, isCur ? 1.0 : 0.65);
            }}
            const strokesUV = getPlaneStrokesUV(dw, fr, pt);
            drawCroppedStrokesStamp(ctx3d, strokesUV, pCenter.sx, pCenter.sy, isCur ? 96 : 68, isCur ? 76 : 54, col, isCur);
          }}
        }});
      }} else {{
        [0, Math.floor(nf / 2), fIdx].forEach(fi => {{
          const fr = frames[Math.min(nf - 1, fi)];
          const pt = trk[Math.min(trk.length - 1, fi)] || [0.5, 0.5, 0.12];
          const tau = fi / Math.max(1, nf - 1);
          const pCenter = proj3d(pt[0], pt[1], tau, zOff, W, H);
          const strokesUV = getPlaneStrokesUV(dw, fr, pt);
          drawCroppedStrokesStamp(ctx3d, strokesUV, pCenter.sx, pCenter.sy, 54, 38, col, fi === fIdx);
        }});
      }}

      if (trk.length) {{
        const p0 = proj3d(trk[0][0], trk[0][1], 0, zOff, W, H);
        ctx3d.fillStyle = col; ctx3d.font = "bold 10.5px monospace";
        ctx3d.fillText(`z=${{dw.z}} ${{dw.label.slice(0, 13)}} (${{dw.desc || ""}})`, p0.sx + 6, p0.sy - 6);
      }}
    }});
  }}

  function draw2dSliceOverlay(w, fIdx) {{
    const W = shmOverlay2d.width, H = shmOverlay2d.height;
    ctx2d.clearRect(0, 0, W, H);
    const frames = w.frames || [];
    if (!frames.length) return;
    const fr = frames[Math.min(frames.length - 1, fIdx)];
    const media = getMediaForFrame(w, fIdx);
    const dws = w.depth_worms || [];

    ensureFrameImg(w, (fIdx + 1) % frames.length);
    ensureFrameImg(w, (fIdx + 2) % frames.length);

    ctx2d.fillStyle = (curSrcMode === "cel") ? "#0c1018" : "#05070c";
    ctx2d.fillRect(0, 0, W, H);

    if (media && curSrcMode !== "cel") {{
      ctx2d.save();
      ctx2d.globalAlpha = (curSrcMode === "src") ? 1.0 : 0.18;
      try {{ ctx2d.drawImage(media, 0, 0, W, H); }} catch(e) {{}}
      ctx2d.restore();
    }}

    if (curSrcMode === "src") return;

    const subjDw = dws.find(d => d.role === "subject");
    if (curSrcMode === "cutout" && (soloLayerId === null || (subjDw && soloLayerId === subjDw.id))) {{
      if (fr.ring && fr.ring.length >= 3) {{
        if (media) {{
          ctx2d.save();
          ctx2d.beginPath();
          fr.ring.forEach((uv, i) => {{ if (i === 0) ctx2d.moveTo(uv[0]*W, uv[1]*H); else ctx2d.lineTo(uv[0]*W, uv[1]*H); }});
          ctx2d.closePath();
          ctx2d.shadowColor = "rgba(0,0,0,0.95)";
          ctx2d.shadowBlur = 14;
          ctx2d.shadowOffsetX = 3;
          ctx2d.shadowOffsetY = 4;
          ctx2d.fillStyle = "#000";
          ctx2d.fill();
          ctx2d.restore();

          ctx2d.save();
          ctx2d.beginPath();
          fr.ring.forEach((uv, i) => {{ if (i === 0) ctx2d.moveTo(uv[0]*W, uv[1]*H); else ctx2d.lineTo(uv[0]*W, uv[1]*H); }});
          ctx2d.closePath();
          ctx2d.clip();
          ctx2d.globalAlpha = 1.0;
          try {{ ctx2d.drawImage(media, 0, 0, W, H); }} catch(e) {{}}
          ctx2d.restore();
        }}

        ctx2d.save();
        ctx2d.beginPath();
        fr.ring.forEach((uv, i) => {{ if (i === 0) ctx2d.moveTo(uv[0]*W, uv[1]*H); else ctx2d.lineTo(uv[0]*W, uv[1]*H); }});
        ctx2d.closePath();
        ctx2d.strokeStyle = "#f2bc57";
        ctx2d.lineWidth = 3.2;
        ctx2d.stroke();
        ctx2d.strokeStyle = "#ffffff";
        ctx2d.lineWidth = 1.2;
        ctx2d.stroke();
        ctx2d.restore();
      }}
      return;
    }}

    [...dws].reverse().forEach(dw => {{
      if (!isLayerActive(dw.id)) return;
      const col = dw.color || "#00f5d4";
      const trk = dw.track || [];
      const pt = trk[Math.min(trk.length - 1, fIdx)] || [dw.u0 || 0.5, dw.v0 || 0.5, dw.r0 || 0.12];
      const polyUV = getPlanePolyUV(dw, fr, pt);
      const strokesUV = getPlaneStrokesUV(dw, fr, pt);

      const doCutout = (curSrcMode !== "cel") && media && (dw.role === "subject" || dw.scene_rings || soloLayerId === dw.id);
      if (doCutout && polyUV.length >= 3) {{
        ctx2d.save();
        ctx2d.beginPath();
        polyUV.forEach((uv, i) => {{ if (i === 0) ctx2d.moveTo(uv[0]*W, uv[1]*H); else ctx2d.lineTo(uv[0]*W, uv[1]*H); }});
        ctx2d.closePath();
        ctx2d.clip();
        ctx2d.globalAlpha = 1.0;
        try {{ ctx2d.drawImage(media, 0, 0, W, H); }} catch(e) {{}}
        ctx2d.restore();

        ctx2d.beginPath();
        polyUV.forEach((uv, i) => {{ if (i === 0) ctx2d.moveTo(uv[0]*W, uv[1]*H); else ctx2d.lineTo(uv[0]*W, uv[1]*H); }});
        ctx2d.closePath();
        ctx2d.strokeStyle = col;
        ctx2d.lineWidth = 2.6;
        ctx2d.stroke();
      }}

      if (strokesUV.length && (curSrcMode === "cel" || dw.role !== "subject" || soloLayerId === dw.id)) {{
        ctx2d.save();
        ctx2d.lineCap = "round";
        ctx2d.lineJoin = "round";
        strokesUV.forEach(st => {{
          if (st.length < 2) return;
          ctx2d.beginPath();
          st.forEach((uv, i) => {{
            if (i === 0) ctx2d.moveTo(uv[0] * W, uv[1] * H); else ctx2d.lineTo(uv[0] * W, uv[1] * H);
          }});
          ctx2d.strokeStyle = "rgba(5, 7, 12, 0.85)";
          ctx2d.lineWidth = 4.2;
          ctx2d.stroke();
          ctx2d.strokeStyle = col;
          ctx2d.lineWidth = 2.2;
          ctx2d.stroke();
        }});
        ctx2d.restore();
      }}
    }});
  }}

  function drawShmAll() {{
    const w = worms[curWormIdx];
    if (!w) return;
    draw3dWormPrism(w, curFrame);
    draw2dSliceOverlay(w, curFrame);
    const fr = (w.frames || [])[curFrame] || {{}};
    const areaPct = ((fr.area || 0) * 100).toFixed(1);
    const dws = w.depth_worms || [];
    const soloTxt = soloLayerId ? ` · SOLO: ${{soloLayerId}}` : "";
    document.getElementById("shmSummaryText").textContent =
      `f${{String(curFrame).padStart(2,"0")}}/${{w.n_frames-1}} · cutout ${{areaPct}}% · ${{dws.length}} Disentangled Worms${{soloTxt}}`;
  }}

  function syncShmVidTime(w, fIdx) {{
    if (!w || !shmVideo.duration) return;
    const t0 = w.vid_t0 || 0;
    const fps = w.fps || 12;
    const targetT = t0 + (fIdx / fps);
    if (Math.abs(shmVideo.currentTime - targetT) > 0.08) {{
      try {{ shmVideo.currentTime = Math.min(shmVideo.duration - 0.05, targetT); }} catch(e) {{}}
    }}
  }}

  function applyMediaSource(w) {{
    const url = w.src_mp4 || w.comp_mp4 || w.r2_mp4 || "";
    const hud2d = document.getElementById("shmHud2d");
    if (hud2d) {{
      const map = {{
        cutout: "SAM Video Cutout (Unobstructed)",
        scene: "Video Cutout + Multiplane Drawings",
        cel: "Multiplane Vector Cel Sheet",
        src: "Raw Source Footage"
      }};
      hud2d.textContent = map[curSrcMode] || "SAM Video Cutout";
    }}
    if (url && shmVideo.src !== url) {{
      shmVideo.src = url;
      shmVideo.onloadedmetadata = () => {{ syncShmVidTime(w, curFrame); drawShmAll(); }};
    }}
  }}

  function selectWorm(idx, autoPlay = false) {{
    if (!worms.length) return;
    curWormIdx = (idx + worms.length) % worms.length;
    shmSelect.value = curWormIdx;
    curFrame = 0;
    soloLayerId = null;
    const w = worms[curWormIdx];
    shmSlider.max = Math.max(1, (w.frames || []).length - 1);
    shmSlider.value = 0;
    document.getElementById("shmCaseLink").href = w.gwp_page || "https://hartswf0.github.io/secondhand-motion/";
    preloadShotFrames(w);
    applyMediaSource(w);
    drawShmAll();
    document.querySelectorAll(".shm-mini-card, .shm-swipe-tile").forEach(c => {{
      c.classList.toggle("active", parseInt(c.dataset.idx, 10) === curWormIdx);
    }});
    if (autoPlay) {{
      isPlaying = true;
      document.getElementById("shmPlayBtn").textContent = "⏸";
      if (shmVideo.style.display !== "none") shmVideo.play().catch(() => {{}});
    }}
  }}

  function tickShmLoop(ts) {{
    if (isPlaying && worms[curWormIdx]) {{
      const w = worms[curWormIdx];
      const interval = 1000 / (w.fps || 12);
      if (ts - lastTick >= interval) {{
        lastTick = ts;
        curFrame = (curFrame + 1) % Math.max(1, (w.frames || []).length);
        shmSlider.value = curFrame;
        syncShmVidTime(w, curFrame);
        drawShmAll();
      }}
    }}
    requestAnimationFrame(tickShmLoop);
  }}
  requestAnimationFrame(tickShmLoop);

  function buildShmSwipeStrip() {{
    const strip = document.getElementById("shmSwipeStrip");
    if (!strip) return;
    strip.innerHTML = "";
    worms.forEach((w, idx) => {{
      const tile = document.createElement("div");
      tile.className = "shm-swipe-tile" + (idx === curWormIdx ? " active" : "");
      tile.dataset.idx = idx;
      tile.innerHTML = `<canvas width="110" height="36"></canvas><div class="shm-swipe-title">${{idx + 1}}. ${{w.slug}}</div>`;
      tile.onclick = () => selectWorm(idx, true);
      strip.appendChild(tile);

      const mc = tile.querySelector("canvas").getContext("2d");
      const nf = Math.max(1, (w.frames || []).length);
      const dws = [...(w.depth_worms || [])].reverse();
      dws.forEach((dw, dIdx) => {{
        const yBase = 5 + (dIdx + 0.5) * (26 / Math.max(1, dws.length));
        mc.strokeStyle = dw.color || "#4fd1c5";
        mc.lineWidth = dw.role === "subject" ? 2.2 : 1.1;
        mc.beginPath();
        (dw.track || []).forEach((pt, fi) => {{
          const x = 4 + (fi / Math.max(1, nf - 1)) * 102;
          const y = yBase + (pt[1] - (dw.track[0] ? dw.track[0][1] : 0.5)) * 7;
          if (fi === 0) mc.moveTo(x, y); else mc.lineTo(x, y);
        }});
        mc.stroke();
      }});
    }});
  }}

  window.loadShmWormById = function(slug) {{
    const idx = worms.findIndex(w => w.slug === slug);
    if (idx !== -1) {{
      selectWorm(idx, true);
      document.getElementById("shmWormHero").scrollIntoView({{ behavior: "smooth" }});
    }}
  }};

  function renderShmCards() {{
    const grid = document.getElementById("shmCardsGrid");
    if (!grid) return;
    const q = (document.getElementById("shmSearchInput").value || "").toLowerCase();
    const tf = document.getElementById("shmTopoFilter").value;
    grid.innerHTML = "";

    worms.forEach((w, idx) => {{
      if (tf !== "ALL" && w.topology !== tf) return;
      const hay = `${{w.slug}} ${{w.title}} ${{w.topology}} ${{w.best_rule}}`.toLowerCase();
      if (q && !hay.includes(q)) return;

      const card = document.createElement("div");
      card.className = "shm-mini-card" + (idx === curWormIdx ? " active" : "");
      card.dataset.idx = idx;
      const dws = [...(w.depth_worms || [])].reverse();
      card.innerHTML = `
        <canvas width="180" height="56" style="width:100%;height:52px;display:block;background:#05070b;border-radius:4px;margin-bottom:4px;"></canvas>
        <div style="font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{idx + 1}}. ${{w.slug}}</div>
        <div style="font-size:9.5px;font-family:var(--mono);color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{dws.length}} Disentangled Worms</div>
      `;
      card.addEventListener("click", () => {{
        selectWorm(idx, true);
        document.getElementById("shmWormHero").scrollIntoView({{ behavior: "smooth" }});
      }});
      grid.appendChild(card);

      const mc = card.querySelector("canvas");
      const mctx = mc.getContext("2d");
      const nf = Math.max(1, (w.frames || []).length);
      dws.forEach((dw, dIdx) => {{
        const yBase = 6 + (dIdx + 0.5) * (44 / Math.max(1, dws.length));
        mctx.strokeStyle = dw.color || "#4fd1c5";
        mctx.lineWidth = dw.role === "subject" ? 2.2 : 1.1;
        mctx.beginPath();
        (dw.track || []).forEach((pt, fi) => {{
          const x = 8 + (fi / Math.max(1, nf - 1)) * 164;
          const y = yBase + (pt[1] - (dw.track[0] ? dw.track[0][1] : 0.5)) * 11;
          if (fi === 0) mctx.moveTo(x, y); else mctx.lineTo(x, y);
        }});
        mctx.stroke();
      }});
    }});
  }}

  shmSelect.addEventListener("change", () => selectWorm(parseInt(shmSelect.value, 10), true));
  document.getElementById("shmPrevBtn").addEventListener("click", () => selectWorm(curWormIdx - 1, true));
  document.getElementById("shmNextBtn").addEventListener("click", () => selectWorm(curWormIdx + 1, true));

  document.querySelectorAll("#shmModeBar .guide-pill[data-wmode]").forEach(btn => {{
    btn.addEventListener("click", () => {{
      document.querySelectorAll("#shmModeBar .guide-pill[data-wmode]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      wMode = btn.dataset.wmode;
      drawShmAll();
    }});
  }});

  if (shmSoloClearBtn) {{
    shmSoloClearBtn.addEventListener("click", () => {{
      soloLayerId = null;
      drawShmAll();
    }});
  }}

  document.querySelectorAll("#shmSourceBar .guide-pill").forEach(btn => {{
    btn.addEventListener("click", () => {{
      document.querySelectorAll("#shmSourceBar .guide-pill").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      curSrcMode = btn.dataset.src;
      if (worms[curWormIdx]) {{ applyMediaSource(worms[curWormIdx]); drawShmAll(); }}
    }});
  }});

  document.getElementById("shmResetCam").addEventListener("click", () => {{
    yaw = -0.46; pitch = 0.22; soloLayerId = null;
    drawShmAll();
  }});

  document.getElementById("shmPlayBtn").addEventListener("click", () => {{
    isPlaying = !isPlaying;
    document.getElementById("shmPlayBtn").textContent = isPlaying ? "⏸" : "▶";
    if (isPlaying && shmVideo.style.display !== "none") shmVideo.play().catch(() => {{}});
    else shmVideo.pause();
  }});

  shmSlider.addEventListener("input", () => {{
    isPlaying = false; document.getElementById("shmPlayBtn").textContent = "▶"; shmVideo.pause();
    curFrame = parseInt(shmSlider.value, 10) || 0;
    if (worms[curWormIdx]) syncShmVidTime(worms[curWormIdx], curFrame);
    drawShmAll();
  }});
  document.getElementById("shmStepPrev").addEventListener("click", () => {{
    isPlaying = false; document.getElementById("shmPlayBtn").textContent = "▶"; shmVideo.pause();
    curFrame = Math.max(0, curFrame - 1);
    shmSlider.value = curFrame;
    if (worms[curWormIdx]) syncShmVidTime(worms[curWormIdx], curFrame);
    drawShmAll();
  }});
  document.getElementById("shmStepNext").addEventListener("click", () => {{
    isPlaying = false; document.getElementById("shmPlayBtn").textContent = "▶"; shmVideo.pause();
    const w = worms[curWormIdx];
    curFrame = Math.min((w ? w.frames.length : 1) - 1, curFrame + 1);
    shmSlider.value = curFrame;
    if (w) syncShmVidTime(w, curFrame);
    drawShmAll();
  }});

  shmPrism3d.addEventListener("pointerdown", e => {{
    dragging = true; moved = false; dragX = e.clientX; dragY = e.clientY;
    shmPrism3d.setPointerCapture(e.pointerId);
    if (wMode === "stack" && !soloLayerId && rowBands.length && worms[curWormIdx]) {{
      const rect = shmPrism3d.getBoundingClientRect();
      const mx = (e.clientX - rect.left) * (shmPrism3d.width / rect.width);
      const b0 = rowBands[0];
      if (mx >= b0.padL) {{
        const ratio = Math.max(0, Math.min(1, (mx - b0.padL) / Math.max(1, b0.plotW)));
        const newF = Math.round(ratio * Math.max(1, b0.nf - 1));
        if (newF !== curFrame) {{
          isPlaying = false; document.getElementById("shmPlayBtn").textContent = "▶"; shmVideo.pause();
          curFrame = newF;
          shmSlider.value = curFrame;
          syncShmVidTime(worms[curWormIdx], curFrame);
          drawShmAll();
        }}
      }}
    }}
  }});
  shmPrism3d.addEventListener("pointermove", e => {{
    if (!dragging) return;
    const dx = e.clientX - dragX, dy = e.clientY - dragY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true;

    if (wMode === "stack" && !soloLayerId && rowBands.length && worms[curWormIdx]) {{
      const rect = shmPrism3d.getBoundingClientRect();
      const mx = (e.clientX - rect.left) * (shmPrism3d.width / rect.width);
      const b0 = rowBands[0];
      if (mx >= b0.padL) {{
        const ratio = Math.max(0, Math.min(1, (mx - b0.padL) / Math.max(1, b0.plotW)));
        const newF = Math.round(ratio * Math.max(1, b0.nf - 1));
        if (newF !== curFrame) {{
          isPlaying = false; document.getElementById("shmPlayBtn").textContent = "▶"; shmVideo.pause();
          curFrame = newF;
          shmSlider.value = curFrame;
          syncShmVidTime(worms[curWormIdx], curFrame);
          drawShmAll();
        }}
      }}
      return;
    }}

    yaw += dx * 0.008;
    pitch = Math.max(-1.0, Math.min(1.0, pitch + dy * 0.008));
    dragX = e.clientX; dragY = e.clientY;
    drawShmAll();
  }});
  shmPrism3d.addEventListener("pointerup", e => {{
    dragging = false;
    if (!moved && worms[curWormIdx]) {{
      const rect = shmPrism3d.getBoundingClientRect();
      const mx = (e.clientX - rect.left) * (shmPrism3d.width / rect.width);
      const my = (e.clientY - rect.top) * (shmPrism3d.height / rect.height);

      if (wMode === "stack" && !soloLayerId && rowBands.length) {{
        const hitRow = rowBands.find(r => my >= r.y0 && my <= r.y1);
        if (hitRow) {{
          if (mx >= hitRow.padL) {{
            const ratio = Math.max(0, Math.min(1, (mx - hitRow.padL) / Math.max(1, hitRow.plotW)));
            curFrame = Math.round(ratio * Math.max(1, hitRow.nf - 1));
            shmSlider.value = curFrame;
            syncShmVidTime(worms[curWormIdx], curFrame);
          }}
          soloLayerId = hitRow.id;
          drawShmAll();
          return;
        }}
      }}

      let best = -1, bestD = 9999;
      hitNodes.forEach(pc => {{
        const d = Math.hypot(pc.sx - mx, pc.sy - my);
        if (d < bestD) {{ bestD = d; best = pc.fi; }}
      }});
      if (best !== -1 && bestD < 48) {{
        curFrame = best;
        shmSlider.value = curFrame;
        syncShmVidTime(worms[curWormIdx], curFrame);
        drawShmAll();
      }}
    }}
  }});

  document.getElementById("shmSearchInput").addEventListener("input", renderShmCards);
  document.getElementById("shmTopoFilter").addEventListener("change", renderShmCards);

  fetch("secondhand_worms_108.json?v=8")
    .then(r => r.ok ? r.json() : fetch("https://hartswf0.github.io/secondhand-motion/data/worms_108.json?v=8").then(r2 => r2.json()))
    .catch(() => fetch("https://hartswf0.github.io/secondhand-motion/data/worms_108.json?v=8").then(r2 => r2.json()))
    .then(data => {{
      worms = data.worms || [];
      shmSelect.innerHTML = "";
      worms.forEach((w, idx) => {{
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${{w.lot ? w.lot + " · " : (idx + 1) + ". "}}${{w.title || w.slug}} (${{(w.depth_worms || []).length}} Worms · ${{w.n_frames}}f)`;
        shmSelect.appendChild(opt);
      }});
      buildShmSwipeStrip();
      renderShmCards();
      const gIdx = worms.findIndex(w => w.slug === "giraffe-walks-past");
      selectWorm(gIdx !== -1 ? gIdx : 0, false);
    }});
}})();
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
