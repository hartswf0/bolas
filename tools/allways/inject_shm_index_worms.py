#!/usr/bin/env python3
"""
Inject Secondhand Motion's native-styled Multiplane Time-Worm Scrubber Studio (#shmWormsHero)
and warm-paper mini-worm Rack badges into /Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo/index.html.
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
  margin-bottom:10px;
}
.w-seg{
  display:inline-flex;border:1.5px solid var(--ink);border-radius:6px;overflow:hidden;
  background:var(--card);flex-wrap:wrap;
}
.w-seg button{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11.5px;
  padding:4px 9px;border:0;background:transparent;color:var(--ink);cursor:pointer;
  border-right:1px solid var(--rule);
}
.w-seg button:last-child{border-right:0}
.w-seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.w-btn{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:11.5px;
  padding:4px 9px;border:1.5px solid var(--ink);border-radius:6px;
  background:var(--card);color:var(--ink);cursor:pointer;text-decoration:none;
  display:inline-flex;align-items:center;gap:4px;
}
.w-btn:hover{border-color:var(--tag)}
.w-btn[aria-pressed="true"]{background:var(--tag);color:#161412;border-color:var(--ink)}
.w-select{
  font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:12.5px;
  padding:4px 9px;border:1.5px solid var(--ink);border-radius:6px;
  background:var(--card);color:var(--ink);cursor:pointer;max-width:310px;
}
.w-screens{
  display:grid;grid-template-columns:1.22fr 1fr;gap:12px;align-items:stretch;
}
@media (max-width:900px){
  .w-screens{grid-template-columns:1fr}
}
.w-screen{
  position:relative;background:var(--cel);border:1.5px solid var(--ink);
  border-radius:6px;overflow:hidden;
}
.w-canvas-wrap{
  position:relative;width:100%;aspect-ratio:4/3;background:var(--cel);
  touch-action:none;user-select:none;
}
.w-canvas-wrap.worm-scrub-area{cursor:ew-resize}
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
.w-controls{
  display:grid;grid-template-columns:auto auto 1fr auto;gap:10px;align-items:center;
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
  display:inline-flex;align-items:center;gap:4px;
}
.w-planes label.subj{border-color:var(--tag);background:var(--tag-soft);color:var(--tag-ink);font-weight:600}
.w-planes label.soloed{outline:2px solid var(--ink)}
.w-planes input{accent-color:var(--tag);margin:0}

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

<section class="worms-stage" id="shmWormsHero" aria-label="Multiplane Time-Worms Scrubber">
  <div class="worms-head">
    <div>
      <h2>
        <span class="lot-pill" id="idxWormLot">SM-0004</span>
        <span id="idxWormTitle">Giraffe Walks Past — Multiplane Time-Worm Scrubber</span>
      </h2>
      <div style="font-size:12.5px;color:var(--muted);margin-top:2px" id="idxWormSub">
        Prelinger Archives · Wonderful World (Part II) · Drag horizontally across the worm on the left to scrub frame-by-frame through every depth plane.
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
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
      <div class="w-seg" role="group" aria-label="Worm scrubber mode">
        <button type="button" data-idxwmode="lanes" aria-pressed="true">Plane Worms (Scrub)</button>
        <button type="button" data-idxwmode="tunnel" aria-pressed="false">3D Cutout Worm</button>
        <button type="button" data-idxwmode="box" aria-pressed="false">Planes in Depth</button>
      </div>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
      <div class="w-seg" role="group" aria-label="Stage view">
        <button type="button" data-idxview="cartoon" aria-pressed="false">Cartoon</button>
        <button type="button" data-idxview="composite" aria-pressed="true">Over footage</button>
        <button type="button" data-idxview="cutout" aria-pressed="false">SAM Cutout</button>
        <button type="button" data-idxview="footage" aria-pressed="false">Footage</button>
        <button type="button" data-idxview="masks" aria-pressed="false">Silhouettes</button>
      </div>
      <button type="button" class="w-btn" id="idxBoilBtn" aria-pressed="true">Boil</button>
      <button type="button" class="w-btn" id="idxCelBtn" aria-pressed="true">Paint cels</button>
    </div>
  </div>

  <div class="w-screens">
    <div class="w-screen">
      <div class="w-canvas-wrap worm-scrub-area">
        <canvas id="idxCvWorm" width="580" height="435"></canvas>
        <span class="w-lbl" id="idxLblWorm">disentangled plane worms · drag horizontally to scrub f</span>
        <span class="w-lbl-r" id="idxLblWormR">6 planes · f 01/33</span>
      </div>
    </div>
    <div class="w-screen">
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
    <div class="w-scrub">
      <div class="w-ticks" id="idxTicks"></div>
      <input type="range" id="idxScrub" min="0" max="32" value="0" step="1" aria-label="Scrub frame">
    </div>
    <div class="w-readout" id="idxReadout">f 01 / 33</div>
  </div>

  <div class="w-foot">
    <span id="idxCaption">Drag horizontally across the left worm canvas to scrub through the SAM cutouts &amp; multiplane drawings.</span>
    <div class="w-planes" id="idxPlanes"></div>
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

  let WORMS = [];
  let curIdx = 0;
  let curWorm = null;
  let S = null;
  let shotCache = new Map();
  let frameImgCache = new Map();

  let wormMode = 'lanes';
  let view = 'composite';
  let boilOn = true;
  let celOn = true;
  let playing = false;
  let f = 0;
  let lastTick = 0;
  let planeOn = {};
  let soloPlaneId = null;

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
    const o = Object.assign({cropToMask:false, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true}, opts||{});
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
        ctx.strokeStyle = '#161412';
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
        ctx.strokeStyle = '#161412';
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
    document.getElementById('idxLblWormR').textContent = `${planes.length} planes · f ${String(fi+1).padStart(2,'0')}/${String(N).padStart(2,'0')}`;

    const zRef = (S && S.z_ref) || curWorm.z_ref || 2;
    if(wormMode === 'tunnel'){
      const padL=38, padR=28, padT=34, padB=28;
      const availW = W-padL-padR, availH = H-padT-padB;
      const step = Math.max(1, Math.floor(N/8));
      const sliceW = Math.min(110, availW*0.24), sliceH = Math.round(sliceW*0.78);
      for(let ti=0; ti<N; ti+=step){
        if(ti===fi) continue;
        const u = N>1 ? ti/(N-1) : 0.5;
        const fr = (curWorm.frames && curWorm.frames[ti]) ? curWorm.frames[ti] : {c:[0.5,0.5]};
        const rx = padL + u*availW - sliceW*0.5, ry = padT + (fr.c?fr.c[1]:0.5)*availH - sliceH*0.5;
        ctx.save(); ctx.globalAlpha = 0.6;
        ctx.fillStyle = '#FBFAF6'; ctx.strokeStyle = '#BFAF97';
        ctx.fillRect(rx,ry,sliceW,sliceH); ctx.strokeRect(rx,ry,sliceW,sliceH);
        drawSamCutoutInRect(ctx, curWorm, ti, rx+2, ry+2, sliceW-4, sliceH-4, {cropToMask:true, drawOutline:true, outlineColor:'#8A4A05', drawDoodle:true});
        ctx.restore();
      }
      const uAct = N>1 ? fi/(N-1) : 0.5;
      const frAct = (curWorm.frames && curWorm.frames[fi]) ? curWorm.frames[fi] : {c:[0.5,0.5]};
      const actW = Math.min(148, availW*0.32), actH = Math.round(actW*0.78);
      const ax = Math.max(padL, Math.min(padL+availW-actW, padL+uAct*availW-actW*0.5));
      const ay = Math.max(padT, Math.min(padT+availH-actH, padT+(frAct.c?frAct.c[1]:0.5)*availH-actH*0.5));
      ctx.fillStyle = '#FFFBF4'; ctx.strokeStyle = '#EF9F3A'; ctx.lineWidth = 2.4;
      ctx.fillRect(ax,ay,actW,actH);
      drawSamCutoutInRect(ctx, curWorm, fi, ax+2, ay+2, actW-4, actH-4, {cropToMask:true, drawOutline:true, outlineColor:'#EF9F3A', drawDoodle:true});
      ctx.strokeRect(ax,ay,actW,actH);
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

    // Default: Disentangled Plane Worms ('lanes')
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

  async function selectShot(idx){
    if(idx < 0 || idx >= WORMS.length) return;
    curIdx = idx;
    curWorm = WORMS[idx];
    S = null;
    f = 0;
    sel.value = String(idx);
    document.getElementById('idxWormLot').textContent = curWorm.lot || 'SM-SHOT';
    document.getElementById('idxWormTitle').textContent = `${curWorm.title || curWorm.slug} — Multiplane Time-Worm Scrubber`;
    document.getElementById('idxWormSub').textContent =
      `Prelinger Archives · ${curWorm.source_title}${curWorm.source_year ? ' ('+curWorm.source_year+')' : ''} · ${curWorm.n_frames} frames @ ${curWorm.fps} fps · Drag horizontally across the left worm canvas to scrub.`;
    document.getElementById('idxFullWormsLink').href = `pages/worms.html?shot=${encodeURIComponent(curWorm.shot_id)}`;

    planeOn = {};
    soloPlaneId = null;
    buildPlanesAndTicks();
    renderAll();

    const relUrl = `shots/${curWorm.shot_id}/shot.json`;
    if(shotCache.has(relUrl)){
      S = shotCache.get(relUrl);
      onReady(curWorm);
      return;
    }
    try{
      const res = await fetch(relUrl);
      if(res.ok){
        const data = await res.json();
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
        if(curWorm === WORMS[idx]){ S = data; onReady(curWorm); }
      }
    }catch(e){}
  }

  function onReady(worm){
    const W = (S && S.W) || worm.W || 480;
    const H = (S && S.H) || worm.H || 360;
    const fps = (S && S.fps) || worm.fps || 12;
    document.getElementById('idxLblStageR').textContent = `${W}×${H} · ${fps} fps`;
    buildPlanesAndTicks();
    for(let i=0;i<Math.min(worm.n_frames||1, 6);i++) getFrameImg(worm, i);
    renderAll();
  }

  // Horizontal worm scrubbing on #idxCvWorm
  let isScrubbing = false;
  function scrubFromWorm(e){
    if(!curWorm) return;
    const rect = cvWorm.getBoundingClientRect();
    const clientX = (e.touches && e.touches.length) ? e.touches[0].clientX : e.clientX;
    const xRel = (clientX - rect.left) / Math.max(1, rect.width);
    const padLFrac = (wormMode === 'lanes') ? (114 / cvWorm.width) : (38 / cvWorm.width);
    const padRFrac = (wormMode === 'lanes') ? (14 / cvWorm.width)  : (28 / cvWorm.width);
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
      renderAll();
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
    const fps = (S && S.fps) || curWorm.fps || 12;
    const N = (S && S.cast && S.cast.frames) ? S.cast.frames.length : (curWorm.n_frames || 1);
    if(now - lastTick >= 1000 / fps){
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
      box.title = 'Click to scrub this Multiplane Time-Worm at the top of the page';
      const nP = (w.depth_worms && w.depth_worms.length) || (w.planes && w.planes.length) || 2;
      box.innerHTML = `
        <canvas width="118" height="32"></canvas>
        <div class="mini-worm-meta">
          <b>${nP} Planes · ${w.n_frames}f</b>
          <span>Scrub worm &#8593;</span>
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
        opt.textContent = `${w.lot ? w.lot + ' · ' : ''}${w.title || w.slug} (${nP} planes · ${w.n_frames}f)`;
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

    # Remove old dark-mode script tail if present
    old_js_marker = "/* === 4D SPATIOTEMPORAL TIME-WORM STUDIO & RACK CARD INTEGRATION === */"
    if old_js_marker in html:
        js_idx = html.index(old_js_marker)
        html = html[:js_idx].rstrip() + "\n</script>\n"

    # Update nav text if needed
    html = html.replace("Time Worms (108)", "Worms (109)")

    old_start = "<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO (108 TRACKED SHOTS) -->"
    old_end   = "<!-- END TIME-WORM STUDIO -->"

    if START_MARKER in html and END_MARKER in html:
        s_idx = html.index(START_MARKER)
        e_idx = html.index(END_MARKER) + len(END_MARKER)
        html = html[:s_idx] + INJECT_BLOCK + html[e_idx:]
    elif old_start in html and old_end in html:
        s_idx = html.index(old_start)
        e_idx = html.index(old_end) + len(old_end)
        html = html[:s_idx] + INJECT_BLOCK + html[e_idx:]
    else:
        target = '<div class="intro">'
        if target in html:
            t_idx = html.index(target)
            html = html[:t_idx] + INJECT_BLOCK + "\n\n" + html[t_idx:]
        else:
            raise RuntimeError("Could not find injection point in index.html")

    with open(SHM_INDEX, "w") as f:
        f.write(html)
    print(f"Updated {SHM_INDEX} ({os.path.getsize(SHM_INDEX) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
