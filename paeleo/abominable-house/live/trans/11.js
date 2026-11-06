// TRANSITION 11 · Snooping (multiview cutaway with keyhole) -> Strangling (ARAP mesh sacks, the last deed before the fire)
// SCION 40 · Physical Tabletop Capture — Paper Performance (after Barnes et al., Video Puppetry, 2008).
// The join is a tabletop capture session seen through the overhead camera. The camera pulls up off the
// snooping picture: it was a print lying on a table. Hands (seen only as their shadows and the dashed
// hand matte the tracker excludes) pick the sacks up as paper cutouts, the snooping print is dragged off
// the table, and underneath lies the strangling print. Cutouts that stay in the film are flipped over in
// the hand (front = the snooping drawing, back = the strangling drawing); cutouts that leave are set down
// in the table margin; cutouts that enter are fetched from the margin. Then the camera lowers back onto the
// new print and the captured paper is replaced by the clean render (the hand matte and paper edge go).
// Typed state: cutout {id, kind, sprite front/back, rest pose (world bottom-centre), keys tp<tl<td<te};
// world = table coordinates, the print's pixel (0,0) is world (0,0); camera = {s, cx, cy}.
// Invariant (numeric): camera(0) and camera(DUR) are the identity (s=1, centre 960,540) and every cutout's
// rest pose on a print equals its deed's lever-scaled marks box, so both seams are the films' own frames.
(function(){
const W=1920,H=1080,DUR=3.4,T_OUT=5.99,T_IN=0.001,PAD=14;
const IDS=['R','B','I','O'];
const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w||W;c.height=h||H;return c};
let CACHE={key:'',P:null};
function leverBox(b,lv){const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}}
function lvFilter(lv){const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
 if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);return fl.join(' ')||'none'}
// the deed's layers, levers baked in exactly as the film composites them
function layersOf(D,lt,e,st,K){const order=D.layers||['bg','V','A'];const mm=D.marks?D.marks(lt,e.A,e.V,K):null;const out={order,bg:mk(),A:mk(),V:mk(),box:{}};
 for(const ly of order){const q=out[ly].getContext('2d');q.save();try{D.draw(q,lt,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}q.restore()}
 for(const ly of['A','V']){if(!mm)continue;const who=ly==='A'?e.A:e.V,lv=st.levers[who],b=mm[ly];const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;
  const c2=mk(),q=c2.getContext('2d');q.filter=lvFilter(lv);q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(out[ly],0,0);out[ly]=c2;out.box[ly]=leverBox(b,lv)}
 return out}
function composite(Lr){const c=mk(),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,W,H);for(const ly of Lr.order)q.drawImage(Lr[ly],0,0);return c}
function cropRect(b){const x0=Math.max(0,Math.floor(b.x-b.w*.45-40)),y0=Math.max(0,Math.floor(b.y-b.h*.6-60)),x1=Math.min(W,Math.ceil(b.x+b.w*1.45+40)),y1=Math.min(H,Math.ceil(b.y+b.h+40));return{x:x0,y:y0,w:Math.max(2,x1-x0),h:Math.max(2,y1-y0)}}
// a cutout: the sack's pixels, cut from the print with a paper margin; a blurred silhouette for its shadow
function cutout(src,r,b,grey){const w=r.w+PAD*2,h=r.h+PAD*2;const raw=mk(w,h),rq=raw.getContext('2d');rq.drawImage(src,r.x,r.y,r.w,r.h,PAD,PAD,r.w,r.h);
 // trim faint glow (halo/shadow filters) so the scissors follow the sack, not its light
 const sil=mk(w,h),sq=sil.getContext('2d');const id=rq.getImageData(0,0,w,h),d=id.data;for(let i=3;i<d.length;i+=4)d[i]=d[i]>110?255:0;sq.putImageData(id,0,0);
 const pap=mk(w,h),pq=pap.getContext('2d');for(let a=0;a<16;a++){const ang=a/16*Math.PI*2;pq.drawImage(sil,Math.cos(ang)*7,Math.sin(ang)*7)}pq.drawImage(sil,0,0);
 pq.globalCompositeOperation='source-in';pq.fillStyle='#f3eee2';pq.fillRect(0,0,w,h);pq.globalCompositeOperation='source-over';
 // a scissor edge: the margin's rim, slightly darker
 const img=mk(w,h),iq=img.getContext('2d');iq.drawImage(pap,0,0);iq.globalCompositeOperation='source-atop';iq.strokeStyle='rgba(120,105,80,.0)';iq.globalCompositeOperation='source-over';
 if(grey)iq.filter='grayscale(1) brightness(.62)';iq.drawImage(raw,0,0);iq.filter='none';
 // printed fiducial on the paper margin: two small squares at the base corners (what the tracker locks onto)
 const sh=mk(w+60,h+60),hq=sh.getContext('2d');hq.filter='blur(9px)';hq.drawImage(pap,30,30);hq.globalCompositeOperation='source-in';hq.fillStyle='#000';hq.fillRect(0,0,w+60,h+60);
 const hole=pap;
 return{img,sh,hole,w,h,ax:b.x+b.w/2-r.x+PAD,ay:b.y+b.h-r.y+PAD,bw:b.w,bh:b.h,r}}
function lift(Lr,grey){const S={};const bgp=mk(),q=bgp.getContext('2d');q.drawImage(Lr.bg,0,0);
 for(const ly of Lr.order){if(ly==='bg')continue;const b=Lr.box[ly];if(!b){q.drawImage(Lr[ly],0,0);continue}const r=cropRect(b);
  const rest=mk(),rq=rest.getContext('2d');rq.drawImage(Lr[ly],0,0);rq.clearRect(r.x,r.y,r.w,r.h);q.drawImage(rest,0,0);S[ly]=cutout(Lr[ly],r,b,grey&&grey[ly])}
 return{bg:bgp,S}}
// ---------------- the plan: pure function of the ledger ----------------
function plan(X,K){const L=X.ledger,k=X.k,eo=L.ev[k-1],ei=L.ev[k],so=L.states[k-1],si=L.states[k];
 const Do=X.DEEDS[eo.deed],Di=X.DEEDS[ei.deed];const mo=Do.marks(T_OUT,eo.A,eo.V,K),mi=Di.marks(T_IN,ei.A,ei.V,K);
 const bo={},bi={},ro={},ri={};bo[eo.A]=leverBox(mo.A,so.levers[eo.A]);bo[eo.V]=leverBox(mo.V,so.levers[eo.V]);ro[eo.A]='A';ro[eo.V]='V';
 bi[ei.A]=leverBox(mi.A,si.levers[ei.A]);bi[ei.V]=leverBox(mi.V,si.levers[ei.V]);ri[ei.A]='A';ri[ei.V]='V';
 const mem=LEDGER.memories(L,ei.A,k).filter(m=>m.other===ei.V);const hes=mem.length?Math.min(1,mem[0].weight):0;const memEv=hes>.3?L.ev[mem[0].k]:null;
 const sacks=[];let nOut=0,nIn=0,nLeave=0,nEnter=0;
 for(const s of IDS){const inO=s in bo,inI=s in bi;if(!inO&&!inI)continue;const kind=inO&&inI?'staying':inO?'leaving':'entering';
  const lv=si.levers[s],tempo=K.cl(-1,1,lv.tempo||0),weight=K.cl(-1,1,lv.weight||0);
  const sk={id:s,kind,ro:ro[s],ri:ri[s],dead:!si.alive[s],hes:s===ei.A&&hes>.3?hes:0,tempo,weight,lv};
  const bc=b=>[b.x+b.w/2,b.y+b.h];
  if(kind==='staying'){sk.p0=bc(bo[s]);sk.p1=bc(bi[s]);sk.r0=0;sk.r1=0;sk.tp=.5+nOut*.14-.04*tempo;sk.td=1.72+nIn*.16+.08*weight;nOut++;nIn++}
  if(kind==='leaving'){sk.p0=bc(bo[s]);sk.r0=0;
   if(sk.dead){sk.p1=[260+nLeave*420,1330+bo[s].w*.3];sk.r1=-Math.PI/2*.92}else{sk.p1=[-300-(nLeave%2)*40,560+nLeave*430];sk.r1=-.12+nLeave*.16}
   sk.tp=.5+nOut*.14-.04*tempo;sk.td=sk.tp+.62;nOut++;nLeave++}
  if(kind==='entering'){sk.p1=bc(bi[s]);sk.r1=0;sk.p0=[2260+(nEnter%2)*30,560+nEnter*440];sk.r0=.1-nEnter*.18;
   sk.tp=1.22+nEnter*.16-.04*tempo;sk.td=1.95+nEnter*.16+.08*weight;nIn++;nEnter++}
  sk.tl=sk.tp+.2;if(sk.hes)sk.td+=.5*sk.hes;sk.te=sk.td+.2;
  sacks.push(sk)}
 const others=IDS.filter(s=>!(s in bo)&&!(s in bi)&&!si.alive[s]);
 const ev=si.evidence.filter(x=>x.k<k);
 return{eo,ei,so,si,sacks,others,ev,hes,memEv,memAgo:mem.length?mem[0].ago:0}}
function build(X,K){const key=X.film.join(',')+'|'+X.k;if(CACHE.key===key)return CACHE.P;
 const P=plan(X,K);const Do=X.DEEDS[P.eo.deed],Di=X.DEEDS[P.ei.deed];
 const Lo=layersOf(Do,T_OUT,P.eo,P.so,K),Li=layersOf(Di,T_IN,P.ei,P.si,K);
 P.fullO=composite(Lo);P.fullI=composite(Li);
 const gO={},gI={};for(const sk of P.sacks){if(sk.ro&&sk.kind==='leaving'&&sk.dead)gO[sk.ro]=true}
 P.lo=lift(Lo,gO);P.li=lift(Li,gI);
 // ghosts: a dead sack that acts again is cut from tracing paper
 for(const sk of P.sacks){sk.front=sk.ro?P.lo.S[sk.ro]:null;sk.back=sk.ri?P.li.S[sk.ri]:null;sk.ghost=sk.dead&&!!sk.ri}
 // the dead elsewhere in the house: their last picture, cut out, laid down in the margin
 P.bodies=P.others.map(s=>{const kd=P.si.deadAt[s];const e=X.ledger.ev[kd];if(!e)return null;const D=X.DEEDS[e.deed];if(!D||!D.marks)return null;
  const role=e.V===s?'V':'A';const c=mk(),q=c.getContext('2d');try{D.draw(q,5.99,e.A,e.V,K,{layer:role,carry:X.ledger.states[kd].body})}catch(err){return null}
  const b=D.marks(5.99,e.A,e.V,K)[role];return{s,C:cutout(c,cropRect(b),b,true)}}).filter(Boolean);
 // the table: dark wood under one overhead lamp, the calibration fiducials at the print's corners
 const TX=-900,TY=-560,TW=W+1800,TH=H+1120;const tb=mk(TW,TH),tq=tb.getContext('2d');tq.fillStyle='#3b2a1d';tq.fillRect(0,0,TW,TH);
 for(let i=0;i<46;i++){const y=i/46*TH,a=.05+K.hash(i*3.7)*.09;tq.strokeStyle=K.hash(i)>.5?`rgba(20,12,6,${a})`:`rgba(120,86,52,${a})`;tq.lineWidth=2+K.hash(i*1.3)*7;tq.beginPath();tq.moveTo(0,y);
  for(let x=0;x<=TW;x+=120)tq.lineTo(x,y+Math.sin(x*.002+i)*14+K.hash(i*9+x)*5);tq.stroke()}
 for(let i=0;i<9;i++){tq.fillStyle='rgba(0,0,0,.35)';tq.fillRect(0,i*TH/9,TW,2)}  // plank joins
 const lg=tq.createRadialGradient(TW/2,TH/2,200,TW/2,TH/2,TW*.62);lg.addColorStop(0,'rgba(255,220,160,.16)');lg.addColorStop(1,'rgba(0,0,0,.6)');tq.fillStyle=lg;tq.fillRect(0,0,TW,TH);
 // paper offcuts on the table
 for(let i=0;i<7;i++){const x=K.hash(i*5.1)*TW,y=K.hash(i*2.3)*TH;if(x>820&&x<820+W+160&&y>480&&y<480+H+160)continue;tq.save();tq.translate(x,y);tq.rotate(K.hash(i*8)*3);tq.fillStyle='rgba(236,228,210,.5)';
  tq.beginPath();tq.moveTo(0,0);tq.lineTo(60+K.hash(i)*90,10);tq.lineTo(40,30+K.hash(i*4)*40);tq.closePath();tq.fill();tq.restore()}
 const fid=(x,y)=>{tq.fillStyle='#f4f1ea';tq.fillRect(x-34,y-34,68,68);tq.fillStyle='#111';tq.fillRect(x-28,y-28,56,56);tq.fillStyle='#f4f1ea';
  for(let j=0;j<9;j++)if(K.hash(x*.01+y*.03+j)>.45)tq.fillRect(x-20+(j%3)*14,y-20+Math.floor(j/3)*14,12,12)};
 fid(-TX-90,-TY-90);fid(-TX+W+90,-TY-90);fid(-TX-90,-TY+H+90);fid(-TX+W+90,-TY+H+90);
 P.table={img:tb,x:TX,y:TY};
 P.scratch=mk();
 CACHE={key,P};return P}
// ---------------- camera ----------------
function camera(u,K){const out=K.sm(.05,.8,u),inn=K.sm(2.5,3.25,u);const s=1-.44*out+.44*inn;const cy=540+70*out*(1-inn);return{s,cx:960,cy}}
function applyCam(g,c){g.translate(960,540);g.scale(c.s,c.s);g.translate(-c.cx,-c.cy)}
// ---------------- a cutout in the hand ----------------
function pose(sk,u,K){const a=K.sm(sk.tp,sk.tl,u),d=K.sm(sk.td,sk.te,u);const h=a*(1-d);
 let p=K.cl(0,1,(u-sk.tl)/(sk.td-sk.tl));
 if(sk.hes){// the doer's hand stops above the print: it remembers who lies there
  const hold=.45*sk.hes;p=p<.5?p/.5*.72:p<.5+hold?.72+.03*Math.sin((p-.5)/hold*Math.PI):.72+(p-.5-hold)/(.5-hold)*.28;p=K.cl(0,1,p)}
 const e=K.sm(0,1,p);let x=K.lerp(sk.p0[0],sk.p1[0],e),y=K.lerp(sk.p0[1],sk.p1[1],e)-Math.sin(Math.PI*e)*80;
 let tr=0;if(sk.hes){const hw=holdWin(sk),b=K.sm(hw[0],hw[0]+.2,u)*(1-K.sm(hw[1]-.15,hw[1],u));tr=Math.sin(u*55)*5*sk.hes*b;
  // it draws back from the one it remembers, toward where it came from
  const dx=sk.p1[0]-sk.p0[0],dy=sk.p1[1]-sk.p0[1],l=Math.hypot(dx,dy)||1;x-=dx/l*90*sk.hes*b;y-=dy/l*90*sk.hes*b-30*b}
 const rot=K.lerp(sk.r0,sk.r1,e)+h*.05*Math.sin(u*3+sk.id.charCodeAt(0));
 // the flip: front (outgoing drawing) turns over to its back (incoming drawing) mid-carry
 const f=sk.kind==='staying'?K.sm(.25,.75,p):sk.kind==='entering'?1:0;
 return{x:x+tr,y,rot,h,p,f}}
function holdWin(sk){const hold=.45*sk.hes;return[sk.tl+.5*(sk.td-sk.tl),sk.tl+(.5+hold)*(sk.td-sk.tl)]}
function drawCut(g,C,x,y,rot,h,sx,alpha,ghost){if(!C)return;g.save();g.translate(x,y);g.rotate(rot);
 const sc=1+.07*h;const ox=10+38*h,oy=14+52*h;
 g.save();g.globalAlpha=(.35+.25*(1-h))*alpha;g.scale(sx*sc,sc);g.drawImage(C.sh,-C.ax-30+ox/sc,-C.ay-30+oy/sc);g.restore();
 g.save();g.scale(sx*sc,sc);if(ghost){if(!C.gimg){C.gimg=mk(C.w,C.h);const q=C.gimg.getContext('2d');q.filter='grayscale(1) brightness(1.35)';q.drawImage(C.img,0,0)}g.globalAlpha=.42*alpha;g.drawImage(C.gimg,-C.ax,-C.ay);g.globalAlpha=.38*alpha;g.drawImage(C.hole,-C.ax,-C.ay)}
 else{g.globalAlpha=alpha;g.drawImage(C.img,-C.ax,-C.ay)}g.restore();
 // fiducials on the paper's foot, and the paper edge while it is edge-on
 if(Math.abs(sx)>.25){g.globalAlpha=alpha*(1-.4*h);g.scale(sx*sc,sc);for(const s of[-1,1]){const fx=s*(C.bw/2+4)-7,fy=-12;g.fillStyle='#111';g.fillRect(fx,fy,14,14);g.fillStyle='#f3eee2';g.fillRect(fx+4,fy+4,6,6)}}
 g.restore()}
// hand: only the shadow it casts and the matte the tracker cuts around it
// one outline (union traced by hand): forearm, palm, four fingers pinching toward the grip at (0,0), thumb
function handPath(g){g.beginPath();g.moveTo(-62,1400);g.lineTo(-58,250);g.quadraticCurveTo(-96,170,-112,96);g.quadraticCurveTo(-120,40,-92,10);g.quadraticCurveTo(-70,-4,-58,30);
 g.lineTo(-44,96);g.lineTo(-52,-30);g.quadraticCurveTo(-48,-56,-30,-56);g.quadraticCurveTo(-14,-56,-12,-30);g.lineTo(-10,-8);g.quadraticCurveTo(-4,-30,10,-30);
 g.quadraticCurveTo(26,-30,28,-6);g.lineTo(30,10);g.quadraticCurveTo(38,-8,52,-4);g.quadraticCurveTo(66,0,64,26);g.lineTo(60,60);g.quadraticCurveTo(72,52,82,62);g.quadraticCurveTo(92,74,84,100);
 g.lineTo(70,170);g.quadraticCurveTo(66,220,64,250);g.lineTo(70,1400);g.closePath()}
let HANDSH=null;const HS=1.7;
function handShadow(){if(HANDSH)return HANDSH;const c=mk(520,2700),q=c.getContext('2d');q.filter='blur(16px)';q.translate(260,180);q.scale(HS,HS);q.fillStyle='#050302';handPath(q);q.fill();HANDSH=c;return c}
function drawHand(g,x,y,ang,hh,a,K){if(a<=0)return;const dx=(x-960)*.05*hh+30*hh,dy=(y-540)*.05*hh+46*hh;
 g.save();g.globalAlpha=.55*a;g.translate(x+dx,y+dy);g.rotate(ang);g.scale(1+.12*hh,1+.12*hh);g.drawImage(handShadow(),-260,-180);g.restore();
 g.save();g.globalAlpha=.8*a;g.translate(x,y);g.rotate(ang);g.scale(HS,HS);g.setLineDash([12,10]);g.lineWidth=3.5/HS*1.6;g.strokeStyle='#a6efd9';handPath(g);g.stroke();g.restore()}
// a hand comes in from the nearest table edge, grips, carries, lets go and withdraws
function handFor(sk,u,P0,K){const a=K.sm(sk.tp-.32,sk.tp,u)*(1-K.sm(sk.te,sk.te+.32,u));if(a<=0)return null;
 const C=sk.kind==='entering'||(sk.kind==='staying'&&P0.f>.5)?sk.back:sk.front;if(!C)return null;
 const ang=P0.x<960?.45:-.45;const gx=P0.x-Math.sin(P0.rot)*C.bh*.6,gy=P0.y-Math.cos(P0.rot)*C.bh*.6;
 const far=1-a;return{x:gx-Math.sin(-ang)*1500*far*far,y:gy+Math.cos(ang)*1500*far*far,ang,hh:.5+.5*P0.h,a}}
// ---------------- draw ----------------
function scan(g,a){if(a<=0)return;g.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2)}
function sheetSlide(u,K){const e=K.sm(1.0,1.65,u);return{dx:-2900*e*e,dy:120*e,rot:-.16*e,e}}
TRANSITION({k:11,scion:40,lineage:'Physical Tabletop Capture — Paper Performance Swarm (after Video Puppetry)',
 op:'the overhead camera rises off the snooping print to show it lying on a table; hands (shadows and hand mattes only) lift the sacks as paper cutouts, drag the snooping print away to bare the strangling print beneath, flip the staying cutouts to their other side, park or fetch the others in the table margin, and the camera lowers onto the new print where the captured paper is replaced by the clean render',
 made:'A wooden capture table under one lamp with four calibration fiducials, two printed sheets (the snooping cutaway on top of the strangling room) and every sack as a double-sided paper cutout cut from the deeds\' own lever-baked layers, with a paper margin and two printed fiducials; the dead lie face up and grey in the margin, ghosts are cut from tracing paper, the house\'s evidence lies along the top edge.',
 moved:'Performers\' hands move everything: each cutout is lifted (its shadow spreads and drifts with height), carried on an arc and set down, staying sacks flipped over in the air while the snooping print is pulled out from under them; a strangler who remembers its victim stops its hand above the print and trembles before it puts itself down.',
 dur:DUR,
 draw(g,u,X,K){const P=build(X,K);
  const imO=X.ledger.states[X.k].impossible.find(q=>q.k===X.k-1),imI=X.ledger.states[X.k+1].impossible.find(q=>q.k===X.k);
  if(u<.05){g.drawImage(P.fullO,0,0);scan(g,imO?1:0);return}
  if(u>=DUR-.04){g.drawImage(P.fullI,0,0);scan(g,imI?1:0);return}
  const c=camera(u,K),sl=sheetSlide(u,K);
  g.fillStyle='#120c08';g.fillRect(0,0,W,H);g.save();applyCam(g,c);
  g.drawImage(P.table.img,P.table.x,P.table.y);
  // the strangling print, under everything; a white paper border round it
  g.fillStyle='rgba(0,0,0,.45)';g.fillRect(-14,-6,W+40,H+40);g.fillStyle='#ece6d8';g.fillRect(-22,-22,W+44,H+44);g.drawImage(P.li.bg,0,0);
  // evidence of the house along the table's top edge; the dead laid in the bottom margin
  const env=K.sm(.35,.9,u)*(1-K.sm(2.6,3.1,u));
  P.ev.forEach((ev,i)=>{const n=P.ev.length,x=-240+(i+.5)/Math.max(1,n)*(W+480),bx={x:x-95,y:-300+(i%2)*40,w:190,h:150};const CQ=X.CONSEQS[ev.deed];
   g.save();g.fillStyle=`rgba(236,230,214,${.9*env})`;g.translate(x,bx.y+bx.h/2);g.rotate((K.hash(i*4.1)-.5)*.3);g.fillRect(-bx.w/2-10,-bx.h/2-10,bx.w+20,bx.h+20);g.restore();
   g.save();g.globalAlpha=env;try{if(CQ&&CQ.trace)CQ.trace(g,bx,X.k-1-ev.k,K);else{g.fillStyle='#555';g.fillRect(bx.x+70,bx.y+60,50,20)}}catch(err){}g.restore()});
  P.bodies.forEach((B,i)=>{drawCut(g,B.C,1500+i*380,1330+B.C.bw*.3,-Math.PI/2*.9,0,1,env,false)});
  // the snooping print: holes where cutouts were lifted out of it, then dragged off the table
  if(sl.e<1){const sq=P.scratch.getContext('2d');sq.setTransform(1,0,0,1,0,0);sq.globalCompositeOperation='source-over';sq.clearRect(0,0,W,H);sq.drawImage(P.lo.bg,0,0);
   sq.globalCompositeOperation='destination-out';for(const sk of P.sacks){if(!sk.front||u<sk.tp+.04)continue;const C=sk.front;sq.drawImage(C.hole,C.r.x-PAD,C.r.y-PAD)}
   sq.globalCompositeOperation='source-over';
   for(const sk of P.sacks){if(!sk.front||u>=sk.tp+.04)continue;sq.drawImage(sk.front.img,sk.front.r.x-PAD,sk.front.r.y-PAD)} // still lying in the print
   g.save();g.translate(sl.dx,sl.dy);g.translate(0,H/2);g.rotate(sl.rot);g.translate(0,-H/2);
   const ring=(ox,oy,c)=>{g.beginPath();g.rect(-22+ox,-22+oy,W+44,H+44);g.rect(ox,oy,W,H);g.fillStyle=c;g.fill('evenodd')};
   ring(18,28,'rgba(0,0,0,.45)');ring(0,0,'#ece6d8');g.drawImage(P.scratch,0,0);g.restore();
   // the hand that pulls the print
   const ha=K.sm(.7,1.0,u)*(1-K.sm(1.55,1.8,u));drawHand(g,-40+sl.dx,560+sl.dy,1.35,.35,ha,K)}
  // the strangler's memory: an old print of what passed between them slides out from under the new one
  const hz=P.sacks.find(q=>q.hes);if(hz&&P.memEv&&X.still){const hw=holdWin(hz),ma=K.sm(hw[0]-.1,hw[0]+.15,u)*(1-K.sm(hw[1]-.05,hw[1]+.25,u));
   if(ma>0){const im=X.still(P.memEv);const sc=.25,mw=W*sc,mh=H*sc,mx=K.cl(80,W-mw-80,hz.p1[0]-mw/2),my=1105+(1-ma)*-60;
    g.save();g.globalAlpha=ma;g.translate(mx+mw/2,my+mh/2);g.rotate(-.05);g.fillStyle='rgba(0,0,0,.5)';g.fillRect(-mw/2-4,-mh/2+8,mw+22,mh+22);g.fillStyle='#e9e1cf';g.fillRect(-mw/2-12,-mh/2-12,mw+24,mh+24);
    g.filter=`sepia(.6) brightness(${.95-.05*Math.min(6,P.memAgo)})`;g.drawImage(im,-mw/2,-mh/2,mw,mh);g.restore()}}
  // the cutouts not yet picked lying in the margin (entering), then every cutout in its pose
  const hands=[];
  const order=P.sacks.slice().sort((a,b)=>(pose(a,u,K).h-pose(b,u,K).h));
  for(const sk of order){if(sk.kind!=='entering'&&u<sk.tp+.04)continue;const Q=pose(sk,u,K);
   const sx=sk.kind==='staying'?Math.cos(Math.PI*Q.f):1;const C=sk.kind==='staying'?(Q.f<.5?sk.front:sk.back):sk.kind==='entering'?sk.back:sk.front;
   const gh=sk.ghost&&(sk.kind==='entering'||Q.f>=.5);
   // ending: on the new print the paper edge and the fiducials dissolve into the clean render
   drawCut(g,C,Q.x,Q.y,Q.rot,Q.h,Math.abs(sx)<.04?.04:sx,1,gh);
   const hd=handFor(sk,u,Q,K);if(hd)hands.push(hd)}
  for(const hd of hands)drawHand(g,hd.x,hd.y,hd.ang,hd.hh,hd.a,K);
  g.restore();
  // the capture becomes the render: clean frame laid over as the camera settles
  const cl=K.sm(2.95,DUR-.06,u);if(cl>0){g.save();g.globalAlpha=cl;g.drawImage(P.fullI,0,0);g.restore()}
  scan(g,imO?1-K.sm(.4,1.6,u):0);scan(g,imI?K.sm(1.6,3,u):0)},
 sound(ac,out0,t0,X,K){const out=ac.createGain();out.gain.value=3.2;out.connect(out0);const P=plan(X,K),S=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1));
  // the camera rising: a soft motor of breath grains
  S.cloud(ac,out,t0+.05,.8,40,{bp:300,q:2,a:.03,d:[.05,.12]},u=>Math.sin(Math.PI*u));
  // the print dragged across the wood: a long paper hush
  S.cloud(ac,out,t0+1.0,.7,120,{bp:2600,q:.9,a:.045,d:[.02,.06],spread:.6},u=>Math.sin(Math.PI*u)*(1-.5*u));
  S.grain(ac,out,t0+1.0,{bp:4200,d:.05,a:.12,pan:-.8,att:.1});
  for(const sk of P.sacks){const px=sk.p0[0],qx=sk.p1[0];
   // pick: paper lifted off paper (a dry snap), the fiducial lock tick
   S.grain(ac,out,t0+sk.tp+.04,{bp:5200,q:2,d:.03,a:.14,pan:pan(px),att:.05});S.grain(ac,out,t0+sk.tp+.12,{f:2900,d:.015,a:.05,pan:pan(px),att:.05});
   S.say(ac,out,sk.id,t0+sk.tp+.06,'tick',.6,pan(px));
   if(sk.kind==='staying')S.cloud(ac,out,t0+K.lerp(sk.tl,sk.td,.4),.25,60,{bp:3200,a:.05,d:[.01,.04]},u=>Math.sin(Math.PI*u)); // the flip
   if(sk.hes)S.say(ac,out,sk.id,t0+K.lerp(sk.tl,sk.td,.55),'breathe',1,pan(qx));
   // set down: paper on paper or wood, and the sack's own landing
   S.grain(ac,out,t0+sk.td+.17,{bp:1800,q:1.2,d:.05,a:.16,pan:pan(qx),att:.08});
   S.say(ac,out,sk.id,t0+sk.td+.18,sk.kind==='leaving'?'step':'land',sk.kind==='leaving'?.6:.55,pan(qx));
   if(sk.dead&&sk.kind==='leaving')S.say(ac,out,sk.id,t0+sk.td+.3,'sink',.7,pan(qx));
   if(sk.ghost)S.cloud(ac,out,t0+sk.tp,1.2,30,{f:440*Math.pow(2,(S.VOICE[sk.id].base+24-69)/12),a:.025,d:[.1,.25],glide:.05},u=>Math.sin(Math.PI*u))}
  P.ev.forEach((ev,i)=>S.grain(ac,out,t0+.5+i*.07,{bp:2000+i*150,d:.03,a:.035,pan:pan(-240+(i+.5)/Math.max(1,P.ev.length)*2400),att:.1}));
  // the camera lowering onto the strangling print
  S.cloud(ac,out,t0+2.5,.75,40,{bp:240,q:2,a:.03,d:[.05,.12]},u=>Math.sin(Math.PI*u))}
});
})();
