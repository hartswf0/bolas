// Ink-and-wash drawing core shared by the atlas sheet and the film. A drawing is a list of parts
// {p: dense points, f: fill token, L: layer, w: ink width, open: bool}. Layers draw in this order:
// far (far-side limbs, their own silhouette), farmark (clipped to far), main (one silhouette: ink is laid
// under the fills so only the outer contour survives), mark (clipped to main), line (interior ink), dot.
const PAL = {
  coat: '#9a7552', coatD: '#6e5038', saddle: '#2e2219', saddleD: '#231912', cream: '#e3d3b2', creamD: '#a9977a',
  ear: '#3a2a1f', nose: '#16110d', eye: '#120d0a', glint: '#f2e6cc', ink: '#1a130e', tongue: '#b8635a',
  // person
  skin: '#c79a7a', skinD: '#9c7358', hair: '#2a211c', coatP: '#3e4a5a', coatPD: '#2c3542', skirt: '#5a4a3e', shoe: '#1e1a17',
  scarf: '#8c3f33', white: '#e9e0cc',
};
function pathOf(ctx, p, open) {
  ctx.beginPath(); ctx.moveTo(p[0][0], p[0][1]);
  for (let i = 1; i < p.length; i++) ctx.lineTo(p[i][0], p[i][1]);
  if (!open) ctx.closePath();
}
function drawDrawing(ctx, parts, opt = {}) {
  const ink = opt.ink || PAL.ink, k = opt.lw || 1;
  ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const by = L => parts.filter(p => p.L === L);
  for (const [base, markL] of [['far', 'farmark'], ['main', 'mark']]) {
    const B = by(base);
    if (!B.length) continue;
    ctx.strokeStyle = ink;
    for (const q of B) { pathOf(ctx, q.p, false); ctx.lineWidth = 2 * (q.w == null ? 2.2 : q.w) * k; ctx.stroke(); }
    for (const q of B) { pathOf(ctx, q.p, false); ctx.fillStyle = PAL[q.f] || q.f; ctx.fill(); }
    const M = by(markL);
    if (M.length) {
      ctx.save(); ctx.beginPath();
      for (const q of B) { ctx.moveTo(q.p[0][0], q.p[0][1]); for (let i = 1; i < q.p.length; i++) ctx.lineTo(q.p[i][0], q.p[i][1]); ctx.closePath(); }
      ctx.clip('nonzero');
      for (const q of M) { pathOf(ctx, q.p, false); ctx.fillStyle = PAL[q.f] || q.f; ctx.globalAlpha = q.a == null ? 1 : q.a; ctx.fill(); }
      ctx.globalAlpha = 1; ctx.restore();
    }
    // interior ink belonging to this layer
    for (const q of parts.filter(p => p.L === base + 'line')) { pathOf(ctx, q.p, true); ctx.lineWidth = (q.w || 1.4) * k; ctx.strokeStyle = PAL[q.f] || q.f || ink; ctx.stroke(); }
  }
  for (const q of by('line')) { pathOf(ctx, q.p, !q.closed); ctx.lineWidth = (q.w || 1.4) * k; ctx.strokeStyle = PAL[q.f] || q.f || ink; ctx.stroke(); }
  for (const q of by('dot')) { pathOf(ctx, q.p, false); ctx.fillStyle = PAL[q.f] || q.f; ctx.fill(); }
  ctx.restore();
}
if (typeof module !== 'undefined') module.exports = { drawDrawing, PAL };
