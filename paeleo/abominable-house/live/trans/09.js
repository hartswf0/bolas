// TRANSITION 09 · Seduction (Whitney harmonic dark room, lamp rings) -> Slander (Gilliam engraved cutout parlour)
// SCION 19 · Moho Pro, Smart-Bone Character Laboratory: bone hierarchy, smart bones, switch layers, mesh deformation.
// The lamp is the rig's SMART BONE. Turning it drives an action on a fan of child bones, one per ring of the
// Whitney lamp halo grown out to cover the room (a ring mesh centred on the lamp; alternate rings turn in
// opposite directions, as the halo's rings did). Each ring is a SWITCH LAYER between the two rooms: its bone
// sweeps the ring and everything behind the bone is the Gilliam parlour. Each sack is a rigged character
// (root, spine, two ear bones) whose drawing is a switch layer too: it hops on its root bone to the next
// shot's mark, the spine bone bends its image through a strip MESH, and halfway it turns through PROFILE
// (view control) where its drawing switches from the harmonic body to the paper card.
// Invariant (numeric, harness): at u=0 every bone is at rest and the frame is the outgoing lever composite;
// at u=dur every bone is at rest and the frame is the incoming composite (deed 10 at t=0).
(function(){
const IDS=['R','B','I','O'];
const COL={R:'#c86a5e',B:'#e0ac48',I:'#93b6dc',O:'#b872d8'};
const DUR=3.2,T_OUT=5.99,T_IN=0.001;
const RING=[0,80,200,330,470,620,780,950,1130,1320,1520,1730,1960,2200];   // ring mesh radii (x), y squashed by .62 like the halo
const SQ=.62,LAMP0=[960,196],LAMP1=[900,262];
const CACHE={};
const sm=(a,b,x)=>{const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)};
const cl=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
function cv(w,h){const c=document.createElement('canvas');c.width=Math.max(2,w);c.height=Math.max(2,h);return c}

// ---------- a deed layer composited exactly as film.html does (levers baked) ----------
function layerFull(D,lt,A,V,ly,carry,lev,K){
  const raw=cv(1920,1080),q=raw.getContext('2d');try{D.draw(q,lt,A,V,K,{layer:ly,carry})}catch(e){}
  if(ly==='bg'||!D.marks)return {c:raw};
  const mk=D.marks(lt,A,V,K,{carry}),b=mk[ly];
  const f=1+.14*Math.max(-1,Math.min(1,lev.loom))-.22*lev.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lev.grey>.05)fl.push(`grayscale(${Math.min(1,lev.grey)}) brightness(${1-.25*lev.grey})`);if(lev.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lev.halo)}px rgba(255,236,180,${Math.min(.9,lev.halo)}))`);
  if(lev.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lev.shadow)}px ${Math.round(-30*lev.shadow)}px ${Math.round(18*lev.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lev.shadow*.4)}))`);
  const out=cv(1920,1080),o=out.getContext('2d');o.filter=fl.join(' ')||'none';o.translate(cx,by);o.scale(f,f);o.translate(-cx,-by);o.drawImage(raw,0,0);
  return {c:out,box:{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}};
}
// a drawing of the switch layer: the whole sack layer cropped generously round its box, anchored at its base
function drawing(Lr){const b=Lr.box;
  const x0=Math.max(0,Math.floor(b.x-280)),y0=Math.max(0,Math.floor(b.y-340)),x1=Math.min(1920,Math.ceil(b.x+b.w+280)),y1=Math.min(1080,Math.ceil(b.y+b.h+70));
  const w=x1-x0,h=y1-y0,c=cv(w,h);c.getContext('2d').drawImage(Lr.c,x0,y0,w,h,0,0,w,h);
  return {c,ox:x0,oy:y0,ax:b.x+b.w/2,ay:b.y+b.h,w:b.w,h:b.h};
}
function impOverlay(q,a){q.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)q.fillRect(0,y,1920,2)}

function build(X,K){
  const key=X.film.join(',');if(CACHE.key===key)return CACHE.v;
  const Lg=X.ledger,k=X.k,eo=Lg.ev[k-1],ei=Lg.ev[k],Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed];
  const sO=Lg.states[k-1],sI=Lg.states[k];
  function room(D,lt,e,st,impK){
    const order=D.layers||['bg','V','A'];let bg=null;const P={};
    for(const ly of order){const Lr=layerFull(D,lt,e.A,e.V,ly,st.body,ly==='bg'?null:st.levers[ly==='A'?e.A:e.V],K);
      if(ly==='bg'||!Lr.box){bg=Lr.c;continue}const d=drawing(Lr);d.order=order.indexOf(ly);P[ly==='A'?e.A:e.V]=d}
    const c=cv(1920,1080),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,1920,1080);if(bg)q.drawImage(bg,0,0);
    return {c,P,imp:Lg.states[impK].impossible.some(z=>z.k===impK-1)};
  }
  const r1=room(Do,T_OUT,eo,sO,k),r2=room(Di,T_IN,ei,sI,k+1);
  function bystander(D,lt,s,st){const other=IDS.find(o=>o!==s);return drawing(layerFull(D,lt,s,other,'A',st.body,st.levers[s],K))}
  const P={};
  for(const s of IDS){
    const inO=!!r1.P[s],inI=!!r2.P[s];if(!inO&&!inI){P[s]={s,kind:'by',alive:sI.alive[s]};continue}
    const old=r1.P[s]||bystander(Do,0.001,s,sO),nw=r2.P[s]||bystander(Di,T_IN,s,sI);
    P[s]={s,old,nw,kind:inO&&inI?'stay':inO?'leave':'enter',alive:sI.alive[s],lev:sI.levers[s],role:s===ei.A?'A':s===ei.V?'V':null};
  }
  // gait per character (root-bone hop): hop height, hop length, squash, rock
  const GAIT={R:{hh:26,hl:130,sq:.10,rock:.07},B:{hh:30,hl:170,sq:.16,rock:0},I:{hh:12,hl:85,sq:.05,rock:0,drag:1},O:{hh:58,hl:230,sq:.06,rock:0}};
  let nl=0,ns=0,ne=0;
  for(const s of IDS){const p=P[s];if(p.kind==='by')continue;const G=GAIT[s],lv=p.lev;
    const tempo=1-.18*cl(-1,1,lv.tempo||0);p.G={...G,hh:G.hh*(1-.35*cl(0,1,lv.weight||0)),sq:G.sq*(1+.6*cl(0,1,lv.weight||0))};
    if(p.kind==='leave'){const dir=p.old.ax<960?-1:1;p.from={x:p.old.ax,y:p.old.ay};p.to={x:dir<0?-260:2180,y:p.old.ay};p.t0=.45+nl*.14;p.t1=p.t0+1.45*tempo;nl++}
    if(p.kind==='stay'){p.from={x:p.old.ax,y:p.old.ay};p.to={x:p.nw.ax,y:p.nw.ay};p.t0=.55+ns*.16;p.t1=Math.min(2.72,p.t0+1.9*tempo);ns++}
    if(p.kind==='enter'){const dir=p.nw.ax<960?-1:1;p.from={x:dir<0?-260:2180,y:p.nw.ay};p.to={x:p.nw.ax,y:p.nw.ay};p.t0=1.0+ne*.16;p.t1=2.72;ne++}
    const dist=Math.abs(p.to.x-p.from.x);p.nh=Math.max(2,Math.round(dist/p.G.hl));p.dir=Math.sign(p.to.x-p.from.x)||1;
    // the view switch (front -> profile -> front) halfway, where the drawing changes
    const mid=lerp(p.t0,p.t1,p.kind==='enter'?.35:p.kind==='leave'?.42:.5);p.s0=mid-.17;p.s1=mid+.17;
    p.ghost=!p.alive&&p.kind!=='leave';p.body=!p.alive&&p.kind==='leave';
  }
  // memory on the way: the incoming doer stalls and leans back if it remembers its victim
  const memA=LEDGER.memories(Lg,ei.A,k).filter(m=>m.other===ei.V&&m.weight>.3);
  const memV=LEDGER.memories(Lg,ei.V,k).filter(m=>m.other===ei.A&&m.weight>.3);
  const pa=P[ei.A];if(memA.length&&pa.kind!=='by'){pa.hes=Math.min(1,memA[0].weight);pa.mem=memA[0];pa.t0=Math.max(.35,pa.t0-.2)}
  if(memV.length&&P[ei.V].kind!=='by')P[ei.V].tremble=Math.min(1,memV[0].weight);
  // (the film plays the doer's memory beat before this transition, so the join always ends on the deed)
  const memCard=null;
  // each piece of evidence hangs from a point of the ring mesh (lower arc of rings 4 and 5, on the wall);
  // when that ring's bone sweeps past its pin it swings
  const n=sI.evidence.length,half=Math.ceil(n/2);
  const evid=sI.evidence.map((e,i)=>{const C=X.CONSEQS&&X.CONSEQS[e.deed];const j=3+(i%2),m=Math.floor(i/2),cnt=i%2?n-half:half;
    // ring 3 carries its pins across the lower arc; ring 4 only on the two sides, clear of the sacks' heads
    let ang;if(i%2===0)ang=cnt<2?Math.PI/2:.22+(Math.PI-.44)*m/(cnt-1);else{const f=cnt<2?0:m/(cnt-1),side=m<cnt/2;const ff=side?f*2:(f-.5)*2;ang=side?.12+.85*Math.min(1,ff):Math.PI-.97+.85*Math.min(1,Math.max(0,ff))}const dir=j%2?-1:1;
    const tc=(((ang-A0)*dir)%(Math.PI*2)+Math.PI*2)%(Math.PI*2)/(Math.PI*2);let up=DUR;for(let uu=0;uu<DUR;uu+=.01)if(ringP(uu,j)>=tc){up=uu;break}
    return {e,C,j,ang,up,dir,age:k-1-e.k,rot:(K.hash(i*7.3+k)-.5)*.2}});
  const dead=IDS.filter(s=>P[s].kind==='by'&&!sI.alive[s]).map((s,i)=>({s,img:bystander(Di,T_IN,s,sI),x:i?1640:250}));
  const v={r1,r2,P,memCard,evid,dead,ei,eo,sI,sO};if(X.still){CACHE.key=key;CACHE.v=v}return v;
}

// ---------- the smart bone and its action ----------
const DIAL=u=>sm(.3,2.62,u);                       // the smart bone's angle, 0..1 of a turn
const LAG=.115,NR=RING.length-1;
function ringP(u,j){const D=DIAL(u)*(1+LAG*(NR-1));return sm(0,1,D-j*LAG)}
const lampAt=u=>{const a=sm(.3,2.62,u);return [lerp(LAMP0[0],LAMP1[0],a),lerp(LAMP0[1],LAMP1[1],a)]};
const A0=-Math.PI/2;
function sectorPath(g,c,r0,r1,dir,p){const a1=A0+dir*p*Math.PI*2;g.beginPath();
  if(p>=.9999){g.ellipse(c[0],c[1],r1,r1*SQ,0,0,Math.PI*2);if(r0>0){g.moveTo(c[0]+r0,c[1]);g.ellipse(c[0],c[1],r0,r0*SQ,0,0,Math.PI*2,true)}return}
  if(r0<=0){g.moveTo(c[0],c[1]);g.ellipse(c[0],c[1],r1,r1*SQ,0,A0,a1,dir<0);g.closePath();return}
  g.ellipse(c[0],c[1],r1,r1*SQ,0,A0,a1,dir<0);g.ellipse(c[0],c[1],r0,r0*SQ,0,a1,A0,dir>0);g.closePath()}
const ePt=(c,r,a)=>[c[0]+r*Math.cos(a),c[1]+r*SQ*Math.sin(a)];

// a Moho bone: tapered kite from base to tip with a joint ring
function bone(g,x0,y0,x1,y1,col,a,dash){if(a<.01)return;const dx=x1-x0,dy=y1-y0,L=Math.hypot(dx,dy);if(L<2)return;const nx=-dy/L,ny=dx/L,wd=Math.min(16,L*.13);
  const mx=x0+dx*.18,my=y0+dy*.18;g.save();g.globalAlpha=a;g.beginPath();g.moveTo(x0,y0);g.lineTo(mx+nx*wd,my+ny*wd);g.lineTo(x1,y1);g.lineTo(mx-nx*wd,my-ny*wd);g.closePath();
  if(dash)g.setLineDash([7,6]);g.fillStyle=dash?'rgba(150,230,170,.18)':col+'cc';g.fill();g.lineWidth=2;g.strokeStyle=dash?'rgba(170,240,190,.9)':'#0d1120';g.stroke();g.setLineDash([]);
  g.beginPath();g.arc(x0,y0,Math.max(3,wd*.45),0,7);g.fillStyle='#f2f4ff';g.fill();g.stroke();g.restore()}

// ---------- a sack's root-bone state at time u ----------
function pstate(p,u){
  let pr=0,hopF=0,moving=false,pause=0;
  const T=p.t1-p.t0;
  if(p.hes){const PZ=.42,a=p.t0+(T-PZ)*.52;let m=u<a?u-p.t0:u<a+PZ?a-p.t0:u-p.t0-PZ;pause=u>a&&u<a+PZ?Math.sin(Math.PI*(u-a)/PZ):0;pr=cl(0,1,m/(T-PZ))}
  else pr=cl(0,1,(u-p.t0)/T);
  moving=u>p.t0&&u<p.t1&&!pause;
  let xr,lift=0,sq=0,lean=0;
  if(p.body){xr=sm(0,1,cl(0,1,(pr-.2)/.8))}                         // a body is dragged after it topples
  else if(p.ghost){xr=sm(0,1,pr);lift=26*Math.sin(Math.PI*pr)}       // a ghost glides on its root bone
  else{const ph=pr*p.nh,i=Math.min(p.nh-1,Math.floor(ph)),f=pr>=1?1:ph-i;hopF=f;
    xr=(i+sm(.12,.88,f))/p.nh;lift=p.G.hh*Math.sin(Math.PI*sm(.08,.92,f));
    const c=Math.min(f,1-f);if(pr>0&&pr<1)sq=p.G.sq*Math.max(0,1-c/.14)-p.G.sq*.5*Math.sin(Math.PI*f);
    lean=p.dir*.22*Math.sin(Math.PI*f)*(pr>0&&pr<1?1:0)}
  // anticipation and settle: a small squash before the first hop and after the last
  if(!p.body&&!p.ghost){sq+=p.G.sq*.8*(sm(p.t0-.18,p.t0,u)-sm(p.t0,p.t0+.08,u));sq+=p.G.sq*.8*Math.max(0,Math.sin(Math.PI*cl(0,1,(u-p.t1)/.22)))}
  if(pause){lean=-p.dir*.34*pause;sq-=.05*pause}
  const x=lerp(p.from.x,p.to.x,xr),y=lerp(p.from.y,p.to.y,xr)-lift;
  // view switch: front -> profile -> front, drawing swaps at profile
  const fp=p.body?0:sm(p.s0,p.s1,u);const fx=Math.max(.07,Math.abs(Math.cos(Math.PI*fp)));const showNew=fp>=.5;
  const H=lerp(p.old.h,p.nw.h,sm(p.s0,p.s1,u));
  let rot=0;if(p.body)rot=p.dir*Math.PI/2*.92*sm(p.t0,p.t0+.35,u);
  if(p.G&&p.G.rock&&moving)rot+=p.G.rock*Math.sin(hopF*Math.PI*2);
  let tx=0;if(p.tremble&&u>p.t0-.2)tx=Math.sin(u*61)*5*p.tremble*(1-sm(2.75,3.05,u));
  return {x:x+tx,y,H,fx,showNew,fp,rot,lean,sq,pr,pause,moving};
}
// draw the switch layer's current drawing through the spine bone's strip mesh
function drawSack(g,im,st,alpha){
  const k=st.H/im.h,sx=k*st.fx*(1+st.sq*.6),sy=k*(1-st.sq);const ident=Math.abs(sx-1)<1e-4&&Math.abs(sy-1)<1e-4&&Math.abs(st.lean)<1e-4&&Math.abs(st.rot)<1e-4;
  g.save();g.globalAlpha=alpha;
  if(ident){g.drawImage(im.c,Math.round(st.x+im.ox-im.ax),Math.round(st.y+im.oy-im.ay));g.restore();return}
  g.translate(st.x,st.y);g.rotate(st.rot);
  const SH=8,dx=(im.ox-im.ax)*sx,cw=im.c.width;
  for(let y=0;y<im.c.height;y+=SH){const ly=im.oy-im.ay+y+SH/2;const hf=Math.max(0,-ly/im.h);const off=st.lean*im.h*.42*hf*hf*sy;
    g.drawImage(im.c,0,y,cw,Math.min(SH,im.c.height-y),dx+off,(im.oy-im.ay+y)*sy,cw*sx,Math.min(SH,im.c.height-y)*sy+.6)}
  g.restore()}
// the character rig drawn over the sack: root, spine, two ears (the active bone red)
function drawRig(g,p,st,a,u){if(a<.01)return;const im=st.showNew?p.nw:p.old,h=st.H*(1-st.sq),w=im.w*(st.H/im.h)*st.fx;
  g.save();g.translate(st.x,st.y);g.rotate(st.rot);
  const bend=y=>st.lean*h*.42*(y/h)*(y/h);
  const j0=[0,-4],j1=[bend(h*.45),-h*.45],j2=[bend(h*.88),-h*.88];
  // ear bones root at the top corners; Inigo's hang down beside him; a hesitating sack drops them
  const hang=p.s==='I',droop=st.pause;const ears=[-1,1].map(sd=>{const r=[bend(h*.9)+sd*w*.3,-h*.9];
    let ang=hang?Math.PI/2-sd*.25:-Math.PI/2+sd*.55;ang+=sd*droop*1.1*(hang?0:1);const L=hang?h*.55:Math.max(26,h*.24);
    if(st.moving&&!hang)ang-=p.dir*.35*Math.sin(Math.PI*st.pr*p.nh);return [r,[r[0]+Math.cos(ang)*L,r[1]+Math.sin(ang)*L]]});
  const dash=p.ghost,act=st.moving?'#e03c31':'#3c74e0';
  bone(g,j0[0],j0[1],j1[0],j1[1],act,a,dash);bone(g,j1[0],j1[1],j2[0],j2[1],'#3c74e0',a,dash);
  for(const[r,e]of ears){g.save();g.globalAlpha=a*.6;g.strokeStyle='#0d1120';g.lineWidth=1.5;g.setLineDash([4,4]);g.beginPath();g.moveTo(j2[0],j2[1]);g.lineTo(r[0],r[1]);g.stroke();g.restore();
    bone(g,r[0],r[1],e[0],e[1],st.pause?'#e03c31':'#3c74e0',a*.9,dash)}
  g.restore()}

function room(g,v,u,K){
  // switch layer per ring: Whitney room below, Gilliam room swept in behind each ring's bone
  g.drawImage(v.r1.c,0,0);
  const c=lampAt(u);
  for(let j=0;j<NR;j++){const p=ringP(u,j);if(p<=0)continue;const dir=j%2?-1:1;
    g.save();sectorPath(g,c,RING[j],RING[j+1],dir,p);g.clip();
    // the incoming room rides in on the bone: a residual rotation about the lamp that settles to zero
    const res=dir*.16*(1-p)*(1-p);if(Math.abs(res)>1e-4){g.translate(c[0],c[1]);g.rotate(-res);g.translate(-c[0],-c[1])}
    g.drawImage(v.r2.c,0,0);g.restore()}
}
function mesh(g,u,a){if(a<.01)return;const c=lampAt(u);g.save();
  for(let j=1;j<=NR;j++){const r=RING[j];const pin=ringP(u,j-1),pout=j<NR?ringP(u,j):pin,p=Math.min(pin,pout);const dir=(j-1)%2?-1:1;
    // unswept part of the ring line: Whitney dots; swept part: an engraved ink line
    const N=Math.round(r*.09)+24;g.fillStyle='rgba(255,226,170,.75)';g.globalAlpha=a*.8;
    for(let q=0;q<N;q++){const t=q/N;if(t<p)continue;const ang=A0+dir*t*Math.PI*2;const P=ePt(c,r,ang);if(P[1]<-10||P[1]>1090||P[0]<-10||P[0]>1930)continue;g.beginPath();g.arc(P[0],P[1],2.2,0,7);g.fill()}
    if(p>0){g.globalAlpha=a*.85;g.strokeStyle='#1b1410';g.lineWidth=3;g.beginPath();g.ellipse(c[0],c[1],r,r*SQ,0,A0,A0+dir*p*Math.PI*2,dir<0);g.stroke();
      g.strokeStyle='rgba(239,227,189,.55)';g.lineWidth=1;g.stroke()}}
  g.globalAlpha=1;
  // child bones at each ring's leading edge
  for(let j=1;j<NR;j++){const p=ringP(u,j);if(p<=0||p>=1)continue;const dir=j%2?-1:1,ang=A0+dir*p*Math.PI*2;const P0=ePt(c,RING[j]+6,ang),P1=ePt(c,RING[j+1]-6,ang);bone(g,P0[0],P0[1],P1[0],P1[1],'#3c74e0',a)}
  // the smart bone: the lamp's own bone, red, turning one full turn
  const sa=A0+DIAL(u)*Math.PI*2;const T=ePt(c,190,sa);bone(g,c[0],c[1],T[0],T[1],'#e03c31',a);
  // its dial: a tick ring
  g.globalAlpha=a*.9;g.strokeStyle='#e03c31';g.lineWidth=3;g.beginPath();g.ellipse(c[0],c[1],60,60*SQ,0,A0,sa);g.stroke();g.restore()}

TRANSITION({k:9,scion:19,lineage:'Moho Pro — Smart-Bone Character Laboratory',
  op:'The lamp becomes a smart bone; turning it once drives a fan of child bones, one per ring of the Whitney halo grown into a mesh over the room, and each bone sweeps its ring as a switch layer from the harmonic dark room to the engraved parlour, while every sack, rigged with root, spine and ear bones, hops on its root bone to its next mark, bends through a strip mesh, and turns through profile where its drawing switches from harmonic body to paper card.',
  made:'Two switch-layer drawings of one room (the Whitney dark room and the Gilliam parlour, each its deed\'s lever-composited background) under a ring mesh centred on the lamp, drawn as the halo\'s dots where unswept and as engraved ink where swept; each sack is a two-drawing switch layer (its harmonic body at the end of the seduction, its paper card at the start of the slander, carried damage and levers baked in) with a visible Moho skeleton of four bones; the house\'s evidence hangs pinned to the mesh on the wall and its dead lie by the skirting.',
  moved:'One smart-bone angle drives everything: ring bones follow it with a lag, alternate rings turning in opposite directions, and the incoming room rides in on each bone with a residual rotation that settles to zero. Sacks are moved only by their root bones (hops with held foot contacts, squash at contacts, spine lean into the hop, Roessler\'s rock, Inigo\'s low drag, Ogiva\'s long precise hops, Belindo\'s heavy short ones), turn to profile to switch drawings, and a doer that remembers its victim stops mid-way, leans back and drops its ear bones.',
  dur:DUR,
  draw(g,u,X,K){
    const v=build(X,K);
    g.save();
    room(g,v,u,K);
    if(v.r1.imp)impOverlay(g,1-sm(.3,1.6,u));if(v.r2.imp)impOverlay(g,sm(1.4,2.7,u));
    const ma=sm(.08,.45,u)*(1-sm(2.62,3.08,u));
    // evidence pinned on mesh points, and the dead lying by the skirting
    if(ma>.01){const c=lampAt(u);for(const E of v.evid){const bw=104,bh=78,P=ePt(c,RING[E.j],E.ang);const dt=u-E.up;const sw=dt>0?E.dir*.45*Math.exp(-dt*3.2)*Math.sin(dt*13):0;
        g.save();g.globalAlpha=ma;g.translate(P[0],P[1]);g.rotate(E.rot+sw);
        g.strokeStyle='#0d1120';g.lineWidth=1.5;g.beginPath();g.moveTo(0,0);g.lineTo(0,14);g.stroke();g.translate(0,14+bh/2);
        g.fillStyle='rgba(0,0,0,.5)';g.fillRect(-bw/2+6,-bh/2+8,bw,bh);g.fillStyle='#efe3bd';g.fillRect(-bw/2,-bh/2,bw,bh);g.fillStyle='#231b15';g.fillRect(-bw/2+5,-bh/2+5,bw-10,bh-10);
        try{if(E.C&&E.C.trace)E.C.trace(g,{x:-bw/2+6,y:-bh/2+6,w:bw-12,h:bh-12},E.age,K)}catch(e){}
        g.restore();g.save();g.globalAlpha=ma;g.fillStyle='#e03c31';g.beginPath();g.arc(P[0],P[1],5,0,7);g.fill();g.strokeStyle='#0d1120';g.lineWidth=2;g.stroke();g.restore()}
      for(const d of v.dead){g.save();g.globalAlpha=ma*.9;g.filter='grayscale(1) brightness(.75)';const st={x:d.x,y:d.img.ay+4,H:d.img.h*.8,fx:1,sq:0,lean:0,rot:Math.PI/2*.92*(d.x<960?-1:1)};drawSack(g,d.img,st,ma*.9);g.restore()}}
    mesh(g,u,ma);
    // the cast: bodies dragged by their root bone, ghosts gliding, the living hopping
    const list=IDS.map(s=>v.P[s]).filter(p=>p.kind!=='by').map(p=>({p,st:pstate(p,u)}));
    list.sort((a,b)=>(a.st.showNew?(a.p.nw.order??0):(a.p.old.order??0))-(b.st.showNew?(b.p.nw.order??0):(b.p.old.order??0)));
    for(const {p,st}of list){const im=st.showNew?p.nw:p.old;let al=1;if(p.ghost)al=1-.5*sm(.3,.7,u)*(1-sm(2.5,2.95,u));
      if(p.body){g.save();g.filter='grayscale(.8) brightness(.8)';drawSack(g,im,st,al);g.restore();
        const a2=sm(p.t0+.2,p.t0+.4,u)*(1-sm(p.t1-.1,p.t1,u))*ma;if(a2>.01){g.save();g.globalAlpha=a2;g.setLineDash([10,8]);g.strokeStyle='#e03c31';g.lineWidth=2.5;g.beginPath();g.moveTo(st.x,st.y-20);g.lineTo(p.dir<0?-10:1930,st.y-20);g.stroke();g.restore()}}
      else drawSack(g,im,st,al);
      // in profile the drawing is all bone: the rig flares while the switch happens
      const prof=1-st.fx;drawRig(g,p,st,Math.min(1,ma*(.75+prof)),u);
      // onion skins of the skeleton: where the root bone was
      if(ma>.05&&st.moving){for(let j=1;j<=3;j++){const s2=pstate(p,u-j*.07);g.save();g.globalAlpha=.25*(1-j/4)*ma;g.strokeStyle=COL[p.s];g.lineWidth=2;g.beginPath();g.moveTo(s2.x,s2.y);g.lineTo(s2.x+s2.lean*20,s2.y-s2.H*.88);g.stroke();g.restore()}}
    }
    g.restore();
  },
  sound(ac,out,t0,X,K){
    const SN=K.SND;let v;try{v=CACHE.key===X.film.join(',')?CACHE.v:build({...X,DEEDS:window.DEEDS,CONSEQS:window.CONSEQS,MEMORIES:window.MEMORIES},K)}catch(e){return}
    const bus=ac.createGain();bus.gain.value=2.8;bus.connect(out);out=bus;
    const at=x=>t0+x,pan=x=>cl(-1,1,x/960-1);
    const N={R:4,B:3,I:6,O:8},eo=v.eo;
    // the smart bone keyed: a click as the rig appears
    SN.grain(ac,out,at(.32),{bp:4200,q:3,d:.015,a:.2});SN.grain(ac,out,at(.34),{f:660,d:.04,a:.08,att:.05});
    // each ring's switch: begins on a harmonic tone of the outgoing pair (Whitney), lands as a paper flap (Gilliam)
    const hA=N[eo.A],hV=N[eo.V];
    for(let j=0;j<NR;j++){const D0=j*LAG/(1+LAG*(NR-1)),D1=(j*LAG+1)/(1+LAG*(NR-1));
      const tS=.3+2.32*D0*.92,tE=.3+2.32*Math.min(1,D1)*.98;const ang=j%2?.4:-.4;
      SN.grain(ac,out,at(tS),{f:110*(j%2?hV:hA)*(1+j*.0),d:.18,a:.05*(1-j/NR*.6),pan:ang,att:.1,type:'triangle'});
      SN.grain(ac,out,at(tE),{bp:2400+j*60,q:1.4,d:.03,a:.09,pan:-ang,att:.08});SN.grain(ac,out,at(tE+.01),{f:150,d:.05,a:.05,pan:-ang})}
    // the lamp bone's sweep under it all: a soft rising cloth hush
    SN.cloud(ac,out,at(.35),2.3,20,{bp:1100,q:.8,a:.022,d:[.05,.14],spread:.5},u=>Math.sin(Math.PI*u));
    for(const s of IDS){const p=v.P[s];if(p.kind==='by')continue;
      // hops: each contact in the sack's own voice
      if(p.body){SN.say(ac,out,s,at(p.t0+.3),'sink',.5,pan(p.from.x));SN.cloud(ac,out,at(p.t0+.35),p.t1-p.t0-.35,30,{bp:400,a:.03,d:[.05,.12],spread:.2},u=>1-u*.5)}
      else if(p.ghost){SN.say(ac,out,s,at(p.t0),'breathe',.6,pan(p.from.x))}
      else{for(let i=0;i<=p.nh;i++){let tt=p.t0+(p.t1-p.t0)*i/p.nh;if(p.hes&&i/p.nh>.52)tt+=0;const x=lerp(p.from.x,p.to.x,i/p.nh);if(tt>DUR)break;SN.say(ac,out,s,at(tt),'step',i===p.nh?.8:.55,pan(x))}}
      // the view switch through profile: a card snap
      const sm2=(p.s0+p.s1)/2,xs=lerp(p.from.x,p.to.x,.5);SN.grain(ac,out,at(sm2),{bp:3200,q:1,d:.03,a:.16,pan:pan(xs),att:.1});SN.grain(ac,out,at(sm2+.01),{f:110*N[s],d:.08,a:.04,pan:pan(xs),type:'triangle'});
      if(p.hes){const T=p.t1-p.t0,a=p.t0+(T-.42)*.52;SN.say(ac,out,s,at(a+.05),'react',.55*p.hes,pan(lerp(p.from.x,p.to.x,.5)));SN.say(ac,out,s,at(a+.2),'breathe',.5,pan(lerp(p.from.x,p.to.x,.5)))}
      if(p.tremble)SN.say(ac,out,s,at(Math.max(.1,p.t1-.2)),'react',.4*p.tremble,pan(p.to.x));
    }
    // set down: the rig released
    SN.grain(ac,out,at(2.75),{bp:900,q:.8,d:.05,a:.12});SN.grain(ac,out,at(2.92),{bp:4000,q:3,d:.012,a:.12});
  }
});
})();
