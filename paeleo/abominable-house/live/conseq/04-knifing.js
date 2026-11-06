// 04 · KNIFING — consequence beat · SCION 29 · GrabCut, cutout extraction
// The doer tries to cut the evidence out of the world. The deed's own end frame is the "scanned page":
// its victim layer is split by colour into typed pieces (body | flour | wig accessory), a box seed is drawn,
// a node lattice is labelled fg/bg, the edges that cross the boundary are cut, and the body comes away as an
// RGBA cutout leaving a transparent hole (checkerboard). What the doer then does with the piece is chosen by
// the ledger. Flour never segments cleanly: whatever flour is left becomes a failure mask (red dashed contour),
// the evidence the cut could not remove.
// Invariant (numeric): body + flour + wig pieces recompose the victim layer exactly (every pixel goes to one piece).
(function(){
const W=1920,H=1080,TS=5.95,FLOOR=930,DUR=3.5;
const FG='#e5483c',BGS='#3f86e8',FAIL='#ff3b30';
const SEEDC={R:'#b4574c',B:'#c9c2b4',I:'#d9cfb8',O:'#b061cc'};
const IDS=['R','B','I','O'];
const TEMP={R:{guilt:.25,pride:.8},B:{guilt:1,pride:.2},I:{guilt:.5,pride:.4},O:{guilt:.15,pride:.9}};
const MASS={R:168*122,B:244*214,I:128*98,O:80*184};
const CUP={x:1694,y:642,w:206,h:292};      // cupboard under the stairs, foreground right
const DOOR={x:1562,y:302,w:158,h:366};     // the room's back door (drawn by the deed's backdrop)
const WIN={x:200,y:202,w:230,h:316};
const mk=(w,h)=>{const c=document.createElement('canvas');c.width=Math.max(1,w);c.height=Math.max(1,h);return c};
const P={},WP={};let S1=null,S2=null;
const sm=(a,b,x)=>{const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)};
const hash=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};

// ---------- the plan: which branch the ledger selects (shared by picture and sound)
function plan(ev,st){
 const A=ev.A,V=ev.V;const imp=(st.impossible||[]).filter(q=>q.k===ev.k);
 const aDead=imp.some(q=>q.who===A),vDead=imp.some(q=>q.who===V);
 let w=null,best=0;
 for(const s of IDS){if(s===A||s===V||!st.alive[s])continue;
  let sc=0;for(const k of st.know[s]){if(k>=ev.k)continue;const e=st.evidence[k];if(e&&(e.A===A||e.V===A||e.A===V||e.V===V))sc+=1}
  const m=st.mind[s][A]||{};sc+=(m.grudge||0)+(m.fear||0)+(m.desire||0)*.5;
  if(sc>best+1e-9){best=sc;w=s}}
 const guilt=(st.mind[A][V]||{}).guilt||0,T=TEMP[A];
 let mode;
 if(aDead||vDead)mode='void';
 else if(st.alive[V])mode='survive';  // the cut did not kill: the victim extracts itself
 else if(guilt>=.9)mode='stay';
 else if(MASS[V]>1.8*MASS[A])mode='cover';
 else if(T.pride>=.85)mode='erase';
 else if(T.pride<.5)mode='flee';
 else mode='hide';
 const found=!!w&&mode!=='void'&&best>=1;
 const knock=!found&&mode!=='void'&&mode!=='survive'&&(V==='R'||V==='O'||(st.body[V]||[]).includes('coins'));
 const lv=st.levers||{};
 return{A,V,mode,vHides:V!=='B',dGuilt:guilt>=.9,witness:found?w:null,knock,aDead,vDead,LA:lv[A]||{},LV:lv[V]||{},LW:found?(lv[w]||{}):{},tempo:1/(1+.35*Math.max(-.6,(lv[A]||{}).tempo||0))}}

// ---------- pieces: extract typed RGBA layers from the deed's own end frame
function plate(A,V,carry,K){
 const key=A+V+JSON.stringify(carry||{});if(P[key])return P[key];
 const D=DEEDS.knifing,op=l=>({layer:l,carry});
 const bg=mk(W,H);try{D.draw(bg.getContext('2d'),TS,A,V,K,op('bg'))}catch(e){}
 const vc=mk(W,H),ac=mk(W,H);try{D.draw(vc.getContext('2d'),TS,A,V,K,op('V'));D.draw(ac.getContext('2d'),TS,A,V,K,op('A'))}catch(e){}
 let m;try{m=D.marks(TS,A,V,K,{carry})}catch(e){m={A:{x:500,y:600,w:300,h:330},V:{x:1200,y:700,w:400,h:230}}}
 // victim region
 const rx=Math.max(0,Math.floor(m.V.x-360)),ry=Math.max(0,Math.floor(m.V.y-80)),rw=Math.min(W-rx,Math.ceil(m.V.w+520)),rh=Math.min(H-ry,1075-ry);
 const src=vc.getContext('2d').getImageData(rx,ry,rw,rh),d=src.data;
 const pieces={body:new ImageData(rw,rh),flour:new ImageData(rw,rh),wig:new ImageData(rw,rh),shade:new ImageData(rw,rh)};
 const bb={body:[1e9,1e9,-1e9,-1e9],flour:[1e9,1e9,-1e9,-1e9],wig:[1e9,1e9,-1e9,-1e9],shade:[1e9,1e9,-1e9,-1e9]};
 for(let i=0;i<d.length;i+=4){const a=d[i+3];if(a<6)continue;const r=d[i],gg=d[i+1],b=d[i+2];
  let k='body';if(a<200&&r<45&&gg<45&&b<45)k='shade';else if(b>r+6&&b>gg+45&&a>40)k='wig';else if(r>243&&gg>238&&b>224&&r-b<26)k='flour';
  const o=pieces[k].data;o[i]=r;o[i+1]=gg;o[i+2]=b;o[i+3]=a;
  if(a>60||k==='shade'){const p=i>>2,x=p%rw,y=(p/rw)|0,q=bb[k];if(x<q[0])q[0]=x;if(y<q[1])q[1]=y;if(x>q[2])q[2]=x;if(y>q[3])q[3]=y}}
 const cv={};for(const k in pieces){cv[k]=mk(rw,rh);cv[k].getContext('2d').putImageData(pieces[k],0,0)}
 const box=k=>bb[k][2]<0?null:{x:rx+bb[k][0],y:ry+bb[k][1],w:bb[k][2]-bb[k][0]+1,h:bb[k][3]-bb[k][1]+1};
 const vb=box('body')||{x:m.V.x,y:m.V.y,w:m.V.w,h:m.V.h},fb=box('flour'),wb=box('wig');
 // grey body (corpse lever), solid matte, ring, transparent hole
 const solid=c=>{const s=mk(c.width,c.height),q=s.getContext('2d');q.drawImage(c,0,0);q.globalCompositeOperation='source-in';q.fillStyle='#fff';q.fillRect(0,0,s.width,s.height);return s};
 const ring=(c,px)=>{const s=solid(c),r=mk(c.width,c.height),q=r.getContext('2d');for(let a=0;a<16;a++)q.drawImage(s,Math.cos(a/16*6.283)*px,Math.sin(a/16*6.283)*px);q.globalCompositeOperation='destination-out';q.drawImage(s,0,0);return r};
 const grey=mk(rw,rh);{const q=grey.getContext('2d');q.drawImage(cv.body,0,0);q.globalCompositeOperation='saturation';q.fillStyle='#808080';q.fillRect(0,0,rw,rh);q.globalCompositeOperation='destination-in';q.drawImage(cv.body,0,0)}
 const matte=solid(cv.body),bring=ring(cv.body,6);
 const hole=mk(rw,rh);{const q=hole.getContext('2d');for(let y=0;y<rh;y+=22)for(let x=0;x<rw;x+=22){q.fillStyle=((x/22+y/22)&1)?'#8d8d8d':'#5e5e5e';q.fillRect(x,y,22,22)}q.globalCompositeOperation='destination-in';q.drawImage(matte,0,0)}
 // doer piece
 const ax=Math.max(0,Math.floor(m.A.x-40)),ay=Math.max(0,Math.floor(m.A.y-40)),aw=Math.min(W-ax,Math.ceil(m.A.w+80)),ah=Math.min(H-ay,1075-ay);
 const dc=mk(aw,ah);dc.getContext('2d').drawImage(ac,-ax,-ay);
 const dgrey=mk(aw,ah);{const q=dgrey.getContext('2d');q.drawImage(dc,0,0);q.globalCompositeOperation='saturation';q.fillStyle='#808080';q.fillRect(0,0,aw,ah);q.globalCompositeOperation='destination-in';q.drawImage(dc,0,0)}
 const dmask=mk(aw,ah);{const q=dmask.getContext('2d');q.drawImage(dc,0,0);q.globalCompositeOperation='source-in';q.fillStyle='#000';q.fillRect(0,0,aw,ah)}
 const dcb=mk(aw,ah);{const q=dcb.getContext('2d');const im=dc.getContext('2d').getImageData(0,0,aw,ah),e=im.data;for(let i=0;i<e.length;i+=4)if(e[i+3]<200&&e[i]<45&&e[i+1]<45&&e[i+2]<45)e[i+3]=0;q.putImageData(im,0,0)}
 const dring=ring(dcb,6);
 // node lattice over the seed box: label from the extracted pieces (the unary term)
 const nodes=[],SP=30,bx0=vb.x-40,by0=vb.y-36,bx1=vb.x+vb.w+40,by1=Math.min(1040,vb.y+vb.h+36);
 const al=(k,x,y)=>{const X=Math.round(x-rx),Y=Math.round(y-ry);if(X<0||Y<0||X>=rw||Y>=rh)return 0;return pieces[k].data[(Y*rw+X)*4+3]};
 let cols=0;for(let y=by0;y<=by1;y+=SP){let c=0;for(let x=bx0;x<=bx1;x+=SP){nodes.push({x,y,fg:al('body',x,y)>100,fl:al('flour',x,y)>100,h:hash(x*.13+y*.71)});c++}cols=c}
 return P[key]={bg,cv,grey,matte,bring,hole,rx,ry,rw,rh,vb,fb,wb,m,dc,dgrey,dmask,dring,ax,ay,aw,ah,nodes,cols,seed:{x:bx0,y:by0,w:bx1-bx0,h:by1-by0}}}

// a sack in the doorway: its idle cutout lifted from the deed's opening frame
function wpiece(w,K){if(WP[w])return WP[w];const o=IDS.find(s=>s!==w);const c=mk(W,H);let m;
 try{DEEDS.knifing.draw(c.getContext('2d'),0,w,o,K,{layer:'A'});m=DEEDS.knifing.marks(0,w,o,K).A}catch(e){m={x:400,y:600,w:300,h:330}}
 const p=mk(Math.ceil(m.w+20),Math.ceil(m.h+20));p.getContext('2d').drawImage(c,-(m.x-10),-(m.y-10));return WP[w]=p}

// ---------- marks in the segmentation idiom
function seedBox(g,b,u,col,t,jit){ // perimeter drawn corner to corner, dashed, crawling
 if(u<=0)return;const per=2*(b.w+b.h);let L=per*Math.min(1,u);const pts=[[b.x,b.y],[b.x+b.w,b.y],[b.x+b.w,b.y+b.h],[b.x,b.y+b.h],[b.x,b.y]];
 g.save();g.strokeStyle=col;g.lineWidth=4;g.setLineDash([18,10]);g.lineDashOffset=-t*60;g.beginPath();
 const J=i=>jit?(hash(i*3.1+Math.floor(t*10))-.5)*jit:0;g.moveTo(pts[0][0]+J(1),pts[0][1]+J(2));
 for(let i=1;i<5&&L>0;i++){const a=pts[i-1],c=pts[i],s=Math.hypot(c[0]-a[0],c[1]-a[1]),f=Math.min(1,L/s);g.lineTo(a[0]+(c[0]-a[0])*f+J(i*5),a[1]+(c[1]-a[1])*f+J(i*7));L-=s}
 g.stroke();g.setLineDash([]);
 // corner handles (the operator's grips)
 if(u>=1){g.fillStyle=col;for(const p of pts.slice(0,4))g.fillRect(p[0]-7,p[1]-7,14,14)}g.restore()}
function ants(g,rc,x,y,sx,sy,t,col,a){ // marching-ants contour of a ring canvas
 if(a<=0)return;const w=rc.width,h=rc.height;if(!S2||S2.width<w||S2.height<h)S2=mk(Math.max(w,S2?S2.width:0),Math.max(h,S2?S2.height:0));
 const q=S2.getContext('2d');q.setTransform(1,0,0,1,0,0);q.globalCompositeOperation='source-over';q.clearRect(0,0,S2.width,S2.height);
 q.fillStyle='#fff';q.fillRect(0,0,w,h);q.strokeStyle=col;q.lineWidth=9;const off=(t*70)%28;q.beginPath();
 for(let k=-h-28;k<w+h;k+=28){q.moveTo(k+off,0);q.lineTo(k+off+h,h)}q.stroke();
 q.globalCompositeOperation='destination-in';q.drawImage(rc,0,0);
 g.save();g.globalAlpha=a;g.translate(x,y);g.scale(sx,sy);g.drawImage(S2,0,0,w,h,0,0,w,h);g.restore()}
function failMask(g,x,y,rx,ry,t,a,i){ // red dashed contour round an island that would not cut out
 if(a<=0)return;g.save();g.globalAlpha=a;g.strokeStyle=FAIL;g.lineWidth=3;g.setLineDash([8,7]);g.lineDashOffset=t*30;g.beginPath();
 for(let k=0;k<=24;k++){const an=k/24*6.283,r=1+.18*(hash(i*9.3+k%24)-.5);const px=x+Math.cos(an)*rx*r,py=y+Math.sin(an)*ry*r;k?g.lineTo(px,py):g.moveTo(px,py)}
 g.closePath();g.stroke();g.restore()}
function flourDot(g,x,y,r,a){g.save();g.globalAlpha=a;g.fillStyle='#fbf7ee';g.beginPath();g.ellipse(x,y,r*1.6,r*.55,0,0,6.283);g.fill();g.restore()}
// background scribble: blue seed strokes that paint the clean plate back over what they cross
function scrub(g,Pl,strokes,u,t){if(u<=0)return;if(!S1)S1=mk(W,H);const q=S1.getContext('2d');q.setTransform(1,0,0,1,0,0);q.globalCompositeOperation='source-over';q.clearRect(0,0,W,H);
 q.lineCap='round';q.lineJoin='round';q.strokeStyle='#000';
 const n=strokes.length;let tot=0;for(const s of strokes)tot+=s.length;let left=tot*u;const vis=[];
 for(const s of strokes){if(left<=0)break;const m=Math.min(s.length,Math.ceil(left));q.lineWidth=s.wd;q.beginPath();q.moveTo(s[0][0],s[0][1]);for(let i=1;i<m;i++)q.lineTo(s[i][0],s[i][1]);q.stroke();vis.push(s.slice(0,m));left-=s.length}
 q.globalCompositeOperation='source-in';q.drawImage(Pl.bg,0,0);g.drawImage(S1,0,0);
 g.save();g.strokeStyle=BGS;g.globalAlpha=.85;g.lineWidth=4;g.lineCap='round';for(const s of vis){if(s.length<2)continue;g.beginPath();g.moveTo(s[0][0],s[0][1]);for(const p of s)g.lineTo(p[0],p[1]);g.stroke()}g.restore()}
function zig(x0,y0,x1,y1,rows,wd,seed){const s=[];const N=rows*10;for(let i=0;i<=N;i++){const u=i/N,row=Math.floor(u*rows),f=(u*rows)%1,dir=row%2?1-f:f;s.push([x0+(x1-x0)*dir+(hash(seed+i)-.5)*14,y0+(y1-y0)*((row+.5)/rows)+(hash(seed+i*1.7)-.5)*10])}s.wd=wd;return s}
function cupboard(g,t,open,K){ // drawn in the room's chalk line
 const ch='rgba(225,208,176,0.34)',f=Math.floor(t*12),J=i=>(hash(i+f*13.1)-.5)*2.4;
 const L=(a,b,c,d,i,w)=>{g.strokeStyle=ch;g.lineWidth=w||2;g.beginPath();g.moveTo(a+J(i),b+J(i+1));g.lineTo((a+c)/2+J(i+2),(b+d)/2+J(i+3));g.lineTo(c+J(i+4),d+J(i+5));g.stroke()};
 const c=CUP;
 // the stair stringer above it
 L(c.x-30,c.y-10,1920,c.y-230,300,2);for(let k=0;k<5;k++){const x=c.x+k*48,y=c.y-10-(k*48)*(220/(1920-c.x+30));L(x,y,x,y-30,310+k*7,1.5);L(x,y-30,x+48,y-30,330+k*7,1.5)}
 g.fillStyle='#120f13';g.fillRect(c.x,c.y,c.w,c.h);
 if(open>0){g.fillStyle='#050405';g.fillRect(c.x+8,c.y+8,c.w-16,c.h-12)}
 // panel: closed fills the opening; open swings toward us on its left hinge (a narrowing trapezoid)
 const pw=(c.w-16)*(1-open);g.fillStyle='#2a2430';g.beginPath();g.moveTo(c.x+8,c.y+8);g.lineTo(c.x+8+pw,c.y+8+open*14);g.lineTo(c.x+8+pw,c.y+c.h-4-open*14);g.lineTo(c.x+8,c.y+c.h-4);g.closePath();g.fill();
 L(c.x,c.y,c.x+c.w,c.y,340);L(c.x+c.w,c.y,c.x+c.w,c.y+c.h,350);L(c.x,c.y,c.x,c.y+c.h,360);
 if(open<.9){L(c.x+8+pw,c.y+12,c.x+8+pw,c.y+c.h-6,370,1.5);g.strokeStyle=ch;g.beginPath();g.arc(c.x+pw-6,c.y+c.h*.55,5,0,6.283);g.stroke()}}

function beat(g,t,ev,st,K,X){
 const L=X&&X.ledger,pre=L?L.states[ev.k]:st;const carry=pre.body;const A=ev.A,V=ev.V;
 const Pl=plate(A,V,carry,K),pl=plan(ev,st),vb=Pl.vb,m=Pl.m;
 const sp=pl.tempo,T=x=>x*sp;            // tempo lever: crisper doers cut sooner
 const found=pl.witness,tF=T({hide:2.05,erase:2.0,flee:2.0,stay:2.35,cover:2.45,void:2.0,survive:2.4}[pl.mode]);const tt=found?Math.min(t,tF+.05):t; // a witness freezes the doer's work
 const mode=pl.mode;
 // ----- per-branch transforms of the pieces
 let bdx=0,bdy=0,bsx=1,bsy=1,bAlpha=1,hole=0,ddx=0,ddy=0,dsl=1,dAlpha=1,trail=[],cover=0,cupOpen=0,cupShut=0,ringBoth=0;
 const lift=sm(T(1.15),T(1.4),tt);
 const vcx=vb.x+vb.w/2,vbot=vb.y+vb.h;
 const dRight=m.A.x+m.A.w;
 if(mode==='hide'){
  cupOpen=sm(T(1.2),T(1.45),tt)-sm(T(2.35),T(2.6),tt);cupShut=sm(T(2.35),T(2.6),tt);
  const u=sm(T(1.4),T(2.35),tt);const tx=CUP.x+CUP.w/2,sx=Math.min(1,(CUP.w-40)/vb.w),sy=Math.min(1,(CUP.h-30)/vb.h);
  bdx=(tx-vcx)*u;bdy=-10*lift*(1-u)+(CUP.y+CUP.h-6-vbot)*u*0;bsx=1+(sx-1)*sm(.55,1,u);bsy=1+(sy-1)*sm(.55,1,u);
  hole=lift;ddx=Math.min(bdx,CUP.x-18-dRight+Math.max(0,bdx-(CUP.x-18-dRight))*0);ddx=Math.max(0,Math.min(bdx,CUP.x-24-dRight));
  ddy=-Math.abs(Math.sin(u*Math.PI*5))*10*(1+.6*(pl.LA.weight||0))*(u>0&&u<1?1:0);
  const n=14;for(let i=0;i<n;i++){const x=vcx+(tx-vcx)*(i+.5)/n;if(vcx+bdx>x+20)trail.push([x+(hash(i*4.4)-.5)*30,FLOOR-2+(hash(i*2.2)-.5)*10,3+4*hash(i*7.7)])}
 }else if(mode==='erase'){
  hole=lift;bAlpha=1-sm(T(1.55),T(2.3),tt);bdy=-8*lift;
 }else if(mode==='flee'){
  const u=sm(T(1.35),T(2.7),tt);ddx=-(dRight+60)*u;ddy=-Math.abs(Math.sin(u*Math.PI*6))*8;
  const n=12;for(let i=0;i<n;i++){const x=m.A.x+m.A.w*.5-(m.A.x+m.A.w*.5+40)*(i+1)/n;if(m.A.x+m.A.w*.5+ddx<x-10)trail.push([x+(i%2?14:-14),FLOOR+2+(i%2?-4:4),4])}
 }else if(mode==='stay'){
  const up=sm(T(1.2),T(1.5),tt)-sm(T(1.85),T(2.25),tt);bdy=-120*up;hole=up;
  const u=sm(T(1.9),T(2.7),tt);ddx=Math.max(0,Math.min(70,vb.x-dRight+10))*u;dsl=1-.08*u;ringBoth=sm(T(2.3),T(2.8),tt);
 }else if(mode==='survive'){
  hole=lift*.9;
  if(pl.vHides){cupOpen=sm(T(1.7),T(1.9),tt)-.7*sm(T(2.6),T(2.9),tt);
   const u=sm(T(1.85),T(2.7),tt);const tx=CUP.x+CUP.w/2,sx=Math.min(1,(CUP.w-40)/vb.w),sy=Math.min(1,(CUP.h-30)/vb.h);
   bdx=(tx-vcx)*u;bdy=-10*lift-Math.abs(Math.sin(u*Math.PI*4))*14*(u>0&&u<1?1:0);bsx=1+(sx-1)*sm(.55,1,u);bsy=1+(sy-1)*sm(.55,1,u);
   const n=12;for(let i=0;i<n;i++){const x=vcx+(tx-vcx)*(i+.5)/n;if(vcx+bdx>x+20)trail.push([x+(hash(i*5.4)-.5)*26,FLOOR-2+(hash(i*3.2)-.5)*10,3+4*hash(i*6.7)])}
  }else{const u=sm(T(1.8),T(2.5),tt);bsy=1+.45*u;bsx=1-.08*u;bdx=-50*u;bdy=-6*lift}
  const fu=sm(T(1.9),T(2.6),tt);
  if(pl.dGuilt){ddx=Math.max(0,Math.min(260,(pl.vHides?CUP.x-40:vb.x-20)-dRight))*sm(T(2.3),T(3.1),tt);ddy=-Math.abs(Math.sin(sm(T(2.3),T(3.1),tt)*Math.PI*4))*8}
  else{ddx=-(60+(pl.vHides?0:60))*fu;dsl=1-.06*fu}
 }else if(mode==='cover'){
  for(let k=0;k<3;k++){const a=T(1.2+k*.17);bdx+=26*Math.sin(Math.PI*sm(a,a+.15,tt))}
  ddx=bdx*.5;cover=sm(T(1.95),T(2.4),tt);
 }
 // levers ramp in so the first frame matches the deed's last
 const rl=sm(.2,1.1,t),LA=pl.LA,LV=pl.LV;
 const dscale=(1+.12*(LA.loom||0)*rl)*(mode==='survive'&&!pl.dGuilt?1-.12*sm(T(1.9),T(2.6),tt):1)*(1-.22*(found?sm(tF+.8,tF+1.3,t):0))*(1-.15*(LA.shrink||0)*rl);
 const vgrey=(st.alive[V]?.25:1)*Math.min(1,(LV.grey||0))*sm(.4,1.3,t),agrey=Math.min(1,LA.grey||0);
 if(pl.aDead)dAlpha=.55+.15*Math.sin(t*9);
 // ----- room
 try{DEEDS.knifing.draw(g,TS+Math.floor(t*12)/12,A,V,K,{layer:'bg',carry})}catch(e){g.drawImage(Pl.bg,0,0)}
 // police lamp in the window: a disappearance reaches the street
 if(pl.knock){const u=sm(2.4,3.4,t);if(u>0){g.save();g.beginPath();g.rect(WIN.x,WIN.y,WIN.w,WIN.h);g.clip();const lx=WIN.x-80+(WIN.w+160)*u,rg=g.createRadialGradient(lx,WIN.y+150,4,lx,WIN.y+150,95);rg.addColorStop(0,'rgba(225,236,255,.75)');rg.addColorStop(1,'rgba(210,225,255,0)');g.fillStyle=rg;g.fillRect(WIN.x,WIN.y,WIN.w,WIN.h);g.restore();
  g.save();g.globalAlpha=.07*Math.sin(Math.PI*u);g.fillStyle='#dfe8ff';g.beginPath();g.moveTo(WIN.x,WIN.y+WIN.h);g.lineTo(WIN.x+WIN.w,WIN.y+WIN.h);g.lineTo(lx+140,FLOOR-40);g.lineTo(lx-60,FLOOR-40);g.closePath();g.fill();g.restore()}}
 // the witness in the back door
 if(found){const u=sm(tF-.25,tF+.15,t);if(u>0){g.save();const dg=g.createLinearGradient(0,DOOR.y,0,DOOR.y+DOOR.h);dg.addColorStop(0,'#3a3026');dg.addColorStop(1,'#7a6448');g.fillStyle=dg;g.fillRect(DOOR.x,DOOR.y,DOOR.w*u,DOOR.h);
  g.beginPath();g.rect(DOOR.x,DOOR.y,DOOR.w,DOOR.h);g.clip();const wp=wpiece(found,K),s=Math.min(.5,(DOOR.h-30)/wp.height);
  const lw=pl.LW||{};const ws=s*(1+.1*(lw.loom||0));g.globalAlpha=u;g.drawImage(wp,DOOR.x+DOOR.w/2-wp.width*ws/2,DOOR.y+DOOR.h-wp.height*ws+4,wp.width*ws,wp.height*ws);g.restore();
  g.save();g.globalAlpha=.16*u;g.fillStyle='#ffe2b0';g.beginPath();g.moveTo(DOOR.x,668);g.lineTo(DOOR.x+DOOR.w,668);g.lineTo(DOOR.x+DOOR.w+160,FLOOR+60);g.lineTo(DOOR.x-260,FLOOR+60);g.closePath();g.fill();g.restore()}}
 // doer's shadow on the wall (shadow lever: PREDATOR lengthens it)
 const dcx=m.A.x+m.A.w/2+ddx,shL=(LA.shadow||0)*rl;
 if(shL>.02&&dAlpha>.6){g.save();g.globalAlpha=Math.min(.42,.1+.28*shL);const k=1.2+1.0*shL,hgt=Math.min(560,m.A.h*k*dscale),wd=m.A.w*(1.05+.3*shL)*dscale,away=(dcx-960)*(.12+.3*shL);
  g.translate(dcx+ddx*0,m.A.y+m.A.h+ddy-6);g.transform(1,0,away/hgt,1,0,0);g.drawImage(Pl.dmask,-wd/2,-hgt,wd,hgt);g.restore()}
 if(mode==='hide'||mode==='survive')cupboard(g,t,cupOpen,K);else cupboard(g,t,0,K);
 // ----- victim pieces
 const rx=Pl.rx,ry=Pl.ry;
 if(hole>0){g.save();g.globalAlpha=hole;g.drawImage(Pl.hole,rx,ry);g.restore()}
 g.drawImage(Pl.cv.shade,rx,ry); // the shared shadow is ground, not figure: it stays
 // flour: the island that will not segment
 let flA=1;if(mode==='erase')flA=1-.9*sm(T(2.0),T(2.7),tt);
 g.save();g.globalAlpha=flA;g.drawImage(Pl.cv.flour,rx,ry);g.restore();
 for(const d of trail)flourDot(g,d[0],d[1],d[2],mode==='erase'?.3:1);
 // the wig is an accessory: it is not the body, so it stays where it fell
 g.drawImage(Pl.cv.wig,rx,ry);
 // body piece (transformed about its bottom centre)
 const drawBody=()=>{if(bAlpha<=0)return;g.save();g.translate(vcx+bdx,vbot+bdy);g.scale(bsx,bsy);g.translate(-vcx,-vbot);
  if(mode==='erase'){const mt=sm(T(1.4),T(1.6),tt)*bAlpha;g.globalAlpha=bAlpha;g.drawImage(Pl.cv.body,rx,ry);g.globalAlpha=mt*.9;g.drawImage(Pl.matte,rx,ry)}
  else{g.drawImage(Pl.cv.body,rx,ry);if(vgrey>0){g.globalAlpha=vgrey;g.drawImage(Pl.grey,rx,ry)}
   if(mode==='survive'){const su=sm(T(1.3),T(1.75),tt);if(su>0){g.globalAlpha=1;g.strokeStyle='#3a2a1e';g.lineWidth=5;g.beginPath();const n=Math.floor(10*su);const y0=vb.y+vb.h*.55;for(let i=0;i<=n;i++){const x=vb.x+vb.w*(.25+.5*i/10);g.moveTo(x-9,y0-16);g.lineTo(x+9,y0+16)}g.stroke();g.beginPath();g.moveTo(vb.x+vb.w*.28,y0);g.lineTo(vb.x+vb.w*(.28+.44*su),y0);g.lineWidth=1.5;g.stroke()}}
   const mf=(mode==='void'||mode==='flee')?0:sm(T(.98),T(1.04),tt)*(1-sm(T(1.08),T(1.3),tt));if(mf>0){g.globalAlpha=mf*.8;g.drawImage(Pl.matte,rx,ry)}}
  g.restore()};
 if(mode==='hide'){ // inside the cupboard it is drawn in the dark, and the panel closes over it
  g.save();drawBody();g.restore();
  if(sm(T(1.4),T(2.35),tt)>.6){g.save();g.beginPath();g.rect(CUP.x+8,CUP.y+8,CUP.w-16,CUP.h-12);g.clip();g.globalAlpha=.55;g.fillStyle='#000';g.fillRect(CUP.x,CUP.y,CUP.w,CUP.h);g.restore()}
  if(cupShut>0){g.save();g.beginPath();g.rect(CUP.x,CUP.y,CUP.w,CUP.h);g.clip();cupboard(g,t,1-cupShut,K);g.restore()}
 }else if(mode==='survive'&&pl.vHides){drawBody();const v=sm(T(1.85),T(2.7),tt);if(v>.6){g.save();g.beginPath();g.rect(CUP.x+8,CUP.y+8,CUP.w-16,CUP.h-12);g.clip();g.globalAlpha=.6;g.fillStyle='#000';g.fillRect(CUP.x,CUP.y,CUP.w,CUP.h);g.restore()}
  const sh=.7*sm(T(2.6),T(2.9),tt);if(sh>0){g.save();g.beginPath();g.rect(CUP.x,CUP.y,CUP.w,CUP.h);g.clip();cupboard(g,t,cupOpen,K);g.restore()}}
 else drawBody();
 // cover: a patch cut from the wall is laid over the body (the world pasted over the figure)
 if(mode==='cover'&&cover>0){const pw=vb.w+70,ph=vb.h+40,sxw=vcx-pw/2,syw=360;const seedU=sm(T(1.7),T(1.95),tt);
  seedBox(g,{x:sxw,y:syw,w:pw,h:ph},seedU*(1-cover),SEEDC[A],t,0);
  const y=syw+(vb.y-20-syw)*cover;g.save();g.drawImage(Pl.bg,sxw,syw,pw,ph,vcx-pw/2+bdx,y,pw,ph);g.restore();
  g.save();g.fillStyle='rgba(0,0,0,.35)';g.fillRect(sxw,syw,pw,ph);g.restore(); // the hole it left in the wall
  if(cover>.95){g.save();g.strokeStyle=FAIL;g.lineWidth=3;g.setLineDash([10,7]);g.lineDashOffset=t*30;g.strokeRect(vcx-pw/2+bdx,y,pw,ph);g.restore()}}
 // ----- segmentation operator marks over the victim
 const seedU=sm(T(.3),T(.75),tt);const sb=Pl.seed;
 const boxU=mode==='flee'?Math.min(.62,seedU):seedU;
 const boxA=1-sm(T(1.3),T(1.6),tt)*(mode==='flee'||mode==='void'?0:1);
 if(boxA>0){g.save();g.globalAlpha=boxA;seedBox(g,sb,boxU,mode==='void'&&t>T(1.1)?(Math.floor(t*6)%2?FAIL:SEEDC[A]):SEEDC[mode==='survive'?V:A],t,mode==='flee'?10:0);g.restore()}
 // foreground scribble seed (red) on the body
 const fs=sm(T(.55),T(.8),tt)*(1-sm(T(1.3),T(1.6),tt));if(fs>0&&mode!=='flee'&&mode!=='void'){g.save();g.globalAlpha=fs;g.strokeStyle=FG;g.lineWidth=6;g.lineCap='round';g.beginPath();
  for(let i=0;i<=16;i++){const u=i/16;const x=vb.x+vb.w*(.25+.5*u),y=vb.y+vb.h*(.55+.12*Math.sin(u*12));i?g.lineTo(x,y):g.moveTo(x,y)}g.stroke();g.restore()}
 // lattice: unary labels, pairwise edges, and the cut
 const la=sm(T(.55),T(.75),tt)*(1-sm(T(1.25),T(1.55),tt));
 if(la>0){g.save();const cut=sm(T(1.0),T(1.08),tt);const N=Pl.nodes,C=Pl.cols;
  for(let i=0;i<N.length;i++){const a=N[i];const lab=q=>{const on=tt>T(.6+q.h*.35);if(mode==='void')return on?0:-1;if(mode==='flee'&&q.h>.4)return -1;if(q.fl)return on?(Math.floor(t*14+q.h*9)%2):-1;return on?(q.fg?1:0):-1};
   const la_=lab(a);for(const j of[i+1,i+C]){if(j>=N.length||(j===i+1&&(i+1)%C===0))continue;const b=N[j],lb=lab(b);const across=la_>=0&&lb>=0&&la_!==lb;
    if(across&&cut>0){g.globalAlpha=la*(1-cut);g.strokeStyle='#fff';g.lineWidth=3}else{g.globalAlpha=la*.45;g.strokeStyle='#c8c0b0';g.lineWidth=1.2}
    if(across&&cut>=1)continue;g.beginPath();g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.stroke()}
   g.globalAlpha=la;g.fillStyle=la_<0?'#9a948a':la_?FG:BGS;g.beginPath();g.arc(a.x,a.y,la_<0?3:5.5,0,6.283);g.fill()}
  g.restore()}
 // the cut contour round the extracted body (marching ants)
 const ra=(mode==='void'||mode==='flee')?0:sm(T(1.0),T(1.15),tt)*(mode==='erase'?bAlpha:1)*(mode==='hide'?1-cupShut:1)*(mode==='cover'?1-cover:1);
 if(ra>0){g.save();g.translate(vcx+bdx,vbot+bdy);g.scale(bsx,bsy);g.translate(-vcx,-vbot);ants(g,Pl.bring,rx-0,ry-0,1,1,t,ringBoth>0?FG:'#111',ra*(.6+.4*(1-ringBoth))+0);g.restore();
  if(ringBoth>0)ants(g,Pl.bring,rx,ry+bdy,1,1,t,FG,ringBoth)}
 // erase: the blue background seeds scrub the clean plate back over the hole and the flour
 if(mode==='erase'){const fb=Pl.fb||vb;const x0=Math.min(vb.x,fb.x)-20,x1=Math.max(vb.x+vb.w,fb.x+fb.w)+20,y0=vb.y-20,y1=Math.max(vbot,fb.y+fb.h)+16;
  scrub(g,Pl,[zig(x0,y0,x1,y1,7,40,11)],sm(T(1.6),T(2.75),tt),t)}
 if(mode==='hide'&&!found){scrub(g,Pl,[zig(vb.x-10,vb.y-10,vb.x+vb.w+10,vbot+6,5,44,23)],sm(T(2.55),T(3.05),tt),t)}
 // survive: the doer boxes the knife and slides it behind itself (the tip still shows)
 if(mode==='survive'){const kx0=dRight-60,ku0=0,ky0=FLOOR+40,ku=sm(T(.75),T(1.15),tt),kx=kx0+(m.A.x+m.A.w*.74-kx0)*ku+ddx*ku,ky=ky0+(FLOOR-14-ky0)*ku;
  const kb={x:kx0-18,y:ky0-30,w:220,h:54};seedBox(g,kb,sm(T(.3),T(.6),tt)*(1-sm(T(.8),T(1.0),tt)),SEEDC[A],t,0);
  g.save();g.translate(kx,ky-10*Math.sin(Math.PI*ku));g.fillStyle='#2a1f18';g.fillRect(0,-8,56,16);g.fillStyle='#b9c2cc';g.strokeStyle='#0d0b09';g.lineWidth=3;g.beginPath();g.moveTo(56,-10);g.lineTo(176,-2);g.lineTo(184,3);g.lineTo(56,9);g.closePath();g.fill();g.stroke();g.restore();
  pl._knife=[kx+150,ky]}
 // ----- the doer piece
 g.save();g.globalAlpha=dAlpha;const dbx=m.A.x+m.A.w/2,dby=m.A.y+m.A.h;g.translate(dbx+ddx,dby+ddy);g.scale(dscale,dscale*dsl);g.translate(-dbx,-dby);
 g.drawImage(Pl.dc,Pl.ax,Pl.ay);if(agrey>0){g.globalAlpha=dAlpha*agrey;g.drawImage(Pl.dgrey,Pl.ax,Pl.ay)}
 // halo lever: the lamp finds the doer
 if((LA.halo||0)>.05){g.globalCompositeOperation='lighter';const rg=g.createRadialGradient(dbx,m.A.y+m.A.h*.4,10,dbx,m.A.y+m.A.h*.4,m.A.h*.9);rg.addColorStop(0,`rgba(255,220,170,${.22*LA.halo*rl})`);rg.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=rg;g.fillRect(m.A.x-200,m.A.y-200,m.A.w+400,m.A.h+400)}
 g.restore();
 if(ringBoth>0){g.save();const dbx2=dbx+ddx;g.translate(dbx2,dby);g.scale(dscale,dscale*dsl);g.translate(-dbx,-dby);ants(g,Pl.dring,Pl.ax,Pl.ay,1,1,t,FG,ringBoth);g.restore()}
 // R counts (pride): three small bows after the door shuts
 // found: the witness draws its own box seed round the doer: the doer becomes the extracted figure
 if(found){const u=sm(tF+.2,tF+.7,t);const db={x:m.A.x+ddx-30,y:m.A.y-30,w:m.A.w*dscale+60,h:m.A.h*dscale+50};db.y=dby-db.h+18;db.x=dbx+ddx-db.w/2;seedBox(g,db,u,SEEDC[found],t,0);
  if(t>tF+.7){g.save();g.translate(dbx+ddx,dby+ddy);g.scale(dscale,dscale*dsl);g.translate(-dbx,-dby);ants(g,Pl.dring,Pl.ax,Pl.ay,1,1,t,FAIL,sm(tF+.7,tF+.9,t));g.restore()}}
 // ----- failure masks: the evidence the cut could not take
 const fa=sm(T(2.6),T(3.0),t);
 if(fa>0&&mode!=='void'){let i=0;const fb=Pl.fb;
  if(fb&&mode!=='erase')failMask(g,fb.x+fb.w/2,fb.y+fb.h/2+4,fb.w/2+18,Math.max(18,fb.h/2+12),t,fa,i++);
  if(mode==='erase'){const ix=(fb?fb.x+fb.w*.3:vb.x),iy=FLOOR+4;flourDot(g,ix,iy,6,1);failMask(g,ix,iy,30,16,t,fa,i++)}
  if(Pl.wb)failMask(g,Pl.wb.x+Pl.wb.w/2,Pl.wb.y+Pl.wb.h/2,Pl.wb.w/2+16,Pl.wb.h/2+12,t,fa,i++);
  if(mode==='survive'&&pl._knife&&!pl.dGuilt)failMask(g,pl._knife[0]+ddx*0,pl._knife[1],34,14,t,fa,i++);
  for(let k=0;k<trail.length;k+=3)failMask(g,trail[k][0],trail[k][1],22,12,t,fa*.9,i++)}
 if(mode==='void'){const u=sm(T(1.2),T(1.8),t);if(u>0){g.save();g.globalAlpha=u;g.strokeStyle=FAIL;g.lineWidth=5;g.beginPath();g.moveTo(sb.x,sb.y);g.lineTo(sb.x+sb.w,sb.y+sb.h);g.moveTo(sb.x+sb.w,sb.y);g.lineTo(sb.x,sb.y+sb.h);g.globalAlpha=u*.6;g.stroke();g.restore()}}
}

// ---------- sound: grains for every operator move
function sound(ac,out0,t0,ev,st,K){const out=ac.createGain();out.gain.value=1.6;out.connect(out0);const S=K.SND,pl=plan(ev,st),sp=pl.tempo,T=x=>t0+x*sp,A=ev.A,V=ev.V,mode=pl.mode;
 const pan=x=>Math.max(-1,Math.min(1,x/960-1));const pA=pan(560),pV=pan(1400);const found=pl.witness,tF=sp*{hide:2.05,erase:2.0,flee:2.0,stay:2.35,cover:2.45,void:2.0,survive:2.4}[mode];
 const live=x=>!found||x-t0<=tF+.05;
 // box seed: four corner clicks
 for(let i=0;i<(mode==='flee'?2:4);i++)S.grain(ac,out,T(.3+i*.11),{f:2200+i*180,d:.012,a:.12,pan:pV,att:.05});
 // lattice labelling: a cloud of tiny ticks, pitched by label (fg high, bg low)
 S.cloud(ac,out,T(.6),.4*sp,90,{pitches:mode==='void'?[60,62]:[60,62,79,81],a:.05,d:[.006,.02],spread:.5},u=>Math.sin(Math.PI*u));
 // the cut: a dry rip along the boundary (strongest sound)
 if(mode!=='void'&&mode!=='flee'){S.cloud(ac,out,T(1.0),.1,260,{bp:3400,q:2,a:.34,d:[.004,.014],spread:.3,noise:1},u=>1-u*.5);S.grain(ac,out,T(1.0),{f:1600,glide:-.5,d:.08,a:.4,pan:pV,att:.05});S.thump(ac,out,T(1.02),.5,80,pV);S.say(ac,out,V,T(1.06),'land',.45,pV)}
 if(mode==='void'){for(let i=0;i<3;i++)S.grain(ac,out,T(1.2+i*.16),{f:220,d:.07,a:.3,pan:pV,type:'square',att:.1})}
 // lift
 if(mode!=='void'&&mode!=='flee')S.say(ac,out,A,T(1.18),'breathe',.4,pA);
 if(mode==='hide'){S.grain(ac,out,T(1.25),{f:180,glide:.6,d:.25,a:.08,pan:pan(1790),noise:.6,bp:900});
  for(let i=0;i<5;i++){const w=T(1.45+i*.18);if(live(w))S.say(ac,out,A,w,'step',.9+.3*(pl.LA.weight||0),pan(700+i*180))}
  S.cloud(ac,out,T(1.45),.9*sp,50,{bp:800,a:.03,d:[.04,.1],noise:1,spread:.6},u=>1);
  if(!found){S.thump(ac,out,T(2.55),.8,70,pan(1790));for(let i=0;i<3;i++)S.say(ac,out,'R',T(2.75+i*.16),'tick',.8,pan(1600))}}
 if(mode==='erase'){S.cloud(ac,out,T(1.6),1.1*sp,70,{bp:5200,q:1,a:.035,d:[.03,.08],noise:1,spread:.4},u=>1);S.say(ac,out,'O',T(2.75),'tick',.6,pA)}
 if(mode==='flee'){for(let i=0;i<7;i++){const w=T(1.4+i*.18);if(live(w))S.say(ac,out,A,w,'step',.7,pan(500-i*90))}S.say(ac,out,'I',T(1.3),'breathe',.6,pA)}
 if(mode==='stay'){S.say(ac,out,'B',T(1.55),'breathe',.8,pA);S.say(ac,out,'B',T(2.12),'land',.6,pV);S.say(ac,out,'B',T(2.45),'sink',.8,pA)}
 if(mode==='survive'){S.grain(ac,out,T(.78),{f:3200,glide:-.3,d:.3,a:.06,pan:pA,noise:.4,bp:4000});S.say(ac,out,A,T(1.15),'tick',.6,pA);
  for(let i=0;i<12;i++)S.grain(ac,out,T(1.3+i*.037),{bp:2500,d:.015,a:.08,pan:pV,att:.1});
  if(pl.vHides){for(let i=0;i<5;i++)S.say(ac,out,V,T(1.9+i*.17),'step',.8,pan(1400+i*80));S.grain(ac,out,T(1.75),{f:160,glide:.5,d:.25,a:.08,pan:pan(1790),noise:.6,bp:900});S.grain(ac,out,T(2.7),{f:200,glide:-.3,d:.2,a:.07,pan:pan(1790),noise:.6,bp:900})}else S.say(ac,out,'B',T(1.9),'land',.7,pV);
  if(pl.dGuilt)S.say(ac,out,A,T(2.4),'sink',.8,pA);else{S.say(ac,out,A,T(1.95),'react',.5,pA);S.say(ac,out,A,T(2.2),'breathe',.6,pA)}}
 if(mode==='cover'){for(let k=0;k<3;k++){S.say(ac,out,A,T(1.27+k*.3),'step',1,pA);S.thump(ac,out,T(1.4+k*.3),.25,90,pV)}S.cloud(ac,out,T(2.2),.5*sp,60,{bp:400,a:.04,d:[.05,.12],noise:1},u=>1-u)}
 if(mode==='hide'&&!found)S.cloud(ac,out,T(2.55),.45,40,{bp:6000,a:.02,d:[.03,.07],noise:1},u=>1); // the sweep
 if(found){S.grain(ac,out,t0+tF-.2,{f:90,glide:.3,d:.4,a:.1,pan:pan(1640),noise:.5,bp:500});S.say(ac,out,found,t0+tF+.1,'react',.8,pan(1640));S.say(ac,out,A,t0+tF+.75,'sink',.7,pA)}
 if(pl.knock){for(let i=0;i<3;i++)S.thump(ac,out,t0+2.6+i*.17,.3,110,pan(320))}
 // failure masks: a soft glass ping per island left behind
 if(mode!=='void')for(let i=0;i<3;i++)S.pluck(ac,out,T(2.65+i*.12),84+i*3,.035,.4,pV)}

// ---------- trace: a flour island with its red failure contour, aging into a stain
function trace(g,box,age,K){const a=Math.exp(-age*.22),cx=box.x+box.w/2,cy=box.y+box.h*.62;
 g.save();g.globalAlpha=.85*a+.15;g.fillStyle='#fbf7ee';g.beginPath();for(let k=0;k<=18;k++){const an=k/18*6.283,r=.36+.1*hash(k*3.7);const x=cx+Math.cos(an)*box.w*r,y=cy+Math.sin(an)*box.h*r*.4;k?g.lineTo(x,y):g.moveTo(x,y)}g.closePath();g.fill();
 g.globalAlpha=a;g.strokeStyle=FAIL;g.lineWidth=Math.max(1.5,box.w/60);g.setLineDash([box.w/14,box.w/18*(1+age*.3)]);g.beginPath();g.ellipse(cx,cy,box.w*.46,box.h*.24,0,0,6.283);g.stroke();
 // the hole's checker corner, smaller each time
 const s=Math.max(3,box.w/14)*(1/(1+age*.3));g.globalAlpha=.6*a;for(let y=0;y<2;y++)for(let x=0;x<2;x++){g.fillStyle=(x+y)&1?'#8d8d8d':'#5e5e5e';g.fillRect(box.x+box.w*.08+x*s,box.y+box.h*.1+y*s,s,s)}g.restore()}

CONSEQ({deed:'knifing',n:4,scion:29,lineage:'GrabCut — Cutout Extraction Swarm',
 op:'The deed\'s last frame is segmented: a box seed and red/blue scribbles label a node lattice, the boundary edges are cut, and the body is lifted out as an RGBA piece leaving a transparent hole; the flour will not separate and is left marked by failure masks.',
 made:'The knifing shot\'s own end frame, split by colour into typed RGBA pieces: the body, the flour (the island that will not segment), the wig as an accessory, and the doer\'s cutout; the hole the body leaves is a checkerboard of transparency. Over it sit the operator\'s marks: dashed box seeds, red foreground and blue background scribbles, a labelled node lattice, marching-ants contours and red dashed failure masks.',
 moved:'The ledger picks the branch: a surviving victim cuts itself out, stitches its seam and slides along a flour trail into the cupboard while the doer boxes the knife and slides it behind itself and shrinks; a dead victim leaves the doer to hide it in the cupboard, scrub it out of the plate, flee, put it back, paste a patch of wall over it, or fail because the body was already dead; and a third sack with history may open the back door and box the doer instead. Doer levers (loom, shadow, tempo, weight, halo, shrink) scale, time and light the cutout; the victim\'s grey lever drains the body piece.',
 dur:DUR,beat,sound,trace});
})();
