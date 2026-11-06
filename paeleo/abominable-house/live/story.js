// THE STORY ENGINE: how believable is each deed, given who these four are and what has already happened?
// P(film) = Π P(event_k | state_k). Each event is scored from (1) the cast's traits and goals (LEGOS entities),
// (2) the house's laws, including the exclusion rules Calvino's narrator lays down (paraphrased), (3) the ledger's minds.
window.STORY=(function(){
 const L0=window.LEDGER,IDS=L0.IDS,ORDER=L0.ORDER,PAIRS=L0.PAIRS;
 const NAMES=['Blackmail','Drugging','Incitement to Suicide','Knifing','Prostitution','Threatening with a Gun','Tying and Gagging','Rape','Seduction','Slander','Snooping','Strangling'];
 // ---- LEGOS entities: traits and goals (what each sack wants, and the lie it lives by) ----
 const CAST={
  R:{name:'Widow Roessler',type:'character',traits:['shrewd','miserly','old','appetitive','manipulative'],goal:'keep the house and its income',lie:'Possession equals safety.'},
  B:{name:'Belindo Kid',type:'character',traits:['strong','impressionable','gentle','loyal','over the hill'],goal:'win one more season',lie:'Strength makes me safe.'},
  I:{name:'Inigo',type:'character',traits:['listless','careless','addicted','playful','disinherited'],goal:'escape into oblivion',lie:'Nothing I do counts.'},
  O:{name:'Ogiva',type:'character',traits:['vain','cold','precise','volatile','bald under the wig'],goal:'be seen and keep her looks',lie:'Being looked at is being safe.'}};
 // motive: how much each deed fits who the doer is (trait alignment), 0..1
 const MOTIVE={
  blackmail:{R:.85,O:.55,I:.3,B:.1}, drugging:{I:.75,R:.6,O:.4,B:.15}, incitement:{R:.55,O:.6,I:.3,B:.08},
  knifing:{O:.55,R:.35,I:.4,B:.12}, prostitution:{R:.85,B:.35,I:.3,O:.2}, gun:{I:.5,O:.45,R:.45,B:.3},
  tying:{B:.8,R:.25,I:.2,O:.2}, assault:{B:.25,I:.25,R:.25,O:.25}, seduction:{O:.85,R:.55,I:.5,B:.35},
  slander:{R:.75,O:.55,I:.35,B:.15}, snooping:{I:.7,R:.65,O:.4,B:.2}, strangling:{B:.9,R:.25,I:.2,O:.25}};
 // victimhood: who invites which deed
 const TARGET={blackmail:{B:.7,I:.7,O:.6,R:.4},drugging:{B:.8,I:.4,R:.5,O:.5},incitement:{B:.8,I:.6,O:.4,R:.2},seduction:{I:.7,O:.6,B:.7,R:.4},prostitution:{I:.7,O:.7,B:.5,R:.15}};
 const HOSTILE=['blackmail','drugging','incitement','knifing','prostitution','gun','tying','assault','slander','snooping','strangling'];
 const sig=x=>1/(1+Math.exp(-x));
 // raw believability of one event in a state, with the reasons (for the reading)
 function rate(st,k,A,V,L){const d=ORDER[k];const why=[];let s=MOTIVE[d][A]*(TARGET[d]?TARGET[d][V]:.6)/.6;
  why.push(`${CAST[A].name.split(' ').pop()} fits ${NAMES[k].toLowerCase()}: ${MOTIVE[d][A].toFixed(2)}`);
  // the dead cannot act or be acted on
  if(!st.alive[A]){s*=.02;why.push('the doer is dead')}else if(!st.alive[V]){s*=.03;why.push('the victim is dead')}
  else if(st.tiedUntil&&st.tiedUntil[A]!=null&&k<st.tiedUntil[A]){s*=.05;why.push('the doer is tied up')}
  // strength: physical deeds need it, or a weakened victim
  const bA=st.belief[A][A].str.m,bV=st.belief[A][V].str.m,weak=['drowsy','rope','gag','emptied'].some(x=>st.body[V].includes(x));
  if(['tying','strangling','assault'].includes(d)){const p=sig(1.4*(bA-bV)+(weak?1.6:0));s*=.3+p;why.push(`overpowering: ${p.toFixed(2)}${weak?' (victim weakened)':''}`)}
  // Calvino's laws (paraphrased from the narrator's flow-chart)
  const did=(dd,a,v)=>L.ev.slice(0,k).some(e=>e.deed===dd&&e.A===a&&e.V===v);
  if(d==='strangling'&&V==='B'){s*=.25;why.push('no one strangles the wrestler')}
  if(d==='knifing'&&A==='B'){why.push('the wrestler would rather strangle')}
  if(d==='tying'&&V==='B'&&A!=='B'){if(did('gun',A,'B')){s*=2.2;why.push('he was held at gunpoint first')}else{s*=.15;why.push('the wrestler cannot be tied unless first held at gunpoint')}}
  if(d==='tying'&&did('gun',A,V)&&V!=='B'){s*=1.6;why.push('gun first, then rope')}
  if(d==='seduction'&&did('assault',A,V)){s*=.06;why.push('one who forced does not then court')}
  if(d==='seduction'&&did('prostitution',A,V)){s*=.3;why.push('courting after selling is wasted effort')}
  if(d==='snooping'&&did('slander',A,V)){s*=.2;why.push('a slanderer has nothing left to snoop for')}
  if(d==='blackmail'&&did('slander',A,V)){s*=.2}
  const deadly=['knifing','incitement','strangling'].filter(dd=>L.ev.slice(0,k).some(e=>e.deed===dd&&e.V===V)).length;
  if(d==='strangling'&&deadly>=2){s*=.15;why.push('three deadly deeds on one sack')}
  // minds: grudge and fear drive hostility; guilt holds back repeat harm; desire draws courtship
  const m=st.mind[A][V];
  if(HOSTILE.includes(d)){s*=1+m.grudge*.9+m.fear*.3-m.guilt*.6;if(m.grudge>.3)why.push(`grudge ${m.grudge.toFixed(2)}`);if(m.guilt>.3)why.push(`guilt ${m.guilt.toFixed(2)} holds back`)}
  if(d==='seduction'){s*=1+m.desire+st.mind[V][A].desire*.5-m.grudge*.5}
  // the house reads the doer (Barthes): a PREDATOR is believed capable
  s*=1+(st.myth[A].PREDATOR||0)*.6*(HOSTILE.includes(d)?1:-.5);
  return{raw:Math.max(0,Math.min(1,s)),why}}
 function tier(p){return p<=.05?'PREPOSTEROUS':p<=.30?'POSSIBLE':p<=.70?'PLAUSIBLE':p<=.95?'PROBABLE':'CERTAIN'}
 // conditional distribution over the 12 pairs for deed k
 function dist(L,k){const st=L.states[k];const r=PAIRS.map(([A,V])=>rate(st,k,A,V,L).raw+1e-4);const z=r.reduce((a,b)=>a+b,0);return r.map(x=>x/z)}
 // score a whole film
 function score(film){const L=L0.run(film);let logp=0,lograw=0;const ev=[];
  for(let k=0;k<12;k++){const[A,V]=PAIRS[film[k]];const r=rate(L.states[k],k,A,V,L);const p=dist(L,k)[film[k]];logp+=Math.log(p);lograw+=Math.log(Math.max(1e-4,r.raw));ev.push({k,A,V,raw:r.raw,p,tier:tier(r.raw),why:r.why})}
  const believ=Math.exp(lograw/12);return{film,logp,believ,tier:tier(believ),ev,L}}
 // ---- MONTE CARLO TREE SEARCH over the 12-step tree (UCT); reward = film believability ----
 function mcts(iter=3000,c=.35,seed=1){let rs=seed;const rnd=()=>{rs=(rs*16807)%2147483647;return rs/2147483647};
  const root={n:0,w:0,kids:{},prefix:[]};const best=new Map();
  const sample=probs=>{let u=rnd(),a=0;for(let i=0;i<12;i++){a+=probs[i];if(u<=a)return i}return 11};
  for(let it=0;it<iter;it++){let node=root;const path=[root];
   while(node.prefix.length<12){const kids=Object.keys(node.kids);if(kids.length<12){// expand one untried move, chosen by the model's own prior
     const L=L0.run(node.prefix.concat(Array(12-node.prefix.length).fill(0)));const pr=dist(L,node.prefix.length);let a;let tries=0;do{a=sample(pr);tries++}while(node.kids[a]&&tries<40);if(node.kids[a]){a=+kids[0]}
     if(!node.kids[a]){node.kids[a]={n:0,w:0,kids:{},prefix:node.prefix.concat([a])};node=node.kids[a];path.push(node);break}}
    let bestU=-1,bk=null;for(const a of Object.keys(node.kids)){const ch=node.kids[a];const u=ch.w/(ch.n||1)+c*Math.sqrt(Math.log(node.n+1)/(ch.n||1));if(u>bestU){bestU=u;bk=ch}}node=bk;path.push(node)}
   // rollout: finish the film by sampling each deed from the model's conditional distribution
   const film=node.prefix.slice();while(film.length<12){const L=L0.run(film.concat(Array(12-film.length).fill(0)));film.push(sample(dist(L,film.length)))}
   const sc=score(film);const key=film.join(',');if(!best.has(key))best.set(key,sc);for(const p of path){p.n++;p.w+=sc.believ}}
  return[...best.values()].sort((a,b)=>b.believ-a.believ)}
 // ---- LEGOS export of a film ----
 function legos(film){const S=score(film),L=S.L,fin=L.states[12];const q=s=>JSON.stringify(s);
  let y=`title: "The Abominable House, film ${film.join(',')}"\ndescription: "${S.ev.map(e=>L0.reading(L,e.k).headline).slice(0,2).join(', ').toLowerCase()} … ${fin.impossible.length} contradictions"\nlocation: "Widow Roessler's boarding house on a hump of wasteland"\nentities:\n`;
  for(const id of IDS){const c=CAST[id];y+=`  - id: ${id}\n    type: character\n    name: ${q(c.name)}\n    traits: [${c.traits.map(q).join(', ')}]\n    state: {alive: ${fin.alive[id]}, body: [${fin.body[id].join(', ')}], archetype: ${L0.dominant(fin.myth[id])}}\n`}
  for(const e of fin.evidence)y+=`  - id: ev${e.k}\n    type: object\n    name: ${q(e.kind)}\n    left_by: ${e.deed}\n`;
  y+=`goals:\n`+IDS.map(id=>`  - id: g_${id}\n    name: ${q(CAST[id].goal)}\n    owner: ${id}\n    status: ${!fin.alive[id]?'failed':(S.ev.filter(e=>e.V===id).length>=4?'failed':'pending')}`).join('\n')+'\n';
  y+=`obstacles:\n`+S.ev.filter(e=>HOSTILE.includes(ORDER[e.k])).map(e=>`  - id: ob${e.k}\n    name: ${q(NAMES[e.k]+' by '+CAST[e.A].name)}\n    affects: g_${e.V}`).join('\n')+'\n';
  y+=`shifts:\n`+S.ev.map(e=>{const a=L.states[e.k],b=L.states[e.k+1];return `  - id: sh${e.k}\n    name: ${q(L0.reading(L,e.k).headline)}\n    causes: [ob${e.k}]\n    results_in: "${e.V}: ${L0.dominant(a.myth[e.V])} -> ${L0.dominant(b.myth[e.V])}${!b.alive[e.V]&&a.alive[e.V]?' (dies)':''}"\n    probability: ${e.p.toFixed(3)}\n    believability: ${e.raw.toFixed(2)}  # ${e.tier}`}).join('\n')+'\n';
  y+=`relations:\n`+S.ev.map(e=>`  - [${ORDER[e.k]}] ${e.A} -> ${e.V}`).join('\n')+'\n';
  y+=`timeline:\n  - id: t_index\n    description: "the twelve entries, in the copybook's order"\n    scenes:\n`+S.ev.map(e=>`      - id: s${e.k+1}\n        description: ${q(NAMES[e.k]+': '+CAST[e.A].name+' to '+CAST[e.V].name)}\n        entities: [${e.A}, ${e.V}]`).join('\n')+`\n      - id: s13\n        description: "Arson. The index does not say who."\n        entities: [${IDS.filter(i=>fin.alive[i]).join(', ')}]\n`;
  return y}
 // ---- Kurosawa: the lie each sack lives by, and whether this film breaks it ----
 const BREAKS={R:e=>e.V==='R'&&['blackmail','prostitution','knifing','assault','slander'].includes(ORDER[e.k]),B:e=>e.V==='B'&&['drugging','tying','incitement','gun'].includes(ORDER[e.k]),I:e=>(e.A==='I'&&['knifing','strangling','incitement'].includes(ORDER[e.k])),O:e=>e.V==='O'&&['slander','snooping','assault','knifing'].includes(ORDER[e.k])};
 function lies(film){const S=score(film),L=S.L;return IDS.map(id=>{const br=S.ev.find(e=>BREAKS[id](e)&&L.states[e.k].alive[id]);const dead=L.states[12].alive[id]?null:L.states[12].deadAt[id];
   return{id,lie:CAST[id].lie,broken:br?br.k:null,dead}})}
 return{CAST,NAMES,rate,tier,dist,score,mcts,legos,lies}})();
