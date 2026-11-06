// MEMORY · I · INIGO — SCION 10 (Schaefer, McPhail & Warren, MLS image deformation, 2006)
// Inigo remembers by dragging landmarks: every remembered still is a fragment of the actual shot, cut on a mesh
// and warped by moving-least-squares from its true landmarks (the two sacks, the frame) to where his dream moves them.
(function(){
const TAU=Math.PI*2;
const IDS=['R','B','I','O'];
const sig=x=>1/(1+Math.exp(-x));
const clamp=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
const sm=(a,b,x)=>{const u=clamp(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
// deterministic hash + smooth value noise (no Math.random, no Date)
const H=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};
function vn(seed,t){const i=Math.floor(t),f=t-i,u=f*f*(3-2*f);return lerp(H(seed*17.3+i),H(seed*17.3+i+1),u)*2-1}

// ---------------- MLS (Schaefer et al. 2006): affine / similarity / rigid ----------------
// P,Q: flat arrays [x0,y0,x1,y1,...] control-point pairs; W: per-handle weight (feature protection); alpha: weight exponent
function MLS(P,Q,W,fam,alpha){const n=P.length/2;
 return function(vx,vy){let sw=0,px=0,py=0,qx=0,qy=0;const w=new Array(n);
  for(let i=0;i<n;i++){const dx=P[2*i]-vx,dy=P[2*i+1]-vy,d2=dx*dx+dy*dy;if(d2<1e-8)return[Q[2*i],Q[2*i+1]];
   w[i]=(W?W[i]:1)/Math.pow(d2,alpha);sw+=w[i];px+=w[i]*P[2*i];py+=w[i]*P[2*i+1];qx+=w[i]*Q[2*i];qy+=w[i]*Q[2*i+1]}
  px/=sw;py/=sw;qx/=sw;qy/=sw;const dx=vx-px,dy=vy-py;
  if(fam==='affine'){let a=0,b=0,c=0,m00=0,m01=0,m10=0,m11=0;
   for(let i=0;i<n;i++){const hx=P[2*i]-px,hy=P[2*i+1]-py,kx=Q[2*i]-qx,ky=Q[2*i+1]-qy,wi=w[i];
    a+=wi*hx*hx;b+=wi*hx*hy;c+=wi*hy*hy;m00+=wi*hx*kx;m01+=wi*hx*ky;m10+=wi*hy*kx;m11+=wi*hy*ky}
   const det=a*c-b*b;if(Math.abs(det)<1e-9)return[vx-px+qx,vy-py+qy];
   const i00=c/det,i01=-b/det,i11=a/det;const r0=dx*i00+dy*i01,r1=dx*i01+dy*i11;
   return[r0*m00+r1*m10+qx,r0*m01+r1*m11+qy]}
  let A=0,B=0,mu=0;
  for(let i=0;i<n;i++){const hx=P[2*i]-px,hy=P[2*i+1]-py,kx=Q[2*i]-qx,ky=Q[2*i+1]-qy,wi=w[i];
   A+=wi*(hx*kx+hy*ky);B+=wi*(hx*ky-hy*kx);mu+=wi*(hx*hx+hy*hy)}
  const s=fam==='rigid'?Math.hypot(A,B)||1:mu||1;
  return[(A*dx-B*dy)/s+qx,(B*dx+A*dy)/s+qy]}}

// warp a whole image on an nx×ny mesh through map(u,v in image px) -> screen px.
// Each cell is drawn as its best-fit parallelogram (the mean of its edge vectors): no clipping, cells overlap by a pixel,
// and the error at a cell corner is half its non-affine part (sub-pixel at these mesh densities).
function warpImage(g,img,map,nx,ny){const W=img.width,Hh=img.height;const V=[];
 for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++)V.push(map(i/nx*W,j/ny*Hh));
 const at=(i,j)=>V[j*(nx+1)+i];const cw=W/nx,ch=Hh/ny;
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const A=at(i,j),B=at(i+1,j),C=at(i,j+1),D=at(i+1,j+1);
  const ax=(B[0]-A[0]+D[0]-C[0])/2/cw,ay=(B[1]-A[1]+D[1]-C[1])/2/cw,cx=(C[0]-A[0]+D[0]-B[0])/2/ch,cy=(C[1]-A[1]+D[1]-B[1])/2/ch;
  const mx=(A[0]+B[0]+C[0]+D[0])/4,my=(A[1]+B[1]+C[1]+D[1])/4;
  g.setTransform(ax,ay,cx,cy,mx,my);const sx=i*cw,sy=j*ch,x0=Math.max(0,sx-1),y0=Math.max(0,sy-1),x1=Math.min(W,sx+cw+1),y1=Math.min(Hh,sy+ch+1);
  g.drawImage(img,x0,y0,x1-x0,y1-y0,x0-sx-cw/2,y0-sy-ch/2,x1-x0,y1-y0)}
 g.setTransform(1,0,0,1,0,0)}

// ---------------- what the remembered event was, and how it feels ----------------
function feelingOf(m,st){if(m.role==='witness')return'witness';
 // this event's own feeling (the deed's rule, through Inigo's temperament), coloured by what he now holds toward the other
 const R=window.LEDGER&&LEDGER.RULE&&LEDGER.RULE[m.deed],T=(window.LEDGER&&LEDGER.TEMPER&&LEDGER.TEMPER.I)||{};const ev=R?(m.role==='victim'?R.mindV:R.mindA):{};
 const mm=(st.mind&&st.mind.I&&st.mind.I[m.other])||{};const v=k=>(ev[k]||0)*(T[k]??1)+(mm[k]||0)*.1;
 // Inigo carries little guilt; when he does, it haunts: past a threshold it outweighs everything
 const sc={fear:v('fear')+v('debt')*.6,guilt:v('guilt')>.3?v('guilt')*1.8:v('guilt')*.3,grudge:v('grudge')*.8,desire:v('desire')*1.1,pride:v('pride')*.9};
 let best='witness',bv=.08;for(const k in sc)if(sc[k]>bv){bv=sc[k];best=k}return best}
// family chosen per feeling (the paper's comparison made into his temperament)
const FAM={fear:'affine',guilt:'rigid',grudge:'affine',desire:'similarity',pride:'similarity',witness:'similarity'};
const TINT={fear:[60,90,150],guilt:[40,30,60],grudge:[120,40,30],desire:[220,120,140],pride:[230,190,90],witness:[120,120,120]};

// landmark boxes in the remembered still (the deed's own geometry at the still's time)
function stillMarks(m){try{const D=window.DEEDS&&DEEDS[m.deed];if(D&&D.marks){const r=D.marks(D.contact+.3,m.A,m.V,window.K);if(r&&r.A&&r.V)return r}}catch(e){}
 return{A:{x:380,y:560,w:220,h:260},V:{x:1300,y:560,w:220,h:260}}}
// a fragment of the actual shot: crop round both sacks, tinted by feeling, softened by age, edges dissolved (memoised)
const CACHE={};
function fragment(m,feel){const key=m.deed+m.A+m.V+feel+Math.min(6,m.ago|0);if(CACHE[key])return CACHE[key];
 const mk=stillMarks(m);let x0=Math.min(mk.A.x,mk.V.x)-110,x1=Math.max(mk.A.x+mk.A.w,mk.V.x+mk.V.w)+110,y0=Math.min(mk.A.y,mk.V.y)-120,y1=Math.max(mk.A.y+mk.A.h,mk.V.y+mk.V.h)+60;
 let w=x1-x0,h=y1-y0;if(w<h*16/9){const c=(x0+x1)/2;w=h*16/9;x0=c-w/2}else{const c=(y0+y1)/2;h=w*9/16;y0=c-h/2}
 w=Math.min(w,1920);h=Math.min(h,1080);x0=clamp(0,1920-w,x0);y0=clamp(0,1080-h,y0);
 const res=Math.round(480/(1+Math.min(6,m.ago|0)*.28));const cw=res,ch=Math.round(res*h/w);
 const cv=document.createElement('canvas');cv.width=cw;cv.height=ch;const q=cv.getContext('2d');
 q.filter='brightness(1.45) contrast(1.15)';if(m.still)q.drawImage(m.still,x0,y0,w,h,0,0,cw,ch);else{q.fillStyle='#222';q.fillRect(0,0,cw,ch)}q.filter='none';
 const T=TINT[feel];q.globalCompositeOperation='color';q.fillStyle=`rgba(${T},${feel==='witness'?.75:.38})`;q.fillRect(0,0,cw,ch);
 q.globalCompositeOperation='source-over';q.fillStyle=`rgba(${T},.12)`;q.fillRect(0,0,cw,ch);
 const sx=cw/w,lm=b=>[(b.x+b.w/2-x0)*sx,(b.y+b.h*.55-y0)*sx,(b.x+b.w/2-x0)*sx,(b.y-y0)*sx];
 const r={cv,A:lm(mk.A),V:lm(mk.V)};CACHE[key]=r;return r}

// the dream: rest handles in screen space, targets moved by feeling, weight and age; returns MLS map image-px -> screen
function dreamMap(fr,m,feel,ox,oy,S,t,seed,amt,extra){const cw=fr.cv.width,ch=fr.cv.height;const me=m.role==='victim'?fr.V:fr.A,ot=m.role==='victim'?fr.A:fr.V;
 const Pimg=[0,0,cw,0,cw,ch,0,ch,cw/2,0,cw,ch/2,cw/2,ch,0,ch/2,me[0],me[1],ot[0],ot[1],ot[2],ot[3]];
 const P=[],Q=[];for(let i=0;i<Pimg.length;i+=2){P.push(ox+Pimg[i]*S,oy+Pimg[i+1]*S)}
 for(let i=0;i<P.length;i++)Q.push(P[i]);
 const W=[1,1,1,1,1,1,1,1,1.6,2.2,2.2];   // the people are protected features: heavier weight
 const cx=ox+cw*S/2,cy=oy+ch*S/2,fw=cw*S,fh=ch*S;const ag=1+(m.ago||0)*.35;const A=amt*(.6+.6*(m.weight||.3));
 // drift: every handle wanders (dreamy; older memories wander farther)
 for(let i=0;i<11;i++){Q[2*i]+=vn(seed+i,t*.55+i)*fw*.035*ag;Q[2*i+1]+=vn(seed+i+40,t*.5+i)*fh*.04*ag}
 const mi=8,oi=9,ti=10;const MOV=(i,dx,dy)=>{Q[2*i]+=dx;Q[2*i+1]+=dy};const ph=Math.sin(t*1.3+seed);
 if(feel==='desire'){const r=.1*A*ph;for(let i=0;i<8;i++){const x=P[2*i]-cx,y=P[2*i+1]-cy;Q[2*i]=cx+x*Math.cos(r)-y*Math.sin(r)+(Q[2*i]-P[2*i]);Q[2*i+1]=cy+x*Math.sin(r)+y*Math.cos(r)+(Q[2*i+1]-P[2*i+1])}
  const mx=(P[2*mi]+P[2*oi])/2;MOV(mi,(mx-P[2*mi])*.35*A,-8*A);MOV(oi,(mx-P[2*oi])*.35*A,-8*A);MOV(ti,(mx-P[2*ti])*.3*A,-6*A);
  for(const i of[4,5,6,7]){MOV(i,(P[2*i]-cx)*.12*A,(P[2*i+1]-cy)*.12*A)}}
 if(feel==='fear'){const gro=extra&&extra.grow||1.3;const tr=t*9;MOV(ti,(P[2*ti]-P[2*mi])*(gro-1)*.4*A,-fh*.32*A*(gro-.6)+vn(seed+70,tr)*5);MOV(oi,(P[2*oi]-P[2*mi])*(gro-1)*.25*A,vn(seed+71,tr)*5);
  MOV(mi,(cx-P[2*mi])*-.1*A,fh*.1*A);const side=P[2*oi]>cx?1:-1;for(const i of side>0?[1,2,5]:[0,3,7])MOV(i,side*fw*.1*A,0);}
 if(feel==='guilt'){const sag=fh*.16*A*(.6+.4*Math.sin(t*.9));MOV(6,0,sag*1.6);MOV(2,0,sag);MOV(3,0,sag);
  MOV(oi,(cx-P[2*oi])*.18*A,fh*.05*A);MOV(ti,(cx-P[2*ti])*.18*A,-fh*.18*A);const r=.07*A*Math.sin(t*.7+1);for(let i=0;i<4;i++){const x=Q[2*i]-cx,y=Q[2*i+1]-cy;Q[2*i]=cx+x*Math.cos(r)-y*Math.sin(r);Q[2*i+1]=cy+x*Math.sin(r)+y*Math.cos(r)}}
 if(feel==='grudge'){MOV(4,0,fh*.14*A*(1+ph*.3));MOV(6,0,-fh*.12*A);MOV(oi,0,fh*.04*A);MOV(ti,0,fh*.1*A)}
 if(feel==='pride'){MOV(mi,0,-fh*.1*A);for(let i=0;i<8;i++)MOV(i,(P[2*i]-cx)*.1*A,(P[2*i+1]-cy)*.1*A);MOV(ti,0,fh*.08*A);MOV(oi,0,fh*.05*A)}
 if(extra&&extra.pull){const[px,py,u]=extra.pull;MOV(oi,(px-Q[2*oi])*u,(py-Q[2*oi+1])*u);MOV(ti,(px-Q[2*ti])*u,(py-90-Q[2*ti+1])*u)}
 if(extra&&extra.bloom!==undefined){const u=extra.bloom,[ex,ey]=extra.from;for(let i=0;i<P.length;i++)Q[i]=lerp(i%2?ey:ex,Q[i],u)}
 const f=MLS(P,Q,W,feel==='desire'&&extra&&extra.bloom!==undefined&&extra.bloom<1?'similarity':FAM[feel],1);
 return{map:(u,v)=>f(ox+u*S,oy+v*S),P,Q,f}}
// warp at full opacity into a scratch buffer (so overlapping triangle edges never double up), then composite once
let BUF=null;
function drawFragment(g,fr,dm,alpha,nx,ny,op){if(!BUF){BUF=document.createElement('canvas');BUF.width=1920;BUF.height=1080}const b=BUF.getContext('2d');
 const Q=dm.Q;let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(let i=0;i<Q.length;i+=2){x0=Math.min(x0,Q[i]);x1=Math.max(x1,Q[i]);y0=Math.min(y0,Q[i+1]);y1=Math.max(y1,Q[i+1])}
 const mx=(x1-x0)*.2+20,my=(y1-y0)*.2+20;const bx=Math.max(0,Math.floor(x0-mx)),by=Math.max(0,Math.floor(y0-my)),bw=Math.min(1920,Math.ceil(x1+mx))-bx,bh=Math.min(1080,Math.ceil(y1+my))-by;if(bw<2||bh<2)return;
 b.setTransform(1,0,0,1,0,0);b.globalCompositeOperation='source-over';b.clearRect(bx,by,bw,bh);b.save();warpImage(b,fr.cv,dm.map,nx||12,ny||7);
 // dissolve the edges in screen space, on an ellipse riding the warped corners (so the mesh never shows a seam)
 const cx=(Q[0]+Q[2]+Q[4]+Q[6])/4,cy=(Q[1]+Q[3]+Q[5]+Q[7])/4,ang=Math.atan2(Q[3]-Q[1]+Q[5]-Q[7],Q[2]-Q[0]+Q[4]-Q[6]);
 const ax=(Math.hypot(Q[2]-Q[0],Q[3]-Q[1])+Math.hypot(Q[4]-Q[6],Q[5]-Q[7]))/4,ay=(Math.hypot(Q[6]-Q[0],Q[7]-Q[1])+Math.hypot(Q[4]-Q[2],Q[5]-Q[3]))/4;
 b.globalCompositeOperation='destination-in';b.translate(cx,cy);b.rotate(ang);b.scale(Math.max(1,ax),Math.max(1,ay));const gr=b.createRadialGradient(0,0,0,0,0,1);
 gr.addColorStop(0,'rgba(0,0,0,1)');gr.addColorStop(.6,'rgba(0,0,0,.95)');gr.addColorStop(.88,'rgba(0,0,0,.3)');gr.addColorStop(1,'rgba(0,0,0,0)');b.fillStyle=gr;b.fillRect(-3,-3,6,6);b.restore();b.globalCompositeOperation='source-over';
 g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=clamp(0,1,alpha);if(op)g.globalCompositeOperation=op;g.drawImage(BUF,bx,by,bw,bh,bx,by,bw,bh);g.restore()}

// ---------------- the sacks themselves are MLS rigs (rigid family: cloth does not shear) ----------------
function sackShape(who,K){const c=(K&&K.CAST&&K.CAST[who])||{w:128,h:98};const w=c.w,h=c.h;const pts=[];const N=10;
 for(let i=0;i<=N;i++)pts.push([-w/2+w*i/N,0]);for(let i=1;i<=N;i++)pts.push([w/2,h*i/N]);
 for(let i=1;i<=N;i++)pts.push([w/2-w*i/N,h+(i>0&&i<N?Math.sin(i/N*Math.PI)*-h*.03:0)]);for(let i=1;i<N;i++)pts.push([-w/2,h-h*i/N]);return{w,h,pts}}
function sackRig(who,K,pose){const{w,h,pts}=sackShape(who,K);
 const P=[-w/2,0, w/2,0, -w/2,h, w/2,h, 0,h*.5, 0,h];
 const sl=pose.slump||0,ln=pose.lean||0,sq=pose.squash||0,br=pose.breath||0;
 const Q=[-w/2*(1+sl*.18+sq*.1),0, w/2*(1+sl*.18+sq*.1),0, -w/2*(1-sl*.1)+ln*h*.3,h*(1-sl*.32-sq*.15+br), w/2*(1-sl*.1)+ln*h*.3,h*(1-sl*.38-sq*.15+br*.8), ln*h*.12+sl*w*.04,h*.5*(1-sl*.3-sq*.15), ln*h*.3,h*(1-sl*.42-sq*.15+br)];
 const f=MLS(P,Q,[2,2,1,1,1.5,1],'rigid',1);return{w,h,pts,f}}
function grey(c,u){const m=(c[0]+c[1]+c[2])/3;return`rgb(${c.map(x=>Math.round(lerp(x,m*.8,u))).join(',')})`}
const CLOTH={R:[214,191,150],B:[232,213,174],I:[226,206,165],O:[240,228,200]};
// draw sack `who` at screen (X,Y base centre), scale s, pose; o: {grey, alpha, sil (silhouette colour), tags}
function drawSack(g,who,X,Y,s,pose,K,o){o=o||{};const r=sackRig(who,K,pose);const M=(x,y)=>{const p=r.f(x,y);return[X+p[0]*s,Y-p[1]*s]};
 const path=pts=>{g.beginPath();pts.forEach((p,i)=>{const q=M(p[0],p[1]);i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])});g.closePath()};
 g.save();g.globalAlpha*=o.alpha??1;
 const gc=o.grey||0;const base=CLOTH[who];
 if(o.sil){g.fillStyle=o.sil}else{const lg=g.createLinearGradient(X,Y-r.h*s,X,Y);lg.addColorStop(0,grey(base.map(x=>Math.min(255,x+12)),gc));lg.addColorStop(1,grey(base.map(x=>x*.72),gc));g.fillStyle=lg}
 path(r.pts);g.fill();if(o.stroke){g.strokeStyle=o.stroke;g.lineWidth=2.5;g.stroke()}if(!o.sil){g.strokeStyle='rgba(60,45,30,.55)';g.lineWidth=2*s;g.stroke()}
 const w=r.w,h=r.h;const band=(y0,y1,col)=>{const pp=[];for(let i=0;i<=8;i++)pp.push([-w/2+w*i/8,y0]);for(let i=8;i>=0;i--)pp.push([-w/2+w*i/8,y1]);path(pp);g.fillStyle=col;g.fill()};
 if(who==='R')band(h*.8,h,o.sil?'#3a1d1a':grey([110,58,51],gc));
 if(who==='B'){band(h*.37,h*.45,o.sil?'#111':grey([42,38,34],gc));if(!o.sil){const c=M(0,h*.66);g.beginPath();g.arc(c[0],c[1],w*.13*s,0,TAU);g.strokeStyle='rgba(120,90,40,.6)';g.lineWidth=3*s;g.stroke()}}
 if(who==='O'){const pp=[[-w/2-6,h*.42],[-w/2-4,h*.95],[-w*.3,h+10],[w*.3,h+10],[w/2+4,h*.95],[w/2+6,h*.42],[w/2-4,h*.55],[w*.2,h*.86],[-w*.2,h*.86],[-w/2+4,h*.55]];path(pp);g.fillStyle=o.sil?'#3a1a45':grey([122,59,143],gc);g.fill()}
 if(who==='I'){ // the long hanging ears, like unwashed hair, hinged at the top corners
  const ear=(sd)=>{const e=clamp(-.5,1,pose.ears||0),sw=pose.earSwing||0;const up=Math.max(0,e);
   // hinge at the top corner; hangs straight down the side to the floor (raised like hands when afraid)
   const hx=sd*(w/2-w*.08),hy=h-2,mx=sd*(w/2+w*.06+Math.sin(sw)*w*.03),my=lerp(h*.5,h*1.25,up),tx=sd*(w/2+w*.16+Math.sin(sw)*w*.05),ty=lerp(3,h*1.65,up);
   const pp=[],ew=w*.26;for(let i=0;i<=8;i++){const u=i/8,a=(1-u)*(1-u),b=2*u*(1-u),c=u*u;pp.push([a*hx+b*mx+c*tx+sd*ew*.5*(1-u*.45),a*hy+b*my+c*ty])}
   for(let i=8;i>=0;i--){const u=i/8,a=(1-u)*(1-u),b=2*u*(1-u),c=u*u;pp.push([a*hx+b*mx+c*tx-sd*ew*.5*(1-u*.45),a*hy+b*my+c*ty])}path(pp);
   g.fillStyle=o.sil?o.sil:grey(base.map(x=>x*.66),gc);g.fill();if(!o.sil){g.strokeStyle='rgba(50,36,24,.7)';g.lineWidth=1.8*s;g.stroke();
    // a few strands: unwashed hair
    g.strokeStyle='rgba(60,45,30,.35)';g.lineWidth=1.2*s;for(const f of[-.25,0,.25]){g.beginPath();for(let i=1;i<=8;i++){const u=i/8,a=(1-u)*(1-u),b=2*u*(1-u),c=u*u;const q=M(a*hx+b*mx+c*tx+sd*ew*f*(1-u*.45),a*hy+b*my+c*ty);i>1?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}}};ear(-1);ear(1)}
 // carried body tags, drawn through the same rig
 const tg=o.tags||[];
 if(!o.sil){const ln=(pts,col,lw)=>{g.beginPath();pts.forEach((p,i)=>{const q=M(p[0],p[1]);i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])});g.strokeStyle=col;g.lineWidth=lw*s;g.stroke()};
  if(tg.includes('rope'))for(const y of[.3,.55])ln([[-w/2,h*y],[0,h*y-4],[w/2,h*y]],'#8a6a3a',4);
  if(tg.includes('cinched'))ln([[-w/2,h*.82],[w/2,h*.82]],'#4a3a2a',5);
  if(tg.includes('gag'))ln([[-w/2,h*.7],[w/2,h*.7]],'#ddd',7);
  if(tg.includes('torn')){ln([[w*.36,h*.08],[w*.42,h*.2],[w*.35,h*.32],[w*.43,h*.44]],'#5a4530',2.5);g.fillStyle='#fbf7ee';g.beginPath();g.ellipse(X+(w*.62)*s,Y-3,30*s,5*s,0,0,TAU);g.fill()}
  if(tg.includes('blot')){g.fillStyle='#14122a';for(let i=0;i<5;i++){const p=M(-w*.36+i*w*.07,h*(.34-i*.05));g.beginPath();g.ellipse(p[0],p[1],(9-i)*s,(4+i*.5)*s,-.5,0,TAU);g.fill()}const d=M(-w*.36,h*.34);g.fillRect(d[0]-2*s,d[1],4*s,16*s)}
  if(tg.includes('tag')){const p=M(w*.5-6,h*.95);g.fillStyle='#efe6c8';g.fillRect(p[0],p[1],22*s,14*s);g.strokeStyle='#553';g.strokeRect(p[0],p[1],22*s,14*s)}
  if(tg.includes('coins'))for(let i=0;i<3;i++){g.fillStyle='#c9a14a';g.beginPath();g.ellipse(X+(w/2+14+i*12)*s,Y-4-i*5*s,9*s,4*s,0,0,TAU);g.fill()}}
 g.restore();return M}

// ---------------- beliefs (PLoT): what Inigo thinks the other is capable of ----------------
function beliefFor(L,k,other,st){try{const b0=L.states[k].belief.I[other],b1=L.states[k+1].belief.I[other];return{b0,b1}}catch(e){const b=st.belief&&st.belief.I&&st.belief.I[other];return{b0:b,b1:b}}}
// the other as Inigo believes it: size = believed strength, nearness = believed danger, doubled outlines = uncertainty
function drawBelief(g,other,b0,b1,u,K,st,x0,floor,t,aq,noShadow){if(!b0||!b1)return;const lv=(st.levers&&st.levers[other])||{};
 const str=lerp(sig(b0.str.m),sig(b1.str.m),u),hz=lerp(b0.harm.m,b1.harm.m,u),vv=lerp(b0.str.v,b1.str.v,u);
 const s=(.6+2.4*str)*(1+.2*(lv.loom||0));const half=K.CAST[other].w*s/2+20;const x=Math.min(x0-hz*560,1920-half);const dead=st.alive&&st.alive[other]===false;
 // the prior: a faint outline, so the change stays readable
 const s0=(.6+2.4*sig(b0.str.m))*(1+.2*(lv.loom||0)),x0p=Math.min(x0-b0.harm.m*560,1920-K.CAST[other].w*s0/2-20);
 g.save();g.globalAlpha=.55*aq;g.setLineDash([10,8]);drawSack(g,other,x0p,floor,s0,{},K,{sil:'rgba(0,0,0,0)',stroke:'rgba(170,180,230,.8)'});g.setLineDash([]);g.restore();
 // shadow lever: its shadow lengthens on the wall
 const sh=lv.shadow||0;if(!noShadow){g.save();g.globalAlpha=(.25+.4*sh)*aq;g.translate(x+80*sh,floor);g.transform(1,0,-.6-1.2*sh,-.55-.6*sh,0,0);drawSack(g,other,0,0,s,{},K,{sil:'#000'});g.restore()}
 // halo lever: the light finds it
 const hl=lv.halo||0;if(hl>.05){const gr=g.createRadialGradient(x,floor-K.CAST[other].h*s*.6,10,x,floor-K.CAST[other].h*s*.6,260*s*.6);gr.addColorStop(0,`rgba(255,230,180,${.35*hl*aq})`);gr.addColorStop(1,'rgba(255,230,180,0)');g.fillStyle=gr;g.fillRect(x-400,floor-700,800,700)}
 for(let i=2;i>=1;i--){g.save();g.globalAlpha=.18*aq*Math.min(1,vv*1.6);drawSack(g,other,x+vn(i*9+3,t*1.4)*60*vv*i,floor,s*(1+.06*i*vv),{},K,{sil:'rgba(0,0,0,0)',stroke:'rgba(170,180,220,.7)'});g.restore()}
 g.save();g.globalAlpha=aq;if(dead)drawSack(g,other,x,floor,s,{slump:.95,squash:.6},K,{sil:'rgb(70,70,78)'});else drawSack(g,other,x,floor,s,{breath:Math.sin(t*2)*.01},K,{sil:`rgb(${Math.round(18+40*hz)},${16},${Math.round(30-10*hz)})`,grey:lv.grey||0});g.restore();
 return{x,s}}

// ---------------- the room (Inigo's attic: a moon window, a floor, the dust of a dream) ----------------
function room(g,t,lv){g.fillStyle='#0b0a14';g.fillRect(0,0,1920,1080);
 const wg=g.createLinearGradient(0,0,0,880);wg.addColorStop(0,'#141226');wg.addColorStop(1,'#1d1a2c');g.fillStyle=wg;g.fillRect(0,0,1920,880);
 g.fillStyle='#120f18';g.fillRect(0,880,1920,200);g.strokeStyle='rgba(120,110,150,.12)';g.lineWidth=2;for(let i=0;i<9;i++){g.beginPath();g.moveTo(0,890+i*i*2.6);g.lineTo(1920,890+i*i*2.6);g.stroke()}
 // window
 g.fillStyle='#2a3150';g.fillRect(150,170,230,300);g.fillStyle='#8fa0c8';g.fillRect(162,182,206,276);g.fillStyle='#2a3150';g.fillRect(262,182,8,276);g.fillRect(162,316,206,8);
 g.fillStyle='rgba(240,240,255,.9)';g.beginPath();g.arc(318,240,26,0,TAU);g.fill();g.fillStyle='#8fa0c8';g.beginPath();g.arc(306,232,24,0,TAU);g.fill();
 // moon light falls on the floor where he lies (halo lever brightens it)
 const hl=(lv.halo||0)+.2;g.save();g.globalCompositeOperation='lighter';g.fillStyle=`rgba(120,130,190,${.07+.12*hl})`;g.beginPath();g.moveTo(162,182);g.lineTo(368,182);g.lineTo(1080,1000);g.lineTo(360,1000);g.closePath();g.fill();g.restore();
 for(let i=0;i<40;i++){const x=200+H(i*3.1)*900+vn(i,t*.3)*40,y=200+H(i*5.7)*700-((t*14+H(i)*300)%300);g.fillStyle=`rgba(200,200,255,${.08+H(i*9)*.15})`;g.fillRect(x,y,3,3)}}

function dominantMem(mems){return mems.find(m=>m.role!=='witness')||mems[0]}

// ---------------- MEMORY ----------------
MEMORY({who:'I',scion:10,lineage:'Schaefer, McPhail & Warren — Image Deformation Using Moving Least Squares (2006)',
 op:'Cut a fragment of the remembered shot onto a mesh and move-least-squares warp it from its true landmarks (frame, Inigo, the other) to dream-drifting targets; the deformation family is the feeling.',
 made:'Remembered stills are crops of the actual deed frames on a 12×7 triangle mesh, tinted by feeling and softened by age; the sacks are MLS rigs whose outlines bend through rigid control-point maps. The room is Inigo\'s moonlit attic floor.',
 moved:'Every handle wanders on smooth hashed noise (older memories wander farther) while the feeling drags specific landmarks: desire turns and draws the two together (similarity), fear stretches the other taller (affine), guilt sags and tilts the frame (rigid). Belief silhouettes grow, shrink and approach from Inigo\'s prior to posterior estimate; archetype levers scale, sink, light, shadow and grey him.',
 flash(g,t,mark,mems,K,X){const st=(X&&X.state)||{};const lv=(st.levers&&st.levers.I)||{};
  const tempo=1+.5*(lv.tempo||0);const tt=t*tempo;const ex=mark.x+mark.w/2,ey=mark.y+mark.h*.25;
  const inA=sm(0,.35,tt),out=1-sm(1.1,1.5,tt),env=inA*out;
  // the present bends first: a ripple through the frame round him, dragged by the same solver
  try{const R=260;const rx=clamp(0,1920-2*R,ex-R),ry=clamp(0,1080-2*R,mark.y+mark.h/2-R);const cv=document.createElement('canvas');cv.width=cv.height=2*R;cv.getContext('2d').drawImage(g.canvas,rx,ry,2*R,2*R,0,0,2*R,2*R);
   const P=[0,0,2*R,0,2*R,2*R,0,2*R,R,R],Q=P.slice();const a=env*26;Q[8]+=Math.sin(tt*3)*a;Q[9]+=-a*.8;
   const f=MLS(P,Q,null,'similarity',1.2);g.save();warpImage(g,cv,(u,v)=>{const p=f(u,v);return[rx+p[0],ry+p[1]]},8,8);g.restore()}catch(e){}
  g.save();g.fillStyle=`rgba(8,6,20,${.5*env})`;g.fillRect(0,0,1920,1080);g.restore();
  if(!mems||!mems.length){ // nothing carried: a blank bubble that drifts up and pops
   g.save();g.globalAlpha=.5*env;g.strokeStyle='rgba(220,220,255,.7)';g.lineWidth=3;g.beginPath();g.ellipse(ex+vn(3,tt)*20,ey-80-tt*60,40+20*inA,30+14*inA,0,0,TAU);g.stroke();g.restore();return}
  const m=mems[0];const feel=feelingOf(m,st);const fr=fragment(m,feel);
  let S=(680/fr.cv.width)*(1+.2*(lv.loom||0)-.25*(lv.shrink||0))*(.75+.35*(m.weight||.3));const fw=fr.cv.width*S,fh=fr.cv.height*S;
  let ox=clamp(20,1900-fw,ex-fw/2),oy=Math.max(20,mark.y-fh*1.35-60)-tt*20;if(oy<20)oy=clamp(20,1060-fh,mark.y+mark.h+20);
  // second memory behind, recombining with the first
  if(mems[1]){const m2=mems[1],f2=feelingOf(m2,st),fr2=fragment(m2,f2);const S2=S*.6;const o2x=ox+fw*.55+vn(11,tt)*30,o2y=oy-fh*.2;
   const d2=dreamMap(fr2,m2,f2,o2x,o2y,S2,tt,91,1,{bloom:inA,from:[ex,ey]});drawFragment(g,fr2,d2,.45*env*(1-.06*m2.ago),8,5,'screen')}
  const dm=dreamMap(fr,m,feel,ox,oy,S,tt,17,1.2,{bloom:sm(0,.4,tt),from:[ex,ey],grow:1.35});
  // the thread from his ears to what he is remembering
  g.save();g.globalAlpha=.6*env;g.strokeStyle='rgba(200,190,230,.6)';g.lineWidth=2;g.beginPath();g.moveTo(ex-mark.w*.45,ey);g.quadraticCurveTo(ex-80,oy+fh+40,ox+fw*.3,oy+fh*.85);g.moveTo(ex+mark.w*.45,ey);g.quadraticCurveTo(ex+80,oy+fh+40,ox+fw*.7,oy+fh*.85);g.stroke();g.restore();
  if(feel==='guilt'){for(let e=2;e>=1;e--){const de=dreamMap(fr,m,feel,ox+e*14,oy+e*18,S,tt-e*.18,17,1.2,{bloom:1,from:[ex,ey]});drawFragment(g,fr,de,.18*env,8,5)}}
  drawFragment(g,fr,dm,env*(1-.05*Math.min(8,m.ago))*(1-.5*(lv.grey||0)),12,7);
  // who: the other, as Inigo now believes it, standing small beside the bubble
  try{const{b0,b1}=beliefFor(X.ledger,m.k,m.other,st);const bx=ox+fw+70>1880?ox-70:ox+fw+70;g.save();g.translate(bx,oy+fh);g.scale(.5,.5);drawBelief(g,m.other,b0,b1,sm(.3,1.0,tt),K,st,0,0,tt,env,true);g.restore()}catch(e){}
 },
 beat(g,t,mems,st,K,X){const lv=(st.levers&&st.levers.I)||{};const alive=!st.alive||st.alive.I!==false;const L=X&&X.ledger;
  const tempo=1+.5*(lv.tempo||0);const tt=t*tempo;room(g,tt,lv);
  const floor=930,IX=430;const body=(st.body&&st.body.I)||[];
  const scale=2.1*(1+.25*(lv.loom||0))*(1-.3*(lv.shrink||0))*(body.includes('emptied')?.92:1);
  if(!alive){ // the others' memory of him: the death still unbending into blank, his empty sack in flour, the living at the edge
   const dk=st.deadAt?st.deadAt.I:null;const e=L&&dk!=null?L.ev[dk]:null;
   if(e){const m={k:dk,deed:e.deed,A:e.A,V:e.V,role:'victim',other:e.A,ago:0,weight:.8,still:X.still(e)};const fr=fragment(m,'witness');const S=900/fr.cv.width;const ox=760,oy=110;
    const dm=dreamMap(fr,m,'witness',ox,oy,S,tt,5,1+tt*.6,{bloom:1-sm(.8,2.4,t)*.85,from:[IX,floor-60]});drawFragment(g,fr,dm,.75*(1-sm(1.6,2.5,t)*.7),12,7)}
   g.fillStyle='rgba(251,247,238,.5)';g.beginPath();g.ellipse(IX,floor+6,200,22,0,0,TAU);g.fill();
   drawSack(g,'I',IX,floor,scale,{slump:1,squash:.9,ears:-.1},K,{grey:1,tags:body});
   let j=0;for(const o of IDS)if(o!=='I'&&(!st.alive||st.alive[o]!==false)){const gl=st.mind&&st.mind[o]&&st.mind[o].I?st.mind[o].I.guilt:0;drawSack(g,o,1500+j*150,floor,1.1+.4*gl,{lean:-.15-.3*gl},K,{sil:'#07060c',alpha:.9});j++}
   return}
  // Inigo, slumped on the floor in the moonlight; levers set his size, sink, light and shadow
  const top=mems.length?dominantMem(mems):null;const feel=top?feelingOf(top,st):'none';
  const breath=Math.sin(tt*1.6)*.02;const drowsy=body.includes('drowsy')?.3:0;
  const pose={slump:Math.min(.95,.5+.35*(lv.weight||0)+drowsy+(feel==='fear'?.15:0)-(feel==='pride'?.3:0)),lean:(feel==='desire'?.25:feel==='guilt'?-.3:0)+.1*(lv.loom||0)+Math.sin(tt*.6)*.04*(1+drowsy),
   ears:feel==='fear'?.9:-.1-.3*(lv.shrink||0),earSwing:Math.sin(tt*1.1)*(.4+.4*(1-(lv.weight||0))),breath,squash:.2*(lv.weight||0)};
  const sh=lv.shadow||0;g.save();g.globalAlpha=.35+.4*sh;g.translate(IX+40,floor);g.transform(1,0,1.1+1.6*sh,-.25-.4*sh,0,0);drawSack(g,'I',0,0,scale,pose,K,{sil:'#04030a'});g.restore();
  const hl=(lv.halo||0);if(hl>.03){const gr=g.createRadialGradient(IX,floor-120,20,IX,floor-120,420);gr.addColorStop(0,`rgba(230,220,255,${.3*hl})`);gr.addColorStop(1,'rgba(230,220,255,0)');g.fillStyle=gr;g.fillRect(IX-450,floor-560,900,600)}
  drawSack(g,'I',IX,floor,scale,pose,K,{grey:Math.max(lv.grey||0,body.includes('greyed')?.6:0),tags:body});
  const ear=[IX,floor-K.CAST.I.h*scale*.55];
  if(!mems.length){ // at peace / bored: the moon window itself drifts above him as a dream with nothing in it
   const cv=document.createElement('canvas');cv.width=240;cv.height=300;const q=cv.getContext('2d');q.drawImage(g.canvas,150,170,230,300,0,0,240,300);
   const ox=650,oy=200,S=1.4,P=[0,0,240,0,240,300,0,300,120,150].map((v,i)=>i%2?oy+v*S:ox+v*S),Q=P.slice();
   for(let i=0;i<5;i++){Q[2*i]+=vn(i,tt*.4)*50;Q[2*i+1]+=vn(i+9,tt*.35)*40}Q[8]+=Math.sin(tt)*60;
   const f=MLS(P,Q,null,'similarity',1);drawFragment(g,{cv},{map:(u,v)=>f(ox+u*S,oy+v*S),Q},.4,8,8);return}
  // the dream: up to three remembered fragments; later in the beat the minor ones drift onto the major and swap partners
  const shown=mems.slice(0,3);const rec=sm(1.0,2.3,t);const slots=[[620,70,860],[1440,80,400],[1010,610,340]];let main=null;
  for(let j=shown.length-1;j>=0;j--){const m=shown[j];const f=feelingOf(m,st);const fr=fragment(m,f);const sl=slots[j];
   let S=sl[2]/fr.cv.width*(j?(.8+.3*m.weight):(.85+.25*m.weight));let ox=sl[0],oy=sl[1];
   if(j&&main){ox=lerp(ox,main.ox+main.fw*(j===1?.62:.2),rec*.55);oy=lerp(oy,main.oy+main.fh*(j===1?.1:.55),rec*.55)}
   const ex={bloom:sm(.0,.5+.2*j,t),from:ear,grow:1.3};
   if(j&&main){ex.pull=[main.ox+main.fw*.5,main.oy+main.fh*.6,rec*.5]}
   const dm=dreamMap(fr,m,f,ox,oy,S,tt,13+j*29,j?1:1.25,ex);const a=(j?.55:.95)*(1-.06*Math.min(8,m.ago))*(1-.4*(lv.grey||0));
   if(j===0)main={ox,oy,fw:fr.cv.width*S,fh:fr.cv.height*S,dm,fr,m,f};
   if(j===0&&f==='guilt')for(let e=2;e>=1;e--){const de=dreamMap(fr,m,f,ox+e*22,oy+e*26,S,tt-e*.2,13,1.25,{bloom:ex.bloom,from:ear});drawFragment(g,fr,de,.16,10,6)}
   drawFragment(g,fr,dm,a,j?9:12,j?5:7,j?'screen':null);
   // thread from the ears
   g.save();g.globalAlpha=.35*(j?.5:1);g.strokeStyle='rgba(200,190,235,.7)';g.lineWidth=2;const tq=dm.Q;g.beginPath();g.moveTo(ear[0]+40,ear[1]);g.bezierCurveTo(ear[0]+200,ear[1]-80,tq[16]-150,tq[17]+120,tq[16],tq[17]);g.stroke();g.restore()}
  // belief update about the other in the strongest memory: prior -> posterior as size and nearness
  if(top&&L){const{b0,b1}=beliefFor(L,top.k,top.other,st);drawBelief(g,top.other,b0,b1,sm(.5,1.8,t),K,st,1800,floor,tt,1)}
 },
 sound(ac,out,t0,kind,mems,K){const S=K.SND;const dur=kind==='flash'?1.5:2.5;const m=mems&&mems[0];
  // Inigo's pitchless breath carries everything
  S.say(ac,out,'I',t0,'breathe',dur,-.4);S.say(ac,out,'I',t0+.05,'breathe',dur*.9,.3);
  if(!m){S.cloud(ac,out,t0+.2,dur-.4,12,{bp:3000,a:.07,d:[.1,.3]},u=>Math.sin(Math.PI*u));return}
  // the remembered event returns transformed: the other's voice, slowed into a drifting, detuned grain cloud
  const V=S.VOICE[m.other]||S.VOICE.R;const base=V.base-12+(m.role==='victim'?0:5);const w=Math.min(1,.4+m.weight);
  S.cloud(ac,out,t0+.25,dur*.8,30*w,{pitches:[base,base+7,base+12,base+3+(m.ago%3)],a:.15*w*(1-.05*Math.min(8,m.ago)),d:[.15,.4],glide:-.08,spread:.6},u=>Math.sin(Math.PI*u));
  S.say(ac,out,m.other,t0+.4,'react',1.3*w,.5);
  if(m.role==='doer'&&m.weight>.5)for(let i=0;i<3;i++)S.say(ac,out,m.other,t0+.9+i*.5,'tick',.4/(i+1),.6); // haunted: it comes back, smaller each time
  if(mems[1]){const V2=S.VOICE[mems[1].other]||S.VOICE.B;S.cloud(ac,out,t0+dur*.45,dur*.45,14,{pitches:[V2.base-12,V2.base-5],a:.09,d:[.2,.5],spread:.9},u=>Math.sin(Math.PI*u))}
 }});
})();
