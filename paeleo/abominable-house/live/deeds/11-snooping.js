// 11 · SNOOPING — SCION 39 · Multiview Drawing Substitution (Turn Lab)
// Each sack is a drawing atlas: four discrete view drawings (F front, Q three-quarter, P profile, K rear),
// each with its own width, ear placement, bulge and attribute drawing, all on one canonical pivot
// (bottom centre, the floor contact). Orientation is a yaw value; the atlas SUBSTITUTES the nearest
// drawing. Interpolation is allowed only inside a view sector (front features slide with yaw: stencil,
// knot, buckle) where the topology corresponds; between views there is a hard swap.
(function(){
const INK='#2a1f17';
const FY=860, CY=226, WALL0=968, WALL1=1012, KX=964, KY=754;     // floor, ceiling, wall faces, keyhole
const DEPTH={R:.62,B:.72,I:.55,O:.6};                              // profile width / front width (canonical)
const EAR={R:{dx:.07,dy:.11,up:.24},B:{dx:.05,dy:.07,up:.17},I:{dx:.1,dy:-.5,up:.68},O:{dx:.06,dy:.08,up:.2}};
const BUL={R:.08,B:.075,I:.035,O:.04};
const SAG={R:7,B:-6,I:20,O:4};
const CLOTH={R:['#d6bf96','#ad9369'],B:['#e8d5ae','#bea57a'],I:['#e2cea5','#b29d74'],O:['#f0e4c8','#c9b993']};
const HAIR='#7a3b8f', HAIRD='#4f2161', SHAWL='#6e3a33', BELT='#2a2622';

// ---------- orientation state -> atlas drawing ----------
function viewOf(yaw){let a=((yaw+180)%360+360)%360-180;const s=a<0?-1:1,m=Math.abs(a);
 if(m<22.5)return{v:'F',f:1,dev:a/22.5};if(m<67.5)return{v:'Q',f:s,dev:(m-45)/22.5};
 if(m<125)return{v:'P',f:s,dev:0};return{v:'K',f:s,dev:0}}
let CARRY={};
function tagsOf(id,o){return o.tags||CARRY[id]||[]}
function geo(K,id,o){const c=K.CAST[id],vw=viewOf(o.yaw||0),v=vw.v,d=DEPTH[id],tg=tagsOf(id,o);
 const wf=v==='P'?d:v==='Q'?(1+d)/2+.04:1;
 const W=c.w*wf*(o.sx||1),H=c.h*(o.sy||1)*(tg.includes('emptied')?.86:1);const e=EAR[id],al=(o.alert||0)-(tg.includes('drowsy')?.45:0);
 const dx=e.dx*c.w,dy=(e.dy+e.up*al)*c.h;let L={dx,dy},R={dx,dy};
 if(v==='Q')L={dx:dx*.4,dy:dy*.78};
 if(v==='P'){R={dx:dx*1.6+W*.02,dy};L={dx:dx*.25,dy:dy*.6}}
 let bl=BUL[id],br=BUL[id];if(v==='P'){br*=1.6;bl*=.7}
 return{c,v,f:vw.f,dev:vw.dev,W,H,L,R,bl,br}}
function frame(g,G,o){g.translate(o.x,o.y);const k=o.k||1;g.scale(k,k);
 if(o.rot){const p=(o.piv||0)*G.W/2*G.f;g.translate(p,0);g.rotate(o.rot);g.translate(-p,0)}
 g.scale(G.f,1);if(o.shear)g.transform(1,0,-o.shear,1,0,0)}
function bodyPath(g,G,sag){const{W,H,bl,br}=G;g.beginPath();g.moveTo(-W*.4,0);g.lineTo(W*.4,0);
 g.quadraticCurveTo(W/2+br*W*.6,-H*.02,W/2+br*W,-H*.42);g.quadraticCurveTo(W/2+br*W*.4,-H*.86,W*.48,-H);
 g.quadraticCurveTo(0,-H+sag,-W*.48,-H);
 g.quadraticCurveTo(-W/2-bl*W*.4,-H*.86,-W/2-bl*W,-H*.42);g.quadraticCurveTo(-W/2-bl*W*.6,-H*.02,-W*.4,0);g.closePath()}
function ear(g,G,s,E,fill){const{W,H}=G;const ax=s*W*.3,ay=-H*.995,bx=s*(W*.5+(s>0?G.br:G.bl)*W*.25),by=-H*.82;
 const tx=s*(W*.48+E.dx),ty=-H-E.dy;const c1x=s*(W*.5+E.dx*.5+W*.03),c1y=-H-Math.max(E.dy,0)*.8-H*.05;
 const c2x=s*(W*.5+Math.abs(E.dx)*.9),c2y=(ty+by)/2;
 g.beginPath();g.moveTo(ax,ay);g.quadraticCurveTo(c1x,c1y,tx,ty);g.quadraticCurveTo(c2x,c2y,bx,by);g.closePath();g.fillStyle=fill;g.fill();
 g.beginPath();g.moveTo(ax,ay);g.quadraticCurveTo(c1x,c1y,tx,ty);g.quadraticCurveTo(c2x,c2y,bx,by);g.stroke()}
function stitches(g,x0,y0,x1,y1,n){g.save();g.setLineDash([5,6]);g.beginPath();g.moveTo(x0,y0);g.lineTo(x1,y1);g.stroke();g.restore()}

// ---------- per-sack attribute drawings, one per view ----------
function deco(g,K,id,G,o){const{W,H,v,dev,c}=G;const fx=v==='F'?dev*W*.09:v==='Q'?W*.17+dev*W*.05:W*.42;
 g.lineWidth=g.lineWidth*.8;g.strokeStyle='rgba(42,31,23,.5)';
 if(v==='Q'){g.fillStyle='rgba(50,32,16,.2)';g.fillRect(-W,-H*1.3,W*.5+W*.34-W*.5+W*.5,H*1.6);
  g.beginPath();g.moveTo(-W*.16,-H*.98);g.quadraticCurveTo(-W*.2,-H*.5,-W*.15,0);g.stroke()}
 if(v==='P')stitches(g,W*.02,-H*.95,-W*.02,-H*.05);
 if(v==='K')stitches(g,0,-H*.97,0,-H*.04);
 if(v==='F'){g.beginPath();g.moveTo(-W*.3,-H*.08);g.quadraticCurveTo(0,-H*.03,W*.3,-H*.08);g.stroke()}
 if(id==='R'){g.fillStyle=SHAWL;g.fillRect(-W,-H*1.3,W*2,H*.5);g.fillStyle='#57281f';
  for(let i=-6;i<=6;i++){const x=i*W*.08;g.beginPath();g.moveTo(x-W*.03,-H*.8);g.lineTo(x,-H*.74);g.lineTo(x+W*.03,-H*.8);g.fill()}
  if(v==='K'){g.fillStyle=SHAWL;g.beginPath();g.moveTo(-W*.36,-H*.81);g.lineTo(W*.36,-H*.81);g.lineTo(0,-H*.5);g.closePath();g.fill();
   g.strokeStyle='#3d1b15';g.beginPath();g.moveTo(-W*.36,-H*.81);g.lineTo(0,-H*.5);g.lineTo(W*.36,-H*.81);g.stroke()}
  else{g.fillStyle='#4e231c';g.beginPath();g.arc(fx,-H*.8,c.w*.05,0,7);g.fill();g.strokeStyle='#4e231c';g.lineWidth*=1.8;
   g.beginPath();g.moveTo(fx,-H*.78);g.lineTo(fx-c.w*.04,-H*.6);g.moveTo(fx,-H*.78);g.lineTo(fx+c.w*.03,-H*.62);g.stroke()}}
 if(id==='B'){g.fillStyle=BELT;g.fillRect(-W,-H*.44,W*2,H*.075);
  if(v!=='K'){g.fillStyle='#9c8045';g.fillRect(fx-c.w*.04,-H*.455,c.w*.08,H*.1)}
  if(v==='F'||v==='Q'){g.save();g.translate(fx,-H*.68);g.scale(v==='Q'?.68:1,1);const r=c.w*.15;g.strokeStyle='rgba(120,88,40,.75)';g.lineWidth*=1.6;
   g.beginPath();g.arc(0,0,r,0,7);g.stroke();g.beginPath();g.moveTo(0,r*.8);g.lineTo(0,-r*.75);g.stroke();
   for(let j=0;j<4;j++){const y=-r*.55+j*r*.28;g.beginPath();g.ellipse(-r*.17,y,r*.12,r*.07,-.6,0,7);g.ellipse(r*.17,y,r*.12,r*.07,.6,0,7);g.stroke()}g.restore()}
  if(v==='K'){g.strokeStyle='rgba(42,31,23,.55)';g.fillStyle='rgba(150,120,80,.35)';g.fillRect(-W*.3,-H*.78,W*.2,H*.18);g.strokeRect(-W*.3,-H*.78,W*.2,H*.18)}}
 if(id==='I'){g.strokeStyle='rgba(60,42,25,.5)';const n=v==='P'?3:4;
  for(let i=0;i<n;i++){const x=(-.3+.6*i/(n-1))*W;g.beginPath();g.moveTo(x-W*.06,-H*.95);g.quadraticCurveTo(x+W*.1,-H*.75,x-W*.02,-H*.55);g.stroke()}
  g.beginPath();g.moveTo(-W*.5,-H*.45);g.quadraticCurveTo(0,-H*.52,W*.5,-H*.44);g.stroke()}
 if(id==='O'&&v!=='K'&&v!=='P'){g.beginPath();g.moveTo(-W*.5,-H*.5);g.quadraticCurveTo(0,-H*.46,W*.5,-H*.5);g.stroke()}}

function wig(g,G,mode){const{W,H,v}=G;if(mode==='off'){g.fillStyle='rgba(255,252,240,.55)';g.beginPath();g.ellipse(W*.12,-H*.93,W*.18,H*.025,0,0,7);g.fill();return}
 g.save();if(mode==='askew'){g.translate(0,-H);g.rotate(.34);g.translate(W*.12,H+H*.03)}
 g.fillStyle=HAIR;g.strokeStyle=HAIRD;g.beginPath();
 if(v==='F'){g.moveTo(-W*.68,-H*.34);g.lineTo(-W*.66,-H*.95);g.quadraticCurveTo(-W*.6,-H*1.13,0,-H*1.12);g.quadraticCurveTo(W*.6,-H*1.13,W*.66,-H*.95);
  g.lineTo(W*.68,-H*.34);g.lineTo(W*.42,-H*.37);g.lineTo(W*.42,-H*.86);g.lineTo(-W*.42,-H*.86);g.lineTo(-W*.42,-H*.37)}
 else if(v==='Q'){g.moveTo(-W*.72,-H*.3);g.lineTo(-W*.64,-H*.95);g.quadraticCurveTo(-W*.5,-H*1.14,W*.1,-H*1.12);g.quadraticCurveTo(W*.62,-H*1.1,W*.62,-H*.9);
  g.lineTo(W*.6,-H*.7);g.lineTo(W*.42,-H*.72);g.lineTo(W*.42,-H*.86);g.lineTo(-W*.22,-H*.86);g.lineTo(-W*.36,-H*.33)}
 else if(v==='P'){g.moveTo(-W*.78,-H*.3);g.lineTo(-W*.66,-H*.95);g.quadraticCurveTo(-W*.5,-H*1.14,W*.2,-H*1.12);g.quadraticCurveTo(W*.62,-H*1.1,W*.6,-H*.9);
  g.lineTo(W*.58,-H*.82);g.lineTo(W*.1,-H*.86);g.quadraticCurveTo(-W*.2,-H*.7,-W*.2,-H*.32)}
 else{g.moveTo(-W*.7,-H*.32);g.lineTo(-W*.66,-H*.95);g.quadraticCurveTo(-W*.6,-H*1.13,0,-H*1.12);g.quadraticCurveTo(W*.6,-H*1.13,W*.66,-H*.95);g.lineTo(W*.7,-H*.32);
  for(let i=6;i>=0;i--){const x=(-.7+1.4*i/6)*W;g.lineTo(x,-H*(i%2?.36:.3))}}
 g.closePath();g.fill();g.stroke();g.beginPath();
 for(let i=0;i<5;i++){const x=(-.5+i*.25)*W;g.moveTo(x,-H*1.05);g.quadraticCurveTo(x-W*.08,-H*.7,x-W*.04,-H*.4)}g.stroke();g.restore()}

function tint(hex,m){let r,g2,b;if(hex[0]==='#'){const a=parseInt(hex.slice(1),16);r=a>>16;g2=(a>>8)&255;b=a&255}else[r,g2,b]=hex.match(/\d+/g).map(Number);const[tr,tg,tb,u]=m;return`rgb(${Math.round(r+(tr-r)*u)},${Math.round(g2+(tg-g2)*u)},${Math.round(b+(tb-b)*u)})`}
function shadow(g,x,y,w,k){g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(x,y+2*k,w*.62*k,9*k,0,0,7);g.fill()}
// carried damage, drawn per view: a mark exists only on the drawings that can see it (multiview rule)
function carryIn(g,G,tg,lw){const{W,H,v}=G;const fx=v==='F'?0:v==='Q'?W*.17:W*.4;const front=v!=='K';
 if(tg.includes('rope')){g.strokeStyle='#8a6a3a';g.lineWidth=lw*2.2;for(const y of[-.3,-.64]){g.beginPath();g.moveTo(-W,H*y+H*.03);g.quadraticCurveTo(0,H*y-H*.04,W,H*y+H*.03);g.stroke()}
  if(v!=='F'){g.beginPath();g.arc(v==='K'?0:-W*.3,-H*.3,lw*2.5,0,7);g.fillStyle='#8a6a3a';g.fill()}}
 if(tg.includes('cinched')){g.strokeStyle='#5a4426';g.lineWidth=lw*2.6;g.beginPath();g.moveTo(-W,-H*.8);g.lineTo(W,-H*.8);g.stroke()}
 if(tg.includes('gag')&&front){g.fillStyle='#e9e2d2';g.strokeStyle=INK;g.lineWidth=lw*.8;g.fillRect(fx-W*.32,-H*.76,W*.64,H*.08);g.strokeRect(fx-W*.32,-H*.76,W*.64,H*.08)}
 if(tg.includes('gag')&&v==='K'){g.fillStyle='#e9e2d2';g.fillRect(-W,-H*.76,W*2,H*.07)}
 if(tg.includes('blot')&&(v==='F'||v==='Q')){g.fillStyle='rgba(20,18,30,.85)';g.beginPath();g.ellipse(fx-W*.14,-H*.5,W*.09,W*.07,.4,0,7);g.fill();g.beginPath();g.arc(fx-W*.02,-H*.42,W*.025,0,7);g.fill()}
 if(tg.includes('torn')){const tx=v==='F'?W*.36:v==='Q'?-W*.3:v==='P'?W*.3:-W*.36;g.strokeStyle=INK;g.lineWidth=lw;g.beginPath();for(let i=0;i<6;i++)g.lineTo(tx+(i%2?W*.05:-W*.03),-H*(.7-i*.07));g.stroke()}}
function carryOut(g,G,tg,lw){const{W,H,v}=G;
 if(tg.includes('tag')&&v!=='K'){const x=v==='F'?W*.3:W*.36;g.strokeStyle=INK;g.lineWidth=lw*.7;g.beginPath();g.moveTo(x,-H*.86);g.lineTo(x+W*.06,-H*.72);g.stroke();
  g.fillStyle='#f6f0dc';g.save();g.translate(x+W*.06,-H*.72);g.rotate(.2);g.fillRect(-10,0,22,15);g.strokeRect(-10,0,22,15);g.restore()}
 if(tg.includes('torn')){g.fillStyle='rgba(251,247,238,.9)';const tx=v==='F'?W*.38:v==='Q'?-W*.32:v==='P'?W*.32:-W*.38;g.beginPath();g.ellipse(tx,-2,W*.12,4,0,0,7);g.fill()}
 if(tg.includes('coins')){g.fillStyle='#c9a640';g.strokeStyle=INK;g.lineWidth=lw*.7;for(let i=0;i<3;i++){g.beginPath();g.ellipse(W*.5+8,-4-i*6,9,4,0,0,7);g.fill();g.stroke()}}}
function sack(g,K,id,o){const G=geo(K,id,o),k=o.k||1,tg=tagsOf(id,o);if(!o.noShadow)shadow(g,o.x,o.y,G.W,k);
 g.save();frame(g,G,o);g.lineWidth=(o.lw||3.4)/k;g.lineJoin='round';g.lineCap='round';g.strokeStyle=INK;
 let cl=CLOTH[id];if(tg.includes('greyed'))cl=cl.map(c=>tint(c,[140,140,140,.55]));const[c0,c1]=o.dark?cl.map(c=>tint(c,o.dark)):cl;const sag=SAG[id]*(o.sy||1)+(tg.includes('emptied')?14:0);
 if(G.v==='P'||G.v==='Q')ear(g,G,-1,G.L,c1);
 bodyPath(g,G,sag);const gr=g.createLinearGradient(-G.W/2,0,G.W/2,0);gr.addColorStop(0,c1);gr.addColorStop(.6,c0);gr.addColorStop(1,c0);g.fillStyle=gr;g.fill();
 g.save();bodyPath(g,G,sag);g.clip();deco(g,K,id,G,o);carryIn(g,G,tg,(o.lw||3.4)/k);g.restore();
 g.strokeStyle=INK;g.lineWidth=(o.lw||3.4)/k;bodyPath(g,G,sag);g.stroke();
 if(G.v==='F'||G.v==='K')ear(g,G,-1,G.L,c0);ear(g,G,1,G.R,c0);
 if(id==='R'&&G.v==='P'){g.strokeStyle='#4e231c';g.lineWidth=5/k;g.beginPath();g.moveTo(G.W*.46,-G.H*.8);g.quadraticCurveTo(G.W*.62,-G.H*.7,G.W*.56,-G.H*.56);g.stroke()}
 if(id==='O')wig(g,G,o.wig||(tg.includes('wig')?'askew':'on'));
 carryOut(g,G,tg,(o.lw||3.4)/k);
  g.restore();return G}

// ---------- pivot alignment: solve the pressed pose so the top front corner meets the keyhole ----------
function contactPt(K,id,o){const G=geo(K,id,o);let lx=G.W*.47,ly=-G.H*.97;lx-= (o.shear||0)*ly;
 const p=(o.piv||0)*G.W/2,c=Math.cos(o.rot||0),s=Math.sin(o.rot||0);return[p+c*(lx-p)-s*ly,s*(lx-p)+c*ly]}
const PRESS={};
function press(K,id){if(PRESS[id])return PRESS[id];
 const base={R:{yaw:90,sx:1.06,rot:.1,piv:.7,alert:.3,v:'sy',lo:.4,hi:1.4},B:{yaw:90,sx:1.0,rot:.12,piv:.9,alert:.5,v:'sy',lo:.3,hi:1.4},
  I:{yaw:90,sx:.88,rot:0,piv:0,alert:0,v:'sy',lo:.6,hi:1.6},O:{yaw:90,rot:.42,piv:.9,alert:.25,v:'sy',lo:.4,hi:1.3}}[id];
 let lo=base.lo,hi=base.hi,o;for(let i=0;i<40;i++){const m=(lo+hi)/2;o=Object.assign({},base,{[base.v]:m});const y=contactPt(K,id,o)[1];
  // y is negative (above floor); want FY+y = KY
  if(base.v==='rot'){if(FY+y<KY)lo=m;else hi=m}else{if(FY+y<KY)hi=m;else lo=m}}
 o.x=KX-contactPt(K,id,o)[0];o.y=FY;PRESS[id]=o;return o}

function boxOf(K,id,o,camOn){const G=geo(K,id,o),k=o.k||1,e=Math.max(0,G.R.dy,G.L.dy);const ex=id==='O'?G.W*.3:0;
 const xs=[-G.W*(.5+G.bl)-Math.abs(G.L.dx)-ex,G.W*(.5+G.br)+Math.abs(G.R.dx)+ex],ys=[-G.H-e-(id==='O'?G.H*.12:0),0];
 const p=(o.piv||0)*G.W/2*G.f,c=Math.cos(o.rot||0),sn=Math.sin(o.rot||0);let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
 for(const lx of xs)for(const ly of ys){const X1=G.f*(lx-(o.shear||0)*ly);let x=o.x+k*(p+c*(X1-p)-sn*ly),y=o.y+k*(sn*(X1-p)+c*ly);
  if(camOn){x=960+(x-960)*1.22;y=700+(y-700)*1.22}x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
 return{x:Math.round(x0),y:Math.round(y0),w:Math.round(x1-x0),h:Math.round(y1-y0)}}
function mix(a,b,u){const o=Object.assign({},b);for(const k of['x','y','sx','sy','rot','piv','alert','shear']){const av=a[k]==null?(k==='sx'||k==='sy'?1:k==='y'?FY:0):a[k],bv=b[k]==null?(k==='sx'||k==='sy'?1:k==='y'?FY:0):b[k];o[k]=av+(bv-av)*u}o.yaw=u<.5?a.yaw:b.yaw;return o}
function step(t,arr){let v=arr[0][1];for(const[a,b]of arr)if(t>=a)v=b;return v}

// ---------- the doer: creep, press, snap ----------
const X0=330;
function doer(K,id,t){const P=press(K,id),xa=P.x-34;
 if(t>=3.6)return after(K,id,t,P);
 let o={x:X0,y:FY,yaw:0,sx:1,sy:1+.01*Math.sin(t*5),rot:0,piv:0,alert:0};
 if(id==='R'){o.yaw=step(t,[[0,0],[.45,45],[.66,90]]);const u=K.cl(0,1,(t-.66)/.94);const n=4,q=u*n,i=Math.min(n-1,Math.floor(q)),fr=q-i;
  o.x=K.lerp(X0,xa,(i+K.sm(.15,.85,fr))/n);if(t>.66&&t<1.6){o.rot=.1*Math.sin(Math.PI*2*fr);o.piv=o.rot>0?.85:-.85;o.y=FY-6*Math.abs(Math.sin(Math.PI*fr))}
  if(u>=1)o.x=xa}
 if(id==='B'){o.yaw=step(t,[[0,0],[.5,45],[.6,90]]);const u=K.cl(0,1,(t-.62)/.93);const n=3,q=u*n,i=Math.min(n-1,Math.floor(q)),fr=q-i;
  o.x=K.lerp(X0,xa,(i+K.sm(.1,.9,fr))/n);if(t>.62&&t<1.55){const s=Math.sin(Math.PI*fr);o.y=FY-24*s;o.sy=1+.09*s;o.sx=1-.06*s}if(u>=1)o.x=xa}
 if(id==='I'){o.yaw=step(t,[[0,0],[.72,45],[.86,90]]);o.x=K.lerp(X0,xa,K.sm(.75,1.6,t));o.rot=-.07+.05*Math.sin(t*5.3)*K.sm(.6,.8,t)*(1-K.sm(1.5,1.6,t));o.piv=-.6;o.shear=-.05;o.sy=.97}
 if(id==='O'){o.yaw=step(t,[[0,0],[.45,90]]);const gl=[[.55,.8],[.92,1.17],[1.29,1.54]];let s=0;for(const[a,b]of gl)s+=K.eo(a,b,t);o.x=K.lerp(X0,xa,s/3)}
 const u=K.sm(1.58,1.86,t);if(u>0)o=mix(o,P,u);
 if(t>1.86){o.x+=2*K.sm(1.86,1.95,t)}
 return o}
function after(K,id,t,P){const T=t-3.6;let o={x:P.x,y:FY,yaw:90,sx:1,sy:1,rot:0,piv:0,alert:1};
 if(id==='R'){o.yaw=0;o.x=P.x-95*K.eo(0,.2,T)-70*K.sm(.3,1.6,T);o.y=FY-28*Math.sin(Math.PI*K.cl(0,1,T/.2));
  o.alert=K.lerp(1,.1,K.sm(.4,1.2,T));o.rot=.06*Math.sin(T*7)*K.sm(.25,.4,T)*(1-K.sm(1.3,1.7,T));o.piv=o.rot>0?.9:-.9}
 if(id==='B'){const a=K.cl(0,1,T/.28);o.x=P.x-140*K.eo(0,.28,T);o.y=FY-34*Math.sin(Math.PI*a);o.rot=-.3*Math.sin(Math.PI*a);o.piv=-.8;
  const land=K.sm(.28,.36,T)*(1-K.sm(.36,.7,T));o.sy=1-.24*land-.1*K.sm(.36,.7,T);o.sx=1+.14*land+.04*K.sm(.36,.7,T);
  o.yaw=step(T,[[0,90],[.6,45],[.7,0]]);o.alert=K.lerp(1,-.35,K.sm(.7,1.3,T))}
 if(id==='I'){o.x=P.x-70*K.eo(0,.15,T);o.alert=T<.35?1:K.lerp(1,0,K.sm(.35,.6,T));o.sy=K.lerp(1,.7,K.sm(.3,.6,T));o.rot=-.12*K.sm(.3,.6,T);o.piv=-.7;
  o.yaw=step(T,[[0,90],[.75,180]]);if(T>.75){o.rot+=.05*Math.sin((T-.75)*6)*(1-K.sm(1.4,1.7,T))}}
 if(id==='O'){o.x=P.x-55*K.eo(0,.12,T)-150*K.sm(.35,1.15,T);o.yaw=step(T,[[0,90],[.16,-90],[1.3,45]]);o.alert=K.lerp(1,0,K.sm(.3,.8,T))}
 if(T<.1){const Q=Object.assign({},P,{alert:1});return mix(Q,o,K.eo(0,.1,T))}
 return o}

// ---------- the victim, in private ----------
const VX=1380;
const VTURN={R:[[0,180],[3.12,-90],[3.22,-45],[3.32,0]],B:[[0,180],[3.2,-90],[3.27,-45],[3.34,0]],I:[[0,180],[3.2,-90],[3.32,-45],[3.44,0]],O:[[0,180],[3.24,-90],[3.31,0]]};
function priv(K,id,t){ // private-activity pose parameters (shared by cutaway and keyhole view)
 const o={sx:1,sy:1,rot:0,piv:0,alert:0,lift:0};
 if(id==='R'){o.rot=.05*Math.sin(t*6.5);o.piv=o.rot>0?.8:-.8}
 if(id==='B'){const p=.5+.5*Math.sin(t*4.6-1.6);o.sy=.95+.08*p;o.sx=1.03-.05*p;o.lift=p}
 if(id==='I'){o.rot=.11*Math.sin(t*2.7);o.piv=.2;o.sy=.96}
 if(id==='O'){o.rot=.03*Math.sin(t*3.1);o.piv=0}
 return o}
function vPose(K,id,t){const T=t-3.6;
 if(t<3.6)return Object.assign({x:VX,y:FY,yaw:90},priv(K,id,t));
 const p={R:{dx:-40,rot:.07,piv:.8},B:{dx:-60},I:{dx:-14,al:.35},O:{dx:-30,wig:'askew'}}[id];
 const s=K.sm(.3,1.0,T);const o={x:VX+p.dx*s,y:FY,yaw:-90,alert:K.lerp(1,p.al!=null?p.al:.75,K.sm(.5,1.4,T)),rot:(p.rot||0)*s,piv:p.piv||0,wig:p.wig};
 if(id==='I')o.sy=.96;return o}
function victimCut(g,K,id,t){const o=vPose(K,id,t);
 if(t<3.6&&id==='B'){const G=geo(K,'B',o);const by=FY-G.H-20-26*o.lift;sack(g,K,id,o);
  g.fillStyle='#333';g.strokeStyle=INK;g.lineWidth=3;g.fillRect(VX-118,by-4,236,8);g.beginPath();g.arc(VX+8,by,50,0,7);g.fillStyle='#3a3a3a';g.fill();g.stroke();g.beginPath();g.arc(VX+8,by,10,0,7);g.fillStyle='#777';g.fill();return}
 sack(g,K,id,o)}
function propsCut(g,K,id,t){ // drawn before the victim
 g.strokeStyle=INK;g.lineWidth=3;
 if(id==='R'){g.fillStyle='#4a3020';g.fillRect(1475,790,130,10);g.fillRect(1482,800,8,60);g.fillRect(1590,800,8,60);g.strokeRect(1475,790,130,10);
  for(let i=0;i<4;i++){const h=[24,40,16,30][i];g.fillStyle='#c9a640';g.fillRect(1490+i*28,790-h,20,h);g.strokeRect(1490+i*28,790-h,20,h);
   for(let j=4;j<h;j+=5){g.beginPath();g.moveTo(1490+i*28,790-j);g.lineTo(1510+i*28,790-j);g.stroke()}}
  if(t<1.9&&K.hash(Math.floor(t*5))>.6){g.fillStyle='#fff3b0';g.beginPath();g.arc(1520,752,5,0,7);g.fill()}}
 if(id==='B'&&t>=3.6){g.fillStyle='#333';g.fillRect(1440,FY-46,236,8);for(const x of[1452,1664]){g.beginPath();g.arc(x,FY-42,42,0,7);g.fillStyle='#3a3a3a';g.fill();g.stroke()}}
 if(id==='I'){g.fillStyle='#4a3020';g.fillRect(VX+40,840,70,20);g.strokeRect(VX+40,840,70,20);g.fillStyle='#efe6d0';g.fillRect(VX+66,806,14,34);g.strokeRect(VX+66,806,14,34);
  const f=1+.15*Math.sin(t*23);g.fillStyle='#ffcc55';g.beginPath();g.ellipse(VX+73,796,5*f,11*f,0,0,7);g.fill();
  g.fillStyle='rgba(255,200,90,.16)';g.beginPath();g.arc(VX+73,796,60,0,7);g.fill();
  g.strokeStyle='rgba(200,200,200,.35)';g.lineWidth=2;g.beginPath();for(let i=0;i<4;i++){const y=780-i*18;g.lineTo(VX+73+8*Math.sin(t*3+i),y)}g.stroke()}
 if(id==='O'){g.fillStyle='#4a3020';g.fillRect(1500,FY-12,80,12);g.fillStyle='#8aa0a8';g.beginPath();g.ellipse(1540,FY-120,34,100,0,0,7);g.fill();
  g.strokeStyle='#5a3a22';g.lineWidth=7;g.stroke();g.strokeStyle=INK;g.lineWidth=3;
  g.fillStyle='rgba(255,255,255,.25)';g.beginPath();g.ellipse(1530,FY-150,8,40,.2,0,7);g.fill();
  g.fillStyle='#3a2618';g.fillRect(1656,FY-150,8,150);g.beginPath();g.arc(1660,FY-168,20,0,7);g.fillStyle='#d8c8b0';g.fill();g.stroke()}}

// ---------- the boarding house cutaway ----------
function cutaway(g,K,t,A,V){const W=1920;
 g.fillStyle='#0b0a09';g.fillRect(0,0,W,1080);
 // hallway (doer side): cold, dark
 let gr=g.createLinearGradient(0,CY,0,FY);gr.addColorStop(0,'#141a27');gr.addColorStop(1,'#1f2738');g.fillStyle=gr;g.fillRect(0,CY,WALL0,FY-CY);
 g.fillStyle='#181e2b';g.fillRect(0,700,WALL0,FY-700);g.strokeStyle='#2c3548';g.lineWidth=3;g.beginPath();g.moveTo(0,700);g.lineTo(WALL0,700);g.stroke();
 g.fillStyle='#aebfd6';g.fillRect(250,380,150,210);g.fillStyle='#1b2232';g.fillRect(320,380,8,210);g.fillRect(250,480,150,8);
 g.fillStyle='rgba(170,190,220,.07)';g.beginPath();g.moveTo(250,590);g.lineTo(400,590);g.lineTo(650,FY);g.lineTo(390,FY);g.closePath();g.fill();
 // victim room: warm, lamplit
 gr=g.createLinearGradient(0,CY,0,FY);gr.addColorStop(0,'#3e2a1d');gr.addColorStop(1,'#5a4030');g.fillStyle=gr;g.fillRect(WALL1,CY,W-WALL1,FY-CY);
 g.fillStyle='rgba(0,0,0,.12)';for(let x=WALL1+20;x<W;x+=44)g.fillRect(x,CY,14,FY-CY);
 g.strokeStyle='#2a1c12';g.lineWidth=5;g.strokeRect(1180,420,120,150);g.fillStyle='#6d5a40';g.fillRect(1183,423,114,144);
 g.fillStyle='#4a3020';g.fillRect(1700,770,60,90);g.fillStyle='#e0b660';g.beginPath();g.moveTo(1705,660);g.lineTo(1755,660);g.lineTo(1770,720);g.lineTo(1690,720);g.closePath();g.fill();g.fillRect(1726,720,8,50);
 const rg=g.createRadialGradient(1730,700,10,1730,700,640);rg.addColorStop(0,'rgba(255,205,120,.38)');rg.addColorStop(1,'rgba(255,205,120,0)');g.fillStyle=rg;g.fillRect(WALL1,CY,W-WALL1,FY-CY);
 // floors
 g.fillStyle='#17130f';g.fillRect(0,FY,WALL0,1080-FY);g.fillStyle='#2e2117';g.fillRect(WALL1,FY,W-WALL1,1080-FY);
 g.strokeStyle='rgba(0,0,0,.35)';g.lineWidth=2;for(let y=FY+30;y<1080;y+=40){g.beginPath();g.moveTo(0,y);g.lineTo(W,y);g.stroke()}
 // keyhole beam into the hall
 const bm=g.createLinearGradient(KX,0,KX-520,0);bm.addColorStop(0,'rgba(255,214,140,.5)');bm.addColorStop(1,'rgba(255,214,140,0)');g.fillStyle=bm;
 g.beginPath();g.moveTo(KX,KY-5);g.lineTo(KX-520,KY-46);g.lineTo(KX-520,KY+60);g.lineTo(KX,KY+5);g.closePath();g.fill();
 g.fillStyle='rgba(255,214,140,.10)';g.beginPath();g.ellipse(KX-330,FY,170,10,0,0,7);g.fill()}
function cam(g){g.translate(960,700);g.scale(1.22,1.22);g.translate(-960,-700)}
function wallSlab(g){g.fillStyle='#2b211a';g.fillRect(WALL0,CY-30,WALL1-WALL0,1080-CY+30);
 g.fillStyle='#5e4430';g.fillRect(WALL0,566,WALL1-WALL0,FY-566);g.strokeStyle='#1a120c';g.lineWidth=3;g.strokeRect(WALL0+2,566,WALL1-WALL0-4,FY-566);
 g.fillStyle='#b8953f';g.beginPath();g.arc(WALL0-5,732,7,0,7);g.arc(WALL1+5,732,7,0,7);g.fill();
 g.fillStyle='#ffdc90';g.fillRect(WALL0-2,KY-4,WALL1-WALL0+4,8);g.fillStyle='#1a120c';g.fillRect(WALL0-4,KY-9,4,18);g.fillRect(WALL1,KY-9,4,18);
 g.fillStyle='#0b0a09';g.fillRect(0,0,1920,CY-30);g.fillStyle='#211a14';g.fillRect(0,CY-30,1920,30)}

// ---------- the keyhole view (iris matte) ----------
function V_B_SHAKE(id,t){return id==='B'&&t>3.2&&t<3.42}
function keyPath(g,cx,cy,s){const r=450*s,n=200*s,a0=Math.acos(n/r);g.beginPath();g.arc(cx,cy,r,a0,Math.PI-a0,true);g.lineTo(cx-380*s,cy+720*s);g.lineTo(cx+380*s,cy+720*s);g.closePath()}
function pov(g,K,t,id,part){const W=1920,X=975,Y=800,k=2.0;
 if(part!=='V'){let gr=g.createLinearGradient(0,0,0,720);gr.addColorStop(0,'#3a271b');gr.addColorStop(1,'#5e4432');g.fillStyle=gr;g.fillRect(0,0,W,720);
 g.fillStyle='rgba(0,0,0,.13)';for(let x=10;x<W;x+=70)g.fillRect(x,0,24,720);
 g.fillStyle='#2e2117';g.fillRect(0,720,W,360);g.strokeStyle='rgba(0,0,0,.3)';g.lineWidth=3;for(const y of[745,780,830,900,990]){g.beginPath();g.moveTo(0,y);g.lineTo(W,y);g.stroke()}
 const rg=g.createRadialGradient(1500,420,20,1500,420,900);rg.addColorStop(0,'rgba(255,205,120,.42)');rg.addColorStop(1,'rgba(255,205,120,0)');g.fillStyle=rg;g.fillRect(0,0,W,1080)}
 const yaw=step(t,VTURN[id]);const p=priv(K,id,t);const caught=t>=VTURN[id][VTURN[id].length-1][0];
 const al=K.sm(3.26,3.38,t);let shake=0;
 const o=Object.assign({x:X,y:Y,k,yaw,lw:5.5,noShadow:false},p,{alert:al});
 if(t>=VTURN[id][1][0]){o.rot=0;}
 if(V_B_SHAKE(id,t))shake=10*(1-K.sm(3.2,3.42,t));
 if(part==='bg')return shake;
 g.strokeStyle=INK;g.lineWidth=5;
 if(id==='R'){g.fillStyle='#4a3020';g.fillRect(620,640,720,22);g.strokeRect(620,640,720,22);g.fillRect(650,662,18,70);g.fillRect(1290,662,18,70);
  for(let i=0;i<6;i++){const x=[640,700,760,1150,1210,1270][i],h=[60,96,40,80,50,110][i];g.fillStyle='#c9a640';g.fillRect(x,640-h,46,h);g.strokeRect(x,640-h,46,h);
   g.lineWidth=2;for(let j=10;j<h;j+=12){g.beginPath();g.moveTo(x,640-j);g.lineTo(x+46,640-j);g.stroke()}g.lineWidth=5}
  if(!caught){const ph=(t*1.6)%1;const cx=X+K.lerp(80,250,ph),cy=520-Math.sin(Math.PI*ph)*150;g.fillStyle='#e8c450';g.beginPath();g.ellipse(cx,cy,16,16*Math.abs(Math.cos(ph*20)),0,0,7);g.fill();g.stroke()}}
 if(id==='I'){const sx=X+105;g.fillStyle='#4a3020';g.fillRect(sx,760,150,40);g.strokeRect(sx,760,150,40);g.fillStyle='#efe6d0';g.fillRect(sx+58,700,34,60);g.strokeRect(sx+58,700,34,60);
  const f=1+.15*Math.sin(t*23);g.fillStyle='#ffcc55';g.beginPath();g.ellipse(sx+75,678,11*f,26*f,0,0,7);g.fill();
  const rg2=g.createRadialGradient(sx+75,678,4,sx+75,678,200);rg2.addColorStop(0,'rgba(255,200,90,.35)');rg2.addColorStop(1,'rgba(255,200,90,0)');g.fillStyle=rg2;g.fillRect(sx-200,480,480,400);
  g.strokeStyle='rgba(210,210,210,.45)';g.lineWidth=4;for(let s=0;s<3;s++){g.beginPath();for(let i=0;i<6;i++){const y=650-i*40-((t*60+s*80)%120);g.lineTo(sx+75+18*Math.sin(t*3+i+s*2),y)}g.stroke()}}
 if(id==='O'){g.fillStyle='#8aa0a8';g.beginPath();g.ellipse(X,240,150,210,0,0,7);g.fill();
  g.save();g.beginPath();g.ellipse(X,240,150,210,0,0,7);g.clip();
  const wigOn=t<2.5;sack(g,K,'O',{x:X,y:560,k:1.25,yaw:yaw===180?0:180-yaw,lw:4,wig:wigOn?'on':'off',alert:al,noShadow:true,dark:[90,110,125,.4]});g.restore();
  g.strokeStyle='#5a3a22';g.lineWidth=16;g.beginPath();g.ellipse(X,240,150,210,0,0,7);g.stroke();g.strokeStyle=INK;g.lineWidth=5;
  g.fillStyle='#3a2618';g.fillRect(1297,470,16,330);g.beginPath();g.arc(1305,440,40,0,7);g.fillStyle='#d8c8b0';g.fill();g.stroke()}
 // the victim, seen from behind at the door, then turning to it
 if(id==='O'){const u=K.sm(2.45,2.95,t);o.wig=t<2.45?'on':'off';sack(g,K,id,o);
  if(t>=2.45){const G=geo(K,'O',{yaw:180});const y0=Y-G.H*k,y1=400+.12*G.H*k;const sx=K.lerp(X,1305,u),sy=K.lerp(y0,y1,u)-80*Math.sin(Math.PI*u);
   g.save();g.translate(sx,sy+G.H*k);g.scale(k,k);g.rotate(.3*Math.sin(Math.PI*u));g.lineWidth=5.5/k;g.strokeStyle=INK;wig(g,Object.assign({},G,{W:G.W*.92}),'on');g.restore()}}
 else if(id==='B'){const drop=K.sm(3.1,3.2,t);if(t>=3.1){o.sy=1;o.sx=1}sack(g,K,id,o);const G=geo(K,'B',o);
  const top=Y-G.H*k-30-70*(t<3.1?p.lift:0);const by=K.lerp(top,Y-90,drop*drop);const hw=G.W*k/2+70;
  g.fillStyle='#444';g.fillRect(X-hw-30,by-8,2*hw+60,16);g.strokeRect(X-hw-30,by-8,2*hw+60,16);
  for(const s of[-1,1]){g.fillStyle='#3a3a3a';g.fillRect(X+s*hw-22,by-95,44,190);g.strokeRect(X+s*hw-22,by-95,44,190)}
}
 else sack(g,K,id,o);
 return shake}

DEED({n:11,key:'snooping',title:'Snooping',scion:39,lineage:'Multiview Drawing Substitution — Turn Lab',
 op:'The doer swaps its front drawing for its profile drawing, presses its top to the keyhole, and the frame becomes the keyhole until the victim swaps its rear drawing for its front one.',
 made:'Each sack is a four-drawing atlas (front, three-quarter, profile, rear) on one floor pivot, each view with its own width, ear placement and its own version of the shawl, belt and wheat stencil, hanging ears or purple wig. The world is a boarding-house cutaway of a cold hallway and a lamplit room split by a door, and a keyhole matte that turns the whole frame into the view through the door.',
 moved:'Orientation is a yaw value that substitutes the nearest view drawing; only inside a view do front features slide continuously, and every turn between views is a hard swap timed per sack. The pressed pose is solved numerically so each sack’s top corner lands on the keyhole: Roessler squats, Belindo squashes and tips, Inigo stretches his empty cloth up, Ogiva tips like a plank.',
 contact:2.3,
 // SOUND. Every view substitution is a dry card click (the drawing swap you can hear). The victim's room is heard through the door:
 // its grains go through one lowpass (the door) that is shut until 1.9, opens 1.9-2.3 with the iris, and shuts again on the cut at 3.6.
 sound(ac,out,t0,A,V,K){const S=K.SND,H=K.hash,pd=x=>K.cl(-1,1,(960+(x-960)*1.22)/960-1),pA=t=>pd(doer(K,A,Math.min(t,5.99)).x),pV=pd(VX);
  const at=t=>t0+t;const card=(t,pan,a=.12)=>{S.grain(ac,out,at(t),{bp:2600+800*H(t*13),q:2.5,d:.014,a,pan,att:.05});S.grain(ac,out,at(t)+.006,{bp:900,q:1,d:.02,a:a*.5,pan,att:.1})};
  // the door: one filter on the victim's room bus
  const door=ac.createBiquadFilter();door.type='lowpass';door.Q.value=.7;door.connect(out);const vb=ac.createGain();vb.gain.value=1;vb.connect(door);
  const f=door.frequency;f.setValueAtTime(420,at(0));f.setValueAtTime(420,at(1.9));f.exponentialRampToValueAtTime(9000,at(2.3));f.setValueAtTime(9000,at(3.6));f.setValueAtTime(380,at(3.601));
  vb.gain.setValueAtTime(.8,at(0));vb.gain.setValueAtTime(.8,at(1.9));vb.gain.linearRampToValueAtTime(1.4,at(2.3));vb.gain.setValueAtTime(1.4,at(3.6));vb.gain.setValueAtTime(.7,at(3.601));
  const vp=t=>(t>=1.9&&t<3.6)?0:pV;
  // room tone of the victim's room (through the door) and a hall clock for the doer's side
  S.cloud(ac,vb,at(0),6,30,{bp:700,a:.012,d:[.08,.25],spread:.3});
  for(let t=.25;t<6;t+=.5)if(t<1.9||t>=3.6)S.grain(ac,out,at(t),{f:1900,d:.012,a:.025,pan:-.85,att:.05});
  // ---- the doer creeps (its voice), every view swap a card click
  const turns={R:[.45,.66],B:[.5,.6],I:[.72,.86],O:[.45]}[A];for(const t of turns)card(t,pA(t));
  if(A==='R')for(let i=0;i<4;i++){const t=.66+(i+.5)*.235;S.say(ac,out,'R',at(t),'step',.5,pA(t))}
  if(A==='B')for(let i=0;i<3;i++){const t=.62+(i+1)*.31;S.say(ac,out,'B',at(t),'step',.45,pA(t))}
  if(A==='I'){S.say(ac,out,'I',at(.75),'breathe',.9,pA(1));S.cloud(ac,out,at(.8),.8,25,{bp:1400,a:.02,d:[.05,.15],spread:.2},u=>Math.sin(Math.PI*u))}
  if(A==='O')for(const t of[.55,.92,1.29]){S.say(ac,out,'O',at(t),'tick',.6,pA(t));S.grain(ac,out,at(t),{bp:5000,d:.22,a:.025,pan:pA(t),att:.3})}
  // press to the door: soft contact and a wood creak
  S.say(ac,out,A,at(1.84),'land',.35,0);S.cloud(ac,out,at(1.84),.3,40,{f:150,glide:.3,noise:.6,a:.03,d:[.03,.08],type:'sawtooth',spread:.1},u=>Math.sin(Math.PI*u));
  // ---- the victim in private (on the door bus)
  if(V==='R'){for(let t=.1;t<3.1;t+=.625)S.grain(ac,vb,at(t+.31),{f:2600+400*H(t),d:.06,a:.09,pan:vp(t),att:.05,type:'triangle'});S.say(ac,vb,'R',at(.2),'breathe',1.6,pV);S.say(ac,vb,'R',at(2.3),'breathe',.8,0)}
  if(V==='B'){for(let n=0;n<3;n++){const tb=(0.029+6.283*n)/4.6,tt=(3.171+6.283*n)/4.6;if(tb<3.1)S.say(ac,vb,'B',at(tb),'step',.5,vp(tb));if(tt<3.1)S.grain(ac,vb,at(tt),{f:1300,d:.12,a:.07,pan:vp(tt),att:.05,type:'triangle'})}}
  if(V==='I'){S.cloud(ac,vb,at(0),3.5,18,{bp:3200,a:.05,d:[.005,.02],spread:.2});S.say(ac,vb,'I',at(.3),'breathe',1.2,pV);S.say(ac,vb,'I',at(2.4),'breathe',.8,0)}
  if(V==='O'){S.say(ac,vb,'O',at(.3),'breathe',1.2,pV);S.cloud(ac,vb,at(2.45),.5,40,{bp:4200,a:.03,d:[.04,.12],spread:.3},u=>Math.sin(Math.PI*u));S.say(ac,vb,'O',at(2.95),'tick',.8,.3)}
  // ---- CONTACT: the frame becomes the keyhole; the door opens to the ear (rising grains, then the seeing chord)
  for(let k=0;k<26;k++){const t=1.9+k*.015;S.grain(ac,out,at(t),{bp:300*Math.pow(16,k/26),q:1.2,d:.06,a:.03+.1*k/26,pan:0,att:.4})}
  S.say(ac,out,A,at(2.15),'breathe',.35,0);
  S.grain(ac,out,at(2.3),{bp:3200,q:1,d:.07,a:.6,att:.08});S.thump(ac,out,at(2.3),1.0,70,0);S.pluck(ac,out,at(2.3),{R:57,B:45,I:64,O:76}[V],.3,1.1,0);
  // ---- caught: the victim's turn, card by card, then its cry
  for(const[t]of VTURN[V].slice(1))card(t,0,.14);
  if(V==='B')S.say(ac,vb,'B',at(3.2),'land',.5,0);
  S.say(ac,vb,V,at(3.33),'react',.9,0);
  // ---- the cut back (the biggest card) and the doer's snap
  card(3.6,pA(3.6),.3);S.say(ac,out,A,at(3.62),'react',.8,pA(3.62));
  if(A==='R'){S.say(ac,out,'R',at(3.8),'land',.6,pA(3.8));for(let t=3.95;t<5.2;t+=.45)S.say(ac,out,'R',at(t),'step',.3,pA(t))}
  if(A==='B'){S.say(ac,out,'B',at(3.88),'land',.5,pA(3.88));card(4.2,pA(4.2));card(4.3,pA(4.3));S.say(ac,out,'B',at(4.5),'sink',.5,pA(4.5))}
  if(A==='I'){S.say(ac,out,'I',at(3.9),'sink',.8,pA(3.9));card(4.35,pA(4.35))}
  if(A==='O'){card(3.76,pA(3.76));S.say(ac,out,'O',at(3.72),'tick',.8,pA(3.72));S.grain(ac,out,at(3.95),{bp:5200,d:.8,a:.012,pan:pA(4.3),att:.5});card(4.9,pA(4.9));S.say(ac,out,'O',at(4.9),'tick',.5,pA(4.9))}
  // the victim edges toward the door, heard through it again
  S.say(ac,vb,V,at(4.0),'step',.5,pV);S.say(ac,vb,V,at(4.45),'step',.4,pV);
 },
 leaves:{A:[],V:['wig']},   // snooping leaves no wound; Ogiva as victim ends with her wig back on askew ('wig' means nothing on the other three)
 marks(t,A,V,K){t=K.cl(0,6,t);
  if(t<1.9||t>=3.6)return{A:boxOf(K,A,doer(K,A,t),true),V:boxOf(K,V,vPose(K,V,t),true)};
  // inside the keyhole: the doer is the camera (its box stays at the pressed pose by the door); the victim is the big figure in the keyhole
  return{A:boxOf(K,A,press(K,A),true),V:boxOf(K,V,Object.assign({x:975,y:800,k:2,yaw:step(t,VTURN[V])},priv(K,V,t)),false)}},
 // LAYERS. Cutaway (t<1.9, t>=3.6): bg = both rooms, lamp, window, keyhole beam, wall slab with door;
 //   V = victim + its props (coins/table, barbell, candle+stool, mirror+wig stand); A = doer (clipped at the wall face) + keyhole glow on its top.
 // Keyhole matte (1.9-3.6): bg = black matte, the room seen through the keyhole (wallpaper, floor, lamp glow), the brass rim;
 //   until 2.05 bg also holds the darkening cutaway. V = the victim large inside the keyhole, its props, the mirror and its reflection,
 //   the vignette over them; until 2.05 also its small darkened cutaway figure with the keyhole punched out. A = empty after 2.05
 //   (the doer is the eye); before 2.05 its darkened pressed figure with the keyhole punched out. Composite bg -> V -> A.
 draw(g,t,A,V,K,opt){t=K.cl(0,6,t);opt=opt||{};CARRY=opt.carry||{};const L=opt.layer,on=q=>!L||L===q;let shake=0;
  const doerDraw=(o)=>{g.save();g.beginPath();g.rect(-200,-200,WALL0+200,1600);g.clip();sack(g,K,A,Object.assign({},o,{dark:[40,52,80,.32]}));g.restore()};
  if(t<1.9||t>=3.6){const o=doer(K,A,t);if(A==='B'&&t>=3.6){const T=t-3.6;if(T>.28&&T<.5)shake=8*(1-(T-.28)/.22)}
   g.save();if(shake)g.translate((K.hash(Math.floor(t*60))-.5)*shake,(K.hash(Math.floor(t*60)+7)-.5)*shake);
   cam(g);if(on('bg')){cutaway(g,K,t,A,V);wallSlab(g)}
   if(on('V')){propsCut(g,K,V,t);victimCut(g,K,V,t)}
   if(on('A')){doerDraw(o);
    if(t>1.75&&t<1.9){const a=K.sm(1.75,1.86,t);const rg=g.createRadialGradient(KX,KY,2,KX,KY,70);rg.addColorStop(0,`rgba(255,220,150,${.7*a})`);rg.addColorStop(1,'rgba(255,220,150,0)');g.fillStyle=rg;g.fillRect(KX-80,KY-80,90,160)}}
   g.restore();return}
  // iris: the frame closes down to the keyhole and opens as the view through it
  const u=K.eo(1.9,2.2,t);const s=K.lerp(.012,1,u),cx=K.lerp(965,960,u),cy=K.lerp(766,400,u),fade=K.sm(1.9,2.0,t);
  if(V_B_SHAKE(V,t)){const a=10*(1-K.sm(3.2,3.42,t));g.translate((K.hash(Math.floor(t*60))-.5)*a,(K.hash(Math.floor(t*60)+3)-.5)*a)}
  const inKey=(part)=>{g.save();keyPath(g,cx,cy,s);g.clip();g.save();if(u<1){g.translate(cx,cy);g.scale(.35+.65*u,.35+.65*u);g.translate(-960,-400)}
   pov(g,K,t,V,part);g.restore();
   if(part!=='bg'){const vg=g.createRadialGradient(cx,cy+120*s,200*s,cx,cy+120*s,760*s);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(0,0,0,.75)');
    if(part==='V')g.globalCompositeOperation='source-atop';g.fillStyle=vg;g.fillRect(0,0,1920,1080);g.globalCompositeOperation='source-over'}g.restore()};
  if(!L){if(t<2.05){const o=doer(K,A,1.89);g.save();cam(g);cutaway(g,K,1.89,A,V);wallSlab(g);propsCut(g,K,V,1.89);victimCut(g,K,V,1.89);doerDraw(o);g.restore()}
   g.fillStyle=`rgba(4,3,3,${fade})`;g.fillRect(0,0,1920,1080);inKey();g.strokeStyle='#3a2a18';g.lineWidth=14*s+2;keyPath(g,cx,cy,s);g.stroke();return}
  if(L==='bg'){if(t<2.05){g.save();cam(g);cutaway(g,K,1.89,A,V);wallSlab(g);g.restore()}g.fillStyle=`rgba(4,3,3,${t<2.05?fade:1})`;g.fillRect(0,0,1920,1080);
   inKey('bg');g.strokeStyle='#3a2a18';g.lineWidth=14*s+2;keyPath(g,cx,cy,s);g.stroke();return}
  const small=(fn)=>{if(t>=2.05)return;g.save();cam(g);fn();g.restore();g.save();g.globalCompositeOperation='source-atop';g.fillStyle=`rgba(4,3,3,${fade})`;g.fillRect(0,0,1920,1080);
   g.globalCompositeOperation='destination-out';keyPath(g,cx,cy,s);g.fill();g.restore()};
  if(L==='V'){small(()=>{propsCut(g,K,V,1.89);victimCut(g,K,V,1.89)});inKey('V')}
  if(L==='A')small(()=>doerDraw(doer(K,A,1.89)));
 },
});
})();
