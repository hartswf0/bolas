/* CRASH LAB cameos. Every <span class="cam" data-who data-c data-at> on a page becomes an animated sprite from
   media/cameo, sized from the shared scale, anchored by its pose (soles, seat or hands) and given lines to say.
   On film pages the cast reacts to the player: they sit down and turn to watch on play, turn back on pause, cheer at the end.
   Data (window.CAM) is written by the site build from media/cameo/cameos.json and site/cameo.py. */
(() => {
  const D = window.CAM, root = document.documentElement.dataset.root || '', REF = 294;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rnd = a => a[Math.floor(Math.random() * a.length)];
  const bases = new Map();
  function camBase(host) {   // --cam may be a clamp(); measure it as a length
    if (bases.has(host)) return bases.get(host);
    const pr = document.createElement('i'); pr.style.cssText = 'position:absolute;width:0;height:var(--cam,110px);visibility:hidden;pointer-events:none';
    host.append(pr); const b = pr.getBoundingClientRect().height || 110; pr.remove(); bases.set(host, b); return b;
  }
  function set(el, key) {
    const m = D.s[key]; if (!m) return false;
    const host = el.parentElement, base = camBase(host);
    const h = base * m.h / REF * (D.k[el.dataset.who] || 1);
    el.dataset.c = key; el.style.height = h + 'px'; el.style.width = (h * m.w / m.h) + 'px';
    el.style.backgroundImage = `url(${root}media/cameo/${key}.webp)`; el.style.backgroundSize = `${m.n * 100}% 100%`;
    el.style.setProperty('--ay', m.ay);
    el.style.clipPath = /-peek$/.test(key) ? `inset(0 -40px ${Math.max(0, (1 - m.ay) * 100 - 2)}% -40px)` : '';
    if (m.n > 1 && !still) { el.style.animationTimingFunction = `steps(${m.n},jump-none)`; el.style.animationDuration = (m.n / 8) + 's'; el.classList.add('run'); }
    else el.classList.remove('run');
    return true;
  }
  function say(el, text, ms = 3800) {
    if (!text) return; let b = el.querySelector('.say'); if (!b) { b = document.createElement('span'); b.className = 'say'; el.append(b); }
    b.textContent = text; b.classList.add('on'); clearTimeout(el._t); el._t = setTimeout(() => b.classList.remove('on'), ms);
  }
  const lines = el => { try { return JSON.parse(el.dataset.say || '[]'); } catch (e) { return []; } };
  const cams = [...document.querySelectorAll('.cam')];
  cams.forEach((el, i) => {
    el.dataset.home = el.dataset.c; if (!set(el, el.dataset.c)) { el.remove(); return; }
    el.style.animationDelay = (-Math.random() * 2).toFixed(2) + 's';
    const L = lines(el); el._i = 0;
    if (L.length) {
      el.setAttribute('role', 'button'); el.tabIndex = 0; el.setAttribute('aria-label', el.dataset.who + ' says something');
      const talk = e => { e.preventDefault(); e.stopPropagation(); say(el, L[el._i++ % L.length]); };
      el.addEventListener('click', talk); el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') talk(e); });
      const card = el.closest('.card'); if (card) card.addEventListener('mouseenter', () => say(el, L[0], 2600));
    }
  });
  addEventListener('resize', () => { bases.clear(); cams.forEach(el => el.isConnected && set(el, el.dataset.c)); });

  // film pages: the cast watches with you
  document.querySelectorAll('.player').forEach(p => {
    const v = p.querySelector('video'), cs = [...p.querySelectorAll('.cam')]; if (!cs.length) return;
    const talker = () => rnd(cs.filter(c => D.play[c.dataset.who]) .concat([])) || null;
    setTimeout(() => { const c = cs.find(c => lines(c).length); if (c) say(c, lines(c)[0]); }, 1200);
    if (!v) return;
    const pose = (c, suf) => { const k = c.dataset.who + suf; return D.s[k] ? set(c, k) : false; };
    v.addEventListener('play', () => { cs.forEach(c => { if (!/-peek$/.test(c.dataset.home)) pose(c, '-sit-back') && c.classList.add('watch'); }); const t = talker(); t && say(t, D.play[t.dataset.who]); });
    v.addEventListener('pause', () => { if (v.ended) return; cs.forEach(c => { c.classList.remove('watch'); set(c, c.dataset.home); }); const t = talker(); t && say(t, D.pause[t.dataset.who]); });
    v.addEventListener('ended', () => { cs.forEach(c => { c.classList.remove('watch'); pose(c, '-jump') || set(c, c.dataset.home); }); const t = talker(); t && say(t, D.end[t.dataset.who], 6000); });
  });

  // production notes: the guide follows you down the page, and every frame plays the film from that moment
  const notes = document.querySelector('.notes');
  if (notes) {
    const g = notes.querySelector('.cam.gs'), gs = notes.querySelector('.gsay'), who = g && g.dataset.who;
    const secs = [...notes.querySelectorAll('.nsec')];
    let last = null;
    const show = el => { if (!el || el === last) return; last = el; const sec = el.closest('.nsec');
      gs.textContent = el.dataset.say; gs.classList.remove('pop'); void gs.offsetWidth; gs.classList.add('pop');
      const pose = el.dataset.pose || sec.dataset.pose; if (g) { const k = who + '-' + pose; set(g, D.s[k] ? k : who + '-point'); }
      secs.forEach(x => x.classList.toggle('cur', x === sec)); };
    const io = new IntersectionObserver(es => { const v = es.filter(e => e.isIntersecting).sort((a, b) => (b.target.classList.contains('beat') - a.target.classList.contains('beat')) || (a.boundingClientRect.top - b.boundingClientRect.top))[0]; v && show(v.target); },
      { rootMargin: '-30% 0px -60% 0px' });
    notes.classList.add('js'); secs.forEach(s => io.observe(s)); notes.querySelectorAll('.beat[data-say]').forEach(b => io.observe(b));
    new IntersectionObserver(es => es.forEach(e => notes.classList.toggle('inview', e.isIntersecting)), { threshold: 0 }).observe(notes);
  }
  const seek = t => { const v = document.querySelector('.player video'); if (!v) return false; v.scrollIntoView({ behavior: 'smooth', block: 'center' });
    v.preload = 'auto'; const go = () => { v.currentTime = t; v.play().catch(() => {}); }; v.readyState >= 1 ? go() : (v.addEventListener('loadedmetadata', go, { once: true }), v.load()); return true; };
  document.addEventListener('click', e => { const a = e.target.closest('[data-t]'); if (a && a.dataset.t !== '' && seek(+a.dataset.t)) { e.preventDefault(); history.replaceState(null, '', '#t=' + a.dataset.t); } });
  const h = location.hash.match(/^#t=(\d+)/); if (h) addEventListener('load', () => seek(+h[1]));

  // the bay: the cast introduces itself, once, when the bay is on screen
  const bay = document.querySelector('.bayhero');
  if (bay && D.talk) {
    const by = w => bay.querySelector(`.cam[data-who="${w}"]`); let started = false;
    const run = () => { if (started) return; started = true; D.talk.forEach(([w, t], i) => setTimeout(() => { const c = by(w); c && say(c, t, 3000); }, 700 + i * 3100)); };
    new IntersectionObserver(es => es.forEach(e => e.isIntersecting && run()), { threshold: .4 }).observe(bay);
  }
})();
