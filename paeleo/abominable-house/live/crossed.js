// CROSSED: four readings of the film besides deed order.
// AUDIENCE: inverse planning (Bayesian theory of mind), after Chandra, Li, Tenenbaum & Ragan-Kelley, "Storytelling as Inverse Inverse
//   Planning" (2023). A watcher sees every deed and infers each sack's hidden intention by Bayes' rule. The likelihood of a deed under
//   an intention comes from the agents' own utility, P(pair | intent) ∝ exp(log U / τ). Each step mixes back a little prior (ε),
//   because these sacks change their plans. Measured per deed:
//   surprise = -log P(observed) / log 12; twist = KL(posterior after || before), summed over sacks;
//   suspense = binary entropy of "the next deed kills someone"; irony = P(audience: doer means harm to victim) × (1 - victim's belief that doer is dangerous).
// AUTHOR (I²P): beam search over films, scored by a device (irony, suspense, twist) plus believability, as in the paper's beam search over scripts.
// CASTLE (Calvino, The Castle of Crossed Destinies): every deed is a card in two strands, the doer's and the victim's; each strand is scored on its own.
// OPENINGS (Calvino, If on a winter's night a traveler): all 1,728 three-deed openings, grouped by the house they leave, each continued
//   by the agents until the point where the next deed is least certain, where it stops.
window.CROSSED=(function(){
 const L0=window.LEDGER,S0=window.STORY,A0=window.AGENTS,IDS=L0.IDS,ORDER=L0.ORDER,PAIRS=L0.PAIRS,NM=A0.NM,RULE=L0.RULE;
 const KINDS=['hostile','win','amend'],EPS=.06,AUD_PIE={P:.5,I:.5,E:.3},TAU=.08+AUD_PIE.E*1.6;
 const H={};for(const s of IDS){H[s]=[null];for(const k of KINDS)for(const t of IDS)if(t!==s)H[s].push({kind:k,target:t})}
 const PRIOR=H.R.map(h=>h?.8/9:.2);
 const lg2=Math.log2,Hb=p=>p<=1e-9||p>=1-1e-9?0:-(p*lg2(p)+(1-p)*lg2(1-p));
 const softmax=(U,tau)=>{const l=U.map(u=>Math.log(Math.max(u,1e-12))/tau);const m=Math.max(...l);const w=l.map(x=>Math.exp(x-m));const z=w.reduce((a,b)=>a+b,0);return w.map(x=>x/z)};
 const hypText=(s,h)=>!h?'no plan':h.kind==='hostile'?`make ${NM[h.target]} pay`:h.kind==='win'?`win ${NM[h.target]}`:`make it right with ${NM[h.target]}`;
 const newPost=()=>Object.fromEntries(IDS.map(s=>[s,PRIOR.slice()]));
 // the watcher's model before deed k: for each sack and each hypothesis about its intention, a distribution over the 12 pairs
 function table(st,k){const T={};for(const s of IDS)T[s]=H[s].map(h=>softmax(PAIRS.map(([a,v])=>A0.utility(st,k,a,v,{intent:h?{[s]:h}:{}},AUD_PIE)),TAU));return T}
 function predict(T,post){const p=Array(12).fill(0);for(const s of IDS)post[s].forEach((w,j)=>{const r=T[s][j];for(let i=0;i<12;i++)p[i]+=w*r[i]/4});return p}
 function killNext(st,k){const out=Array(12).fill(null);if(!RULE[ORDER[k]].kills)return out;for(let i=0;i<12;i++){const[a,v]=PAIRS[i];out[i]=L0.step(st,{k,deed:ORDER[k],A:a,V:v})}return out}
 // suspense reads ahead to the next deed that can kill (incitement III, knifing IV, strangling XII): how uncertain is it, from here, that it will?
 function lethalAhead(st,k,post,T,pred,kids){let j=k;while(j<12&&!RULE[ORDER[j]].kills)j++;if(j>=12)return{j:null,pd:0};
  let P=pred,KD=kids;if(j!==k){P=predict(table(st,j),post);KD=killNext(st,j)}let pd=0;for(let i=0;i<12;i++){const v=PAIRS[i][1];if(KD[i]&&st.alive[v]&&!KD[i].alive[v])pd+=P[i]}return{j,pd}}
 // one observed deed: all four measures plus the updated posterior and the next state
 function observe(st,k,post,i,T,pred,kids){const[A,V]=PAIRS[i];const la=lethalAhead(st,k,post,T,pred,kids),pd=la.pd;
  let pH=0;H[A].forEach((h,j)=>{if(h&&h.kind==='hostile'&&h.target===V)pH+=post[A][j]});
  const irony=pH*(1-Math.min(1,Math.max(0,st.belief[V][A].harm.m)));
  const surprise=Math.min(1.5,-lg2(Math.max(pred[i],1e-9))/lg2(12));
  const np={};let twist=0;for(const s of IDS){let z=0;const q=post[s].map((p,j)=>{const x=p*T[s][j][i];z+=x;return x});np[s]=q.map((x,j)=>(1-EPS)*x/z+EPS*PRIOR[j]);twist+=np[s].reduce((a,p,j)=>a+(p>0?p*lg2(p/post[s][j]):0),0)}
  const next=kids[i]||L0.step(st,{k,deed:ORDER[k],A,V});
  return{m:{k,pd,lethal:la.j,suspense:Hb(pd),irony,surprise,twist,p:pred[i],entropy:-pred.reduce((a,p)=>a+(p>0?p*lg2(p):0),0)/lg2(12)},post:np,st:next}}
 const tops=post=>Object.fromEntries(IDS.map(s=>{let j=1;for(let q=2;q<post[s].length;q++)if(post[s][q]>post[s][j])j=q;return[s,{h:H[s][j],text:hypText(s,H[s][j]),p:post[s][j],none:post[s][0]}]}));
 // ---- the audience watching a whole film ----
 function audience(film){let st=L0.init(),post=newPost();const out=[];
  for(let k=0;k<12;k++){const T=table(st,k),pred=predict(T,post),kids=killNext(st,k);const before=tops(post);const r=observe(st,k,post,film[k],T,pred,kids);
   out.push({...r.m,before,after:tops(r.post)});post=r.post;st=r.st}
  return out}
 // ---- the author: beam search for a device, inverse inverse planning ----
 const DEV={
  irony:{label:'IRONY',f:(m)=>m.reduce((a,x)=>a+x.irony,0)*3},
  suspense:{label:'SUSPENSE',f:(m)=>m.reduce((a,x)=>a+x.suspense,0)*2.5},
  twist:{label:'TWIST',f:(m)=>{let early=0,late=0;for(const x of m)if(x.k<6)early+=x.twist+x.surprise*.3;else late=Math.max(late,x.twist*3+x.surprise);return late-early}}};
 // the castle's demand on the author: no strand may be one pair repeated; every pair used more than twice costs
 const castle=f=>{const c={};let pen=0;for(const i of f){c[i]=(c[i]||0)+1;if(c[i]>2)pen+=.8}return pen};
 function author(dev,{width=14,lambda=1.5,seed=1}={}){let rs=seed>>>0||1;const rnd=()=>{rs=(rs*16807)%2147483647;return rs/2147483647};
  let beam=[{film:[],st:L0.init(),post:newPost(),m:[],lr:0,ev:[]}];
  for(let k=0;k<12;k++){const cand=[];
   for(const b of beam){const T=table(b.st,k),pred=predict(T,b.post),kids=killNext(b.st,k);
    for(let i=0;i<12;i++){const[A,V]=PAIRS[i];if(!b.st.alive[A]||!b.st.alive[V]||(b.st.tiedUntil[A]!=null&&k<b.st.tiedUntil[A]))continue;
     const raw=S0.rate(b.st,k,A,V,{ev:b.ev}).raw;const r=observe(b.st,k,b.post,i,T,pred,kids);
     const m=b.m.concat([r.m]),lr=b.lr+Math.log(Math.max(raw,.01));const ev=b.ev.concat([{k,deed:ORDER[k],A,V}]);
     cand.push({film:b.film.concat([i]),st:r.st,post:r.post,m,lr,ev,score:DEV[dev].f(m)+lambda*lr/4-castle(b.film.concat([i]))+rnd()*.15})}}
   cand.sort((a,b)=>b.score-a.score);beam=cand.slice(0,width)}
  return beam.map(b=>({film:b.film,score:b.score,believ:Math.exp(b.lr/12),m:b.m}))}
 // ---- the castle: each sack's strand ----
 function strands(film,aud){const sc=S0.score(film),L=sc.L;const out={};
  for(const s of IDS){const cards=[];let lr=0,n=0,sur=0,ns=0,contra=0;
   for(let k=0;k<12;k++){const e=L.ev[k];const dead=!L.states[k].alive[s];const role=e.A===s?'A':e.V===s?'V':L.states[k+1].know[s].includes(k)?'W':'';
    if(role==='A'||role==='V'){lr+=Math.log(Math.max(sc.ev[k].raw,1e-4));n++;if(L.states[k+1].impossible.some(q=>q.k===k&&q.who===s))contra++}
    if(role==='A'&&aud){sur+=aud[k].surprise;ns++}
    cards.push({k,role,dead,other:role==='A'?e.V:role==='V'?e.A:null,deed:e.deed})}
   const believ=n?Math.exp(lr/n):0;const coherence=ns?Math.max(0,1-sur/ns):1;
   out[s]={cards,believ,tier:S0.tier(believ),coherence,contra,n,holds:n>0&&believ>.3&&!contra}}
  const live=IDS.filter(s=>out[s].n);const weakest=live.reduce((a,s)=>out[s].believ<out[a].believ?s:a,live[0]);
  return{per:out,weakest,min:out[weakest].believ,holding:live.filter(s=>out[s].holds).length}}
 // ---- the openings ----
 function signature(st,mind){return IDS.map(s=>{const it=mind.intent[s];return[st.alive[s]?'':'dead',st.body[s].slice().sort().join('+'),L0.dominant(st.myth[s]),it?it.kind+'>'+it.target:''].join('/')}).join('|')}
 function describe(st,mind){return IDS.map(s=>{const bits=[];if(!st.alive[s])bits.push('dead');else{if(st.body[s].length)bits.push(st.body[s].join(', '));const it=mind.intent[s];if(it)bits.push('plans to '+hypText(s,it));bits.push(L0.dominant(st.myth[s]).toLowerCase())}return NM[s]+': '+bits.join('; ')}).join(' · ')}
 function agentStep(st,mind,k,i){const[A,V]=PAIRS[i];const it=mind.intent[A];if(it&&it.target===V&&((it.kind==='hostile'&&A0.HOSTILE.has(ORDER[k]))||(it.kind==='win'&&ORDER[k]==='seduction')))delete mind.intent[A];
  const e={k,deed:ORDER[k],A,V};const s2=L0.step(st,e);A0.observe(mind,s2,e,k);A0.reflect(mind,s2,k);return s2}
 function openings(pie={P:.5,I:.5,E:.4}){const tau=.08+pie.E*1.6;const G=new Map();let rejected=0;
  for(let o=0;o<1728;o++){const f=[Math.floor(o/144),Math.floor(o/12)%12,o%12];let st=L0.init();const mind=A0.newMind();let lr=0;const ev=[];
   for(let k=0;k<3;k++){const[A,V]=PAIRS[f[k]];lr+=Math.log(Math.max(1e-4,S0.rate(st,k,A,V,{ev}).raw));ev.push({k,deed:ORDER[k],A,V});st=agentStep(st,mind,k,f[k])}
   if(st.impossible.length){rejected++;continue}
   const sig=signature(st,mind),desc=describe(st,mind);const film=f.slice();let cut=3,bestH=-1,at=null;
   for(let k=3;k<12;k++){const p=softmax(PAIRS.map(([a,v])=>A0.utility(st,k,a,v,mind,pie)),tau);const order=p.map((x,i)=>[i,x]).sort((a,b)=>b[1]-a[1]);const h=(order[0][1]+order[1][1])*order[1][1]/order[0][1];if(h>bestH){bestH=h;cut=k;at=order.slice(0,2)}
    film.push(order[0][0]);st=agentStep(st,mind,k,order[0][0])}
   const rec={film,cut,H:bestH,next:at,believ:Math.exp(lr/3)};if(!G.has(sig))G.set(sig,{sig,desc,members:[]});G.get(sig).members.push(rec)}
  const groups=[...G.values()].map(g=>{g.members.sort((a,b)=>b.believ-a.believ);g.best=g.members[0];g.size=g.members.length;return g});
  groups.sort((a,b)=>b.best.believ*Math.log(1+b.size)-a.best.believ*Math.log(1+a.size));
  return{groups,rejected,total:1728}}
 return{audience,author,strands,openings,agentStep,DEV,hypText,H}})();
