// TRANSITION 01 · Blackmail (Reiniger silhouette theatre) -> Drugging (spring-dynamics room)
// SCION 43 · Collage Graph Rewriting. Both shots are read as TYPED ENTITY GRAPHS, and the outgoing graph is
// rewritten into the incoming one by a short list of rules, each a cut-and-paste of real picture fragments:
//   LAMP  -> LAMP   REPLACE  (shared visual anchor: both lamps hang from (960,0); the cut-card lamp swings out on its
//                             cord and comes back as the spring room's lamp)
//   WALL  -> WALL   SPLIT    (the amber glass is cut into wallpaper-stripe-width cards that turn over, centre out,
//                             in the order the lamp's swing reaches them; the black arch, stairs and door go with them)
//   FLOOR -> FLOOR  REPLACE  (the board floor is laid in from below over the black proscenium ground)
//   TABLE+CUP       ENTER    (no counterpart: the table piece is placed last, over the photograph)
//   PHOTO           SPLIT    (from the blackmailer's hand; falls to the floor; the table is laid over it: evidence buried)
//   SACK  -> SACK   per role: STAY = the black card is slit along its attribute line (belt/shawl/wig/ears) and its two
//                   lips fold back to reveal the cloth sack; LEAVE = EXIT, the old cut card walks out (door or edge) still
//                   in the old language; ENTER = the cloth sack comes in from the side it will stand on.
// Preconditions (scene-event contract): a sack is rewritten only while it stands on rewritten floor; the door strip turns
// only after a leaver has gone through; the table is placed only after the photo has landed. Numerical invariant
// (checked by the seam harness): u=0 equals the outgoing end frame, u=dur equals the incoming first frame.
(function(){
const DUR=3.0,FLOORY=800,STRIPW=64,NSTRIP=30,LAMP={x:880,y:0,w:160,h:268},TAB={x:796,y:584,w:328,h:230};
const DOOR={x:1592,y:380,w:176,h:482},OUTFLOOR=862;
const SLIT={R:.2,B:.6,I:.32,O:.24};          // attribute line, fraction from the top of the body: shawl, belt, ears, wig
const IDS=['R','B','I','O'];
const cl=(a,b,x)=>Math.max(a,Math.min(b,x)),sm=(a,b,x)=>{const u=cl(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
const eio=u=>u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;
const H=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};
let CACHE=null;
const mkc=()=>{const c=document.createElement('canvas');c.width=1920;c.height=1080;return c};
function levBox(b,lv){const f=1+.14*cl(-1,1,lv.loom)-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f,f,cx,by}}
function levFilter(lv){const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
 if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);return fl.join(' ')||'none'}
// ---------- the plan: roles, boxes and timing (shared by picture and sound; no canvas) ----------
function plan(L,K){const D0=DEEDS[L.ev[0].deed],D1=DEEDS[L.ev[1].deed],e0=L.ev[0],e1=L.ev[1],s0=L.states[0],s1=L.states[1];
 const m0=D0.marks(5.99,e0.A,e0.V,K),m1=D1.marks(0,e1.A,e1.V,K);const P={e0,e1,sacks:[]};
 for(const id of IDS){const r0=id===e0.A?'A':id===e0.V?'V':null,r1=id===e1.A?'A':id===e1.V?'V':null;if(!r0&&!r1)continue;
  const S={id,r0,r1,kind:r0&&r1?'stay':r0?'leave':'enter'};
  if(r0)S.b0=levBox(m0[r0],s0.levers[id]);if(r1)S.b1=levBox(m1[r1],s1.levers[id]);
  const lv=(r1?s1:s0).levers[id];S.hops=Math.round(3+2*cl(0,1,lv.tempo+.3));S.hh=cl(10,60,36-30*lv.weight);
  // memory: does this sack carry the one it is about to meet?
  S.hes=0;if(r1){const other=r1==='A'?e1.V:e1.A;const ms=LEDGER.memories(L,id,1).filter(m=>m.other===other);if(ms.length&&ms[0].weight>.3){S.hes=cl(0,1,ms[0].weight);S.mem=ms[0];S.other=other}}
  if(S.kind==='leave'){S.u0=.15;S.u1=1.25;const cx=S.b0.x+S.b0.w/2;S.exit=cx>960?(S.b0.w<300?'door':'right'):'left'}
  if(S.kind==='stay'){S.u0=.25;S.u1=2.4}
  if(S.kind==='enter'){S.u0=1.2;S.u1=2.7;const cx=S.b1.x+S.b1.w/2;S.from=cx<960?-1:1}
  P.sacks.push(S)}
 const st=P.sacks.filter(S=>S.kind==='stay');if(st.length===2){const d=S=>Math.sign((S.b1.x+S.b1.w/2)-(S.b0.x+S.b0.w/2));if(d(st[0])!==d(st[1]))st.forEach(S=>S.cross=true)}
 P.photoT=[.3,1.55];P.floorT=[.95,1.55];P.tableT=[1.75,2.35];P.lampSwap=.42;P.slitT=[1.45,2.1];
 P.strip=i=>{const xc=i*STRIPW+STRIPW/2;return .45+1.2*Math.abs(xc-960)/960};
 return P}
// progress along a sack's path, with a stall (hesitation) in the middle when it remembers the other
function prog(S,u){let t=cl(0,1,(u-S.u0)/(S.u1-S.u0));const q=.34*S.hes,a=(1-q)/2;let w,st=0;
 if(t<a)w=.5*t/a;else if(t<a+q){w=.5;st=Math.sin(Math.PI*(t-a)/q)}else w=.5+.5*(t-a-q)/(1-a-q);return{p:eio(w),stall:st,t}}
// ---------- cached pictures: both shots split into layers, levers applied exactly as the film does ----------
function build(X,K){const L=X.ledger,P=plan(L,K),key=X.film.join(',');const C={key,P};
 const pic=(k,t,st)=>{const e=L.ev[k],D=DEEDS[e.deed],out={};const raw={};
  for(const ly of['bg','A','V']){const c=mkc(),q=c.getContext('2d');try{D.draw(q,t,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}raw[ly]=c}
  out.bg=raw.bg;out.order=D.layers||['bg','V','A'];out.raw=raw;out.marks=D.marks(t,e.A,e.V,K);return out};
 C.O=pic(0,5.99,L.states[0]);C.I=pic(1,0,L.states[1]);
 // the room without its table (the table is a separate ENTER node): mask wood, cup and their dark edges, fill each row across the gap
 {const c=mkc(),q=c.getContext('2d');q.drawImage(C.I.bg,0,0);const X0=TAB.x-10,W=TAB.w+20,Hh=TAB.h-6,id=q.getImageData(X0,TAB.y,W,Hh),d=id.data;
  const M=new Uint8Array(W*Hh);for(let y=0;y<Hh;y++)for(let x=0;x<W;x++){const i=(y*W+x)*4,r=d[i],gg=d[i+1],bb=d[i+2],yy=TAB.y+y;
   if((r-bb>26&&r>45)||(r+gg+bb>420)||(yy<FLOORY-4&&r+gg+bb<75))M[y*W+x]=1}
  // grow the mask by 2px (anti-aliased edges)
  for(let it=0;it<2;it++){const M2=M.slice();for(let y=1;y<Hh-1;y++)for(let x=1;x<W-1;x++)if(!M[y*W+x]&&(M[y*W+x-1]||M[y*W+x+1]||M[(y-1)*W+x]||M[(y+1)*W+x]))M2[y*W+x]=1;M.set(M2)}
  for(let y=0;y<Hh;y++){let x=0;while(x<W){if(!M[y*W+x]){x++;continue}let e=x;while(e<W&&M[y*W+e])e++;const l=Math.max(0,x-1),r=Math.min(W-1,e);
    for(let k=x;k<e;k++){const f=(k-l)/Math.max(1,r-l),i=(y*W+k)*4;for(let ch=0;ch<3;ch++)d[i+ch]=d[(y*W+l)*4+ch]*(1-f)+d[(y*W+r)*4+ch]*f}x=e}}
  q.putImageData(id,X0,TAB.y);C.clean=c}
 // PHOTO node: split it off the blackmailer's layer (cream card pixels), so it can travel alone
 const e0=L.ev[0],rA=C.O.raw.A,mA=C.O.marks.A;{const x0=Math.max(0,Math.floor(mA.x-mA.w)),y0=Math.max(0,Math.floor(mA.y-mA.h)),x1=Math.min(1920,Math.ceil(mA.x+mA.w*2)),y1=Math.min(1080,Math.ceil(mA.y+mA.h*1.2));
  const d=rA.getContext('2d').getImageData(x0,y0,x1-x0,y1-y0).data;let bx0=1e9,by0=1e9,bx1=-1,by1=-1,n=0;
  for(let y=0;y<y1-y0;y+=2)for(let x=0;x<x1-x0;x+=2){const i=(y*(x1-x0)+x)*4,r=d[i],g=d[i+1],b=d[i+2],a=d[i+3];if(a>240&&r>205&&g>188&&b>145&&r-b<80){n++;bx0=Math.min(bx0,x);by0=Math.min(by0,y);bx1=Math.max(bx1,x);by1=Math.max(by1,y)}}
  if(n>40){const pb={x:x0+bx0-9,y:y0+by0-9,w:bx1-bx0+18,h:by1-by0+18};const pc=document.createElement('canvas');pc.width=pb.w;pc.height=pb.h;pc.getContext('2d').drawImage(rA,pb.x,pb.y,pb.w,pb.h,0,0,pb.w,pb.h);
   rA.getContext('2d').clearRect(pb.x,pb.y,pb.w,pb.h);C.photo={c:pc,b:pb}}}
 // lever-applied sack images
 const levImg=(pc,role,id,st)=>{const lv=st.levers[id],b=pc.marks[role],f=1+.14*cl(-1,1,lv.loom)-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;const c=mkc(),q=c.getContext('2d');
  q.filter=levFilter(lv);q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(pc.raw[role],0,0);return c};
 for(const S of P.sacks){if(S.r0)S.imgO=levImg(C.O,S.r0,S.id,L.states[0]);if(S.r1)S.imgI=levImg(C.I,S.r1,S.id,L.states[1])}
 if(C.photo){const lv=L.states[0].levers[e0.A];const f=1+.14*cl(-1,1,lv.loom)-.22*lv.shrink,cx=mA.x+mA.w/2,by=mA.y+mA.h;C.photo.f=f;C.photo.x=cx+(C.photo.b.x-cx)*f;C.photo.y=by+(C.photo.b.y-by)*f;C.photo.lv=lv}
 // the remembered moment, as a torn scrap (only used when a traveller hesitates)
 try{const st=X.still(L.ev[0]);const D0=DEEDS[L.ev[0].deed],mm=D0.marks(D0.contact+.3,e0.A,e0.V,K);const x0=Math.min(mm.A.x,mm.V.x)-40,y0=Math.min(mm.A.y,mm.V.y)-60,x1=Math.max(mm.A.x+mm.A.w,mm.V.x+mm.V.w)+40,y1=Math.max(mm.A.y+mm.A.h,mm.V.y+mm.V.h)+20;
  const sc=document.createElement('canvas');sc.width=Math.max(10,x1-x0);sc.height=Math.max(10,y1-y0);sc.getContext('2d').drawImage(st,x0,y0,sc.width,sc.height,0,0,sc.width,sc.height);C.scrap=sc}catch(err){}
 return C}
// ---------- collage helpers ----------
function ragged(g,x,y,w,h,seed,j){g.beginPath();const n=Math.max(4,Math.round((w+h)/40));const pt=(i,tot,ax,ay,bx,by,s)=>{const u=i/tot,nx=ay-by,ny=bx-ax,ln=Math.hypot(nx,ny)||1;const o=(H(seed+s*31+i*1.7)-.5)*j;return[ax+(bx-ax)*u+nx/ln*o,ay+(by-ay)*u+ny/ln*o]};
 const E=[[x,y,x+w,y],[x+w,y,x+w,y+h],[x+w,y+h,x,y+h],[x,y+h,x,y]];let first=true;
 E.forEach((e,s)=>{const m=Math.max(2,Math.round(n*(s%2?h:w)/(w+h)));for(let i=0;i<m;i++){const p=pt(i,m,...e,s);if(first){g.moveTo(...p);first=false}else g.lineTo(...p)}});g.closePath()}
// a picture fragment of src (region r) drawn as a lifted paper piece: offset, scale, rotation about its centre, lift 0..1
function piece(g,src,r,dx,dy,sc,rot,lift,seed){g.save();const cx=r.x+r.w/2,cy=r.y+r.h/2;g.translate(cx+dx,cy+dy);g.rotate(rot);g.scale(sc,sc);g.translate(-cx,-cy);
 if(lift>.01){g.save();g.shadowColor=`rgba(0,0,0,${.55*lift})`;g.shadowBlur=26*lift;g.shadowOffsetX=10*lift;g.shadowOffsetY=16*lift;ragged(g,r.x,r.y,r.w,r.h,seed,6*lift);g.fillStyle='#e9dfcb';g.fill();g.restore();
  ragged(g,r.x,r.y,r.w,r.h,seed,6*lift);g.clip();g.drawImage(src,r.x,r.y,r.w,r.h,r.x,r.y,r.w,r.h);g.lineWidth=3;g.strokeStyle=`rgba(240,230,210,${.8*lift})`;g.stroke()}
 else g.drawImage(src,r.x,r.y,r.w,r.h,r.x,r.y,r.w,r.h);g.restore()}
// a sack image (full-frame layer canvas) placed with its anchor (ax,ay) at (x,y), scaled and rotated
function sackAt(g,img,ax,ay,x,y,sc,rot,clip){g.save();if(clip)clip(g);g.translate(x,y);g.rotate(rot||0);g.scale(sc,sc);g.translate(-ax,-ay);g.drawImage(img,0,0);g.restore()}
// ---------- the frame ----------
function draw(g,u,X,K){const key=X.film.join(',');if(!CACHE||CACHE.key!==key)CACHE=build(X,K);const C=CACHE,P=C.P;
 g.save();g.setTransform(1,0,0,1,0,0);
 // 0 · the outgoing world, whole (bg only; sacks are carried separately)
 g.drawImage(C.O.bg,0,0);
 // 1 · WALL split: stripe cards turn over, centre out
 for(let i=0;i<NSTRIP;i++){const x=i*STRIPW,t0=P.strip(i),ph=cl(0,1,(u-t0)/.34);if(ph<=0)continue;const r={x,y:0,w:STRIPW,h:FLOORY};
  if(ph>=1){g.drawImage(C.clean,x,0,STRIPW,FLOORY,x,0,STRIPW,FLOORY);continue}
  g.fillStyle='#0b0a09';g.fillRect(x,0,STRIPW,FLOORY);const sx=Math.abs(Math.cos(Math.PI*ph));const src=ph<.5?C.O.bg:C.clean;
  g.save();g.translate(x+STRIPW/2,0);g.scale(Math.max(.02,sx),1);g.translate(-x-STRIPW/2,0);g.drawImage(src,x,0,STRIPW,FLOORY,x,0,STRIPW,FLOORY);
  g.fillStyle=`rgba(0,0,0,${.45*(1-sx)})`;g.fillRect(x,0,STRIPW,FLOORY);g.restore()}
 // 2 · FLOOR replace: boards laid in from below
 {const a=sm(P.floorT[0],P.floorT[1],u);if(a>0){const r={x:0,y:FLOORY,w:1920,h:280};piece(g,C.clean,r,0,(1-a)*300,1,0,(1-a)>.001?Math.min(1,(1-a)*3):0,7)}}
 // 3 · TABLE+CUP enter: until placed, its slot still shows the old picture (where the photograph lands)
 const tA=sm(P.tableT[0],P.tableT[1],u);
 const drawPhoto=()=>{if(!C.photo)return;const ph=C.photo,pu=sm(P.photoT[0],P.photoT[1],u);const w=ph.b.w*ph.f,h=ph.b.h*ph.f;
  const tx=TAB.x+TAB.w*.5-w*.5,ty=FLOORY-h*1.12,fl=Math.sin(pu*Math.PI*3)*(1-pu);
  const x=ph.x+(tx-ph.x)*pu+fl*60,y=ph.y+(ty-ph.y)*(pu*pu)-Math.sin(pu*Math.PI)*60,rot=pu*.1+fl*.5;
  g.save();g.translate(x+w/2,y+h/2);g.rotate(rot);if(pu>0&&pu<1){g.shadowColor='rgba(0,0,0,.4)';g.shadowBlur=12;g.shadowOffsetY=8}
  g.drawImage(ph.c,-w/2,-h/2,w,h);g.restore()};
 if(tA<1&&u>=P.photoT[0]+.6)drawPhoto();
 if(tA>0)piece(g,C.I.bg,TAB,0,-(1-tA)*240,1+.08*(1-tA),(1-tA)*-.05,(1-tA)>.001?Math.min(1,(1-tA)*2.5):0,3);
 // 4 · LAMP replace: the cut-card lamp swings out on its cord; at the top of the swing it is the spring room's lamp
 {const env=1-sm(.1,1.5,u),th=.32*Math.sin(Math.PI*cl(0,1,u/.84)*1)*env+(u>.84?.12*Math.sin((u-.84)*7.4)*env:0);
  const moving=Math.abs(th)>.002||(u>.05&&u<1.5);if(u>0&&u<1.6){g.save();g.fillStyle='#0b0a09';g.fillRect(LAMP.x,LAMP.y,LAMP.w,LAMP.h);g.restore();
   const src=u<P.lampSwap?C.O.bg:C.I.bg;g.save();g.translate(960,0);g.rotate(th);g.translate(-960,0);piece(g,src,LAMP,0,0,1,0,moving?Math.min(1,u*5)*sm(1.6,1.0,u)+.0:0,11);g.restore()}
  else if(u>=1.6)g.drawImage(C.I.bg,LAMP.x,LAMP.y,LAMP.w,LAMP.h,LAMP.x,LAMP.y,LAMP.w,LAMP.h)}
 // photograph in flight is drawn above everything but the sacks
 // 5 · SACKS
 const rank=S=>S.kind==='leave'?0:S.kind==='enter'?3:(S.cross&&S.b1.x<S.b0.x?1:2);const order=P.sacks.slice().sort((a,b)=>rank(a)-rank(b));
 for(const S of order)drawSack(g,S,u,C,P,K);
 if(C.photo&&u<P.photoT[0]+.6)drawPhoto();
 g.restore()}
function drawSack(g,S,u,C,P,K){
 if(S.kind==='leave'){const b=S.b0,ax=b.x+b.w/2,ay=b.y+b.h;const t=cl(0,1,(u-S.u0)/(S.u1-S.u0));if(t>=1)return;
  let tx,clip=null,sc=1;if(S.exit==='door'){tx=DOOR.x+DOOR.w/2}else tx=S.exit==='right'?1920+b.w*.8:-b.w*.8;
  const walk=S.exit==='door'?cl(0,1,t/.72):t,p=eio(walk),x=ax+(tx-ax)*p,hop=Math.abs(Math.sin(Math.PI*S.hops*p))*S.hh*(1-sm(.9,1,walk));
  let y=ay-hop;if(S.exit==='door'&&t>.72){// through the doorway: smaller (into depth), darker, gone
   const d=(t-.72)/.28;sc=1-.35*d;y=ay-d*30;g.save();g.globalAlpha=1-d*d;g.filter=`brightness(${1-.6*d})`;sackAt(g,S.imgO,ax,ay,x,y,sc,0,null);g.restore();return}
  sackAt(g,S.imgO,ax,ay,x,y,sc,(Math.sin(Math.PI*S.hops*p*2))*.03*(1-sm(.9,1,walk)),clip);return}
 if(S.kind==='enter'){const b=S.b1,ax=b.x+b.w/2,ay=b.y+b.h;const pr=prog(S,u);if(pr.t<=0)return;const sx=S.from<0?-b.w*.9:1920+b.w*.9;
  const x=sx+(ax-sx)*pr.p,hop=Math.abs(Math.sin(Math.PI*S.hops*pr.p))*S.hh,rot=S.from*.07*pr.stall;
  if(pr.stall>0)scrap(g,S,x,ay-b.h,pr.stall,C);sackAt(g,S.imgI,ax,ay,x,ay-hop,1,rot);return}
 // STAY: carried from its old box to its new one; slit along its attribute line once it is on the new floor
 const b0=S.b0,b1=S.b1,a0x=b0.x+b0.w/2,a0y=b0.y+b0.h,a1x=b1.x+b1.w/2,a1y=b1.y+b1.h;const pr=prog(S,u),p=pr.p;
 const up=S.cross&&a1x<a0x?Math.sin(Math.PI*p):0,s01=b1.h/b0.h,sg=(1+(s01-1)*p)*(1-.12*up),x=a0x+(a1x-a0x)*p,yb=a0y+(a1y-a0y)*p-40*up,hop=Math.abs(Math.sin(Math.PI*S.hops*p))*S.hh,y=yb-hop;
 const dir=Math.sign(a1x-a0x)||1,rot=-dir*.08*pr.stall+Math.sin(Math.PI*S.hops*p*2)*.02;
 if(pr.stall>0)scrap(g,S,x,y-b0.h*sg,pr.stall,C);
 // precondition: the cut opens only after the new floor is laid
 const o=sm(P.slitT[0],P.slitT[1],u);
 if(o<=0){sackAt(g,S.imgO,a0x,a0y,x,y,sg,rot);return}
 if(o>=1){sackAt(g,S.imgI,a1x,a1y,x,y,sg/s01,rot);return}
 const hD=b0.h*sg,top=y-hD*1.9,bot=y+hD*.35,yS=y-hD*(1-SLIT[S.id]),bandT=yS-o*(yS-top),bandB=yS+o*(bot-yS);
 // cloth inside the opening
 sackAt(g,S.imgI,a1x,a1y,x,y,sg/s01,rot,q=>{q.beginPath();q.rect(0,bandT,1920,bandB-bandT);q.clip()});
 // the two black lips fold back toward the outer edges
 g.save();g.beginPath();g.rect(0,top-400,1920,bandT-top+400);g.clip();g.translate(0,top);g.scale(1,1-o);g.translate(0,-top);
 g.beginPath();g.rect(0,0,1920,yS);g.clip();sackAt(g,S.imgO,a0x,a0y,x,y,sg,rot);g.restore();
 g.save();g.beginPath();g.rect(0,bandB,1920,1080-bandB);g.clip();g.translate(0,bot);g.scale(1,1-o);g.translate(0,-bot);
 g.beginPath();g.rect(0,yS,1920,1080);g.clip();sackAt(g,S.imgO,a0x,a0y,x,y,sg,rot);g.restore();
 // the cut edges
 const wD=b0.w*sg*.5+20;g.save();g.strokeStyle=`rgba(244,234,214,${.9*(1-o)})`;g.lineWidth=3;
 for(const yy of[bandT,bandB]){g.beginPath();for(let i=0;i<=12;i++){const xx=x-wD+2*wD*i/12,j=(H(i*3.1+yy)-.5)*6;i?g.lineTo(xx,yy+j):g.moveTo(xx,yy+j)}g.stroke()}g.restore()}
// a hesitating sack: a torn scrap of the remembered shot surfaces behind it while it stalls
function scrap(g,S,x,y,a,C){if(!C.scrap)return;const sc=C.scrap,w=300,h=w*sc.height/sc.width;g.save();g.globalAlpha=.85*a;g.translate(x,y-h*.5-30);g.rotate((H(S.id.charCodeAt(0))-.5)*.2);
 g.shadowColor='rgba(0,0,0,.5)';g.shadowBlur=18;g.shadowOffsetY=10;ragged(g,-w/2,-h/2,w,h,S.id.charCodeAt(0),10);g.fillStyle='#e9dfcb';g.fill();g.shadowColor='transparent';
 ragged(g,-w/2+5,-h/2+5,w-10,h-10,S.id.charCodeAt(0)+1,8);g.clip();g.filter=S.mem&&S.mem.role==='victim'?'grayscale(.6) contrast(1.2)':'sepia(.5)';g.drawImage(sc,-w/2,-h/2,w,h);g.restore()}
// ---------- sound: snips, paper, cards turning, the lamp, the cast's own voices ----------
function sound(ac,out0,t0,X,K){const out=ac.createGain();out.gain.value=1.7;out.connect(out0);const L=X.ledger,P=plan(L,K),S_=K.SND,pan=x=>cl(-1,1,x/960-1);
 // lamp: a creak at the swing, a tick when it is swapped
 S_.cloud(ac,out,t0+.05,.8,16,{f:180,glide:-.2,a:.02,d:[.05,.12],type:'triangle',noise:.4,spread:.1},u=>Math.sin(Math.PI*u));
 S_.grain(ac,out,t0+P.lampSwap,{f:1800,d:.03,a:.12,att:.05});
 // wall cards turning: one dry tick per stripe, panned by its x
 for(let i=0;i<NSTRIP;i+=2)S_.grain(ac,out,t0+P.strip(i)+.17,{bp:3200+H(i)*1500,q:3,d:.03,a:.11,pan:pan(i*STRIPW+32),att:.1});
 // floor laid, table placed: paper slap + low thump
 S_.grain(ac,out,t0+P.floorT[1]-.02,{bp:900,q:.8,d:.12,a:.45,att:.08});S_.thump(ac,out,t0+P.floorT[1],.6,70);
 S_.grain(ac,out,t0+P.tableT[1]-.02,{bp:1400,q:1,d:.09,a:.2,pan:0,att:.08});S_.thump(ac,out,t0+P.tableT[1],.5,90);
 // the photograph flutters down and lands
 S_.cloud(ac,out,t0+P.photoT[0],P.photoT[1]-P.photoT[0],14,{bp:4200,a:.025,d:[.02,.05],spread:.3},u=>Math.sin(Math.PI*u));
 S_.grain(ac,out,t0+P.photoT[1],{bp:2600,d:.04,a:.1,att:.05});
 for(const S of P.sacks){const steps=[];let last=null;for(let i=0;i<=180;i++){const u=S.u0+(S.u1-S.u0)*i/180;let p;if(S.kind==='leave')p=eio(cl(0,1,S.exit==='door'?(u-S.u0)/((S.u1-S.u0)*.72):(u-S.u0)/(S.u1-S.u0)));else p=prog(S,u).p;
   const ph=Math.floor(S.hops*p+1e-6);if(last!==null&&ph>last)steps.push([u,p]);last=ph}
  const bx=S.kind==='enter'?S.b1:S.b0,x0=bx.x+bx.w/2;
  for(const[u,p]of steps){const x=S.kind==='stay'?x0+(S.b1.x+S.b1.w/2-x0)*p:x0;S_.say(ac,out,S.id,t0+u,'step',.9,pan(x))}
  if(S.kind!=='leave')S_.say(ac,out,S.id,t0+S.u1,'land',.6,pan(S.b1.x+S.b1.w/2));
  if(S.kind==='leave'&&S.exit==='door'){S_.grain(ac,out,t0+S.u1,{bp:500,d:.14,a:.18,pan:.75,att:.1});S_.thump(ac,out,t0+S.u1,.25,80,.75)}
  if(S.kind==='stay'){// the slit: two scissor snips, then the cloth
   const us=[];for(let i=0;i<=120;i++){const u=S.u0+(S.u1-S.u0)*i/120;if(prog(S,u).p>=.42&&u>=P.floorT[1]-.2){us.push(u);break}}const uc=us[0]||1.6;
   for(let j=0;j<2;j++)S_.grain(ac,out,t0+uc+j*.07,{bp:6500,q:4,d:.03,a:.14,pan:pan(S.b1.x),att:.05});S_.cloud(ac,out,t0+uc+.12,.35,20,{bp:1200,a:.03,d:[.02,.06]},u=>1-u)}
  if(S.hes>0){const a=(1-.34*S.hes)/2,um=S.u0+(S.u1-S.u0)*(a+.17*S.hes);S_.say(ac,out,S.id,t0+um-.1,'react',.5+.5*S.hes,pan((bx.x+bx.w/2)));S_.say(ac,out,S.id,t0+um+.15,'breathe',.6)}}}
TRANSITION({k:1,scion:43,lineage:'Collage Graph Rewriting — Identity Change Swarm',dur:DUR,
 op:'Both shots are typed entity graphs; the silhouette graph is rewritten into the spring room by cut-and-paste rules: the lamp is replaced on its shared cord, the wall is split into stripe cards that turn over, the floor and table are laid in, the photograph splits from the blackmailer and is buried under the table, and each sack is slit along its attribute line to show its cloth (staying), walks out as an old card (leaving), or comes in as cloth (entering).',
 made:'Cut fragments of the two real frames: the amber shadow-theatre backdrop and black card sacks from Blackmail, the striped room, boards, table and cloth sacks from Drugging, each fragment a paper piece with a torn edge and a lifted shadow while it moves. The photograph is lifted off the blackmailer as its own piece.',
 moved:'A fixed rule schedule: lamp swap at the top of its swing, stripe cards turning centre-out, the floor and table placed by hand, the photo falling to where the table will go. Each sack follows its role path in hops (more for quick sacks, lower for heavy ones), stalls and leans away under a scrap of the remembered shot if it remembers the one it meets, and is slit open only once it stands on the new floor.',
 draw,sound});
})();
