// Exhaustive playtest of game.js: explores every reachable state.
const G = require('./school-2000-engine.js');
const key = s => JSON.stringify({ ...s, log: 0, ending: s.ending && s.ending.title, notes: [...s.notes].sort(), heard: 0 });
const seen = new Map();
const endings = {}, noteReach = {}, assumptionsPerEnd = [];
let dead = [], noops = [], maxDepth = 0, states = 0;
const q = [[G.init(), 0]];
seen.set(key(q[0][0]), 1);
while (q.length) {
  const [s, d] = q.shift(); states++; maxDepth = Math.max(maxDepth, d);
  if (s.phase === 'end') {
    endings[s.ending.title] = (endings[s.ending.title] || 0) + 1;
    s.notes.forEach(n => noteReach[n] = 1);
    assumptionsPerEnd.push(new Set(s.notes.map(n => G.NOTES[n].a)).size);
    continue;
  }
  const A = G.actions(s).filter(a => a.ok);
  if (!A.length) dead.push(s);
  for (const a of A) {
    const n = G.act(s, a.id); const k = key(n);
    if (k === key(s)) { noops.push([s.tick, s.phase, a.id]); continue; }
    if (!seen.has(k)) { seen.set(k, 1); q.push([n, d + 1]); }
  }
}
const all = Object.keys(G.NOTES);
console.log('states explored:', states, ' max depth:', maxDepth);
console.log('dead ends (no enabled action, not ended):', dead.length);
console.log('no-op actions:', noops.length, noops.slice(0, 5));
console.log('endings reached:', endings);
console.log('notes reachable:', all.filter(n => noteReach[n]).length, '/', all.length, ' unreachable:', all.filter(n => !noteReach[n]));
const z = assumptionsPerEnd.filter(x => x === 0).length;
console.log('ending states:', assumptionsPerEnd.length, ' with zero assumptions reached:', z,
  ' mean assumptions per ending:', (assumptionsPerEnd.reduce((a, b) => a + b, 0) / assumptionsPerEnd.length).toFixed(2));
// the passive path
let s = G.init(); while (s.phase === 'lesson') s = G.act(s, 'listen'); s = G.act(s, 'r_trans');
console.log('passive path ending:', s.ending.title, ' notes:', s.notes);
// regressions from the critique
const run=ids=>{let s=G.init();for(const id of ids){const n=G.act(s,id);if(n===s)return {err:'disabled:'+id,s};s=n}return {s}};
let r=run(['listen','listen','listen','listen','listen','listen','listen','listen','listen','listen']);
console.log('passive: objective', r.s.objective, '| mentions book?', r.s.log.some(l=>/desk says/.test(l.t)));
r=run(['read','go','emile','emile','feed','listen','listen']);
console.log('feed path:', r.err||'', 'classHeardOld', r.s.classHeardOld, 'notes', r.s.notes.includes('hopper'));
r=run(['cap','listen','listen','listen','listen','listen','listen','lucie']);
console.log('cap-off lucie: same?', r.s.notes.includes('same'), 'knowT', r.s.knowT);
// late feed impossible
r=run(['read','go','emile','emile','listen','listen','listen']); console.log('feed after canal enabled?', G.actions(r.s).find(a=>a.id==='feed').ok, 'tick', r.s.tick);
// a curious path
s = G.init();
for (const id of ['listen','listen','listen','listen','listen','listen','read','lucie','show','go','hopper','emile','emile','feed','listen']) s = G.act(s, id);
console.log('curious path phase:', s.phase, 'tick', s.tick, 'patience', s.patience, 'notes', s.notes.length, 'fed', s.fed);
