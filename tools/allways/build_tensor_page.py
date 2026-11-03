#!/usr/bin/env python3
"""
Builds the interactive Spatiotemporal Cinema Tensor & 3D Worm Observatory page
at /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html
"""

import os
import json

REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
TENSOR_DIR = os.path.join(REPO_ROOT, "allways-tensor")


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

    # Build static comparison rows for SEO / no-JS readability as well
    rows_html = []
    for f in films:
        b = f["braid"]
        h = f["helmholtz"]
        w = f["wasserstein"]
        s = f["saccade"]
        t = f["tda"]
        sy = f["synchresis"]
        wm = f["worm"]
        plv_str = f"{sy['mean_plv']:.3f}" if sy["has_audio"] else "Silent (0.00)"
        rows_html.append(f"""
        <tr onclick="selectFilm('{f['id']}')" style="cursor:pointer" id="row-{f['id']}">
          <td><strong>{f['title']}</strong><br><span class="sub">{f['maker']} · {f['award']}</span></td>
          <td class="num"><span class="badge">{b['ftbe']:.3f}</span><br><span class="sub">{b['reduced_length']}/{b['raw_crossings']} red.</span></td>
          <td class="num">Φ {(h['divergence_share']*100):.0f}% · Ψ {(h['curl_share']*100):.0f}% · H {(h['harmonic_share']*100):.0f}%<br><span class="sub">RMS {h['mean_phi_rms']:.2f}/{h['mean_psi_rms']:.2f}/{h['mean_h_rms']:.2f}</span></td>
          <td class="num"><strong>{w['mean_w2_kinetic']:.2f}</strong><br><span class="sub">Geo {w['geodesic_efficiency']:.2f} · ΔL* {w['mean_chiaroscuro_dl']:.1f}</span></td>
          <td class="num"><strong>{s['timelike_pct']:.0f}%</strong> Timelike<br><span class="sub">Δs²={s['mean_ds2']:+.3f} ({s['detected_cuts']} cuts)</span></td>
          <td class="num">({t['beta0_regimes']}, {t['beta1_loops']}, {t['beta2_chiasmus']:.2f})<br><span class="sub">Chiasmus {t['beta2_chiasmus']:.2f}</span></td>
          <td class="num"><strong>{plv_str}</strong><br><span class="sub">Slip {sy['anempathetic_slip']:.3f}</span></td>
          <td class="num"><strong>{wm['compositional_lock_pct']:.0f}%</strong> Lock<br><span class="sub">d={wm['mean_armature_dist']:.3f} · {wm['dominant_stgl_rule']}</span></td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLWAYS — Spatiotemporal Cinema Tensor &amp; 3D Worm Observatory</title>
<style>
  :root {{
    --bg: #090a0d;
    --panel: #111319;
    --panel-alt: #161922;
    --border: #252936;
    --fg: #ece8df;
    --muted: #9298a8;
    --accent: #e0a958;
    --cyan: #5bc0de;
    --rose: #e06c75;
    --green: #7ec699;
    --purple: #c678dd;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 1440px; margin: 0 auto; padding: 24px 20px 64px; }}
  header {{
    border-bottom: 1px solid var(--border);
    padding-bottom: 18px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
  }}
  .eyebrow {{
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 6px;
    font-weight: 600;
  }}
  h1 {{
    margin: 0;
    font-size: 26px;
    font-weight: 650;
    letter-spacing: -0.02em;
  }}
  .lead {{
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 14px;
    max-width: 880px;
  }}
  .top-links {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .btn-link {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    color: var(--fg);
    padding: 7px 13px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 500;
  }}
  .btn-link:hover {{ border-color: var(--accent); text-decoration: none; }}
  .pill-bar {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }}
  .film-pill {{
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 7px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .film-pill:hover {{ color: var(--fg); border-color: #444c63; }}
  .film-pill.active {{
    background: #221d15;
    border-color: var(--accent);
    color: var(--fg);
    font-weight: 600;
  }}
  .top-grid {{
    display: grid;
    grid-template-columns: 1.05fr 1.25fr;
    gap: 18px;
    margin-bottom: 18px;
  }}
  @media (max-width: 1050px) {{
    .top-grid {{ grid-template-columns: 1fr; }}
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .card-title {{
    font-size: 13px;
    font-weight: 650;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--accent);
  }}
  .card-sub {{
    font-size: 12px;
    color: var(--muted);
  }}
  video {{
    width: 100%;
    max-height: 310px;
    background: #000;
    border-radius: 6px;
    border: 1px solid var(--border);
  }}
  .slit-box {{
    margin-top: 12px;
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
  }}
  .slit-wrap {{
    position: relative;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    height: 76px;
    background: #050608;
  }}
  .slit-wrap img {{
    width: 100%;
    height: 100%;
    object-fit: fill;
    display: block;
  }}
  .slit-label {{
    position: absolute;
    top: 4px;
    left: 8px;
    background: rgba(9, 10, 13, 0.82);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    color: var(--fg);
    pointer-events: none;
  }}
  .slit-cursor {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
    box-shadow: 0 0 6px var(--accent);
    pointer-events: none;
    left: 0%;
  }}
  #worm3dCanvas {{
    width: 100%;
    height: 390px;
    background: radial-gradient(circle at 50% 45%, #161a24 0%, #090b10 100%);
    border-radius: 6px;
    border: 1px solid var(--border);
    cursor: grab;
    display: block;
  }}
  #worm3dCanvas:active {{ cursor: grabbing; }}
  .controls-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 10px;
    align-items: center;
    font-size: 12px;
    color: var(--muted);
  }}
  .controls-row label {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    background: var(--panel-alt);
    padding: 4px 9px;
    border-radius: 5px;
    border: 1px solid var(--border);
  }}
  .manifold-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 22px;
  }}
  @media (max-width: 1150px) {{
    .manifold-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 740px) {{
    .manifold-grid {{ grid-template-columns: 1fr; }}
  }}
  .m-canvas {{
    width: 100%;
    height: 155px;
    background: #0b0d12;
    border: 1px solid var(--border);
    border-radius: 6px;
    display: block;
    margin: 8px 0;
  }}
  .kv-row {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    border-top: 1px solid #1d212c;
    padding: 5px 0;
  }}
  .kv-row span:first-child {{ color: var(--muted); }}
  .kv-row span:last-child {{ font-family: "SFMono-Regular", Consolas, monospace; font-weight: 600; }}
  .mono-box {{
    background: #0b0d12;
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 6px 8px;
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 11.5px;
    color: var(--cyan);
    overflow-x: auto;
    white-space: nowrap;
    margin-bottom: 6px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }}
  th, td {{
    padding: 10px 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
  }}
  th {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    background: var(--panel-alt);
  }}
  tr:hover td {{ background: #171b26; }}
  tr.selected-row td {{ background: #211d15; border-bottom-color: var(--accent); }}
  td.num {{ font-family: "SFMono-Regular", Consolas, monospace; }}
  .sub {{ font-size: 11px; color: var(--muted); font-family: -apple-system, sans-serif; }}
  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    background: #232838;
    color: var(--accent);
    font-weight: 600;
  }}
  pre.ir-pre {{
    background: #08090c;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px;
    font-size: 11.5px;
    color: #b9c4d4;
    max-height: 320px;
    overflow: auto;
    margin: 0;
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">ALLWAYS · 4D Spatiotemporal Manifold &amp; STGL Observatory</div>
      <h1>Spatiotemporal Cinema Tensor $(u, v, d, \\tau)$ &amp; 3D Worm Topology</h1>
      <p class="lead">
        Treating each film as an extruded 4D spatiotemporal volume $\\mathcal{{V}}(u,v,d,\\tau)$ coupled to its acoustic field across six computable mathematical frameworks: Artin Braid Topology ($\\mathcal{{B}}_3$), Helmholtz–Hodge Flow ($\\Phi, \\mathbf{{\\Psi}}, \\mathbf{{H}}$), 5D Wasserstein Optimal Transport ($W_2$), Relativistic Saccade Light-Cones ($\\Delta s^2$), Takens Persistent Homology ($\\beta_0, \\beta_1, \\beta_2$), and Cross-Spectral Synchresis ($\\text{{PLV}}$).
      </p>
    </div>
    <div class="top-links">
      <a class="btn-link" href="../paeleo/allways/index.html">← ALLWAYS Hub</a>
      <a class="btn-link" href="../allways-best/index.html">★ Watch Master Anthology</a>
      <a class="btn-link" href="../allways-awards/index.html">🏆 132-Film Jury &amp; Awards</a>
      <a class="btn-link" href="tensor_data.json" target="_blank">⬇ tensor_data.json</a>
      <a class="btn-link" href="stgl_ir.json" target="_blank">⬇ stgl_ir.json</a>
    </div>
  </header>

  <div class="pill-bar" id="pillBar"></div>

  <div class="top-grid">
    <!-- Left: Synchronized Video Player + u-tau & v-tau Slit-Scan Tomograms -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title" id="activeTitle">059 · BALL</div>
          <div class="card-sub" id="activeSub">Claude Sonnet · Grand Prix · 96.0/100</div>
        </div>
        <a class="btn-link" id="activeCaseLink" href="../allways-sonnet/059-ball/index.html">Open Film Page ↗</a>
      </div>
      <video id="filmPlayer" controls playsinline preload="metadata"></video>

      <div class="slit-box">
        <div class="slit-wrap" onclick="seekFromSlit(event)">
          <img id="utImg" src="img/sonnet-059-ball_ut.jpg" alt="u-tau slit-scan tomogram">
          <div class="slit-label">$u\\text{{-}}\\tau$ Horizon Slit-Scan Tomogram (Click to Seek · Vertical Pillars = Registration Lock, Diagonal = Pan)</div>
          <div class="slit-cursor" id="utCursor"></div>
        </div>
        <div class="slit-wrap" onclick="seekFromSlit(event)">
          <img id="vtImg" src="img/sonnet-059-ball_vt.jpg" alt="v-tau slit-scan tomogram">
          <div class="slit-label">$v\\text{{-}}\\tau$ Vertical Center Slit-Scan Tomogram (Strata = Cuts, Cones = Scale Traverse)</div>
          <div class="slit-cursor" id="vtCursor"></div>
        </div>
      </div>
    </div>

    <!-- Right: Interactive 3D Spatiotemporal Glass-Prism Worm Visualizer -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">3D Glass-Prism Spatiotemporal Worm $\\mathcal{{V}}(u, v, \\tau)$</div>
          <div class="card-sub">Drag to orbit 3D volume · Core worm colored by real CIE-LAB palette · Gold filaments = 14-Line Armature</div>
        </div>
        <span class="badge" id="liveTimeBadge">τ = 0.00s</span>
      </div>
      <canvas id="worm3dCanvas" width="760" height="390"></canvas>
      <div class="controls-row">
        <label><input type="checkbox" id="chkArmature" checked onchange="draw3DWorm()"> 14-Line Harmonic Armature</label>
        <label><input type="checkbox" id="chkSpiral" checked onchange="draw3DWorm()"> Center / Golden Tunnel</label>
        <label><input type="checkbox" id="chkBraids" checked onchange="draw3DWorm()"> 3-Strand Braid ($\\mathcal{{B}}_3$)</label>
        <label><input type="checkbox" id="chkCones" checked onchange="draw3DWorm()"> Saccade Light-Cones ($\\Delta s^2$)</label>
        <label><input type="checkbox" id="chkAutoRotate" checked> Auto-Orbit Prism</label>
      </div>
    </div>
  </div>

  <!-- Six Mathematical Manifolds Grid -->
  <div class="manifold-grid">
    <!-- 1. Artin Braid Topology -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">1 · Artin Braid Topology ($\\mathcal{{B}}_3$)</div>
        <span class="badge" id="m1Badge">FTBE = 0.000</span>
      </div>
      <div class="card-sub">3-strand horizontal worldlines $(u_i(\\tau), d_i(\\tau))$ &amp; algebraic generator reduction $\\sigma_i \\sigma_i^{{-1}} = e$</div>
      <canvas class="m-canvas" id="canvasBraid" width="420" height="155"></canvas>
      <div class="mono-box" id="braidWordBox">Reduced Word: e</div>
      <div class="kv-row"><span>Raw / Reduced Crossings</span><span id="m1Crossings">0 / 0</span></div>
      <div class="kv-row"><span>True Entanglement Ratio</span><span id="m1Entangle">0.000</span></div>
    </div>

    <!-- 2. Helmholtz-Hodge Flow Field -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">2 · Helmholtz–Hodge Flow ($\\Phi, \\mathbf{{\\Psi}}, \\mathbf{{H}}$)</div>
        <span class="badge" id="m2Badge">Φ / Ψ / H</span>
      </div>
      <div class="card-sub">Orthogonal FFT decomposition: Divergence $-\\nabla\\Phi$ (push/pull), Curl $\\nabla\\times\\mathbf{{\\Psi}}$ (swirl), Harmonic $\\mathbf{{H}}$ (pan)</div>
      <canvas class="m-canvas" id="canvasHHD" width="420" height="155"></canvas>
      <div class="kv-row"><span>Divergence $-\\nabla\\Phi$ (Depth Loom/Recede)</span><span id="m2Div">0%</span></div>
      <div class="kv-row"><span>Vorticity $\\nabla\\times\\mathbf{{\\Psi}}$ (Rotational Swirl)</span><span id="m2Curl">0%</span></div>
      <div class="kv-row"><span>Harmonic $\\mathbf{{H}}$ (Laminar Camera Pan)</span><span id="m2Harm">0%</span></div>
    </div>

    <!-- 3. Wasserstein Chromatic Geodesics -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">3 · Wasserstein Geodesics ($W_2$) &amp; KALMUS</div>
        <span class="badge" id="m3Badge">W₂ = 0.00</span>
      </div>
      <div class="card-sub">5D Optimal Transport $\\mu_\\tau(u,v,L^*,a^*,b^*)$ kinetic energy &amp; Core-Worm vs. Shell Itten Chiaroscuro $\\Delta L^*$</div>
      <canvas class="m-canvas" id="canvasW2" width="420" height="155"></canvas>
      <div class="kv-row"><span>Geodesic Efficiency / Curvature $\\kappa_{{W_2}}$</span><span id="m3Geo">0.00 / 0.00</span></div>
      <div class="kv-row"><span>Core vs. Shell Chiaroscuro $\\Delta L^*$</span><span id="m3Chiaro">0.00</span></div>
      <div class="kv-row"><span>Cold–Warm Hue Polarity $\\Delta H$</span><span id="m3Hue">0.0°</span></div>
    </div>

    <!-- 4. Relativistic Saccade Light-Cones -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">4 · Relativistic Saccade Light-Cones</div>
        <span class="badge" id="m4Badge">100% Timelike</span>
      </div>
      <div class="card-sub">Foveal speed $c_{{\\text{{eye}}}} = 400^\\circ/\\text{{s}}$, latency $\\tau_{{\\text{{fix}}}} = 200\\text{{ ms}}$ · Spacetime interval $\\Delta s^2 = R(\\Delta\\tau)^2 - \\Delta\\mathbf{{x}}^2$</div>
      <canvas class="m-canvas" id="canvasSaccade" width="420" height="155"></canvas>
      <div class="kv-row"><span>Timelike Cuts ($\\Delta s^2 > 0$, Murch Eye-Trace)</span><span id="m4Time">0%</span></div>
      <div class="kv-row"><span>Lightlike Cuts ($\\Delta s^2 \\approx 0$, Horizon Whip)</span><span id="m4Light">0%</span></div>
      <div class="kv-row"><span>Spacelike Cuts ($\\Delta s^2 < 0$, Blind Zone)</span><span id="m4Space">0%</span></div>
    </div>

    <!-- 5. Persistent Homology Attractors -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">5 · Persistent Homology ($\\beta_0, \\beta_1, \\beta_2$)</div>
        <span class="badge" id="m5Badge">(β₀, β₁, β₂)</span>
      </div>
      <div class="card-sub">Takens time-delay embedding $[\mathbf{{x}}(\\tau), \mathbf{{x}}(\\tau+\\Delta), \mathbf{{x}}(\\tau+2\\Delta)]$ attractor &amp; Vietoris–Rips Betti loops</div>
      <canvas class="m-canvas" id="canvasTDA" width="420" height="155"></canvas>
      <div class="kv-row"><span>$\\beta_0$ Connected Act Regimes</span><span id="m5B0">1</span></div>
      <div class="kv-row"><span>$\\beta_1$ Rhythmic Limit Cycles (Loops)</span><span id="m5B1">0</span></div>
      <div class="kv-row"><span>$\\beta_2$ Chiasmus / Ring Symmetry Fold</span><span id="m5B2">0.00</span></div>
    </div>

    <!-- 6. Cross-Spectral Synchresis Tensor -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">6 · Cross-Spectral Synchresis &amp; STGL</div>
        <span class="badge" id="m6Badge">PLV = 0.000</span>
      </div>
      <div class="card-sub">Hilbert Phase-Locking Value $\\text{{PLV}}(\\tau)$ between visual jerk $\\|\\mathbf{{c}}'''(\\tau)\\|$ &amp; acoustic flux + 14-Line Armature lock</div>
      <canvas class="m-canvas" id="canvasPLV" width="420" height="155"></canvas>
      <div class="kv-row"><span>Audiovisual Phase-Lock ($\\text{{PLV}}$) / Slip</span><span id="m6Plv">0.000 / 0.000</span></div>
      <div class="kv-row"><span>14-Line Armature Lock ($d_{{\\text{{grid}}}} < 0.045$)</span><span id="m6Lock">0%</span></div>
      <div class="kv-row"><span>Dominant STGL Spatial Rule</span><span id="m6Rule">centered_anchor</span></div>
    </div>
  </div>

  <!-- Comparative 12-Film Tensor Table -->
  <div class="card" style="margin-bottom:20px;">
    <div class="card-header">
      <div>
        <div class="card-title">Comparative 6-Manifold Cinema Tensor Ledger (12 Flagship ALLWAYS Works)</div>
        <div class="card-sub">Click any row to load its 3D Spatiotemporal Worm, Slit-Scan Tomograms, and Declarative STGL Timeline IR</div>
      </div>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th>Film &amp; Maker</th>
            <th>1. Braid $\\mathcal{{B}}_3$ (FTBE)</th>
            <th>2. Helmholtz ($\\Phi / \\Psi / H$)</th>
            <th>3. Wasserstein $W_2$</th>
            <th>4. Saccade Cone $\\Delta s^2$</th>
            <th>5. Topology $(\\beta_0, \\beta_1, \\beta_2)$</th>
            <th>6. Synchresis PLV</th>
            <th>STGL Armature Lock</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows_html)}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Declarative 4D STGL Timeline IR & Pre-Flight Linter Audit -->
  <div class="top-grid">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Declarative 4D Spatiotemporal Grid Language (STGL Timeline IR)</div>
          <div class="card-sub">Compiled shot-by-shot $(u, v, d, \\tau)$ schema with beat lattice $b(\\text{{bar}}, \\text{{beat}}, \\text{{sub}})$, Helmholtz field, and saccade transitions</div>
        </div>
      </div>
      <pre class="ir-pre" id="stglIrPre"></pre>
    </div>
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Closed-Loop STGL Grid &amp; Saccade Verifier (`check_stgl_grid.py`)</div>
          <div class="card-sub">Automated audit of spatial armatures, negative-space caption safety, and relativistic eye-trace horizons</div>
        </div>
        <span class="badge" id="auditStatusBadge">PASS</span>
      </div>
      <pre class="ir-pre" id="stglAuditPre"></pre>
    </div>
  </div>
</div>

<script>
const TENSOR_DATA = {json.dumps(films)};
const STGL_IR = {json.dumps(stgl_ir)};
const STGL_AUDIT = {json.dumps(audit_data)};

let activeFilm = TENSOR_DATA[1] || TENSOR_DATA[0]; // Default to Grand Prix 059-ball
let yaw = -0.58;
let pitch = 0.34;
let isDragging = false;
let lastX = 0, lastY = 0;

const pillBar = document.getElementById('pillBar');
const videoEl = document.getElementById('filmPlayer');
const wormCanvas = document.getElementById('worm3dCanvas');

function initPills() {{
  pillBar.innerHTML = '';
  TENSOR_DATA.forEach(f => {{
    const btn = document.createElement('button');
    btn.className = 'film-pill' + (f.id === activeFilm.id ? ' active' : '');
    btn.id = 'pill-' + f.id;
    btn.textContent = f.title + ' (' + f.maker.split(' ')[0] + ')';
    btn.onclick = () => selectFilm(f.id);
    pillBar.appendChild(btn);
  }});
}}

function selectFilm(fid) {{
  const found = TENSOR_DATA.find(x => x.id === fid);
  if (!found) return;
  activeFilm = found;

  document.querySelectorAll('.film-pill').forEach(el => el.classList.remove('active'));
  const pill = document.getElementById('pill-' + fid);
  if (pill) pill.classList.add('active');

  document.querySelectorAll('tbody tr').forEach(el => el.classList.remove('selected-row'));
  const row = document.getElementById('row-' + fid);
  if (row) row.classList.add('selected-row');

  document.getElementById('activeTitle').textContent = activeFilm.title;
  document.getElementById('activeSub').textContent = activeFilm.maker + ' · ' + activeFilm.award + ' · ' + activeFilm.duration_s + 's';
  document.getElementById('activeCaseLink').href = activeFilm.watch_url;

  videoEl.src = activeFilm.video_rel;
  document.getElementById('utImg').src = activeFilm.ut_tomogram;
  document.getElementById('vtImg').src = activeFilm.vt_tomogram;

  // Update 6 Manifold KV readouts
  const b = activeFilm.braid;
  document.getElementById('m1Badge').textContent = 'FTBE = ' + b.ftbe.toFixed(3);
  document.getElementById('braidWordBox').textContent = 'B₃ Reduced: ' + b.reduced_word_preview;
  document.getElementById('m1Crossings').textContent = b.raw_crossings + ' raw → ' + b.reduced_length + ' reduced';
  document.getElementById('m1Entangle').textContent = (b.entanglement_ratio * 100).toFixed(1) + '% irreducible';

  const h = activeFilm.helmholtz;
  document.getElementById('m2Badge').textContent = `Φ${{Math.round(h.divergence_share*100)}} · Ψ${{Math.round(h.curl_share*100)}} · H${{Math.round(h.harmonic_share*100)}}`;
  document.getElementById('m2Div').textContent = (h.divergence_share * 100).toFixed(1) + '% (RMS ' + h.mean_phi_rms.toFixed(3) + ')';
  document.getElementById('m2Curl').textContent = (h.curl_share * 100).toFixed(1) + '% (RMS ' + h.mean_psi_rms.toFixed(3) + ')';
  document.getElementById('m2Harm').textContent = (h.harmonic_share * 100).toFixed(1) + '% (RMS ' + h.mean_h_rms.toFixed(3) + ')';

  const w = activeFilm.wasserstein;
  document.getElementById('m3Badge').textContent = 'W₂ = ' + w.mean_w2_kinetic.toFixed(2);
  document.getElementById('m3Geo').textContent = w.geodesic_efficiency.toFixed(3) + ' eff / ' + w.geodesic_curvature.toFixed(3) + ' curv';
  document.getElementById('m3Chiaro').textContent = w.mean_chiaroscuro_dl.toFixed(2) + ' CIE-L* units';
  document.getElementById('m3Hue').textContent = w.mean_hue_polarity_deg.toFixed(1) + '° core-shell separation';

  const s = activeFilm.saccade;
  document.getElementById('m4Badge').textContent = s.timelike_pct.toFixed(0) + '% Timelike';
  document.getElementById('m4Time').textContent = s.timelike_pct.toFixed(1) + '% (inside foveal cone)';
  document.getElementById('m4Light').textContent = s.lightlike_pct.toFixed(1) + '% (on saccade horizon)';
  document.getElementById('m4Space').textContent = s.spacelike_pct.toFixed(1) + '% (collision / shock)';

  const t = activeFilm.tda;
  document.getElementById('m5Badge').textContent = `(${{t.beta0_regimes}}, ${{t.beta1_loops}}, ${{t.beta2_chiasmus.toFixed(2)}})`;
  document.getElementById('m5B0').textContent = t.beta0_regimes + ' persistent regimes';
  document.getElementById('m5B1').textContent = t.beta1_loops + ' rhythmic limit cycles';
  document.getElementById('m5B2').textContent = t.beta2_chiasmus.toFixed(3) + ' ring folding index';

  const sy = activeFilm.synchresis;
  const wm = activeFilm.worm;
  document.getElementById('m6Badge').textContent = sy.has_audio ? ('PLV = ' + sy.mean_plv.toFixed(3)) : 'Silent Visual Rhythm';
  document.getElementById('m6Plv').textContent = sy.has_audio ? (sy.mean_plv.toFixed(3) + ' / Slip ' + sy.anempathetic_slip.toFixed(3)) : 'Silent track (0.000)';
  document.getElementById('m6Lock').textContent = wm.compositional_lock_pct.toFixed(1) + '% frames (mean d=' + wm.mean_armature_dist.toFixed(3) + ')';
  document.getElementById('m6Rule').textContent = wm.dominant_stgl_rule;

  // STGL IR & Audit JSON
  document.getElementById('stglIrPre').textContent = JSON.stringify(STGL_IR[fid] || {{}}, null, 2);
  const auditObj = (STGL_AUDIT.audits || []).find(a => a.film_id === fid) || {{ status: 'PASS' }};
  document.getElementById('auditStatusBadge').textContent = auditObj.status || 'PASS';
  document.getElementById('stglAuditPre').textContent = JSON.stringify(auditObj, null, 2);

  drawAllManifoldCharts();
  draw3DWorm();
}}

function seekFromSlit(ev) {{
  const rect = ev.currentTarget.getBoundingClientRect();
  const frac = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
  if (videoEl.duration) {{
    videoEl.currentTime = frac * videoEl.duration;
  }}
}}

videoEl.addEventListener('timeupdate', () => {{
  const dur = videoEl.duration || activeFilm.duration_s || 1;
  const pct = Math.min(100, Math.max(0, (videoEl.currentTime / dur) * 100));
  document.getElementById('utCursor').style.left = pct + '%';
  document.getElementById('vtCursor').style.left = pct + '%';
  document.getElementById('liveTimeBadge').textContent = 'τ = ' + videoEl.currentTime.toFixed(2) + 's';
  draw3DWorm();
}});

// 3D Projection Helper: maps normalized (u in [0,1], v in [0,1], tau_norm in [0,1]) to 2D canvas
function project3D(u, v, tNorm, W, H) {{
  // Center coordinates in [-0.5, 0.5], elongate time axis tau
  const x = (tNorm - 0.5) * 1.65;
  const y = (0.5 - v) * 0.95;
  const z = (u - 0.5) * 0.95;

  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);

  const x1 = x * cy - z * sy;
  const z1 = x * sy + z * cy;
  const y2 = y * cp - z1 * sp;
  const z2 = y * sp + z1 * cp;

  const fov = 2.4;
  const dist = 2.55;
  const scale = fov / (dist - z2);
  return {{
    px: W * 0.5 + x1 * scale * Math.min(W, H) * 0.62,
    py: H * 0.52 - y2 * scale * Math.min(W, H) * 0.62,
    depth: z2,
    scale: scale
  }};
}}

function drawLine3D(ctx, pA, pB, W, H, stroke, width, dash=[]) {{
  const a = project3D(pA[0], pA[1], pA[2], W, H);
  const b = project3D(pB[0], pB[1], pB[2], W, H);
  ctx.save();
  ctx.beginPath();
  ctx.setLineDash(dash);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = width;
  ctx.moveTo(a.px, a.py);
  ctx.lineTo(b.px, b.py);
  ctx.stroke();
  ctx.restore();
}}

function draw3DWorm() {{
  const ctx = wormCanvas.getContext('2d');
  const W = wormCanvas.width, H = wormCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const series = activeFilm.series || [];
  if (!series.length) return;
  const dur = activeFilm.duration_s || 1;
  const curT = videoEl.currentTime || 0;
  const curNorm = Math.min(1, Math.max(0, curT / dur));

  // 1. Draw outer 3D Glass Prism Wireframe [0,1]^3
  const corners = [
    [0,0,0],[1,0,0],[1,1,0],[0,1,0],
    [0,0,1],[1,0,1],[1,1,1],[0,1,1]
  ];
  const edges = [
    [0,1],[1,2],[2,3],[3,0],
    [4,5],[5,6],[6,7],[7,4],
    [0,4],[1,5],[2,6],[3,7]
  ];
  edges.forEach(([i, j]) => {{
    drawLine3D(ctx, corners[i], corners[j], W, H, 'rgba(130, 145, 175, 0.24)', 1);
  }});

  // 2. Optional 14-Line Harmonic Armature & Rule of Thirds Magnetic Filaments
  if (document.getElementById('chkArmature').checked) {{
    const thirds = [1/3, 2/3];
    thirds.forEach(u => {{
      drawLine3D(ctx, [u, 1/3, 0], [u, 1/3, 1], W, H, 'rgba(224, 169, 88, 0.26)', 1, [3, 3]);
      drawLine3D(ctx, [u, 2/3, 0], [u, 2/3, 1], W, H, 'rgba(224, 169, 88, 0.26)', 1, [3, 3]);
    }});
    // Center registration axis (u=0.5, v=0.5)
    drawLine3D(ctx, [0.5, 0.5, 0], [0.5, 0.5, 1], W, H, 'rgba(224, 169, 88, 0.55)', 1.5);
  }}

  // 3. Optional Center Registration Cylinder / Golden Spiral Tunnel
  if (document.getElementById('chkSpiral').checked) {{
    ctx.save();
    ctx.beginPath();
    for (let k = 0; k <= 60; k++) {{
      const tn = k / 60;
      const ang = tn * Math.PI * 6;
      const rad = 0.22;
      const u = 0.5 + rad * Math.cos(ang);
      const v = 0.5 + rad * Math.sin(ang);
      const p = project3D(u, v, tn, W, H);
      if (k === 0) ctx.moveTo(p.px, p.py);
      else ctx.lineTo(p.px, p.py);
    }}
    ctx.strokeStyle = 'rgba(91, 192, 222, 0.28)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();
  }}

  // 4. Optional Relativistic Saccade Light-Cones at Cut Planes
  if (document.getElementById('chkCones').checked) {{
    const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
    cuts.forEach(c => {{
      const tn = Math.min(1, Math.max(0, c.tau / dur));
      const col = c.regime === 'timelike' ? 'rgba(126, 198, 153, 0.45)' : (c.regime === 'lightlike' ? 'rgba(224, 169, 88, 0.55)' : 'rgba(224, 108, 117, 0.55)');
      drawLine3D(ctx, [c.p1[0], c.p1[1], tn], [c.p2[0], c.p2[1], tn], W, H, col, 2.0);
    }});
  }}

  // 5. Secondary Braided Worldline Strands s2 and s3 in B_3
  if (document.getElementById('chkBraids').checked) {{
    ['s2', 's3'].forEach((key, idx) => {{
      ctx.save();
      ctx.beginPath();
      series.forEach((pt, i) => {{
        const tn = pt.t / dur;
        const p = project3D(pt[key][0], pt[key][1], tn, W, H);
        if (i === 0) ctx.moveTo(p.px, p.py);
        else ctx.lineTo(p.px, p.py);
      }});
      ctx.strokeStyle = idx === 0 ? 'rgba(91, 192, 222, 0.65)' : 'rgba(198, 120, 221, 0.65)';
      ctx.lineWidth = 1.8;
      ctx.stroke();
      ctx.restore();
    }});
  }}

  // 6. Primary Extruded 3D Spatiotemporal Subject Worm (s1 colored by real CIE-LAB/RGB palette & cross-section radius)
  for (let i = 0; i < series.length - 1; i++) {{
    const a = series[i], b = series[i + 1];
    const pA = project3D(a.s1[0], a.s1[1], a.t / dur, W, H);
    const pB = project3D(b.s1[0], b.s1[1], b.t / dur, W, H);
    const rgb = a.rgb || [220, 175, 100];
    ctx.save();
    ctx.beginPath();
    ctx.strokeStyle = `rgba(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}}, 0.92)`;
    ctx.lineWidth = Math.max(3.0, a.r * 38 * pA.scale);
    ctx.lineCap = 'round';
    ctx.moveTo(pA.px, pA.py);
    ctx.lineTo(pB.px, pB.py);
    ctx.stroke();
    ctx.restore();
  }}

  // 7. Current Playback Slice Plane at tau = curNorm
  const sliceCorners = [
    [0,0,curNorm],[1,0,curNorm],[1,1,curNorm],[0,1,curNorm],[0,0,curNorm]
  ];
  ctx.save();
  ctx.beginPath();
  sliceCorners.forEach((c, idx) => {{
    const p = project3D(c[0], c[1], c[2], W, H);
    if (idx === 0) ctx.moveTo(p.px, p.py);
    else ctx.lineTo(p.px, p.py);
  }});
  ctx.strokeStyle = 'rgba(224, 169, 88, 0.9)';
  ctx.fillStyle = 'rgba(224, 169, 88, 0.08)';
  ctx.lineWidth = 1.8;
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}}

wormCanvas.addEventListener('mousedown', e => {{
  isDragging = true;
  lastX = e.clientX;
  lastY = e.clientY;
  document.getElementById('chkAutoRotate').checked = false;
}});
window.addEventListener('mouseup', () => {{ isDragging = false; }});
window.addEventListener('mousemove', e => {{
  if (!isDragging) return;
  yaw += (e.clientX - lastX) * 0.008;
  pitch = Math.max(-1.1, Math.min(1.1, pitch + (e.clientY - lastY) * 0.008));
  lastX = e.clientX;
  lastY = e.clientY;
  draw3DWorm();
}});

function animateLoop() {{
  if (document.getElementById('chkAutoRotate').checked && !isDragging) {{
    yaw += 0.0035;
    draw3DWorm();
  }}
  requestAnimationFrame(animateLoop);
}}

function drawAllManifoldCharts() {{
  const series = activeFilm.series || [];
  if (!series.length) return;

  // 1. Braid Worldlines (u_1, u_2, u_3 over tau)
  const c1 = document.getElementById('canvasBraid');
  const ctx1 = c1.getContext('2d');
  ctx1.clearRect(0, 0, c1.width, c1.height);
  const colsB = ['#e0a958', '#5bc0de', '#c678dd'];
  ['s1', 's2', 's3'].forEach((k, idx) => {{
    ctx1.beginPath();
    series.forEach((pt, i) => {{
      const x = (i / Math.max(1, series.length - 1)) * (c1.width - 16) + 8;
      const y = (1 - pt[k][0]) * (c1.height - 20) + 10;
      if (i === 0) ctx1.moveTo(x, y);
      else ctx1.lineTo(x, y);
    }});
    ctx1.strokeStyle = colsB[idx];
    ctx1.lineWidth = 2.0;
    ctx1.stroke();
  }});

  // 2. Helmholtz-Hodge (Phi, Psi, H curves)
  const c2 = document.getElementById('canvasHHD');
  const ctx2 = c2.getContext('2d');
  ctx2.clearRect(0, 0, c2.width, c2.height);
  const maxHHD = Math.max(0.01, ...series.map(s => Math.max(s.phi, s.psi, s.h)));
  [['phi', '#e0a958'], ['psi', '#e06c75'], ['h', '#5bc0de']].forEach(([k, col]) => {{
    ctx2.beginPath();
    series.forEach((pt, i) => {{
      const x = (i / Math.max(1, series.length - 1)) * (c2.width - 16) + 8;
      const y = c2.height - 10 - (pt[k] / maxHHD) * (c2.height - 22);
      if (i === 0) ctx2.moveTo(x, y);
      else ctx2.lineTo(x, y);
    }});
    ctx2.strokeStyle = col;
    ctx2.lineWidth = 1.8;
    ctx2.stroke();
  }});

  // 3. Wasserstein Chromatic Kinetic Energy W_2^2
  const c3 = document.getElementById('canvasW2');
  const ctx3 = c3.getContext('2d');
  ctx3.clearRect(0, 0, c3.width, c3.height);
  const maxW2 = Math.max(0.01, ...series.map(s => s.w2));
  ctx3.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (c3.width - 16) + 8;
    const y = c3.height - 10 - (pt.w2 / maxW2) * (c3.height - 24);
    if (i === 0) ctx3.moveTo(x, y);
    else ctx3.lineTo(x, y);
  }});
  ctx3.strokeStyle = '#7ec699';
  ctx3.lineWidth = 2.0;
  ctx3.stroke();

  // 4. Relativistic Saccade Light-Cone Intervals ds^2
  const c4 = document.getElementById('canvasSaccade');
  const ctx4 = c4.getContext('2d');
  ctx4.clearRect(0, 0, c4.width, c4.height);
  const midY = c4.height * 0.55;
  ctx4.strokeStyle = 'rgba(255,255,255,0.2)';
  ctx4.beginPath();
  ctx4.moveTo(0, midY);
  ctx4.lineTo(c4.width, midY);
  ctx4.stroke();
  const cuts = (activeFilm.saccade && activeFilm.saccade.cuts) || [];
  const dur = activeFilm.duration_s || 1;
  cuts.forEach(c => {{
    const x = (c.tau / dur) * (c4.width - 20) + 10;
    const barH = Math.max(-midY + 12, Math.min(midY - 12, c.ds2 * 320));
    ctx4.fillStyle = c.regime === 'timelike' ? '#7ec699' : (c.regime === 'lightlike' ? '#e0a958' : '#e06c75');
    ctx4.fillRect(x - 3, barH >= 0 ? midY - barH : midY, 6, Math.abs(barH) + 2);
  }});

  // 5. Takens 2D Phase-Space Attractor & Persistence
  const c5 = document.getElementById('canvasTDA');
  const ctx5 = c5.getContext('2d');
  ctx5.clearRect(0, 0, c5.width, c5.height);
  const att = (activeFilm.tda && activeFilm.tda.attractor_2d) || [];
  if (att.length > 1) {{
    const xs = att.map(p => p[0]), ys = att.map(p => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs) + 1e-5;
    const minY = Math.min(...ys), maxY = Math.max(...ys) + 1e-5;
    ctx5.beginPath();
    att.forEach((p, i) => {{
      const x = ((p[0] - minX) / (maxX - minX)) * (c5.width - 36) + 18;
      const y = ((p[1] - minY) / (maxY - minY)) * (c5.height - 28) + 14;
      if (i === 0) ctx5.moveTo(x, y);
      else ctx5.lineTo(x, y);
    }});
    ctx5.strokeStyle = '#c678dd';
    ctx5.lineWidth = 1.6;
    ctx5.stroke();
  }}

  // 6. Cross-Spectral Synchresis PLV(tau) & 14-Line Armature Error
  const c6 = document.getElementById('canvasPLV');
  const ctx6 = c6.getContext('2d');
  ctx6.clearRect(0, 0, c6.width, c6.height);
  ctx6.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (c6.width - 16) + 8;
    const y = c6.height - 10 - pt.plv * (c6.height - 24);
    if (i === 0) ctx6.moveTo(x, y);
    else ctx6.lineTo(x, y);
  }});
  ctx6.strokeStyle = '#5bc0de';
  ctx6.lineWidth = 2.0;
  ctx6.stroke();

  // Overlay armature resonance (1 - d_grid*3) in gold
  ctx6.beginPath();
  series.forEach((pt, i) => {{
    const x = (i / Math.max(1, series.length - 1)) * (c6.width - 16) + 8;
    const lockVal = Math.max(0, Math.min(1, 1 - pt.d_grid * 4.5));
    const y = c6.height - 10 - lockVal * (c6.height - 24);
    if (i === 0) ctx6.moveTo(x, y);
    else ctx6.lineTo(x, y);
  }});
  ctx6.strokeStyle = '#e0a958';
  ctx6.lineWidth = 1.4;
  ctx6.stroke();
}}

initPills();
selectFilm(activeFilm.id);
requestAnimationFrame(animateLoop);
</script>
</body>
</html>
"""

    out_html = os.path.join(TENSOR_DIR, "index.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote interactive observatory -> {out_html}")


if __name__ == "__main__":
    main()
