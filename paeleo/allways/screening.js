/* ALLWAYS screening room. Reads screening.json (built by tools/allways/screening.py) and plays every film of
   every run in one frame at one loudness. Two <video> elements alternate so the next film is loaded and
   ready before the current one ends. */
(function () {
  'use strict';
  var SITE = '../../';                                  // manifest paths are relative to the repository root
  var FAM_ORDER = { scion: 0, broll: 1, other: 2 };
  var FAM_NAME = { scion: 'SCION operators', broll: 'B-roll of civilization', other: 'Collections and studies' };
  var BROLL = ['nobody-home', 'almost-human', 'terra-incognita', 'split-second', 'cut-to-the-chase', 'kinetic', 'zero-memory', 'homonym', 'anybody-anywhere', 'collective-inventories', 'mnemonil', 'planimetric'];
  var $ = function (id) { return document.getElementById(id); };
  var vids = [$('v0'), $('v1')];
  var S = { M: null, films: [], runs: {}, runOn: {}, famOn: {}, order: 'prompt', copies: false, queue: [], i: -1, active: 0,
            started: false, ctx: null, nodes: [null, null], muted: false, loaded: [null, null], seq: 0, advancing: false };

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function fmt(t) { t = Math.max(0, t || 0); var m = Math.floor(t / 60), s = Math.floor(t % 60); return m + ':' + (s < 10 ? '0' : '') + s; }
  function toast(msg) { var t = $('toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toast.h); toast.h = setTimeout(function () { t.classList.remove('show'); }, 3200); }
  function aspectName(w, h) { if (!w || !h) return ''; var r = w / h; if (Math.abs(r - 16 / 9) < .03) return '16:9'; if (Math.abs(r - 4 / 3) < .03) return '4:3'; if (Math.abs(r - 5 / 4) < .03) return '5:4'; return w + '×' + h; }
  function runRank(id) { var o = S.M.run_order || []; var i = o.indexOf(id); return i < 0 ? 99 : i; }
  function keyRank(f) { if (f.family === 'scion') return Number(f.key) || 0; if (f.family === 'broll') { var i = BROLL.indexOf(f.key); return i < 0 ? 99 : i; } return 0; }
  function groupLabel(f) {
    if (S.order === 'run') return S.runs[f.run] ? S.runs[f.run].name : f.run;
    if (f.family === 'scion') return 'SCION ' + String(f.key).padStart(3, '0');
    if (f.family === 'broll') return 'B-roll · ' + f.key.replace(/-/g, ' ');
    return 'Collections and studies';
  }

  // ---- queue -----------------------------------------------------------------------------------------
  function cmpPrompt(a, b) {
    return (FAM_ORDER[a.family] - FAM_ORDER[b.family]) || (keyRank(a) - keyRank(b)) || (a.family === 'other' ? a.id.localeCompare(b.id) : 0) || (runRank(a.run) - runRank(b.run)) || a.id.localeCompare(b.id);
  }
  function build() {
    var keep = S.queue[S.i] ? S.queue[S.i].f.id : null;
    var fs = S.films.filter(function (f) { return S.runOn[f.run] && S.famOn[f.family]; });
    if (S.order === 'prompt') fs.sort(cmpPrompt);
    else if (S.order === 'run') fs.sort(function (a, b) { return (runRank(a.run) - runRank(b.run)) || cmpPrompt(a, b); });
    else { var seed = 7; var rnd = function () { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }; fs.sort(cmpPrompt); for (var i = fs.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)); var t = fs[i]; fs[i] = fs[j]; fs[j] = t; } }
    S.queue = [];
    fs.forEach(function (f) {
      S.queue.push({ f: f, ci: 0 });
      if (S.copies) for (var c = 1; c < f.copies.length; c++) S.queue.push({ f: f, ci: c });
    });
    S.i = keep ? S.queue.findIndex(function (q) { return q.f.id === keep; }) : -1;
    renderList(); tally(); if (S.started) preloadNext();
  }
  function tally() {
    var secs = S.queue.reduce(function (a, q) { return a + (q.f.copies[q.ci].duration || 0); }, 0);
    $('tally').textContent = S.queue.length + ' to play · ' + Math.floor(secs / 3600) + ' h ' + String(Math.floor(secs % 3600 / 60)).padStart(2, '0') + ' min';
  }

  // ---- list and chips --------------------------------------------------------------------------------
  function renderList() {
    var ol = $('list'); ol.replaceChildren(); var last = null;
    S.queue.forEach(function (q, idx) {
      var f = q.f, g = groupLabel(f);
      if (g !== last) { var h = el('li', 'grp', g); ol.appendChild(h); last = g; }
      var li = el('li'), b = el('button', 'row'); b.type = 'button'; b.dataset.idx = idx;
      var im = el('img'); im.loading = 'lazy'; im.alt = ''; im.src = SITE + f.poster; im.width = 72; im.height = 54;
      var t = el('span'); var name = el('b', '', f.title.replace(/ — .*$/, ''));
      var meta = el('small', '', (S.runs[f.run] ? S.runs[f.run].name : f.run) + ' · ' + fmt(f.copies[q.ci].duration) + (q.ci ? ' · ' + f.copies[q.ci].label : ''));
      t.append(name, meta); b.append(im, t);
      b.addEventListener('click', function () { go(idx, true); });
      li.appendChild(b); ol.appendChild(li);
    });
    mark();
  }
  function mark() {
    document.querySelectorAll('#list button.row').forEach(function (b) { b.setAttribute('aria-current', String(Number(b.dataset.idx) === S.i)); });
    var cur = document.querySelector('#list button.row[aria-current="true"]');
    if (cur && S.started) { var box = $('list'); var r = cur.getBoundingClientRect(), br = box.getBoundingClientRect(); if (r.top < br.top + 40 || r.bottom > br.bottom) box.scrollTop += r.top - br.top - 60; }   // scroll the list only, never the page
  }
  function chips() {
    var rc = $('runs'); rc.replaceChildren();
    S.M.runs.forEach(function (r) {
      var b = el('button', 'r-' + r.id, r.name); b.type = 'button'; b.setAttribute('aria-pressed', 'true');
      b.addEventListener('click', function () { S.runOn[r.id] = !S.runOn[r.id]; b.setAttribute('aria-pressed', String(S.runOn[r.id])); build(); });
      rc.appendChild(b);
    });
    var fc = $('fams'); fc.replaceChildren();
    ['scion', 'broll', 'other'].forEach(function (k) {
      var b = el('button', '', FAM_NAME[k]); b.type = 'button'; b.setAttribute('aria-pressed', 'true');
      b.addEventListener('click', function () { S.famOn[k] = !S.famOn[k]; b.setAttribute('aria-pressed', String(S.famOn[k])); build(); });
      fc.appendChild(b);
    });
  }

  // ---- audio levelling -------------------------------------------------------------------------------
  function audioOn() {
    if (S.ctx) { if (S.ctx.state === 'suspended') S.ctx.resume(); return; }
    var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    try {
      S.ctx = new AC();
      vids.forEach(function (v, i) { var src = S.ctx.createMediaElementSource(v), g = S.ctx.createGain(); src.connect(g); g.connect(S.ctx.destination); S.nodes[i] = g; });
      vids.forEach(function (v, i) { applyGain(i); });
    } catch (e) { S.ctx = null; S.nodes = [null, null]; }
  }
  function applyGain(i) {
    var db = Number(vids[i].dataset.gain || 0), lin = Math.pow(10, db / 20);
    if (S.nodes[i]) { S.nodes[i].gain.value = S.muted ? 0 : lin; vids[i].volume = 1; }
    else vids[i].volume = S.muted ? 0 : Math.min(1, lin);          // without Web Audio the element can only be turned down
  }

  // ---- playback --------------------------------------------------------------------------------------
  function srcOf(q) { return SITE + q.f.copies[q.ci].src; }
  function load(slot, q) {
    var v = vids[slot], c = q.f.copies[q.ci];
    v.dataset.gain = c.gain_db || 0; v.dataset.key = q.f.id + '#' + q.ci;
    S.loaded[slot] = q;
    if (v.getAttribute('src') !== srcOf(q)) { v.src = srcOf(q); v.load(); }
    v.poster = SITE + q.f.poster; applyGain(slot);
  }
  function preloadNext() {
    var n = S.queue[S.i + 1]; if (!n) return;
    var idle = 1 - S.active, key = n.f.id + '#' + n.ci;
    if (vids[idle].dataset.key !== key) load(idle, n);
  }
  function go(idx, user, startAt) {
    if (idx < 0 || idx >= S.queue.length) { if (idx >= S.queue.length) { stopAll(); toast('End of the programme'); } return; }
    var wasStarted = S.started;
    if (user) { $('big').hidden = true; S.started = true; audioOn(); }
    var q = S.queue[idx], myseq = ++S.seq;
    // while running, the next film always goes on the idle element, so the one on screen is never touched
    var slot = wasStarted ? 1 - S.active : S.active;
    load(slot, q);                                       // no reload if the idle element already holds this film
    var v = vids[slot];
    S.i = idx; S.advancing = false; mark(); meta(q);
    history.replaceState(null, '', '#' + q.f.id);
    var begin = function () {
      if (myseq !== S.seq) return;
      if (startAt || v.currentTime > 0.05) { try { v.currentTime = startAt || 0; } catch (e) { /* not seekable yet */ } }
      var p = v.play(); if (p && p.catch) p.catch(function () { $('big').hidden = false; S.started = false; setPlayIcon(); });
      vids.forEach(function (x, i) { x.classList.toggle('on', i === slot); });
      var old = vids[S.active];
      if (slot !== S.active) setTimeout(function () { if (vids[S.active] !== old) old.pause(); }, 220);
      S.active = slot; setPlayIcon(); mediaSession(q);
      setTimeout(function () { if (myseq === S.seq) preloadNext(); }, 320);   // after the old frame has faded out
    };
    if (v.readyState >= 3) begin(); else { var once = function () { v.removeEventListener('canplay', once); begin(); }; v.addEventListener('canplay', once); }
  }
  function slotOf(v) { return vids.indexOf(v); }
  function next() { go(S.i + 1, false); }
  function stopAll() { vids.forEach(function (v) { v.pause(); }); setPlayIcon(); }
  function setPlayIcon() { var v = vids[S.active]; $('play').textContent = (v.paused || !S.started) ? '▶' : '❚❚'; }
  function toggle() {
    if (!S.started) { if (S.i < 0) go(0, true); else go(S.i, true, vids[S.active].currentTime); return; }
    var v = vids[S.active]; if (v.paused) v.play(); else v.pause(); setPlayIcon();
  }

  // ---- panel -----------------------------------------------------------------------------------------
  function meta(q) {
    var f = q.f, c = f.copies[q.ci], run = S.runs[f.run] || { name: f.run };
    var box = $('now'); box.replaceChildren();
    var rl = el('div', 'runline'); var chip = el('span', 'chip r-' + f.run, run.name); rl.append(chip, document.createTextNode('  ' + groupLabel({ run: f.run, family: f.family, key: f.key }) + (S.order === 'run' ? '' : '')));
    box.append(rl, el('h1', '', f.title.replace(/ — .*$/, '')));
    if (f.sub || / — /.test(f.title)) box.append(el('p', 'sub', f.sub || f.title.replace(/^.*? — /, '')));
    var d1 = el('dl'), d2 = el('dl');
    function row(dl, k, v) { if (!v) return; dl.append(el('dt', '', k), el('dd', '', v)); }
    row(d1, 'State', [f.state, f.verdict].filter(function (x) { return x; }).join(' · '));
    var a = d1.appendChild(el('dt', '', 'Case study')); var dd = el('dd'); var link = el('a', '', 'Open the film’s own page ↗'); link.href = SITE + f.case; dd.appendChild(link); d1.appendChild(dd);
    var gain = c.silent ? 'no sound to level' : (c.gain_db >= 0 ? '+' : '−') + Math.abs(c.gain_db).toFixed(1) + ' dB (measured ' + (c.lufs == null ? '?' : c.lufs.toFixed(1)) + ' LUFS, target ' + S.M.target_lufs + ')';
    row(d2, 'Frame', aspectName(c.w, c.h) + (Math.abs((c.w / c.h) - 16 / 9) < .03 ? ', fills the frame' : ', fitted whole, no cropping') + ' · ' + Math.round(c.fps) + ' fps');
    row(d2, 'Volume', gain);
    if (f.copies.length > 1) {
      d2.append(el('dt', '', 'Copies of this film')); var dd2 = el('dd', 'copies');
      f.copies.forEach(function (cc, ci) {
        var b = el('button', '', cc.label + ' · ' + fmt(cc.duration)); b.type = 'button'; b.setAttribute('aria-pressed', String(ci === q.ci));
        b.addEventListener('click', function () { var t = vids[S.active].currentTime; var at = S.queue.findIndex(function (x) { return x.f === f && x.ci === ci; });
          if (at >= 0) go(at, true, 0); else { S.queue[S.i] = { f: f, ci: ci }; go(S.i, true, 0); } });
        dd2.appendChild(b);
      });
      d2.appendChild(dd2);
    }
    box.append(d1, d2);
    document.title = f.title.replace(/ — .*$/, '') + ' · ALLWAYS Screening Room';
  }
  function mediaSession(q) {
    if (!('mediaSession' in navigator) || !window.MediaMetadata) return;
    var f = q.f; navigator.mediaSession.metadata = new MediaMetadata({ title: f.title.replace(/ — .*$/, ''), artist: (S.runs[f.run] || {}).name || f.run, album: 'ALLWAYS', artwork: [{ src: new URL(SITE + f.poster, location.href).href, sizes: '320x180' }] });
    navigator.mediaSession.setActionHandler('nexttrack', function () { next(); });
    navigator.mediaSession.setActionHandler('previoustrack', function () { go(S.i - 1, true); });
  }

  // ---- wiring ----------------------------------------------------------------------------------------
  function tick() {
    var v = vids[S.active]; if (!S.started || !v.duration || isNaN(v.duration)) return;
    $('seek').value = Math.round(v.currentTime / v.duration * 1000);
    $('time').textContent = fmt(v.currentTime) + ' / ' + fmt(v.duration);
    if (!S.advancing && !v.paused && v.duration - v.currentTime < 0.09 && S.queue[S.i + 1]) { S.advancing = true; next(); }
  }
  vids.forEach(function (v, i) {
    v.addEventListener('ended', function () { if (i === S.active && !S.advancing) { S.advancing = true; if (S.queue[S.i + 1]) next(); else { stopAll(); toast('End of the programme'); } } });
    v.addEventListener('play', setPlayIcon); v.addEventListener('pause', setPlayIcon);
    v.addEventListener('error', function () {
      if (i !== S.active || !S.started) return;
      toast('Could not load “' + (S.queue[S.i] ? S.queue[S.i].f.title : '') + '”; skipping'); setTimeout(next, 700);
    });
  });
  $('big').addEventListener('click', function () { go(Math.max(0, S.i), true); });
  $('play').addEventListener('click', toggle);
  $('next').addEventListener('click', function () { if (!S.started) { go(Math.min(S.queue.length - 1, S.i + 1), true); } else go(S.i + 1, true); });
  $('prev').addEventListener('click', function () { var v = vids[S.active]; if (S.started && v.currentTime > 3) go(S.i, true); else go(Math.max(0, S.i - 1), true); });
  $('seek').addEventListener('input', function () { var v = vids[S.active]; if (v.duration) v.currentTime = this.value / 1000 * v.duration; });
  $('mute').addEventListener('click', function () { S.muted = !S.muted; this.setAttribute('aria-pressed', String(S.muted)); vids.forEach(function (v, i) { applyGain(i); }); });
  $('fs').addEventListener('click', function () { var st = $('stage'); (st.requestFullscreen || st.webkitRequestFullscreen || function () {}).call(st); });
  $('order').addEventListener('change', function () { S.order = this.value; build(); });
  $('copies').addEventListener('change', function () { S.copies = this.checked; build(); });
  document.addEventListener('keydown', function (e) {
    if (e.target.matches('input[type=range],select,input,textarea') && e.key !== 'Escape') return;
    if (e.altKey || e.metaKey || e.ctrlKey) return;
    if (e.key === ' ') { e.preventDefault(); toggle(); } else if (e.key === 'n' || e.key === 'ArrowRight') go(S.i + 1, true);
    else if (e.key === 'p' || e.key === 'ArrowLeft') go(Math.max(0, S.i - 1), true); else if (e.key === 'f') $('fs').click(); else if (e.key === 'm') $('mute').click();
  });
  window.addEventListener('hashchange', function () { var id = location.hash.slice(1), at = S.queue.findIndex(function (q) { return q.f.id === id && q.ci === 0; }); if (at >= 0 && at !== S.i) go(at, S.started); });
  setInterval(tick, 50);

  fetch('screening.json').then(function (r) { return r.json(); }).then(function (M) {
    S.M = M; S.films = M.films; M.runs.forEach(function (r) { S.runs[r.id] = r; S.runOn[r.id] = true; });
    ['scion', 'broll', 'other'].forEach(function (k) { S.famOn[k] = true; });
    chips(); build();
    var start = S.queue.findIndex(function (q) { return q.f.id === location.hash.slice(1); });
    var first = start >= 0 ? start : 0; S.i = first; meta(S.queue[first]); mark(); load(0, S.queue[first]); vids[0].classList.add('on'); preloadNext();
    $('now').dataset.ready = '1';
  }).catch(function (e) { $('now').textContent = 'The programme could not be loaded (' + e.message + '). Each run’s own page lists its films.'; });
})();
