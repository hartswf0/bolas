// THE AGENTS: the four sacks decide who does each deed.
// BDI (Rao & Georgeff; Bratman): Beliefs = the PLoT beliefs and what each sack knows; Desires = its goal (LEGOS) and its
// feelings toward each other; Intentions = a committed plan toward one other that persists until carried out.
// Memory stream (Park et al. 2023): every known event becomes a record with importance; retrieval scores
// recency + importance + relevance; reflections are written when importance accumulates; plans are recorded too.
// PIE (Hartsoe, Growing Entanglements): P = practical vs symbolic reasons, I = individual vs collective belief, E = entropy (how much chance).
window.AGENTS=(function(){
 const L0=window.LEDGER,S0=window.STORY,IDS=L0.IDS,ORDER=L0.ORDER,PAIRS=L0.PAIRS;
 const NM={R:'Roessler',B:'Belindo',I:'Inigo',O:'Ogiva'};
 const VERB={blackmail:'blackmailed',drugging:'drugged',incitement:'drove to despair',knifing:'knifed',prostitution:'sold',gun:'held at gunpoint',tying:'tied and gagged',assault:'assaulted',seduction:'seduced',slander:'slandered',snooping:'spied on',strangling:'strangled'};
 const HOSTILE=new Set(['blackmail','drugging','incitement','knifing','prostitution','gun','tying','assault','slander','snooping','strangling']);
 const MOT={blackmail:{R:.85,O:.55,I:.3,B:.1},drugging:{I:.75,R:.6,O:.4,B:.15},incitement:{R:.55,O:.6,I:.3,B:.08},knifing:{O:.55,R:.35,I:.4,B:.12},prostitution:{R:.85,B:.35,I:.3,O:.2},gun:{I:.5,O:.45,R:.45,B:.3},tying:{B:.8,R:.25,I:.2,O:.2},assault:{B:.25,I:.25,R:.25,O:.25},seduction:{O:.85,R:.55,I:.5,B:.35},slander:{R:.75,O:.55,I:.35,B:.15},snooping:{I:.7,R:.65,O:.4,B:.2},strangling:{B:.9,R:.25,I:.2,O:.25}};
 const sig=x=>1/(1+Math.exp(-x));
 // ---- utility of sack s doing deed k to v, under PIE ----
 function utility(st,k,s,v,mind,pie){const d=ORDER[k];
  // beliefs: individual (s's own) vs collective (the house's mean) — the I dial
  const bel=(t)=>{const own=st.belief[s][t];let m=0,h=0;for(const o of IDS){m+=st.belief[o][t].str.m;h+=st.belief[o][t].harm.m}return{str:lerp(m/4,own.str.m,pie.I),harm:lerp(h/4,own.harm.m,pie.I)}};
  const bs=bel(s),bv=bel(v);const weak=['drowsy','rope','gag','emptied'].some(x=>st.body[v].includes(x));
  // PRACTICAL reasons (Obeyesekere's side): interest, leverage, fear, capacity
  const m=st.mind[s][v];let P=MOT[d][s];
  if(HOSTILE.has(d))P*=1+m.grudge*1.2+m.fear*.5+m.debt*.4-m.guilt*.8; else P*=1+m.desire*1.4-m.grudge*.6;
  if(['tying','strangling','assault'].includes(d))P*=.3+sig(1.4*(bs.str-bv.str)+(weak?1.6:0));
  if(d==='gun'||d==='blackmail')P*=1+bv.harm*.6; // leverage against a dangerous one
  if(d==='strangling'&&v==='B')P*=.2;if(d==='tying'&&v==='B'&&s!=='B'&&!st.evidence.some(e=>e.deed==='gun'&&e.A===s&&e.V==='B'))P*=.15;
  // SYMBOLIC reasons (Sahlins / Barthes's side): the roles the house has given them
  const ms=st.myth[s],mv=st.myth[v];let Sy;
  if(d==='seduction')Sy=(ms.SEDUCER||0)+(ms.IDOL||0)*.6+.1+((mv.DREAMER||0)+(mv['GENTLE GIANT']||0))*.5;
  else if(d==='blackmail'||d==='prostitution')Sy=(ms.MISER||0)+(ms.LANDLADY||0)*.6+(ms.PREDATOR||0)*.5+.1+((mv.VICTIM||0)+(mv.SCAPEGOAT||0))*.6;
  else if(d==='snooping'||d==='slander')Sy=(ms.SPY||0)+(ms.MISER||0)*.4+(ms.LANDLADY||0)*.4+.1+((mv.SCAPEGOAT||0)+(mv.IDOL||0)*.5)*.6;
  else Sy=(ms.PREDATOR||0)+(ms.BRUTE||0)*.6+.1+((mv.VICTIM||0)+(mv.SCAPEGOAT||0)+(mv.DREAMER||0)*.3)*.6;
  // intention: commitment to a plan toward v (Bratman)
  const it=mind.intent[s];let C=1;if(it&&it.target===v)C=(it.kind==='hostile'&&HOSTILE.has(d))||(it.kind==='win'&&d==='seduction')?2.2:it.kind==='win'?.4:it.kind==='amend'&&HOSTILE.has(d)?.3:1;
  let U=Math.pow(Math.max(1e-4,P),pie.P)*Math.pow(Math.max(1e-4,Sy),1-pie.P)*C;
  if(!st.alive[s])U*=.02;if(st.tiedUntil&&st.tiedUntil[s]!=null&&k<st.tiedUntil[s])U*=.02;if(!st.alive[v])U*=.03;return U}
 const lerp=(a,b,u)=>a+(b-a)*u;
 // ---- memory stream: records, retrieval, reflection, plans ----
 function observe(mind,st,e,k){const imp=(who)=>{const role=e.A===who?'doer':e.V===who?'victim':'witness';const other=role==='doer'?e.V:e.A;const m=st.mind[who][other]||{};
   const w=role==='witness'?.25:Math.min(1,(m.fear||0)+(m.guilt||0)+(m.grudge||0)*.7+(m.desire||0)*.7+(m.debt||0)*.5);return{role,other,imp:Math.max(1,Math.round(1+9*w+(st.alive[e.V]?0:3)))}};
  const ref=st.evidence[k]&&st.evidence[k].refused;const vb=ref?'tried to strangle':VERB[e.deed];
  for(const s of IDS){if(!st.know[s].includes(k))continue;const{role,other,imp:I}=imp(s);
   const text=role==='doer'?`I ${vb} ${NM[e.V]}.`:role==='victim'?`${NM[e.A]} ${vb} me.`:`I learned that ${NM[e.A]} ${vb} ${NM[e.V]}.`;
   mind.stream[s].push({t:k,kind:'observation',text,importance:Math.min(10,I),about:[e.A,e.V].filter(x=>x!==s),deed:e.deed});mind.acc[s]+=I;
   if(!st.alive[e.V]&&e.V!==s&&!mind.stream[s].some(r=>r.kind==='observation'&&r.deadNote===e.V))mind.stream[s].push({t:k,kind:'observation',text:`${NM[e.V]} is dead.`,importance:9,about:[e.V],deadNote:e.V})}}
 function retrieve(mind,s,k,about,deed,n=3){const R=mind.stream[s].map((r,i)=>{const rec=Math.pow(.85,k-r.t),imp=r.importance/10,rel=(about&&r.about.includes(about)?1:0)+(deed&&r.deed===deed?.4:0);return{r,i,score:rec+imp+rel}});return R.sort((a,b)=>b.score-a.score).slice(0,n)}
 function reflect(mind,st,k){for(const s of IDS){if(mind.acc[s]<14||!st.alive[s])continue;mind.acc[s]=0;
   // ask: who has been most on my mind? then conclude something about them from beliefs and feelings (template, not an LLM)
   const tally={};for(const r of mind.stream[s].slice(-8))for(const a of r.about)tally[a]=(tally[a]||0)+r.importance;const o=Object.keys(tally).sort((a,b)=>tally[b]-tally[a])[0];if(!o)continue;
   const m=st.mind[s][o],b=st.belief[s][o],ev=retrieve(mind,s,k,o,null,3).map(x=>x.i);const out=[];
   if(b.harm.m>.45)out.push(`${NM[o]} is dangerous.`);if(m.grudge>.5)out.push(`${NM[o]} will pay for what was done.`);if(m.guilt>.5)out.push(`I have wronged ${NM[o]}.`);if(m.desire>.5)out.push(`I want ${NM[o]}.`);if(m.debt>.4)out.push(`I owe ${NM[o]} and they know it.`);if(m.fear>.6)out.push(`I am afraid of ${NM[o]}.`);
   if(!st.alive[o])out.push(`${NM[o]} is gone, and the house will ask why.`);const arch=L0.dominant(st.myth[s]);out.push(`The house sees me as the ${arch.toLowerCase()}.`);
   for(const text of out.slice(0,2))mind.stream[s].push({t:k,kind:'reflection',text,importance:7,about:[o],links:ev});
   // intention (BDI): a committed plan, written into the stream
   if(!mind.intent[s]||mind.intent[s].target!==o){const kind=m.grudge>.5||b.harm.m>.6?'hostile':m.desire>.5?'win':m.guilt>.6?'amend':null;if(kind){mind.intent[s]={target:o,kind,since:k};mind.stream[s].push({t:k,kind:'plan',text:kind==='hostile'?`I will make ${NM[o]} pay.`:kind==='win'?`I will win ${NM[o]}.`:`I will make it right with ${NM[o]}.`,importance:8,about:[o]})}}}}
 function newMind(){return{stream:{R:[],B:[],I:[],O:[]},acc:{R:0,B:0,I:0,O:0},intent:{},why:[]}}
 // ---- the agents write a film: at each deed, every (doer, target) is weighed; E sets how much chance enters ----
 function generate(pie={P:.5,I:.5,E:.5},seed=1){let rs=seed>>>0||1;const rnd=()=>{rs=(rs*16807)%2147483647;return rs/2147483647};
  let st=L0.init();const mind=newMind();const film=[];
  for(let k=0;k<12;k++){const U=PAIRS.map(([a,v])=>utility(st,k,a,v,mind,pie));const tau=.08+pie.E*1.6;const lg=U.map(u=>Math.log(u)/tau);const mx=Math.max(...lg);const w=lg.map(x=>Math.exp(x-mx));const z=w.reduce((a,b)=>a+b,0);
   let u=rnd()*z,i=0;for(;i<11;i++){u-=w[i];if(u<=0)break}film.push(i);const[A,V]=PAIRS[i];
   mind.why.push({k,A,V,p:w[i]/z,intent:mind.intent[A]&&mind.intent[A].target===V?mind.intent[A].kind:null,recall:retrieve(mind,A,k,V,ORDER[k],2).map(x=>x.r.text)});
   const it=mind.intent[A];if(it&&it.target===V&&((it.kind==='hostile'&&HOSTILE.has(ORDER[k]))||(it.kind==='win'&&ORDER[k]==='seduction'))){delete mind.intent[A];mind.stream[A].push({t:k,kind:'plan',text:`Done: ${NM[V]}.`,importance:5,about:[V]})}
   st=L0.step(st,{k,deed:ORDER[k],A,V});observe(mind,st,{k,deed:ORDER[k],A,V},k);reflect(mind,st,k)}
  return{film,mind,state:st}}
 // the minds behind any film (replay through the same stream/reflection/plan machinery)
 function minds(film){let st=L0.init();const mind=newMind();const per=[];for(let k=0;k<12;k++){const[A,V]=PAIRS[film[k]];per.push({k,recall:{A:retrieve(mind,A,k,V,ORDER[k],3).map(x=>x.r),V:retrieve(mind,V,k,A,ORDER[k],3).map(x=>x.r)},intent:JSON.parse(JSON.stringify(mind.intent)),streamLen:Object.fromEntries(IDS.map(s=>[s,mind.stream[s].length]))});
   st=L0.step(st,{k,deed:ORDER[k],A,V});observe(mind,st,{k,deed:ORDER[k],A,V},k);reflect(mind,st,k)}return{mind,per}}
 return{utility,generate,minds,retrieve,observe,reflect,newMind,HOSTILE,NM}})();
