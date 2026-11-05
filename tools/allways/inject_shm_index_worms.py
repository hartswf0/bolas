#!/usr/bin/env python3
"""
Inject Secondhand Motion's native-styled Multiplane Space-Worm Explorer (#shmWormsHero)
with the 3D Parallel & Stretched Output Timelines ("Multiplane Multi-Worm") renderer,
6 Interpretation Lenses, Variant Switcher, Slow-Motion Controls, Plain-English
Worm Decoder Grid, Mobile Zero-Scroll PiP/Split UX, custom styled range slider and
scrollbars, zero emoji characters, collision-free labels, and warm-paper mini-worm
Rack badges into /Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/index.html.
"""

import os

SHM_INDEX = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/index.html"

START_MARKER = "<!-- BEGIN SECONDHAND MOTION WORMS STUDIO -->"
END_MARKER   = "<!-- END SECONDHAND MOTION WORMS STUDIO -->"

INJECT_BLOCK = r"""<!-- BEGIN SECONDHAND MOTION WORMS STUDIO -->
<style>
* {
  scrollbar-width: thin;
  scrollbar-color: var(--rule-strong) transparent;
}
*::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
*::-webkit-scrollbar-track {
  background: transparent;
}
*::-webkit-scrollbar-thumb {
  background: var(--rule-strong);
  border-radius: 999px;
}
.worms-stage{
  background:var(--sheet); border:1.5px solid var(--ink); border-radius:10px;
  padding:8px 10px; box-shadow:0 4px 0 var(--rule-strong); margin:0 0 18px;
  display:flex; flex-direction:column; gap:6px;
}
.worms-stage.locked-fullscreen{
  position:fixed; inset:0; width:100vw; height:100dvh; z-index:9999;
  margin:0; border-radius:0; border:0; box-shadow:none; overflow:hidden;
  overscroll-behavior:none;
  padding-left:max(8px, env(safe-area-inset-left, 0px));
  padding-right:max(8px, env(safe-area-inset-right, 0px));
  padding-bottom:max(6px, env(safe-area-inset-bottom, 0px));
}
.worms-stage.locked-fullscreen .w-screens{
  flex:1 1 auto; min-height:0;
}
.worms-stage.locked-fullscreen .w-screen-worm{
  height:100%;
}
.worms-stage.locked-fullscreen .w-screen-worm .w-canvas-wrap{
  aspect-ratio:auto; height:100%;
}
body.worms-no-scroll{
  overflow:hidden !important; position:fixed; inset:0; width:100vw; height:100dvh; overscroll-behavior:none;
}
.worms-head{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding-bottom:6px;border-bottom:1px solid var(--rule);
  overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;
}
.worms-head::-webkit-scrollbar{display:none;width:0;height:0}
.w-scroll-strip{
  display:flex;align-items:center;gap:5px;overflow-x:auto;max-width:100%;
  scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;
}
.w-scroll-strip::-webkit-scrollbar{display:none;width:0;height:0}
.lot-pill{
  font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;
  padding:3px 7px;border-radius:4px;background:var(--tag-soft);color:var(--tag-ink);
  border:1px solid var(--tag);white-space:nowrap;flex-shrink:0;
}
.w-seg{
  display:inline-flex;border:1.5px solid var(--ink);border-radius:5px;overflow:hidden;
  background:var(--card);flex-shrink:0;
}
.w-seg button{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11px;
  padding:3px 8px;border:0;background:transparent;color:var(--ink);cursor:pointer;
  border-right:1px solid var(--rule);white-space:nowrap;line-height:1.2;
}
.w-seg button:last-child{border-right:0}
.w-seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.w-btn{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11px;
  padding:3px 8px;border:1.5px solid var(--ink);border-radius:5px;
  background:var(--card);color:var(--ink);cursor:pointer;text-decoration:none;
  display:inline-flex;align-items:center;gap:4px;white-space:nowrap;flex-shrink:0;line-height:1.2;
}
.w-btn:hover{border-color:var(--tag)}
.w-btn[aria-pressed="true"]{background:var(--tag);color:#161412;border-color:var(--ink)}
.w-btn-stop[aria-pressed="true"]{background:#B8332A;color:#FBFAF6;border-color:var(--ink)}
.w-btn-recover{background:var(--tag-soft);color:var(--tag-ink);border-color:var(--tag)}
.w-select{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11.5px;
  padding:3px 24px 3px 8px;border:1.5px solid var(--ink);border-radius:5px;
  background-color:var(--card);color:var(--ink);cursor:pointer;max-width:290px;
  appearance:none;-webkit-appearance:none;line-height:1.2;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath fill='none' stroke='%23161412' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M1 1L5 5L9 1'/%3E%3C/svg%3E");
  background-repeat:no-repeat;
  background-position:right 7px center;
}
.w-screens{
  position:relative;display:grid;grid-template-columns:1.38fr 1fr;gap:8px;align-items:stretch;
}
.w-screen{
  position:relative;background:var(--cel);border:1.5px solid var(--ink);
  border-radius:6px;overflow:hidden;display:flex;flex-direction:column;
}
.w-pane-bar{
  height:30px;padding:0 6px;background:var(--sheet);border-bottom:1px solid var(--rule);
  display:flex;align-items:center;justify-content:space-between;gap:5px;flex-shrink:0;
  overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;
}
.w-pane-bar::-webkit-scrollbar{display:none;width:0;height:0}
.w-canvas-wrap{
  position:relative;width:100%;aspect-ratio:4/3;background:var(--cel);
  touch-action:none;user-select:none;flex:1;
}
.w-canvas-wrap.worm-scrub-area{cursor:ew-resize;aspect-ratio:16/10.5}
.w-screen canvas{display:block;width:100%;height:100%}
.w-screen .w-lbl{
  position:absolute;bottom:5px;left:6px;
  font-family:'JetBrains Mono',monospace;font-size:9.5px;
  background:rgba(246,239,227,0.92);color:#161412;
  padding:1px 6px;border-radius:3px;border:1px solid var(--rule-strong);
  pointer-events:none;z-index:2;max-width:58%;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.w-screen .w-lbl-r{
  position:absolute;bottom:5px;right:6px;
  font-family:'JetBrains Mono',monospace;font-size:9.5px;
  background:var(--tag-soft);color:var(--tag-ink);
  padding:1px 6px;border-radius:3px;border:1px solid var(--tag);
  pointer-events:none;z-index:2;font-weight:600;white-space:nowrap;
}
.w-mob-pip-btn{display:none}
.w-dock{
  display:flex;flex-direction:column;gap:5px;padding-top:4px;border-top:1px solid var(--rule);
}
.w-planes-row{
  display:flex;align-items:center;justify-content:space-between;gap:6px;
  overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;
}
.w-planes-row::-webkit-scrollbar{display:none;width:0;height:0}
.w-planes{
  display:flex;gap:4px;align-items:center;flex-wrap:nowrap;
  scrollbar-width:none;-ms-overflow-style:none;
}
.w-planes::-webkit-scrollbar{display:none;width:0;height:0}
.w-plane-pill{
  font-family:'JetBrains Mono',monospace;font-size:10px;
  padding:2px 7px;border:1px solid var(--rule-strong);border-radius:4px;
  background:var(--card);color:var(--ink);cursor:pointer;user-select:none;
  display:inline-flex;align-items:center;gap:4px;white-space:nowrap;flex-shrink:0;
}
.w-plane-pill.subj{border-color:var(--tag);background:var(--tag-soft);color:var(--tag-ink);font-weight:600}
.w-plane-pill[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.w-plane-pill.subj[aria-pressed="true"]{background:var(--tag);color:#161412;border-color:var(--ink)}
.w-plane-pill[aria-pressed="false"]{opacity:0.45}
.w-play-lab{
  display:inline-flex;align-items:center;gap:4px;background:var(--card);
  border:1px solid var(--rule-strong);border-radius:4px;padding:1px 6px;
  font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--ink);
  white-space:nowrap;flex-shrink:0;
}
.w-play-lab input[type=range]{
  width:52px;height:12px;margin:0;cursor:pointer;appearance:none;-webkit-appearance:none;background:transparent;
}
.w-play-lab input[type=range]::-webkit-slider-runnable-track{
  height:4px;border-radius:999px;background:var(--rule);border:1px solid var(--ink);
}
.w-play-lab input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;appearance:none;width:10px;height:10px;border-radius:50%;
  background:var(--tag);border:1.5px solid var(--ink);margin-top:-4px;
}
.w-controls{
  display:grid;grid-template-columns:auto auto 1fr auto auto;gap:6px;align-items:center;
}
.w-scrub{position:relative;display:flex;align-items:center;height:22px}
.w-scrub input[type=range]{
  width:100%;cursor:pointer;margin:0;background:transparent;
  appearance:none;-webkit-appearance:none;position:relative;z-index:2;
}
.w-scrub input[type=range]:focus{outline:none}
.w-scrub input[type=range]::-webkit-slider-runnable-track{
  height:6px;border-radius:999px;background:var(--rule);border:1px solid var(--ink);
}
.w-scrub input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;appearance:none;width:15px;height:15px;border-radius:50%;
  background:var(--tag);border:2px solid var(--ink);margin-top:-5.5px;
  box-shadow:0 1px 2px rgba(0,0,0,0.22);
}
.w-scrub input[type=range]::-moz-range-track{
  height:6px;border-radius:999px;background:var(--rule);border:1px solid var(--ink);
}
.w-scrub input[type=range]::-moz-range-thumb{
  width:15px;height:15px;border-radius:50%;background:var(--tag);border:2px solid var(--ink);
  box-shadow:0 1px 2px rgba(0,0,0,0.22);
}
.w-ticks{position:absolute;left:7px;right:7px;top:1px;height:5px;pointer-events:none;z-index:1}
.w-ticks span{position:absolute;top:0;width:1.5px;height:4px;background:var(--rule-strong);transform:translateX(-1px)}
.w-ticks span.drawn{background:var(--ink);height:6px;width:2px}
.w-ticks span.line{background:var(--tag);height:7px;width:2.5px}
.w-readout{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;color:var(--ink);min-width:74px;text-align:right;white-space:nowrap}

/* Mobile Zero-Scroll Operational Layout */
@media (max-width:860px){
  .worms-stage{padding:6px 8px;margin-bottom:12px;gap:5px}
  .w-select{max-width:175px;font-size:11px;padding:2px 20px 2px 6px}
  .w-mob-pip-btn{display:inline-flex}
  .w-screens.mob-pip{
    display:block;position:relative;
  }
  .w-screens.mob-pip .w-screen-worm .w-canvas-wrap{
    aspect-ratio:4/3;
  }
  .w-screens.mob-pip .w-screen-stage{
    position:absolute;right:6px;bottom:6px;width:36%;max-width:156px;
    z-index:6;box-shadow:0 6px 18px rgba(0,0,0,0.48);
    border:2px solid var(--tag);border-radius:6px;
  }
  .w-screens.mob-pip .w-screen-stage .w-pane-bar{display:none}
  .w-screens.mob-pip .w-screen-stage .w-lbl,
  .w-screens.mob-pip .w-screen-stage .w-lbl-r{
    font-size:8px;padding:1px 4px;bottom:3px;
  }
  .w-screens.mob-split{
    display:grid;grid-template-columns:1.18fr 0.82fr;gap:5px;
  }
  .w-controls{
    grid-template-columns:auto auto 1fr auto;gap:4px;
  }
  .w-controls [aria-label="Playback speed"]{display:none}
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
    <div class="w-scroll-strip">
      <span class="lot-pill" id="idxWormLot">SM-0004</span>
      <button type="button" class="w-btn" id="idxPrevShot">Prev</button>
      <select class="w-select" id="idxShotSelect" aria-label="Select shot"></select>
      <button type="button" class="w-btn" id="idxNextShot">Next</button>
      <button type="button" class="w-btn w-btn-recover" id="idxResetBtn" style="display:none">Reset</button>
    </div>
    <div class="w-scroll-strip">
      <button type="button" class="w-btn w-mob-pip-btn" id="idxMobPipBtn" aria-pressed="true">PiP / Split</button>
      <button type="button" class="w-btn" id="idxLockScreenBtn" aria-pressed="false" title="Lock this studio to full 100dvh viewport with zero page scroll">No-Scroll</button>
      <a class="w-btn" id="idxFullWormsLink" href="pages/worms.html">Studio (109)</a>
    </div>
  </div>

  <div class="w-screens mob-pip" id="idxScreensWrap">
    <div class="w-screen w-screen-worm">
      <div class="w-pane-bar">
        <div class="w-scroll-strip">
          <div class="w-seg" role="group" aria-label="Space-Worm Interpretation Lens">
            <button type="button" data-idxwmode="all" aria-pressed="false">All 6</button>
            <button type="button" data-idxwmode="parallel" aria-pressed="true">1 · 3D Butter</button>
            <button type="button" data-idxwmode="lanes" aria-pressed="false">2 · Planes</button>
            <button type="button" data-idxwmode="parts" aria-pressed="false">3 · Parts</button>
            <button type="button" data-idxwmode="strobe" aria-pressed="false">4 · Trail</button>
            <button type="button" data-idxwmode="kymo" aria-pressed="false">5 · Graphs</button>
            <button type="button" data-idxwmode="anatomy" aria-pressed="false">6 · Rig</button>
            <button type="button" data-idxwmode="box" aria-pressed="false">7 · Depth Box</button>
            <button type="button" data-idxwmode="wall" aria-pressed="false">All 109</button>
          </div>
        </div>
        <div class="w-scroll-strip" id="idxParallelTools">
          <div class="w-seg" id="idxParallelSubSeg" role="group" aria-label="Parallel Timeline Sub-mode">
            <button type="button" data-idxpsub="butter" aria-pressed="true">Butter</button>
            <button type="button" data-idxpsub="slices" aria-pressed="false">Slices</button>
            <button type="button" data-idxpsub="radial" aria-pressed="false">Radial</button>
            <button type="button" data-idxpsub="dual" aria-pressed="false">2-Rail</button>
          </div>
          <button type="button" class="w-btn" id="idxParThemeBtn" aria-pressed="true">Dark</button>
        </div>
      </div>
      <div class="w-canvas-wrap worm-scrub-area">
        <canvas id="idxCvWorm" width="680" height="468"></canvas>
        <span class="w-lbl" id="idxLblWorm">parallel output timelines (3D stretch) · drag to scrub</span>
        <span class="w-lbl-r" id="idxLblWormR">6 planes · f 01/33</span>
      </div>
    </div>

    <div class="w-screen w-screen-stage" id="idxStageScreenCard">
      <div class="w-pane-bar">
        <div class="w-scroll-strip">
          <div class="w-seg" role="group" aria-label="Stage view">
            <button type="button" data-idxview="all4" aria-pressed="false">All 4</button>
            <button type="button" data-idxview="composite" aria-pressed="true">Over Footage</button>
            <button type="button" data-idxview="xray" aria-pressed="false">Parts X-Ray</button>
            <button type="button" data-idxview="cutout" aria-pressed="false">SAM Cutout</button>
            <button type="button" data-idxview="cartoon" aria-pressed="false">Cartoon</button>
            <button type="button" data-idxview="footage" aria-pressed="false">Footage</button>
            <button type="button" data-idxview="masks" aria-pressed="false">Masks</button>
          </div>
        </div>
        <div class="w-scroll-strip" id="idxVariantWrap" style="display:none">
          <div class="w-seg" role="group" aria-label="Version">
            <button type="button" id="idxVarGwp" data-idxvar="gwp" aria-pressed="true">GWP</button>
            <button type="button" id="idxVarSam" data-idxvar="sam" aria-pressed="false" style="display:none">SAM</button>
            <button type="button" id="idxVarRedraw" data-idxvar="redraw" aria-pressed="false" style="display:none">Redraw</button>
            <button type="button" id="idxVarInt" data-idxvar="int" aria-pressed="false" style="display:none">24fps</button>
          </div>
        </div>
      </div>
      <div class="w-canvas-wrap">
        <canvas id="idxCvStage" width="480" height="360"></canvas>
        <span class="w-lbl" id="idxLblStage">composite over footage · camera pans with shot</span>
        <span class="w-lbl-r" id="idxLblStageR">480×360 · 12 fps</span>
      </div>
    </div>
  </div>

  <div class="w-dock">
    <div class="w-planes-row">
      <div class="w-planes" id="idxPlanes"></div>
      <div style="display:inline-flex;align-items:center;gap:4px;flex-shrink:0">
        <button type="button" class="w-btn w-btn-recover" id="idxZoomCrumb" style="display:none" title="Zoom out to all planes">&lt;- All Planes</button>
        <label class="w-play-lab" title="Constrained Play: Scale multiplane parallax k = z_ref / z (0x flat to 2.5x hyper-stereo)">
          <span>k</span>
          <input type="range" id="idxKScale" min="0" max="250" value="100" step="10">
          <b id="idxKScaleVal">1.0x</b>
        </label>
        <label class="w-play-lab" title="Constrained Play: Explode depth planes apart vertically to inspect occluded parts">
          <span>Explode</span>
          <input type="range" id="idxExplode" min="0" max="100" value="0" step="5">
          <b id="idxExplodeVal">0%</b>
        </label>
        <button type="button" class="w-btn w-btn-recover" id="idxShowAllPlanes" style="display:none">All Planes</button>
      </div>
    </div>
    <div class="w-controls">
      <button type="button" class="w-btn w-btn-stop" id="idxPlayBtn" aria-pressed="false">Play</button>
      <div style="display:inline-flex;gap:3px">
        <button type="button" class="w-btn" id="idxStepPrev">-1f</button>
        <button type="button" class="w-btn" id="idxStepNext">+1f</button>
      </div>
      <div class="w-scrub">
        <div class="w-ticks" id="idxTicks"></div>
        <input type="range" id="idxScrub" min="0" max="32" value="0" step="1" aria-label="Scrub frame">
      </div>
      <div class="w-seg" role="group" aria-label="Playback speed">
        <button type="button" data-idxspeed="1" aria-pressed="true">1x</button>
        <button type="button" data-idxspeed="0.5" aria-pressed="false">0.5x</button>
        <button type="button" data-idxspeed="0.25" aria-pressed="false">0.25x</button>
      </div>
      <div class="w-readout" id="idxReadout">f 01 / 33</div>
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
  const showAllPlanesBtn = document.getElementById('idxShowAllPlanes');
  const resetBtn = document.getElementById('idxResetBtn');
  const zoomCrumbBtn = document.getElementById('idxZoomCrumb');
  const kScaleRange = document.getElementById('idxKScale');
  const kScaleVal = document.getElementById('idxKScaleVal');
  const explodeRange = document.getElementById('idxExplode');
  const explodeVal = document.getElementById('idxExplodeVal');

  const varWrap = document.getElementById('idxVariantWrap');
  const varGwp = document.getElementById('idxVarGwp');
  const varSam = document.getElementById('idxVarSam');
  const varRedraw = document.getElementById('idxVarRedraw');
  const varInt = document.getElementById('idxVarInt');
  const parTools = document.getElementById('idxParallelTools');
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
  let parallelSubMode = 'butter';
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
  let zoomPlaneId = null;
  let selectedPartId = null;
  let hoveredPartId = null;
  let kScale = 1.0;
  let explodeAmt = 0.0;
  let wormHitBoxes = [];
  let stageHitBoxes = [];
  let hitTransform = {tx: 0, ty: 0, sx: 1, sy: 1};
  let rackMiniWorms = [];

  const PART_PALETTE = [
    '#D97706', '#2E7A4A', '#2B6CB0', '#B8332A',
    '#6B46C1', '#0D9488', '#C05621', '#4338CA',
    '#9D174D', '#15803D', '#1D4ED8', '#A16207'
  ];

  function pushHitBox(b){
    wormHitBoxes.push(Object.assign({}, b, {
      x: hitTransform.tx + b.x * hitTransform.sx,
      y: hitTransform.ty + b.y * hitTransform.sy,
      w: b.w * hitTransform.sx,
      h: b.h * hitTransform.sy
    }));
  }

  const LENS_META = {
    parallel: {
      title: 'Lens 1 · Parallel & Stretched Output Timelines (3D Multi-Worm):',
      desc: 'Parallel output timelines are prepared around the central input spine; distributed keyframes fan out via white correspondence rays (stretched 1/K slower per layer with head fixed) and intersect the circular cross-section ring as upright 3D frame cards.',
      lbl: 'parallel output timelines (3D stretch) · drag to scrub'
    },
    lanes: {
      title: 'Lens 2 · Disentangled Plane Worms:',
      desc: 'One horizontal cel strip per depth plane (Near -> Subject -> Far). Click [+ Parts] on any plane header to drill into its constituent parts.',
      lbl: 'disentangled plane worms · click [+ Parts] to drill in'
    },
    parts: {
      title: 'Lens 3 · Decomposed Part Atlas & Causal Microscope:',
      desc: 'Decomposes the shot into every individual character stroke and scene object (QuickDraw asset, agent drawing, or procedural element). Click any part card to open its Causal Motion Microscope.',
      lbl: 'decomposed shot parts · click any card for causal microscope'
    },
    strobe: {
      title: 'Lens 4 · Space-Time Stroboscopic Trail (Muybridge View):',
      desc: 'Lays the entire space-worm directly over the 4:3 scene: ghost SAM cutouts + ink poses from Start (green) to End (red), connected by the centroid spine, joint curves, and planted-foot anchors.',
      lbl: 'stroboscopic motion trail · drag to scrub'
    },
    kymo: {
      title: 'Lens 5 · Slit-Scan & Motion Graphs (X-T, Y-T & Looming):',
      desc: 'Separates horizontal travel X(t), vertical gait bounce Y(t), and silhouette scale R(t) vs. camera pan so you can read speed, direction, and rhythm at a glance.',
      lbl: 'spatiotemporal graphs X(t), Y(t), R(t) · drag to scrub'
    },
    anatomy: {
      title: 'Lens 6 · Anatomy, Seed Line & Joint Braids:',
      desc: 'Compares The Line (f=0 Quick, Draw! seed doodle) against Frame f’s warped rig + skeleton joints on top, with anatomical joint sub-worms and 2D limb-crossing (braid) markers below.',
      lbl: 'seed line vs warped rig + joint sub-worms · drag to scrub'
    },
    box: {
      title: 'Lens 7 · Planes in Depth (Multiplane Camera Box):',
      desc: 'Secondhand Motion’s receding multiplane cards (z=10 far horizon down to z=1.2 foreground), showing how each plane shifts by k = z_ref / z as the camera pans.',
      lbl: 'multiplane depth box (z) · drag to scrub'
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
    const zNum = Math.max(0.2, Number(planeZ) || zRef);
    const k = (zRef / zNum) * kScale;
    const explodeDy = (Math.log2(zNum / zRef) * -28) * explodeAmt;
    if(S && Array.isArray(S.camera) && S.camera[fi] != null){
      const cam = S.camera[fi];
      const cx = Array.isArray(cam) ? Number(cam[0]) : Number(cam.dx !== undefined ? cam.dx : cam.x);
      const cy = Array.isArray(cam) ? Number(cam[1]) : Number(cam.dy !== undefined ? cam.dy : cam.y);
      return {
        dx: (Number.isFinite(cx) ? cx : 0) * k,
        dy: (Number.isFinite(cy) ? cy : 0) * k + explodeDy
      };
    }
    if(curWorm && curWorm.frames && curWorm.frames[fi]){
      const cam = curWorm.frames[fi].cam || [0,0];
      const W = (S && S.W) || curWorm.W || 480;
      const H = (S && S.H) || curWorm.H || 360;
      const cx = Number(cam[0]) || 0;
      const cy = Number(cam[1]) || 0;
      return {dx: cx * W * k, dy: cy * H * k + explodeDy};
    }
    return {dx:0, dy:explodeDy};
  }

  function getObjectStrokes(o, fi){
    if(!o) return [];
    if(o.frames && Array.isArray(o.frames[fi]) && o.frames[fi].length > 0){
      return o.frames[fi];
    }
    if(Array.isArray(o.strokes) && o.strokes.length > 0){
      return o.strokes;
    }
    if(Array.isArray(o.frames)){
      for(let d = 1; d < o.frames.length; d++){
        if(fi - d >= 0 && Array.isArray(o.frames[fi - d]) && o.frames[fi - d].length > 0) return o.frames[fi - d];
        if(fi + d < o.frames.length && Array.isArray(o.frames[fi + d]) && o.frames[fi + d].length > 0) return o.frames[fi + d];
      }
    }
    return [];
  }

  function computeStrokesBBox(strokes, W, H){
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    let visMinX = Infinity, visMinY = Infinity, visMaxX = -Infinity, visMaxY = -Infinity;
    let nPts = 0;
    const mX = (W || 480) * 0.12, mY = (H || 360) * 0.12;
    for(const s of (strokes || [])){
      for(const p of (s || [])){
        const x = Number(p[0]), y = Number(p[1]);
        if(!Number.isFinite(x) || !Number.isFinite(y)) continue;
        nPts++;
        if(x < minX) minX = x; if(y < minY) minY = y;
        if(x > maxX) maxX = x; if(y > maxY) maxY = y;
        if(x >= -mX && x <= (W || 480) + mX && y >= -mY && y <= (H || 360) + mY){
          if(x < visMinX) visMinX = x; if(y < visMinY) visMinY = y;
          if(x > visMaxX) visMaxX = x; if(y > visMaxY) visMaxY = y;
        }
      }
    }
    if(visMinX < visMaxX && visMinY < visMaxY){
      minX = visMinX; minY = visMinY; maxX = visMaxX; maxY = visMaxY;
    }
    if(!Number.isFinite(minX) || minX > maxX){
      return {x0: 0, y0: 0, x1: W || 480, y1: H || 360, cx: (W || 480)*0.5, cy: (H || 360)*0.5, w: W || 480, h: H || 360, nPts: 0};
    }
    return {
      x0: minX, y0: minY, x1: maxX, y1: maxY,
      cx: (minX + maxX) * 0.5, cy: (minY + maxY) * 0.5,
      w: Math.max(8, maxX - minX), h: Math.max(8, maxY - minY),
      nPts
    };
  }

  function extractShotParts(fi, filterPlaneId){
    const W = (S && S.W) || (curWorm && curWorm.W) || 480;
    const H = (S && S.H) || (curWorm && curWorm.H) || 360;
    const zRef = (S && S.z_ref) || (curWorm && curWorm.z_ref) || 2;
    const planes = getActivePlanes();
    const parts = [];
    let colorIdx = 0;

    for(const plane of planes){
      if(filterPlaneId && plane.id !== filterPlaneId) continue;
      const off = camOffset(plane.z, fi);
      const off0 = camOffset(plane.z, 0);
      const kMult = (zRef / Math.max(0.2, plane.z)) * kScale;

      if(plane.id === 'char'){
        const charFrames = (S && S.cast && Array.isArray(S.cast.frames)) ? S.cast.frames : null;
        const strokesFi = (charFrames && charFrames[fi]) ? charFrames[fi] :
          ((curWorm && curWorm.frames && curWorm.frames[fi] && curWorm.frames[fi].doodle)
            ? curWorm.frames[fi].doodle.map(s => s.map(p => [p[0]*W, p[1]*H])) : []);
        const strokes0 = (charFrames && charFrames[0]) ? charFrames[0] :
          ((curWorm && curWorm.frames && curWorm.frames[0] && curWorm.frames[0].doodle)
            ? curWorm.frames[0].doodle.map(s => s.map(p => [p[0]*W, p[1]*H])) : strokesFi);

        const bbFi = computeStrokesBBox(strokesFi, W, H);
        const bb0  = computeStrokesBBox(strokes0, W, H);
        const rigDx = bbFi.cx - bb0.cx;
        const rigDy = bbFi.cy - bb0.cy;
        const camDx = off.dx - off0.dx;
        const camDy = off.dy - off0.dy;

        parts.push({
          id: 'char:whole',
          label: (S && S.cast && S.cast.label) || plane.label || 'Subject Rig',
          shortLabel: 'Subject Rig',
          planeId: 'char',
          planeLabel: plane.label || 'Subject',
          planeZ: plane.z,
          kMult,
          kind: 'char_whole',
          sourceTag: 'SAM+RIG',
          sourceFull: (S && S.cast && S.cast.source) || 'QuickDraw seed + SAM warp',
          color: '#D97706',
          strokes: strokesFi,
          strokes0,
          off,
          bbox: bbFi,
          bbox0: bb0,
          nStrokes: strokesFi.length,
          nPts: bbFi.nPts,
          camDisp: {dx: camDx, dy: camDy},
          rigDisp: {dx: rigDx, dy: rigDy},
          totalDisp: {dx: camDx + rigDx, dy: camDy + rigDy},
          isAnimated: true
        });

        strokesFi.forEach((s, sIdx)=>{
          if(!s || s.length < 2) return;
          const s0 = (strokes0 && strokes0[sIdx]) ? strokes0[sIdx] : s;
          const sbbFi = computeStrokesBBox([s], W, H);
          const sbb0  = computeStrokesBBox([s0], W, H);
          const sRigDx = sbbFi.cx - sbb0.cx;
          const sRigDy = sbbFi.cy - sbb0.cy;
          const col = PART_PALETTE[(colorIdx++) % PART_PALETTE.length];
          parts.push({
            id: `char:s${sIdx}`,
            label: `Char Stroke #${sIdx+1}`,
            shortLabel: `Stroke S${sIdx+1}`,
            planeId: 'char',
            planeLabel: plane.label || 'Subject',
            planeZ: plane.z,
            kMult,
            kind: 'char_stroke',
            sourceTag: 'RIG-STROKE',
            sourceFull: `Subject pen stroke ${sIdx+1} of ${strokesFi.length} (${s.length} pts)`,
            color: col,
            strokes: [s],
            strokes0: [s0],
            off,
            bbox: sbbFi,
            bbox0: sbb0,
            nStrokes: 1,
            nPts: s.length,
            camDisp: {dx: camDx, dy: camDy},
            rigDisp: {dx: sRigDx, dy: sRigDy},
            totalDisp: {dx: camDx + sRigDx, dy: camDy + sRigDy},
            isAnimated: true
          });
        });
      } else if(S && Array.isArray(S.objects)){
        const objs = S.objects.filter(o => o.plane === plane.id);
        for(const o of objs){
          const ost = getObjectStrokes(o, fi);
          if(!ost || !ost.length) continue;
          const ost0 = getObjectStrokes(o, 0);
          const bbFi = computeStrokesBBox(ost, W, H);
          const bb0  = computeStrokesBBox(ost0, W, H);
          const hasAnimFrames = Boolean(o.frames && Array.isArray(o.frames) && o.frames.some(fr => Array.isArray(fr) && fr.length > 0));
          const rigDx = hasAnimFrames ? (bbFi.cx - bb0.cx) : 0;
          const rigDy = hasAnimFrames ? (bbFi.cy - bb0.cy) : 0;
          const camDx = off.dx - off0.dx;
          const camDy = off.dy - off0.dy;

          const rawSrc = String(o.source || o.class || 'scene');
          let srcTag = 'SCENE';
          if(rawSrc.startsWith('quickdraw:')) srcTag = 'QD';
          else if(rawSrc.includes('agent')) srcTag = 'AGENT';
          else if(rawSrc.includes('procedural')) srcTag = 'PROC';

          const col = PART_PALETTE[(colorIdx++) % PART_PALETTE.length];
          const niceId = String(o.id || o.class || 'obj').replace(/_/g, ' ');
          parts.push({
            id: `obj:${o.id}`,
            label: `${niceId} (${o.class || plane.id})`,
            shortLabel: String(o.id || o.class || 'part').slice(0, 12),
            planeId: plane.id,
            planeLabel: plane.label || plane.id,
            planeZ: Number(o.z) || plane.z,
            kMult,
            kind: 'object',
            sourceTag: srcTag,
            sourceFull: rawSrc,
            color: col,
            strokes: ost,
            strokes0: ost0,
            off,
            bbox: bbFi,
            bbox0: bb0,
            nStrokes: ost.length,
            nPts: bbFi.nPts,
            camDisp: {dx: camDx, dy: camDy},
            rigDisp: {dx: rigDx, dy: rigDy},
            totalDisp: {dx: camDx + rigDx, dy: camDy + rigDy},
            isAnimated: hasAnimFrames
          });
        }
      } else if(curWorm && Array.isArray(curWorm.depth_worms)){
        const dwObj = curWorm.depth_worms.find(d => d.id === plane.id);
        if(dwObj && Array.isArray(dwObj.strokes0) && dwObj.strokes0.length){
          const u0 = Number.isFinite(dwObj.u0) ? dwObj.u0 : 0.5;
          const v0 = Number.isFinite(dwObj.v0) ? dwObj.v0 : 0.5;
          const mapped = dwObj.strokes0.map(s => s.map(p => [(u0 + p[0])*W, (v0 + p[1])*H]));
          const bb = computeStrokesBBox(mapped, W, H);
          const col = PART_PALETTE[(colorIdx++) % PART_PALETTE.length];
          parts.push({
            id: `dw:${plane.id}`,
            label: `${plane.label || plane.id}`,
            shortLabel: String(plane.label || plane.id).slice(0, 12),
            planeId: plane.id,
            planeLabel: plane.label || plane.id,
            planeZ: plane.z,
            kMult,
            kind: 'dw_fallback',
            sourceTag: 'PLANE',
            sourceFull: 'Depth-worm strokes0',
            color: col,
            strokes: mapped,
            strokes0: mapped,
            off,
            bbox: bb,
            bbox0: bb,
            nStrokes: mapped.length,
            nPts: bb.nPts,
            camDisp: {dx: off.dx - off0.dx, dy: off.dy - off0.dy},
            rigDisp: {dx: 0, dy: 0},
            totalDisp: {dx: off.dx - off0.dx, dy: off.dy - off0.dy},
            isAnimated: false
          });
        }
      }
    }
    return parts;
  }

  function drawPartInRect(ctx, part, fi, tx, ty, tw, th, opts){
    const o = Object.assign({cropToPart: true, showGhost0: false, color: null, width: 2.0}, opts || {});
    const W = (S && S.W) || (curWorm && curWorm.W) || 480;
    const H = (S && S.H) || (curWorm && curWorm.H) || 360;
    const off = camOffset(part.planeZ, fi);

    let strokes = part.strokes || [];
    if(part.kind === 'char_whole'){
      const cf = (S && S.cast && S.cast.frames && S.cast.frames[fi]) ? S.cast.frames[fi] : null;
      if(cf) strokes = cf;
    } else if(part.kind === 'char_stroke'){
      const sIdx = parseInt(part.id.split(':s')[1], 10) || 0;
      const cf = (S && S.cast && S.cast.frames && S.cast.frames[fi]) ? S.cast.frames[fi] : null;
      if(cf && cf[sIdx]) strokes = [cf[sIdx]];
    } else if(part.kind === 'object' && S && Array.isArray(S.objects)){
      const objId = part.id.replace(/^obj:/, '');
      const found = S.objects.find(ob => ob.id === objId);
      if(found) strokes = getObjectStrokes(found, fi);
    }

    const shifted = strokes.map(s => (s || []).map(p => [p[0] + off.dx, p[1] + off.dy]));
    const bb = computeStrokesBBox(shifted, W, H);
    let minX = o.cropToPart ? bb.x0 : 0;
    let minY = o.cropToPart ? bb.y0 : 0;
    let maxX = o.cropToPart ? bb.x1 : W;
    let maxY = o.cropToPart ? bb.y1 : H;

    if(o.cropToPart){
      const padX = Math.max(10, (maxX - minX) * 0.18);
      const padY = Math.max(10, (maxY - minY) * 0.18);
      minX -= padX; minY -= padY; maxX += padX; maxY += padY;
    }

    const srcW = Math.max(14, maxX - minX);
    const srcH = Math.max(14, maxY - minY);
    const scale = Math.min(Math.max(4, tw - 4) / srcW, Math.max(4, th - 4) / srcH);
    const dw = srcW * scale, dh = srcH * scale;
    const ox = tx + (tw - dw) * 0.5, oy = ty + (th - dh) * 0.5;

    ctx.save();
    ctx.beginPath();
    ctx.rect(tx, ty, tw, th);
    ctx.clip();

    const img = getFrameImg(curWorm, fi);
    if(img && o.cropToPart){
      ctx.save();
      ctx.globalAlpha = 0.20;
      const clX = Math.max(0, Math.min(W - 12, minX));
      const clY = Math.max(0, Math.min(H - 12, minY));
      const clW = Math.max(12, Math.min(W - clX, srcW));
      const clH = Math.max(12, Math.min(H - clY, srcH));
      ctx.drawImage(img, clX, clY, clW, clH, ox, oy, dw, dh);
      ctx.restore();
    }

    if(o.showGhost0 && part.strokes0 && part.strokes0.length){
      const off0 = camOffset(part.planeZ, 0);
      ctx.strokeStyle = 'rgba(46, 122, 74, 0.45)';
      ctx.lineWidth = Math.max(1.0, o.width * 0.75);
      ctx.setLineDash([2, 2]);
      for(const s of part.strokes0){
        if(!s || s.length < 2) continue;
        ctx.beginPath();
        for(let i = 0; i < s.length; i++){
          const px = ox + (s[i][0] + off0.dx - minX) * scale;
          const py = oy + (s[i][1] + off0.dy - minY) * scale;
          if(i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = 'rgba(251, 250, 246, 0.92)';
    ctx.lineWidth = o.width + 2.2;
    for(const s of shifted){
      if(!s || s.length < 2) continue;
      ctx.beginPath();
      for(let i = 0; i < s.length; i++){
        const px = ox + (s[i][0] - minX) * scale;
        const py = oy + (s[i][1] - minY) * scale;
        if(i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }

    ctx.strokeStyle = o.color || part.color || '#161412';
    ctx.lineWidth = o.width;
    for(const s of shifted){
      if(!s || s.length < 2) continue;
      ctx.beginPath();
      for(let i = 0; i < s.length; i++){
        const px = ox + (s[i][0] - minX) * scale;
        const py = oy + (s[i][1] - minY) * scale;
        if(i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }
    ctx.restore();
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
    const zRef = (S && S.z_ref) || curWorm.z_ref || 2;
    const objs = (S && Array.isArray(S.objects)) ? S.objects.filter(o => o.plane === plane.id) : [];
    const off = camOffset(plane.z, fi);
    const t = tintForPlane(plane.id, plane.z, zRef);

    if(cropToPlane){
      ctx.save();
      ctx.fillStyle = t.fill;
      ctx.globalAlpha = 0.35;
      ctx.fillRect(tx, ty, tw, th);
      ctx.restore();
    }

    const allStrokes = [];
    for(const o of objs){
      const ost = getObjectStrokes(o, fi);
      if(ost && ost.length){
        for(const s of ost){
          if(s && s.length>=2) allStrokes.push(s.map(p => [p[0]+off.dx, p[1]+off.dy]));
        }
      }
    }

    if(allStrokes.length === 0 && curWorm && Array.isArray(curWorm.depth_worms)){
      const dwObj = curWorm.depth_worms.find(d => d.id === plane.id);
      if(dwObj && Array.isArray(dwObj.strokes0) && dwObj.strokes0.length){
        const u0 = Number.isFinite(dwObj.u0) ? dwObj.u0 : 0.5;
        const v0 = Number.isFinite(dwObj.v0) ? dwObj.v0 : 0.5;
        for(const s of dwObj.strokes0){
          if(s && s.length >= 2){
            allStrokes.push(s.map(p => [(u0 + p[0])*W + off.dx, (v0 + p[1])*H + off.dy]));
          }
        }
      }
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    let visMinX = Infinity, visMinY = Infinity, visMaxX = -Infinity, visMaxY = -Infinity;
    const marginX = W * 0.08, marginY = H * 0.08;
    for(const s of allStrokes){
      for(const p of s){
        const x = p[0], y = p[1];
        if(!Number.isFinite(x) || !Number.isFinite(y)) continue;
        if(x < minX) minX = x; if(y < minY) minY = y;
        if(x > maxX) maxX = x; if(y > maxY) maxY = y;
        if(x >= -marginX && x <= W + marginX && y >= -marginY && y <= H + marginY){
          if(x < visMinX) visMinX = x; if(y < visMinY) visMinY = y;
          if(x > visMaxX) visMaxX = x; if(y > visMaxY) visMaxY = y;
        }
      }
    }

    if(visMinX < visMaxX && visMinY < visMaxY){
      minX = visMinX; minY = visMinY; maxX = visMaxX; maxY = visMaxY;
    }

    if(!cropToPlane || minX >= maxX || minY >= maxY || !Number.isFinite(minX)){
      minX = 0; minY = 0; maxX = W; maxY = H;
    } else {
      const padX = Math.max(8, (maxX-minX)*0.10), padY = Math.max(6, (maxY-minY)*0.14);
      minX -= padX; minY -= padY;
      maxX += padX; maxY += padY;
    }

    const srcW = Math.max(16, maxX-minX), srcH = Math.max(12, maxY-minY);
    const rawScaleX = Math.max(4, tw - 4) / srcW;
    const rawScaleY = Math.max(4, th - 4) / srcH;
    const scaleX = cropToPlane ? rawScaleX : Math.min(rawScaleX, rawScaleY);
    const scaleY = cropToPlane
      ? Math.min(rawScaleY, Math.max(rawScaleX, rawScaleY * 0.80))
      : Math.min(rawScaleX, rawScaleY);
    const dw = srcW*scaleX, dh = srcH*scaleY;
    const ox = tx + (tw-dw)*0.5, oy = ty + (th-dh)*0.5;

    const img = getFrameImg(curWorm, fi);
    if(cropToPlane && img){
      ctx.save();
      ctx.globalAlpha = allStrokes.length ? 0.24 : 0.65;
      const clX = Math.max(0, Math.min(W - 16, minX));
      const clY = Math.max(0, Math.min(H - 16, minY));
      const clW = Math.max(16, Math.min(W - clX, srcW));
      const clH = Math.max(16, Math.min(H - clY, srcH));
      ctx.drawImage(img, clX, clY, clW, clH, tx, ty, tw, th);
      ctx.restore();
    }

    if(allStrokes.length){
      ctx.save();
      ctx.beginPath();
      ctx.rect(tx, ty, tw, th);
      ctx.clip();
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.strokeStyle = 'rgba(251, 250, 246, 0.90)';
      ctx.lineWidth = 3.2;
      for(const s of allStrokes){
        ctx.beginPath();
        for(let i=0;i<s.length;i++){
          const px = ox + (s[i][0]-minX)*scaleX, py = oy + (s[i][1]-minY)*scaleY;
          if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
        }
        ctx.stroke();
      }
      ctx.strokeStyle = '#161412';
      ctx.lineWidth = cropToPlane ? 1.65 : 1.45;
      for(const s of allStrokes){
        ctx.beginPath();
        for(let i=0;i<s.length;i++){
          const px = ox + (s[i][0]-minX)*scaleX, py = oy + (s[i][1]-minY)*scaleY;
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
      skewY: -0.16,
      skewX: -0.09,
      butterSlab: true,
      slabDepth: 5.5,
      noHit: false,
      togglePlane: false
    }, opts || {});

    if(!o.noHit){
      pushHitBox({
        x: cx - cw * 0.56,
        y: cy - ch * 0.56,
        w: cw * 1.12,
        h: ch * 1.12,
        fi: fi,
        planeId: (o.plane && o.plane.id) ? o.plane.id : null,
        togglePlane: Boolean(o.togglePlane)
      });
    }

    ctx.save();
    ctx.globalAlpha = o.alpha;
    ctx.translate(cx, cy);
    ctx.transform(1, o.skewY, o.skewX, 1, 0, 0);

    const x0 = -cw * 0.5;
    const y0 = -ch * 0.5;

    ctx.fillStyle = 'rgba(0,0,0,0.40)';
    ctx.fillRect(x0 + 3, y0 + 4, cw + (o.butterSlab ? o.slabDepth : 0), ch + (o.butterSlab ? o.slabDepth * 0.65 : 0));

    if(o.butterSlab && o.slabDepth > 0){
      const sd = o.slabDepth;
      const sy = sd * 0.62;
      ctx.fillStyle = '#E5BE62';
      ctx.beginPath();
      ctx.moveTo(x0 + cw, y0);
      ctx.lineTo(x0 + cw + sd, y0 + sy);
      ctx.lineTo(x0 + cw + sd, y0 + ch + sy);
      ctx.lineTo(x0 + cw, y0 + ch);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = '#C4942D';
      ctx.beginPath();
      ctx.moveTo(x0, y0 + ch);
      ctx.lineTo(x0 + cw, y0 + ch);
      ctx.lineTo(x0 + cw + sd, y0 + ch + sy);
      ctx.lineTo(x0 + sd, y0 + ch + sy);
      ctx.closePath();
      ctx.fill();
    }

    ctx.fillStyle = o.bgFill;
    ctx.fillRect(x0, y0, cw, ch);

    const footerH = o.label ? 14 : 0;
    const contentH = ch - footerH;

    ctx.save();
    ctx.beginPath();
    ctx.rect(x0 + 1.5, y0 + 1.5, cw - 3, Math.max(10, contentH - 2));
    ctx.clip();

    const img = getFrameImg(curWorm, fi);
    if(o.plane && o.plane.id !== 'char'){
      if(img){
        ctx.save();
        ctx.globalAlpha = 0.22;
        ctx.drawImage(img, x0 + 1.5, y0 + 1.5, cw - 3, contentH - 2);
        ctx.restore();
      }
      drawPlaneObjectsInRect(ctx, o.plane, fi, x0 + 2, y0 + 2, cw - 4, contentH - 4, true);
    } else {
      if(img && !o.cropToMask){
        ctx.save();
        ctx.globalAlpha = 0.38;
        ctx.drawImage(img, x0 + 1.5, y0 + 1.5, cw - 3, contentH - 2);
        ctx.restore();
      }
      drawSamCutoutInRect(ctx, curWorm, fi, x0 + 2, y0 + 2, cw - 4, contentH - 4, {
        cropToMask: o.cropToMask,
        drawOutline: true,
        outlineColor: o.borderColor === '#FFFFFF' ? '#EF9F3A' : o.borderColor,
        drawDoodle: true,
        doodleColor: '#161412'
      });
    }
    ctx.restore();

    if(o.label){
      ctx.save();
      ctx.beginPath();
      ctx.rect(x0 + 1, y0 + ch - footerH, cw - 2, footerH - 1);
      ctx.clip();
      ctx.fillStyle = 'rgba(12, 13, 18, 0.90)';
      ctx.fillRect(x0 + 1, y0 + ch - footerH, cw - 2, footerH - 1);
      ctx.fillStyle = o.labelColor;
      ctx.font = '700 8.5px "JetBrains Mono", monospace';
      ctx.fillText(o.label, x0 + 4, y0 + ch - 4);
      ctx.restore();
    }

    ctx.strokeStyle = o.borderColor;
    ctx.lineWidth = o.borderWidth;
    ctx.strokeRect(x0, y0, cw, ch);

    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#161412';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(0, 0, 2.4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function renderParallelTimelinesMode(ctx, W, H, fi, N, planes, zRef){
    const dark = parallelDark;
    if(dark){
      const bg = ctx.createRadialGradient(W*0.42, H*0.46, 20, W*0.5, H*0.5, W*0.75);
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

    const keys = (S && S.keys) || curWorm.keys || {};
    const drawnArr = (keys.drawn && keys.drawn.length >= 2)
      ? keys.drawn.slice()
      : [0, Math.floor(N*0.25), Math.floor(N*0.5), Math.floor(N*0.75), Math.max(0, N-1)];
    const drawnSet = new Set(drawnArr);
    const lineRGB = dark ? '255,255,255' : '22,20,18';

    // Sub-mode: SLICES (All N Slices flat contact sheet — shows ALL active depth planes + subject at each frame)
    if(parallelSubMode === 'slices'){
      const pad = 10, padBot = 28;
      const availW = W - pad * 2;
      const availH = H - pad - padBot;
      const aspect = availW / Math.max(1, availH);
      const cols = Math.max(4, Math.min(9, Math.ceil(Math.sqrt(N * aspect * 0.85))));
      const rows = Math.max(1, Math.ceil(N / cols));
      const gap = 5;
      const cellW = Math.floor((availW - gap * (cols - 1)) / cols);
      const cellH = Math.floor((availH - gap * (rows - 1)) / rows);

      for(let ti = 0; ti < N; ti++){
        const c = ti % cols;
        const r = Math.floor(ti / cols);
        const x = pad + c * (cellW + gap);
        const y = pad + r * (cellH + gap);
        const isCur = (ti === fi);
        const isKey = (ti === 0 || drawnSet.has(ti));

        ctx.fillStyle = isCur ? '#EF9F3A' : '#C4942D';
        ctx.fillRect(x + 2.5, y + 2.5, cellW, cellH);

        ctx.fillStyle = isCur ? '#FFFDF4' : '#FBFAF6';
        ctx.fillRect(x, y, cellW, cellH);

        const footH = 13;
        const bodyH = Math.max(12, cellH - footH);
        const img = getFrameImg(curWorm, ti);
        ctx.save();
        ctx.beginPath();
        ctx.rect(x + 1, y + 1, cellW - 2, bodyH - 1);
        ctx.clip();
        if(img){
          ctx.globalAlpha = isCur ? 0.42 : 0.25;
          ctx.drawImage(img, x + 1, y + 1, cellW - 2, bodyH - 1);
          ctx.globalAlpha = 1;
        }
        for(const p of planes){
          if(p.id !== 'char' && isPlaneVisible(p.id)){
            drawPlaneObjectsInRect(ctx, p, ti, x + 2, y + 2, cellW - 4, bodyH - 3, false);
          }
        }
        drawSamCutoutInRect(ctx, curWorm, ti, x + 2, y + 2, cellW - 4, bodyH - 3, {
          cropToMask: true,
          drawOutline: true,
          outlineColor: isCur ? '#EF9F3A' : (isKey ? '#2E7A4A' : '#8A6114'),
          drawDoodle: true,
          doodleColor: '#161412'
        });
        ctx.restore();

        ctx.fillStyle = isCur ? '#EF9F3A' : 'rgba(18,16,14,0.88)';
        ctx.fillRect(x + 1, y + cellH - footH, cellW - 2, footH - 1);
        ctx.fillStyle = isCur ? '#161412' : (isKey ? '#FBE6C8' : '#FFFFFF');
        ctx.font = '700 8.5px "JetBrains Mono", monospace';
        const tag = `f${String(ti+1).padStart(2,'0')}${ti===0?' SEED':(isKey?' KEY':'')}`;
        ctx.fillText(tag, x + 4, y + cellH - 3.5);

        ctx.strokeStyle = isCur ? '#EF9F3A' : (isKey ? '#F5C469' : 'rgba(255,255,255,0.55)');
        ctx.lineWidth = isCur ? 2.4 : 1.1;
        ctx.strokeRect(x, y, cellW, cellH);

        pushHitBox({x, y, w: cellW, h: cellH, fi: ti, planeId: null, togglePlane: false});
      }
      return;
    }

    const topSafe = 16;
    const botSafe = 28;

    const vx = W * 0.06, vy = H * 0.22;
    const fx = W * 0.90, fy = H * 0.74;

    function spinePt(u){
      const p = Math.pow(Math.max(0, Math.min(1, u)), 0.92);
      return {
        x: vx + p * (fx - vx),
        y: vy + p * (fy - vy),
        s: 0.52 + p * 0.64
      };
    }

    // Sub-mode: BUTTER (All parallel depth rails × All time slices simultaneously, parting open at fi)
    if(parallelSubMode === 'butter'){
      const visPlanes = planes.filter(p => isPlaneVisible(p.id));
      const activeList = visPlanes.length ? visPlanes : planes;
      const K = Math.max(1, activeList.length);
      const RAIL_COLORS = ['#EF9F3A', '#FF453A', '#32D74B', '#409CFF', '#BF5AF2', '#FFD60A', '#64D2FF'];

      const maxSlices = Math.min(N, K > 2 ? 12 : 16);
      const sliceSet = new Set([0, N - 1, fi]);
      drawnArr.forEach(k => { if(k >= 0 && k < N) sliceSet.add(k); });
      for(let s = 0; s < maxSlices; s++){
        const ti = maxSlices === 1 ? 0 : Math.round((s / (maxSlices - 1)) * (N - 1));
        sliceSet.add(ti);
      }
      const sliceFrames = Array.from(sliceSet).sort((a, b) => a - b);

      function butterRailPt(rIdx, u){
        const c = spinePt(u);
        const plane = activeList[rIdx];
        if(plane.id === 'char' || K === 1) return {x: c.x, y: c.y, s: c.s};
        const laneNorm = (rIdx / Math.max(1, K - 1)) - 0.5;
        const spreadX = laneNorm * 225 * Math.max(0.65, c.s);
        const spreadY = -laneNorm * 135 * Math.max(0.65, c.s);
        return {
          x: Math.max(38, Math.min(W - 38, c.x + spreadX)),
          y: Math.max(topSafe + 24, Math.min(H - botSafe - 24, c.y + spreadY)),
          s: c.s
        };
      }

      for(let rIdx = 0; rIdx < K; rIdx++){
        const plane = activeList[rIdx];
        const isSubj = (plane.id === 'char');
        const col = isSubj ? '#EF9F3A' : RAIL_COLORS[rIdx % RAIL_COLORS.length];
        const p0 = butterRailPt(rIdx, 0.03), p1 = butterRailPt(rIdx, 0.97);
        ctx.strokeStyle = col;
        ctx.lineWidth = isSubj ? 2.2 : 1.4;
        ctx.globalAlpha = isSubj ? 0.85 : 0.55;
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p1.x, p1.y);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      const allSliceDrawList = [];
      let activeSpinePt = spinePt(0.5);

      for(const ti of sliceFrames){
        const rawU = N > 1 ? (ti / (N - 1)) : 0.5;
        let partShift = 0;
        if(ti < fi) partShift = -0.05;
        else if(ti > fi) partShift = 0.05;
        const u = Math.max(0.03, Math.min(0.97, 0.07 + rawU * 0.84 + partShift));
        const sp = spinePt(u);
        if(ti === fi) activeSpinePt = sp;

        ctx.strokeStyle = (ti === fi) ? '#FFFFFF' : `rgba(${lineRGB}, 0.24)`;
        ctx.lineWidth = (ti === fi) ? 1.8 : 0.8;
        for(let rIdx = 0; rIdx < K; rIdx++){
          const rp = butterRailPt(rIdx, u);
          ctx.beginPath();
          ctx.moveTo(sp.x, sp.y);
          ctx.lineTo(rp.x, rp.y);
          ctx.stroke();

          const plane = activeList[rIdx];
          const isSubj = (plane.id === 'char');
          const col = isSubj ? '#EF9F3A' : RAIL_COLORS[rIdx % RAIL_COLORS.length];
          const kSpeed = zRef / Math.max(0.3, plane.z);
          const fPlane = isSubj ? ti : Math.max(0, Math.min(N - 1, Math.round(ti * Math.min(1.2, Math.max(0.35, kSpeed)))));
          allSliceDrawList.push({
            ti, fPlane, u, rIdx, plane, isSubj, col,
            x: rp.x, y: rp.y, s: rp.s,
            isActive: (ti === fi)
          });
        }
      }

      ctx.save();
      ctx.strokeStyle = '#EF9F3A';
      ctx.lineWidth = 1.6;
      ctx.setLineDash([5, 3]);
      ctx.beginPath();
      ctx.ellipse(activeSpinePt.x, activeSpinePt.y, 128, 86, -0.14, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      allSliceDrawList.sort((a, b) => (a.isActive - b.isActive) || (a.u - b.u) || (a.y - b.y));
      for(const item of allSliceDrawList){
        const isKey = (item.ti === 0 || drawnSet.has(item.ti));
        const baseW = item.isActive ? (item.isSubj ? 92 : 68) : (item.isSubj ? 60 : 44);
        const baseH = item.isActive ? (item.isSubj ? 76 : 56) : (item.isSubj ? 50 : 36);
        const cw = Math.round(baseW * (item.isActive ? 1.0 : Math.max(0.66, item.s * 0.92)));
        const ch = Math.round(baseH * (item.isActive ? 1.0 : Math.max(0.66, item.s * 0.92)));
        const shortLbl = String(item.plane.label || item.plane.id).split('(')[0].trim().slice(0, 8);
        drawUpright3DCard(ctx, item.x, item.y, cw, ch, item.fPlane, {
          plane: item.isSubj ? null : item.plane,
          borderColor: item.isActive ? '#FFFFFF' : (isKey ? '#F5C469' : item.col),
          borderWidth: item.isActive ? 2.4 : (isKey ? 1.6 : 1.1),
          bgFill: '#FFFDF5',
          alpha: item.isActive ? 1.0 : 0.86,
          cropToMask: item.isSubj,
          butterSlab: true,
          slabDepth: item.isActive ? 7 : Math.max(3, 4.5 * item.s),
          togglePlane: false,
          label: item.isActive ? `${shortLbl} f${String(item.ti+1).padStart(2,'0')}` : (item.isSubj ? `f${String(item.ti+1).padStart(2,'0')}` : null),
          labelColor: item.isActive ? '#EF9F3A' : (isKey ? '#FFD60A' : '#FFFFFF')
        });
      }
      return;
    }

    const uPlay = 0.16 + (N > 1 ? (fi / (N - 1)) : 0.5) * 0.68;
    const spPlay = spinePt(uPlay);

    if(parallelSubMode === 'dual'){
      const redOff  = {dx: -118, dy: 72};
      const blueOff = {dx: 122,  dy: -54};

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

      ctx.strokeStyle = `rgba(${lineRGB}, 0.75)`;
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
      const ringRx = Math.hypot(bPlay.x - rPlay.x, bPlay.y - rPlay.y) * 0.54;
      const ringRy = ringRx * 0.88;

      ctx.save();
      ctx.strokeStyle = `rgba(${lineRGB}, 0.54)`;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.ellipse(spPlay.x, spPlay.y, ringRx, ringRy, -0.15, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      const bgPlane = planes.find(p => p.id !== 'char') || planes[0];
      const M = Math.min(N, 7);
      for(let s = 0; s < M; s++){
        const ti = M === 1 ? 0 : Math.round((s / (M - 1)) * (N - 1));
        if(ti === fi) continue;
        const u = 0.16 + (N > 1 ? (ti / (N - 1)) : 0.5) * 0.68;
        const pc = spinePt(u), pr = redPt(u), pb = bluePt(u);
        const f1 = Math.max(0, Math.min(N - 1, Math.round(ti * 0.5)));
        const f2 = Math.max(0, Math.min(N - 1, Math.round(ti * 0.5 + N * 0.25)));
        const cw = Math.round(52 * pc.s), ch = Math.round(44 * pc.s);
        drawUpright3DCard(ctx, pb.x, pb.y, cw, ch, f2, {plane: bgPlane, borderColor: '#2E7CF6', borderWidth: 1.3, alpha: 0.82, cropToMask: false});
        drawUpright3DCard(ctx, pc.x, pc.y, cw, ch, ti, {plane: null, borderColor: `rgba(${lineRGB}, 0.65)`, borderWidth: 1.2, alpha: 0.82, cropToMask: false});
        drawUpright3DCard(ctx, pr.x, pr.y, cw, ch, f1, {plane: null, borderColor: '#FF3B30', borderWidth: 1.4, alpha: 0.86, cropToMask: true, label: `f${ti+1}`});
      }

      const fStretched1 = Math.max(0, Math.min(N - 1, Math.round(fi * 0.5)));
      const fStretched2 = Math.max(0, Math.min(N - 1, Math.round(fi * 0.5 + N * 0.25)));
      const bx = Math.max(54, Math.min(W - 54, bPlay.x));
      const by = Math.max(topSafe + 38, Math.min(H - botSafe - 38, bPlay.y));
      const rx = Math.max(54, Math.min(W - 54, rPlay.x));
      const ry = Math.max(topSafe + 42, Math.min(H - botSafe - 42, rPlay.y));

      ctx.save();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(rx, ry);
      ctx.lineTo(spPlay.x, spPlay.y);
      ctx.lineTo(bx, by);
      ctx.stroke();
      ctx.restore();

      drawUpright3DCard(ctx, bx, by, 82, 68, fStretched2, {
        plane: bgPlane,
        borderColor: '#2E7CF6',
        borderWidth: 2.0,
        cropToMask: false,
        label: `out 2 · f${fStretched2+1}`,
        labelColor: '#6CA6FF'
      });

      drawUpright3DCard(ctx, spPlay.x, spPlay.y, 84, 70, fi, {
        plane: null,
        borderColor: '#FFFFFF',
        borderWidth: 2.2,
        cropToMask: false,
        label: `spine · f${fi+1}/${N}`,
        labelColor: '#EF9F3A'
      });

      drawUpright3DCard(ctx, rx, ry, 92, 76, fStretched1, {
        plane: null,
        borderColor: '#FF3B30',
        borderWidth: 2.4,
        cropToMask: true,
        label: `out 1 (1/2x) · f${fStretched1+1}`,
        labelColor: '#FF6961'
      });

      ctx.fillStyle = dark ? 'rgba(6, 7, 10, 0.84)' : 'rgba(251, 250, 246, 0.90)';
      ctx.fillRect(10, H - 28, W - 20, 22);
      ctx.font = '700 11px "JetBrains Mono", monospace';
      ctx.fillStyle = '#FF453A';
      ctx.fillText('output timeline 1: SAM cutout (1/K stretched)', 16, H - 13);
      ctx.fillStyle = '#409CFF';
      ctx.textAlign = 'right';
      ctx.fillText('output timeline 2: multiplane parallax', W - 16, H - 13);
      ctx.textAlign = 'left';
      return;
    }

    // Sub-mode 1: Radial Multi-Worm Fan — ALL slices along ALL K rails at once
    const visPlanes = planes.filter(p => isPlaneVisible(p.id));
    const activeList = visPlanes.length ? visPlanes : planes;
    const K = Math.max(2, activeList.length);
    const RAIL_COLORS = ['#EF9F3A', '#FF453A', '#32D74B', '#409CFF', '#BF5AF2', '#FFD60A', '#64D2FF'];

    const baseRad = Math.min(W, H) * 0.31;

    function railAngle(rIdx){
      return -Math.PI * 0.72 + (rIdx / K) * (Math.PI * 2);
    }

    function railPt(rIdx, u){
      const c = spinePt(u);
      const ang = railAngle(rIdx);
      const radScale = Math.max(0.68, c.s);
      const rx = Math.cos(ang) * baseRad * 1.15 * radScale;
      const ry = Math.sin(ang) * baseRad * 0.84 * radScale;
      return {x: c.x + rx, y: c.y + ry, s: c.s, ang, radScale};
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

        const nFan = isSubj ? 8 : 5;
        ctx.strokeStyle = `rgba(${lineRGB}, ${isSubj ? (dark ? 0.40 : 0.32) : (dark ? 0.20 : 0.16)})`;
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
      ctx.strokeStyle = isSubj ? '#EF9F3A' : `rgba(${lineRGB}, 0.52)`;
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

    const ringScale = Math.max(0.68, spPlay.s);
    const ringR = baseRad * ringScale;
    ctx.save();
    ctx.strokeStyle = `rgba(${lineRGB}, 0.62)`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(spPlay.x, spPlay.y, ringR * 1.15, ringR * 0.84, -0.08, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    const M = Math.min(N, 6);
    for(let s = 0; s < M; s++){
      const ti = M === 1 ? 0 : Math.round((s / (M - 1)) * (N - 1));
      if(ti === fi) continue;
      const u = 0.16 + (N > 1 ? (ti / (N - 1)) : 0.5) * 0.68;
      for(let rIdx = 0; rIdx < K; rIdx++){
        const plane = activeList[rIdx];
        const isSubj = (plane.id === 'char');
        const rp = railPt(rIdx, u);
        const col = isSubj ? '#EF9F3A' : RAIL_COLORS[rIdx % RAIL_COLORS.length];
        const cw = Math.round((isSubj ? 52 : 42) * rp.s);
        const ch = Math.round((isSubj ? 44 : 34) * rp.s);
        const cx = Math.max(cw * 0.55 + 6, Math.min(W - cw * 0.55 - 6, rp.x));
        const cy = Math.max(topSafe + ch * 0.55 + 4, Math.min(H - botSafe - ch * 0.55 - 4, rp.y));
        drawUpright3DCard(ctx, cx, cy, cw, ch, ti, {
          plane: isSubj ? null : plane,
          borderColor: col,
          borderWidth: 1.2,
          alpha: 0.78,
          cropToMask: isSubj
        });
      }
    }

    const railCards = [];
    for(let rIdx = 0; rIdx < K; rIdx++){
      const plane = activeList[rIdx];
      const rawPt = railPt(rIdx, uPlay);
      const isSubj = (plane.id === 'char');
      const cw = isSubj ? 80 : 66;
      const ch = isSubj ? 68 : 56;
      const cx = Math.max(cw * 0.55 + 8, Math.min(W - cw * 0.55 - 8, rawPt.x));
      const cy = Math.max(topSafe + ch * 0.55 + 4, Math.min(H - botSafe - ch * 0.55 - 4, rawPt.y));
      const col = isSubj ? '#EF9F3A' : RAIL_COLORS[rIdx % RAIL_COLORS.length];
      const kSpeed = zRef / Math.max(0.3, plane.z);
      const fLayer = isSubj
        ? fi
        : Math.max(0, Math.min(N - 1, Math.round(fi * Math.min(1.2, Math.max(0.35, kSpeed)))));
      railCards.push({rIdx, plane, cx, cy, cw, ch, col, kSpeed, fLayer, isSubj});
    }

    ctx.save();
    ctx.strokeStyle = `rgba(${lineRGB}, 0.85)`;
    ctx.lineWidth = 1.5;
    for(const rc of railCards){
      ctx.beginPath();
      ctx.moveTo(spPlay.x, spPlay.y);
      ctx.lineTo(rc.cx, rc.cy);
      ctx.stroke();
    }
    ctx.restore();

    drawUpright3DCard(ctx, spPlay.x, spPlay.y, 68, 58, fi, {
      plane: null,
      borderColor: '#FFFFFF',
      borderWidth: 2.0,
      cropToMask: false,
      label: `Spine f${fi+1}`,
      labelColor: '#FFFFFF'
    });

    railCards.sort((a, b) => a.cy - b.cy);
    for(const rc of railCards){
      const shortLbl = String(rc.plane.label || rc.plane.id).split('(')[0].trim().slice(0, 10);
      drawUpright3DCard(ctx, rc.cx, rc.cy, rc.cw, rc.ch, rc.fLayer, {
        plane: rc.isSubj ? null : rc.plane,
        borderColor: rc.col,
        borderWidth: rc.isSubj ? 2.4 : 1.7,
        cropToMask: rc.isSubj,
        label: `${shortLbl} z=${rc.plane.z}`,
        labelColor: rc.col
      });
    }

    ctx.fillStyle = dark ? 'rgba(6, 7, 10, 0.82)' : 'rgba(251, 250, 246, 0.90)';
    ctx.fillRect(10, H - 28, W - 20, 22);
    ctx.fillStyle = dark ? '#FFFFFF' : '#161412';
    ctx.font = '700 11px "Bricolage Grotesque", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      `In this framework, ${K} parallel depth-plane timelines fan out around the spine (k = z_ref / z).`,
      W * 0.5, H - 13
    );
    ctx.textAlign = 'left';
  }

  function renderSingleStageView(ctx, W, H, fi, vMode){
    const img = getFrameImg(curWorm, fi);

    if(vMode === 'footage'){
      if(img) ctx.drawImage(img,0,0,W,H);
      return;
    }
    if(vMode === 'masks'){
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
    if(vMode === 'cutout'){
      if(img){ ctx.save(); ctx.globalAlpha=0.16; ctx.drawImage(img,0,0,W,H); ctx.restore(); }
      drawSamCutoutInRect(ctx, curWorm, fi, 0, 0, W, H, {cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
      return;
    }
    if(vMode === 'xray'){
      if(img){
        ctx.save();
        ctx.globalAlpha = 0.25;
        ctx.drawImage(img, 0, 0, W, H);
        ctx.restore();
      }
      ctx.fillStyle = 'rgba(251, 250, 246, 0.72)';
      ctx.fillRect(0, 0, W, H);

      const parts = extractShotParts(fi, zoomPlaneId);
      const labelQueue = [];

      for(const part of parts){
        if(!isPlaneVisible(part.planeId)) continue;
        if(part.kind === 'char_whole' && parts.some(p => p.kind === 'char_stroke')) continue;

        const isSel = (part.id === selectedPartId);
        const isHov = (part.id === hoveredPartId);
        const st = part.strokes || [];
        if(!st.length) continue;

        const dx = part.off.dx, dy = part.off.dy;
        drawStrokes(ctx, st, {color: 'rgba(251,250,246,0.92)', width: (isSel || isHov) ? 6.0 : 4.2, dx, dy});
        drawStrokes(ctx, st, {color: part.color, width: (isSel || isHov) ? 3.2 : 2.1, dx, dy});

        const bx = part.bbox.x0 + dx, by = part.bbox.y0 + dy;
        const bw = part.bbox.w, bh = part.bbox.h;
        ctx.save();
        ctx.strokeStyle = part.color;
        ctx.lineWidth = (isSel || isHov) ? 2.2 : 1.1;
        ctx.globalAlpha = (isSel || isHov) ? 0.96 : 0.52;
        ctx.setLineDash((isSel || isHov) ? [] : [3, 2]);
        ctx.strokeRect(bx, by, bw, bh);
        ctx.restore();

        stageHitBoxes.push({
          x: bx - 3, y: by - 3, w: Math.max(12, bw + 6), h: Math.max(12, bh + 6),
          partId: part.id, planeId: part.planeId
        });

        const cx = part.bbox.cx + dx, cy = part.bbox.cy + dy;
        if(Math.hypot(part.camDisp.dx, part.camDisp.dy) > 0.6){
          const vx = cx + part.camDisp.dx * 1.35, vy = cy + part.camDisp.dy * 1.35;
          ctx.save();
          ctx.strokeStyle = '#2B6CB0'; ctx.lineWidth = 1.8;
          ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(vx, vy); ctx.stroke();
          ctx.fillStyle = '#2B6CB0';
          ctx.beginPath(); ctx.arc(vx, vy, 2.4, 0, Math.PI * 2); ctx.fill();
          ctx.restore();
        }
        if(Math.hypot(part.rigDisp.dx, part.rigDisp.dy) > 0.6){
          const rx = cx + part.rigDisp.dx * 1.35, ry = cy + part.rigDisp.dy * 1.35;
          ctx.save();
          ctx.strokeStyle = '#D97706'; ctx.lineWidth = 2.0;
          ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(rx, ry); ctx.stroke();
          ctx.fillStyle = '#D97706';
          ctx.beginPath(); ctx.arc(rx, ry, 2.6, 0, Math.PI * 2); ctx.fill();
          ctx.restore();
        }

        labelQueue.push({
          text: `${part.shortLabel} z=${part.planeZ} [${part.sourceTag}]`,
          x: Math.max(4, Math.min(W - 115, bx)),
          y: Math.max(22, Math.min(H - 16, by - 13)),
          color: part.color,
          prio: (isSel || isHov) ? 10 : (part.planeId === 'char' ? 5 : 2)
        });
      }

      labelQueue.sort((a, b) => b.prio - a.prio);
      const placed = [];
      ctx.font = '700 8.5px "JetBrains Mono", monospace';
      for(const lbl of labelQueue){
        const tw = ctx.measureText(lbl.text).width + 8;
        const th = 12;
        let ly = lbl.y;
        let overlap = true;
        for(let tries = 0; tries < 5 && overlap; tries++){
          overlap = placed.some(r => !(lbl.x + tw < r.x || lbl.x > r.x + r.w || ly + th < r.y || ly > r.y + r.h));
          if(overlap) ly += 13;
        }
        if(overlap || ly + th > H - 2) continue;
        placed.push({x: lbl.x, y: ly, w: tw, h: th});
        ctx.fillStyle = 'rgba(251, 250, 246, 0.92)';
        ctx.fillRect(lbl.x, ly, tw, th);
        ctx.strokeStyle = lbl.color; ctx.lineWidth = 1.1;
        ctx.strokeRect(lbl.x, ly, tw, th);
        ctx.fillStyle = '#161412';
        ctx.fillText(lbl.text, lbl.x + 4, ly + 9);
      }

      ctx.fillStyle = 'rgba(22, 20, 18, 0.86)';
      ctx.fillRect(6, 5, W - 12, 15);
      ctx.fillStyle = '#FBFAF6';
      ctx.font = '700 9px "JetBrains Mono", monospace';
      ctx.fillText('PARTS X-RAY · Blue Vec=Cam Parallax · Amber Vec=Rig Motion · Click any part', 10, 15.5);
      return;
    }
    if(vMode === 'composite'){
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
      if(zoomPlaneId !== null && plane.id !== zoomPlaneId) continue;
      const off = camOffset(plane.z, fi);
      if(plane.id === 'char'){
        const strokes = (S && S.cast && S.cast.frames && S.cast.frames[fi]) ? S.cast.frames[fi] :
          ((curWorm.frames && curWorm.frames[fi] && curWorm.frames[fi].doodle) ? curWorm.frames[fi].doodle.map(s=>s.map(p=>[p[0]*W,p[1]*H])) : []);
        if(celFill && strokes.length) drawStrokes(ctx, strokes, {color:'rgba(0,0,0,0)', width:0.1, boilSeed, boilAmp, fill:celFill});
        if(vMode === 'composite') drawStrokes(ctx, strokes, {color:'rgba(251,250,246,0.92)', width:5.2, boilSeed, boilAmp});
        else if(fi===0 && vMode==='cartoon') drawStrokes(ctx, strokes, {color:'#EF9F3A', width:6, boilSeed, boilAmp});
        drawStrokes(ctx, strokes, {color:'#161412', width:2.5, boilSeed, boilAmp});
      } else if(S && Array.isArray(S.objects)){
        const objs = S.objects.filter(o => o.plane === plane.id);
        const depthAlpha = plane.z>=10 ? 0.65 : (plane.z>=6 ? 0.78 : (plane.z>=3 ? 0.90 : 0.98));
        const depthWidth = plane.z>=10 ? 1.6  : (plane.z>=6 ? 1.9  : 2.2);
        for(const o of objs){
          const ost = getObjectStrokes(o, fi);
          if(!ost || !ost.length) continue;
          if(vMode === 'composite'){
            drawStrokes(ctx, ost, {color:'rgba(251,250,246,0.86)', width:depthWidth+2.4, dx:off.dx, dy:off.dy, boilSeed:boilSeed+1, boilAmp:boilAmp*0.6});
          }
          drawStrokes(ctx, ost, {color:`rgba(22,20,18,${depthAlpha})`, width:depthWidth, dx:off.dx, dy:off.dy, boilSeed:boilSeed+1, boilAmp:boilAmp*0.6, fill:(celFill && plane.z<10 && o.class!=='grass' && o.class!=='ground')?celFill:null});
        }
      } else if(curWorm && Array.isArray(curWorm.depth_worms)){
        const dwObj = curWorm.depth_worms.find(d => d.id === plane.id);
        if(dwObj && Array.isArray(dwObj.strokes0) && dwObj.strokes0.length){
          const u0 = Number.isFinite(dwObj.u0) ? dwObj.u0 : 0.5;
          const v0 = Number.isFinite(dwObj.v0) ? dwObj.v0 : 0.5;
          const mapped = dwObj.strokes0.map(s => s.map(p => [(u0 + p[0])*W + off.dx, (v0 + p[1])*H + off.dy]));
          if(vMode === 'composite') drawStrokes(ctx, mapped, {color:'rgba(251,250,246,0.84)', width:4.0});
          drawStrokes(ctx, mapped, {color:'#161412', width:1.8});
        }
      }
    }

    const allStageParts = extractShotParts(fi, zoomPlaneId);
    for(const part of allStageParts){
      if(!isPlaneVisible(part.planeId)) continue;
      if(part.kind === 'char_whole' && allStageParts.some(p => p.kind === 'char_stroke')) continue;
      const bx = part.bbox.x0 + part.off.dx, by = part.bbox.y0 + part.off.dy;
      stageHitBoxes.push({
        x: bx - 3, y: by - 3, w: Math.max(12, part.bbox.w + 6), h: Math.max(12, part.bbox.h + 6),
        partId: part.id, planeId: part.planeId
      });
    }

    const focusId = hoveredPartId || selectedPartId;
    if(focusId){
      const fp = allStageParts.find(p => p.id === focusId);
      if(fp && fp.strokes && fp.strokes.length){
        const dx = fp.off.dx, dy = fp.off.dy;
        drawStrokes(ctx, fp.strokes, {color: '#EF9F3A', width: 5.5, dx, dy});
        drawStrokes(ctx, fp.strokes, {color: fp.color, width: 2.8, dx, dy});
        ctx.save();
        ctx.strokeStyle = fp.color; ctx.lineWidth = 2.0; ctx.setLineDash([4, 2]);
        ctx.strokeRect(fp.bbox.x0 + dx - 3, fp.bbox.y0 + dy - 3, fp.bbox.w + 6, fp.bbox.h + 6);
        ctx.restore();
      }
    }
  }

  function renderStage(fi){
    if(!curWorm) return;
    stageHitBoxes = [];
    const W = (S && S.W) || curWorm.W || 480;
    const H = (S && S.H) || curWorm.H || 360;
    if(cvStage.width !== W || cvStage.height !== H){ cvStage.width = W; cvStage.height = H; }
    const ctx = ctxStage;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#FBFAF6';
    ctx.fillRect(0,0,W,H);

    if(view === 'all4'){
      const qViews = [
        {id:'composite', lbl:'Over Footage'},
        {id:'xray',      lbl:'Parts X-Ray'},
        {id:'cartoon',   lbl:'Cartoon'},
        {id:'footage',   lbl:'Footage'}
      ];
      const hw = W * 0.5, hh = H * 0.5;
      qViews.forEach((qv, idx)=>{
        const qx = (idx % 2) * hw, qy = Math.floor(idx / 2) * hh;
        ctx.save();
        ctx.beginPath(); ctx.rect(qx, qy, hw, hh); ctx.clip();
        ctx.translate(qx, qy);
        ctx.scale(0.5, 0.5);
        renderSingleStageView(ctx, W, H, fi, qv.id);
        ctx.restore();
        ctx.strokeStyle = '#161412'; ctx.lineWidth = 1.2;
        ctx.strokeRect(qx, qy, hw, hh);
        ctx.fillStyle = 'rgba(22, 20, 18, 0.82)';
        ctx.fillRect(qx + 4, qy + 4, 92, 15);
        ctx.fillStyle = '#FBFAF6';
        ctx.font = '700 9px "JetBrains Mono", monospace';
        ctx.fillText(qv.lbl, qx + 8, qy + 14.5);
      });
      return;
    }

    renderSingleStageView(ctx, W, H, fi, view);
  }

  function renderPartsInspectorMode(ctx, W, H, fi, N, planes, zRef){
    const srcW = (S && S.W) || curWorm.W || 480;
    const srcH = (S && S.H) || curWorm.H || 360;
    const allParts = extractShotParts(fi, zoomPlaneId);
    const activePart = selectedPartId ? allParts.find(p => p.id === selectedPartId) : null;

    if(activePart){
      const padL = 12, padR = 12, padT = 8, padB = 26;
      const topBarH = 22;

      ctx.fillStyle = '#161412';
      ctx.beginPath(); ctx.roundRect(padL, padT, W - padL - padR, topBarH, 4); ctx.fill();

      const backW = 92;
      ctx.fillStyle = '#EF9F3A';
      ctx.beginPath(); ctx.roundRect(padL + 3, padT + 3, backW, topBarH - 6, 3); ctx.fill();
      ctx.fillStyle = '#161412';
      ctx.font = '700 9.5px "JetBrains Mono", monospace';
      ctx.fillText('<- All Parts', padL + 9, padT + 14.5);
      pushHitBox({x: padL + 3, y: padT + 3, w: backW, h: topBarH - 6, selectPartId: '__NONE__'});

      ctx.fillStyle = '#FBFAF6';
      ctx.font = '700 9.5px "JetBrains Mono", monospace';
      const hdrMeta = `${activePart.label} · Plane: ${activePart.planeLabel} (z=${activePart.planeZ}, k=${activePart.kMult.toFixed(2)}x) · Src: ${activePart.sourceFull}`;
      ctx.fillText(hdrMeta.slice(0, 82), padL + backW + 10, padT + 14.5);

      const stripH = 42;
      const mainY = padT + topBarH + 6;
      const mainH = H - mainY - stripH - padB - 6;
      const leftW = Math.round((W - padL - padR - 8) * 0.46);
      const rightX = padL + leftW + 8;
      const rightW = W - padR - rightX;

      ctx.fillStyle = '#FFFDF8';
      ctx.strokeStyle = activePart.color;
      ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.roundRect(padL, mainY, leftW, mainH, 6); ctx.fill(); ctx.stroke();

      ctx.fillStyle = '#161412';
      ctx.font = '700 10px "Bricolage Grotesque", sans-serif';
      ctx.fillText(`ISOLATED PART GEOMETRY (f=${String(fi+1).padStart(2,'0')} vs Seed f=01)`, padL + 8, mainY + 14);

      drawPartInRect(ctx, activePart, fi, padL + 8, mainY + 20, leftW - 16, mainH - 44, {
        cropToPart: true, showGhost0: true, color: activePart.color, width: 2.5
      });

      ctx.fillStyle = 'rgba(22, 20, 18, 0.06)';
      ctx.fillRect(padL + 4, mainY + mainH - 22, leftW - 8, 18);
      ctx.font = '600 8.5px "JetBrains Mono", monospace';
      ctx.fillStyle = '#161412';
      ctx.fillText(`Tot Δ:(${activePart.totalDisp.dx.toFixed(1)},${activePart.totalDisp.dy.toFixed(1)})`, padL + 6, mainY + mainH - 10);
      ctx.fillStyle = '#2B6CB0';
      ctx.fillText(`Cam:(${activePart.camDisp.dx.toFixed(1)},${activePart.camDisp.dy.toFixed(1)})`, padL + 114, mainY + mainH - 10);
      ctx.fillStyle = '#D97706';
      ctx.fillText(`Rig:(${activePart.rigDisp.dx.toFixed(1)},${activePart.rigDisp.dy.toFixed(1)})`, padL + 214, mainY + mainH - 10);

      ctx.fillStyle = '#FFFFFF';
      ctx.strokeStyle = '#BFAF97';
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.roundRect(rightX, mainY, rightW, mainH, 6); ctx.fill(); ctx.stroke();

      ctx.fillStyle = '#161412';
      ctx.font = '700 10px "Bricolage Grotesque", sans-serif';
      ctx.fillText('CAUSAL MOTION DECOMPOSITION: Total(t) = k·Cam(t) + Rig(t)', rightX + 8, mainY + 14);

      const gx0 = rightX + 34, gy0 = mainY + 24, gw = rightW - 44, gh = Math.max(36, mainH - 60);
      ctx.fillStyle = '#FBFAF6';
      ctx.strokeStyle = '#D8CCB8';
      ctx.lineWidth = 1;
      ctx.fillRect(gx0, gy0, gw, gh);
      ctx.strokeRect(gx0, gy0, gw, gh);

      const midY = gy0 + gh * 0.5;
      ctx.strokeStyle = 'rgba(22,20,18,0.22)';
      ctx.setLineDash([2, 2]);
      ctx.beginPath(); ctx.moveTo(gx0, midY); ctx.lineTo(gx0 + gw, midY); ctx.stroke();
      ctx.setLineDash([]);

      const seriesCam = [], seriesRig = [], seriesTot = [];
      let maxAbs = 12;
      for(let ti = 0; ti < N; ti++){
        const cOff = camOffset(activePart.planeZ, ti);
        let rDx = 0;
        if(activePart.kind === 'char_whole' || activePart.kind === 'char_stroke' || activePart.isAnimated){
          let stT = [];
          if(activePart.kind === 'char_whole'){
            stT = (S && S.cast && S.cast.frames && S.cast.frames[ti]) ? S.cast.frames[ti] : [];
          } else if(activePart.kind === 'char_stroke'){
            const sIdx = parseInt(activePart.id.split(':s')[1], 10) || 0;
            const fSt = (S && S.cast && S.cast.frames && S.cast.frames[ti]) ? S.cast.frames[ti] : [];
            stT = fSt[sIdx] ? [fSt[sIdx]] : [];
          } else if(S && Array.isArray(S.objects)){
            const objId = activePart.id.replace(/^obj:/, '');
            const o = S.objects.find(ob => ob.id === objId);
            if(o) stT = getObjectStrokes(o, ti);
          }
          if(stT && stT.length){
            const bbT = computeStrokesBBox(stT, srcW, srcH);
            rDx = bbT.cx - activePart.bbox0.cx;
          }
        }
        const totDx = cOff.dx + rDx;
        seriesCam.push(cOff.dx);
        seriesRig.push(rDx);
        seriesTot.push(totDx);
        maxAbs = Math.max(maxAbs, Math.abs(cOff.dx), Math.abs(rDx), Math.abs(totDx));
      }

      const plotCurve = (arr, col, width, dash)=>{
        if(arr.length < 2) return;
        ctx.save();
        ctx.strokeStyle = col; ctx.lineWidth = width;
        if(dash) ctx.setLineDash(dash);
        ctx.beginPath();
        for(let ti = 0; ti < arr.length; ti++){
          const x = gx0 + (ti / (arr.length - 1)) * gw;
          const y = midY - (arr[ti] / maxAbs) * (gh * 0.44);
          if(ti === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.restore();
      };

      plotCurve(seriesCam, '#2B6CB0', 1.8, [4, 2]);
      plotCurve(seriesRig, '#D97706', 2.0, null);
      plotCurve(seriesTot, '#161412', 2.4, null);

      const phX = gx0 + (N > 1 ? (fi / (N - 1)) * gw : gw * 0.5);
      ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.moveTo(phX, gy0); ctx.lineTo(phX, gy0 + gh); ctx.stroke();

      ctx.fillStyle = '#5E554B';
      ctx.font = '600 8.5px "JetBrains Mono", monospace';
      ctx.fillText(`+${Math.round(maxAbs)}`, rightX + 4, gy0 + 8);
      ctx.fillText('0', rightX + 14, midY + 3);
      ctx.fillText(`-${Math.round(maxAbs)}`, rightX + 4, gy0 + gh - 2);

      const xs = (S && Array.isArray(S.xsheet) && S.xsheet[fi]) ? S.xsheet[fi] : null;
      const xsText = xs
        ? `X-Sheet f${String(fi+1).padStart(2,'0')} [${xs.kind || 'I'}]: ${xs.note || 'Inbetween'}`
        : `Frame f${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`;
      ctx.fillStyle = '#161412';
      ctx.font = '600 8.5px "JetBrains Mono", monospace';
      ctx.fillText(xsText.slice(0, 56), rightX + 8, gy0 + gh + 14);
      ctx.fillStyle = '#161412'; ctx.fillText('— Total', rightX + 8, gy0 + gh + 27);
      ctx.fillStyle = '#2B6CB0'; ctx.fillText('-- k·Cam', rightX + 76, gy0 + gh + 27);
      ctx.fillStyle = '#D97706'; ctx.fillText('— Rig', rightX + 150, gy0 + gh + 27);

      const stripY = H - stripH - padB;
      const sibParts = allParts.filter(p => !(p.kind === 'char_whole' && allParts.some(q => q.kind === 'char_stroke'))).slice(0, 10);
      const nSib = Math.max(1, sibParts.length);
      const sGap = 4;
      const sW = (W - padL - padR - sGap * (nSib - 1)) / nSib;
      sibParts.forEach((sp, idx)=>{
        const sx = padL + idx * (sW + sGap);
        const isCur = (sp.id === activePart.id);
        ctx.fillStyle = isCur ? '#FFF8EB' : '#FFFFFF';
        ctx.strokeStyle = isCur ? sp.color : '#C9BBA6';
        ctx.lineWidth = isCur ? 2.2 : 1.1;
        ctx.beginPath(); ctx.roundRect(sx, stripY, sW, stripH, 4); ctx.fill(); ctx.stroke();

        drawPartInRect(ctx, sp, fi, sx + 2, stripY + 12, sW - 4, stripH - 14, {
          cropToPart: true, showGhost0: false, color: sp.color, width: 1.5
        });
        ctx.fillStyle = '#161412';
        ctx.font = '700 8px "JetBrains Mono", monospace';
        ctx.fillText(sp.shortLabel.slice(0, 8), sx + 3, stripY + 9.5);
        pushHitBox({x: sx, y: stripY, w: sW, h: stripH, selectPartId: sp.id, planeId: sp.planeId});
      });
      return;
    }

    const padL = 10, padR = 10, padT = 6, padB = 26;
    const topBarH = 20;

    let displayParts = [];
    if(zoomPlaneId !== null){
      displayParts = allParts.filter(p => !(p.kind === 'char_whole' && allParts.length > 1)).slice(0, 15);
    } else {
      const charWhole = allParts.find(p => p.kind === 'char_whole');
      if(charWhole) displayParts.push(charWhole);
      const sceneObjs = allParts.filter(p => p.kind === 'object' || p.kind === 'dw_fallback');
      const seenClasses = new Set();
      const primaryObjs = [], secondaryObjs = [];
      for(const o of sceneObjs){
        const clsKey = `${o.planeId}:${o.shortLabel.replace(/[0-9]+$/, '')}`;
        if(!seenClasses.has(clsKey) || seenClasses.size < 6){
          seenClasses.add(clsKey);
          primaryObjs.push(o);
        } else {
          secondaryObjs.push(o);
        }
      }
      displayParts.push(...primaryObjs.slice(0, 10));
      const charStrokes = allParts.filter(p => p.kind === 'char_stroke').slice(0, Math.max(2, 15 - displayParts.length));
      displayParts.push(...charStrokes);
      if(displayParts.length < 15){
        displayParts.push(...secondaryObjs.slice(0, 15 - displayParts.length));
      }
    }

    ctx.fillStyle = '#EFE6D5';
    ctx.strokeStyle = '#C9BBA6';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(padL, padT, W - padL - padR, topBarH, 4); ctx.fill(); ctx.stroke();

    let hdrX = padL + 6;
    if(zoomPlaneId !== null){
      const bw = 88;
      ctx.fillStyle = '#161412';
      ctx.beginPath(); ctx.roundRect(hdrX, padT + 2, bw, topBarH - 4, 3); ctx.fill();
      ctx.fillStyle = '#EF9F3A';
      ctx.font = '700 9px "JetBrains Mono", monospace';
      ctx.fillText('<- All Planes', hdrX + 6, padT + 13);
      pushHitBox({x: hdrX, y: padT + 2, w: bw, h: topBarH - 4, zoomPlaneOut: true});
      hdrX += bw + 8;
    }

    ctx.fillStyle = '#161412';
    ctx.font = '700 9px "JetBrains Mono", monospace';
    const titleStr = zoomPlaneId
      ? `PLANE [${zoomPlaneId.toUpperCase()}] PARTS (${displayParts.length}/${allParts.length}) · Click any card for Causal Microscope`
      : `DECOMPOSED SHOT PARTS (${displayParts.length} of ${allParts.length} total) · Click any card for Causal Microscope`;
    ctx.fillText(titleStr.slice(0, 86), hdrX, padT + 13.5);

    const gridY = padT + topBarH + 5;
    const availW = W - padL - padR;
    const availH = H - gridY - padB;
    const nCards = Math.max(1, displayParts.length);
    const cols = nCards <= 4 ? 2 : (nCards <= 6 ? 3 : (nCards <= 8 ? 4 : 5));
    const rows = Math.ceil(nCards / cols);
    const gap = 5;
    const cw = (availW - gap * (cols - 1)) / cols;
    const ch = (availH - gap * (rows - 1)) / rows;

    displayParts.forEach((part, idx)=>{
      const c = idx % cols, r = Math.floor(idx / cols);
      const cx = padL + c * (cw + gap);
      const cy = gridY + r * (ch + gap);
      const isHov = (part.id === hoveredPartId);

      ctx.save();
      ctx.fillStyle = isHov ? '#FFFBF2' : '#FFFFFF';
      ctx.strokeStyle = isHov ? part.color : '#C9BBA6';
      ctx.lineWidth = isHov ? 2.2 : 1.2;
      ctx.beginPath(); ctx.roundRect(cx, cy, cw, ch, 5); ctx.fill(); ctx.stroke();

      const topH = 14;
      ctx.fillStyle = 'rgba(22, 20, 18, 0.06)';
      ctx.fillRect(cx + 1, cy + 1, cw - 2, topH);
      ctx.fillStyle = part.color;
      ctx.fillRect(cx + 1, cy + 1, 4, topH);

      ctx.fillStyle = '#161412';
      ctx.font = '700 8.5px "Bricolage Grotesque", sans-serif';
      ctx.fillText(part.shortLabel.slice(0, 11), cx + 8, cy + 11);

      ctx.fillStyle = '#5E554B';
      ctx.font = '600 7.5px "JetBrains Mono", monospace';
      const rightTag = `z=${part.planeZ}·${part.sourceTag}`;
      const rtw = ctx.measureText(rightTag).width;
      if(cw - rtw - 4 > 48){
        ctx.fillText(rightTag, cx + cw - rtw - 4, cy + 10.5);
      }

      const footH = 13;
      const bodyY = cy + topH + 2;
      const bodyH = Math.max(16, ch - topH - footH - 4);
      drawPartInRect(ctx, part, fi, cx + 3, bodyY, cw - 6, bodyH, {
        cropToPart: true, showGhost0: true, color: part.color, width: 1.9
      });

      const footY = cy + ch - footH;
      ctx.fillStyle = 'rgba(239, 230, 213, 0.55)';
      ctx.fillRect(cx + 1, footY, cw - 2, footH - 1);
      ctx.fillStyle = '#4A4238';
      ctx.font = '600 7.5px "JetBrains Mono", monospace';
      const statStr = `${part.nStrokes}S/${part.nPts}p Δ(${Math.round(part.totalDisp.dx)},${Math.round(part.totalDisp.dy)})`;
      ctx.fillText(statStr.slice(0, 20), cx + 4, footY + 9.5);
      ctx.restore();

      pushHitBox({x: cx, y: cy, w: cw, h: ch, selectPartId: part.id, planeId: part.planeId});
    });
  }

  function renderSingleWormLens(ctx, W, H, fi, N, planes, zRef, mode){
    if(mode === 'parallel'){
      renderParallelTimelinesMode(ctx, W, H, fi, N, planes, zRef);
      return;
    }
    if(mode === 'parts'){
      renderPartsInspectorMode(ctx, W, H, fi, N, planes, zRef);
      return;
    }

    if(mode === 'strobe'){
      const padT = 36, padB = 30, padL = 16, padR = 16;
      const stageW = W - padL - padR, stageH = H - padT - padB;
      ctx.save();
      ctx.beginPath(); ctx.roundRect(padL, padT, stageW, stageH, 6); ctx.clip();
      const bgImg = getFrameImg(curWorm, fi) || getFrameImg(curWorm, 0);
      if(bgImg){ ctx.globalAlpha = 0.25; ctx.drawImage(bgImg, padL, padT, stageW, stageH); ctx.globalAlpha = 1; }
      ctx.fillStyle = 'rgba(251,250,246,0.45)'; ctx.fillRect(padL, padT, stageW, stageH);

      for(const plane of planes){
        if(plane.id !== 'char' && isPlaneVisible(plane.id)){
          drawPlaneObjectsInRect(ctx, plane, fi, padL, padT, stageW, stageH, false);
        }
      }

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

    if(mode === 'kymo'){
      const padL = 128, padR = 16, padT = 38, padB = 22;
      const trackW = W - padL - padR, availH = H - padT - padB, gap = 8;
      const bandH = (availH - gap*2) / 3;
      const frames = curWorm.frames || [];
      const bands = [
        {title:'Horizontal X(t)', sub:'Left to Right travel', color:'#EF9F3A', getVal:fr=>fr.c?fr.c[0]:0.5},
        {title:'Vertical Bounce Y(t)', sub:'Top to Bottom gait', color:'#2E7A4A', getVal:fr=>fr.c?fr.c[1]:0.5},
        {title:'Scale R(t) & Pan', sub:'Looming size & cam', color:'#2B6CB0', getVal:fr=>Math.min(1,(fr.r||0.15)*2.5)}
      ];
      bands.forEach((b, bIdx)=>{
        const y0 = padT + bIdx*(bandH + gap);
        ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.1;
        ctx.beginPath(); ctx.roundRect(10, y0, W-20, bandH, 5); ctx.fill(); ctx.stroke();
        ctx.save();
        ctx.beginPath(); ctx.rect(11, y0+1, padL-16, bandH-2); ctx.clip();
        ctx.fillStyle = 'rgba(239,159,58,0.12)'; ctx.fillRect(11, y0+1, padL-16, bandH-2);
        ctx.fillStyle = '#161412'; ctx.font = '700 10.5px "Bricolage Grotesque", sans-serif';
        ctx.fillText(b.title, 15, y0 + bandH*0.42);
        ctx.fillStyle = '#6B6259'; ctx.font = '500 9px "JetBrains Mono", monospace';
        ctx.fillText(b.sub, 15, y0 + bandH*0.72);
        ctx.restore();
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

    if(mode === 'anatomy'){
      const padL = 14, padR = 14, padT = 38, padB = 18;
      const topH = Math.round((H - padT - padB)*0.48);
      const botY = padT + topH + 10, botH = H - padB - botY;
      const halfW = Math.round((W - padL - padR - 10)*0.5);
      ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.roundRect(padL, padT, halfW, topH, 5); ctx.fill(); ctx.stroke();
      drawSamCutoutInRect(ctx, curWorm, 0, padL+6, padT+20, halfW-12, topH-26, {cropToMask:true, drawOutline:true, outlineColor:'#BFAF97', drawDoodle:true, doodleColor:'#EF9F3A'});
      ctx.fillStyle = '#8A4A05'; ctx.font = '700 10px "JetBrains Mono", monospace';
      ctx.fillText('THE LINE (f=01 Seed Doodle)', padL+8, padT+14);
      pushHitBox({x: padL, y: padT, w: halfW, h: topH, fi: 0, planeId: null, togglePlane: false});

      const rx0 = padL + halfW + 10;
      ctx.fillStyle = '#FFFDF8'; ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.roundRect(rx0, padT, halfW, topH, 5); ctx.fill(); ctx.stroke();
      drawSamCutoutInRect(ctx, curWorm, fi, rx0+6, padT+20, halfW-12, topH-26, {cropToMask:true, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true, doodleColor:'#161412'});
      ctx.fillStyle = '#161412';
      ctx.fillText(`WARPED RIG @ f=${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`, rx0+8, padT+14);

      ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#BFAF97'; ctx.lineWidth = 1.1;
      ctx.beginPath(); ctx.roundRect(padL, botY, W-padL-padR, botH, 5); ctx.fill(); ctx.stroke();
      const jPadL = padL + 116, jTrackW = W - padR - jPadL - 10;
      const joints = curWorm.joints || {};
      const jNames = Object.keys(joints);
      const colors = ['#EF9F3A','#2E7A4A','#2B6CB0','#B8432F','#6B46C1'];
      const rows = jNames.length
        ? jNames.slice(0,5).map((jn,i)=>({label:jn.replace(/_/g,' '), pts:joints[jn], color:colors[i%colors.length]}))
        : (curWorm.depth_worms||[]).slice(0,5).map((dw,i)=>({label:dw.label, pts:(dw.track||[]).map(t=>[t[0],t[1]]), color:dw.color||colors[i%colors.length]}));
      const rTop = botY + 18, rH = Math.max(16, (botH - 24)/Math.max(1, rows.length));
      rows.forEach((r, idx)=>{
        const ry = rTop + idx*rH;
        ctx.save();
        ctx.beginPath(); ctx.rect(padL + 6, ry, jPadL - padL - 10, rH); ctx.clip();
        ctx.fillStyle = '#6B6259'; ctx.font = '600 9.5px "JetBrains Mono", monospace';
        ctx.fillText(String(r.label).slice(0,14), padL+8, ry + rH*0.65);
        ctx.restore();
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
      ctx.beginPath(); ctx.moveTo(scrubX, rTop-2); ctx.lineTo(scrubX, botY+botH-4); ctx.stroke(); ctx.restore();
      return;
    }

    if(mode === 'box'){
      const padX=28, padT=40, padB=24, availW=W-padX*2, availH=H-padT-padB, nP=planes.length;
      const srcW = (S && S.W) || curWorm.W || 480, srcH = (S && S.H) || curWorm.H || 360;
      planes.forEach((plane, idx)=>{
        const vis = isPlaneVisible(plane.id);
        const u = nP===1 ? 0.5 : idx/(nP-1);
        const scale = 0.54 + u*0.34;
        const pw = availW*scale, ph = availH*scale;
        const cx = padX + (1-u)*(availW-pw)*0.85 + u*(availW-pw)*0.12;
        const cy = padT + (1-u)*6 + u*(availH-ph)*0.85;
        const off = camOffset(plane.z, fi);
        const sx = pw/srcW, sy = ph/srcH;
        const t = tintForPlane(plane.id, plane.z, zRef);
        ctx.save(); ctx.globalAlpha = vis ? 1 : 0.22;
        ctx.fillStyle = t.fill; ctx.strokeStyle = t.stroke; ctx.lineWidth = plane.id==='char'?2.2:1.3;
        ctx.beginPath(); ctx.roundRect(cx,cy,pw,ph,4); ctx.fill(); ctx.stroke();
        ctx.save(); ctx.beginPath(); ctx.rect(cx,cy,pw,ph); ctx.clip();
        if(plane.id==='char'){
          drawSamCutoutInRect(ctx, curWorm, fi, cx, cy, pw, ph, {cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
        } else {
          drawPlaneObjectsInRect(ctx, plane, fi, cx, cy, pw, ph, false);
        }
        ctx.restore();
        const lblText = `${plane.label} · z=${plane.z}`;
        ctx.font='600 9.5px "JetBrains Mono", monospace';
        const tw = ctx.measureText(lblText).width + 8;
        const lx = cx + 6 + (idx % 2) * Math.min(110, pw * 0.35);
        const ly = cy + 4;
        ctx.fillStyle = 'rgba(251, 250, 246, 0.92)';
        ctx.fillRect(lx, ly, tw, 13);
        ctx.fillStyle='#161412';
        ctx.fillText(lblText, lx+4, ly+10);
        ctx.restore();
        pushHitBox({x: cx, y: cy, w: pw, h: ph, fi, planeId: plane.id, togglePlane: true});
      });
      return;
    }

    // Disentangled Plane Worms ('lanes') — supports Semantic Zoom into Plane Parts!
    if(zoomPlaneId !== null){
      const planeParts = extractShotParts(fi, zoomPlaneId).filter(p => !(p.kind === 'char_whole' && zoomPlaneId === 'char')).slice(0, 7);
      const padL = 132, padR = 14, padT = 26, padB = 22;
      const availH = H - padT - padB;
      const nP = Math.max(1, planeParts.length);
      const laneGap = 5;
      const laneH = Math.max(26, (availH - laneGap * (nP - 1)) / nP);
      const trackW = W - padL - padR;

      ctx.fillStyle = '#161412';
      ctx.beginPath(); ctx.roundRect(10, 4, 96, 18, 3); ctx.fill();
      ctx.fillStyle = '#EF9F3A';
      ctx.font = '700 9.5px "JetBrains Mono", monospace';
      ctx.fillText('<- All Planes', 16, 16);
      pushHitBox({x: 10, y: 4, w: 96, h: 18, zoomPlaneOut: true});

      ctx.fillStyle = '#161412';
      ctx.font = '700 9.5px "JetBrains Mono", monospace';
      ctx.fillText(`PLANE [${zoomPlaneId.toUpperCase()}] PART LANES (${planeParts.length} parts) · Click part header to inspect`, 114, 16.5);

      for(let pIdx = 0; pIdx < planeParts.length; pIdx++){
        const part = planeParts[pIdx];
        const y0 = padT + pIdx * (laneH + laneGap);
        const isSel = (part.id === selectedPartId || part.id === hoveredPartId);

        ctx.save();
        ctx.fillStyle = isSel ? '#FFFBF2' : '#FFFFFF';
        ctx.strokeStyle = isSel ? part.color : '#BFAF97';
        ctx.lineWidth = isSel ? 2.0 : 1.1;
        ctx.beginPath(); ctx.roundRect(10, y0, W - 20, laneH, 5); ctx.fill(); ctx.stroke();

        ctx.save();
        ctx.beginPath(); ctx.rect(11, y0 + 1, padL - 16, laneH - 2); ctx.clip();
        ctx.fillStyle = 'rgba(239, 230, 213, 0.55)';
        ctx.fillRect(11, y0 + 1, padL - 16, laneH - 2);
        ctx.fillStyle = part.color;
        ctx.fillRect(11, y0 + 1, 4, laneH - 2);
        ctx.fillStyle = '#161412';
        ctx.font = '700 10px "Bricolage Grotesque", sans-serif';
        ctx.fillText(part.shortLabel.slice(0, 14), 19, y0 + Math.min(15, laneH * 0.44));
        ctx.fillStyle = '#5E554B';
        ctx.font = '500 8.5px "JetBrains Mono", monospace';
        ctx.fillText(`${part.sourceTag} · ${part.nStrokes}S/${part.nPts}p`, 19, y0 + Math.min(28, laneH * 0.80));
        ctx.restore();
        pushHitBox({x: 11, y: y0 + 1, w: padL - 16, h: laneH - 2, selectPartId: part.id, setMode: 'parts'});

        ctx.save();
        ctx.beginPath(); ctx.rect(padL, y0 + 2, trackW, laneH - 4); ctx.clip();

        const nStamps = Math.min(N, 6);
        const celH = Math.max(20, laneH - 8);
        const celW = Math.round(celH * 1.18);
        let lastRight = -999;
        for(let sIdx = 0; sIdx < nStamps; sIdx++){
          const ti = nStamps === 1 ? 0 : Math.round((sIdx / (nStamps - 1)) * (N - 1));
          const cx = padL + (N > 1 ? (ti / (N - 1)) * trackW : trackW * 0.5);
          const rx = Math.max(padL + 2, Math.min(padL + trackW - celW - 2, cx - celW * 0.5));
          if(rx < lastRight + 4) continue;
          lastRight = rx + celW;
          const ry = y0 + (laneH - celH) * 0.5;
          ctx.fillStyle = '#FBFAF6';
          ctx.strokeStyle = '#C9BBA6';
          ctx.lineWidth = 1.0;
          ctx.fillRect(rx, ry, celW, celH);
          drawPartInRect(ctx, part, ti, rx + 2, ry + 2, celW - 4, celH - 4, {
            cropToPart: true, showGhost0: false, color: part.color, width: 1.6
          });
          ctx.strokeRect(rx, ry, celW, celH);
          pushHitBox({x: rx, y: ry, w: celW, h: celH, fi: ti});
        }

        const actX = padL + (N > 1 ? (fi / (N - 1)) * trackW : trackW * 0.5);
        const actH = Math.max(22, laneH - 4);
        const actW = Math.round(actH * 1.24);
        const arx = Math.max(padL + 2, Math.min(padL + trackW - actW - 2, actX - actW * 0.5));
        const ary = y0 + (laneH - actH) * 0.5;
        ctx.fillStyle = '#FFFBF4';
        ctx.strokeStyle = part.color;
        ctx.lineWidth = 2.0;
        ctx.fillRect(arx, ary, actW, actH);
        drawPartInRect(ctx, part, fi, arx + 2, ary + 2, actW - 4, actH - 4, {
          cropToPart: true, showGhost0: true, color: part.color, width: 2.0
        });
        ctx.strokeRect(arx, ary, actW, actH);
        ctx.restore();
        ctx.restore();
      }

      const scrubX = padL + (N > 1 ? (fi / (N - 1)) * trackW : trackW * 0.5);
      ctx.save();
      ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2; ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(scrubX, padT - 4); ctx.lineTo(scrubX, H - padB + 4); ctx.stroke();
      ctx.restore();
      return;
    }

    const planesNearFirst = planes.slice().reverse();
    const padL = 128, padR = 16, padT = 38, padB = 22;
    const availH = H - padT - padB;
    const nP = Math.max(1, planesNearFirst.length);
    const laneGap = 6;
    const laneH = Math.max(36, (availH - laneGap*(nP-1)) / nP);
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
      ctx.beginPath(); ctx.roundRect(10, y0, W-20, laneH, 5); ctx.fill(); ctx.stroke();

      ctx.save();
      ctx.beginPath(); ctx.rect(11, y0+1, padL-16, laneH-2); ctx.clip();
      ctx.fillStyle = t.fill;
      ctx.fillRect(11, y0+1, padL-16, laneH-2);
      ctx.fillStyle = '#161412';
      ctx.font = '700 11px "Bricolage Grotesque", sans-serif';
      ctx.fillText(String(plane.label||plane.id).split('(')[0].trim().slice(0,15), 15, y0 + Math.min(16, laneH*0.36));
      ctx.fillStyle = '#6B6259';
      ctx.font = '500 9px "JetBrains Mono", monospace';
      ctx.fillText(`z=${plane.z} · k=${((zRef/Math.max(0.2,plane.z))*kScale).toFixed(2)}x`, 15, y0 + Math.min(29, laneH*0.64));
      if(laneH >= 38){
        const bx = 15, by = y0 + laneH - 15, bw = 54, bh = 12;
        ctx.fillStyle = 'rgba(22, 20, 18, 0.82)';
        ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 2.5); ctx.fill();
        ctx.fillStyle = '#EF9F3A';
        ctx.font = '700 8px "JetBrains Mono", monospace';
        ctx.fillText('+ Parts', bx + 6, by + 9);
        pushHitBox({x: bx, y: by, w: bw, h: bh, zoomPlaneIn: plane.id});
      }
      ctx.restore();
      pushHitBox({x: 11, y: y0 + 1, w: padL - 16, h: Math.max(18, laneH - 17), fi, planeId: plane.id, togglePlane: true});

      ctx.save();
      ctx.beginPath(); ctx.rect(padL, y0+2, trackW, laneH-4); ctx.clip();

      if(N >= 2){
        ctx.save();
        ctx.beginPath();
        const srcW = (S && S.W) || curWorm.W || 480;
        for(let ti = 0; ti < N; ti++){
          const x = padL + (ti / (N - 1)) * trackW;
          let uVal = 0.5;
          if(isChar && curWorm.frames && curWorm.frames[ti] && curWorm.frames[ti].c){
            uVal = curWorm.frames[ti].c[0];
          } else {
            const offT = camOffset(plane.z, ti);
            uVal = 0.5 + (offT.dx / Math.max(120, srcW * 0.75));
          }
          const y = y0 + 6 + Math.max(0.08, Math.min(0.92, uVal)) * (laneH - 12);
          if(ti === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = isChar ? 'rgba(239, 159, 58, 0.55)' : t.stroke;
        ctx.lineWidth = 2.0;
        ctx.stroke();
        ctx.restore();
      }

      const actX = padL + (N>1 ? (fi/(N-1))*trackW : trackW*0.5);
      const actH = Math.max(26, laneH - 6), actW = Math.round(actH * 1.28);

      const nStamps = Math.min(N, 6);
      const celH = Math.max(22, laneH - 10), celW = Math.round(celH * 1.20);
      let lastStampRight = -999;

      for(let sIdx=0; sIdx<nStamps; sIdx++){
        const ti = nStamps===1 ? 0 : Math.round((sIdx/(nStamps-1))*(N-1));
        const cx = padL + (N>1 ? (ti/(N-1))*trackW : trackW*0.5);
        const rx = Math.max(padL+2, Math.min(padL+trackW-celW-2, cx-celW*0.5));
        if(rx < lastStampRight + 4) continue;
        lastStampRight = rx + celW;
        const ry = y0 + (laneH-celH)*0.5;
        ctx.save(); ctx.globalAlpha = vis ? 0.94 : 0.30;
        ctx.fillStyle = '#FBFAF6'; ctx.strokeStyle = '#C9BBA6'; ctx.lineWidth = 1.1;
        ctx.fillRect(rx,ry,celW,celH);
        if(isChar) drawSamCutoutInRect(ctx, curWorm, ti, rx+1, ry+1, celW-2, celH-2, {cropToMask:true, drawOutline:false, drawDoodle:true});
        else drawPlaneObjectsInRect(ctx, plane, ti, rx+1, ry+1, celW-2, celH-2, true);
        ctx.strokeRect(rx,ry,celW,celH);
        ctx.restore();
        pushHitBox({x: rx, y: ry, w: celW, h: celH, fi: ti, planeId: null, togglePlane: false});
      }

      const arx = Math.max(padL+2, Math.min(padL+trackW-actW-2, actX-actW*0.5));
      const ary = y0 + (laneH-actH)*0.5;
      ctx.fillStyle = '#FFFBF4'; ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2.0;
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

  function renderAll109WormsWall(ctx, W, H, fi, N){
    ctx.fillStyle = '#0D0C0A';
    ctx.fillRect(0, 0, W, H);
    const total = WORMS.length || 1;
    const cols = 11;
    const rows = Math.ceil(total / cols);
    const pad = 6, padBot = 24, gap = 3;
    const cw = (W - pad*2 - gap*(cols - 1)) / cols;
    const ch = (H - pad - padBot - gap*(rows - 1)) / rows;
    const uNorm = N > 1 ? fi / (N - 1) : 0;

    WORMS.forEach((w, idx)=>{
      const c = idx % cols;
      const r = Math.floor(idx / cols);
      const cx = pad + c * (cw + gap);
      const cy = pad + r * (ch + gap);
      const isCur = (idx === curIdx);

      ctx.save();
      ctx.fillStyle = isCur ? '#2B2214' : '#161411';
      ctx.strokeStyle = isCur ? '#EF9F3A' : '#332E27';
      ctx.lineWidth = isCur ? 2.0 : 1.0;
      ctx.beginPath();
      ctx.roundRect(cx, cy, cw, ch, 3);
      ctx.fill();
      ctx.stroke();

      ctx.beginPath();
      ctx.rect(cx + 1, cy + 1, cw - 2, ch - 2);
      ctx.clip();

      const dws = w.depth_worms || [];
      for(let i = dws.length - 1; i >= 0; i--){
        const dw = dws[i];
        const tr = dw.track || [];
        if(!tr.length) continue;
        ctx.beginPath();
        for(let ti = 0; ti < tr.length; ti++){
          const tx = cx + 4 + (tr.length > 1 ? (ti / (tr.length - 1)) * (cw - 8) : (cw - 8) * 0.5);
          const ty = cy + 11 + Math.max(0.05, Math.min(0.95, tr[ti][1])) * (ch - 14);
          if(ti === 0) ctx.moveTo(tx, ty); else ctx.lineTo(tx, ty);
        }
        ctx.strokeStyle = dw.role === 'subject' ? '#EF9F3A' : (dw.color || '#6E98D6');
        ctx.lineWidth = dw.role === 'subject' ? 1.6 : 0.85;
        ctx.globalAlpha = dw.role === 'subject' ? 0.95 : 0.45;
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      const wfCount = (w.frames && w.frames.length) || w.n_frames || 1;
      const wFi = Math.min(wfCount - 1, Math.max(0, Math.round(uNorm * (wfCount - 1))));
      const playX = cx + 4 + uNorm * (cw - 8);
      ctx.strokeStyle = isCur ? '#FFFFFF' : 'rgba(239, 159, 58, 0.72)';
      ctx.lineWidth = 1.05;
      ctx.beginPath();
      ctx.moveTo(playX, cy + 10);
      ctx.lineTo(playX, cy + ch - 2);
      ctx.stroke();

      const fr = w.frames && w.frames[wFi];
      if(fr && fr.doodle){
        ctx.strokeStyle = '#FFFDF8';
        ctx.lineWidth = 0.9;
        const dBox = Math.min(cw * 0.35, ch - 12);
        const dx0 = Math.max(cx + 2, Math.min(cx + cw - dBox - 2, playX - dBox * 0.5));
        const dy0 = cy + 10 + (ch - 11 - dBox) * 0.5;
        for(const s of fr.doodle){
          if(!s || s.length < 2) continue;
          ctx.beginPath();
          for(let k = 0; k < s.length; k++){
            const px = dx0 + s[k][0] * dBox;
            const py = dy0 + s[k][1] * dBox;
            if(k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.stroke();
        }
      }

      ctx.fillStyle = isCur ? '#EF9F3A' : '#CFC6B8';
      ctx.font = '700 7.5px "JetBrains Mono", monospace';
      const lbl = `${(w.lot || '').replace('SM-','')} ${(w.title || w.slug || '').slice(0, 7)}`.trim();
      ctx.fillText(lbl, cx + 3, cy + 8.5);
      ctx.restore();

      pushHitBox({x: cx, y: cy, w: cw, h: ch, selectShotIdx: idx});
    });
  }

  function areAllPlanesOn(planes){
    if(soloPlaneId !== null) return false;
    return planes.every(p => planeOn[p.id] !== false);
  }

  function togglePlaneVisibility(pid){
    const planes = getActivePlanes();
    soloPlaneId = null;
    planeOn[pid] = (planeOn[pid] === false) ? true : false;
    const anyVisible = planes.some(p => planeOn[p.id] !== false);
    if(!anyVisible) planeOn = {};
  }

  function renderWorm(fi){
    if(!curWorm) return;
    wormHitBoxes = [];
    hitTransform = {tx: 0, ty: 0, sx: 1, sy: 1};
    const W = cvWorm.width, H = cvWorm.height;
    const ctx = ctxWorm;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#FBFAF6';
    ctx.fillRect(0,0,W,H);
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const planes = getActivePlanes();
    const meta = LENS_META[wormMode] || LENS_META.parallel;
    const lblText = (wormMode === 'all')
      ? 'all 6 lenses simultaneously · click any slice or badge'
      : (wormMode === 'wall')
        ? 'all 109 space-worms live wall · click any worm to select'
        : (wormMode === 'parallel' && parallelSubMode === 'butter')
          ? 'butter loaf (all depth rails × all slices · click any slice)'
          : (wormMode === 'parallel' && parallelSubMode === 'slices')
            ? 'all slices contact sheet (click any slice)'
            : meta.lbl;
    document.getElementById('idxLblWorm').textContent = lblText;
    const visCount = planes.filter(p => isPlaneVisible(p.id)).length;
    const planeTxt = zoomPlaneId
      ? `Plane: ${zoomPlaneId}`
      : ((visCount === planes.length) ? `All ${planes.length} planes` : `${visCount}/${planes.length} planes`);
    document.getElementById('idxLblWormR').textContent = `${planeTxt} · f ${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`;

    const zRef = (S && S.z_ref) || curWorm.z_ref || 2;

    if(wormMode === 'wall'){
      renderAll109WormsWall(ctx, W, H, fi, N);
      return;
    }

    if(wormMode === 'all'){
      const lenses = [
        {id:'parallel', lbl:'1 · 3D Butter'},
        {id:'lanes',    lbl:'2 · Planes'},
        {id:'parts',    lbl:'3 · Parts'},
        {id:'strobe',   lbl:'4 · Trail'},
        {id:'kymo',     lbl:'5 · Graphs'},
        {id:'anatomy',  lbl:'6 · Rig'}
      ];
      const cols = 3, rows = 2;
      const pad = 6, padBot = 24, gap = 5;
      const pw = (W - pad*2 - gap*(cols - 1)) / cols;
      const ph = (H - pad - padBot - gap*(rows - 1)) / rows;
      lenses.forEach((m, idx)=>{
        const c = idx % cols, r = Math.floor(idx / cols);
        const px = pad + c * (pw + gap);
        const py = pad + r * (ph + gap);
        const sx = pw / W, sy = ph / H;

        ctx.save();
        ctx.beginPath();
        ctx.roundRect(px, py, pw, ph, 5);
        ctx.clip();
        ctx.fillStyle = '#FBFAF6';
        ctx.fillRect(px, py, pw, ph);
        ctx.translate(px, py);
        ctx.scale(sx, sy);
        hitTransform = {tx: px, ty: py, sx, sy};
        renderSingleWormLens(ctx, W, H, fi, N, planes, zRef, m.id);
        ctx.restore();

        hitTransform = {tx: 0, ty: 0, sx: 1, sy: 1};
        ctx.strokeStyle = '#161412';
        ctx.lineWidth = 1.3;
        ctx.beginPath();
        ctx.roundRect(px, py, pw, ph, 5);
        ctx.stroke();

        const bx = px + 5, by = py + 4, bw = 92, bh = 15;
        ctx.fillStyle = 'rgba(22, 20, 18, 0.86)';
        ctx.beginPath();
        ctx.roundRect(bx, by, bw, bh, 3);
        ctx.fill();
        ctx.fillStyle = '#EF9F3A';
        ctx.font = '700 9px "JetBrains Mono", monospace';
        ctx.fillText(m.lbl, bx + 5, by + 11);
        pushHitBox({x: bx, y: by, w: bw, h: bh, setMode: m.id});
      });
      return;
    }

    renderSingleWormLens(ctx, W, H, fi, N, planes, zRef, wormMode);
  }

  function drawRackMiniWorm(cv, w, uNorm){
    const c = cv.getContext('2d');
    c.fillStyle = '#FBFAF6';
    c.fillRect(0, 0, 118, 32);
    const dws = w.depth_worms || [];
    for(let i = dws.length - 1; i >= 0; i--){
      const dw = dws[i], tr = dw.track || [];
      if(!tr.length) continue;
      c.beginPath();
      for(let ti = 0; ti < tr.length; ti++){
        const x = 4 + (tr.length > 1 ? (ti / (tr.length - 1)) * 110 : 55);
        const y = 4 + Math.max(0.08, Math.min(0.92, tr[ti][1])) * 24;
        if(ti === 0) c.moveTo(x, y); else c.lineTo(x, y);
      }
      c.strokeStyle = dw.role === 'subject' ? '#EF9F3A' : (dw.color || '#8A6114');
      c.lineWidth = dw.role === 'subject' ? 2.4 : 1.25;
      c.globalAlpha = dw.role === 'subject' ? 0.95 : 0.45;
      c.stroke();
    }
    c.globalAlpha = 1;
    const nf = (w.frames && w.frames.length) || 1;
    const actQ = Math.min(nf - 1, Math.max(0, Math.round((uNorm || 0) * (nf - 1))));
    const qList = [0, actQ, nf - 1];
    for(const q of qList){
      const fr = w.frames && w.frames[q];
      if(!fr || !fr.doodle) continue;
      const xOff = (nf > 1 ? (q / (nf - 1)) : 0.5) * 90;
      c.strokeStyle = (q === actQ) ? '#161412' : 'rgba(138, 74, 5, 0.55)';
      c.lineWidth = (q === actQ) ? 1.15 : 0.85;
      for(const s of fr.doodle){
        if(!s || s.length < 2) continue;
        c.beginPath();
        for(let k = 0; k < s.length; k++){
          const px = 3 + xOff + s[k][0] * 24, py = 2 + s[k][1] * 28;
          if(k === 0) c.moveTo(px, py); else c.lineTo(px, py);
        }
        c.stroke();
      }
    }
    const pxPlay = 4 + (uNorm || 0) * 110;
    c.strokeStyle = '#EF9F3A';
    c.lineWidth = 1.4;
    c.beginPath();
    c.moveTo(pxPlay, 1);
    c.lineTo(pxPlay, 31);
    c.stroke();
  }

  function syncRackMiniWorms(uNorm){
    for(let i = rackMiniWorms.length - 1; i >= 0; i--){
      const item = rackMiniWorms[i];
      if(!item.cv.isConnected){
        rackMiniWorms.splice(i, 1);
        continue;
      }
      drawRackMiniWorm(item.cv, item.w, uNorm);
    }
  }

  function updateConditionalState(){
    const planes = getActivePlanes();
    const allActive = areAllPlanesOn(planes);
    if(showAllPlanesBtn) showAllPlanesBtn.style.display = allActive ? 'none' : '';
    if(zoomCrumbBtn){
      const hasZoom = (zoomPlaneId !== null || selectedPartId !== null);
      zoomCrumbBtn.style.display = hasZoom ? '' : 'none';
      if(selectedPartId !== null){
        zoomCrumbBtn.textContent = zoomPlaneId ? `<- Plane [${zoomPlaneId}]` : '<- All Parts';
      } else if(zoomPlaneId !== null){
        zoomCrumbBtn.textContent = '<- All Planes';
      }
    }
    if(resetBtn){
      const isModified = (f !== 0) || !allActive || (view !== 'composite')
        || (Math.abs(kScale - 1.0) > 0.01) || (explodeAmt > 0.01) || (zoomPlaneId !== null) || (selectedPartId !== null);
      resetBtn.style.display = isModified ? '' : 'none';
    }
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
    updateConditionalState();
    syncRackMiniWorms(N > 1 ? f / (N - 1) : 0);
  }

  function buildPlanesAndTicks(){
    planesEl.innerHTML = '';
    ticksEl.innerHTML = '';
    if(!curWorm) return;
    const planes = getActivePlanes();
    const allActive = areAllPlanesOn(planes) && zoomPlaneId === null;

    const allBtn = document.createElement('button');
    allBtn.type = 'button';
    allBtn.className = 'w-plane-pill';
    allBtn.setAttribute('aria-pressed', allActive ? 'true' : 'false');
    allBtn.textContent = `All (${planes.length})`;
    allBtn.addEventListener('click', ()=>{
      soloPlaneId = null;
      zoomPlaneId = null;
      selectedPartId = null;
      planeOn = {};
      buildPlanesAndTicks();
      renderAll();
    });
    planesEl.appendChild(allBtn);

    planes.slice().reverse().forEach(p=>{
      const vis = isPlaneVisible(p.id);
      const isZoomed = (zoomPlaneId === p.id);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'w-plane-pill' + (p.id === 'char' ? ' subj' : '');
      btn.setAttribute('aria-pressed', vis ? 'true' : 'false');
      btn.title = 'Click to toggle plane visibility · Double-click (or Shift-click) to zoom into this plane’s parts';
      btn.textContent = `${isZoomed ? '[*] ' : ''}${p.label} · z=${p.z}`;
      btn.addEventListener('click', (e)=>{
        if(e.shiftKey || wormMode === 'parts'){
          zoomPlaneId = (zoomPlaneId === p.id) ? null : p.id;
          selectedPartId = null;
          planeOn[p.id] = true;
          buildPlanesAndTicks();
          renderAll();
          return;
        }
        togglePlaneVisibility(p.id);
        buildPlanesAndTicks();
        renderAll();
      });
      btn.addEventListener('dblclick', ()=>{
        zoomPlaneId = (zoomPlaneId === p.id) ? null : p.id;
        selectedPartId = null;
        planeOn[p.id] = true;
        buildPlanesAndTicks();
        renderAll();
      });
      planesEl.appendChild(btn);
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
    document.getElementById('idxFullWormsLink').href = `pages/worms.html?shot=${encodeURIComponent(curWorm.shot_id)}`;

    const hasMultiVar = Boolean(curWorm.has_sam_shot || curWorm.has_redraw_shot || curWorm.has_integrated);
    if(varWrap) varWrap.style.display = hasMultiVar ? '' : 'none';
    varSam.style.display = curWorm.has_sam_shot ? '' : 'none';
    varRedraw.style.display = curWorm.has_redraw_shot ? '' : 'none';
    varInt.style.display = curWorm.has_integrated ? '' : 'none';

    planeOn = {};
    soloPlaneId = null;
    zoomPlaneId = null;
    selectedPartId = null;
    hoveredPartId = null;
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
    for(let i=0;i<(worm.n_frames||1);i++) getFrameImg(worm, i);
    renderAll();
  }

  function eventToCanvasPt(cv, e){
    const rect = cv.getBoundingClientRect();
    const clientX = (e.changedTouches && e.changedTouches.length) ? e.changedTouches[0].clientX : ((e.touches && e.touches.length) ? e.touches[0].clientX : e.clientX);
    const clientY = (e.changedTouches && e.changedTouches.length) ? e.changedTouches[0].clientY : ((e.touches && e.touches.length) ? e.touches[0].clientY : e.clientY);
    return {
      x: ((clientX - rect.left) / Math.max(1, rect.width)) * cv.width,
      y: ((clientY - rect.top) / Math.max(1, rect.height)) * cv.height,
      clientX,
      clientY
    };
  }

  function findWormHit(pt){
    for(let i = wormHitBoxes.length - 1; i >= 0; i--){
      const b = wormHitBoxes[i];
      if(pt.x >= b.x && pt.x <= b.x + b.w && pt.y >= b.y && pt.y <= b.y + b.h){
        return b;
      }
    }
    return null;
  }

  function findStageHit(pt){
    let best = null;
    let bestArea = Infinity;
    for(let i = stageHitBoxes.length - 1; i >= 0; i--){
      const b = stageHitBoxes[i];
      if(pt.x >= b.x && pt.x <= b.x + b.w && pt.y >= b.y && pt.y <= b.y + b.h){
        const area = b.w * b.h;
        if(area < bestArea){
          bestArea = area;
          best = b;
        }
      }
    }
    return best;
  }

  // Click into any slice OR drag horizontally to scrub like slicing butter
  let isScrubbing = false;
  let wormDownPt = null;
  let wormDragged = false;

  function scrubFromWorm(e){
    if(!curWorm) return;
    if(wormMode === 'parallel' && parallelSubMode === 'slices'){
      const pt = eventToCanvasPt(cvWorm, e);
      const hit = findWormHit(pt);
      if(hit && hit.fi !== undefined && hit.fi !== null && hit.fi !== f){
        f = hit.fi;
        getFrameImg(curWorm, f);
        renderAll();
      }
      return;
    }
    const pt = eventToCanvasPt(cvWorm, e);
    const xRel = pt.x / Math.max(1, cvWorm.width);
    let padLFrac = 38 / cvWorm.width, padRFrac = 28 / cvWorm.width;
    if(wormMode === 'parallel'){ padLFrac = 0.08; padRFrac = 0.08; }
    else if(wormMode === 'lanes' || wormMode === 'kymo'){ padLFrac = 128 / cvWorm.width; padRFrac = 16 / cvWorm.width; }
    else if(wormMode === 'parts'){ padLFrac = 0.48; padRFrac = 0.03; }
    else if(wormMode === 'strobe'){ padLFrac = 16 / cvWorm.width; padRFrac = 16 / cvWorm.width; }
    else if(wormMode === 'anatomy'){ padLFrac = 130 / cvWorm.width; padRFrac = 24 / cvWorm.width; }
    const u = Math.max(0, Math.min(1, (xRel - padLFrac) / Math.max(0.1, 1 - padLFrac - padRFrac)));
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    const nf = Math.round(u * Math.max(0, N - 1));
    if(nf !== f){ f = nf; getFrameImg(curWorm, f); renderAll(); }
  }
  cvWorm.addEventListener('pointerdown', (e)=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.textContent = 'Play';
    isScrubbing = true;
    wormDragged = false;
    wormDownPt = eventToCanvasPt(cvWorm, e);
    cvWorm.setPointerCapture(e.pointerId);
    const hit = findWormHit(wormDownPt);
    if(!hit){
      scrubFromWorm(e);
    }
  });
  cvWorm.addEventListener('pointermove', (e)=>{
    const pt = eventToCanvasPt(cvWorm, e);
    if(!isScrubbing){
      const hit = findWormHit(pt);
      cvWorm.style.cursor = hit ? 'pointer' : 'ew-resize';
      const newHov = (hit && hit.selectPartId && hit.selectPartId !== '__NONE__') ? hit.selectPartId : null;
      if(newHov !== hoveredPartId){
        hoveredPartId = newHov;
        renderAll();
      }
      return;
    }
    if(wormDownPt && Math.hypot(pt.clientX - wormDownPt.clientX, pt.clientY - wormDownPt.clientY) > 6){
      wormDragged = true;
    }
    if(wormDragged) scrubFromWorm(e);
  });
  cvWorm.addEventListener('pointerleave', ()=>{
    if(hoveredPartId !== null){
      hoveredPartId = null;
      renderAll();
    }
  });
  cvWorm.addEventListener('pointerup', (e)=>{
    if(isScrubbing && !wormDragged && wormDownPt){
      const pt = eventToCanvasPt(cvWorm, e);
      const hit = findWormHit(pt) || findWormHit(wormDownPt);
      if(hit){
        if(hit.selectShotIdx !== undefined){
          selectShot(hit.selectShotIdx);
          isScrubbing = false;
          wormDownPt = null;
          return;
        }
        if(hit.zoomPlaneOut){
          zoomPlaneId = null;
          selectedPartId = null;
          buildPlanesAndTicks();
          renderAll();
          isScrubbing = false;
          wormDownPt = null;
          return;
        }
        if(hit.zoomPlaneIn){
          zoomPlaneId = hit.zoomPlaneIn;
          selectedPartId = null;
          planeOn[hit.zoomPlaneIn] = true;
          buildPlanesAndTicks();
          renderAll();
          isScrubbing = false;
          wormDownPt = null;
          return;
        }
        if(hit.selectPartId){
          selectedPartId = (hit.selectPartId === '__NONE__') ? null : hit.selectPartId;
          if(hit.setMode){
            wormMode = hit.setMode;
            document.querySelectorAll('[data-idxwmode]').forEach(b=>b.setAttribute('aria-pressed', b.dataset.idxwmode===wormMode?'true':'false'));
          }
          renderAll();
          isScrubbing = false;
          wormDownPt = null;
          return;
        }
        if(hit.setMode){
          wormMode = hit.setMode;
          document.querySelectorAll('[data-idxwmode]').forEach(b=>b.setAttribute('aria-pressed', b.dataset.idxwmode===wormMode?'true':'false'));
          if(parTools) parTools.style.display = (wormMode === 'parallel' || wormMode === 'all') ? '' : 'none';
          renderAll();
          isScrubbing = false;
          wormDownPt = null;
          return;
        }
        if(hit.togglePlane && hit.planeId){
          togglePlaneVisibility(hit.planeId);
          buildPlanesAndTicks();
        }
        if(hit.fi !== undefined && hit.fi !== null){
          f = hit.fi;
          getFrameImg(curWorm, f);
        }
        renderAll();
      } else {
        scrubFromWorm(e);
      }
    }
    isScrubbing = false;
    wormDownPt = null;
  });
  cvWorm.addEventListener('pointercancel', ()=>{ isScrubbing = false; wormDownPt = null; });

  cvStage.addEventListener('pointermove', (e)=>{
    const pt = eventToCanvasPt(cvStage, e);
    const hit = findStageHit(pt);
    cvStage.style.cursor = hit ? 'pointer' : 'default';
    const newHov = hit ? hit.partId : null;
    if(newHov !== hoveredPartId){
      hoveredPartId = newHov;
      renderAll();
    }
  });
  cvStage.addEventListener('pointerleave', ()=>{
    if(hoveredPartId !== null){
      hoveredPartId = null;
      renderAll();
    }
  });
  cvStage.addEventListener('click', (e)=>{
    if(window.innerWidth <= 860 && mobPipMode) return;
    const pt = eventToCanvasPt(cvStage, e);
    const hit = findStageHit(pt);
    if(hit && hit.partId){
      selectedPartId = (selectedPartId === hit.partId) ? null : hit.partId;
      if(selectedPartId && wormMode !== 'parts'){
        wormMode = 'parts';
        document.querySelectorAll('[data-idxwmode]').forEach(b=>b.setAttribute('aria-pressed', b.dataset.idxwmode==='parts'?'true':'false'));
        if(parTools) parTools.style.display = 'none';
      }
      renderAll();
    }
  });

  if(zoomCrumbBtn){
    zoomCrumbBtn.addEventListener('click', ()=>{
      if(selectedPartId !== null) selectedPartId = null;
      else if(zoomPlaneId !== null) zoomPlaneId = null;
      buildPlanesAndTicks();
      renderAll();
    });
  }
  if(kScaleRange){
    kScaleRange.addEventListener('input', ()=>{
      kScale = (parseInt(kScaleRange.value, 10) || 0) / 100;
      if(kScaleVal) kScaleVal.textContent = kScale.toFixed(1) + 'x';
      renderAll();
    });
  }
  if(explodeRange){
    explodeRange.addEventListener('input', ()=>{
      explodeAmt = (parseInt(explodeRange.value, 10) || 0) / 100;
      if(explodeVal) explodeVal.textContent = Math.round(explodeAmt * 100) + '%';
      renderAll();
    });
  }

  document.querySelectorAll('[data-idxwmode]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      wormMode = btn.dataset.idxwmode;
      document.querySelectorAll('[data-idxwmode]').forEach(b=>b.setAttribute('aria-pressed', b===btn?'true':'false'));
      if(parTools) parTools.style.display = (wormMode === 'parallel' || wormMode === 'all') ? '' : 'none';
      if(curWorm && (wormMode === 'strobe' || wormMode === 'kymo' || wormMode === 'parallel' || wormMode === 'all')){
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
      parThemeBtn.textContent = parallelDark ? 'Dark' : 'Paper';
      renderAll();
    });
  }
  if(showAllPlanesBtn){
    showAllPlanesBtn.addEventListener('click', ()=>{
      soloPlaneId = null;
      zoomPlaneId = null;
      selectedPartId = null;
      planeOn = {};
      buildPlanesAndTicks();
      renderAll();
    });
  }
  if(resetBtn){
    resetBtn.addEventListener('click', ()=>{
      playing = false;
      playBtn.setAttribute('aria-pressed', 'false');
      playBtn.textContent = 'Play';
      f = 0;
      soloPlaneId = null;
      zoomPlaneId = null;
      selectedPartId = null;
      hoveredPartId = null;
      planeOn = {};
      kScale = 1.0;
      explodeAmt = 0.0;
      if(kScaleRange) kScaleRange.value = '100';
      if(kScaleVal) kScaleVal.textContent = '1.0x';
      if(explodeRange) explodeRange.value = '0';
      if(explodeVal) explodeVal.textContent = '0%';
      view = 'composite';
      document.querySelectorAll('[data-idxview]').forEach(b=>b.setAttribute('aria-pressed', b.dataset.idxview==='composite'?'true':'false'));
      buildPlanesAndTicks();
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
  const lockScreenBtn = document.getElementById('idxLockScreenBtn');
  const heroStage = document.getElementById('shmWormsHero');
  let isLockedFullscreen = false;
  function setLockedFullscreen(on){
    isLockedFullscreen = Boolean(on);
    if(heroStage) heroStage.classList.toggle('locked-fullscreen', isLockedFullscreen);
    document.body.classList.toggle('worms-no-scroll', isLockedFullscreen);
    if(lockScreenBtn){
      lockScreenBtn.setAttribute('aria-pressed', String(isLockedFullscreen));
      lockScreenBtn.textContent = isLockedFullscreen ? 'Exit No-Scroll' : 'No-Scroll';
    }
    renderAll();
  }
  if(lockScreenBtn){
    lockScreenBtn.addEventListener('click', ()=> setLockedFullscreen(!isLockedFullscreen));
  }
  if(new URLSearchParams(window.location.search).get('noscroll') === '1'){
    setLockedFullscreen(true);
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
  playBtn.addEventListener('click', ()=>{
    playing = !playing;
    playBtn.setAttribute('aria-pressed', String(playing));
    playBtn.textContent = playing ? 'Stop' : 'Play';
    if(playing){ lastTick = performance.now(); requestAnimationFrame(loop); }
  });
  document.getElementById('idxStepPrev').addEventListener('click', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.textContent = 'Play';
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm ? curWorm.n_frames : 1);
    f = (f - 1 + N) % N; renderAll();
  });
  document.getElementById('idxStepNext').addEventListener('click', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.textContent = 'Play';
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm ? curWorm.n_frames : 1);
    f = (f + 1) % N; renderAll();
  });
  scrub.addEventListener('input', ()=>{
    playing = false; playBtn.setAttribute('aria-pressed','false'); playBtn.textContent = 'Play';
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
      box.title = 'Click or scrub this Space-Worm';
      const nP = (w.depth_worms && w.depth_worms.length) || (w.planes && w.planes.length) || 2;
      box.innerHTML = `
        <canvas width="118" height="32"></canvas>
        <div class="mini-worm-meta">
          <b>${nP} Planes · ${w.n_frames}f</b>
          <span>Explore worm</span>
        </div>
      `;
      const cv = box.querySelector('canvas');
      drawRackMiniWorm(cv, w, 0);
      rackMiniWorms.push({cv, w});

      cv.addEventListener('pointermove', (e)=>{
        const r = cv.getBoundingClientRect();
        const u = Math.max(0, Math.min(1, (e.clientX - r.left) / Math.max(1, r.width)));
        drawRackMiniWorm(cv, w, u);
      });

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
