// 11 · SNOOPING — consequence beat · SCION 30 · SAM 2 — Prompted Mask Proposal Swarm
// Native primitives: points (positive / negative), box prompts, masks (vertex contours that refine from coarse to fine),
// segment proposals, object IDs (one colour per sack), a confidence proxy (ring), correction strokes, source-frame linkage
// (each carried mask keeps a line back to the frame it was cut from).
// The snooper's knowledge = the events the victim knew that it did not (ledger st.know transferred). Each one is a
// mask cut from that event's own still (X.still), proposed on the victim, tracked through the keyhole and carried by the doer.
// Branches (all from the ledger): secrets vs. empty proposal; victim notices and plugs the keyhole (a negative point and
// a new plug mask; the linkage is cut) vs. stays unaware; victim already dead (grey lost object; the doer flees);
// doer already dead (ghost mask); a third sack who is a SPY/PREDATOR watches from the corridor; the doer's temperament
// decides how it carries what it learned (R stacks and counts, B is weighed down and turns away, I lets one drift off, O wears them as a fan).
(function(){
const IDC={R:'255,112,84',B:'84,168,255',I:'142,224,96',O:'214,128,255'};   // object-ID colours
const CLOTH={R:['#d6bf96','#a78e65'],B:['#e8d5ae','#b9a077'],I:['#e2cea5','#ad9870'],O:['#f0e4c8','#c4b48d']};
const S=1.22, FLOOR=895, WX0=970, WX1=1024, KX=968, KY=766, CEIL=122, DUR=3.2;
const EAR={R:{len:.26,ang:.42,bx:.36},B:{len:.17,ang:.5,bx:.36},I:{len:.72,ang:2.98,bx:.45},O:{len:.13,ang:.3,bx:.34}};
const SNOOP_T0=.35;

// ---------- ledger reading ----------
function secretsOf(ev,st,L){const A=ev.A,V=ev.V;let out=[];
 if(L&&L.states[ev.k]){const b=L.states[ev.k];out=st.know[A].filter(k=>k!==ev.k&&!b.know[A].includes(k))}
 else out=st.know[A].filter(k=>{const e=st.evidence[k];return e&&k!==ev.k&&e.A!==A&&e.V!==A&&e.deed!=='slander'&&st.know[V].includes(k)});
 return out.sort((a,b)=>a-b)}
function noticedOf(ev,st){const A=ev.A,V=ev.V;if(!st.alive[V]||!st.alive[A])return false;const m=st.mind[V][A]||{};
 const bel=st.belief&&st.belief[V]&&st.belief[V][A]?st.belief[V][A].harm.m:0;const lv=st.levers[V]||{};
 let s=Math.max(m.fear||0,m.grudge||0)*.6+bel*.5+({R:.35,O:.3,B:.05,I:-.25})[V]+(lv.tempo||0)*.3+(m.desire||0)*.2;
 if(st.body[V].includes('drowsy'))s-=.5;if(st.body[V].includes('gag')||st.body[V].includes('rope'))s-=.15;return s>.32}
function watcherOf(ev,st){let best=null,bs=.22;for(const w of ['R','B','I','O']){if(w===ev.A||w===ev.V||!st.alive[w])continue;const my=st.myth[w]||{};
 const s=(my.SPY||0)+(my.PREDATOR||0)*.35;if(s>bs){bs=s;best=w}}return best}
function lerpLv(a,b,u){const o={};for(const k of ['loom','weight','tempo','halo','shadow','shrink','grey'])o[k]=(a&&a[k]||0)*(1-u)+(b&&b[k]||0)*u;return o}

// ---------- the mask proposal: a sack is a box prompt + a contour that refines ----------
// local coords: origin bottom centre, y negative up. r = refinement 0..1 (vertex count and boundary error)
function bodyPts(K,W,H,o,seed,r,tq){const n=Math.round(8+r*48),pts=[];const bul=o.bul||.07,sag=o.sag||0,pinch=o.pinch||0;
 for(let i=0;i<n;i++){const th=i/n*Math.PI*2,c=Math.cos(th),s=Math.sin(th);const p=3.4;const rr=Math.pow(Math.pow(Math.abs(c),p)+Math.pow(Math.abs(s),p),-1/p);
  let x=c*rr*W/2*(1+bul*(1-Math.abs(s))),y=-H/2-s*rr*H/2;if(s>0)y+=sag*Math.pow(1-Math.abs(c),2);
  if(pinch&&s>0)x*=1-pinch*Math.exp(-Math.pow((s-.55)/.16,2));
  if(y>0)y=0;const j=(1-r)*7+1.1;x+=(K.hash(seed+i*3.1+tq)-.5)*j;y+=(K.hash(seed+i*5.7+tq*1.3)-.5)*j;pts.push([x,y])}return pts}
function earPts(W,H,id,side,ang,len){const E=EAR[id];const bx=side*W*E.bx,by=-H*.93,w=W*(id==='I'?.2:.17);const a=ang*side,L=len*H;
 const dx=Math.sin(a),dy=-Math.cos(a);const nx=-dy,ny=dx;const out=[];
 // a lobe: base (two points) to a rounded tip, sampled along two quadratic sides
 const p0=[bx-nx*w*.5,by-ny*w*.5],p2=[bx+nx*w*.5,by+ny*w*.5],tip=[bx+dx*L,by+dy*L];const c0=[bx+dx*L*.5-nx*w*.55,by+dy*L*.5-ny*w*.55],c2=[bx+dx*L*.5+nx*w*.5,by+dy*L*.5+ny*w*.5];
 const q=(a,c,b,u)=>[(1-u)*(1-u)*a[0]+2*u*(1-u)*c[0]+u*u*b[0],(1-u)*(1-u)*a[1]+2*u*(1-u)*c[1]+u*u*b[1]];
 for(let i=0;i<=6;i++)out.push(q(p0,c0,tip,i/6));for(let i=5;i>=0;i--)out.push(q(p2,c2,tip,i/6));return out}
function poly(g,pts){g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath()}
function bbox(pts){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const[x,y]of pts){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}return{x0,y0,x1,y1}}
function rgba(c,a){return`rgba(${c},${Math.max(0,a)})`}
function greyMix(hex,gr){const n=parseInt(hex.slice(1),16);let r=n>>16,g=n>>8&255,b=n&255;const y=(r*.3+g*.59+b*.11)*.85;r=r+(y-r)*gr;g=g+(y-g)*gr;b=b+(y-b)*gr;return`rgb(${r|0},${g|0},${b|0})`}

// draw one sack as an accepted mask with its attributes and carried damage as sub-masks
function sack(g,K,id,x,o,t){const c=K.CAST[id],lv=o.lv||{},body=o.body||[];
 const kk=S*(1+.12*Math.max(0,lv.loom||0)-.18*(lv.shrink||0));let W=c.w*kk*(o.sx||1),H=c.h*kk*(o.sy||1);
 if(body.includes('emptied'))H*=.8;const gr=Math.min(1,(lv.grey||0)+(o.grey||0)+(body.includes('greyed')?.5:0));
 const tq=Math.floor(t*12)*.37;const r=o.r??1;
 const seed=({R:11,B:23,I:37,O:51})[id];
 const droop=(lv.shrink||0)*.6+(body.includes('drowsy')?.5:0)+(o.droop||0);
 const E=EAR[id];let ang=E.ang+droop-(o.alert||0)*(id==='I'?1.1:.35);ang=Math.max(0,ang);
 const pts=bodyPts(K,W,H,{bul:id==='R'?.1:id==='B'?.09:.05,sag:(id==='I'?H*.22:H*.04)+(o.slump||0)*H*.2,pinch:body.includes('cinched')?.22:0},seed,r,tq);
 const eL=earPts(W,H,id,-1,ang,E.len),eR=earPts(W,H,id,1,ang,E.len);
 g.save();g.translate(x,o.floor??FLOOR);if(o.rot)g.rotate(o.rot);if(o.lean)g.transform(1,0,o.lean,1,0,0);
 g.globalAlpha*=o.alpha??1;
 // shadow lever: cast on the back wall (left, away from the keyhole light), tracked as its own object
 if(o.wallShadow){const sh=o.wallShadow;g.save();g.translate(-W*.6-sh*90,0);g.scale(1.05+sh*.55,1+sh*1.3);
  g.fillStyle=`rgba(4,6,12,${.18+sh*.3})`;poly(g,pts);g.fill();poly(g,eL);g.fill();poly(g,eR);g.fill();
  if(sh>.15){g.setLineDash([8,8]);g.strokeStyle=rgba(IDC[id],sh*.55*(o.idA??1));g.lineWidth=2/(1+sh);poly(g,pts);g.stroke();g.setLineDash([])}g.restore()}
 g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(0,2,W*.55,8,0,0,7);g.fill();
 if(lv.halo>.05){const hg=g.createRadialGradient(0,-H*.7,10,0,-H*.7,W*1.1);hg.addColorStop(0,`rgba(255,236,190,${lv.halo*.32})`);hg.addColorStop(1,'rgba(255,236,190,0)');g.fillStyle=hg;g.fillRect(-W*1.2,-H*1.8,W*2.4,H*2)}
 const cg=g.createLinearGradient(-W/2,0,W/2,0);cg.addColorStop(0,greyMix(CLOTH[id][0],gr));cg.addColorStop(1,greyMix(CLOTH[id][1],gr));
 g.fillStyle=cg;g.strokeStyle='#2a1f17';g.lineWidth=2;for(const e of [eL,eR]){poly(g,e);g.fill();g.stroke()}
 poly(g,pts);g.fill();
 // attribute sub-masks, clipped to the body
 g.save();poly(g,pts);g.clip();
 if(id==='R'){g.fillStyle=greyMix('#6e3a33',gr);g.fillRect(-W,-H*1.2,W*2,H*.42)}
 if(id==='B'){g.fillStyle=greyMix('#2a2622',gr*.5);g.fillRect(-W,-H*.44,W*2,H*.08);g.strokeStyle=greyMix('#8a6a32',gr);g.lineWidth=4;g.beginPath();g.arc(0,-H*.7,W*.13,0,7);g.stroke();
  g.beginPath();g.moveTo(0,-H*.6);g.lineTo(0,-H*.8);for(let k=0;k<3;k++){g.moveTo(0,-H*(.64+k*.05));g.lineTo(-W*.04,-H*(.68+k*.05));g.moveTo(0,-H*(.64+k*.05));g.lineTo(W*.04,-H*(.68+k*.05))}g.stroke()}
 // carried damage: each tag is its own small segment proposal (dashed white contour)
 g.setLineDash([5,4]);g.lineWidth=2;
 if(body.includes('rope')){g.strokeStyle='#8a6a3a';g.lineWidth=7;g.setLineDash([]);for(const yy of [.32,.62]){g.beginPath();g.moveTo(-W,-H*yy);g.lineTo(W,-H*yy-6);g.stroke()}g.setLineDash([5,4]);g.lineWidth=2}
 if(body.includes('gag')){g.fillStyle='#e9e0cc';g.fillRect(-W,-H*.9,W*2,H*.07)}
 if(body.includes('blot')){g.fillStyle='#14131c';g.beginPath();g.ellipse(-W*.18,-H*.4,W*.1,H*.07,.4,0,7);g.fill()}
 if(body.includes('tag')){g.fillStyle='#efe6d0';g.fillRect(W*.1,-H*.36,W*.18,H*.13);g.strokeStyle='#5a4a3a';g.setLineDash([]);g.strokeRect(W*.1,-H*.36,W*.18,H*.13);g.setLineDash([5,4])}
 if(body.includes('torn')){g.strokeStyle='#3a2a1c';g.setLineDash([]);g.lineWidth=2.5;g.beginPath();for(let k=0;k<7;k++)g.lineTo(W*.25+(k%2?8:-8),-H*(.15+k*.07));g.stroke();
  g.fillStyle='#fbf7ee';for(let k=0;k<5;k++){g.beginPath();g.arc(W*.25+(K.hash(k+seed)-.5)*14,-H*(.12+k*.05),3,0,7);g.fill()}g.setLineDash([5,4])}
 g.restore();
 poly(g,pts);g.stroke();
 if(body.includes('coins')){g.fillStyle='#c9a24a';g.strokeStyle='#6d5320';g.lineWidth=1.5;for(let k=0;k<4;k++){g.beginPath();g.ellipse(W*.62,-6-k*7,12,4,0,0,7);g.fill();g.stroke()}}
 if(id==='O'){ // the wig: its own object part, long, hanging past the shoulders
  const wg=[[-W*.62,-H*1.04],[W*.62,-H*1.04],[W*.7,-H*.78],[W*.64,-H*.5],[W*.4,-H*.58],[W*.38,-H*.8],[-W*.38,-H*.8],[-W*.4,-H*.58],[-W*.64,-H*.5],[-W*.7,-H*.78]];
  g.save();if(o.wigOff){g.translate(o.wigOff[0],o.wigOff[1]);g.rotate(o.wigOff[2]||0)}
  g.fillStyle=greyMix('#7a3b8f',gr);g.strokeStyle=greyMix('#4f2161',gr);poly(g,wg);g.fill();g.stroke();
  g.strokeStyle=greyMix('#5d2a70',gr);g.lineWidth=1.5;for(let k=-3;k<=3;k++){g.beginPath();g.moveTo(k*W*.17,-H*1.0);g.lineTo(k*W*.2,-H*(.6+.04*(k&1)));g.stroke()}g.restore()}
 // the mask overlay: tint, contour, box prompt, positive point, ID swatch, confidence ring
 const ida=(o.idA??1)*(1-gr*.75);
 if(ida>.02){const col=o.idc||IDC[id];g.fillStyle=rgba(col,.07*ida);poly(g,pts);g.fill();poly(g,eL);g.fill();poly(g,eR);g.fill();
  g.strokeStyle=rgba(col,.95*ida);g.lineWidth=3;if(o.dash)g.setLineDash([10,7]);poly(g,pts);g.stroke();poly(g,eL);g.stroke();poly(g,eR);g.stroke();g.setLineDash([]);
  const bb=bbox(pts.concat(eL,eR));const p=12,cl=20;g.lineWidth=2.5;g.strokeStyle=rgba(col,.8*ida);g.beginPath();
  for(const[cx,cy,sx,sy]of [[bb.x0-p,bb.y0-p,1,1],[bb.x1+p,bb.y0-p,-1,1],[bb.x0-p,bb.y1+p,1,-1],[bb.x1+p,bb.y1+p,-1,-1]]){g.moveTo(cx+sx*cl,cy);g.lineTo(cx,cy);g.lineTo(cx,cy+sy*cl)}g.stroke();
  g.fillStyle=rgba(col,ida);g.fillRect(bb.x0-p,bb.y0-p-18,14,14);
  const conf=o.conf??1;g.lineWidth=4;g.strokeStyle=rgba('255,255,255',.18*ida);g.beginPath();g.arc(bb.x1+p+2,bb.y0-p-12,9,0,7);g.stroke();
  g.strokeStyle=rgba(col,ida);g.beginPath();g.arc(bb.x1+p+2,bb.y0-p-12,9,-Math.PI/2,-Math.PI/2+conf*Math.PI*2);g.stroke();
  if(o.point){g.fillStyle='#fff';g.beginPath();g.arc(0,-H*.48,6,0,7);g.fill();g.strokeStyle=rgba(col,ida);g.lineWidth=3;g.beginPath();g.arc(0,-H*.48,12,0,7);g.stroke()}}
 g.restore();
 return{W,H,top:(o.floor??FLOOR)-H,cx:x}}

// ---------- the world plate (dimmed under the mask view) ----------
function plate(g,K,t,beam){g.fillStyle='#0b0d12';g.fillRect(0,0,1920,1080);
 let gr=g.createLinearGradient(0,CEIL,0,FLOOR);gr.addColorStop(0,'#121826');gr.addColorStop(1,'#1d2536');g.fillStyle=gr;g.fillRect(0,CEIL,WX0,FLOOR-CEIL);
 g.fillStyle='#171c28';g.fillRect(0,700,WX0,FLOOR-700);g.strokeStyle='#29324a';g.lineWidth=3;g.beginPath();g.moveTo(0,700);g.lineTo(WX0,700);g.stroke();
 g.fillStyle='#9fb3d6';g.globalAlpha=.55;g.fillRect(90,250,80,110);g.fillRect(180,250,80,110);g.fillRect(90,370,80,110);g.fillRect(180,370,80,110);g.globalAlpha=1;
 const wl=g.createLinearGradient(260,480,600,895);wl.addColorStop(0,'rgba(150,175,220,.12)');wl.addColorStop(1,'rgba(150,175,220,0)');g.fillStyle=wl;g.beginPath();g.moveTo(90,480);g.lineTo(260,480);g.lineTo(640,895);g.lineTo(300,895);g.closePath();g.fill();
 gr=g.createLinearGradient(WX1,0,1920,0);gr.addColorStop(0,'#3e2c1f');gr.addColorStop(1,'#6e5134');g.fillStyle=gr;g.fillRect(WX1,CEIL,1920-WX1,FLOOR-CEIL);
 g.fillStyle='rgba(0,0,0,.12)';for(let x=WX1+20;x<1920;x+=46)g.fillRect(x,CEIL,18,FLOOR-CEIL);
 const lg=g.createRadialGradient(1850,560,10,1850,560,560);lg.addColorStop(0,'rgba(255,214,140,.45)');lg.addColorStop(1,'rgba(255,214,140,0)');g.fillStyle=lg;g.fillRect(WX1,CEIL,1920-WX1,FLOOR-CEIL);
 g.fillStyle='#d9b064';g.beginPath();g.moveTo(1820,520);g.lineTo(1890,520);g.lineTo(1905,570);g.lineTo(1805,570);g.closePath();g.fill();g.fillStyle='#3a2a1a';g.fillRect(1850,570,8,90);
 g.fillStyle='#120f0c';g.fillRect(0,FLOOR,WX0,1080-FLOOR);g.fillStyle='#2c1f15';g.fillRect(WX1,FLOOR,1920-WX1,1080-FLOOR);
 g.strokeStyle='rgba(0,0,0,.3)';g.lineWidth=2;for(let y=FLOOR+40;y<1080;y+=46){g.beginPath();g.moveTo(0,y);g.lineTo(1920,y);g.stroke()}
 g.fillStyle='#2b211a';g.fillRect(WX0,CEIL-30,WX1-WX0,1080-CEIL+30);g.strokeStyle='#1a130e';g.lineWidth=3;g.strokeRect(WX0+6,CEIL+140,WX1-WX0-12,FLOOR-CEIL-140);
 g.fillStyle='#c9a24a';g.beginPath();g.arc(WX0-4,KY-34,6,0,7);g.fill();g.beginPath();g.arc(WX1+4,KY-34,6,0,7);g.fill();
 // keyhole channel
 g.fillStyle='#050403';g.beginPath();g.arc(WX0-1,KY-6,5,0,7);g.fill();g.fillRect(WX0-3,KY-6,4,16);
 if(beam>.01){const bm=g.createLinearGradient(KX,0,KX-560,0);bm.addColorStop(0,`rgba(255,214,140,${.45*beam})`);bm.addColorStop(1,'rgba(255,214,140,0)');g.fillStyle=bm;
  g.beginPath();g.moveTo(KX,KY-5);g.lineTo(KX-560,KY-50);g.lineTo(KX-560,KY+64);g.lineTo(KX,KY+5);g.closePath();g.fill();
  g.fillStyle=`rgba(255,220,150,${.8*beam})`;g.beginPath();g.arc(WX0-1,KY-4,4,0,7);g.fill()}
 g.fillStyle='rgba(6,8,14,.26)';g.fillRect(0,0,1920,1080)}  // mask view: the plate sits dimmed under the overlays

// ---------- a carried secret: a mask cut from the remembered event's still ----------
const CROP={};
function cropOf(K,e){const key=e.deed+e.A+e.V;if(CROP[key])return CROP[key];let c={x:300,y:300,w:1320,h:700};
 try{const D=window.DEEDS&&DEEDS[e.deed];if(D&&D.marks){const m=D.marks(D.contact,e.A,e.V,K);const x0=Math.min(m.A.x,m.V.x),y0=Math.min(m.A.y,m.V.y),x1=Math.max(m.A.x+m.A.w,m.V.x+m.V.w),y1=Math.max(m.A.y+m.A.h,m.V.y+m.V.h);
  let w=x1-x0+160,h=y1-y0+140;const cx=(x0+x1)/2,cy=(y0+y1)/2;if(w/h<16/9)w=h*16/9;else h=w*9/16;w=Math.min(w,1920);h=Math.min(h,1080);c={x:K.cl(0,1920-w,cx-w/2),y:K.cl(0,1080-h,cy-h/2),w,h}}}catch(err){}
 CROP[key]=c;return c}
const SMALL={};  // the cut-out fragment, kept at tile resolution (source-frame linkage: deed, doer, victim, contact time)
function smallOf(K,X,e){const key=e.deed+e.A+e.V;if(SMALL[key])return SMALL[key];if(!X||!X.still||typeof document==='undefined')return null;
 try{const cv=X.still(e);const c=cropOf(K,e);const sm=document.createElement('canvas');sm.width=400;sm.height=224;sm.getContext('2d').drawImage(cv,c.x,c.y,c.w,c.h,0,0,400,224);SMALL[key]=sm;return sm}catch(err){return null}}
function tileMask(K,w,h,r,seed,tq){const n=Math.round(6+r*34),pts=[];for(let i=0;i<n;i++){const th=i/n*Math.PI*2,c=Math.cos(th),s=Math.sin(th);const p=4;const rr=Math.pow(Math.pow(Math.abs(c),p)+Math.pow(Math.abs(s),p),-1/p);
  const j=(1-r)*.16+.015;const q=1+(K.hash(seed+i*2.3+tq)-.5)*j;pts.push([c*rr*w/2*q,s*rr*h/2*q])}return pts}
function tile(g,K,X,e,col,x,y,sc,o){const w=250*sc,h=140*sc;if(w<3)return;const tq=Math.floor(o.t*12)*.29;const pts=tileMask(K,w,h,o.r,e.k*7.7+1,tq);
 g.save();g.translate(x,y);if(o.rot)g.rotate(o.rot);g.globalAlpha*=o.alpha??1;
 g.save();poly(g,pts);g.clip();let ok=false;
 const sm=smallOf(K,X,e);if(sm){g.drawImage(sm,-w/2,-h/2,w,h);ok=true}
 if(!ok){g.fillStyle='#3a2c20';g.fillRect(-w/2,-h/2,w,h)}
 if(o.grey){g.fillStyle=`rgba(120,120,120,${o.grey*.6})`;g.globalCompositeOperation='saturation';g.fillRect(-w/2,-h/2,w,h);g.globalCompositeOperation='source-over'}
 g.fillStyle=rgba(col,.14);g.fillRect(-w/2,-h/2,w,h);g.restore();
 g.strokeStyle=rgba(col,.95);g.lineWidth=Math.max(1.5,3*sc);if(o.dash)g.setLineDash([9*sc+2,6*sc+2]);poly(g,pts);g.stroke();g.setLineDash([]);
 if(sc>.25){const p=7*sc,cl=14*sc;g.lineWidth=2;g.strokeStyle=rgba(col,.7);g.beginPath();
  for(const[cx,cy,sx,sy]of [[-w/2-p,-h/2-p,1,1],[w/2+p,-h/2-p,-1,1],[-w/2-p,h/2+p,1,-1],[w/2+p,h/2+p,-1,-1]]){g.moveTo(cx+sx*cl,cy);g.lineTo(cx,cy);g.lineTo(cx,cy+sy*cl)}g.stroke();
  const conf=o.conf??1;g.lineWidth=3;g.strokeStyle=rgba(col,1);g.beginPath();g.arc(w/2+p,-h/2-p-9*sc,7*sc,-Math.PI/2,-Math.PI/2+conf*Math.PI*2);g.stroke()}
 g.restore()}

// ---------- tracking: a path through the keyhole with history boxes ----------
function path(u,x0,y0,x1,y1){ // victim -> keyhole (shrinking) -> slot (growing)
 const ux=KX+(WX1-WX0)/2;if(u<.45){const v=u/.45,e=v*v*(3-2*v);return{x:x0+(ux-x0)*e,y:y0+(KY-y0)*e-Math.sin(Math.PI*v)*40,s:1-.9*e}}
 const v=(u-.45)/.55,e=1-Math.pow(1-v,3);return{x:ux+(x1-ux)*e,y:KY+(y1-KY)*e-Math.sin(Math.PI*v)*70,s:.1+.9*e}}

// ---------- the beat ----------
function plan(ev,st,X,K){const L=X&&X.ledger;const A=ev.A,V=ev.V;const sec=secretsOf(ev,st,L);const prev=L&&L.states[ev.k]?L.states[ev.k]:st;
 let ax=420,vx=1420;try{const D=window.DEEDS&&DEEDS.snooping;if(D&&D.marks){const m=D.marks(6,A,V,K);ax=m.A.x+m.A.w/2;vx=m.V.x+m.V.w/2}}catch(err){}
 ax=K.cl(260,WX0-160,ax);vx=K.cl(WX1+170,1760,vx);
 const evs=sec.map(k=>L?L.ev[k]:{k,deed:st.evidence[k].deed,A:st.evidence[k].A,V:st.evidence[k].V});
 return{A,V,sec,evs,prev,ax,vx,noticed:noticedOf(ev,st),deadV:!st.alive[V],ghostA:!st.alive[A],watcher:watcherOf(ev,st),tempo:1+.25*K.cl(-1,1,(st.levers[A]||{}).tempo||0)}}
function slot(P,K,i,n,t,ah,aw){const A=P.A,ax=P.ax;const top=FLOOR-ah;
 if(A==='R'){return{x:ax-aw*.5-110,y:FLOOR-55-i*Math.min(92,560/n),s:.62,rot:0}}            // stacked and counted
 if(A==='B'){return{x:ax+(K.hash(i*3.3)-.5)*110,y:top-50-i*Math.min(56,330/n),s:.6,rot:(K.hash(i*1.7)-.5)*.5}}  // piled on him
 if(A==='I'){const a=i/n*Math.PI*2+t*1.1;return{x:ax-70+Math.cos(a)*230,y:top-150+Math.sin(a)*95,s:.55,rot:Math.sin(a)*.3}}  // loose orbit
 const a=-1.1+2.2*(n>1?i/(n-1):.5);return{x:ax+Math.sin(a)*240,y:top-60-Math.cos(a)*200,s:.55,rot:a*.45}}  // worn as a fan

function beat(g,t,ev,st,K,X){const P=plan(ev,st,X,K);const A=P.A,V=P.V,tp=P.tempo;
 const plugT=1.75/tp,plugged=P.noticed?K.sm(plugT,plugT+.25,t):0;
 plate(g,K,t,1-plugged);
 const lvA=lerpLv(P.prev.levers[A],st.levers[A],K.sm(1.0,2.6,t)),lvV=st.levers[V];
 // ---- victim ----
 let vx=P.vx,vo={lv:lvV,body:st.body[V],point:t>SNOOP_T0&&t<1.2,conf:1};
 if(P.deadV){Object.assign(vo,{grey:.85,idA:.35,dash:true,slump:.6,droop:.8,conf:0,point:t>SNOOP_T0&&t<1.2})}
 else if(P.noticed){const u=K.sm(1.15/tp,1.6/tp,t);const cW=K.CAST[V].w*S;vx=K.lerp(P.vx,WX1+cW*.55+14,u);
  vo.alert=K.sm(.95,1.2,t)*(1-.4*K.sm(2.4,2.9,t));vo.lean=-.18*K.sm(1.1,1.5,t)*(1-K.sm(2.3,2.8,t));vo.conf=1;
  if(V==='O')vo.wigOff=[0,0,0]}
 else{vo.slump=.1*Math.sin(t*1.3);vo.droop=V==='I'?.1:0}
 const vS=sack(g,K,V,vx,vo,t);
 // plug: a new mask proposal on the room side of the keyhole, refining
 if(P.noticed&&t>plugT-.1){const r=K.sm(plugT,plugT+.5,t);const px=WX1+10,py=KY-4;g.save();
  const plugC={R:'#6e3a33',B:'#fbf7ee',I:'#d8c49b',O:'#7a3b8f'}[V];const pts=tileMask(K,54,62,r,77,Math.floor(t*12));
  g.translate(px,py);g.fillStyle=plugC;poly(g,pts);g.fill();g.strokeStyle=rgba(IDC[V],.95);g.lineWidth=2.5;poly(g,pts);g.stroke();
  g.strokeStyle=rgba(IDC[V],.8);g.beginPath();g.moveTo(-36,-30);g.lineTo(-36,-44);g.lineTo(-22,-44);g.moveTo(36,30);g.lineTo(36,44);g.lineTo(22,44);g.stroke();
  // the victim's limb of cloth reaching to it (a line of action, not a hand)
  const reach=1-K.sm(plugT+.35,plugT+.8,t);if(reach>0){g.strokeStyle=greyMix(CLOTH[V][0],0);g.lineWidth=10*reach+2;g.lineCap='round';g.beginPath();g.moveTo(10,0);g.quadraticCurveTo(40,20,vx-px-vS.W*.35,-(py-(FLOOR-vS.H*.75)));g.stroke()}
  g.restore();
  // negative point on the corridor face: the snooper's view is corrected out
  const nA=K.sm(plugT+.1,plugT+.3,t);g.save();g.translate(WX0-34,KY-4);g.globalAlpha=nA;g.fillStyle='#1a0b0b';g.beginPath();g.arc(0,0,22,0,7);g.fill();
  g.strokeStyle='#ff4a4a';g.lineWidth=5;g.beginPath();g.arc(0,0,22,0,7);g.stroke();g.beginPath();g.moveTo(-11,0);g.lineTo(11,0);g.stroke();g.restore();
  // the correction stroke: the victim scrubs the view region out of the snooper's mask (drawn on the corridor side, across the beam)
  const cs=K.sm(plugT+.05,plugT+.45,t),fade=1-.6*K.sm(2.6,3.1,t);if(cs>0){g.save();g.globalAlpha=fade;g.strokeStyle='rgba(255,74,74,.42)';g.lineWidth=11;g.lineCap='round';g.lineJoin='round';g.beginPath();
   const m=Math.floor(cs*9);for(let i=0;i<=m;i++){const x=WX0-60-(i%2?150:20)+K.hash(i*5.1)*20,y=KY-60+i*14;i?g.lineTo(x,y):g.moveTo(x,y)}g.stroke();g.restore()}}
 // ---- the doer ----
 const c=K.CAST[A];let ax=P.ax,ao={lv:lvA,body:st.body[A],wallShadow:Math.max(0,lvA.shadow)*.9,point:false};
 const nS=P.sec.length;
 if(P.ghostA)Object.assign(ao,{alpha:.5,grey:.7,dash:true,idA:.6});
 if(P.noticed){const st2=K.sm(plugT+.15,plugT+.45,t);ao.alert=st2*(1-.5*K.sm(2.6,3,t));ax-=st2*60*(A==='I'?.4:1);ao.conf=1-.45*st2;ao.dash=st2>.5||ao.dash}
 const land=1.05+Math.min(6,Math.max(1,nS))*.12;
 if(nS===0&&!P.deadV){ao.droop=.4*K.sm(1.5,2.1,t);ao.slump=.3*K.sm(1.5,2.1,t)}
 else if(A==='R'){ao.lean=.05*Math.sin(t*5)*K.sm(1.6,2,t);ao.sy=1+.03*Math.sin(t*9)*K.sm(1.6,2.2,t)}
 else if(A==='B'){const wgt=K.sm(1.4,2.4,t);ao.sy=1-.1*wgt*Math.min(1,nS/3);ao.sx=1+.05*wgt;ao.droop=.3*wgt;ax-=80*K.sm(2.2,3,t);ao.lean=.08*K.sm(2.2,3,t)}
 else if(A==='I'){ao.droop=-.1;ao.slump=.15}
 else if(A==='O'){const u=K.sm(1.6,2.4,t);ao.sy=1+.05*u;ao.lean=-.03*u}
 if(P.deadV&&!P.ghostA){const f=K.sm(2.0/tp,2.9/tp,t);ax-=f*(ax-120);ao.alert=K.sm(1.3,1.6,t);ao.lean=.15*f}
 const aS=sack(g,K,A,ax,ao,t);
 // ---- the snoop proposal: a positive point on the victim (from the keyhole) ----
 if(t>SNOOP_T0-.05&&(t<1.3||(!P.noticed&&!P.deadV))){const u=K.sm(SNOOP_T0-.05,SNOOP_T0+.2,t)*(P.noticed||P.deadV?1-K.sm(1.1,1.3,t):1-.4*K.sm(1.1,1.4,t));g.save();g.globalAlpha=u;g.strokeStyle=rgba(IDC[A],.7);g.lineWidth=2;g.setLineDash([4,8]);
  g.beginPath();g.moveTo(WX0-2,KY-4);g.lineTo(vx,vS.top+vS.H*.52);g.stroke();g.setLineDash([]);g.fillStyle=rgba(IDC[A],1);g.beginPath();g.arc(vx,vS.top+vS.H*.52,7,0,7);g.fill();
  g.strokeStyle='#fff';g.lineWidth=2;g.beginPath();g.arc(vx,vS.top+vS.H*.52,13+4*Math.sin(t*12),0,7);g.stroke();g.restore()}
 // ---- tiles: each secret proposed on the victim, tracked through the keyhole, carried ----
 const items=P.evs.slice(0,6).map(e=>({e,col:IDC[e.A===V?e.V:e.A]}));
 if(P.deadV)items.push({e:null,col:'170,170,170',body:true});
 const n=items.length;
 if(n===0){ // empty proposal: a dashed box comes back with nothing
  const u=K.sm(.6,1.7,t),p=path(u,vx,vS.top+vS.H*.5,ax+aS.W*.2,aS.top-80),fade=1-K.sm(2.3,2.8,t);
  if(t>.5){g.save();g.globalAlpha=fade*K.sm(.5,.7,t);g.translate(p.x,p.y);g.strokeStyle=rgba(IDC[A],.8);g.lineWidth=2.5;g.setLineDash([8,8]);const w=120*p.s,h=70*p.s;g.strokeRect(-w/2,-h/2,w,h);g.setLineDash([]);
   g.lineWidth=3;g.beginPath();g.arc(w/2+8,-h/2-10,7*p.s+2,-Math.PI/2,-Math.PI/2+.05);g.stroke();g.restore()}}
 const tiles=[];
 for(let i=0;i<n;i++){const it=items[i];const t0=.55+i*.13/tp,t1=t0+.95/tp;const u=K.cl(0,1,(t-t0)/(t1-t0));if(t<t0-.15)continue;
  const sl=slot(P,K,i,n,t,aS.H,aS.W);const sx=sl.x+(ax-P.ax);
  let drift=0;if(A==='I'&&i===n-1&&n>1&&!it.body)drift=K.sm(2.0,3.1,t);
  const x0=vx+(K.hash(i*4.1)-.5)*vS.W*.6,y0=vS.top+vS.H*(.25+.5*K.hash(i*2.9));const p=path(u,x0,y0,sx,sl.y-drift*260);
  const sc=K.lerp(p.s*.85,sl.s,u>.45?K.sm(.6,1,u):0)*(n>5?.85:1);
  const emerge=K.sm(t0-.15,t0+.05,t);
  // tracking history: earlier boxes of the same object id
  if(u>0&&u<1){g.save();for(let h=1;h<=4;h++){const q=path(K.cl(0,1,u-h*.05),x0,y0,sx,sl.y);const w=250*q.s*.85,hh=140*q.s*.85;g.strokeStyle=rgba(it.col,.28-.06*h);g.lineWidth=2;g.strokeRect(q.x-w/2,q.y-hh/2,w,hh)}g.restore()}
  tiles.push({it,x:p.x,y:p.y,sc:Math.max(.05,sc*emerge),r:K.sm(t0,t1,t),rot:u>=1?sl.rot:0,u,drift})}
 // source-frame linkage: from carried masks back to the keyhole (and on to the victim while it is open)
 for(const tl of tiles){if(tl.u<1)continue;g.save();g.strokeStyle=rgba(tl.it.col,.35*(1-tl.drift));g.lineWidth=1.5;g.setLineDash([3,6]);g.beginPath();g.moveTo(tl.x,tl.y);g.lineTo(WX0-4,KY-4);
  if(!plugged||plugged<.5)g.lineTo(vx,vS.top+vS.H*.5);g.stroke();g.restore()}
 for(const tl of tiles){const o={t,r:tl.r,rot:tl.rot,dash:plugged>.5,conf:1-.5*plugged-.6*tl.drift,alpha:1-tl.drift,grey:tl.it.body?1:0};
  if(tl.it.body){ // what the snooper saw: the victim as a still, grey object
   g.save();g.translate(tl.x,tl.y);g.scale(tl.sc*1.2,tl.sc*1.2);g.fillStyle='#1a1a1a';g.fillRect(-90,-55,180,110);sack(g,K,V,0,{floor:50,grey:1,idA:.4,dash:true,slump:.6,droop:.8,conf:0},t);g.restore();
   continue}
  tile(g,K,X,tl.it.e,tl.it.col,tl.x,tl.y,tl.sc,o)}
 // R counts: a tick mark per landed tile on the stack
 if(A==='R'&&n>0){g.save();g.strokeStyle=rgba(IDC.R,.9);g.lineWidth=3;for(let i=0;i<n;i++){const tl=tiles[i];if(!tl||tl.u<1)continue;const k=K.sm(0,.1,t-(.55+i*.13/tp+.95/tp));
  g.globalAlpha=k;g.beginPath();g.moveTo(tl.x-70,tl.y-12);g.lineTo(tl.x-70,tl.y+12);g.stroke()}g.restore()}
 // ---- a watcher in the corridor: a third sack whose own mask proposes the snooper ----
 if(P.watcher){const w=P.watcher,u=K.sm(1.9,2.4,t);if(u>0){const wx=-K.CAST[w].w*S*.25+u*40;
  g.save();g.globalAlpha=u;sack(g,K,w,wx,{lv:st.levers[w],body:st.body[w],conf:.7},t);
  g.strokeStyle=rgba(IDC[w],.7);g.lineWidth=2;g.setLineDash([4,8]);g.beginPath();g.moveTo(wx+30,FLOOR-K.CAST[w].h*S*.6);g.lineTo(ax,aS.top+aS.H*.5);g.stroke();g.setLineDash([]);
  g.fillStyle=rgba(IDC[w],1);g.beginPath();g.arc(ax,aS.top+aS.H*.5,7,0,7);g.fill();g.strokeStyle='#fff';g.lineWidth=2;g.beginPath();g.arc(ax,aS.top+aS.H*.5,13,0,7);g.stroke();g.restore()}}
}

// ---------- sound: grains only ----------
function sound(ac,out,t0,ev,st,K){const SND=K.SND;if(!SND)return;const bus=ac.createGain();bus.gain.value=2.4;bus.connect(out);out=bus;const A=ev.A,V=ev.V;const sec=secretsOf(ev,st,null);const noticed=noticedOf(ev,st),deadV=!st.alive[V];
 const tp=1+.25*K.cl(-1,1,(st.levers[A]||{}).tempo||0);const pa=-.55,pv=.5;const mf=m=>440*Math.pow(2,(m-69)/12);
 SND.cloud(ac,out,t0,DUR,6,{bp:300,a:.02,d:[.1,.3]});                              // room hush
 SND.grain(ac,out,t0+SNOOP_T0,{f:mf(96),d:.03,a:.16,pan:pv,att:.05});SND.grain(ac,out,t0+SNOOP_T0+.05,{f:mf(103),d:.03,a:.12,pan:pv,att:.05}); // the prompt click
 SND.cloud(ac,out,t0+SNOOP_T0+.06,.35,60,{bp:3200,q:4,a:.03,d:[.01,.03],spread:.2},u=>1-u);               // mask fills
 const n=Math.min(8,sec.length)+(deadV?1:0);const base={R:45,B:33,I:57,O:81};
 if(n===0){SND.grain(ac,out,t0+.7,{f:mf(70),glide:-.45,d:.9,a:.07,pan:0,type:'triangle',att:.2});SND.say(ac,out,A,t0+1.6,'sink',.6,pa)}
 for(let i=0;i<n;i++){const s=t0+.55+i*.13/tp,e=sec[i]!==undefined?st.evidence[sec[i]]:null;const oth=e?(e.A===V?e.V:e.A):V;const m=base[oth]+24;
  SND.grain(ac,out,s,{f:mf(m),glide:.3,d:.12,a:.08,pan:pv,att:.2});                       // proposed on the victim
  SND.grain(ac,out,s+.42/tp,{f:mf(m+12),d:.04,a:.06,pan:.02,att:.1});                     // through the keyhole
  SND.say(ac,out,A,s+.95/tp,'tick',.8,pa);if(A==='R')SND.pluck(ac,out,s+.97/tp,76+i%3*2,.12,.4,pa)}
 if(noticed){SND.say(ac,out,V,t0+1.0,'react',.7,pv);SND.say(ac,out,V,t0+1.2/tp,'step',.8,.15);
  SND.thump(ac,out,t0+1.75/tp,.5,90,.05);SND.cloud(ac,out,t0+1.75/tp,.25,80,{bp:400,a:.05,d:[.01,.04],spread:.1},u=>1-u);
  SND.grain(ac,out,t0+1.85/tp,{f:mf(60),d:.06,a:.12,pan:0,att:.05});SND.say(ac,out,A,t0+1.95/tp,'react',.5,pa)}
 if(deadV){SND.say(ac,out,A,t0+1.35,'react',.6,pa);for(let k=0;k<4;k++)SND.say(ac,out,A,t0+(2.0+k*.2)/tp,'step',.9,pa-.1*k)}
 if(A==='B'&&n>0)SND.say(ac,out,'B',t0+2.0,'sink',.8,pa);
 if(A==='O'&&n>0){for(let k=0;k<3;k++)SND.grain(ac,out,t0+2.1+k*.08,{f:mf(93+[0,4,7][k]),d:.25,a:.05,pan:pa,att:.1})}
 if(A==='I'&&n>1){SND.say(ac,out,'I',t0+2.0,'breathe',.9,pa);SND.grain(ac,out,t0+2.4,{f:mf(88),glide:.5,d:.6,a:.03,pan:-.3,att:.3})}
 if(watcherOf(ev,st))SND.grain(ac,out,t0+2.05,{f:mf(98),d:.03,a:.1,pan:-.95,att:.05})}

// ---------- trace: the keyhole mask, coarsening as it ages ----------
function trace(g,box,age,K){const a=Math.exp(-age*.22);if(a<.03)return;const cx=box.x+box.w/2,cy=box.y+box.h/2,s=Math.min(box.w,box.h)/100;
 const r=K.cl(0,1,1-age*.12);g.save();g.translate(cx,cy);g.scale(s,s);g.globalAlpha=a;
 g.fillStyle='#050403';g.beginPath();g.arc(0,-12,16,0,7);g.fill();g.beginPath();g.moveTo(-8,-4);g.lineTo(8,-4);g.lineTo(14,32);g.lineTo(-14,32);g.closePath();g.fill();
 const n=Math.round(6+r*30);g.strokeStyle='rgba(255,214,140,.85)';g.lineWidth=2.5;g.setLineDash([6,5]);g.beginPath();
 for(let i=0;i<=n;i++){const th=i/n*Math.PI*2;const q=1+(K.hash(i*3.7+age)-.5)*(1-r)*.5;const x=Math.cos(th)*30*q,y=Math.sin(th)*40*q+4;i?g.lineTo(x,y):g.moveTo(x,y)}g.stroke();g.setLineDash([]);
 g.fillStyle='#fff';g.beginPath();g.arc(0,-12,4,0,7);g.fill();g.strokeStyle='rgba(255,214,140,.9)';g.lineWidth=2;g.beginPath();g.arc(0,-12,9,0,7);g.stroke();g.restore()}

CONSEQ({deed:'snooping',n:11,scion:30,lineage:'SAM 2 — Prompted Mask Proposal Swarm',
 op:'A positive point placed through the keyhole segments the victim\'s secrets into masks cut from their own shots; the masks are tracked through the keyhole into the snooper\'s keeping, unless the victim answers with a negative point and a plug.',
 made:'Every sack is an accepted segmentation mask over a dimmed plate of the corridor and the lamplit room: a refining vertex contour with its attribute as a sub-mask, a box prompt, an object-ID colour and a confidence ring; carried damage shows as small sub-masks. Each secret is a mask cut out of the remembered event\'s own still, edged in the ID colour of the other sack in it.',
 moved:'Masks move by tracking: each secret is proposed on the victim, refines from a coarse polygon to a fine one as it travels through the keyhole, leaves a trail of earlier boxes and keeps a linkage line back to its source. The ledger chooses the rest: who notices and plugs, whether anything is learned, whether the victim is already dead, who watches, and how the doer carries what it took; myth levers set shadow, size, light, colour and timing.',
 dur:DUR,beat,sound,trace});
})();
