#!/usr/bin/env python3
"""
Builds the Zero-Scroll 100dvh Cinema, 8-Grid Viewfinder & Spatiotemporal Tensor Workstation at:
  /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html
"""

import os
import json
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


def main():
    tensor_path = os.path.join(TENSOR_DIR, "tensor_data.json")
    ir_path = os.path.join(TENSOR_DIR, "stgl_ir.json")
    grids_path = os.path.join(TENSOR_DIR, "eight_grids_archive.json")
    scion_shapes_path = os.path.join(TENSOR_DIR, "scion_shapes.json")

    with open(tensor_path) as f:
        tensor_data = json.load(f)
    with open(ir_path) as f:
        stgl_ir = json.load(f)

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

    films = tensor_data["films"]
    for film in films:
        film["ut_b64"] = encode_img_b64(film["ut_tomogram"])
        film["vt_b64"] = encode_img_b64(film["vt_tomogram"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>ALLWAYS — Zero-Scroll 4D Cinema Tensor, 8-Grid Viewfinder &amp; 3D Worm Studio</title>
<style>
  :root {{
    --bg: #07080b;
    --panel: #0e1017;
    --panel-alt: #141822;
    --border: #232838;
    --fg: #ede9e0;
    --muted: #8c93a6;
    --accent: #e5ae5c;
    --cyan: #56c2e6;
    --rose: #e36874;
    --green: #72cc96;
    --purple: #c77ae0;
    --mono: "SFMono-Regular", ui-monospace, Consolas, Menlo, monospace;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100dvh;
    overflow: hidden;
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    font-size: 12px;
    user-select: none;
  }}
  a {{ color: var(--accent); text-decoration: none; }}

  /* Fullscreen 3-Row Cockpit Grid (Zero Scroll) */
  .cockpit {{
    display: grid;
    grid-template-rows: 44px 1fr 92px;
    width: 100vw;
    height: 100dvh;
    gap: 6px;
    padding: 6px 8px;
  }}

  /* ROW 1: Top Bar (44px) */
  .topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 0 10px;
    overflow: hidden;
  }}
  .brand-cluster {{
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
  }}
  .brand-tag {{
    font-family: var(--mono);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--accent);
    background: #241d12;
    border: 1px solid var(--accent);
    padding: 2px 7px;
    border-radius: 4px;
  }}
  .film-strip-pills {{
    display: flex;
    align-items: center;
    gap: 4px;
    overflow-x: auto;
    scrollbar-width: none;
    padding: 2px 0;
  }}
  .film-strip-pills::-webkit-scrollbar {{ display: none; }}
  .f-pill {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 550;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.1s ease;
  }}
  .f-pill:hover {{ color: var(--fg); border-color: #3d455e; }}
  .f-pill.active {{
    background: #251e13;
    border-color: var(--accent);
    color: #fff;
    font-weight: 650;
  }}
  .telemetry-chips {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 10.5px;
    white-space: nowrap;
  }}
  .t-chip {{
    background: #090b10;
    border: 1px solid var(--border);
    padding: 3px 6px;
    border-radius: 4px;
    color: var(--fg);
  }}
  .t-chip b {{ color: var(--accent); font-weight: 600; }}
  .btn {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--fg);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 550;
    cursor: pointer;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }}
  .btn:hover {{ border-color: var(--accent); color: #fff; }}
  .btn.active {{ background: #261f14; border-color: var(--accent); color: var(--accent); }}
  .btn.rose {{ background: #291419; border-color: var(--rose); color: var(--rose); }}
  .btn.gold {{ background: #261f14; border-color: var(--accent); color: var(--accent); font-weight: 650; }}

  /* ROW 2: Center Stage (1fr) */
  .center-stage {{
    display: grid;
    grid-template-columns: 56% 44%;
    gap: 6px;
    min-height: 0;
    overflow: hidden;
  }}

  /* Left Column: Big Video Player + Acrylic Viewfinder & HUD */
  .theater-pane {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    padding: 8px;
  }}
  .theater-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    flex-shrink: 0;
  }}
  .theater-title {{
    font-size: 14px;
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .theater-sub {{
    font-size: 11px;
    color: var(--muted);
    margin-left: 8px;
  }}
  .video-container {{
    position: relative;
    flex: 1;
    min-height: 0;
    width: 100%;
    background: #000;
    border-radius: 5px;
    overflow: hidden;
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .video-container video {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }}
  #hudOverlayCanvas {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: auto;
    cursor: crosshair;
  }}
  .hud-passthrough {{
    clip-path: inset(0 0 38px 0);
  }}
  .theater-foot {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 5px;
    margin-top: 6px;
    flex-shrink: 0;
    flex-wrap: wrap;
  }}
  .hud-checks {{
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .hud-checks label {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    padding: 3px 6px;
    border-radius: 4px;
    font-size: 10px;
    color: var(--muted);
    cursor: pointer;
  }}
  .hud-checks input:checked + span {{ color: var(--fg); font-weight: 600; }}

  /* Right Column: Upper 3D Worm Dock + Lower 6-Manifold & 8-Grid Archive Dock */
  .instrument-dock {{
    display: grid;
    grid-template-rows: 46% 54%;
    gap: 6px;
    min-height: 0;
    overflow: hidden;
  }}
  .dock-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }}
  .dock-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
    flex-shrink: 0;
  }}
  .dock-title {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
    white-space: nowrap;
  }}
  .tab-strip {{
    display: flex;
    gap: 3px;
    flex-wrap: wrap;
  }}
  .tab-btn {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
  }}
  .tab-btn:hover {{ color: #fff; }}
  .tab-btn.active {{
    background: #251e13;
    border-color: var(--accent);
    color: var(--accent);
  }}
  .canvas-fill {{
    flex: 1;
    min-height: 0;
    width: 100%;
    background: radial-gradient(circle at 50% 45%, #141824 0%, #07090d 100%);
    border: 1px solid var(--border);
    border-radius: 5px;
    display: block;
  }}
  .dock-foot {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-top: 4px;
    flex-shrink: 0;
    font-size: 10px;
    color: var(--muted);
  }}
  .dock-foot input[type=range] {{
    flex: 1;
    accent-color: var(--accent);
    height: 4px;
    cursor: pointer;
  }}

  /* 6-Manifold All-at-Once Mini Grid */
  .mini-six-grid {{
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 5px;
  }}
  .mini-cell {{
    background: #090b10;
    border: 1px solid var(--border);
    border-radius: 5px;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    flex-direction: column;
  }}
  .mini-cell:hover {{ border-color: var(--accent); }}
  .mini-cell-lbl {{
    position: absolute;
    top: 3px;
    left: 5px;
    right: 5px;
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    font-family: var(--mono);
    color: var(--fg);
    pointer-events: none;
    z-index: 2;
  }}
  .mini-cell-lbl span:first-child {{ color: var(--accent); font-weight: 600; }}
  .mini-cell canvas {{ width: 100%; height: 100%; display: block; }}

  /* 8-Rule Perspective Archive 4x2 Grid inside Lower Dock */
  .eight-grid-deck {{
    flex: 1;
    min-height: 0;
    display: none;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 5px;
  }}
  .eight-grid-deck.active {{ display: grid; }}
  .g8-card {{
    background: #080a0f;
    border: 1px solid var(--border);
    border-radius: 5px;
    overflow: hidden;
    position: relative;
    cursor: pointer;
    display: flex;
    flex-direction: column;
  }}
  .g8-card:hover, .g8-card.active {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
  .g8-card img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}
  .g8-cap {{
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(7, 8, 12, 0.86);
    padding: 2px 5px;
    font-size: 9px;
    line-height: 1.25;
  }}
  .g8-cap b {{ color: var(--accent); display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .g8-cap span {{ color: var(--fg); font-size: 8.5px; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .g8-actions {{
    position: absolute;
    top: 3px;
    right: 3px;
    display: flex;
    gap: 3px;
    z-index: 5;
  }}
  .g8-btn {{
    background: rgba(10, 12, 18, 0.88);
    border: 1px solid var(--accent);
    color: var(--accent);
    font-size: 8.5px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 3px;
    cursor: pointer;
  }}
  .g8-btn:hover {{ background: var(--accent); color: #090b10; }}
  .scion-modal {{
    position: absolute;
    inset: 8px;
    background: rgba(10, 12, 18, 0.96);
    border: 1px solid var(--accent);
    border-radius: 7px;
    z-index: 30;
    display: none;
    flex-direction: column;
    padding: 10px 12px;
    box-shadow: 0 12px 36px rgba(0,0,0,0.85);
  }}
  .scion-modal.active {{ display: flex; }}
  .scion-modal-body {{
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    font-family: var(--mono);
    font-size: 10.5px;
    line-height: 1.45;
    white-space: pre-wrap;
    color: var(--fg);
    background: #07080c;
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 8px 10px;
    margin-top: 6px;
    user-select: text;
  }}

  .single-manifold-pane {{
    flex: 1;
    min-height: 0;
    display: none;
    flex-direction: column;
  }}
  .single-manifold-pane.active {{ display: flex; }}

  /* ROW 3: Bottom NLE Scrubber + Slit-Scan Tomograms (92px) */
  .bottom-scrubber {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 4px 8px;
    display: grid;
    grid-template-columns: 1.15fr 1fr 1fr;
    gap: 8px;
    align-items: stretch;
    min-height: 0;
    overflow: hidden;
  }}
  .scrubber-col {{
    display: flex;
    flex-direction: column;
    min-height: 0;
    position: relative;
  }}
  .scrubber-lbl {{
    font-size: 9px;
    font-family: var(--mono);
    color: var(--muted);
    margin-bottom: 2px;
    display: flex;
    justify-content: space-between;
  }}
  #masterTimelineCanvas {{
    flex: 1;
    min-height: 0;
    width: 100%;
    background: #07080c;
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: ew-resize;
    display: block;
  }}
  .slit-box {{
    flex: 1;
    min-height: 0;
    position: relative;
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    cursor: ew-resize;
    background: #000;
  }}
  .slit-box img {{ width: 100%; height: 100%; object-fit: fill; display: block; }}
  .playhead-line {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
    box-shadow: 0 0 6px var(--accent);
    pointer-events: none;
    left: 0%;
  }}
  .ledger-scroll {{
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    font-size: 10.5px;
  }}
  .ledger-scroll table {{ width: 100%; border-collapse: collapse; }}
  .ledger-scroll th, .ledger-scroll td {{ padding: 4px 6px; border-bottom: 1px solid var(--border); text-align: left; }}
  .ledger-scroll th {{ background: var(--panel-alt); color: var(--muted); font-size: 9px; text-transform: uppercase; position: sticky; top: 0; }}
  .ledger-scroll tr:hover td {{ background: #181c28; cursor: pointer; }}
</style>
</head>
<body>
<div class="cockpit">
  <!-- ROW 1: TOP BAR -->
  <div class="topbar">
    <div class="brand-cluster">
      <span class="brand-tag">4D TENSOR LAB</span>
      <button class="btn gold" onclick="playEightGridsReel()" title="Watch the 8-Rule Archival Perspective Breakdown Reel">★ 8-Grid Reel (28s)</button>
      <button class="btn" onclick="stepFilm(-1)" title="Previous Film">◀</button>
      <button class="btn" onclick="stepFilm(1)" title="Next Film">▶</button>
    </div>

    <div class="film-strip-pills" id="filmPillList"></div>

    <div class="telemetry-chips">
      <span class="t-chip" id="chipTime"><b>τ</b> 0.00s</span>
      <span class="t-chip" id="chipLock"><b>Grid</b> 92%</span>
      <span class="t-chip" id="chipSaccade"><b>Δs²</b> +0.03</span>
      <span class="t-chip" id="chipFTBE"><b>FTBE</b> 2.41</span>
      <span class="t-chip" id="chipLinter" style="color:var(--green);border-color:#1f4730;">STGL PASS</span>
    </div>

    <div class="brand-cluster">
      <a class="btn" href="../paeleo/allways/index.html">← Hub</a>
      <a class="btn" href="../allways-best/index.html">★ Best</a>
      <a class="btn" href="../allways-awards/index.html">🏆 Awards</a>
    </div>
  </div>

  <!-- ROW 2: CENTER STAGE -->
  <div class="center-stage">
    <!-- Left: Primary Cinema Screening Room + Live Acrylic Viewfinder Overlay -->
    <div class="theater-pane">
      <div class="theater-head">
        <div style="display:flex;align-items:baseline;min-width:0;">
          <span class="theater-title" id="stageTitle">059 · BALL</span>
          <span class="theater-sub" id="stageSub">Claude Sonnet · Grand Prix · 96.0/100</span>
        </div>
        <div style="display:flex;gap:4px;flex-shrink:0;align-items:center;">
          <select id="viewfinderCardSelect" class="btn gold" onchange="onViewfinderCardChange(this.value)" title="Overlay Physical Acrylic Viewfinder Grid on Live Video">
            <option value="none">Acrylic Viewfinder: Off (14-Line)</option>
            <option value="golden_spiral">#1 Golden Ratio / Fibonacci Spiral</option>
            <option value="frame_in_frame">#2 Frame in a Frame (Sub-framing)</option>
            <option value="s_curve">#3 S-Curve (Leading Bezier)</option>
            <option value="symmetry">#4 Symmetry (Vertical Bisector)</option>
            <option value="rule_of_thirds">#5 The Rule of Thirds (3×3)</option>
            <option value="centered">#6 Centered (Channel + Baseline)</option>
            <option value="v_shape">#7 V-Shape (Converging Wedge)</option>
            <option value="negative_space">#8 Negative Space (U-Bracket)</option>
          </select>
          <button class="btn" id="btnCounterfactual" onclick="toggleCounterfactualReg()">⌖ Lock `register`</button>
          <button class="btn rose" id="btnResetSandbox" onclick="resetSandbox()" style="display:none;">↺ Reset</button>
          <a class="btn" id="stageCaseLink" href="../allways-sonnet/059-ball/index.html" target="_blank">Case ↗</a>
        </div>
      </div>

      <div class="video-container">
        <video id="mainVideo" controls playsinline preload="metadata"></video>
        <canvas id="hudOverlayCanvas" class="hud-passthrough" width="800" height="450"></canvas>
        <div class="scion-modal" id="scionPromptModal">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
            <strong id="scionModalTitle" style="color:var(--accent);font-size:12px;">SCION 114 // Golden Spiral</strong>
            <div style="display:flex;gap:5px;align-items:center;">
              <button class="btn gold" id="scionModalPlayBtn">▶ Play 24s Proof Film</button>
              <button class="btn" onclick="copyActiveScionPrompt()">📋 Copy Prompt</button>
              <a class="btn" id="scionModalMdLink" href="#" target="_blank">Raw .md ↗</a>
              <button class="btn rose" onclick="closeScionPromptModal()">✕ Close</button>
            </div>
          </div>
          <div class="scion-modal-body" id="scionModalBody"></div>
        </div>
      </div>

      <div class="theater-foot">
        <div class="hud-checks">
          <label><input type="checkbox" id="hudArmature" checked onchange="renderHUD()"><span>14-Line Armature</span></label>
          <label><input type="checkbox" id="hudRegCircle" checked onchange="renderHUD()"><span>`059` Rim ($R=0.28H$)</span></label>
          <label><input type="checkbox" id="hudStrands" checked onchange="renderHUD()"><span>3-Strand Braid $\\mathcal{{B}}_3$</span></label>
          <label><input type="checkbox" id="hudSaccade" checked onchange="renderHUD()"><span>Saccade Cone $R(\\tau)$</span></label>
          <label><input type="checkbox" id="hudHelmholtz" checked onchange="renderHUD()"><span>Helmholtz Sink $-\\nabla\\Phi$</span></label>
        </div>
        <span style="font-size:10px;color:var(--muted);font-family:var(--mono);" id="hudNodeReadout">(u=0.50, v=0.50, d=0.72)</span>
      </div>
    </div>

    <!-- Right: Split Instrument Dock -->
    <div class="instrument-dock">
      <!-- Upper Dock: 3D Spatiotemporal Worm / 360° Torus / Dual Diff / Toric Camera -->
      <div class="dock-card">
        <div class="dock-head">
          <span class="dock-title">4D Spatiotemporal Volume $\\mathcal{{V}}(u,v,\\tau)$</span>
          <div class="tab-strip">
            <button class="tab-btn active" id="modeBtn-prism" onclick="setViewMode('prism')">3D Worm Prism</button>
            <button class="tab-btn" id="modeBtn-torus" onclick="setViewMode('torus')">360° Torus</button>
            <button class="tab-btn" id="modeBtn-diff" onclick="setViewMode('diff')">Dual-Film Diff</button>
            <button class="tab-btn" id="modeBtn-toric" onclick="setViewMode('toric')">Toric Camera</button>
          </div>
        </div>

        <canvas id="multiModeCanvas" class="canvas-fill" width="680" height="230"></canvas>

        <div class="dock-foot">
          <span>Semantic Zoom:</span>
          <input type="range" id="zoomSlider" min="1" max="12" step="0.25" value="1" oninput="onZoomChange(this.value)">
          <span style="font-family:var(--mono);color:var(--accent);min-width:38px;" id="zoomVal">1.0×</span>
          <select id="compareSelect" class="btn" style="padding:1px 5px;font-size:10px;" onchange="renderMultiModeCanvas()"></select>
          <label style="display:inline-flex;align-items:center;gap:3px;cursor:pointer;">
            <input type="checkbox" id="chkAutoOrbit" checked> <span>Orbit</span>
          </label>
        </div>
      </div>

      <!-- Lower Dock: 8-Grid Perspective Archive + 6-Manifold Interactive Workbench -->
      <div class="dock-card">
        <div class="dock-head">
          <span class="dock-title" id="manifoldDockTitle">8-Grid Perspective Archive &amp; 6-Manifold Deck</span>
          <div class="tab-strip">
            <button class="tab-btn active" id="mTab-grids" onclick="setManifoldTab('grids')">★ 8-Grids</button>
            <button class="tab-btn" id="mTab-all" onclick="setManifoldTab('all')">⊞ All 6</button>
            <button class="tab-btn" id="mTab-1" onclick="setManifoldTab('1')">1·Braid</button>
            <button class="tab-btn" id="mTab-2" onclick="setManifoldTab('2')">2·HHD</button>
            <button class="tab-btn" id="mTab-3" onclick="setManifoldTab('3')">3·W₂</button>
            <button class="tab-btn" id="mTab-4" onclick="setManifoldTab('4')">4·Cone</button>
            <button class="tab-btn" id="mTab-5" onclick="setManifoldTab('5')">5·TDA</button>
            <button class="tab-btn" id="mTab-6" onclick="setManifoldTab('6')">6·PLV</button>
            <button class="tab-btn" id="mTab-7" onclick="setManifoldTab('7')">Ledger</button>
          </div>
        </div>

        <!-- View 'grids': 8 Composition Grids Archive Deck (4x2 Zero-Scroll Grid) -->
        <div class="eight-grid-deck active" id="pane-grids"></div>

        <!-- View 'all': All 6 Manifolds Mini-Grid -->
        <div class="mini-six-grid" id="pane-all" style="display:none;">
          <div class="mini-cell" onclick="setManifoldTab('1')">
            <div class="mini-cell-lbl"><span>1 · Braid B₃</span><span id="mLbl1">FTBE 2.41</span></div>
            <canvas id="miniCv1" width="220" height="105"></canvas>
          </div>
          <div class="mini-cell" onclick="setManifoldTab('2')">
            <div class="mini-cell-lbl"><span>2 · Helmholtz ΦΨH</span><span id="mLbl2">40/38/13%</span></div>
            <canvas id="miniCv2" width="220" height="105"></canvas>
          </div>
          <div class="mini-cell" onclick="setManifoldTab('3')">
            <div class="mini-cell-lbl"><span>3 · Wasserstein W₂</span><span id="mLbl3">Geo 0.71</span></div>
            <canvas id="miniCv3" width="220" height="105"></canvas>
          </div>
          <div class="mini-cell" onclick="setManifoldTab('4')">
            <div class="mini-cell-lbl"><span>4 · Saccade Cone</span><span id="mLbl4">54% TL</span></div>
            <canvas id="miniCv4" width="220" height="105"></canvas>
          </div>
          <div class="mini-cell" onclick="setManifoldTab('5')">
            <div class="mini-cell-lbl"><span>5 · Takens TDA</span><span id="mLbl5">(9,50,0.37)</span></div>
            <canvas id="miniCv5" width="220" height="105"></canvas>
          </div>
          <div class="mini-cell" onclick="setManifoldTab('6')">
            <div class="mini-cell-lbl"><span>6 · Synchresis PLV</span><span id="mLbl6">0.446</span></div>
            <canvas id="miniCv6" width="220" height="105"></canvas>
          </div>
        </div>

        <!-- View 1: Artin Braid B_3 Sandbox -->
        <div class="single-manifold-pane" id="pane-1">
          <canvas id="cvBraid" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>Pull Strands Taut ($\\sigma_i\\sigma_i^{{-1}}\\to e$):</span>
            <input type="range" id="braidTautSlider" min="0" max="1" step="0.02" value="0" oninput="renderManifolds()">
            <span id="braidWordReadout" style="font-family:var(--mono);color:var(--cyan);">B₃: σ1 · σ2⁻¹</span>
          </div>
        </div>

        <!-- View 2: Helmholtz-Hodge Sandbox -->
        <div class="single-manifold-pane" id="pane-2">
          <canvas id="cvHHD" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>Isolate Orthogonal Field:</span>
            <button class="tab-btn active" id="hhdFilter-all" onclick="setHHDFilter('all')">All V</button>
            <button class="tab-btn" id="hhdFilter-phi" onclick="setHHDFilter('phi')">−∇Φ (Loom)</button>
            <button class="tab-btn" id="hhdFilter-psi" onclick="setHHDFilter('psi')">∇×Ψ (Swirl)</button>
            <button class="tab-btn" id="hhdFilter-h" onclick="setHHDFilter('h')">H (Pan)</button>
          </div>
        </div>

        <!-- View 3: Wasserstein W2 & KALMUS Sandbox -->
        <div class="single-manifold-pane" id="pane-3">
          <canvas id="cvW2" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>Core-Worm Aperture $r_{{\\text{{worm}}}}$:</span>
            <input type="range" id="kalmusRadiusSlider" min="0.08" max="0.42" step="0.01" value="0.22" oninput="renderManifolds()">
            <span id="w2Readout" style="font-family:var(--mono);color:var(--green);">ΔL* 16.0 · W₂² 0.49</span>
          </div>
        </div>

        <!-- View 4: Relativistic Saccade Light-Cones Sandbox -->
        <div class="single-manifold-pane" id="pane-4">
          <canvas id="cvSaccade" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>$c_{{\\text{{eye}}}}$:</span>
            <input type="range" id="cEyeSlider" min="200" max="700" step="10" value="400" oninput="onSaccadeParamChange()">
            <span id="cEyeVal" style="font-family:var(--mono);color:var(--accent);">400°/s</span>
            <span>$\\tau_{{\\text{{fix}}}}$:</span>
            <input type="range" id="tauFixSlider" min="100" max="320" step="5" value="200" oninput="onSaccadeParamChange()">
            <span id="tauFixVal" style="font-family:var(--mono);color:var(--accent);">200ms</span>
          </div>
        </div>

        <!-- View 5: Takens Persistent Homology Sandbox -->
        <div class="single-manifold-pane" id="pane-5">
          <canvas id="cvTDA" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>Vietoris–Rips Radius $\\epsilon$:</span>
            <input type="range" id="epsSlider" min="0.15" max="2.20" step="0.05" value="0.75" oninput="renderManifolds()">
            <span id="tdaReadout" style="font-family:var(--mono);color:var(--purple);">ε=0.75 · Chiasmus 0.37</span>
          </div>
        </div>

        <!-- View 6: Cross-Spectral Synchresis PLV Sandbox -->
        <div class="single-manifold-pane" id="pane-6">
          <canvas id="cvPLV" class="canvas-fill" width="640" height="190"></canvas>
          <div class="dock-foot">
            <span>Cymatic Grid Coupling $g_{{\\mu\\nu}}$:</span>
            <input type="range" id="cymaticGainSlider" min="0" max="3" step="0.1" value="1.2" oninput="renderManifolds(); renderHUD();">
            <span id="plvReadout" style="font-family:var(--mono);color:var(--cyan);">PLV 0.446 · Slip 0.005</span>
          </div>
        </div>

        <!-- View 7: 12-Film Ledger -->
        <div class="single-manifold-pane" id="pane-7">
          <div class="ledger-scroll">
            <table>
              <thead>
                <tr><th>Film</th><th>FTBE</th><th>Φ/Ψ/H</th><th>W₂</th><th>Timelike</th><th>TDA</th><th>PLV</th><th>Lock</th></tr>
              </thead>
              <tbody id="corpusTableBody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ROW 3: BOTTOM NLE SCRUBBER & SLIT-SCAN TOMOGRAM BAR (92px) -->
  <div class="bottom-scrubber">
    <div class="scrubber-col">
      <div class="scrubber-lbl">
        <span>MASTER TIMELINE (Chroma Core · $W_2^2$ Energy · Cut Cones $\\Delta s^2$)</span>
        <span id="scrubberTimeLbl" style="color:var(--accent);">0.00s / 40.2s</span>
      </div>
      <canvas id="masterTimelineCanvas" width="640" height="66"></canvas>
    </div>

    <div class="scrubber-col">
      <div class="scrubber-lbl">
        <span>$u\\text{{-}}\\tau$ HORIZON SLIT-SCAN TOMOGRAM</span>
        <span>Vertical = Lock · Diagonal = Pan</span>
      </div>
      <div class="slit-box" onmousemove="scrubFromSlit(event)" onclick="scrubFromSlit(event, true)">
        <img id="utSlitImg" alt="u-tau slit-scan">
        <div class="playhead-line" id="utPlayhead"></div>
      </div>
    </div>

    <div class="scrubber-col">
      <div class="scrubber-lbl">
        <span>$v\\text{{-}}\\tau$ VERTICAL SLIT-SCAN TOMOGRAM</span>
        <span>Strata = Cuts · Cone = Zoom</span>
      </div>
      <div class="slit-box" onmousemove="scrubFromSlit(event)" onclick="scrubFromSlit(event, true)">
        <img id="vtSlitImg" alt="v-tau slit-scan">
        <div class="playhead-line" id="vtPlayhead"></div>
      </div>
    </div>
  </div>
</div>

<script>
const FILMS = {json.dumps(films)};
const STGL_IR = {json.dumps(stgl_ir)};
const EIGHT_GRIDS = {json.dumps(grids_data)};
const SCION_SHAPES = {json.dumps(scion_shapes_data)};
let activeScionPromptOp = null;

let activeFilmIndex = 1; // Default 059-ball
let activeFilm = FILMS[activeFilmIndex] || FILMS[0];
let compareFilm = FILMS[10] || FILMS[0];
let viewMode = 'prism';
let activeManifoldTab = 'grids'; // Show 8-Grids Archive Deck first so user sees all 8 rules immediately!
let activeViewfinderRule = 'none';
let hhdFilter = 'all';
let curTime = 0.0;
let semanticZoom = 1.0;

let cEyeDeg = 400;
let tauFixMs = 200;
let counterfactualReg = false;
let userNodeOffset = {{ du: 0.0, dv: 0.0 }};
let draggingHUD = false;

let yaw = -0.56, pitch = 0.32;
let dragging3D = false, lastMX = 0, lastMY = 0;

const videoEl = document.getElementById('mainVideo');
const hudCanvas = document.getElementById('hudOverlayCanvas');
const multiCanvas = document.getElementById('multiModeCanvas');
const tlCanvas = document.getElementById('masterTimelineCanvas');

function initUI() {{
  const pillList = document.getElementById('filmPillList');
  const compSel = document.getElementById('compareSelect');
  const tbody = document.getElementById('corpusTableBody');
  const gridsDeck = document.getElementById('pane-grids');
  pillList.innerHTML = '';
  compSel.innerHTML = '';
  tbody.innerHTML = '';
  gridsDeck.innerHTML = '';

  FILMS.forEach((f, idx) => {{
    const btn = document.createElement('button');
    btn.className = 'f-pill' + (f.id === activeFilm.id ? ' active' : '');
    btn.id = 'fpill-' + f.id;
    btn.textContent = f.title;
    btn.onclick = () => selectFilmByIndex(idx);
    pillList.appendChild(btn);

    const opt = document.createElement('option');
    opt.value = f.id;
    opt.textContent = 'vs ' + f.title;
    if (f.id === compareFilm.id) opt.selected = true;
    compSel.appendChild(opt);

    const tr = document.createElement('tr');
    tr.onclick = () => selectFilmByIndex(idx);
    const h = f.helmholtz, w = f.wasserstein, s = f.saccade, t = f.tda, sy = f.synchresis, wm = f.worm;
    tr.innerHTML = `
      <td><strong>${{f.title}}</strong></td>
      <td style="font-family:var(--mono)">${{f.braid.ftbe.toFixed(2)}}</td>
      <td style="font-family:var(--mono)">${{Math.round(h.divergence_share*100)}}/${{Math.round(h.curl_share*100)}}/${{Math.round(h.harmonic_share*100)}}</td>
      <td style="font-family:var(--mono)">${{w.mean_w2_kinetic.toFixed(2)}}</td>
      <td style="font-family:var(--mono)">${{s.timelike_pct.toFixed(0)}}%</td>
      <td style="font-family:var(--mono)">(${{t.beta0_regimes}},${{t.beta1_loops}},${{t.beta2_chiasmus.toFixed(2)}})</td>
      <td style="font-family:var(--mono)">${{sy.mean_plv.toFixed(2)}}</td>
      <td style="font-family:var(--mono)">${{wm.compositional_lock_pct.toFixed(0)}}%</td>
    `;
    tbody.appendChild(tr);
  }});

  // Populate 8-Rule Archival Perspective Cards + SCION 114–121 Film & Prompt Buttons
  (EIGHT_GRIDS.rules || []).forEach(r => {{
    const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === r.id);
    const card = document.createElement('div');
    card.className = 'g8-card';
    card.id = 'g8card-' + r.id;
    card.onclick = () => loadArchivalRuleExemplar(r);
    const scionBadge = op ? `SCION ${{op.scion_id}}` : `#${{r.num}}`;
    card.innerHTML = `
      <div class="g8-actions">
        <button class="g8-btn" title="Play 24s 8-Cut SCION Shape Proof Film" onclick="playScionShapeFilm('${{r.id}}', event)">▶ Film</button>
        <button class="g8-btn" title="Read Full Standalone SCION Prompt" onclick="openScionPromptModal('${{r.id}}', event)">📜 SCION</button>
      </div>
      <img src="${{r.overlay_b64 || r.overlay_img}}" alt="${{r.name}}">
      <div class="g8-cap">
        <b>${{scionBadge}} · ${{r.name.split('(')[0].trim()}}</b>
        <span>${{r.winner.film_title}} · ${{r.winner.source_title}}</span>
      </div>
    `;
    gridsDeck.appendChild(card);
  }});
}}

function playScionShapeFilm(ruleId, ev) {{
  if (ev) ev.stopPropagation();
  closeScionPromptModal();
  const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === ruleId);
  if (!op) return;
  document.querySelectorAll('.g8-card').forEach(el => el.classList.remove('active'));
  const c = document.getElementById('g8card-' + ruleId);
  if (c) c.classList.add('active');

  activeViewfinderRule = 'none';
  document.getElementById('viewfinderCardSelect').value = 'none';

  document.getElementById('stageTitle').textContent = op.title;
  document.getElementById('stageSub').textContent = `24.0s · 8 Archival Cuts (Phase I Observation → II Viewfinder Lock → III Contextual Release → IV Return)`;
  document.getElementById('stageCaseLink').href = op.prompt_rel;

  videoEl.src = op.film_file;
  videoEl.currentTime = 0;
  videoEl.play().catch(() => {{}});
}}

function openScionPromptModal(ruleId, ev) {{
  if (ev) ev.stopPropagation();
  const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === ruleId);
  if (!op) return;
  activeScionPromptOp = op;
  document.getElementById('scionModalTitle').textContent = op.title;
  document.getElementById('scionModalBody').textContent = op.prompt_markdown;
  document.getElementById('scionModalMdLink').href = op.prompt_rel;
  document.getElementById('scionModalPlayBtn').onclick = (e) => playScionShapeFilm(ruleId, e);
  document.getElementById('scionPromptModal').classList.add('active');
}}

function closeScionPromptModal() {{
  document.getElementById('scionPromptModal').classList.remove('active');
}}

function copyActiveScionPrompt() {{
  if (!activeScionPromptOp) return;
  navigator.clipboard.writeText(activeScionPromptOp.prompt_markdown);
}}

function playEightGridsReel() {{
  document.getElementById('stageTitle').textContent = '8 Composition Rules — Archival Perspective Reel';
  document.getElementById('stageSub').textContent = '8 Sequential Rules from @gfxmotionbyahmar Foraged Across Opus, Argon, Sol & Sonnet (28.0s)';
  activeViewfinderRule = 'none';
  document.getElementById('viewfinderCardSelect').value = 'none';
  videoEl.src = 'eight-perspectives.mp4';
  videoEl.currentTime = 0;
  videoEl.play().catch(() => {{}});
  setManifoldTab('grids');
}}

function loadArchivalRuleExemplar(r) {{
  document.querySelectorAll('.g8-card').forEach(el => el.classList.remove('active'));
  const c = document.getElementById('g8card-' + r.id);
  if (c) c.classList.add('active');

  activeViewfinderRule = r.id;
  document.getElementById('viewfinderCardSelect').value = r.id;

  const w = r.winner;
  document.getElementById('stageTitle').textContent = `#${{r.num}} ${{r.name}} — ${{w.film_title}}`;
  document.getElementById('stageSub').textContent = `${{w.maker}} · Source: ${{w.source_title}} @ ${{w.timestamp_s}}s (Fit Score: ${{(w.score*100).toFixed(1)}}%)`;
  document.getElementById('stageCaseLink').href = w.case_url;

  videoEl.src = w.video_rel;
  videoEl.onloadedmetadata = () => {{
    videoEl.currentTime = Math.max(0, w.timestamp_s - 0.8);
    videoEl.play().catch(() => {{}});
    videoEl.onloadedmetadata = null;
  }};
  renderHUD();
}}

function onViewfinderCardChange(ruleId) {{
  activeViewfinderRule = ruleId;
  renderHUD();
}}

function stepFilm(delta) {{
  const nextIdx = (activeFilmIndex + delta + FILMS.length) % FILMS.length;
  selectFilmByIndex(nextIdx);
}}

function selectFilmByIndex(idx) {{
  activeFilmIndex = idx;
  activeFilm = FILMS[idx];
  curTime = 0.0;
  resetSandbox(false);

  document.querySelectorAll('.f-pill').forEach(el => el.classList.remove('active'));
  const p = document.getElementById('fpill-' + activeFilm.id);
  if (p) {{
    p.classList.add('active');
    p.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
  }}

  document.getElementById('stageTitle').textContent = activeFilm.title;
  document.getElementById('stageSub').textContent = activeFilm.maker + ' · ' + activeFilm.award + ' · ' + activeFilm.duration_s + 's';
  document.getElementById('stageCaseLink').href = activeFilm.watch_url;

  videoEl.src = activeFilm.video_rel;
  document.getElementById('utSlitImg').src = activeFilm.ut_b64 || activeFilm.ut_tomogram;
  document.getElementById('vtSlitImg').src = activeFilm.vt_b64 || activeFilm.vt_tomogram;

  renderAll();
}}

function setManifoldTab(tabId) {{
  activeManifoldTab = tabId;
  ['grids', 'all', '1', '2', '3', '4', '5', '6', '7'].forEach(k => {{
    const b = document.getElementById('mTab-' + k);
    if (b) b.classList.toggle('active', k === tabId);
  }});
  document.getElementById('pane-grids').classList.toggle('active', tabId === 'grids');
  document.getElementById('pane-all').style.display = (tabId === 'all') ? 'grid' : 'none';
  for (let i = 1; i <= 7; i++) {{
    const p = document.getElementById('pane-' + i);
    if (p) p.classList.toggle('active', String(i) === tabId);
  }}
  renderManifolds();
}}

function sampleAtTime(film, tSec) {{
  const s = film.series || [];
  if (!s.length) return null;
  let best = s[0], bestD = 1e9;
  for (let i = 0; i < s.length; i++) {{
    const d = Math.abs(s[i].t - tSec);
    if (d < bestD) {{ bestD = d; best = s[i]; }}
  }}
  return best;
}}

function getModifiedNode(pt) {{
  if (!pt) return [0.5, 0.5, 0.5];
  let u = pt.s1[0] + userNodeOffset.du;
  let v = pt.s1[1] + userNodeOffset.dv;
  if (counterfactualReg) {{
    u = 0.5 + (u - 0.5) * 0.12;
    v = 0.5 + (v - 0.5) * 0.12;
  }}
  return [Math.max(0.03, Math.min(0.97, u)), Math.max(0.03, Math.min(0.97, v)), pt.s1[2]];
}}

function toggleCounterfactualReg() {{
  counterfactualReg = !counterfactualReg;
  document.getElementById('btnCounterfactual').classList.toggle('active', counterfactualReg);
  document.getElementById('btnResetSandbox').style.display = (counterfactualReg || userNodeOffset.du !== 0 || userNodeOffset.dv !== 0) ? 'inline-flex' : 'none';
  renderAll();
}}

function resetSandbox(rerender=true) {{
  counterfactualReg = false;
  userNodeOffset = {{ du: 0.0, dv: 0.0 }};
  cEyeDeg = 400;
  tauFixMs = 200;
  document.getElementById('cEyeSlider').value = 400;
  document.getElementById('tauFixSlider').value = 200;
  document.getElementById('cEyeVal').textContent = '400°/s';
  document.getElementById('tauFixVal').textContent = '200ms';
  document.getElementById('btnCounterfactual').classList.remove('active');
  document.getElementById('btnResetSandbox').style.display = 'none';
  if (rerender) renderAll();
}}

function setViewMode(m) {{
  viewMode = m;
  ['prism', 'torus', 'diff', 'toric'].forEach(k => {{
    document.getElementById('modeBtn-' + k).classList.toggle('active', k === m);
  }});
  renderMultiModeCanvas();
}}

function setHHDFilter(f) {{
  hhdFilter = f;
  ['all', 'phi', 'psi', 'h'].forEach(k => {{
    document.getElementById('hhdFilter-' + k).classList.toggle('active', k === f);
  }});
  renderManifolds();
}}

function onZoomChange(val) {{
  semanticZoom = parseFloat(val);
  document.getElementById('zoomVal').textContent = semanticZoom.toFixed(1) + '×';
  renderMultiModeCanvas();
  renderMasterTimeline();
}}

function onSaccadeParamChange() {{
  cEyeDeg = parseFloat(document.getElementById('cEyeSlider').value);
  tauFixMs = parseFloat(document.getElementById('tauFixSlider').value);
  document.getElementById('cEyeVal').textContent = cEyeDeg.toFixed(0) + '°/s';
  document.getElementById('tauFixVal').textContent = tauFixMs.toFixed(0) + 'ms';
  document.getElementById('btnResetSandbox').style.display = 'inline-flex';
  renderAll();
}}

function getLiveHorizonSW() {{
  const cEyeSW = cEyeDeg / 40.0;
  const evalWindowS = Math.max(0.005, 0.222 - (tauFixMs / 1000.0));
  return Math.max(0.04, cEyeSW * evalWindowS);
}}

// Draw the selected Physical Acrylic Viewfinder Grid (from @gfxmotionbyahmar) onto the live HUD canvas
function drawAcrylicViewfinderOverlay(ctx, W, H, ruleId) {{
  if (!ruleId || ruleId === 'none') return;
  const pad = 16;
  ctx.save();
  // Outer Acrylic Card Bevel
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(pad, pad, W - pad * 2, H - pad * 2);

  ctx.strokeStyle = 'rgba(242, 196, 92, 0.94)';
  ctx.lineWidth = 3.2;

  if (ruleId === 'golden_spiral') {{
    const gx = pad + (W - pad * 2) * 0.618;
    const gy = pad + (H - pad * 2) * 0.618;
    ctx.strokeStyle = 'rgba(242, 196, 92, 0.45)';
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(gx, pad); ctx.lineTo(gx, H - pad); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(W - pad, gy); ctx.stroke();

    ctx.strokeStyle = 'rgba(242, 196, 92, 0.95)';
    ctx.lineWidth = 3.4;
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
  }} else if (ruleId === 'frame_in_frame') {{
    const ix0 = W * 0.17, iy0 = H * 0.14, iw = W * 0.66, ih = H * 0.72;
    ctx.strokeRect(ix0, iy0, iw, ih);
  }} else if (ruleId === 's_curve') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.20, H * 0.88);
    ctx.bezierCurveTo(W * 0.78, H * 0.72, W * 0.22, H * 0.28, W * 0.80, H * 0.12);
    ctx.stroke();
  }} else if (ruleId === 'symmetry') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.5, pad);
    ctx.lineTo(W * 0.5, H - pad);
    ctx.stroke();
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
    ctx.moveTo(W * 0.12, pad);
    ctx.lineTo(W * 0.50, H * 0.84);
    ctx.lineTo(W * 0.88, pad);
    ctx.stroke();
  }} else if (ruleId === 'negative_space') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.08, H * 0.64);
    ctx.lineTo(W * 0.08, H * 0.10);
    ctx.lineTo(W * 0.92, H * 0.10);
    ctx.lineTo(W * 0.92, H * 0.64);
    ctx.stroke();
  }}
  ctx.restore();
}}

// 1. Live Video HUD Overlay
function renderHUD() {{
  const ctx = hudCanvas.getContext('2d');
  const W = hudCanvas.width, H = hudCanvas.height;
  ctx.clearRect(0, 0, W, H);

  drawAcrylicViewfinderOverlay(ctx, W, H, activeViewfinderRule);

  const pt = sampleAtTime(activeFilm, curTime);
  if (!pt) return;
  const modS1 = getModifiedNode(pt);
  const cymGain = parseFloat(document.getElementById('cymaticGainSlider').value || 1.2);
  const bassWarp = (pt.sub_bass || 0) * 0.032 * cymGain;
  const centShift = ((pt.centroid || 0.5) - 0.5) * 0.035 * cymGain;

  if (document.getElementById('hudArmature').checked && activeViewfinderRule === 'none') {{
    ctx.save();
    ctx.strokeStyle = 'rgba(229, 174, 92, 0.30)';
    ctx.lineWidth = 1.1;
    const lines = [
      [[0,0],[1,1]], [[0,1],[1,0]],
      [[0.5,0],[0.5,1]], [[0,0.5+centShift],[1,0.5+centShift]],
      [[1/3-bassWarp,0],[1/3-bassWarp,1]], [[2/3+bassWarp,0],[2/3+bassWarp,1]],
      [[0,1/3-bassWarp],[1,1/3-bassWarp]], [[0,2/3+bassWarp],[1,2/3+bassWarp]],
      [[0,0],[0.5,1]], [[0.5,0],[1,1]], [[0,1],[0.5,0]], [[0.5,1],[1,0]]
    ];
    lines.forEach(([a, b]) => {{
      ctx.beginPath(); ctx.moveTo(a[0] * W, a[1] * H); ctx.lineTo(b[0] * W, b[1] * H); ctx.stroke();
    }});
    ctx.restore();
  }}

  if (document.getElementById('hudRegCircle').checked) {{
    ctx.save();
    const rPx = (0.28 + bassWarp * 0.5) * H;
    ctx.beginPath();
    ctx.arc(W * 0.5, H * 0.5, rPx, 0, Math.PI * 2);
    ctx.strokeStyle = counterfactualReg ? 'rgba(114, 204, 150, 0.88)' : 'rgba(86, 194, 230, 0.42)';
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  }}

  if (document.getElementById('hudHelmholtz').checked && pt.sink) {{
    const sx = pt.sink[0] * W, sy = pt.sink[1] * H;
    ctx.save();
    ctx.beginPath();
    ctx.arc(sx, sy, 9 + pt.phi * 16, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(227, 104, 116, 0.65)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  }}

  if (document.getElementById('hudSaccade').checked) {{
    const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
    let nearCut = cuts[0], minCD = 999;
    cuts.forEach(c => {{
      const d = Math.abs(c.tau - curTime);
      if (d < minCD) {{ minCD = d; nearCut = c; }}
    }});
    if (nearCut && minCD < 2.2) {{
      const rSW = getLiveHorizonSW();
      const p1x = nearCut.p1[0] * W, p1y = nearCut.p1[1] * H;
      const p2x = (nearCut.p2[0] + userNodeOffset.du) * W;
      const p2y = (nearCut.p2[1] + userNodeOffset.dv) * H;
      const jumpSW = Math.hypot((p2x - p1x) / W, (p2y - p1y) / H);
      const ds2Live = (rSW * rSW) - (jumpSW * jumpSW);
      const coneCol = ds2Live > 0.01 ? 'rgba(114, 204, 150, 0.65)' : (ds2Live > -0.012 ? 'rgba(229, 174, 92, 0.75)' : 'rgba(227, 104, 116, 0.75)');

      ctx.save();
      ctx.beginPath();
      ctx.arc(p1x, p1y, rSW * W, 0, Math.PI * 2);
      ctx.fillStyle = coneCol.replace('0.65', '0.09').replace('0.75', '0.11');
      ctx.fill();
      ctx.strokeStyle = coneCol;
      ctx.lineWidth = 1.6;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(p1x, p1y);
      ctx.lineTo(p2x, p2y);
      ctx.stroke();
      ctx.restore();
    }}
  }}

  if (document.getElementById('hudStrands').checked) {{
    const nodes = [
      {{ u: modS1[0], v: modS1[1], d: modS1[2], col: '#e5ae5c', lbl: 's₁' }},
      {{ u: pt.s2[0], v: pt.s2[1], d: pt.s2[2], col: '#56c2e6', lbl: 's₂' }},
      {{ u: pt.s3[0], v: pt.s3[1], d: pt.s3[2], col: '#c77ae0', lbl: 's₃' }}
    ];
    ctx.save();
    ctx.beginPath();
    ctx.setLineDash([2, 3]);
    ctx.moveTo(modS1[0] * W, modS1[1] * H);
    ctx.lineTo(0.5 * W, 0.5 * H);
    ctx.strokeStyle = 'rgba(229, 174, 92, 0.5)';
    ctx.stroke();
    ctx.restore();

    nodes.forEach((n, idx) => {{
      const nx = n.u * W, ny = n.v * H;
      ctx.save();
      ctx.beginPath();
      ctx.arc(nx, ny, idx === 0 ? 8 : 5.5, 0, Math.PI * 2);
      ctx.fillStyle = n.col;
      ctx.fill();
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(n.lbl, nx + 10, ny + 3);
      ctx.restore();
    }});
  }}
  document.getElementById('hudNodeReadout').textContent = `(u=${{modS1[0].toFixed(2)}}, v=${{modS1[1].toFixed(2)}}, d=${{modS1[2].toFixed(2)}})`;
}}

hudCanvas.addEventListener('mousedown', e => {{
  draggingHUD = true;
  updateHUDDrag(e);
}});
window.addEventListener('mouseup', () => {{ draggingHUD = false; }});
window.addEventListener('mousemove', e => {{
  if (draggingHUD) updateHUDDrag(e);
}});

function updateHUDDrag(e) {{
  const rect = hudCanvas.getBoundingClientRect();
  const uClick = Math.max(0.05, Math.min(0.95, (e.clientX - rect.left) / rect.width));
  const vClick = Math.max(0.05, Math.min(0.95, (e.clientY - rect.top) / rect.height));
  const pt = sampleAtTime(activeFilm, curTime);
  if (pt) {{
    userNodeOffset.du = uClick - pt.s1[0];
    userNodeOffset.dv = vClick - pt.s1[1];
    document.getElementById('btnResetSandbox').style.display = 'inline-flex';
    renderAll();
  }}
}}

// 2. Multi-Mode Spatiotemporal Volume Canvas
function project3DPoint(u, v, tNorm, W, H, xCenterOffset=0, scaleMult=1.0) {{
  const x = (tNorm - 0.5) * 1.68;
  const y = (0.5 - v) * 0.90;
  const z = (u - 0.5) * 0.90;
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = x * cy - z * sy;
  const z1 = x * sy + z * cy;
  const y2 = y * cp - z1 * sp;
  const z2 = y * sp + z1 * cp;
  const scale = (2.35 / (2.55 - z2)) * scaleMult;
  return {{
    px: W * 0.5 + xCenterOffset + x1 * scale * Math.min(W, H) * 0.62,
    py: H * 0.52 - y2 * scale * Math.min(W, H) * 0.62,
    scale: scale
  }};
}}

function drawPrismVolume(ctx, film, W, H, xOffset=0, scaleMult=1.0, isPrimary=true) {{
  const series = film.series || [];
  if (!series.length) return;
  const dur = film.duration_s || 1;
  const curNorm = Math.min(1, Math.max(0, curTime / dur));

  const halfWin = 0.5 / semanticZoom;
  const tMin = Math.max(0, Math.min(1 - 2 * halfWin, curNorm - halfWin));
  const tMax = Math.min(1, tMin + 2 * halfWin);

  const corners = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];
  const edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  ctx.save();
  ctx.strokeStyle = 'rgba(130, 145, 180, 0.22)';
  ctx.lineWidth = 1;
  edges.forEach(([i, j]) => {{
    const a = project3DPoint(corners[i][0], corners[i][1], corners[i][2], W, H, xOffset, scaleMult);
    const b = project3DPoint(corners[j][0], corners[j][1], corners[j][2], W, H, xOffset, scaleMult);
    ctx.beginPath(); ctx.moveTo(a.px, a.py); ctx.lineTo(b.px, b.py); ctx.stroke();
  }});

  const c0 = project3DPoint(0.5, 0.5, 0, W, H, xOffset, scaleMult);
  const c1 = project3DPoint(0.5, 0.5, 1, W, H, xOffset, scaleMult);
  ctx.strokeStyle = 'rgba(229, 174, 92, 0.45)';
  ctx.setLineDash([4, 4]);
  ctx.beginPath(); ctx.moveTo(c0.px, c0.py); ctx.lineTo(c1.px, c1.py); ctx.stroke();
  ctx.restore();

  const visSeries = series.filter(pt => {{
    const tn = pt.t / dur;
    return tn >= tMin - 0.02 && tn <= tMax + 0.02;
  }});

  ['s2', 's3'].forEach((k, idx) => {{
    ctx.save();
    ctx.beginPath();
    visSeries.forEach((pt, i) => {{
      const tn = (pt.t / dur - tMin) / Math.max(1e-4, tMax - tMin);
      const p = project3DPoint(pt[k][0], pt[k][1], tn, W, H, xOffset, scaleMult);
      if (i === 0) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py);
    }});
    ctx.strokeStyle = idx === 0 ? 'rgba(86, 194, 230, 0.5)' : 'rgba(199, 122, 224, 0.5)';
    ctx.lineWidth = 1.4;
    ctx.stroke();
    ctx.restore();
  }});

  for (let i = 0; i < visSeries.length - 1; i++) {{
    const a = visSeries[i], b = visSeries[i + 1];
    const tnA = (a.t / dur - tMin) / Math.max(1e-4, tMax - tMin);
    const tnB = (b.t / dur - tMin) / Math.max(1e-4, tMax - tMin);
    const nA = isPrimary ? getModifiedNode(a) : a.s1;
    const nB = isPrimary ? getModifiedNode(b) : b.s1;
    const pA = project3DPoint(nA[0], nA[1], tnA, W, H, xOffset, scaleMult);
    const pB = project3DPoint(nB[0], nB[1], tnB, W, H, xOffset, scaleMult);
    const rgb = a.rgb || [225, 175, 95];
    ctx.save();
    ctx.beginPath();
    ctx.strokeStyle = `rgba(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}}, 0.92)`;
    ctx.lineWidth = Math.max(2.2, a.r * 30 * pA.scale);
    ctx.lineCap = 'round';
    ctx.moveTo(pA.px, pA.py);
    ctx.lineTo(pB.px, pB.py);
    ctx.stroke();
    ctx.restore();
  }}

  if (curNorm >= tMin && curNorm <= tMax) {{
    const sliceT = (curNorm - tMin) / Math.max(1e-4, tMax - tMin);
    const sc = [[0,0,sliceT],[1,0,sliceT],[1,1,sliceT],[0,1,sliceT],[0,0,sliceT]];
    ctx.save();
    ctx.beginPath();
    sc.forEach((c, idx) => {{
      const p = project3DPoint(c[0], c[1], c[2], W, H, xOffset, scaleMult);
      if (idx === 0) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py);
    }});
    ctx.fillStyle = 'rgba(229, 174, 92, 0.09)';
    ctx.strokeStyle = 'rgba(229, 174, 92, 0.9)';
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }}
}}

function renderMultiModeCanvas() {{
  const ctx = multiCanvas.getContext('2d');
  const W = multiCanvas.width, H = multiCanvas.height;
  ctx.clearRect(0, 0, W, H);

  if (viewMode === 'prism') {{
    drawPrismVolume(ctx, activeFilm, W, H, 0, 1.0, true);
  }} else if (viewMode === 'diff') {{
    const compId = document.getElementById('compareSelect').value;
    compareFilm = FILMS.find(x => x.id === compId) || FILMS[0];
    drawPrismVolume(ctx, activeFilm, W, H, -W * 0.24, 0.72, true);
    drawPrismVolume(ctx, compareFilm, W, H, W * 0.24, 0.72, false);
    ctx.fillStyle = '#e5ae5c'; ctx.font = 'bold 11px sans-serif';
    ctx.fillText('A: ' + activeFilm.title, 12, 18);
    ctx.fillStyle = '#56c2e6';
    ctx.fillText('B: ' + compareFilm.title, W * 0.52, 18);
  }} else if (viewMode === 'torus') {{
    const series = activeFilm.series || [];
    const cx = W * 0.5, cy = H * 0.5;
    const rInner = 42, rMid = 72;
    const dur = activeFilm.duration_s || 1;
    series.forEach((pt, i) => {{
      const a0 = (i / series.length) * Math.PI * 2 - Math.PI * 0.5;
      const a1 = ((i + 1.2) / series.length) * Math.PI * 2 - Math.PI * 0.5;
      const rgb = pt.rgb || [200, 160, 90];
      ctx.beginPath();
      ctx.arc(cx, cy, rInner + 11, a0, a1);
      ctx.strokeStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
      ctx.lineWidth = 18;
      ctx.stroke();
      const spike = rMid + Math.min(34, (pt.phi + pt.psi) * 18 + pt.w2 * 5);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a0) * rMid, cy + Math.sin(a0) * rMid);
      ctx.lineTo(cx + Math.cos(a0) * spike, cy + Math.sin(a0) * spike);
      ctx.strokeStyle = 'rgba(229, 174, 92, 0.75)';
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }});
    const curAng = (curTime / dur) * Math.PI * 2 - Math.PI * 0.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(curAng) * (rMid + 38), cy + Math.sin(curAng) * (rMid + 38));
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
  }} else if (viewMode === 'toric') {{
    const pt = sampleAtTime(activeFilm, curTime) || activeFilm.series[0];
    const modS1 = getModifiedNode(pt);
    const cx = W * 0.5, cy = H * 0.52;
    for (let r = 24; r <= 96; r += 24) {{
      ctx.beginPath();
      ctx.ellipse(cx, cy, r * 1.5, r * 0.85, 0, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(86, 194, 230, 0.25)';
      ctx.stroke();
    }}
    const camX = cx + (modS1[0] - 0.5) * 170;
    const camY = cy + (modS1[2] - 0.5) * 100;
    ctx.beginPath(); ctx.arc(camX, camY, 8, 0, Math.PI * 2); ctx.fillStyle = '#e5ae5c'; ctx.fill();
    ctx.fillStyle = '#ede9e0'; ctx.font = '10.5px monospace';
    ctx.fillText(`Toric Manifold: α=${{((0.5+modS1[2])*48).toFixed(1)}}° θ=${{((modS1[0]-0.5)*90).toFixed(1)}}° φ=${{((0.5-modS1[1])*60).toFixed(1)}}°`, 14, 18);
  }}
}}

multiCanvas.addEventListener('mousedown', e => {{
  dragging3D = true; lastMX = e.clientX; lastMY = e.clientY;
  document.getElementById('chkAutoOrbit').checked = false;
}});
window.addEventListener('mouseup', () => {{ dragging3D = false; }});
window.addEventListener('mousemove', e => {{
  if (!dragging3D) return;
  yaw += (e.clientX - lastMX) * 0.008;
  pitch = Math.max(-1.15, Math.min(1.15, pitch + (e.clientY - lastMY) * 0.008));
  lastMX = e.clientX; lastMY = e.clientY;
  renderMultiModeCanvas();
}});

// 3. Bottom Master Scrubber
function renderMasterTimeline() {{
  const ctx = tlCanvas.getContext('2d');
  const W = tlCanvas.width, H = tlCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const dur = activeFilm.duration_s || 1;
  const rSW = getLiveHorizonSW();

  series.forEach((pt, i) => {{
    const x0 = (i / series.length) * W;
    const wBar = (W / series.length) + 1;
    const rgb = pt.rgb || [180, 150, 90];
    ctx.fillStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
    ctx.fillRect(x0, 2, wBar, 12);
  }});

  const maxW2 = Math.max(0.05, ...series.map(s => s.w2));
  ctx.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * W;
    const y = H - 6 - (pt.w2 / maxW2) * (H - 24);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#72cc96';
  ctx.lineWidth = 1.6;
  ctx.stroke();

  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  cuts.forEach(c => {{
    const x = (c.tau / dur) * W;
    const ds2 = (rSW * rSW) - (c.jump_sw * c.jump_sw);
    ctx.fillStyle = ds2 > 0.01 ? '#72cc96' : (ds2 > -0.012 ? '#e5ae5c' : '#e36874');
    ctx.fillRect(x - 1, 16, 2.5, H - 18);
  }});

  const px = (curTime / dur) * W;
  ctx.fillStyle = '#e5ae5c';
  ctx.fillRect(px - 1, 0, 2.5, H);
  document.getElementById('scrubberTimeLbl').textContent = `${{curTime.toFixed(2)}}s / ${{dur.toFixed(1)}}s`;
}}

function scrubToFraction(frac, seekVideo=false) {{
  const dur = activeFilm.duration_s || 1;
  curTime = Math.max(0, Math.min(dur, frac * dur));
  if (seekVideo && videoEl.duration) {{
    videoEl.currentTime = curTime;
  }}
  const pct = (curTime / dur) * 100;
  document.getElementById('utPlayhead').style.left = pct + '%';
  document.getElementById('vtPlayhead').style.left = pct + '%';
  renderAll(false);
}}

tlCanvas.addEventListener('mousemove', e => {{
  if (e.buttons !== 1) return;
  const rect = tlCanvas.getBoundingClientRect();
  scrubToFraction((e.clientX - rect.left) / rect.width, true);
}});
tlCanvas.addEventListener('click', e => {{
  const rect = tlCanvas.getBoundingClientRect();
  scrubToFraction((e.clientX - rect.left) / rect.width, true);
}});

function scrubFromSlit(e, clickSeek=false) {{
  if (!clickSeek && e.buttons !== 1) return;
  const rect = e.currentTarget.getBoundingClientRect();
  scrubToFraction((e.clientX - rect.left) / rect.width, true);
}}

videoEl.addEventListener('timeupdate', () => {{
  curTime = videoEl.currentTime || 0;
  const dur = activeFilm.duration_s || 1;
  const pct = Math.min(100, (curTime / dur) * 100);
  document.getElementById('utPlayhead').style.left = pct + '%';
  document.getElementById('vtPlayhead').style.left = pct + '%';
  renderAll(false);
}});

// 4. Manifold Renderers
function drawBraidOn(ctx, W, H, taut) {{
  ctx.clearRect(0, 0, W, H);
  const series = activeFilm.series || [];
  if (!series.length) return;
  const cols = ['#e5ae5c', '#56c2e6', '#c77ae0'];
  const canonicalU = [0.25, 0.50, 0.75];
  ['s1', 's2', 's3'].forEach((k, idx) => {{
    ctx.beginPath();
    series.forEach((pt, i) => {{
      const x = (i / Math.max(1, series.length - 1)) * (W - 14) + 7;
      const rawU = (idx === 0) ? getModifiedNode(pt)[0] : pt[k][0];
      const uVal = (1 - taut) * rawU + taut * canonicalU[idx];
      const y = (1 - uVal) * (H - 24) + 16;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }});
    ctx.strokeStyle = cols[idx];
    ctx.lineWidth = 1.8;
    ctx.stroke();
  }});
}}

function drawHHDOn(ctx, W, H, isFull) {{
  ctx.clearRect(0, 0, W, H);
  const series = activeFilm.series || [];
  if (!series.length) return;
  const maxV = Math.max(0.02, ...series.map(s => Math.max(s.phi, s.psi, s.h)));
  [['phi', '#e5ae5c'], ['psi', '#e36874'], ['h', '#56c2e6']].forEach(([k, col]) => {{
    if (isFull && hhdFilter !== 'all' && hhdFilter !== k) return;
    ctx.beginPath();
    series.forEach((pt, i) => {{
      const x = (i / Math.max(1, series.length - 1)) * (W - 14) + 7;
      const y = H - 8 - (pt[k] / maxV) * (H - 26);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }});
    ctx.strokeStyle = col;
    ctx.lineWidth = 1.7;
    ctx.stroke();
  }});
}}

function drawW2On(ctx, W, H) {{
  ctx.clearRect(0, 0, W, H);
  const series = activeFilm.series || [];
  if (!series.length) return;
  const maxW2 = Math.max(0.05, ...series.map(s => s.w2));
  ctx.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (W - 14) + 7;
    const y = H - 8 - (pt.w2 / maxW2) * (H - 28);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#72cc96';
  ctx.lineWidth = 1.9;
  ctx.stroke();
}}

function drawSaccadeOn(ctx, W, H) {{
  ctx.clearRect(0, 0, W, H);
  const rSW = getLiveHorizonSW();
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  const dur = activeFilm.duration_s || 1;
  const midY = H * 0.56;
  ctx.strokeStyle = 'rgba(255,255,255,0.2)';
  ctx.beginPath(); ctx.moveTo(0, midY); ctx.lineTo(W, midY); ctx.stroke();
  cuts.forEach(cut => {{
    const x = (cut.tau / dur) * (W - 16) + 8;
    const effJump = counterfactualReg ? cut.jump_sw * 0.25 : cut.jump_sw;
    const ds2 = (rSW * rSW) - (effJump * effJump);
    ctx.fillStyle = ds2 > 0.01 ? '#72cc96' : (ds2 > -0.012 ? '#e5ae5c' : '#e36874');
    const bH = Math.max(-midY + 14, Math.min(midY - 10, ds2 * 340));
    ctx.fillRect(x - 2.5, bH >= 0 ? midY - bH : midY, 5, Math.abs(bH) + 2);
  }});
}}

function drawTDAOn(ctx, W, H, eps) {{
  ctx.clearRect(0, 0, W, H);
  const att = (activeFilm.tda && activeFilm.tda.attractor_2d) || [];
  if (att.length < 2) return;
  const xs = att.map(p => p[0]), ys = att.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs) + 1e-5;
  const minY = Math.min(...ys), maxY = Math.max(...ys) + 1e-5;
  const pts = att.map(p => [
    ((p[0] - minX) / (maxX - minX)) * (W - 32) + 16,
    ((p[1] - minY) / (maxY - minY)) * (H - 30) + 18
  ]);
  const radPx = eps * (W / 24);
  ctx.fillStyle = 'rgba(199, 122, 224, 0.06)';
  pts.forEach(([px, py]) => {{
    ctx.beginPath(); ctx.arc(px, py, radPx, 0, Math.PI * 2); ctx.fill();
  }});
  ctx.beginPath();
  pts.forEach(([px, py], i) => {{ if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py); }});
  ctx.strokeStyle = '#c77ae0';
  ctx.lineWidth = 1.6;
  ctx.stroke();
}}

function drawPLVOn(ctx, W, H) {{
  ctx.clearRect(0, 0, W, H);
  const series = activeFilm.series || [];
  if (!series.length) return;
  ctx.beginPath();
  series.forEach((s, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (W - 14) + 7;
    const y = H - 8 - s.plv * (H - 26);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#56c2e6';
  ctx.lineWidth = 1.8;
  ctx.stroke();
}}

function renderManifolds() {{
  const taut = parseFloat(document.getElementById('braidTautSlider').value || 0);
  const eps = parseFloat(document.getElementById('epsSlider').value || 0.75);
  const b = activeFilm.braid, h = activeFilm.helmholtz, w = activeFilm.wasserstein, s = activeFilm.saccade, t = activeFilm.tda, sy = activeFilm.synchresis;

  document.getElementById('mLbl1').textContent = 'FTBE ' + b.ftbe.toFixed(2);
  document.getElementById('mLbl2').textContent = `${{Math.round(h.divergence_share*100)}}/${{Math.round(h.curl_share*100)}}/${{Math.round(h.harmonic_share*100)}}%`;
  document.getElementById('mLbl3').textContent = 'W₂ ' + w.mean_w2_kinetic.toFixed(2);
  document.getElementById('mLbl4').textContent = s.timelike_pct.toFixed(0) + '% TL';
  document.getElementById('mLbl5').textContent = `(${{t.beta0_regimes}},${{t.beta1_loops}},${{t.beta2_chiasmus.toFixed(2)}})`;
  document.getElementById('mLbl6').textContent = 'PLV ' + sy.mean_plv.toFixed(2);

  if (activeManifoldTab === 'all') {{
    drawBraidOn(document.getElementById('miniCv1').getContext('2d'), 220, 105, taut);
    drawHHDOn(document.getElementById('miniCv2').getContext('2d'), 220, 105, false);
    drawW2On(document.getElementById('miniCv3').getContext('2d'), 220, 105);
    drawSaccadeOn(document.getElementById('miniCv4').getContext('2d'), 220, 105);
    drawTDAOn(document.getElementById('miniCv5').getContext('2d'), 220, 105, eps);
    drawPLVOn(document.getElementById('miniCv6').getContext('2d'), 220, 105);
  }} else if (activeManifoldTab === '1') {{
    drawBraidOn(document.getElementById('cvBraid').getContext('2d'), 640, 190, taut);
    document.getElementById('braidWordReadout').textContent = 'B₃: ' + b.reduced_word_preview;
  }} else if (activeManifoldTab === '2') {{
    drawHHDOn(document.getElementById('cvHHD').getContext('2d'), 640, 190, true);
  }} else if (activeManifoldTab === '3') {{
    drawW2On(document.getElementById('cvW2').getContext('2d'), 640, 190);
  }} else if (activeManifoldTab === '4') {{
    drawSaccadeOn(document.getElementById('cvSaccade').getContext('2d'), 640, 190);
  }} else if (activeManifoldTab === '5') {{
    drawTDAOn(document.getElementById('cvTDA').getContext('2d'), 640, 190, eps);
    document.getElementById('tdaReadout').textContent = `ε=${{eps.toFixed(2)}} · Chiasmus ${{t.beta2_chiasmus.toFixed(2)}}`;
  }} else if (activeManifoldTab === '6') {{
    drawPLVOn(document.getElementById('cvPLV').getContext('2d'), 640, 190);
  }}
}}

function updateTopTelemetry() {{
  const pt = sampleAtTime(activeFilm, curTime) || activeFilm.series[0];
  if (!pt) return;
  const dGrid = counterfactualReg ? pt.d_grid * 0.2 : pt.d_grid;
  const rSW = getLiveHorizonSW();
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  let nearCut = cuts[0] || {{ jump_sw: 0.08, tau: 0 }};
  cuts.forEach(c => {{ if (Math.abs(c.tau - curTime) < Math.abs(nearCut.tau - curTime)) nearCut = c; }});
  const effJump = counterfactualReg ? nearCut.jump_sw * 0.25 : nearCut.jump_sw;
  const ds2 = (rSW * rSW) - (effJump * effJump);

  document.getElementById('chipTime').innerHTML = `<b>τ</b> ${{curTime.toFixed(1)}}s`;
  document.getElementById('chipLock').innerHTML = `<b>Lock</b> ${{activeFilm.worm.compositional_lock_pct.toFixed(0)}}%`;
  document.getElementById('chipSaccade').innerHTML = `<b>Δs²</b> ${{ds2 >= 0 ? '+' : ''}}${{ds2.toFixed(2)}}`;
  document.getElementById('chipFTBE').innerHTML = `<b>FTBE</b> ${{activeFilm.braid.ftbe.toFixed(2)}}`;
  const linter = document.getElementById('chipLinter');
  if (dGrid <= 0.12 && ds2 >= -0.015) {{
    linter.textContent = 'STGL PASS';
    linter.style.color = 'var(--green)';
  }} else {{
    linter.textContent = 'SHOCK CUT';
    linter.style.color = 'var(--rose)';
  }}
}}

function renderAll(includeManifolds=true) {{
  renderHUD();
  renderMultiModeCanvas();
  renderMasterTimeline();
  updateTopTelemetry();
  if (includeManifolds) renderManifolds();
}}

window.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.code === 'Space') {{ e.preventDefault(); if (videoEl.paused) videoEl.play(); else videoEl.pause(); }}
  else if (e.code === 'ArrowRight') {{ videoEl.currentTime = Math.min(videoEl.duration || 60, (videoEl.currentTime || 0) + 1.5); }}
  else if (e.code === 'ArrowLeft') {{ videoEl.currentTime = Math.max(0, (videoEl.currentTime || 0) - 1.5); }}
}});

function tickOrbit() {{
  if (document.getElementById('chkAutoOrbit').checked && !dragging3D && (viewMode === 'prism' || viewMode === 'diff')) {{
    yaw += 0.0032;
    renderMultiModeCanvas();
  }}
  requestAnimationFrame(tickOrbit);
}}

initUI();
selectFilmByIndex(activeFilmIndex);
requestAnimationFrame(tickOrbit);
</script>
</body>
</html>
"""

    out_html = os.path.join(TENSOR_DIR, "index.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote zero-scroll 100dvh cockpit with 8-Grid Archive -> {out_html} ({os.path.getsize(out_html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
