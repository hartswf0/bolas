// B · BELINDO KID — memory in the body. SCION-LINEAR-SKINNING (lineage 37, Weighted Skinning).
// Belindo's cloth is ONE mesh bound to a six-bone rig by normalised vertex weights (linear blend skinning).
// Every memory is a texture: a crop of the remembered shot, transformed by the feeling, bound to the mesh
// region where the deed touched him (a region mask), so it rides the cloth like a bruise or a tattoo and
// never swims. Heavy memories add corrective deformation where they sit (guilt drags the cloth down).
// Others' stories (witness memories) arrive as stencil transfers and are skinned on him exactly like his own.
(function(){
'use strict';
const TAU=Math.PI*2;
const cl=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
const sm=(a,b,x)=>{const u=cl(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
const eo=(a,b,x)=>{const u=cl(0,1,(x-a)/(b-a));return 1-Math.pow(1-u,3)};
const sig=x=>1/(1+Math.exp(-x));
const H=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};
const CLOTH='#e8d5ae',BELT='#2a2622';
const ATTR={R:{w:168,h:122,fill:'#d6bf96',acc:'#6e3a33'},B:{w:244,h:214,fill:'#e8d5ae',acc:'#2a2622'},I:{w:128,h:98,fill:'#e2cea5',acc:'#b59c72'},O:{w:80,h:184,fill:'#f0e4c8',acc:'#7a3b8f'}};

// ======================= RIG: bind/rest matrices =======================
// 2D affine [a,b,c,d,e,f]: x' = a x + c y + e ; y' = b x + d y + f
const mul=(m,n)=>[m[0]*n[0]+m[2]*n[1],m[1]*n[0]+m[3]*n[1],m[0]*n[2]+m[2]*n[3],m[1]*n[2]+m[3]*n[3],m[0]*n[4]+m[2]*n[5]+m[4],m[1]*n[4]+m[3]*n[5]+m[5]];
const T=(x,y)=>[1,0,0,1,x,y],R=a=>{const c=Math.cos(a),s=Math.sin(a);return[c,s,-s,c,0,0]},S=(x,y)=>[x,0,0,y,0,0];
const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
// bones in rest space (unit body: width 1, height 1, base centre at origin, up = -y)
const BONES=[{p:-1,j:[0,0]},{p:0,j:[0,-.33]},{p:1,j:[0,-.66]},{p:2,j:[0,-1]},{p:3,j:[-.5,-1]},{p:3,j:[.5,-1]}];
const SPINE_V=[0,.33,.66,1];
// vertex-to-bone weights for a rest point (unit space) — normalised (invariant: sum = 1)
function weights(x,y){const v=-y,w=[0,0,0,0,0,0];let s=0;
 for(let i=0;i<4;i++){w[i]=Math.exp(-Math.pow((v-SPINE_V[i])/.2,2));s+=w[i]}
 for(let i=0;i<4;i++)w[i]/=s;
 // ear influence near the two top corners (the ears are his hands)
 const eL=Math.max(0,1-Math.hypot(x+.5,y+1)/.2)*.7,eR=Math.max(0,1-Math.hypot(x-.5,y+1)/.2)*.7,ek=1-eL-eR;
 for(let i=0;i<4;i++)w[i]*=ek;w[4]=eL;w[5]=eR;return w}
// pose: per bone {a, sx, sy}; returns skin matrices M_i * B_i^-1 in unit space
function skinMats(pose){const M=[],out=[];
 for(let i=0;i<BONES.length;i++){const b=BONES[i],pj=b.p<0?[0,0]:BONES[b.p].j,q=pose[i]||{};
  const local=mul(T(b.j[0]-pj[0],b.j[1]-pj[1]),mul(R(q.a||0),S(q.sx||1,q.sy||1)));
  M[i]=b.p<0?mul(T(0,0),local):mul(M[b.p],local);out[i]=mul(M[i],T(-b.j[0],-b.j[1]))}return out}
function lbs(mats,x,y,w){let X=0,Y=0;for(let i=0;i<6;i++){if(w[i]<1e-6)continue;const p=ap(mats[i],x,y);X+=w[i]*p[0];Y+=w[i]*p[1]}return[X,Y]}
// rest outline of the sack in uv: u,v in 0..1 -> unit rest point (bulges at the middle, full to bursting)
function rest(u,v){v=cl(0,1,v);const bul=(1+.13*Math.sin(Math.PI*Math.pow(v,.85)))*(v<.1?.86+.14*Math.sqrt(v/.1):1)*(v>.9?1-.06*(v-.9)/.1:1);
 const bot=v<.1?(1-v/.1)*.035*Math.sin(u*Math.PI):0;return[(u-.5)*bul,-v-.035*Math.sin(u*Math.PI)*Math.pow(v,6)+bot]}

// ======================= region masks: where a deed lands on his body =======================
// victim role: the place it was done to him; doer role: the ears/upper corners (his hands); witness: lower cloth (told to him)
const REGION_V={blackmail:[.72,.2],drugging:[.5,.86],incitement:[.5,.62],knifing:[.42,.27],prostitution:[.82,.5],gun:[.5,.66],tying:[.5,.4],assault:[.16,.52],seduction:[.34,.7],slander:[.58,.6],snooping:[.22,.82],strangling:[.5,.93]};
function region(m,i){
 if(m.role==='victim')return REGION_V[m.deed]||[.5,.5];
 if(m.role==='doer'){const L=(m.k%2===0);return[L?.24:.76,.8-.05*(i%2)]}
 return[[.3,.68,.5,.2,.8][i%5],.16+.04*(i%3)]}
// the dominant feeling of a memory, from the deed's rule and Belindo's temperament
function feeling(m){if(m.role==='witness')return'story';
 const r=LEDGER.RULE[m.deed],src=m.role==='doer'?r.mindA:r.mindV,T0=LEDGER.TEMPER.B;let best='fear',bv=-1;
 for(const k in src){const v=src[k]*(T0[k]??1);if(v>bv){bv=v;best=k}}
 if(bv<=0)return m.role==='doer'?'pride':'fear';return best}
const TINT={fear:['#2c2350','#d6cdf0'],guilt:['#2a1a10','#a07850'],grudge:['#3a0e0a','#d0745a'],desire:['#5a2235','#f4c3a8'],pride:['#4a3510','#f0d27a'],debt:['#2f3016','#c8b66a'],story:['#4e3420','#4e3420']};

// ======================= textures: the remembered still, cropped and transformed =======================
const TEX={};const KEEP={fear:.5,guilt:.45,grudge:.4,desire:.55,pride:.5,debt:.5,story:0};
function cropRect(m){let r=null;try{const D=window.DEEDS&&DEEDS[m.deed];if(D&&D.marks){const mk=D.marks(D.contact+.3,m.A,m.V,window.K);const a=mk.A,b=mk.V;const x0=Math.min(a.x,b.x),y0=Math.min(a.y,b.y),x1=Math.max(a.x+a.w,b.x+b.w),y1=Math.max(a.y+a.h,b.y+b.h);r=[x0,y0,x1-x0,y1-y0]}}catch(e){}
 if(!r||!isFinite(r[0]))r=[480,300,960,620];
 let[x,y,w,h]=r;const pad=50;x-=pad;y-=pad*1.6;w+=pad*2;h+=pad*2.4;const asp=1.35;if(w/h<asp){const nw=h*asp;x-=(nw-w)/2;w=nw}else{const nh=w/asp;y-=(nh-h)/2;h=nh}
 if(w>1900){w=1900;h=w/asp}x=cl(0,1920-w,x);y=cl(0,1080-h,y);return[x,y,w,h]}
function texture(m,feel){const ab=Math.min(6,m.ago|0);const key=m.deed+m.A+m.V+m.role+feel+ab;if(TEX[key])return TEX[key];
 const W=256,Hh=190,cv=document.createElement('canvas');cv.width=W;cv.height=Hh;const q=cv.getContext('2d');const[x,y,w,h]=cropRect(m);
 q.filter=ab>2?`blur(${Math.min(1.6,(ab-2)*.4)}px)`:'none';if(m.still)q.drawImage(m.still,x,y,w,h,0,0,W,Hh);q.filter='none';
 const id=q.getImageData(0,0,W,Hh),d=id.data,[c0,c1]=TINT[feel].map(hx=>[parseInt(hx.slice(1,3),16),parseInt(hx.slice(3,5),16),parseInt(hx.slice(5,7),16)]);
 const lum=new Float32Array(W*Hh);for(let i=0;i<W*Hh;i++)lum[i]=(d[i*4]*.3+d[i*4+1]*.59+d[i*4+2]*.11)/255;
 // contrast-stretch so a dark room still yields the sacks
 let lo=1,hi=0;for(let i=0;i<W*Hh;i+=7){lo=Math.min(lo,lum[i]);hi=Math.max(hi,lum[i])}const rg=Math.max(.05,hi-lo);
 for(let yy=0;yy<Hh;yy++)for(let xx=0;xx<W;xx++){const i=yy*W+xx;let L=cl(0,1,(lum[i]-lo)/rg);
  const ex=(xx/W-.5)*2,ey=(yy/Hh-.5)*2,rr=Math.hypot(ex,ey),edge=Math.max(Math.abs(ex),Math.abs(ey));let a=1;
  if(feel==='story'){ // stencil transfer: an ink outline of the scene, like the wheat on his front
   const Lr=lum[i+(xx<W-1?1:0)],Ld=lum[i+(yy<Hh-1?W:0)];const e=Math.abs(lum[i]-Lr)+Math.abs(lum[i]-Ld);const ink=e>.05*rg||L>.72;
   a=ink?.95:0;L=0;if(rr>1.05)a=0}
  else if(feel==='fear'){a=1-sm(.7,1.05,rr*.85+.15*edge);L=Math.pow(L,.8)}                  // bruise: soft, spreading
  else if(feel==='guilt'){a=(1-sm(.72,1,edge+.18*(H(xx*.13+yy*7.7)-.5)))*.96;L=Math.pow(L,.9)} // stain: ragged, soaked
  else if(feel==='grudge'){a=edge<.94?1:0;L=L>.45?1:L>.22?.5:0}                  // patch sewn on: hard, posterised
  else if(feel==='desire'){a=1-sm(.5,1,rr*rr*.9+.1);L=.35+.65*L}                  // warm, soft oval
  else{a=edge<.95?1:0}
  const kp=KEEP[feel]||0;for(let c=0;c<3;c++)d[i*4+c]=lerp(c0[c]+(c1[c]-c0[c])*L,cl(0,255,(d[i*4+c]-lo*255)/rg),kp);d[i*4+3]=255*a}
 q.putImageData(id,0,0);TEX[key]=cv;return cv}
let WHEAT=null;function wheat(){if(WHEAT)return WHEAT;const cv=document.createElement('canvas');cv.width=cv.height=200;const q=cv.getContext('2d');q.strokeStyle='#8a5a3a';q.lineWidth=7;q.lineCap='round';
 q.beginPath();q.arc(100,100,86,0,TAU);q.stroke();q.lineWidth=6;q.beginPath();q.moveTo(100,168);q.lineTo(100,40);q.stroke();
 for(let k=0;k<5;k++){const y=56+k*22;q.beginPath();q.ellipse(84,y+6,8,16,-.6,0,TAU);q.stroke();q.beginPath();q.ellipse(116,y+6,8,16,.6,0,TAU);q.stroke()}
 q.beginPath();q.ellipse(100,34,7,14,0,0,TAU);q.stroke();WHEAT=cv;return cv}

// affine texture triangle (src in texture px -> dst screen), slight dilation to hide seams
function tri(g,img,s0,s1,s2,d0,d1,d2){
 const cx=(d0[0]+d1[0]+d2[0])/3,cy=(d0[1]+d1[1]+d2[1])/3,ex=p=>[p[0]+(p[0]-cx)*.04,p[1]+(p[1]-cy)*.04];const e0=ex(d0),e1=ex(d1),e2=ex(d2);
 g.save();g.beginPath();g.moveTo(e0[0],e0[1]);g.lineTo(e1[0],e1[1]);g.lineTo(e2[0],e2[1]);g.closePath();g.clip();
 const x1=s1[0]-s0[0],y1=s1[1]-s0[1],x2=s2[0]-s0[0],y2=s2[1]-s0[1],den=x1*y2-x2*y1;if(Math.abs(den)<1e-9){g.restore();return}
 const X1=d1[0]-d0[0],Y1=d1[1]-d0[1],X2=d2[0]-d0[0],Y2=d2[1]-d0[1];
 const a=(X1*y2-X2*y1)/den,b=(Y1*y2-Y2*y1)/den,c=(X2*x1-X1*x2)/den,d=(Y2*x1-Y1*x2)/den;
 g.transform(a,b,c,d,d0[0]-a*s0[0]-c*s0[1],d0[1]-b*s0[0]-d*s0[1]);g.drawImage(img,0,0);g.restore()}

// ======================= the skinned body =======================
// P: {x,y,s (px per unit width), hs (height/width), pose, corr:[{u,v,feel,amp}], lie}
function makeBody(P){const mats=skinMats(P.pose);const hs=P.hs;
 const f=(u,v,raw)=>{const r=rest(u,v);let[x,y]=raw||r;const w=weights(x,y);let[X,Y]=lbs(mats,x,y,w);
  // corrective deformation: each heavy memory displaces the cloth where it sits
  for(const c of P.corr){const du=u-c.u,dv=v-c.v,k=Math.exp(-(du*du+dv*dv)/(.045)),a=c.amp*k;
   if(c.feel==='guilt'){Y+=.11*a;X-=du*.1*a}            // dragged down, gathers
   else if(c.feel==='fear'){X-=du*.07*a;Y+=dv*.08*a}     // pinched in, flinching from the spot
   else if(c.feel==='grudge'){X-=du*.18*a}               // clenched
   else if(c.feel==='desire'){X+=.03*a;Y-=.02*a}          // swells toward
   else if(c.feel==='debt'){Y+=.045*a}}
  const sx=X*P.s,sy=Y*P.s*hs;if(P.lie){const c=Math.cos(P.lie),s=Math.sin(P.lie);return[P.x+sx*c-sy*s,P.y+sx*s+sy*c]}return[P.x+sx,P.y+sy]};
 return{f,mats}}
function earPts(B,side,P){ // ear: base on the top corner (blended), tip fully on the ear bone
 const m=B.mats[side<0?4:5];const cx=.5*side,base=[[cx-.13*side,-1],[cx,-1],[cx,-.9]];const tip=[cx+.12*side,-1.2];
 const toS=([x,y])=>{let sx=x*P.s,sy=y*P.s*P.hs;if(P.lie){const c=Math.cos(P.lie),s=Math.sin(P.lie);return[P.x+sx*c-sy*s,P.y+sx*s+sy*c]}return[P.x+sx,P.y+sy]};
 const pts=base.map(p=>{const w=weights(p[0],p[1]);return toS(lbs(B.mats,p[0],p[1],w))});const t=ap(m,tip[0],tip[1]);const mid=ap(m,cx+.06*side,-1.12);
 return[pts[0],toS(mid),toS(t),pts[2]]}

const NU=12,NV=12;
function drawSack(g,P,mems,tm,opt){const B=makeBody(P);const f=B.f;
 const grid=[];for(let j=0;j<=NV;j++){grid[j]=[];for(let i=0;i<=NU;i++)grid[j][i]=f(i/NU,j/NV)}
 const restA=1/(NU*NV);
 // body fill, shaded per quad by its stretch (area ratio vs rest): compression darkens, stretch lightens
 g.save();
 const outline=[];for(let i=0;i<=NU;i++)outline.push(grid[0][i]);for(let j=1;j<=NV;j++)outline.push(grid[j][NU]);for(let i=NU-1;i>=0;i--)outline.push(grid[NV][i]);for(let j=NV-1;j>0;j--)outline.push(grid[j][0]);
 const poly=(ps)=>{g.beginPath();g.moveTo(ps[0][0],ps[0][1]);for(const p of ps)g.lineTo(p[0],p[1]);g.closePath()};
 // ears behind
 for(const sd of[-1,1]){const e=earPts(B,sd,P);poly(e);g.fillStyle='#d8c398';g.fill();g.strokeStyle='rgba(60,40,20,.5)';g.lineWidth=2;g.stroke()}
 poly(outline);g.fillStyle=CLOTH;g.fill();
 g.save();poly(outline);g.clip();
 for(let j=0;j<NV;j++)for(let i=0;i<NU;i++){const a=grid[j][i],b=grid[j][i+1],c=grid[j+1][i+1],d=grid[j+1][i];
  const ar=Math.abs((b[0]-a[0])*(d[1]-a[1])-(d[0]-a[0])*(b[1]-a[1]))/(P.s*P.s*P.hs)/restA;const sh=cl(-.25,.25,(ar-1)*1.6);
  if(Math.abs(sh)<.015)continue;g.fillStyle=sh>0?`rgba(255,250,235,${sh*.5})`:`rgba(60,40,20,${-sh*.7})`;g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.lineTo(c[0],c[1]);g.lineTo(d[0],d[1]);g.closePath();g.fill()}
 {const tp=f(.5,1),bt=f(.5,0);const gr=g.createLinearGradient(tp[0],tp[1],bt[0],bt[1]);gr.addColorStop(0,'rgba(255,248,230,.12)');gr.addColorStop(.6,'rgba(40,25,10,0)');gr.addColorStop(1,'rgba(40,25,10,.22)');g.fillStyle=gr;poly(outline);g.fill()}
 // the weave: the mesh itself, drawn as thread
 g.strokeStyle='rgba(120,90,50,.18)';g.lineWidth=1.2;
 for(let j=1;j<NV;j++){g.beginPath();for(let i=0;i<=NU;i++){const p=grid[j][i];i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()}
 for(let i=1;i<NU;i++){g.beginPath();for(let j=0;j<=NV;j++){const p=grid[j][i];j?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()}
 // the printed ornament (wheat stencil), skinned — held intact through every pose
 skinPatch(g,f,wheat(),.5,.64,.34,.34*1.14,1,0);
 // memory patches, each bound to its region
 for(const pm of tm)if(pm.fly>=1)drawPatch(g,f,pm,P);
 // belt at 40%
 const bt=[],bb=[];for(let i=0;i<=NU;i++){bt.push(f(i/NU,.43));bb.push(f(i/NU,.37))}poly(bt.concat(bb.reverse()));g.fillStyle=BELT;g.fill();
 g.restore();
 // seam outline
 // grey lever: colour leaves the cloth (saturation composite over the skinned body, cheap)
 if(opt.grey>.02){g.save();g.globalCompositeOperation='saturation';g.globalAlpha=cl(0,1,opt.grey*.95);g.fillStyle='#808080';poly(outline);g.fill();for(const sd of[-1,1]){poly(earPts(B,sd,P));g.fill()}g.globalCompositeOperation='source-over';g.globalAlpha=opt.grey*.3;g.fillStyle='#1a1a1c';poly(outline);g.fill();g.restore()}
 poly(outline);g.strokeStyle='rgba(70,48,25,.75)';g.lineWidth=2.5;g.stroke();
 g.restore();
 return{f,grid,B}}
// a texture bound to the mesh at (uc,vc) with uv size du,dv; fly in [0..1]: 0 = flat card at P.card, 1 = skinned
function skinPatch(g,f,img,uc,vc,du,dv,alpha,rot,card,fly,nn){const n=nn||3,W=img.width,Hh=img.height;const pts=[];
 for(let j=0;j<=n;j++){pts[j]=[];for(let i=0;i<=n;i++){const a=i/n-.5,b=j/n-.5;const ru=a*du*Math.cos(rot)-b*dv*Math.sin(rot),rv=a*du*Math.sin(rot)+b*dv*Math.cos(rot);
  let p=f(uc+ru,vc-rv);if(card&&fly<1){const q=[card.x+(i/n)*card.w,card.y+(j/n)*card.h];const k=fly;p=[lerp(q[0],p[0],k),lerp(q[1],p[1],k)]}pts[j][i]=p}}
 g.save();g.globalAlpha=alpha;
 for(let j=0;j<n;j++)for(let i=0;i<n;i++){const s=(i2,j2)=>[i2/n*W,j2/n*Hh];
  tri(g,img,s(i,j),s(i+1,j),s(i+1,j+1),pts[j][i],pts[j][i+1],pts[j+1][i+1]);tri(g,img,s(i,j),s(i+1,j+1),s(i,j+1),pts[j][i],pts[j+1][i+1],pts[j+1][i])}
 g.restore();return pts}
function drawPatch(g,f,pm,P){if(pm.show<=.001)return;
 const{uc,vc,du,dv,feel,img}=pm;
 // halo on the cloth around the memory (bruise spreading, stain running down, glow)
 const c=f(uc,vc),rr=du*P.s*.75*(.6+.4*pm.show);
 if(feel==='fear'){const gr=g.createRadialGradient(c[0],c[1],rr*.3,c[0],c[1],rr*1.25);gr.addColorStop(0,'rgba(80,60,130,.35)');gr.addColorStop(.7,'rgba(150,140,60,.18)');gr.addColorStop(1,'rgba(150,140,60,0)');g.fillStyle=gr;g.globalAlpha=pm.alpha*pm.show;g.fillRect(c[0]-rr*1.3,c[1]-rr*1.3,rr*2.6,rr*2.6);g.globalAlpha=1}
 if(feel==='guilt'){ // the stain runs downward: heavy
  g.save();g.globalAlpha=pm.alpha*pm.show*.4;g.strokeStyle='#5a3a20';g.lineCap='round';for(let k=0;k<4;k++){const u=uc+(k/3-.5)*du*.7;const len=dv*(.5+.7*H(k+pm.k*3.1))*pm.show;const p0=f(u,vc-dv*.35);g.lineWidth=2+3*H(k*2.3+pm.k);g.beginPath();g.moveTo(p0[0],p0[1]);for(let s=1;s<=6;s++){const p=f(u,vc-dv*.35-len*s/6);g.lineTo(p[0],p[1])}g.stroke()}g.restore()}
 if(feel==='desire'){const gr=g.createRadialGradient(c[0],c[1],0,c[0],c[1],rr*1.4);gr.addColorStop(0,'rgba(255,200,170,.45)');gr.addColorStop(1,'rgba(255,200,170,0)');g.globalCompositeOperation='lighter';g.globalAlpha=pm.alpha*pm.show;g.fillStyle=gr;g.fillRect(c[0]-rr*1.5,c[1]-rr*1.5,rr*3,rr*3);g.globalAlpha=1;g.globalCompositeOperation='source-over'}
 const sc=lerp(.35,1,eo(0,1,pm.show));
 const pts=skinPatch(g,f,img,uc,vc,du*sc,dv*sc,pm.alpha*Math.min(1,pm.show*2),pm.rot,pm.card,pm.fly,du>.4?4:3);
 // sewn edge for grudge, gold edge for pride, coins for debt
 const n=pts.length-1,edge=[];for(let i=0;i<=n;i++)edge.push(pts[0][i]);for(let j=1;j<=n;j++)edge.push(pts[j][n]);for(let i=n-1;i>=0;i--)edge.push(pts[n][i]);for(let j=n-1;j>0;j--)edge.push(pts[j][0]);
 if(feel==='grudge'||feel==='pride'){g.save();g.globalAlpha=pm.alpha*pm.show;g.strokeStyle=feel==='grudge'?'#2a0806':'#c9a23a';g.lineWidth=feel==='grudge'?4:3;g.setLineDash(feel==='grudge'?[10,8]:[]);g.beginPath();g.moveTo(edge[0][0],edge[0][1]);for(const p of edge)g.lineTo(p[0],p[1]);g.closePath();g.stroke();g.restore()}
 if(feel==='story'&&pm.fly>=1){g.save();g.globalAlpha=pm.alpha*pm.show*.5;g.strokeStyle='#4e3420';g.lineWidth=2;g.setLineDash([3,6]);g.beginPath();g.moveTo(edge[0][0],edge[0][1]);for(const p of edge)g.lineTo(p[0],p[1]);g.closePath();g.stroke();g.restore()}
 if(feel==='debt'){for(let k=0;k<3;k++){const p=f(uc+(k-1)*du*.3,vc-dv*.6-.04*k);g.beginPath();g.ellipse(p[0],p[1]+10,12,9,0,0,TAU);g.fillStyle='#c9a23a';g.globalAlpha=pm.alpha*pm.show;g.fill();g.strokeStyle='#6a4e14';g.lineWidth=2;g.stroke();g.globalAlpha=1}}}

// ======================= the others, as Belindo believes them to be =======================
function figure(g,id,x,y,sc,o){const A=ATTR[id];const w=A.w*sc,h=A.h*sc;g.save();g.globalAlpha=o.a;if(o.dead){g.translate(x+h/2,y-w/2);g.rotate(-Math.PI/2);x=0;y=0;o.lit='#55524e'}
 // the same rest outline as Belindo's cloth, in the other's proportions (Inigo slumps: his top sags)
 const pts=[];const N=16;const P=(u,v)=>{let[rx,ry]=rest(u,v);if(id==='I')ry*=1-.28*Math.sin(Math.PI*u)*Math.pow(v,3)-.1*v*(1-u);return[x+rx*w,y+ry*h]};
 for(let i=0;i<=N;i++)pts.push(P(i/N,0));for(let j=1;j<=N;j++)pts.push(P(1,j/N));for(let i=N-1;i>=0;i--)pts.push(P(i/N,1));for(let j=N-1;j>0;j--)pts.push(P(0,j/N));
 const path=(dx)=>{g.beginPath();g.moveTo(pts[0][0]+dx,pts[0][1]);for(const p of pts)g.lineTo(p[0]+dx,p[1]);g.closePath()};
 for(let k=0;k<o.ghosts;k++){const dx=(k%2?1:-1)*o.unc*(1+(k>>1));path(dx);g.strokeStyle='rgba(230,215,190,.22)';g.lineWidth=2;g.stroke()}
 if(o.dashed){path(0);g.setLineDash([12,10]);g.strokeStyle='rgba(235,220,195,.55)';g.lineWidth=3;g.stroke();g.restore();return}
 // ears (R and I; O's are under the wig)
 const ear=(sd)=>{const c=P(sd<0?0:1,1);g.beginPath();if(id==='I'){g.moveTo(c[0]-sd*w*.05,c[1]);g.quadraticCurveTo(c[0]+sd*w*.16,c[1]+h*.2,c[0]+sd*w*.08,c[1]+h*.85);g.lineTo(c[0]-sd*w*.02,c[1]+h*.8);g.quadraticCurveTo(c[0]+sd*w*.04,c[1]+h*.3,c[0]-sd*w*.12,c[1]+h*.04)}else{g.moveTo(c[0]-sd*w*.14,c[1]);g.lineTo(c[0]+sd*w*.12,c[1]-h*.2);g.lineTo(c[0],c[1]+h*.1)}g.closePath();g.fill()};
 const dim=o.lit;g.fillStyle=dim;if(id!=='O'){ear(-1);ear(1)}
 path(0);const gr=g.createLinearGradient(x,y-h,x,y);gr.addColorStop(0,dim);gr.addColorStop(1,'#2a2118');g.fillStyle=gr;g.fill();g.strokeStyle='rgba(240,225,200,.6)';g.lineWidth=2.5;g.stroke();
 if(id==='R'){g.save();path(0);g.clip();g.fillStyle=A.acc;g.fillRect(x-w,y-h*1.1,w*2,h*.32);g.restore()}
 if(id==='I'){g.fillStyle='rgba(60,45,30,.35)';ear(-1);ear(1)}
 if(id==='O'){const t=P(.5,1);g.fillStyle=A.acc;g.beginPath();g.ellipse(t[0],t[1]+h*.02,w*.62,h*.09,0,0,TAU);g.fill();
  for(const sd of[-1,1]){g.beginPath();g.moveTo(t[0]+sd*w*.62,t[1]);g.quadraticCurveTo(t[0]+sd*w*.72,t[1]+h*.3,t[0]+sd*w*.56,t[1]+h*.5);g.lineTo(t[0]+sd*w*.38,t[1]+h*.46);g.quadraticCurveTo(t[0]+sd*w*.44,t[1]+h*.2,t[0]+sd*w*.3,t[1]);g.fill()}}
 g.restore()}

// ======================= poses from feelings and levers =======================
function poseFrom(t,acc,lv,tempo,imp){const br=Math.sin(t*TAU*(.55+.35*tempo));imp=imp||0;
 const tremor=acc.fear*(.018*Math.sin(t*41.3)+.012*Math.sin(t*67.1));
 const bow=-(acc.guilt*.1+lv.shrink*.08),lean=.06*lv.loom-acc.fear*.07+acc.desire*.06;
 return[{a:0},{a:lean*.5+tremor+bow*.3,sy:1+.012*br-.05*acc.guilt,sx:1+.02*br+.03*acc.guilt},{a:lean*.6+bow*.5-acc.grudge*.02+imp,sy:1+.01*br-.04*acc.guilt,sx:1-.02*acc.grudge+.01*br},{a:bow*.4+imp*.8,sx:1-.015*acc.grudge},
  {a:-.5*acc.guilt+.9*acc.fear*(.8+.2*Math.sin(t*9))-.35*lv.shrink+.25*acc.grudge-.2*acc.desire+.06*br},{a:.5*acc.guilt-.9*acc.fear*(.8+.2*Math.sin(t*9.4))+.35*lv.shrink-.25*acc.grudge+.15*acc.desire-.06*br}]}

function room(g,t,lv,cx){const W=1920,Hh=1080;g.fillStyle='#120e0c';g.fillRect(0,0,W,Hh);
 const wall=g.createLinearGradient(0,0,0,880);wall.addColorStop(0,'#1d1716');wall.addColorStop(1,'#2a201b');g.fillStyle=wall;g.fillRect(0,0,W,880);
 g.fillStyle='#1a1310';g.fillRect(0,880,W,200);g.strokeStyle='rgba(0,0,0,.4)';g.lineWidth=2;for(let k=0;k<9;k++){g.beginPath();g.moveTo(0,890+k*k*3);g.lineTo(W,890+k*k*3);g.stroke()}
 const I=.22+.55*cl(0,1,lv.halo+.25)*(1-.6*lv.grey);const sp=g.createRadialGradient(cx,330,40,cx,640,720);sp.addColorStop(0,`rgba(255,214,150,${I})`);sp.addColorStop(1,'rgba(255,214,150,0)');g.fillStyle=sp;g.fillRect(0,0,W,Hh);
 g.fillStyle='#0b0807';g.beginPath();g.moveTo(cx-50,90);g.lineTo(cx+50,90);g.lineTo(cx+30,64);g.lineTo(cx-30,64);g.fill();g.fillStyle=`rgba(255,226,170,${.5+I})`;g.beginPath();g.ellipse(cx,92,24,6,0,0,TAU);g.fill();
 g.strokeStyle='#0b0807';g.lineWidth=3;g.beginPath();g.moveTo(cx,0);g.lineTo(cx,64);g.stroke()}

function accum(list,tt){const a={fear:0,guilt:0,grudge:0,desire:0,pride:0,debt:0,story:0};for(const pm of list){a[pm.feel]=(a[pm.feel]||0)+pm.weight*pm.show}for(const k in a)a[k]=Math.min(1,a[k]);return a}
function rank(mems){ // weights saturate at 1: break ties by recency, and guilt weighs most on him
 return mems.map((m,i)=>({m,i,s:m.weight-.035*m.ago+(m.role==='doer'?.06:0)})).sort((a,b)=>b.s-a.s||a.i-b.i).map(x=>x.m)}
function planPatches(mems,P0,max){const out=[];
 rank(mems).slice(0,max).forEach((m,i)=>{const feel=feeling(m);const[uc,vc]=region(m,i);
  const big=i===0?.56:(m.role==='witness'?.24:.27+.06*m.weight);const du=big,dv=du*(190/256)*1.14*.9;
  const fade=feel==='guilt'?Math.pow(.97,m.ago):Math.max(.3,1-m.ago*.09);
  out.push({k:m.k,m,feel,uc,vc,du,dv,weight:m.weight,alpha:fade*(.7+.3*m.weight),rot:(H(m.k*5.3)-.5)*.22,img:texture(m,feel)})});
 // lay the patches out in the cloth's free slots (around the wheat, either side of the belt): each memory takes
 // the free slot nearest the region where it happened, strongest first, so none covers another
 const SL=[[.21,.7,.34],[.79,.7,.34],[.27,.2,.44],[.73,.2,.44],[.5,.9,.24]];const free=SL.map(()=>true);
 out.forEach((p,i)=>{let bi=-1,bd=1e9;SL.forEach((q,j)=>{if(!free[j]||(i===0&&j===4))return;const d=Math.hypot(q[0]-p.uc,(q[1]-p.vc)*1.3);if(d<bd){bd=d;bi=j}});
  if(bi<0)return;free[bi]=false;const q=SL[bi];p.slot=bi;p.uc=q[0];p.vc=q[1];p.du=Math.min(p.du,q[2])*(i===0?1.08:1);p.dv=p.du*(190/256)*1.14*.9;
  if(bi===4){p.vc=.92-p.dv*.1}
  if(i===0){p.du=Math.max(p.du,.5);p.dv=p.du*(190/256)*1.14*.9;p.uc=cl(p.du/2+.03,1-p.du/2-.03,p.uc);p.vc=q[1]>.5?cl(.43+p.dv/2+.02,1-p.dv/2-.03,p.vc):cl(p.dv/2+.03,.37-p.dv/2,p.vc);
   SL.forEach((r,j)=>{if(free[j]&&Math.abs(r[0]-p.uc)<(r[2]+p.du)/2&&Math.abs(r[1]-p.vc)<(r[2]*.76+p.dv)/2)free[j]=false})}});
 return out}

// ======================= MEMORY =======================
MEMORY({who:'B',scion:37,lineage:'Weighted Skinning — Mesh Attachment Laboratory',
 op:'Bind each remembered shot, cropped and tinted by its feeling, to the region of Belindo\'s skinned cloth mesh where the deed touched him, and let the memory\'s weight bend his bones and add corrective sag there.',
 made:'Belindo is one cloth mesh of 13×13 vertices bound by normalised weights to a six-bone rig (four spine bones and two ears that act as his hands), with his belt and wheat stencil skinned onto it. His memories are crops of the actual remembered shots, recoloured by feeling (violet bruise, brown soaked stain, red sewn patch, rose glow, ink stencil for stories told to him) and bound to the mesh as textures.',
 moved:'Bone poses come from the feelings he carries and the house\'s archetype levers: guilt bows the spine and drags the cloth down under the stain, fear pinches the cloth and throws the ears up, grudge clenches the belt, desire swells him toward the other. On the right the other stands as Belindo believes them to be, swelling or shrinking from the size he believed before the event to the size he believes now, shadow reaching toward him by how dangerous he thinks they are.',
 flash(g,t,mark,mems,K,X){if(!mems||!mems.length)return;const st=X.state||{};const lv=(st.levers&&st.levers.B)||{};
  const env=eo(0,.35,t)*(1-sm(1.1,1.5,t));if(env<=.002)return;
  const s=mark.w,hs=mark.h/mark.w,P={x:mark.x+mark.w/2,y:mark.y+mark.h,s,hs,pose:[],corr:[]};
  const pl=planPatches(mems,P,2);pl.forEach((p,i)=>{p.show=eo(.05+i*.25,.5+i*.25,t)*(1-sm(1.15,1.5,t));p.fly=1;p.alpha*=i?0.8:1;p.du*=i?.8:1.15;p.dv*=i?.8:1.15});
  const acc=accum(pl,t);const pose=poseFrom(t,acc,lv,1);pose[0].a*=.3;P.pose=pose.map((q,i)=>i>=4?{a:0}:q);P.corr=pl.map(p=>({u:p.uc,v:p.vc,feel:p.feel,amp:p.weight*p.show}));
  const Bd=makeBody(P);
  // the weave of the bind mesh lights up over him (the skin being shown), then the memories rise on it
  const ol=[];for(let i=0;i<=10;i++)ol.push(Bd.f(i/10,0));for(let j=1;j<=8;j++)ol.push(Bd.f(1,j/8));for(let i=9;i>=0;i--)ol.push(Bd.f(i/10,1));for(let j=7;j>0;j--)ol.push(Bd.f(0,j/8));
  const cxm=mark.x+mark.w/2,cym=mark.y+mark.h/2;g.save();g.beginPath();ol.forEach((p,i)=>{const q=[cxm+(p[0]-cxm)*.9,cym+(p[1]-cym)*.94];i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])});g.closePath();g.clip();
  g.save();g.globalAlpha=.35*env;g.strokeStyle='rgba(255,236,200,.8)';g.lineWidth=1.3;
  for(let j=1;j<8;j++){g.beginPath();for(let i=0;i<=10;i++){const p=Bd.f(i/10,j/8);i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()}
  for(let i=1;i<10;i++){g.beginPath();for(let j=0;j<=8;j++){const p=Bd.f(i/10,j/8);j?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()}g.restore();
  for(const p of pl)drawPatch(g,Bd.f,p,P);g.restore();
  // the other, as he believes them now: a dashed outline beside him, sized by believed strength
  const m=pl[0].m,o=m.other;if(o&&o!=='B'&&st.belief){const b=st.belief.B[o];const sc=(.55+.9*sig(b.str.m))*(mark.w/244)*1.1;const side=mark.x+mark.w/2>960?-1:1;
   const fx=side>0?mark.x+mark.w+ATTR[o].w*sc*.7:mark.x-ATTR[o].w*sc*.7;
   if(X.ledger&&X.ledger.states[m.k]){const b0=X.ledger.states[m.k].belief.B[o];const sc0=(.55+.9*sig(b0.str.m))*(mark.w/244)*1.1;figure(g,o,fx,mark.y+mark.h,sc0,{a:env*.8,ghosts:0,unc:0,dashed:true})}
   figure(g,o,fx,mark.y+mark.h,sc,{a:env*.42*sm(.2,.6,t),dead:st.alive&&!st.alive[o],ghosts:Math.round(b.str.v*3),unc:b.str.v*14,lit:'#6a5a48',dashed:false});
   const c=Bd.f(pl[0].uc,pl[0].vc);g.save();g.globalAlpha=env*.5;g.strokeStyle=ATTR[o].acc==='#b59c72'?'#d9c39a':ATTR[o].acc;g.lineWidth=2;g.setLineDash([4,8]);g.beginPath();g.moveTo(c[0],c[1]);g.lineTo(fx,mark.y+mark.h-ATTR[o].h*sc*.6);g.stroke();g.restore()}},

 beat(g,t,mems,st,K,X){const L=X.ledger;const lv=st.levers.B;const alive=st.alive.B;
  const selfP=sig(st.belief.B.B.str.m)/sig(1.5);  // what he believes his own strength is
  const cx=720;room(g,t,lv,cx);
  const s=244*2.15*(1+.22*cl(-1,1,lv.loom)-.3*lv.shrink)*(.85+.15*selfP),hs=214/244;
  const P={x:cx,y:900,s,hs,pose:[],corr:[]};
  const pl=planPatches(alive?mems:mems,P,5);
  // each memory flies in from the remembered other's side as a card (the shot) and binds to its region
  const fig=pl.length?pl[0].m.other:null;
  pl.forEach((p,i)=>{const t0=.25+i*.3,t1=t0+.55;p.fly=alive?eo(t0+.12,t1,t):1;p.show=sm(t0,t0+.14,t)*(alive?1:1-sm(.8,2.2,t)*.7);
   const cw=lerp(560,380,Math.min(1,i/3)),ch=cw*190/256;p.card={x:1420-cw/2-60*(i%2),y:250+40*i-ch/2+100,w:cw,h:ch}});
  const acc=accum(pl,t);
  const tempo=.5+.5*cl(-1,1,lv.tempo);let imp=0;
  pl.forEach((p,i)=>{const t1=.25+i*.3+.55,d=t-t1;if(d>0){const dir=p.feel==='desire'?1:p.feel==='guilt'?-.6:-1;imp+=dir*.07*(.5+p.weight)*(1+.6*lv.weight)*Math.exp(-d*(4+3*tempo))*Math.sin(d*(14+8*tempo))}});
  let pose=poseFrom(t,acc,lv,tempo,imp);
  if(!alive){const sl=.62-.06*sm(0,2.4,t);pose=pose.map((q,i)=>i>=4?{a:(i===4?-1.25:1.25)}:{a:i===3?.06:0,sy:i?sl:1,sx:i?1/Math.sqrt(sl):1});}
  if(!mems.length){const tw=Math.max(0,Math.sin(t*2.3))**8;pose[4].a+=-.25*tw;pose[5].a+=.18*Math.max(0,Math.sin(t*1.7+2))**8}
  P.pose=pose;P.corr=pl.map(p=>({u:p.uc,v:p.vc,feel:p.feel,amp:p.weight*p.show*(1+.4*lv.weight)}));
    // shadow: length and darkness from the shadow lever
  g.save();const shL=1+1.6*lv.shadow;g.fillStyle=`rgba(0,0,0,${.35+.35*cl(0,1,lv.shadow)})`;g.beginPath();g.ellipse(cx+40*shL,903,s*.55*shL,22+10*shL,0,0,TAU);g.fill();g.restore();
  // the other(s) as believed: prior (dashed, before the remembered event) -> posterior (filled, now)
  if(alive&&fig){const others=[];for(const p of pl)if(p.m.other&&p.m.other!=='B'&&!others.includes(p.m.other))others.push(p.m.other);
   others.slice(0,2).reverse().forEach((o,ri)=>{const front=ri===others.slice(0,2).length-1;const m=pl.find(p=>p.m.other===o).m;
    const b0=L.states[m.k].belief.B[o],b1=st.belief.B[o];const u=eo(.9,2.0,t);const p0=sig(b0.str.m),p1=sig(b1.str.m);const pp=lerp(p0,p1,u);
    const h0=b0.harm.m,h1=b1.harm.m,hh=lerp(h0,h1,u),vv=lerp(b0.str.v,b1.str.v,u);
    const sc0=1.75*(.55+.9*p0),sc=1.75*(.55+.9*pp);const fx=front?1420:Math.min(1720,1890-ATTR[o].w*sc*.55),fy=front?900:884;const ap=sm(.15,.6,t);
    // danger: its shadow reaches across the floor toward Belindo
    g.save();g.globalAlpha=ap;const reach=200+620*hh;const gr=g.createLinearGradient(fx,0,fx-reach,0);gr.addColorStop(0,`rgba(20,0,10,${.45+.4*hh})`);gr.addColorStop(1,'rgba(20,0,10,0)');g.fillStyle=gr;g.beginPath();g.moveTo(fx+ATTR[o].w*sc*.4,fy+4);g.lineTo(fx-reach,fy+12+30*hh);g.lineTo(fx-reach,fy-6);g.lineTo(fx-ATTR[o].w*sc*.5,fy-4);g.closePath();g.fill();g.restore();
    if(Math.abs(sc-sc0)>.02||u<1)figure(g,o,fx,fy,sc0,{a:ap*.9,ghosts:0,unc:0,dashed:true});
    figure(g,o,fx,fy,sc,{a:ap*(front?1:.7),ghosts:st.alive[o]?Math.round(vv*4):0,unc:vv*22,lit:hh>.5?'#6a4a40':'#6a5a48',dead:!st.alive[o]})})}
  // threads: each bound memory to the other it involved
  const Bd=drawSack(g,P,pl,pl,{grey:lv.grey});
  const thr={};if(alive)for(const p of pl){if(p.fly<1||!p.m.other||p.m.other==='B'||thr[p.m.other])continue;thr[p.m.other]=1;const c=Bd.f(p.uc,p.vc);const o=p.m.other;const fr=o===fig?1420:1720;g.save();g.globalAlpha=.35*p.show*sm(1,1.6,t);g.strokeStyle=o==='O'?'#a060b8':o==='R'?'#a8564a':'#cdb88e';g.lineWidth=2;g.setLineDash([3,9]);g.beginPath();g.moveTo(c[0],c[1]);g.quadraticCurveTo((c[0]+fr)/2,c[1]-120,fr,820);g.stroke();g.restore()}
  // flying cards drawn above everything until bound
  for(const p of pl)if(p.fly<1&&p.show>0)drawPatch(g,Bd.f,p,P);
  // at peace: no memories — slow breath, ears twitching, a mote drifting through the lamp
  if(!mems.length&&alive){for(let k=0;k<6;k++){const x=cx-260+H(k)*520+30*Math.sin(t*.8+k),y=200+((H(k*3)*600+t*22)%600);g.fillStyle='rgba(255,236,190,.35)';g.beginPath();g.arc(x,y,2.2,0,TAU);g.fill()}}
  if(lv.grey>.05||!alive){g.fillStyle=`rgba(10,10,12,${(alive?.15*lv.grey:.25+.25*sm(.5,2.4,t))})`;g.fillRect(0,0,1920,1080)}},

 sound(ac,out,t0,kind,mems,K){const S=K.SND;mems=mems&&mems.length?rank(mems):[];const m0=mems[0];
  if(kind==='flash'){if(!m0)return;S.say(ac,out,'B',t0+.05,'react',.9,-.2);S.thump(ac,out,t0+.35,.6,40,-.2);
   // the remembered shot's own sound returns, heard through his cloth (low-passed, short)
   try{const D=window.DEEDS&&DEEDS[m0.deed];if(D&&D.sound){const lp=ac.createBiquadFilter();lp.type='lowpass';lp.frequency.value=380;const gg=ac.createGain();gg.gain.value=0;gg.gain.setValueAtTime(0,Math.max(ac.currentTime,0));gg.gain.setValueAtTime(0,t0+.1);gg.gain.linearRampToValueAtTime(1.4,t0+.3);gg.gain.setValueAtTime(1.4,t0+.85);gg.gain.linearRampToValueAtTime(0,t0+1.4);lp.connect(gg);gg.connect(out);D.sound(ac,lp,t0+.35-D.contact,m0.A,m0.V,K)}}catch(e){}
   return}
  // beat: a heartbeat in his deep voice; each memory binding has the sound of its feeling
  for(let k=0;k<5;k++)S.say(ac,out,'B',t0+.2+k*.48,'step',.35+.1*(k%2),-.3);
  if(!mems||!mems.length){S.say(ac,out,'B',t0+.3,'breathe',2);return}
  mems.slice(0,5).forEach((m,i)=>{const w=t0+.25+i*.3+.55,f=feeling(m),a=.5+.5*m.weight;
   if(f==='guilt'){S.say(ac,out,'B',w,'sink',.8*a,-.3);S.thump(ac,out,w,.5*a,38,-.3)}
   else if(f==='fear'){S.cloud(ac,out,w-.1,.5,60,{bp:200,a:.05*a,d:[.01,.03]},u=>1-u);S.say(ac,out,'B',w,'land',.6*a,-.3)}
   else if(f==='grudge'){for(let q=0;q<3;q++)S.say(ac,out,'B',w+q*.09,'tick',.7*a,-.3)}
   else if(f==='desire'){S.pluck(ac,out,w,57+(m.k%3)*3,.25*a,1.2,-.2)}
   else if(f==='story'){S.say(ac,out,m.other||'I',w-.2,'breathe',.6,.4)}
   else S.say(ac,out,'B',w,'land',.5*a,-.3)})}
});
// numeric invariant (bind): weights normalise to 1 at every rest vertex; exported for test
window.__B_WEIGHT_TEST=function(){let worst=0;for(let j=0;j<=NV;j++)for(let i=0;i<=NU;i++){const[x,y]=rest(i/NU,j/NV);const w=weights(x,y);worst=Math.max(worst,Math.abs(w.reduce((a,b)=>a+b,0)-1))}return worst};
})();
