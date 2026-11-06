// TRANSITION 06 · Threatening with a Gun (IK corner, revolver) -> Tying and Gagging (Sutherland vector display)
// SCION 12 · Localized Deformation Weights (bounded biharmonic weights, Jacobson/Baran/Popovic/Sorkine 2011).
// The join is a rig: the gun room and every sack are auto-rigged from their cutout masks. Each mask becomes a
// grid graph (only cells the cutout actually covers, so weights cannot bleed across the gap between an ear and
// the head); point handles are pinned on it, and for every handle j a weight w_j minimises sum_i (L w_j)_i^2
// (discrete bilaplacian energy) under 0 <= w_j <= 1, w_j(handle j) = 1, w_j(other handles) = 0, solved by
// projected Gauss-Seidel from a geodesic init, then normalised to a partition of unity. Skinning is linear
// blend with translation handles: v' = v + sum_j w_j(v) (c_j(u) - p_j).
// The painted IK picture dissolves triangle by triangle in order of influence (near a handle first), leaving its
// weight field drawn as isolines: the rig's debug heat map, drawn as light-pen lines, IS the vector display the
// tying shot is made of. The incoming picture is then skinned back from the same handles onto its rest pose.
// Invariants (numerical): w in [0,1], sum_j w_j = 1 at every node, w_j(p_j) = 1; at c = p the map is identity.
(function(){
const W=1920,H=1080,DUR=3.2,T_OUT=5.99,T_IN=0.001,IDS=['R','B','I','O'];
const PH='169,242,210';
// ======================= BBW solver on a masked grid graph =======================
// nx*ny grid, inDom[i] bool, hs = grid indices of handles; returns per-handle weight arrays over the full grid
function bbw(nx,ny,inDom,hs,sweeps){
 const N=nx*ny,id=new Int32Array(N).fill(-1),nodes=[];
 for(let i=0;i<N;i++)if(inDom[i])id[i]=nodes.push(i)-1;
 const M=nodes.length,nb=[],nw=[],deg=new Float64Array(M);
 const DIRS=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,.5],[1,-1,.5],[-1,1,.5],[-1,-1,.5]];
 for(let m=0;m<M;m++){const i=nodes[m],gx=i%nx,gy=(i/nx)|0,a=[],b=[];
  for(const[dx,dy,wt]of DIRS){const x=gx+dx,y=gy+dy;if(x<0||y<0||x>=nx||y>=ny)continue;const q=id[y*nx+x];if(q<0)continue;a.push(q);b.push(wt);deg[m]+=wt}
  nb.push(a);nw.push(b)}
 const hm=hs.map(i=>id[i]);const nH=hm.length;
 // geodesic distance from each handle (Dijkstra, small graphs)
 const geo=hm.map(s=>{const d=new Float64Array(M).fill(Infinity),done=new Uint8Array(M);if(s<0)return d;d[s]=0;
  for(let it=0;it<M;it++){let u=-1,best=Infinity;for(let m=0;m<M;m++)if(!done[m]&&d[m]<best){best=d[m];u=m}if(u<0)break;done[u]=1;
   const A=nb[u],B=nw[u];for(let k=0;k<A.length;k++){const v=A[k],l=B[k]===1?1:1.4142;if(d[u]+l<d[v])d[v]=d[u]+l}}return d});
 const fixed=new Uint8Array(M);hm.forEach(s=>{if(s>=0)fixed[s]=1});
 const reach=new Uint8Array(M);for(let m=0;m<M;m++)for(let j=0;j<nH;j++)if(isFinite(geo[j][m]))reach[m]=1;
 const Wm=[];
 for(let j=0;j<nH;j++){const w=new Float64Array(M);
  for(let m=0;m<M;m++){if(!reach[m])continue;let s=0,me=0;for(let k=0;k<nH;k++){const dd=geo[k][m];const v=dd===0?1e9:1/(dd*dd);s+=v;if(k===j)me=v}w[m]=me/s}
  hm.forEach((s,k)=>{if(s>=0)w[s]=k===j?1:0});
  const r=new Float64Array(M);for(let m=0;m<M;m++){let v=deg[m]*w[m];const A=nb[m],B=nw[m];for(let k=0;k<A.length;k++)v-=B[k]*w[A[k]];r[m]=v}
  const qii=new Float64Array(M);for(let m=0;m<M;m++){let s=deg[m]*deg[m];for(const b of nw[m])s+=b*b;qii[m]=s}
  for(let sw=0;sw<sweeps;sw++)for(let m=0;m<M;m++){if(fixed[m]||!reach[m])continue;
   const A=nb[m],B=nw[m];let q=deg[m]*r[m];for(let k=0;k<A.length;k++)q-=B[k]*r[A[k]];
   let nv=w[m]-q/qii[m];nv=nv<0?0:nv>1?1:nv;const dl=nv-w[m];if(dl===0)continue;w[m]=nv;
   r[m]+=deg[m]*dl;for(let k=0;k<A.length;k++)r[A[k]]-=B[k]*dl}
  Wm.push(w)}
 // partition of unity
 for(let m=0;m<M;m++){let s=0;for(let j=0;j<nH;j++)s+=Wm[j][m];if(s>1e-9)for(let j=0;j<nH;j++)Wm[j][m]/=s}
 // every grid node (outside the domain or unreachable) takes the weights of its nearest reachable domain node
 const src=new Int32Array(N).fill(-1),qu=[];for(let i=0;i<N;i++)if(id[i]>=0&&reach[id[i]]){src[i]=id[i];qu.push(i)}
 for(let h=0;h<qu.length;h++){const i=qu[h],gx=i%nx,gy=(i/nx)|0;for(const[dx,dy]of DIRS){const x=gx+dx,y=gy+dy;if(x<0||y<0||x>=nx||y>=ny)continue;const q=y*nx+x;if(src[q]<0){src[q]=src[i];qu.push(q)}}}
 const out=[];for(let j=0;j<nH;j++){const a=new Float32Array(N);for(let i=0;i<N;i++)a[i]=src[i]>=0?Wm[j][src[i]]:1/nH;out.push(a)}
 // invariants, measured
 let mn=1,mx=0,se=0;for(let i=0;i<N;i++){let s=0;for(let j=0;j<nH;j++){const v=out[j][i];s+=v;if(v<mn)mn=v;if(v>mx)mx=v}se=Math.max(se,Math.abs(s-1))}
 const stat={nodes:M,min:mn,max:mx,sumErr:se,handleOk:hs.every((i,j)=>Math.abs(out[j][i]-1)<1e-6)};
 return{W:out,inDom,stat}}
// ======================= textured triangle =======================
function tri(g,img,s0,s1,s2,d0,d1,d2,s3,d3){
 const den=(s1[0]-s0[0])*(s2[1]-s0[1])-(s2[0]-s0[0])*(s1[1]-s0[1]);if(Math.abs(den)<1e-6)return;
 const ux=s1[0]-s0[0],uy=s1[1]-s0[1],vx=s2[0]-s0[0],vy=s2[1]-s0[1];
 const a=((d1[0]-d0[0])*vy-(d2[0]-d0[0])*uy)/den,c=((d2[0]-d0[0])*ux-(d1[0]-d0[0])*vx)/den;
 const b=((d1[1]-d0[1])*vy-(d2[1]-d0[1])*uy)/den,d=((d2[1]-d0[1])*ux-(d1[1]-d0[1])*vx)/den;
 const e=d0[0]-a*s0[0]-c*s0[1],f=d0[1]-b*s0[0]-d*s0[1];
 const cx=(d0[0]+d1[0]+d2[0])/3,cy=(d0[1]+d1[1]+d2[1])/3,ex=p=>{const dx=p[0]-cx,dy=p[1]-cy,l=Math.hypot(dx,dy)||1;return[p[0]+dx/l*1.1,p[1]+dy/l*1.1]};
 const A0=ex(d0),A1=ex(d1),A2=ex(d2),A3=d3?ex(d3):null,q3=s3||s0;
 const sx=Math.max(0,Math.floor(Math.min(s0[0],s1[0],s2[0],q3[0])-2)),sy=Math.max(0,Math.floor(Math.min(s0[1],s1[1],s2[1],q3[1])-2)),sx1=Math.min(img.width,Math.ceil(Math.max(s0[0],s1[0],s2[0],q3[0])+2)),sy1=Math.min(img.height,Math.ceil(Math.max(s0[1],s1[1],s2[1],q3[1])+2));if(sx1<=sx||sy1<=sy)return;
 g.save();g.beginPath();g.moveTo(A0[0],A0[1]);g.lineTo(A1[0],A1[1]);if(A3)g.lineTo(A3[0],A3[1]);g.lineTo(A2[0],A2[1]);g.closePath();g.clip();g.transform(a,b,c,d,e,f);g.drawImage(img,sx,sy,sx1-sx,sy1-sy,sx,sy,sx1-sx,sy1-sy);g.restore()}
// ======================= a rig: grid + weights + skinning =======================
// rig = {nx,ny,c,ox,oy (screen of node 0), P:[handles screen], W, tau}
function mkRig(nx,ny,c,ox,oy,inDom,hp,sweeps){
 const hs=hp.map(([x,y])=>{let gx=Math.round((x-ox)/c),gy=Math.round((y-oy)/c);gx=Math.max(0,Math.min(nx-1,gx));gy=Math.max(0,Math.min(ny-1,gy));return gy*nx+gx});
 // snap each handle to an in-domain node, distinct
 const used=new Set();for(let j=0;j<hs.length;j++){let i=hs[j];if(!inDom[i]||used.has(i)){const gx0=i%nx,gy0=(i/nx)|0;let best=-1,bd=1e9;
   for(let q=0;q<nx*ny;q++){if(!inDom[q]||used.has(q))continue;const d=(q%nx-gx0)**2+(((q/nx)|0)-gy0)**2;if(d<bd){bd=d;best=q}}if(best>=0)i=best}hs[j]=i;used.add(i)}
 const R=bbw(nx,ny,inDom,hs,sweeps);
 const P=hs.map(i=>[ox+(i%nx)*c,oy+((i/nx)|0)*c]);
 const tau=new Float32Array(nx*ny);for(let i=0;i<nx*ny;i++){let m=0;for(const w of R.W)if(w[i]>m)m=w[i];tau[i]=1-m}
 // normalise tau to 0..1 over the domain
 let t0=1,t1=0;for(let i=0;i<nx*ny;i++)if(inDom[i]){t0=Math.min(t0,tau[i]);t1=Math.max(t1,tau[i])}for(let i=0;i<nx*ny;i++)tau[i]=Math.max(0,Math.min(1,(tau[i]-t0)/((t1-t0)||1)));
 return{nx,ny,c,ox,oy,P,hs,W:R.W,inDom,tau,stat:R.stat}}
function skin(R,C){const n=R.nx*R.ny,V=new Array(n),D=C.map((q,j)=>[q[0]-R.P[j][0],q[1]-R.P[j][1]]);
 for(let i=0;i<n;i++){let x=R.ox+(i%R.nx)*R.c,y=R.oy+((i/R.nx)|0)*R.c;for(let j=0;j<D.length;j++){const w=R.W[j][i];if(w>1e-4){x+=w*D[j][0];y+=w*D[j][1]}}V[i]=[x,y]}return V}
// point skinned through a rig (bilinear weights)
function skinPt(R,C,x,y){const fx=(x-R.ox)/R.c,fy=(y-R.oy)/R.c,gx=Math.max(0,Math.min(R.nx-2,Math.floor(fx))),gy=Math.max(0,Math.min(R.ny-2,Math.floor(fy))),ax=Math.max(0,Math.min(1,fx-gx)),ay=Math.max(0,Math.min(1,fy-gy));
 let X=x,Y=y;C.forEach((q,j)=>{const w=R.W[j],i=gy*R.nx+gx,v=w[i]*(1-ax)*(1-ay)+w[i+1]*ax*(1-ay)+w[i+R.nx]*(1-ax)*ay+w[i+R.nx+1]*ax*ay;X+=v*(q[0]-R.P[j][0]);Y+=v*(q[1]-R.P[j][1])});return[X,Y]}
// draw the textured mesh; alphaOf(tauOfCell) -> alpha per cell; img pixel (0,0) is node 0's screen point minus (ox,oy) offset (sx0,sy0)
function drawMesh(g,R,img,V,alphaOf,sx0,sy0,st,two){st=st||1;for(let gy=0;gy+st<R.ny;gy+=st)for(let gx=0;gx+st<R.nx;gx+=st){const a=gy*R.nx+gx,b=a+st,c=a+R.nx*st,d=c+st;
  if(!(R.inDom[a]||R.inDom[b]||R.inDom[c]||R.inDom[d]))continue;
  const al=alphaOf((R.tau[a]+R.tau[b]+R.tau[c]+R.tau[d])/4);if(al<=.004)continue;
  const S=i=>[(i%R.nx)*R.c+sx0,((i/R.nx)|0)*R.c+sy0];
  g.globalAlpha=Math.min(1,al);if(two){tri(g,img,S(a),S(b),S(c),V[a],V[b],V[c]);tri(g,img,S(b),S(d),S(c),V[b],V[d],V[c])}else tri(g,img,S(a),S(b),S(c),V[a],V[b],V[c],S(d),V[d])}
 g.globalAlpha=1}
// isolines of handle weights (marching squares) at the deformed positions: the rig's heat map as vector strokes
function isolines(g,R,V,levels,js,fields){g.beginPath();
 for(const j of js){const w=fields?fields[j]:R.W[j];for(const L of levels)for(let gy=0;gy<R.ny-1;gy++)for(let gx=0;gx<R.nx-1;gx++){const i=gy*R.nx+gx,c=[i,i+1,i+1+R.nx,i+R.nx];
  if(!fields&&!(R.inDom[c[0]]||R.inDom[c[1]]||R.inDom[c[2]]||R.inDom[c[3]]))continue;
  const v=c.map(q=>w[q]);if((v[0]>L)===(v[1]>L)&&(v[1]>L)===(v[2]>L)&&(v[2]>L)===(v[3]>L))continue;const pts=[];
  for(let e=0;e<4;e++){const p=c[e],q=c[(e+1)%4],a=v[e],b=v[(e+1)%4];if((a>L)!==(b>L)){const t=(L-a)/(b-a);pts.push([V[p][0]+(V[q][0]-V[p][0])*t,V[p][1]+(V[q][1]-V[p][1])*t])}}
  for(let k=0;k+1<pts.length;k+=2){g.moveTo(pts[k][0],pts[k][1]);g.lineTo(pts[k+1][0],pts[k+1][1])}}}
 g.stroke()}
function handleMark(g,x,y,s,a){g.strokeStyle=`rgba(${PH},${a})`;g.lineWidth=2;g.strokeRect(x-s,y-s,2*s,2*s);g.beginPath();g.moveTo(x-s*2,y);g.lineTo(x-s,y);g.moveTo(x+s,y);g.lineTo(x+s*2,y);g.moveTo(x,y-s*2);g.lineTo(x,y-s);g.moveTo(x,y+s);g.lineTo(x,y+s*2);g.stroke()}

// the room drawn whole, then masked by its own influence order: a per-node alpha image (one pixel per node)
// warped by the same skin, smoothly interpolated, so the picture gives way along the weight field
const ROOMJ=[0,1,2,3,4,5,6,12];let OFF=null;
function roomMasked(g,R,img,V,alphaOf){if(!OFF){OFF={a:mkc(),m:mkc(),t:document.createElement('canvas')};OFF.t.width=R.nx;OFF.t.height=R.ny}
 const n=R.nx*R.ny,al=new Float32Array(n);let mn=1,mx=0;for(let i=0;i<n;i++){al[i]=Math.max(0,Math.min(1,alphaOf(R.tau[i])));mn=Math.min(mn,al[i]);mx=Math.max(mx,al[i])}
 if(mx<=.003)return;if(mn>=.997){drawMesh(g,R,img,V,()=>1,RX0,RY0,2,1);return}
 const qa=OFF.a.getContext('2d');qa.globalCompositeOperation='source-over';qa.clearRect(0,0,W,H);drawMesh(qa,R,img,V,()=>1,RX0,RY0,2,1);
 const qt=OFF.t.getContext('2d'),id=qt.createImageData(R.nx,R.ny);for(let i=0;i<n;i++){id.data[i*4]=id.data[i*4+1]=id.data[i*4+2]=255;id.data[i*4+3]=Math.round(al[i]*255)}qt.putImageData(id,0,0);
 const qm=OFF.m.getContext('2d');qm.clearRect(0,0,W,H);qm.imageSmoothingEnabled=true;
 for(let gy=0;gy+2<R.ny;gy+=2)for(let gx=0;gx+2<R.nx;gx+=2){const a=gy*R.nx+gx,b=a+2,c=a+2*R.nx,d=c+2,S=i=>[(i%R.nx)+.5,((i/R.nx)|0)+.5];tri(qm,OFF.t,S(a),S(b),S(c),V[a],V[b],V[c]);tri(qm,OFF.t,S(b),S(d),S(c),V[b],V[d],V[c])}
 qa.globalCompositeOperation='destination-in';qa.drawImage(OFF.m,0,0);qa.globalCompositeOperation='source-over';g.drawImage(OFF.a,0,0)}
// ======================= the room rig (film independent) =======================
const RX0=-192,RY0=-108,RC=64,RNX=37,RNY=21;
// gun corner -> tying display: lamp off the table up to the ceiling; the picture frame opens into the door frame;
// the wall corner is pushed out of frame; the floor line drops to the display floor; frame corners pinned
const RP=[[170,585],[1502,290],[1618,430],[1700,0],[1700,884],[0,880],[900,880],[0,0],[900,0],[0,1080],[960,1080],[1920,1080],[1300,520]];
const RQ=[[705,165],[1776,458],[1963,900],[2080,0],[2080,903],[0,903],[1000,903],[0,0],[900,0],[0,1080],[960,1080],[1920,1080],[1300,520]];
let ROOM=null;
function roomRigs(){if(ROOM)return ROOM;const dom=new Array(RNX*RNY).fill(true);
 ROOM={o:mkRig(RNX,RNY,RC,RX0,RY0,dom,RP,260),i:mkRig(RNX,RNY,RC,RX0,RY0,dom,RQ,260)};return ROOM}
function roomC(E){const R=roomRigs();return R.o.P.map((p,j)=>{const q=R.i.P[j];let x=p[0]+(q[0]-p[0])*E,y=p[1]+(q[1]-p[1])*E;
 if(j===0){const s=Math.sin(Math.PI*E);x-=60*s;y-=120*s} // the lamp is lifted on an arc
 return[x,y]})}
// ======================= cached layers (as the film composites them) =======================
const mkc=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c};
function leverBox(b,lv){const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}}
function layersOf(D,lt,e,st,K){const order=D.layers||['bg','V','A'];const mk=D.marks?D.marks(lt,e.A,e.V,K):null;const out={order,bg:mkc(),A:mkc(),V:mkc(),box:{}};
 for(const ly of order){const q=out[ly].getContext('2d');q.save();try{D.draw(q,lt,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}q.restore()}
 for(const ly of['A','V']){if(!mk)continue;const who=ly==='A'?e.A:e.V,lv=st.levers[who],b=mk[ly];const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
  if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);
  const c2=mkc(),q=c2.getContext('2d');q.filter=fl.join(' ')||'none';q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(out[ly],0,0);out[ly]=c2;out.box[ly]=leverBox(b,lv)}
 return out}
function composite(Lr){const c=mkc(),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,W,H);for(const ly of Lr.order)q.drawImage(Lr[ly],0,0);return c}
function cropRect(b){const x0=Math.max(0,Math.floor(b.x-b.w*.45-40)),y0=Math.max(0,Math.floor(b.y-b.h*.6-60)),x1=Math.min(W,Math.ceil(b.x+b.w*1.45+40)),y1=Math.min(H,Math.ceil(b.y+b.h+40));return{x:x0,y:y0,w:Math.max(2,x1-x0),h:Math.max(2,y1-y0)}}
// lift each sack out of its layer; whatever of the layer lies outside the crop stays with the room
function lift(Lr){const S={};const bgp=mkc(),q=bgp.getContext('2d');q.drawImage(Lr.bg,0,0);
 for(const ly of Lr.order){if(ly==='bg')continue;const b=Lr.box[ly];if(!b){q.drawImage(Lr[ly],0,0);continue}const r=cropRect(b);
  const sp=document.createElement('canvas');sp.width=r.w;sp.height=r.h;sp.getContext('2d').drawImage(Lr[ly],-r.x,-r.y);
  const rest=mkc(),rq=rest.getContext('2d');rq.drawImage(Lr[ly],0,0);rq.clearRect(r.x,r.y,r.w,r.h);q.drawImage(rest,0,0);S[ly]={img:sp,r,b}}
 return{bg:bgp,S}}
// ======================= auto-rig a cutout =======================
// handles: 0 left foot, 1 right foot, 2 belly, 3 crown, 4 left ear tip, 5 right ear tip (found from the mask)
function rigSprite(S){const iw=S.img.width,ih=S.img.height,dat=S.img.getContext('2d').getImageData(0,0,iw,ih).data;
 const c=Math.max(8,Math.ceil(Math.max(iw,ih)/30)),nx=Math.ceil(iw/c)+1,ny=Math.ceil(ih/c)+1,dom=new Array(nx*ny).fill(false);
 const al=(x,y)=>x<0||y<0||x>=iw||y>=ih?0:dat[(y*iw+x)*4+3];
 for(let gy=0;gy<ny;gy++)for(let gx=0;gx<nx;gx++){const x0=gx*c,y0=gy*c;let hit=false;
  for(let y=y0-(c>>1);y<=y0+(c>>1)&&!hit;y+=2)for(let x=x0-(c>>1);x<=x0+(c>>1);x+=2)if(al(x,y)>60){hit=true;break}dom[gy*nx+gx]=hit}
 const b=S.b,ox=S.r.x,oy=S.r.y,cx=b.x+b.w/2;
 let eL=null,eR=null,dL=-1,dR=-1;
 for(let i=0;i<nx*ny;i++){if(!dom[i])continue;const x=ox+(i%nx)*c,y=oy+((i/nx)|0)*c;if(y>b.y+b.h*.3)continue;
  const d=Math.hypot(x-cx,(y-(b.y+b.h*.55))*1.2);if(x<cx&&d>dL){dL=d;eL=[x,y]}if(x>=cx&&d>dR){dR=d;eR=[x,y]}}
 const hp=[[b.x+b.w*.15,b.y+b.h-6],[b.x+b.w*.85,b.y+b.h-6],[cx,b.y+b.h*.6],[cx,b.y+b.h*.12],eL||[b.x,b.y],eR||[b.x+b.w,b.y]];
 const R=mkRig(nx,ny,c,ox,oy,dom,hp,180);R.img=S.img;R.S=S;{let f=Float32Array.from(dom,v=>v?1:0);for(let pass=0;pass<2;pass++){const o=new Float32Array(f.length);for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){let s2=0,n2=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const X=x+dx,Y=y+dy;if(X<0||Y<0||X>=nx||Y>=ny)continue;s2+=f[Y*nx+X];n2++}o[y*nx+x]=s2/n2}f=o}R.dom01=f}return R}
// ======================= the plan (pure function of the ledger) =======================
function plan(X,K){const L=X.ledger,k=X.k,eo=L.ev[k-1],ei=L.ev[k],so=L.states[k-1],si=L.states[k];
 const ro={},ri={};ro[eo.A]='A';ro[eo.V]='V';ri[ei.A]='A';ri[ei.V]='V';
 const mem=LEDGER.memories(L,ei.A,k).filter(m=>m.other===ei.V);const hes=mem.length?Math.min(1,mem[0].weight):0;
 const sacks=[];
 for(const s of IDS){const inO=s in ro,inI=s in ri;if(!inO&&!inI)continue;const lv=si.levers[s]||{};
  sacks.push({id:s,kind:inO&&inI?'staying':inO?'leaving':'entering',ro:ro[s],ri:ri[s],ghost:inI&&!si.alive[s],deadO:inO&&!so.alive[s],
   hes:s===ei.A?hes:0,tempo:lv.tempo||0,weight:lv.weight||0,gunner:s===eo.A})}
 const others=IDS.filter(s=>!(s in ro)&&!(s in ri)&&!si.alive[s]);
 const ev=si.evidence.filter(x=>x.k<k-1);
 return{eo,ei,so,si,sacks,others,ev,hes}}
let CACHE={key:'',P:null};
function build(X,K){const key=X.film.join(',')+'|'+X.k;if(CACHE.key===key)return CACHE.P;
 const P=plan(X,K);const Do=X.DEEDS[P.eo.deed],Di=X.DEEDS[P.ei.deed];roomRigs();
 const Lo=layersOf(Do,T_OUT,P.eo,P.so,K),Li=layersOf(Di,T_IN,P.ei,P.si,K);
 P.fullO=composite(Lo);P.fullI=composite(Li);P.lo=lift(Lo);P.li=lift(Li);
 const DOOR={x:1776,y:458,w:187,h:442};
 for(const sk of P.sacks){
  sk.Ro=sk.ro?rigSprite(P.lo.S[sk.ro]):null;sk.Ri=sk.ri?rigSprite(P.li.S[sk.ri]):null;
  const tempo=sk.tempo;sk.t0=DUR*(.16-.04*tempo);sk.t1=DUR*(.84-.04*tempo);
  if(sk.kind==='staying'){sk.H0=sk.Ro.P;sk.H1=sk.Ri.P}
  if(sk.kind==='leaving'){sk.H0=sk.Ro.P;const b=sk.Ro.S.b,fx=b.x+b.w/2,fy=b.y+b.h;
   if(sk.deadO){sk.H1=sk.H0.map(([x,y])=>[x,y-260]);sk.fade=true}                       // a ghost leaves upward
   else if(fx>1100){sk.door=true;const dx=DOOR.x+DOOR.w/2,dy=DOOR.y+DOOR.h;sk.H1=sk.H0.map(([x,y])=>[dx+(x-fx)*.14,dy+(y-fy)*.9])}  // into the door
   else{sk.H1=sk.H0.map(([x,y])=>[x-fx-b.w*.9-200,y])}}                                  // out to the left
  if(sk.kind==='entering'){sk.H1=sk.Ri.P;const b=sk.Ri.S.b,fx=b.x+b.w/2,fy=b.y+b.h;
   if(sk.ghost){sk.H0=sk.H1.map(([x,y])=>[fx+(x-fx)*.8,fy+(y-fy)*.05]);sk.rise=true}   // a ghost rises out of the floor
   else if(fx>960){sk.door=true;const dx=DOOR.x+DOOR.w/2,dy=DOOR.y+DOOR.h;sk.H0=sk.H1.map(([x,y])=>[dx+(x-fx)*.14,dy+(y-fy)*.9])}
   else{sk.H0=sk.H1.map(([x,y])=>[x-fx-b.w*.9-200,y])}}
  sk.bodyStay=sk.kind==='staying'&&sk.ghost&&P.so.alive[sk.id]; // (gun never kills; kept for safety)
  const a=sk.H0[2],z=sk.H1[2],d=Math.hypot(z[0]-a[0],z[1]-a[1]),bw=(sk.Ri||sk.Ro).S.b.w;
  sk.hops=sk.fade||sk.rise?0:Math.max(1,Math.min(5,Math.round(d/(bw*1.1+60))));
  // the revolver: lifted off the gunner's aiming ear and put down on the floor where it stood
  if(sk.gunner&&sk.Ro){const e=sk.Ro.P[4][0]>sk.Ro.P[5][0]?4:5;sk.gunEar=e;sk.gunAt=[...sk.Ro.P[e]];sk.gunRest=[Math.min(1500,sk.Ro.S.b.x+sk.Ro.S.b.w+40),880]}}
 // the dead elsewhere: their own last picture from the deed that killed them
 P.bodies=P.others.map(s=>{const kd=P.si.deadAt[s];const e=X.ledger.ev[kd];if(!e)return null;const D=X.DEEDS[e.deed];if(!D||!D.marks)return null;
  const role=e.V===s?'V':'A';const c=mkc(),q=c.getContext('2d');try{D.draw(q,5.99,e.A,e.V,K,{layer:role,carry:X.ledger.states[kd].body})}catch(err){return null}
  const b=D.marks(5.99,e.A,e.V,K)[role];const r=cropRect(b);const sp=document.createElement('canvas');sp.width=r.w;sp.height=r.h;sp.getContext('2d').drawImage(c,-r.x,-r.y);return{img:sp,r,b,s}}).filter(Boolean);
 window.T06_STATS={room:[ROOM.o.stat,ROOM.i.stat],others:P.others,bodies:P.bodies.length,alive:P.si.alive,aliveO:P.so.alive,sacks:P.sacks.map(s=>({id:s.id,kind:s.kind,g:s.ghost,d:s.deadO,o:s.Ro&&s.Ro.stat,i:s.Ri&&s.Ri.stat}))};
 CACHE={key,P};return P}
// ======================= sack travel: handle trajectories =======================
function progress(sk,u,K){let p=K.cl(0,1,(u-sk.t0)/(sk.t1-sk.t0));
 if(sk.hes>.3){const hold=.3*sk.hes;const q=p<.45?p/.45*.5:p<.45+hold?.5:.5+(p-.45-hold)/(.55-hold)*.5;p=K.cl(0,1,q)}return p}
function handlesAt(sk,u,K){const p=progress(sk,u,K),n=sk.hops,e=n?p:K.sm(0,1,p);
 const pe=K.cl(0,1,progress(sk,u-.07,K)); // ears trail the body
 const B=(sk.Ri||sk.Ro).S.b,hh=B.h;let lift=0,ph=0,env=0;
 if(n){ph=(p*n)%1;env=K.sm(0,.04,p)*(1-K.sm(.96,1,p));lift=hh*(.26-.1*K.cl(-1,1,sk.weight))*Math.sin(Math.PI*ph)*env}
 const C=sk.H0.map((a,j)=>{const z=sk.H1[j],ear=j>=4,ee=ear?(n?pe:K.sm(0,1,pe)):e;
  let x=a[0]+(z[0]-a[0])*ee,y=a[1]+(z[1]-a[1])*ee;
  if(j>=2)y-=lift;else y-=lift*.9;
  if(ear&&n){y+=hh*.06*Math.cos(Math.PI*ph)*env;x-=(z[0]>a[0]?1:-1)*hh*.05*env} // ears flop, localised to the ear weights
  if(j===2)y+=hh*.08*Math.pow(1-Math.sin(Math.PI*ph),3)*env; // the belly squashes on landing
  return[x,y]});
 if(sk.kind==='staying'){// sacks that cross the room pass at two depths: rightward in front and lower, leftward behind and higher
  const dir=Math.sign(sk.H1[2][0]-sk.H0[2][0]),d=Math.sin(Math.PI*K.cl(0,1,e))*dir*K.cl(0,1,Math.abs(sk.H1[2][0]-sk.H0[2][0])/400);
  const fx=(C[0][0]+C[1][0])/2,fy=(C[0][1]+C[1][1])/2,f=1+.1*d;for(const q of C){q[0]=fx+(q[0]-fx)*f;q[1]=fy+(q[1]-fy)*f+40*d}}
 if(sk.hes>.3){const hp=K.sm(.4,.5,p)*(1-K.sm(.5+.3*sk.hes,.6+.3*sk.hes,p));// hesitation: crown leans back, ears flatten
  const back=-hp*.25*sk.hes*B.w;C[3][0]+=back;C[4][0]+=back*1.3;C[5][0]+=back*1.3;C[4][1]+=hp*hh*.2;C[5][1]+=hp*hh*.2;C[2][0]+=back*.3}
 return{C,p}}
function scan(g,a){if(a<=0)return;g.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2)}
// ======================= draw =======================
TRANSITION({k:6,scion:12,lineage:'Alec Jacobson — Localized Deformation Weights',
 op:'the gun room and every sack are auto-rigged from their cutout masks with bounded biharmonic weights (min sum (Lw)^2, 0<=w<=1, partition of unity); point handles carry room and cast to the display\'s positions by linear blend skinning, and the painted picture dissolves cell by cell in order of influence into its own weight isolines, which are the vector strokes of the tying display',
 made:'Two textured grid meshes of the rooms (37x21 nodes, 13 point handles each: lamp, picture corners, wall corner, floor, frame pins) and one masked grid mesh per sack cutout (only cells the cutout covers, so ear and head are not neighbours), each with six handles: two feet, belly, crown and the two ear tips found from the mask. Between the two pictures the house is only its rig drawn as light: weight isolines, partition lines and Sketchpad-style handle marks.',
 moved:'Handle trajectories move everything: the lamp is lifted off its table on an arc to hang from the ceiling, the picture frame stretches open into the door, the wall corner is pushed out of frame, the floor drops to the display floor. Sacks hop on their foot handles while the ear handles trail and flop, so only the ears bend; the threatened victim\'s raised ears come down on their own weights; a sack with a strong memory of its victim stops halfway, crown and ears pulled back; the revolver is put down on the floor and stays as evidence.',
 dur:DUR,
 draw(g,u,X,K){const P=build(X,K),RM=roomRigs();
  const imO=X.ledger.states[X.k].impossible.find(q=>q.k===X.k-1),imI=X.ledger.states[X.k+1].impossible.find(q=>q.k===X.k);
  const s=u/DUR;
  if(s<=.02){g.drawImage(P.fullO,0,0);scan(g,imO?1:0);return}
  if(u>=DUR-.03){g.drawImage(P.fullI,0,0);scan(g,imI?1:0);return}
  const E=K.sm(.1,.86,s),C=roomC(E);g.fillStyle='#000';g.fillRect(0,0,W,H);
  const VO=skin(RM.o,C),VI=skin(RM.i,C);
  const rig=K.sm(.02,.14,s)*(1-K.sm(.86,.97,s)); // how much of the rig is shown as light
  // 1 · the room: painted corner gives way near its handles first, the display fills in from its handles outward
  const aO=t=>1-K.sm(.1+.3*t,.42+.3*t,s),aI=t=>K.sm(.36+.3*t,.62+.3*t,s);
  roomMasked(g,RM.o,P.lo.bg,VO,aO);
  roomMasked(g,RM.i,P.li.bg,VI,aI);
  // 2 · the rig as light: weight isolines (the heat map) and the partition lines, then the handles
  if(rig>0){g.lineWidth=1.6;g.lineCap='round';
   const fo=1-K.sm(.35,.6,s),fi=K.sm(.35,.6,s);
   if(fo>0){g.strokeStyle=`rgba(${PH},${.28*rig*fo})`;isolines(g,RM.o,VO,[.2,.75],ROOMJ);g.strokeStyle=`rgba(${PH},${.7*rig*fo})`;g.lineWidth=2.2;isolines(g,RM.o,VO,[.5],ROOMJ)}
   if(fi>0){g.lineWidth=1.6;g.strokeStyle=`rgba(${PH},${.28*rig*fi})`;isolines(g,RM.i,VI,[.2,.75],ROOMJ);g.strokeStyle=`rgba(${PH},${.7*rig*fi})`;g.lineWidth=2.2;isolines(g,RM.i,VI,[.5],ROOMJ)}
   C.forEach(([x,y],j)=>{if(x>-20&&x<W+20&&y>-20&&y<H+20)handleMark(g,x,y,7,.85*rig)});
   // the lamp handle's path, a dotted construction line
   g.save();g.setLineDash([3,10]);g.strokeStyle=`rgba(${PH},${.35*rig})`;g.lineWidth=1.5;g.beginPath();for(let i=0;i<=24;i++){const q=roomC(i/24)[0];i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke();g.restore()}
  // 3 · the house remembers: evidence pinned in the room mesh along the skirting; the dead where they were left
  const env=K.sm(.12,.3,s)*(1-K.sm(.8,.95,s));
  P.ev.forEach((ev,i)=>{const n=P.ev.length,x0=150+(i+.5)/Math.max(1,n)*1150,y0=845+(i%2)*60;const q=skinPt(RM.o,C,x0,y0);const bx={x:q[0]-70,y:q[1]-45,w:140,h:90};const CQ=X.CONSEQS[ev.deed];
   g.save();g.globalAlpha=env*.95;try{if(CQ&&CQ.trace)CQ.trace(g,bx,X.k-1-ev.k,K);else{g.fillStyle='#fbf7ee';g.fillRect(bx.x+50,bx.y+50,40,10)}}catch(err){}
   g.globalAlpha=env*.6;handleMark(g,q[0],q[1]+40,4,.6);g.restore()});
  P.bodies.forEach((B,i)=>{const sc=.7,x0=150+i*260,q=skinPt(RM.o,C,x0,905);g.save();g.globalAlpha=env*.9;g.filter='grayscale(1) brightness(.75)';
   g.translate(q[0],q[1]);g.scale(sc,sc);g.drawImage(B.img,-(B.b.x-B.r.x),-(B.b.y+B.b.h-B.r.y));g.restore()});
  // 4 · the cast: each cutout skinned by its own weights; it trades its painted cloth for its vector self cell by cell
  const dirOf=sk=>sk.kind==='staying'?Math.sign(sk.H1[2][0]-sk.H0[2][0]):0;const order=P.sacks.slice().sort((a,b)=>dirOf(a)-dirOf(b)||(a.ri==='A')-(b.ri==='A'));
  for(const sk of order){const {C:Hc,p}=handlesAt(sk,u,K);
   let fade=1;if(sk.fade)fade=1-K.sm(.2,.9,p);
   const ghostF=sk.ghost||sk.deadO?`drop-shadow(0 0 ${Math.round(16)}px rgba(190,255,210,.8))`:'none';
   let vis=1;if(sk.door&&sk.kind==='leaving')vis=1-K.sm(.85,1,p);if(sk.door&&sk.kind==='entering')vis=K.sm(0,.12,p);
   g.save();if(ghostF!=='none')g.filter=ghostF;
   if(sk.Ro){const V=skin(sk.Ro,Hc);const a=t=>(1-.72*K.sm(.12,.42,p))*(1-K.sm(.48,.78,p))*fade*vis;drawMesh(g,sk.Ro,sk.Ro.img,V,a,0,0,2);sk._Vo=V}
   if(sk.Ri){const V=skin(sk.Ri,Hc);const a=t=>K.sm(.45,.88,p)*vis*(sk.rise?.3+.7*K.sm(0,1,p):1);drawMesh(g,sk.Ri,sk.Ri.img,V,a,0,0,2);sk._Vi=V}
   g.restore();
   // the dead: a ghost's outline burns green (a filter would be clipped away per cell, so it is stroked)
   if(sk.ghost||sk.deadO){const R=p<.5&&sk.Ro?sk.Ro:(sk.Ri||sk.Ro),V=R===sk.Ro?sk._Vo:sk._Vi,ga=.75*(1-K.sm(.8,.97,s))*fade*vis*K.sm(0,.06,s);
    if(ga>.01&&V){g.save();g.shadowColor='rgba(190,255,210,.9)';g.shadowBlur=22;g.lineWidth=3;g.strokeStyle=`rgba(200,255,220,${ga})`;isolines(g,R,V,[.35],[0],[R.dom01]);g.restore()}}
   // the sack's own rig in light: ear weights at .5 (where each ear starts), crown/belly partition, handle marks
   const ra=K.sm(.05,.25,p)*(1-K.sm(.75,.97,p))*rig*vis*fade;
   if(ra>.01){const R=p<.5&&sk.Ro?sk.Ro:(sk.Ri||sk.Ro),V=R===sk.Ro?sk._Vo:sk._Vi;
    g.lineWidth=2.6;g.strokeStyle=`rgba(${PH},${.95*ra})`;isolines(g,R,V,[.5],[0],[R.dom01]);
    g.lineWidth=2;g.strokeStyle=`rgba(${PH},${.8*ra})`;isolines(g,R,V,[.5],[4,5]);
    g.lineWidth=1.3;g.strokeStyle=`rgba(${PH},${.4*ra})`;isolines(g,R,V,[.2,.5,.8],[0,1,2,3]);
    Hc.forEach(([x,y])=>handleMark(g,x,y,5,.9*ra))}}
  // the revolver: taken off the aiming ear, set down on the floor, left in the house
  for(const sk of P.sacks){if(!sk.gunner||!sk.Ro)continue;const {C:Hc}=handlesAt(sk,u,K);const d=K.sm(.1,.3,s),f=K.eo(.3,.48,s);
   const src=[Hc[sk.gunEar][0],Hc[sk.gunEar][1]];const rest=skinPt(RM.o,C,sk.gunRest[0],sk.gunRest[1]);
   const gx=K.lerp(src[0],rest[0],f),gy=K.lerp(src[1],rest[1],f)-Math.sin(Math.PI*f)*40;
   const ga=d*(1-K.sm(.82,.95,s));if(ga<=0)continue;const CQ=X.CONSEQS.gun;
   g.save();g.globalAlpha=ga;try{if(CQ&&CQ.trace)CQ.trace(g,{x:gx-40,y:gy-60,w:150,h:90},0,K)}catch(err){}g.restore();
   if(rig>0&&f>0&&f<1){g.save();g.setLineDash([3,8]);g.strokeStyle=`rgba(${PH},${.5*rig})`;g.beginPath();g.moveTo(src[0],src[1]);g.lineTo(gx,gy);g.stroke();g.restore()}}
  scan(g,imO?1-E:0);scan(g,imI?E:0)},
 sound(ac,out0,t0,X,K){const out=ac.createGain();out.gain.value=2.6;out.connect(out0);const S=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1)),mf=m=>440*Math.pow(2,(m-69)/12);
  const P=plan(X,K);const L=X.ledger;
  // handles pinned on the room: one light-pen tick each
  RP.forEach((p,j)=>S.grain(ac,out,t0+.06+j*.035,{f:2600+((j*7)%5)*240,d:.016,a:.07,pan:pan(p[0]),att:.05}));
  // the solver converging: grains spread in pitch that close to one tone as the weights settle
  for(let i=0;i<45;i++){const v=K.hash(i*3.1+6),tt=.3+v*1.9,dev=(K.hash(i*5.3)-.5)*14*(1-v);S.grain(ac,out,t0+tt,{f:mf(69+dev),d:.06+.05*v,a:.012+.02*v,pan:(K.hash(i*1.7)-.5)*1.4,type:'triangle',att:.4})}
  // the room is pulled: a low rubbery band, the lamp rising on its arc
  S.cloud(ac,out,t0+.3,2.2,20,{f:90,glide:.25,noise:.6,bp:600,q:2,a:.04,d:[.05,.12],type:'triangle'},u=>Math.sin(Math.PI*u));
  S.grain(ac,out,t0+.5,{f:220,d:1.4,a:.04,glide:.5,type:'sine',att:.4});
  // the phosphor coming up: a thin high hiss
  S.cloud(ac,out,t0+1.4,1.5,24,{bp:6500,q:4,a:.015,d:[.04,.12]},u=>Math.sin(Math.PI*u));
  // the cast: each hop on its foot handles, the landing, ears, ghosts, doors
  const DQ=X.DEEDS[P.eo.deed],DI=X.DEEDS[P.ei.deed];
  for(const sk of P.sacks){const tempo=sk.tempo,a0=DUR*(.16-.04*tempo),a1=DUR*(.84-.04*tempo);
   const bo=sk.ro?DQ.marks(T_OUT,P.eo.A,P.eo.V,K)[sk.ro]:null,bi=sk.ri?DI.marks(T_IN,P.ei.A,P.ei.V,K)[sk.ri]:null;
   const x0=bo?bo.x+bo.w/2:(bi.x>960?1870:-100),x1=bi?bi.x+bi.w/2:(bo.x>1100?1870:-150);
   const n=Math.max(1,Math.min(5,Math.round(Math.abs(x1-x0)/((bi||bo).w*1.1+60))));
   const hold=sk.hes>.3?.3*sk.hes:0;
   const tAt=pp=>{const q=pp<.5?pp*.45/.5:pp===.5?.45:.45+hold+(pp-.5)/.5*(.55-hold);return a0+(a1-a0)*q};
   for(let h=1;h<=n;h++){const pp=h/n,tt=hold?tAt(pp):a0+(a1-a0)*pp;S.say(ac,out,sk.id,t0+tt,h===n?'land':'step',h===n?.6:1,pan(K.lerp(x0,x1,pp)))}
   if(sk.hes>.3)S.say(ac,out,sk.id,t0+tAt(.5)+.05,'breathe',.9,pan((x0+x1)/2));
   if(sk.ghost||sk.deadO)S.cloud(ac,out,t0+a0,1.4,30,{f:mf(S.VOICE[sk.id].base+24),a:.03,d:[.1,.25],glide:.05},u=>Math.sin(Math.PI*u));
   if(sk.ro==='V'&&sk.kind!=='leaving')S.say(ac,out,sk.id,t0+a0+.3,'sink',.6,pan(x0)); // the raised ears come down
   if((sk.kind==='entering'&&x0>1700)||(sk.kind==='leaving'&&x1>1700))S.cloud(ac,out,t0+(sk.kind==='entering'?a0:a1-.3),.4,40,{f:150,glide:-.2,a:.04,d:[.02,.06],noise:.5,type:'triangle',bp:900},u=>1-u)}
  // the revolver set down on the floor: a metal tick and a small knock (never a shot)
  const gx=DQ.marks(T_OUT,P.eo.A,P.eo.V,K).A;S.grain(ac,out,t0+DUR*.3,{bp:3200,q:6,d:.03,a:.16,pan:pan(gx.x+gx.w),att:.1});S.thump(ac,out,t0+DUR*.48,.35,120,pan(gx.x+gx.w));
  // evidence in the house: a soft tick for each trace as it is found
  P.ev.forEach((ev,i)=>S.grain(ac,out,t0+.7+i*.16,{f:1300+i*150,d:.04,a:.04,pan:pan(150+(i+.5)/Math.max(1,P.ev.length)*1150),att:.1}))}
});
})();
