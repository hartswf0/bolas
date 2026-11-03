#!/usr/bin/env python3
"""
Builds the Single-File Epistemic Cinema Thinking Machine at:
  /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html

Implements all six epistemic interface principles:
  1. Surface the Invisible (live video HUD overlays for 14-line armature, cymatic string warp,
     Helmholtz sink attractor, 3-strand depth nodes, and expanding foveal saccade light-cones)
  2. Overcome Cognitive Limits (linked brushing across all 8 canvases + unified causal state bar)
  3. Support Multiple Modes (3D Glass-Prism Worm, u-tau/v-tau Slit-Scans, 360° Radial Cinemetrics
     Torus, and Dual-Film Split Comparator)
  4. Direct Manipulation (live sliders for foveal speed c_eye, neural fixation latency tau_fix,
     Vietoris-Rips filtration radius epsilon, braid tautness reduction, and draggable focal nodes)
  5. Semantic Zoom (1x Macro Corpus/Film view down to 12x Micro Cut-Plane inspection)
  6. Constrained Play (counterfactual registration & eye-trace repair sandbox with live STGL linter)
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
    audit_path = os.path.join(TENSOR_DIR, "stgl_audit.json")

    with open(tensor_path) as f:
        tensor_data = json.load(f)
    with open(ir_path) as f:
        stgl_ir = json.load(f)
    audit_data = {"audits": []}
    if os.path.exists(audit_path):
        with open(audit_path) as f:
            audit_data = json.load(f)

    films = tensor_data["films"]
    for film in films:
        film["ut_b64"] = encode_img_b64(film["ut_tomogram"])
        film["vt_b64"] = encode_img_b64(film["vt_tomogram"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLWAYS — Spatiotemporal Cinema Tensor &amp; Epistemic Thinking Machine</title>
<style>
  :root {{
    --bg: #07080b;
    --panel: #0e1017;
    --panel-alt: #141822;
    --panel-hi: #1b2030;
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
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    line-height: 1.45;
    overflow-x: hidden;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .app {{ max-width: 1520px; margin: 0 auto; padding: 16px 18px 56px; }}

  /* Top Epistemic Header */
  .top-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
    padding-bottom: 14px;
    margin-bottom: 12px;
  }}
  .eyebrow {{
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 4px;
  }}
  h1 {{
    margin: 0;
    font-size: 22px;
    font-weight: 680;
    letter-spacing: -0.02em;
  }}
  .sub-lead {{
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 12.5px;
    max-width: 880px;
  }}
  .nav-cluster {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .btn {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--fg);
    padding: 6px 11px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 550;
    cursor: pointer;
    transition: all 0.12s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }}
  .btn:hover {{ border-color: var(--accent); color: #fff; text-decoration: none; }}
  .btn.active {{ background: #261f14; border-color: var(--accent); color: var(--accent); }}
  .btn.rose {{ background: #261419; border-color: var(--rose); color: var(--rose); }}

  /* Principle Strip */
  .principle-bar {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    margin-bottom: 12px;
  }}
  @media (max-width: 1100px) {{ .principle-bar {{ grid-template-columns: repeat(3, 1fr); }} }}
  @media (max-width: 640px) {{ .principle-bar {{ grid-template-columns: repeat(2, 1fr); }} }}
  .p-chip {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 9px;
    font-size: 11px;
  }}
  .p-chip b {{ color: var(--accent); display: block; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .p-chip span {{ color: var(--muted); font-size: 10.5px; }}

  /* Film Selector & Mode Switcher */
  .selector-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 12px;
  }}
  .pill-list {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .f-pill {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 11.5px;
    cursor: pointer;
    font-weight: 500;
  }}
  .f-pill:hover {{ color: var(--fg); border-color: #3d455e; }}
  .f-pill.active {{
    background: #251e13;
    border-color: var(--accent);
    color: var(--fg);
    font-weight: 650;
  }}

  /* Live Causal Telemetry Ribbon (Overcome Cognitive Limits) */
  .telemetry-ribbon {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 8px;
    background: #0b0d13;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 14px;
    font-family: var(--mono);
  }}
  @media (max-width: 1100px) {{ .telemetry-ribbon {{ grid-template-columns: repeat(4, 1fr); }} }}
  .t-cell {{ display: flex; flex-direction: column; }}
  .t-cell .k {{ font-size: 9.5px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }}
  .t-cell .v {{ font-size: 13px; font-weight: 650; color: var(--fg); }}

  /* Primary Workbench Grid */
  .stage-grid {{
    display: grid;
    grid-template-columns: 1.05fr 1.35fr;
    gap: 14px;
    margin-bottom: 12px;
  }}
  @media (max-width: 1080px) {{ .stage-grid {{ grid-template-columns: 1fr; }} }}

  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 12px;
    display: flex;
    flex-direction: column;
  }}
  .card-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }}
  .card-title {{
    font-size: 12px;
    font-weight: 680;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--accent);
  }}
  .card-sub {{ font-size: 11px; color: var(--muted); }}

  /* Video + Direct Manipulation HUD Canvas Stack */
  .video-hud-stack {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--border);
  }}
  .video-hud-stack video {{
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
    cursor: crosshair;
  }}
  .hud-toggles {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
    font-size: 11px;
  }}
  .hud-toggles label {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    padding: 3px 8px;
    border-radius: 4px;
    cursor: pointer;
    color: var(--muted);
  }}
  .hud-toggles input:checked + span {{ color: var(--fg); font-weight: 600; }}

  /* Multi-Mode 3D Worm / Radial Torus / Slit-Scan / Dual Diff Viewport */
  #multiModeCanvas {{
    width: 100%;
    height: 350px;
    background: radial-gradient(circle at 50% 45%, #151924 0%, #080a0f 100%);
    border-radius: 6px;
    border: 1px solid var(--border);
    cursor: grab;
    display: block;
  }}
  #multiModeCanvas:active {{ cursor: grabbing; }}

  /* Master Semantic-Zoom Linked Timeline + Tomograms */
  .timeline-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 12px;
    margin-bottom: 14px;
  }}
  #masterTimelineCanvas {{
    width: 100%;
    height: 118px;
    background: #07080c;
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: ew-resize;
    display: block;
  }}
  .slit-pair {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 8px;
  }}
  @media (max-width: 800px) {{ .slit-pair {{ grid-template-columns: 1fr; }} }}
  .slit-strip {{
    position: relative;
    height: 66px;
    border-radius: 5px;
    overflow: hidden;
    border: 1px solid var(--border);
    cursor: pointer;
    background: #000;
  }}
  .slit-strip img {{ width: 100%; height: 100%; object-fit: fill; display: block; }}
  .slit-tag {{
    position: absolute;
    top: 4px;
    left: 6px;
    background: rgba(7, 8, 11, 0.84);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10.5px;
    color: var(--fg);
    pointer-events: none;
  }}
  .slit-playhead {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
    box-shadow: 0 0 6px var(--accent);
    pointer-events: none;
    left: 0%;
  }}

  /* 6-Manifold Interactive Sandbox Grid */
  .manifolds-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 16px;
  }}
  @media (max-width: 1180px) {{ .manifolds-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (max-width: 740px) {{ .manifolds-grid {{ grid-template-columns: 1fr; }} }}

  .m-canvas {{
    width: 100%;
    height: 195px;
    background: #090b10;
    border: 1px solid var(--border);
    border-radius: 6px;
    display: block;
    cursor: pointer;
    margin: 6px 0;
  }}
  .slider-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11px;
    margin-top: 4px;
  }}
  .slider-bar input[type=range] {{
    flex: 1;
    accent-color: var(--accent);
    cursor: pointer;
  }}
  .slider-val {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--accent);
    min-width: 68px;
    text-align: right;
  }}
  .kv-mini {{
    display: flex;
    justify-content: space-between;
    font-size: 11.5px;
    padding: 3px 0;
    border-top: 1px solid #181c26;
  }}
  .kv-mini span:first-child {{ color: var(--muted); }}
  .kv-mini span:last-child {{ font-family: var(--mono); font-weight: 600; }}

  .badge {{
    font-family: var(--mono);
    font-size: 10.5px;
    padding: 2px 7px;
    border-radius: 4px;
    background: #1f2433;
    color: var(--accent);
    font-weight: 600;
  }}
  .badge.green {{ background: #132a1e; color: var(--green); }}
  .badge.rose {{ background: #2c161b; color: var(--rose); }}
  .badge.cyan {{ background: #122730; color: var(--cyan); }}

  /* Matrix & STGL Inspector */
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ padding: 8px 9px; border-bottom: 1px solid var(--border); text-align: left; }}
  th {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); background: var(--panel-alt); }}
  tr.film-row {{ cursor: pointer; }}
  tr.film-row:hover td {{ background: #161a26; }}
  tr.film-row.active-row td {{ background: #221d14; border-bottom-color: var(--accent); }}
  pre.code-box {{
    background: #07080b;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    font-family: var(--mono);
    font-size: 11px;
    color: #b8c4d8;
    max-height: 260px;
    overflow: auto;
    margin: 0;
  }}
</style>
</head>
<body>
<div class="app">
  <!-- Header -->
  <div class="top-header">
    <div>
      <div class="eyebrow">ALLWAYS · Epistemic Media for Thinking the Unthinkable · Self-Contained Single-File Edition</div>
      <h1>4D Spatiotemporal Cinema Tensor $(u, v, d, \\tau)$ &amp; Interactive Worm Laboratory</h1>
      <p class="sub-lead">
        Every mathematical structure—Artin Braids ($\\mathcal{{B}}_3$), Helmholtz–Hodge Potentials ($\\Phi, \\mathbf{{\\Psi}}, \\mathbf{{H}}$), 5D Wasserstein Optimal Transport ($W_2$), Relativistic Saccade Light-Cones ($\\Delta s^2$), Takens Persistent Homology ($\\beta_0, \\beta_1, \\beta_2$), and Cross-Spectral Synchresis ($\\text{{PLV}}$)—is rendered as a live, directly manipulable instrument coupled to the film frame.
      </p>
    </div>
    <div class="nav-cluster">
      <a class="btn" href="../paeleo/allways/index.html">← ALLWAYS Hub</a>
      <a class="btn" href="../allways-best/index.html">★ 24-Cut Master Film</a>
      <a class="btn" href="../allways-awards/index.html">🏆 132-Film Jury &amp; Awards</a>
    </div>
  </div>

  <!-- 6 Epistemic Principles Banner -->
  <div class="principle-bar">
    <div class="p-chip"><b>1. Surface the Invisible</b><span>Live frame HUD: 14-line armature, cymatic warp, Helmholtz sinks &amp; saccade cones</span></div>
    <div class="p-chip"><b>2. Overcome Limits</b><span>Linked hover-brushing across all 8 canvases + unified causal state ribbon</span></div>
    <div class="p-chip"><b>3. Multiple Modes</b><span>Switch 3D Worm Prism, Slit-Scan Tomogram, 360° Radial Torus &amp; Dual-Film Diff</span></div>
    <div class="p-chip"><b>4. Direct Manipulation</b><span>Drag $c_{{\\text{{eye}}}}$, $\\tau_{{\\text{{fix}}}}$, Vietoris–Rips $\\epsilon$, braid tautness &amp; focal nodes live</span></div>
    <div class="p-chip"><b>5. Semantic Zoom</b><span>Zoom timeline &amp; 3D worm from $1\\times$ macro film arc to $12\\times$ micro cut window</span></div>
    <div class="p-chip"><b>6. Constrained Play</b><span>Counterfactual `fit: register` &amp; eye-trace sandbox with live STGL linter</span></div>
  </div>

  <!-- Film Selector Bar -->
  <div class="selector-bar">
    <div class="pill-list" id="filmPillList"></div>
    <div style="display:flex;gap:8px;align-items:center;">
      <span style="font-size:11px;color:var(--muted);">Compare Against:</span>
      <select id="compareSelect" class="btn" onchange="renderAll()"></select>
    </div>
  </div>

  <!-- Live Causal Telemetry Ribbon (Externalized Working Memory) -->
  <div class="telemetry-ribbon">
    <div class="t-cell"><span class="k">Playhead τ / Shot</span><span class="v" id="telTime">0.00s · Shot 01</span></div>
    <div class="t-cell"><span class="k">Subject Node (u, v, d)</span><span class="v" id="telNode">(0.50, 0.50, 0.72)</span></div>
    <div class="t-cell"><span class="k">14-Line Armature Error</span><span class="v" id="telGridErr">d = 0.012 (LOCKED)</span></div>
    <div class="t-cell"><span class="k">Helmholtz (Φ / Ψ / H)</span><span class="v" id="telHHD">0.42 / 0.35 / 0.18</span></div>
    <div class="t-cell"><span class="k">Wasserstein W₂² Energy</span><span class="v" id="telW2">0.48 · ΔL* 16.0</span></div>
    <div class="t-cell"><span class="k">Nearest Cut Interval Δs²</span><span class="v" id="telSaccade">+0.032 (Timelike)</span></div>
    <div class="t-cell"><span class="k">Braid Word / FTBE</span><span class="v" id="telBraid">FTBE 2.406</span></div>
    <div class="t-cell"><span class="k">Synchresis PLV / Slip</span><span class="v" id="telPLV">PLV 0.446</span></div>
  </div>

  <!-- Primary Stage: Left = Augmented Video + Counterfactual HUD | Right = Multi-Mode 3D Worm / Torus / Diff -->
  <div class="stage-grid">
    <!-- Left Viewport: Video + Live Epistemic HUD Overlay -->
    <div class="card">
      <div class="card-head">
        <div>
          <div class="card-title" id="stageTitle">059 · BALL (Claude Sonnet)</div>
          <div class="card-sub" id="stageSub">Drag the target node on the video frame to test counterfactual Eye-Trace &amp; STGL Armature lock</div>
        </div>
        <div style="display:flex;gap:6px;">
          <button class="btn" id="btnCounterfactual" onclick="toggleCounterfactualReg()">⌖ Simulate `fit: register` Lock</button>
          <button class="btn rose" id="btnResetSandbox" onclick="resetSandbox()" style="display:none;">↺ Reset Sandbox</button>
          <a class="btn" id="stageCaseLink" href="../allways-sonnet/059-ball/index.html" target="_blank">Case Study ↗</a>
        </div>
      </div>

      <div class="video-hud-stack">
        <video id="mainVideo" controls playsinline preload="metadata"></video>
        <canvas id="hudOverlayCanvas" width="640" height="360"></canvas>
      </div>

      <div class="hud-toggles">
        <label><input type="checkbox" id="hudArmature" checked onchange="renderHUD()"><span>14-Line Harmonic Armature</span></label>
        <label><input type="checkbox" id="hudRegCircle" checked onchange="renderHUD()"><span>`059-ball` Registration Rim ($R=0.28H$)</span></label>
        <label><input type="checkbox" id="hudStrands" checked onchange="renderHUD()"><span>3-Strand Braid Nodes $(u_i,v_i,d_i)$</span></label>
        <label><input type="checkbox" id="hudSaccade" checked onchange="renderHUD()"><span>Relativistic Saccade Cone $R(\\tau)$</span></label>
        <label><input type="checkbox" id="hudHelmholtz" checked onchange="renderHUD()"><span>Helmholtz Sink &amp; Cymatic Warp</span></label>
      </div>
    </div>

    <!-- Right Viewport: Multi-Mode Spatiotemporal Visualizer -->
    <div class="card">
      <div class="card-head">
        <div>
          <div class="card-title">Multi-Mode Spatiotemporal Volume Inspector</div>
          <div class="card-sub">Switch representations or drag to orbit 3D volume · Wheel/slider for Semantic Zoom</div>
        </div>
        <div style="display:flex;gap:5px;flex-wrap:wrap;">
          <button class="btn active" id="modeBtn-prism" onclick="setViewMode('prism')">1 · 3D Worm Prism</button>
          <button class="btn" id="modeBtn-torus" onclick="setViewMode('torus')">2 · 360° Cinemetrics Torus</button>
          <button class="btn" id="modeBtn-diff" onclick="setViewMode('diff')">3 · Dual-Film Diff</button>
          <button class="btn" id="modeBtn-toric" onclick="setViewMode('toric')">4 · Toric Camera Manifold</button>
        </div>
      </div>

      <canvas id="multiModeCanvas" width="820" height="350"></canvas>

      <div class="slider-bar" style="margin-top:8px;">
        <span>Semantic Zoom ($1\\times$ Macro $\\to 12\\times$ Micro Cut Window):</span>
        <input type="range" id="zoomSlider" min="1" max="12" step="0.25" value="1" oninput="onZoomChange(this.value)">
        <span class="slider-val" id="zoomVal">1.0× Full</span>
        <label style="display:inline-flex;align-items:center;gap:4px;margin-left:8px;cursor:pointer;">
          <input type="checkbox" id="chkAutoOrbit" checked> <span>Auto-Orbit</span>
        </label>
      </div>
    </div>
  </div>

  <!-- Master Linked-Brushing Timeline & Embedded Slit-Scan Tomograms -->
  <div class="timeline-card">
    <div class="card-head" style="margin-bottom:6px;">
      <div class="card-title">Linked Spatiotemporal Timeline &amp; Tomographic Slit-Scan Strata ($u\\text{{-}}\\tau$ Horizon &amp; $v\\text{{-}}\\tau$ Vertical)</div>
      <div class="card-sub">Hover or drag anywhere to scrub all 8 visualizers simultaneously · Green/Gold/Red ticks = Timelike / Lightlike / Spacelike Cuts</div>
    </div>
    <canvas id="masterTimelineCanvas" width="1440" height="118"></canvas>
    <div class="slit-pair">
      <div class="slit-strip" onmousemove="scrubFromSlit(event)" onclick="scrubFromSlit(event, true)">
        <img id="utSlitImg" alt="u-tau horizon slit-scan">
        <div class="slit-tag">$u\\text{{-}}\\tau$ Horizon Slit-Scan (Vertical Pillar = Locked Registration · Diagonal Wave = Camera Pan)</div>
        <div class="slit-playhead" id="utPlayhead"></div>
      </div>
      <div class="slit-strip" onmousemove="scrubFromSlit(event)" onclick="scrubFromSlit(event, true)">
        <img id="vtSlitImg" alt="v-tau vertical slit-scan">
        <div class="slit-tag">$v\\text{{-}}\\tau$ Vertical Slit-Scan (Crisp Strata = Cut Planes · Expanding Funnel = Scale Traverse)</div>
        <div class="slit-playhead" id="vtPlayhead"></div>
      </div>
    </div>
  </div>

  <!-- Six Interactive Manifold Visualizers (Direct Manipulation Sandboxes) -->
  <div class="manifolds-grid">
    <!-- 1. Artin Braid Topology B_3 -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">1 · Artin Braid Loom ($\\mathcal{{B}}_3$) &amp; FTBE</div>
        <span class="badge" id="badgeBraid">FTBE = 2.406</span>
      </div>
      <div class="card-sub">Worldline crossings $\\sigma_1^{{\\pm 1}}, \\sigma_2^{{\\pm 1}}$ in $(u, d, \\tau)$ · Pull strands taut to cancel trivial pacing $\\sigma_i\\sigma_i^{{-1}}=e$</div>
      <canvas class="m-canvas" id="cvBraid" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>Pull Strands Taut (Free Reduction):</span>
        <input type="range" id="braidTautSlider" min="0" max="1" step="0.02" value="0" oninput="renderBraidCanvas()">
        <span class="slider-val" id="braidTautVal">Raw (0%)</span>
      </div>
      <div class="kv-mini"><span>Reduced Braid Word</span><span id="kvBraidWord" style="color:var(--cyan);">σ1 · σ2⁻¹</span></div>
      <div class="kv-mini"><span>Raw → Reduced Crossings (Entanglement)</span><span id="kvBraidCount">17 → 7 (41.2%)</span></div>
    </div>

    <!-- 2. Helmholtz-Hodge Fluid Field -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">2 · Helmholtz–Hodge Ternary &amp; Flow Field</div>
        <span class="badge cyan" id="badgeHHD">Φ 40% · Ψ 38% · H 13%</span>
      </div>
      <div class="card-sub">Left: Ternary Phase Portrait $(\\|\\nabla\\Phi\\|, \\|\\nabla\\times\\mathbf{{\\Psi}}\\|, \\|\\mathbf{{H}}\\|)$ · Right: Live orthogonal vector field</div>
      <canvas class="m-canvas" id="cvHHD" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>Synthesize Component Gain:</span>
        <button class="btn active" id="hhdFilter-all" onclick="setHHDFilter('all')">All V</button>
        <button class="btn" id="hhdFilter-phi" onclick="setHHDFilter('phi')">−∇Φ (Depth)</button>
        <button class="btn" id="hhdFilter-psi" onclick="setHHDFilter('psi')">∇×Ψ (Curl)</button>
        <button class="btn" id="hhdFilter-h" onclick="setHHDFilter('h')">H (Pan)</button>
      </div>
      <div class="kv-mini"><span>Gravitational Sink / Source Locus</span><span id="kvHHDSink">(0.50, 0.50)</span></div>
      <div class="kv-mini"><span>Director Regime Signature</span><span id="kvHHDRegime">Balanced Push-Swirl</span></div>
    </div>

    <!-- 3. Wasserstein Chromatic Geodesics & KALMUS -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">3 · 5D Wasserstein ($W_2$) &amp; KALMUS Stratigraphy</div>
        <span class="badge green" id="badgeW2">Geo Eff = 0.71</span>
      </div>
      <div class="card-sub">Top: Core-Worm vs. Shell CIE-$L^*a^*b^*$ stratigraphy · Bottom: $W_2^2$ kinetic energy &amp; geodesic curvature</div>
      <canvas class="m-canvas" id="cvW2" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>Core-Sample Aperture Radius $r_{{\\text{{worm}}}}$:</span>
        <input type="range" id="kalmusRadiusSlider" min="0.08" max="0.42" step="0.01" value="0.22" oninput="renderW2Canvas()">
        <span class="slider-val" id="kalmusRadiusVal">r = 0.22</span>
      </div>
      <div class="kv-mini"><span>Itten Chiaroscuro $\\Delta L^*$ / Hue $\\Delta H$</span><span id="kvW2Itten">16.0 L* / 12.4°</span></div>
      <div class="kv-mini"><span>Mechanical Light Work $W_2^2$ (Mean / Peak)</span><span id="kvW2Work">0.49 / 2.85</span></div>
    </div>

    <!-- 4. Relativistic Saccade Light-Cones -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">4 · Relativistic Saccade Light-Cones ($\\Delta s^2$)</div>
        <span class="badge" id="badgeSaccade">54% Timelike</span>
      </div>
      <div class="card-sub">Drag biological foveal speed $c_{{\\text{{eye}}}}$ &amp; fixation latency $\\tau_{{\\text{{fix}}}}$ to reshape the causal horizon live</div>
      <canvas class="m-canvas" id="cvSaccade" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>$c_{{\\text{{eye}}}}$:</span>
        <input type="range" id="cEyeSlider" min="200" max="700" step="10" value="400" oninput="onSaccadeParamChange()">
        <span class="slider-val" id="cEyeVal">400°/s</span>
        <span>$\\tau_{{\\text{{fix}}}}$:</span>
        <input type="range" id="tauFixSlider" min="100" max="320" step="5" value="200" oninput="onSaccadeParamChange()">
        <span class="slider-val" id="tauFixVal">200ms</span>
      </div>
      <div class="kv-mini"><span>Live Classification (Timelike / Light / Space)</span><span id="kvSaccadeSplit">7 / 2 / 4 cuts</span></div>
      <div class="kv-mini"><span>Murch Eye-Trace Horizon Radius $R$</span><span id="kvSaccadeRad">0.220 screen-widths</span></div>
    </div>

    <!-- 5. Persistent Homology Attractors (TDA) -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">5 · Takens Attractor &amp; Vietoris–Rips ($\\beta_0, \\beta_1, \\beta_2$)</div>
        <span class="badge" id="badgeTDA" style="color:var(--purple);">(9, 50, 0.37)</span>
      </div>
      <div class="card-sub">Drag filtration radius $\\epsilon$ to grow Vietoris–Rips balls, merge $\\beta_0$ regimes, and close $\\beta_1$ limit cycles</div>
      <canvas class="m-canvas" id="cvTDA" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>Vietoris–Rips Filtration Radius $\\epsilon$:</span>
        <input type="range" id="epsSlider" min="0.15" max="2.20" step="0.05" value="0.75" oninput="renderTDACanvas()">
        <span class="slider-val" id="epsVal">ε = 0.75</span>
      </div>
      <div class="kv-mini"><span>Active $\\beta_0$ Components / $\\beta_1$ Loops at $\\epsilon$</span><span id="kvTDALive">4 regimes · 18 loops</span></div>
      <div class="kv-mini"><span>$\\beta_2$ Chiasmus Ring-Folding Symmetry</span><span id="kvTDAChiasmus">0.370</span></div>
    </div>

    <!-- 6. Cross-Spectral Synchresis & Cymatics -->
    <div class="card">
      <div class="card-head">
        <div class="card-title">6 · Cross-Spectral Synchresis &amp; Cymatic Tensor</div>
        <span class="badge cyan" id="badgePLV">PLV = 0.446</span>
      </div>
      <div class="card-sub">Left: Hilbert Phase-Locking Polar Clock $e^{{i(\\theta_{{\\text{{vis}}}}-\\theta_{{\\text{{aud}}}})}}$ · Right: $\\text{{PLV}}(\\tau)$ &amp; Anempathetic Slip</div>
      <canvas class="m-canvas" id="cvPLV" width="450" height="195"></canvas>
      <div class="slider-bar">
        <span>Cymatic Grid Coupling Gain $g_{{\\mu\\nu}}$:</span>
        <input type="range" id="cymaticGainSlider" min="0" max="3" step="0.1" value="1.2" oninput="renderPLVCanvas(); renderHUD();">
        <span class="slider-val" id="cymaticGainVal">1.2×</span>
      </div>
      <div class="kv-mini"><span>Empathetic Lock Peak / Anempathetic Slip</span><span id="kvPLVStats">0.892 / 0.005</span></div>
      <div class="kv-mini"><span>Sub-Bass ($20\\text{{–}}80\\text{{ Hz}}$) / Centroid Drive</span><span id="kvPLVBands">0.31 / 0.44</span></div>
    </div>
  </div>

  <!-- Comparative 12-Film Corpus Matrix + Declarative STGL Timeline IR & Live Linter -->
  <div class="stage-grid">
    <div class="card">
      <div class="card-head">
        <div class="card-title">12-Film Spatiotemporal Tensor Ledger (Click Any Row to Load)</div>
        <div class="card-sub">Compare all 4 makers across the 6 mathematical frameworks</div>
      </div>
      <div style="overflow-x:auto;">
        <table id="corpusTable">
          <thead>
            <tr>
              <th>Film &amp; Maker</th>
              <th>FTBE ($\\mathcal{{B}}_3$)</th>
              <th>HHD ($\\Phi/\\Psi/H$)</th>
              <th>$W_2$ / $\\Delta L^*$</th>
              <th>Timelike $\\Delta s^2$</th>
              <th>TDA $(\\beta_0,\\beta_1,\\beta_2)$</th>
              <th>PLV</th>
              <th>STGL Lock</th>
            </tr>
          </thead>
          <tbody id="corpusTableBody"></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <div class="card-title">Declarative 4D STGL Timeline IR &amp; Live Closed-Loop Verifier</div>
          <div class="card-sub">Updates live when you manipulate nodes or saccade parameters in the sandbox</div>
        </div>
        <span class="badge green" id="linterStatusBadge">STGL LINTER: PASS</span>
      </div>
      <pre class="code-box" id="stglLiveBox"></pre>
    </div>
  </div>
</div>

<script>
const FILMS = {json.dumps(films)};
const STGL_IR = {json.dumps(stgl_ir)};
const STGL_AUDIT = {json.dumps(audit_data)};

let activeFilm = FILMS[1] || FILMS[0]; // 059-ball default
let compareFilm = FILMS[10] || FILMS[0]; // sol-059-radius default comparison
let viewMode = 'prism'; // 'prism' | 'torus' | 'diff' | 'toric'
let hhdFilter = 'all';
let curTime = 0.0;
let semanticZoom = 1.0;

// Direct-manipulation sandbox state
let cEyeDeg = 400;
let tauFixMs = 200;
let counterfactualReg = false;
let userNodeOffset = {{ du: 0.0, dv: 0.0 }};
let draggingHUD = false;

// 3D Orbit state
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
  pillList.innerHTML = '';
  compSel.innerHTML = '';
  tbody.innerHTML = '';

  FILMS.forEach(f => {{
    const btn = document.createElement('button');
    btn.className = 'f-pill' + (f.id === activeFilm.id ? ' active' : '');
    btn.id = 'fpill-' + f.id;
    btn.textContent = f.title;
    btn.onclick = () => selectFilm(f.id);
    pillList.appendChild(btn);

    const opt = document.createElement('option');
    opt.value = f.id;
    opt.textContent = f.title + ' (' + f.maker + ')';
    if (f.id === compareFilm.id) opt.selected = true;
    compSel.appendChild(opt);

    const tr = document.createElement('tr');
    tr.className = 'film-row' + (f.id === activeFilm.id ? ' active-row' : '');
    tr.id = 'frow-' + f.id;
    tr.onclick = () => selectFilm(f.id);
    const h = f.helmholtz, w = f.wasserstein, s = f.saccade, t = f.tda, sy = f.synchresis, wm = f.worm;
    tr.innerHTML = `
      <td><strong>${{f.title}}</strong><br><span style="font-size:10.5px;color:var(--muted)">${{f.maker}}</span></td>
      <td style="font-family:var(--mono)">${{f.braid.ftbe.toFixed(2)}}</td>
      <td style="font-family:var(--mono)">${{Math.round(h.divergence_share*100)}}/${{Math.round(h.curl_share*100)}}/${{Math.round(h.harmonic_share*100)}}</td>
      <td style="font-family:var(--mono)">${{w.mean_w2_kinetic.toFixed(2)}} / ${{w.mean_chiaroscuro_dl.toFixed(1)}}</td>
      <td style="font-family:var(--mono)">${{s.timelike_pct.toFixed(0)}}%</td>
      <td style="font-family:var(--mono)">(${{t.beta0_regimes}},${{t.beta1_loops}},${{t.beta2_chiasmus.toFixed(2)}})</td>
      <td style="font-family:var(--mono)">${{sy.mean_plv.toFixed(3)}}</td>
      <td style="font-family:var(--mono)">${{wm.compositional_lock_pct.toFixed(0)}}%</td>
    `;
    tbody.appendChild(tr);
  }});
}}

function selectFilm(fid) {{
  const found = FILMS.find(x => x.id === fid);
  if (!found) return;
  activeFilm = found;
  curTime = 0.0;
  resetSandbox(false);

  document.querySelectorAll('.f-pill').forEach(el => el.classList.remove('active'));
  const p = document.getElementById('fpill-' + fid);
  if (p) p.classList.add('active');

  document.querySelectorAll('.film-row').forEach(el => el.classList.remove('active-row'));
  const r = document.getElementById('frow-' + fid);
  if (r) r.classList.add('active-row');

  document.getElementById('stageTitle').textContent = activeFilm.title + ' (' + activeFilm.maker + ')';
  document.getElementById('stageCaseLink').href = activeFilm.watch_url;

  videoEl.src = activeFilm.video_rel;
  document.getElementById('utSlitImg').src = activeFilm.ut_b64 || activeFilm.ut_tomogram;
  document.getElementById('vtSlitImg').src = activeFilm.vt_b64 || activeFilm.vt_tomogram;

  renderAll();
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
  const btn = document.getElementById('btnCounterfactual');
  btn.classList.toggle('active', counterfactualReg);
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
  renderHHDCanvas();
}}

function onZoomChange(val) {{
  semanticZoom = parseFloat(val);
  document.getElementById('zoomVal').textContent = semanticZoom.toFixed(1) + '× ' + (semanticZoom > 1.5 ? 'Micro' : 'Full');
  renderMultiModeCanvas();
  renderMasterTimeline();
}}

function onSaccadeParamChange() {{
  cEyeDeg = parseFloat(document.getElementById('cEyeSlider').value);
  tauFixMs = parseFloat(document.getElementById('tauFixSlider').value);
  document.getElementById('cEyeVal').textContent = cEyeDeg.toFixed(0) + '°/s';
  document.getElementById('tauFixVal').textContent = tauFixMs.toFixed(0) + 'ms';
  document.getElementById('btnResetSandbox').style.display = 'inline-flex';
  renderSaccadeCanvas();
  renderHUD();
  renderMasterTimeline();
  updateTelemetryAndSTGL();
}}

// Compute live saccade horizon radius in screen widths (40 deg horizontal FOV)
function getLiveHorizonSW() {{
  const cEyeSW = cEyeDeg / 40.0;
  const evalWindowS = Math.max(0.005, 0.222 - (tauFixMs / 1000.0));
  return Math.max(0.04, cEyeSW * evalWindowS);
}}

// 1. Live Video HUD Overlay (Surface the Invisible + Direct Manipulation)
function renderHUD() {{
  const ctx = hudCanvas.getContext('2d');
  const W = hudCanvas.width, H = hudCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const pt = sampleAtTime(activeFilm, curTime);
  if (!pt) return;
  const modS1 = getModifiedNode(pt);
  const cymGain = parseFloat(document.getElementById('cymaticGainSlider').value || 1.2);
  const bassWarp = (pt.sub_bass || 0) * 0.035 * cymGain;
  const centShift = ((pt.centroid || 0.5) - 0.5) * 0.04 * cymGain;

  // A. 14-Line Harmonic Armature with Cymatic Acoustic String Deformation
  if (document.getElementById('hudArmature').checked) {{
    ctx.save();
    ctx.strokeStyle = 'rgba(229, 174, 92, 0.34)';
    ctx.lineWidth = 1.1;
    // Main diagonals & reciprocals
    const lines = [
      [[0,0],[1,1]], [[0,1],[1,0]],
      [[0.5,0],[0.5,1]], [[0,0.5+centShift],[1,0.5+centShift]],
      [[1/3-bassWarp,0],[1/3-bassWarp,1]], [[2/3+bassWarp,0],[2/3+bassWarp,1]],
      [[0,1/3-bassWarp],[1,1/3-bassWarp]], [[0,2/3+bassWarp],[1,2/3+bassWarp]],
      [[0,0],[0.5,1]], [[0.5,0],[1,1]], [[0,1],[0.5,0]], [[0.5,1],[1,0]]
    ];
    lines.forEach(([a, b]) => {{
      ctx.beginPath();
      ctx.moveTo(a[0] * W, a[1] * H);
      ctx.lineTo(b[0] * W, b[1] * H);
      ctx.stroke();
    }});
    ctx.restore();
  }}

  // B. 059-ball Target Registration Rim (R = 0.28 * H at center [0.5, 0.5])
  if (document.getElementById('hudRegCircle').checked) {{
    ctx.save();
    const rPx = (0.28 + bassWarp * 0.6) * H;
    ctx.beginPath();
    ctx.arc(W * 0.5, H * 0.5, rPx, 0, Math.PI * 2);
    ctx.strokeStyle = counterfactualReg ? 'rgba(114, 204, 150, 0.85)' : 'rgba(86, 194, 230, 0.45)';
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.restore();
  }}

  // C. Helmholtz-Hodge Gravitational Sink/Source Attractor
  if (document.getElementById('hudHelmholtz').checked && pt.sink) {{
    const sx = pt.sink[0] * W, sy = pt.sink[1] * H;
    ctx.save();
    ctx.beginPath();
    ctx.arc(sx, sy, 10 + pt.phi * 18, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(227, 104, 116, 0.65)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = 'rgba(227, 104, 116, 0.85)';
    ctx.font = '10px monospace';
    ctx.fillText('∇Φ Sink', sx + 12, sy + 4);
    ctx.restore();
  }}

  // D. Relativistic Saccade Light-Cone around nearest cut
  if (document.getElementById('hudSaccade').checked) {{
    const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
    let nearCut = cuts[0], minCD = 999;
    cuts.forEach(c => {{
      const d = Math.abs(c.tau - curTime);
      if (d < minCD) {{ minCD = d; nearCut = c; }}
    }});
    if (nearCut && minCD < 2.5) {{
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
      ctx.fillStyle = coneCol.replace('0.65', '0.10').replace('0.75', '0.12');
      ctx.fill();
      ctx.strokeStyle = coneCol;
      ctx.lineWidth = 1.8;
      ctx.stroke();

      // Vector from p1 to p2
      ctx.beginPath();
      ctx.moveTo(p1x, p1y);
      ctx.lineTo(p2x, p2y);
      ctx.strokeStyle = coneCol;
      ctx.lineWidth = 2.0;
      ctx.stroke();
      ctx.restore();
    }}
  }}

  // E. 3-Strand Worldline Nodes & Magnetic Armature Tether
  if (document.getElementById('hudStrands').checked) {{
    const nodes = [
      {{ u: modS1[0], v: modS1[1], d: modS1[2], col: '#e5ae5c', lbl: 's₁ (Drag)' }},
      {{ u: pt.s2[0], v: pt.s2[1], d: pt.s2[2], col: '#56c2e6', lbl: 's₂' }},
      {{ u: pt.s3[0], v: pt.s3[1], d: pt.s3[2], col: '#c77ae0', lbl: 's₃' }}
    ];
    // Magnetic tether from s1 to center (0.5, 0.5)
    ctx.save();
    ctx.beginPath();
    ctx.setLineDash([2, 3]);
    ctx.moveTo(modS1[0] * W, modS1[1] * H);
    ctx.lineTo(0.5 * W, 0.5 * H);
    ctx.strokeStyle = 'rgba(229, 174, 92, 0.55)';
    ctx.stroke();
    ctx.restore();

    nodes.forEach((n, idx) => {{
      const nx = n.u * W, ny = n.v * H;
      const rad = idx === 0 ? 9 : 6;
      ctx.save();
      ctx.beginPath();
      ctx.arc(nx, ny, rad, 0, Math.PI * 2);
      ctx.fillStyle = n.col;
      ctx.fill();
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(`${{n.lbl}} d=${{n.d.toFixed(2)}}`, nx + 11, ny + 3);
      ctx.restore();
    }});
  }}
}}

// Direct manipulation of s1 focal node on HUD canvas
hudCanvas.addEventListener('mousedown', e => {{
  draggingHUD = true;
  updateHUDDrag(e);
}});
window.addEventListener('mouseup', () => {{ draggingHUD = false; }});
hudCanvas.addEventListener('mousemove', e => {{
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

// 2. Multi-Mode Spatiotemporal Viewport (3D Prism | 360° Torus | Dual-Film Diff | Toric Manifold)
function project3DPoint(u, v, tNorm, W, H, xCenterOffset=0, scaleMult=1.0) {{
  const x = (tNorm - 0.5) * 1.65;
  const y = (0.5 - v) * 0.92;
  const z = (u - 0.5) * 0.92;
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = x * cy - z * sy;
  const z1 = x * sy + z * cy;
  const y2 = y * cp - z1 * sp;
  const z2 = y * sp + z1 * cp;
  const scale = (2.35 / (2.55 - z2)) * scaleMult;
  return {{
    px: W * 0.5 + xCenterOffset + x1 * scale * Math.min(W, H) * 0.60,
    py: H * 0.52 - y2 * scale * Math.min(W, H) * 0.60,
    scale: scale
  }};
}}

function drawPrismVolume(ctx, film, W, H, xOffset=0, scaleMult=1.0, isPrimary=true) {{
  const series = film.series || [];
  if (!series.length) return;
  const dur = film.duration_s || 1;
  const curNorm = Math.min(1, Math.max(0, curTime / dur));

  // Semantic zoom window in normalized time [tMin, tMax]
  const halfWin = 0.5 / semanticZoom;
  const tMin = Math.max(0, Math.min(1 - 2 * halfWin, curNorm - halfWin));
  const tMax = Math.min(1, tMin + 2 * halfWin);

  // Outer wireframe box
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

  // Center registration filament
  const c0 = project3DPoint(0.5, 0.5, 0, W, H, xOffset, scaleMult);
  const c1 = project3DPoint(0.5, 0.5, 1, W, H, xOffset, scaleMult);
  ctx.strokeStyle = 'rgba(229, 174, 92, 0.5)';
  ctx.setLineDash([4, 4]);
  ctx.beginPath(); ctx.moveTo(c0.px, c0.py); ctx.lineTo(c1.px, c1.py); ctx.stroke();
  ctx.restore();

  // Filter series to semantic zoom window
  const visSeries = series.filter(pt => {{
    const tn = pt.t / dur;
    return tn >= tMin - 0.02 && tn <= tMax + 0.02;
  }});

  // Secondary strands s2, s3
  ['s2', 's3'].forEach((k, idx) => {{
    ctx.save();
    ctx.beginPath();
    visSeries.forEach((pt, i) => {{
      const tn = (pt.t / dur - tMin) / Math.max(1e-4, tMax - tMin);
      const p = project3DPoint(pt[k][0], pt[k][1], tn, W, H, xOffset, scaleMult);
      if (i === 0) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py);
    }});
    ctx.strokeStyle = idx === 0 ? 'rgba(86, 194, 230, 0.55)' : 'rgba(199, 122, 224, 0.55)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  }});

  // Primary Core Worm s1 colored by CIE-LAB/RGB palette
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
    ctx.lineWidth = Math.max(2.5, a.r * 34 * pA.scale);
    ctx.lineCap = 'round';
    ctx.moveTo(pA.px, pA.py);
    ctx.lineTo(pB.px, pB.py);
    ctx.stroke();
    ctx.restore();
  }}

  // Playhead slicing plane
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
    ctx.lineWidth = 1.6;
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
    drawPrismVolume(ctx, activeFilm, W, H, -W * 0.24, 0.68, true);
    drawPrismVolume(ctx, compareFilm, W, H, W * 0.24, 0.68, false);
    ctx.fillStyle = '#e5ae5c';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('A: ' + activeFilm.title, 20, 24);
    ctx.fillStyle = '#56c2e6';
    ctx.fillText('B: ' + compareFilm.title, W * 0.52, 24);
  }} else if (viewMode === 'torus') {{
    // Frederic Brodbeck 360° Radial Cinemetrics Torus
    const series = activeFilm.series || [];
    const cx = W * 0.5, cy = H * 0.5;
    const rInner = 68, rMid = 112;
    const dur = activeFilm.duration_s || 1;
    series.forEach((pt, i) => {{
      const a0 = (i / series.length) * Math.PI * 2 - Math.PI * 0.5;
      const a1 = ((i + 1.2) / series.length) * Math.PI * 2 - Math.PI * 0.5;
      const rgb = pt.rgb || [200, 160, 90];
      // Color ring
      ctx.beginPath();
      ctx.arc(cx, cy, rInner + 18, a0, a1);
      ctx.strokeStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
      ctx.lineWidth = 28;
      ctx.stroke();
      // Outer motion + W2 spike
      const spike = rMid + Math.min(52, (pt.phi + pt.psi) * 28 + pt.w2 * 8);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a0) * rMid, cy + Math.sin(a0) * rMid);
      ctx.lineTo(cx + Math.cos(a0) * spike, cy + Math.sin(a0) * spike);
      ctx.strokeStyle = 'rgba(229, 174, 92, 0.75)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }});
    // Playhead ray
    const curAng = (curTime / dur) * Math.PI * 2 - Math.PI * 0.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(curAng) * (rMid + 58), cy + Math.sin(curAng) * (rMid + 58));
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#ede9e0';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('360° CINEMETRICS TORUS', cx, cy + 4);
    ctx.textAlign = 'left';
  }} else if (viewMode === 'toric') {{
    // Lino & Christie 3D-to-2D Toric Camera Manifold (alpha, theta, phi)
    const pt = sampleAtTime(activeFilm, curTime) || activeFilm.series[0];
    const modS1 = getModifiedNode(pt);
    const cx = W * 0.5, cy = H * 0.52;
    for (let r = 35; r <= 140; r += 35) {{
      ctx.beginPath();
      ctx.ellipse(cx, cy, r * 1.45, r * 0.85, 0, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(86, 194, 230, 0.25)';
      ctx.stroke();
    }}
    const camX = cx + (modS1[0] - 0.5) * 220;
    const camY = cy + (modS1[2] - 0.5) * 140;
    ctx.beginPath();
    ctx.arc(camX, camY, 9, 0, Math.PI * 2);
    ctx.fillStyle = '#e5ae5c';
    ctx.fill();
    ctx.fillStyle = '#ede9e0';
    ctx.font = '11px monospace';
    ctx.fillText(`Toric Solver: α=${{((0.5+modS1[2])*48).toFixed(1)}}° θ=${{((modS1[0]-0.5)*90).toFixed(1)}}° φ=${{((0.5-modS1[1])*60).toFixed(1)}}°`, 20, 26);
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

// 3. Master Linked-Brushing Timeline
function renderMasterTimeline() {{
  const ctx = tlCanvas.getContext('2d');
  const W = tlCanvas.width, H = tlCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const dur = activeFilm.duration_s || 1;
  const rSW = getLiveHorizonSW();

  // Track 1 (Top): Core RGB Stratigraphy Strip
  series.forEach((pt, i) => {{
    const x0 = (i / series.length) * W;
    const wBar = (W / series.length) + 1;
    const rgb = pt.rgb || [180, 150, 90];
    ctx.fillStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
    ctx.fillRect(x0, 6, wBar, 18);
  }});

  // Track 2 (Middle): W2 Kinetic Energy + Helmholtz Divergence
  const maxW2 = Math.max(0.05, ...series.map(s => s.w2));
  ctx.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * W;
    const y = 78 - (pt.w2 / maxW2) * 44;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#72cc96';
  ctx.lineWidth = 1.8;
  ctx.stroke();

  // Track 3 (Bottom): Relativistic Cut Markers
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  cuts.forEach(c => {{
    const x = (c.tau / dur) * W;
    const ds2 = (rSW * rSW) - (c.jump_sw * c.jump_sw);
    ctx.fillStyle = ds2 > 0.01 ? '#72cc96' : (ds2 > -0.012 ? '#e5ae5c' : '#e36874');
    ctx.fillRect(x - 1.5, 28, 3, H - 34);
  }});

  // Playhead cursor
  const px = (curTime / dur) * W;
  ctx.fillStyle = '#e5ae5c';
  ctx.fillRect(px - 1, 0, 2.5, H);
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
  const rect = tlCanvas.getBoundingClientRect();
  scrubToFraction((e.clientX - rect.left) / rect.width, e.buttons === 1);
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

// 4. Six Individual Manifold Visualizers
function renderBraidCanvas() {{
  const c = document.getElementById('cvBraid');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const taut = parseFloat(document.getElementById('braidTautSlider').value || 0);
  document.getElementById('braidTautVal').textContent = taut > 0.5 ? `Reduced (${{Math.round(taut*100)}}%)` : `Raw (${{Math.round(taut*100)}}%)`;

  const cols = ['#e5ae5c', '#56c2e6', '#c77ae0'];
  const canonicalU = [0.25, 0.50, 0.75];
  ['s1', 's2', 's3'].forEach((k, idx) => {{
    ctx.beginPath();
    series.forEach((pt, i) => {{
      const x = (i / Math.max(1, series.length - 1)) * (W - 20) + 10;
      const rawU = (idx === 0) ? getModifiedNode(pt)[0] : pt[k][0];
      const uVal = (1 - taut) * rawU + taut * canonicalU[idx];
      const y = (1 - uVal) * (H - 28) + 14;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }});
    ctx.strokeStyle = cols[idx];
    ctx.lineWidth = 2.2;
    ctx.stroke();
  }});

  // Playhead
  const px = (curTime / (activeFilm.duration_s || 1)) * (W - 20) + 10;
  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, H); ctx.stroke();

  const b = activeFilm.braid;
  document.getElementById('badgeBraid').textContent = 'FTBE = ' + b.ftbe.toFixed(3);
  document.getElementById('kvBraidWord').textContent = b.reduced_word_preview;
  document.getElementById('kvBraidCount').textContent = `${{b.raw_crossings}} → ${{b.reduced_length}} (${{(b.entanglement_ratio*100).toFixed(1)}}%)`;
}}

function renderHHDCanvas() {{
  const c = document.getElementById('cvHHD');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const pt = sampleAtTime(activeFilm, curTime) || activeFilm.series[0];
  const h = activeFilm.helmholtz;
  document.getElementById('badgeHHD').textContent = `Φ ${{Math.round(h.divergence_share*100)}}% · Ψ ${{Math.round(h.curl_share*100)}}% · H ${{Math.round(h.harmonic_share*100)}}%`;
  document.getElementById('kvHHDSink').textContent = pt && pt.sink ? `(${{pt.sink[0].toFixed(2)}}, ${{pt.sink[1].toFixed(2)}})` : '(0.50, 0.50)';
  document.getElementById('kvHHDRegime').textContent = h.divergence_share > 0.45 ? 'Kubrickian Depth Push/Pull (Φ)' : (h.curl_share > 0.40 ? 'Rotational Vortex (Ψ)' : 'Balanced Laminar-Depth');

  // Left half: Ternary Phase Triangle
  const ax = 95, ay = 24, bx = 22, by = 168, cxT = 168, cyT = 168;
  ctx.strokeStyle = 'rgba(150,165,195,0.45)';
  ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.lineTo(cxT, cyT); ctx.closePath(); ctx.stroke();
  ctx.fillStyle = '#e5ae5c'; ctx.font = '10px monospace'; ctx.fillText('−∇Φ', ax - 14, ay - 6);
  ctx.fillStyle = '#e36874'; ctx.fillText('∇×Ψ', bx - 10, by + 13);
  ctx.fillStyle = '#56c2e6'; ctx.fillText('H', cxT - 4, cyT + 13);

  const tot = (pt.phi + pt.psi + pt.h) + 1e-5;
  const wPhi = pt.phi / tot, wPsi = pt.psi / tot, wH = pt.h / tot;
  const dotX = ax * wPhi + bx * wPsi + cxT * wH;
  const dotY = ay * wPhi + by * wPsi + cyT * wH;
  ctx.beginPath(); ctx.arc(dotX, dotY, 6, 0, Math.PI * 2); ctx.fillStyle = '#e5ae5c'; ctx.fill();

  // Right half: Live 2D Vector Field Preview
  const vx0 = 205, vy0 = 18, vw = 230, vh = 158;
  ctx.strokeStyle = 'rgba(130,145,175,0.25)';
  ctx.strokeRect(vx0, vy0, vw, vh);
  const su = pt.sink ? pt.sink[0] : 0.5, sv = pt.sink ? pt.sink[1] : 0.5;
  for (let gx = 0; gx < 8; gx++) {{
    for (let gy = 0; gy < 6; gy++) {{
      const u = (gx + 0.5) / 8, v = (gy + 0.5) / 6;
      const dx = u - su, dy = v - sv;
      let fx = 0, fy = 0;
      if (hhdFilter === 'all' || hhdFilter === 'phi') {{ fx += -dx * pt.phi * 18; fy += -dy * pt.phi * 18; }}
      if (hhdFilter === 'all' || hhdFilter === 'psi') {{ fx += -dy * pt.psi * 18; fy += dx * pt.psi * 18; }}
      if (hhdFilter === 'all' || hhdFilter === 'h') {{ fx += pt.h * 14; }}
      const px = vx0 + u * vw, py = vy0 + v * vh;
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px + fx, py + fy);
      ctx.strokeStyle = '#56c2e6';
      ctx.lineWidth = 1.4;
      ctx.stroke();
    }}
  }}
}}

function renderW2Canvas() {{
  const c = document.getElementById('cvW2');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const rVal = parseFloat(document.getElementById('kalmusRadiusSlider').value || 0.22);
  document.getElementById('kalmusRadiusVal').textContent = 'r = ' + rVal.toFixed(2);

  // Top band: KALMUS Core-Sample Palette Barcode
  series.forEach((pt, i) => {{
    const x = (i / series.length) * (W - 16) + 8;
    const bw = (W - 16) / series.length + 1;
    const rgb = pt.rgb || [200, 160, 100];
    ctx.fillStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
    ctx.fillRect(x, 10, bw, 28);
  }});

  // Bottom curve: 5D Wasserstein W_2^2 Chromatic Kinetic Energy
  const maxW2 = Math.max(0.05, ...series.map(s => s.w2));
  ctx.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (W - 16) + 8;
    const y = H - 14 - (pt.w2 / maxW2) * (H - 64);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#72cc96';
  ctx.lineWidth = 2.0;
  ctx.stroke();

  const w = activeFilm.wasserstein;
  const scaleChiaro = (w.mean_chiaroscuro_dl * (0.22 / rVal)).toFixed(1);
  document.getElementById('badgeW2').textContent = 'Geo Eff = ' + w.geodesic_efficiency.toFixed(2);
  document.getElementById('kvW2Itten').textContent = `${{scaleChiaro}} L* / ${{w.mean_hue_polarity_deg.toFixed(1)}}°`;
  document.getElementById('kvW2Work').textContent = `${{w.mean_w2_kinetic.toFixed(2)}} / ${{w.peak_w2_shock.toFixed(2)}}`;
}}

function renderSaccadeCanvas() {{
  const c = document.getElementById('cvSaccade');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const rSW = getLiveHorizonSW();
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  const dur = activeFilm.duration_s || 1;
  const midY = H * 0.54;

  // Horizon line ds^2 = 0
  ctx.strokeStyle = 'rgba(255,255,255,0.25)';
  ctx.beginPath(); ctx.moveTo(0, midY); ctx.lineTo(W, midY); ctx.stroke();

  let nT = 0, nL = 0, nS = 0;
  cuts.forEach(cut => {{
    const x = (cut.tau / dur) * (W - 24) + 12;
    const effJump = counterfactualReg ? cut.jump_sw * 0.25 : cut.jump_sw;
    const ds2 = (rSW * rSW) - (effJump * effJump);
    let col = '#72cc96';
    if (Math.abs(ds2) <= 0.012) {{ col = '#e5ae5c'; nL++; }}
    else if (ds2 > 0) {{ col = '#72cc96'; nT++; }}
    else {{ col = '#e36874'; nS++; }}

    const bH = Math.max(-midY + 14, Math.min(midY - 14, ds2 * 450));
    ctx.fillStyle = col;
    ctx.fillRect(x - 4, bH >= 0 ? midY - bH : midY, 8, Math.abs(bH) + 2);
  }});

  const tot = Math.max(1, nT + nL + nS);
  document.getElementById('badgeSaccade').textContent = Math.round(100 * nT / tot) + '% Timelike';
  document.getElementById('kvSaccadeSplit').textContent = `${{nT}} Timelike · ${{nL}} Lightlike · ${{nS}} Spacelike`;
  document.getElementById('kvSaccadeRad').textContent = rSW.toFixed(3) + ' screen-widths';
}}

function renderTDACanvas() {{
  const c = document.getElementById('cvTDA');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const eps = parseFloat(document.getElementById('epsSlider').value || 0.75);
  document.getElementById('epsVal').textContent = 'ε = ' + eps.toFixed(2);

  const att = (activeFilm.tda && activeFilm.tda.attractor_2d) || [];
  if (att.length < 2) return;
  const xs = att.map(p => p[0]), ys = att.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs) + 1e-5;
  const minY = Math.min(...ys), maxY = Math.max(...ys) + 1e-5;

  const pts = att.map(p => [
    ((p[0] - minX) / (maxX - minX)) * (W - 44) + 22,
    ((p[1] - minY) / (maxY - minY)) * (H - 36) + 18
  ]);

  const radPx = eps * 26;
  // Draw Vietoris-Rips balls & recurrence chords
  let loopsAtEps = 0;
  ctx.fillStyle = 'rgba(199, 122, 224, 0.06)';
  pts.forEach(([px, py]) => {{
    ctx.beginPath(); ctx.arc(px, py, radPx, 0, Math.PI * 2); ctx.fill();
  }});

  ctx.strokeStyle = 'rgba(86, 194, 230, 0.28)';
  ctx.lineWidth = 1;
  for (let i = 0; i < pts.length; i++) {{
    for (let j = i + 4; j < pts.length; j++) {{
      if (Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) <= radPx * 1.35) {{
        loopsAtEps++;
        ctx.beginPath(); ctx.moveTo(pts[i][0], pts[i][1]); ctx.lineTo(pts[j][0], pts[j][1]); ctx.stroke();
      }}
    }}
  }}

  // Phase trajectory spine
  ctx.beginPath();
  pts.forEach(([px, py], i) => {{
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }});
  ctx.strokeStyle = '#c77ae0';
  ctx.lineWidth = 1.8;
  ctx.stroke();

  const t = activeFilm.tda;
  const liveRegimes = Math.max(1, Math.round(t.beta0_regimes * (1.2 / (eps + 0.4))));
  document.getElementById('badgeTDA').textContent = `(${{liveRegimes}}, ${{loopsAtEps}}, ${{t.beta2_chiasmus.toFixed(2)}})`;
  document.getElementById('kvTDALive').textContent = `${{liveRegimes}} regimes · ${{loopsAtEps}} recurrence chords`;
  document.getElementById('kvTDAChiasmus').textContent = t.beta2_chiasmus.toFixed(3);
}}

function renderPLVCanvas() {{
  const c = document.getElementById('cvPLV');
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const pt = sampleAtTime(activeFilm, curTime) || series[0];
  const sy = activeFilm.synchresis;
  const gain = parseFloat(document.getElementById('cymaticGainSlider').value || 1.2);
  document.getElementById('cymaticGainVal').textContent = gain.toFixed(1) + '×';

  // Left: Polar Phase-Locking Clock
  const cx = 82, cy = H * 0.5, rad = 58;
  ctx.strokeStyle = 'rgba(140, 155, 185, 0.35)';
  ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.stroke();
  const ang = (1 - (pt.plv || 0)) * Math.PI * 1.4;
  const vecLen = Math.max(0.15, pt.plv || 0.1) * rad;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + Math.cos(ang) * vecLen, cy - Math.sin(ang) * vecLen);
  ctx.strokeStyle = '#56c2e6';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.fillStyle = '#ede9e0';
  ctx.font = '10px monospace';
  ctx.fillText('Δθ Phase', cx - 24, cy + rad + 15);

  // Right: PLV(tau) + Armature Resonance curves
  const x0 = 165, wPlot = W - 178;
  ctx.beginPath();
  series.forEach((s, i) => {{
    const x = x0 + (i / Math.max(1, series.length - 1)) * wPlot;
    const y = H - 16 - s.plv * (H - 34);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.strokeStyle = '#56c2e6';
  ctx.lineWidth = 2.0;
  ctx.stroke();

  document.getElementById('badgePLV').textContent = sy.has_audio ? ('PLV = ' + sy.mean_plv.toFixed(3)) : 'Silent Track';
  document.getElementById('kvPLVStats').textContent = `${{sy.peak_plv.toFixed(3)}} / Slip ${{sy.anempathetic_slip.toFixed(3)}}`;
  document.getElementById('kvPLVBands').textContent = `${{(pt.sub_bass || 0).toFixed(2)}} / ${{(pt.centroid || 0).toFixed(2)}}`;
}}

function updateTelemetryAndSTGL() {{
  const pt = sampleAtTime(activeFilm, curTime) || activeFilm.series[0];
  if (!pt) return;
  const modS1 = getModifiedNode(pt);
  const dGrid = counterfactualReg ? pt.d_grid * 0.2 : Math.max(0, pt.d_grid - Math.hypot(userNodeOffset.du, userNodeOffset.dv) * 0.3);
  const rSW = getLiveHorizonSW();
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  let nearCut = cuts[0] || {{ jump_sw: 0.08, tau: 0 }};
  cuts.forEach(c => {{ if (Math.abs(c.tau - curTime) < Math.abs(nearCut.tau - curTime)) nearCut = c; }});
  const effJump = counterfactualReg ? nearCut.jump_sw * 0.25 : nearCut.jump_sw;
  const ds2 = (rSW * rSW) - (effJump * effJump);

  document.getElementById('telTime').textContent = `τ = ${{curTime.toFixed(2)}}s / ${{activeFilm.duration_s}}s`;
  document.getElementById('telNode').textContent = `(${{modS1[0].toFixed(2)}}, ${{modS1[1].toFixed(2)}}, ${{modS1[2].toFixed(2)}})`;
  document.getElementById('telGridErr').textContent = `d = ${{dGrid.toFixed(3)}} ${{dGrid < 0.045 ? 'LOCK' : 'DRIFT'}}`;
  document.getElementById('telHHD').textContent = `${{pt.phi.toFixed(2)}} / ${{pt.psi.toFixed(2)}} / ${{pt.h.toFixed(2)}}`;
  document.getElementById('telW2').textContent = `W₂² ${{pt.w2.toFixed(2)}} · ΔL* ${{activeFilm.wasserstein.mean_chiaroscuro_dl}}`;
  document.getElementById('telSaccade').textContent = `${{ds2 >= 0 ? '+' : ''}}${{ds2.toFixed(3)}} (${{ds2 >= 0 ? 'Timelike' : 'Spacelike'}})`;
  document.getElementById('telBraid').textContent = `FTBE ${{activeFilm.braid.ftbe.toFixed(2)}}`;
  document.getElementById('telPLV').textContent = `PLV ${{pt.plv.toFixed(3)}}`;

  // Update live STGL Linter & JSON preview
  const irObj = JSON.parse(JSON.stringify(STGL_IR[activeFilm.id] || {{}}));
  if (irObj.shots && irObj.shots.length) {{
    irObj.shots[0].spatial_grid.focal_node = [Number(modS1[0].toFixed(3)), Number(modS1[1].toFixed(3))];
    irObj.shots[0].spatial_grid.mean_grid_error = Number(dGrid.toFixed(4));
    irObj.shots[0].transition_out.spacetime_ds2 = Number(ds2.toFixed(4));
    irObj.shots[0].transition_out.type = ds2 >= 0 ? 'eye_trace_match' : 'eisenstein_collision';
  }}
  const linterBadge = document.getElementById('linterStatusBadge');
  if (dGrid <= 0.12 && ds2 >= -0.012) {{
    linterBadge.textContent = 'STGL LINTER: PASS (TIMELIKE LOCK)';
    linterBadge.className = 'badge green';
  }} else {{
    linterBadge.textContent = 'STGL LINTER: COLLISION / DRIFT WARNING';
    linterBadge.className = 'badge rose';
  }}
  document.getElementById('stglLiveBox').textContent = JSON.stringify(irObj, null, 2);
}}

function renderAll(includeManifolds=true) {{
  renderHUD();
  renderMultiModeCanvas();
  renderMasterTimeline();
  updateTelemetryAndSTGL();
  if (includeManifolds) {{
    renderBraidCanvas();
    renderHHDCanvas();
    renderW2Canvas();
    renderSaccadeCanvas();
    renderTDACanvas();
    renderPLVCanvas();
  }}
}}

function tickOrbit() {{
  if (document.getElementById('chkAutoOrbit').checked && !dragging3D && (viewMode === 'prism' || viewMode === 'diff')) {{
    yaw += 0.0032;
    renderMultiModeCanvas();
  }}
  requestAnimationFrame(tickOrbit);
}}

initUI();
selectFilm(activeFilm.id);
requestAnimationFrame(tickOrbit);
</script>
</body>
</html>
"""

    out_html = os.path.join(TENSOR_DIR, "index.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote single-file epistemic visualizer -> {out_html} ({os.path.getsize(out_html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
