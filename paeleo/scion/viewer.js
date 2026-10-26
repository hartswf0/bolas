/* SCION through the dog: the live viewer on paeleo/scion/. One canvas, the same running loop, any of the 54 lenses.
   Markup: #viewer containing canvas, .pick (the list is built here), .now (name, look, show, lineage), [data-tour], [data-restart]. */
(() => {
  const root = document.getElementById('viewer'); if (!root) return;
  const cv = root.querySelector('canvas'), R = Scion.make(cv), L = Scion.LENSES, SW = window.SWARMS;
  let cur = 47, t = 0, last = performance.now(), visible = true, tour = false, tourT = 0;
  const m = /^#lens-(\d+)$/.exec(location.hash); if (m && +m[1] >= 1 && +m[1] <= 54) cur = +m[1] - 1;
  const pick = root.querySelector('.pick'), fams = [];
  for (const s of SW) if (!fams.includes(s.family)) fams.push(s.family);
  pick.innerHTML = fams.map(f => `<optgroup label="${f}">` + SW.filter(s => s.family === f).map(s => `<option value="${s.id - 1}">${String(s.id).padStart(2, '0')} · ${s.title.split(' — ')[0]}</option>`).join('') + '</optgroup>').join('');
  const show = () => { const s = SW[cur], l = L[cur]; pick.value = cur;
    root.querySelector('.n').textContent = `SCION ${String(s.id).padStart(2, '0')} · ${s.family}`; root.querySelector('.t').textContent = s.title;
    root.querySelector('.look').textContent = l.look; root.querySelector('.show').textContent = l.show; root.querySelector('.lin').textContent = s.lineage;
    root.querySelector('.op').href = `operator.html#s${s.id}`; };
  const go = i => { cur = (i + 54) % 54; show(); history.replaceState(null, '', `#lens-${cur + 1}`); };
  pick.addEventListener('change', () => { tour = false; sync(); go(+pick.value); });
  root.querySelector('[data-prev]').addEventListener('click', () => { tour = false; sync(); go(cur - 1); });
  root.querySelector('[data-next]').addEventListener('click', () => { tour = false; sync(); go(cur + 1); });
  const tb = root.querySelector('[data-tour]'); const sync = () => tb.setAttribute('aria-pressed', String(tour));
  tb.addEventListener('click', () => { tour = !tour; tourT = 0; sync(); });
  root.querySelector('[data-restart]').addEventListener('click', () => { t = 0; });
  new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(cv);
  document.querySelectorAll('[data-lens]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); tour = false; sync(); go(+a.dataset.lens - 1); root.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function tick(now) {
    requestAnimationFrame(tick); const dt = Math.min(.1, (now - last) / 1000); last = now; if (!visible) return;
    if (!reduce || tour) t = (t + dt) % Scion.LOOP;
    if (tour) { tourT += dt; if (tourT > 6) { tourT = 0; go(cur + 1); } }
    R.draw(cur, reduce && !tour ? (L[cur].still || 18.5) : t);
  }
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => { show(); requestAnimationFrame(tick); });
})();
