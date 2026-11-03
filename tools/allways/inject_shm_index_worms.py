#!/usr/bin/env python3
"""
Injects the Zero-Scroll, Mobile-First Multi-Plane & Cutout 4D Spatiotemporal Worm Studio
AT THE VERY TOP of https://hartswf0.github.io/secondhand-motion/ (index.html), BEFORE .intro,
so opening the page on mobile shows the Visual Depth Layer Cards, 3D Cutout Worm / 3D Multiplane
Cel Stack, and Unobstructed 2D SAM Video Cutout Stage immediately at y=0 with ZERO vertical scrolling!
"""

import os
import re

SHM_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo"
INDEX_PATH = os.path.join(SHM_ROOT, "index.html")


STUDIO_HTML = """
<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO (108 TRACKED SHOTS) -->
<section id="time-worms-studio" aria-labelledby="tw-h" style="border:2px solid var(--ink);border-radius:10px;background:#080a10;color:#f3f5fa;padding:6px 8px;gap:5px;margin-top:8px;">
  <style>
    @media (max-width:760px) {
      .wrap { gap:14px !important; }
      .sm-head { padding:6px 0 !important; gap:4px 10px !important; }
      .sm-head nav { font-size:12px !important; gap:2px 10px !important; }
    }
    #time-worms-studio .tw-row { display:flex; align-items:center; justify-content:space-between; gap:5px; flex-wrap:wrap; }
    #time-worms-studio .tw-btn { background:#1a2234; color:#f3f5fa; border:1px solid #2b3550; border-radius:5px; padding:3px 7px; font:700 10.5px var(--mono); cursor:pointer; white-space:nowrap; }
    #time-worms-studio .tw-btn[aria-pressed="true"], #time-worms-studio .tw-btn.gold { background:#ffd166; color:#080a10; border-color:#ffd166; }

    /* Row 2: Live Visual Depth Layer Cards (Shows what is inside each depth layer!) */
    #time-worms-studio .tw-depth-bar { display:flex; align-items:stretch; gap:5px; overflow-x:auto; padding:3px 0; scrollbar-width:none; -webkit-overflow-scrolling:touch; }
    #time-worms-studio .tw-depth-bar::-webkit-scrollbar { display:none; }
    #time-worms-studio .tw-lcard { flex:0 0 104px; background:#121723; border:1.5px solid #252f45; border-radius:6px; padding:3px 4px; cursor:pointer; display:flex; flex-direction:column; gap:2px; opacity:0.48; transition:opacity 0.12s, border-color 0.12s; }
    #time-worms-studio .tw-lcard.active { opacity:1; background:#171f30; }
    #time-worms-studio .tw-lcard.solo { opacity:1; background:rgba(255,209,102,0.14); box-shadow:0 0 0 1px #ffd166; }
    #time-worms-studio .tw-lcard-h { font:700 9.5px var(--mono); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    #time-worms-studio .tw-lcard canvas { width:100%; height:30px; display:block; background:#06080e; border-radius:3px; border:1px solid rgba(255,255,255,0.07); }
    #time-worms-studio .tw-lcard-sub { font:500 9px var(--sans); color:#8e99b0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

    /* Side-by-side even on mobile so ZERO vertical scroll is needed! */
    #time-worms-studio .tw-grid { display:grid; grid-template-columns:1.22fr 0.78fr; gap:5px; }
    #time-worms-studio .tw-grid.full3d { grid-template-columns:1fr; }
    #time-worms-studio .tw-grid.full3d .p2d { display:none; }
    #time-worms-studio .tw-pane { position:relative; height:225px; background:#04060a; border:1px solid #242d42; border-radius:6px; overflow:hidden; }
    @media (max-width: 760px) {
      #time-worms-studio .tw-pane { height:186px; }
    }
    /* Built-in horizontal swipe strip of all 108 Multi-Plane Worms */
    #time-worms-studio .tw-strip { display:flex; gap:5px; overflow-x:auto; padding:3px 0 1px; scrollbar-width:none; -webkit-overflow-scrolling:touch; }
    #time-worms-studio .tw-strip::-webkit-scrollbar { display:none; }
    #time-worms-studio .tw-tile { flex:0 0 92px; background:#111622; border:1px solid #242d42; border-radius:5px; padding:3px; cursor:pointer; }
    #time-worms-studio .tw-tile.active { border-color:#ffd166; background:rgba(255,209,102,0.1); }
    #time-worms-studio .tw-tile canvas { width:100%; height:32px; display:block; background:#04060a; border-radius:3px; }
    #time-worms-studio .tw-tile-t { font:700 9.5px var(--sans); color:#f3f5fa; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:2px; }
  </style>

  <!-- Row 1: Compact Shot Selector + View Mode -->
  <div class="tw-row">
    <div style="display:flex;align-items:center;gap:4px;flex:1;min-width:140px;">
      <button type="button" class="tw-btn" id="twPrevBtn">◀</button>
      <button type="button" class="tw-btn gold" id="twPlayPause">▶</button>
      <select id="twSelect" style="flex:1;min-width:95px;background:#080a10;color:#f3f5fa;border:1px solid #2b3550;border-radius:5px;padding:3px 5px;font:700 11px var(--sans);" aria-label="Select tracked shot">
        <option>Loading 108 multiplane cutout worms...</option>
      </select>
      <button type="button" class="tw-btn" id="twNextBtn">▶</button>
    </div>
    <div style="display:flex;gap:3px;align-items:center;" id="twModeBtns">
      <button type="button" class="tw-btn" data-wmode="orbit3d" aria-pressed="true" title="3D Spatiotemporal Cutout Worm">Cutout Worm</button>
      <button type="button" class="tw-btn" data-wmode="box3d" aria-pressed="false" title="3D Multiplane Cel Stack (like giraffe-walks-past)">3D Planes</button>
      <button type="button" class="tw-btn" data-wmode="lanes" aria-pressed="false" title="Horizontal Multiplane Swimlanes">Z×τ</button>
      <button type="button" class="tw-btn" id="twFull3dBtn" aria-pressed="false">Full 3D</button>
      <a href="pages/worms.html" class="tw-btn" style="text-decoration:none;color:#00f5d4;">App ↗</a>
    </div>
  </div>

  <!-- Row 2: Live Visual Depth Layer Cards (Shows what is in each depth layer — tap any card to SOLO it!) -->
  <div class="tw-depth-bar" id="twDepthBar"></div>

  <!-- Row 3: Side-by-Side 3D Cutout Worm / 3D Planes + Unobstructed 2D Cutout Stage -->
  <div class="tw-grid" id="twStageGrid">
    <div class="tw-pane p3d">
      <canvas id="twCanvas3D" width="640" height="360" style="width:100%;height:100%;display:block;cursor:grab;touch-action:none;"></canvas>
      <span id="twHud3D" style="position:absolute;top:4px;left:5px;background:rgba(8,10,16,0.86);padding:1px 5px;border-radius:3px;font:600 9px var(--mono);color:#f3f5fa;pointer-events:none;">3D Cutout Worm · Tap any Layer Card above to solo</span>
      <div style="position:absolute;top:4px;right:5px;display:flex;gap:3px;">
        <button type="button" class="tw-btn" id="twMaskVidBtn" aria-pressed="true" style="padding:1px 5px;font-size:9px;">Video Cutouts</button>
        <button type="button" class="tw-btn" id="twResetAngle" style="padding:1px 5px;font-size:9px;">Reset</button>
      </div>
    </div>
    <div class="tw-pane p2d">
      <video id="twVideo" playsinline loop muted style="display:none;"></video>
      <canvas id="twCanvas2D" width="480" height="360" style="width:100%;height:100%;display:block;"></canvas>
      <span id="twHud2D" style="position:absolute;top:4px;left:5px;background:rgba(8,10,16,0.86);padding:1px 5px;border-radius:3px;font:600 9px var(--mono);color:#f3f5fa;pointer-events:none;">SAM Video Cutout</span>
      <div style="position:absolute;top:4px;right:5px;display:flex;gap:2px;" id="twVidSourceBar">
        <button type="button" class="tw-btn" data-vmode="cutout" aria-pressed="true" style="padding:1px 5px;font-size:9px;">Cutout</button>
        <button type="button" class="tw-btn" data-vmode="scene" aria-pressed="false" style="padding:1px 5px;font-size:9px;">Cutout+Planes</button>
        <button type="button" class="tw-btn" data-vmode="cel" aria-pressed="false" style="padding:1px 5px;font-size:9px;">Cel Sheet</button>
        <button type="button" class="tw-btn" data-vmode="src" aria-pressed="false" style="padding:1px 5px;font-size:9px;">Raw</button>
      </div>
    </div>
  </div>

  <!-- Row 4: Scrubber + 1-Line Telemetry -->
  <div class="tw-row">
    <button type="button" class="tw-btn" id="twStepPrev" style="padding:2px 6px;">-1f</button>
    <input type="range" id="twSlider" min="0" max="49" value="0" step="1" style="flex:1;min-width:80px;accent-color:#ffd166;height:5px;">
    <button type="button" class="tw-btn" id="twStepNext" style="padding:2px 6px;">+1f</button>
    <span id="twFrameReadout" style="font:600 10px var(--mono);color:#8e99b0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:48vw;">Loading...</span>
  </div>

  <!-- Row 5: Built-in Horizontal Touch-Swipe Strip of All 108 Multi-Plane Worms -->
  <div class="tw-strip" id="twSwipeStrip"></div>
</section>
"""

STUDIO_JS = """
/* === 4D SPATIOTEMPORAL TIME-WORM STUDIO & RACK CARD INTEGRATION === */
(function(){
  let WORMS = [];
  let BY_SLUG = {};
  let curIdx = 0;
  let curF = 0;
  let vMode = "cutout";
  let wMode = "orbit3d";
  let showMaskVid = true;
  let isPlaying = false;
  let lastTick = 0;
  let soloLayerId = null;
  let yaw = -0.48, pitch = 0.24, dragging = false, lx = 0, ly = 0, moved = false;
  let hitPts = [];
  const frameCache = {};

  const vid = document.getElementById("twVideo");
  const c2d = document.getElementById("twCanvas2D");
  const ctx2 = c2d ? c2d.getContext("2d") : null;
  const c3d = document.getElementById("twCanvas3D");
  const ctx3 = c3d ? c3d.getContext("2d") : null;
  const sel = document.getElementById("twSelect");
  const sld = document.getElementById("twSlider");

  function getFrameDir(w) {
    if (!w) return "";
    if (w.frame_dir) return w.frame_dir;
    const s = (w.slug === "giraffe-walks-past") ? "giraffe" : w.slug;
    return "https://hartswf0.github.io/secondhand-motion/shots/" + s + "-gwp/frames";
  }

  function ensureFrameImg(w, fi) {
    if (!w) return null;
    const fDir = getFrameDir(w);
    if (!fDir) return null;
    if (!frameCache[w.slug]) frameCache[w.slug] = {};
    const bag = frameCache[w.slug];
    if (bag[fi]) return (bag[fi].complete && bag[fi].naturalWidth > 0) ? bag[fi] : null;
    const im = new Image();
    im.onload = () => {
      if (WORMS[curIdx] && WORMS[curIdx].slug === w.slug) {
        drawLayerCardThumbs(w, curF);
        drawAll();
      }
    };
    im.src = `${fDir}/f${String(fi).padStart(3, "0")}.jpg`;
    bag[fi] = im;
    return null;
  }

  function preloadShotFrames(w) {
    if (!w) return;
    const nf = (w.frames || []).length;
    ensureFrameImg(w, 0);
    ensureFrameImg(w, Math.floor(nf / 2));
    ensureFrameImg(w, Math.max(0, nf - 1));
    (w.keys || []).forEach(k => { if (k >= 0 && k < nf) ensureFrameImg(w, k); });
    for (let i = 0; i < nf; i += 2) ensureFrameImg(w, i);
  }

  function getMediaForFrame(w, fi) {
    const im = ensureFrameImg(w, fi);
    if (im) return im;
    if (vid && vid.readyState >= 2 && vid.videoWidth > 0) return vid;
    const bag = frameCache[w.slug] || {};
    let bestImg = null, bestDist = 9999;
    Object.keys(bag).forEach(k => {
      const cand = bag[k];
      if (cand && cand.complete && cand.naturalWidth > 0) {
        const d = Math.abs(parseInt(k, 10) - fi);
        if (d < bestDist) { bestDist = d; bestImg = cand; }
      }
    });
    return bestImg;
  }

  function getPlanePolyUV(dw, fr, pt) {
    if (dw.role === "subject" && fr && fr.ring && fr.ring.length >= 3) {
      return fr.ring;
    }
    if (dw.scene_rings && dw.scene_rings.length && dw.scene_rings[0].length >= 3) {
      const dx = pt ? (pt[0] - (dw.u0 || 0.5)) : 0;
      const dy = pt ? (pt[1] - (dw.v0 || 0.5)) : 0;
      return dw.scene_rings[0].map(uv => [uv[0] + dx, uv[1] + dy]);
    }
    if (dw.poly0 && dw.poly0.length >= 3 && pt) {
      return dw.poly0.map(duv => [pt[0] + duv[0], pt[1] + duv[1]]);
    }
    return [];
  }

  function getPlaneStrokesUV(dw, fr, pt) {
    if (dw.role === "subject" && fr && fr.doodle && fr.doodle.length) {
      return fr.doodle;
    }
    if (dw.strokes0 && dw.strokes0.length && pt) {
      return dw.strokes0.map(st => st.map(duv => [pt[0] + duv[0], pt[1] + duv[1]]));
    }
    return [];
  }

  function isLayerActive(id) {
    return soloLayerId === null || soloLayerId === id;
  }

  function renderDepthPills(w) {
    const bar = document.getElementById("twDepthBar");
    if (!bar) return;
    const dws = w.depth_worms || [];
    bar.innerHTML = "";

    const allCard = document.createElement("div");
    allCard.className = "tw-lcard" + (soloLayerId === null ? " solo" : " active");
    allCard.style.flex = "0 0 74px";
    allCard.style.justifyContent = "center";
    allCard.style.alignItems = "center";
    allCard.innerHTML = `
      <div style="font:700 10px var(--mono);color:#ffd166;">ALL ${dws.length}</div>
      <div style="font:600 9px var(--sans);color:#f3f5fa;">Layers</div>
      <div style="font:500 8px var(--mono);color:#8e99b0;">Reset</div>
    `;
    allCard.onclick = () => { soloLayerId = null; renderDepthPills(w); drawAll(); };
    bar.appendChild(allCard);

    dws.forEach((dw, idx) => {
      const isSolo = (soloLayerId === dw.id);
      const isOn = isLayerActive(dw.id);
      const card = document.createElement("div");
      card.className = "tw-lcard" + (isSolo ? " solo" : (isOn ? " active" : ""));
      card.style.borderColor = isSolo ? "#ffd166" : (isOn ? (dw.color + "88") : "#252f45");
      const shortLbl = dw.label.replace("Drawing Plane: ","").replace("Rig: ","").slice(0, 11);
      card.innerHTML = `
        <div class="tw-lcard-h" style="color:${dw.color}">z=${dw.z} ${shortLbl}</div>
        <canvas width="98" height="30" data-dwidx="${idx}"></canvas>
        <div class="tw-lcard-sub" title="${dw.desc || dw.label}">${dw.desc || dw.label}</div>
      `;
      card.onclick = () => {
        soloLayerId = (soloLayerId === dw.id) ? null : dw.id;
        renderDepthPills(w);
        drawAll();
      };
      bar.appendChild(card);
    });

    drawLayerCardThumbs(w, curF);
  }

  function drawLayerCardThumbs(w, fIdx) {
    const bar = document.getElementById("twDepthBar");
    if (!bar || !w) return;
    const frames = w.frames || [];
    const fr = frames[Math.min(frames.length - 1, fIdx)] || frames[0] || {};
    const media = getMediaForFrame(w, fIdx);
    const dws = w.depth_worms || [];

    bar.querySelectorAll("canvas[data-dwidx]").forEach(cv => {
      const idx = parseInt(cv.dataset.dwidx, 10);
      const dw = dws[idx];
      if (!dw) return;
      const g = cv.getContext("2d");
      const cw = cv.width, ch = cv.height;
      g.clearRect(0, 0, cw, ch);
      g.fillStyle = "#06080e";
      g.fillRect(0, 0, cw, ch);

      const trk = dw.track || [];
      const pt = trk[Math.min(trk.length - 1, fIdx)] || [dw.u0 || 0.5, dw.v0 || 0.5, dw.r0 || 0.15];
      const col = dw.color || "#00f5d4";

      if (dw.role === "subject" && fr.ring && fr.ring.length >= 3) {
        let u0 = 1, v0 = 1, u1 = 0, v1 = 0;
        fr.ring.forEach(([u, v]) => {
          if (u < u0) u0 = u; if (u > u1) u1 = u;
          if (v < v0) v0 = v; if (v > v1) v1 = v;
        });
        const pad = 0.05;
        u0 = Math.max(0, u0 - pad); v0 = Math.max(0, v0 - pad);
        u1 = Math.min(1, u1 + pad); v1 = Math.min(1, v1 + pad);
        const su = Math.max(0.12, u1 - u0), sv = Math.max(0.12, v1 - v0);
        const mapX = u => ((u - u0) / su) * (cw - 8) + 4;
        const mapY = v => ((v - v0) / sv) * (ch - 4) + 2;

        if (media) {
          const mw = media.videoWidth || media.naturalWidth || 384;
          const mh = media.videoHeight || media.naturalHeight || 288;
          g.save();
          g.beginPath();
          fr.ring.forEach(([u, v], i) => {
            if (i === 0) g.moveTo(mapX(u), mapY(v)); else g.lineTo(mapX(u), mapY(v));
          });
          g.closePath();
          g.clip();
          try {
            g.drawImage(media, u0 * mw, v0 * mh, su * mw, sv * mh, 4, 2, cw - 8, ch - 4);
          } catch(e) {}
          g.restore();
        }
        g.strokeStyle = col;
        g.lineWidth = 1.6;
        g.beginPath();
        fr.ring.forEach(([u, v], i) => {
          if (i === 0) g.moveTo(mapX(u), mapY(v)); else g.lineTo(mapX(u), mapY(v));
        });
        g.closePath();
        g.stroke();
        return;
      }

      const strokesUV = getPlaneStrokesUV(dw, fr, pt);
      if (strokesUV.length) {
        let u0 = 1e9, v0 = 1e9, u1 = -1e9, v1 = -1e9;
        strokesUV.forEach(st => st.forEach(([u, v]) => {
          if (u < u0) u0 = u; if (u > u1) u1 = u;
          if (v < v0) v0 = v; if (v > v1) v1 = v;
        }));
        const su = Math.max(0.08, u1 - u0), sv = Math.max(0.08, v1 - v0);
        const sc = Math.min((cw - 10) / su, (ch - 6) / sv);
        const cx = 0.5 * (u0 + u1), cy = 0.5 * (v0 + v1);
        g.strokeStyle = col;
        g.lineWidth = 1.5;
        g.lineCap = "round";
        g.lineJoin = "round";
        strokesUV.forEach(st => {
          if (st.length < 2) return;
          g.beginPath();
          st.forEach(([u, v], i) => {
            const x = cw * 0.5 + (u - cx) * sc;
            const y = ch * 0.5 + (v - cy) * sc;
            if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
          });
          g.stroke();
        });
      }
    });
  }

  function proj3(u, v, tau, zOff, W, H) {
    const x = u - 0.5;
    const y = (0.5 - v) + zOff;
    const z = (tau - 0.5) * 1.55;
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
    const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
    const sc = (Math.min(W, H) * 0.88) / Math.max(0.55, 2.20 - z2 * 0.5);
    return { sx: W * 0.50 + x1 * sc, sy: H * 0.52 - y2 * sc, sc };
  }

  function drawMediaIn3DMask(media, poly, tau, zOff, W, H, alpha) {
    if (!media || !poly || poly.length < 3 || !ctx3) return false;
    const mw = media.videoWidth || media.naturalWidth || 0;
    const mh = media.videoHeight || media.naturalHeight || 0;
    if (!mw || !mh) return false;

    const p00 = proj3(0, 0, tau, zOff, W, H);
    const p10 = proj3(1, 0, tau, zOff, W, H);
    const p01 = proj3(0, 1, tau, zOff, W, H);

    ctx3.save();
    ctx3.beginPath();
    poly.forEach((uv, idx) => {
      const p = proj3(uv[0], uv[1], tau, zOff, W, H);
      if (idx === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
    });
    ctx3.closePath();
    ctx3.clip();
    ctx3.globalAlpha = alpha;
    ctx3.transform(
      (p10.sx - p00.sx) / mw, (p10.sy - p00.sy) / mw,
      (p01.sx - p00.sx) / mh, (p01.sy - p00.sy) / mh,
      p00.sx, p00.sy
    );
    try { ctx3.drawImage(media, 0, 0, mw, mh); } catch(e) {}
    ctx3.restore();
    return true;
  }

  function draw3D() {
    if (!ctx3 || !WORMS.length) return;
    const W = c3d.width, H = c3d.height;
    ctx3.clearRect(0, 0, W, H);
    const w = WORMS[curIdx];
    if (!w || !w.frames || !w.frames.length) return;
    const frames = w.frames, nf = frames.length;
    const fIdx = Math.max(0, Math.min(nf - 1, curF));
    const dws = w.depth_worms || [];
    hitPts = [];

    const hud3 = document.getElementById("twHud3D");
    if (hud3) {
      if (soloLayerId) {
        const sdw = dws.find(d => d.id === soloLayerId);
        hud3.textContent = sdw ? `SOLO LAYER: z=${sdw.z} ${sdw.label} (${sdw.desc || ""})` : "3D Cutout Worm";
      } else {
        hud3.textContent = wMode === "box3d"
          ? "3D Multiplane Cel Stack (Drag to turn · Tap Layer Card to solo)"
          : (wMode === "lanes" ? "Z×τ Multiplane Swimlanes" : "3D Cutout Worm · Tap any Layer Card above to solo");
      }
    }

    if (wMode === "lanes") {
      const padL = 114, padR = 14, padT = 22, padB = 18;
      const plotW = W - padL - padR, plotH = H - padT - padB;
      const nL = Math.max(1, dws.length);
      const curX = padL + (fIdx / Math.max(1, nf - 1)) * plotW;
      ctx3.strokeStyle = "rgba(255,209,102,0.75)"; ctx3.lineWidth = 2;
      ctx3.beginPath(); ctx3.moveTo(curX, padT - 4); ctx3.lineTo(curX, H - padB + 4); ctx3.stroke();

      [...dws].reverse().forEach((dw, dIdx) => {
        const on = isLayerActive(dw.id);
        const ly0 = padT + (dIdx + 0.5) * (plotH / nL);
        const lh = (plotH / nL) * 0.78;
        const col = dw.color || "#00f5d4";
        ctx3.fillStyle = on ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.2)";
        ctx3.fillRect(padL, ly0 - lh * 0.5, plotW, lh);
        ctx3.fillStyle = on ? col : "rgba(142,153,176,0.35)";
        ctx3.font = "bold 10px monospace";
        ctx3.fillText(`z=${dw.z} ${dw.label.slice(0, 10)}`, 5, ly0 - 2);
        ctx3.fillStyle = "rgba(142,153,176,0.75)";
        ctx3.font = "9px sans-serif";
        ctx3.fillText((dw.desc || "").slice(0, 15), 5, ly0 + 9);
        if (!on) return;
        const trk = dw.track || [];
        ctx3.strokeStyle = col; ctx3.lineWidth = dw.role === "subject" ? 3.0 : 2.0;
        ctx3.beginPath();
        trk.forEach((pt, fi) => {
          const tx = padL + (fi / Math.max(1, nf - 1)) * plotW;
          const ty = ly0 + (pt[0] - 0.5) * lh;
          if (dw.role === "subject") hitPts.push({ fi, sx: tx, sy: ty });
          if (fi === 0) ctx3.moveTo(tx, ty); else ctx3.lineTo(tx, ty);
        });
        ctx3.stroke();
      });
      return;
    }

    if (wMode === "box3d") {
      const nPlanes = Math.max(1, dws.length);
      const sc = Math.min(W, H) * 0.62;
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const tilt = 0.34;
      const PBox = (u, v, rankIdx) => {
        const X = (u - 0.5);
        const Zd = (rankIdx / Math.max(1, nPlanes - 1) - 0.5) * 1.15;
        const rx = X * cy - Zd * sy;
        const rz = X * sy + Zd * cy;
        return {
          sx: W * 0.50 + rx * sc,
          sy: H * 0.54 + (v - 0.5) * sc * 0.75 - rz * sc * tilt,
          depth: rz
        };
      };

      const ordered = dws.map((dw, idx) => ({ dw, idx, d: PBox(0.5, 0.5, idx).depth }))
                         .sort((a, b) => a.d - b.d);

      ordered.forEach(({ dw, idx }) => {
        if (!isLayerActive(dw.id)) return;
        const corners = [PBox(0, 0, idx), PBox(1, 0, idx), PBox(1, 1, idx), PBox(0, 1, idx)];
        ctx3.beginPath();
        corners.forEach((c, i) => { if (i === 0) ctx3.moveTo(c.sx, c.sy); else ctx3.lineTo(c.sx, c.sy); });
        ctx3.closePath();
        ctx3.fillStyle = "rgba(18, 24, 38, 0.42)";
        ctx3.fill();
        ctx3.strokeStyle = dw.color || "#00f5d4";
        ctx3.lineWidth = (soloLayerId === dw.id || dw.role === "subject") ? 2.2 : 1.1;
        ctx3.stroke();
      });

      const fr = frames[Math.min(nf - 1, fIdx)];
      const media = getMediaForFrame(w, fIdx);

      ordered.forEach(({ dw, idx }) => {
        if (!isLayerActive(dw.id)) return;
        const col = dw.color || "#00f5d4";
        const trk = dw.track || [];
        const pt = trk[Math.min(trk.length - 1, fIdx)] || [dw.u0 || 0.5, dw.v0 || 0.5, dw.r0 || 0.12];

        const polyUV = getPlanePolyUV(dw, fr, pt);
        if (showMaskVid && media && (dw.role === "subject" || dw.scene_rings || soloLayerId === dw.id) && polyUV.length >= 3) {
          const mw = media.videoWidth || media.naturalWidth || 0;
          const mh = media.videoHeight || media.naturalHeight || 0;
          if (mw && mh) {
            const p00 = PBox(0, 0, idx), p10 = PBox(1, 0, idx), p01 = PBox(0, 1, idx);
            ctx3.save();
            ctx3.beginPath();
            polyUV.forEach((uv, i) => {
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
            ctx3.closePath();
            ctx3.clip();
            ctx3.transform(
              (p10.sx - p00.sx) / mw, (p10.sy - p00.sy) / mw,
              (p01.sx - p00.sx) / mh, (p01.sy - p00.sy) / mh,
              p00.sx, p00.sy
            );
            try { ctx3.drawImage(media, 0, 0, mw, mh); } catch(e) {}
            ctx3.restore();

            ctx3.beginPath();
            polyUV.forEach((uv, i) => {
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
            ctx3.closePath();
            ctx3.strokeStyle = "#ffffff";
            ctx3.lineWidth = 2.0;
            ctx3.stroke();
          }
        }

        const strokesUV = getPlaneStrokesUV(dw, fr, pt);
        if (strokesUV.length) {
          ctx3.strokeStyle = dw.role === "subject" ? "#ffffff" : col;
          ctx3.lineWidth = dw.role === "subject" ? 2.2 : 1.7;
          ctx3.lineCap = "round";
          ctx3.lineJoin = "round";
          strokesUV.forEach(st => {
            if (st.length < 2) return;
            ctx3.beginPath();
            st.forEach((uv, i) => {
              const p = PBox(uv[0], uv[1], idx);
              if (i === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
            ctx3.stroke();
          });
        }

        const topL = PBox(0, 0, idx);
        ctx3.fillStyle = col;
        ctx3.font = "bold 10.5px monospace";
        ctx3.fillText(`z=${dw.z} ${dw.label} (${dw.desc || ""})`, topL.sx + 4, topL.sy - 5);
      });
      return;
    }

    const box = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]].map(c => proj3(c[0],c[1],c[2],0,W,H));
    [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([a,b]) => {
      ctx3.beginPath(); ctx3.moveTo(box[a].sx, box[a].sy); ctx3.lineTo(box[b].sx, box[b].sy);
      ctx3.strokeStyle = "rgba(142,153,176,0.16)"; ctx3.lineWidth = 1; ctx3.stroke();
    });

    const nL = Math.max(1, dws.length);
    [...dws].reverse().forEach((dw, revIdx) => {
      const origIdx = nL - 1 - revIdx;
      if (!isLayerActive(dw.id)) return;
      const col = dw.color || "#00f5d4";
      const trk = dw.track || [];
      const isSubj = (dw.role === "subject");
      const isSolo = (soloLayerId === dw.id);
      const zOff = isSolo ? 0.0 : (isSubj ? 0.0 : ((origIdx / Math.max(1, nL - 1)) - 0.45) * 0.52);

      if (isSubj || isSolo) {
        const sliceIndices = [];
        const step = Math.max(1, Math.floor((nf - 1) / 5));
        for (let s = 0; s < nf; s += step) sliceIndices.push(s);
        if (!sliceIndices.includes(nf - 1)) sliceIndices.push(nf - 1);
        if (!sliceIndices.includes(fIdx)) sliceIndices.push(fIdx);
        sliceIndices.sort((a, b) => a - b);

        sliceIndices.forEach(fi => {
          const isCur = (fi === fIdx);
          const fr = frames[Math.min(nf - 1, fi)];
          const pt = trk[Math.min(trk.length - 1, fi)];
          const tau = fi / Math.max(1, nf - 1);
          const polyUV = getPlanePolyUV(dw, fr, pt);

          let drewVid = false;
          if (showMaskVid && polyUV.length >= 3 && (isSubj || dw.scene_rings || isSolo)) {
            const media = getMediaForFrame(w, fi);
            if (media) {
              drewVid = drawMediaIn3DMask(media, polyUV, tau, zOff, W, H, isCur ? 1.0 : 0.62);
            }
          }

          if (polyUV.length >= 3) {
            ctx3.beginPath();
            polyUV.forEach((uv, j) => {
              const p = proj3(uv[0], uv[1], tau, zOff, W, H);
              if (j === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
            ctx3.closePath();
            if (!drewVid) {
              ctx3.fillStyle = isCur ? (col + "44") : (col + "18");
              ctx3.fill();
            }
            ctx3.strokeStyle = isCur ? "#ffffff" : col;
            ctx3.lineWidth = isCur ? 3.0 : 1.6;
            ctx3.stroke();
          }

          if (!isSubj || !drewVid || isSolo) {
            const strokesUV = getPlaneStrokesUV(dw, fr, pt);
            if (strokesUV.length) {
              ctx3.strokeStyle = isCur ? "#ffffff" : col;
              ctx3.lineWidth = isCur ? 2.0 : 1.3;
              strokesUV.forEach(st => {
                if (st.length < 2) return;
                ctx3.beginPath();
                st.forEach((uv, k) => {
                  const p = proj3(uv[0], uv[1], tau, zOff, W, H);
                  if (k === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
                });
                ctx3.stroke();
              });
            }
          }
        });
      } else {
        [0, fIdx].forEach(fi => {
          const fr = frames[Math.min(nf - 1, fi)];
          const pt = trk[Math.min(trk.length - 1, fi)];
          const tau = fi / Math.max(1, nf - 1);
          const strokesUV = getPlaneStrokesUV(dw, fr, pt);
          if (strokesUV.length) {
            ctx3.strokeStyle = (fi === fIdx) ? col : (col + "88");
            ctx3.lineWidth = (fi === fIdx) ? 1.5 : 1.0;
            strokesUV.forEach(st => {
              if (st.length < 2) return;
              ctx3.beginPath();
              st.forEach((uv, k) => {
                const p = proj3(uv[0], uv[1], tau, zOff, W, H);
                if (k === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
              });
              ctx3.stroke();
            });
          }
        });
      }

      ctx3.strokeStyle = col; ctx3.lineWidth = (isSubj || isSolo) ? 3.4 : 1.8;
      ctx3.beginPath();
      trk.forEach((pt, fi) => {
        const p = proj3(pt[0], pt[1], fi / Math.max(1, nf - 1), zOff, W, H);
        if (isSubj || isSolo) hitPts.push({ fi, sx: p.sx, sy: p.sy });
        if (fi === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
      });
      ctx3.stroke();

      if (trk.length) {
        const p0 = proj3(trk[0][0], trk[0][1], 0, zOff, W, H);
        ctx3.fillStyle = col; ctx3.font = "bold 10px monospace";
        ctx3.fillText(`z=${dw.z} ${dw.label.slice(0, 12)}`, p0.sx + 4, p0.sy - 4);
      }
    });
  }

  function draw2D() {
    if (!ctx2 || !WORMS.length) return;
    const W = c2d.width, H = c2d.height;
    ctx2.clearRect(0, 0, W, H);
    const w = WORMS[curIdx];
    if (!w || !w.frames || !w.frames.length) return;
    const fIdx = Math.max(0, Math.min(w.frames.length - 1, curF));
    const fr = w.frames[fIdx];
    const media = getMediaForFrame(w, fIdx);
    const dws = w.depth_worms || [];

    ensureFrameImg(w, (fIdx + 1) % w.frames.length);
    ensureFrameImg(w, (fIdx + 2) % w.frames.length);

    ctx2.fillStyle = (vMode === "cel") ? "#0c1018" : "#05070c";
    ctx2.fillRect(0, 0, W, H);

    if (media && vMode !== "cel") {
      ctx2.save();
      ctx2.globalAlpha = (vMode === "src") ? 1.0 : 0.18;
      try { ctx2.drawImage(media, 0, 0, W, H); } catch(e) {}
      ctx2.restore();
    }

    if (vMode === "src") return;

    const subjDw = dws.find(d => d.role === "subject");
    if (vMode === "cutout" && (soloLayerId === null || (subjDw && soloLayerId === subjDw.id))) {
      if (fr.ring && fr.ring.length >= 3) {
        if (media) {
          ctx2.save();
          ctx2.beginPath();
          fr.ring.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
          ctx2.closePath();
          ctx2.shadowColor = "rgba(0,0,0,0.95)";
          ctx2.shadowBlur = 14;
          ctx2.shadowOffsetX = 3;
          ctx2.shadowOffsetY = 4;
          ctx2.fillStyle = "#000";
          ctx2.fill();
          ctx2.restore();

          ctx2.save();
          ctx2.beginPath();
          fr.ring.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
          ctx2.closePath();
          ctx2.clip();
          ctx2.globalAlpha = 1.0;
          try { ctx2.drawImage(media, 0, 0, W, H); } catch(e) {}
          ctx2.restore();
        }

        ctx2.save();
        ctx2.beginPath();
        fr.ring.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
        ctx2.closePath();
        ctx2.strokeStyle = "#ffd166";
        ctx2.lineWidth = 3.2;
        ctx2.stroke();
        ctx2.strokeStyle = "#ffffff";
        ctx2.lineWidth = 1.2;
        ctx2.stroke();
        ctx2.restore();
      }
      return;
    }

    [...dws].reverse().forEach(dw => {
      if (!isLayerActive(dw.id)) return;
      const col = dw.color || "#00f5d4";
      const trk = dw.track || [];
      const pt = trk[Math.min(trk.length - 1, fIdx)] || [dw.u0 || 0.5, dw.v0 || 0.5, dw.r0 || 0.12];
      const polyUV = getPlanePolyUV(dw, fr, pt);
      const strokesUV = getPlaneStrokesUV(dw, fr, pt);

      const doCutout = (vMode !== "cel") && media && (dw.role === "subject" || dw.scene_rings || soloLayerId === dw.id);
      if (doCutout && polyUV.length >= 3) {
        ctx2.save();
        ctx2.beginPath();
        polyUV.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
        ctx2.closePath();
        ctx2.clip();
        ctx2.globalAlpha = 1.0;
        try { ctx2.drawImage(media, 0, 0, W, H); } catch(e) {}
        ctx2.restore();

        ctx2.beginPath();
        polyUV.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
        ctx2.closePath();
        ctx2.strokeStyle = col;
        ctx2.lineWidth = 2.6;
        ctx2.stroke();
      }

      if (strokesUV.length && (vMode === "cel" || dw.role !== "subject" || soloLayerId === dw.id)) {
        ctx2.save();
        ctx2.lineCap = "round";
        ctx2.lineJoin = "round";
        strokesUV.forEach(st => {
          if (st.length < 2) return;
          ctx2.beginPath();
          st.forEach((uv, i) => {
            if (i === 0) ctx2.moveTo(uv[0] * W, uv[1] * H); else ctx2.lineTo(uv[0] * W, uv[1] * H);
          });
          ctx2.strokeStyle = "rgba(5, 7, 12, 0.85)";
          ctx2.lineWidth = 4.2;
          ctx2.stroke();
          ctx2.strokeStyle = col;
          ctx2.lineWidth = 2.2;
          ctx2.stroke();
        });
        ctx2.restore();
      }
    });
  }

  function drawAll() {
    const w = WORMS[curIdx];
    if (!w) return;
    draw3D();
    draw2D();
    const fIdx = Math.max(0, Math.min(w.frames.length - 1, curF));
    const fr = w.frames[fIdx] || {};
    const areaPct = ((fr.area || 0) * 100).toFixed(1);
    const dws = w.depth_worms || [];
    const soloTxt = soloLayerId ? ` · SOLO: ${soloLayerId}` : "";
    document.getElementById("twFrameReadout").textContent =
      `f${String(fIdx).padStart(2,"0")}/${w.n_frames-1} · cutout ${areaPct}% · ${dws.length} Layers${soloTxt}`;
  }

  function syncVidTime(w, fIdx) {
    if (!w || !vid || !vid.duration || !isFinite(vid.duration)) return;
    const t0 = w.vid_t0 || 0;
    const fps = w.fps || 12;
    const targetT = t0 + (fIdx / fps);
    if (Math.abs(vid.currentTime - targetT) > 0.08) {
      try { vid.currentTime = Math.min(vid.duration - 0.05, targetT); } catch(e) {}
    }
  }

  function setFrame(fIdx, syncV) {
    const w = WORMS[curIdx];
    if (!w) return;
    curF = Math.max(0, Math.min(w.n_frames - 1, fIdx));
    sld.value = curF;
    if (syncV) {
      syncVidTime(w, curF);
      drawLayerCardThumbs(w, curF);
    }
    drawAll();
  }

  window.loadSecondhandWorm = function(slugOrIdx, autoPlay) {
    if (!WORMS.length) return;
    let idx = typeof slugOrIdx === "number" ? slugOrIdx : WORMS.findIndex(w => w.slug === slugOrIdx);
    if (idx < 0) idx = 0;
    if (idx >= WORMS.length) idx = 0;
    curIdx = idx;
    sel.value = idx;
    curF = 0;
    soloLayerId = null;
    const w = WORMS[idx];
    sld.max = Math.max(1, w.n_frames - 1);
    sld.value = 0;
    preloadShotFrames(w);
    renderDepthPills(w);
    const vUrl = w.src_mp4 || w.comp_mp4 || w.r2_mp4 || "";
    const hud2d = document.getElementById("twHud2D");
    if (hud2d) {
      const map = {
        cutout: "SAM Video Cutout (Unobstructed)",
        scene: "Video Cutout + Multiplane Drawings",
        cel: "Multiplane Vector Cel Sheet",
        src: "Raw Source Footage"
      };
      hud2d.textContent = map[vMode] || "SAM Video Cutout";
    }
    if (vUrl && vid.src !== vUrl) {
      vid.src = vUrl;
      vid.onloadedmetadata = () => { syncVidTime(w, curF); drawAll(); };
    }
    setFrame(0, false);
    document.querySelectorAll("#twSwipeStrip .tw-tile").forEach(t => {
      t.classList.toggle("active", parseInt(t.dataset.idx, 10) === curIdx);
    });
    if (autoPlay) {
      isPlaying = true;
      document.getElementById("twPlayPause").textContent = "⏸";
      vid.play().catch(() => {});
    }
  };

  function tickLoop(ts) {
    if (isPlaying && WORMS[curIdx]) {
      const w = WORMS[curIdx];
      const interval = 1000 / (w.fps || 12);
      if (ts - lastTick >= interval) {
        lastTick = ts;
        curF = (curF + 1) % Math.max(1, w.n_frames);
        sld.value = curF;
        syncVidTime(w, curF);
        drawAll();
      }
    }
    requestAnimationFrame(tickLoop);
  }
  requestAnimationFrame(tickLoop);

  function buildSwipeStrip() {
    const strip = document.getElementById("twSwipeStrip");
    if (!strip) return;
    strip.innerHTML = "";
    WORMS.forEach((w, idx) => {
      const tile = document.createElement("div");
      tile.className = "tw-tile" + (idx === curIdx ? " active" : "");
      tile.dataset.idx = idx;
      tile.innerHTML = `<canvas width="110" height="34"></canvas><div class="tw-tile-t">${idx+1}. ${w.slug}</div>`;
      tile.onclick = () => window.loadSecondhandWorm(idx, true);
      strip.appendChild(tile);

      const mc = tile.querySelector("canvas").getContext("2d");
      const nf = Math.max(1, w.frames.length);
      const dws = w.depth_worms || [];
      dws.forEach((dw, dIdx) => {
        mc.strokeStyle = dw.color || "#00f5d4";
        mc.lineWidth = dw.role === "subject" ? 2.0 : 1.2;
        mc.beginPath();
        (dw.track || []).forEach((pt, fi) => {
          const x = 4 + (fi / Math.max(1, nf - 1)) * 102;
          const y = 6 + (dIdx / Math.max(1, dws.length - 1)) * 22 + (pt[0] - 0.5) * 12;
          if (fi === 0) mc.moveTo(x, y); else mc.lineTo(x, y);
        });
        mc.stroke();
      });
    });
  }

  function decorateRackCards() {
    if (!WORMS.length) return;
    document.querySelectorAll("#out .tag").forEach(card => {
      if (card.dataset.wormDecorated) return;
      const href = card.getAttribute("href") || "";
      const titleEl = card.querySelector(".body b");
      const titleTxt = titleEl ? titleEl.textContent.toLowerCase().replace(/\\s+/g, "-") : "";
      let slug = BY_SLUG[titleTxt] ? titleTxt : null;
      if (!slug) {
        for (const s of Object.keys(BY_SLUG)) {
          if (href.includes("/" + s + "/") || href.includes("#" + s) || href.includes(s + "-")) { slug = s; break; }
        }
      }
      if (!slug || !BY_SLUG[slug]) return;
      card.dataset.wormDecorated = "1";
      const w = BY_SLUG[slug];
      const dws = w.depth_worms || [];

      const stripWrap = document.createElement("div");
      stripWrap.style.cssText = "margin-top:4px;padding:4px 6px;background:#080a10;border-radius:5px;border:1px solid var(--rule-strong);display:flex;align-items:center;justify-content:space-between;gap:6px;";
      const miniC = document.createElement("canvas");
      miniC.width = 120; miniC.height = 34;
      miniC.style.cssText = "width:104px;height:30px;display:block;";
      const mc = miniC.getContext("2d");
      const nf = Math.max(1, w.frames.length);
      dws.forEach((dw, dIdx) => {
        mc.strokeStyle = dw.color || "#00f5d4";
        mc.lineWidth = dw.role === "subject" ? 2.0 : 1.2;
        mc.beginPath();
        (dw.track || []).forEach((pt, fi) => {
          const x = 5 + (fi / Math.max(1, nf - 1)) * 110;
          const y = 6 + (dIdx / Math.max(1, dws.length - 1)) * 22 + (pt[0] - 0.5) * 12;
          if (fi === 0) mc.moveTo(x, y); else mc.lineTo(x, y);
        });
        mc.stroke();
      });

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.style.cssText = "font-size:10.5px;padding:2px 6px;background:#ffd166;color:#080a10;border-color:#ffd166;font-weight:700;";
      btn.textContent = `▶ ${dws.length} Layers`;
      btn.onclick = (e) => {
        e.preventDefault(); e.stopPropagation();
        window.loadSecondhandWorm(slug, true);
        window.scrollTo({ top: 0, behavior: "smooth" });
      };
      stripWrap.append(miniC, btn);
      const bodyEl = card.querySelector(".body");
      if (bodyEl) bodyEl.insertBefore(stripWrap, bodyEl.querySelector(".rail") || bodyEl.firstChild);
    });
  }

  document.getElementById("twPlayPause").onclick = () => {
    isPlaying = !isPlaying;
    document.getElementById("twPlayPause").textContent = isPlaying ? "⏸" : "▶";
    if (isPlaying) vid.play().catch(()=>{}); else vid.pause();
  };
  document.getElementById("twStepPrev").onclick = () => {
    isPlaying = false; document.getElementById("twPlayPause").textContent = "▶"; vid.pause();
    setFrame(curF - 1, true);
  };
  document.getElementById("twStepNext").onclick = () => {
    isPlaying = false; document.getElementById("twPlayPause").textContent = "▶"; vid.pause();
    setFrame(curF + 1, true);
  };
  sld.oninput = () => {
    isPlaying = false; document.getElementById("twPlayPause").textContent = "▶"; vid.pause();
    setFrame(parseInt(sld.value, 10), true);
  };
  sel.onchange = () => window.loadSecondhandWorm(parseInt(sel.value, 10), true);
  document.getElementById("twPrevBtn").onclick = () => window.loadSecondhandWorm(curIdx - 1, true);
  document.getElementById("twNextBtn").onclick = () => window.loadSecondhandWorm(curIdx + 1, true);

  document.querySelectorAll("#twModeBtns .tw-btn[data-wmode]").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#twModeBtns .tw-btn[data-wmode]").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      wMode = b.dataset.wmode;
      drawAll();
    };
  });
  document.getElementById("twFull3dBtn").onclick = (e) => {
    const g = document.getElementById("twStageGrid");
    const full = g.classList.toggle("full3d");
    e.target.setAttribute("aria-pressed", String(full));
    drawAll();
  };
  const mvBtn = document.getElementById("twMaskVidBtn");
  if (mvBtn) {
    mvBtn.onclick = () => {
      showMaskVid = !showMaskVid;
      mvBtn.setAttribute("aria-pressed", String(showMaskVid));
      drawAll();
    };
  }
  document.querySelectorAll("#twVidSourceBar .tw-btn").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#twVidSourceBar .tw-btn").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      vMode = b.dataset.vmode;
      const w = WORMS[curIdx];
      if (w) {
        const hud2d = document.getElementById("twHud2D");
        if (hud2d) {
          const map = {
            cutout: "SAM Video Cutout (Unobstructed)",
            scene: "Video Cutout + Multiplane Drawings",
            cel: "Multiplane Vector Cel Sheet",
            src: "Raw Source Footage"
          };
          hud2d.textContent = map[vMode] || "SAM Video Cutout";
        }
        drawAll();
      }
    };
  });

  c3d.addEventListener("pointerdown", e => { dragging = true; moved = false; lx = e.clientX; ly = e.clientY; c3d.setPointerCapture(e.pointerId); });
  c3d.addEventListener("pointermove", e => {
    if (!dragging) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) moved = true;
    if (wMode === "orbit3d" || wMode === "box3d") {
      yaw += dx * 0.008;
      pitch = Math.max(-1.0, Math.min(1.0, pitch + dy * 0.008));
      lx = e.clientX; ly = e.clientY;
      drawAll();
    }
  });
  c3d.addEventListener("pointerup", e => {
    dragging = false;
    if (!moved && WORMS[curIdx] && hitPts.length) {
      const rect = c3d.getBoundingClientRect();
      const mx = (e.clientX - rect.left) * (c3d.width / rect.width);
      const my = (e.clientY - rect.top) * (c3d.height / rect.height);
      let best = -1, bestD = 9999;
      hitPts.forEach(p => { const d = Math.hypot(p.sx - mx, p.sy - my); if (d < bestD) { bestD = d; best = p.fi; } });
      if (best !== -1 && bestD < 50) setFrame(best, true);
    }
  });
  document.getElementById("twResetAngle").onclick = () => {
    yaw = -0.48; pitch = 0.24; soloLayerId = null;
    if (WORMS[curIdx]) renderDepthPills(WORMS[curIdx]);
    drawAll();
  };

  const outEl = document.getElementById("out");
  if (outEl) new MutationObserver(() => decorateRackCards()).observe(outEl, { childList: true, subtree: true });

  fetch("data/worms_108.json?v=7")
    .catch(() => fetch("https://hartswf0.github.io/secondhand-motion/data/worms_108.json?v=7"))
    .then(r => r.json())
    .then(d => {
      WORMS = d.worms || [];
      WORMS.forEach(w => { BY_SLUG[w.slug] = w; });
      sel.innerHTML = "";
      WORMS.forEach((w, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${idx+1}. ${w.slug} (${(w.depth_worms||[]).length} Layers)`;
        sel.appendChild(opt);
      });
      buildSwipeStrip();
      const gIdx = WORMS.findIndex(w => w.slug === "giraffe");
      window.loadSecondhandWorm(gIdx !== -1 ? gIdx : 0, false);
      decorateRackCards();
    });
})();
"""


def main():
    with open(INDEX_PATH, "r") as f:
        html = f.read()

    # Remove any previous injection if re-running
    html = re.sub(
        r"<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO.*?<!-- END TIME-WORM STUDIO -->\n*",
        "",
        html,
        flags=re.S,
    )
    html = re.sub(
        r"/\* === 4D SPATIOTEMPORAL TIME-WORM STUDIO & RACK CARD INTEGRATION === \*/.*?\n</script>",
        "</script>",
        html,
        flags=re.S,
    )

    # Inject BEFORE <div class="intro"> so it sits at y=0 on mobile with ZERO scrolling!
    target_intro = '<div class="intro">'
    block = STUDIO_HTML.strip() + "\n<!-- END TIME-WORM STUDIO -->\n\n" + target_intro
    assert target_intro in html, 'Could not find <div class="intro"> in index.html'
    html = html.replace(target_intro, block, 1)

    last_script_idx = html.rfind("</script>")
    html = html[:last_script_idx] + "\n" + STUDIO_JS.strip() + "\n</script>" + html[last_script_idx + len("</script>"):]

    with open(INDEX_PATH, "w") as f:
        f.write(html)
    print(f"Updated {INDEX_PATH} ({len(html) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
