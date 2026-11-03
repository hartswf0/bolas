#!/usr/bin/env python3
"""
Injects the Minimal, Mobile-First Multi-Depth 4D Spatiotemporal Worm Studio
(108 Tracked Shots · 375 Depth Strata) directly onto the front page of
https://hartswf0.github.io/secondhand-motion/ (index.html), AND adds a live
Multi-Depth Worm mini-canvas + '▶ 4D Worm' button to every matching rack card.
"""

import os
import re

SHM_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo"
INDEX_PATH = os.path.join(SHM_ROOT, "index.html")


STUDIO_HTML = """
<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO (108 TRACKED SHOTS) -->
<section id="time-worms-studio" aria-labelledby="tw-h" style="border:2px solid var(--ink);border-radius:10px;background:#0d1018;color:#f1f3f9;padding:8px 10px;gap:6px;">
  <style>
    #time-worms-studio .tw-row { display:flex; align-items:center; justify-content:space-between; gap:6px; flex-wrap:wrap; }
    #time-worms-studio .tw-btn { background:#1b2234; color:#f1f3f9; border:1px solid #2d3752; border-radius:5px; padding:4px 8px; font:600 11px var(--mono); cursor:pointer; white-space:nowrap; }
    #time-worms-studio .tw-btn[aria-pressed="true"], #time-worms-studio .tw-btn.gold { background:#f2bc57; color:#090b10; border-color:#f2bc57; font-weight:700; }
    #time-worms-studio .tw-depth-bar { display:flex; align-items:center; gap:5px; overflow-x:auto; padding:3px 0; scrollbar-width:none; }
    #time-worms-studio .tw-depth-bar::-webkit-scrollbar { display:none; }
    #time-worms-studio .tw-dpill { display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:999px; font:600 10.5px var(--mono); background:#141926; border:1px solid #2d3752; cursor:pointer; white-space:nowrap; opacity:0.45; }
    #time-worms-studio .tw-dpill.on { opacity:1; border-color:currentColor; background:rgba(255,255,255,0.07); }
    #time-worms-studio .tw-grid { display:grid; grid-template-columns:1.15fr 0.85fr; gap:6px; }
    #time-worms-studio .tw-pane { position:relative; height:290px; background:#05070b; border:1px solid #252d42; border-radius:7px; overflow:hidden; }
    @media (max-width: 760px) {
      #time-worms-studio .tw-grid { grid-template-columns:1fr; gap:5px; }
      #time-worms-studio .tw-pane.p3d { height:195px; }
      #time-worms-studio .tw-pane.p2d { height:160px; }
    }
  </style>

  <!-- Row 1: Compact Shot Selector + View Mode + Fullscreen Link -->
  <div class="tw-row">
    <div style="display:flex;align-items:center;gap:4px;flex:1;min-width:190px;">
      <button type="button" class="tw-btn" id="twPrevBtn">◀</button>
      <button type="button" class="tw-btn gold" id="twPlayPause">▶</button>
      <select id="twSelect" style="flex:1;min-width:130px;background:#090b10;color:#f1f3f9;border:1px solid #2d3752;border-radius:5px;padding:4px 6px;font:700 11.5px var(--sans);" aria-label="Select tracked shot">
        <option>Loading 108 multi-depth worms...</option>
      </select>
      <button type="button" class="tw-btn" id="twNextBtn">▶</button>
    </div>
    <div style="display:flex;gap:4px;align-items:center;overflow-x:auto;" id="twModeBtns">
      <button type="button" class="tw-btn" data-wmode="orbit3d" aria-pressed="true">3D Depth Worms</button>
      <button type="button" class="tw-btn" data-wmode="lanes" aria-pressed="false">Depth Lanes (Z×τ)</button>
      <button type="button" class="tw-btn" id="twSubToggle" aria-pressed="true">Sub-Worms</button>
      <a href="pages/worms.html" class="tw-btn" style="text-decoration:none;color:#4fd1c5;">Fullscreen ↗</a>
    </div>
  </div>

  <!-- Row 2: Horizontal Multi-Depth Stratum Pills (Tap any depth to solo/toggle) -->
  <div class="tw-depth-bar" id="twDepthBar">
    <span style="font:600 10px var(--mono);color:#8b95ab;white-space:nowrap;">DEPTHS:</span>
  </div>

  <!-- Compact Synchronized Stage: 3D Multi-Depth Worms + 2D Video & Contours -->
  <div class="tw-grid">
    <div class="tw-pane p3d">
      <canvas id="twCanvas3D" width="720" height="400" style="width:100%;height:100%;display:block;cursor:grab;touch-action:none;"></canvas>
      <span id="tw3DTag" style="position:absolute;top:5px;left:6px;background:rgba(9,11,16,0.82);padding:2px 6px;border-radius:4px;font:500 10px var(--mono);color:#8b95ab;pointer-events:none;">Drag to orbit · Tap worm to seek</span>
      <button type="button" class="tw-btn" id="twResetAngle" style="position:absolute;top:5px;right:6px;padding:2px 6px;font-size:10px;">Reset</button>
    </div>
    <div class="tw-pane p2d">
      <video id="twVideo" playsinline loop muted style="width:100%;height:100%;object-fit:contain;display:block;background:#000;"></video>
      <canvas id="twCanvas2D" width="600" height="380" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;"></canvas>
      <div style="position:absolute;top:5px;right:6px;display:flex;gap:3px;" id="twVidSourceBar">
        <button type="button" class="tw-btn" data-vmode="comp" aria-pressed="true" style="padding:2px 6px;font-size:10px;">3-Way</button>
        <button type="button" class="tw-btn" data-vmode="src" aria-pressed="false" style="padding:2px 6px;font-size:10px;">Raw</button>
        <button type="button" class="tw-btn" data-vmode="art" aria-pressed="false" style="padding:2px 6px;font-size:10px;">Cartoon</button>
      </div>
    </div>
  </div>

  <!-- Row 3: Compact Scrubber + 1-Line Telemetry -->
  <div class="tw-row" style="padding-top:2px;">
    <button type="button" class="tw-btn" id="twStepPrev">-1f</button>
    <input type="range" id="twSlider" min="0" max="49" value="0" step="1" style="flex:1;min-width:110px;accent-color:#f2bc57;height:5px;">
    <button type="button" class="tw-btn" id="twStepNext">+1f</button>
    <span id="twFrameReadout" style="font:500 11px var(--mono);color:#8b95ab;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Loading...</span>
  </div>
</section>
"""

STUDIO_JS = """
/* === 4D SPATIOTEMPORAL TIME-WORM STUDIO & RACK CARD INTEGRATION === */
(function(){
  let WORMS = [];
  let BY_SLUG = {};
  let curIdx = 0;
  let curF = 0;
  let vMode = "comp";
  let wMode = "orbit3d";
  let showSub = true;
  let activeDepths = new Set();
  let yaw = -0.58, pitch = 0.34, dragging = false, lx = 0, ly = 0, moved = false;
  let hitPts = [];

  const vid = document.getElementById("twVideo");
  const c2d = document.getElementById("twCanvas2D");
  const ctx2 = c2d ? c2d.getContext("2d") : null;
  const c3d = document.getElementById("twCanvas3D");
  const ctx3 = c3d ? c3d.getContext("2d") : null;
  const sel = document.getElementById("twSelect");
  const sld = document.getElementById("twSlider");

  function proj3(u, v, tau, zNorm, W, H) {
    const x = u - 0.5;
    const y = (0.5 - v) + (zNorm - 0.35) * 0.28;
    const z = (tau - 0.5) * 1.55;
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
    const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
    const sc = (Math.min(W, H) * 0.78) / Math.max(0.55, 2.35 - z2 * 0.5);
    return { sx: W * 0.50 + x1 * sc, sy: H * 0.52 - y2 * sc, sc };
  }

  function isDepthOn(id) {
    return activeDepths.size === 0 || activeDepths.has(id);
  }

  function renderDepthPills(w) {
    const bar = document.getElementById("twDepthBar");
    if (!bar) return;
    const dws = w.depth_worms || [];
    bar.innerHTML = `<span style="font:600 10px var(--mono);color:#8b95ab;white-space:nowrap;">DEPTHS (${dws.length}):</span>`;
    const allB = document.createElement("button");
    allB.type = "button";
    allB.className = "tw-dpill" + (activeDepths.size === 0 ? " on" : "");
    allB.style.color = "#f1f3f9";
    allB.textContent = `All (${dws.length})`;
    allB.onclick = () => { activeDepths.clear(); renderDepthPills(w); drawAll(); };
    bar.appendChild(allB);

    dws.forEach(dw => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "tw-dpill" + (isDepthOn(dw.id) ? " on" : "");
      b.style.color = dw.color || "#4fd1c5";
      b.innerHTML = `<span style="width:6px;height:6px;border-radius:50%;background:${dw.color};display:inline-block;"></span>z=${dw.z} ${dw.label}`;
      b.onclick = () => {
        if (activeDepths.size === 1 && activeDepths.has(dw.id)) activeDepths.clear();
        else { activeDepths.clear(); activeDepths.add(dw.id); }
        renderDepthPills(w);
        drawAll();
      };
      bar.appendChild(b);
    });
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

    if (wMode === "lanes") {
      const padL = 108, padR = 18, padT = 22, padB = 22;
      const plotW = W - padL - padR, plotH = H - padT - padB;
      const nL = Math.max(1, dws.length);
      const curX = padL + (fIdx / Math.max(1, nf - 1)) * plotW;
      ctx3.strokeStyle = "rgba(242,188,87,0.55)"; ctx3.lineWidth = 1.5;
      ctx3.beginPath(); ctx3.moveTo(curX, padT - 6); ctx3.lineTo(curX, H - padB + 6); ctx3.stroke();

      dws.forEach((dw, dIdx) => {
        const on = isDepthOn(dw.id);
        const ly0 = padT + (dIdx + 0.5) * (plotH / nL);
        const lh = (plotH / nL) * 0.72;
        const col = dw.color || "#4fd1c5";
        ctx3.fillStyle = on ? col : "rgba(139,149,171,0.4)";
        ctx3.font = "bold 10px monospace";
        ctx3.fillText(`z=${dw.z} ${dw.label.slice(0, 10)}`, 6, ly0 + 3);
        if (!on) return;
        const trk = dw.track || [];
        ctx3.strokeStyle = col; ctx3.lineWidth = dw.role === "subject" ? 2.5 : 1.7;
        ctx3.beginPath();
        trk.forEach((pt, fi) => {
          const tx = padL + (fi / Math.max(1, nf - 1)) * plotW;
          const ty = ly0 + (pt[0] - 0.5) * lh * 0.9;
          if (dw.role === "subject") hitPts.push({ fi, sx: tx, sy: ty });
          if (fi === 0) ctx3.moveTo(tx, ty); else ctx3.lineTo(tx, ty);
        });
        ctx3.stroke();
      });
      return;
    }

    const box = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]].map(c => proj3(c[0],c[1],c[2],0.35,W,H));
    [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([a,b]) => {
      ctx3.beginPath(); ctx3.moveTo(box[a].sx, box[a].sy); ctx3.lineTo(box[b].sx, box[b].sy);
      ctx3.strokeStyle = "rgba(139,149,171,0.22)"; ctx3.lineWidth = 1; ctx3.stroke();
    });

    [...dws].reverse().forEach(dw => {
      if (!isDepthOn(dw.id)) return;
      const col = dw.color || "#4fd1c5";
      const trk = dw.track || [];
      const zNorm = Math.min(1.0, Math.log(Math.max(1.0, dw.z || 2.0)) / Math.log(12.0));
      const isSubj = dw.role === "subject";

      if (isSubj) {
        const step = Math.max(1, Math.floor(nf / 14));
        frames.forEach((fr, fi) => {
          if (fi !== fIdx && fi % step !== 0 && !(w.keys || []).includes(fi)) return;
          if (!fr.ring || fr.ring.length < 3) return;
          ctx3.strokeStyle = (fi === fIdx) ? "#ffffff" : col + "bb";
          ctx3.fillStyle = (fi === fIdx) ? col + "50" : col + "18";
          ctx3.lineWidth = (fi === fIdx) ? 2.4 : 1.1;
          ctx3.beginPath();
          fr.ring.forEach((uv, j) => {
            const p = proj3(uv[0], uv[1], fi / Math.max(1, nf - 1), zNorm, W, H);
            if (j === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
          });
          ctx3.closePath(); ctx3.fill(); ctx3.stroke();
        });
      } else {
        const step = Math.max(1, Math.floor(nf / 9));
        trk.forEach((pt, fi) => {
          if (fi !== fIdx && fi % step !== 0) return;
          const p = proj3(pt[0], pt[1], fi / Math.max(1, nf - 1), zNorm, W, H);
          const rx = Math.max(5, pt[2] * p.sc * 0.5);
          ctx3.strokeStyle = (fi === fIdx) ? "#ffffff" : col + "99";
          ctx3.lineWidth = (fi === fIdx) ? 1.8 : 1.0;
          ctx3.beginPath(); ctx3.ellipse(p.sx, p.sy, rx, rx * 0.6, 0, 0, Math.PI * 2); ctx3.stroke();
        });
      }

      ctx3.strokeStyle = col; ctx3.lineWidth = isSubj ? 2.6 : 1.8;
      ctx3.beginPath();
      trk.forEach((pt, fi) => {
        const p = proj3(pt[0], pt[1], fi / Math.max(1, nf - 1), zNorm, W, H);
        if (isSubj) hitPts.push({ fi, sx: p.sx, sy: p.sy });
        if (fi === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
      });
      ctx3.stroke();

      if (showSub && dw.sub_worms) {
        dw.sub_worms.forEach(sw => {
          ctx3.strokeStyle = col + "99"; ctx3.lineWidth = 1.1; ctx3.setLineDash([3, 3]);
          ctx3.beginPath();
          if (sw.pts) {
            sw.pts.forEach((uv, fi) => {
              const p = proj3(uv[0], uv[1], fi / Math.max(1, nf - 1), zNorm, W, H);
              if (fi === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
          } else if (sw.u0 !== undefined) {
            trk.forEach((pt, fi) => {
              const p = proj3(sw.u0 + (pt[0] - trk[0][0]), sw.v0 + (pt[1] - trk[0][1]), fi / Math.max(1, nf - 1), zNorm, W, H);
              if (fi === 0) ctx3.moveTo(p.sx, p.sy); else ctx3.lineTo(p.sx, p.sy);
            });
          }
          ctx3.stroke(); ctx3.setLineDash([]);
        });
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
    (w.depth_worms || []).forEach(dw => {
      if (!isDepthOn(dw.id)) return;
      const col = dw.color || "#4fd1c5";
      const pt = (dw.track || [])[Math.min((dw.track || []).length - 1, fIdx)];
      if (!pt) return;
      if (dw.role === "subject" && fr.ring && fr.ring.length >= 3) {
        ctx2.strokeStyle = col; ctx2.fillStyle = col + "22"; ctx2.lineWidth = 2.2;
        ctx2.beginPath();
        fr.ring.forEach((uv, i) => { if (i === 0) ctx2.moveTo(uv[0]*W, uv[1]*H); else ctx2.lineTo(uv[0]*W, uv[1]*H); });
        ctx2.closePath(); ctx2.fill(); ctx2.stroke();
      } else {
        const cx = pt[0]*W, cy = pt[1]*H, rx = pt[2]*W*0.6, ry = pt[2]*H*0.4;
        ctx2.strokeStyle = col + "bb"; ctx2.lineWidth = 1.4; ctx2.setLineDash([4, 4]);
        ctx2.beginPath(); ctx2.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); ctx2.stroke(); ctx2.setLineDash([]);
      }
    });
  }

  function drawAll() {
    const w = WORMS[curIdx];
    if (!w) return;
    draw3D();
    draw2D();
    const fIdx = Math.max(0, Math.min(w.frames.length - 1, curF));
    const fr = w.frames[fIdx];
    const dws = w.depth_worms || [];
    document.getElementById("twFrameReadout").textContent =
      `f${String(fIdx).padStart(2,"0")}/${w.n_frames-1} · ${dws.length} Depths (${dws.map(d=>"z="+d.z).join("→")}) · ${w.best_rule} ${w.best_fit}%`;
  }

  function setFrame(fIdx, syncV) {
    const w = WORMS[curIdx];
    if (!w) return;
    curF = Math.max(0, Math.min(w.n_frames - 1, fIdx));
    sld.value = curF;
    if (syncV && vid.duration && isFinite(vid.duration)) {
      const targetT = (curF / Math.max(1, w.n_frames - 1)) * vid.duration;
      if (Math.abs(vid.currentTime - targetT) > 0.04) vid.currentTime = targetT;
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
    activeDepths.clear();
    const w = WORMS[idx];
    sld.max = Math.max(1, w.n_frames - 1);
    sld.value = 0;
    renderDepthPills(w);
    const vUrl = (vMode === "src") ? w.src_mp4 : ((vMode === "art") ? w.art_mp4 : w.comp_mp4);
    if (vid.src !== vUrl) vid.src = vUrl;
    setFrame(0, false);
    if (autoPlay) vid.play().catch(() => {});
  };

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
      stripWrap.style.cssText = "margin-top:4px;padding:4px 6px;background:#090b10;border-radius:5px;border:1px solid var(--rule-strong);display:flex;align-items:center;justify-content:space-between;gap:6px;";
      const miniC = document.createElement("canvas");
      miniC.width = 120; miniC.height = 34;
      miniC.style.cssText = "width:108px;height:32px;display:block;";
      const mc = miniC.getContext("2d");
      const nf = Math.max(1, w.frames.length);
      dws.forEach((dw, dIdx) => {
        mc.strokeStyle = dw.color || "#4fd1c5";
        mc.lineWidth = dw.role === "subject" ? 1.8 : 1.1;
        mc.beginPath();
        (dw.track || []).forEach((pt, fi) => {
          const x = 6 + (fi / Math.max(1, nf - 1)) * 108;
          const y = 7 + (dIdx / Math.max(1, dws.length - 1)) * 20 + (pt[0] - 0.5) * 12;
          if (fi === 0) mc.moveTo(x, y); else mc.lineTo(x, y);
        });
        mc.stroke();
      });

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.style.cssText = "font-size:10.5px;padding:2px 6px;background:#f2bc57;color:#090b10;border-color:#f2bc57;font-weight:700;";
      btn.textContent = `▶ ${dws.length} Depths`;
      btn.onclick = (e) => {
        e.preventDefault(); e.stopPropagation();
        window.loadSecondhandWorm(slug, true);
        document.getElementById("time-worms-studio").scrollIntoView({ behavior: "smooth" });
      };
      stripWrap.append(miniC, btn);
      const bodyEl = card.querySelector(".body");
      if (bodyEl) bodyEl.insertBefore(stripWrap, bodyEl.querySelector(".rail") || bodyEl.firstChild);
    });
  }

  if (vid) {
    vid.addEventListener("timeupdate", () => {
      const w = WORMS[curIdx];
      if (!w || !vid.duration || !isFinite(vid.duration)) return;
      const f = Math.round((vid.currentTime / vid.duration) * (w.n_frames - 1));
      if (f !== curF) setFrame(f, false);
    });
    vid.addEventListener("play", () => { document.getElementById("twPlayPause").textContent = "⏸"; });
    vid.addEventListener("pause", () => { document.getElementById("twPlayPause").textContent = "▶"; });
  }

  document.getElementById("twPlayPause").onclick = () => { if (vid.paused) vid.play().catch(()=>{}); else vid.pause(); };
  document.getElementById("twStepPrev").onclick = () => { vid.pause(); setFrame(curF - 1, true); };
  document.getElementById("twStepNext").onclick = () => { vid.pause(); setFrame(curF + 1, true); };
  sld.oninput = () => { vid.pause(); setFrame(parseInt(sld.value, 10), true); };
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
  document.getElementById("twSubToggle").onclick = (e) => {
    showSub = !showSub;
    e.target.setAttribute("aria-pressed", String(showSub));
    drawAll();
  };
  document.querySelectorAll("#twVidSourceBar .tw-btn").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#twVidSourceBar .tw-btn").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      vMode = b.dataset.vmode;
      window.loadSecondhandWorm(curIdx, !vid.paused);
    };
  });

  c3d.addEventListener("pointerdown", e => { dragging = true; moved = false; lx = e.clientX; ly = e.clientY; c3d.setPointerCapture(e.pointerId); });
  c3d.addEventListener("pointermove", e => {
    if (!dragging) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) moved = true;
    if (wMode === "orbit3d") {
      yaw += dx * 0.008;
      pitch = Math.max(-1.1, Math.min(1.1, pitch + dy * 0.008));
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
  document.getElementById("twResetAngle").onclick = () => { yaw = -0.58; pitch = 0.34; drawAll(); };

  const outEl = document.getElementById("out");
  if (outEl) new MutationObserver(() => decorateRackCards()).observe(outEl, { childList: true, subtree: true });

  fetch("data/worms_108.json")
    .catch(() => fetch("https://hartswf0.github.io/secondhand-motion/data/worms_108.json"))
    .then(r => r.json())
    .then(d => {
      WORMS = d.worms || [];
      WORMS.forEach(w => { BY_SLUG[w.slug] = w; });
      sel.innerHTML = "";
      WORMS.forEach((w, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${idx+1}. ${w.slug} (${(w.depth_worms||[]).length} Depth Worms · ${w.n_frames}f)`;
        sel.appendChild(opt);
      });
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
        r"<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO.*?<!-- END TIME-WORM STUDIO -->\n?",
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

    target_section = '<section aria-labelledby="st-h">'
    block = STUDIO_HTML.strip() + "\n<!-- END TIME-WORM STUDIO -->\n\n" + target_section
    assert target_section in html, "Could not find <section aria-labelledby=\"st-h\"> in index.html"
    html = html.replace(target_section, block, 1)

    assert html.endswith("</script>") or "</script>" in html
    last_script_idx = html.rfind("</script>")
    html = html[:last_script_idx] + "\n" + STUDIO_JS.strip() + "\n</script>" + html[last_script_idx + len("</script>"):]

    with open(INDEX_PATH, "w") as f:
        f.write(html)
    print(f"Updated {INDEX_PATH} ({len(html) / 1024:.1f} KB)")

    nojekyll_path = os.path.join(SHM_ROOT, ".nojekyll")
    with open(nojekyll_path, "w") as f:
        f.write("")


if __name__ == "__main__":
    main()
