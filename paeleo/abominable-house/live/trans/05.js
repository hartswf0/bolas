// TRANSITION 05 · Prostitution (state-machine parlour) -> Threatening with a Gun (IK corner)
// SCION 11 · Connelly Barnes, Video Puppetry tabletop.
// The overhead camera pulls up off the parlour: the shot was a paper stage card lying on a table, and
// every sack is a paper cutout (its own deed layer, levers baked, cut out on its mark box). Next to the
// parlour card lies the gun corner's card. Hands move the cutouts across the table: leaving sacks are slid
// off to the table edge, staying sacks are carried from one card to the other and turned over (the back of
// each cutout is the same sack drawn in the incoming language), entering sacks are picked up from the table
// edge, turned over and set on their marks. The hands exist only as occlusion masks (hatched, dashed): the
// composite never records them. Each cutout leaves its tracked transform as a trail (the recorded
// performance). The camera then comes down on the corner card until it is the incoming frame.
// Invariant (numeric, checked by the harness): u=0 is the outgoing deed's lever composite at t=5.99,
// u=dur is deed 06's lever composite at t=0 (carry = states[5].body).
(function(){
const IDS=['R','B','I','O'];
const COL={R:'#a0574c',B:'#5a5048',I:'#c9b089',O:'#9a58b0'};
const GAP=170, C2X=1920+GAP;            // world x of card 2 (the gun corner)
const REST_Y=1500;                      // world y of the table-edge row (bottom of resting cutouts)
const OV={s:.6,cx0:1640,cx1:2420,cy:790};       // overview camera
const CACHE={};
const sm=(a,b,x)=>{const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)};
const cl=(a,b,x)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,u)=>a+(b-a)*u;
function cv(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c}

// ---------- the deed layer, composited exactly as film.html composites it (levers baked in) ----------
function layerFull(D,lt,A,V,ly,carry,lev,K){
  const raw=cv(1920,1080),q=raw.getContext('2d');try{D.draw(q,lt,A,V,K,{layer:ly,carry})}catch(e){}
  if(ly==='bg'||!D.marks)return {c:raw};
  const mk=D.marks(lt,A,V,K,{carry}),b=mk[ly];
  const f=1+.14*Math.max(-1,Math.min(1,lev.loom))-.22*lev.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const fl=[];if(lev.grey>.05)fl.push(`grayscale(${Math.min(1,lev.grey)}) brightness(${1-.25*lev.grey})`);if(lev.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lev.halo)}px rgba(255,236,180,${Math.min(.9,lev.halo)}))`);
  if(lev.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lev.shadow)}px ${Math.round(-30*lev.shadow)}px ${Math.round(18*lev.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lev.shadow*.4)}))`);
  const out=cv(1920,1080),o=out.getContext('2d');o.filter=fl.join(' ')||'none';o.translate(cx,by);o.scale(f,f);o.translate(-cx,-by);o.drawImage(raw,0,0);
  return {c:out,box:{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}};
}
// cut a piece out of a layer on its mark box; the rest of the layer stays on the card (props, floor marks)
function cutPiece(L){
  const b=L.box;const x0=Math.max(0,Math.floor(b.x-110)),y0=Math.max(0,Math.floor(b.y-80)),x1=Math.min(1920,Math.ceil(b.x+b.w+30)),y1=Math.min(1080,Math.ceil(b.y+b.h+22));
  const w=Math.max(2,x1-x0),h=Math.max(2,y1-y0);const img=cv(w,h);img.getContext('2d').drawImage(L.c,x0,y0,w,h,0,0,w,h);
  const rem=cv(1920,1080),r=rem.getContext('2d');r.drawImage(L.c,0,0);r.clearRect(x0,y0,w,h);
  // paper edge: the cutout's silhouette dilated, filled with paper
  const P=9,edge=cv(w+2*P,h+2*P),e=edge.getContext('2d');for(let i=0;i<16;i++){const a=i/16*Math.PI*2;e.drawImage(img,P+Math.cos(a)*P*.8,P+Math.sin(a)*P*.8)}
  e.globalCompositeOperation='source-in';e.fillStyle='#f3ecdc';e.fillRect(0,0,w+2*P,h+2*P);
  const sil=cv(w+2*P,h+2*P),s=sil.getContext('2d');s.drawImage(edge,0,0);s.globalCompositeOperation='source-in';s.fillStyle='#000';s.fillRect(0,0,w+2*P,h+2*P);
  return {img,edge,sil,P,ox:x0,oy:y0,ax:b.x+b.w/2,ay:b.y+b.h,h:b.h,w:b.w,rem};
}
function impOverlay(q){q.fillStyle='rgba(120,220,150,.06)';for(let y=0;y<1080;y+=6)q.fillRect(0,y,1920,2)}

function build(X,K){
  const key=X.film.join(',');if(CACHE.key===key)return CACHE.v;
  const Lg=X.ledger,k=X.k,eo=Lg.ev[k-1],ei=Lg.ev[k],Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed];
  const sO=Lg.states[k-1],sI=Lg.states[k],tO=5.99,tI=0.001;
  const cards=[],pieces={};
  function card(D,lt,e,st,impK){
    const order=D.layers||['bg','V','A'],c=cv(1920,1080),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,1920,1080);const P={};
    for(const ly of order){const Lr=layerFull(D,lt,e.A,e.V,ly,st.body,ly==='bg'?null:st.levers[ly==='A'?e.A:e.V],K);
      if(ly==='bg'||!Lr.box){q.drawImage(Lr.c,0,0);continue}const p=cutPiece(Lr);q.drawImage(p.rem,0,0);p.order=order.indexOf(ly);P[ly==='A'?e.A:e.V]=p}
    const imp=Lg.states[impK].impossible.some(z=>z.k===impK-1);
    return {c,P,imp};
  }
  const c1=card(Do,tO,eo,sO,k),c2=card(Di,tI,ei,sI,k+1);
  // any sack not in a deed is drawn in that deed's language as a bystander (its first frame, its levers)
  function bystander(D,lt,s,st){const other=IDS.find(o=>o!==s);const Lr=layerFull(D,lt,s,other,'A',st.body,st.levers[s],K);return cutPiece(Lr)}
  for(const s of IDS){
    const old=c1.P[s]||bystander(Do,0,s,sO),nw=c2.P[s]||bystander(Di,tI,s,sI);
    const inO=!!c1.P[s],inI=!!c2.P[s];
    pieces[s]={s,old,nw,inO,inI,kind:inO&&inI?'stay':inO?'leave':inI?'enter':'by',alive:sI.alive[s],
      ghost:!sI.alive[s]&&inI, role:s===ei.A?'A':s===ei.V?'V':null};
  }
  // resting places on the table edge (the hall between rooms): nearest free slot
  const SL=[380,860,1340,1820,2300,2780,3260,3740],used=[];
  const slot=x=>{let best=-1,bd=1e9;SL.forEach((v,i)=>{if(!used.includes(i)&&Math.abs(v-x)<bd){bd=Math.abs(v-x);best=i}});used.push(best);return SL[best]};
  const order=['leave','stay','enter','by'];let nst=0,nen=0,nlv=0;
  for(const kind of order)for(const s of IDS){const p=pieces[s];if(p.kind!==kind)continue;
    if(kind==='leave'){p.from={x:p.old.ax,y:p.old.ay};p.to={x:slot(p.old.ax),y:REST_Y};p.t0=.72+nlv*.16;p.t1=p.t0+.78;p.f0=p.t0+.3;p.f1=p.f0+.3;nlv++}
    if(kind==='stay'){p.from={x:p.old.ax,y:p.old.ay};p.to={x:C2X+p.nw.ax,y:p.nw.ay};p.t0=.88+nst*.18;p.t1=p.t0+1.05;p.f0=p.t0+.4;p.f1=p.f0+.34;nst++}
    if(kind==='enter'){const tx=C2X+p.nw.ax;p.from={x:slot(tx),y:REST_Y};p.to={x:tx,y:p.nw.ay};p.t0=1.1+nen*.18;p.t1=p.t0+.95;p.f0=p.t0+.16;p.f1=p.f0+.32;nen++}
    if(kind==='by'){const x=slot(1980);p.from=p.to={x,y:REST_Y};p.t0=1.55+(s.charCodeAt(0)%3)*.1;p.t1=p.t0+.5;p.f0=p.t0+.12;p.f1=p.f0+.28}
  }
  // memory on the way: the doer hesitates over its victim if it carries a strong memory of it
  const memA=LEDGER.memories(Lg,ei.A,k).filter(m=>m.other===ei.V&&m.weight>.3);
  const memV=LEDGER.memories(Lg,ei.V,k).filter(m=>m.other===ei.A&&m.weight>.3);
  const pa=pieces[ei.A];if(memA.length&&pa.kind!=='by'){pa.hes=Math.min(1,memA[0].weight);pa.t1+=.22}
  if(memV.length)pieces[ei.V].tremble=Math.min(1,memV[0].weight);
  // evidence still in the house: each earlier deed's trace, on a slip of card on the table
  const evid=sI.evidence.map((e,i)=>{const C=X.CONSEQS&&X.CONSEQS[e.deed];const pos=[[2005,250],[2005,560],[2005,860],[190,1610],[3800,1610],[1100,1630],[2950,1630],[2005,1180],[600,1180],[3450,1180],[1580,1650],[2500,1650]][i%12];
    return {e,C,x:pos[0],y:pos[1],age:k-1-e.k,rot:(K.hash(i*7.3+k)-.5)*.5}});
  const v={c1,c2,pieces,evid,ei,eo,sI,memA,memV,dur:3.3};if(X.still){CACHE.key=key;CACHE.v=v}return v;
}

// ---------- the camera (overhead, over the table) ----------
function cam(u,dur){
  const a=sm(.1,.75,u),b=sm(2.45,3.0,u);
  const s0=1,s1=OV.s;let s=Math.exp(lerp(Math.log(s0),Math.log(s1),a));s=Math.exp(lerp(Math.log(s),Math.log(1),b));
  // pan follows the action across the overview, then descends on card 2
  const px=lerp(OV.cx0,OV.cx1,sm(.7,2.4,u));
  let cx=lerp(960,px,a),cy=lerp(540,OV.cy,a);cx=lerp(cx,C2X+960,b);cy=lerp(cy,540,b);
  // when zooming, keep the target point fixed proportionally (blend by scale so the motion reads as a descent)
  return {s,cx,cy};
}
const W2S=(C,x,y)=>({x:(x-C.cx)*C.s+960,y:(y-C.cy)*C.s+540});

// a piece's state at time u
function pstate(p,u,K){
  let pr;
  if(p.hes){const D=p.t1-p.t0;const k1=p.t0+D*.38,k2=k1+.34,k3=k2+.12;
    pr=u<k1?.52*sm(p.t0,k1,u):u<k2?.52-.07*sm(k1,k2,u):u<k3?.45+.02*sm(k2,k3,u):.47+.53*sm(k3,p.t1,u)}
  else pr=sm(p.t0,p.t1,u);
  const held=u>p.t0-.05&&u<p.t1+.05;const lift=Math.sin(Math.PI*cl(0,1,(u-p.t0)/(p.t1-p.t0)))*(p.kind==='by'?.4:1);
  let x=lerp(p.from.x,p.to.x,pr),y=lerp(p.from.y,p.to.y,pr)-90*lift;
  let fp=cl(0,1,(u-p.f0)/(p.f1-p.f0));fp=fp*fp*(3-2*fp);
  const showNew=fp>=.5,fx=Math.abs(Math.cos(Math.PI*fp));
  // displayed height travels from the old drawing's size to the new one's
  const H=lerp(p.old.h,p.nw.h,sm(p.f0,p.f1,u));
  let rot=0;
  if(!p.alive){const R=Math.PI/2*.94;     // a body lies on its side on the table; a ghost rises from it
    if(p.kind==='by')rot=R;else if(p.kind==='leave')rot=R*sm(p.t1-.25,p.t1,u);else if(p.kind==='enter')rot=R*(1-sm(p.t0,p.t0+.4,u))}
  if(p.hes&&u>p.t0&&u<p.t1)rot+=Math.sin(u*31)*.035*p.hes*sm(p.t0+.3,p.t0+.5,u)*(1-sm(p.t1-.35,p.t1,u));
  if(p.tremble&&u>p.t0&&u<p.t1+.2){x+=Math.sin(u*57)*4*p.tremble;rot+=Math.sin(u*43)*.01*p.tremble}
  return {x,y,H,fx,showNew,fp,rot,held,lift,pr};
}

function drawPiece(g,p,st,C,edgeA,K,lv,ghostA,ghostT){
  const im=st.showNew?p.nw:p.old,k=st.H/im.h;
  g.save();const S=W2S(C,st.x,st.y);g.translate(S.x,S.y);g.rotate(st.rot);g.scale(C.s*k*Math.max(.02,st.fx),C.s*k);
  const dx=im.ox-im.ax,dy=im.oy-im.ay;
  // cast shadow on the table: longer for a lifted piece and for a sack whose shadow lever is high
  if(edgeA>0){const sh=(10+40*st.lift+26*Math.max(0,lv.shadow))*edgeA;g.globalAlpha=.45*edgeA;g.drawImage(im.sil,dx-im.P+sh*.6,dy-im.P+sh);g.globalAlpha=edgeA;if(ghostT>.01){g.globalAlpha=edgeA*(1-ghostT);g.drawImage(im.edge,dx-im.P,dy-im.P);g.globalAlpha=edgeA*ghostT;g.filter='sepia(1) hue-rotate(75deg) saturate(2.5) brightness(1.05)'}g.drawImage(im.edge,dx-im.P,dy-im.P);g.filter='none'}
  g.globalAlpha=ghostA;g.drawImage(im.img,dx,dy);
  // the back of the paper shows white as it turns
  const back=1-st.fx;if(back>.02&&st.fp>0&&st.fp<1){g.globalAlpha=back*.9;g.drawImage(im.edge,dx-im.P,dy-im.P)}
  g.restore();
  // fiducial corners while the tracker holds the piece
  if(st.held&&edgeA>.3){const w=im.w*k*C.s*st.fx,h=st.H*C.s,x0=S.x-w/2,y0=S.y-h,c=COL[p.s];g.save();g.strokeStyle=c;g.globalAlpha=.85*edgeA;g.lineWidth=3;const L=14;
    for(const[cx,cy,sx,sy]of[[x0,y0,1,1],[x0+w,y0,-1,1],[x0,S.y,1,-1],[x0+w,S.y,-1,-1]]){g.beginPath();g.moveTo(cx,cy+sy*L);g.lineTo(cx,cy);g.lineTo(cx+sx*L,cy);g.stroke()}g.restore()}
}

// the puppeteer's hand, present only as its occlusion mask (keyed out of the composite)
function hand(g,x,y,sc,ang,a){if(a<.01)return;g.save();g.translate(x,y);g.rotate(ang);g.scale(sc,sc);g.globalAlpha=a;
  // seen from overhead: fingertips at the contact (0,0), the arm reaching back toward the puppeteer
  const parts=[];const cap=(x0,y0,x1,y1,r)=>{const p=new Path2D(),an=Math.atan2(y1-y0,x1-x0);p.arc(x0,y0,r,an+Math.PI/2,an-Math.PI/2);p.arc(x1,y1,r,an-Math.PI/2,an+Math.PI/2);p.closePath();parts.push(p)};
  cap(0,420,8,170,62);                                  // forearm
  const palm=new Path2D();palm.roundRect(-58,40,124,140,40);parts.push(palm);
  cap(-42,-2,-44,60,15);cap(-14,-14,-14,56,16);cap(14,-10,14,56,16);cap(40,6,38,64,14); // four fingers
  cap(86,64,60,130,17);                                 // thumb
  const all=new Path2D();for(const p of parts)all.addPath(p);
  g.fillStyle='rgba(120,190,215,.16)';g.fill(all,'nonzero');g.save();g.clip(all,'nonzero');g.strokeStyle='rgba(150,215,235,.3)';g.lineWidth=3;for(let i=-700;i<700;i+=20){g.beginPath();g.moveTo(i,-100);g.lineTo(i+620,520);g.stroke()}g.restore();
  g.setLineDash([10,8]);g.lineWidth=3;g.strokeStyle='rgba(175,232,250,.75)';for(const p of parts)g.stroke(p);g.setLineDash([]);
  g.restore()}

function table(g,C,u,K){
  g.fillStyle='#1d140e';g.fillRect(0,0,1920,1080);
  // wood grain in world space (it pans with the table)
  g.save();g.strokeStyle='rgba(120,80,45,.16)';g.lineWidth=Math.max(1,3*C.s);
  for(let i=0;i<70;i++){const wy=-600+i*44+K.hash(i)*20;const p0=W2S(C,-800,wy);const p1=W2S(C,4800,wy+K.hash(i*3)*60-30);if(p1.y<-20&&p0.y<-20||p0.y>1100&&p1.y>1100)continue;
    g.beginPath();g.moveTo(p0.x,p0.y);g.bezierCurveTo((p0.x*2+p1.x)/3,p0.y+12*Math.sin(i),(p0.x+p1.x*2)/3,p1.y-12*Math.cos(i),p1.x,p1.y);g.stroke()}g.restore();
  // the capture lamp over the table
  const L=W2S(C,2045,700),gr=g.createRadialGradient(L.x,L.y,50*C.s,L.x,L.y,2600*C.s);gr.addColorStop(0,'rgba(255,225,170,.16)');gr.addColorStop(1,'rgba(0,0,0,.35)');g.fillStyle=gr;g.fillRect(0,0,1920,1080)}

function cardAt(g,C,c,wx,imp){const p=W2S(C,wx,0),w=1920*C.s,h=1080*C.s;
  if(C.s<.999){g.save();g.fillStyle='rgba(0,0,0,.5)';g.fillRect(p.x+12*C.s+6,p.y+18*C.s+6,w,h);g.fillStyle='#efe7d6';const m=Math.max(2,14*C.s);g.fillRect(p.x-m,p.y-m,w+2*m,h+2*m);g.restore()}
  g.drawImage(c,p.x,p.y,w,h)}
function impAt(g,C,wx){const p=W2S(C,wx,0);g.save();g.beginPath();g.rect(p.x,p.y,1920*C.s,1080*C.s);g.clip();g.translate(p.x,p.y);g.scale(C.s,C.s);impOverlay(g);g.restore()}
function regMarks(g,C,wx,a){if(a<.02)return;g.save();g.globalAlpha=a;g.strokeStyle='#e8f4ff';g.lineWidth=2;
  for(const[x,y]of[[wx-40,-40],[wx+1960,-40],[wx-40,1120],[wx+1960,1120]]){const p=W2S(C,x,y);g.beginPath();g.arc(p.x,p.y,9,0,7);g.moveTo(p.x-16,p.y);g.lineTo(p.x+16,p.y);g.moveTo(p.x,p.y-16);g.lineTo(p.x,p.y+16);g.stroke()}g.restore()}

TRANSITION({k:5,scion:11,lineage:'Connelly Barnes — Video Puppetry Tabletop',
  op:'The overhead camera rises off the parlour to show it is a paper stage card on a table; each sack is cut out of its deed layer on its mark box, hands (present only as keyed-out occlusion masks) slide the cutouts across the table to the gun-corner card or off to the table edge, turning each one over so its back is the same sack drawn in the incoming language, and the camera descends on the corner card.',
  made:'Two stage cards (the parlour and the corner, each its deed\'s background plus whatever its sack layers leave outside the cutouts) lie side by side on a dark table with registration marks; the sacks are paper cutouts with a white cut edge, each a two-sided piece (outgoing drawing on the face, incoming drawing on the back, levers and carried damage baked in), and the house\'s evidence lies on slips of card along the table edge.',
  moved:'A schedule of grips: each cutout is held between a grip and a release, translated along an arc, lifted (longer shadow) and flipped about its vertical axis; its tracked transform leaves a trail in the sack\'s colour. The camera interpolates in log-scale from the outgoing card to an overview of both cards and down to the incoming card; a doer that remembers its victim stalls and backs up mid-carry.',
  dur:3.3,
  draw(g,u,X,K){
    const v=build(X,K);const dur=v.dur,C=cam(u,dur);
    g.save();
    {table(g,C,u,K);
      const reg=sm(.35,.7,u)*(1-sm(2.4,2.75,u));
      cardAt(g,C,v.c1.c,0,v.c1.imp);cardAt(g,C,v.c2.c,C2X,v.c2.imp);regMarks(g,C,0,reg*.7);regMarks(g,C,C2X,reg*.7);
      // evidence slips: the house's history so far
      const ea=sm(.3,.75,u);
      if(ea>.01)for(const E of v.evid){const p=W2S(C,E.x,E.y),bw=150*C.s,bh=112*C.s;g.save();g.globalAlpha=ea;g.translate(p.x,p.y);g.rotate(E.rot);
        g.fillStyle='rgba(0,0,0,.45)';g.fillRect(-bw/2+5,-bh/2+7,bw,bh);g.fillStyle='#efe7d6';g.fillRect(-bw/2,-bh/2,bw,bh);g.fillStyle='#2a221c';g.fillRect(-bw/2+5,-bh/2+5,bw-10,bh-10);
        try{if(E.C&&E.C.trace)E.C.trace(g,{x:-bw/2+6,y:-bh/2+6,w:bw-12,h:bh-12},E.age,K)}catch(e){}
        g.restore()}
      // trails: the recorded performance of each tracked cutout
      const ta=sm(.75,1,u)*(1-sm(2.35,2.75,u));
      if(ta>.01)for(const s of IDS){const p=v.pieces[s];if(p.kind==='by')continue;const te=Math.min(u,p.t1);if(te<=p.t0)continue;g.save();g.strokeStyle=COL[s];g.globalAlpha=.75*ta;g.lineWidth=3;g.beginPath();
        let first=true;for(let tt=p.t0;tt<=te+1e-6;tt+=.03){const st=pstate(p,tt,K);const q=W2S(C,st.x,st.y-st.H*.5);if(first){g.moveTo(q.x,q.y);first=false}else g.lineTo(q.x,q.y)}g.stroke();
        g.fillStyle=COL[s];for(let tt=p.t0;tt<=te;tt+=.12){const st=pstate(p,tt,K);const q=W2S(C,st.x,st.y-st.H*.5);g.beginPath();g.arc(q.x,q.y,4,0,7);g.fill()}g.restore()}
      // pieces: resting first, held ones on top (in the incoming deed's layer order at the end)
      const edgeA=sm(.12,.45,u)*(1-sm(2.55,2.95,u));
      const list=IDS.map(s=>({p:v.pieces[s],st:pstate(v.pieces[s],u,K)}));
      list.sort((a,b)=>(a.st.held?1:0)-(b.st.held?1:0)||(((a.st.showNew?a.p.nw:a.p.old).order??-1)-((b.st.showNew?b.p.nw:b.p.old).order??-1)));
      for(const {p,st}of list){const lv=(st.showNew?v.sI:X.ledger.states[X.k-1]).levers[p.s]||{};
        let ga=1,gt=0;if(p.ghost){gt=sm(.2,.6,u)*(1-sm(2.5,2.95,u));ga=1-.5*gt}
        if(!p.alive&&p.kind!=='stay'&&!p.ghost){g.save();g.filter='grayscale(1) brightness(.8)';drawPiece(g,p,st,C,edgeA,K,lv,1,0);g.restore()}else drawPiece(g,p,st,C,edgeA,K,lv,ga,gt)}
      if(v.c1.imp)impAt(g,C,0);if(v.c2.imp)impAt(g,C,C2X);
      // hands (masks only)
      for(const {p,st}of list){const a=sm(p.t0-.25,p.t0,u)*(1-sm(p.t1,p.t1+.2,u));if(a<.01)continue;
        const tip=W2S(C,st.x,st.y-st.H*.55);const out=u<p.t0?1-sm(p.t0-.25,p.t0,u):sm(p.t1,p.t1+.2,u);
        const hx=tip.x+out*140,hy=tip.y+out*700;hand(g,hx,hy,C.s*.9,-.18+(p.s.charCodeAt(0)%4-1.5)*.08,a)}
    }
    g.restore();
  },
  sound(ac,out,t0,X,K){
    const SN=K.SND;let v;try{v=CACHE.key===X.film.join(',')?CACHE.v:build({...X,DEEDS:window.DEEDS,CONSEQS:window.CONSEQS,MEMORIES:window.MEMORIES},K)}catch(e){return}
    const at=x=>t0+x,H=K.hash;
    const panW=(x,u)=>{const C=cam(u,v.dur);return cl(-1,1,W2S(C,x,0).x/960-1)};
    // the overhead camera: a shutter tick per captured frame, quiet, all the way through
    for(let i=0;i<Math.floor(v.dur*6);i++)SN.grain(ac,out,at(i/6+.02),{f:2400+H(i)*300,d:.008,a:.018,att:.05});
    // lift-off: the table opens around the card
    SN.cloud(ac,out,at(.1),.6,28,{bp:1400,q:.8,a:.035,d:[.04,.12],spread:.6},u=>Math.sin(Math.PI*u));
    for(const s of IDS){const p=v.pieces[s];
      // grip: a paper tick and the sack's own tick
      SN.grain(ac,out,at(p.t0),{bp:3800,q:2,d:.02,a:.12,pan:panW(p.from.x,p.t0),att:.05});SN.say(ac,out,s,at(p.t0+.02),'tick',.7,panW(p.from.x,p.t0));
      // slide across the table
      if(p.kind!=='by')SN.cloud(ac,out,at(p.t0+.05),p.t1-p.t0-.1,16,{bp:2600,q:1.2,a:.03,d:[.03,.09],spread:.5},u=>Math.sin(Math.PI*u));
      // turning the paper: a snap at the edge-on moment
      const fm=(p.f0+p.f1)/2;SN.grain(ac,out,at(fm),{bp:3000,q:1,d:.035,a:.16,pan:panW(p.to.x,fm),att:.1});SN.grain(ac,out,at(fm+.012),{f:180,d:.05,a:.07,pan:panW(p.to.x,fm)});
      // set down: the sack lands in its own voice; a body sinks
      const pan=panW(p.to.x,p.t1);if(!p.alive&&p.kind!=='stay'&&!p.ghost)SN.say(ac,out,s,at(p.t1-.05),'sink',.5,pan);else if(p.kind==='stay'||p.kind==='enter')SN.say(ac,out,s,at(p.t1),'land',.55,pan);else SN.say(ac,out,s,at(p.t1),'step',.8,pan);
      if(p.hes){const k1=p.t0+(p.t1-p.t0)*.38;SN.say(ac,out,s,at(k1+.05),'react',.6*p.hes,panW(p.to.x,k1));SN.say(ac,out,s,at(k1+.15),'breathe',.4,panW(p.to.x,k1))}
      if(p.tremble)SN.say(ac,out,s,at(p.t0+.3),'react',.45*p.tremble,panW(p.to.x,p.t0+.3));
    }
    // the descent onto the corner card: a soft rising hush
    SN.cloud(ac,out,at(2.45),.55,26,{bp:900,q:.7,a:.03,d:[.05,.14],spread:.4},u=>u*(1-u)*4);
  }
});
})();
