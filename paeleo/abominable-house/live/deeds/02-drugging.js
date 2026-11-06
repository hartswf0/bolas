// 02 · Drugging — SCION 41 · Secondary Dynamics (inertia and restraint)
// Every body is a set of damped springs integrated at a fixed step from t=0 to t on each call:
//   lean θ   : inverted pendulum about the base corner, θ'' = -kθ(θ-θ*) - cθ θ' + G sinθ + inertia + forcing
//   squash s : height spring, s'' = -ks(s-s*) - cs s'
//   bend β   : spine curvature spring driven by base acceleration and lean acceleration
//   ears, wig locks, shawl tail : point masses on springs with gravity and a length constraint (follow-through)
//   lamp     : pendulum; floor : spring that takes impulses when a body hits the boards
// The drug is not an animation: it changes the coefficients. After the cup, the victim's kθ falls below its own
// gravity term G, damping falls, ear stiffness falls, s* sinks — so it wobbles, sways, sags and tips over by itself;
// the floor collision (restitution .2, friction) takes the last energy out. Invariant: with the drug at zero no
// body falls (kθ > G for every sack); energy decays once the scripted sources stop.
(function(){
const FY=800,TX0=846,TX1=1074,TY=FY-106,DT=1/200,GR=1800,CUPW=44,CUPH=54;
const cxA=TX0+56,cxV=TX1-58;
const LAMPX=960,LAMPL=300;
const clamp=(a,b,x)=>Math.max(a,Math.min(b,x));
const smo=(a,b,x)=>{const u=clamp(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
const eoc=(a,b,x)=>{const u=clamp(0,1,(x-a)/(b-a));return 1-Math.pow(1-u,3)};
const H=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};
// per-sack material priors (mass proxy, lean damping, ear spring, ear rest in body frame as fraction of w,h)
const MAT={
 R:{w:168,h:122,m:1.6,z:.55,ek:150,ez:.55,er:[.13,.14],el:.66,col:'#d6bf96',dk:'#8d7652'},
 B:{w:244,h:214,m:4.0,z:.45,ek:120,ez:.5,er:[.10,.10],el:.52,col:'#e8d5ae',dk:'#94805a'},
 I:{w:128,h:98,m:.7,z:.18,ek:60,ez:.22,er:[.16,-.78],el:1.0,col:'#e2cea5',dk:'#8f7b55'},
 O:{w:80,h:184,m:1.0,z:.62,ek:220,ez:.6,er:[.22,.07],el:.56,col:'#f0e4c8',dk:'#9a8866'}};
// victim drug schedule: wobble start, collapse start, wobble forcing amp, sag floor, ear limpness
// mode 'sag': squat sacks lose the squash spring and pour down (the weight wins over ks); 'fall': the tall one loses kθ and topples
const DRUG={R:{w0:3.3,c0:4.3,F:5.5,sMin:.6,k1:1.5,mode:'sag',flop:.45,slide:16},B:{w0:3.55,c0:4.4,F:3.2,sMin:.64,k1:1.4,mode:'sag',flop:.35,slide:22},
 I:{w0:3.2,c0:3.85,F:7,sMin:.36,k1:1.7,mode:'sag',flop:.6,slide:26},O:{w0:3.25,c0:4.1,F:3.6,sMin:.86,k1:1.35,mode:'fall'}};
const CONTACT=2.7;
// camera: a 1.25 dolly-in about the table foot so the cast reads at thumbnail size (marks() uses the same map)
const CAM={s:1.25,cx:960,cy:FY};
// carried damage from earlier shots, set at the top of every simulate() call (pure per call)
let TAGS={R:[],B:[],I:[],O:[]};const has=(id,tag)=>(TAGS[id]||[]).indexOf(tag)>=0;

function mkSack(id,role){const M=MAT[id];const G=3*GR/(2*M.h);
 const x0=role==='A'?TX0-M.w/2-10:TX1+M.w/2+12;
 return {id,role,M,G,x:role==='A'?x0-170:x0,xv:0,xa:0,xHome:x0,th:0,om:0,s:1,sv:0,b:0,bv:0,
  ears:[null,null],locks:[null,null],tail:null,landed:-1,k:6*G,zz:M.z};}

// local (y up, origin base centre) -> world
function L2W(S,lx,ly){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;
 const px=S.th>=0?ww/2:-ww/2;const u=ly/hh;const lx2=lx+S.b*hh*u*u;const dx=lx2-px;
 const c=Math.cos(S.th),sn=Math.sin(S.th);return [S.x+px+dx*c+ly*sn,FY-(-dx*sn+ly*c)];}
function prof(id,u){let p=1+.05*Math.sin(Math.PI*u)-.07*u*u*u;if(id==='I')p+=.06*Math.sin(Math.PI*u*.8);if(id==='O')p=1+.03*Math.sin(Math.PI*u)-.05*u*u;
 if(has(id,'cinched'))p*=1-.22*Math.exp(-Math.pow((u-.82)/.06,2));return p}
function corner(S,side){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;return L2W(S,side*ww/2*prof(S.id,1),hh)}
function earRest(S,side){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;
 return L2W(S,side*(ww/2*prof(S.id,1)+M.er[0]*M.w),hh+M.er[1]*M.h)}
function topC(S){return L2W(S,0,S.M.h*S.s)}

// ---------- doer scripts: base x target, lean target, stretch, near-ear (right) target, prop tilt -----------
function doerPlan(S,id,t,W){const P={xt:S.xHome,tht:0,st:1,ear:null,tilt:0};
 const home=S.xHome,start=home-170;
 const cupTop=[W.cup.x,TY-CUPH];
 if(id==='R'){P.xt=start+(home-start)*smo(.4,1.15,t);
  P.tht=.07*smo(1.05,1.3,t)*(1-smo(2.3,2.6,t))+.035*Math.sin(2*Math.PI*1.1*(t-1.4))*smo(1.3,1.5,t)*(1-smo(2.0,2.2,t));
  if(t>1.05&&t<2.35){let tx=cupTop[0]-4,ty=cupTop[1]-46;let tl=2.3*smo(1.2,1.4,t)*(1-smo(1.9,2.0,t));
   for(const d of[1.45,1.68,1.91])ty+=10*Math.exp(-Math.pow((t-d)/.05,2));
   if(t>1.95){tx=W.cup.x-CUPW/2-10;ty=TY-CUPH*.5}
   P.ear={x:tx,y:ty,k:3};P.tilt=tl}
  // after: rocks with satisfaction, leans toward the victim (keen eye)
  P.tht+=.06*Math.sin(2*Math.PI*.9*(t-3.2))*smo(3.2,3.6,t)*(1-smo(5.0,5.4,t))+.05*smo(4.8,5.3,t);}
 if(id==='B'){P.xt=start+(home-start)*smo(.45,1.0,t);
  P.tht=.11*smo(1.0,1.3,t)*(1-smo(2.25,2.6,t));
  if(t>1.0&&t<2.3){let tx=cupTop[0]-6,ty=cupTop[1]-30,tl=1.9*smo(1.38,1.5,t);
   if(t>1.55&&t<1.92){const a=(t-1.55)*2*Math.PI*2.7;tx=cupTop[0]+9*Math.cos(a);ty=cupTop[1]+4+4*Math.sin(a);tl=2.6}
   if(t>1.95){tx=W.cup.x-CUPW/2-14;ty=TY-CUPH*.55;tl=.3}
   P.ear={x:tx,y:ty,k:2.2};P.tilt=tl}
  // after: steps back, gentle, sorry; ears let go
  P.xt-=26*smo(3.6,4.4,t);P.tht-=.07*smo(3.6,4.2,t);P.st=1-.04*smo(4.4,5,t);}
 if(id==='I'){P.xt=start+(home-start)*smo(.5,1.25,t);
  P.tht=-.05+.12*smo(1.15,1.4,t)*(1-smo(2.1,2.4,t));P.st=1+.1*smo(1.15,1.4,t)*(1-smo(2.1,2.4,t));
  if(t>1.15&&t<2.15){let tx=cupTop[0]-20,ty=cupTop[1]-34,tl=0;
   if(t>1.42)tl=2.9*smo(1.42,1.52,t)*(1-smo(1.62,1.8,t));
   if(t>1.82){tx=W.cup.x-CUPW/2-8;ty=TY-CUPH*.4}
   P.ear={x:tx,y:ty,k:t>1.82?6:1.4};P.tilt=tl}
  // after: lounges back, the vial swings from the hanging ear
  P.tht-=.12*smo(2.6,3.2,t);P.st-=.05*smo(2.6,3.2,t);}
 if(id==='O'){P.xt=start+(home-start)*eoc(.4,.95,t);
  P.tht=.03*smo(1.0,1.2,t)*(1-smo(2.25,2.4,t));
  if(t>.98&&t<2.3){let tx=cupTop[0]+1,ty=cupTop[1]-92,tl=3.14*smo(1.25,1.33,t)*(1-smo(1.78,1.86,t));
   if(t>1.9){tx=W.cup.x-CUPW/2-8;ty=TY-CUPH*.6}
   P.ear={x:tx,y:ty,k:4};P.tilt=tl}
  // after: leans away, chin up, steps off — cold
  P.tht-=.08*smo(3.0,3.5,t);P.xt-=34*smo(3.2,4.2,t);}
 return P}

// cup x on the table (pushed by the doer's ear), then victim grabs it
function cupPushX(id,t){if(id==='I'){// a careless flick: overshoot and settle (closed-form damped oscillator)
  if(t<1.86)return cxA;const u=t-1.86;const target=cxV;const d=target-cxA;
  return cxA+d*(1-Math.exp(-7*u)*(Math.cos(13*u)-(.25)*Math.sin(13*u)))}
 const [p0,p1]=id==='R'?[2.0,2.32]:id==='B'?[1.98,2.22]:[1.92,2.14];
 return cxA+(cxV-cxA)*smo(p0,p1,t)}

function victimPlan(S,id,t,W){const P={tht:0,st:1,ear:null,drink:0};
 const M=S.M,mouth=topC(S);
 const g0=2.28,l0=2.44,d0=CONTACT,d1=id==='B'?2.98:id==='R'?3.15:3.08,s1=d1+.32;
 const hold=[mouth[0]-M.w*.22-10,mouth[1]-62];
 if(t>g0&&t<s1+.05){let tx=W.cupX0+CUPW/2+6,ty=TY-CUPH*.55;
  if(t>l0&&t<d1+.04){const u=smo(l0,d0,t);tx=tx+(hold[0]-tx)*u;ty=ty+(hold[1]-ty)*u}
  if(id==='R'&&t>2.5&&t<2.7){ty-=0}
  if(t>=d1+.04){const u=smo(d1,s1,t);tx=hold[0]+(W.cupX0+CUPW/2+6-hold[0])*u;ty=hold[1]+(TY-CUPH*.55-hold[1])*u}
  P.ear={x:tx,y:ty,k:3.5}}
 const tiltMax=id==='B'?1.55:id==='O'?1.0:id==='I'?1.15:1.25;
 P.drink=tiltMax*smo(d0-.06,d0+(id==='B'?.1:.22),t)*(1-smo(d1-.06,d1+.1,t));
 if(id==='R')P.tht=-.04*smo(2.42,2.6,t)*(1-smo(2.62,2.7,t))+(-.06)*smo(2.6,2.75,t)*(1-smo(d1,d1+.2,t)); // sniff, then a measured sip
 if(id==='B')P.tht=-.09*smo(2.6,2.72,t)*(1-smo(d1,d1+.2,t));
 if(id==='O')P.tht=-.03*smo(2.6,2.75,t)*(1-smo(d1,d1+.2,t));
 if(id==='I')P.st=1+.06*smo(2.4,2.7,t)*(1-smo(d1,d1+.2,t));
 P.d1=d1;P.s1=s1;return P}

function victimPlanTimes(id){const d1=id==='B'?2.98:id==='R'?3.15:3.08;return d1+.32}
function stepPoint(p,tx,ty,k,z,g,anchor,len,dt){// spring point mass with gravity and length constraint
 const c=2*z*Math.sqrt(k);p.vx+=(k*(tx-p.x)-c*p.vx)*dt;p.vy+=(k*(ty-p.y)-c*p.vy+g)*dt;p.x+=p.vx*dt;p.y+=p.vy*dt;
 if(anchor){const dx=p.x-anchor[0],dy=p.y-anchor[1],d=Math.hypot(dx,dy);if(d>len){p.x=anchor[0]+dx/d*len;p.y=anchor[1]+dy/d*len;
   const rn=(p.vx*dx+p.vy*dy)/d;if(rn>0){p.vx-=rn*dx/d;p.vy-=rn*dy/d}}}
 if(p.y>FY-2){p.y=FY-2;p.vy*=-.2;p.vx*=.9}}

function simulate(t,A,V,carry){
 TAGS={R:[],B:[],I:[],O:[]};if(carry)for(const k in carry)TAGS[k]=(carry[k]||[]).slice();
 const SA=mkSack(A,'A'),SV=mkSack(V,'V');
 const W={cup:{x:cxA,y:TY,rot:0,held:false,level:1,tint:0,fall:-1,fallDir:1},cupX0:cxV,parts:[],stains:[],lamp:{p:0,v:0},fl:{y:0,v:0},
  SA,SV,tLand:-1,vialTip:null,tilt:0,dd:0,drink:0,ev:[],tr:[]};
 for(const S of[SA,SV]){for(const sd of[-1,1]){const r=earRest(S,sd);S.ears[sd<0?0:1]={x:r[0],y:r[1],vx:0,vy:0}}
  if(S.id==='O')for(const sd of[-1,1]){const c=corner(S,sd);S.locks[sd<0?0:1]={x:c[0]+sd*6,y:c[1]+S.M.h*.5,vx:0,vy:0}}
  if(S.id==='R'){const c=corner(S,1);S.tail={x:c[0]+6,y:c[1]+26,vx:0,vy:0}}
  {const c=L2W(S,S.M.w/2,S.M.h*.45);S.dang={x:c[0]+6,y:c[1]+30,vx:0,vy:0}}}
 const n=Math.round(t/DT);let lastTilt=0;
 for(let i=0;i<=n;i++){const tm=i*DT;const dt=i===n?0:DT;
  const PA=doerPlan(SA,A,tm,W),PV=victimPlan(SV,V,tm,W);
  // drug state of victim
  const Dg=DRUG[V];W.dd=smo(CONTACT,CONTACT+.6,tm);
  const Dw=smo(Dg.w0,Dg.w0+.35,tm),Dc=smo(Dg.c0,Dg.c0+.25,tm);
  // ---- cup ----
  const cupFree=!(PV.ear&&tm>2.44&&tm<PV.d1+.32);
  if(tm<2.28){W.cup.x=cupPushX(A,tm);W.cupX0=Math.max(W.cupX0,0)}
  if(tm>=2.28&&tm<2.44)W.cup.x=W.cupX0=cupPushX(A,2.28);
  W.cup.held=!cupFree&&tm>2.44;W.drink=PV.drink;
  if(W.cup.held){const e=SV.ears[0];W.cup.x=e.x-CUPW/2-4;W.cup.y=e.y+CUPH*.55;W.cup.rot=PV.drink}
  else if(tm>=PV.d1+.32){W.cup.x=W.cupX0;W.cup.y=TY;W.cup.rot=0}
  if(tm>CONTACT&&tm<PV.d1+.05)W.cup.level=Math.max(0,W.cup.level-dt*(V==='B'?4.5:V==='R'?1.4:2.1)*(PV.drink>.7?1:0));
  if(W.cup.fall>0){W.cup.rot=W.cup.fallDir*1.55*smo(W.cup.fall,W.cup.fall+.22,tm)}
  // ---- sacks ----
  for(const [S,P,isV] of [[SA,PA,false],[SV,PV,true]]){const M=S.M;
   // base x: spring follower of the scripted x (gives the primary acceleration)
   const kx=90,cx=2*.95*Math.sqrt(kx);const xa=kx*(P.xt!==undefined?P.xt-S.x:S.xHome-S.x)-cx*S.xv;
   if(!isV){S.xv+=xa*dt;S.x+=S.xv*dt;S.xa=xa}else{const d=DRUG[S.id];const xs=S.xHome+(d.slide||0)*smo(d.c0,d.c0+.6,tm);const a2=kx*(xs-S.x)-cx*S.xv;S.xv+=a2*dt;S.x+=S.xv*dt;S.xa=a2}
   // coefficients (the drug changes these)
   let k=6*S.G,z=M.z,F=0,tht=P.tht,ks=420,zs=.32,st=P.st*(has(S.id,'emptied')?.84:1),ek=M.ek*(has(S.id,'drowsy')?.45:1);
   if(has(S.id,'drowsy'))F+=.9*Math.sin(2*Math.PI*.55*tm+(isV?1:0));
   if(isV){const d=DRUG[S.id];
    k=6*S.G*(1-Dw)+d.k1*S.G*Dw;k=k*(1-Dc)+(d.mode==='fall'?.25:2.2)*S.G*Dc;z=M.z*(1-Dw)+.05*Dw+(d.mode==='sag'?.5*Dc:0);
    const w1=Math.sqrt(Math.max(1,d.k1*S.G-S.G));
    F=d.F*Dw*(1-Dc*.85)*Math.sin(w1*(tm-d.w0)-Math.PI/2)*smo(d.w0,d.w0+.6,tm);
    tht+=.05*Dc;F+=(d.mode==='fall'?3.5:0)*Dc;
    ks=420*(1-.7*Dw)*(1-.6*Dc);zs=.32*(1-.6*Dw)*(1-Dc)+.3*Dc+.5*(S.landed>0?1:0);
    st=st*(1-(1-(d.mode==='fall'?d.sMin:.9))*smo(d.w0,d.c0,tm));
    if(d.mode==='sag'){st-=(st-d.sMin)*Dc;
     if(S.landed<0&&Dc>.3&&S.sv>-.02&&S.s<d.sMin+.12){S.landed=tm;W.ev.push({k:'land',t:tm,x:S.x,id:S.id});const J=1.2*M.m;W.fl.v+=J*3.2;W.lamp.v+=J*.012;
      if(M.m>1.2&&W.cup.fall<0){W.cup.fall=tm+.04;W.cup.fallDir=1;W.ev.push({k:'cupfall',t:tm+.04,x:W.cup.x})}
      for(let q=0;q<8;q++){const hx=H(q*7.3+M.m);W.parts.push({x:S.x+(hx-.5)*M.w*1.3,y:FY-3,vx:(hx-.5)*260,vy:-100-H(q*3.1)*160,kind:'dust',t0:tm,live:1})}}}
    if(S.landed>0)st+=.012*Math.sin(2*Math.PI*.45*(tm-S.landed-1))*smo(S.landed+.8,S.landed+1.4,tm);
    ek=ek*(1-.94*smo(CONTACT+.4,d.w0+.4,tm));}
   else{ if(A==='B'&&tm>3.6)ek=M.ek*.45; }
   const c=2*z*Math.sqrt(k);if(isV)W.krat=k/(6*S.G);
   const inert=-S.xa*1.1/M.h;
   const alpha=-k*(S.th-tht)-c*S.om+S.G*Math.sin(S.th)+inert+F;
   S.om+=alpha*dt;S.th+=S.om*dt;
   if(S.landed>0){S.om*=Math.pow(.02,dt)}
   if(S.th>Math.PI/2){S.th=Math.PI/2;if(S.landed<0){S.landed=tm;W.ev.push({k:'land',t:tm,x:S.x,id:S.id});const J=Math.abs(S.om)*M.m;W.fl.v+=J*3.2;W.lamp.v+=J*.012;S.sv-=Math.abs(S.om)*.06;
     if(M.m>1.2&&W.cup.fall<0){W.cup.fall=tm+.04;W.cup.fallDir=1;W.ev.push({k:'cupfall',t:tm+.04,x:W.cup.x})}
     for(let q=0;q<10;q++){const hx=H(q*7.3+M.m);W.parts.push({x:S.x+M.w*(.2+hx*.9),y:FY-3,vx:(hx-.3)*220,vy:-120-H(q*3.1)*200,kind:'dust',t0:tm,live:1})}}
    S.om=-S.om*.2}
   if(S.th<-.6){S.th=-.6;S.om=0}
   const cs=2*zs*Math.sqrt(ks);S.sv+=(-ks*(S.s-st)-cs*S.sv)*dt;S.s+=S.sv*dt;if(S.s<.3){S.s=.3;S.sv=-S.sv*.2}S.s=Math.min(1.2,S.s);
   let kb=160,bt=0;if(isV&&DRUG[S.id].mode==='sag'){const Dc2=smo(DRUG[S.id].c0,DRUG[S.id].c0+.3,tm);kb=160*(1-.7*Dc2);bt=DRUG[S.id].flop*Dc2}
   const cb=2*.28*Math.sqrt(kb);S.bv+=(-kb*(S.b-bt)-cb*S.bv-S.xa*.5/M.h-alpha*.012)*dt;S.b+=S.bv*dt;
   // ears: point masses that follow the corner (follow-through); a scripted ear task overrides the target
   for(const sd of[-1,1]){const e=S.ears[sd<0?0:1];const r=earRest(S,sd);const cn=corner(S,sd);
    let tx=r[0],ty=r[1],kk=ek,zz=M.ez,len=M.el*M.h*(isV?1-.4*W.dd:1);
    const task=(!isV&&sd>0&&P.ear)?P.ear:(isV&&sd<0&&P.ear)?P.ear:null;
    if(task){tx=task.x;ty=task.y;kk=M.ek*task.k;zz=.75;len=Math.max(len,Math.hypot(tx-cn[0],ty-cn[1])+4)}
    stepPoint(e,tx,ty,kk,zz,task?0:260,cn,len,dt)}
   if(S.id==='O')for(const sd of[-1,1]){const l=S.locks[sd<0?0:1];const cn=corner(S,sd);const mid=L2W(S,sd*(M.w*(1+(1-S.s)*.55)/2+7),S.M.h*S.s*.5);
    stepPoint(l,mid[0],mid[1]+30,70,.22,700,[cn[0]+sd*4,cn[1]-6],M.h*.68,dt)}
   {const an=L2W(S,M.w*(1+(1-S.s)*.55)/2,M.h*S.s*.45);stepPoint(S.dang,an[0]+4,an[1]+26,40,.2,600,an,30,dt)}
   if(S.id==='R'){const sl=isV?smo(DRUG.R.w0,DRUG.R.c0+.6,tm):0;const cn=L2W(S,M.w*(1+(1-S.s)*.55)/2,M.h*S.s*(.88-.2*sl));
    const tg=L2W(S,M.w*(1+(1-S.s)*.55)/2+8,M.h*S.s*(.62-.25*sl));stepPoint(S.tail,tg[0],tg[1],90*(1-.8*sl),.25,500,cn,28+40*sl,dt)}
  }
  // ---- doer's prop and what falls from it ----
  const et=SA.ears[1];const tilt=PA.tilt;W.tilt=tilt;
  const mx=et.x+Math.sin(tilt)*18,my=et.y-Math.cos(tilt)*18;W.vialTip=[et.x,et.y];
  if(dt>0){const spawn=(vx,vy,kind,j)=>W.parts.push({x:mx+(H(j)-.5)*4,y:my,vx:vx+et.vx*.5,vy:vy+et.vy*.4,kind,t0:tm,live:1});
   if(A==='R'){for(const d of[1.47,1.70,1.93])if(Math.abs(tm-d)<DT/2)spawn(0,40,'drop',i)}
   if(A==='B'&&tm>1.43&&tm<1.56&&i%2===0)spawn((H(i)-.5)*40,20,'grain',i)
   if(A==='I'&&tm>1.47&&tm<1.6&&i%3===0)spawn(-30+(H(i)-.5)*240,-60-H(i+5)*140,'drop',i)
   if(A==='O'&&tm>1.36&&tm<1.78&&i%2===0)spawn(0,60,'thread',i)}
  for(const p of W.parts){if(!p.live||p.kind==='stain'||p.kind==='in')continue;p.vy+=GR*dt;p.x+=p.vx*dt;p.y+=p.vy*dt;
   if(p.kind==='dust'){if(tm-p.t0>.9)p.live=0;p.vy-=GR*dt*.85;p.vx*=Math.pow(.2,dt);continue}
   const inCup=!W.cup.held&&Math.abs(p.x-W.cup.x)<CUPW/2-3&&p.y>TY-CUPH+4&&p.y<TY;
   if(inCup){W.ev.push({k:'in',t:tm,x:p.x,kind:p.kind});p.kind='in';W.cup.tint=Math.min(1,W.cup.tint+.18);p.live=0}
   else if(p.y>TY&&p.x>TX0&&p.x<TX1){p.y=TY;p.kind='stain';W.ev.push({k:'splat',t:tm,x:p.x})}
   else if(p.y>FY){p.y=FY;p.kind='stain'}}
  // ---- floor and lamp ----
  W.fl.v+=(-900*W.fl.y-2*.25*30*W.fl.v)*dt;W.fl.y+=W.fl.v*dt;
  W.lamp.v+=(-(GR/LAMPL)*Math.sin(W.lamp.p)-.9*W.lamp.v)*dt;W.lamp.p+=W.lamp.v*dt;
  // spoon taps from Belindo jolt the boards a little
  if(A==='B'&&dt>0){for(const d of[1.6,1.75,1.9])if(Math.abs(tm-d)<DT/2){W.fl.v+=18;W.lamp.v+=.03}}
  if(i%2===0)W.tr.push({t:tm,ax:SA.x,vx:SV.x,om:SV.om,th:SV.th,k:SV.k,kr:W.krat||1,cx:W.cup.x});
 }
 W.mouth=topC(SV);W.tint=W.parts.reduce((a,p)=>a+(p.kind==='in'?1:0),0);
 return W}

// ---------------- drawing -----------------
function bodyPts(S){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s,N=12,pts=[];
 for(let i=0;i<=N;i++){const u=i/N;pts.push(L2W(S,-ww/2*prof(S.id,u),u*hh))}
 for(let i=1;i<N;i++){const u=i/N;pts.push(L2W(S,-ww/2*prof(S.id,1)+u*ww*prof(S.id,1),hh))}
 for(let i=N;i>=0;i--){const u=i/N;pts.push(L2W(S,ww/2*prof(S.id,u),u*hh))}return pts}
// carried tags, drawn in this deed's language: anything that hangs is a spring point (S.dang), anything worn moves with the body frame
function tagsIn(g,S,W){const M=S.M,id=S.id,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;
 if(has(id,'greyed')){g.fillStyle='rgba(120,120,125,.38)';g.fillRect(0,0,1920,1080)}
 if(has(id,'blot')){const c=L2W(S,-ww*.18,hh*.55);g.fillStyle='rgba(28,30,62,.85)';g.beginPath();g.ellipse(c[0],c[1],ww*.11+6,hh*.07+5,S.th,0,7);g.fill();
  g.beginPath();g.ellipse(c[0]+ww*.1,c[1]+9,5,4,0,0,7);g.fill()}
 if(has(id,'torn')){g.strokeStyle='#3a2c1c';g.lineWidth=3;g.beginPath();for(let k=0;k<=6;k++){const p=L2W(S,ww*.32+(k%2?7:-7),hh*(.25+.07*k));k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke();
  g.fillStyle='#fbf7ee';for(let k=0;k<4;k++){const p=L2W(S,ww*.34,hh*(.22+.04*k));g.fillRect(p[0]+k*3,p[1]+k*4,4,4)}}}
function tagsOut(g,S,W){const M=S.M,id=S.id,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;
 const loop=(u,col,wd)=>{g.strokeStyle=col;g.lineWidth=wd;g.beginPath();for(let k=0;k<=10;k++){const v=k/10;const p=L2W(S,(-ww/2*prof(id,u)-2)+(ww*prof(id,u)+4)*v,hh*u+Math.sin(Math.PI*v)*-4);k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()};
 if(has(id,'rope')){loop(.45,'#8a6a3a',5);loop(.62,'#8a6a3a',5);const an=L2W(S,ww/2*prof(id,.45)+2,hh*.45);
  g.strokeStyle='#8a6a3a';g.lineWidth=5;g.beginPath();g.moveTo(an[0],an[1]);g.quadraticCurveTo(an[0]+10,(an[1]+S.dang.y)/2,S.dang.x,S.dang.y);g.stroke()}
 if(has(id,'gag'))loop(.86,'#3c3c40',8);
 if(has(id,'cinched'))loop(.82,'#5a4026',4);
 if(has(id,'tag')){const an=L2W(S,ww*.18,hh*.72);g.strokeStyle='#222';g.lineWidth=1.5;const tx=an[0]+(S.dang.x-an[0])*.25,ty=an[1]+22;g.beginPath();g.moveTo(an[0],an[1]);g.lineTo(tx,ty);g.stroke();
  g.save();g.translate(tx,ty);g.rotate(S.th+(S.dang.x-an[0]-4)*.01);g.fillStyle='#f4eedc';g.strokeStyle='#555';g.fillRect(-12,0,24,16);g.strokeRect(-12,0,24,16);g.restore();
  g.fillStyle='#b00';g.beginPath();g.arc(an[0],an[1],3,0,7);g.fill()}
 if(has(id,'coins')){const b=L2W(S,ww*.5+12,0);g.fillStyle='#c9a646';g.strokeStyle='#6d5418';g.lineWidth=1.5;for(let k=0;k<4;k++){g.beginPath();g.ellipse(b[0]+(k%2)*3,b[1]-4-k*6,10,4,0,0,7);g.fill();g.stroke()}}}
function bodyPath(g,S){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s,N=12,pts=[];
 for(let i=0;i<=N;i++){const u=i/N;pts.push(L2W(S,-ww/2*prof(S.id,u),u*hh))}
 const dip=S.id==='I'?.16:S.id==='B'?.03:.06;
 for(let i=1;i<N;i++){const u=i/N;const lx=-ww/2*prof(S.id,1)+u*ww*prof(S.id,1);pts.push(L2W(S,lx,hh*(1-dip*Math.sin(Math.PI*u))))}
 for(let i=N;i>=0;i--){const u=i/N;pts.push(L2W(S,ww/2*prof(S.id,u),u*hh))}
 g.beginPath();g.moveTo(pts[0][0],pts[0][1]);
 for(let i=1;i<pts.length-1;i++){const mxp=(pts[i][0]+pts[i+1][0])/2,myp=(pts[i][1]+pts[i+1][1])/2;g.quadraticCurveTo(pts[i][0],pts[i][1],mxp,myp)}
 g.lineTo(pts[pts.length-1][0],pts[pts.length-1][1]);g.closePath();return pts}
function band(g,S,u0,u1,inset){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s,N=6;g.beginPath();
 for(let i=0;i<=N;i++){const u=u0+(u1-u0)*i/N;const p=L2W(S,-ww/2*prof(S.id,u)-inset,u*hh);i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}
 for(let i=N;i>=0;i--){const u=u0+(u1-u0)*i/N;const p=L2W(S,ww/2*prof(S.id,u)+inset,u*hh);g.lineTo(p[0],p[1])}g.closePath()}
function ear(g,S,sd,fill,line){const M=S.M,bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s,e=S.ears[sd<0?0:1];
 const a=L2W(S,sd*ww/2*prof(S.id,1)*(S.id==='I'?.72:.45),hh*(S.id==='I'?.9:.96)),b=L2W(S,sd*ww/2*prof(S.id,.8)+(S.id==='I'?sd*3:0),hh*(S.id==='I'?.9:.8)),cn=corner(S,sd);
 const mx=(cn[0]*2+e.x)/3,my=(cn[1]*2+e.y)/3;
 g.beginPath();g.moveTo(a[0],a[1]);g.quadraticCurveTo(mx+(a[0]-cn[0])*.25,my+(a[1]-cn[1])*.25,e.x,e.y);
 g.quadraticCurveTo(mx+(b[0]-cn[0])*.25,my+(b[1]-cn[1])*.25,b[0],b[1]);g.closePath();g.fillStyle=fill;g.fill();g.strokeStyle=line;g.lineWidth=2.5;g.stroke();
 if(S.id==='I'){g.strokeStyle='rgba(60,45,25,.55)';g.lineWidth=1.5;for(const f of[.35,.65]){const sx=a[0]+(b[0]-a[0])*f,sy=a[1]+(b[1]-a[1])*f;g.beginPath();g.moveTo(sx,sy);g.quadraticCurveTo(mx,my,e.x+(f-.5)*8,e.y-4);g.stroke()}}}

function drawSack(g,S,W,isV,lampX){const M=S.M,id=S.id;
 const D=isV?W.dd:0;
 // contact shadow
 const base=L2W(S,0,0);const lyingK=Math.sin(Math.abs(S.th));
 g.fillStyle='rgba(0,0,0,.38)';g.beginPath();g.ellipse(base[0]+lyingK*M.h*.5*Math.sign(S.th||1),FY+4,M.w*.62+lyingK*M.h*.35,13,0,0,7);g.fill();
 const fill=M.col,line='#4a3b28';
 // back ear (away from lamp) first
 const backSd=S.role==='A'?-1:1;ear(g,S,backSd,id==='I'?'#7d6a48':M.dk,line);
 // body
 const pts=bodyPath(g,S);let x0=1e9,x1=-1e9;for(const p of pts){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0])}
 const gr=g.createLinearGradient(x0,0,x1,0);const lit=S.role==='A';
 gr.addColorStop(0,lit?M.dk:fill);gr.addColorStop(.55,fill);gr.addColorStop(1,lit?fill:M.dk);
 g.fillStyle=gr;g.fill();
 g.save();bodyPath(g,S);g.clip();
 // drug: a grey-green cast spreads down from the mouth
 if(D>0){const u=W.dd;const tc=topC(S),bc=L2W(S,0,0);const lg=g.createLinearGradient(tc[0],tc[1],bc[0],bc[1]);
  const f=clamp(0,1,(W.tm-CONTACT)/1.4);lg.addColorStop(0,`rgba(92,120,96,${.55*u})`);lg.addColorStop(clamp(.01,.98,f),`rgba(92,120,96,${.38*u})`);lg.addColorStop(Math.min(1,f+.02),'rgba(92,120,96,0)');
  g.fillStyle=lg;g.fillRect(x0-50,0,x1-x0+100,1080)}
 // attributes
 if(id==='B'){g.fillStyle='#2a2622';band(g,S,.36,.44,4);g.fill();
  const c=L2W(S,0,M.h*S.s*.64);const r=M.w*.15;g.strokeStyle='rgba(110,80,40,.75)';g.lineWidth=4;g.beginPath();g.arc(c[0],c[1],r,0,7);g.stroke();
  g.save();g.translate(c[0],c[1]);g.rotate(S.th);g.lineWidth=3;g.beginPath();g.moveTo(0,r*.75);g.lineTo(0,-r*.75);
  for(let k=0;k<4;k++){const y=-r*.55+k*r*.3;g.moveTo(0,y+8);g.lineTo(-11,y-2);g.moveTo(0,y+8);g.lineTo(11,y-2)}g.stroke();g.restore()}
 if(id==='R'){const sl=isV?smo(DRUG.R.w0,DRUG.R.c0+.6,W.tm):0;g.fillStyle='#6e3a33';band(g,S,.8-.2*sl,.98-.2*sl,6);g.fill();
  g.strokeStyle='rgba(30,10,8,.45)';g.lineWidth=2;for(let k=1;k<4;k++){band(g,S,.8-.2*sl+k*.045,.8-.2*sl+k*.045+.004,6);g.stroke()}}
 // fold lines: sag shows as creases
 tagsIn(g,S,W);
 const sag=clamp(0,1,(1-S.s)/.35);if(sag>.02){g.strokeStyle=`rgba(70,52,30,${.55*sag})`;g.lineWidth=2.5;
  for(const u of[.22,.4,.58]){const bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;g.beginPath();for(let k=0;k<=8;k++){const v=k/8;const p=L2W(S,-ww/2+ww*v,u*hh+Math.sin(Math.PI*v)*(-6*sag)+Math.sin(v*9+u*20)*2*sag);k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke()}}
 g.restore();
 bodyPath(g,S);g.strokeStyle=line;g.lineWidth=3;g.stroke();
 // top seam stitch
 {const bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;g.setLineDash([7,6]);g.strokeStyle='rgba(74,59,40,.7)';g.lineWidth=2;g.beginPath();
  for(let k=0;k<=8;k++){const v=k/8;const p=L2W(S,(-ww/2+ww*v)*.86,hh*(.9-(id==='I'?.12:.04)*Math.sin(Math.PI*v)));k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])}g.stroke();g.setLineDash([])}
 if(id==='R'){const sl=isV?smo(DRUG.R.w0,DRUG.R.c0+.6,W.tm):0;const cn=L2W(S,M.w*(1+(1-S.s)*.55)/2+3,M.h*S.s*(.95-.2*sl)),cn2=L2W(S,M.w*(1+(1-S.s)*.55)/2+3,M.h*S.s*(.8-.2*sl));
  g.fillStyle='#6e3a33';g.strokeStyle='#3a1c18';g.lineWidth=2;g.beginPath();g.moveTo(cn[0],cn[1]);g.quadraticCurveTo(S.tail.x+8,(cn[1]+S.tail.y)/2,S.tail.x,S.tail.y);g.lineTo(S.tail.x-8,S.tail.y-4);g.quadraticCurveTo(cn2[0],cn2[1]+8,cn2[0],cn2[1]);g.closePath();g.fill();g.stroke()}
 // front ear
 ear(g,S,-backSd,id==='I'?'#b8a27a':fill,line);
 tagsOut(g,S,W);
 // Ogiva's wig: a cap and two locks on springs
 if(id==='O'){if(has('O','wig')){const c=topC(S);g.save();g.translate(c[0],c[1]);g.rotate(.35);g.translate(-c[0]+16,-c[1]+8);drawSack.wig(g,S,M);g.restore()}else drawSack.wig(g,S,M)}
}
drawSack.wig=function(g,S,M){{const bul=1+(1-S.s)*.55,ww=M.w*bul,hh=M.h*S.s;g.fillStyle='#7a3b8f';g.strokeStyle='#3d1848';g.lineWidth=2.5;
  for(const sd of[-1,1]){const l=S.locks[sd<0?0:1];const a=L2W(S,sd*(ww/2+10),hh+4),b=L2W(S,sd*ww*.15,hh*.9),m=L2W(S,sd*(ww/2+16),hh*.6),q=L2W(S,sd*(ww/2-10),hh*.5);
   g.beginPath();g.moveTo(a[0],a[1]);g.quadraticCurveTo(m[0],m[1],l.x+sd*6,l.y);g.lineTo(l.x-sd*10,l.y-6);g.quadraticCurveTo(q[0],q[1],b[0],b[1]);g.closePath();g.fill();g.stroke()}
  g.beginPath();const c0=L2W(S,-ww/2-10,hh*.86);g.moveTo(c0[0],c0[1]);
  for(let k=1;k<=10;k++){const v=k/10;const p=L2W(S,-ww/2-10+(ww+20)*v,hh*.86+Math.sin(Math.PI*v)*(hh*.14+20));g.lineTo(p[0],p[1])}
  for(let k=10;k>=0;k--){const v=k/10;const p=L2W(S,-ww/2-6+(ww+12)*v,hh*.84+Math.sin(Math.PI*v)*hh*.05);g.lineTo(p[0],p[1])}g.closePath();g.fill();g.stroke();
  g.strokeStyle='rgba(30,8,40,.5)';g.lineWidth=1.5;for(const sd of[-1,1]){const l=S.locks[sd<0?0:1];const a=L2W(S,sd*(ww/2+2),hh*.95);g.beginPath();g.moveTo(a[0],a[1]);g.quadraticCurveTo(a[0]+sd*6,(a[1]+l.y)/2,l.x-sd*4,l.y-8);g.stroke()}}
}

function drawProp(g,A,W){const e=W.vialTip;if(!e)return;g.save();g.translate(e[0],e[1]);g.rotate(W.tilt);
 if(A==='B'){// big spoon heaped with white powder
  g.strokeStyle='#8a8a90';g.lineWidth=6;g.beginPath();g.moveTo(0,22);g.lineTo(0,-8);g.stroke();
  g.fillStyle='#b8b8c0';g.beginPath();g.ellipse(0,-18,13,10,0,0,7);g.fill();
  if(W.tm<1.47){g.fillStyle='#fbf7ee';g.beginPath();g.ellipse(0,-24,10,7,0,0,7);g.fill()}}
 else{// small dark vial with a green drug
  const s=A==='O'?1.15:A==='I'?1.3:1.35;g.scale(s,s);
  g.fillStyle='#2d3a30';g.strokeStyle='#0f1512';g.lineWidth=2;g.beginPath();g.roundRect(-9,-14,18,30,4);g.fill();g.stroke();
  g.fillStyle='#7fbf5a';g.fillRect(-6,-2,12,14);g.fillStyle='#2d3a30';g.fillRect(-4,-21,8,8);
  if(W.tilt<.5){g.fillStyle='#8a5a32';g.fillRect(-5,-26,10,7)}}
 g.restore()}

function drawCup(g,W){const c=W.cup;const lie=c.held?0:Math.abs(Math.sin(c.rot));
 g.save();g.translate(c.x,c.y-(CUPH/2*(1-lie)+CUPW/2*lie));g.rotate(c.rot);
 g.fillStyle='#ece6d8';g.strokeStyle='#4e463a';g.lineWidth=3;
 g.beginPath();g.moveTo(-CUPW/2,-CUPH/2);g.lineTo(CUPW/2,-CUPH/2);g.lineTo(CUPW/2-5,CUPH/2);g.lineTo(-CUPW/2+5,CUPH/2);g.closePath();g.fill();g.stroke();
 g.fillStyle='#b9b2a2';g.fillRect(-CUPW/2+3,CUPH/2-8,CUPW-6,5);
 g.beginPath();g.arc(CUPW/2+3,-1,11,-1.3,1.3);g.lineWidth=5;g.stroke();
 const lv=c.level*(c.fall>0&&W.tm>c.fall+.1?.1:1);const tint=Math.min(1,W.tint/3);
 if(lv>.02){g.fillStyle=`rgb(${110-40*tint|0},${78+70*tint|0},${44+16*tint|0})`;
  g.beginPath();g.ellipse(0,-CUPH/2+1,CUPW/2-2,6,0,0,7);g.fill();g.strokeStyle='#4e463a';g.lineWidth=2;g.stroke()}
 // the dose sits as a green swirl on the surface
 if(tint>0&&lv>.02){g.strokeStyle='rgba(150,220,100,.95)';g.lineWidth=2.5;g.beginPath();g.ellipse(2,-CUPH/2+1,9*tint+4,3,0,0,5.5);g.stroke()}
 g.restore();
 if(c.held&&c.rot>.7&&c.level>.02&&W.mouth){const cy=c.y-CUPH/2,co=Math.cos(c.rot),sn=Math.sin(c.rot);
  const rx=c.x+CUPW/2*co+CUPH/2*sn,ry=cy+CUPW/2*sn-CUPH/2*co;const m=W.mouth;
  g.strokeStyle='rgba(110,150,70,.95)';g.lineWidth=7;g.lineCap='round';g.beginPath();g.moveTo(rx,ry);g.quadraticCurveTo(rx+6,(ry+m[1])/2,m[0]-6,m[1]+4);g.stroke();g.lineCap='butt'}
 if(c.fall>0&&W.tm>c.fall+.12){const u=smo(c.fall+.12,c.fall+.9,W.tm);g.fillStyle='rgba(110,150,70,.9)';g.beginPath();g.ellipse(c.x+34+22*u,TY+1,10+28*u,4,0,0,7);g.fill();
  g.strokeStyle='rgba(110,150,70,.85)';g.lineWidth=4;g.beginPath();g.moveTo(TX1+4,TY+3);g.lineTo(TX1+5,TY+3+(FY-TY-6)*u);g.stroke()}
}

function drawRoom(g,W){const lp=W.lamp.p;const bx=LAMPX+Math.sin(lp)*LAMPL,by=Math.cos(lp)*LAMPL;
 // wall
 let gr=g.createLinearGradient(0,0,0,FY);gr.addColorStop(0,'#14131a');gr.addColorStop(1,'#272029');g.fillStyle=gr;g.fillRect(0,0,1920,FY);
 g.fillStyle='rgba(255,255,255,.025)';for(let x=0;x<1920;x+=48)g.fillRect(x,0,18,FY-120);
 g.fillStyle='#1d1715';g.fillRect(0,FY-120,1920,120);g.fillStyle='#2b211c';g.fillRect(0,FY-124,1920,6);
 // floor boards
 gr=g.createLinearGradient(0,FY,0,1080);gr.addColorStop(0,'#3a2a1f');gr.addColorStop(1,'#1c1510');g.fillStyle=gr;g.fillRect(0,FY,1920,280);
 g.strokeStyle='rgba(0,0,0,.35)';g.lineWidth=2;for(let k=-12;k<14;k++){g.beginPath();g.moveTo(960+k*60,FY);g.lineTo(960+k*190,1080);g.stroke()}
 // lamp light pool (moves with the pendulum)
 const lg=g.createRadialGradient(bx,by+40,10,bx,by+300,760);lg.addColorStop(0,'rgba(255,214,150,.42)');lg.addColorStop(.5,'rgba(255,190,120,.14)');lg.addColorStop(1,'rgba(255,190,120,0)');
 g.fillStyle=lg;g.fillRect(0,0,1920,1080);
 const fp=g.createRadialGradient(bx*1.0,FY+30,10,bx,FY+30,520);fp.addColorStop(0,'rgba(255,205,140,.25)');fp.addColorStop(1,'rgba(255,205,140,0)');g.fillStyle=fp;g.fillRect(0,FY-40,1920,320);
 // cord + shade
 g.strokeStyle='#0c0b0c';g.lineWidth=3;g.beginPath();g.moveTo(LAMPX,0);g.lineTo(bx,by);g.stroke();
 g.save();g.translate(bx,by);g.rotate(-lp);g.fillStyle='#3d3226';g.beginPath();g.moveTo(-14,0);g.lineTo(14,0);g.lineTo(46,44);g.lineTo(-46,44);g.closePath();g.fill();
 g.fillStyle='#ffe2a8';g.beginPath();g.ellipse(0,44,40,8,0,0,7);g.fill();g.restore();
 // table
 g.fillStyle='rgba(0,0,0,.35)';g.beginPath();g.ellipse((TX0+TX1)/2,FY+4,(TX1-TX0)*.6,12,0,0,7);g.fill();
 g.fillStyle='#4a2f1e';g.fillRect(TX0+16,TY+10,12,FY-TY-10);g.fillRect(TX1-28,TY+10,12,FY-TY-10);
 g.fillStyle='#6a4428';g.fillRect(TX0-6,TY,TX1-TX0+12,13);g.fillStyle='#8a5c36';g.fillRect(TX0-6,TY,TX1-TX0+12,3);
 g.fillStyle='#3b2618';g.fillRect(TX0+4,TY+13,TX1-TX0-8,10)}

DEED({n:2,key:'drugging',title:'Drugging',scion:41,lineage:'Secondary Dynamics — Inertia and Restraint',
 op:'The doer doses a cup and pushes it over; once the victim drinks, its own spring constants are lowered until gravity wins and it wobbles, sags and tips over asleep.',
 made:'Each sack is a lean pendulum, a squash spring and a bend spring with ears, wig locks and shawl tail hung on point-mass springs; the room is a table, a cup, and a lamp on a pendulum cord over the boards. The drug is a green liquid (powder from Belindo) that falls as ballistic drops into the cup and tints the victim from the top down.',
 moved:'Scripted base positions and ear targets are the only primary impulses; lean, squash, bend, ears, hair and lamp all follow through by fixed-step integration from t=0. Drinking lowers the victim\'s stiffness and damping below its own weight, so the wobble, the sag, the fall and the floor jolt that knocks the cup over all come out of the solver.',
 contact:CONTACT,
 leaves:{A:[],V:['drowsy']},
 // layers: 'bg' = room, table, stains and the cup while it stands on the table; 'V' = victim, its shadow, the cup while held, landing dust;
 // 'A' = doer, its shadow, the vial/spoon and every drop or grain it lets fall. Composite bg -> V -> A (the full frame draws in that order).
 draw(g,t,A,V,K,opt){opt=opt||{};const L=opt.layer;const W=simulate(t,A,V,opt.carry);W.tm=t;
  g.save();g.translate(CAM.cx,CAM.cy);g.scale(CAM.s,CAM.s);g.translate(-CAM.cx,-CAM.cy);g.translate(0,W.fl.y*.6);
  if(!L||L==='bg'){drawRoom(g,W);
   for(const p of W.parts)if(p.kind==='stain'){g.fillStyle='rgba(90,120,62,.8)';g.beginPath();g.ellipse(p.x,p.y,4,2,0,0,7);g.fill()}
   if(!W.cup.held)drawCup(g,W)}
  if(!L||L==='V'){drawSack(g,W.SV,W,true);if(W.cup.held)drawCup(g,W);
   for(const p of W.parts)if(p.live&&p.kind==='dust'){const a=1-(t-p.t0)/.9;g.fillStyle=`rgba(251,247,238,${.5*a})`;g.beginPath();g.arc(p.x,p.y,5+12*(1-a),0,7);g.fill()}}
  if(!L||L==='A'){drawSack(g,W.SA,W,false);drawProp(g,A,W);
   for(const p of W.parts){if(!p.live)continue;
    if(p.kind==='drop'||p.kind==='thread'){g.fillStyle='#8fd05e';g.beginPath();g.ellipse(p.x,p.y,p.kind==='thread'?2.5:4.5,6,0,0,7);g.fill()}
    if(p.kind==='grain'){g.fillStyle='#fbf7ee';g.fillRect(p.x-2,p.y-2,4,4)}}}
  g.restore()},
 marks(t,A,V,K,opt){const W=simulate(t,A,V,opt&&opt.carry);const box=S=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
   for(const p of bodyPts(S)){const X=CAM.cx+(p[0]-CAM.cx)*CAM.s,Y=CAM.cy+(p[1]+W.fl.y*.6-CAM.cy)*CAM.s;x0=Math.min(x0,X);x1=Math.max(x1,X);y0=Math.min(y0,Y);y1=Math.max(y1,Y)}
   return {x:Math.round(x0),y:Math.round(y0),w:Math.round(x1-x0),h:Math.round(y1-y0)}};
  return {A:box(W.SA),V:box(W.SV)}},
 // sound: every event read off the same simulation the picture uses. Deed voice = the victim's spring itself:
 // one grain at each turning point of its lean, pitched by sqrt(k) — the drug is heard as the pitch falling and the beats slowing.
 sound(ac,out0,t0,A,V,K){const out=ac.createGain();out.gain.value=1.4;out.connect(out0);const S=K.SND,W=simulate(6,A,V),H=K.hash;const px=x=>clamp(-1,1,(CAM.cx+(x-CAM.cx)*CAM.s)/960-1);
  const at=t=>t0+t;const say=(id,t,gs,amt,x)=>S.say(ac,out,id,at(t),gs,amt,px(x));
  const SA=W.SA,SV=W.SV,MA=MAT[A],MV=MAT[V];
  // doer footsteps from distance walked
  const stride={R:52,B:74,I:40,O:36}[A];let acc=0;for(let i=1;i<W.tr.length;i++){acc+=Math.abs(W.tr[i].ax-W.tr[i-1].ax);if(acc>stride){acc=0;say(A,W.tr[i].t,'step',A==='I'?.6:.9,W.tr[i].ax)}}
  // the prop comes up
  say(A,{R:1.12,B:1.02,I:1.2,O:1.0}[A],'tick',.8,TX0);
  // dosing: drops plink into the cup, grains hiss, Ogiva's thread trickles, missed drops splat on the board
  let last=-1;for(const e of W.ev){if(e.k==='in'&&e.t-last>.03){last=e.t;
    if(A==='B')S.cloud(ac,out,at(e.t),.05,200,{bp:4200,a:.03,d:[.005,.02],spread:.1});
    else{S.grain(ac,out,at(e.t),{f:1250+H(e.t*91)*500,glide:-.55,d:.07,a:.16,pan:px(e.x),att:.08});S.grain(ac,out,at(e.t)+.01,{f:300,glide:-.4,d:.05,a:.07,pan:px(e.x)})}}
   if(e.k==='splat')S.grain(ac,out,at(e.t),{bp:900,q:3,d:.03,a:.08,pan:px(e.x)})}
  if(A==='B'){S.cloud(ac,out,at(1.42),.14,160,{bp:3500,a:.03,d:[.01,.03],spread:.2});for(const d of[1.6,1.75,1.9])S.grain(ac,out,at(d),{f:2650,d:.09,a:.14,pan:px(cxA),att:.04});
   S.cloud(ac,out,at(1.55),.37,90,{bp:1600,q:4,a:.02,d:[.02,.05],spread:.1})}
  if(A==='O')S.cloud(ac,out,at(1.36),.44,140,{bp:5200,q:3,a:.025,d:[.01,.03],spread:.05});
  // the push: cup slides across the board
  const p0={R:2.0,B:1.98,I:1.86,O:1.92}[A],p1={R:2.32,B:2.22,I:2.2,O:2.14}[A];
  S.cloud(ac,out,at(p0),p1-p0,A==='I'?160:90,{bp:700,q:2,a:A==='I'?.05:.035,d:[.02,.06],spread:.2},u=>A==='I'?Math.pow(1-u,2):Math.sin(Math.PI*u));
  // victim takes the cup
  say(V,2.3,'tick',.8,cxV);
  // CONTACT: the swallow — the shot's loudest event; gulps sized by the drinker
  const gulps={R:[2.7,2.92],B:[2.7,2.79,2.88],I:[2.7,2.94],O:[2.7]}[V],gsz={R:.8,B:1.2,I:.65,O:.55}[V];
  gulps.forEach((g,i)=>{S.grain(ac,out,at(g),{f:{R:150,B:95,I:190,O:260}[V],glide:-.45,d:.13,a:.32*gsz*(i?.7:1),noise:.25,pan:px(SV.xHome),att:.15});
   S.grain(ac,out,at(g)+.02,{bp:500,q:2,d:.08,a:.12*gsz,pan:px(SV.xHome)})});
  S.thump(ac,out,at(CONTACT),.9,70,px(SV.xHome));S.pluck(ac,out,at(CONTACT),{R:57,B:45,I:69,O:81}[V],.12,1.4,px(SV.xHome));
  say(V,CONTACT+.06,'react',.5,SV.xHome);
  // cup set down
  S.grain(ac,out,at(victimPlanTimes(V)),{f:1900,d:.05,a:.12,pan:px(cxV),att:.05});
  // the spring voice: grain at each turning point of the victim's lean, pitch ~ sqrt(k/k0)
  const base={R:330,B:196,I:440,O:660}[V];
  for(let i=1;i<W.tr.length;i++){const a=W.tr[i-1],b=W.tr[i];if(b.t<CONTACT+.3)continue;if((a.om>0)!==(b.om>0)){const amp=Math.min(1,Math.abs(b.th)*6);if(amp<.08)continue;
    S.grain(ac,out,at(b.t),{f:base*Math.sqrt(Math.max(.05,b.kr)),glide:-.08,d:.16,a:.11*amp,type:'triangle',pan:px(b.vx),att:.1})}}
  say(V,DRUG[V].c0,'sink',.9,SV.xHome);
  for(const e of W.ev){if(e.k==='land'){say(V,e.t,'land',V==='B'?.55:.6,e.x);S.cloud(ac,out,at(e.t),.3,50,{bp:300,a:.03,d:[.03,.08]},u=>1-u);
     say(V,e.t+.7,'breathe',1.1,e.x)}
   if(e.k==='cupfall'){S.grain(ac,out,at(e.t+.2),{f:1700,d:.06,a:.13,pan:px(e.x),att:.05});S.grain(ac,out,at(e.t+.3),{f:1500,d:.05,a:.07,pan:px(e.x)});
     S.cloud(ac,out,at(e.t+.25),.8,60,{bp:2200,q:3,a:.018,d:[.02,.05],spread:.1},u=>1-u)}}
  // doer afterwards
  if(A==='R')say('R',3.4,'react',.3,SA.xHome);if(A==='B')say('B',4.4,'sink',.4,SA.xHome);if(A==='I')say('I',3.0,'breathe',.8,SA.xHome);if(A==='O')say('O',3.25,'tick',.7,SA.xHome);
 }
});
})();
