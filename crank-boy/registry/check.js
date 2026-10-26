// Check the shared registry before committing: node registry/check.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..');
const ctx = { window: {} };
for (const f of ['registry.js', 'notes.js', 'library.js', 'films.js', 'kit.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname, f), 'utf8'), ctx, { filename: f });
const R = ctx.window.CRANK, N = ctx.window.CRANK_NOTES, T = ctx.window.CRANK_TEXT;
const errs = [];
const exists = p => !p || p.startsWith('#') || p.startsWith('http') || fs.existsSync(path.join(root, p.split('#')[0]));
const agents = new Set(R.agents.map(a => a.id));
const prompts = new Set(R.prompts.map(p => p.id)), models = new Set(R.models.map(m => m.id));
R.agents.forEach(a => { if (!prompts.has(a.prompt)) errs.push(`agent ${a.id}: unknown prompt ${a.prompt}`); if (!models.has(a.model)) errs.push(`agent ${a.id}: unknown model ${a.model}`); });
const ids = new Set();
R.versions.forEach(v => {
  if (ids.has(v.id)) errs.push(`version ${v.id}: duplicate id`); ids.add(v.id);
  if (!agents.has(v.agent)) errs.push(`version ${v.id}: unknown agent ${v.agent}`);
  for (const k of ['play', 'making', 'mirror', 'card']) if (!exists(v[k])) errs.push(`version ${v.id}: ${k} file missing: ${v[k]}`);
  for (const k of ['tag', 'title', 'status', 'youPlay', 'line']) if (!v[k]) errs.push(`version ${v.id}: missing ${k}`);
});
R.proposals.forEach(p => { if (!exists(p.text)) errs.push(`proposal ${p.id}: missing ${p.text}`); });
R.library.forEach(l => {
  if (!exists(l.file)) errs.push(`library ${l.key}: missing ${l.file}`);
  else if (T[l.key] !== fs.readFileSync(path.join(root, l.file), 'utf8').trim()) errs.push(`library ${l.key}: library.js is stale, run python3 registry/build_library.py`);
});
const nids = new Set();
N.forEach(n => {
  if (nids.has(n.id)) errs.push(`note ${n.id}: duplicate id`); nids.add(n.id);
  if (!agents.has(n.from)) errs.push(`note ${n.id}: unknown sender ${n.from}`);
  (n.to || []).forEach(t => { if (t !== 'all' && !agents.has(t)) errs.push(`note ${n.id}: unknown recipient ${t}`); });
  if (n.re && !N.some(m => m.id === n.re)) errs.push(`note ${n.id}: answers unknown note ${n.re}`);
});

// films.js: every film has a poster and, if local, a file; ids are unique; every group exists
const FI = ctx.window.CRANK_FILMS, KIT = ctx.window.CRANK_KIT;
if (FI) {
  const g = new Set(FI.groups.map(x => x.id)), fids = new Set();
  FI.films.forEach(f => {
    if (fids.has(f.id)) errs.push(`film ${f.id}: duplicate id`); fids.add(f.id);
    if (!g.has(f.group)) errs.push(`film ${f.id}: unknown group ${f.group}`);
    if (f.thumb && !exists(f.thumb)) errs.push(`film ${f.id}: thumb missing: ${f.thumb}`);
    if (f.src && f.src.local && !exists(f.src.local)) errs.push(`film ${f.id}: file missing: ${f.src.local}`);
    if (!f.src && !f.open && !f.external) errs.push(`film ${f.id}: nothing to play or open`);
    (f.links || []).forEach(l => { if (l.href && !l.href.startsWith('http') && !exists(l.href.split('?')[0])) errs.push(`film ${f.id}: link missing: ${l.href}`); });
  });
  R.versions.filter(v => v.film).forEach(v => { if (!fids.has(v.id + '-played')) errs.push(`version ${v.id}: film is not in films.js, run registry/build_films.py`); });
  R.shorts.forEach(s => { if (!fids.has(s.id)) errs.push(`short ${s.id}: not in films.js, run registry/build_films.py`); });
}
if (KIT) {
  KIT.cards.forEach(c => { for (const k of ['image', 'clean']) if (!exists(c[k])) errs.push(`kit ${c.id}: ${k} missing`); c.parts.forEach(p => { if (!exists(p.file)) errs.push(`kit ${c.id}: part missing ${p.file}`); }); });
  KIT.plates.forEach(p => { for (const k of ['video', 'strip']) if (!exists(p[k])) errs.push(`kit plate ${p.name}: ${k} missing`); });
  KIT.v9.cast.concat(KIT.v9.layers, KIT.v9.plates).forEach(x => { if (!exists(x.file)) errs.push(`kit v9: missing ${x.file}`); });
  KIT.tools.forEach(t => { if (!exists(t.file)) errs.push(`kit tool: missing ${t.file}`); });
}
if (errs.length) { console.log(errs.join('\n')); process.exit(1); }
console.log(`OK: ${R.versions.length} versions, ${R.agents.length} seats, ${N.length} notes, ${R.library.length} library texts, ${FI ? FI.films.length : 0} films, ${KIT ? KIT.cards.reduce((a, c) => a + c.parts.length, 0) : 0} kit pieces`);
