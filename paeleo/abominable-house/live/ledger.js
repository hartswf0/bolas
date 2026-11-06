// THE LEDGER: a film is 12 events; every later state is computed from them (no hand-made state).
window.LEDGER=(function(){
 const ORDER=['blackmail','drugging','incitement','knifing','prostitution','gun','tying','assault','seduction','slander','snooping','strangling'];
 const IDS=['R','B','I','O'];const PAIRS=[];for(const a of IDS)for(const v of IDS)if(a!==v)PAIRS.push([a,v]);
 // character: how each sack carries what it did (guilt) and what was done to it (fear/grudge)
 const TEMPER={R:{guilt:.25,fear:.6,grudge:.9,pride:.8},B:{guilt:1,fear:.5,grudge:.4,pride:.2},I:{guilt:.5,fear:.3,grudge:.2,pride:.4},O:{guilt:.15,fear:.7,grudge:.8,pride:.9}};
 // what each deed does to bodies, lives, knowledge and the house
 const RULE={
  blackmail:{V:['coins'],A:['coins'],mindV:{fear:.7,debt:.8,grudge:.6},mindA:{guilt:.3,pride:.6},secret:true,evidence:'photograph'},
  drugging:{V:['drowsy'],A:[],mindV:{fear:.4,grudge:.3},mindA:{guilt:.4},evidence:'cup'},
  incitement:{V:['greyed','drowsy'],A:[],kills:true,mindV:{},mindA:{guilt:.9},evidence:'lamp'},
  knifing:{V:['emptied','torn'],A:[],kills:true,mindV:{fear:1,grudge:1},mindA:{guilt:1},evidence:'flour'},
  prostitution:{V:[],A:['coins'],mindV:{fear:.6,grudge:.8},mindA:{guilt:.5,pride:.4},evidence:'coins'},
  gun:{V:[],A:[],mindV:{fear:1,grudge:.5},mindA:{guilt:.4,pride:.5},evidence:'gun'},
  tying:{V:['rope','gag'],A:[],mindV:{fear:.8,grudge:.7},mindA:{guilt:.5},evidence:'rope'},
  assault:{V:['torn'],A:[],mindV:{fear:1,grudge:1},mindA:{guilt:.8},evidence:'curtain'},
  seduction:{V:[],A:[],mindV:{desire:.9},mindA:{desire:.5,pride:.4},evidence:'flower'},
  slander:{V:['blot','tag'],A:[],mindV:{grudge:.9,fear:.3},mindA:{guilt:.3,pride:.5},public:true,evidence:'ink'},
  snooping:{V:[],A:[],mindV:{},mindA:{pride:.3},learns:true,evidence:'keyhole'},
  strangling:{V:['cinched'],A:[],kills:true,refusedBy:'B',mindV:{fear:1,grudge:1},mindA:{guilt:1},evidence:'cord'}};

 // ---------- PLoT: every deed is a tug-of-war match; observers update beliefs about strength and harm ----------
 const PRIOR_STR={R:0,B:1.5,I:-.8,O:-.4};
 const HARM={blackmail:.3,drugging:.5,incitement:.8,knifing:1,prostitution:.5,gun:.7,tying:.5,assault:.9,seduction:0,slander:.3,snooping:.1,strangling:1};
 const sig=x=>1/(1+Math.exp(-x));
 function blankBelief(){const b={};for(const o of IDS){b[o]={};for(const t of IDS)b[o][t]={str:{m:PRIOR_STR[t],v:1},harm:{m:0,v:1}}}return b}
 function observe(bel,e,refused){const y=refused?0:1;const sA=bel[e.A].str,sV=bel[e.V].str;const p=sig(sA.m-sV.m);
  sA.m+=sA.v*(y-p)*.9;sV.m-=sV.v*(y-p)*.9;const sh=p*(1-p)*.9;sA.v=Math.max(.05,sA.v*(1-sA.v*sh));sV.v=Math.max(.05,sV.v*(1-sV.v*sh));
  const h=bel[e.A].harm,r=.3,gk=h.v/(h.v+r);h.m+=gk*((refused?.5:1)*HARM[e.deed]-h.m);h.v=h.v*r/(h.v+r)}
 // ---------- Barthes: the archetype the house reads each sack as; deeds rewrite the myth ----------
 const ARCH=['MISER','LANDLADY','BRUTE','GENTLE GIANT','FALLEN LORD','DREAMER','IDOL','SEDUCER','PREDATOR','VICTIM','SCAPEGOAT','SPY','INVULNERABLE','CORPSE','GHOST'];
 const ARCH0={R:{MISER:.5,LANDLADY:.5},B:{'GENTLE GIANT':.6,BRUTE:.4},I:{'FALLEN LORD':.6,DREAMER:.4},O:{IDOL:.7,SEDUCER:.3}};
 const SHIFT={blackmail:[{MISER:.4,PREDATOR:.3},{VICTIM:.5}],drugging:[{PREDATOR:.4},{VICTIM:.3,DREAMER:.3}],incitement:[{PREDATOR:.7},{CORPSE:1}],knifing:[{PREDATOR:1,BRUTE:.3},{CORPSE:1}],
  prostitution:[{MISER:.5,PREDATOR:.4},{VICTIM:.7}],gun:[{BRUTE:.5,PREDATOR:.4},{VICTIM:.6}],tying:[{BRUTE:.5},{VICTIM:.6}],assault:[{PREDATOR:1},{VICTIM:1}],seduction:[{SEDUCER:.8},{DREAMER:.4}],
  slander:[{SPY:.3,PREDATOR:.2},{SCAPEGOAT:1}],snooping:[{SPY:.9},{}],strangling:[{PREDATOR:1,BRUTE:.4},{CORPSE:1}]};
 function mixIn(w,sh,a){const o={};for(const k of ARCH)o[k]=(w[k]||0)*(1-a)+(sh[k]||0)*a;let s=0;for(const k of ARCH)s+=o[k];for(const k of ARCH)o[k]/=s||1;return o}
 function dominant(w){return ARCH.reduce((a,b)=>(w[b]||0)>(w[a]||0)?b:a,ARCH[0])}
 // archetypes act as LEVERS: the shared animation controls every module reads
 function levers(w){const L=k=>w[k]||0;return{
  loom:L('BRUTE')*.8+L('PREDATOR')+L('INVULNERABLE')*.6-L('VICTIM')*.8-L('SCAPEGOAT')*.5,   // leans in, takes space, drawn larger
  weight:L('GENTLE GIANT')*.5+L('BRUTE')*.8+L('MISER')*.2-L('DREAMER')*.4,                // heavier steps, deeper thumps
  tempo:L('IDOL')*.4+L('SPY')*.5+L('SEDUCER')*.3-L('DREAMER')*.5-L('CORPSE'),              // faster, crisper timing
  halo:L('IDOL')*.8+L('SEDUCER')*.6+L('INVULNERABLE')*.5,                                  // the light finds it
  shadow:L('PREDATOR')+L('SPY')*.6+L('MISER')*.3,                                          // its shadow lengthens and darkens
  shrink:L('VICTIM')*.6+L('SCAPEGOAT')*.8,                                                 // drawn smaller, ears down
  grey:Math.min(1,L('CORPSE')+L('GHOST'))}}                                                // colour leaves it
 const HEAD={blackmail:'BLACKMAILS',drugging:'DRUGS',incitement:'DRIVES TO DESPAIR',knifing:'KNIFES',prostitution:'SELLS',gun:'HOLDS AT GUNPOINT',tying:'BINDS AND GAGS',assault:'ASSAULTS',seduction:'SEDUCES',slander:'SLANDERS',snooping:'SPIES ON',strangling:'STRANGLES'};
 const NAME={R:'WIDOW',B:'WRESTLER',I:'HEIR',O:'MODEL'};
 // a reading of event k in the user's template: headline, PLoT prior -> posterior (house view), Barthes match
 function reading(L2,k){const e=L2.ev[k],a=L2.states[k],b=L2.states[k+1];const ref=b.evidence[k].refused;
  const house=(st,t,f)=>{const obs=IDS.filter(o=>st.alive[o]||true);let s=0;for(const o of obs)s+=f(st.belief[o][t]);return s/obs.length};
  const str=(st,t)=>house(st,t,x=>sig(x.str.m)),harm=(st,t)=>house(st,t,x=>x.harm.m);
  return{headline:ref?`${NAME[e.A]} FAILS TO STRANGLE ${NAME[e.V]}`:`${NAME[e.A]} ${HEAD[e.deed]} ${NAME[e.V]}`,
   plot:[{who:e.A,what:'strength',p0:str(a,e.A),p1:str(b,e.A)},{who:e.V,what:'strength',p0:str(a,e.V),p1:str(b,e.V)},{who:e.A,what:'danger',p0:harm(a,e.A),p1:harm(b,e.A)}],
   match:[dominant(b.myth[e.A]),dominant(b.myth[e.V])],mythBefore:[dominant(a.myth[e.A]),dominant(a.myth[e.V])]}}
 function blank(){const m={};for(const a of IDS){m[a]={};for(const b of IDS)if(a!==b)m[a][b]={fear:0,guilt:0,grudge:0,desire:0,debt:0,pride:0}}return m}
 // ---- THE FRAME (Knowles and Tenney, The House of Dust): each deed happens in a room, under a light, before whoever is there,
 // and leaves a material. Witnesses learn the deed if the room is lit; a sack entering a lit room later finds the traces left there.
 const SITE={blackmail:'parlour',drugging:'kitchen',incitement:'attic',knifing:'kitchen',prostitution:'parlour',gun:'stairwell',tying:'cellar',assault:'bedroom',seduction:'bedroom',slander:'parlour',snooping:'stairwell',strangling:'attic'};
 const ROOMS=['parlour','kitchen','stairwell','cellar','bedroom','attic'];const BASE={parlour:2,kitchen:1,stairwell:0,cellar:0,bedroom:1,attic:1};
 const LIGHTN=['in the dark','by one candle','by a lamp','by firelight'];const HOME={R:'parlour',B:'cellar',I:'attic',O:'bedroom'};
 const FADES=new Set(['flower','keyhole']);
 // the fire clock: from deed IX the smoke and then the fire light every room a step more
 const lightAt=(site,k)=>Math.min(3,BASE[site]+(k>=8?1:0)+(k>=10?1:0));
 function init(){const st={k:0,loc:{...HOME},traces:Object.fromEntries(ROOMS.map(r=>[r,[]])),frames:[],tiedUntil:{},body:{R:[],B:[],I:[],O:[]},alive:{R:true,B:true,I:true,O:true},deadAt:{},know:{R:[],B:[],I:[],O:[]},mind:blank(),evidence:[],impossible:[],survived:[],belief:blankBelief(),myth:JSON.parse(JSON.stringify(ARCH0)),levers:{}};for(const x of IDS){for(const a of ARCH)st.myth[x][a]=st.myth[x][a]||0;st.levers[x]=levers(st.myth[x])}return st}
 const clone=s=>JSON.parse(JSON.stringify(s));
 // one deed: the state after event e, given the state before it (pure)
 function step(st0,e){const r=RULE[e.deed];const st=clone(st0);st.k=e.k+1;
   // a dead sack cannot act or be acted on: the film is still played (a hypothesis), but the ledger records the contradiction
   if(!st.alive[e.A]||!st.alive[e.V])st.impossible.push({k:e.k,who:!st.alive[e.A]?e.A:e.V,why:'dead'});
   // a sack tied up cannot act for the next two deeds
   else if(st.tiedUntil[e.A]!=null&&e.k<st.tiedUntil[e.A])st.impossible.push({k:e.k,who:e.A,why:'tied'});
   const refused=r.refusedBy&&r.refusedBy===e.V;const prior=st.body[e.V].slice();
   if(!refused){for(const tg of r.V)if(!st.body[e.V].includes(tg))st.body[e.V].push(tg);for(const tg of r.A)if(!st.body[e.A].includes(tg))st.body[e.A].push(tg);
    // death depends on history: Belindo has too much flour to bleed out; despair only kills a sack already carrying it
    let dies=!!r.kills;
    if(e.deed==='knifing'){dies=e.V!=='B'&&['rope','emptied','torn','drowsy'].some(x=>prior.includes(x))}
    if(e.deed==='incitement'){let load=0;for(const o of IDS)if(o!==e.V){const m=st.mind[e.V][o];load+=m.fear+m.grudge*.6+m.debt*.4}dies=load>1.5}
    if(dies){st.alive[e.V]=false;st.deadAt[e.V]=e.k}else if(r.kills){st.survived=(st.survived||[]).concat([e.k])}}
   const TA=TEMPER[e.A],TV=TEMPER[e.V];
   for(const[k,v]of Object.entries(r.mindV))st.mind[e.V][e.A][k]=Math.min(1,st.mind[e.V][e.A][k]+v*(TV[k]??1)*(refused?.4:1));
   for(const[k,v]of Object.entries(r.mindA))st.mind[e.A][e.V][k]=Math.min(1,st.mind[e.A][e.V][k]+v*(TA[k]??1));
   // knowledge: participants know; slander makes it everyone's; snooping gives the doer the victim's past
   const who=r.public?IDS:[e.A,e.V];for(const s of who)if(!st.know[s].includes(e.k))st.know[s].push(e.k);
   if(r.learns)for(const k of st.know[e.V])if(!st.know[e.A].includes(k))st.know[e.A].push(k);
   // the frame: room, light, witnesses, traces found
   const site=SITE[e.deed],light=lightAt(site,e.k);st.loc[e.A]=site;st.loc[e.V]=site;
   const inh=IDS.filter(o=>o!==e.A&&o!==e.V&&st.alive[o]&&st.loc[o]===site);
   if(light>=1)for(const o of inh)if(!st.know[o].includes(e.k))st.know[o].push(e.k);
   const found=[];if(light>=1)for(const tr of st.traces[site])for(const s2 of [e.A,e.V])if(st.alive[s2]&&!st.know[s2].includes(tr.k)){st.know[s2].push(tr.k);found.push({who:s2,k:tr.k,mat:tr.mat})}
   st.traces[site]=st.traces[site].filter(tr=>!FADES.has(tr.mat)||e.k-tr.k<2);if(!refused||e.deed!=='strangling')st.traces[site].push({k:e.k,mat:r.evidence});
   if(e.deed==='tying'&&!refused)st.tiedUntil[e.V]=e.k+3;
   st.frames.push({k:e.k,site,light,lightName:LIGHTN[light],material:r.evidence,inhabitants:inh,dark:light<1,found});
   st.evidence.push({k:e.k,deed:e.deed,A:e.A,V:e.V,kind:r.evidence,refused});
   for(const o of IDS)if(st.know[o].includes(e.k))observe(st.belief[o],e,refused);
   const[sa,sv]=SHIFT[e.deed];if(refused){st.myth[e.V]=mixIn(st.myth[e.V],{INVULNERABLE:1},.5);st.myth[e.A]=mixIn(st.myth[e.A],{VICTIM:.5,PREDATOR:.5},.3)}else{st.myth[e.A]=mixIn(st.myth[e.A],sa,.35);const svx=(sv.CORPSE&&st.alive[e.V])?{VICTIM:.9,SCAPEGOAT:.1}:sv;st.myth[e.V]=mixIn(st.myth[e.V],svx,(sv.CORPSE&&!st.alive[e.V])?.8:.35)}
   for(const x of IDS){if(!st.alive[x]&&st.impossible.some(q=>q.who===x&&q.k===e.k))st.myth[x]=mixIn(st.myth[x],{GHOST:1},.5);st.levers[x]=levers(st.myth[x])}
   return st}
 function run(film){ // film: 12 pair indices (or [[A,V],...])
  const ev=film.map((p,k)=>{const[A,V]=Array.isArray(p)?p:PAIRS[p];return{k,deed:ORDER[k],A,V}});
  let st=init();const states=[clone(st)];for(const e of ev){st=step(st,e);states.push(st)}return{ev,states}}
 // the memories a sack carries into step k (strongest first): what it did, what was done to it, what it knows of
 function memories(L,who,k){const st=L.states[k];const out=[];for(const i of st.know[who]){const e=L.ev[i];const role=e.A===who?'doer':e.V===who?'victim':'witness';const other=role==='doer'?e.V:e.A;
   const m=role==='witness'?.35:(role==='doer'?st.mind[who][e.V]:st.mind[who][e.A]);const weight=role==='witness'?.35:Math.min(1,(m.fear||0)+(m.guilt||0)+(m.grudge||0)*.6+(m.desire||0)*.7+(m.debt||0)*.5+(m.pride||0)*.3);
   out.push({k:i,deed:e.deed,A:e.A,V:e.V,role,other,ago:k-1-i,weight})}return out.sort((a,b)=>b.weight-a.weight)}
 return{SITE,ROOMS,LIGHTN,HOME,lightAt,ORDER,IDS,PAIRS,RULE,TEMPER,ARCH,ARCH0,SHIFT,HARM,init,step,run,memories,reading,levers,dominant}})();
