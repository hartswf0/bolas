// 05 · Incitement to Prostitution — SCION 48 · State Machines (characters that can refuse)
// Three explicit machines (DOER, VICTIM, HATCH) run off one event schedule. The picture at t is
// recomputed from scratch: replay every event up to t, each state's action maps (local time, entry pose)
// to a pose. Guards: hatch opens only after VICTIM has been PRESENTED for its dwell; coins fly only while
// HATCH is in PAY; doer TAKE is entered on the first coin event. Refusal is a real state with consequence:
// it shoves the doer back (scaled by mass ratio), leaves plant-marks on the floor and escalates PUSH2.
(function(){
const FY=900, DOOR=1520, HATCH_Y=652, X0V=1110, X0A=580, CONTACT=3.0, CAM=1.45, CX=1100;
const MASS={R:168*122,B:244*214,I:128*98,O:80*184};
const PRICE={R:2,B:4,I:3,O:5};          // coins paid depend on who is presented
const COIN_DT=0.2;

// ---------- machine engine ----------
// events: [{t, s}] sorted. defs[s](u, D, from, ctx) -> pose. Replays from init; returns {state,u,pose}.
function run(events, defs, init, t, ctx){
  let from=init, cur={state:events[0].s,u:0,pose:init};
  for(let i=0;i<events.length;i++){
    const e=events[i]; if(e.t>t) break;
    const nt=i+1<events.length?events[i+1].t:1e9, D=nt-e.t;
    if(t>=nt){ from=defs[e.s](D,D,from,ctx); cur={state:e.s,u:D,pose:from}; continue; }
    const u=t-e.t; return {state:e.s,u,D,pose:defs[e.s](u,D,from,ctx)};
  }
  return cur;
}
const P=(o,p)=>Object.assign({},o,p);

// ---------- character parameters ----------
function ctxFor(A,V,K){
  const a=K.CAST[A], v=K.CAST[V], ratio=MASS[V]/MASS[A];
  const half=(a.w+v.w)/2+6;
  const d1=K.cl(40,150,130/Math.sqrt(ratio));              // first shove distance
  const back={R:60,B:90,I:40,O:55}[V];                       // how far the refusal gives back
  const recoil=K.cl(50,220,{R:90,B:150,I:45,O:80}[V]*Math.sqrt(ratio)); // how far the doer is thrown
  const n=PRICE[V];
  const ev={
    approach:0.4, push1:1.0, shoved:1.12, refuse:1.48, push2:2.02, shoved2:2.3,
    present:2.66, open:2.78, pay:CONTACT, take:CONTACT+0.12,
  };
  ev.shut=CONTACT+n*COIN_DT+0.35; ev.withdraw=ev.shut+0.05; ev.left=ev.shut+0.12; ev.hold=5.35;
  return {A,V,a,v,ratio,half,d1,back,recoil,n,ev,K};
}

// ---------- VICTIM machine ----------
const NEUT={x:0,lean:0,rot:0,sq:1,lift:0,eL:0,eR:0,sag:0,bulge:0,ex:0,turn:0};
function victimDefs(){return{
  IDLE:(u,D,f,c)=>{const b=Math.sin(u*2.1+(c.V.charCodeAt(0)))*0.006;return P(f,{sq:1+b})},
  SHOVED:(u,D,f,c)=>{const K=c.K,k=K.eo(0,0.32,u),j=Math.sin(K.cl(0,1,u/0.36)*Math.PI);
    const tilt=c.V==='I'?0.10:c.V==='O'?0.05:0.035;
    return P(f,{x:X0V+c.d1*k,rot:tilt*j,eL:f.eL+0.6*j,eR:f.eR+0.6*j,sq:1-0.05*j})},
  REFUSE:(u,D,f,c)=>{const K=c.K,s=K.sm(0,0.18,u)*(1-K.sm(D-0.12,D,u)),k=K.eo(0.05,0.3,u);
    const no=Math.sin(u*26)*0.05*s;const base={x:f.x-c.back*k,rot:0,lean:no};
    if(c.V==='R') return P(f,P(base,{rot:-0.16*s+0.05*Math.sin(u*28)*s,sq:1+0.12*s,lift:0,eL:0.9*s,eR:0.9*s,ex:s}));       // plants low, digs in, shakes
    if(c.V==='B') return P(f,P(base,{rot:-0.09*s,sq:1-0.10*s,lift:6*s,bulge:0.08*s,eL:1*s,eR:1*s,ex:s}));                    // heaves up, swells
    if(c.V==='I') return P(f,P(base,{rot:-0.05*s,sag:0.55*s,sq:1+0.25*s,eL:-1,eR:-1,ex:s}));                                 // goes boneless
    return P(f,P(base,{rot:-0.22*s,sq:1-0.03*s,eL:0.4*s,eR:0.4*s,ex:s}));                                                        // O: rigid plank tilt back
  },
  SHOVED2:(u,D,f,c)=>{const K=c.K,k=K.sm(0,0.34,u),j=Math.sin(K.cl(0,1,u/0.36)*Math.PI);
    const ix=c.V==='I'?0.4:0;
    return P(f,{x:K.lerp(f.x,DOOR,k),rot:K.lerp(f.rot,0,k)+0.07*j,sq:K.lerp(f.sq,1,k),lift:K.lerp(f.lift,0,k),bulge:K.lerp(f.bulge,0,k),
      sag:K.lerp(f.sag,ix,k),eL:K.lerp(f.eL,0.3,k),eR:K.lerp(f.eR,0.3,k),ex:K.lerp(f.ex,0,k)})},
  PRESENTED:(u,D,f,c)=>{const K=c.K,k=K.sm(0,0.25,u),q=Math.sin(u*30)*(1-K.sm(0,0.25,u))*0.01;
    const tgt={R:{eL:0.2,eR:0.2,ex:1,sq:1.04},B:{eL:-0.6,eR:-0.6,ex:0,sq:1.0,rot:0.03},I:{eL:-1,eR:-1,sag:0.3,rot:0.04},O:{eL:0.1,eR:0.1,ex:0,sq:0.97}}[c.V];
    const o={rot:q};for(const k2 in tgt){o[k2]=K.lerp(f[k2],tgt[k2],k)+(k2==='rot'?q:0)}return P(f,o)},
  LEFT:(u,D,f,c)=>{const K=c.K,k=K.sm(0,0.9,u);
    const tgt={R:{sq:1.12,eL:-0.4,eR:0.1,ex:2,rot:0.02,turn:0.6},B:{eL:-1,eR:-1,sq:1.05,rot:0.04,sag:0.15,turn:0.5},
               I:{eL:-1,eR:-1,sag:0.75,sq:1.18,rot:0.09,turn:0.7},O:{eL:-0.2,eR:0.3,ex:2,rot:-0.015,turn:0.8}}[c.V];
    const o={};for(const k2 in tgt){o[k2]=K.lerp(f[k2],tgt[k2],k)}
    o.lean=Math.sin(u*1.3)*0.008*k;o.grey=0.55*k;return P(f,o)},
}}
function victimEvents(c){const e=c.ev;return[{t:0,s:'IDLE'},{t:e.shoved,s:'SHOVED'},{t:e.refuse,s:'REFUSE'},{t:e.shoved2,s:'SHOVED2'},{t:e.present,s:'PRESENTED'},{t:e.left,s:'LEFT'}]}
function victimInit(c){return P(NEUT,{x:X0V,eL:c.V==='I'?-1:0,eR:c.V==='I'?-1:0,sag:c.V==='I'?0.25:0})}

// ---------- HATCH machine (world) ----------
function hatchAt(c,t){
  const e=c.ev,K=c.K;
  const evs=[{t:0,s:'SHUT'},{t:e.open,s:'OPEN'},{t:e.pay,s:'PAY'},{t:e.shut,s:'CLOSE'}];
  const defs={SHUT:()=>({o:0,arm:0}),OPEN:(u)=>({o:K.eo(0,0.18,u),arm:0}),
    PAY:(u)=>({o:1,arm:K.sm(0,0.08,u)*(1-K.sm(c.n*COIN_DT,c.n*COIN_DT+0.15,u))}),CLOSE:(u)=>({o:1-K.sm(0,0.2,u),arm:0})};
  return run(evs,defs,{o:0,arm:0},t,c);
}

// ---------- DOER machine ----------
function doerDefs(){return{
  IDLE:(u,D,f,c)=>P(f,{sq:1+Math.sin(u*2.3)*0.005}),
  APPROACH:(u,D,f,c)=>{const K=c.K,tx=X0V-c.half;let k,bob=0,rot=0;
    if(c.A==='R'){k=K.sm(0,D,u);rot=Math.sin(u*9)*0.05;}                               // rocking walk
    else if(c.A==='B'){const st=u/D*3;k=(Math.floor(st)+K.sm(0,1,st%1))/3;if(u>=D)k=1;bob=Math.abs(Math.sin(st*Math.PI))*14;}  // three heavy stomps
    else if(c.A==='I'){k=K.eo(0,D,u);rot=-0.12*Math.sin(K.cl(0,1,u/D)*Math.PI);}        // loose slide
    else {const st=u/D*5;k=(Math.floor(st)+K.sm(0.3,1,st%1))/5;if(u>=D)k=1;bob=Math.sin((st%1)*Math.PI)*10;} // five exact hops
    return P(f,{x:K.lerp(X0A,tx,k),lift:bob,rot,eL:c.A==='I'?-1:0.2,eR:c.A==='I'?-1:0.2})},
  PUSH1:(u,D,f,c,vx)=>{const K=c.K,j=K.sm(0,0.12,u)*(1-K.sm(D-0.1,D,u));
    const lean={R:0.16,B:0.22,I:0.30,O:0.12}[c.A], pw=c.ratio>1.5?1.25:1;
    const nudge=c.A==='R'?Math.abs(Math.sin(u*24))*0.06:0;
    return P(f,{x:vx-c.half+lean*c.a.h*0.5*j,lean:(lean+nudge)*j*pw,sq:1+(c.ratio>1.5?0.1:0.04)*j,rot:0,lift:0,
      eL:c.A==='I'?-1:0.5*j,eR:c.A==='I'?-1:0.5*j})},
  RECOIL:(u,D,f,c,vx)=>{const K=c.K,k=K.eo(0,0.3,u),s=Math.sin(K.cl(0,1,u/0.35)*Math.PI);
    const x=vx-c.half-c.recoil*k;
    return P(f,{x,lean:K.lerp(f.lean,-0.12,s)*(1-k*0.3),rot:-0.08*s,sq:1-0.06*s,eL:c.A==='I'?-1:1*s,eR:c.A==='I'?-1:1*s,
      lift:c.A==='O'?18*s:0})},                       // escalate: wind-up uses the rest of the window below
  PUSH2:(u,D,f,c,vx)=>{const K=c.K,w=K.sm(0,0.22,u),go=K.sm(0.2,0.32,u);
    // identity wind-up then a harder shove that follows the victim to the door
    let sw=0,lean0={R:0.2,B:0.32,I:0.4,O:0.18}[c.A],extra={};
    if(c.A==='B'){extra.bulge=0.10*w*(1-go*0.5);extra.lift=8*w*(1-go);}                       // swells first
    if(c.A==='O'){extra.ex=w*(1-go)*1;}                                                        // wig flick
    if(c.A==='R'){sw=Math.sin(u*30)*0.04*w;}                                                   // shakes herself up
    if(c.A==='I'){extra.rot=0.18*go*(1-K.sm(0.4,0.5,u));}                                      // flops into it
    const xr=f.x-30*w, xc=vx-c.half+12;
    const x=go<1?K.lerp(xr,xc,go):xc;
    return P(f,Object.assign({x,lean:-0.08*w*(1-go)+(lean0+sw)*go*(1-K.sm(D-0.15,D,u)*0.7),sq:1+0.06*go,rot:0,
      eL:c.A==='I'?-1:0.8*w,eR:c.A==='I'?-1:0.8*w,ex:0},extra))},
  WAIT:(u,D,f,c,vx)=>{const K=c.K,k=K.sm(0,0.2,u);
    const kn=u<0.5?Math.max(0,Math.sin(u*Math.PI*2/0.25))*0.12:0;
    return P(f,{x:K.lerp(f.x,DOOR-c.half-14,k),lean:K.lerp(f.lean,0.03,k)+kn,sq:K.lerp(f.sq,1,k),bulge:0,lift:0,rot:0,ex:0,
      eL:c.A==='I'?-1:K.lerp(f.eL,0.9,k),eR:c.A==='I'?-0.6:K.lerp(f.eR,0.9,k)})},             // ears up: ready to receive
  TAKE:(u,D,f,c)=>{const K=c.K,got=K.cl(0,c.n,Math.floor((u+0.12)/COIN_DT));
    const ph=((u+0.12)%COIN_DT)/COIN_DT, j=got>0?Math.exp(-ph*4):0;
    let o={bulge:0.012*got,coins:got};
    if(c.A==='R'){o.rot=-0.05*j;o.sq=1+0.04*j;o.ex=0.5*K.cl(0,1,got/c.n);}                     // bobs per coin, tucks under shawl
    if(c.A==='B'){o.lift=4*j;o.eL=1;o.eR=1;}
    if(c.A==='I'){o.rot=0.06*Math.sin(u*7);o.eL=-1+0.7*j;}                                     // ear flicks to catch
    if(c.A==='O'){o.lean=-0.04;o.eL=0.3;o.eR=1;}                                                // one ear up, precise
    return P(f,o)},
  WITHDRAW:(u,D,f,c)=>{const K=c.K,tx={R:930,B:990,I:860,O:900}[c.A];let k,rot=0,bob=0;
    if(c.A==='R'){k=K.sm(0,D,u);rot=Math.sin(u*8)*0.045;}
    else if(c.A==='B'){const st=u/D*3;k=(Math.floor(st)+K.sm(0,1,st%1))/3;if(u>=D)k=1;bob=Math.abs(Math.sin(st*Math.PI))*10;}
    else if(c.A==='I'){k=K.sm(0,D,u);rot=-0.07;}
    else {const st=u/D*4;k=(Math.floor(st)+K.sm(0.3,1,st%1))/4;if(u>=D)k=1;bob=Math.sin((st%1)*Math.PI)*8;}
    return P(f,{x:K.lerp(f.x,tx,k),rot,lift:bob,lean:0,sq:1,turn:-0.5*k,eL:c.A==='I'?-1:0.1,eR:c.A==='I'?-1:(c.A==='O'?1:0.2)})},
  HOLD:(u,D,f,c)=>P(f,{rot:c.A==='R'?Math.sin(u*3)*0.02:0,lift:0}),
}}
function doerEvents(c){const e=c.ev;return[{t:0,s:'IDLE'},{t:e.approach,s:'APPROACH'},{t:e.push1,s:'PUSH1'},{t:e.refuse,s:'RECOIL'},
  {t:e.push2,s:'PUSH2'},{t:e.present,s:'WAIT'},{t:e.take,s:'TAKE'},{t:e.withdraw,s:'WITHDRAW'},{t:e.hold,s:'HOLD'}]}
function doerInit(c){return P(NEUT,{x:X0A,eL:c.A==='I'?-1:0,eR:c.A==='I'?-1:0,sag:c.A==='I'?0.25:0,coins:0})}

// the doer machine reads the victim's x (coupling through declared state, not pixels)
function doerAt(c,t,vdefs,vev,vinit){
  const ddefs=doerDefs(), wrapped={};
  const vX=tt=>run(vev,vdefs,vinit,tt,c).pose.x;
  const evs=doerEvents(c);
  for(const s in ddefs) wrapped[s]=(u,D,f,cc)=>{
    // absolute time of this state's sample = event time + u
    const et=evs.find(e=>e.s===s).t; return ddefs[s](u,D,f,cc,vX(et+u));};
  return run(evs,wrapped,doerInit(c),t,c);
}

function poses(t,A,V,K){const c=ctxFor(A,V,K);const vdefs=victimDefs(),vev=victimEvents(c),vinit=victimInit(c);
  return {c,vs:run(vev,vdefs,vinit,t,c),ds:doerAt(c,t,vdefs,vev,vinit),hs:hatchAt(c,t).pose};}
// ---------- drawing ----------
function cloth(g,id,x0,y0,x1,y1,pal){const gr=g.createLinearGradient(x0,y0,x1,y1);gr.addColorStop(0,pal[0]);gr.addColorStop(1,pal[1]);return gr}
function earPath(g,cx,cy,side,e,len,wid){
  // e: -1 hang down outside, 0 corner nub, 1 raised up
  let ax,ay;
  if(e>=0){const a=-Math.PI/2+side*(0.6-0.55*e);ax=Math.cos(a);ay=Math.sin(a);}
  else{const m=-e;const a0=-Math.PI/2+side*0.6+(side<0?2*Math.PI:0),a1=Math.PI/2-side*0.10;const A=a0+(a1-a0)*m;
    ax=Math.cos(A);ay=Math.sin(A);}
  const L=len*(1+0.35*Math.max(0,e))*(e<0?1+(-e)*0.6:1);
  const tx=cx+ax*L,ty=cy+ay*L;
  g.beginPath();g.moveTo(cx-side*wid,cy+2);g.quadraticCurveTo(cx+ax*L*0.5+side*4,cy+ay*L*0.5-4,tx,ty);
  g.quadraticCurveTo(cx+ax*L*0.4-side*2,cy+ay*L*0.6+6,cx-side*2,cy+wid*0.9);g.closePath();
}
function drawSack(g,id,p,K,light,tags){
  tags=tags||[];const has=k=>tags.indexOf(k)>=0;
  if(has('drowsy')&&id!=='I')p=P(p,{eL:p.eL*0.5-0.45,eR:p.eR*0.5-0.45,sag:Math.max(p.sag,0.12)});
  const C=K.CAST[id],w0=C.w*(has('emptied')?1.06:1),h0=C.h*(has('emptied')?0.8:1);
  const sq=p.sq*(1+p.bulge*0.3), w=w0*sq*(1+p.sag*0.08), h=h0/sq*(1-p.sag*0.22);
  const by=FY-p.lift;
  // shadow
  g.save();g.fillStyle='rgba(8,5,10,0.45)';g.beginPath();g.ellipse(p.x+20,FY+6,w*0.62,14,0,0,7);g.fill();g.restore();
  g.save();g.translate(p.x,by);g.rotate(p.rot);g.transform(1,0,-p.lean,1,0,0);
  const hw=w/2,dip=p.sag*h*0.28,bl=p.bulge*w0*0.5+p.sag*w*0.06;
  const pal={R:['#cdb38a','#9c8462'],B:['#e8d5ae','#a7926c'],I:['#e2cea5','#9d8a68'],O:['#f0e4c8','#b4a785']}[id];
  const lit=light||1;
  // ears behind body for hanging
  const earLen={R:20,B:26,I:46,O:15}[id], earW={R:10,B:13,I:15,O:8}[id];
  const drawEars=()=>{g.fillStyle=pal[1];
    earPath(g,-hw+4-(p.eL<-0.5?6:0),-h+dip*0.2,-1,p.eL,earLen,earW);g.fill();
    earPath(g,hw-4+(p.eR<-0.5?6:0),-h+dip*0.2,1,p.eR,earLen,earW);g.fill();
    g.strokeStyle='rgba(60,45,30,0.5)';g.lineWidth=1.5;
    earPath(g,-hw+4,-h+dip*0.2,-1,p.eL,earLen,earW);g.stroke();earPath(g,hw-4,-h+dip*0.2,1,p.eR,earLen,earW);g.stroke();};
  const front=(p.eL<-0.5||p.eR<-0.5);
  if(id!=='O'&&!front) drawEars();
  // body
  const body=new Path2D();body.moveTo(-hw+8,0);
  body.quadraticCurveTo(0,6,hw-8,0);
  body.bezierCurveTo(hw+bl+6,-h*0.3,hw+bl+2,-h*0.75,hw-2,-h);
  body.quadraticCurveTo(0,-h+dip*2,-hw+2,-h);
  body.bezierCurveTo(-hw-bl-2,-h*0.75,-hw-bl-6,-h*0.3,-hw+8,0);body.closePath();
  const gr=g.createLinearGradient(-hw-20,-h,hw,0);gr.addColorStop(0,pal[0]);gr.addColorStop(1,pal[1]);
  g.fillStyle=gr;g.fill(body);
  g.save();g.clip(body);
  // turn: shade the side facing away (turned to the wall reads as a dark half)
  if(p.turn){g.fillStyle=`rgba(20,12,18,${Math.abs(p.turn)*0.35})`;if(p.turn>0)g.fillRect(-hw*0.1,-h-10,hw*1.5,h+20);else g.fillRect(-hw*1.4,-h-10,hw*1.3,h+20);}
  // weave
  g.strokeStyle='rgba(90,70,40,0.10)';g.lineWidth=1;for(let yy=-h;yy<0;yy+=7){g.beginPath();g.moveTo(-hw-10,yy);g.lineTo(hw+10,yy+2);g.stroke();}
  // lamp side warm
  const lg=g.createLinearGradient(-hw,0,hw,0);lg.addColorStop(0,`rgba(255,200,120,${0.18*lit})`);lg.addColorStop(1,'rgba(0,0,0,0.18)');g.fillStyle=lg;g.fillRect(-hw-20,-h-20,w+40,h+40);
  // attributes
  if(id==='R'){const bh=h/5, slip=K.cl(0,2,p.ex);const rise=slip<=1?slip*bh*0.4:bh*0.4*(2-slip);const tl=slip>1?(slip-1)*0.25:0;
    g.save();g.translate(0,-h+bh*0.5-rise);g.rotate(tl);g.fillStyle='#6e3a33';g.fillRect(-hw-20,-bh*0.6,w+40,bh*1.2);
    g.fillStyle='rgba(0,0,0,0.25)';g.fillRect(-hw-20,bh*0.45,w+40,4);
    g.strokeStyle='rgba(180,110,90,0.35)';g.lineWidth=2;for(let k=-hw;k<hw;k+=14){g.beginPath();g.moveTo(k,bh*0.6);g.lineTo(k+3,bh*0.6+8);g.stroke();}
    g.restore();}
  if(id==='B'){g.fillStyle='#2a2622';g.fillRect(-hw-20,-h*0.62,w+40,h*0.075);g.fillStyle='#6d6050';g.fillRect(-10,-h*0.62,20,h*0.075);
    const cy=-h*0.3,r=h*0.17;g.strokeStyle='rgba(110,70,40,0.55)';g.lineWidth=4;g.beginPath();g.arc(0,cy,r,0,7);g.stroke();
    g.lineWidth=3;g.beginPath();g.moveTo(0,cy+r*0.8);g.lineTo(0,cy-r*0.75);g.stroke();
    for(let k=0;k<4;k++){const yy=cy-r*0.55+k*r*0.32;g.beginPath();g.ellipse(-r*0.22,yy,r*0.2,r*0.09,-0.6,0,7);g.stroke();g.beginPath();g.ellipse(r*0.22,yy,r*0.2,r*0.09,0.6,0,7);g.stroke();}}
  if(id==='I'){g.strokeStyle='rgba(80,60,40,0.30)';g.lineWidth=2;for(const fx of[-0.45,0.1,0.5]){g.beginPath();g.moveTo(hw*fx,-h*0.85);g.lineTo(hw*fx+6,-h*0.35);g.stroke();}}
  // coin bulge glint
  if(p.coins&&id==='R'){const bh=h/5;for(let k=0;k<p.coins;k++){g.fillStyle='#d9b24a';g.beginPath();g.ellipse(-hw*0.5+k*22,-h+bh*1.1,9,4,0,0,7);g.fill();}}
  // carried damage drawn inside the cloth
  const grey=Math.max(p.grey||0,has('greyed')?1:0);
  if(grey>0){g.globalCompositeOperation='saturation';g.fillStyle=`rgba(128,128,128,${0.85*grey})`;g.fillRect(-hw-30,-h-30,w+60,h+60);
    g.globalCompositeOperation='source-over';g.fillStyle=`rgba(60,60,70,${0.25*grey})`;g.fillRect(-hw-30,-h-30,w+60,h+60);}
  if(has('blot')){g.fillStyle='rgba(18,20,40,0.85)';g.beginPath();g.ellipse(hw*0.3,-h*0.5,w*0.09,h*0.07,0.4,0,7);g.fill();
    g.fillRect(hw*0.3-2,-h*0.5,4,h*0.16);g.beginPath();g.arc(hw*0.3,-h*0.34,4,0,7);g.fill();}
  if(has('torn')){g.strokeStyle='rgba(40,28,18,0.9)';g.lineWidth=3;g.beginPath();for(let k=0;k<6;k++){g.lineTo(-hw*0.55+(k%2?8:-4),-h*0.75+k*h*0.08);}g.stroke();
    g.fillStyle='#fbf7ee';for(let k=0;k<4;k++){g.beginPath();g.arc(-hw*0.55+2,-h*0.3+k*h*0.07,3,0,7);g.fill();}}
  g.restore();
  g.strokeStyle='rgba(60,45,30,0.6)';g.lineWidth=2;g.stroke(body);
  if(has('rope')||has('cinched')){g.strokeStyle='#4a3a24';g.lineWidth=4;
    const bands=has('rope')?[0.32,0.68]:[];if(has('cinched'))bands.push(0.88);
    for(const b of bands){const y=-h*b,ww=hw+bl*0.6+(b>0.85?-4:3);g.beginPath();g.moveTo(-ww,y);g.quadraticCurveTo(0,y+7,ww,y-2);g.stroke();}
    if(has('rope')){g.beginPath();g.moveTo(hw,-h*0.68);g.quadraticCurveTo(hw+14,-h*0.6,hw+8,-h*0.5);g.stroke();}}
  if(has('gag')){g.fillStyle='#c9c3b6';g.beginPath();g.moveTo(-hw-4,-h*0.86);g.lineTo(hw+4,-h*0.88);g.lineTo(hw+4,-h*0.77);g.lineTo(-hw-4,-h*0.75);g.closePath();g.fill();
    g.strokeStyle='rgba(60,50,40,0.5)';g.lineWidth=1.5;g.stroke();}
  if(has('tag')){g.strokeStyle='#2a2018';g.lineWidth=1.5;g.beginPath();g.moveTo(hw*0.55,-h*0.8);g.lineTo(hw*0.7,-h*0.62);g.stroke();
    g.fillStyle='#efe6cf';g.save();g.translate(hw*0.7,-h*0.62);g.rotate(0.2);g.fillRect(-11,0,22,28);g.strokeRect(-11,0,22,28);g.restore();
    g.fillStyle='#8a8a8a';g.beginPath();g.arc(hw*0.55,-h*0.8,3,0,7);g.fill();}
  if(has('coins')){for(let k=0;k<3;k++){g.fillStyle='#d9b24a';g.beginPath();g.ellipse(hw*0.55,-4-k*6,11,4,0,0,7);g.fill();g.strokeStyle='#8a6a1e';g.lineWidth=1;g.stroke();}}
  if(has('emptied')){g.fillStyle='rgba(251,247,238,0.8)';for(let k=0;k<7;k++){g.beginPath();g.ellipse(-hw*0.9+k*(w*0.9/6),4,12,3,0,0,7);g.fill();}}
  // seam
  if(id!=='O'&&front) drawEars();
  g.strokeStyle='rgba(70,50,30,0.35)';g.setLineDash([6,6]);g.beginPath();g.moveTo(-hw+8,-3);g.quadraticCurveTo(0,3,hw-8,-3);g.stroke();g.setLineDash([]);
  if(id==='O'){ // wig over the top, strands past the shoulders; ex = flick / askew
    const fl=K.cl(-1,2,p.ex), ask=Math.max(fl>1?(fl-1):0,has('wig')?1:0), flick=fl<=1?fl:0;
    g.save();g.translate(ask*10,0);g.rotate(-0.12*ask);
    g.fillStyle='#7a3b8f';g.beginPath();
    g.moveTo(-hw-8,-h*0.42-flick*20);
    g.quadraticCurveTo(-hw-14,-h-8,0,-h-24);
    g.quadraticCurveTo(hw+14+flick*30,-h-8-flick*18,hw+8+flick*40,-h*0.45-flick*30);
    g.lineTo(hw-2+flick*28,-h*0.5-flick*24);
    g.quadraticCurveTo(hw-6,-h*0.88,0,-h*0.88);
    g.quadraticCurveTo(-hw+6,-h*0.88,-hw+2,-h*0.45);g.closePath();g.fill();
    g.strokeStyle='rgba(40,10,50,0.6)';g.lineWidth=1.5;for(let k=-3;k<=3;k++){g.beginPath();g.moveTo(k*6,-h-18);g.quadraticCurveTo(k*12,-h*0.9,(k<0?-hw-4:hw+4+flick*30),-h*0.5);g.stroke();}
    g.fillStyle='rgba(255,220,255,0.18)';g.beginPath();g.ellipse(-8,-h-12,14,5,-0.3,0,7);g.fill();
    g.restore();}
  g.restore();
}

function room(g,K,hs,doorLight){
  // wall
  const wg=g.createLinearGradient(0,0,0,FY);wg.addColorStop(0,'#17121a');wg.addColorStop(1,'#2b2128');g.fillStyle=wg;g.fillRect(0,0,1920,FY);
  // wallpaper stripes
  g.fillStyle='rgba(255,230,200,0.025)';for(let x=0;x<1920;x+=64)g.fillRect(x,0,26,FY-170);
  // wainscot
  g.fillStyle='#221a1a';g.fillRect(0,FY-170,1920,170);g.fillStyle='#3a2a24';g.fillRect(0,FY-176,1920,8);
  for(let x=-360;x<2300;x+=200){if(x>DOOR-330&&x<DOOR+130)continue;g.strokeStyle='rgba(0,0,0,0.35)';g.lineWidth=3;g.strokeRect(x,FY-150,160,120);}
  // floor
  const fg=g.createLinearGradient(0,FY,0,1080);fg.addColorStop(0,'#3a2a20');fg.addColorStop(1,'#1a120e');g.fillStyle=fg;g.fillRect(0,FY,1920,180);
  g.strokeStyle='rgba(0,0,0,0.35)';g.lineWidth=2;for(let i=0;i<7;i++){const y=FY+8+i*i*4.2;g.beginPath();g.moveTo(0,y);g.lineTo(1920,y);g.stroke();}
  // door
  const dx0=DOOR-112,dx1=DOOR+112,dy0=FY-420;
  g.fillStyle='#120c0c';g.fillRect(dx0-22,dy0-22,dx1-dx0+44,FY-dy0+22);
  const dg=g.createLinearGradient(dx0,0,dx1,0);dg.addColorStop(0,'#4a3122');dg.addColorStop(1,'#2e1e15');g.fillStyle=dg;g.fillRect(dx0,dy0,dx1-dx0,FY-dy0);
  g.strokeStyle='rgba(0,0,0,0.45)';g.lineWidth=4;g.strokeRect(dx0+24,dy0+40,dx1-dx0-48,150);g.strokeRect(dx0+24,dy0+250,dx1-dx0-48,140);
  g.fillStyle='#b08a3e';g.beginPath();g.arc(dx0+26,dy0+230,8,0,7);g.fill();
  // hatch: a brass-framed slot whose shutter slides aside
  const hx0=DOOR-56,hx1=DOOR+56,hy0=HATCH_Y-22,hy1=HATCH_Y+22,op=hs.o;
  g.fillStyle='#8a6a2e';g.fillRect(hx0-9,hy0-9,hx1-hx0+18,hy1-hy0+18);
  g.fillStyle='#050304';g.fillRect(hx0,hy0,hx1-hx0,hy1-hy0);
  if(op>0){const gl=g.createLinearGradient(0,hy0,0,hy1);gl.addColorStop(0,`rgba(255,214,140,${0.65*op})`);gl.addColorStop(1,`rgba(140,90,40,${0.35*op})`);g.fillStyle=gl;g.fillRect(hx0,hy0,(hx1-hx0)*op,hy1-hy0);}
  g.save();g.beginPath();g.rect(hx0,hy0,hx1-hx0,hy1-hy0);g.clip();g.fillStyle='#5a3e26';g.fillRect(hx0+(hx1-hx0)*op,hy0,hx1-hx0,hy1-hy0);
  g.strokeStyle='rgba(0,0,0,0.4)';g.lineWidth=2;for(let k=1;k<4;k++){g.beginPath();g.moveTo(hx0+(hx1-hx0)*op+k*28,hy0);g.lineTo(hx0+(hx1-hx0)*op+k*28,hy1);g.stroke();}g.restore();
  // a dark cuff — the hand stays unseen
  if(hs.arm>0){g.fillStyle='#0b0708';g.beginPath();const ax=DOOR-6,ay=HATCH_Y+4;g.ellipse(ax-hs.arm*30,ay,20+hs.arm*14,11,0.1,0,7);g.fill();}
  // light cone from hatch onto the presented sack
  if(op>0){g.save();g.globalCompositeOperation='lighter';const cg=g.createLinearGradient(0,hy1,0,FY);cg.addColorStop(0,`rgba(255,200,120,${0.13*op})`);cg.addColorStop(1,`rgba(255,180,90,${0.03*op})`);
    g.fillStyle=cg;g.beginPath();g.moveTo(hx0,hy1);g.lineTo(hx1,hy1);g.lineTo(hx1+120,FY+30);g.lineTo(hx0-140,FY+30);g.closePath();g.fill();g.restore();}
  // lamp (left)
  const lx=470;g.strokeStyle='#2a2018';g.lineWidth=8;g.beginPath();g.moveTo(lx,FY);g.lineTo(lx,470);g.stroke();
  g.fillStyle='#2a2018';g.fillRect(lx-40,FY-10,80,12);
  g.fillStyle='#c89a52';g.beginPath();g.moveTo(lx-70,470);g.lineTo(lx+70,470);g.lineTo(lx+46,390);g.lineTo(lx-46,390);g.closePath();g.fill();
  g.save();g.globalCompositeOperation='lighter';const rg=g.createRadialGradient(lx,470,10,lx,560,900);rg.addColorStop(0,'rgba(255,190,110,0.34)');rg.addColorStop(0.4,'rgba(255,170,90,0.08)');rg.addColorStop(1,'rgba(0,0,0,0)');
  g.fillStyle=rg;g.fillRect(0,0,1920,1080);g.restore();
}

function coin(g,x,y,r,spin){g.save();g.translate(x,y);g.scale(Math.max(0.15,Math.abs(Math.cos(spin))),1);g.fillStyle='#d9b24a';g.beginPath();g.arc(0,0,r,0,7);g.fill();
  g.strokeStyle='#8a6a1e';g.lineWidth=2;g.stroke();g.fillStyle='rgba(255,250,200,0.6)';g.beginPath();g.arc(-r*0.3,-r*0.3,r*0.3,0,7);g.fill();g.restore();}

DEED({
  n:5, key:'prostitution', title:'Incitement to Prostitution',
  scion:48, lineage:'State Machines — Characters That Can Refuse',
  op:'A doer shoves the victim toward a door; the victim refuses once and is shoved again; a hatch opens, coins pass through to the doer, and the victim is left standing at the door.',
  made:'Each sack is a pose record (x, lean, tilt, squash, sag, two ear states, attribute flag) drawn as a cloth silhouette; the doer, the victim and the door hatch are three finite-state machines. The room is a night boarding-house wall with a lamp on the left and a door with a brass hatch on the right.',
  moved:'A fixed event schedule drives the machines (IDLE, APPROACH, PUSH1, RECOIL, PUSH2, WAIT, TAKE, WITHDRAW for the doer; IDLE, SHOVED, REFUSE, SHOVED2, PRESENTED, LEFT for the victim) and every frame replays it from t=0. Guards couple them: the doer follows the victim\'s x while pushing, the refusal throws the doer back by the mass ratio, the hatch opens only after the victim is presented, and the doer takes one coin per coin event.',
  contact:CONTACT,
  leaves:{A:['coins'],V:['greyed']},
  draw(g,t,A,V,K,opt){
    const L=opt&&opt.layer, carry=(opt&&opt.carry)||{};
    const S=poses(t,A,V,K), c=S.c, vs=S.vs, ds=S.ds, hs=S.hs;
    g.save();g.translate(960,960);g.scale(CAM,CAM);g.translate(-CX,-FY);
    if(!L||L==='bg'){
      room(g,K,hs);
      // persistent world data: skid from the shoves, plant marks where the victim refused
      const vx=vs.pose.x;
      if(vx>X0V+2){g.strokeStyle='rgba(15,9,6,0.55)';g.lineWidth=4;const hw=K.CAST[V].w*0.42;
        for(const s of[-1,1]){g.beginPath();g.moveTo(X0V+s*hw,FY+4);g.lineTo(vx+s*hw,FY+4);g.stroke();}}
      if(t>=c.ev.refuse+0.1){const px=X0V+c.d1-c.back*0.6,hw=K.CAST[V].w*0.45;g.fillStyle='rgba(230,215,180,0.20)';
        for(let i=0;i<7;i++){g.beginPath();g.ellipse(px+hw*(i%2?1:-1)*(0.7+0.1*(i>>1))-10,FY+8+((i*7)%10),14+i*2,3,0,0,7);g.fill();}}
      g.save();g.setTransform(1,0,0,1,0,0);
      const vg=g.createRadialGradient(960,560,400,960,560,1200);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(0,0,0,0.55)');g.fillStyle=vg;g.fillRect(0,0,1920,1080);
      g.restore();
    }
    // victim (under the hatch light), then doer in front
    if(!L||L==='V') drawSack(g,V,vs.pose,K,1+hs.o*0.6,carry[V]);
    if(!L||L==='A'){
      drawSack(g,A,ds.pose,K,1,carry[A]);
      // coins: each leaves the hatch on its own event, arcs to the doer's top, vanishes into it
      if(t>=c.ev.pay){const dp=ds.pose,dh=K.CAST[A].h/(dp.sq||1);
        for(let i=0;i<c.n;i++){const t0=c.ev.pay+i*COIN_DT,fl=0.32,u=(t-t0)/fl;if(u<0||u>1)continue;
          const sx=DOOR-40,sy=HATCH_Y+4,ex=dp.x+(A==='O'?6:0),ey=FY-dp.lift-dh+12;
          const x=K.lerp(sx,ex,u),y=K.lerp(sy,ey,u)-Math.sin(u*Math.PI)*70;
          coin(g,x,y,17,u*9+i);}
        // Ogiva holds the last coin up to the lamp; Inigo tosses one; Belindo hangs them on his belt
        const tl=t-(c.ev.pay+c.n*COIN_DT+0.32);
        if(A==='O'&&tl>0){const dh2=K.CAST.O.h;coin(g,dp.x+6+dp.lean*dh2,FY-dp.lift-dh2-34-Math.min(1,tl*4)*10,13,tl*2);}
        if(A==='I'&&tl>0&&tl<0.8){const u=tl/0.8;coin(g,dp.x-20,FY-dp.lift-K.CAST.I.h-Math.sin(u*Math.PI)*170,12,u*14);}
        if(A==='B'&&tl>0){const dh2=K.CAST.B.h;g.fillStyle='rgba(240,200,90,0.9)';for(let i=0;i<c.n;i++){g.beginPath();g.arc(dp.x-40+i*16+dp.lean*dh2*0.6,FY-dp.lift-dh2*0.62,6,0,7);g.fill();}}
      }
    }
    g.restore();
  },
  marks(t,A,V,K){
    const S=poses(t,A,V,K);
    const box=(id,p)=>{const C=K.CAST[id],sq=p.sq*(1+p.bulge*0.3),w=C.w*sq*(1+p.sag*0.08)+(p.bulge*C.w)+12,h=C.h/sq*(1-p.sag*0.22)+(id==='O'?24:0)+(id==='I'?0:8);
      const lean=p.lean*h, x0=p.x-w/2+Math.min(0,lean), x1=p.x+w/2+Math.max(0,lean), y0=FY-p.lift-h, y1=FY;
      const X=x=>960+(x-CX)*CAM, Y=y=>960+(y-FY)*CAM;
      return {x:Math.round(X(x0)),y:Math.round(Y(y0)),w:Math.round((x1-x0)*CAM),h:Math.round((y1-y0)*CAM)};};
    return {A:box(A,S.ds.pose),V:box(V,S.vs.pose)};
  },
  sound(ac,out,t0,A,V,K){
    const SN=K.SND, c=ctxFor(A,V,K), e=c.ev, at=x=>t0+x;
    const px=x=>K.cl(-1,1,(960+(x-CX)*CAM)/960-1);
    const ax=tt=>poses(tt,A,V,K).ds.pose.x, vx=tt=>poses(tt,A,V,K).vs.pose.x;
    // lineage sound: every state transition throws a latch; doer latch low, victim latch mid, hatch latch high
    const latch=(tt,m,pan)=>SN.grain(ac,out,at(tt),{f:440*Math.pow(2,(m-69)/12),d:0.018,a:0.05,pan,type:'square',att:0.05});
    [e.approach,e.push1,e.refuse,e.push2,e.present,e.take,e.withdraw,e.hold].forEach(tt=>latch(tt,52,px(ax(tt))));
    [e.shoved,e.refuse,e.shoved2,e.present,e.left].forEach(tt=>latch(tt,64,px(vx(tt))));
    [e.open,e.pay,e.shut].forEach(tt=>latch(tt,88,px(DOOR)));
    // idle breath
    SN.say(ac,out,A,at(0.02),'breathe',0.4,px(X0A));SN.say(ac,out,V,at(0.05),'breathe',0.4,px(X0V));
    // doer footfalls from its gait
    const gait=(t1,D,kind)=>{const n={R:3,B:3,I:1,O:5}[A];
      if(A==='I'){SN.cloud(ac,out,at(t1),D,40,{bp:900,a:0.035,d:[0.03,0.08],spread:0.2},u=>Math.sin(Math.PI*u));SN.say(ac,out,'I',at(t1+D*0.9),'step',0.8,px(ax(t1+D)));return;}
      for(let k=1;k<=n;k++){const tt=t1+D*k/n-(A==='R'?D*0.15:0);SN.say(ac,out,A,at(tt),'step',A==='B'?0.8:1,px(ax(tt)));}};
    gait(e.approach,e.push1-e.approach);
    // push 1: contact thud, victim skids
    SN.say(ac,out,A,at(e.shoved),'land',0.6,px(vx(e.shoved)));
    SN.cloud(ac,out,at(e.shoved),0.32,90,{bp:350,q:2,a:0.05,d:[0.02,0.05],spread:0.2},u=>1-u);
    // refusal: the victim's voice, the doer thrown back
    SN.say(ac,out,V,at(e.refuse+0.04),'react',1.2,px(vx(e.refuse)));
    SN.say(ac,out,A,at(e.refuse+0.12),'land',0.5,px(ax(e.refuse+0.12)));
    if(V==='R'||V==='O')for(let k=0;k<4;k++)SN.say(ac,out,V,at(e.refuse+0.12+k*0.12),'tick',0.6,px(vx(e.refuse)));
    // push 2: wind-up breath, harder shove, skid to the door, body meets wood
    SN.say(ac,out,A,at(e.push2),'breathe',0.25,px(ax(e.push2)));
    SN.say(ac,out,A,at(e.shoved2),'land',0.9,px(vx(e.shoved2)));
    SN.cloud(ac,out,at(e.shoved2),0.34,110,{bp:320,q:2,a:0.06,d:[0.02,0.05],spread:0.2},u=>1-u*0.6);
    SN.thump(ac,out,at(e.shoved2+0.34),0.6,85,px(DOOR));
    // knock: two raps on the door frame
    [0.0625,0.3125].forEach(u=>SN.grain(ac,out,at(e.present+u),{bp:420,q:3,d:0.05,a:0.35,pan:px(DOOR-120),att:0.05}));
    // hatch slides open
    SN.cloud(ac,out,at(e.open),0.18,120,{bp:1600,q:2,a:0.04,d:[0.01,0.03],spread:0.1},u=>1);
    // CONTACT: the coins come through; each coin rings as it leaves the hatch and clinks where it lands
    const coinM=[91,95,98,94,96];
    for(let i=0;i<c.n;i++){const tt=e.pay+i*COIN_DT,a=i===0?0.5:0.3;
      SN.pluck(ac,out,at(tt),coinM[i%5],a,0.5,px(DOOR-40));
      SN.grain(ac,out,at(tt),{f:440*Math.pow(2,(coinM[i%5]+7-69)/12)*1.003,d:0.25,a:a*0.4,pan:px(DOOR),att:0.02});
      SN.say(ac,out,A,at(tt+0.32),'tick',0.9,px(ax(tt+0.32)));
      SN.grain(ac,out,at(tt+0.32),{f:3300+K.hash(i)*400,d:0.04,a:0.12,pan:px(ax(tt+0.32)),att:0.05});}
    SN.thump(ac,out,at(e.pay),0.35,70,px(DOOR));
    // victim under the light breathes; after, it sinks
    SN.say(ac,out,V,at(e.present+0.1),'breathe',0.6,px(DOOR));
    // hatch shuts
    SN.cloud(ac,out,at(e.shut),0.16,120,{bp:1400,q:2,a:0.04,d:[0.01,0.03],spread:0.1},u=>1);
    SN.grain(ac,out,at(e.shut+0.19),{bp:600,q:2,d:0.06,a:0.3,pan:px(DOOR),att:0.05});
    SN.say(ac,out,V,at(e.left+0.2),'sink',0.8,px(DOOR));
    // per-doer coda with the money
    const tl=e.pay+c.n*COIN_DT+0.32;
    if(A==='I'){SN.grain(ac,out,at(tl),{f:2800,d:0.03,a:0.15,pan:px(ax(tl))});SN.pluck(ac,out,at(tl+0.8),93,0.2,0.3,px(ax(tl+0.8)));}
    if(A==='O')SN.pluck(ac,out,at(tl+0.15),100,0.18,0.6,px(ax(tl)));
    if(A==='B')for(let k=0;k<c.n;k++)SN.grain(ac,out,at(tl+0.05+k*0.05),{f:2500+k*180,d:0.03,a:0.1,pan:px(ax(tl))});
    if(A==='R')SN.cloud(ac,out,at(tl),0.3,40,{bp:600,a:0.03,d:[0.02,0.05]},u=>1-u);
    // withdraw footfalls
    const D=e.hold-e.withdraw,n={R:4,B:3,I:1,O:4}[A];
    if(A==='I')SN.cloud(ac,out,at(e.withdraw),D,30,{bp:900,a:0.03,d:[0.03,0.08],spread:0.2},u=>Math.sin(Math.PI*u));
    else for(let k=1;k<=n;k++){const tt=e.withdraw+D*k/n-(A==='R'?D*0.1:0);SN.say(ac,out,A,at(tt),'step',0.7,px(ax(tt)));}
  }
});
})();
