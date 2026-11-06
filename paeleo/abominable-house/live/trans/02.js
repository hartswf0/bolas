// TRANSITION 02 · Drugging (spring-dynamics room) -> Incitement to Suicide (Norstein fog planes)
// SCION 24 · Live2D Cubism — Portrait Volume Illusion.
// The house is one rigged drawing with a single parameter axis, HouseAngle (0 -> 90). Each room is a
// keyform: the drugging room is the drawing at HouseAngle 0, the fog room is the drawing at HouseAngle 90,
// and the two are adjacent faces of one warp deformer (a cylinder-like lattice). Between the keyforms the
// lattice is interpolated from flat to curved and back (volume keyform), so the house turns its head.
// Every sack is a child warp deformer glued to the house lattice, with its own parameters:
//   AngleX (turn: the middle of the drawing slides toward the turn, the outline stays put),
//   EarL/EarR physics (top rows are point masses lagging the sack's screen acceleration),
//   Walk (squash/bob per step), EarLift (an almost-speaking lift), Droop (drowsy expression state).
// A sack in both shots switches drawings (part opacity keyform) at its own view limit, mid-turn.
// Invariant (numeric): at u=0 and u=dur every deformer is identity, so the frames equal the deeds' frames.
(function(){
const W=1920,H=1080,R=960/Math.sin(Math.PI/4),DUR=3.0,IDS=['R','B','I','O'];
const cl=(a,b,x)=>Math.max(a,Math.min(b,x)),lerp=(a,b,u)=>a+(b-a)*u;
const sm=(a,b,x)=>{const u=cl(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
const FLOOR=['cup','flour','coins','gun','rope','cord'];
const P0=.22,P1=DUR-.24;                       // the HouseAngle sweep window
const pAt=u=>sm(P0,P1,u);
const volAt=p=>Math.sin(Math.PI*p);            // the curved keyform's weight (0 at both rooms)
const mkc=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c};

// ---------- the house deformer: face coordinate (Phi degrees on the drum, y) -> screen ----------
// face 0 (drugging) pixel x maps to Phi=(x/W-.5)*90; face 1 (fog room) to Phi=(x/W-.5)*90-90; the shared column Phi=-45 is the house corner
function drum(Phi,y,p,vol){const th=90*p,ad=Phi+th,a=ad*Math.PI/180,c=Math.cos(a);
 const xf=W/2+ad/90*W,xd=W/2+R*Math.sin(a);
 const yd=H*.5+(y-H*.5)*(.8+.2*c);
 return [lerp(xf,xd,vol),lerp(y,yd,vol),c]}
const phiOf=(x,face)=>(x/W-.5)*90-90*face;

// ---------- textured triangle mesh ----------
function tri(g,img,x0,y0,x1,y1,x2,y2,u0,v0,u1,v1,u2,v2,cx,cy,cw,ch){
 const den=u0*(v1-v2)+u1*(v2-v0)+u2*(v0-v1);if(Math.abs(den)<1e-6)return;
 const mx=(x0+x1+x2)/3,my=(y0+y1+y2)/3,ex=(x,y)=>{const dx=x-mx,dy=y-my,d=Math.hypot(dx,dy)||1;return [x+dx/d*.9,y+dy/d*.9]};
 const A=ex(x0,y0),B=ex(x1,y1),C=ex(x2,y2);
 g.save();g.beginPath();g.moveTo(A[0],A[1]);g.lineTo(B[0],B[1]);g.lineTo(C[0],C[1]);g.closePath();g.clip();
 const a=(x0*(v1-v2)+x1*(v2-v0)+x2*(v0-v1))/den,b=(y0*(v1-v2)+y1*(v2-v0)+y2*(v0-v1))/den,
  c=(x0*(u2-u1)+x1*(u0-u2)+x2*(u1-u0))/den,d=(y0*(u2-u1)+y1*(u0-u2)+y2*(u1-u0))/den,
  e=(x0*(u1*v2-u2*v1)+x1*(u2*v0-u0*v2)+x2*(u0*v1-u1*v0))/den,f=(y0*(u1*v2-u2*v1)+y1*(u2*v0-u0*v2)+y2*(u0*v1-u1*v0))/den;
 g.transform(a,b,c,d,e,f);
 const sx=Math.max(0,cx-2),sy=Math.max(0,cy-2),sw=Math.min(img.width-sx,cw+4),sh=Math.min(img.height-sy,ch+4);
 if(sw>0&&sh>0)g.drawImage(img,sx,sy,sw,sh,sx,sy,sw,sh);g.restore()}
// map(sx,sy) -> [x,y,vis]; source rect in img pixels
function mesh(g,img,sx0,sy0,sw,sh,nx,ny,map){const P=[];
 for(let j=0;j<=ny;j++){const row=[];for(let i=0;i<=nx;i++)row.push(map(sx0+sw*i/nx,sy0+sh*j/ny));P.push(row)}
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const a=P[j][i],b=P[j][i+1],c=P[j+1][i+1],d=P[j+1][i];if(a[2]<=0&&b[2]<=0)continue;
  const u0=sx0+sw*i/nx,u1=sx0+sw*(i+1)/nx,v0=sy0+sh*j/ny,v1=sy0+sh*(j+1)/ny,cw=u1-u0,ch=v1-v0;
  tri(g,img,a[0],a[1],b[0],b[1],c[0],c[1],u0,v0,u1,v0,u1,v1,u0,v0,cw,ch);
  tri(g,img,a[0],a[1],c[0],c[1],d[0],d[1],u0,v0,u1,v1,u0,v1,u0,v0,cw,ch)}
 return P}

// ---------- the deeds' layers with the film's lever composite, cut into parts ----------
function leverFilter(lv){const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);
 if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
 if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);
 return fl.join(' ')||'none'}
const leverScale=lv=>1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink;
function alphaBox(cv){const q=cv.getContext('2d'),d=q.getImageData(0,0,cv.width,cv.height).data;let x0=1e9,y0=1e9,x1=-1,y1=-1;
 for(let y=0;y<cv.height;y+=2)for(let x=0;x<cv.width;x+=2)if(d[(y*cv.width+x)*4+3]>3){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}
 if(x1<0)return null;return {x:Math.max(0,x0-3),y:Math.max(0,y0-3),w:Math.min(cv.width,x1+4)-Math.max(0,x0-3),h:Math.min(cv.height,y1+4)-Math.max(0,y0-3)}}
// one deed frame -> {bg canvas, parts:{A:{img,ox,oy,box},V:{...}}, order}
function cut(D,t,e,st,K){const order=D.layers||['bg','V','A'];const mk=D.marks?D.marks(t,e.A,e.V,K,{carry:st.body}):null;const out={order,parts:{}};
 const raw=mkc(W,H);
 for(const ly of order){const q=raw.getContext('2d');q.setTransform(1,0,0,1,0,0);q.clearRect(0,0,W,H);q.save();try{D.draw(q,t,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}q.restore();
  if(ly==='bg'){const bg=mkc(W,H);bg.getContext('2d').drawImage(raw,0,0);out.bg=bg;continue}
  const who=ly==='A'?e.A:e.V,lv=st.levers[who],b=mk?mk[ly]:{x:ly==='A'?400:1300,y:600,w:200,h:250};
  const f=mk?leverScale(lv):1,cx=b.x+b.w/2,by=b.y+b.h;
  const lay=mkc(W,H),q2=lay.getContext('2d');q2.save();q2.filter=mk?leverFilter(lv):'none';q2.translate(cx,by);q2.scale(f,f);q2.translate(-cx,-by);q2.drawImage(raw,0,0);q2.restore();
  const box={x:cx-b.w*f/2,y:by-b.h*f,w:b.w*f,h:b.h*f};const ab=alphaBox(lay)||{x:box.x,y:box.y,w:1,h:1};
  const x0=Math.floor(Math.min(ab.x,box.x)),y0=Math.floor(Math.min(ab.y,box.y)),x1=Math.ceil(Math.max(ab.x+ab.w,box.x+box.w)),y1=Math.ceil(Math.max(ab.y+ab.h,box.y+box.h));
  const sp=mkc(Math.max(2,x1-x0),Math.max(2,y1-y0));sp.getContext('2d').drawImage(lay,-x0,-y0);
  out.parts[ly]={who,img:sp,ox:x0,oy:y0,box}}
 return out}
// a bystander drawn by the fog room's own hand (incitement doer layer at t=0), so it belongs to the house
function bystander(D,id,st,K){const other=IDS.find(s=>s!==id);const e={A:id,V:other};const c=cut(D,0,e,st,K);return c.parts.A}

// ---------- the cast plan, a pure function of the ledger ----------
function plan(X,K){const L=X.ledger,k=X.k,e1=L.ev[k-1],e2=L.ev[k],s1=L.states[k-1],s2=L.states[k];
 const role=(e,s)=>s===e.A?'A':s===e.V?'V':null;const cast=[];
 for(const s of IDS){const o1=role(e1,s),o2=role(e2,s);const kind=o1&&o2?'stay':o1?'leave':o2?'enter':'by';
  const m=o2==='A'?LEDGER.memories(L,s,k).filter(q=>q.other===e2.V):o2==='V'?LEDGER.memories(L,s,k).filter(q=>q.other===e2.A):[];
  const lv=s2.levers[s];
  cast.push({id:s,o1,o2,kind,alive:s2.alive[s],ghost:!s2.alive[s]&&!!o2,drowsy:s2.body[s].includes('drowsy'),newDrowsy:e1.V===s,
   mem:m[0]&&m[0].weight>.3?m[0]:null,lv,tempo:1+.35*cl(-1,1,lv.tempo),weight:cl(-1,1,lv.weight)})}
 return {e1,e2,s1,s2,cast}}

// ---------- per-sack deformer parameters at time u ----------
const STEP={R:2.1,B:1.5,I:1.2,O:2.6};
function travel(c,pl,u){ // m (0..1 along path), rise (drugged sack getting up), gaze/lift from memory, moving (walk envelope)
 let t0=.25,t1=DUR-.3;
 if(c.kind==='enter')t0=.3;
 if(c.kind==='leave')t1=DUR-.6;
 if(c.kind==='stay'&&c.newDrowsy)t0=.95;                      // the drugged sack first gets up, then walks
 if(c.tempo<1)t0+=.25*(1-c.tempo);else{const mid=(t0+t1)/2,f=Math.min(1.25,c.tempo);t0=mid-(mid-t0)/f;t1=mid+(t1-mid)/f}
 let uu=u,gaze=0,lift=0,hold=0,hd=0;
 if(c.mem&&c.o2==='A'){ // hesitation: it looks at the one it will meet, withdraws its gaze, almost speaks, stays silent
  const w=cl(.3,1,c.mem.weight);hd=.5*w+.3;const h0=t0+(t1-hd-t0)*.38;
  uu=u-cl(0,hd,u-h0)*.92;const q=cl(0,1,(u-h0)/hd);hold=Math.sin(Math.PI*q);
  gaze=q<.55?Math.sin(Math.PI*q/.55):-.6*Math.sin(Math.PI*(q-.55)/.45);
  lift=Math.exp(-Math.pow((q-.8)/.07,2))*w}
 if(c.mem&&c.o2==='V'){const q=cl(0,1,(u-1.3)/.6);lift=-Math.sin(Math.PI*q)*cl(.3,1,c.mem.weight)}   // flinch: ears down
 const t1e=t1-hd*.92,m=sm(t0,t1e,uu);
 const moving=Math.sin(Math.PI*cl(0,1,(uu-t0)/(t1e-t0)))*(1-.9*hold);
 const rise=c.kind==='stay'&&c.newDrowsy?sm(.3,.95,u):m;
 return {m,rise,gaze,lift,moving}}

// ---------- the transition ----------
let CACHE=null;
function setup(X,K){const key=X.film.join(',')+'|'+X.k;if(CACHE&&CACHE.key===key)return CACHE;
 const pl=plan(X,K),D1=X.DEEDS[pl.e1.deed],D2=X.DEEDS[pl.e2.deed];
 const out=cut(D1,5.99,pl.e1,pl.s1,K),inn=cut(D2,0,pl.e2,pl.s2,K);
 for(const c of pl.cast){c.p1=c.o1?out.parts[c.o1]:null;c.p2=c.o2?inn.parts[c.o2]:null;if(c.kind==='by')c.pb=bystander(D2,c.id,pl.s2,K)}
 // evidence left so far: drawn by each consequence module's own trace, as small cards on the house corner
 const ev=pl.s2.evidence.map(q=>{const cv=mkc(140,140),g2=cv.getContext('2d');const C=X.CONSEQS[q.deed],age=X.k-1-q.k;
  try{if(C&&C.trace)C.trace(g2,{x:10,y:10,w:120,h:120},age,K);else{g2.fillStyle='rgba(220,210,190,.7)';g2.fillRect(50,50,40,40)}}catch(err){}
  return {q,img:cv}});
 CACHE={key,pl,out,inn,ev};return CACHE}

// draw one part through its child deformer
// geo: {Phi (drum deg of anchor centre), base (face y of anchor bottom), w,h (anchor size now)}, prm: {turn,earX,lift,droop,sq,alpha}
function drawPart(g,part,geo,prm,p,vol,exact){if(!part||prm.alpha<=.003)return;const b=part.box,img=part.img;
 g.save();g.globalAlpha=prm.alpha;if(prm.filter)g.filter=prm.filter;
 if(exact){g.drawImage(img,part.ox,part.oy);g.restore();return}
 const bcx=b.x+b.w/2,bby=b.y+b.h,nx=img.width>260?10:7,ny=img.height>220?9:7;
 mesh(g,img,0,0,img.width,img.height,nx,ny,(sx,sy)=>{
  let lx=(part.ox+sx-bcx)/b.w,ly=(bby-(part.oy+sy))/b.h;
  // AngleX: the middle slides toward the turn, the outline holds (Live2D head-turn warp), width narrows a little
  const a=prm.turn,inside=Math.max(0,.25-lx*lx)/.25;
  lx=lx+a*.26*inside;lx*=1-.28*Math.abs(a)*cl(0,1,ly*1.2+.2);
  // ear physics + lift + droop on the top rows
  const top=cl(0,1,(ly-.62)/.38);lx+=prm.earX*top*top;
  ly=ly*prm.sq+(prm.lift*.16)*top*top-prm.droop*.12*top*top;
  const X=bcx+lx*geo.w,Y=geo.base-ly*geo.h;   // face px (centre-relative)
  const Phi=geo.Phi+(X-bcx)*90/W;return drum(Phi,Y,p,vol)});
 g.restore()}

function draw(g,u,X,K){const S=setup(X,K),pl=S.pl;
 const exA=u<=.0005,exB=u>=DUR-.012;const p=exA?0:exB?1:pAt(u),vol=volAt(p);
 g.fillStyle='#000';g.fillRect(0,0,W,H);
 // ---- the house: two keyform drawings on one lattice ----
 if(exA)g.drawImage(S.out.bg,0,0);else if(exB)g.drawImage(S.inn.bg,0,0);
 else{for(const face of[0,1]){const img=face?S.inn.bg:S.out.bg;
   const P=mesh(g,img,0,0,W,H,20,10,(sx,sy)=>drum(phiOf(sx,face),sy,p,vol));
   // the turned-away side of the drawing loses the lamp
   for(let i=0;i<20;i++){const c=(P[0][i][2]+P[0][i+1][2])/2;const dk=vol*(1-c)*.95+.35*(face?(1-p):p)*vol;if(dk<.01)continue;
    g.fillStyle=`rgba(4,4,6,${cl(0,.92,dk)})`;g.beginPath();g.moveTo(P[0][i][0],P[0][i][1]);g.lineTo(P[0][i+1][0],P[0][i+1][1]);g.lineTo(P[10][i+1][0],P[10][i+1][1]);g.lineTo(P[10][i][0],P[10][i][1]);g.closePath();g.fill()}
   // the deformer lattice shows while the house is between keyforms
   const la=.2*vol;if(la>.01){g.strokeStyle=`rgba(150,176,255,${la})`;g.lineWidth=1;
    for(let j=0;j<=10;j+=2){g.beginPath();for(let i=0;i<=20;i++){const q=P[j][i];if(q[2]<=0)continue;i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}
    for(let i=0;i<=20;i+=2){if(P[0][i][2]<=0)continue;g.beginPath();for(let j=0;j<=10;j++){const q=P[j][i];j?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}
    g.fillStyle=`rgba(190,205,255,${la*1.6})`;for(let j=0;j<=10;j+=2)for(let i=0;i<=20;i+=2){const q=P[j][i];if(q[2]>0)g.fillRect(q[0]-2,q[1]-2,4,4)}}}
  // the house corner (shared lattice column Phi=-45) and the evidence hung on it
  const ca=vol;if(ca>.02){const top=drum(-45,60,p,vol),bot=drum(-45,880,p,vol);
   if(top[2]>0){g.globalAlpha=ca;g.fillStyle='#120e0c';g.fillRect(top[0]-9,top[1],18,bot[1]-top[1]);g.fillStyle='rgba(80,64,50,.6)';g.fillRect(top[0]-9,top[1],3,bot[1]-top[1]);
    let nw=0,nf=0;S.ev.forEach((E,i)=>{const floor=FLOOR.includes(E.q.kind);const n=floor?nf++:nw++;const side=n%2?1:-1,hy=floor?850+(n%2)*26:300+Math.floor(n/2)*150+(n%2)*60,ph=-45+side*(floor?4+Math.floor(n/2)*3:3.2);const c=drum(ph,hy,p,vol);if(c[2]<=0)return;
     const sx=(drum(ph+.5,hy,p,vol)[0]-c[0])/(W*.5/90);g.save();g.translate(c[0],c[1]);g.scale(Math.max(.15,sx)*.9,.9);g.drawImage(E.img,-70,-70);g.restore();
     if(!floor){g.strokeStyle='rgba(30,24,20,.8)';g.lineWidth=2;g.beginPath();g.moveTo(top[0],c[1]-60);g.lineTo(c[0],c[1]-50);g.stroke()}});
    g.globalAlpha=1}}}
 // ---- the cast: child deformers glued to the house lattice ----
 const items=[];
 for(const c of pl.cast){const tv=travel(c,pl,u);const m=exA?0:exB?1:tv.m;let rank=1;
  if(c.kind==='by'){if(exA||exB||!c.pb)continue;
   const b=c.pb.box,side=IDS.indexOf(c.id)%2?1:-1;const geo={Phi:-45+side*7,base:860,w:b.w*.62,h:b.h*.62*(c.alive?1:.45)};
   const turn=c.alive?.5*Math.sin(u*1.7+side):0;
   items.push({rank:0,f:()=>drawPart(g,c.pb,geo,{turn,earX:0,lift:0,droop:c.drowsy?1:0,sq:1,alpha:vol*(c.alive?.85:.6),filter:c.alive?'brightness(.8)':'grayscale(1) brightness(.5)'},p,vol,false)});continue}
  const b1=c.p1&&c.p1.box,b2=c.p2&&c.p2.box;
  let Phi,base,w,h,turn=0,dir=0;
  if(c.kind==='stay'){const P1=phiOf(b1.x+b1.w/2,0),P2=phiOf(b2.x+b2.w/2,1),r=exA?0:exB?1:tv.rise;Phi=lerp(P1,P2,m);base=lerp(b1.y+b1.h,b2.y+b2.h,m);w=lerp(b1.w,b2.w,r);h=lerp(b1.h,b2.h,r);dir=Math.sign((P2+90)-P1)||1}
  if(c.kind==='leave'){const P1=phiOf(b1.x+b1.w/2,0);Phi=P1+34*(c.alive&&!c.newDrowsy?m:0);base=b1.y+b1.h;w=b1.w;h=b1.h;dir=1}
  if(c.kind==='enter'){const P2=phiOf(b2.x+b2.w/2,1);Phi=P2-30*(1-m);base=b2.y+b2.h;w=b2.w;h=b2.h;dir=1}
  const walking=(c.alive||c.ghost)&&!(c.kind==='leave'&&c.newDrowsy);   // a drugged sleeper left behind is carried off by the house, asleep
  turn=walking?dir*.85*tv.moving+tv.gaze*(c.o2==='A'?1:-1)*.9:0;
  // walk: per-sack step rate, heavier sacks squash more; drowsy sacks sway and droop
  const fs=STEP[c.id]*c.tempo*(c.drowsy?.7:1);const ph=Math.abs(Math.sin(Math.PI*fs*u));
  const sq=1-(.035+.04*Math.max(0,c.weight))*ph*tv.moving*(walking?1:0)-(c.drowsy?.04*Math.sin(Math.PI*cl(0,1,u/DUR)):0);
  base-=walking?(c.id==='B'?6:10)*(1-ph)*tv.moving*(c.drowsy?.4:1):0;
  // ear physics: a damped pendulum driven by this sack's screen acceleration (deterministic re-integration)
  let ang=0,av=0,prevX=null,prevV=0;const dt=1/120,kk=c.id==='I'?40:c.id==='B'?90:70,dd=c.id==='I'?2.2:4;
  const xsAt=t=>{const q=travel(c,pl,t).m,pp=pAt(t),vv=volAt(pp);let ph2;
   if(c.kind==='stay')ph2=lerp(phiOf(b1.x+b1.w/2,0),phiOf(b2.x+b2.w/2,1),q);else if(c.kind==='leave')ph2=phiOf(b1.x+b1.w/2,0)+34*(c.alive&&!c.newDrowsy?q:0);else ph2=phiOf(b2.x+b2.w/2,1)-30*(1-q);return drum(ph2,700,pp,vv)[0]};
  if(!exA&&!exB)for(let t=0;t<=u;t+=dt){const x=xsAt(t);if(prevX!==null){const v=(x-prevX)/dt;const acc=(v-prevV)/dt;prevV=v;av+=(-kk*ang-dd*av-acc*.0016)*dt;ang+=av*dt}prevX=x}
  const env=sm(0,.3,u)*(1-sm(DUR-.4,DUR-.05,u));const earX=cl(-.35,.35,ang)*env;
  const droop=c.drowsy?(c.newDrowsy?.9:.5)*env:0;
  // part switching: a sack in both shots trades its drugging-room drawing for its fog-room drawing at its view limit
  const sw=c.kind==='stay'?(exA?0:exB?1:c.newDrowsy?sm(.25,.75,tv.rise):sm(.4,.6,m)):c.kind==='enter'?1:0;
  const vis=c.kind==='leave'?1:c.kind==='enter'?1:1;
  const gA=c.ghost?.55:1;
  const geo={Phi,base,w,h};
  const ex=(exA&&c.kind!=='enter')||(exB&&c.kind!=='leave');
  rank=(p<.5?(c.o1==='A'?2:1):(c.o2==='A'?2:1));
  const prm=(alpha)=>({turn:ex?0:turn,earX:ex?0:earX,lift:ex?0:tv.lift,droop:ex?0:droop,sq:ex?1:sq,alpha:alpha*gA*vis,filter:c.ghost?'grayscale(1) brightness(1.2)':null});
  items.push({rank,y:base,f:()=>{
   if(c.kind==='stay'){
    // each drawing keeps its own anchor normalisation; both ride the same current anchor
    if(sw<1)drawPart(g,c.p1,geo,prm(1-sw*sw),p,vol,exA);
    if(sw>0)drawPart(g,c.p2,geo,prm(Math.sqrt(sw)),p,vol,exB)}
   else if(c.kind==='leave'){if(!exB)drawPart(g,c.p1,geo,prm(1),p,vol,exA)}
   else if(c.kind==='enter'){if(!exA)drawPart(g,c.p2,geo,prm(1),p,vol,exB)}}})}
 items.sort((a,b)=>a.rank-b.rank||(a.y||0)-(b.y||0)).forEach(it=>it.f());
 g.globalAlpha=1;g.filter='none'}

// ---------- sound: grains for the parameter sweep, the cast's own voices for steps and hesitation ----------
function sound(ac,out0,t0,X,K){const S=K.SND,L=X.ledger,k=X.k;const pl=plan(X,K);const out=ac.createGain();out.gain.value=1.5;out.connect(out0);
 const at=u=>t0+u;
 // the lattice: one tick each time the HouseAngle parameter crosses a lattice column (20 per face), pitch = parameter value
 let last=0;for(let i=1;i<=20;i++){const target=i/20;let lo=P0,hi=P1;for(let it=0;it<20;it++){const md=(lo+hi)/2;if(pAt(md)<target)lo=md;else hi=md}
  const uu=(lo+hi)/2;if(uu-last<.02)continue;last=uu;const pan=-.6+1.2*target;
  S.grain(ac,out,at(uu),{f:700+target*900,d:.03,a:.05+.05*volAt(target),pan,att:.05});S.grain(ac,out,at(uu)+.004,{bp:2600,q:3,d:.015,a:.03,pan})}
 // the house turning: a low wooden hush under the sweep
 S.cloud(ac,out,at(P0),P1-P0,22,{bp:260,q:.9,a:.04,d:[.08,.22],spread:.9},u=>Math.sin(Math.PI*u));
 // the fog room's hush arriving at the end
 S.cloud(ac,out,at(DUR-1.1),1.1,30,{bp:320,q:.8,a:.018,d:[.2,.45],spread:.9},u=>u);
 for(const c of pl.cast){if(c.kind==='by')continue;if(!c.alive&&!c.ghost)continue;if(c.kind==='leave'&&c.newDrowsy){S.say(ac,out,c.id,at(.8),'breathe',1.2,.6);continue}
  const pan=c.o2==='A'||(!c.o2&&c.o1==='A')?-.4:.4;const fs=STEP[c.id]*c.tempo*(c.drowsy?.7:1);
  let lastS=-1;for(let n=1;n<12;n++){const uu=n/fs;if(uu>DUR-.25)break;const tv=travel(c,pl,uu);if(tv.moving<.25)continue;if(uu-lastS<.18)continue;lastS=uu;
   S.say(ac,out,c.id,at(uu),'step',(c.drowsy?.5:.8)*(1+.3*Math.max(0,c.weight)),pan*(c.kind==='leave'?1.6:1))}
  if(c.kind==='stay'){let lo=0,hi=DUR;for(let it=0;it<18;it++){const md=(lo+hi)/2;if(travel(c,pl,md).m<.5)lo=md;else hi=md}S.say(ac,out,c.id,at(lo),'tick',.7,pan)}
  if(c.drowsy&&c.newDrowsy){S.say(ac,out,c.id,at(.5),'breathe',.9,pan);S.say(ac,out,c.id,at(.6),'sink',.5,pan)}
  if(c.mem&&c.o2==='A'){const w=cl(.3,1,c.mem.weight);S.say(ac,out,c.id,at(1.1),'breathe',.6+.4*w,pan);S.say(ac,out,c.id,at(1.05+(.55*w+.25)*.78),'react',.25*w,pan)}
  if(c.mem&&c.o2==='V')S.say(ac,out,c.id,at(1.45),'tick',.4,pan);
  if(c.o2){let lo=0,hi=DUR;for(let it=0;it<18;it++){const md=(lo+hi)/2;if(travel(c,pl,md).m<.97)lo=md;else hi=md}S.say(ac,out,c.id,at(Math.min(DUR-.15,hi)),'step',.5,pan)}}}   // each arrives on its mark in the fog room

TRANSITION({k:2,scion:24,lineage:'Live2D Cubism — Portrait Volume Illusion',
 op:'The house is one rigged drawing with a HouseAngle parameter: the drugging room is its keyform at 0 and the fog room its keyform at 90, the lattice between them bends from flat to curved and back, and each sack is a child deformer glued to it that turns, walks, swings its ears by physics, and swaps its drawing at its view limit.',
 made:'Both rooms are the deeds\' own background layers mapped as textures on one warp lattice whose shared column is the house corner, where the evidence cards hang; the sacks are the deeds\' own clean layers (carried damage and levers baked in) cut out as parts, each on its own small warp grid. A pale deformer lattice shows only while the house is between keyforms.',
 moved:'One parameter sweep drives the house; each sack\'s AngleX, walk squash, ear pendulum (re-integrated from its screen acceleration), droop and ear-lift are functions of time and the ledger (tempo and weight levers, drowsy, memory). A doer with a strong memory of its victim pauses on the way, looks toward it, withdraws its gaze, lifts its ears as if to speak, and goes on silent.',
 dur:DUR,draw,sound});
})();
