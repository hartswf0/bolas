// TRANSITION 08 · Rape (occlusion candle room) -> Seduction (Whitney harmonic dark room under a lamp)
// SCION 42 · Neural Layered Puppet, few-shot structure. Each sack, and the room itself, is re-fit as a
// layered mesh template driven by a small latent pose z = {x, y, w, h, lean, sag, sq, tilt}. The example
// frames are the deed layers themselves (outgoing at t=5.99, incoming at t=0; a doer behind the door jamb
// also gets a second outgoing example at t=1.0 to supply the cells the jamb hid). Between examples the
// pose is unseen: the puppet is rendered by warping the nearest example's texture through the deformation
// basis D(z;a,b), and the distance to the nearest example is drawn as exposed mesh (the confidence map).
// The change of visual language is a VISIBILITY STATE per mesh cell: each cell of the room and of each
// sack switches from the candle-room example to the lamp-room example at its own time (the lamp's reach
// learns the room outward; the corner where it happened is relearned last). No crossfade.
// Invariant (numeric, harness seam check): at u=0 every vertex maps to its own source pixel (identity
// mesh, drawn without warping), at u=dur the same holds for the incoming examples.
(function(){
const IDS=['R','B','I','O'];
const COL={R:'#c0705f',B:'#a89a88',I:'#d8c49a',O:'#b878d0'};
const DUR=3.4,T_OUT=5.99,T_IN=0.001;
const LAMP=[960,195],CANDLE=[516,292];
const sm=(a,b,x)=>{const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)};
const cl=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
function cv(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c}
let CACHE={key:null,v:null};

// ---------- deed layer as film.html composites it (levers baked: loom/shrink scale, grey, halo, shadow) ----------
function layerFull(D,lt,A,V,ly,carry,lev,K){
  const raw=cv(1920,1080),q=raw.getContext('2d');try{D.draw(q,lt,A,V,K,{layer:ly,carry})}catch(e){}
  if(ly==='bg'||!D.marks)return {c:raw};
  const b=D.marks(lt,A,V,K)[ly];
  const f=1+.14*cl(-1,1,lev.loom)-.22*lev.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lev.grey>.05)fl.push(`grayscale(${Math.min(1,lev.grey)}) brightness(${1-.25*lev.grey})`);if(lev.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lev.halo)}px rgba(255,236,180,${Math.min(.9,lev.halo)}))`);
  if(lev.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lev.shadow)}px ${Math.round(-30*lev.shadow)}px ${Math.round(18*lev.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lev.shadow*.4)}))`);
  const out=cv(1920,1080),o=out.getContext('2d');o.filter=fl.join(' ')||'none';o.translate(cx,by);o.scale(f,f);o.translate(-cx,-by);o.drawImage(raw,0,0);
  return {c:out,box:{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}};
}
// an example frame: the layer cut on its box (+pad, may extend off-canvas), the remainder stays with the room
function example(Lr){
  const b=Lr.box,pl=Math.max(90,b.w*.4),pr=Math.max(40,b.w*.3),pt=Math.max(50,b.h*.3),pb=30;
  const x0=Math.floor(b.x-pl),y0=Math.floor(b.y-pt),w=Math.ceil(b.w+pl+pr),h=Math.ceil(b.h+pt+pb);
  const img=cv(w,h);img.getContext('2d').drawImage(Lr.c,-x0,-y0);
  const rem=cv(1920,1080),r=rem.getContext('2d');r.drawImage(Lr.c,0,0);r.clearRect(x0,y0,w,h);
  return {img,ox:x0,oy:y0,box:{...b},rem,z:zOf(b)};
}
const zOf=b=>({x:b.x+b.w/2,y:b.y+b.h,w:b.w,h:b.h,lean:0,sag:0,sq:0,tilt:0});
// per-cell alpha coverage of an example over the canonical (a,b) grid
function coverage(ex,GX,GY,A0,A1,B0,B1){const c=cv(GX*4,GY*4),q=c.getContext('2d');const b=ex.box;
  // map box-normalised coordinates to the small canvas
  const sx=GX*4/((A1-A0)*b.w),sy=GY*4/((B1-B0)*b.h);q.setTransform(sx,0,0,sy,-(b.x+A0*b.w)*sx,-(b.y+b.h-B1*b.h)*sy);q.drawImage(ex.img,ex.ox,ex.oy);
  const d=q.getImageData(0,0,GX*4,GY*4).data,out=[];for(let j=0;j<GY;j++)for(let i=0;i<GX;i++){let s=0;for(let y=0;y<4;y++)for(let x=0;x<4;x++)s+=d[((j*4+y)*GX*4+i*4+x)*4+3];out.push(s/(16*255))}return out}

// ---------- the deformation basis: canonical (a,b) in box units (a across, b up from the floor) -> screen ----------
function D(z,a,b,jit,seed,K){
  let lx=(a-.5)*z.w,ly=-b*z.h;const bb=Math.max(0,b),ac=Math.min(1,Math.pow(2*a-1,2));
  lx+=z.lean*z.h*bb*bb;
  ly+=z.sag*z.h*bb*bb*(1-ac);
  lx*=1+.5*z.sq;ly*=1-z.sq;
  if(jit){lx+=(K.hash(seed*1.7)-.5)*jit;ly+=(K.hash(seed*2.9+3)-.5)*jit}
  const c=Math.cos(z.tilt),s=Math.sin(z.tilt);return [z.x+lx*c-ly*s,z.y+lx*s+ly*c]}
// textured triangle
function tri(g,img,s0,s1,s2,d0,d1,d2){
  const den=(s1[0]-s0[0])*(s2[1]-s0[1])-(s2[0]-s0[0])*(s1[1]-s0[1]);if(Math.abs(den)<1e-6)return;
  const ux=s1[0]-s0[0],uy=s1[1]-s0[1],vx=s2[0]-s0[0],vy=s2[1]-s0[1];
  const a=((d1[0]-d0[0])*vy-(d2[0]-d0[0])*uy)/den,c=((d2[0]-d0[0])*ux-(d1[0]-d0[0])*vx)/den;
  const b=((d1[1]-d0[1])*vy-(d2[1]-d0[1])*uy)/den,d=((d2[1]-d0[1])*ux-(d1[1]-d0[1])*vx)/den;
  const e=d0[0]-a*s0[0]-c*s0[1],f=d0[1]-b*s0[0]-d*s0[1];
  const mx=(d0[0]+d1[0]+d2[0])/3,my=(d0[1]+d1[1]+d2[1])/3,ex=p=>{const dx=p[0]-mx,dy=p[1]-my,l=Math.hypot(dx,dy)||1;return [p[0]+dx/l*.9,p[1]+dy/l*.9]};
  const p0=ex(d0),p1=ex(d1),p2=ex(d2);
  g.save();g.beginPath();g.moveTo(p0[0],p0[1]);g.lineTo(p1[0],p1[1]);g.lineTo(p2[0],p2[1]);g.closePath();g.clip();g.transform(a,b,c,d,e,f);
  const x0=Math.max(0,Math.floor(Math.min(s0[0],s1[0],s2[0])-2)),y0=Math.max(0,Math.floor(Math.min(s0[1],s1[1],s2[1])-2)),x1=Math.min(img.width,Math.ceil(Math.max(s0[0],s1[0],s2[0])+2)),y1=Math.min(img.height,Math.ceil(Math.max(s0[1],s1[1],s2[1])+2));
  if(x1>x0&&y1>y0)g.drawImage(img,x0,y0,x1-x0,y1-y0,x0,y0,x1-x0,y1-y0);g.restore()}
// a room cell without clipping: the cell's source rect under the mean affine of its two corner frames
// (the room field is smooth, so neighbouring cells meet to within a pixel; 1px overdraw hides the joins)
function quad(g,img,s00,s10,s01,s11,d00,d10,d01,d11){
  const sx=(s00[0]+s01[0])/2,sy=(s00[1]+s10[1])/2,sw=(s10[0]+s11[0])/2-sx,sh=(s01[1]+s11[1])/2-sy;if(sw<1||sh<1)return;
  const ax=((d10[0]-d00[0])+(d11[0]-d01[0]))/2/sw,ay=((d10[1]-d00[1])+(d11[1]-d01[1]))/2/sw,cx=((d01[0]-d00[0])+(d11[0]-d10[0]))/2/sh,cy=((d01[1]-d00[1])+(d11[1]-d10[1]))/2/sh;
  const mx=(d00[0]+d10[0]+d01[0]+d11[0])/4,my=(d00[1]+d10[1]+d01[1]+d11[1])/4;
  g.save();g.setTransform(ax,ay,cx,cy,mx,my);const x0=Math.max(0,sx-3),y0=Math.max(0,sy-3),x1=Math.min(img.width,sx+sw+3),y1=Math.min(img.height,sy+sh+3);
  g.drawImage(img,x0,y0,x1-x0,y1-y0,x0-(sx+sw/2),y0-(sy+sh/2),x1-x0,y1-y0);g.restore()}
// draw one mesh cell (two triangles) from an example texture
function cellFrom(g,ex,srcOf,V00,V10,V01,V11,ci){if(ex.cov&&ci!=null&&ex.cov[ci]<.002)return;const s00=srcOf(ex,V00.a,V00.b),s10=srcOf(ex,V10.a,V10.b),s01=srcOf(ex,V01.a,V01.b),s11=srcOf(ex,V11.a,V11.b);
  tri(g,ex.img,s00,s10,s11,V00.p,V10.p,V11.p);tri(g,ex.img,s00,s11,s01,V00.p,V11.p,V01.p)}
const srcSack=(ex,a,b)=>{const p=D(ex.z,a,b);return [p[0]-ex.ox,p[1]-ex.oy]};

// ---------- the room as a layered template: one deformation field, two example textures ----------
const RG={X:24,Y:14},BX=12,BY=7;   // fine mesh 24x14 for the warp; visibility blocks 12x7
function roomField(x,y){ // displacement from candle-room space to lamp-room space
  let dx=0,dy=0;const add=(cx,cy,sx,ox,oy)=>{const w=Math.exp(-((x-cx)**2+(y-cy)**2)/(2*sx*sx));dx+=w*ox;dy+=w*oy};
  add(CANDLE[0],CANDLE[1],420,LAMP[0]-CANDLE[0],LAMP[1]-CANDLE[1]);   // the candle's light moves to the lamp
  add(1884,520,260,140,0);                                              // the corner recedes into the dark
  add(250,620,260,-170,0);                                              // the door recedes
  const fl=Math.exp(-((y-868)**2)/(2*140*140));dy+=-18*fl;              // the floor line 868 -> 850
  return [dx,dy]}

function build(X,K){
  const key=X.film.join(',');if(CACHE.key===key)return CACHE.v;
  const Lg=X.ledger,k=X.k,eo=Lg.ev[k-1],ei=Lg.ev[k],Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed];
  const sO=Lg.states[k-1],sI=Lg.states[k];
  // examples and room textures
  function frame(D,lt,e,st){const order=D.layers||['bg','V','A'];const bg=cv(1920,1080),q=bg.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,1920,1080);const P={};
    for(const ly of order){const who=ly==='A'?e.A:e.V;const Lr=layerFull(D,lt,e.A,e.V,ly,st.body,ly==='bg'?null:st.levers[who],K);
      if(ly==='bg'||!Lr.box){q.drawImage(Lr.c,0,0);continue}const ex=example(Lr);ex.order=order.indexOf(ly);q.drawImage(ex.rem,0,0);P[who]=ex}
    return {bg,P}}
  const FO=frame(Do,T_OUT,eo,sO),FI=frame(Di,T_IN,ei,sI);
  const impO=sI.impossible.some(z=>z.k===k-1),impI=Lg.states[k+1].impossible.some(z=>z.k===k);
  // the room mesh: vertex v (candle space), source in candle texture = v, source in lamp texture = v + d(v)
  const room=[];for(let j=0;j<=RG.Y;j++)for(let i=0;i<=RG.X;i++){const x=i/RG.X*1920,y=j/RG.Y*1080;const d=roomField(x,y);if(i===0||i===RG.X)d[0]=0;if(j===0||j===RG.Y)d[1]=0;room.push({x,y,dx:d[0],dy:d[1],bx:i===0||i===RG.X,by:j===0||j===RG.Y})}
  // visibility state per room cell: switches at a time set by its distance from the lamp (the corner is last)
  const rcell=[];for(let j=0;j<BY;j++)for(let i=0;i<BX;i++){const cx=(i+.5)/BX*1920,cy=(j+.5)/BY*1080;
    const dist=Math.hypot(cx-LAMP[0],(cy-LAMP[1])*1.25);const vb=FO.P[eo.V]?FO.P[eo.V].box:{x:1750,y:700,w:150,h:170};
    const dc=Math.hypot(cx-(vb.x+vb.w/2),(cy-(vb.y+vb.h/2))*.8);rcell.push({i,j,cx,cy,tf:Math.min(2.72,.95+1.3*cl(0,1,dist/1500)+.75*Math.exp(-dc/330)+(K.hash(i*13+j*7+k)-.5)*.16)})}
  // ---------- the cast ----------
  const A0=eo.A,V0=eo.V,A1=ei.A,V1=ei.V;
  const mem=(s,kk)=>{const m=LEDGER.memories(Lg,s,k).find(q=>q.k===kk);return m?m.weight:0};
  const P={};
  for(const s of IDS){const inO=!!FO.P[s],inI=!!FI.P[s];
    P[s]={s,inO,inI,kind:inO&&inI?'stay':inO?'leave':inI?'enter':'by',exO:FO.P[s],exI:FI.P[s],alive:sI.alive[s],ghost:!sI.alive[s]&&inI,
      lvO:sO.levers[s],lvI:sI.levers[s]}}
  // few-shot: a doer behind the door jamb gets a second outgoing example (t=1.0) for the cells the jamb hid
  const GX=6,GY=7,AA=[-.45,1.45],BB=[-.18,1.32];
  for(const s of IDS){const p=P[s];if(!p.exO||p.kind!=='stay')continue;const b=p.exO.box;if(b.x>430)continue;
    const who=s===A0?'A':'V';const Lr=layerFull(Do,1.0,A0,V0,who,sO.body,sO.levers[s],K);const ex2=example(Lr);
    // the second example, fitted to the first one's box, keeps only the pixels the first one could not see
    const e1=p.exO,b1=e1.box,b2=ex2.box,fill=cv(e1.img.width,e1.img.height),q=fill.getContext('2d');
    q.save();q.beginPath();q.rect(b1.x-e1.ox-4,b1.y-e1.oy-4,b1.w+8,b1.h+8);q.clip();q.translate(-e1.ox,-e1.oy);q.translate(b1.x+b1.w/2,b1.y+b1.h);q.scale(b1.w/b2.w,b1.h/b2.h);q.translate(-(b2.x+b2.w/2),-(b2.y+b2.h));q.drawImage(ex2.img,ex2.ox,ex2.oy);q.restore();
    q.globalCompositeOperation='destination-out';q.drawImage(e1.img,0,0);
    p.exO2={img:fill,ox:e1.ox,oy:e1.oy,box:b1,z:e1.z};p.fuse=true}
  for(const s of IDS)for(const ex of [P[s].exO,P[s].exI,P[s].exO2])if(ex)ex.cov=coverage(ex,GX,GY,AA[0],AA[1],BB[0],BB[1]);
  // memory of event k-1 (what happened in the corner) on whoever goes on into the next shot
  for(const s of IDS){const p=P[s];p.memW=(s===A0||s===V0)?mem(s,k-1):0;p.meets=(s===A0&&(A1===V0||V1===V0))||(s===V0&&(A1===A0||V1===A0))}
  // schedules
  const tempoT=lv=>1-.18*cl(-1,1,lv.tempo);
  for(const s of IDS){const p=P[s],lv=p.lvI||p.lvO;p.wt=.5+.6*Math.max(0,lv.weight);p.tm=tempoT(lv);
    if(p.kind==='stay'){const zO=p.exO.z,zI=p.exI.z;p.dir=Math.sign(zI.x-zO.x)||1;
      if(s===V0){ // she is found where she was left; the new template is fitted to her crumpled pose in place, then she rises
        p.tw=[1.0,1.3];p.rise=[1.25,1.85];p.go=[1.8,2.95]}
      else if(s===A0){p.tw=[1.25,1.55];p.rise=null;p.go=[.75,2.9]}
      else{p.tw=[1.3,1.6];p.go=[.9,2.85]}
      p.go[1]=Math.min(2.98,p.go[0]+(p.go[1]-p.go[0])*p.tm);
      if(p.memW>.3){p.hes=Math.min(1,p.memW)*(p.meets?1:.6);}}
  }
  // meeting again: if the two must pass each other on the way to their marks, the doer of the corner goes first
  // and stands at its mark; the victim stops short of it, turns away, then passes behind it (darker, further back)
  if(P[A0].kind==='stay'&&P[V0].kind==='stay'){const a=P[A0],b=P[V0];const xa=a.exI.z.x,b0=b.exO.z.x,b1=b.exI.z.x;
    if((xa-b0)*(xa-b1)<0){a.go=[.6,1.85];b.tw=[.85,1.15];b.rise=[1.05,1.55];b.go=[1.45,2.95];const stop=xa+Math.sign(b0-xa)*((a.exI.z.w+b.exO.z.w)/2+60);
      b.hesAt=cl(.08,.9,(stop-b0)/(b1-b0));b.hes=Math.max(b.hes||0,.8);b.passBehind=A0}
    else{ // no crossing: they still slow as they come into the same light
      for(const q of [a,b])if(q.hes)q.hesAt=.7}}
  for(const s of IDS){const p=P[s];
    if(p.kind==='leave'){if(s===A0){p.go=[p.memW>.3?.95:.55,1.55];p.look=p.memW>.3?Math.min(1,p.memW):0}else{p.go=null}}
    if(p.kind==='enter'){const zI=p.exI.z;p.from=zI.x<960?-zI.w*.9-60:1920+zI.w*.9+60;if(p.from>960&&P[V0].kind==='leave')p.passBehind=V0;p.go=[1.05,2.9];p.go[1]=Math.min(2.98,p.go[0]+(p.go[1]-p.go[0])*p.tm);p.dir=Math.sign(zI.x-p.from)}
    // cell switch order inside a sack: bottom first, rising (the new example is fitted from the floor up)
    p.cellT=[];for(let j=0;j<GY;j++)for(let i=0;i<GX;i++)p.cellT.push((GY-1-j)/(GY-1)*.7+.3*K.hash(i*3.1+j*5.3+s.charCodeAt(0)))}
  // the leaving victim keeps her corner: her cells go dark with the corner's room cells
  if(P[V0].kind==='leave'){const b=P[V0].exO.box;const near=rcell.filter(c=>Math.abs(c.cx-(b.x+b.w/2))<200&&Math.abs(c.cy-(b.y+b.h/2))<240);P[V0].tOut=Math.max(...near.map(c=>c.tf),2.3)}
  // the evidence in the house
  const evid=sI.evidence.map((e,i)=>{const C=X.CONSEQS&&X.CONSEQS[e.deed];const n=sI.evidence.length;const x=470+(i+.5)/n*1180;const y=i%2?968:1012;return {e,C,x,y,age:k-1-e.k,rot:(K.hash(i*7.3+k)-.5)*.3}});
  // the dead who are in neither shot: a template with no example here (mesh only), lying by the wall
  const dead=IDS.filter(s=>P[s].kind==='by'&&!sI.alive[s]).map((s,i)=>({s,x:i?1560:420,deadAt:sI.deadAt[s]}));
  const v={FO,FI,room,rcell,P,GX,GY,AA,BB,evid,dead,impO,impI,A0,V0,A1,V1,ei,eo,sI};
  if(X.still){CACHE.key=key;CACHE.v=v}return v}

// ---------- latent pose of a sack at time u ----------
function hopPath(p,u,x0,x1,y0,y1,K){const [g0,g1]=p.go;let pr=sm(g0,g1,u);
  // hesitation: the memory of the corner stops it short and turns it away
  let away=0,bow=0;if(p.hes){const f=p.hesAt||.42,k1=lerp(g0,g1,f),k2=k1+.55*p.hes;
    if(u<k1)pr=f*sm(g0,k1,u);else if(u<k2){const q=Math.sin(Math.PI*cl(0,1,(u-k1)/(k2-k1)));pr=f-.05*q;away=q}
    else pr=f+(1-f)*sm(k2,Math.max(k2+.25,g1),u);bow=away*p.hes}
  const dist=Math.abs(x1-x0),nh=Math.max(2,Math.round(dist/(150+p.s.charCodeAt(0)%3*20)));const ph=pr*nh;
  const hop=Math.abs(Math.sin(Math.PI*ph))*(u>g0&&pr<1?1:0);
  const x=lerp(x0,x1,pr),y=lerp(y0,y1,pr)-hop*(16+10*p.wt)*(1-.5*bow);
  const land=(1-hop)*(u>g0&&pr<.999?1:0);
  return {x,y,pr,hop,land,away,bow}}
function pose(p,u,v,K){
  const s=p.s;let z,tex=null,sw=0,alpha=1,unc=0,cells=null,fuseA=0;
  if(p.kind==='stay'){const zO=p.exO.z,zI=p.exI.z;
    // the crumpled victim: the lamp-room template is fitted to her crumpled pose (her old box), then the pose relaxes
    let base=zO;const rise=p.rise?sm(p.rise[0],p.rise[1],u):1;
    const H=p.rise?lerp(zO.h,zI.h*.92,rise):zO.h,Wd=p.rise?lerp(zO.w,zI.w,rise):zO.w;
    const hp=hopPath(p,u,zO.x,zI.x,zO.y,zI.y,K);
    const w=lerp(Wd,zI.w,hp.pr),h=lerp(H,zI.h,hp.pr);
    const lean=.07*p.dir*(hp.hop>0?1:0)*Math.min(1,p.wt)-hp.away*.16*p.dir*(s===v.V0?1:.6)+(p.rise?(1-rise)*.06:0);
    const sag=hp.bow*.16+(p.rise?.1*(1-rise):0)+(s===v.A0&&p.memW>.3?.06*sm(.6,1.2,u)*(1-sm(2.6,3,u)):0);
    const sq=.06*p.wt*hp.land*Math.pow(1-hp.hop,3)-hp.bow*.05;
    z={x:hp.x,y:hp.y,w,h,lean,sag,sq,tilt:0};
    sw=1;// cell switch from candle example to lamp example
    cells=p.cellT.map(c=>sm(0,1,(u-lerp(p.tw[0],p.tw[1],c))/.06));
    unc=Math.max(Math.sin(Math.PI*cl(0,1,(u-p.go[0])/(p.go[1]-p.go[0]))),p.rise?Math.sin(Math.PI*cl(0,1,(u-p.tw[0])/(p.rise[1]-p.tw[0]))):0,hp.bow);
    unc*=1-sm(2.75,3.0,u);
    if(p.fuse)fuseA=sm(0,1,Math.abs(hp.x-zO.x)/120);
    if(p.ghost)alpha=1-.45*Math.sin(Math.PI*cl(0,1,u/DUR));
  }
  if(p.kind==='leave'){const zO=p.exO.z;
    if(p.go){ // the doer goes out through the door, looking back at the corner if it carries the guilt
      const lk=p.look?Math.sin(Math.PI*cl(0,1,(u-.25)/.65))*p.look:0;
      const pr=sm(p.go[0],p.go[1],u),hop=Math.abs(Math.sin(Math.PI*pr*3))*(pr>0&&pr<1?1:0);
      z={...zO,x:zO.x-pr*(zO.w+260),y:zO.y-hop*14,lean:.12*lk-.06*(pr>0&&pr<1?1:0),sag:.08*lk};
      unc=Math.max(.6*lk,Math.sin(Math.PI*pr))*.9}
    else{ // the victim is left as she was, alone, turned to the wall; the lamp never reaches her corner
      const tO=p.tOut;const curl=sm(.4,1.6,u);
      z={...zO,lean:.035*curl,sag:.04*curl,sq:.03*curl+.01*Math.sin(u*2.3)*curl};
      cells=p.cellT.map(c=>1-sm(0,1,(u-(tO-.25+c*.35))/.08));alpha=1;unc=.35*sm(.6,1.2,u)*(1-sm(tO-.2,tO+.2,u));p.goneAt=tO+.2}
  }
  if(p.kind==='enter'){const zI=p.exI.z;const hp=hopPath(p,u,p.from,zI.x,zI.y,zI.y,K);
    z={...zI,x:hp.x,y:hp.y,lean:.07*p.dir*(hp.hop>0?1:0),sq:.05*p.wt*hp.land*Math.pow(1-hp.hop,3)};
    // entering: first only the template (mesh), its cells fill with the example as it nears its example pose
    cells=p.cellT.map(c=>sm(0,1,(hp.pr-(.25+c*.55))/.12));unc=(1-sm(.75,1,hp.pr))*sm(p.go[0]-.2,p.go[0]+.2,u);
    if(p.ghost)alpha=1-.45*Math.sin(Math.PI*cl(0,1,u/DUR))}
  return {z,cells,unc,alpha,fuseA}}

function drawSack(g,p,ps,v,K,u){
  const {z,cells,unc,alpha}=ps;if(!z)return;const GX=v.GX,GY=v.GY,AA=v.AA,BB=v.BB;
  const exA=p.exO,exB=p.exI;
  // identity shortcut (exact seam): the pose equals an example and every cell shows that example
  const same=(e)=>e&&Math.abs(z.x-e.z.x)<.01&&Math.abs(z.y-e.z.y)<.01&&Math.abs(z.w-e.z.w)<.01&&Math.abs(z.h-e.z.h)<.01&&!z.lean&&!z.sag&&!z.sq&&!z.tilt;
  const allIs=val=>!cells||cells.every(c=>c===val);
  g.save();g.globalAlpha=alpha;
  if(p.kind!=='enter'&&same(exA)&&(p.kind==='leave'?allIs(1):allIs(0))&&!(p.fuse&&ps.fuseA>0)){g.drawImage(exA.img,exA.ox,exA.oy);g.restore();return}
  if(p.kind!=='leave'&&same(exB)&&allIs(1)){g.drawImage(exB.img,exB.ox,exB.oy);g.restore();return}
  const jit=unc*10*(z.w/150);const sd=p.s.charCodeAt(0)*31;
  const Vt=[];for(let j=0;j<=GY;j++)for(let i=0;i<=GX;i++){const a=lerp(AA[0],AA[1],i/GX),b=lerp(BB[1],BB[0],j/GY);
    const inner=a>-.05&&a<1.05&&b>-.05&&b<1.1;Vt.push({a,b,p:D(z,a,b,inner?jit:0,sd+i*17+j*29+Math.floor(u*8),K)})}
  for(let j=0;j<GY;j++)for(let i=0;i<GX;i++){const ci=j*GX+i;const V00=Vt[j*(GX+1)+i],V10=Vt[j*(GX+1)+i+1],V01=Vt[(j+1)*(GX+1)+i],V11=Vt[(j+1)*(GX+1)+i+1];
    const c=p.kind==='leave'?(p.go?1:cells[ci]):cells?cells[ci]:0;
    if(p.kind==='leave'){ if(c>.5)cellFrom(g,exA,srcSack,V00,V10,V01,V11,ci);continue}
    if(p.kind==='enter'){ if(c>.5)cellFrom(g,exB,srcSack,V00,V10,V01,V11,ci);continue}
    if(c>.5)cellFrom(g,exB,srcSack,V00,V10,V01,V11,ci);
    else{if(p.fuse&&ps.fuseA>0){g.save();g.globalAlpha=alpha*ps.fuseA;cellFrom(g,p.exO2,srcSack,V00,V10,V01,V11,ci);g.restore()}cellFrom(g,exA,srcSack,V00,V10,V01,V11,ci)}}
  g.restore();
  // the confidence map: the template's mesh shows where the pose is unseen (no example near it)
  if(unc>.03){g.save();g.globalAlpha=Math.min(1,unc)*.8*(p.ghost?.6:1);g.strokeStyle=COL[p.s];g.lineWidth=1.6;const n=4;
    for(let i=0;i<=n;i++){g.beginPath();for(let j=0;j<=n;j++){const q=D(z,i/n,j/n*1.02,jit,sd+i*5+j*11+Math.floor(u*8),K);j?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}
    for(let j=0;j<=n;j++){g.beginPath();for(let i=0;i<=n;i++){const q=D(z,i/n,j/n*1.02,jit,sd+i*5+j*11+Math.floor(u*8),K);i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}
    g.fillStyle=COL[p.s];for(let j=0;j<=n;j++)for(let i=0;i<=n;i++){const q=D(z,i/n,j/n*1.02,jit,sd+i*5+j*11+Math.floor(u*8),K);g.beginPath();g.arc(q[0],q[1],2.6+3*unc*K.hash(i*7+j*3+sd),0,7);g.fill()}
    g.restore()}
}

function impOverlay(g,a){if(a<.01)return;g.save();g.globalAlpha=a;g.fillStyle='rgba(120,220,150,.06)';for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2);g.restore()}

TRANSITION({k:8,scion:42,lineage:'Neural Layered Puppet — Few-Shot Structure Swarm',
  op:'Every sack and the room are re-fit as layered mesh templates under a small latent pose; between the outgoing example (candle room, t=5.99) and the incoming example (lamp room, t=0) the pose is unseen, so each template is warped by a deterministic deformation basis and its mesh is shown in proportion to that uncertainty, while each mesh cell switches its visibility state from the old example texture to the new one at its own time, the lamp\'s reach first and the corner last.',
  made:'The room is a 12x7 textured mesh carrying two example textures (the candle room with its remainder props, and the dark lamp room) and one smooth displacement field that moves the candle to the lamp and pushes the door and the corner into the dark. Each sack is a 6x7 mesh in box units carrying its outgoing and incoming deed layers (levers and carried damage baked in), with a second outgoing example from earlier in the deed to fill cells the door jamb hid.',
  moved:'A latent pose per sack (position, size, lean, sag, squash, tilt) is driven by hops whose height and landing squash follow the weight lever and whose duration follows the tempo lever; a sack that carries the memory of the corner stops short, bows and turns away, more so if it is about to meet the other one again. The victim, if she goes on, is re-fitted where she lies and rises; if not, she is left as she was and her cells go dark with the corner; the doer, if it leaves, goes out through the door and looks back if it carries guilt.',
  dur:DUR,
  draw(g,u,X,K){
    const v=build(X,K);
    // ---- room ----
    const w=sm(.7,2.85,u),bul=Math.sin(Math.PI*cl(0,1,(u-.6)/2.4));
    const roomFlip=c=>u>=c.tf;
    if(u<.6){g.drawImage(v.FO.bg,0,0)}
    else if(u>3.05){g.drawImage(v.FI.bg,0,0)}
    else{g.fillStyle='#1c1814';g.fillRect(0,0,1920,1080);
      const R=v.room,NX=RG.X+1;
      const disp=r=>{const bx=(r.x-LAMP[0]),by=(r.y-LAMP[1]),l=Math.hypot(bx,by)||1;const b=bul*18*Math.exp(-l/900);return [r.bx?r.x:r.x+w*r.dx+bx/l*b,r.by?r.y:r.y+w*r.dy+by/l*b]};
      const P2=R.map(disp);
      for(let j=0;j<RG.Y;j++)for(let i=0;i<RG.X;i++){const c=v.rcell[(j>>1)*BX+(i>>1)];const i00=j*NX+i,i10=i00+1,i01=i00+NX,i11=i01+1;const fl=roomFlip(c);
        const S=fl?(r=>[r.x+r.dx,r.y+r.dy]):(r=>[r.x,r.y]);const img=fl?v.FI.bg:v.FO.bg;
        quad(g,img,S(R[i00]),S(R[i10]),S(R[i01]),S(R[i11]),P2[i00],P2[i10],P2[i01],P2[i11])}
      // cells near their switch show their mesh edge (the room template's own uncertainty)
      g.save();g.lineWidth=1.2;for(const c of v.rcell){const d=u-c.tf;if(d<-.18||d>.22)continue;const a=d<0?sm(-.18,0,d):1-sm(0,.22,d);
        const i00=2*c.j*NX+2*c.i;const q=[P2[i00],P2[i00+1],P2[i00+2],P2[i00+NX+2],P2[i00+2*NX+2],P2[i00+2*NX+1],P2[i00+2*NX],P2[i00+NX]];g.strokeStyle=`rgba(245,220,160,${.32*a})`;g.beginPath();q.forEach((p,n)=>n?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.stroke();
        g.fillStyle=`rgba(245,220,160,${.5*a})`;for(let n=0;n<8;n+=2){const p=q[n];g.beginPath();g.arc(p[0],p[1],2.2,0,7);g.fill()}}g.restore()}
    // ---- evidence still in the house (lying on the floor of the old room until its cell is relearned) ----
    const ea=sm(.25,.75,u);
    if(ea>.01)for(const E of v.evid){const c=v.rcell.find(c=>Math.abs(c.cx-E.x)<=80+1e-6&&Math.abs(c.cy-E.y)<=78)||{tf:2.4};const a=ea*(1-sm(c.tf-.05,c.tf+.05,u));if(a<.01)continue;
      const d=roomField(E.x,E.y),x=E.x+w*d[0],y=E.y+w*d[1];const bw=104,bh=70;g.save();g.globalAlpha=a;g.translate(x,y);g.rotate(E.rot);
      g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse(0,bh*.42,bw*.55,9,0,0,7);g.fill();
      try{if(E.C&&E.C.trace)E.C.trace(g,{x:-bw/2,y:-bh/2,w:bw,h:bh},E.age,K)}catch(e){}g.restore()}
    // ---- the dead in neither shot: a template with no example (mesh only), lying by the wall ----
    for(const d of v.dead){const a=sm(.35,.9,u)*(1-sm(2.4,2.9,u));if(a<.01)continue;const C=K.CAST[d.s];const z={x:d.x,y:880,w:C.h*1.15,h:C.w*.55,lean:0,sag:-.05,sq:0,tilt:0};
      g.save();g.globalAlpha=a*.35;g.fillStyle='#8c8a86';g.beginPath();[[0,0],[1,0],[1,1],[0,1]].forEach(([i,j],n)=>{const q=D(z,i,j);n?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])});g.closePath();g.fill();
      g.globalAlpha=a*.9;g.strokeStyle=COL[d.s];g.lineWidth=2;const n=4;
      for(let i=0;i<=n;i++){g.beginPath();for(let j=0;j<=n;j++){const q=D(z,i/n,j/n);j?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}
      for(let j=0;j<=n;j++){g.beginPath();for(let i=0;i<=n;i++){const q=D(z,i/n,j/n);i?g.lineTo(q[0],q[1]):g.moveTo(q[0],q[1])}g.stroke()}g.restore()}
    // ---- sacks: in the incoming deed's layer order (victim then doer), the outgoing victim under all ----
    const order=IDS.slice().sort((a,b)=>{const r=p=>p.kind==='leave'?(p.s===v.V0?0:1):p.exI?2+(p.exI.order||0):1;return r(v.P[a])-r(v.P[b])});
    const PS={};for(const s of IDS){const p=v.P[s];if(p.kind!=='by')PS[s]=pose(p,u,v,K)}
    for(const s of IDS){const p=v.P[s];if(!p.passBehind||!PS[s].z)continue;const o=PS[p.passBehind].z;if(!o)continue;const z=PS[s].z;
      const ov=cl(0,1,1-(Math.abs(z.x-o.x)-(z.w+o.w)/2)/120);if(ov>0){PS[s].behind=ov;z.w*=1-.12*ov;z.h*=1-.12*ov;z.y-=14*ov}}
    order.sort((a,b)=>((PS[a]&&PS[a].behind)?-1:0)-((PS[b]&&PS[b].behind)?-1:0));
    for(const s of order){const p=v.P[s];if(p.kind==='by')continue;const ps=PS[s];if(p.goneAt&&u>p.goneAt)continue;
      // the victim left in the corner sinks into the dark before her cells are let go
      const dk=p.kind==='leave'&&!p.go?.55*sm(1.0,p.tOut-.15,u):0;const br=1-.45*(ps.behind||0)-dk;
      if(br<.995){const o=v.tmp||(v.tmp=cv(1920,1080)),q=o.getContext('2d');q.setTransform(1,0,0,1,0,0);q.clearRect(0,0,1920,1080);drawSack(q,p,ps,v,K,u);g.save();g.filter=`brightness(${br})`;g.drawImage(o,0,0);g.restore()}else drawSack(g,p,ps,v,K,u)}
    // impossible-event overlays (Calvino's rejected contradictions) follow the visibility of each example
    if(v.impO)impOverlay(g,1-sm(.9,2.5,u));if(v.impI)impOverlay(g,sm(.9,2.5,u)+(u>3.05?1:0)*0);
  },
  sound(ac,out,t0,X,K){
    const SN=K.SND,H=K.hash;let v;try{v=CACHE.key===X.film.join(',')?CACHE.v:build({...X,DEEDS:window.DEEDS,CONSEQS:window.CONSEQS,MEMORIES:window.MEMORIES},K)}catch(e){return}
    const bus=ac.createGain();bus.gain.value=4;bus.connect(out);out=bus;   // the transition is quiet grains; lift them to the film's level
    const at=x=>t0+x,pan=x=>cl(-1,1,x/960-1);
    // the candle room's hush thins out as the room is relearned
    SN.cloud(ac,out,at(0),1.8,12,{bp:700,q:.7,a:.03,d:[.08,.22],spread:.5},u=>1-u);
    // each relearned room cell: a small glassy tick, panned by where the cell is (every second cell)
    v.rcell.forEach((c,i)=>{if(i%3)return;SN.grain(ac,out,at(c.tf),{f:2600+H(i)*1800,d:.012,a:.035,pan:pan(c.cx),att:.05})});
    // the lamp room's harmonic series arrives: 110 Hz x the incoming pair's harmonic numbers, pulsed, rising
    const HN={R:4,B:3,I:6,O:8};for(const s of [v.A1,v.V1]){const f=110*HN[s];for(let i=0;i<6;i++){const tt=1.6+i*.3;SN.grain(ac,out,at(tt),{f,d:.24,a:.012+.03*i/5,pan:s===v.A1?-.35:.35,att:.2})}}
    for(const s of IDS){const p=v.P[s];if(p.kind==='by')continue;
      if(p.kind==='stay'||p.kind==='enter'){const x0=p.kind==='stay'?p.exO.z.x:p.from,x1=p.exI.z.x;const nh=Math.max(2,Math.round(Math.abs(x1-x0)/(150+s.charCodeAt(0)%3*20)));
        // a footfall per hop landing (the sack's own voice), sampled from the actual pose
        let last=0;for(let tt=p.go[0];tt<=p.go[1]+.05;tt+=1/60){const ps=pose(p,tt,v,K);const x=ps.z?ps.z.x:x1;const ph=Math.abs(x-x0)/(Math.abs(x1-x0)||1)*nh;const n=Math.floor(ph+.5);if(n>last&&n<=nh){last=n;SN.say(ac,out,s,at(tt),s==='B'&&n%3?'tick':'step',.5,pan(x))}}
        SN.say(ac,out,s,at(p.go[1]),'land',.35,pan(x1));
        // the sack's cells switch to the new example: a short cloth rustle
        if(p.tw)SN.cloud(ac,out,at(p.tw[0]),p.tw[1]-p.tw[0]+.1,25,{bp:3200,q:1,a:.03,d:[.01,.04],spread:.2},u=>Math.sin(Math.PI*u))}
      if(s===v.V0&&p.kind==='stay'){SN.say(ac,out,s,at(.5),'breathe',.8,pan(p.exO.z.x));SN.say(ac,out,s,at(p.rise[0]),'sink',.35,pan(p.exO.z.x))}
      if(s===v.V0&&p.kind==='leave'){SN.say(ac,out,s,at(.7),'breathe',1.2,pan(p.exO.z.x));SN.cloud(ac,out,at(p.tOut-.2),.5,30,{bp:500,a:.025,d:[.05,.15]},u=>1-u)}
      if(p.hes){const k1=lerp(p.go[0],p.go[1],.42);SN.say(ac,out,s,at(k1+.05),'react',.35*p.hes,0);SN.say(ac,out,s,at(k1+.2),'breathe',.5,0)}
      if(p.kind==='leave'&&p.go){SN.grain(ac,out,at(p.go[1]-.1),{f:140,d:.06,a:.08,noise:.5,bp:600,pan:-.9});SN.grain(ac,out,at(p.go[1]-.04),{bp:2400,q:3,d:.02,a:.07,pan:-.9});if(p.look)SN.say(ac,out,s,at(.45),'react',.3*p.look,-.9)}}
  }
});
})();
