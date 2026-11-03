#!/usr/bin/env python3
"""
Injects the Interactive 4D Spatiotemporal Time-Worm Studio (108 Tracked Shots)
directly onto the front page of https://hartswf0.github.io/secondhand-motion/ (index.html),
AND adds a live 3D Polygon Time-Worm mini-canvas + 'Inspect 4D Time Worm' button
to every matching hang-tag card on the rack!
"""

import os
import re

SHM_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/secondhand_motion_repo"
INDEX_PATH = os.path.join(SHM_ROOT, "index.html")


STUDIO_HTML = """
<!-- INTERACTIVE 4D SPATIOTEMPORAL TIME-WORM STUDIO (108 TRACKED SHOTS) -->
<section id="time-worms-studio" aria-labelledby="tw-h" style="border:2px solid var(--ink);border-radius:10px;background:var(--sheet);padding:16px;gap:12px;">
  <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;">
    <div>
      <span class="eyebrow">Ground-Truth SAM Silhouettes × Depth Strata × Camera Pan × Articulated Joint Braids</span>
      <h2 id="tw-h" style="margin-top:2px;">4D Spatiotemporal Time Worms (108 Tracked Shots)</h2>
    </div>
    <a href="pages/worms.html" style="font:600 13px var(--mono);">Open Fullscreen 108-Worm Studio →</a>
  </div>

  <!-- Quick Flagship Subject Pills -->
  <div id="twQuickBar" style="display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;">
    <button type="button" class="chip" data-slug="aircraft-carrier" aria-pressed="true">Aircraft Carrier (50f Cone)</button>
    <button type="button" class="chip" data-slug="ant" aria-pressed="false">Ant (25f · 12 Limb Braids)</button>
    <button type="button" class="chip" data-slug="camera" aria-pressed="false">Camera Lens (37f Locked Pillar)</button>
    <button type="button" class="chip" data-slug="dragon" aria-pressed="false">Dragon (32f Articulated)</button>
    <button type="button" class="chip" data-slug="flying-saucer" aria-pressed="false">Flying Saucer (28f Shear Ribbon)</button>
    <button type="button" class="chip" data-slug="giraffe" aria-pressed="false">Giraffe (17f Walk / Pan)</button>
    <button type="button" class="chip" data-slug="horse" aria-pressed="false">Horse (Gallop Braid)</button>
    <button type="button" class="chip" data-slug="hurricane" aria-pressed="false">Hurricane (39f Spiral Vortex)</button>
    <button type="button" class="chip" data-slug="crab" aria-pressed="false">Crab (38f Multi-Leg Braid)</button>
    <button type="button" class="chip" data-slug="roller-coaster" aria-pressed="false">Roller Coaster</button>
    <button type="button" class="chip" data-slug="sailboat" aria-pressed="false">Sailboat</button>
  </div>

  <!-- Shot Selector & Video/Overlay Mode Controls -->
  <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;padding:8px 10px;background:var(--paper);border:1px solid var(--rule-strong);border-radius:6px;">
    <div style="display:flex;gap:6px;align-items:center;flex:1;min-width:240px;">
      <button type="button" class="chip" id="twPrevBtn">◀</button>
      <select id="twSelect" style="flex:1;max-width:100%;" aria-label="Select tracked shot">
        <option>Loading 108 tracked time worms...</option>
      </select>
      <button type="button" class="chip" id="twNextBtn">▶</button>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;" id="twModeBtns">
      <span style="font:600 11px var(--mono);color:var(--muted);">3D WORM VIEW:</span>
      <button type="button" class="chip" data-wmode="tube" aria-pressed="true">1 · 3D Polygon Tube (u,v,τ)</button>
      <button type="button" class="chip" data-wmode="world" aria-pressed="false">2 · Camera-Stabilized World</button>
      <button type="button" class="chip" data-wmode="braid" aria-pressed="false">3 · Joint Braid (B_n)</button>
      <button type="button" class="chip" data-wmode="depth" aria-pressed="false">4 · 4D Depth (u,d,τ)</button>
    </div>
  </div>

  <!-- Dual Stage: Left = Video + 2D SAM Polygon/Joints, Right = Drag-to-Rotate 3D Time Worm -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,380px),1fr));gap:12px;">
    <!-- Left Viewport -->
    <div style="display:flex;flex-direction:column;border:1px solid var(--rule-strong);border-radius:6px;overflow:hidden;background:#090b10;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;padding:6px 10px;background:var(--paper);border-bottom:1px solid var(--rule);flex-wrap:wrap;">
        <div style="display:flex;gap:4px;align-items:center;" id="twVidSourceBar">
          <span style="font:600 11px var(--mono);color:var(--muted);">VIDEO:</span>
          <button type="button" class="chip" data-vmode="comp" aria-pressed="true" style="padding:2px 8px;font-size:12px;">Comparison</button>
          <button type="button" class="chip" data-vmode="src" aria-pressed="false" style="padding:2px 8px;font-size:12px;">Raw Archive</button>
          <button type="button" class="chip" data-vmode="art" aria-pressed="false" style="padding:2px 8px;font-size:12px;">Redraw</button>
        </div>
        <div style="display:flex;gap:4px;align-items:center;">
          <button type="button" class="chip" id="twTogMask" aria-pressed="true" style="padding:2px 8px;font-size:12px;">SAM Mask</button>
          <button type="button" class="chip" id="twTogJoints" aria-pressed="true" style="padding:2px 8px;font-size:12px;">Joints</button>
          <button type="button" class="chip" id="twTogCam" aria-pressed="true" style="padding:2px 8px;font-size:12px;">Cam Vec</button>
        </div>
      </div>
      <div style="position:relative;aspect-ratio:4/3;width:100%;background:#000;">
        <video id="twVideo" playsinline loop muted style="width:100%;height:100%;object-fit:contain;display:block;"></video>
        <canvas id="twCanvas2D" width="640" height="480" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;"></canvas>
      </div>
    </div>

    <!-- Right Viewport: 3D Extruded Worm -->
    <div style="display:flex;flex-direction:column;border:1px solid var(--rule-strong);border-radius:6px;overflow:hidden;background:#0b0d12;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;padding:6px 10px;background:var(--paper);border-bottom:1px solid var(--rule);">
        <span style="font:600 11px var(--mono);color:var(--muted);" id="tw3DHeading">DRAG 3D CANVAS TO ROTATE · GOLD = KEYFRAMES (K) · CYAN = ACTIVE SLICE</span>
        <button type="button" class="chip" id="twResetAngle" style="padding:2px 8px;font-size:12px;">Reset 3D Angle</button>
      </div>
      <div style="position:relative;aspect-ratio:4/3;width:100%;background:#0b0d12;">
        <canvas id="twCanvas3D" width="680" height="480" style="width:100%;height:100%;display:block;cursor:grab;"></canvas>
      </div>
    </div>
  </div>

  <!-- Transport & Keyframe Bar -->
  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 10px;background:var(--paper);border:1px solid var(--rule-strong);border-radius:6px;">
    <button type="button" class="chip" id="twStepPrev">◀ -1f</button>
    <button type="button" class="chip" id="twPlayPause" aria-pressed="true">▶ Play</button>
    <button type="button" class="chip" id="twStepNext">+1f ▶</button>
    <span id="twFrameReadout" style="font:600 12px var(--mono);min-width:145px;">Frame 0 / 49 (0.00s)</span>
    <input type="range" id="twSlider" min="0" max="49" value="0" step="1" style="flex:1;min-width:140px;accent-color:var(--tag);">
    <div id="twKeysBar" style="display:flex;gap:4px;overflow-x:auto;"></div>
  </div>

  <!-- 4-Card Ground-Truth Readout -->
  <div class="notes" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));">
    <div class="note"><b id="twIns1Title">1. 3D Worm Topology</b><p id="twIns1Body">—</p></div>
    <div class="note"><b id="twIns2Title">2. SAM Polygon Slice</b><p id="twIns2Body">—</p></div>
    <div class="note"><b id="twIns3Title">3. 4D Depth &amp; Camera Pan</b><p id="twIns3Body">—</p></div>
    <div class="note"><b id="twIns4Title">4. Articulated Joints &amp; Braids</b><p id="twIns4Body">—</p></div>
  </div>
</section>
"""

STUDIO_JS = """
/* === 4D SPATIOTEMPORAL TIME-WORM STUDIO & RACK CARD INTEGRATION === */
(function(){
  const JCOLS = ["#5bc8eb","#f56565","#68d391","#b794f4","#f2bc57","#ed64a6","#4fd1c5","#fbd38d"];
  let WORMS = [];
  let BY_SLUG = {};
  let curIdx = 0;
  let curF = 0;
  let vMode = "comp";
  let wMode = "tube";
  let showMask = true, showJoints = true, showCam = true;
  let yaw = 0.62, pitch = -0.34, dragging = false, lx = 0, ly = 0;

  const vid = document.getElementById("twVideo");
  const c2d = document.getElementById("twCanvas2D");
  const ctx2 = c2d ? c2d.getContext("2d") : null;
  const c3d = document.getElementById("twCanvas3D");
  const ctx3 = c3d ? c3d.getContext("2d") : null;
  const sel = document.getElementById("twSelect");
  const sld = document.getElementById("twSlider");

  function proj3(X, Y, T, W, H) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const x1 = X * cy + T * sy, z1 = -X * sy + T * cy;
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const y2 = Y * cp - z1 * sp, z2 = Y * sp + z1 * cp;
    const fov = 1.9 / (2.3 + z2 * 0.55);
    return [W * 0.50 + x1 * W * 0.44 * fov, H * 0.52 + y2 * H * 0.48 * fov];
  }

  function draw2D() {
    if (!ctx2 || !WORMS.length) return;
    const W = c2d.width, H = c2d.height;
    ctx2.clearRect(0, 0, W, H);
    const w = WORMS[curIdx];
    if (!w || !w.frames || !w.frames.length) return;
    const fIdx = Math.max(0, Math.min(w.frames.length - 1, curF));
    const fr = w.frames[fIdx];
    ctx2.save();

    if (showMask && fr.ring && fr.ring.length >= 3) {
      ctx2.beginPath();
      fr.ring.forEach((uv, i) => {
        if (i === 0) ctx2.moveTo(uv[0] * W, uv[1] * H);
        else ctx2.lineTo(uv[0] * W, uv[1] * H);
      });
      ctx2.closePath();
      ctx2.fillStyle = "rgba(91, 200, 235, 0.18)";
      ctx2.fill();
      ctx2.strokeStyle = "#5bc8eb";
      ctx2.lineWidth = 2.5;
      ctx2.stroke();

      ctx2.beginPath();
      for (let i = 0; i <= fIdx; i++) {
        const c = w.frames[i].c;
        if (i === 0) ctx2.moveTo(c[0] * W, c[1] * H);
        else ctx2.lineTo(c[0] * W, c[1] * H);
      }
      ctx2.strokeStyle = "#f2bc57";
      ctx2.lineWidth = 2.5;
      ctx2.stroke();
      ctx2.beginPath();
      ctx2.arc(fr.c[0] * W, fr.c[1] * H, 5.5, 0, Math.PI * 2);
      ctx2.fillStyle = "#f2bc57";
      ctx2.fill();
    }

    if (showJoints && w.joints) {
      Object.keys(w.joints).forEach((jn, jIdx) => {
        const tr = w.joints[jn];
        if (!tr || !tr.length) return;
        const col = JCOLS[jIdx % JCOLS.length];
        ctx2.beginPath();
        for (let i = 0; i <= Math.min(fIdx, tr.length - 1); i++) {
          if (i === 0) ctx2.moveTo(tr[i][0] * W, tr[i][1] * H);
          else ctx2.lineTo(tr[i][0] * W, tr[i][1] * H);
        }
        ctx2.strokeStyle = col;
        ctx2.lineWidth = 2;
        ctx2.stroke();
        const cur = tr[Math.min(fIdx, tr.length - 1)];
        ctx2.beginPath();
        ctx2.arc(cur[0] * W, cur[1] * H, 4.5, 0, Math.PI * 2);
        ctx2.fillStyle = col;
        ctx2.fill();
        ctx2.fillStyle = "#fff";
        ctx2.font = "bold 11px sans-serif";
        ctx2.fillText(jn, cur[0] * W + 6, cur[1] * H - 4);
      });
    }

    if (showCam && (Math.abs(fr.cam[0]) > 0.001 || Math.abs(fr.cam[1]) > 0.001)) {
      const ox = W * 0.5, oy = H * 0.90;
      ctx2.strokeStyle = "#f56565";
      ctx2.lineWidth = 2.5;
      ctx2.beginPath();
      ctx2.moveTo(ox, oy);
      ctx2.lineTo(ox + fr.cam[0] * W * 2.0, oy + fr.cam[1] * H * 2.0);
      ctx2.stroke();
      ctx2.fillStyle = "#f56565";
      ctx2.font = "bold 11px monospace";
      ctx2.fillText(`CAM PAN Δ(${(fr.cam[0]*100).toFixed(1)}%, ${(fr.cam[1]*100).toFixed(1)}%)`, ox - 65, oy - 8);
    }
    ctx2.restore();
  }

  function draw3D() {
    if (!ctx3 || !WORMS.length) return;
    const W = c3d.width, H = c3d.height;
    ctx3.clearRect(0, 0, W, H);
    const w = WORMS[curIdx];
    if (!w || !w.frames || !w.frames.length) return;
    const frames = w.frames, nf = frames.length;
    const fIdx = Math.max(0, Math.min(nf - 1, curF));
    ctx3.save();

    const corners = [
      [-0.5,-0.5,-0.5],[0.5,-0.5,-0.5],[0.5,0.5,-0.5],[-0.5,0.5,-0.5],
      [-0.5,-0.5, 0.5],[0.5,-0.5, 0.5],[0.5,0.5, 0.5],[-0.5,0.5, 0.5]
    ].map(c => proj3(c[0], c[1], c[2], W, H));
    [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([a,b]) => {
      ctx3.beginPath();
      ctx3.moveTo(corners[a][0], corners[a][1]);
      ctx3.lineTo(corners[b][0], corners[b][1]);
      ctx3.strokeStyle = "rgba(95, 110, 145, 0.35)";
      ctx3.lineWidth = 1;
      ctx3.stroke();
    });

    if (wMode === "tube" || wMode === "world") {
      const useW = (wMode === "world");
      [0, 4, 8, 12].forEach(rIdx => {
        ctx3.beginPath();
        for (let i = 0; i < nf; i++) {
          const fr = frames[i];
          const tau = (i / Math.max(1, nf - 1)) - 0.5;
          const dx = useW ? -fr.cam[0] : 0, dy = useW ? -fr.cam[1] : 0;
          const uv = fr.ring[rIdx % fr.ring.length];
          const p = proj3((uv[0] + dx) - 0.5, (uv[1] + dy) - 0.5, tau, W, H);
          if (i === 0) ctx3.moveTo(p[0], p[1]); else ctx3.lineTo(p[0], p[1]);
        }
        ctx3.strokeStyle = "rgba(91, 200, 235, 0.22)";
        ctx3.lineWidth = 1;
        ctx3.stroke();
      });

      for (let i = 0; i < nf; i++) {
        const fr = frames[i];
        const tau = (i / Math.max(1, nf - 1)) - 0.5;
        const isCur = (i === fIdx), isKey = w.keys && w.keys.includes(i);
        if (nf > 38 && !isCur && !isKey && (i % 2 !== 0)) continue;
        const dx = useW ? -fr.cam[0] : 0, dy = useW ? -fr.cam[1] : 0;
        ctx3.beginPath();
        fr.ring.forEach((uv, idx) => {
          const p = proj3((uv[0] + dx) - 0.5, (uv[1] + dy) - 0.5, tau, W, H);
          if (idx === 0) ctx3.moveTo(p[0], p[1]); else ctx3.lineTo(p[0], p[1]);
        });
        ctx3.closePath();
        if (isCur) {
          ctx3.fillStyle = "rgba(242, 188, 87, 0.32)"; ctx3.fill();
          ctx3.strokeStyle = "#5bc8eb"; ctx3.lineWidth = 3; ctx3.stroke();
        } else if (isKey) {
          ctx3.strokeStyle = "rgba(242, 188, 87, 0.85)"; ctx3.lineWidth = 1.8; ctx3.stroke();
        } else {
          ctx3.strokeStyle = (i <= fIdx) ? "rgba(91, 200, 235, 0.45)" : "rgba(154, 163, 181, 0.18)";
          ctx3.lineWidth = 1; ctx3.stroke();
        }
      }

      ctx3.beginPath();
      for (let i = 0; i < nf; i++) {
        const fr = frames[i];
        const tau = (i / Math.max(1, nf - 1)) - 0.5;
        const c = useW ? fr.c_world : fr.c;
        const p = proj3(c[0] - 0.5, c[1] - 0.5, tau, W, H);
        if (i === 0) ctx3.moveTo(p[0], p[1]); else ctx3.lineTo(p[0], p[1]);
      }
      ctx3.strokeStyle = "#f2bc57"; ctx3.lineWidth = 3; ctx3.stroke();

    } else if (wMode === "braid") {
      Object.keys(w.joints || {}).forEach((jn, jIdx) => {
        const tr = w.joints[jn], col = JCOLS[jIdx % JCOLS.length];
        ctx3.beginPath();
        for (let i = 0; i < tr.length; i++) {
          const p = proj3(tr[i][0] - 0.5, tr[i][1] - 0.5, (i / Math.max(1, nf - 1)) - 0.5, W, H);
          if (i === 0) ctx3.moveTo(p[0], p[1]); else ctx3.lineTo(p[0], p[1]);
        }
        ctx3.strokeStyle = col; ctx3.lineWidth = 2.6; ctx3.stroke();
        const cur = tr[Math.min(fIdx, tr.length - 1)];
        const cp = proj3(cur[0] - 0.5, cur[1] - 0.5, (fIdx / Math.max(1, nf - 1)) - 0.5, W, H);
        ctx3.beginPath(); ctx3.arc(cp[0], cp[1], 5.5, 0, Math.PI * 2); ctx3.fillStyle = col; ctx3.fill();
        ctx3.fillStyle = "#fff"; ctx3.font = "bold 11px sans-serif"; ctx3.fillText(jn, cp[0] + 7, cp[1] + 3);
      });
      (w.braid_events || []).forEach(ev => {
        const p = proj3(ev.u - 0.5, ev.v - 0.5, (ev.f / Math.max(1, nf - 1)) - 0.5, W, H);
        ctx3.beginPath(); ctx3.arc(p[0], p[1], 7, 0, Math.PI * 2); ctx3.fillStyle = "#f56565"; ctx3.fill();
        ctx3.fillStyle = "#fff"; ctx3.font = "bold 10px monospace"; ctx3.fillText(ev.gen, p[0] + 8, p[1] - 4);
      });
    } else if (wMode === "depth") {
      for (let i = 0; i < nf; i++) {
        const fr = frames[i];
        const p = proj3(fr.c[0] - 0.5, (1.0 - fr.d_subj) - 0.5, (i / Math.max(1, nf - 1)) - 0.5, W, H);
        ctx3.beginPath(); ctx3.arc(p[0], p[1], Math.max(4, fr.r * 38), 0, Math.PI * 2);
        ctx3.strokeStyle = (i === fIdx) ? "#5bc8eb" : "rgba(242, 188, 87, 0.55)";
        ctx3.lineWidth = (i === fIdx) ? 3 : 1.4; ctx3.stroke();
      }
    }

    ctx3.fillStyle = "#f2bc57";
    ctx3.font = "bold 12px monospace";
    ctx3.fillText(`${w.slug.toUpperCase()} · ${w.topology.replace(/_/g, " ")} (${w.n_frames}f)`, 14, 22);
    ctx3.restore();
  }

  function updateUI() {
    const w = WORMS[curIdx];
    if (!w) return;
    const fIdx = Math.max(0, Math.min(w.frames.length - 1, curF));
    const fr = w.frames[fIdx];
    const isK = w.keys && w.keys.includes(fIdx);
    document.getElementById("twFrameReadout").textContent = `Frame ${fIdx} / ${w.n_frames - 1} (${fr.t.toFixed(2)}s) ${isK ? "★ KEY" : ""}`;
    sld.value = fIdx;

    document.getElementById("twIns1Title").textContent = `${w.topology.replace(/_/g, " ")} · ${w.best_rule.replace(/_/g, " ").toUpperCase()} (${w.best_fit}%)`;
    document.getElementById("twIns1Body").textContent = `Source: "${w.source_title}". ${w.why_clip}`;

    document.getElementById("twIns2Title").textContent = `Centroid (${fr.c[0].toFixed(3)}, ${fr.c[1].toFixed(3)}) · Area ${(fr.area*100).toFixed(1)}%`;
    document.getElementById("twIns2Body").textContent = `World-stabilized centroid: (${fr.c_world[0].toFixed(3)}, ${fr.c_world[1].toFixed(3)}) · Radius r=${fr.r.toFixed(3)}.`;

    const pLabels = (w.planes || []).map(p => `${p.id}(z=${p.z})`).join(", ");
    document.getElementById("twIns3Title").textContent = `Subject Depth ${fr.d_subj.toFixed(2)} vs Scene ${fr.d_scene.toFixed(2)}`;
    document.getElementById("twIns3Body").textContent = `Camera shift: Δu=${(fr.cam[0]*100).toFixed(1)}%, Δv=${(fr.cam[1]*100).toFixed(1)}%. Planes: ${pLabels}.`;

    const jn = Object.keys(w.joints || {});
    document.getElementById("twIns4Title").textContent = `${jn.length} Joints · ${w.braid_count} Braid Crossings · ${w.planted_count} Planted`;
    document.getElementById("twIns4Body").textContent = jn.length ? `Tracked joints: ${jn.join(", ")}.` : `Tracked via 16-vertex SAM silhouette rings.`;
  }

  function setFrame(fIdx, syncV) {
    const w = WORMS[curIdx];
    if (!w) return;
    curF = Math.max(0, Math.min(w.n_frames - 1, fIdx));
    if (syncV && vid.duration && isFinite(vid.duration)) {
      const targetT = (curF / Math.max(1, w.n_frames - 1)) * vid.duration;
      if (Math.abs(vid.currentTime - targetT) > 0.04) vid.currentTime = targetT;
    }
    draw2D();
    draw3D();
    updateUI();
  }

  window.loadSecondhandWorm = function(slugOrIdx, autoPlay) {
    if (!WORMS.length) return;
    let idx = typeof slugOrIdx === "number" ? slugOrIdx : WORMS.findIndex(w => w.slug === slugOrIdx);
    if (idx < 0) idx = 0;
    if (idx >= WORMS.length) idx = 0;
    curIdx = idx;
    sel.value = idx;
    curF = 0;
    const w = WORMS[idx];

    document.querySelectorAll("#twQuickBar .chip").forEach(b => {
      b.setAttribute("aria-pressed", String(b.dataset.slug === w.slug));
    });

    sld.max = Math.max(1, w.n_frames - 1);
    sld.value = 0;

    const kb = document.getElementById("twKeysBar");
    kb.innerHTML = "";
    (w.keys || []).forEach((kf, kIdx) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.style.padding = "2px 7px";
      b.style.fontSize = "11px";
      b.textContent = `K${String(kIdx+1).padStart(2,"0")}(f${kf})`;
      b.onclick = () => { vid.pause(); setFrame(kf, true); };
      kb.appendChild(b);
    });

    const vUrl = (vMode === "src") ? w.src_mp4 : ((vMode === "art") ? w.art_mp4 : w.comp_mp4);
    if (vid.src !== vUrl) vid.src = vUrl;
    setFrame(0, false);
    if (autoPlay) vid.play().catch(() => {});
  };

  /* Decorate rack cards with mini 3D Time-Worm strips & Inspect buttons */
  function decorateRackCards() {
    if (!WORMS.length) return;
    document.querySelectorAll("#out .tag").forEach(card => {
      if (card.dataset.wormDecorated) return;
      const href = card.getAttribute("href") || "";
      const titleEl = card.querySelector(".body b");
      const titleTxt = titleEl ? titleEl.textContent.toLowerCase().replace(/\s+/g, "-") : "";
      let slug = null;
      if (BY_SLUG[titleTxt]) slug = titleTxt;
      else {
        for (const s of Object.keys(BY_SLUG)) {
          if (href.includes("/" + s + "/") || href.includes("#" + s) || href.includes(s + "-")) {
            slug = s; break;
          }
        }
      }
      if (!slug || !BY_SLUG[slug]) return;
      card.dataset.wormDecorated = "1";
      const w = BY_SLUG[slug];

      const stripWrap = document.createElement("div");
      stripWrap.style.cssText = "margin-top:4px;padding:5px 7px;background:#0b0d12;border-radius:5px;border:1px solid var(--rule-strong);display:flex;align-items:center;justify-content:space-between;gap:6px;";
      const miniC = document.createElement("canvas");
      miniC.width = 120; miniC.height = 36;
      miniC.style.cssText = "width:110px;height:34px;display:block;";
      const mc = miniC.getContext("2d");
      const nf = w.frames.length;
      w.frames.forEach((fr, fi) => {
        if (fi % Math.max(1, Math.floor(nf / 10)) !== 0 && fi !== nf - 1) return;
        const bx = 14 + (fi / Math.max(1, nf - 1)) * 92;
        const by = 22 - (fi / Math.max(1, nf - 1)) * 8;
        mc.beginPath();
        fr.ring.forEach((uv, k) => {
          const rx = bx + (uv[0] - 0.5) * 26;
          const ry = by + (uv[1] - 0.5) * 22;
          if (k === 0) mc.moveTo(rx, ry); else mc.lineTo(rx, ry);
        });
        mc.closePath();
        mc.strokeStyle = (w.keys && w.keys.includes(fi)) ? "#f2bc57" : "rgba(91,200,235,0.65)";
        mc.lineWidth = 1.2;
        mc.stroke();
      });

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.style.cssText = "font-size:11px;padding:2px 7px;background:var(--tag);color:#161412;border-color:var(--tag);";
      btn.textContent = "▶ 4D Worm";
      btn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
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
    vid.addEventListener("play", () => { document.getElementById("twPlayPause").textContent = "⏸ Pause"; });
    vid.addEventListener("pause", () => { document.getElementById("twPlayPause").textContent = "▶ Play"; });
  }

  document.getElementById("twPlayPause").onclick = () => { if (vid.paused) vid.play().catch(()=>{}); else vid.pause(); };
  document.getElementById("twStepPrev").onclick = () => { vid.pause(); setFrame(curF - 1, true); };
  document.getElementById("twStepNext").onclick = () => { vid.pause(); setFrame(curF + 1, true); };
  sld.oninput = () => { vid.pause(); setFrame(parseInt(sld.value, 10), true); };
  sel.onchange = () => window.loadSecondhandWorm(parseInt(sel.value, 10), true);
  document.getElementById("twPrevBtn").onclick = () => window.loadSecondhandWorm(curIdx - 1, true);
  document.getElementById("twNextBtn").onclick = () => window.loadSecondhandWorm(curIdx + 1, true);

  document.querySelectorAll("#twQuickBar .chip").forEach(b => {
    b.onclick = () => window.loadSecondhandWorm(b.dataset.slug, true);
  });
  document.querySelectorAll("#twModeBtns .chip").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#twModeBtns .chip").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      wMode = b.dataset.wmode;
      draw3D();
    };
  });
  document.querySelectorAll("#twVidSourceBar .chip").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#twVidSourceBar .chip").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      vMode = b.dataset.vmode;
      window.loadSecondhandWorm(curIdx, !vid.paused);
    };
  });

  function bindTog(id, getV, setV) {
    const el = document.getElementById(id);
    el.onclick = () => { setV(!getV()); el.setAttribute("aria-pressed", String(getV())); draw2D(); };
  }
  bindTog("twTogMask", () => showMask, v => showMask = v);
  bindTog("twTogJoints", () => showJoints, v => showJoints = v);
  bindTog("twTogCam", () => showCam, v => showCam = v);

  c3d.addEventListener("pointerdown", e => { dragging = true; lx = e.clientX; ly = e.clientY; c3d.setPointerCapture(e.pointerId); });
  c3d.addEventListener("pointermove", e => {
    if (!dragging) return;
    yaw += (e.clientX - lx) * 0.008;
    pitch = Math.max(-1.2, Math.min(1.2, pitch + (e.clientY - ly) * 0.008));
    lx = e.clientX; ly = e.clientY;
    draw3D();
  });
  c3d.addEventListener("pointerup", () => { dragging = false; });
  document.getElementById("twResetAngle").onclick = () => { yaw = 0.62; pitch = -0.34; draw3D(); };

  const outEl = document.getElementById("out");
  if (outEl) {
    new MutationObserver(() => decorateRackCards()).observe(outEl, { childList: true, subtree: true });
  }

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
        opt.textContent = `${idx+1}. ${w.slug.toUpperCase()} — ${w.title} (${w.n_frames}f · ${w.topology.replace(/_/g, " ")})`;
        sel.appendChild(opt);
      });
      window.loadSecondhandWorm(0, false);
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

    # Create .nojekyll in secondhand_motion_repo root so GitHub Pages deploys without slow Jekyll builds
    nojekyll_path = os.path.join(SHM_ROOT, ".nojekyll")
    with open(nojekyll_path, "w") as f:
        f.write("")
    print(f"Created {nojekyll_path}")


if __name__ == "__main__":
    main()
