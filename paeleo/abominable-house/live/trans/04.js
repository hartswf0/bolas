// TRANSITION 04 · Knifing (Foldès drawn lines) -> Prostitution (state-machine parlour)
// SCION 35 · Moving Least Squares, gesture warp. The whole join is one deformation problem:
// both pictures are cut into textured triangle meshes and pulled by a few control handles
// (Schaefer, Lewis, Warren 2006: w_i = 1/|p_i - v|^2, closed-form affine / similarity / rigid maps).
// The room uses the RIGID family (architecture should rotate, not shear); sacks use AFFINE
// (cloth should squash and stretch); a hesitating sack's top uses SIMILARITY (leans, keeps shape).
// Outgoing room: handles p -> c(u); incoming parlour: handles q -> c(u); c(0)=p, c(1)=q, so both
// end frames are identity maps. Invariant (testable): when c = p the mesh map is the identity
// (vertex error 0 px) — the seams are drawn from the same cached layers the film composites.
(function(){
const W=1920,H=1080,DUR=3.2,T_OUT=5.99,T_IN=0.001;
const IDS=['R','B','I','O'];
// ---------------- MLS solver (point handles) ----------------
function mls(P,Q,v,fam){let sw=0,px=0,py=0,qx=0,qy=0;const w=[];
 for(let i=0;i<P.length;i++){const dx=P[i][0]-v[0],dy=P[i][1]-v[1],d2=dx*dx+dy*dy;if(d2<1e-6)return [Q[i][0],Q[i][1]];const wi=1/d2;w.push(wi);sw+=wi;px+=wi*P[i][0];py+=wi*P[i][1];qx+=wi*Q[i][0];qy+=wi*Q[i][1]}
 px/=sw;py/=sw;qx/=sw;qy/=sw;const vx=v[0]-px,vy=v[1]-py;
 if(fam==='affine'){let a=0,b=0,d=0,m11=0,m12=0,m21=0,m22=0;
  for(let i=0;i<P.length;i++){const ax=P[i][0]-px,ay=P[i][1]-py,bx=Q[i][0]-qx,by=Q[i][1]-qy,wi=w[i];a+=wi*ax*ax;b+=wi*ax*ay;d+=wi*ay*ay;m11+=wi*ax*bx;m12+=wi*ax*by;m21+=wi*ay*bx;m22+=wi*ay*by}
  const det=a*d-b*b;if(Math.abs(det)<1e-9)return [vx+qx,vy+qy];const i11=d/det,i12=-b/det,i22=a/det;
  const M11=i11*m11+i12*m21,M12=i11*m12+i12*m22,M21=i12*m11+i22*m21,M22=i12*m12+i22*m22;
  return [vx*M11+vy*M21+qx,vx*M12+vy*M22+qy]}
 let mu=0,c=0,s=0;for(let i=0;i<P.length;i++){const ax=P[i][0]-px,ay=P[i][1]-py,bx=Q[i][0]-qx,by=Q[i][1]-qy,wi=w[i];mu+=wi*(ax*ax+ay*ay);c+=wi*(ax*bx+ay*by);s+=wi*(ax*by-ay*bx)}
 if(fam==='rigid'){const n=Math.hypot(c,s)||1;c/=n;s/=n}else{c/=mu||1;s/=mu||1}
 return [vx*c-vy*s+qx,vx*s+vy*c+qy]}
// textured triangle: maps source triangle (image px) onto destination triangle
function tri(g,img,s0,s1,s2,d0,d1,d2){
 const den=(s1[0]-s0[0])*(s2[1]-s0[1])-(s2[0]-s0[0])*(s1[1]-s0[1]);if(Math.abs(den)<1e-6)return;
 const ux=s1[0]-s0[0],uy=s1[1]-s0[1],vx=s2[0]-s0[0],vy=s2[1]-s0[1];
 const a=((d1[0]-d0[0])*vy-(d2[0]-d0[0])*uy)/den,c=((d2[0]-d0[0])*ux-(d1[0]-d0[0])*vx)/den;
 const b=((d1[1]-d0[1])*vy-(d2[1]-d0[1])*uy)/den,d=((d2[1]-d0[1])*ux-(d1[1]-d0[1])*vx)/den;
 const e=d0[0]-a*s0[0]-c*s0[1],f=d0[1]-b*s0[0]-d*s0[1];
 const cx=(d0[0]+d1[0]+d2[0])/3,cy=(d0[1]+d1[1]+d2[1])/3,ex=p=>{const dx=p[0]-cx,dy=p[1]-cy,l=Math.hypot(dx,dy)||1;return[p[0]+dx/l*1.2,p[1]+dy/l*1.2]};
 const A0=ex(d0),A1=ex(d1),A2=ex(d2);
 g.save();g.beginPath();g.moveTo(A0[0],A0[1]);g.lineTo(A1[0],A1[1]);g.lineTo(A2[0],A2[1]);g.closePath();g.clip();g.transform(a,b,c,d,e,f);
 // draw only the source triangle's bounding box (a full-image draw per triangle is ~40x slower)
 const x0=Math.max(0,Math.floor(Math.min(s0[0],s1[0],s2[0])-2)),y0=Math.max(0,Math.floor(Math.min(s0[1],s1[1],s2[1])-2)),x1=Math.min(img.width,Math.ceil(Math.max(s0[0],s1[0],s2[0])+2)),y1=Math.min(img.height,Math.ceil(Math.max(s0[1],s1[1],s2[1])+2));
 if(x1>x0&&y1>y0)g.drawImage(img,x0,y0,x1-x0,y1-y0,x0,y0,x1-x0,y1-y0);g.restore()}
// warp an image whose pixel (0,0) sits at screen (ox,oy): rest handles P, current handles Q.
// Each grid cell is drawn with the least-squares affine of its four mapped corners, without a clip
// (clipping a 1080p canvas per triangle is 20x slower in software); neighbours agree to < 1 px
// wherever the MLS field is smooth, and where it folds the fold is shown, not hidden.
function warp(g,img,ox,oy,P,Q,fam,nx,ny){const iw=img.width,ih=img.height,V=[],cw=iw/nx,ch=ih/ny;
 for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++)V.push(mls(P,Q,[i*cw+ox,j*ch+oy],fam));
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const A=V[j*(nx+1)+i],B=V[j*(nx+1)+i+1],C=V[(j+1)*(nx+1)+i],D=V[(j+1)*(nx+1)+i+1];
  const a=((B[0]-A[0])+(D[0]-C[0]))/2/cw,b=((B[1]-A[1])+(D[1]-C[1]))/2/cw,c=((C[0]-A[0])+(D[0]-B[0]))/2/ch,d=((C[1]-A[1])+(D[1]-B[1]))/2/ch;
  const mx=(A[0]+B[0]+C[0]+D[0])/4,my=(A[1]+B[1]+C[1]+D[1])/4,sx=(i+.5)*cw,sy=(j+.5)*ch;
  g.setTransform(a,b,c,d,mx-a*sx-c*sy,my-b*sx-d*sy);
  const x0=Math.max(0,i*cw-1.5),y0=Math.max(0,j*ch-1.5),x1=Math.min(iw,(i+1)*cw+1.5),y1=Math.min(ih,(j+1)*ch+1.5);
  g.drawImage(img,x0,y0,x1-x0,y1-y0,x0,y0,x1-x0,y1-y0)}
 g.setTransform(1,0,0,1,0,0)}
const lerpP=(a,b,u)=>[a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u];
// ---------------- the room handles: knifing line-room -> parlour ----------------
// knifing: pendant lamp bulb, door corners, wall/floor line, light pool; parlour: floor lamp, door, wainscot, floor
const RP=[[960,236],[1560,300],[1720,300],[1560,670],[1720,670],[300,670],[1000,670],[960,950],[0,0],[1920,0],[0,1080],[1920,1080],[0,540],[1920,540],[960,1080],[480,0],[1440,0]];
const RQ=[[70,280],[1405,350],[1730,350],[1405,960],[1730,960],[300,705],[1000,705],[900,1000],[0,0],[1920,0],[0,1080],[1920,1080],[0,540],[1920,540],[960,1080],[480,0],[1440,0]];
function roomHandles(e,K){return RP.map((p,i)=>{const q=RQ[i];let x=lerpP(p,q,e);
  if(i===0){const sw=Math.sin(e*Math.PI);x=[x[0],x[1]-70*sw]}            // the lamp is carried on an arc, a pendulum let go
  if(i>=1&&i<=4){const sw=Math.sin(e*Math.PI);x=[x[0]+40*sw*(i%2?-1:1),x[1]]} // the door frame breathes open as it swells
  return x})}
// ---------------- cached layers (one render per film) ----------------
let CACHE={key:'',P:null};
const mk=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c};
function leverBox(b,lv){const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}}
function layersOf(D,lt,e,st,K){const order=D.layers||['bg','V','A'];const mkk=D.marks?D.marks(lt,e.A,e.V,K):null;const out={order,bg:mk(),A:mk(),V:mk(),box:{}};
 for(const ly of order){const q=out[ly].getContext('2d');q.save();try{D.draw(q,lt,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}q.restore()}
 // levers baked in exactly as the film composites them
 for(const ly of['A','V']){if(!mkk)continue;const who=ly==='A'?e.A:e.V,lv=st.levers[who],b=mkk[ly];const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
  if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);
  const c2=mk(),q=c2.getContext('2d');q.filter=fl.join(' ')||'none';q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(out[ly],0,0);out[ly]=c2;out.box[ly]=leverBox(b,lv)}
 return out}
function cropRect(b){const x0=Math.max(0,Math.floor(b.x-b.w*.45-40)),y0=Math.max(0,Math.floor(b.y-b.h*.55-60)),x1=Math.min(W,Math.ceil(b.x+b.w*1.45+40)),y1=Math.min(H,Math.ceil(b.y+b.h+70));return{x:x0,y:y0,w:Math.max(2,x1-x0),h:Math.max(2,y1-y0)}}
// lift a sack out of its layer: the sprite, and the remainder of the layer goes to the room
function lift(Lr){const S={};const bgp=mk(),q=bgp.getContext('2d');q.drawImage(Lr.bg,0,0);
 for(const ly of Lr.order){if(ly==='bg')continue;const b=Lr.box[ly];if(!b){q.drawImage(Lr[ly],0,0);continue}const r=cropRect(b);
  const sp=document.createElement('canvas');sp.width=r.w;sp.height=r.h;sp.getContext('2d').drawImage(Lr[ly],-r.x,-r.y);
  const rest=mk(),rq=rest.getContext('2d');rq.drawImage(Lr[ly],0,0);rq.clearRect(r.x,r.y,r.w,r.h);q.drawImage(rest,0,0);S[ly]={img:sp,r,b}}
 return{bg:bgp,S}}
function composite(Lr){const c=mk(),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,W,H);for(const ly of Lr.order)q.drawImage(Lr[ly],0,0);return c}
// ---------------- the plan: who travels where (pure function of the ledger) ----------------
function plan(X,K){const L=X.ledger,k=X.k,eo=L.ev[k-1],ei=L.ev[k],so=L.states[k-1],si=L.states[k];
 const Do=X.DEEDS?X.DEEDS[eo.deed]:(window.DEEDS||{})[eo.deed],Di=X.DEEDS?X.DEEDS[ei.deed]:(window.DEEDS||{})[ei.deed];
 const mo=Do.marks(T_OUT,eo.A,eo.V,K),mi=Di.marks(T_IN,ei.A,ei.V,K);
 const bo={},bi={},ro={},ri={};bo[eo.A]=leverBox(mo.A,so.levers[eo.A]);bo[eo.V]=leverBox(mo.V,so.levers[eo.V]);ro[eo.A]='A';ro[eo.V]='V';
 bi[ei.A]=leverBox(mi.A,si.levers[ei.A]);bi[ei.V]=leverBox(mi.V,si.levers[ei.V]);ri[ei.A]='A';ri[ei.V]='V';
 const mem=LEDGER.memories(L,ei.A,k).filter(m=>m.other===ei.V);const hes=mem.length?Math.min(1,mem[0].weight):0;
 const sacks=[];
 for(const s of IDS){const inO=s in bo,inI=s in bi;if(!inO&&!inI)continue;
  const lv=si.levers[s],tempo=lv.tempo||0,weight=lv.weight||0;
  let kind=inO&&inI?'staying':inO?'leaving':'entering';
  const deadO=!so.alive[s]||!si.alive[s];                     // dead by the end of the knifing
  const sk={id:s,kind,ro:ro[s],ri:ri[s],dead:!si.alive[s],ghost:inI&&!si.alive[s],hes:s===ei.A?hes:0,
   t0:DUR*(.12-.04*tempo),t1:DUR*(.9-.04*tempo),weight,tempo,lv};
  if(kind==='staying'){sk.b0=bo[s];sk.b1=bi[s]}
  if(kind==='leaving'){const b=bo[s];sk.b0=b;
   if(sk.dead){sk.b1={x:b.x-b.w*.08,y:b.y+b.h*.55,w:b.w*1.16,h:b.h*.45};sk.body=true}  // a body: pressed into the floor where it lies
   else{const side=b.x+b.w/2<960?-1:1;sk.crawl=b.h<b.w*.45;sk.b1={x:side<0?-b.w*1.6-80:W+b.w*.6+80,y:b.y+10,w:b.w,h:b.h}}}
  if(kind==='entering'){const b=bi[s];sk.b1=b;
   if(sk.ghost){sk.b0={x:b.x+b.w*.1,y:b.y+b.h-8,w:b.w*.8,h:8}}                   // a ghost rises out of the floor
   else{sk.door=true;sk.t0=DUR*(.36-.04*tempo);sk.b0={x:1560,y:960-b.h*.95,w:b.w*.12,h:b.h*.95}}}          // a living sack is pulled out of the door
  // a dead knifing victim who acts next leaves its body and rises as a ghost
  if(kind==='staying'&&sk.ghost){sk.bodyCopy=true;const b0=sk.b0,b1=sk.b1;sk.bm={x:b0.x+b0.w/2-b1.w/2,y:b0.y+b0.h-b1.h-30,w:b1.w,h:b1.h}} // rises out of the body first, then goes
  sacks.push(sk)}
 // the dead who are elsewhere in the house, and the evidence so far
 const others=IDS.filter(s=>!(s in bo)&&!(s in bi)&&!si.alive[s]);
 const ev=si.evidence.filter(x=>x.k<k-1);
 return{eo,ei,so,si,sacks,others,ev,hes}}
// travel of one sack: handles BL BR TL TR C at time u (screen coordinates), plus hop events
function hopsOf(sk){const a=[sk.b0.x+sk.b0.w/2,sk.b0.y+sk.b0.h],b=[sk.b1.x+sk.b1.w/2,sk.b1.y+sk.b1.h];const d=Math.hypot(b[0]-a[0],b[1]-a[1]);
 if(sk.body||sk.ghost||sk.crawl||sk.door&&d<40)return 0;return Math.max(1,Math.min(5,Math.round(d/(Math.max(sk.b0.w,sk.b1.w)*1.1+60))))}
function progress(sk,u,K){let p=K.cl(0,1,(u-sk.t0)/(sk.t1-sk.t0));
 if(sk.hes>.3){const hold=.28*sk.hes;// hesitation: stops halfway, the memory of the other holds it back
  const q=p<.45?p/.45*.5:p<.45+hold?.5:.5+(p-.45-hold)/(.55-hold)*.5;p=K.cl(0,1,q)}
 return p}
function boxHandles(b){return[[b.x,b.y+b.h],[b.x+b.w,b.y+b.h],[b.x,b.y],[b.x+b.w,b.y],[b.x+b.w/2,b.y+b.h*.5]]}
function travel(sk,u,K){if(sk.door){const C=roomHandles(K.sm(.05*DUR,.92*DUR,Math.max(u,sk.t0)),K),dx=(C[1][0]+C[2][0]+C[3][0]+C[4][0])/4,dy=(C[3][1]+C[4][1])/2,dh=dy-(C[1][1]+C[2][1])/2;sk.b0={x:dx-sk.b1.w*.06,y:dy-Math.min(sk.b1.h,dh*.9),w:sk.b1.w*.12,h:Math.min(sk.b1.h,dh*.9)}}
 const p=progress(sk,u,K),n=hopsOf(sk);
 if(sk.bm){const a=p<.45?sk.b0:sk.bm,b=p<.45?sk.bm:sk.b1,q=p<.45?K.sm(0,.45,p):K.sm(.45,1,p),L=(k)=>K.lerp(a[k],b[k],q);const bob=Math.sin(p*Math.PI)*Math.sin(u*5)*6;
  const x=L('x')+L('w')/2,y=L('y')+L('h')+bob*(1-K.sm(.85,1,p)),w=L('w'),h=L('h');return{Q:[[x-w/2,y],[x+w/2,y],[x-w/2,y-h],[x+w/2,y-h],[x,y-h/2]],p,x,y,w,h,n:0}}const e=n?p:K.sm(0,1,p);
 const b0=sk.b0,b1=sk.b1,sz=K.sm(0,1,p);const w=K.lerp(b0.w,b1.w,sz),h=K.lerp(b0.h,b1.h,sz);
 const x=K.lerp(b0.x+b0.w/2,b1.x+b1.w/2,e),y=K.lerp(b0.y+b0.h,b1.y+b1.h,e);
 let lift=0,sq=0,trail=0;
 if(n){const ph=(p*n)%1,env=K.sm(0,.04,p)*(1-K.sm(.96,1,p));const HH=h*(.28-.12*K.cl(-1,1,sk.weight));lift=HH*Math.sin(Math.PI*ph)*env;
  sq=(Math.pow(1-Math.sin(Math.PI*ph),3)*.16-.06*Math.sin(Math.PI*ph))*env;trail=-(b1.x-b0.x>0?1:-1)*Math.cos(Math.PI*ph)*.12*w*env}
 if(sk.crawl){const env=K.sm(0,.05,p)*(1-K.sm(.95,1,p));trail=Math.sin(p*Math.PI*10)*.08*w*env;sq=-Math.max(0,Math.sin(p*Math.PI*10))*.5*env} // an emptied survivor drags itself out: inchworm on its top handles
 const by=y-lift,hh=h*(1-sq),ww=w*(1+sq*.7);let lean=0;
 if(sk.hes>.3){const hp=K.sm(.4,.5,p)*(1-K.sm(.5+.28*sk.hes,.6+.28*sk.hes,p));lean=-hp*.22*sk.hes*ww+hp*Math.sin(u*40)*3}
 const Q=[[x-ww/2,by],[x+ww/2,by],[x-ww/2+trail+lean,by-hh],[x+ww/2+trail*.6+lean,by-hh],[x+lean*.4,by-hh*.5]];
 return{Q,p,x,y:by,w:ww,h:hh,n}}
// ---------------- draw ----------------
function build(X,K){const key=X.film.join(',')+'|'+X.k;if(CACHE.key===key)return CACHE.P;
 const P=plan(X,K);const Do=X.DEEDS[P.eo.deed],Di=X.DEEDS[P.ei.deed];
 const Lo=layersOf(Do,T_OUT,P.eo,P.so,K),Li=layersOf(Di,T_IN,P.ei,P.si,K);
 P.fullO=composite(Lo);P.fullI=composite(Li);P.lo=lift(Lo);P.li=lift(Li);
 // the dead elsewhere: their own last picture, taken from the deed that killed them
 P.bodies=P.others.map((s,i)=>{const kd=P.si.deadAt[s];const e=P.so&&X.ledger.ev[kd];if(!e)return null;const D=X.DEEDS[e.deed];if(!D||!D.marks)return null;
  const role=e.V===s?'V':'A';const c=mk(),q=c.getContext('2d');try{D.draw(q,5.99,e.A,e.V,K,{layer:role,carry:X.ledger.states[kd].body})}catch(err){return null}
  const b=D.marks(5.99,e.A,e.V,K)[role];const r=cropRect(b);const sp=document.createElement('canvas');sp.width=r.w;sp.height=r.h;sp.getContext('2d').drawImage(c,-r.x,-r.y);return{img:sp,r,b,s}}).filter(Boolean);
 CACHE={key,P};return P}
let SC=null;function scratch(){if(!SC)SC=mk();const q=SC.getContext('2d');q.setTransform(1,0,0,1,0,0);q.clearRect(0,0,W,H);return q}
function scan(g,a){if(a<=0)return;g.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2)}
function drawSprite(g,S,Q,alpha,fam,filter){if(!S||alpha<=0.003)return;const q=scratch();warp(q,S.img,S.r.x,S.r.y,boxHandles(S.b),Q,fam,8,8);g.save();g.globalAlpha=Math.min(1,alpha);if(filter)g.filter=filter;g.drawImage(SC,0,0);g.restore()}
TRANSITION({k:4,scion:35,lineage:'Moving Least Squares — Gesture Warp Swarm',
 op:'both rooms and every sack are cut into textured triangle meshes and pulled by a dozen control handles under closed-form MLS maps (rigid for the room, affine for cloth, similarity for a hesitating lean); the outgoing picture is pulled p→c(u), the incoming pulled back q→c(u), c(0)=p, c(1)=q',
 made:'The knifing room\'s pencil lines and the parlour\'s panelled wall, each a single cached picture cut into a 14×8 triangle mesh; each sack is its own lifted sprite cut into a 6×6 mesh, with five handles at its feet, ear corners and belly.',
 moved:'Handle trajectories move everything: the pendant lamp is carried on an arc to become the floor lamp, the door corners swell into the parlour door, the floor line drops to the wainscot. Sacks hop on their feet handles (ears trail, squash on landing), a dead body is pressed into the floor, a newcomer is pulled out of the door as a sliver, and a sack with a strong memory of its victim stops halfway and leans back.',
 dur:DUR, plan,
 draw(g,u,X,K){const P=build(X,K);
  const imO=P.so.impossible.find(q=>q.k===X.k-1)||X.ledger.states[X.k].impossible.find(q=>q.k===X.k-1),imI=X.ledger.states[X.k+1].impossible.find(q=>q.k===X.k);
  const E=K.sm(.05*DUR,.92*DUR,u);
  if(E<=0){g.drawImage(P.fullO,0,0);scan(g,imO?1:0);return}
  if(u>=DUR-.03&&E>=1){g.drawImage(P.fullI,0,0);scan(g,imI?1:0);return}
  // 1 · the room: outgoing pulled forward, incoming pulled back, the incoming laid over as its map settles
  const C=roomHandles(E,K);g.fillStyle='#000';g.fillRect(0,0,W,H);
  g.drawImage(P.lo.bg,0,0);warp(g,P.lo.bg,0,0,RP,C,'rigid',24,14);   // identity underlay catches any sub-pixel crack
  const wb=K.sm(.22,.78,E);if(wb>0){const q=scratch();q.drawImage(P.li.bg,0,0);warp(q,P.li.bg,0,0,RQ,C,'rigid',24,14);g.save();g.globalAlpha=wb;g.drawImage(SC,0,0);g.restore()}
  // 2 · the house remembers: evidence of earlier deeds along the skirting, the dead lying where they were left
  const env=Math.pow(Math.sin(Math.PI*K.cl(0,1,u/DUR)),.8);
  P.ev.forEach((ev,i)=>{const n=P.ev.length,x=180+(i+.5)/Math.max(1,n)*1100,bx={x:x-70,y:930+(i%2)*55,w:140,h:90};const CQ=X.CONSEQS[ev.deed];
   g.save();g.globalAlpha=env*.95;try{if(CQ&&CQ.trace)CQ.trace(g,bx,X.k-1-ev.k,K);else{g.fillStyle='#fbf7ee';g.fillRect(bx.x+50,bx.y+50,40,10)}}catch(err){}g.restore()});
  P.bodies.forEach((B,i)=>{const s=.6,bw=B.b.w*s,bh=B.b.h*s,x0=120+i*260,y1=1000;const Q=[[x0,y1],[x0+bw,y1],[x0,y1-bh],[x0+bw,y1-bh],[x0+bw/2,y1-bh/2]];
   drawSprite(g,B,Q,env*.85,'affine','grayscale(1) brightness(.7)')});
  // 3 · the cast: leaving, staying, entering
  for(const sk of P.sacks){const T=travel(sk,u,K);
   const So=sk.ro?P.lo.S[sk.ro]:null,Si=sk.ri?P.li.S[sk.ri]:null;
   const fam=sk.hes>.3&&T.p>.35&&T.p<.75?'similarity':'affine';
   if(sk.kind==='leaving'){drawSprite(g,So,T.Q,sk.body?1-K.sm(.55,.97,T.p):1,fam);
    if(sk.body){const CQ=X.CONSEQS.knifing;const bx={x:sk.b1.x,y:sk.b1.y-20,w:sk.b1.w,h:sk.b1.h+60};g.save();g.globalAlpha=K.sm(.4,.8,T.p)*(1-K.sm(.85*DUR,DUR-.05,u));try{CQ&&CQ.trace&&CQ.trace(g,bx,0,K)}catch(err){}g.restore()}}
   if(sk.kind==='staying'){
    if(sk.bodyCopy){// the body stays down; what gets up is the ghost
     const b=sk.b0,Qb=boxHandles({x:b.x-b.w*.05,y:b.y+b.h*.4*K.sm(0,1,T.p),w:b.w*1.1,h:b.h*(1-.4*K.sm(0,1,T.p))});drawSprite(g,So,Qb,1-K.sm(.6,.97,T.p),'affine');
     drawSprite(g,Si,T.Q,.12+.88*K.sm(.25,1,T.p),fam,`drop-shadow(0 0 ${Math.round(18*(1-T.p))}px rgba(190,255,210,.8))`)}
    else{drawSprite(g,So,T.Q,1-K.sm(.5,.68,T.p),fam);drawSprite(g,Si,T.Q,K.sm(.38,.56,T.p),fam)}}
   if(sk.kind==='entering'){const a=sk.ghost?.25+.75*K.sm(.1,1,T.p):K.sm(0,.15,T.p);
    drawSprite(g,Si,T.Q,a,fam,sk.ghost?`drop-shadow(0 0 ${Math.round(18*(1-T.p))}px rgba(190,255,210,.8))`:null)}}
  scan(g,imO?1-E:0);scan(g,imI?E:0)},
 sound(ac,out,t0,X,K){const P=plan(X,K),S=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1));
  // the handles are pinned: one tick per handle as each sack is taken hold of
  for(const sk of P.sacks){const x=sk.b0.x+sk.b0.w/2;for(let i=0;i<5;i++)S.grain(ac,out,t0+sk.t0-.08+i*.025,{f:2400+i*310,d:.018,a:.16,pan:pan(x),att:.05})}
  // the room stretches: a rubbery band of grains rising as the mesh is pulled, then settling
  S.cloud(ac,out,t0+.15,DUR*.8,40,{bp:700,q:3,a:.12,d:[.03,.09],glide:.3,noise:.7,f:110,type:'triangle'},u=>Math.sin(Math.PI*u));
  S.grain(ac,out,t0+DUR*.45,{f:330,d:.6,a:.12,glide:-.3,type:'triangle',att:.3}); // the lamp let go on its arc
  S.thump(ac,out,t0+DUR*.74,1.6,70,.5);S.grain(ac,out,t0+DUR*.74,{f:196,d:.35,a:.14,type:'triangle',att:.05,pan:.5}); // the parlour door settles into its frame: the room has arrived
  for(const sk of P.sacks){const n=hopsOf(sk);const tt=p=>{// invert progress (with hesitation) numerically
    for(let i=0;i<=200;i++){const u=sk.t0+(sk.t1-sk.t0+1)*i/200;if(progress(sk,u,K)>=p)return u}return sk.t1};
   for(let h=1;h<=n;h++){const u=tt(h/n),x=K.lerp(sk.b0.x,sk.b1.x,h/n)+sk.b0.w/2;S.say(ac,out,sk.id,t0+u,h===n?'land':'step',h===n?1:1.6,pan(x))}
   if(sk.body||sk.bodyCopy)S.say(ac,out,sk.id,t0+DUR*.35,'sink',.9,pan(sk.b0.x));
   if(sk.ghost)S.cloud(ac,out,t0+sk.t0,1.4,25,{f:440*Math.pow(2,(S.VOICE[sk.id].base+24-69)/12),a:.03,d:[.1,.25],glide:.05},u=>Math.sin(Math.PI*u));
   if(sk.door){S.cloud(ac,out,t0+sk.t0,.5,60,{f:150,glide:-.2,a:.05,d:[.02,.06],noise:.5,type:'triangle',bp:900},u=>1-u);}
   if(sk.hes>.3)S.say(ac,out,sk.id,t0+tt(.5)+.05,'breathe',.9,pan(sk.b0.x))}
  P.ev.forEach((ev,i)=>S.grain(ac,out,t0+.6+i*.18,{f:1200+i*170,d:.05,a:.05,pan:pan(180+(i+.5)/Math.max(1,P.ev.length)*1100),att:.1}))}
});
})();
