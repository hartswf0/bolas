#!/usr/bin/env python3
"""
Inject Secondhand Motion's native-styled Multiplane Space-Worm Explorer (#shmWormsHero)
with the 3D Parallel & Stretched Output Timelines ("Multiplane Multi-Worm") renderer,
6 Interpretation Lenses, Variant Switcher, Slow-Motion Controls, Plain-English
Worm Decoder Grid, Mobile Zero-Scroll PiP/Split UX, and warm-paper mini-worm Rack badges into
/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/index.html.
"""

import os

SHM_INDEX = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/index.html"

START_MARKER = "<!-- BEGIN SECONDHAND MOTION WORMS STUDIO -->"
END_MARKER   = "<!-- END SECONDHAND MOTION WORMS STUDIO -->"

INJECT_BLOCK = r"""<!-- BEGIN SECONDHAND MOTION WORMS STUDIO -->
<style>
.worms-stage{
  background:var(--sheet); border:1.5px solid var(--ink); border-radius:10px;
  padding:14px; box-shadow:0 6px 0 var(--rule-strong); margin:0 0 26px;
}
.worms-head{
  display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;
  margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--rule);
}
.worms-head h2{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:20px;
  letter-spacing:-0.015em;margin:0;display:inline-flex;align-items:center;gap:8px;
}
.worms-head .lot-pill{
  font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  padding:2px 7px;border-radius:4px;background:var(--tag-soft);color:var(--tag-ink);
}
.worms-bar{
  display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;
  margin-bottom:8px;
}
.w-scroll-strip{
  display:flex;align-items:center;gap:6px;overflow-x:auto;max-width:100%;
  scrollbar-width:none;-webkit-overflow-scrolling:touch;
}
.w-scroll-strip::-webkit-scrollbar{display:none}
.w-seg{
  display:inline-flex;border:1.5px solid var(--ink);border-radius:6px;overflow:hidden;
  background:var(--card);flex-shrink:0;
}
.w-seg button{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11.5px;
  padding:4px 9px;border:0;background:transparent;color:var(--ink);cursor:pointer;
  border-right:1px solid var(--rule);white-space:nowrap;
}
.w-seg button:last-child{border-right:0}
.w-seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.w-btn{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11.5px;
  padding:4px 9px;border:1.5px solid var(--ink);border-radius:6px;
  background:var(--card);color:var(--ink);cursor:pointer;text-decoration:none;
  display:inline-flex;align-items:center;gap:4px;white-space:nowrap;flex-shrink:0;
}
.w-btn:hover{border-color:var(--tag)}
.w-btn[aria-pressed="true"]{background:var(--tag);color:#161412;border-color:var(--ink)}
.w-select{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:12.5px;
  padding:4px 9px;border:1.5px solid var(--ink);border-radius:6px;
  background:var(--card);color:var(--ink);cursor:pointer;max-width:310px;
}
.w-lens-banner{
  display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;
  padding:5px 10px;margin-bottom:9px;border-radius:6px;
  background:var(--tag-soft);border:1px solid var(--tag);color:var(--ink);font-size:12px;
}
.w-lens-banner b{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;color:var(--tag-ink)}
.w-screens{
  position:relative;display:grid;grid-template-columns:1.35fr 1fr;gap:12px;align-items:stretch;
}
.w-screen{
  position:relative;background:var(--cel);border:1.5px solid var(--ink);
  border-radius:6px;overflow:hidden;
}
.w-canvas-wrap{
  position:relative;width:100%;aspect-ratio:4/3;background:var(--cel);
  touch-action:none;user-select:none;
}
.w-canvas-wrap.worm-scrub-area{cursor:ew-resize;aspect-ratio:16/11}
.w-screen canvas{display:block;width:100%;height:100%}
.w-screen .w-lbl{
  position:absolute;top:7px;left:9px;
  font-family:'JetBrains Mono',monospace;font-size:10.5px;
  background:rgba(246,239,227,0.92);color:#161412;
  padding:2px 7px;border-radius:4px;border:1px solid var(--rule-strong);
  pointer-events:none;z-index:2;
}
.w-screen .w-lbl-r{
  position:absolute;top:7px;right:9px;
  font-family:'JetBrains Mono',monospace;font-size:10.5px;
  background:var(--tag-soft);color:var(--tag-ink);
  padding:2px 7px;border-radius:4px;border:1px solid var(--tag);
  pointer-events:none;z-index:2;font-weight:600;
}
.w-mob-pip-btn{display:none}
.w-controls{
  display:grid;grid-template-columns:auto auto auto 1fr auto;gap:8px;align-items:center;
  margin-top:10px;padding-top:9px;border-top:1px solid var(--rule);
}
.w-scrub{position:relative;display:flex;align-items:center;height:24px}
.w-scrub input[type=range]{width:100%;accent-color:var(--tag);cursor:pointer;margin:0}
.w-ticks{position:absolute;left:6px;right:6px;top:2px;height:6px;pointer-events:none}
.w-ticks span{position:absolute;top:0;width:2px;height:6px;background:var(--rule-strong);transform:translateX(-1px)}
.w-ticks span.drawn{background:var(--ink);height:8px;width:2.5px}
.w-ticks span.line{background:var(--tag);height:10px;width:3px}
.w-readout{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--muted);min-width:86px;text-align:right}
.w-foot{
  display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;
  margin-top:8px;font-size:12px;color:var(--muted);
}
.w-planes{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.w-planes label{
  font-family:'JetBrains Mono',monospace;font-size:10.5px;
  padding:2px 7px;border:1px solid var(--rule-strong);border-radius:4px;
  background:var(--card);cursor:pointer;user-select:none;
  display:inline-flex;align-items:center;gap:4px;white-space:nowrap;
}
.w-planes label.subj{border-color:var(--tag);background:var(--tag-soft);color:var(--tag-ink);font-weight:600}
.w-planes label.soloed{outline:2px solid var(--ink)}
.w-planes input{accent-color:var(--tag);margin:0}

.w-decoder-grid{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;
  margin-top:9px;padding-top:9px;border-top:1px solid var(--rule);
}
.w-dec-card{
  background:var(--card);border:1px solid var(--rule-strong);border-radius:6px;
  padding:7px 9px;display:flex;flex-direction:column;gap:2px;
}
.w-dec-card .dk{
  font-family:'JetBrains Mono',monospace;font-size:9.5px;text-transform:uppercase;
  letter-spacing:0.05em;color:var(--tag-ink);font-weight:600;
}
.w-dec-card .dv{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:13px;color:var(--ink);
}
.w-dec-card .dp{font-size:11px;color:var(--muted);line-height:1.3;margin:0}

/* Mobile-First Zero-Scroll Layout */
@media (max-width:860px){
  .worms-stage{padding:9px;margin-bottom:16px}
  .worms-head{margin-bottom:6px;padding-bottom:6px;gap:6px}
  .worms-head h2{font-size:16px}
  #idxWormSub{display:none}
  .w-select{max-width:190px;font-size:11.5px;padding:3px 6px}
  .w-lens-banner{padding:4px 8px;margin-bottom:6px;font-size:11px}
  #idxLensDesc{display:none}
  .w-mob-pip-btn{display:inline-flex}
  .w-screens.mob-pip{
    display:block;position:relative;
  }
  .w-screens.mob-pip .w-screen-worm .w-canvas-wrap{
    aspect-ratio:4/3;
  }
  .w-screens.mob-pip .w-screen-stage{
    position:absolute;right:8px;bottom:8px;width:36%;max-width:165px;
    z-index:6;box-shadow:0 6px 18px rgba(0,0,0,0.48);
    border:2px solid var(--tag);border-radius:6px;
  }
  .w-screens.mob-pip .w-screen-stage .w-lbl,
  .w-screens.mob-pip .w-screen-stage .w-lbl-r{
    font-size:8.5px;padding:1px 4px;top:3px;
  }
  .w-screens.mob-split{
    display:grid;grid-template-columns:1.18fr 0.82fr;gap:6px;
  }
  .w-controls{
    grid-template-columns:auto auto 1fr auto;gap:5px;margin-top:6px;padding-top:6px;
  }
  .w-controls [aria-label="Playback speed"]{display:none}
  .w-foot{margin-top:5px;gap:4px}
  #idxCaption{display:none}
  .w-planes{flex-wrap:nowrap;overflow-x:auto;max-width:100%;scrollbar-width:none}
  .w-planes::-webkit-scrollbar{display:none}
  .w-decoder-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:6px;padding-top:6px}
  .w-dec-card{padding:5px 7px}
  .w-dec-card .dp{display:none}
}

/* Warm-paper mini worm badge on Rack cards */
.mini-worm-box{
  margin-top:6px;padding:5px 7px;border-radius:6px;
  background:var(--cel);border:1px solid var(--rule-strong);
  display:flex;align-items:center;justify-content:space-between;gap:8px;cursor:pointer;
}
.mini-worm-box:hover{border-color:var(--ink);background:var(--tag-soft)}
.mini-worm-box canvas{
  width:118px;height:32px;border-radius:3px;background:var(--sheet);
  border:1px solid var(--rule);flex-shrink:0;
}
.mini-worm-meta{
  font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);
  line-height:1.25;text-align:right;
}
.mini-worm-meta b{color:var(--tag-ink);display:block;font-size:10.5px}
</style>

<section class="worms-stage" id="shmWormsHero" aria-label="Multiplane Space-Worms Explorer">
  <div class="worms-head">
    <div>
      <h2>
        <span class="lot-pill" id="idxWormLot">SM-0004</span>
        <span id="idxWormTitle">Giraffe Walks Past — Multiplane Space-Worm Explorer</span>
      </h2>
      <div style="font-size:12.5px;color:var(--muted);margin-top:2px" id="idxWormSub">
        Prelinger Archives · Wonderful World (Part II) · Switch between 6 Space-Worm Lenses and drag horizontally across the left screen to scrub.
      </div>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
      <button type="button" class="w-btn" id="idxPrevShot">&#9664;</button>
      <select class="w-select" id="idxShotSelect" aria-label="Select shot"></select>
      <button type="button" class="w-btn" id="idxNextShot">&#9654;</button>
      <a class="w-btn" id="idxFullWormsLink" href="pages/worms.html">Full Worms Studio (109) &#8599;</a>
    </div>
  </div>

  <div class="worms-bar">
    <div class="w-scroll-strip">
      <span style="font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;color:var(--muted);flex-shrink:0">LENS:</span>
      <div class="w-seg" role="group" aria-label="Space-Worm Interpretation Lens">
        <button type="button" data-idxwmode="parallel" aria-pressed="true">1 · Parallel Timelines (3D Stretch)</button>
        <button type="button" data-idxwmode="lanes" aria-pressed="false">2 · Plane Worms</button>
        <button type="button" data-idxwmode="strobe" aria-pressed="false">3 · Stroboscopic Trail</button>
        <button type="button" data-idxwmode="kymo" aria-pressed="false">4 · Slit-Scan &amp; Graphs</button>
        <button type="button" data-idxwmode="anatomy" aria-pressed="false">5 · Anatomy &amp; Joints</button>
        <button type="button" data-idxwmode="box" aria-pressed="false">6 · Planes in Depth</button>
      </div>
    </div>
    <div class="w-scroll-strip">
      <div class="w-seg" id="idxParallelSubSeg" role="group" aria-label="Parallel Timeline Sub-mode">
        <button type="button" data-idxpsub="radial" aria-pressed="true">Radial Multi-Worm Fan</button>
        <button type="button" data-idxpsub="dual" aria-pressed="false">2-Rail Stretch (Red / Blue)</button>
      </div>
      <button type="button" class="w-btn" id="idxParThemeBtn" aria-pressed="true" title="Toggle high-contrast cinema black backdrop for white correspondence rays">Dark / Paper</button>
      <div class="w-seg" role="group" aria-label="Version">
        <button type="button" id="idxVarGwp" data-idxvar="gwp" aria-pressed="true">Multiplane (GWP)</button>
        <button type="button" id="idxVarSam" data-idxvar="sam" aria-pressed="false" style="display:none">SAM Cutout</button>
        <button type="button" id="idxVarRedraw" data-idxvar="redraw" aria-pressed="false" style="display:none">Puppet Redraw</button>
        <button type="button" id="idxVarInt" data-idxvar="int" aria-pressed="false" style="display:none">Integrated 24fps</button>
      </div>
      <div class="w-seg" role="group" aria-label="Stage view">
        <button type="button" data-idxview="cartoon" aria-pressed="false">Cartoon</button>
        <button type="button" data-idxview="composite" aria-pressed="true">Over footage</button>
        <button type="button" data-idxview="cutout" aria-pressed="false">SAM Cutout</button>
        <button type="button" data-idxview="footage" aria-pressed="false">Footage</button>
        <button type="button" data-idxview="masks" aria-pressed="false">Silhouettes</button>
      </div>
      <button type="button" class="w-btn" id="idxBoilBtn" aria-pressed="true">Boil</button>
      <button type="button" class="w-btn" id="idxCelBtn" aria-pressed="true">Paint cels</button>
      <button type="button" class="w-btn w-mob-pip-btn" id="idxMobPipBtn" aria-pressed="true">PiP / Split</button>
    </div>
  </div>

  <div class="w-lens-banner">
    <div>
      <b id="idxLensTitle">Lens 1 · Parallel &amp; Stretched Output Timelines (3D Multi-Worm):</b>
      <span id="idxLensDesc">Parallel output timelines are prepared around the central input spine; distributed keyframes fan out via white correspondence rays (stretched 1/K slower per layer with head fixed) and intersect the circular cross-section ring as upright 3D frame cards.</span>
    </div>
  </div>

  <div class="w-screens mob-pip" id="idxScreensWrap">
    <div class="w-screen w-screen-worm">
      <div class="w-canvas-wrap worm-scrub-area">
        <canvas id="idxCvWorm" width="680" height="468"></canvas>
        <span class="w-lbl" id="idxLblWorm">parallel output timelines (3D stretch) · drag horizontally to scrub f</span>
        <span class="w-lbl-r" id="idxLblWormR">6 planes · f 01/33</span>
      </div>
    </div>
    <div class="w-screen w-screen-stage" id="idxStageScreenCard">
      <div class="w-canvas-wrap">
        <canvas id="idxCvStage" width="480" height="360"></canvas>
        <span class="w-lbl" id="idxLblStage">composite over footage · camera pans with shot</span>
        <span class="w-lbl-r" id="idxLblStageR">480×360 · 12 fps</span>
      </div>
    </div>
  </div>

  <div class="w-controls">
    <button type="button" class="w-btn" id="idxPlayBtn" aria-pressed="false">&#9654; Play</button>
    <div style="display:inline-flex;gap:4px">
      <button type="button" class="w-btn" id="idxStepPrev">&#8592;</button>
      <button type="button" class="w-btn" id="idxStepNext">&#8594;</button>
    </div>
    <div class="w-seg" role="group" aria-label="Playback speed">
      <button type="button" data-idxspeed="1" aria-pressed="true">1×</button>
      <button type="button" data-idxspeed="0.5" aria-pressed="false">0.5×</button>
      <button type="button" data-idxspeed="0.25" aria-pressed="false">0.25×</button>
    </div>
    <div class="w-scrub">
      <div class="w-ticks" id="idxTicks"></div>
      <input type="range" id="idxScrub" min="0" max="32" value="0" step="1" aria-label="Scrub frame">
    </div>
    <div class="w-readout" id="idxReadout">f 01 / 33</div>
  </div>

  <div class="w-foot">
    <span id="idxCaption">Drag horizontally across the left 3D timeline highway to scrub through the SAM cutouts &amp; multiplane drawings.</span>
    <div class="w-planes" id="idxPlanes"></div>
  </div>

  <div class="w-decoder-grid">
    <div class="w-dec-card">
      <span class="dk">1 · What the Worm Does in Space</span>
      <div class="dv" id="idxDecShapeT">—</div>
      <p class="dp" id="idxDecShapeP">—</p>
    </div>
    <div class="w-dec-card">
      <span class="dk">2 · Camera Pan vs. Depth Parallax</span>
      <div class="dv" id="idxDecCamT">—</div>
      <p class="dp" id="idxDecCamP">—</p>
    </div>
    <div class="w-dec-card">
      <span class="dk">3 · Drawing Rig &amp; Sub-Worm Anatomy</span>
      <div class="dv" id="idxDecRigT">—</div>
      <p class="dp" id="idxDecRigP">—</p>
    </div>
    <div class="w-dec-card">
      <span class="dk">4 · Live Frame Telemetry &amp; Versions</span>
      <div class="dv" id="idxDecLiveT">—</div>
      <p class="dp" id="idxDecLiveP">—</p>
    </div>
  </div>
</section>

<script>
(function(){
  const cvWorm = document.getElementById('idxCvWorm');
  const ctxWorm = cvWorm.getContext('2d');
  const cvStage = document.getElementById('idxCvStage');
  const ctxStage = cvStage.getContext('2d');
  const sel = document.getElementById('idxShotSelect');
  const playBtn = document.getElementById('idxPlayBtn');
  const scrub = document.getElementById('idxScrub');
  const readout = document.getElementById('idxReadout');
  const ticksEl = document.getElementById('idxTicks');
  const planesEl = document.getElementById('idxPlanes');

  const varGwp = document.getElementById('idxVarGwp');
  const varSam = document.getElementById('idxVarSam');
  const varRedraw = document.getElementById('idxVarRedraw');
  const varInt = document.getElementById('idxVarInt');
  const parSubSeg = document.getElementById('idxParallelSubSeg');
  const parThemeBtn = document.getElementById('idxParThemeBtn');
  const screensWrap = document.getElementById('idxScreensWrap');
  const mobPipBtn = document.getElementById('idxMobPipBtn');

  let WORMS = [];
  let curIdx = 0;
  let curWorm = null;
  let curVariant = 'gwp';
  let S = null;
  let shotCache = new Map();
  let frameImgCache = new Map();

  let wormMode = 'parallel';
  let parallelSubMode = 'radial';
  let parallelDark = true;
  let mobPipMode = true;
  let view = 'composite';
  let boilOn = true;
  let celOn = true;
  let playing = false;
  let speedMult = 1.0;
  let f = 0;
  let lastTick = 0;
  let planeOn = {};
  let soloPlaneId = null;

  const LENS_META = {
    parallel: {
      title: 'Lens 1 · Parallel & Stretched Output Timelines (3D Multi-Worm):',
      desc: 'Parallel output timelines are prepared around the central input spine; distributed keyframes fan out via white correspondence rays (stretched 1/K slower per layer with head fixed) and intersect the circular cross-section ring as upright 3D frame cards.',
      lbl: 'parallel output timelines (3D stretch) · drag horizontally to scrub f'
    },
    lanes: {
      title: 'Lens 2 · Disentangled Plane Worms:',
      desc: 'One horizontal cel strip per depth plane (Near → Subject → Far). Shows how fast foreground vs. background scrolls and stamps real SAM video cutouts + ink drawings along time.',
      lbl: 'disentangled plane worms · drag horizontally to scrub f'
    },
    strobe: {
      title: 'Lens 3 · Space-Time Stroboscopic Trail (Muybridge View):',
      desc: 'Lays the entire space-worm directly over the 4:3 scene: ghost SAM cutouts + ink poses from Start (green) to End (red), connected by the centroid spine, joint curves, and planted-foot anchors.',
      lbl: 'stroboscopic motion trail over scene · drag horizontally to scrub f'
    },
    kymo: {
      title: 'Lens 4 · Slit-Scan & Motion Graphs (X-T, Y-T & Looming):',
      desc: 'Separates horizontal travel X(t), vertical gait bounce Y(t), and silhouette scale R(t) vs. camera pan so you can read speed, direction, and rhythm at a glance.',
      lbl: 'spatiotemporal graphs X(t), Y(t), R(t) · drag horizontally to scrub f'
    },
    anatomy: {
      title: 'Lens 5 · Anatomy, Seed Line & Joint Braids:',
      desc: 'Compares The Line (f=0 Quick, Draw! seed doodle) against Frame f’s warped rig + skeleton joints on top, with anatomical joint sub-worms and 2D limb-crossing (braid) markers below.',
      lbl: 'seed line vs warped rig + joint sub-worms · drag horizontally to scrub f'
    },
    box: {
      title: 'Lens 6 · Planes in Depth (Multiplane Camera Box):',
      desc: 'Secondhand Motion’s receding multiplane cards (z=10 far horizon down to z=1.2 foreground), showing how each plane shifts by k = z_ref / z as the camera pans.',
      lbl: 'multiplane depth box (z) · drag horizontally to scrub f'
    }
  };

  const TOPO_HUMAN = {
    LOCKED_PILLAR: 'Anchored / Stationary Subject',
    DIAGONAL_SHEAR_BAND: 'Cross-Frame Traverse',
    SERPENTINE_CORKSCREW: 'Oscillating / Winding Path',
    LOOMING_FUNNEL_CONE: 'Looming / Approaching Camera',
    RADIAL_BURST: 'Radial Expansion / Turn'
  };

  const PLANE_TINTS = {
    far:   {fill:'rgba(92, 128, 188, 0.22)', stroke:'#3A5F9CD0'},
    mid:   {fill:'rgba(58, 125, 68, 0.24)',  stroke:'#2E6B3AD0'},
    near:  {fill:'rgba(196, 148, 52, 0.28)', stroke:'#8A6114D0'},
    char:  {fill:'rgba(239, 159, 58, 0.34)', stroke:'#8A4A05'}
  };
  function tintForPlane(pid, z, zRef){
    if(pid === 'char') return PLANE_TINTS.char;
    if(PLANE_TINTS[pid]) return PLANE_TINTS[pid];
    if(z < (zRef || 2)) return PLANE_TINTS.near;
    if(z <= (zRef || 2) * 2.2) return PLANE_TINTS.mid;
    return PLANE_TINTS.far;
  }

  function jitter(pt, seed, amp){
    const x = pt[0], y = pt[1];
    const h1 = Math.sin(x*12.9898 + y*78.233 + seed*43.1) * 43758.5453;
    const h2 = Math.cos(x*93.9898 + y*12.233 + seed*19.7) * 28413.1234;
    return [x + (h1 - Math.floor(h1) - 0.5)*2*amp, y + (h2 - Math.floor(h2) - 0.5)*2*amp];
  }

  function drawStrokes(ctx, strokes, opts){
    const o = Object.assign({color:'#161412', width:2.4, dx:0, dy:0, boilSeed:0, boilAmp:0, fill:null}, opts||{});
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = o.color;
    ctx.lineWidth = o.width;
    if(o.fill && strokes && strokes.length){
      ctx.fillStyle = o.fill;
      for(const s of strokes){
        if(!s || s.length < 4) continue;
        ctx.beginPath();
        for(let i=0;i<s.length;i++){
          let x = s[i][0] + o.dx, y = s[i][1] + o.dy;
          if(o.boilAmp>0){ const j = jitter([x,y], o.boilSeed+i*0.07, o.boilAmp); x=j[0]; y=j[1]; }
          if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        }
        ctx.closePath();
        ctx.fill();
      }
    }
    for(const s of (strokes||[])){
      if(!s || s.length < 2) continue;
      ctx.beginPath();
      for(let i=0;i<s.length;i++){
        let x = s[i][0] + o.dx, y = s[i][1] + o.dy;
        if(o.boilAmp>0){ const j = jitter([x,y], o.boilSeed+i*0.1, o.boilAmp); x=j[0]; y=j[1]; }
        if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function getFrameImg(worm, fi){
    if(!worm) return null;
    if(S && S._imgs && S._imgs[fi] && S._imgs[fi].complete && S._imgs[fi].naturalWidth > 0){
      return S._imgs[fi];
    }
    const key = worm.shot_id + ':' + fi;
    if(frameImgCache.has(key)){
      const im = frameImgCache.get(key);
      return (im.complete && im.naturalWidth > 0) ? im : null;
    }
    const im = new Image();
    im.crossOrigin = 'anonymous';
    const pad = String(fi).padStart(3, '0');
    im.src = `shots/${worm.shot_id}/frames/f${pad}.jpg`;
    im.onload = () => { if(curWorm === worm) renderAll(); };
    frameImgCache.set(key, im);
    return null;
  }

  function getActivePlanes(){
    if(S && Array.isArray(S.planes) && S.planes.length) return S.planes.slice().sort((a,b)=>b.z - a.z);
    if(curWorm && Array.isArray(curWorm.planes) && curWorm.planes.length) return curWorm.planes.slice().sort((a,b)=>b.z - a.z);
    return [{id:'char', z:2, label:'Subject'}];
  }

  function isPlaneVisible(pid){
    if(soloPlaneId) return pid === soloPlaneId;
    return planeOn[pid] !== false;
  }

  function camOffset(planeZ, fi){
    const zRef = (S && S.z_ref) || (curWorm && curWorm.z_ref) || 2;
    if(S && Array.isArray(S.camera) && S.camera[fi]){
      return {dx: S.camera[fi].dx * (zRef / planeZ), dy: S.camera[fi].dy * (zRef / planeZ)};
    }
    if(curWorm && curWorm.frames && curWorm.frames[fi]){
      const cam = curWorm.frames[fi].cam || [0,0];
      const W = (S && S.W) || curWorm.W || 480;
      const H = (S && S.H) || curWorm.H || 360;
      return {dx: cam[0]*W*(zRef/planeZ), dy: cam[1]*H*(zRef/planeZ)};
    }
    return {dx:0, dy:0};
  }

  function drawSamCutoutInRect(ctx, worm, fi, tx, ty, tw, th, opts){
    const o = Object.assign({cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true, alpha:1.0}, opts||{});
    const img = getFrameImg(worm, fi);
    const W = (S && S.W) || worm.W || 480;
    const H = (S && S.H) || worm.H || 360;

    let polysPx = [];
    if(S && Array.isArray(S.masks) && S.masks[fi] && S.masks[fi].length){
      polysPx = S.masks[fi];
    } else if(worm.frames && worm.frames[fi] && worm.frames[fi].ring && worm.frames[fi].ring.length){
      polysPx = [worm.frames[fi].ring.map(p => [p[0]*W, p[1]*H])];
    }

    let minX = W, minY = H, maxX = 0, maxY = 0;
    for(const poly of polysPx){
      for(const p of poly){
        if(p[0]<minX) minX=p[0]; if(p[1]<minY) minY=p[1];
        if(p[0]>maxX) maxX=p[0]; if(p[1]>maxY) maxY=p[1];
      }
    }
    const strokesPx = (S && S.cast && S.cast.frames && S.cast.frames[fi]) ? S.cast.frames[fi] : null;
    if(strokesPx){
      for(const s of strokesPx){
        for(const p of (s||[])){
          if(p[0]<minX) minX=p[0]; if(p[1]<minY) minY=p[1];
          if(p[0]>maxX) maxX=p[0]; if(p[1]>maxY) maxY=p[1];
        }
      }
    }
    if(minX >= maxX || minY >= maxY){
      minX = W*0.15; maxX = W*0.85; minY = H*0.15; maxY = H*0.85;
    } else {
      const padX = Math.max(14, (maxX-minX)*0.18), padY = Math.max(14, (maxY-minY)*0.18);
      minX = Math.max(0, minX-padX); minY = Math.max(0, minY-padY);
      maxX = Math.min(W, maxX+padX); maxY = Math.min(H, maxY+padY);
    }

    const srcX = o.cropToMask ? minX : 0, srcY = o.cropToMask ? minY : 0;
    const srcW = o.cropToMask ? Math.max(16, maxX-minX) : W;
    const srcH = o.cropToMask ? Math.max(16, maxY-minY) : H;
    const scale = Math.min(tw/srcW, th/srcH);
    const dw = srcW*scale, dh = srcH*scale;
    const ox = tx + (tw-dw)*0.5, oy = ty + (th-dh)*0.5;

    ctx.save();
    ctx.globalAlpha = o.alpha;
    if(img && polysPx.length){
      ctx.save();
      ctx.beginPath();
      for(const poly of polysPx){
        if(!poly || poly.length<3) continue;
        for(let i=0;i<poly.length;i++){
          const px = ox + (poly[i][0]-srcX)*scale, py = oy + (poly[i][1]-srcY)*scale;
          if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
        }
        ctx.closePath();
      }
      ctx.clip();
      ctx.drawImage(img, srcX, srcY, srcW, srcH, ox, oy, dw, dh);
      ctx.restore();

      if(o.drawOutline){
        ctx.strokeStyle = o.outlineColor;
        ctx.lineWidth = 1.5;
        for(const poly of polysPx){
          if(!poly || poly.length<3) continue;
          ctx.beginPath();
          for(let i=0;i<poly.length;i++){
            const px = ox + (poly[i][0]-srcX)*scale, py = oy + (poly[i][1]-srcY)*scale;
            if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
          }
          ctx.closePath();
          ctx.stroke();
        }
      }
    }
    if(o.drawDoodle){
      if(strokesPx && strokesPx.length){
        ctx.strokeStyle = o.doodleColor || '#161412';
        ctx.lineWidth = Math.max(1.3, 2.2*Math.min(1, scale*1.3));
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        for(const s of strokesPx){
          if(!s || s.length<2) continue;
          ctx.beginPath();
          for(let i=0;i<s.length;i++){
            const px = ox + (s[i][0]-srcX)*scale, py = oy + (s[i][1]-srcY)*scale;
            if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
          }
          ctx.stroke();
        }
      } else if(worm.frames && worm.frames[fi] && worm.frames[fi].doodle){
        ctx.strokeStyle = o.doodleColor || '#161412';
        ctx.lineWidth = 1.5;
        for(const s of worm.frames[fi].doodle){
          if(!s || s.length<2) continue;
          ctx.beginPath();
          for(let i=0;i<s.length;i++){
            const px = ox + (s[i][0]*W-srcX)*scale, py = oy + (s[i][1]*H-srcY)*scale;
            if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
          }
          ctx.stroke();
        }
      }
    }
    ctx.restore();
  }

  function drawPlaneObjectsInRect(ctx, plane, fi, tx, ty, tw, th, cropToPlane){
    const W = (S && S.W) || curWorm.W || 480;
    const H = (S && S.H) || curWorm.H || 360;
    const objs = (S && Array.isArray(S.objects)) ? S.objects.filter(o => o.plane === plane.id) : [];
    const off = camOffset(plane.z, fi);
    const allStrokes = [];
    for(const o of objs){
      const ost = (o.frames && o.frames[fi]) ? o.frames[fi] : o.strokes;
      if(ost && ost.length){
        for(const s of ost){
          if(s && s.length>=2) allStrokes.push(s.map(p => [p[0]+off.dx, p[1]+off.dy]));
        }
      }
    }
    let minX = W, minY = H, maxX = 0, maxY = 0;
    for(const s of allStrokes){
      for(const p of s){
        if(p[0]<minX) minX=p[0]; if(p[1]<minY) minY=p[1];
        if(p[0]>maxX) maxX=p[0]; if(p[1]>maxY) maxY=p[1];
      }
    }
    if(!cropToPlane || minX >= maxX || minY >= maxY){
      minX = 0; minY = 0; maxX = W; maxY = H;
    } else {
      const padX = Math.max(16, (maxX-minX)*0.18), padY = Math.max(16, (maxY-minY)*0.18);
      minX = Math.max(0, minX-padX); minY = Math.max(0, minY-padY);
      maxX = Math.min(W, maxX+padX); maxY = Math.min(H, maxY+padY);
    }
    const srcW = Math.max(20, maxX-minX), srcH = Math.max(20, maxY-minY);
    const scale = Math.min(tw/srcW, th/srcH);
    const dw = srcW*scale, dh = srcH*scale;
    const ox = tx + (tw-dw)*0.5, oy = ty + (th-dh)*0.5;
    if(allStrokes.length){
      ctx.save();
      ctx.strokeStyle = '#161412';
      ctx.lineWidth = Math.max(1.2, 1.9*Math.min(1, scale*1.4));
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      for(const s of allStrokes){
        ctx.beginPath();
        for(let i=0;i<s.length;i++){
          const px = ox + (s[i][0]-minX)*scale, py = oy + (s[i][1]-minY)*scale;
          if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  function drawUpright3DCard(ctx, cx, cy, cw, ch, fi, opts){
    const o = Object.assign({
      plane: null,
      borderColor: '#FFFFFF',
      borderWidth: 1.8,
      bgFill: '#FBFAF6',
      alpha: 1.0,
      cropToMask: true,
      label: null,
      labelColor: '#FFFFFF',
      subLabel: null,
      skewY: -0.18,
      skewX: -0.10
    }, opts || {});

    ctx.save();
    ctx.globalAlpha = o.alpha;
    ctx.translate(cx, cy);
    ctx.transform(1, o.skewY, o.skewX, 1, 0, 0);

    const x0 = -cw * 0.5;
    const y0 = -ch * 0.5;

    ctx.fillStyle = 'rgba(0,0,0,0.42)';
    ctx.fillRect(x0 + 3, y0 + 4, cw, ch);

    ctx.fillStyle = o.bgFill;
    ctx.fillRect(x0, y0, cw, ch);

    ctx.save();
    ctx.beginPath();
    ctx.rect(x0 + 1.5, y0 + 1.5, cw - 3, ch - 3);
    ctx.clip();

    const img = getFrameImg(curWorm, fi);
    if(o.plane && o.plane.id !== 'char'){
      if(img){
        ctx.save();
        ctx.globalAlpha = 0.22;
        ctx.drawImage(img, x0 + 1.5, y0 + 1.5, cw - 3, ch - 3);
        ctx.restore();
      }
      drawPlaneObjectsInRect(ctx, o.plane, fi, x0 + 2, y0 + 2, cw - 4, ch - 4, true);
    } else {
      if(img && !o.cropToMask){
        ctx.save();
        ctx.globalAlpha = 0.38;
        ctx.drawImage(img, x0 + 1.5, y0 + 1.5, cw - 3, ch - 3);
        ctx.restore();
      }
      drawSamCutoutInRect(ctx, curWorm, fi, x0 + 2, y0 + 2, cw - 4, ch - 4, {
        cropToMask: o.cropToMask,
        drawOutline: true,
        outlineColor: o.borderColor === '#FFFFFF' ? '#EF9F3A' : o.borderColor,
        drawDoodle: true,
        doodleColor: '#161412'
      });
    }
    ctx.restore();

    ctx.strokeStyle = o.borderColor;
    ctx.lineWidth = o.borderWidth;
    ctx.strokeRect(x0, y0, cw, ch);

    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#161412';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(0, 0, 2.6, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    if(o.label){
      ctx.font = '700 9.5px "JetBrains Mono", monospace';
      const tw = ctx.measureText(o.label).width + 8;
      ctx.fillStyle = 'rgba(12, 13, 18, 0.86)';
      ctx.fillRect(x0, y0 - 15, tw, 13);
      ctx.fillStyle = o.labelColor;
      ctx.fillText(o.label, x0 + 4, y0 - 5);
    }
    if(o.subLabel){
      ctx.font = '600 8.5px "JetBrains Mono", monospace';
      const sw = ctx.measureText(o.subLabel).width + 6;
      ctx.fillStyle = 'rgba(12, 13, 18, 0.78)';
      ctx.fillRect(x0 + 2, y0 + ch - 13, sw, 11);
      ctx.fillStyle = '#F6EFE3';
      ctx.fillText(o.subLabel, x0 + 5, y0 + ch - 4.5);
    }
    ctx.restore();
  }

  function renderParallelTimelinesMode(ctx, W, H, fi, N, planes, zRef){
    const dark = parallelDark;
    if(dark){
      const bg = ctx.createRadialGradient(W*0.38, H*0.42, 20, W*0.5, H*0.5, W*0.75);
      bg.addColorStop(0, '#141720');
      bg.addColorStop(1, '#06070A');
      ctx.fillStyle = bg;
    } else {
      const bg = ctx.createLinearGradient(0, 0, 0, H);
      bg.addColorStop(0, '#EFE6D5');
      bg.addColorStop(1, '#E4D7C0');
      ctx.fillStyle = bg;
    }
    ctx.fillRect(0, 0, W, H);

    const vx = -W * 0.04, vy = H * 0.17;
    const fx = W * 0.99,  fy = H * 0.79;

    function spinePt(u){
      const p = Math.pow(Math.max(0, Math.min(1, u)), 0.88);
      return {
        x: vx + p * (fx - vx),
        y: vy + p * (fy - vy),
        s: 0.24 + p * 0.96
      };
    }

    const uPlay = 0.16 + (N > 1 ? (fi / (N - 1)) : 0.5) * 0.64;
    const spPlay = spinePt(uPlay);

    const keys = (S && S.keys) || curWorm.keys || {};
    const drawnArr = (keys.drawn && keys.drawn.length >= 2)
      ? keys.drawn.slice()
      : [0, Math.floor(N*0.25), Math.floor(N*0.5), Math.floor(N*0.75), Math.max(0, N-1)];

    const lineRGB = dark ? '255,255,255' : '22,20,18';

    if(parallelSubMode === 'dual'){
      const redOff  = {dx: -84, dy: 82};
      const blueOff = {dx: 108, dy: -46};

      function redPt(u){
        const c = spinePt(u);
        return {x: c.x + redOff.dx * c.s, y: c.y + redOff.dy * c.s, s: c.s};
      }
      function bluePt(u){
        const c = spinePt(u);
        return {x: c.x + blueOff.dx * c.s, y: c.y + blueOff.dy * c.s, s: c.s};
      }

      const nBlocks = Math.max(3, Math.min(8, drawnArr.length));
      for(let b = 0; b < nBlocks; b++){
        const uIn0 = (b / nBlocks) * 0.88;
        const uIn1 = ((b + 1) / nBlocks) * 0.88;
        const uOut0 = Math.min(1.0, uIn0 * 1.12);
        const uOut1 = Math.min(1.0, uIn1 * 1.12);

        const c0 = spinePt(uIn0), c1 = spinePt(uIn1);
        const r0 = redPt(uOut0),  r1 = redPt(uOut1);
        const bl0 = bluePt(uOut0), bl1 = bluePt(uOut1);

        ctx.fillStyle = (b % 2 === 0)
          ? `rgba(${lineRGB}, ${dark ? 0.14 : 0.11})`
          : `rgba(${lineRGB}, ${dark ? 0.04 : 0.03})`;
        ctx.beginPath();
        ctx.moveTo(c0.x, c0.y); ctx.lineTo(c1.x, c1.y);
        ctx.lineTo(r1.x, r1.y); ctx.lineTo(r0.x, r0.y);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = (b % 2 === 1)
          ? `rgba(${lineRGB}, ${dark ? 0.14 : 0.11})`
          : `rgba(${lineRGB}, ${dark ? 0.04 : 0.03})`;
        ctx.beginPath();
        ctx.moveTo(c0.x, c0.y); ctx.lineTo(c1.x, c1.y);
        ctx.lineTo(bl1.x, bl1.y); ctx.lineTo(bl0.x, bl0.y);
        ctx.closePath();
        ctx.fill();

        const subRays = 12;
        ctx.strokeStyle = `rgba(${lineRGB}, ${dark ? 0.36 : 0.28})`;
        ctx.lineWidth = 0.75;
        for(let r = 0; r <= subRays; r++){
          const fSub = r / subRays;
          const uc = uIn0 + fSub * (uIn1 - uIn0);
          const uo = uOut0 + fSub * (uOut1 - uOut0);
          const pc = spinePt(uc);
          const pr = redPt(uo);
          const pb = bluePt(uo);
          ctx.beginPath();
          ctx.moveTo(pc.x, pc.y); ctx.lineTo(pr.x, pr.y);
          ctx.moveTo(pc.x, pc.y); ctx.lineTo(pb.x, pb.y);
          ctx.stroke();
        }
      }

      const cStart = spinePt(0), cEnd = spinePt(1);
      const rStart = redPt(0),   rEnd = redPt(1);
      const bStart = bluePt(0),  bEnd = bluePt(1);

      ctx.strokeStyle = `rgba(${lineRGB}, 0.72)`;
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(cStart.x, cStart.y); ctx.lineTo(cEnd.x, cEnd.y); ctx.stroke();

      ctx.strokeStyle = '#FF3B30';
      ctx.lineWidth = 2.4;
      ctx.beginPath(); ctx.moveTo(rStart.x, rStart.y); ctx.lineTo(rEnd.x, rEnd.y); ctx.stroke();

      ctx.strokeStyle = '#2E7CF6';
      ctx.lineWidth = 2.4;
      ctx.beginPath(); ctx.moveTo(bStart.x, bStart.y); ctx.lineTo(bEnd.x, bEnd.y); ctx.stroke();

      const rPlay = redPt(uPlay);
      const bPlay = bluePt(uPlay);
      const ringRx = Math.hypot(bPlay.x - rPlay.x, bPlay.y - rPlay.y) * 0.56;
      const ringRy = ringRx * 0.94;

      ctx.save();
      ctx.strokeStyle = `rgba(${lineRGB}, 0.52)`;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.ellipse(spPlay.x, spPlay.y, ringRx, ringRy, -0.15, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      const fStretched1 = Math.max(0, Math.min(N - 1, Math.round(fi * 0.5)));
      const fStretched2 = Math.max(0, Math.min(N - 1, Math.min(N - 1, Math.round(fi * 0.5 + N * 0.25))));
      const bgPlane = planes.find(p => p.id !== 'char') || planes[0];

      drawUpright3DCard(ctx, bPlay.x, bPlay.y, 78, 66, fStretched2, {
        plane: bgPlane,
        borderColor: '#2E7CF6',
        borderWidth: 2.0,
        cropToMask: false,
        label: `output timeline 2`,
        labelColor: '#6CA6FF',
        subLabel: `${bgPlane ? bgPlane.label : 'Parallax'} · f${fStretched2+1}`
      });

      const fPrev = Math.max(0, fi - 2);
      const spEcho = spinePt(Math.max(0.06, uPlay - 0.045));
      drawUpright3DCard(ctx, spEcho.x, spEcho.y, 82, 70, fPrev, {
        plane: null,
        borderColor: `rgba(${lineRGB}, 0.55)`,
        borderWidth: 1.3,
        alpha: 0.72,
        cropToMask: false
      });

      drawUpright3DCard(ctx, spPlay.x, spPlay.y, 88, 74, fi, {
        plane: null,
        borderColor: '#FFFFFF',
        borderWidth: 2.2,
        cropToMask: false,
        label: `input spine · f${fi+1}/${N}`,
        labelColor: '#EF9F3A',
        subLabel: `1.0× realtime`
      });

      drawUpright3DCard(ctx, rPlay.x, rPlay.y, 96, 82, fStretched1, {
        plane: null,
        borderColor: '#FF3B30',
        borderWidth: 2.4,
        cropToMask: true,
        label: `output timeline 1`,
        labelColor: '#FF6961',
        subLabel: `1/2× stretched · f${fStretched1+1}`
      });

      ctx.save();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2.4;
      ctx.shadowColor = 'rgba(255,255,255,0.75)';
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.moveTo(rPlay.x, rPlay.y);
      ctx.lineTo(spPlay.x, spPlay.y);
      ctx.lineTo(bPlay.x, bPlay.y);
      ctx.stroke();
      ctx.restore();

      ctx.fillStyle = '#FF453A';
      ctx.font = '700 13px "Bricolage Grotesque", sans-serif';
      ctx.fillText('output timeline 1 (SAM cutout · 1/K stretched)', Math.max(12, rPlay.x - 52), Math.min(H - 12, rPlay.y + 58));

      ctx.fillStyle = '#409CFF';
      ctx.fillText('output timeline 2 (multiplane parallax)', Math.min(W - 245, bPlay.x + 48), Math.max(38, bPlay.y + 10));

      ctx.fillStyle = dark ? '#FFFFFF' : '#161412';
      ctx.font = '800 15px "Bricolage Grotesque", sans-serif';
      ctx.fillText('Parallel & Stretched Output Timelines', W * 0.43, 44);
      ctx.fillStyle = dark ? 'rgba(246,239,227,0.82)' : '#5E554B';
      ctx.font = '500 11.5px "Bricolage Grotesque", sans-serif';
      ctx.fillText('Distributed input is stretched 1 / K slower per timeline with the head fixed.', W * 0.43, 62);
      return;
    }

    // Sub-mode 1: Radial Multi-Worm Fan (all depth planes around the 3D cross-section ring)
    const visPlanes = planes.filter(p => isPlaneVisible(p.id));
    const activeList = visPlanes.length ? visPlanes : planes;
    const K = Math.max(2, activeList.length);

    const RADIAL_ANGLES = [-2.55, 2.25, -1.35, 0.18, 1.15, -0.55, 2.85, -1.95];
    const RAIL_COLORS = ['#EF9F3A', '#FF453A', '#32D74B', '#409CFF', '#BF5AF2', '#FFD60A', '#64D2FF'];

    const baseRad = Math.min(W, H) * 0.30;

    function railPt(rIdx, u){
      const c = spinePt(u);
      const ang = RADIAL_ANGLES[rIdx % RADIAL_ANGLES.length];
      const rx = Math.cos(ang) * baseRad * 1.08 * c.s;
      const ry = Math.sin(ang) * baseRad * 0.88 * c.s;
      return {x: c.x + rx, y: c.y + ry, s: c.s, ang};
    }

    const nSegs = Math.max(4, Math.min(7, drawnArr.length));
    for(let rIdx = 0; rIdx < K; rIdx++){
      const plane = activeList[rIdx];
      const isSubj = (plane.id === 'char');
      const stretchFactor = 1 + (rIdx / Math.max(1, K)) * 0.32;

      for(let s = 0; s < nSegs; s++){
        const uIn0 = (s / nSegs) * 0.82;
        const uIn1 = ((s + 1) / nSegs) * 0.82;
        const uOut0 = Math.min(1.0, uIn0 * stretchFactor);
        const uOut1 = Math.min(1.0, uIn1 * stretchFactor);

        if(isSubj && s % 2 === 0){
          const c0 = spinePt(uIn0), c1 = spinePt(uIn1);
          const p0 = railPt(rIdx, uOut0), p1 = railPt(rIdx, uOut1);
          ctx.fillStyle = `rgba(${lineRGB}, ${dark ? 0.13 : 0.09})`;
          ctx.beginPath();
          ctx.moveTo(c0.x, c0.y); ctx.lineTo(c1.x, c1.y);
          ctx.lineTo(p1.x, p1.y); ctx.lineTo(p0.x, p0.y);
          ctx.closePath();
          ctx.fill();
        }

        const nFan = isSubj ? 9 : 6;
        ctx.strokeStyle = `rgba(${lineRGB}, ${isSubj ? (dark ? 0.42 : 0.34) : (dark ? 0.22 : 0.18)})`;
        ctx.lineWidth = isSubj ? 0.85 : 0.65;
        for(let k = 0; k <= nFan; k++){
          const fSub = k / nFan;
          const uc = uIn0 + fSub * (uIn1 - uIn0);
          const uo = uOut0 + fSub * (uOut1 - uOut0);
          const pc = spinePt(uc);
          const pr = railPt(rIdx, uo);
          ctx.beginPath();
          ctx.moveTo(pc.x, pc.y);
          ctx.lineTo(pr.x, pr.y);
          ctx.stroke();
        }
      }

      const pStart = railPt(rIdx, 0), pEnd = railPt(rIdx, 1);
      ctx.strokeStyle = isSubj ? '#EF9F3A' : `rgba(${lineRGB}, 0.55)`;
      ctx.lineWidth = isSubj ? 2.0 : 1.15;
      ctx.beginPath();
      ctx.moveTo(pStart.x, pStart.y);
      ctx.lineTo(pEnd.x, pEnd.y);
      ctx.stroke();
    }

    const c0 = spinePt(0), c1 = spinePt(1);
    ctx.strokeStyle = `rgba(${lineRGB}, 0.80)`;
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(c0.x, c0.y); ctx.lineTo(c1.x, c1.y); ctx.stroke();

    const ringR = baseRad * spPlay.s;
    ctx.save();
    ctx.strokeStyle = `rgba(${lineRGB}, 0.62)`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(spPlay.x, spPlay.y, ringR * 1.08, ringR * 0.88, -0.10, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    for(let e = 3; e >= 1; e--){
      const fEcho = Math.max(0, fi - e * 2);
      const uEcho = Math.max(0.05, uPlay - e * 0.032);
      const pe = spinePt(uEcho);
      drawUpright3DCard(ctx, pe.x, pe.y, 70, 60, fEcho, {
        plane: null,
        borderColor: `rgba(${lineRGB}, 0.45)`,
        borderWidth: 1.1,
        alpha: 0.48 + (3 - e) * 0.14,
        cropToMask: false
      });
    }

    const railCards = [];
    for(let rIdx = 0; rIdx < K; rIdx++){
      const plane = activeList[rIdx];
      const pt = railPt(rIdx, uPlay);
      const col = plane.id === 'char' ? '#EF9F3A' : RAIL_COLORS[rIdx % RAIL_COLORS.length];
      const kSpeed = zRef / Math.max(0.3, plane.z);
      const fLayer = plane.id === 'char'
        ? fi
        : Math.max(0, Math.min(N - 1, Math.round(fi * Math.min(1.2, Math.max(0.35, kSpeed)))));
      railCards.push({rIdx, plane, pt, col, kSpeed, fLayer});
    }

    ctx.save();
    ctx.strokeStyle = `rgba(${lineRGB}, 0.85)`;
    ctx.lineWidth = 1.6;
    for(const rc of railCards){
      ctx.beginPath();
      ctx.moveTo(spPlay.x, spPlay.y);
      ctx.lineTo(rc.pt.x, rc.pt.y);
      ctx.stroke();
    }
    ctx.restore();

    drawUpright3DCard(ctx, spPlay.x, spPlay.y, 82, 70, fi, {
      plane: null,
      borderColor: '#FFFFFF',
      borderWidth: 2.2,
      cropToMask: false,
      label: `Center Spine · f${fi+1}`,
      labelColor: '#FFFFFF'
    });

    railCards.sort((a, b) => a.pt.y - b.pt.y);
    for(const rc of railCards){
      const isSubj = (rc.plane.id === 'char');
      const cw = isSubj ? 92 : 72;
      const ch = isSubj ? 78 : 62;
      const shortLbl = String(rc.plane.label || rc.plane.id).split('(')[0].trim().slice(0, 14);
      drawUpright3DCard(ctx, rc.pt.x, rc.pt.y, cw, ch, rc.fLayer, {
        plane: isSubj ? null : rc.plane,
        borderColor: rc.col,
        borderWidth: isSubj ? 2.5 : 1.8,
        cropToMask: isSubj,
        label: `${shortLbl} (z=${rc.plane.z})`,
        labelColor: rc.col,
        subLabel: `k=${rc.kSpeed.toFixed(2)}× · f${rc.fLayer+1}`
      });
    }

    const capW = Math.min(W - 24, 470);
    ctx.fillStyle = dark ? 'rgba(6, 7, 10, 0.78)' : 'rgba(251, 250, 246, 0.88)';
    ctx.fillRect(W * 0.5 - capW * 0.5, H - 36, capW, 30);
    ctx.fillStyle = dark ? '#FFFFFF' : '#161412';
    ctx.font = '700 11.5px "Bricolage Grotesque", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      `In this framework, ${K} parallel depth-plane timelines fan out around the spine (k = z_ref / z).`,
      W * 0.5, H - 17
    );
    ctx.textAlign = 'left';
  }

  function renderStage(fi){
    if(!curWorm) return;
    const W = (S && S.W) || curWorm.W || 480;
    const H = (S && S.H) || curWorm.H || 360;
    if(cvStage.width !== W || cvStage.height !== H){ cvStage.width = W; cvStage.height = H; }
    const ctx = ctxStage;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#FBFAF6';
    ctx.fillRect(0,0,W,H);
    const img = getFrameImg(curWorm, fi);

    if(view === 'footage'){
      if(img) ctx.drawImage(img,0,0,W,H);
      return;
    }
    if(view === 'masks'){
      if(img){ ctx.save(); ctx.globalAlpha=0.3; ctx.drawImage(img,0,0,W,H); ctx.restore(); }
      const masks = (S && S.masks && S.masks[fi]) ? S.masks[fi] :
        ((curWorm.frames && curWorm.frames[fi] && curWorm.frames[fi].ring) ? [curWorm.frames[fi].ring.map(p=>[p[0]*W,p[1]*H])] : []);
      masks.forEach(poly=>{
        if(!poly || poly.length<3) return;
        ctx.beginPath();
        poly.forEach((p,j)=>{ if(j===0) ctx.moveTo(p[0],p[1]); else ctx.lineTo(p[0],p[1]); });
        ctx.closePath();
        ctx.fillStyle = 'rgba(239,159,58,0.52)'; ctx.fill();
        ctx.strokeStyle = '#8A4A05'; ctx.lineWidth = 2; ctx.stroke();
      });
      return;
    }
    if(view === 'cutout'){
      if(img){ ctx.save(); ctx.globalAlpha=0.16; ctx.drawImage(img,0,0,W,H); ctx.restore(); }
      drawSamCutoutInRect(ctx, curWorm, fi, 0, 0, W, H, {cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
      return;
    }
    if(view === 'composite'){
      if(img){
        ctx.save(); ctx.globalAlpha = 0.55; ctx.drawImage(img,0,0,W,H); ctx.restore();
        ctx.fillStyle = 'rgba(246,239,227,0.22)'; ctx.fillRect(0,0,W,H);
      }
    } else {
      const g = ctx.createLinearGradient(0,0,0,H*0.72);
      g.addColorStop(0,'#F4E8D1'); g.addColorStop(1,'#FBFAF6');
      ctx.fillStyle = g; ctx.fillRect(0,0,W,H);
      ctx.fillStyle = '#EDE0C5'; ctx.fillRect(0,H*0.68,W,H*0.32);
    }

    const boilSeed = boilOn ? ((fi%3)+1) : 0;
    const boilAmp  = boilOn ? 0.85 : 0;
    const planes = getActivePlanes();
    const celFill = celOn ? '#FBFAF6' : null;

    for(const plane of planes){
      if(!isPlaneVisible(plane.id)) continue;
      const off = camOffset(plane.z, fi);
      if(plane.id === 'char'){
        const strokes = (S && S.cast && S.cast.frames && S.cast.frames[fi]) ? S.cast.frames[fi] :
          ((curWorm.frames && curWorm.frames[fi] && curWorm.frames[fi].doodle) ? curWorm.frames[fi].doodle.map(s=>s.map(p=>[p[0]*W,p[1]*H])) : []);
        if(celFill && strokes.length) drawStrokes(ctx, strokes, {color:'rgba(0,0,0,0)', width:0.1, boilSeed, boilAmp, fill:celFill});
        if(fi===0 && view==='cartoon') drawStrokes(ctx, strokes, {color:'#EF9F3A', width:6, boilSeed, boilAmp});
        drawStrokes(ctx, strokes, {color:'#161412', width:2.5, boilSeed, boilAmp});
      } else if(S && Array.isArray(S.objects)){
        const objs = S.objects.filter(o => o.plane === plane.id);
        const depthAlpha = plane.z>=10 ? 0.50 : (plane.z>=6 ? 0.65 : (plane.z>=3 ? 0.85 : 0.95));
        for(const o of objs){
          const ost = (o.frames && o.frames[fi]) ? o.frames[fi] : o.strokes;
          if(!ost) continue;
          drawStrokes(ctx, ost, {color:`rgba(22,20,18,${depthAlpha})`, width:1.9, dx:off.dx, dy:off.dy, boilSeed:boilSeed+1, boilAmp:boilAmp*0.6, fill:(celFill && plane.z<10)?celFill:null});
        }
      }
    }
  }

  function renderWorm(fi){
    if(!curWorm) return;
    const W = cvWorm.width, H = cvWorm.height;
    const ctx = ctxWorm;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#FBFAF6';
    ctx.fillRect(0,0,W,H);
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const planes = getActivePlanes();
    const meta = LENS_META[wormMode] || LENS_META.parallel;
    document.getElementById('idxLblWorm').textContent = meta.lbl;
    document.getElementById('idxLblWormR').textContent = `${planes.length} planes · f ${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`;

    const zRef = (S && S.z_ref) || curWorm.z_ref || 2;

    if(wormMode === 'parallel'){
      renderParallelTimelinesMode(ctx, W, H, fi, N, planes, zRef);
      return;
    }

    if(wormMode === 'strobe'){
      const padT = 30, padB = 30, padL = 14, padR = 14;
      const stageW = W - padL - padR, stageH = H - padT - padB;
      ctx.save();
      ctx.beginPath(); ctx.roundRect(padL, padT, stageW, stageH, 6); ctx.clip();
      const bgImg = getFrameImg(curWorm, fi) || getFrameImg(curWorm, 0);
      if(bgImg){ ctx.globalAlpha = 0.25; ctx.drawImage(bgImg, padL, padT, stageW, stageH); ctx.globalAlpha = 1; }
      ctx.fillStyle = 'rgba(251,250,246,0.45)'; ctx.fillRect(padL, padT, stageW, stageH);

      const nGhosts = Math.min(N, 7);
      for(let g=0; g<nGhosts; g++){
        const ti = nGhosts===1 ? 0 : Math.round((g/(nGhosts-1))*(N-1));
        if(ti === fi) continue;
        drawSamCutoutInRect(ctx, curWorm, ti, padL, padT, stageW, stageH, {
          cropToMask:false, drawOutline:true, outlineColor: ti===0 ? '#2E7A4A' : (ti===N-1 ? '#B8432F' : '#8A6114'),
          drawDoodle:true, doodleColor:'rgba(22,20,18,0.55)', alpha: 0.32
        });
      }
      const frames = curWorm.frames || [];
      if(frames.length >= 2){
        ctx.beginPath();
        frames.forEach((fr, ti)=>{
          const c = fr.c || [0.5,0.5];
          const x = padL + c[0]*stageW, y = padT + c[1]*stageH;
          if(ti===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        });
        ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 3.2; ctx.stroke();
      }
      drawSamCutoutInRect(ctx, curWorm, fi, padL, padT, stageW, stageH, {
        cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true, doodleColor:'#161412', alpha:1.0
      });
      ctx.restore();
      ctx.strokeStyle = '#161412'; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.roundRect(padL, padT, stageW, stageH, 6); ctx.stroke();
      return;
    }

    if(wormMode === 'kymo'){
      const padL = 116, padR = 16, padT = 30, padB = 22;
      const trackW = W - padL - padR, availH = H - padT - padB, gap = 7;
      const bandH = (availH - gap*2) / 3;
      const frames = curWorm.frames || [];
      const bands = [
        {title:'Horizontal X(t)', sub:'Left ↔ Right', color:'#EF9F3A', getVal:fr=>fr.c?fr.c[0]:0.5, stamps:true},
        {title:'Vertical Bounce Y(t)', sub:'Top ↕ Bottom', color:'#2E7A4A', getVal:fr=>fr.c?fr.c[1]:0.5},
        {title:'Scale R(t) & Cam Pan', sub:'Size & Camera', color:'#2B6CB0', getVal:fr=>Math.min(1,(fr.r||0.15)*2.5)}
      ];
      bands.forEach((b, bIdx)=>{
        const y0 = padT + bIdx*(bandH + gap);
        ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.1;
        ctx.beginPath(); ctx.roundRect(8, y0, W-16, bandH, 5); ctx.fill(); ctx.stroke();
        ctx.fillStyle = 'rgba(239,159,58,0.12)'; ctx.fillRect(9, y0+1, padL-14, bandH-2);
        ctx.fillStyle = '#161412'; ctx.font = '700 10.5px "Bricolage Grotesque", sans-serif';
        ctx.fillText(b.title, 13, y0 + bandH*0.42);
        ctx.fillStyle = '#6B6259'; ctx.font = '500 9px "JetBrains Mono", monospace';
        ctx.fillText(b.sub, 13, y0 + bandH*0.72);
        if(frames.length >= 2){
          ctx.beginPath();
          frames.forEach((fr, ti)=>{
            const x = padL + (N>1 ? (ti/(N-1))*trackW : trackW*0.5);
            const y = y0 + 8 + Math.max(0,Math.min(1,b.getVal(fr)))*(bandH-16);
            if(ti===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
          });
          ctx.strokeStyle = b.color; ctx.lineWidth = 2.4; ctx.stroke();
        }
      });
      const scrubX = padL + (N>1 ? (fi/(N-1))*trackW : trackW*0.5);
      ctx.save(); ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2; ctx.setLineDash([4,3]);
      ctx.beginPath(); ctx.moveTo(scrubX, padT-4); ctx.lineTo(scrubX, H-padB+4); ctx.stroke(); ctx.restore();
      return;
    }

    if(wormMode === 'anatomy'){
      const padL = 12, padR = 12, padT = 28, padB = 20;
      const topH = Math.round((H - padT - padB)*0.52);
      const botY = padT + topH + 8, botH = H - padB - botY;
      const halfW = Math.round((W - padL - padR - 8)*0.5);
      ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.roundRect(padL, padT, halfW, topH, 5); ctx.fill(); ctx.stroke();
      drawSamCutoutInRect(ctx, curWorm, 0, padL+6, padT+20, halfW-12, topH-26, {cropToMask:true, drawOutline:true, outlineColor:'#BFAF97', drawDoodle:true, doodleColor:'#EF9F3A'});
      ctx.fillStyle = '#8A4A05'; ctx.font = '700 10px "JetBrains Mono", monospace';
      ctx.fillText('THE LINE (f=01 Seed Doodle)', padL+8, padT+14);

      const rx0 = padL + halfW + 8;
      ctx.fillStyle = '#FFFDF8'; ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.roundRect(rx0, padT, halfW, topH, 5); ctx.fill(); ctx.stroke();
      drawSamCutoutInRect(ctx, curWorm, fi, rx0+6, padT+20, halfW-12, topH-26, {cropToMask:true, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true, doodleColor:'#161412'});
      ctx.fillStyle = '#161412';
      ctx.fillText(`WARPED RIG @ f=${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`, rx0+8, padT+14);

      ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.1;
      ctx.beginPath(); ctx.roundRect(padL, botY, W-padL-padR, botH, 5); ctx.fill(); ctx.stroke();
      const jPadL = padL + 104, jTrackW = W - padR - jPadL - 8;
      const joints = curWorm.joints || {};
      const jNames = Object.keys(joints);
      const colors = ['#EF9F3A','#2E7A4A','#2B6CB0','#B8432F','#6B46C1'];
      const rows = jNames.length
        ? jNames.slice(0,5).map((jn,i)=>({label:jn.replace(/_/g,' '), pts:joints[jn], color:colors[i%colors.length]}))
        : (curWorm.depth_worms||[]).slice(0,5).map((dw,i)=>({label:dw.label, pts:(dw.track||[]).map(t=>[t[0],t[1]]), color:dw.color||colors[i%colors.length]}));
      const rTop = botY + 18, rH = Math.max(16, (botH - 24)/Math.max(1, rows.length));
      rows.forEach((r, idx)=>{
        const ry = rTop + idx*rH;
        ctx.fillStyle = '#6B6259'; ctx.font = '600 9.5px "JetBrains Mono", monospace';
        ctx.fillText(String(r.label).slice(0,13), padL+8, ry + rH*0.65);
        const pts = r.pts || [];
        if(pts.length >= 2){
          ctx.beginPath();
          pts.forEach((uv, ti)=>{
            const x = jPadL + (N>1 ? (ti/(N-1))*jTrackW : jTrackW*0.5);
            const y = ry + 3 + Math.max(0,Math.min(1,uv[1]))*(rH-6);
            if(ti===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
          });
          ctx.strokeStyle = r.color; ctx.lineWidth = 2; ctx.stroke();
        }
      });
      const scrubX = jPadL + (N>1 ? (fi/(N-1))*jTrackW : jTrackW*0.5);
      ctx.save(); ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2; ctx.setLineDash([4,3]);
      ctx.beginPath(); ctx.moveTo(scrubX, rTop-4); ctx.lineTo(scrubX, botY+botH-4); ctx.stroke(); ctx.restore();
      return;
    }

    if(wormMode === 'box'){
      const padX=26, padY=28, availW=W-padX*2, availH=H-padY*2, nP=planes.length;
      const srcW = (S && S.W) || curWorm.W || 480, srcH = (S && S.H) || curWorm.H || 360;
      planes.forEach((plane, idx)=>{
        const vis = isPlaneVisible(plane.id);
        const u = nP===1 ? 0.5 : idx/(nP-1);
        const scale = 0.54 + u*0.34;
        const pw = availW*scale, ph = availH*scale;
        const cx = padX + (1-u)*(availW-pw)*0.85 + u*(availW-pw)*0.12;
        const cy = padY + (1-u)*4 + u*(availH-ph)*0.82;
        const off = camOffset(plane.z, fi);
        const sx = pw/srcW, sy = ph/srcH;
        const t = tintForPlane(plane.id, plane.z, zRef);
        ctx.save(); ctx.globalAlpha = vis ? 1 : 0.22;
        ctx.fillStyle = t.fill; ctx.strokeStyle = t.stroke; ctx.lineWidth = plane.id==='char'?2.2:1.3;
        ctx.beginPath(); ctx.roundRect(cx,cy,pw,ph,4); ctx.fill(); ctx.stroke();
        ctx.save(); ctx.beginPath(); ctx.rect(cx,cy,pw,ph); ctx.clip();
        if(plane.id==='char'){
          drawSamCutoutInRect(ctx, curWorm, fi, cx, cy, pw, ph, {cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
        } else if(S && Array.isArray(S.objects)){
          for(const o of S.objects.filter(x=>x.plane===plane.id)){
            const ost = (o.frames && o.frames[fi]) ? o.frames[fi] : o.strokes;
            if(ost) drawStrokes(ctx, ost.map(s=>s.map(p=>[cx+(p[0]+off.dx)*sx, cy+(p[1]+off.dy)*sy])), {color:'#161412', width:1.4});
          }
        }
        ctx.restore();
        ctx.fillStyle='#161412'; ctx.font='600 10px "JetBrains Mono", monospace';
        ctx.fillText(`${plane.label} · z=${plane.z}`, cx+6, cy+13);
        ctx.restore();
      });
      return;
    }

    // Disentangled Plane Worms ('lanes')
    const planesNearFirst = planes.slice().reverse();
    const padL = 114, padR = 14, padT = 28, padB = 20;
    const availH = H - padT - padB;
    const nP = Math.max(1, planesNearFirst.length);
    const laneGap = 5;
    const laneH = Math.max(34, (availH - laneGap*(nP-1)) / nP);
    const trackW = W - padL - padR;

    for(let pIdx=0; pIdx<planesNearFirst.length; pIdx++){
      const plane = planesNearFirst[pIdx];
      const vis = isPlaneVisible(plane.id);
      const y0 = padT + pIdx*(laneH + laneGap);
      const t = tintForPlane(plane.id, plane.z, zRef);
      const isChar = (plane.id === 'char');

      ctx.save();
      ctx.globalAlpha = vis ? 1 : 0.32;
      ctx.fillStyle = isChar ? '#FFFDF8' : '#FFFFFF';
      ctx.strokeStyle = isChar ? '#EF9F3A' : '#BFAF97';
      ctx.lineWidth = isChar ? 1.8 : 1.1;
      ctx.beginPath(); ctx.roundRect(8, y0, W-16, laneH, 5); ctx.fill(); ctx.stroke();

      ctx.fillStyle = t.fill;
      ctx.fillRect(9, y0+1, padL-14, laneH-2);
      ctx.fillStyle = '#161412';
      ctx.font = '700 11px "Bricolage Grotesque", sans-serif';
      ctx.fillText(String(plane.label||plane.id).split('(')[0].trim().slice(0,15), 13, y0 + Math.min(19, laneH*0.44));
      ctx.fillStyle = '#6B6259';
      ctx.font = '500 9.5px "JetBrains Mono", monospace';
      ctx.fillText(`z=${plane.z} · k=${(zRef/Math.max(0.2,plane.z)).toFixed(2)}x`, 13, y0 + Math.min(33, laneH*0.78));

      ctx.save();
      ctx.beginPath(); ctx.rect(padL, y0+2, trackW, laneH-4); ctx.clip();

      const nStamps = Math.min(N, isChar ? 6 : 5);
      const celH = Math.max(24, laneH - 8), celW = Math.round(celH * 1.22);
      for(let sIdx=0; sIdx<nStamps; sIdx++){
        const ti = nStamps===1 ? 0 : Math.round((sIdx/(nStamps-1))*(N-1));
        if(Math.abs(ti - fi) <= Math.max(1, Math.floor(N/(nStamps*2.4)))) continue;
        const cx = padL + (N>1 ? (ti/(N-1))*trackW : trackW*0.5);
        const rx = Math.max(padL+2, Math.min(padL+trackW-celW-2, cx-celW*0.5));
        const ry = y0 + (laneH-celH)*0.5;
        ctx.save(); ctx.globalAlpha = vis ? 0.7 : 0.25;
        ctx.fillStyle = '#FBFAF6'; ctx.strokeStyle = '#DED2BF';
        ctx.fillRect(rx,ry,celW,celH); ctx.strokeRect(rx,ry,celW,celH);
        if(isChar) drawSamCutoutInRect(ctx, curWorm, ti, rx+1, ry+1, celW-2, celH-2, {cropToMask:true, drawOutline:false, drawDoodle:true});
        else drawPlaneObjectsInRect(ctx, plane, ti, rx+1, ry+1, celW-2, celH-2, true);
        ctx.restore();
      }

      const actX = padL + (N>1 ? (fi/(N-1))*trackW : trackW*0.5);
      const actH = Math.max(28, laneH - 4), actW = Math.round(actH * 1.32);
      const arx = Math.max(padL+2, Math.min(padL+trackW-actW-2, actX-actW*0.5));
      const ary = y0 + (laneH-actH)*0.5;
      ctx.fillStyle = '#FFFBF4'; ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2.1;
      ctx.fillRect(arx,ary,actW,actH);
      if(isChar) drawSamCutoutInRect(ctx, curWorm, fi, arx+1, ary+1, actW-2, actH-2, {cropToMask:true, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
      else drawPlaneObjectsInRect(ctx, plane, fi, arx+1, ary+1, actW-2, actH-2, true);
      ctx.strokeRect(arx,ary,actW,actH);

      ctx.restore();
      ctx.restore();
    }

    const scrubX = padL + (N>1 ? (fi/(N-1))*trackW : trackW*0.5);
    ctx.save();
    ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2; ctx.setLineDash([4,3]);
    ctx.beginPath(); ctx.moveTo(scrubX, padT-4); ctx.lineTo(scrubX, H-padB+4); ctx.stroke();
    ctx.restore();
  }

  function updateDecoder(fi){
    if(!curWorm) return;
    const frames = curWorm.frames || [];
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const planes = getActivePlanes();
    const zRef = (S && S.z_ref) || curWorm.z_ref || 2;

    const c0 = (frames[0] && frames[0].c) ? frames[0].c : [0.5, 0.5];
    const c1 = (frames[frames.length-1] && frames[frames.length-1].c) ? frames[frames.length-1].c : [0.5, 0.5];
    const dxPct = Math.round((c1[0] - c0[0]) * 100);
    const dyPct = Math.round((c1[1] - c0[1]) * 100);
    const dirStr = Math.abs(dxPct) < 5 && Math.abs(dyPct) < 5
      ? 'Holds position near frame center'
      : `${dxPct > 3 ? 'Moves Right (+' + dxPct + '%)' : (dxPct < -3 ? 'Moves Left (' + dxPct + '%)' : 'Steady X')}${Math.abs(dyPct) > 3 ? ', ' + (dyPct > 0 ? 'Down +' + dyPct + '%' : 'Up ' + dyPct + '%') : ''}`;
    document.getElementById('idxDecShapeT').textContent = TOPO_HUMAN[curWorm.topology] || curWorm.topology || 'Tracked Motion';
    document.getElementById('idxDecShapeP').textContent =
      `${dirStr} from (${c0[0].toFixed(2)}, ${c0[1].toFixed(2)}) to (${c1[0].toFixed(2)}, ${c1[1].toFixed(2)}) over ${curWorm.duration_s || (N/12).toFixed(1)}s.`;

    const minZ = Math.min(...planes.map(p=>p.z));
    const maxZ = Math.max(...planes.map(p=>p.z));
    const panMag = Math.round((curWorm.cam_pan_mag || 0) * ((S && S.W) || curWorm.W || 480));
    document.getElementById('idxDecCamT').textContent = `${planes.length} Depth Planes (z=${minZ} → z=${maxZ})`;
    document.getElementById('idxDecCamP').textContent =
      panMag > 4
        ? `Camera pans ~${panMag}px. Near plane (z=${minZ}) moves ${(zRef/minZ).toFixed(2)}× camera speed; far (z=${maxZ}) moves ${(zRef/maxZ).toFixed(2)}×.`
        : `Minimal camera pan (~${panMag}px). Subject moves across ${planes.length} depth strata.`;

    const nJoints = Object.keys(curWorm.joints || {}).length;
    const keys = (S && S.keys) || curWorm.keys || {};
    const nDrawn = (keys.drawn || [0]).length;
    document.getElementById('idxDecRigT').textContent = `${nDrawn} Drawn Keys · ${nJoints || planes.length} Sub-Worms`;
    document.getElementById('idxDecRigP').textContent =
      `Quick, Draw! seed (f=01) tracked across ${N} SAM masks with ${curWorm.braid_count || 0} braid crossings & ${curWorm.planted_count || 0} planted contacts.`;

    const fr = frames[Math.min(frames.length-1, fi)] || {};
    const fc = fr.c || [0.5, 0.5];
    const vers = ['Multiplane GWP'];
    if(curWorm.is_flagship) vers.push('Flagship 6-Plane');
    if(curWorm.has_sam_shot) vers.push('SAM Cutout');
    if(curWorm.has_redraw_shot) vers.push('Puppet Redraw');
    if(curWorm.has_integrated) vers.push('Integrated 24fps');
    document.getElementById('idxDecLiveT').textContent = `f ${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')} · (${fc[0].toFixed(2)}, ${fc[1].toFixed(2)})`;
    document.getElementById('idxDecLiveP').textContent = `Versions (${vers.length}): ${vers.join(', ')}.`;
  }

  function renderAll(){
    if(!curWorm) return;
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    if(f >= N) f = N - 1;
    if(f < 0) f = 0;
    renderWorm(f);
    renderStage(f);
    scrub.max = Math.max(0, N - 1);
    scrub.value = String(f);
    readout.textContent = `f ${String(f+1).padStart(2,'0')} / ${String(N).padStart(2,'0')}`;
    updateDecoder(f);
  }

  function buildPlanesAndTicks(){
    planesEl.innerHTML = '';
    ticksEl.innerHTML = '';
    if(!curWorm) return;
    const planes = getActivePlanes();
    planes.forEach(p=>{
      if(!(p.id in planeOn)) planeOn[p.id] = true;
      const lab = document.createElement('label');
      if(p.id === 'char') lab.classList.add('subj');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = planeOn[p.id] !== false;
      cb.addEventListener('change', ()=>{
        planeOn[p.id] = cb.checked;
        soloPlaneId = null;
        renderAll();
      });
      const sp = document.createElement('span');
      sp.textContent = `${p.label} · z=${p.z}`;
      lab.appendChild(cb); lab.appendChild(sp);
      planesEl.appendChild(lab);
    });

    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const keys = (S && S.keys) || curWorm.keys || {};
    const drawn = new Set(keys.drawn || [0]);
    for(let i=0;i<N;i++){
      const s = document.createElement('span');
      s.style.left = (N===1 ? 0 : (i/(N-1))*100) + '%';
      if(i===0) s.className = 'line';
      else if(drawn.has(i)) s.className = 'drawn';
      ticksEl.appendChild(s);
    }
  }

  async function loadVariant(worm, variant){
    curVariant = variant;
    [varGwp, varSam, varRedraw, varInt].forEach(b=>{
      b.setAttribute('aria-pressed', b.dataset.idxvar === variant ? 'true' : 'false');
    });
    let relUrl = `shots/${worm.shot_id}/shot.json`;
    if(variant === 'sam' && worm.has_sam_shot) relUrl = `shots/${worm.slug}-sam/shot.json`;
    else if(variant === 'redraw' && worm.has_redraw_shot) relUrl = `shots/${worm.slug}-redraw/shot.json`;
    else if(variant === 'int' && worm.has_integrated) relUrl = `shots/${worm.slug}/integrated/shot.json`;

    if(shotCache.has(relUrl)){
      S = shotCache.get(relUrl);
      onReady(worm);
      return;
    }
    try{
      const res = await fetch(relUrl);
      if(res.ok){
        const data = await res.json();
        if(!data.W && data.canvas){
          data.W = data.canvas.width || 480;
          data.H = data.canvas.height || 360;
          data.fps = data.canvas.fps || 24;
        }
        if(Array.isArray(data.footage)){
          data._imgs = data.footage.map(src=>{
            if(typeof src === 'string' && src.startsWith('data:')){
              const im = new Image();
              im.onload = () => { if(S === data) renderAll(); };
              im.src = src;
              return im;
            }
            return null;
          });
        }
        shotCache.set(relUrl, data);
        if(curWorm === worm && curVariant === variant){ S = data; onReady(worm); }
      }
    }catch(e){}
  }

  function selectShot(idx){
    if(idx < 0 || idx >= WORMS.length) return;
    curIdx = idx;
    curWorm = WORMS[idx];
    S = null;
    f = 0;
    sel.value = String(idx);
    document.getElementById('idxWormLot').textContent = curWorm.lot || 'SM-SHOT';
    document.getElementById('idxWormTitle').textContent = `${curWorm.title || curWorm.slug} — Multiplane Space-Worm Explorer`;
    document.getElementById('idxWormSub').textContent =
      `Prelinger Archives · ${curWorm.source_title}${curWorm.source_year ? ' ('+curWorm.source_year+')' : ''} · ${curWorm.n_frames} frames @ ${curWorm.fps} fps · Switch between 6 Space-Worm Lenses and drag horizontally across the left screen to scrub.`;
    document.getElementById('idxFullWormsLink').href = `pages/worms.html?shot=${encodeURIComponent(curWorm.shot_id)}`;

    varSam.style.display = curWorm.has_sam_shot ? '' : 'none';
    varRedraw.style.display = curWorm.has_redraw_shot ? '' : 'none';
    varInt.style.display = curWorm.has_integrated ? '' : 'none';

    planeOn = {};
    soloPlaneId = null;
    buildPlanesAndTicks();
    renderAll();
    loadVariant(curWorm, 'gwp');
  }

  function onReady(worm){
    const W = (S && S.W) || worm.W || 480;
    const H = (S && S.H) || worm.H || 360;
    const fps = (S && S.fps) || worm.fps || 12;
    document.getElementById('idxLblStageR').textContent = `${W}×${H} · ${fps} fps`;
    buildPlanesAndTicks();
    for(let i=0;i<Math.min(worm.n_frames||1, 8);i++) getFrameImg(worm, i);
    renderAll();
  }

  // Horizontal worm scrubbing on #idxCvWorm
  let isScrubbing = false;
  function scrubFromWorm(e){
    if(!curWorm) return;
    const rect = cvWorm.getBoundingClientRect();
    const clientX = (e.touches && e.touches.length) ? e.touches[0].clientX : e.clientX;
    const xRel = (clientX - rect.left) / Math.max(1, rect.width);
    let padLFrac = 38 / cvWorm.width, padRFrac = 28 / cvWorm.width;
    if(wormMode === 'parallel'){ padLFrac = 0.10; padRFrac = 0.10; }
    else if(wormMode === 'lanes' || wormMode === 'kymo'){ padLFrac = 114 / cvWorm.width; padRFrac = 14 / cvWorm.width; }
    else if(wormMode === 'strobe'){ padLFrac = 14 / cvWorm.width; padRFrac = 14 / cvWorm.width; }
    else if(wormMode === 'anatomy'){ padLFrac = 116 / cvWorm.width; padRFrac = 20 / cvWorm.width; }
    const u = Math.max(0, Math.min(1, (xRel - padLFrac) / Math.max(0.1, 1 - padLFrac - padRFrac)));
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const nf = Math.round(u * Math.max(0, N - 1));
    if(nf !== f){ f = nf; getFrameImg(curWorm, f); renderAll(); }
  }
  cvWorm.addEventListener('pointerdown', (e)=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.innerHTML='&#9654; Play';
    isScrubbing = true; cvWorm.setPointerCapture(e.pointerId); scrubFromWorm(e);
  });
  cvWorm.addEventListener('pointermove', (e)=>{ if(isScrubbing) scrubFromWorm(e); });
  cvWorm.addEventListener('pointerup', ()=>{ isScrubbing = false; });
  cvWorm.addEventListener('pointercancel', ()=>{ isScrubbing = false; });

  document.querySelectorAll('[data-idxwmode]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      wormMode = btn.dataset.idxwmode;
      document.querySelectorAll('[data-idxwmode]').forEach(b=>b.setAttribute('aria-pressed', b===btn?'true':'false'));
      const m = LENS_META[wormMode] || LENS_META.parallel;
      document.getElementById('idxLensTitle').textContent = m.title;
      document.getElementById('idxLensDesc').textContent = m.desc;
      if(parSubSeg) parSubSeg.style.display = (wormMode === 'parallel') ? '' : 'none';
      if(parThemeBtn) parThemeBtn.style.display = (wormMode === 'parallel') ? '' : 'none';
      if(curWorm && (wormMode === 'strobe' || wormMode === 'kymo' || wormMode === 'parallel')){
        const N = curWorm.n_frames || 1;
        for(let i=0;i<N;i+=Math.max(1, Math.floor(N/8))) getFrameImg(curWorm, i);
      }
      renderAll();
    });
  });
  document.querySelectorAll('[data-idxpsub]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      parallelSubMode = btn.dataset.idxpsub;
      document.querySelectorAll('[data-idxpsub]').forEach(b=>b.setAttribute('aria-pressed', b===btn?'true':'false'));
      renderAll();
    });
  });
  if(parThemeBtn){
    parThemeBtn.addEventListener('click', ()=>{
      parallelDark = !parallelDark;
      parThemeBtn.setAttribute('aria-pressed', String(parallelDark));
      renderAll();
    });
  }
  if(mobPipBtn && screensWrap){
    mobPipBtn.addEventListener('click', ()=>{
      mobPipMode = !mobPipMode;
      mobPipBtn.setAttribute('aria-pressed', String(mobPipMode));
      screensWrap.classList.toggle('mob-pip', mobPipMode);
      screensWrap.classList.toggle('mob-split', !mobPipMode);
    });
  }
  const stageScreenCard = document.getElementById('idxStageScreenCard');
  if(stageScreenCard && screensWrap){
    stageScreenCard.addEventListener('click', ()=>{
      if(window.innerWidth <= 860 && mobPipMode){
        mobPipMode = false;
        if(mobPipBtn) mobPipBtn.setAttribute('aria-pressed', 'false');
        screensWrap.classList.remove('mob-pip');
        screensWrap.classList.add('mob-split');
      }
    });
  }
  [varGwp, varSam, varRedraw, varInt].forEach(btn=>{
    btn.addEventListener('click', ()=>{ if(curWorm) loadVariant(curWorm, btn.dataset.idxvar); });
  });
  document.querySelectorAll('[data-idxspeed]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      speedMult = parseFloat(btn.dataset.idxspeed) || 1.0;
      document.querySelectorAll('[data-idxspeed]').forEach(b=>b.setAttribute('aria-pressed', b===btn?'true':'false'));
    });
  });
  document.querySelectorAll('[data-idxview]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      view = btn.dataset.idxview;
      document.querySelectorAll('[data-idxview]').forEach(b=>b.setAttribute('aria-pressed', b===btn?'true':'false'));
      renderAll();
    });
  });
  document.getElementById('idxBoilBtn').addEventListener('click', (e)=>{
    boilOn = !boilOn; e.currentTarget.setAttribute('aria-pressed', String(boilOn)); renderAll();
  });
  document.getElementById('idxCelBtn').addEventListener('click', (e)=>{
    celOn = !celOn; e.currentTarget.setAttribute('aria-pressed', String(celOn)); renderAll();
  });
  playBtn.addEventListener('click', ()=>{
    playing = !playing;
    playBtn.setAttribute('aria-pressed', String(playing));
    playBtn.innerHTML = playing ? '&#9646;&#9646; Pause' : '&#9654; Play';
    if(playing){ lastTick = performance.now(); requestAnimationFrame(loop); }
  });
  document.getElementById('idxStepPrev').addEventListener('click', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.innerHTML='&#9654; Play';
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm ? curWorm.n_frames : 1);
    f = (f - 1 + N) % N; renderAll();
  });
  document.getElementById('idxStepNext').addEventListener('click', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.innerHTML='&#9654; Play';
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm ? curWorm.n_frames : 1);
    f = (f + 1) % N; renderAll();
  });
  scrub.addEventListener('input', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.innerHTML='&#9654; Play';
    f = parseInt(scrub.value, 10) || 0; renderAll();
  });
  document.getElementById('idxPrevShot').addEventListener('click', ()=> selectShot((curIdx - 1 + WORMS.length) % WORMS.length));
  document.getElementById('idxNextShot').addEventListener('click', ()=> selectShot((curIdx + 1) % WORMS.length));
  sel.addEventListener('change', ()=> selectShot(parseInt(sel.value, 10) || 0));

  function loop(now){
    if(!playing || !curWorm) return;
    const fps = ((S && S.fps) || curWorm.fps || 12) * speedMult;
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    if(now - lastTick >= 1000 / Math.max(1, fps)){
      f = (f + 1) % N;
      getFrameImg(curWorm, (f + 1) % N);
      renderAll();
      lastTick = now;
    }
    requestAnimationFrame(loop);
  }

  // Inject warm-paper mini worm badges onto Rack hang-tags (#out .tag)
  function decorateRackCards(){
    if(!WORMS.length) return;
    const byShotId = new Map();
    const bySlug = new Map();
    WORMS.forEach((w, idx)=>{
      byShotId.set(w.shot_id, {w, idx});
      if(!bySlug.has(w.slug)) bySlug.set(w.slug, {w, idx});
    });

    document.querySelectorAll('#out .tag').forEach(card=>{
      if(card.querySelector('.mini-worm-box')) return;
      const href = card.getAttribute('href') || '';
      const mPage = href.match(/pages\/([a-z0-9-]+)\.html/i);
      const mShot = href.match(/shots\/([a-z0-9-]+)\//i);
      const mHash = href.match(/#([a-z0-9-]+)$/i);
      const key = mPage ? mPage[1] : (mShot ? mShot[1] : (mHash ? mHash[1] : ''));

      let match = key ? byShotId.get(key) : null;
      let targetVar = 'gwp';
      if(key && key.endsWith('-sam')) targetVar = 'sam';
      else if(key && key.endsWith('-redraw')) targetVar = 'redraw';
      else if(href.includes('/integrated/')) targetVar = 'int';

      if(!match && key){
        const base = key.replace(/-(gwp|sam|redraw)$/, '');
        match = byShotId.get(base + '-gwp') || bySlug.get(base);
      }
      if(!match){
        const bEl = card.querySelector('.body b');
        const tSlug = bEl ? bEl.textContent.trim().toLowerCase().replace(/\s+/g, '-') : '';
        if(tSlug) match = byShotId.get(tSlug) || bySlug.get(tSlug);
      }
      if(!match) return;

      const {w, idx} = match;
      const box = document.createElement('div');
      box.className = 'mini-worm-box';
      box.title = 'Click to explore & scrub this Space-Worm at the top of the page';
      const nP = (w.depth_worms && w.depth_worms.length) || (w.planes && w.planes.length) || 2;
      box.innerHTML = `
        <canvas width="118" height="32"></canvas>
        <div class="mini-worm-meta">
          <b>${nP} Planes · ${w.n_frames}f</b>
          <span>Explore worm &#8593;</span>
        </div>
      `;
      const cv = box.querySelector('canvas');
      const c = cv.getContext('2d');
      c.fillStyle = '#FBFAF6'; c.fillRect(0,0,118,32);
      const dws = w.depth_worms || [];
      for(let i=dws.length-1;i>=0;i--){
        const dw = dws[i], tr = dw.track || [];
        if(!tr.length) continue;
        c.beginPath();
        for(let ti=0;ti<tr.length;ti++){
          const x = 4 + (tr.length>1 ? (ti/(tr.length-1))*110 : 55);
          const y = 4 + Math.max(0.08, Math.min(0.92, tr[ti][1]))*24;
          if(ti===0) c.moveTo(x,y); else c.lineTo(x,y);
        }
        c.strokeStyle = dw.role==='subject' ? '#EF9F3A' : (dw.color || '#8A6114');
        c.lineWidth = dw.role==='subject' ? 2.5 : 1.3;
        c.globalAlpha = dw.role==='subject' ? 0.95 : 0.45;
        c.stroke();
      }
      c.globalAlpha = 1;
      const nf = (w.frames && w.frames.length) || 1;
      for(const q of [0, Math.floor(nf/2), nf-1]){
        const fr = w.frames && w.frames[q];
        if(!fr || !fr.doodle) continue;
        const xOff = (nf>1 ? (q/(nf-1)) : 0.5) * 90;
        c.strokeStyle = q===0 ? '#8A4A05' : '#161412';
        c.lineWidth = 0.95;
        for(const s of fr.doodle){
          if(!s || s.length<2) continue;
          c.beginPath();
          for(let k=0;k<s.length;k++){
            const px = 3 + xOff + s[k][0]*24, py = 2 + s[k][1]*28;
            if(k===0) c.moveTo(px,py); else c.lineTo(px,py);
          }
          c.stroke();
        }
      }

      box.addEventListener('click', (e)=>{
        e.preventDefault();
        e.stopPropagation();
        selectShot(idx);
        if(targetVar !== 'gwp') loadVariant(w, targetVar);
        document.getElementById('shmWormsHero').scrollIntoView({behavior:'smooth', block:'start'});
      });
      const bodyEl = card.querySelector('.body') || card;
      bodyEl.insertBefore(box, bodyEl.querySelector('.rail') || null);
    });
  }

  const outEl = document.getElementById('out');
  if(outEl) new MutationObserver(()=> decorateRackCards()).observe(outEl, {childList:true, subtree:true});

  fetch('data/worms_108.json')
    .then(r => r.json())
    .then(data => {
      WORMS = data.worms || [];
      sel.innerHTML = '';
      WORMS.forEach((w, i)=>{
        const opt = document.createElement('option');
        opt.value = String(i);
        const nP = (w.depth_worms && w.depth_worms.length) || (w.planes && w.planes.length) || 2;
        const nV = 1 + (w.has_sam_shot?1:0) + (w.has_redraw_shot?1:0) + (w.has_integrated?1:0);
        opt.textContent = `${w.lot ? w.lot + ' · ' : ''}${w.title || w.slug} (${nP} planes · ${nV} ver · ${w.n_frames}f)`;
        sel.appendChild(opt);
      });
      selectShot(0);
      decorateRackCards();
      setTimeout(decorateRackCards, 600);
    })
    .catch(err => console.warn('Worms load err:', err));
})();
</script>
<!-- END SECONDHAND MOTION WORMS STUDIO -->"""


def main():
    with open(SHM_INDEX, "r") as f:
        html = f.read()

    if START_MARKER in html and END_MARKER in html:
        s_idx = html.index(START_MARKER)
        e_idx = html.index(END_MARKER) + len(END_MARKER)
        html = html[:s_idx] + INJECT_BLOCK + html[e_idx:]
    else:
        raise RuntimeError("Could not find injection markers in index.html")

    with open(SHM_INDEX, "w") as f:
        f.write(html)
    print(f"Updated {SHM_INDEX} ({os.path.getsize(SHM_INDEX) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
