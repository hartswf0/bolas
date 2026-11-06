// TRANSITION 10 · Slander (Gilliam engraved cutout parlour) -> Snooping (multiview cutaway: hallway | door with keyhole | lamplit room)
// SCION 28 · After Effects — Mask and Performance Plate Foundry. The join is built as a composition, not a dissolve:
//   PLATE A  the slander parlour (its bg layer + whatever the sack layers leave outside their mattes) is CORNER-PINNED
//            back into the picture frame that hangs on the lamplit room's wall, cropped by an animated LAYER MASK;
//            when it sits in the frame it is LUMA-KEYED out, light tones first (paper wall, then hatching, the black
//            onlookers last), leaving the frame's own panel: the slander becomes something that hangs in the house.
//   PLATE B  the cutaway (bg + props) sits underneath and is revealed as plate A recedes.
//   SACKS    each sack is ROTOSCOPED out of its deed layer (a matte cut on its mark box, levers and carried damage baked
//            in) and PARENTED to a MOTION-TRACKED null that runs from its outgoing mark to its incoming mark.
//            The drawing is SUBSTITUTED only behind a HOLDOUT, never in the open: for a sack that stays on its side the
//            holdout is plate A's own mask edge (inside the mask: the Gilliam card; outside: the multiview drawing);
//            for a sack that crosses sides it is the wall slab between hallway and room (it goes in behind the slab as a
//            card and comes out as a drawing). Leavers exit at the frame edges, enterers come in under plate A.
//   LIGHT    inserted elements (evidence, the dead, passers-by) are graded to the plate's light: in the unlit hall they
//            sink into the dark by the last frame — still in the house, no longer seen.
//   UI       the working project stays visible while it works: roto splines with vertices, track points with search
//            boxes and keyframe trails, corner-pin handles; a lost track (red, jittering) is the doer's hesitation.
// Numerical invariant (checked by the seam harness): u=0 equals the outgoing deed's lever composite at t=5.99, u=dur equals
// the incoming deed's first frame (t=0, levers and carry applied).
(function(){
const DUR=3.2,IDS=['R','B','I','O'];
const CAMX=x=>960+(x-960)*1.22,CAMY=y=>700+(y-700)*1.22;
const WL=CAMX(968),WR=CAMX(1012),WMID=(WL+WR)/2;               // the wall slab on screen
const SLAB={x:WL-10,y:0,w:WR-WL+20,h:1080};
const FRAME={x:CAMX(1183),y:CAMY(423),w:114*1.22,h:144*1.22};    // the picture panel on the room wall
const FRC={x:FRAME.x+FRAME.w/2,y:FRAME.y+FRAME.h/2};
const ST=FRAME.h*1.14/1080;                                      // plate A's final scale (its crop fills the panel)
const PIV={x:(FRC.x-960*ST)/(1-ST),y:(FRC.y-540*ST)/(1-ST)};     // fixed point of the pull-back
const CROPF={x:960-FRAME.w/ST/2,y:540-FRAME.h/ST/2,w:FRAME.w/ST,h:FRAME.h/ST}; // plate-space crop that lands on the panel
const FLOORY=CAMY(860);
const MASKCOL=['#f3d23c','#4fd6e8','#e86fd0','#7fe36a'];
let CACHE={key:null,v:null},PLAN={key:null,v:null};
const sm=(a,b,x)=>{const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)};
const cl=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
const eio=(a,b,x)=>{const u=cl(0,1,(x-a)/(b-a));return u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2};
function cv(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c}

// ---------- lever scaling exactly as film.html applies it ----------
function levF(lev){return 1+.14*Math.max(-1,Math.min(1,lev.loom))-.22*lev.shrink}
function levBox(b,lev){const f=levF(lev),cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}}
function layerFull(D,lt,A,V,ly,carry,lev,K){
  const raw=cv(1920,1080),q=raw.getContext('2d');try{D.draw(q,lt,A,V,K,{layer:ly,carry})}catch(e){}
  if(ly==='bg'||!D.marks)return {c:raw};
  const b=D.marks(lt,A,V,K)[ly];
  const f=levF(lev),cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lev.grey>.05)fl.push(`grayscale(${Math.min(1,lev.grey)}) brightness(${1-.25*lev.grey})`);if(lev.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lev.halo)}px rgba(255,236,180,${Math.min(.9,lev.halo)}))`);
  if(lev.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lev.shadow)}px ${Math.round(-30*lev.shadow)}px ${Math.round(18*lev.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lev.shadow*.4)}))`);
  const out=cv(1920,1080),o=out.getContext('2d');o.filter=fl.join(' ')||'none';o.translate(cx,by);o.scale(f,f);o.translate(-cx,-by);o.drawImage(raw,0,0);
  return {c:out,box:levBox(b,lev)};
}
// rotoscope: cut the sack out of its layer on its mark box; what stays outside the matte stays on the plate
function roto(L){
  const b=L.box;const x0=Math.max(0,Math.floor(b.x-120)),y0=Math.max(0,Math.floor(b.y-90)),x1=Math.min(1920,Math.ceil(b.x+b.w+40)),y1=Math.min(1080,Math.ceil(b.y+b.h+26));
  const w=Math.max(2,x1-x0),h=Math.max(2,y1-y0);const img=cv(w,h);img.getContext('2d').drawImage(L.c,x0,y0,w,h,0,0,w,h);
  const rem=cv(1920,1080),r=rem.getContext('2d');r.drawImage(L.c,0,0);r.clearRect(x0,y0,w,h);
  // the roto spline: 26 rays from the box centre, outermost opaque pixel within the mark (+ a margin)
  let poly=[];try{const d=img.getContext('2d').getImageData(0,0,w,h).data;const cx=b.x+b.w/2-x0,cy=b.y+b.h*.55-y0,R=Math.hypot(b.w,b.h)*.62+14;
    for(let i=0;i<26;i++){const a=i/26*Math.PI*2,ca=Math.cos(a),sa=Math.sin(a);let hit=null;
      for(let rr=R;rr>2;rr-=3){const px=Math.round(cx+ca*rr),py=Math.round(cy+sa*rr);if(px<0||py<0||px>=w||py>=h)continue;if(d[(py*w+px)*4+3]>60){hit=[px+x0+ca*5,py+y0+sa*5];break}}
      if(hit)poly.push(hit)}}catch(e){}
  if(poly.length<5)poly=[[b.x,b.y],[b.x+b.w,b.y],[b.x+b.w,b.y+b.h],[b.x,b.y+b.h]];
  return {img,ox:x0,oy:y0,box:b,ax:b.x+b.w/2,ay:b.y+b.h,h:b.h,w:b.w,rem,poly};
}
function impOverlay(q,a){q.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)q.fillRect(0,y,1920,2)}

// ---------- the plan: who travels where and when (ledger + marks only; no canvases, so sound can use it) ----------
function plan(X,K){
  const key=X.film.join(',');if(PLAN.key===key)return PLAN.v;
  const Lg=X.ledger,k=X.k,eo=Lg.ev[k-1],ei=Lg.ev[k],Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed];
  const sO=Lg.states[k-1],sI=Lg.states[k];
  const mO=Do.marks(5.99,eo.A,eo.V,K),mI=Di.marks(0.001,ei.A,ei.V,K);
  const bO={},bI={};bO[eo.A]=levBox(mO.A,sO.levers[eo.A]);bO[eo.V]=levBox(mO.V,sO.levers[eo.V]);bI[ei.A]=levBox(mI.A,sI.levers[ei.A]);bI[ei.V]=levBox(mI.V,sI.levers[ei.V]);
  const sacks=[];let nst=0;
  for(const s of IDS){const inO=s in bO,inI=s in bI,rO=inO?(s===eo.A?'A':'V'):null,rI=inI?(s===ei.A?'A':'V'):null;
    const kind=inO&&inI?'stay':inO?'leave':inI?'enter':'by';const sk={id:s,kind,rO,rI,alive:sI.alive[s],ghost:inI&&!sI.alive[s]};
    if(kind==='stay'){const a=bO[s],b=bI[s];sk.from={x:a.x+a.w/2,y:a.y+a.h};sk.to={x:b.x+b.w/2,y:b.y+b.h};sk.hO=a.h;sk.hN=b.h;
      sk.cross=(rO==='A')!==(rI==='A');sk.t0=.5+nst*.14;sk.t1=sk.t0+(sk.cross?1.85:1.55);nst++}
    if(kind==='leave'){const a=bO[s];sk.from={x:a.x+a.w/2,y:a.y+a.h};sk.to={x:rO==='A'?-260:2200,y:FLOORY};sk.hO=a.h;sk.t0=.45;sk.t1=2.6}
    if(kind==='enter'){const b=bI[s];sk.to={x:b.x+b.w/2,y:b.y+b.h};sk.from={x:rI==='A'?-260:2200,y:b.y+b.h};sk.hN=b.h;sk.t0=.95;sk.t1=2.75}
    if(kind==='by'){if(sk.alive){sk.from={x:WMID+40,y:FLOORY};sk.to={x:-300,y:FLOORY};sk.t0=.95+(s.charCodeAt(0)%3)*.12;sk.t1=sk.t0+1.95}
      else{const x=[140,300,520,700][IDS.indexOf(s)];sk.from=sk.to={x,y:FLOORY+40};sk.t0=0;sk.t1=0}}
    sacks.push(sk)}
  // memory on the way: the doer's track is lost (held, jittering) if it carries a strong memory of the one it will meet
  const memA=LEDGER.memories(Lg,ei.A,k).filter(m=>m.other===ei.V&&m.weight>.3);
  const memV=LEDGER.memories(Lg,ei.V,k).filter(m=>m.other===ei.A&&m.weight>.3);
  const pa=sacks.find(z=>z.id===ei.A);if(memA.length&&pa.kind!=='by'){pa.hes=Math.min(1,memA[0].weight);pa.memK=memA[0].k;pa.t1=Math.min(2.85,pa.t1+.3)}
  const pv=sacks.find(z=>z.id===ei.V);if(memV.length)pv.trem=Math.min(1,memV[0].weight);
  const impO=Lg.states[k].impossible.some(z=>z.k===k-1),impI=Lg.states[k+1].impossible.some(z=>z.k===k);
  const v={sacks,eo,ei,sO,sI,memA,memV,impO,impI,bO,bI};PLAN.key=key;PLAN.v=v;return v;
}
// progress along a track (with a held, lost-track stretch for the hesitant doer)
function prog(sk,u){if(sk.t1<=sk.t0)return 0;
  if(sk.hes){const D=sk.t1-sk.t0,k1=sk.t0+D*.42,k2=k1+.42*sk.hes+.1,k3=k2+.08;
    return u<k1?.55*eio(sk.t0,k1,u):u<k2?.55-.05*sm(k1,k2,u):u<k3?.5:.5+.5*eio(k3,sk.t1,u)}
  return eio(sk.t0,sk.t1,u)}
function lost(sk,u){if(!sk.hes)return 0;const D=sk.t1-sk.t0,k1=sk.t0+D*.42,k2=k1+.42*sk.hes+.1;return u>k1-.05&&u<k2+.05?1:0}
function posOf(sk,u,K){const p=prog(sk,u);let x=lerp(sk.from.x,sk.to.x,p),y=lerp(sk.from.y,sk.to.y,p);
  // a walk: small hops along the floor (12 fps steps, as the parlour was shot)
  const moving=p>0&&p<1;if(moving){const ph=(u-sk.t0)*4.2;y-=Math.abs(Math.sin(ph*Math.PI))*14*(sk.id==='I'?.4:1)}
  if(sk.trem&&u>.3&&u<DUR-.25){x+=(K.hash(Math.floor(u*24)+3.3)-.5)*9*sk.trem}
  if(sk.hes&&lost(sk,u)){x+=(K.hash(Math.floor(u*24)*1.7)-.5)*6}
  return{x,y,p}}

// ---------- build the plates (cached per film) ----------
function build(X,K){
  const key=X.film.join(',');if(CACHE.key===key)return CACHE.v;
  const P=plan(X,K),Lg=X.ledger,k=X.k,eo=P.eo,ei=P.ei,Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed],sO=P.sO,sI=P.sI;
  function plate(D,lt,e,st){const order=D.layers||['bg','V','A'],c=cv(1920,1080),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,1920,1080);const pc={};
    for(const ly of order){const Lr=layerFull(D,lt,e.A,e.V,ly,st.body,ly==='bg'?null:st.levers[ly==='A'?e.A:e.V],K);
      if(ly==='bg'||!Lr.box){q.drawImage(Lr.c,0,0);continue}const p=roto(Lr);q.drawImage(p.rem,0,0);pc[ly==='A'?e.A:e.V]=p}
    return{c,pc}}
  const A=plate(Do,5.99,eo,sO),B=plate(Di,0.001,ei,sI);
  // wall slab holdout, cut from plate B
  const slab=cv(SLAB.w,SLAB.h);slab.getContext('2d').drawImage(B.c,SLAB.x,SLAB.y,SLAB.w,SLAB.h,0,0,SLAB.w,SLAB.h);
  // drawings for sacks the incoming shot does not hold (leavers, passers-by, the dead): the snooping language, first frame
  const extra={};
  for(const sk of P.sacks){if(sk.kind==='leave'||sk.kind==='by'){const role=sk.kind==='leave'?sk.rO:'A',other=IDS.find(o=>o!==sk.id);
    const Lr=role==='A'?layerFull(Di,0.001,sk.id,other,'A',sI.body,sI.levers[sk.id],K):layerFull(Di,0.001,other,sk.id,'V',sI.body,sI.levers[sk.id],K);
    const pc=roto(Lr);
    // graded to the unlit hall: the insert takes the plate's light once, here
    const dk=cv(pc.img.width,pc.img.height),dq=dk.getContext('2d');dq.filter=sk.alive?'brightness(.55) saturate(.6)':'grayscale(.8) brightness(.45)';dq.drawImage(pc.img,0,0);pc.dark=Object.assign({},pc,{img:dk});
    extra[sk.id]=pc}}
  // evidence still in the house: inserts on the floors of the hall and the room
  const SLOTS=[[90,985],[300,1010],[520,975],[760,1015],[1110,1000],[1350,1030],[1560,990],[1800,1020],[200,1060],[640,1062],[1240,1065],[1690,1066]];
  const evid=sI.evidence.map((e,i)=>({e,C:X.CONSEQS&&X.CONSEQS[e.deed],x:SLOTS[i%12][0],y:SLOTS[i%12][1],age:k-1-e.k,hall:SLOTS[i%12][0]<WL,
    t:.75+i*.07}));
  for(const ev of evid){const t=cv(220,160),q=t.getContext('2d');if(ev.C&&ev.C.trace){q.save();try{ev.C.trace(q,{x:50,y:30,w:120,h:90},ev.age,K)}catch(e){}q.restore()}
    q.globalCompositeOperation='source-atop';q.fillStyle=ev.hall?'rgba(18,26,44,.55)':'rgba(70,40,18,.28)';q.fillRect(0,0,220,160);ev.img=t}
  const work=cv(1920,1080),key2=cv(Math.ceil(FRAME.w)+4,Math.ceil(FRAME.h)+4),tmp=cv(220,160);
  // the remembered moment, as a reference plate the tracker shows when the doer's track is lost
  const pa=P.sacks.find(z=>z.memK!=null);const memPlate=pa&&X.still?X.still(Lg.ev[pa.memK]):null;
  const v={A,B,slab,extra,evid,work,key2,tmp,memPlate};if(X.still){CACHE.key=key;CACHE.v=v}return v;
}

// ---------- the corner pin of plate A: pull back into the picture panel ----------
function pin(u){const e=eio(.28,2.05,u);const s=Math.exp(Math.log(ST)*e);
  const T=(x,y)=>({x:PIV.x+(x-PIV.x)*s,y:PIV.y+(y-PIV.y)*s});
  const cr={x:lerp(0,CROPF.x,e),y:lerp(0,CROPF.y,e),w:lerp(1920,CROPF.w,e),h:lerp(1080,CROPF.h,e)};
  const a=T(cr.x,cr.y),b=T(cr.x+cr.w,cr.y+cr.h);return{e,s,T,crop:cr,Q:{x:a.x,y:a.y,w:b.x-a.x,h:b.y-a.y}}}
const rectPath=(g,r)=>{g.beginPath();g.rect(r.x,r.y,r.w,r.h)};
function clipOut(g,r){g.beginPath();g.rect(-50,-50,2020,1180);g.rect(r.x,r.y,r.w,r.h);g.clip('evenodd')}
// a sprite (roto piece) on its tracked null: anchor-to-anchor, scaled
function sprite(g,pc,x,y,sc,alpha,rot){if(!pc||alpha<=0)return;g.save();g.globalAlpha*=alpha;g.translate(x,y);if(rot)g.rotate(rot);g.scale(sc,sc);g.translate(-pc.ax,-pc.ay);g.drawImage(pc.img,pc.ox,pc.oy);g.restore()}
function splineOf(g,pc,x,y,sc,col,a,u,seed){if(a<.02||!pc)return;g.save();g.globalAlpha=a;g.strokeStyle=col;g.lineWidth=2.6;g.lineJoin='round';
  const P=pc.poly.map(p=>[x+(p[0]-pc.ax)*sc,y+(p[1]-pc.ay)*sc]);const n=P.length;const draw=Math.min(1,u)*n;
  g.beginPath();for(let i=0;i<=Math.floor(draw)&&i<=n;i++){const p=P[i%n],q=P[(i+n-1)%n],r=P[(i+1)%n];
    // a smooth (Catmull-like) roto curve through the vertices
    if(i===0)g.moveTo(p[0],p[1]);else{const c1=[q[0]+(p[0]-P[(i+n-2)%n][0])/6,q[1]+(p[1]-P[(i+n-2)%n][1])/6],c2=[p[0]-(r[0]-q[0])/6,p[1]-(r[1]-q[1])/6];g.bezierCurveTo(c1[0],c1[1],c2[0],c2[1],p[0],p[1])}}
  g.stroke();g.fillStyle=col;for(let i=0;i<Math.min(n,Math.floor(draw)+1);i++){const p=P[i];g.fillRect(p[0]-3.5,p[1]-3.5,7,7)}g.restore()}
function trackPt(g,x,y,a,col,lostA,K,u){if(a<.02)return;g.save();g.globalAlpha=a;const c=lostA?'#ff4a3a':col;
  const j=lostA?(K.hash(Math.floor(u*24)+.5)-.5)*8:0;g.strokeStyle=c;g.lineWidth=1.6;g.strokeRect(x-14+j,y-14,28,28);g.setLineDash(lostA?[3,5]:[6,4]);g.strokeRect(x-38-j,y-38,76,76);g.setLineDash([]);
  g.beginPath();g.moveTo(x-6,y);g.lineTo(x+6,y);g.moveTo(x,y-6);g.lineTo(x,y+6);g.stroke();g.restore()}
function trail(g,sk,u,a,col,K,oy){if(a<.02||sk.t1<=sk.t0)return;g.save();g.globalAlpha=a*.85;g.fillStyle=col;
  for(let i=0;i<=24;i++){const uu=lerp(sk.t0,sk.t1,i/24);const p=posOf(sk,uu,K);const done=uu<=u;g.globalAlpha=a*(done?.85:.35);g.fillRect(p.x-2,p.y+oy-2,4,4)}g.restore()}
function handle(g,x,y,a){if(a<.02)return;g.save();g.globalAlpha=a;g.strokeStyle='#f3d23c';g.lineWidth=2;g.beginPath();g.arc(x,y,10,0,7);g.moveTo(x-16,y);g.lineTo(x+16,y);g.moveTo(x,y-16);g.lineTo(x,y+16);g.stroke();g.restore()}

TRANSITION({ k:10, scion:28, lineage:'After Effects — Mask and Performance Plate Foundry (keying, tracking, rotoscoping, compositing)',
  op:'The slander parlour plate is corner-pinned back into the picture panel on the lamplit room\'s wall under an animated layer mask and then luma-keyed out light-first; each sack is rotoscoped out of its layer, parented to a motion-tracked null from its old mark to its new one, and its drawing is substituted only behind a holdout: plate A\'s mask edge for a sack that keeps its side, the wall slab for a sack that crosses.',
  made:'Two plates (the engraved parlour, and the cutaway hallway/wall/room) and one roto matte per sack cut from the deeds\' own layers with levers and carried damage baked in; the wall slab is a holdout matte cut from the cutaway plate. Evidence, the dead and passers-by are inserts graded to the plate\'s light.',
  moved:'Keyframed transforms: a corner-pin pull-back about a fixed point, a crop mask, tracked nulls with 12-step walking hops, and a luma-key threshold sweeping from white to black. Visible project marks show it working: roto splines, track points with search boxes and keyframe trails, corner-pin handles, a lost track where the doer hesitates.',
  dur:DUR,
  draw(g,u,X,K){
    const P=plan(X,K),V=build(X,K),W=V.work,w=W.getContext('2d');u=cl(0,DUR,u);
    const pn=pin(u),Q=pn.Q;const ui=sm(.02,.4,u)*(1-sm(2.35,2.85,u));
    const keyT=sm(2.4,2.95,u);   // luma key threshold sweep (0 = nothing keyed, 1 = all keyed)
    // 1. plate B (cutaway, props)
    g.drawImage(V.B.c,0,0);
    // passers-by and the dead, graded to the unlit hall (they sink into its dark by the last frame)
    const lightOut=1-sm(2.35,3.1,u);
    for(const sk of P.sacks){if(sk.kind!=='by')continue;const pc=V.extra[sk.id];
      if(sk.alive){const p=posOf(sk,u,K);if(u<sk.t0||u>sk.t1)continue;g.save();g.beginPath();g.rect(-400,0,WL+400,1080);g.clip();sprite(g,pc.dark,p.x,p.y,1,.9);g.restore()}
      else{const a=sm(.6,1.1,u)*lightOut;g.save();g.globalAlpha=a*.5;g.fillStyle='#000';g.beginPath();g.ellipse(sk.from.x,sk.from.y+4,pc.w*.6,10,0,0,7);g.fill();g.restore();sprite(g,pc.dark,sk.from.x,sk.from.y,.85,a,-.42)}}
    // sacks living under plate A: enterers, and the new drawings of sacks keeping their side
    for(const sk of P.sacks){
      if(sk.kind==='enter'){const p=posOf(sk,u,K);const pc=V.B.pc[sk.id];g.save();if(sk.rI==='A'){g.beginPath();g.rect(-400,0,WL+400,1080);g.clip()}else{g.beginPath();g.rect(WR,0,2400,1080);g.clip()}
        sprite(g,pc,p.x,p.y,1,sk.ghost?lerp(.5,1,sm(2.5,3.1,u)):1);g.restore()}
      if(sk.kind==='stay'&&!sk.cross){const p=posOf(sk,u,K);const pc=V.B.pc[sk.id];const sc=lerp(sk.hO/sk.hN,1,p.p);g.save();if(sk.rI==='A'){g.beginPath();g.rect(-400,0,WL+400,1080);g.clip()}
        sprite(g,pc,p.x,p.y,sc,sk.ghost?lerp(.5,1,sm(2.5,3.1,u)):1);g.restore()}
      if(sk.kind==='leave'){const p=posOf(sk,u,K);const pc=V.extra[sk.id];if(u>sk.t1)continue;const sc=sk.hO/pc.h;g.save();if(sk.rO==='A'){g.beginPath();g.rect(-400,0,WL+400,1080);g.clip()}sprite(g,pc,p.x,p.y,sc,1);g.restore()}}
    if(P.impI){g.save();clipOut(g,Q);impOverlay(g,1);g.restore()}
    // 2. plate A, corner-pinned and cropped by its mask, keyed at the end
    const kx=Math.floor(FRAME.x)-1,ky=Math.floor(FRAME.y)-1;
    if(Q.w>1){const ww=keyT>0?V.key2.getContext('2d',{willReadFrequently:true}):g;if(keyT>0){ww.setTransform(1,0,0,1,0,0);ww.clearRect(0,0,V.key2.width,V.key2.height);ww.translate(-kx,-ky)}
      {const w=ww;w.save();rectPath(w,Q);w.clip();
      w.translate(PIV.x,PIV.y);w.scale(pn.s,pn.s);w.translate(-PIV.x,-PIV.y);w.drawImage(V.A.c,0,0);if(P.impO)impOverlay(w,1);w.restore();
      // sacks keeping their side still show as cards while inside plate A's mask (the mask edge is their holdout)
      w.save();rectPath(w,Q);w.clip();for(const sk of P.sacks){if(!((sk.kind==='stay'&&!sk.cross)||sk.kind==='leave'))continue;const p=posOf(sk,u,K);
        const sc=sk.kind==='stay'?lerp(1,sk.hN/sk.hO,p.p):1;sprite(w,V.A.pc[sk.id],p.x,p.y,sc,1)}w.restore();
      // the light-wrap of the receding plate: a thin glow and grain match on its edge while it moves
      if(pn.e>0&&pn.e<1){w.save();w.strokeStyle=`rgba(255,232,180,${.35*Math.sin(Math.PI*pn.e)})`;w.lineWidth=3;w.strokeRect(Q.x,Q.y,Q.w,Q.h);w.restore()}
      if(keyT>0){const kw=V.key2.width,kh=V.key2.height;try{w.setTransform(1,0,0,1,0,0);const id=w.getImageData(0,0,kw,kh),d=id.data;const thr=1.04-1.12*keyT,soft=.09;
          for(let i=0;i<d.length;i+=4){if(!d[i+3])continue;const l=(.3*d[i]+.59*d[i+1]+.11*d[i+2])/255;const m=cl(0,1,(thr-l)/soft+.5);d[i+3]=Math.round(d[i+3]*m)}
          w.putImageData(id,0,0)}catch(e){}}
      }if(keyT>0)g.drawImage(V.key2,kx,ky)}
    // 3. sacks crossing sides: the wall slab hides the substitution
    for(const sk of P.sacks){if(!(sk.kind==='stay'&&sk.cross))continue;const p=posOf(sk,u,K);const fromL=sk.rO==='A';
      g.save();g.beginPath();if(fromL)g.rect(-400,0,WMID+400,1080);else g.rect(WMID,0,2400,1080);g.clip();sprite(g,V.A.pc[sk.id],p.x,p.y,lerp(1,sk.hN/sk.hO,p.p),1);g.restore();
      g.save();clipOut(g,Q);g.beginPath();if(fromL)g.rect(WR,0,2400,1080);else g.rect(-400,0,WL+400,1080);g.clip();sprite(g,V.B.pc[sk.id],p.x,p.y,lerp(sk.hO/sk.hN,1,p.p),sk.ghost?lerp(.5,1,sm(2.5,3.1,u)):1);g.restore()}
    // the slab holdout over everything that passes behind it (outside plate A's mask)
    g.save();clipOut(g,Q);g.drawImage(V.slab,SLAB.x,SLAB.y);g.restore();
    // 4. evidence inserts, graded to the light where they lie
    g.save();clipOut(g,Q);for(const ev of V.evid){const a=sm(ev.t,ev.t+.4,u)*(ev.hall?lightOut:1-sm(2.4,3.1,u));if(a<.01)continue;
      g.globalAlpha=a;g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(ev.x,ev.y+38,62,9,0,0,7);g.fill();g.drawImage(ev.img,ev.x-110,ev.y-80)}g.restore();
    // 5. the working project: corner-pin handles, roto splines, track points and keyframe trails
    if(ui>0){const T0=pin(0).Q,T1=pin(DUR).Q;const cs=[[0,0],[1,0],[1,1],[0,1]];
      g.save();g.globalAlpha=ui*.6;g.fillStyle='#f3d23c';for(const[c0,c1]of cs)for(let i=0;i<=20;i++){const qq=pin(lerp(.28,2.05,i/20)).Q;g.fillRect(qq.x+qq.w*c0-1.5,qq.y+qq.h*c1-1.5,3,3)}g.restore();
      for(const[c0,c1]of cs)handle(g,Q.x+Q.w*c0,Q.y+Q.h*c1,ui*(pn.e<.999?1:.5));
      g.save();g.globalAlpha=ui*.8;g.strokeStyle='#f3d23c';g.lineWidth=1.5;g.setLineDash([10,6]);g.strokeRect(Q.x,Q.y,Q.w,Q.h);g.restore();
      // slab holdout outline
      g.save();clipOut(g,Q);g.globalAlpha=ui*.6;g.strokeStyle='#e86fd0';g.lineWidth=2;g.setLineDash([4,6]);g.strokeRect(WL,CAMY(196),WR-WL,1080-CAMY(196));g.restore();
      P.sacks.forEach((sk,i)=>{const col=MASKCOL[IDS.indexOf(sk.id)];if(sk.kind==='by'&&!sk.alive)return;if(sk.kind==='by'&&(u<sk.t0||u>sk.t1))return;
        const p=posOf(sk,u,K);let pc,sc;const newSide=sk.cross?(sk.rO==='A'?p.x>WMID:p.x<WMID):!(p.x>Q.x&&p.x<Q.x+Q.w&&p.y>Q.y&&p.y<Q.y+Q.h);
        if(sk.kind==='enter'){pc=V.B.pc[sk.id];sc=1}else if(sk.kind==='by'||sk.kind==='leave'&&newSide){pc=V.extra[sk.id];sc=sk.kind==='leave'?sk.hO/pc.h:1}
        else if(sk.kind==='leave'){pc=V.A.pc[sk.id];sc=1}else if(newSide){pc=V.B.pc[sk.id];sc=lerp(sk.hO/sk.hN,1,p.p)}else{pc=V.A.pc[sk.id];sc=lerp(1,sk.hN/sk.hO,p.p)}
        const sa=ui*(sk.ghost?.9:1);g.save();if(sk.kind==='by'){g.beginPath();g.rect(-400,0,WL+400,1080);g.clip()}splineOf(g,pc,p.x,p.y,sc,sk.ghost?'#7fe36a':col,sa,(u-.05-i*.06)/.45,i);
        trail(g,sk,u,ui,col,K,-pc.h*sc*.5);trackPt(g,p.x,p.y-pc.h*sc*.5,ui,col,lost(sk,u),K,u);g.restore()})}
    // the doer's lost track: the remembered shot comes up as a reference plate over it, red-framed, while it hesitates
    if(V.memPlate){const sk=P.sacks.find(z=>z.memK!=null);const D=sk.t1-sk.t0,k1=sk.t0+D*.42,k2=k1+.42*sk.hes+.1;const a=sm(k1-.05,k1+.12,u)*(1-sm(k2,k2+.18,u));
      if(a>.01){const p=posOf(sk,u,K);const w0=300,h0=169,x0=cl(20,1900-w0,p.x-w0/2),y0=Math.max(40,p.y-(sk.hN||sk.hO||200)*1.15-h0-40);
        g.save();g.globalAlpha=a*(.75+.25*K.hash(Math.floor(u*24)));g.drawImage(V.memPlate,x0,y0,w0,h0);g.globalAlpha=a;g.strokeStyle='#ff4a3a';g.lineWidth=3;g.setLineDash([8,5]);g.strokeRect(x0,y0,w0,h0);
        g.setLineDash([]);g.beginPath();g.moveTo(x0+w0/2,y0+h0);g.lineTo(p.x,p.y-(sk.hN||sk.hO||200)*.5-40);g.stroke();g.restore()}}
    // grain matched across plate and inserts while they are being joined
    const gr=Math.sin(Math.PI*cl(0,1,u/DUR));if(gr>.02){g.save();g.globalAlpha=.10*gr;for(let i=0;i<260;i++){const h=K.hash(i*3.7+Math.floor(u*24)*.13);g.fillStyle=h>.5?'#fff3dc':'#000';g.fillRect(K.hash(i*1.3+Math.floor(u*24))*1920,K.hash(i*7.1+Math.floor(u*24)*.7)*1080,2,2)}g.restore()}
  },
  sound(ac,out,t0,X,K){const P=plan(X,K),S=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1));
    // the plate is taken: a paper lift and a long slide of engraved card pulled back into the panel
    S.cloud(ac,out,t0+.25,1.8,36,{bp:1600,q:2,a:.06,d:[.02,.07],noise:1,spread:.4},u=>Math.sin(Math.PI*u)*(1-u*.5));
    // corner-pin keyframes: four handle ticks at the start and at the landing
    for(let i=0;i<4;i++){S.grain(ac,out,t0+.22+i*.03,{f:2600+i*240,d:.016,a:.06,pan:pan([0,1920,1920,0][i]),att:.05});S.grain(ac,out,t0+2.05+i*.03,{f:2100+i*200,d:.02,a:.06,pan:pan(FRC.x),att:.05})}
    // roto splines: a dry click per vertex as each matte is drawn on
    P.sacks.forEach((sk,i)=>{if(sk.kind==='by')return;const x=sk.from.x;for(let v=0;v<6;v++)S.grain(ac,out,t0+.06+i*.06+v*.07,{bp:5200,q:5,d:.008,a:.07,pan:pan(x)})});
    // the walks, in each sack's own voice; the crossing sack's swap behind the wall is a hush through the door
    for(const sk of P.sacks){if(sk.t1<=sk.t0)continue;const n=Math.max(3,Math.round((sk.t1-sk.t0)*4.2*.6));
      for(let h=1;h<=n;h++){const uu=sk.t0+(sk.t1-sk.t0)*h/n,p=posOf(sk,uu,K);S.say(ac,out,sk.id,t0+uu,h===n&&sk.kind!=='leave'&&sk.kind!=='by'?'land':'step',sk.kind==='by'?.5:1.1,pan(p.x))}
      if(sk.cross){let uc=sk.t0;for(let i=0;i<=80;i++){const uu=lerp(sk.t0,sk.t1,i/80);if((posOf(sk,uu,K).x>WMID)!==(sk.rO!=='A')){uc=uu;break}}
        S.cloud(ac,out,t0+uc-.08,.35,60,{bp:700,a:.045,d:[.02,.06],noise:1},u=>Math.sin(Math.PI*u));S.say(ac,out,sk.id,t0+uc+.1,'react',.5,pan(WMID))}
      if(sk.hes)S.say(ac,out,sk.id,t0+sk.t0+(sk.t1-sk.t0)*.45,'breathe',.9,pan(sk.from.x));
      if(sk.ghost)S.cloud(ac,out,t0+sk.t0,1.4,18,{f:440*Math.pow(2,(S.VOICE[sk.id].base+24-69)/12),a:.025,d:[.1,.25],glide:.05},u=>Math.sin(Math.PI*u));
      if(sk.kind==='by'&&!sk.alive)S.say(ac,out,sk.id,t0+.7,'sink',.6,pan(sk.from.x))}
    // evidence set down: one soft tap each
    X.ledger.states[X.k].evidence.forEach((e,i)=>S.grain(ac,out,t0+.8+i*.07,{bp:900+i*120,d:.03,a:.05,pan:(K.hash(i)-.5)}));
    // the luma key: a hiss narrowing from bright to dark as the panel empties
    S.cloud(ac,out,t0+2.4,.6,40,{bp:6000,q:1,a:.05,d:[.01,.04],noise:1,spread:.2,glide:-.4},u=>1-u);
    S.grain(ac,out,t0+2.95,{f:180,d:.25,a:.16,glide:-.2,pan:pan(FRC.x),type:'triangle',att:.2});
  }
});
})();
