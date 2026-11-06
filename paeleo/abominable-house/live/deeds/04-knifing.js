// 04 · KNIFING — SCION 7 · Peter Foldès, Drawn Metamorphosis
// Every sack is a hand-authored KEY CONTOUR (point list) split by five landmarks
// L0 bottom-centre, L1 bottom-right, L2 right ear tip, L3 left ear tip, L4 bottom-left.
// Each landmark segment is resampled to a fixed count, so point i of any key
// corresponds to point i of every other key (the correspondence map). All motion is
// computed in-betweening between keys: idle -> blade (doer), idle -> empty (victim),
// wig -> fallen wig, mound small -> mound full. Invariant: landmark indices are fixed
// (OFF[k]) for every key, so no in-between can flip topology between landmarks.
(function(){
const SEGN=[8,22,30,22,8], OFF=[0,8,30,60,82], NP=90;
const FLOOR=930, VX=1330, S=2.3, C=2.6, Q=S/1.6;
const INK='#17130f', STEEL='#e4e8ee', FLOUR='#fbf7ee';

// ---------- key drawings (normalised: x in widths from centre, y in heights from floor)
const KEYS={
 R:{ // wide, low, oldest: bottom bulges, low blunt ears
  idle:[[[0,0],[0.3,0],[0.49,0.02]],
        [[0.49,0.02],[0.56,0.22],[0.55,0.55],[0.5,0.84],[0.55,0.98]],
        [[0.55,0.98],[0.36,0.92],[0,0.95],[-0.36,0.92],[-0.55,0.98]],
        [[-0.55,0.98],[-0.5,0.84],[-0.55,0.55],[-0.56,0.22],[-0.49,0.02]],
        [[-0.49,0.02],[-0.3,0],[0,0]]],
  empty:[[[0,0],[0.4,0],[0.66,0.01]],
        [[0.66,0.01],[0.7,0.1],[0.64,0.24],[0.82,0.26]],
        [[0.82,0.26],[0.5,0.34],[0.15,0.3],[-0.2,0.36],[-0.5,0.32],[-0.84,0.25]],
        [[-0.84,0.25],[-0.64,0.22],[-0.7,0.1],[-0.66,0.01]],
        [[-0.66,0.01],[-0.3,0],[0,0]]]},
 B:{ // full to bursting: round belly, domed top
  idle:[[[0,0],[0.3,0],[0.48,0.02]],
        [[0.48,0.02],[0.55,0.2],[0.58,0.48],[0.53,0.8],[0.5,0.93],[0.55,1.03]],
        [[0.55,1.03],[0.38,0.99],[0,1.02],[-0.38,0.99],[-0.55,1.03]],
        [[-0.55,1.03],[-0.5,0.93],[-0.53,0.8],[-0.58,0.48],[-0.55,0.2],[-0.48,0.02]],
        [[-0.48,0.02],[-0.3,0],[0,0]]],
  empty:[[[0,0],[0.4,0],[0.62,0.01]],
        [[0.62,0.01],[0.68,0.12],[0.6,0.26],[0.7,0.34]],
        [[0.7,0.34],[0.45,0.33],[0.28,0.4],[0.06,0.35],[-0.14,0.41],[-0.36,0.35],[-0.68,0.4]],
        [[-0.68,0.4],[-0.6,0.28],[-0.68,0.12],[-0.62,0.01]],
        [[-0.62,0.01],[-0.3,0],[0,0]]]},
 I:{ // half empty: sunken top, both ears hang beside him like hair
  idle:[[[0,0],[0.3,0],[0.49,0.02]],
        [[0.49,0.02],[0.53,0.22],[0.55,0.4],[0.62,0.36]],
        [[0.62,0.36],[0.63,0.62],[0.53,0.9],[0.3,0.82],[0,0.76],[-0.3,0.82],[-0.53,0.9],[-0.63,0.62],[-0.62,0.36]],
        [[-0.62,0.36],[-0.55,0.4],[-0.53,0.22],[-0.49,0.02]],
        [[-0.49,0.02],[-0.3,0],[0,0]]],
  empty:[[[0,0],[0.4,0],[0.66,0.01]],
        [[0.66,0.01],[0.7,0.07],[1.0,0.03]],
        [[1.0,0.03],[0.92,0.1],[0.55,0.15],[0,0.12],[-0.55,0.15],[-0.92,0.1],[-1.0,0.03]],
        [[-1.0,0.03],[-0.7,0.07],[-0.66,0.01]],
        [[-0.66,0.01],[-0.3,0],[0,0]]]},
 O:{ // tall, narrow, straight; crisp small ears
  idle:[[[0,0],[0.3,0],[0.48,0.01]],
        [[0.48,0.01],[0.52,0.4],[0.51,0.8],[0.49,0.94],[0.56,1.02]],
        [[0.56,1.02],[0.3,0.97],[0,0.99],[-0.3,0.97],[-0.56,1.02]],
        [[-0.56,1.02],[-0.49,0.94],[-0.51,0.8],[-0.52,0.4],[-0.48,0.01]],
        [[-0.48,0.01],[-0.3,0],[0,0]]],
  empty:[[[0,0],[0.4,0],[0.56,0.01]],    // buckled: the top half folds over away from the cut
        [[0.56,0.01],[0.62,0.2],[0.64,0.4],[1.0,0.36],[1.45,0.2],[1.7,0.12]],
        [[1.7,0.12],[1.78,0.2],[1.66,0.3]],
        [[1.66,0.3],[1.2,0.42],[0.7,0.52],[0.2,0.5],[-0.5,0.42],[-0.6,0.2],[-0.52,0.01]],
        [[-0.52,0.01],[-0.3,0],[0,0]]]}
};
// blade key profiles: (u along root->tip, v across in blade widths). edge path ends at tip (1,0); spine starts at tip
const BLADES={
 paring:{W:19,edge:[[0.14,0.55],[0.2,0.85],[0.26,0.6],[0.7,0.55],[0.93,0.2],[1,0]],spine:[[1,0],[0.8,-0.3],[0.26,-0.45],[0.2,-0.8],[0.14,-0.55]]},
 cleaver:{W:34,edge:[[0.18,0.4],[0.26,0.45],[0.3,1.25],[0.9,1.35],[0.99,1.2],[1,0]],spine:[[1,0],[0.98,-0.35],[0.3,-0.35],[0.26,-0.45],[0.18,-0.4]]},
 ear:{W:22,edge:[[0.2,0.55],[0.45,0.42],[0.7,0.32],[0.9,0.18],[1,0]],spine:[[1,0],[0.86,-0.12],[0.6,-0.2],[0.4,-0.3],[0.2,-0.55]]},
 stiletto:{W:9,edge:[[0.1,0.6],[0.13,0.6],[0.14,1.9],[0.19,1.9],[0.2,0.5],[1,0]],spine:[[1,0],[0.2,-0.5],[0.19,-1.9],[0.14,-1.9],[0.13,-0.6],[0.1,-0.6]]}
};
// pile mound key (normalised: x in pile widths, y in pile heights)
const MOUND=[[-0.5,0],[-0.38,0.18],[-0.22,0.55],[-0.08,0.92],[0.04,1],[0.18,0.7],[0.3,0.45],[0.42,0.2],[0.5,0]];
const MOUND0=[[-0.5,0],[-0.3,0.4],[0,0.9],[0.3,0.4],[0.5,0]];

// ---------- correspondence: resample each landmark segment to its fixed count
function resample(pl,n,keepEnd){
 const L=[0];for(let i=1;i<pl.length;i++)L.push(L[i-1]+Math.hypot(pl[i][0]-pl[i-1][0],pl[i][1]-pl[i-1][1]));
 const tot=L[L.length-1]||1e-6,out=[],den=keepEnd?n-1:n;let j=0;
 for(let k=0;k<n;k++){const s=tot*k/den;while(j<pl.length-2&&L[j+1]<s)j++;const a=(s-L[j])/((L[j+1]-L[j])||1e-6);
  out.push([pl[j][0]+(pl[j+1][0]-pl[j][0])*a,pl[j][1]+(pl[j+1][1]-pl[j][1])*a]);}
 return out}
function contour(segs){let o=[];segs.forEach((s,i)=>{o=o.concat(resample(s,SEGN[i],false))});return o}
const RES={};for(const id in KEYS)RES[id]={idle:contour(KEYS[id].idle),empty:contour(KEYS[id].empty)};
const ix=(seg,f)=>OFF[seg]+Math.round(f*(SEGN[seg]-1));
// carried damage enters as a modified base key drawing (contour edits), and as marks anchored to contour indices
let CAR={};const MEMO={};
const has=(id,tag)=>!!(CAR[id]&&CAR[id].indexOf(tag)>=0);
const ew=i=>Math.exp(-Math.pow((i-OFF[2])/4,2))+Math.exp(-Math.pow((i-OFF[3])/4,2));
function base(id){const tg=(CAR[id]||[]).slice().sort().join(',');const k=id+'|'+tg;if(MEMO[k])return MEMO[k];
 const e=has(id,'emptied')?0.3:0,dr=has(id,'drowsy'),ci=has(id,'cinched'),Iq=RES[id].idle,E=RES[id].empty;
 return MEMO[k]=Iq.map((p,i)=>{let q=[p[0]+(E[i][0]-p[0])*e,p[1]+(E[i][1]-p[1])*e];
  if(dr)q[1]-=0.08*ew(i);
  if(ci){const nk=Math.exp(-Math.pow((i-ix(1,0.84))/2.5,2))+Math.exp(-Math.pow((i-ix(3,0.16))/2.5,2));q[0]*=1-0.2*nk}
  return q})}
const lerpP=(a,b,u)=>[a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u];

// ---------- key timing helper: piecewise eased path through [time,value] keys
function track(t,keys,sm){if(t<=keys[0][0])return keys[0][1];for(let i=0;i<keys.length-1;i++){const[a,pa]=keys[i],[b,pb]=keys[i+1];
 if(t<=b){const u=sm(a,b,t);return Array.isArray(pa)?lerpP(pa,pb,u):pa+(pb-pa)*u}}return keys[keys.length-1][1]}

// ---------- victim
const VS={
 R:{Td:1.8,cap:1.0,fl:0.6},B:{Td:2.4,cap:1.15,fl:0.5},I:{Td:1.0,cap:0.42,fl:0},O:{Td:1.5,cap:0.9,fl:1}};
function slitDef(A,V,K){const vh=K.CAST[V].h;let v;
 if(A==='R'){v=K.cl(0.2,0.78,K.CAST.R.h*0.5/vh);return[[-0.5,v],[0.12,v+0.02]]}
 if(A==='B')return[[-0.46,0.86],[0.16,0.3]];
 if(A==='I'){v=K.cl(0.22,0.7,K.CAST.I.h*0.55/vh);return[[-0.5,v-0.03],[-0.12,v+0.09]]}
 v=K.cl(0.28,0.7,K.CAST.O.h*0.58/vh);return[[-0.5,v],[0.32,v]]}
function victim(t,A,V,K){
 const cs=K.CAST[V],P=VS[V],w=cs.w*S,h=cs.h*S;
 const dq=u=>1-(1-u)*(1-u);const d=dq(K.cl(0,1,(t-C-0.06)/P.Td));const capC=has(V,'emptied')?0.6:1;                     // flour drained 0..1
 const s=K.sm(C+0.15,C+P.Td+0.35,t);                 // slump in-between idle->empty
 const hit=K.sm(C-0.02,C+0.08,t)*(1-K.sm(C+0.25,C+1.1,t));
 let shear=0,sy=1,ear=0,x=VX;
 if(V==='R'){sy=1-0.07*hit;ear=-0.05*hit;shear=0.03*hit+0.025*Math.sin((t-C)*5)*K.sm(C+0.8,C+1.2,t)*(1-K.sm(C+1.6,C+2.6,t))}
 if(V==='B'){const hb=K.sm(C+0.1,C+0.5,t)*(1-K.sm(C+0.8,C+1.8,t));shear=0.06*hb;ear=0.05*hb}
 if(V==='I'){shear=-0.14*K.sm(C+0.25,C+0.6,t)*(1-K.sm(C+0.7,C+1.2,t))}   // late, careless look down at the cut
 if(V==='O'){sy=1+0.05*hit;ear=0.16*hit;shear=0.05*hit;x+=6*hit}
 shear-=0.05*d*(1-s);
 const loc=[];const I=base(V),E=RES[V].empty;
 for(let i=0;i<NP;i++){const p=lerpP(I[i],E[i],s);
  const wE=Math.exp(-Math.pow((i-OFF[2])/4,2))+Math.exp(-Math.pow((i-OFF[3])/4,2));p[1]+=ear*wE;loc.push(p)}
 const pts=loc.map(p=>[x+(p[0]+shear*p[1])*w,FLOOR-p[1]*h*sy]);
 const BL=pts[OFF[4]],BR=pts[OFF[1]],TR=pts[ix(2,0.2)],TL=pts[ix(2,0.8)];
 const map=(u,v)=>{const a=u+0.5;return lerpP(lerpP(BL,BR,a),lerpP(TL,TR,a),v)};
 const sd=slitDef(A,V,K);
 return{capC,pts,loc,map,S0:map(...sd[0]),S1:map(...sd[1]),d,s,w,h,x,P,V,sd,hit,
  rate:(dq(K.cl(0,1,(t+0.03-C-0.06)/P.Td))-d)/0.03*P.Td/2}}

// ---------- doer
function doerPlan(t,A,V,K,root,vs,strikeX){
 const sm=K.sm,S0=vs.S0,S1=vs.S1,R=(dx,dy)=>[root[0]+dx*Q,root[1]+dy*Q];let x,shear=0,sy=1,m,tip,bend=0,ear=0,cut,trailOn;
 const start=A==='B'?440:A==='O'?470:430;
 if(A==='R'){ // three deliberate hitches, rocking; a short paring blade; saws twice
  const u=K.cl(0,1,(t-0.4)/1.5)*3,k=Math.min(2,Math.floor(u));const st=u>=3?1:(k+sm(0,1,u-k))/3;
  x=K.lerp(start,strikeX,st)-20*sm(3.4,4.2,t);
  shear=0.06*Math.sin((t-0.4)*Math.PI*2)*(t>0.4&&t<1.9?1:0)+0.08*sm(3.6,4.3,t)+0.015*Math.sin(t*4)*sm(4,4.6,t);
  sy=1-0.03*Math.abs(Math.sin((t-0.4)*Math.PI*2))*(t>0.4&&t<1.9?1:0);
  m=sm(1.7,2.3,t)*(1-sm(3.25,3.85,t));
  tip=track(t,[[0,R(40,20)],[2.25,R(70,25)],[2.6,S0],[2.78,S1],[2.92,lerpP(S0,S1,0.5)],[3.08,S1],[3.35,R(70,20)]],sm);
  cut=sm(2.6,2.78,t);trailOn=[2.55,3.15]}
 else if(A==='B'){ // heavy steps, a hesitation, rears up, his shoulder becomes a cleaver, chops from above
  x=K.lerp(start,strikeX,sm(0.4,1.6,t))-30*sm(3.4,4.4,t);
  const walk=t>0.4&&t<1.6;sy=1-(walk?0.045*Math.abs(Math.sin((t-0.4)*Math.PI*2.5)):0);
  shear=-0.06*sm(1.6,1.85,t)*(1-sm(2.0,2.3,t))+0.05*sm(2.45,2.65,t)*(1-sm(3.0,3.6,t))-0.03*sm(3.8,4.6,t);
  sy*=1+0.12*sm(2.0,2.35,t)*(1-sm(2.5,2.7,t))-0.05*sm(2.55,2.7,t)*(1-sm(2.9,3.3,t))-0.04*sm(3.8,4.6,t);
  ear=-0.08*sm(1.6,1.85,t)*(1-sm(2.0,2.2,t))-0.1*sm(3.8,4.6,t);
  m=sm(1.95,2.35,t)*(1-sm(3.2,3.9,t));
  tip=track(t,[[0,R(-60,-120)],[2.35,R(-150,-280)],[2.5,R(60,-330)],[2.6,S0],[2.72,S1],[2.82,lerpP(S1,[S1[0]+10,FLOOR-10],0.8)],[3.5,R(140,70)]],sm);
  cut=sm(2.6,2.72,t);trailOn=[2.42,2.9]}
 else if(A==='I'){ // drifts in, his hanging ear lifts into a thin blade, a careless flick, the ear falls again
  x=K.lerp(start,strikeX,K.eo(0.4,2.1,t))-10*sm(3.4,4.5,t);
  shear=0.05*Math.sin(t*Math.PI*1.6)*(t>0.4?1:0)*(1-sm(2.3,2.5,t)*(1-sm(3.0,3.6,t)))-0.05*sm(3.2,4,t);
  m=sm(1.9,2.4,t)*(1-sm(2.85,3.5,t));
  tip=track(t,[[0,R(40,80)],[2.4,R(150,95)],[2.53,R(130,-30)],[2.6,S0],[2.7,S1],[2.82,[S1[0]+40,S1[1]-70]],[3.35,R(70,110)]],sm);
  bend=0.9*(1-sm(2.4,2.58,t))-0.5*sm(2.55,2.7,t)*(1-sm(2.75,3.1,t))+0.9*sm(2.85,3.3,t);
  cut=sm(2.6,2.7,t);trailOn=[2.5,2.85]}
 else { // glides without bob, stands still, a straight stiletto, one precise lunge and draw, then preens
  x=K.lerp(start,strikeX,sm(0.4,1.5,t))+30*sm(2.45,2.6,t)*(1-sm(2.95,3.35,t));
  sy=1+0.025*sm(3.3,3.8,t);
  m=sm(2.0,2.35,t)*(1-sm(2.95,3.3,t));
  tip=track(t,[[0,R(40,0)],[2.35,R(150,0)],[2.5,R(165,0)],[2.6,S0],[2.85,S1],[2.95,S1],[3.3,R(70,0)]],sm);
  cut=sm(2.6,2.85,t);trailOn=[2.55,2.95]}
 return{x,shear,sy,m,tip,bend,ear,cut,trailOn}}
function bodyWorld(A,K,x,shear,sy,ear,toss){
 const cs=K.CAST[A],w=cs.w*S,h=cs.h*S;
 return base(A).map((p,i)=>{const wE=Math.exp(-Math.pow((i-OFF[2])/4,2))+Math.exp(-Math.pow((i-OFF[3])/4,2));
  return[x+(p[0]+shear*p[1])*w,FLOOR-(p[1]+ear*wE)*h*sy]})}
const PROF={R:'paring',B:'cleaver',I:'ear',O:'stiletto'};
function doer(t,A,V,K,vs){
 const cs=K.CAST[A],vc=K.CAST[V];const gap={R:40,B:150,I:120,O:110}[A]*Q;
 const strikeX=VX-vc.w*S/2-gap-cs.w*S/2;
 // root from un-sheared idle at the current x (two-pass so root tracks the body)
 const pre=doerPlan(t,A,V,K,[0,0],vs,strikeX);
 const b0=bodyWorld(A,K,pre.x,pre.shear,pre.sy,pre.ear);
 const rLo=b0[ix(1,0.45)],rHi=b0[ix(2,0.28)],root=lerpP(rLo,rHi,0.5);
 const pl=doerPlan(t,A,V,K,root,vs,strikeX);
 const body=b0;let pts=body,blade=null;
 if(pl.m>0.001){
  const pr=BLADES[PROF[A]],W=pr.W*S,tp=pl.tip;let dx=tp[0]-root[0],dy=tp[1]-root[1];const L=Math.max(40,Math.hypot(dx,dy));dx/=L;dy/=L;const nx=-dy,ny=dx;
  const at=(u,v)=>{const bv=v+pl.bend*Math.sin(Math.PI*u)*3.5*(L/200);return[root[0]+dx*u*L+nx*bv*W,root[1]+dy*u*L+ny*bv*W]};
  const s1=body.slice(OFF[1],ix(1,0.45)+1).concat(pr.edge.map(q=>at(q[0],q[1])));
  const s2=pr.spine.map(q=>at(q[0],q[1])).concat([rHi]).concat(body.slice(ix(2,0.28)+1,OFF[3]+1));
  const key=body.slice();const r1=resample(s1,SEGN[1]+1,true),r2=resample(s2,SEGN[2]+1,true);
  for(let k=0;k<SEGN[1];k++)key[OFF[1]+k]=r1[k];for(let k=0;k<SEGN[2];k++)key[OFF[2]+k]=r2[k];
  const mm=K.sm(0,1,pl.m);pts=body.map((p,i)=>lerpP(p,key[i],mm));
  const steel=pr.edge.filter(q=>q[0]>=0.26||A==='I').concat(pr.spine.filter(q=>q[0]>=0.26||A==='I')).map(q=>at(q[0],q[1]));
  blade={from:ix(1,0.45),to:ix(2,0.28),m:mm,steel};
 }
 return{pts,body,pl,blade,cs,w:cs.w*S,h:cs.h*S}}

// ---------- drawing
function jit(K,pts,t,seed,amp){const f=Math.floor(t*12);return pts.map((p,i)=>[p[0]+(K.hash(i*7.13+f*31.7+seed)-0.5)*amp,p[1]+(K.hash(i*3.71+f*17.3+seed+9)-0.5)*amp])}
function closed(g,p){const n=p.length;g.beginPath();let m=lerpP(p[n-1],p[0],0.5);g.moveTo(m[0],m[1]);
 for(let i=0;i<n;i++){const q=p[(i+1)%n];m=lerpP(p[i],q,0.5);g.quadraticCurveTo(p[i][0],p[i][1],m[0],m[1])}g.closePath()}
function open(g,p){g.beginPath();g.moveTo(p[0][0],p[0][1]);for(let i=1;i<p.length-1;i++){const m=lerpP(p[i],p[i+1],0.5);g.quadraticCurveTo(p[i][0],p[i][1],m[0],m[1])}g.lineTo(p[p.length-1][0],p[p.length-1][1])}
function line(g,pts,col,w){open(g,pts);g.strokeStyle=col;g.lineWidth=w;g.lineCap='round';g.lineJoin='round';g.stroke()}

function backdrop(g,t,K,sway){
 const gr=g.createLinearGradient(0,0,0,1080);gr.addColorStop(0,'#211f26');gr.addColorStop(0.62,'#2b2830');gr.addColorStop(0.63,'#1c1a1e');gr.addColorStop(1,'#141215');
 g.fillStyle=gr;g.fillRect(0,0,1920,1080);
 const lx=960+Math.sin(sway)*120,ly=230;
 const rg=g.createRadialGradient(lx,ly+40,10,lx,ly+300,1000);rg.addColorStop(0,'rgba(255,214,150,0.30)');rg.addColorStop(0.5,'rgba(255,200,130,0.08)');rg.addColorStop(1,'rgba(0,0,0,0)');
 g.fillStyle=rg;g.fillRect(0,0,1920,1080);
 g.fillStyle='rgba(255,210,150,0.07)';g.beginPath();g.ellipse(lx,FLOOR+20,700,90,0,0,Math.PI*2);g.fill();
 const ch='rgba(225,208,176,0.32)',f=Math.floor(t*12),J=(i)=>(K.hash(i+f*13.1)-0.5)*2;
 const L=(a,b,c,d,i,w)=>line(g,[[a+J(i),b+J(i+1)],[(a+c)/2+J(i+2),(b+d)/2+J(i+3)],[c+J(i+4),d+J(i+5)]],ch,w||2);
 L(0,668,1920,672,1,2.5);L(150,668,120,1080,10);L(1770,668,1800,1080,20);
 // window, left, with moon
 L(200,200,430,204,30);L(430,204,428,520,40);L(428,520,198,516,50);L(198,516,200,200,60);L(314,202,313,518,70);L(199,358,429,362,80);
 g.strokeStyle=ch;g.lineWidth=2;g.beginPath();g.arc(372+J(90),262+J(91),22,0,Math.PI*2);g.stroke();
 // door, right
 L(1560,668,1562,300,100);L(1562,300,1720,302,110);L(1720,302,1722,668,120);g.beginPath();g.arc(1700,500,6,0,Math.PI*2);g.stroke();
 // lamp: cord, shade, bulb
 L(960,0,lx,ly-60,130,2);
 g.fillStyle='rgba(255,226,170,0.9)';g.beginPath();g.arc(lx,ly+8,12,0,Math.PI*2);g.fill();
 line(g,[[lx-60,ly],[lx-24,ly-62],[lx+24,ly-62],[lx+60,ly],[lx-60,ly]],'rgba(235,220,190,0.75)',2.5);
 for(let i=0;i<9;i++){const x=40+i*230+J(140+i)*3;L(x,30,x+6,640,150+i*7,1)}
}
function shadow(g,x,w,a){g.fillStyle=`rgba(0,0,0,${a})`;g.beginPath();g.ellipse(x,FLOOR+4,w*0.62,14,0,0,Math.PI*2);g.fill()}

function attrs(g,id,pts,t,K,extra){
 const f=Math.floor(t*12);
 if(id==='R'){const a=ix(1,0.74),b=ix(3,0.26);const poly=pts.slice(a,b+1);
  g.fillStyle='#6e3a33';closed(g,poly);g.fill();g.strokeStyle=INK;g.lineWidth=2.5;g.stroke();
  const lo=pts[b],hi=pts[a];for(let k=1;k<10;k++){const p=lerpP(lo,hi,k/10);line(g,[p,[p[0]+(K.hash(k+f)-0.5)*3,p[1]+12]],'#6e3a33',3)}}
 if(id==='B'){const q=[pts[ix(1,0.34)],pts[ix(1,0.44)],pts[ix(3,0.56)],pts[ix(3,0.66)]];
  g.fillStyle='#2a2622';g.beginPath();g.moveTo(...q[0]);g.lineTo(...q[1]);g.quadraticCurveTo((q[1][0]+q[2][0])/2,(q[1][1]+q[2][1])/2+10,...q[2]);g.lineTo(...q[3]);g.quadraticCurveTo((q[3][0]+q[0][0])/2,(q[3][1]+q[0][1])/2+10,...q[0]);g.fill();
  const BL=pts[OFF[4]],BR=pts[OFF[1]],TR=pts[ix(2,0.2)],TL=pts[ix(2,0.8)];const c=lerpP(lerpP(BL,BR,0.5),lerpP(TL,TR,0.5),0.7);
  const sx=Math.hypot(BR[0]-BL[0],BR[1]-BL[1])*0.17,syy=Math.max(6,(lerpP(BL,BR,.5)[1]-lerpP(TL,TR,.5)[1])*0.17);
  g.strokeStyle='#9a8460';g.lineWidth=3;g.beginPath();g.ellipse(c[0],c[1],sx,syy,0,0,Math.PI*2);g.stroke();
  g.beginPath();g.moveTo(c[0],c[1]+syy*0.8);g.lineTo(c[0],c[1]-syy*0.7);g.stroke();
  for(let k=0;k<4;k++){const yy=c[1]-syy*0.5+k*syy*0.3;g.beginPath();g.ellipse(c[0]-sx*0.2,yy,sx*0.18,syy*0.09,-0.6,0,Math.PI*2);g.ellipse(c[0]+sx*0.2,yy,sx*0.18,syy*0.09,0.6,0,Math.PI*2);g.stroke()}}
 if(id==='I'){ // fold line of each hanging ear
  line(g,[pts[OFF[2]],pts[ix(1,0.82)],pts[ix(2,0.24)]],INK,2);line(g,[pts[OFF[3]],pts[ix(3,0.18)],pts[ix(2,0.76)]],INK,2)}
 if(id==='O'){const wig=extra.wig;if(!extra.bald&&!has('O','wig')){g.fillStyle='#7a3b8f';closed(g,pts.slice(ix(1,0.86),ix(3,0.14)+1));g.fill()}if(!extra.later)wigLine(g,wig)}}
function wigLine(g,wig){if(has('O','wig'))wig=wig.map((q,i)=>[q[0]+22+i*0.8,q[1]-8+i*1.2]);line(g,wig,'#7a3b8f',34);
  for(let k=0;k<3;k++)line(g,wig.map((p,i)=>[p[0]+(k-1)*7,p[1]+(k-1)*3]),'#4f2160',2);}
function wigFrom(pts,K,toss,t){ // wig polyline anchored to landmarks: right strand, top, left strand
 const ids=[];for(let i=ix(1,0.5);i<=OFF[3]+Math.round(0.5*(SEGN[3]-1));i++)ids.push(i);
 let cx=0;ids.forEach(i=>cx+=pts[i][0]);cx/=ids.length;
 let w=resample(ids.map(i=>[pts[i][0]+Math.sign(pts[i][0]-cx)*9,pts[i][1]-5]),24,true);
 if(toss){w=w.map((p,i)=>{const e=Math.abs(i-11.5)/11.5;return[p[0]+toss*e*e*40*(i<12?1:0.6),p[1]-toss*e*e*20]})}
 return w}

function carried(g,id,p,t,K){
 const BL=p[OFF[4]],BR=p[OFF[1]],TR=p[ix(2,0.2)],TL=p[ix(2,0.8)],at=(u,v)=>lerpP(lerpP(BL,BR,u+0.5),lerpP(TL,TR,u+0.5),v);
 const W=Math.hypot(BR[0]-BL[0],BR[1]-BL[1]),f=Math.floor(t*12);
 const chord=(fa,col,w)=>{const a=p[ix(1,fa)],b=p[ix(3,1-fa)],m=lerpP(a,b,0.5);line(g,[a,[m[0],m[1]+8],b],INK,w+4);line(g,[a,[m[0],m[1]+8],b],col,w)};
 if(has(id,'rope')){chord(0.3,'#a88550',6);chord(0.62,'#a88550',6);const k=lerpP(p[ix(1,0.62)],p[ix(3,0.38)],0.5);g.strokeStyle=INK;g.lineWidth=3;g.beginPath();g.ellipse(k[0],k[1]+8,9,6,0.5,0,Math.PI*2);g.stroke()}
 if(has(id,'gag'))chord(0.8,'#efe7d6',13);
 if(has(id,'cinched')){const a=p[ix(1,0.84)],b=p[ix(3,0.16)];line(g,[a,lerpP(a,b,0.5),b],INK,5)}
 if(has(id,'blot')){const c=at(-0.18,0.55),r=W*0.09;const bl=[];for(let k=0;k<12;k++){const an=k/12*Math.PI*2;bl.push([c[0]+Math.cos(an)*r*(0.75+0.5*K.hash(k*3.3)),c[1]+Math.sin(an)*r*(0.75+0.5*K.hash(k*5.1))])}g.fillStyle='#120e0b';closed(g,bl);g.fill()}
 if(has(id,'tag')){const c=at(0.18,0.62);g.save();g.translate(c[0],c[1]);g.rotate(0.15);g.fillStyle='#f6f1e4';g.fillRect(-16,-11,32,22);g.strokeStyle=INK;g.lineWidth=2;g.strokeRect(-16,-11,32,22);g.restore();line(g,[[c[0]-2,c[1]-12],[c[0]+4,c[1]-26]],INK,3)}
 if(has(id,'torn')){const a=p[ix(2,0.06)],b=p[ix(1,0.8)],z=[];for(let k=0;k<=6;k++){const q=lerpP(a,b,k/6);z.push([q[0]+(k%2?-7:7),q[1]])}line(g,z,INK,3);g.fillStyle=FLOUR;for(let k=0;k<4;k++){const q=lerpP(a,b,0.2+k*0.2);g.beginPath();g.arc(q[0]+4,q[1]+3,3,0,Math.PI*2);g.fill()}}
 if(has(id,'coins')){const c=at(0.32,0.08);for(let k=0;k<3;k++){g.fillStyle='#d9b04a';g.beginPath();g.ellipse(c[0]+k*6,c[1]-k*7,12,5,0,0,Math.PI*2);g.fill();g.strokeStyle=INK;g.lineWidth=2;g.stroke()}}
}
function drawSack(g,id,pts,t,K,seed,fillA,extra,blade){
 const p=jit(K,pts,t,seed,2.2);
 g.fillStyle=K.CAST[id].fill;closed(g,p);g.fill();
 // cloth crease lines (in-betweened with the contour)
 const c1=lerpP(p[OFF[0]],p[ix(2,0.5)],0.15),c2=lerpP(p[OFF[0]],p[ix(2,0.5)],0.85);
 line(g,[c1,lerpP(c1,c2,0.5).map((v,i)=>v+(i?0:4)),c2],'rgba(120,96,62,0.35)',2);
 if(has(id,'greyed')){g.fillStyle='rgba(105,108,118,0.5)';closed(g,p);g.fill()}
 attrs(g,id,extra.attrPts?jit(K,extra.attrPts,t,seed,2.2):p,t,K,extra);
 carried(g,id,p,t,K);
 closed(g,p);g.strokeStyle=INK;g.lineWidth=4;g.lineJoin='round';g.stroke();
 if(blade&&blade.m>0.5){const a=K.sm(0.6,0.95,blade.m),st=blade.steel;g.save();g.globalAlpha=a;g.beginPath();g.moveTo(...st[0]);for(const q of st)g.lineTo(...q);g.closePath();
  g.fillStyle=STEEL;g.fill();g.strokeStyle=INK;g.lineWidth=3;g.stroke();const h=Math.floor(st.length/2);line(g,st.slice(0,h),'#ffffff',2.5);g.restore()}
}

// ---------- sound: everything is grains. the cast speaks through K.SND.say; the deed adds
// pen-scratch grains while a contour is being redrawn into a blade, a cloth rip on the cut,
// and flour running out as a stream of very short sand grains.
function SOUND(ac,out,t0,A,V,K){const SN=K.SND,H=K.hash,P=VS[V],pan=x=>K.cl(-1,1,x/960-1);
 const vsAt=t=>victim(t,A,V,K),dAt=t=>doer(t,A,V,K,vsAt(t));
 const dx=t=>dAt(t).pl.x,vp=pan(VX),at=t=>t0+t;
 const say=(id,t,gest,amt,x)=>SN.say(ac,out,id,at(t),gest,amt,pan(x));
 // doer travel, per sack
 if(A==='R'){[0.9,1.4,1.9].forEach(t=>say('R',t,'step',1,dx(t)));[0.65,1.15,1.65].forEach(t=>say('R',t,'tick',0.5,dx(t)));say('R',3.75,'step',0.7,dx(3.75))}
 if(A==='B'){[0.6,1.0,1.4,1.6].forEach(t=>say('B',t,'step',0.8,dx(t)));say('B',1.65,'breathe',0.4,dx(1.65));say('B',2.15,'react',0.35,dx(2.15));say('B',3.85,'sink',0.6,dx(3.85))}
 if(A==='I'){[0.8,1.35,1.9].forEach(t=>say('I',t,'step',0.7,dx(t)));say('I',3.3,'breathe',0.6,dx(3.3))}
 if(A==='O'){say('O',0.4,'tick',0.8,dx(0.4));say('O',1.5,'tick',0.8,dx(1.5));SN.cloud(ac,out,at(0.4),1.1,30,{bp:5200,a:0.012,d:[0.05,0.12],spread:0.1},u=>Math.sin(Math.PI*u));say('O',2.45,'tick',1,dx(2.45));say('O',3.4,'tick',0.6,dx(3.4));say('O',3.5,'tick',0.4,dx(3.5))}
 // the contour being redrawn: pen-scratch grains whose band rises as the blade grows, falls as it retracts
 const W={R:[1.7,2.3,3.25,3.85],B:[1.95,2.35,3.2,3.9],I:[1.9,2.4,2.85,3.5],O:[2.0,2.35,2.95,3.3]}[A];
 const scratch=(a,b,up)=>{const n=Math.round((b-a)*90);for(let k=0;k<n;k++){const u=(k+H(k*3.7+a))/n,t=a+u*(b-a),v=up?u:1-u;
  SN.grain(ac,out,at(t),{bp:700+2600*v,q:4,d:0.012+0.02*H(k*1.3),a:0.05+0.04*Math.sin(Math.PI*u),pan:pan(dx(t)+60)})}};
 scratch(W[0],W[1],true);scratch(W[2],W[3],false);
 if(A==='I')SN.cloud(ac,out,at(2.5),0.12,200,{bp:1800,a:0.05,d:[0.01,0.03],spread:0.1});           // the lazy flick
 if(A==='B')SN.cloud(ac,out,at(2.42),0.16,220,{bp:500,a:0.06,d:[0.01,0.04],spread:0.1},u=>u);      // the cleaver coming down
 // contact: steel tick + cloth rip along the cut (R saws twice) + a body thump
 const cuts={R:[[2.6,0.18],[2.8,0.12],[2.95,0.13]],B:[[2.6,0.12]],I:[[2.6,0.1]],O:[[2.6,0.25]]}[A];
 SN.grain(ac,out,at(C),{f:2900,type:'triangle',d:0.16,a:0.22,pan:vp,att:0.03});SN.grain(ac,out,at(C+0.005),{f:4350,d:0.1,a:0.12,pan:vp,att:0.03});
 SN.thump(ac,out,at(C),A==='B'?1.3:0.8,A==='B'?42:70,vp);
 cuts.forEach(([c,d],j)=>{const n=Math.round(d*500);for(let k=0;k<n;k++){const u=H(k*1.91+j*7),t=c+u*d;SN.grain(ac,out,at(t),{bp:2200+2400*H(k*4.3+j),q:2,d:0.004+0.008*H(k*2.2),a:(j?0.12:0.18)*(1-0.5*u),pan:vp,att:0.2})}});
 // the victim answers in its own voice
 if(V==='I')say('I',C+0.35,'breathe',0.5,VX);else say(V,C+(V==='B'?0.15:0.04),'react',1,VX);
 say(V,C+0.3,'sink',V==='B'?1.2:0.8,VX);
 // flour running out: very short sand grains, density following the flow, plus the softer hiss where it lands
 const cap=P.cap*(has(V,'emptied')?0.6:1),n=Math.round(520*P.Td*cap);
 for(let k=0;k<n;k++){const u=Math.pow(H(k*0.731+3),1.6),t=C+0.06+u*P.Td,fl=1-u;
  SN.grain(ac,out,at(t),{bp:2400+3600*H(k*2.17),q:1.2,d:0.003+0.007*H(k*5.3),a:0.1*fl+0.015,pan:vp-0.08+0.06*H(k*9.1),att:0.3});
  if(k%4===0)SN.grain(ac,out,at(t+0.18),{bp:700+500*H(k*7.7),q:1,d:0.012+0.02*H(k*1.1),a:0.05*fl,pan:vp-0.12})}
 say(V,C+P.Td+0.3,'land',V==='B'?0.3:0.6,VX);
 if(V==='O'){say('O',C+1.45,'tick',0.7,VX+60);say('O',C+1.52,'tick',0.45,VX+70)}
}

DEED({
 n:4,key:'knifing',title:'Knifing',scion:7,lineage:'Peter Foldès — Drawn Metamorphosis',
 op:'The doer\'s contour is in-betweened into a blade key drawing, the blade tip is driven along a slit on the victim, and the victim\'s contour is in-betweened from its full key to its emptied key while flour runs out of the slit.',
 made:'Each sack is a hand-authored key contour of 90 corresponding points (five landmark segments) inked over a flat cloth fill, with its shawl, belt, wig or hanging ears attached to fixed contour indices. The room is a boiling chalk-line drawing of a night parlour under one lamp.',
 moved:'Nothing is animated directly: every frame is a computed in-between of key drawings (idle, blade, emptied, fallen wig, flour mound) on eased per-sack timing tracks. The doer\'s shoulder in-betweens into its own blade and back; the victim\'s contour sinks from its full key to its empty key as the drained-flour value rises.',
 contact:C,
 leaves:{A:[],V:['emptied','torn','wig']},
 marks(t,A,V,K,opt){CAR=(opt&&opt.carry)||{};const vs=victim(t,A,V,K),D=doer(t,A,V,K,vs);
  const bb=ps=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const q of ps){x0=Math.min(x0,q[0]);y0=Math.min(y0,q[1]);x1=Math.max(x1,q[0]);y1=Math.max(y1,q[1])}return{x:x0,y:y0,w:x1-x0,h:y1-y0}};
  return{A:bb(D.pts),V:bb(vs.pts)}},
 sound(ac,out,t0,A,V,K){SOUND(ac,out,t0,A,V,K)},
 draw(g,t,A,V,K,opt){
  const LY=opt&&opt.layer,on=l=>!LY||LY===l;CAR=(opt&&opt.carry)||{};
  const vs=victim(t,A,V,K);const D=doer(t,A,V,K,vs);
  const sway=A==='B'?0.06*Math.sin((t-C)*5)*Math.exp(-(t-C)*1.2)*(t>C?1:0):0;
  if(on('bg'))backdrop(g,t,K,sway);
  if(on('V'))shadow(g,vs.x,vs.w*(1+0.4*vs.s),0.45);if(on('A'))shadow(g,D.pl.x,D.w,0.45);
  if(on('V')){
  // victim + wig
  let extra={};
  if(V==='O'){let w=wigFrom(vs.pts,K,0,t);const fa=K.sm(C+0.55,C+1.5,t);
   if(fa>0){const fx=vs.x+vs.w*0.1;const fl0=[];for(let k=0;k<=16;k++){const a=k/16*Math.PI*3.2,r=46-k*1.8;fl0.push([fx+Math.cos(a)*r*1.5,FLOOR+22-Math.sin(a)*r*0.45])}const fallen=resample(fl0,24,true);
    w=w.map((p,i)=>{const q=lerpP(p,fallen[i],fa);q[1]-=Math.sin(Math.PI*fa)*60;return q})}
   extra.wig=w;extra.bald=fa>0.05;extra.later=fa>0.05}
  drawSack(g,V,vs.pts,t,K,11,1,extra,null);if(extra.later)wigLine(g,extra.wig);
  // slit: lens cut into the victim along its own (moving) coordinates
  const cut=D.pl.cut;
  if(cut>0){const a=vs.S0,b=lerpP(vs.S0,vs.S1,cut);const dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy)||1,nx=-dy/L,ny=dx/L;
   const op=(2.5+6*K.sm(C,C+0.5,t))*Q*(V==='I'?0.7:1)*(1-0.3*vs.s);const up=[],dn=[];
   for(let k=0;k<=10;k++){const u=k/10,p=lerpP(a,b,u),o=Math.sin(Math.PI*u)*op;up.push([p[0]-nx*o,p[1]-ny*o]);dn.push([p[0]+nx*o,p[1]+ny*o])}
   const lens=up.concat(dn.slice().reverse());const crust=dn.slice(1,10);
   g.fillStyle=FLOUR;g.globalAlpha=K.cl(0,1,vs.rate*2+ (vs.d<1?0.3:0));closed(g,dn.slice(2,9).concat([lerpP(a,b,0.5)]));g.fill();g.globalAlpha=1;
   // flour: ribbon + falling grains + mound, all from the slit's lower lip
   const lip=lerpP(a,b,0.5),lp=[lip[0]+nx*op*0.6*Math.sign(ny||1),Math.max(lip[1],lip[1]+ny*op)];
   const flow=K.cl(0,1,vs.rate)*vs.P.cap*vs.capC;
   const pw=Math.sqrt(K.CAST[V].w*K.CAST[V].h*vs.P.cap*vs.capC)*S*1.45,pd=Math.pow(vs.d,0.6);
   const pileW=pw*0.95*(0.15+0.85*pd),pileH=pileW*0.16*(0.5+0.5*pd);const v0=victim(C+0.1,A,V,K),pcx=lerpP(v0.S0,v0.S1,0.5)[0]-20*Q;
   if(flow>0.01){const ww=(10+40*flow)*Q;const fl=[[lp[0]-ww*0.3,lp[1]],[lp[0]+ww*0.3,lp[1]],[pcx+ww*0.6,FLOOR-pileH*0.8],[pcx-ww*0.6,FLOOR-pileH*0.8]];
    g.fillStyle='rgba(251,247,238,0.92)';g.beginPath();g.moveTo(...fl[0]);g.quadraticCurveTo(lp[0]-ww*0.6,(lp[1]+FLOOR)/2,...fl[3]);g.lineTo(...fl[2]);g.quadraticCurveTo(lp[0]+ww*0.6,(lp[1]+FLOOR)/2,...fl[1]);g.fill()}
   // grains: each born at a fixed time, ballistic, pure function of t
   g.strokeStyle=FLOUR;g.lineCap='round';
   for(let k=0;k<300;k++){const tb=C+0.05+k*0.008;if(tb>C+vs.P.Td)break;const age=t-tb;if(age<0)break;
    const r=1-(tb-C)/vs.P.Td;if(K.hash(k*1.7)>r*vs.P.cap+0.08)continue;
    const vx=(K.hash(k*3.1)-0.65)*160,y=lp[1]+40*age+900*age*age;if(y>FLOOR-4)continue;const xx=lp[0]+vx*age;
    g.lineWidth=2+K.hash(k)*3;g.beginPath();g.moveTo(xx,y);g.lineTo(xx-vx*0.015,y-(40+1800*age)*0.015);g.stroke()}
   const relens=()=>{g.fillStyle='#4a3826';closed(g,lens);g.fill();g.strokeStyle=INK;g.lineWidth=2.5;g.stroke();line(g,crust,FLOUR,4.5*Q*0.8)};
   if(vs.d>0.005){const mk=MOUND.map((q,i)=>lerpP(MOUND0[Math.min(4,Math.round(i/2))],q,pd));
    const mp=resample(mk,24,true).map(q=>[pcx+q[0]*pileW,FLOOR+6-q[1]*pileH]);g.fillStyle=FLOUR;
    const mj=jit(K,mp,t,77,1.5);g.beginPath();g.moveTo(...mj[0]);for(let i=1;i<mj.length;i++)g.lineTo(...mj[i]);g.closePath();g.fill();
    g.strokeStyle='rgba(23,19,15,0.6)';g.lineWidth=2;g.stroke();
    if(flow>0.05)for(let k=0;k<6;k++){const a2=K.hash(k*9+Math.floor(t*12))*Math.PI;g.fillStyle='rgba(251,247,238,0.5)';g.beginPath();g.arc(pcx+Math.cos(a2)*pileW*0.35,FLOOR-pileH-6-Math.sin(a2)*16*flow,4+5*flow,0,Math.PI*2);g.fill()}}
   relens();
  }
  }
  if(!on('A'))return;
  // doer: onion-skin ghosts of the preceding in-betweens during the stroke (Foldès trail)
  const tr=D.pl.trailOn;
  if(t>tr[0]&&t<tr[1]+0.25){const fade=1-K.sm(tr[1],tr[1]+0.25,t);
   for(const [dt,al] of [[0.1,0.16],[0.05,0.3]]){const Dg=doer(t-dt,A,V,K,victim(t-dt,A,V,K));g.save();g.globalAlpha=al*fade;closed(g,Dg.pts);g.strokeStyle='#e8dcc4';g.lineWidth=3;g.stroke();g.restore()}}
  // ghost of the idle key while the body is mid-metamorphosis
  if(D.blade&&D.blade.m<0.98){g.save();g.globalAlpha=0.35*Math.sin(Math.PI*D.blade.m);closed(g,D.body);g.strokeStyle='#e8dcc4';g.lineWidth=2;g.setLineDash([6,8]);g.stroke();g.restore()}
  let dex={attrPts:D.body};if(A==='O'){const toss=K.sm(3.35,3.6,t)*Math.sin((t-3.35)*9)*Math.exp(-(t-3.35)*2.2)*(t>3.35?1:0);dex.wig=wigFrom(D.body,K,toss,t)}
  drawSack(g,A,D.pts,t,K,23,1,dex,D.blade);
  // stroke line: the tip's path over the last 0.12 s
  if(D.blade&&t>tr[0]&&t<tr[1]+0.2){const tp=[];for(let k=0;k<=8;k++){const tt=t-0.12+k*0.015;const vv=victim(tt,A,V,K);const dd=doer(tt,A,V,K,vv);tp.push(dd.pl.tip)}
   g.save();g.globalAlpha=1-K.sm(tr[1],tr[1]+0.2,t);line(g,tp,'#fff6e0',5);g.restore()}
  // impact frame: a one-beat burst of short marks around the slit start
  const ib=K.sm(C-0.01,C+0.02,t)*(1-K.sm(C+0.06,C+0.2,t));
  if(ib>0){const c=vs.S0;g.strokeStyle=`rgba(255,246,224,${ib})`;g.lineWidth=4;for(let k=0;k<9;k++){const an=k/9*Math.PI*2+0.3,r0=26,r1=26+30+K.hash(k)*25;g.beginPath();g.moveTo(c[0]+Math.cos(an)*r0,c[1]+Math.sin(an)*r0);g.lineTo(c[0]+Math.cos(an)*r1,c[1]+Math.sin(an)*r1);g.stroke()}}
 }
});
})();
