// TRANSITION 07 · Tying and Gagging (Sutherland vector display) -> Rape (occlusion candle room, drop curtain)
// SCION 13 · Nora Willett — Secondary Motion for Performed 2D Animation (2017).
// Primary-motion trajectories drive everything; secondary rig links follow through on inertial spring-dampers:
//  * THE WORLD: the outgoing phosphor screen is cut into 48 vertical ribbons hanging from the ceiling rail.
//    Each ribbon is hoisted (primary: a commanded length, left to right, from the door side) and its
//    actual length follows on a 2nd-order spring-damper (the hem lags the cord). Each ribbon also swings as a
//    variable-length pendulum (theta'' = -(g/l)theta - c theta' - 2(l'/l)theta' + F_draught/l): as it shortens
//    it whips. Behind the ribbons is the candle room; on the right the ribbons are drawn up behind the pelmet,
//    which drops in on its own spring and becomes the head of the drop curtain.
//  * THE CAST: each sack's base moves on a primary path (hops, door, ghost rise, memory stall); its body is cut
//    into horizontal bands whose lateral lag is a spring-damper driven by the base acceleration (material
//    presets per sack), with a vertical squash spring driven by the hops. Rope and gag ends are 4-link
//    pendulum chains (gravity + draught) with a collision mask against the sack's body. A band changes
//    material (vector -> candle-lit) when the hem of the ribbon behind it has passed above it.
// Invariants (numeric): at u=0 every ribbon has l=H, theta=0 and every sack has lag=0, so frame 0 is the
// outgoing composite; at u=DUR the ribbons are behind the pelmet / above the frame and every sack is at its
// incoming box with lag ~0 (asserted by the seam check).
(function(){
const W=1920,H=1080,DUR=3.0,T_OUT=5.99,T_IN=0.001,IDS=['R','B','I','O'];
const DT=1/240,NS=Math.ceil(DUR/DT)+2;
const NR=48,RW=W/NR,PEL={x:672,y:76};                 // pelmet of the candle room in screen space (x>=672, y<=76)
const DOORS={x0:72,x1:324,top:436,floor:868};          // doorway opening of the candle room in screen space
const FLOORI=868;
const MAT={ // material presets: lateral lag spring (w,z), squash spring (ws,zs), lag gain
 R:{w:8.5,z:.32,ws:16,zs:.35,gain:1.0},  // the shawl rocks after the stop
 B:{w:11,z:.55,ws:12,zs:.5,gain:.7},     // full to bursting: stiff, heavy, little lag, deep settle
 I:{w:4.6,z:.22,ws:10,zs:.28,gain:1.5},  // half empty: limp, trails a long way and wobbles
 O:{w:6.2,z:.3,ws:20,zs:.4,gain:1.25}};  // tall and narrow: the top and the wig whip
const mk=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c};
// ---------------- the film's own lever compositing, baked (same as film.html) ----------------
function leverBox(b,lv){const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;return{x:cx+(b.x-cx)*f,y:by+(b.y-by)*f,w:b.w*f,h:b.h*f}}
function leverize(c,b,lv){const f=1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink,cx=b.x+b.w/2,by=b.y+b.h;
 const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
 if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);
 const c2=mk(),q=c2.getContext('2d');q.filter=fl.join(' ')||'none';q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(c,0,0);return c2}
function layersOf(D,lt,e,st,K){const order=D.layers||['bg','V','A'];const mm=D.marks?D.marks(lt,e.A,e.V,K):null;const out={order,bg:mk(),A:mk(),V:mk(),box:{}};
 for(const ly of order){const q=out[ly].getContext('2d');q.save();try{D.draw(q,lt,e.A,e.V,K,{layer:ly,carry:st.body})}catch(err){}q.restore()}
 if(mm)for(const ly of['A','V']){const who=ly==='A'?e.A:e.V;out[ly]=leverize(out[ly],mm[ly],st.levers[who]);out.box[ly]=leverBox(mm[ly],st.levers[who])}
 return out}
function cropRect(b){const x0=Math.max(0,Math.floor(b.x-b.w*.45-40)),y0=Math.max(0,Math.floor(b.y-b.h*.55-60)),x1=Math.min(W,Math.ceil(b.x+b.w*1.45+40)),y1=Math.min(H,Math.ceil(b.y+b.h+70));return{x:x0,y:y0,w:Math.max(2,x1-x0),h:Math.max(2,y1-y0)}}
function crop(c,b){const r=cropRect(b),sp=document.createElement('canvas');sp.width=r.w;sp.height=r.h;sp.getContext('2d').drawImage(c,-r.x,-r.y);return{img:sp,r,b}}
function lift(Lr){const S={};const bgp=mk(),q=bgp.getContext('2d');q.drawImage(Lr.bg,0,0);
 for(const ly of Lr.order){if(ly==='bg')continue;const b=Lr.box[ly];if(!b){q.drawImage(Lr[ly],0,0);continue}const r=cropRect(b);
  const rest=mk(),rq=rest.getContext('2d');rq.drawImage(Lr[ly],0,0);rq.clearRect(r.x,r.y,r.w,r.h);q.drawImage(rest,0,0);S[ly]=crop(Lr[ly],b)}
 return{bg:bgp,S}}
function composite(Lr){const c=mk(),q=c.getContext('2d');q.fillStyle='#000';q.fillRect(0,0,W,H);for(const ly of Lr.order)q.drawImage(Lr[ly],0,0);return c}
// a sack's picture in one deed's language, whatever role it has there (used to convert a leaving sack)
function spriteIn(D,lt,s,st,K){const o=IDS.find(x=>x!==s);const c=mk(),q=c.getContext('2d');try{D.draw(q,lt,s,o,K,{layer:'A',carry:st.body})}catch(err){return null}
 const b=D.marks(lt,s,o,K).A;return crop(leverize(c,b,st.levers[s]),leverBox(b,st.levers[s]))}
// ---------------- primary motion: the ribbons ----------------
function ribbonPlan(i){const xc=(i+.5)*RW,right=xc>=PEL.x;
 const ts=.22+1.25*Math.pow(i/(NR-1),.9),td=.85;          // hoist front travels from the door (left) to the curtain (right)
 return{i,x:i*RW,xc,right,ts,td,lEnd:right?PEL.y-14:-40}}
function lCmd(R,u,K){return K.lerp(H,R.lEnd,K.sm(R.ts,R.ts+R.td,u))}
function draught(R,u){// the draught from the door: a gust front travelling right with the hoist, plus the push of the hoist itself
 const a=u-R.ts;const gust=a>-.1&&a<.9?Math.sin(Math.PI*(a+.1)/1)*1:0;return 620*gust*(.55+.45*Math.sin(R.i*1.7))}
function simRibbon(R,K){const L=new Float32Array(NS),T=new Float32Array(NS);let l=H,lv=0,th=0,tv=0;const w=13,z=.42,G=2600,C=.9;
 for(let n=0;n<NS;n++){const u=n*DT;L[n]=l;T[n]=th;
  const c=lCmd(R,u,K);const la=-w*w*(l-c)-2*z*w*lv;lv+=la*DT;l+=lv*DT;      // the hem follows the cord on a spring-damper
  const le=Math.max(60,l);const ta=-(G/le)*th-C*tv-2*(lv/le)*tv+draught(R,u)/le;tv+=ta*DT;th+=tv*DT;th=Math.max(-.35,Math.min(.35,th))}
 return{L,T}}
// ---------------- primary motion: the cast ----------------
function plan(X,K){const L=X.ledger,k=X.k,eo=L.ev[k-1],ei=L.ev[k],so=L.states[k-1],si=L.states[k];
 const DD=X.DEEDS||window.DEEDS;const Do=DD[eo.deed],Di=DD[ei.deed];
 const mo=Do.marks(T_OUT,eo.A,eo.V,K),mi=Di.marks(T_IN,ei.A,ei.V,K);
 const bo={},bi={},ro={},ri={};bo[eo.A]=leverBox(mo.A,so.levers[eo.A]);bo[eo.V]=leverBox(mo.V,so.levers[eo.V]);ro[eo.A]='A';ro[eo.V]='V';
 bi[ei.A]=leverBox(mi.A,si.levers[ei.A]);bi[ei.V]=leverBox(mi.V,si.levers[ei.V]);ri[ei.A]='A';ri[ei.V]='V';
 const mem=LEDGER.memories(L,ei.A,k).filter(m=>m.other===ei.V);const hes=mem.length?Math.min(1,mem[0].weight):0;
 const sacks=[];
 for(const s of IDS){const inO=s in bo,inI=s in bi;if(!inO&&!inI)continue;
  const lv=si.levers[s],tempo=K.cl(-1,1,lv.tempo||0),weight=K.cl(-1,1,lv.weight||0);
  const kind=inO&&inI?'staying':inO?'leaving':'entering';
  const sk={id:s,kind,ro:ro[s],ri:ri[s],dead:!si.alive[s],ghost:inI&&!si.alive[s],hes:s===ei.A?hes:0,weight,tempo,lv,tags:si.body[s]||[]};
  if(kind==='staying'){sk.b0=bo[s];sk.b1=bi[s];sk.t0=.45-.08*tempo;sk.t1=2.55-.12*tempo;if(sk.ghost)sk.bodyCopy=true}
  if(kind==='leaving'){sk.b0=bo[s];sk.t0=.25-.05*tempo;sk.t1=1.6-.08*tempo;
   if(sk.dead){sk.corpse=true}                                       // a dead sack is pressed into the floor where it lies
   else sk.doorOut=true}
  if(kind==='entering'){const b=bi[s];sk.b1=b;
   if(sk.ghost){sk.b0={x:b.x+b.w*.1,y:b.y+b.h-6,w:b.w*.8,h:6};sk.t0=1.0;sk.t1=2.6}         // a ghost rises out of the floorboards
   else{const sc=.82;sk.b0={x:(DOORS.x0+DOORS.x1)/2-b.w*sc/2,y:DOORS.floor-b.h*sc,w:b.w*sc,h:b.h*sc};sk.doorIn=true;sk.t0=.75-.1*tempo;sk.t1=2.62-.08*tempo}}
  sacks.push(sk)}
 // the doorway is one at a time: whoever comes in waits until the one going out has gone
 if(sacks.some(x=>x.kind==='leaving'&&!x.dead))for(const x of sacks)if(x.doorIn){x.t0=Math.max(x.t0,1.3);x.t1=Math.max(x.t1,2.8)}
 const others=IDS.filter(s=>!(s in bo)&&!(s in bi)&&!si.alive[s]);
 const ev=si.evidence.filter(x=>x.k<k);
 return{eo,ei,so,si,sacks,others,ev,hes,Do,Di}}
function hopsOf(sk){if(sk.ghost&&sk.kind==='entering')return 0;const a=sk.b0.x+sk.b0.w/2,b=sk.b1.x+sk.b1.w/2;const d=Math.abs(b-a)+Math.abs(sk.b1.y+sk.b1.h-sk.b0.y-sk.b0.h);
 if(d<12)return 0;return Math.max(1,Math.min(6,Math.round(d/(Math.max(sk.b0.w,sk.b1.w)*.9+70))))}
function progress(sk,u,K){let p=K.cl(0,1,(u-sk.t0)/(sk.t1-sk.t0));
 if(sk.hes>.3){const hold=.3*sk.hes;const q=p<.42?p/.42*.45:p<.42+hold?.45:.45+(p-.42-hold)/(.58-hold)*.55;p=K.cl(0,1,q)}
 return p}
// base (primary) of a sack at u: foot centre, size, hop lift
function base(sk,u,K){const p=progress(sk,u,K),n=sk.n;const e=n?K.sm(0,1,p):K.sm(0,1,p);
 const b0=sk.b0,b1=sk.b1,sz=K.sm(.1,.9,p);const w=K.lerp(b0.w,b1.w,sz),h=K.lerp(b0.h,b1.h,sz);
 // a sack hops: it only travels while it is in the air, so each take-off and landing is a jolt the body must follow
 const ex=n?(Math.min(n-1,Math.floor(e*n))+K.sm(.12,.88,e*n-Math.min(n-1,Math.floor(e*n))))/n:e;
 let x=K.lerp(b0.x+b0.w/2,b1.x+b1.w/2,ex),y=K.lerp(b0.y+b0.h,b1.y+b1.h,e),lift=0;
 if(sk.depth){const a=Math.sin(Math.PI*e);y-=sk.depth*34*a;sk._f=1-sk.depth*.08*a}else sk._f=1;
 if(n){const ph=(e*n)%1,env=K.sm(0,.03,e)*(1-K.sm(.97,1,e));lift=h*(.24-.1*sk.weight)*Math.sin(Math.PI*ph)*env}
 if(sk.hes>.3){// the memory stops it: it steps back from the one it is about to meet, then goes on
  const dir=Math.sign((sk.b1.x+sk.b1.w/2)-(sk.b0.x+sk.b0.w/2))||1;const hp=K.sm(.4,.47,p)*(1-K.sm(.45+.3*sk.hes,.55+.3*sk.hes,p));x-=dir*42*sk.hes*hp}
 return{x,y:y-lift,w:w*sk._f,h:h*sk._f,p,lift}}
// secondary motion of the cast: lateral lag q (top relative to base, px) and squash s, from the base acceleration
function simSack(sk,K){const M=MAT[sk.id],w=M.w,z=M.z*(1+.35*Math.max(0,sk.weight)),ws=M.ws,zs=M.zs;
 const Q=new Float32Array(NS),S=new Float32Array(NS);let q=0,qv=0,s=0,sv=0;
 const X=[],Y=[];for(let n=0;n<NS;n++){const b=base(sk,n*DT,K);X.push(b.x);Y.push(b.y)}
 for(let n=0;n<NS;n++){Q[n]=q;S[n]=s;const n0=Math.max(0,n-1),n1=Math.min(NS-1,n+1);
  const ax=(X[n1]-2*X[n]+X[n0])/(DT*DT)*(n0===n||n1===n?0:1),ay=(Y[n1]-2*Y[n]+Y[n0])/(DT*DT)*(n0===n||n1===n?0:1);
  const qa=-w*w*q-2*z*w*qv-ax*M.gain*1.5;qv+=qa*DT;q+=qv*DT;q=Math.max(-90,Math.min(90,q));
  const sa=-ws*ws*s-2*zs*ws*sv+ay/900;sv+=sa*DT;s+=sv*DT;s=Math.max(-.22,Math.min(.22,s))}
 return{Q,S}}
// rope and gag ends: 4-link chains hanging from knot points on the sack, gravity + draught, collision mask = body box
function simTails(sk,K,sim){const ends=[];const tg=sk.tags;
 if(tg.includes('rope')){ends.push({f:.3,side:1,len:46,col:'rope'});ends.push({f:.56,side:-1,len:38,col:'rope'})}
 if(tg.includes('gag')){ends.push({f:.86,side:1,len:34,col:'gag'});ends.push({f:.86,side:1,len:26,col:'gag',off:.5})}
 if(tg.includes('cinched'))ends.push({f:.8,side:-1,len:30,col:'cord'});
 if(!ends.length)return[];
 return ends.map((E,ei)=>{const NL=4,seg=E.len/NL;const out=[];
  const anchor=n=>{const u=n*DT,b=base(sk,u,K),q=sim.Q[n],s=sim.S[n];const hh=b.h*(1-s),ww=b.w*(1+s*.6);return[b.x+E.side*ww*.47+q*Math.pow(E.f,1.5),b.y-hh*E.f,b,ww,hh,q]};
  let a=anchor(0);const P=[],O=[];for(let j=0;j<=NL;j++){P.push([a[0]+E.side*j*1.5,a[1]+j*seg]);O.push([P[j][0],P[j][1]])}
  for(let n=0;n<NS;n++){a=anchor(n);const [ax,ay,b,ww,hh,q]=a;O[0]=P[0];P[0]=[ax,ay];
   const wind=-30*Math.sin(n*DT*6+ei*1.3);                       // the draught on a loose end
   for(let j=1;j<=NL;j++){const vx=(P[j][0]-O[j][0])*.994,vy=(P[j][1]-O[j][1])*.994;O[j]=[P[j][0],P[j][1]];P[j][0]+=vx+wind*DT*DT*60;P[j][1]+=vy+1400*DT*DT}
   for(let it=0;it<4;it++)for(let j=1;j<=NL;j++){const p0=P[j-1],p1=P[j],dx=p1[0]-p0[0],dy=p1[1]-p0[1],d=Math.hypot(dx,dy)||1,c=(d-seg)/d;
    if(j===1){p1[0]-=dx*c;p1[1]-=dy*c}else{p0[0]+=dx*c*.5;p0[1]+=dy*c*.5;p1[0]-=dx*c*.5;p1[1]-=dy*c*.5}
    // collision mask: the cord cannot pass into the sack's body, nor through the floor
    const fy=K.cl(0,1,(b.y-p1[1])/hh),edge=b.x+E.side*ww*.47+q*Math.pow(fy,1.5);if(E.side>0?p1[0]<edge:p1[0]>edge)p1[0]=edge;if(p1[1]>b.y-2)p1[1]=b.y-2}
   out.push(P.map(p=>[p[0],p[1]]))}
  return{E,frames:out}})}
// ---------------- build (cached per film) ----------------
let CACHE={key:'',P:null};
function build(X,K){const key=X.film.join(',')+'|'+X.k;if(CACHE.key===key)return CACHE.P;
 const P=plan(X,K);const Lo=layersOf(P.Do,T_OUT,P.eo,P.so,K),Li=layersOf(P.Di,T_IN,P.ei,P.si,K);
 P.fullO=composite(Lo);P.fullI=composite(Li);P.lo=lift(Lo);P.li=lift(Li);P.inBg=Li.bg;
 // the old picture the ribbons are cut from: outgoing room, plus any dead sack that stays in it
 const rib=mk(),rq=rib.getContext('2d');rq.drawImage(P.lo.bg,0,0);
 P.rib=rib;
 // pelmet sprite (incoming room) that drops in on a spring
 const pel=document.createElement('canvas');pel.width=W-PEL.x;pel.height=PEL.y+4;pel.getContext('2d').drawImage(Li.bg,-PEL.x,0);P.pel=pel;
 P.R=[];for(let i=0;i<NR;i++){const R=ribbonPlan(i);Object.assign(R,simRibbon(R,K));P.R.push(R)}
 // pelmet spring: commanded drop at .25..1.0, follows with overshoot
 {const Y=new Float32Array(NS);let y=-PEL.y-30,v=0;const w=11,z=.38;for(let n=0;n<NS;n++){Y[n]=y;const c=K.lerp(-PEL.y-30,0,K.sm(.25,.95,n*DT));const a=-w*w*(y-c)-2*z*w*v;v+=a*DT;y+=v*DT}P.pelY=Y}
 for(const sk of P.sacks){if(sk.kind!=='leaving')continue;sk.Si=spriteIn(P.Di,T_IN,sk.id,P.si,K);    // its candle-room self, for when the hem passes it
  if(sk.corpse){const c=sk.b0.x+sk.b0.w/2,bw=(sk.Si?sk.Si.b.w:sk.b0.w*.7)*1.12,bh=(sk.Si?sk.Si.b.h:sk.b0.h*.7)*.5;sk.b1={x:K.cl(380,1500,c)-bw/2,y:FLOORI+6-bh,w:bw,h:bh};sk.t0=.3;sk.t1=1.4;continue}
  const bw=sk.Si?sk.Si.b.w*.8:sk.b0.w*.55,bh=sk.Si?sk.Si.b.h*.8:sk.b0.h*.55;sk.b1={x:(DOORS.x0+DOORS.x1)/2-bw/2,y:DOORS.floor-bh,w:bw,h:bh}}
 // a ghost that acts again leaves its body behind on the floor
 P.corpses=[];for(const sk of P.sacks)if(sk.bodyCopy){const S=spriteIn(P.Di,T_IN,sk.id,P.si,K);if(S){const c=sk.b0.x+sk.b0.w/2;P.corpses.push({S,x:K.cl(380,1500,c),w:S.b.w*1.12,h:S.b.h*.5})}}
 // two sacks that cross each other's path pass at different depths (the one bound for the corner goes behind)
 {const tr=P.sacks.filter(s=>s.b1&&s.b0&&!s.corpse);for(let i=0;i<tr.length;i++)for(let j=i+1;j<tr.length;j++){const a=tr[i],b=tr[j];const c=x=>x.x+x.w/2;
  if(Math.sign(c(a.b0)-c(b.b0))!==Math.sign(c(a.b1)-c(b.b1))){const back=c(a.b1)>c(b.b1)?a:b,front=back===a?b:a;back.depth=1;front.depth=-1}}}
 for(const sk of P.sacks){sk.n=sk.corpse?0:hopsOf(sk);sk.sim=simSack(sk,K);sk.tails=simTails(sk,K,sk.sim);
  sk.So=sk.ro?P.lo.S[sk.ro]:null;sk.Si=sk.ri?P.li.S[sk.ri]:(sk.Si||null);
  if(sk.kind==='entering')sk.So=null}
 // the dead elsewhere in the house: their last picture, taken from the deed that killed them, drawn in the candle room
 P.bodies=P.others.map(s=>{const kd=P.si.deadAt[s];const e=X.ledger.ev[kd];if(!e)return null;const D=(X.DEEDS||window.DEEDS)[e.deed];if(!D||!D.marks)return null;
  const role=e.V===s?'V':'A';const c=mk(),q=c.getContext('2d');try{D.draw(q,5.99,e.A,e.V,K,{layer:role,carry:X.ledger.states[kd+1].body})}catch(err){return null}
  return crop(c,D.marks(5.99,e.A,e.V,K)[role])}).filter(Boolean);
 CACHE={key,P};return P}
const at=(A,u)=>{const f=K_cl(u/DT,0,NS-1.001),i=Math.floor(f),r=f-i;return A[i]*(1-r)+A[i+1]*r};
function K_cl(x,a,b){return Math.max(a,Math.min(b,x))}
function hemAt(P,x,u){const i=Math.max(0,Math.min(NR-1,Math.floor(x/RW)));return Math.max(0,at(P.R[i].L,u))}
// ---------------- draw helpers ----------------
function drawRibbon(g,P,R,u){const l=Math.max(0,at(R.L,u)),th=at(R.T,u);if(l<1)return;
 const M=12,src=P.rib;const sw=Math.sin(th);
 for(let j=0;j<M;j++){const s0=j/M*l,s1=(j+1)/M*l;const d0=l*sw*Math.pow(s0/l,1.6),d1=l*sw*Math.pow(s1/l,1.6);const sh=(d1-d0)/Math.max(.01,s1-s0);
  const sy=H-l+s0,sh_=s1-s0;if(sh_<=0)continue;
  g.setTransform(1,0,sh,1,d0-sh*s0,0);g.drawImage(src,R.x,sy,RW,Math.min(sh_+(j<M-1?.6:0),H-sy),R.x,s0,RW,Math.min(sh_+(j<M-1?.6:0),H-sy))}
 g.setTransform(1,0,0,1,0,0);
 if(l<H-1){const dh=l*sw;// the hem: a lit edge in the old language, and the shadow the ribbon throws into the new room
  const gr=g.createLinearGradient(0,l,0,l+26);gr.addColorStop(0,'rgba(0,0,0,.45)');gr.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=gr;g.fillRect(R.x+dh,l,RW,26);
  g.strokeStyle='rgba(169,242,210,.75)';g.lineWidth=2;g.beginPath();g.moveTo(R.x+dh,l-1);g.lineTo(R.x+dh+RW,l-1);g.stroke()}}
// one sack: banded sprite, each band lagging by the secondary field; band material switches where the hem has passed
function drawSack(g,P,sk,u,K){const b=base(sk,u,K),q=at(sk.sim.Q,u),s=at(sk.sim.S,u);const hh=b.h*(1-s),ww=b.w*(1+s*.6);
 const hem=hemAt(P,b.x,u);const NB=14;
 const door=sk.doorIn?1-K.sm(.0,.3,b.p):sk.doorOut?K.sm(.6,.95,b.p):0;
 const doorA=sk.doorOut?1-K.sm(.85,1,b.p):sk.doorIn?K.sm(0,.12,b.p):1;
 const ghostA=doorA*(sk.ghost?(sk.kind==='entering'?.15+.85*K.sm(.05,1,b.p):1-.45*Math.sin(Math.PI*b.p)):1)*(sk.corpse?1-K.sm(DUR-.5,DUR-.08,u):1);
 g.save();
 if(door>0){g.beginPath();g.rect(DOORS.x0,0,W-DOORS.x0,H);g.clip();if(door>.02)g.filter=`brightness(${1-.95*door})`}
 if(sk.corpse)g.filter=`grayscale(${K.sm(.2,.9,b.p)}) brightness(${1-.4*K.sm(.2,.9,b.p)})`;
 if(sk.ghost)g.filter=`drop-shadow(0 0 ${Math.round(16*(1-b.p)+2)}px rgba(190,255,210,.8))`;
 for(const which of['o','i']){const S=which==='o'?sk.So:sk.Si;if(!S)continue;const bx=S.b;
  const sx=ww/bx.w,sy=hh/bx.h;
  for(let j=0;j<NB;j++){// band j covers sprite rows (in sprite coords); f = height fraction of the band bottom
   const r0=S.r.y+S.r.h*j/NB,r1=S.r.y+S.r.h*(j+1)/NB;
   const f0=(bx.y+bx.h-r1)/bx.h,f1=(bx.y+bx.h-r0)/bx.h;const fm=(f0+f1)/2;
   const scrY=b.y-hh*fm;const isNew=!sk.So||(sk.Si&&scrY>hem);if((which==='i')!==isNew)continue;
   const o0=q*Math.pow(K.cl(0,1.3,f1),1.5),o1=q*Math.pow(K.cl(0,1.3,f0),1.5);
   const y0=b.y-hh*f1,y1=b.y-hh*f0;const shr=(o1-o0)/Math.max(.01,y1-y0);
   const x0=b.x+(S.r.x-(bx.x+bx.w/2))*sx;
   g.save();g.globalAlpha=ghostA;
   // map: dest x = X + shr*(Y - y0) + o0 ; implement with transform (1,0,shr,1, o0 - shr*y0, 0) on top of the position
   g.setTransform(1,0,shr,1,o0-shr*y0,0);
   g.drawImage(S.img,0,r0-S.r.y,S.img.width,Math.max(1,r1-r0+.6),x0,y0,S.img.width*sx,Math.max(1,y1-y0+.6*sy));
   g.restore()}}
 g.restore();
 // the cut line where the hem crosses the sack: a short phosphor stroke, the old language leaving it
 if(sk.So&&sk.Si&&hem<b.y&&hem>b.y-hh){g.save();g.strokeStyle='rgba(169,242,210,.8)';g.lineWidth=2;const o=q*Math.pow(K.cl(0,1,(b.y-hem)/hh),1.5);g.beginPath();g.moveTo(b.x-ww*.5+o,hem);g.lineTo(b.x+ww*.5+o,hem);g.stroke();g.restore()}
 // rope / gag / cord ends, in phosphor above the hem and in hemp below it
 const env=K.sm(.02,.16,b.p)*(1-K.sm(.86,.99,b.p));
 if(env>0)for(const T of sk.tails){const fr=T.frames[Math.max(0,Math.min(T.frames.length-1,Math.round(u/DT)))];
  const newMat=fr[0][1]>hem||!sk.So;const col=newMat?(T.E.col==='gag'?'#d9cbb0':T.E.col==='cord'?'#3a2c22':'#a8844f'):'#a9f2d2';
  g.save();g.globalAlpha=env*ghostA;g.strokeStyle=col;g.lineWidth=T.E.col==='gag'?6:4;g.lineCap='round';g.lineJoin='round';
  g.beginPath();g.moveTo(fr[0][0],fr[0][1]);for(let j=1;j<fr.length;j++)g.lineTo(fr[j][0],fr[j][1]);g.stroke();
  g.fillStyle=col;g.beginPath();g.arc(fr[0][0],fr[0][1],5,0,7);g.fill();g.restore()}
 return b}
function scan(g,a){if(a<=0)return;g.fillStyle=`rgba(120,220,150,${.06*a})`;for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2)}
TRANSITION({k:7,scion:13,lineage:'Nora Willett — Secondary Motion Swarm',
 op:'the outgoing vector screen is cut into hanging ribbons that are hoisted from the door side to the curtain side; each hem follows its cord on a spring-damper and swings as a shortening pendulum in the door draught, uncovering the candle room behind, while the pelmet drops in on its own spring; the sacks travel on primary hop paths and their bodies, rope ends and gags follow through on material-specific springs, each band turning candle-lit where the hem has passed',
 made:'The old room is 48 vertical ribbons cut from the phosphor screen picture, each a 12-segment strip with a lit hem; behind them is the candle room picture, with its pelmet as a separate piece. Each sack is its own lifted sprite in both languages, cut into 14 horizontal bands, plus rope, gag and cord ends as 4-link chains.',
 moved:'Primary trajectories (the hoist cords, the pelmet drop, the sacks\' hops, the door, a ghost rising, a memory\'s stall) are integrated once at 240 Hz into spring-damper and pendulum states: the hems lag and whip as they shorten, a sack\'s top lags its base and settles after it stops (Inigo limp and long, Belindo stiff, Ogiva\'s top whipping, Roessler rocking). Cord ends swing on gravity and the draught and are kept out of the body by a collision mask.',
 dur:DUR,
 draw(g,u,X,K){const P=build(X,K);
  const imO=X.ledger.states[X.k].impossible.find(q=>q.k===X.k-1),imI=X.ledger.states[X.k+1].impossible.find(q=>q.k===X.k);
  if(u<=.001){g.drawImage(P.fullO,0,0);scan(g,imO?1:0);return}
  if(u>=DUR-.02){g.drawImage(P.fullI,0,0);scan(g,imI?1:0);return}
  g.setTransform(1,0,0,1,0,0);g.drawImage(P.inBg,0,0);
  // the house remembers: what earlier deeds left lies on the floorboards once the old picture has gone off them
  const fade=1-K.sm(DUR-.5,DUR-.08,u);
  P.ev.forEach((ev,i)=>{const n=P.ev.length,x=360+(i+.5)/Math.max(1,n)*1120,bx={x:x-62,y:885+(i%2)*62,w:124,h:80};const CQ=X.CONSEQS[ev.deed];
   g.save();g.globalAlpha=fade*K.cl(0,1,(bx.y-hemAt(P,x,u))/40);try{if(CQ&&CQ.trace)CQ.trace(g,bx,X.k-1-ev.k,K);else{g.fillStyle='#fbf7ee';g.fillRect(bx.x+40,bx.y+40,40,10)}}catch(err){}g.restore()});
  // the dead elsewhere: still sacks laid against the dark corner, greyed
  P.bodies.forEach((B,i)=>{const sc=.72,bw=B.b.w*sc,bh=B.b.h*sc,x0=352+i*(bw+24),y1=FLOORI+6;const hm=hemAt(P,x0+bw/2,u);const a=fade*K.cl(0,1,(y1-bh-hm)/60);if(a<=0)return;
   g.save();g.globalAlpha=a;g.filter='grayscale(1) brightness(.62)';g.translate(x0-(B.b.x-B.r.x)*sc,y1-(B.b.y+B.b.h-B.r.y)*sc);g.scale(sc,sc);g.drawImage(B.img,0,0);g.restore()});
  // the entering are already in the candle room, behind the old picture
  for(const sk of P.sacks)if(sk.kind==='entering')drawSack(g,P,sk,u,K);
  for(const C of P.corpses){const y1=FLOORI+6,hm=hemAt(P,C.x,u);const a=fade*K.cl(0,1,(y1-C.h-hm)/60);if(a<=0)continue;const S=C.S,sx=C.w/S.b.w,sy=C.h/S.b.h;
   g.save();g.globalAlpha=a;g.filter='grayscale(1) brightness(.62)';g.translate(C.x-C.w/2-(S.b.x-S.r.x)*sx,y1-(S.b.y+S.b.h-S.r.y)*sy);g.scale(sx,sy);g.drawImage(S.img,0,0);g.restore()}
  // the old picture, in ribbons
  for(const R of P.R)drawRibbon(g,P,R,u);
  // the pelmet drops in and the right-hand ribbons go up behind it
  const py=at(P.pelY,u);if(py>-PEL.y-28)g.drawImage(P.pel,PEL.x,py);
  // the cast, in depth order: leaving, staying, entering; the incoming doer last
  const order=P.sacks.filter(s=>s.kind!=='entering').sort((a,b)=>(a.kind==='leaving'?0:a.kind==='staying'?1:2)-(b.kind==='leaving'?0:b.kind==='staying'?1:2)||(a.ri==='A')-(b.ri==='A'));
  for(const sk of order)drawSack(g,P,sk,u,K);
  scan(g,imO?1-K.sm(.3,2.2,u):0);scan(g,imI?K.sm(.3,2.2,u):0)},
 sound(ac,out0,t0,X,K){const out=ac.createGain();out.gain.value=1.6;out.connect(out0);const S=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1));const P=build(X,K);
  // the ribbons: a cord tick as each one is taken up (phosphor click), cloth hush while it rises, a soft flap where it whips
  for(let i=0;i<NR;i+=2){const R=ribbonPlan(i);S.grain(ac,out,t0+R.ts,{f:2600+i*18,d:.015,a:.13,pan:pan(R.xc),att:.05});
   S.grain(ac,out,t0+R.ts+.05,{bp:1400+i*40,q:1.2,d:.5,a:.08,pan:pan(R.xc),att:.6});
   if(i%6===0)S.grain(ac,out,t0+R.ts+R.td*.85,{bp:500,q:1,d:.09,a:.16,pan:pan(R.xc),att:.2})}
  // the pelmet lands on its rail: a wooden knock, then a small bounce
  S.thump(ac,out,t0+.72,.8,120,.4);S.grain(ac,out,t0+.9,{f:220,d:.05,a:.12,pan:.4,att:.1});
  // the candle room's time comes up under it: candle grains and the clock
  S.cloud(ac,out,t0+1.0,DUR-1.0,16,{bp:3200,q:2,a:.03,d:[.004,.012],spread:.1},u=>u);
  for(let c=1.4;c<DUR;c+=.5)S.grain(ac,out,t0+c,{f:1900,d:.012,a:.08,pan:-.2,att:.05});
  // the cast: steps at each landing, a door creak for entering/leaving, breath where the memory stops the doer
  for(const sk of P.sacks){if(sk.corpse){S.say(ac,out,sk.id,t0+.5,'sink',.8,pan(sk.b0.x));continue}
   const n=hopsOf(sk);const tt=p=>{for(let i=0;i<=240;i++){const u=sk.t0+(sk.t1-sk.t0+1)*i/240;if(progress(sk,u,K)>=p)return u}return sk.t1};
   const ix=sk.b0.x+sk.b0.w/2,fx=sk.b1.x+sk.b1.w/2;
   for(let h=1;h<=n;h++){const u=tt(h/n);S.say(ac,out,sk.id,t0+u,h===n?'land':'step',h===n?1.1:1.3,pan(K.lerp(ix,fx,h/n)))}
   if(sk.doorIn||sk.doorOut){const u=sk.doorIn?sk.t0:tt(.85);S.cloud(ac,out,t0+u,.45,50,{f:150,glide:-.2,a:.04,d:[.02,.06],noise:.5,type:'triangle',bp:900},v=>1-v)}
   if(sk.ghost)S.cloud(ac,out,t0+sk.t0,1.4,36,{f:440*Math.pow(2,(S.VOICE[sk.id].base+24-69)/12),a:.025,d:[.1,.25],glide:.05},v=>Math.sin(Math.PI*v));
   if(sk.hes>.3)S.say(ac,out,sk.id,t0+tt(.45)+.05,'breathe',.8,pan(ix))}
  if(P.sacks.some(s=>s.tags.includes('rope')||s.tags.includes('gag')))S.cloud(ac,out,t0+.6,1.6,14,{bp:2200,q:3,a:.03,d:[.02,.05]},v=>Math.sin(Math.PI*v))}
});
})();
