#!/usr/bin/env python3
"""
Builds a Clean, Mobile-First, Zero-Chart-Junk Screening Room & Visual Composition Studio at:
  /Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/index.html

Design Principles (Edward Tufte / High Data-Ink Ratio, Mobile-First):
  1. Film First: Clean 16:9 player with ZERO default clutter over the picture.
  2. One Guide at a Time: Tap any of the 8 Shape pills (Golden Spiral, Frame-in-Frame,
     S-Curve, Symmetry, Rule of Thirds, Centered, V-Shape, Negative Space) to project
     that single clean viewfinder guide over the video—or leave it Off.
  3. Real Photographic Evidence Only (No BS / No Fake Sci-Fi Telemetry):
     - Real photographic slit-scan time strip (actual pixels sliced from the film).
     - Real Subject vs. Background color strip extracted from each frame.
     - One clean, optional 3D Subject Path showing where the main subject moves
       through (x, y, time) across the shot.
  4. Mobile-Friendly Responsive Layout:
     - Sticky 16:9 video player on mobile with horizontal touch-scroll pill bars
       and clean tap-to-play cards for the 8 Shape Films (SCION 114–121) and
       all 142 ALLWAYS films.
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

    # Keep only the essential fields for the 12 flagship slit-scan films
    flagship_slits = {}
    for film in tensor_data.get("films", []):
        flagship_slits[film["id"]] = {
            "ut_b64": encode_img_b64(film["ut_tomogram"]),
            "vt_b64": encode_img_b64(film["vt_tomogram"]),
        }

    # Slim down worms_140 series to keep the page fast and responsive on mobile
    slim_films = []
    for wf in worms_140_data.get("films", []):
        slits = flagship_slits.get(wf["id"], {})
        slim_films.append({
            "id": wf["id"],
            "title": wf["title"],
            "maker": wf["maker"],
            "group": wf["group"],
            "video_rel": wf["video_rel"],
            "case_url": wf["case_url"],
            "duration_s": wf["duration_s"],
            "dominant_topology": wf["dominant_topology"],
            "ut_b64": slits.get("ut_b64", ""),
            "series": [
                {
                    "t": s["t"],
                    "c": s["c"],
                    "r": s["r"],
                    "rgb_core": s["rgb_core"],
                    "rgb_shell": s["rgb_shell"],
                    "topology": s.get("topology", ""),
                }
                for s in wf.get("series", [])
            ],
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALLWAYS — 8 Composition Shapes &amp; Film Archive</title>
<style>
  :root {{
    --bg: #0b0c10;
    --panel: #13151c;
    --panel-hover: #1b1e28;
    --border: #262a38;
    --fg: #f0ede6;
    --muted: #949ba8;
    --gold: #eab354;
    --cyan: #5bc0be;
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

  /* Header Bar */
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
    letter-spacing: 0.04em;
    color: var(--fg);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .brand span {{
    background: var(--gold);
    color: #0b0c10;
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 800;
  }}
  .nav-links {{
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
  }}
  .btn {{
    background: #1c202b;
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
    color: #0b0c10;
    border-color: var(--gold);
  }}

  /* Main Responsive Layout: 2 Columns on Desktop, Clean Vertical Stack on Mobile */
  .layout {{
    display: grid;
    grid-template-columns: 1.15fr 1fr;
    gap: 16px;
    max-width: 1520px;
    margin: 0 auto;
    padding: 14px;
    align-items: start;
  }}
  @media (max-width: 920px) {{
    .layout {{
      grid-template-columns: 1fr;
      padding: 0 0 24px 0;
      gap: 10px;
    }}
    .player-column {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
    }}
    .player-card {{
      border-radius: 0 !important;
      border-left: none !important;
      border-right: none !important;
      border-top: none !important;
    }}
    .browser-column {{
      padding: 0 12px;
    }}
  }}

  /* Left Column: Clean Video Stage + Single Viewfinder Bar + Real Frame Color/Slit Scrubber */
  .player-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }}
  .stage-header {{
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--border);
  }}
  .stage-title {{
    font-weight: 700;
    font-size: 15px;
    color: var(--fg);
  }}
  .stage-meta {{
    font-size: 12px;
    color: var(--muted);
  }}
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

  /* Horizontal Touch-Scroll Pill Bar for the 8 Viewfinder Guides */
  .guide-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 9px 12px;
    overflow-x: auto;
    border-top: 1px solid var(--border);
    background: #0f1117;
    scrollbar-width: none;
  }}
  .guide-bar::-webkit-scrollbar {{ display: none; }}
  .guide-lbl {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    font-weight: 700;
    margin-right: 2px;
    flex-shrink: 0;
  }}
  .pill {{
    background: #1a1d27;
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
    color: #0b0c10;
    border-color: var(--gold);
  }}

  /* Photographic Slit-Scan & Subject/Background Color Strip */
  .scrubber-Area {{
    padding: 10px 14px 12px;
    border-top: 1px solid var(--border);
    background: var(--panel);
  }}
  .scrubber-head {{
    display: flex;
    justify-content: space-between;
    font-size: 11.5px;
    color: var(--muted);
    margin-bottom: 5px;
  }}
  #colorStripCanvas {{
    width: 100%;
    height: 44px;
    border-radius: 6px;
    border: 1px solid var(--border);
    display: block;
    cursor: pointer;
    background: #08090c;
  }}
  .slit-wrap {{
    margin-top: 6px;
    position: relative;
    height: 46px;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--border);
    cursor: pointer;
    display: none;
  }}
  .slit-wrap.visible {{ display: block; }}
  .slit-wrap img {{
    width: 100%;
    height: 100%;
    object-fit: fill;
    display: block;
  }}
  .playhead {{
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--gold);
    pointer-events: none;
  }}

  /* Right Column: Section Tabs & Clean Card Grid */
  .section-tabs {{
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
    overflow-x: auto;
    padding-bottom: 2px;
  }}
  .tab-pane {{ display: none; }}
  .tab-pane.active {{ display: block; }}

  .shape-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 12px;
  }}
  @media (max-width: 540px) {{
    .shape-grid {{
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
  }}
  .shape-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: border-color 0.15s;
  }}
  .shape-card.active, .shape-card:hover {{
    border-color: var(--gold);
  }}
  .shape-thumb {{
    position: relative;
    aspect-ratio: 16 / 9;
    background: #000;
    cursor: pointer;
  }}
  .shape-thumb img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}
  .shape-badge {{
    position: absolute;
    top: 6px;
    left: 6px;
    background: rgba(11, 12, 16, 0.86);
    color: var(--gold);
    border: 1px solid rgba(234, 179, 84, 0.5);
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
  }}
  .shape-body {{
    padding: 9px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
  }}
  .shape-name {{
    font-weight: 700;
    font-size: 13px;
    color: var(--fg);
  }}
  .shape-desc {{
    font-size: 11.5px;
    color: var(--muted);
    line-height: 1.35;
  }}
  .shape-actions {{
    display: flex;
    gap: 5px;
    margin-top: auto;
    padding-top: 4px;
    flex-wrap: wrap;
  }}
  .mini-btn {{
    flex: 1;
    text-align: center;
    justify-content: center;
    padding: 5px 7px;
    font-size: 11.5px;
    border-radius: 5px;
    background: #1c202b;
    color: var(--fg);
    border: 1px solid var(--border);
    cursor: pointer;
    font-weight: 600;
  }}
  .mini-btn.gold {{
    background: var(--gold);
    color: #0b0c10;
    border-color: var(--gold);
  }}

  /* All 142 Films Browser List */
  .filter-bar {{
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .film-list {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 70vh;
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
  .film-row:hover, .film-row.active {{
    border-color: var(--gold);
    background: var(--panel-hover);
  }}
  .film-row-title {{ font-weight: 700; font-size: 13px; }}
  .film-row-sub {{ font-size: 11.5px; color: var(--muted); }}
  .swatch-pair {{
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }}
  .swatch {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.2);
  }}

  /* Simple 3D Subject Path Canvas (Clean, Single-Purpose) */
  .path3d-box {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 12px;
  }}
  #path3dCanvas {{
    width: 100%;
    height: 290px;
    background: #08090d;
    border-radius: 6px;
    border: 1px solid var(--border);
    display: block;
    cursor: grab;
  }}

  /* Prompt Modal */
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
    <span>ALLWAYS</span>
    8 Composition Shapes &amp; Archival Cinema Studio
  </div>
  <div class="nav-links">
    <button class="btn gold" onclick="playEightGridsReel()">▶ 8-Shape Reel (28s)</button>
    <a class="btn" href="../paeleo/allways/index.html">← Hub</a>
    <a class="btn" href="../allways-best/index.html">★ Best Film</a>
    <a class="btn" href="../allways-awards/index.html">🏆 Awards</a>
  </div>
</header>

<main class="layout">
  <!-- LEFT COLUMN: Clean Video Player + Single Viewfinder Guide Bar + Real Color/Slit Timeline -->
  <section class="player-column">
    <div class="player-card">
      <div class="stage-header">
        <div>
          <div class="stage-title" id="stageTitle">114 · GOLDEN SPIRAL</div>
          <div class="stage-meta" id="stageSub">SCION 114 · 24.0s · 8 Archival Cuts</div>
        </div>
        <a class="btn" id="stageCaseLink" href="../paeleo/allways/scion/prompts/scion-114-golden-spiral-logarithmic-torque.md" target="_blank">Source ↗</a>
      </div>

      <div class="video-wrap">
        <video id="mainVideo" controls playsinline preload="metadata"></video>
        <canvas id="guideCanvas" width="800" height="450"></canvas>
      </div>

      <!-- One Clean Composition Guide at a Time (Tap to Toggle) -->
      <div class="guide-bar">
        <span class="guide-lbl">Viewfinder:</span>
        <button class="pill active" id="vf-none" onclick="setGuide('none')">Off</button>
        <button class="pill" id="vf-golden_spiral" onclick="setGuide('golden_spiral')">1 · Golden Spiral</button>
        <button class="pill" id="vf-frame_in_frame" onclick="setGuide('frame_in_frame')">2 · Frame in Frame</button>
        <button class="pill" id="vf-s_curve" onclick="setGuide('s_curve')">3 · S-Curve</button>
        <button class="pill" id="vf-symmetry" onclick="setGuide('symmetry')">4 · Symmetry</button>
        <button class="pill" id="vf-rule_of_thirds" onclick="setGuide('rule_of_thirds')">5 · Rule of Thirds</button>
        <button class="pill" id="vf-centered" onclick="setGuide('centered')">6 · Centered</button>
        <button class="pill" id="vf-v_shape" onclick="setGuide('v_shape')">7 · V-Shape</button>
        <button class="pill" id="vf-negative_space" onclick="setGuide('negative_space')">8 · Negative Space</button>
      </div>

      <!-- Real Frame Color Strip (Subject vs. Background) + Photographic Slit-Scan -->
      <div class="scrubber-Area">
        <div class="scrubber-head">
          <span>Timeline Barcode (Top: Subject Color · Bottom: Background Color · White Line: Subject Horizontal Path)</span>
          <span id="timeLabel" style="color:var(--gold);font-family:var(--mono);">0.0s</span>
        </div>
        <canvas id="colorStripCanvas" width="720" height="44"></canvas>

        <div class="slit-wrap" id="slitWrap" onclick="scrubSlit(event)">
          <img id="slitImg" alt="Photographic Horizon Slit-Scan">
          <div class="playhead" id="slitPlayhead"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- RIGHT COLUMN: Clean Tabbed Browser (1. 8 Shape Films & Prompts | 2. All 142 Films | 3. 3D Subject Path) -->
  <section class="browser-column">
    <div class="section-tabs">
      <button class="btn active" id="tabBtn-shapes" onclick="switchTab('shapes')">★ 8 Shape Films &amp; SCION Prompts</button>
      <button class="btn" id="tabBtn-library" onclick="switchTab('library')">All 142 Films</button>
      <button class="btn" id="tabBtn-path3d" onclick="switchTab('path3d')">3D Subject Path</button>
    </div>

    <!-- TAB 1: The 8 Shapes (Each with its 24s Film, Archival Match, and SCION Prompt) -->
    <div class="tab-pane active" id="tab-shapes">
      <div class="shape-grid" id="shapeCardsGrid"></div>
    </div>

    <!-- TAB 2: All 142 Playable ALLWAYS Films -->
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

    <!-- TAB 3: Clean 3D Subject Path (Shows how the subject moves in x, y over time) -->
    <div class="tab-pane" id="tab-path3d">
      <div class="path3d-box">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
          <div>
            <strong>3D Subject Trajectory through Time</strong>
            <div style="font-size:12px;color:var(--muted);">Drag to rotate · Tube color = real subject color · Tube width = subject size in frame</div>
          </div>
          <label style="font-size:12px;cursor:pointer;display:flex;align-items:center;gap:4px;">
            <input type="checkbox" id="chkSpin3D" checked> Auto-rotate
          </label>
        </div>
        <canvas id="path3dCanvas" width="680" height="290"></canvas>
      </div>
    </div>
  </section>
</main>

<!-- Modal for Inspecting Full SCION Prompt (SCION 114–121) -->
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

const videoEl = document.getElementById('mainVideo');
const guideCanvas = document.getElementById('guideCanvas');
const colorCanvas = document.getElementById('colorStripCanvas');
const pathCanvas = document.getElementById('path3dCanvas');

let activeFilm = FILMS_142[1] || FILMS_142[0]; // Default to SCION 114 Golden Spiral
let activeGuide = 'none';
let activeTab = 'shapes';
let libFilter = 'all';
let curTime = 0.0;
let activePromptOp = null;

// 3D rotation angles
let yaw = -0.55, pitch = 0.28, dragging3D = false, lastX = 0, lastY = 0;

function init() {{
  renderShapeCards();
  renderLibraryList();
  loadFilmObject(activeFilm, false);
}}

function renderShapeCards() {{
  const grid = document.getElementById('shapeCardsGrid');
  grid.innerHTML = '';
  (EIGHT_GRIDS.rules || []).forEach(r => {{
    const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === r.id);
    const scionId = op ? op.scion_id : (113 + r.num);
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
        <div class="shape-desc">${{r.geometry}}</div>
        <div class="shape-actions">
          <button class="mini-btn gold" onclick="playShapeFilm('${{r.id}}')">▶ 24s Film</button>
          <button class="mini-btn" onclick="jumpArchivalShot('${{r.id}}')">⌖ Shot</button>
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
        <div class="film-row-sub">${{f.maker}} · ${{f.duration_s}}s · ${{f.dominant_topology.replace(/_/g, ' ')}}</div>
      </div>
      <div class="swatch-pair" title="Subject Color / Background Color">
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
  ['shapes', 'library', 'path3d'].forEach(k => {{
    document.getElementById('tabBtn-' + k).classList.toggle('active', k === tabId);
    document.getElementById('tab-' + k).classList.toggle('active', k === tabId);
  }});
  if (tabId === 'path3d') draw3DSubjectPath();
}}

function loadFilmObject(f, autoplay) {{
  activeFilm = f;
  curTime = 0.0;
  document.getElementById('stageTitle').textContent = f.title;
  document.getElementById('stageSub').textContent = `${{f.maker}} · ${{f.duration_s}}s · ${{f.dominant_topology.replace(/_/g, ' ')}}`;
  document.getElementById('stageCaseLink').href = f.case_url;

  videoEl.src = f.video_rel;
  if (autoplay) videoEl.play().catch(() => {{}});

  const slitWrap = document.getElementById('slitWrap');
  if (f.ut_b64) {{
    document.getElementById('slitImg').src = f.ut_b64;
    slitWrap.classList.add('visible');
  }} else {{
    slitWrap.classList.remove('visible');
  }}

  drawColorStrip();
  if (activeTab === 'path3d') draw3DSubjectPath();
  if (activeTab === 'library') renderLibraryList();
}}

function playShapeFilm(ruleId) {{
  const op = (SCION_SHAPES.operators || []).find(o => o.rule_id === ruleId);
  if (!op) return;
  document.querySelectorAll('.shape-card').forEach(el => el.classList.remove('active'));
  const card = document.getElementById('scard-' + ruleId);
  if (card) card.classList.add('active');

  setGuide('none'); // Film has its own 4-phase viewfinder lock built in
  const fMatch = FILMS_142.find(f => f.id === 'shape-' + op.scion_id);
  if (fMatch) {{
    loadFilmObject(fMatch, true);
  }} else {{
    videoEl.src = op.film_file;
    videoEl.play().catch(() => {{}});
  }}
}}

function jumpArchivalShot(ruleId) {{
  const r = (EIGHT_GRIDS.rules || []).find(x => x.id === ruleId);
  if (!r) return;
  setGuide(ruleId);
  const w = r.winner;
  document.getElementById('stageTitle').textContent = `#${{r.num}} ${{r.name.split('(')[0].trim()}} — ${{w.source_title}}`;
  document.getElementById('stageSub').textContent = `In ${{w.film_title}} (${{w.maker}}) @ ${{w.timestamp_s}}s`;
  document.getElementById('stageCaseLink').href = w.case_url;

  videoEl.src = w.video_rel;
  videoEl.onloadedmetadata = () => {{
    videoEl.currentTime = Math.max(0, w.timestamp_s - 0.8);
    videoEl.play().catch(() => {{}});
    videoEl.onloadedmetadata = null;
  }};
}}

function playEightGridsReel() {{
  setGuide('none');
  const fMatch = FILMS_142.find(f => f.id === 'shape-eight-reel');
  if (fMatch) loadFilmObject(fMatch, true);
}}

function setGuide(ruleId) {{
  activeGuide = ruleId;
  ['none', 'golden_spiral', 'frame_in_frame', 's_curve', 'symmetry', 'rule_of_thirds', 'centered', 'v_shape', 'negative_space'].forEach(k => {{
    const b = document.getElementById('vf-' + k);
    if (b) b.classList.toggle('active', k === ruleId);
  }});
  drawGuideOverlay();
}}

function drawGuideOverlay() {{
  const ctx = guideCanvas.getContext('2d');
  const W = guideCanvas.width, H = guideCanvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!activeGuide || activeGuide === 'none') return;

  const pad = 18;
  ctx.save();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(pad, pad, W - pad * 2, H - pad * 2);

  ctx.strokeStyle = 'rgba(234, 179, 84, 0.95)';
  ctx.lineWidth = 3.2;

  if (activeGuide === 'golden_spiral') {{
    const gx = pad + (W - pad * 2) * 0.618;
    const gy = pad + (H - pad * 2) * 0.618;
    ctx.strokeStyle = 'rgba(234, 179, 84, 0.45)';
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(gx, pad); ctx.lineTo(gx, H - pad); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(W - pad, gy); ctx.stroke();

    ctx.strokeStyle = 'rgba(234, 179, 84, 0.96)';
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
  }} else if (activeGuide === 'frame_in_frame') {{
    ctx.strokeRect(W * 0.17, H * 0.14, W * 0.66, H * 0.72);
  }} else if (activeGuide === 's_curve') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.20, H * 0.88);
    ctx.bezierCurveTo(W * 0.78, H * 0.72, W * 0.22, H * 0.28, W * 0.80, H * 0.12);
    ctx.stroke();
  }} else if (activeGuide === 'symmetry') {{
    ctx.beginPath(); ctx.moveTo(W * 0.5, pad); ctx.lineTo(W * 0.5, H - pad); ctx.stroke();
  }} else if (activeGuide === 'rule_of_thirds') {{
    [1/3, 2/3].forEach(f => {{
      ctx.beginPath(); ctx.moveTo(W * f, pad); ctx.lineTo(W * f, H - pad); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, H * f); ctx.lineTo(W - pad, H * f); ctx.stroke();
    }});
  }} else if (activeGuide === 'centered') {{
    [0.42, 0.58].forEach(f => {{
      ctx.beginPath(); ctx.moveTo(W * f, pad); ctx.lineTo(W * f, H - pad); ctx.stroke();
    }});
    ctx.beginPath(); ctx.moveTo(pad, H * 0.68); ctx.lineTo(W - pad, H * 0.68); ctx.stroke();
  }} else if (activeGuide === 'v_shape') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.12, pad); ctx.lineTo(W * 0.50, H * 0.84); ctx.lineTo(W * 0.88, pad);
    ctx.stroke();
  }} else if (activeGuide === 'negative_space') {{
    ctx.beginPath();
    ctx.moveTo(W * 0.08, H * 0.64); ctx.lineTo(W * 0.08, H * 0.10);
    ctx.lineTo(W * 0.92, H * 0.10); ctx.lineTo(W * 0.92, H * 0.64);
    ctx.stroke();
  }}
  ctx.restore();
}}

// Draw Clean Subject vs. Background Color Strip + White Subject Path
function drawColorStrip() {{
  const ctx = colorCanvas.getContext('2d');
  const W = colorCanvas.width, H = colorCanvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!activeFilm || !activeFilm.series || !activeFilm.series.length) return;

  const ser = activeFilm.series;
  const n = ser.length;
  const bw = W / n;

  ser.forEach((s, i) => {{
    const x = i * bw;
    ctx.fillStyle = `rgb(${{s.rgb_core[0]}},${{s.rgb_core[1]}},${{s.rgb_core[2]}})`;
    ctx.fillRect(x, 0, bw + 1, H * 0.55);
    ctx.fillStyle = `rgb(${{s.rgb_shell[0]}},${{s.rgb_shell[1]}},${{s.rgb_shell[2]}})`;
    ctx.fillRect(x, H * 0.55, bw + 1, H * 0.45);
  }});

  // Overlay white horizontal subject position curve u(t)
  ctx.beginPath();
  ser.forEach((s, i) => {{
    const px = (i / Math.max(1, n - 1)) * W;
    const py = 4 + s.c[0] * (H - 8);
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }});
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Playhead
  const dur = activeFilm.duration_s || videoEl.duration || 1;
  const px = Math.min(1, Math.max(0, curTime / dur)) * W;
  ctx.fillStyle = '#eab354';
  ctx.fillRect(px - 1.5, 0, 3, H);
}}

colorCanvas.addEventListener('click', e => {{
  const rect = colorCanvas.getBoundingClientRect();
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
  document.getElementById('timeLabel').textContent = `${{curTime.toFixed(1)}}s / ${{dur.toFixed(1)}}s`;
  document.getElementById('slitPlayhead').style.left = `${{Math.min(100, (curTime / dur) * 100)}}%`;
  drawColorStrip();
  if (activeTab === 'path3d') draw3DSubjectPath();
}});

// Clean, Single-Purpose 3D Subject Path (x, y, time)
function project3D(u, v, tNorm, W, H) {{
  const x = (tNorm - 0.5) * 1.65;
  const y = (0.5 - v) * 0.92;
  const z = (u - 0.5) * 0.92;
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = x * cy - z * sy;
  const z1 = x * sy + z * cy;
  const y2 = y * cp - z1 * sp;
  const z2 = y * sp + z1 * cp;
  const scale = 2.3 / (2.55 - z2);
  return {{
    px: W * 0.5 + x1 * scale * Math.min(W, H) * 0.62,
    py: H * 0.52 - y2 * scale * Math.min(W, H) * 0.62,
    scale
  }};
}}

function draw3DSubjectPath() {{
  const ctx = pathCanvas.getContext('2d');
  const W = pathCanvas.width, H = pathCanvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!activeFilm || !activeFilm.series || !activeFilm.series.length) return;

  const corners = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];
  const edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  ctx.strokeStyle = 'rgba(150, 160, 185, 0.22)';
  ctx.lineWidth = 1;
  edges.forEach(([i, j]) => {{
    const a = project3D(corners[i][0], corners[i][1], corners[i][2], W, H);
    const b = project3D(corners[j][0], corners[j][1], corners[j][2], W, H);
    ctx.beginPath(); ctx.moveTo(a.px, a.py); ctx.lineTo(b.px, b.py); ctx.stroke();
  }});

  const ser = activeFilm.series;
  const n = ser.length;
  for (let i = 0; i < n - 1; i++) {{
    const a = ser[i], b = ser[i + 1];
    const pA = project3D(a.c[0], a.c[1], i / Math.max(1, n - 1), W, H);
    const pB = project3D(b.c[0], b.c[1], (i + 1) / Math.max(1, n - 1), W, H);
    const rgb = a.rgb_core;
    ctx.beginPath();
    ctx.strokeStyle = `rgb(${{rgb[0]}},${{rgb[1]}},${{rgb[2]}})`;
    ctx.lineWidth = Math.max(3, a.r * 34 * pA.scale);
    ctx.lineCap = 'round';
    ctx.moveTo(pA.px, pA.py);
    ctx.lineTo(pB.px, pB.py);
    ctx.stroke();
  }}

  // Current time slice plane
  const dur = activeFilm.duration_s || 1;
  const tNorm = Math.min(1, Math.max(0, curTime / dur));
  const slice = [[0,0,tNorm],[1,0,tNorm],[1,1,tNorm],[0,1,tNorm],[0,0,tNorm]];
  ctx.beginPath();
  slice.forEach((c, idx) => {{
    const p = project3D(c[0], c[1], c[2], W, H);
    if (idx === 0) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py);
  }});
  ctx.strokeStyle = '#eab354';
  ctx.lineWidth = 1.8;
  ctx.stroke();
}}

pathCanvas.addEventListener('pointerdown', e => {{
  dragging3D = true; lastX = e.clientX; lastY = e.clientY;
  document.getElementById('chkSpin3D').checked = false;
}});
window.addEventListener('pointerup', () => {{ dragging3D = false; }});
window.addEventListener('pointermove', e => {{
  if (!dragging3D) return;
  yaw += (e.clientX - lastX) * 0.008;
  pitch = Math.max(-1.1, Math.min(1.1, pitch + (e.clientY - lastY) * 0.008));
  lastX = e.clientX; lastY = e.clientY;
  draw3DSubjectPath();
}});

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

function tick() {{
  if (activeTab === 'path3d' && document.getElementById('chkSpin3D').checked && !dragging3D) {{
    yaw += 0.004;
    draw3DSubjectPath();
  }}
  requestAnimationFrame(tick);
}}

init();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""

    out_html = os.path.join(TENSOR_DIR, "index.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote clean, mobile-first screening room -> {out_html} ({os.path.getsize(out_html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
