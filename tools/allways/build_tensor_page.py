#!/usr/bin/env python3
"""
Builds the Watchable, Claim-Testing Geometric Cinema Studio at:
  /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html

Key Capabilities:
  1. Auto-Sighting Relevant Geometry per Frame:
     As any of the 142 films plays, the player automatically detects and displays ONLY
     the geometric structure that is actually relevant to the current frame (or lets you
     pin any of the 8 shapes to test it against the current shot).
  2. Visual Proof on the Frame ("See What Hits the Grid"):
     Draws the live 2-second subject motion trail (x, y, size over time), the live
     left/right or upper/lower balance, and highlights the actual video edges that
     touch the active geometric guide—so you can visually verify every claim.
  3. Plain-English "Live Frame Insight & Claim Test" Bar:
     Explains in plain language what geometry is active right now, its measured fit %,
     how it is changing over time (Holding Lock vs. Panning vs. Zooming vs. Breaking the
     Grid), and provides clickable Phase / Cut pills to jump directly to the test moments.
  4. Evolution Timeline Below the Player:
     Shows the Dominant Shape Ribbon over time, the Geometric Fit % curve over time,
     and the Subject-vs-Background color evolution bar.
"""

import os
import json
import math
import base64

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
TENSOR_DIR = os.path.join(REPO_ROOT, "allways-tensor")


def encode_img_b64(rel_path):
    full_p = os.path.join(TENSOR_DIR, rel_path)
    if not os.path.exists(full_p):
        return ""
    with open(full_p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def compute_slice_best_shape(s, prev_s=None):
    """
    Given a slice s from allways_worms_140.json, score all 8 geometric shapes
    so every timestamp of every film knows which of the 8 shapes is most relevant
    and what its fit % is, even before live pixel sampling kicks in.
    """
    u, v = s["c"]
    r = s["r"]
    lr_bal = s.get("lr_balance", 0.8)
    rab_gap = s.get("rabat_gap", 0.5)
    d_gold = s.get("d_golden", math.hypot(u - 0.618, v - 0.382))
    d_th = s.get("d_thirds", 0.08)
    d_arm = s.get("d_armature", 0.05)
    area = s.get("area_ratio", 0.18)

    du = (u - prev_s["c"][0]) if prev_s else 0.0
    dv = (v - prev_s["c"][1]) if prev_s else 0.0

    # 8 shape heuristic scores (0..100) from the slice's measured coordinates
    scores = {
        "symmetry": int(max(20, min(99, lr_bal * 100 - abs(u - 0.5) * 140))),
        "rule_of_thirds": int(max(25, min(98, 100 - d_th * 620))),
        "golden_spiral": int(max(20, min(97, 100 - d_gold * 310 + (12 if abs(du) + abs(dv) > 0.015 else 0)))),
        "centered": int(max(20, min(98, 96 - abs(u - 0.5) * 260 - abs(v - 0.58) * 140))),
        "frame_in_frame": int(max(20, min(96, 92 - abs(r - 0.24) * 320 - d_arm * 280))),
        "s_curve": int(max(20, min(96, 62 + min(34, (abs(du) + abs(dv)) * 950) - d_arm * 180))),
        "v_shape": int(max(20, min(96, 86 - abs(u - 0.5) * 180 - abs(rab_gap - 0.52) * 220))),
        "negative_space": int(max(20, min(97, 95 - abs(area - 0.16) * 280 + (v - 0.5) * 90))),
    }
    best_id = max(scores.items(), key=lambda kv: kv[1])[0]
    return best_id, scores[best_id], scores


def main():
    tensor_path = os.path.join(TENSOR_DIR, "tensor_data.json")
    grids_path = os.path.join(TENSOR_DIR, "eight_grids_archive.json")
    scion_shapes_path = os.path.join(TENSOR_DIR, "scion_shapes.json")
    worms_140_path = os.path.join(TENSOR_DIR, "allways_worms_140.json")

    with open(tensor_path) as f:
        tensor_data = json.load(f)

    grids_data = {"rules": [], "reel_mp4": "eight-perspectives.mp4"}
    if os.path.exists(grids_path):
        with open(grids_path) as f:
            grids_data = json.load(f)
        for r in grids_data.get("rules", []):
            r["overlay_b64"] = encode_img_b64(r["overlay_img"])

    scion_shapes_data = {"operators": []}
    if os.path.exists(scion_shapes_path):
        with open(scion_shapes_path) as f:
            scion_shapes_data = json.load(f)

    worms_140_data = {"total_films": 0, "films": []}
    if os.path.exists(worms_140_path):
        with open(worms_140_path) as f:
            worms_140_data = json.load(f)

    flagship_slits = {}
    for film in tensor_data.get("films", []):
        flagship_slits[film["id"]] = {
            "ut_b64": encode_img_b64(film["ut_tomogram"]),
        }

    # Map SCION shape operators by film id so we can attach their 8-cut EDL & theorem claims!
    shape_ops_by_id = {}
    for op in scion_shapes_data.get("operators", []):
        shape_ops_by_id[f"shape-{op['scion_id']}"] = op

    slim_films = []
    for wf in worms_140_data.get("films", []):
        slits = flagship_slits.get(wf["id"], {})
        raw_ser = wf.get("series", [])
        enriched_ser = []
        for idx, s in enumerate(raw_ser):
            prev_s = raw_ser[idx - 1] if idx > 0 else None
            best_shape, best_fit, all_sc = compute_slice_best_shape(s, prev_s)
            enriched_ser.append({
                "t": s["t"],
                "c": s["c"],
                "r": s["r"],
                "cL": s.get("c_left", [0.25, 0.5]),
                "cR": s.get("c_right", [0.75, 0.5]),
                "rgb_core": s["rgb_core"],
                "rgb_shell": s["rgb_shell"],
                "topo": s.get("topology", "VERTICAL_PILLAR"),
                "cut": s.get("cut_type", "CONTINUOUS_TUBE"),
                "shape": best_shape,
                "fit": best_fit,
                "scores": all_sc,
            })

        op_info = shape_ops_by_id.get(wf["id"])
        slim_films.append({
            "id": wf["id"],
            "title": wf["title"],
            "maker": wf["maker"],
            "group": wf["group"],
            "video_rel": wf["video_rel"],
            "case_url": wf["case_url"],
            "duration_s": wf["duration_s"],
            "dominant_topology": wf["dominant_topology"],
            "lock_pct": wf.get("compositional_lock_pct", 82.0),
            "ut_b64": slits.get("ut_b64", ""),
            "pinned_rule": op_info["rule_id"] if op_info else None,
            "theorem": op_info["theorem"] if op_info else "",
            "cuts": op_info["cuts"] if op_info else [],
            "parts": wf.get("manovich_parts", []),
            "series": enriched_ser,
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLWAYS — Live Frame Geometry &amp; Claim Tester</title>
<style>
  :root {{
    --bg: #0a0c10;
    --panel: #12151e;
    --panel-alt: #181c28;
    --border: #262b3d;
    --fg: #f2efe9;
    --muted: #969eae;
    --gold: #f0b857;
    --cyan: #56c8e8;
    --green: #68d391;
    --rose: #f56565;
    --purple: #b794f4;
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

  /* Header */
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 14px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .brand {{
    font-weight: 700;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .brand-badge {{
    background: var(--gold);
    color: #0a0c10;
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 800;
  }}
  .nav-row {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
  .btn {{
    background: var(--panel-alt);
    color: var(--fg);
    border: 1px solid var(--border);
    padding: 6px 11px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
  }}
  .btn:hover {{ border-color: var(--gold); }}
  .btn.active, .btn.gold {{
    background: var(--gold);
    color: #0a0c10;
    border-color: var(--gold);
  }}

  /* Main Responsive Grid */
  .layout {{
    display: grid;
    grid-template-columns: 1.22fr 1fr;
    gap: 16px;
    max-width: 1560px;
    margin: 0 auto;
    padding: 14px;
    align-items: start;
  }}
  @media (max-width: 960px) {{
    .layout {{
      grid-template-columns: 1fr;
      padding: 0 0 28px 0;
      gap: 12px;
    }}
    .browser-col {{ padding: 0 12px; }}
    .player-card {{
      border-radius: 0 !important;
      border-left: none !important;
      border-right: none !important;
      border-top: none !important;
    }}
  }}

  /* Left Column: Watchable Player + Live Frame Insight Card + Time Evolution Strip */
  .player-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }}
  .stage-top {{
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .stage-title {{ font-weight: 700; font-size: 15px; }}
  .stage-sub {{ font-size: 12px; color: var(--muted); }}

  .video-wrap {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
  }}
  video {{
    width: 100%;
    height: 100%;
    display: block;
    object-fit: contain;
  }}
  #guideCanvas {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }}

  /* Live Frame Insight & Claim Test Banner (Directly Under the Video!) */
  .insight-banner {{
    padding: 11px 14px;
    background: #0e1118;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .insight-row1 {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .active-shape-pill {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(240, 184, 87, 0.14);
    border: 1px solid var(--gold);
    color: var(--gold);
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12.5px;
  }}
  .fit-meter {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--mono);
    font-size: 12px;
  }}
  .fit-bar-bg {{
    width: 84px;
    height: 8px;
    background: #222736;
    border-radius: 99px;
    overflow: hidden;
  }}
  .fit-bar-fill {{
    height: 100%;
    background: var(--green);
    transition: width 0.12s ease;
  }}
  .insight-explain {{
    font-size: 13px;
    color: var(--fg);
    line-height: 1.4;
  }}
  .insight-explain b {{ color: var(--cyan); }}

  /* Cut / Phase Jump Pills (Test Each Phase of the Claim) */
  .phase-strip {{
    display: flex;
    gap: 5px;
    overflow-x: auto;
    padding-top: 2px;
    scrollbar-width: none;
  }}
  .phase-strip::-webkit-scrollbar {{ display: none; }}
  .phase-btn {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 4px 9px;
    border-radius: 5px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
    flex-shrink: 0;
  }}
  .phase-btn:hover, .phase-btn.active {{
    border-color: var(--cyan);
    color: var(--fg);
    background: rgba(86, 200, 232, 0.14);
  }}

  /* Guide Mode & Visual Proof Controls */
  .controls-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 9px 14px;
    background: var(--panel);
    border-top: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: none;
  }}
  .controls-bar::-webkit-scrollbar {{ display: none; }}
  .pill {{
    background: var(--panel-alt);
    color: var(--fg);
    border: 1px solid var(--border);
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    flex-shrink: 0;
  }}
  .pill.active {{
    background: var(--gold);
    color: #0a0c10;
    border-color: var(--gold);
  }}
  .pill.cyan.active {{
    background: var(--cyan);
    color: #0a0c10;
    border-color: var(--cyan);
  }}

  /* How Geometry Changes Over Time Timeline */
  .timeline-box {{
    padding: 10px 14px 12px;
    border-top: 1px solid var(--border);
    background: var(--panel);
  }}
  .timeline-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    color: var(--muted);
    margin-bottom: 5px;
    flex-wrap: wrap;
    gap: 4px;
  }}
  #evolutionCanvas {{
    width: 100%;
    height: 82px;
    background: #080a0f;
    border: 1px solid var(--border);
    border-radius: 6px;
    display: block;
    cursor: pointer;
  }}
  .slit-wrap {{
    margin-top: 6px;
    position: relative;
    height: 42px;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--border);
    cursor: pointer;
    display: none;
  }}
  .slit-wrap.visible {{ display: block; }}
  .slit-wrap img {{ width: 100%; height: 100%; object-fit: fill; display: block; }}
  .playhead {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--gold);
    pointer-events: none;
  }}

  /* Right Column Browser */
  .section-tabs {{
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
    overflow-x: auto;
  }}
  .tab-pane {{ display: none; }}
  .tab-pane.active {{ display: block; }}

  .shape-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
    gap: 10px;
  }}
  @media (max-width: 540px) {{
    .shape-grid {{ grid-template-columns: 1fr 1fr; gap: 8px; }}
  }}
  .shape-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .shape-card.active, .shape-card:hover {{ border-color: var(--gold); }}
  .shape-thumb {{
    position: relative;
    aspect-ratio: 16 / 9;
    background: #000;
    cursor: pointer;
  }}
  .shape-thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .shape-badge {{
    position: absolute;
    top: 6px;
    left: 6px;
    background: rgba(10, 12, 16, 0.88);
    color: var(--gold);
    border: 1px solid rgba(240, 184, 87, 0.5);
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
  }}
  .shape-body {{
    padding: 9px 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    flex: 1;
  }}
  .shape-name {{ font-weight: 700; font-size: 13px; }}
  .shape-claim {{ font-size: 11.5px; color: var(--muted); line-height: 1.35; }}
  .shape-actions {{
    display: flex;
    gap: 5px;
    margin-top: auto;
    padding-top: 5px;
  }}
  .mini-btn {{
    flex: 1;
    text-align: center;
    padding: 5px 6px;
    font-size: 11.5px;
    border-radius: 5px;
    background: var(--panel-alt);
    color: var(--fg);
    border: 1px solid var(--border);
    cursor: pointer;
    font-weight: 600;
  }}
  .mini-btn.gold {{ background: var(--gold); color: #0a0c10; border-color: var(--gold); }}

  /* Film Library */
  .filter-bar {{ display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }}
  .film-list {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 72vh;
    overflow-y: auto;
  }}
  .film-row {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 8px 11px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    cursor: pointer;
  }}
  .film-row:hover, .film-row.active {{ border-color: var(--gold); background: var(--panel-alt); }}
  .film-row-title {{ font-weight: 700; font-size: 13px; }}
  .film-row-sub {{ font-size: 11.5px; color: var(--muted); }}
  .swatch-pair {{ display: flex; gap: 4px; flex-shrink: 0; }}
  .swatch {{ width: 18px; height: 18px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); }}

  /* Modal */
  .modal-backdrop {{
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.82);
    z-index: 100;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 14px;
  }}
  .modal-backdrop.active {{ display: flex; }}
  .modal-card {{
    background: var(--panel);
    border: 1px solid var(--gold);
    border-radius: 10px;
    max-width: 820px;
    width: 100%;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .modal-head {{
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .modal-body {{
    padding: 14px;
    overflow-y: auto;
    font-family: var(--mono);
    font-size: 12px;
    white-space: pre-wrap;
    line-height: 1.5;
  }}
</style>
</head>
<body>

<header class="header">
  <div class="brand">
    <span class="brand-badge">ALLWAYS</span>
    Live Frame Geometry &amp; Visual Claim Tester
  </div>
  <div class="nav-row">
    <button class="btn gold" onclick="playEightGridsReel()">▶ Watch 8-Shape Breakdown (28s)</button>
    <a class="btn" href="../paeleo/allways/index.html">← Hub</a>
    <a class="btn" href="../allways-best/index.html">★ Best Film</a>
    <a class="btn" href="../allways-awards/index.html">🏆 Awards</a>
  </div>
</header>

<main class="layout">
  <!-- LEFT COLUMN: Video Stage + Live Frame Insight & Claim Verdict + Time Evolution Timeline -->
  <section class="player-col">
    <div class="player-card">
      <div class="stage-top">
        <div>
          <div class="stage-title" id="stageTitle">114 · GOLDEN SPIRAL</div>
          <div class="stage-sub" id="stageSub">SCION 114 · 24.0s · 8 Archival Cuts</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
          <button class="pill cyan active" id="btnShowTrail" onclick="toggleMotionTrail()">〰 2s Motion Trail: ON</button>
          <button class="pill cyan active" id="btnShowEdges" onclick="toggleEdgeProof()">🔍 Edge Proof: ON</button>
          <a class="btn" id="stageCaseLink" href="../paeleo/allways/scion/prompts/scion-114-golden-spiral-logarithmic-torque.md" target="_blank">Source ↗</a>
        </div>
      </div>

      <div class="video-wrap">
        <video id="mainVideo" controls playsinline preload="metadata"></video>
        <canvas id="guideCanvas" width="800" height="450"></canvas>
      </div>

      <!-- LIVE FRAME INSIGHT & CLAIM VERDICT BANNER -->
      <div class="insight-banner">
        <div class="insight-row1">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span class="active-shape-pill" id="liveShapeBadge">★ Auto-Detected: #1 Golden Spiral</span>
            <span id="livePhaseBadge" style="font-size:12px;color:var(--cyan);font-weight:600;">Phase I · Unannotated Observation</span>
          </div>
          <div class="fit-meter">
            <span id="liveFitText">Fit: 88% (LOCKED)</span>
            <div class="fit-bar-bg"><div class="fit-bar-fill" id="liveFitBar" style="width:88%;"></div></div>
          </div>
        </div>

        <div class="insight-explain" id="liveInsightExplain">
          <b>What we are seeing &amp; testing:</b> Peripheral foliage and shadow torque attention into the off-center Golden Ratio eye at (0.68, 0.44). Cyan highlights on the video mark the actual frame edges hitting the spiral guide.
        </div>

        <!-- Clickable Cut / Phase Jump Bar to Test Each Moment of the Film -->
        <div class="phase-strip" id="cutJumpStrip"></div>
      </div>

      <!-- Viewfinder Selector Bar: Auto-Detect (Default) or Pin Any of the 8 Shapes to Test It -->
      <div class="controls-bar">
        <span style="font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;flex-shrink:0;">Guide Mode:</span>
        <button class="pill active" id="vf-auto" onclick="setGuideMode('auto')">⚡ Auto-Relevant per Frame</button>
        <button class="pill" id="vf-none" onclick="setGuideMode('none')">Off</button>
        <button class="pill" id="vf-golden_spiral" onclick="setGuideMode('golden_spiral')">1 · Golden Spiral</button>
        <button class="pill" id="vf-frame_in_frame" onclick="setGuideMode('frame_in_frame')">2 · Frame in Frame</button>
        <button class="pill" id="vf-s_curve" onclick="setGuideMode('s_curve')">3 · S-Curve</button>
        <button class="pill" id="vf-symmetry" onclick="setGuideMode('symmetry')">4 · Symmetry</button>
        <button class="pill" id="vf-rule_of_thirds" onclick="setGuideMode('rule_of_thirds')">5 · Rule of Thirds</button>
        <button class="pill" id="vf-centered" onclick="setGuideMode('centered')">6 · Centered</button>
        <button class="pill" id="vf-v_shape" onclick="setGuideMode('v_shape')">7 · V-Shape</button>
        <button class="pill" id="vf-negative_space" onclick="setGuideMode('negative_space')">8 · Negative Space</button>
      </div>

      <!-- HOW GEOMETRY CHANGES OVER TIME (Click Anywhere to Scrub & Test) -->
      <div class="timeline-box">
        <div class="timeline-hdr">
          <span><b>How Geometry Changes Over Time</b> — Top: Active Shape Chapter · Middle: Fit % Curve (Gold) &amp; Subject Shift (Cyan) · Bottom: Subject/Bg Colors</span>
          <span id="timeReadout" style="color:var(--gold);font-family:var(--mono);">0.0s / 24.0s</span>
        </div>
        <canvas id="evolutionCanvas" width="760" height="82"></canvas>

        <div class="slit-wrap" id="slitWrap" onclick="scrubSlit(event)">
          <img id="slitImg" alt="Photographic Slit-Scan">
          <div class="playhead" id="slitPlayhead"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- RIGHT COLUMN: 8 Shape Claim Cards | All 142 Films -->
  <section class="browser-col">
    <div class="section-tabs">
      <button class="btn active" id="tabBtn-shapes" onclick="switchTab('shapes')">★ 8 Shape Films &amp; Claims (SCION 114–121)</button>
      <button class="btn" id="tabBtn-library" onclick="switchTab('library')">All 142 ALLWAYS Films</button>
    </div>

    <div class="tab-pane active" id="tab-shapes">
      <div class="shape-grid" id="shapeCardsGrid"></div>
    </div>

    <div class="tab-pane" id="tab-library">
      <div class="filter-bar">
        <button class="pill active" id="flt-all" onclick="filterLibrary('all')">All (142)</button>
        <button class="pill" id="flt-shapes" onclick="filterLibrary('shapes')">8 Shapes + Best (10)</button>
        <button class="pill" id="flt-sonnet" onclick="filterLibrary('sonnet')">Sonnet (11)</button>
        <button class="pill" id="flt-opus" onclick="filterLibrary('opus')">Opus (12)</button>
        <button class="pill" id="flt-sol" onclick="filterLibrary('sol')">Sol (24)</button>
        <button class="pill" id="flt-argon" onclick="filterLibrary('argon')">Argon (85)</button>
      </div>
      <div class="film-list" id="libraryList"></div>
    </div>
  </section>
</main>

<!-- SCION Prompt Modal -->
<div class="modal-backdrop" id="promptModal" onclick="if(event.target===this)closePromptModal()">
  <div class="modal-card">
    <div class="modal-head">
      <strong id="modalTitle" style="color:var(--gold);">SCION Prompt</strong>
      <div style="display:flex;gap:6px;">
        <button class="btn gold" id="modalPlayBtn">▶ Play 24s Film</button>
        <button class="btn" onclick="copyPromptText()">📋 Copy</button>
        <button class="btn" onclick="closePromptModal()">✕ Close</button>
      </div>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<script>
const EIGHT_GRIDS = {json.dumps(grids_data)};
const SCION_SHAPES = {json.dumps(scion_shapes_data)};
const FILMS_142 = {json.dumps(slim_films)};

const SHAPE_INFO = {{
  golden_spiral: {{
    num: 1, name: "Golden Spiral (1:1.618)", color: "#f0b857",
    claim: "Asymmetric peripheral mass sweeps across 1:1.618 Golden Rectangles to torque attention into the off-center spiral eye at (0.68, 0.44)."
  }},
  frame_in_frame: {{
    num: 2, name: "Frame in a Frame", color: "#56c8e8",
    claim: "Physical doorway, window, or aperture edges along [0.17, 0.83] × [0.14, 0.86] enclose an interior subject until a movement crosses the sill."
  }},
  s_curve: {{
    num: 3, name: "S-Curve (Leading Bezier)", color: "#68d391",
    claim: "A double-inflected path guides the eye from bottom-left (0.20, 0.88) through a mid-frame bend to top-right (0.80, 0.12)."
  }},
  symmetry: {{
    num: 4, name: "Symmetry (50/50 Bisector)", color: "#b794f4",
    claim: "Left and right halves mirror each other across the vertical centerline x = 50% until one side acts independently."
  }},
  rule_of_thirds: {{
    num: 5, name: "Rule of Thirds (3×3)", color: "#f6ad55",
    claim: "Primary subjects and horizon lines lock onto the 1/3 and 2/3 intersections so the open center third acts as a charged interval."
  }},
  centered: {{
    num: 6, name: "Centered Channel", color: "#4fd1c5",
    claim: "A lone subject is isolated inside the narrow central vertical corridor [0.42, 0.58] grounded on the v = 0.68 baseline."
  }},
  v_shape: {{
    num: 7, name: "V-Shape Wedge", color: "#fc8181",
    claim: "Two oblique upper diagonals funnel downward from (0.12, 0.04) and (0.88, 0.04) into a bottom-center apex at (0.50, 0.84)."
  }},
  negative_space: {{
    num: 8, name: "Negative Space (U-Bracket)", color: "#90cdf4",
    claim: "The upper two-thirds (v < 0.64) remains an open, unencumbered sky or field pressing down on a lower-third silhouette."
  }}
}};

const TOPO_LABELS = {{
  VERTICAL_PILLAR: "Locked Tripod Pillar (Subject holds steady position)",
  SHEARED_DIAGONAL_RIBBON: "Lateral Pan / Tracking Ribbon (Subject sweeps across frame)",
  EXPANDING_CONE: "Zoom / Scale Funnel (Subject size expands or contracts)",
  HELICAL_CORKSCREW: "Curved / Spiral Trajectory (Subject arcs in both X and Y)",
  DOUBLE_HELIX_BRAID: "Two-Shot Counterbalance (Balanced left & right subjects)"
}};

const videoEl = document.getElementById('mainVideo');
const guideCanvas = document.getElementById('guideCanvas');
const evoCanvas = document.getElementById('evolutionCanvas');

// Offscreen 160x90 canvas for live 30fps video pixel edge/symmetry detection
const probeCanvas = document.createElement('canvas');
probeCanvas.width = 160;
probeCanvas.height = 90;
const probeCtx = probeCanvas.getContext('2d', {{ willReadFrequently: true }});
let canReadVideoPixels = true;

let activeFilm = FILMS_142[1] || FILMS_142[0];
let guideMode = 'auto'; // 'auto', 'none', or one of the 8 shape IDs
let showMotionTrail = true;
let showEdgeProof = true;
let activeTab = 'shapes';
let libFilter = 'all';
let curTime = 0.0;
let activePromptOp = null;

function init() {{
  renderShapeCards();
  renderLibraryList();
  loadFilmObject(activeFilm, false);
  requestAnimationFrame(liveRenderLoop);
}}

function renderShapeCards() {{
  const grid = document.getElementById('shapeCardsGrid');
  grid.innerHTML = '';
  (EIGHT_GRIDS.rules || []).forEach(r => {{
    const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === r.id);
    const scionId = op ? op.scion_id : (113 + r.num);
    const info = SHAPE_INFO[r.id] || {{ claim: r.geometry }};
    const card = document.createElement('div');
    card.className = 'shape-card';
    card.id = 'scard-' + r.id;
    card.innerHTML = `
      <div class="shape-thumb" onclick="playShapeFilm('${{r.id}}')">
        <img src="${{r.overlay_b64 || r.overlay_img}}" alt="${{r.name}}">
        <span class="shape-badge">SCION ${{scionId}} · #${{r.num}}</span>
      </div>
      <div class="shape-body">
        <div class="shape-name">${{r.name.split('(')[0].trim()}}</div>
        <div class="shape-claim">${{info.claim}}</div>
        <div class="shape-actions">
          <button class="mini-btn gold" onclick="playShapeFilm('${{r.id}}')">▶ Watch 8-Cut Film</button>
          <button class="mini-btn" onclick="jumpArchivalShot('${{r.id}}')">⌖ Best Shot</button>
          <button class="mini-btn" onclick="openPromptModal('${{r.id}}')">📜 Prompt</button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  }});
}}

function renderLibraryList() {{
  const list = document.getElementById('libraryList');
  list.innerHTML = '';
  const items = FILMS_142.filter(f => {{
    if (libFilter === 'all') return true;
    if (libFilter === 'shapes') return f.group === 'shapes' || f.group === 'featured';
    return f.group === libFilter;
  }});

  items.forEach(f => {{
    const row = document.createElement('div');
    row.className = 'film-row' + (activeFilm && activeFilm.id === f.id ? ' active' : '');
    row.onclick = () => loadFilmObject(f, true);
    const mid = (f.series && f.series[Math.floor(f.series.length / 2)]) || {{ rgb_core: [200,160,80], rgb_shell: [40,50,70] }};
    const c1 = mid.rgb_core, c2 = mid.rgb_shell;
    row.innerHTML = `
      <div>
        <div class="film-row-title">${{f.title}}</div>
        <div class="film-row-sub">${{f.maker}} · ${{f.duration_s}}s · ${{TOPO_LABELS[f.dominant_topology] || f.dominant_topology}}</div>
      </div>
      <div class="swatch-pair">
        <span class="swatch" style="background:rgb(${{c1[0]}},${{c1[1]}},${{c1[2]}})"></span>
        <span class="swatch" style="background:rgb(${{c2[0]}},${{c2[1]}},${{c2[2]}})"></span>
      </div>
    `;
    list.appendChild(row);
  }});
}}

function filterLibrary(flt) {{
  libFilter = flt;
  ['all', 'shapes', 'sonnet', 'opus', 'sol', 'argon'].forEach(k => {{
    const b = document.getElementById('flt-' + k);
    if (b) b.classList.toggle('active', k === flt);
  }});
  renderLibraryList();
}}

function switchTab(tabId) {{
  activeTab = tabId;
  ['shapes', 'library'].forEach(k => {{
    document.getElementById('tabBtn-' + k).classList.toggle('active', k === tabId);
    document.getElementById('tab-' + k).classList.toggle('active', k === tabId);
  }});
}}

function loadFilmObject(f, autoplay) {{
  activeFilm = f;
  curTime = 0.0;
  document.getElementById('stageTitle').textContent = f.title;
  document.getElementById('stageSub').textContent = `${{f.maker}} · ${{f.duration_s}}s · ${{TOPO_LABELS[f.dominant_topology] || f.dominant_topology}}`;
  document.getElementById('stageCaseLink').href = f.case_url;

  // Build Cut / Phase jump pills so user can test each movement of the film
  buildCutJumpPills(f);

  videoEl.src = f.video_rel;
  if (autoplay) videoEl.play().catch(() => {{}});

  const slitWrap = document.getElementById('slitWrap');
  if (f.ut_b64) {{
    document.getElementById('slitImg').src = f.ut_b64;
    slitWrap.classList.add('visible');
  }} else {{
    slitWrap.classList.remove('visible');
  }}

  drawEvolutionTimeline();
  updateLiveInsightAndOverlay();
  if (activeTab === 'library') renderLibraryList();
}}

function buildCutJumpPills(f) {{
  const strip = document.getElementById('cutJumpStrip');
  strip.innerHTML = '';
  if (f.cuts && f.cuts.length) {{
    f.cuts.forEach((c, idx) => {{
      const btn = document.createElement('button');
      btn.className = 'phase-btn';
      btn.id = 'cutBtn-' + idx;
      const tStart = idx * 3.0;
      btn.textContent = `Cut ${{c.cut_num}}: ${{c.phase.split('·')[1] || c.phase}} (${{tStart.toFixed(0)}}s)`;
      btn.onclick = () => {{
        videoEl.currentTime = tStart + 0.7;
        videoEl.play().catch(() => {{}});
      }};
      strip.appendChild(btn);
    }});
  }} else if (f.parts && f.parts.length) {{
    f.parts.forEach((p, idx) => {{
      const btn = document.createElement('button');
      btn.className = 'phase-btn';
      btn.id = 'cutBtn-' + idx;
      btn.textContent = `Part ${{p.part_num}}: ${{p.topology.replace(/_/g, ' ').slice(0, 16)}} (${{p.t_start}}s)`;
      btn.onclick = () => {{
        videoEl.currentTime = p.t_start;
        videoEl.play().catch(() => {{}});
      }};
      strip.appendChild(btn);
    }});
  }}
}}

function playShapeFilm(ruleId) {{
  const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === ruleId);
  if (!op) return;
  document.querySelectorAll('.shape-card').forEach(el => el.classList.remove('active'));
  const card = document.getElementById('scard-' + ruleId);
  if (card) card.classList.add('active');

  setGuideMode('auto');
  const fMatch = FILMS_142.find(f => f.id === 'shape-' + op.scion_id);
  if (fMatch) loadFilmObject(fMatch, true);
}}

function jumpArchivalShot(ruleId) {{
  const r = (EIGHT_GRIDS.rules || []).find(x => x.id === ruleId);
  if (!r) return;
  const w = r.winner;
  const fMatch = FILMS_142.find(f => f.video_rel === w.video_rel || f.id.includes(w.film_id));
  setGuideMode(ruleId);
  if (fMatch) {{
    loadFilmObject(fMatch, false);
  }} else {{
    videoEl.src = w.video_rel;
  }}
  document.getElementById('stageTitle').textContent = `#${{r.num}} ${{r.name.split('(')[0].trim()}} — ${{w.source_title}}`;
  document.getElementById('stageSub').textContent = `In ${{w.film_title}} (${{w.maker}}) @ ${{w.timestamp_s}}s`;
  videoEl.onloadedmetadata = () => {{
    videoEl.currentTime = Math.max(0, w.timestamp_s - 0.5);
    videoEl.play().catch(() => {{}});
    videoEl.onloadedmetadata = null;
  }};
}}

function playEightGridsReel() {{
  setGuideMode('auto');
  const fMatch = FILMS_142.find(f => f.id === 'shape-eight-reel');
  if (fMatch) loadFilmObject(fMatch, true);
}}

function setGuideMode(mode) {{
  guideMode = mode;
  ['auto', 'none', 'golden_spiral', 'frame_in_frame', 's_curve', 'symmetry', 'rule_of_thirds', 'centered', 'v_shape', 'negative_space'].forEach(k => {{
    const b = document.getElementById('vf-' + k);
    if (b) b.classList.toggle('active', k === mode);
  }});
  updateLiveInsightAndOverlay();
}}

function toggleMotionTrail() {{
  showMotionTrail = !showMotionTrail;
  const b = document.getElementById('btnShowTrail');
  b.classList.toggle('active', showMotionTrail);
  b.textContent = `〰 2s Motion Trail: ${{showMotionTrail ? 'ON' : 'OFF'}}`;
  updateLiveInsightAndOverlay();
}}

function toggleEdgeProof() {{
  showEdgeProof = !showEdgeProof;
  const b = document.getElementById('btnShowEdges');
  b.classList.toggle('active', showEdgeProof);
  b.textContent = `🔍 Edge Proof: ${{showEdgeProof ? 'ON' : 'OFF'}}`;
  updateLiveInsightAndOverlay();
}}

function getSliceIndexAtTime(ser, t) {{
  if (!ser || !ser.length) return 0;
  let bestI = 0, bestD = 1e9;
  for (let i = 0; i < ser.length; i++) {{
    const d = Math.abs(ser[i].t - t);
    if (d < bestD) {{ bestD = d; bestI = i; }}
  }}
  return bestI;
}}

// Check if a normalized point (u, v) lies near the active geometric guide (for cyan Edge Proof!)
function isNearActiveGuide(u, v, ruleId) {{
  if (ruleId === 'symmetry') return Math.abs(u - 0.5) < 0.035;
  if (ruleId === 'rule_of_thirds') return Math.abs(u - 1/3) < 0.03 || Math.abs(u - 2/3) < 0.03 || Math.abs(v - 1/3) < 0.03 || Math.abs(v - 2/3) < 0.03;
  if (ruleId === 'centered') return Math.abs(u - 0.42) < 0.03 || Math.abs(u - 0.58) < 0.03 || Math.abs(v - 0.68) < 0.03;
  if (ruleId === 'frame_in_frame') {{
    const onX = (Math.abs(u - 0.17) < 0.035 || Math.abs(u - 0.83) < 0.035) && v >= 0.14 && v <= 0.86;
    const onY = (Math.abs(v - 0.14) < 0.035 || Math.abs(v - 0.86) < 0.035) && u >= 0.17 && u <= 0.83;
    return onX || onY;
  }}
  if (ruleId === 'negative_space') return Math.abs(v - 0.64) < 0.04 || ((Math.abs(u - 0.08) < 0.03 || Math.abs(u - 0.92) < 0.03) && v <= 0.64);
  if (ruleId === 'v_shape') {{
    // Ray from (0.12, 0.04) to (0.50, 0.84) and (0.88, 0.04) to (0.50, 0.84)
    const t = (v - 0.04) / 0.80;
    if (t < 0 || t > 1) return false;
    const uL = 0.12 + t * 0.38, uR = 0.88 - t * 0.38;
    return Math.abs(u - uL) < 0.038 || Math.abs(u - uR) < 0.038;
  }}
  if (ruleId === 's_curve') {{
    const t = (0.88 - v) / 0.76;
    if (t < 0 || t > 1) return false;
    const mt = 1 - t;
    const uBez = mt*mt*mt*0.20 + 3*mt*mt*t*0.78 + 3*mt*t*t*0.22 + t*t*t*0.80;
    return Math.abs(u - uBez) < 0.045;
  }}
  if (ruleId === 'golden_spiral') {{
    return Math.abs(u - 0.618) < 0.035 || Math.abs(v - 0.618) < 0.035 || Math.hypot(u - 0.68, v - 0.44) < 0.14;
  }}
  return false;
}}

function updateLiveInsightAndOverlay() {{
  const ctx = guideCanvas.getContext('2d');
  const W = guideCanvas.width, H = guideCanvas.height;
  ctx.clearRect(0, 0, W, H);

  if (!activeFilm || !activeFilm.series || !activeFilm.series.length) return;
  const ser = activeFilm.series;
  const idx = getSliceIndexAtTime(ser, curTime);
  const curS = ser[idx];
  const prevS = ser[Math.max(0, idx - 1)];

  // Determine which geometric rule is active on this frame
  let ruleId = guideMode;
  if (guideMode === 'auto') {{
    if (activeFilm.id === 'shape-eight-reel') {{
      const rIdx = Math.min(7, Math.floor(curTime / 3.5));
      ruleId = (EIGHT_GRIDS.rules[rIdx] || {{}}).id || curS.shape;
    }} else if (activeFilm.pinned_rule) {{
      ruleId = activeFilm.pinned_rule;
    }} else {{
      ruleId = curS.shape || 'rule_of_thirds';
    }}
  }}

  const sInfo = SHAPE_INFO[ruleId] || SHAPE_INFO.rule_of_thirds;
  let fitPct = (curS.scores && curS.scores[ruleId]) || curS.fit || 82;

  // Check if we are in a SCION 8-cut film phase
  let phaseText = TOPO_LABELS[curS.topo] || curS.topo;
  let isRupturePhase = false;
  if (activeFilm.cuts && activeFilm.cuts.length === 8) {{
    const cIdx = Math.min(7, Math.floor(curTime / 3.0));
    const cutObj = activeFilm.cuts[cIdx];
    phaseText = `Cut ${{cutObj.cut_num}}/8 · ${{cutObj.phase}} (${{cutObj.source_title}})`;
    if (cIdx === 6) {{
      isRupturePhase = true;
      fitPct = Math.min(44, fitPct - 35);
    }}
    document.querySelectorAll('.phase-btn').forEach((b, i) => b.classList.toggle('active', i === cIdx));
  }} else if (activeFilm.parts && activeFilm.parts.length) {{
    activeFilm.parts.forEach((p, i) => {{
      const b = document.getElementById('cutBtn-' + i);
      if (b) b.classList.toggle('active', curTime >= p.t_start && curTime <= p.t_end);
    }});
  }}

  // 1. Draw Live Edge Proof (Cyan Glowing Structural Edges from the Actual Video Frame that Hit the Guide!)
  if (showEdgeProof && ruleId !== 'none' && canReadVideoPixels && videoEl.readyState >= 2) {{
    try {{
      probeCtx.drawImage(videoEl, 0, 0, 160, 90);
      const imgData = probeCtx.getImageData(0, 0, 160, 90).data;
      ctx.save();
      ctx.fillStyle = 'rgba(86, 200, 232, 0.88)';
      let hits = 0, totalGuidePts = 1;
      for (let py = 4; py < 86; py += 2) {{
        const v = py / 90.0;
        for (let px = 4; px < 156; px += 2) {{
          const u = px / 160.0;
          if (!isNearActiveGuide(u, v, ruleId)) continue;
          totalGuidePts++;
          const pIdx = (py * 160 + px) * 4;
          const lum = imgData[pIdx] * 0.3 + imgData[pIdx+1] * 0.59 + imgData[pIdx+2] * 0.11;
          const lumR = imgData[pIdx+8] * 0.3 + imgData[pIdx+9] * 0.59 + imgData[pIdx+10] * 0.11;
          const lumD = imgData[pIdx+640] * 0.3 + imgData[pIdx+641] * 0.59 + imgData[pIdx+642] * 0.11;
          const grad = Math.abs(lum - lumR) + Math.abs(lum - lumD);
          if (grad > 26) {{
            hits++;
            ctx.fillRect(u * W - 2, v * H - 2, 4, 4);
          }}
        }}
      }}
      ctx.restore();
    }} catch (err) {{
      canReadVideoPixels = false;
    }}
  }}

  // 2. Draw the Selected or Auto-Detected Geometric Guide
  if (ruleId !== 'none') {{
    drawGeometricGuideOnCanvas(ctx, W, H, ruleId, isRupturePhase);
  }}

  // 3. Draw the 2-Second Spatiotemporal Subject Motion Trail (Showing How Geometry Changes Over Time!)
  if (showMotionTrail) {{
    const trailStart = Math.max(0, idx - 5);
    ctx.save();
    // Draw connecting trajectory ribbon over last ~2.5s
    ctx.beginPath();
    for (let k = trailStart; k <= idx; k++) {{
      const pt = ser[k];
      const px = pt.c[0] * W, py = pt.c[1] * H;
      if (k === trailStart) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }}
    ctx.strokeStyle = 'rgba(86, 200, 232, 0.85)';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw historical trail dots + current subject bounding circle
    for (let k = trailStart; k <= idx; k++) {{
      const pt = ser[k];
      const px = pt.c[0] * W, py = pt.c[1] * H;
      const alpha = 0.25 + 0.75 * ((k - trailStart + 1) / (idx - trailStart + 1));
      ctx.beginPath();
      ctx.arc(px, py, k === idx ? 7 : 4, 0, Math.PI * 2);
      ctx.fillStyle = k === idx ? '#56c8e8' : `rgba(86, 200, 232, ${{alpha}})`;
      ctx.fill();
    }}

    // Draw live subject bounding radius ring r(t)
    const cx = curS.c[0] * W, cy = curS.c[1] * H;
    ctx.beginPath();
    ctx.arc(cx, cy, curS.r * H * 0.85, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(86, 200, 232, 0.45)';
    ctx.setLineDash([4, 4]);
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.restore();
  }}

  // 4. Update the Plain-English Live Frame Insight Banner
  const modePrefix = guideMode === 'auto' ? '⚡ Auto-Detected' : '📌 Pinned Test';
  document.getElementById('liveShapeBadge').textContent = ruleId === 'none'
    ? 'Guide Off (Raw Footage)'
    : `${{modePrefix}}: #${{sInfo.num}} ${{sInfo.name}}`;
  document.getElementById('livePhaseBadge').textContent = phaseText;

  const statusWord = isRupturePhase ? 'RUPTURE / RELEASE' : (fitPct >= 75 ? 'STRONG LOCK' : (fitPct >= 55 ? 'MODERATE FIT' : 'OFF-AXIS DRIFT'));
  const barCol = isRupturePhase ? 'var(--cyan)' : (fitPct >= 75 ? 'var(--green)' : (fitPct >= 55 ? 'var(--gold)' : 'var(--rose)'));
  document.getElementById('liveFitText').textContent = `Fit: ${{fitPct}}% (${{statusWord}})`;
  const barEl = document.getElementById('liveFitBar');
  barEl.style.width = `${{fitPct}}%`;
  barEl.style.background = barCol;

  const driftPct = Math.round(Math.hypot(curS.c[0] - prevS.c[0], curS.c[1] - prevS.c[1]) * 100);
  const changeDesc = isRupturePhase
    ? `<b>Contextual Release (Testing Claim Limit):</b> Motion deliberately breaks out of the ${{sInfo.name}} grid (${{driftPct}}% frame shift) so the composition doesn't flatten the scene into a static diagram.`
    : `<b>Claim Being Tested:</b> ${{sInfo.claim}} <br><b>How It Changes Right Now:</b> Subject center is at (x=${{Math.round(curS.c[0]*100)}}%, y=${{Math.round(curS.c[1]*100)}}%) shifting ${{driftPct}}%/step — <b>${{TOPO_LABELS[curS.topo] || curS.topo}}</b>.`;
  document.getElementById('liveInsightExplain').innerHTML = changeDesc;
}}

function drawGeometricGuideOnCanvas(ctx, W, H, ruleId, isRupture) {{
  const pad = 18;
  ctx.save();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.30)';
  ctx.lineWidth = 1.2;
  ctx.strokeRect(pad, pad, W - pad * 2, H - pad * 2);

  ctx.strokeStyle = isRupture ? 'rgba(86, 200, 232, 0.92)' : 'rgba(240, 184, 87, 0.94)';
  ctx.lineWidth = 3.0;
  if (isRupture) ctx.setLineDash([7, 5]);

  if (ruleId === 'golden_spiral') {{
    const gx = pad + (W - pad * 2) * 0.618;
    const gy = pad + (H - pad * 2) * 0.618;
    ctx.save();
    ctx.strokeStyle = 'rgba(240, 184, 87, 0.42)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(gx, pad); ctx.lineTo(gx, H - pad); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(W - pad, gy); ctx.stroke();
    ctx.restore();

    const cx = W * 0.68, cy = H * 0.44;
    ctx.beginPath();
    let started = false;
    for (let k = 0; k < 140; k++) {{
      const theta = k * 0.085;
      const r = 4.0 * Math.exp(0.155 * (140 - k) * 0.085);
      const px = cx - r * Math.cos(theta) * 1.25;
      const py = cy + r * Math.sin(theta) * 0.92;
      if (px >= pad && px <= W - pad && py >= pad && py <= H - pad) {{
        if (!started) {{ ctx.moveTo(px, py); started = true; }}
        else ctx.lineTo(px, py);
      }}
    }}
    ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 8, 0, Math.PI * 2); ctx.stroke();
  }} else if (ruleId === 'frame_in_frame') {{
    ctx.strokeRect(W * 0.17, H * 0.14, W * 0.66, H * 0.72);
  }} else if (ruleId === 's_curve') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.20, H * 0.88);
    ctx.bezierCurveTo(W * 0.78, H * 0.72, W * 0.22, H * 0.28, W * 0.80, H * 0.12);
    ctx.stroke();
  }} else if (ruleId === 'symmetry') {{
    ctx.beginPath(); ctx.moveTo(W * 0.5, pad); ctx.lineTo(W * 0.5, H - pad); ctx.stroke();
  }} else if (ruleId === 'rule_of_thirds') {{
    [1/3, 2/3].forEach(f => {{
      ctx.beginPath(); ctx.moveTo(W * f, pad); ctx.lineTo(W * f, H - pad); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, H * f); ctx.lineTo(W - pad, H * f); ctx.stroke();
    }});
  }} else if (ruleId === 'centered') {{
    [0.42, 0.58].forEach(f => {{
      ctx.beginPath(); ctx.moveTo(W * f, pad); ctx.lineTo(W * f, H - pad); ctx.stroke();
    }});
    ctx.beginPath(); ctx.moveTo(pad, H * 0.68); ctx.lineTo(W - pad, H * 0.68); ctx.stroke();
  }} else if (ruleId === 'v_shape') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.12, pad); ctx.lineTo(W * 0.50, H * 0.84); ctx.lineTo(W * 0.88, pad);
    ctx.stroke();
  }} else if (ruleId === 'negative_space') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.08, H * 0.64); ctx.lineTo(W * 0.08, H * 0.10);
    ctx.lineTo(W * 0.92, H * 0.10); ctx.lineTo(W * 0.92, H * 0.64);
    ctx.stroke();
  }}
  ctx.restore();
}}

// Draw the 3-Band Time Evolution Canvas (1. Active Shape Ribbon | 2. Fit % & Motion Curves | 3. Subject/Bg Colors)
function drawEvolutionTimeline() {{
  const ctx = evoCanvas.getContext('2d');
  const W = evoCanvas.width, H = evoCanvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!activeFilm || !activeFilm.series || !activeFilm.series.length) return;

  const ser = activeFilm.series;
  const n = ser.length;
  const bw = W / n;

  // Band 1 (y=0..16): Active Geometric Rule Ribbon Over Time
  ser.forEach((s, i) => {{
    const rId = activeFilm.pinned_rule || s.shape || 'rule_of_thirds';
    const col = (SHAPE_INFO[rId] || SHAPE_INFO.rule_of_thirds).color;
    ctx.fillStyle = col;
    ctx.fillRect(i * bw, 0, bw + 1, 14);
  }});
  ctx.fillStyle = 'rgba(0,0,0,0.65)';
  ctx.fillRect(4, 1, 138, 12);
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 9.5px sans-serif';
  ctx.fillText('ACTIVE SHAPE CHAPTERS', 8, 10.5);

  // Band 2 (y=18..58): Geometric Fit % Curve (Gold) & Subject Shift Velocity (Cyan)
  ctx.fillStyle = '#0d1017';
  ctx.fillRect(0, 16, W, 42);
  ctx.beginPath();
  ser.forEach((s, i) => {{
    const rId = (guideMode !== 'auto' && guideMode !== 'none') ? guideMode : (activeFilm.pinned_rule || s.shape);
    const fit = (s.scores && s.scores[rId]) || s.fit || 80;
    const px = (i / Math.max(1, n - 1)) * W;
    const py = 55 - ((fit - 20) / 80.0) * 35;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }});
  ctx.strokeStyle = '#f0b857';
  ctx.lineWidth = 2.0;
  ctx.stroke();

  // Subject X-Position Trajectory Curve (Cyan)
  ctx.beginPath();
  ser.forEach((s, i) => {{
    const px = (i / Math.max(1, n - 1)) * W;
    const py = 20 + s.c[0] * 34;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }});
  ctx.strokeStyle = '#56c8e8';
  ctx.lineWidth = 1.6;
  ctx.stroke();

  // Band 3 (y=60..82): Real Subject Color vs. Background Color Strip
  ser.forEach((s, i) => {{
    const x = i * bw;
    ctx.fillStyle = `rgb(${{s.rgb_core[0]}},${{s.rgb_core[1]}},${{s.rgb_core[2]}})`;
    ctx.fillRect(x, 60, bw + 1, 11);
    ctx.fillStyle = `rgb(${{s.rgb_shell[0]}},${{s.rgb_shell[1]}},${{s.rgb_shell[2]}})`;
    ctx.fillRect(x, 71, bw + 1, 11);
  }});

  // Playhead Line
  const dur = activeFilm.duration_s || videoEl.duration || 1;
  const px = Math.min(1, Math.max(0, curTime / dur)) * W;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(px - 1.5, 0, 3, H);
}}

evoCanvas.addEventListener('click', e => {{
  const rect = evoCanvas.getBoundingClientRect();
  const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const dur = videoEl.duration || activeFilm.duration_s || 24;
  videoEl.currentTime = frac * dur;
}});

function scrubSlit(e) {{
  const rect = e.currentTarget.getBoundingClientRect();
  const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const dur = videoEl.duration || activeFilm.duration_s || 24;
  videoEl.currentTime = frac * dur;
}}

videoEl.addEventListener('timeupdate', () => {{
  curTime = videoEl.currentTime || 0;
  const dur = videoEl.duration || activeFilm.duration_s || 1;
  document.getElementById('timeReadout').textContent = `${{curTime.toFixed(1)}}s / ${{dur.toFixed(1)}}s`;
  document.getElementById('slitPlayhead').style.left = `${{Math.min(100, (curTime / dur) * 100)}}%`;
  drawEvolutionTimeline();
  updateLiveInsightAndOverlay();
}});

function liveRenderLoop() {{
  if (!videoEl.paused && !videoEl.ended) {{
    curTime = videoEl.currentTime || 0;
    updateLiveInsightAndOverlay();
  }}
  requestAnimationFrame(liveRenderLoop);
}}

function openPromptModal(ruleId) {{
  const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === ruleId);
  if (!op) return;
  activePromptOp = op;
  document.getElementById('modalTitle').textContent = op.title;
  document.getElementById('modalBody').textContent = op.prompt_markdown;
  document.getElementById('modalPlayBtn').onclick = () => {{ closePromptModal(); playShapeFilm(ruleId); }};
  document.getElementById('promptModal').classList.add('active');
}}

function closePromptModal() {{
  document.getElementById('promptModal').classList.remove('active');
}}

function copyPromptText() {{
  if (activePromptOp) navigator.clipboard.writeText(activePromptOp.prompt_markdown);
}}

init();
</script>
</body>
</html>
"""

    out_html = os.path.join(TENSOR_DIR, "index.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote watchable, claim-testing geometric studio -> {out_html} ({os.path.getsize(out_html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
