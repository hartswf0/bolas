// TRANSITION 03 · Incitement to Suicide (Norstein fog planes) -> Knifing (Foldès drawn line metamorphosis)
// SCION 14 · Nora Willett — Pose2Pose: pose selection and transfer.
// Nothing here is warped or cross-faded. Every frame of every sack is ONE drawing selected from a small
// illustration bank (drawings harvested from the two deeds themselves: fog-plane cutouts from incitement,
// key-contour drawings from knifing). A target performance (walk, hesitation, entering, leaving) is written
// for each sack; a Viterbi pass picks the drawing sequence that matches the performance's pose and the
// language of the room it stands in, under a transition penalty that forbids flicker. The room is decoded
// the same way from a bank of room plates (fog plate, thick fog, chalk-line drawing, lamp lit, boiling plates).
// Typed state: drawing = {style:'N'|'F', deed, A, V, role, t, box, q (squash), m (moving), ph (gait phase)}.
// Invariant (numeric): first decoded drawing of a sack present in the outgoing shot is that shot's own end
// drawing; last decoded drawing of a sack present in the incoming shot is that shot's own first drawing.
(function(){
const DUR=3.2,H0=0.45,H1=0.28,HZ=12;           // hold outgoing, decoded at 12 drawings/s, hold incoming
const NS=Math.round((DUR-H0-H1)*HZ)+1;          // decoded steps
const IDS=['R','B','I','O'];
const DOOR={x0:1562,x1:1720,y0:302,y1:668};      // the knifing parlour's door (its backdrop geometry)
const FLOOR4=930;
let C=null;                                      // cache for one film
const off=(w,h)=>{const c=document.createElement('canvas');c.width=w||1920;c.height=h||1080;return c};
function reset(q){q.setTransform(1,0,0,1,0,0);q.globalAlpha=1;q.globalCompositeOperation='source-over';q.filter='none'}
const ease=(a,b,u)=>{const x=Math.max(0,Math.min(1,(u-a)/(b-a)));return x*x*(3-2*x)};
const lerp=(a,b,u)=>a+(b-a)*u;
function lvMix(a,b,u){const o={};for(const k in a)o[k]=lerp(a[k]||0,b[k]||0,u);return o}
function lvFilter(lv){const fl=[];if(lv.grey>.05)fl.push(`grayscale(${Math.min(1,lv.grey)}) brightness(${1-.25*lv.grey})`);if(lv.halo>.15)fl.push(`drop-shadow(0 0 ${Math.round(28*lv.halo)}px rgba(255,236,180,${Math.min(.9,lv.halo)}))`);
 if(lv.shadow>.15)fl.push(`drop-shadow(${Math.round(-60*lv.shadow)}px ${Math.round(-30*lv.shadow)}px ${Math.round(18*lv.shadow)}px rgba(0,0,0,${Math.min(.8,.35+lv.shadow*.4)}))`);return fl.join(' ')||'none'}
const lvScale=lv=>1+.14*Math.max(-1,Math.min(1,lv.loom))-.22*lv.shrink;

// ================= PLAN: a pure function of the ledger and the deeds' marks (no pixels needed) =================
function plan(L,K){
 const D3=DEEDS.incitement,D4=DEEDS.knifing,eo=L.ev[2],ei=L.ev[3],s2=L.states[2],s3=L.states[3];
 const mo=D3.marks(5.99,eo.A,eo.V,K),mi=D4.marks(0,ei.A,ei.V,K);
 const roleIn=(e,s)=>e.A===s?'A':e.V===s?'V':null;
 const partner=(s,e)=>e.A===s?e.V:e.V===s?e.A:IDS.find(x=>x!==s);
 const sacks=[];
 for(const s of IDS){const ro=roleIn(eo,s),ri=roleIn(ei,s);if(!ro&&!ri)continue;
  const dead=!s3.alive[s],ghost=dead&&!!ri,body=dead&&!!ro&&!ri;
  const kind=ro&&ri?'staying':ro?'leaving':'entering';
  const S={id:s,ro,ri,kind,dead,ghost,body};
  // rest scale of the sack in each language (box width / cast width at t=0)
  const r3=D3.marks(0,ro?eo.A:s,ro?eo.V:partner(s,eo),K)[ro||'A'],r4=D4.marks(0,ri?ei.A:s,ri?ei.V:partner(s,ei),K)[ri||'A'];
  S.sigN=(ro?mo[ro]:r3).w/K.CAST[s].w;S.sigF=(ri?mi[ri]:r4).w/K.CAST[s].w;S.sigD=Math.min(132/K.CAST[s].w,320/K.CAST[s].h);
  // ---------- illustration bank: drawings harvested from both deeds ----------
  const bank=[];
  const add=(style,deed,A,V,role,t,exact)=>{const D=DEEDS[deed];const m=D.marks(t,A,V,K)[role],m2=D.marks(Math.min(5.99,t+.08),A,V,K)[role],m0=D.marks(0,A,V,K)[role];
   bank.push({style,deed,A,V,role,t,exact,box:m,sig:m.w/K.CAST[s].w,q:(m.h/m.w)/(m0.h/m0.w),m:Math.min(1,Math.abs(m2.x+m2.w/2-m.x-m.w/2)/.08/90)})};
  // Norstein fog-plane cutouts
  if(ro)add('N','incitement',eo.A,eo.V,ro,5.99,'end');
  {const A=s,V=(ro==='A')?eo.V:IDS.find(x=>x!==s);for(const t of [0,.5,.8,1.1,1.4,1.7])add('N','incitement',A,V,'A',t,null)}
  // Foldès key-contour drawings
  if(ri)add('F','knifing',ei.A,ei.V,ri,0,'start');
  {const A=s,V=(ri==='A')?ei.V:IDS.find(x=>x!==s);for(const t of [.25,.55,.85,1.15,1.45])add('F','knifing',A,V,'A',t,null)}
  // the fog victim that survived gets up again: its own sinking drawings, to be read backwards
  if(ro==='V'&&!dead)for(const t of [3.0,4.0,5.0])add('N','incitement',eo.A,eo.V,'V',t,'rise');
  // a rare gesture drawing: the shrink (recoil) of a sack that remembers — the fog victim's first sinking
  {const A=IDS.find(x=>x!==s);add('N','incitement',A,s,'V',2.2,'recoil')}
  // gait phase: walk drawings of one deed get evenly spread phases in harvest order (representative clusters of a step cycle)
  for(const st of ['N','F']){const w=bank.filter(d=>d.style===st&&!d.exact&&d.m>.25);w.forEach((d,i)=>d.ph=i/w.length)}
  S.bank=bank;
  // ---------- target performance ----------
  const a0=ro?{x:mo[ro].x+mo[ro].w/2,y:mo[ro].y+mo[ro].h}:null,a1=ri?{x:mi[ri].x+mi[ri].w/2,y:mi[ri].y+mi[ri].h}:null;
  S.a0=a0;S.a1=a1;
  const other=ri?(ri==='A'?ei.V:ei.A):null;
  const mem=other?LEDGER.memories(L,s,3).filter(m=>m.other===other)[0]:null;S.hes=mem&&mem.weight>.4?Math.min(1,mem.weight):0;S.mem=mem||null;
  S.lvA=s2.levers[s];S.lvB=s3.levers[s];
  S.track=[];
  const doorX=(DOOR.x0+DOOR.x1)/2,doorY=DOOR.y1+4;
  const fromLeft=kind==='entering'&&a1.x<960;
  for(let i=0;i<NS;i++){const u=H0+i/HZ;let x,y,sig,inDoor=0,vis=1,still=false,q=1;
   const riser=ro==='V'&&!dead,qEnd=riser?bank[0].q:1;
   if(riser)q=lerp(qEnd,1,ease(.5,1.15,u));
   if(kind==='staying'&&!body||ghost){ // walk from the fog room's end mark to the parlour's start mark
    const t0=riser?1.0:.55+(ghost?.25:0),t1=DUR-H1-.06;
    let p=ease(t0,t1,u);
    if(S.hes){const hp=.55,hu=lerp(t0,t1,.5),hd=.35*S.hes;const pa=ease(t0,hu,u)*hp,pb=ease(hu+hd,t1,u)*(1-hp);p=pa+pb;if(u>hu&&u<hu+hd){q=.86;still=true;p-=.06*S.hes*Math.sin(Math.PI*(u-hu)/hd)}}
    x=lerp(a0.x,a1.x,p);y=lerp(a0.y,a1.y,p);sig=lerp(S.sigN,S.sigF,p);vis=ghost?.55+.25*K.hash(i*3.7+s.charCodeAt(0)):1}
   else if(body){x=a0.x;y=a0.y;sig=S.sigN;still=true}
   else if(kind==='leaving'){ // walks upstage into the open door and on into the fog room
    const t0=riser?.95:.55,t1=2.05,t2=2.4;const p=ease(t0,t1,u);x=lerp(a0.x,doorX,p);y=lerp(a0.y,doorY,p);sig=lerp(S.sigN,S.sigD,p);
    if(u>t1){inDoor=ease(t1,t2,u);y=doorY-26*inDoor;sig*=1-.35*inDoor;vis=1-inDoor}}
   else{ // entering: from the left edge, or out of the door of the fog room
    if(fromLeft){const t0=.5,t1=DUR-H1-.06;let p=ease(t0,t1,u);
     if(S.hes){const hu=lerp(t0,t1,.55),hd=.35*S.hes;p=ease(t0,hu,u)*.6+ease(hu+hd,t1,u)*.4;if(u>hu&&u<hu+hd){q=.86;still=true}}
     x=lerp(-K.CAST[s].w*S.sigF*.7,a1.x,p);y=a1.y;sig=S.sigF}
    else{const t0=1.3,t1=DUR-H1-.06,pi=ease(t0,t0+.3,u);let p=ease(t0+.25,t1,u);
     if(S.hes){const hu=lerp(t0+.25,t1,.5),hd=.3*S.hes;p=ease(t0+.25,hu,u)*.5+ease(hu+hd,t1,u)*.5;if(u>hu&&u<hu+hd){q=.86;still=true}}
     x=lerp(doorX,a1.x,p);y=lerp(doorY,a1.y,p);sig=lerp(S.sigD,S.sigF,p);inDoor=1-pi;vis=u<t0?0:1}}
   S.track.push({u,x,y,sig,inDoor,vis,still,q})}
  for(let i=0;i<NS;i++){const a=S.track[Math.max(0,i-1)],b=S.track[Math.min(NS-1,i+1)];const sp=Math.hypot(b.x-a.x,b.y-a.y)/(2/HZ);S.track[i].m=S.track[i].still?0:Math.min(1,sp/90)}
  // gait phase from distance walked (one step cycle per ~0.55 sack widths)
  let dist=0;for(let i=0;i<NS;i++){if(i)dist+=Math.hypot(S.track[i].x-S.track[i-1].x,S.track[i].y-S.track[i-1].y);S.track[i].ph=(dist/(K.CAST[s].w*S.track[i].sig*.55))%1}
  sacks.push(S)}
 // ---------- the room: a bank of plates decoded by the same DP ----------
 const PL=[{id:'N0',lev:0},{id:'N1',lev:1},{id:'F0',lev:2},{id:'F1',lev:3},{id:'Fb',lev:4}];
 const levAt=u=>u<.8?0:u<1.15?lerp(0,1,ease(.8,1.0,u)):u<1.5?lerp(1,2,ease(1.15,1.3,u)):u<1.85?lerp(2,3,ease(1.5,1.65,u)):lerp(3,4,ease(1.85,2.0,u));
 const room=viterbi(NS,PL.length,(i,j)=>{const d=PL[j].lev-levAt(H0+i/HZ);return d*d*4+(i===0&&j!==0?1e6:0)+(i===NS-1&&j!==4?1e6:0)},(a,b)=>b===a?0:(b===a+1?1.2:1e6));
 const roomPath=room.map(j=>PL[j].id);
 const swStep=roomPath.indexOf('F0');const uSw=H0+swStep/HZ;
 // ---------- each sack: Viterbi over its drawing bank ----------
 for(const S of sacks){const B=S.bank,n=B.length;
  const roomStyle=i=>roomPath[i][0];
  const sOff=(S.a0?S.a0.x:S.a1.x)/1920*.25;                        // the left of the room changes language first
  const unary=(i,j)=>{const d=B[j],tr=S.track[i];let c=0;
   const inN=tr.inDoor>.5||(roomStyle(i)==='N'&&H0+i/HZ<uSw+sOff)||S.body;
   const wantN=inN?1:0;c+=(d.style==='N'?1-wantN:wantN)*6;
   c+=3*(d.m-tr.m)*(d.m-tr.m);c+=40*(d.q-tr.q)*(d.q-tr.q);
   if(tr.m>.25&&d.ph!=null){let dp=Math.abs(d.ph-tr.ph);dp=Math.min(dp,1-dp);c+=12*dp}
   if(tr.m>.25&&d.ph==null)c+=1.5;
   if(d.exact==='recoil')c+=S.hes&&tr.still?-1:12;
   if(d.exact==='rise')c+=tr.m>.3?6:0;                         // rare drawing: only for the hesitation
   if(i===0&&S.ro&&d.exact!=='end')c+=1e6;if(i===NS-1&&S.ri&&d.exact!=='start')c+=1e6;
   if(S.body&&d.exact!=='end')c+=1e6;
   return c};
  const pair=(a,b)=>{if(a===b)return 0;const A=B[a],Bb=B[b];return .9+2*Math.abs(A.q-Bb.q)+(A.style!==Bb.style?.6:0)};
  S.path=viterbi(NS,n,unary,pair)}
 return{sacks,roomPath,uSw,eo,ei,mo,mi};
}
function viterbi(T,N,unary,pair){const cost=[],back=[];
 for(let i=0;i<T;i++){cost.push(new Float64Array(N));back.push(new Int32Array(N));
  for(let j=0;j<N;j++){const u=unary(i,j);if(i===0){cost[i][j]=u;continue}let best=1e18,bi=0;for(let k=0;k<N;k++){const c=cost[i-1][k]+pair(k,j);if(c<best){best=c;bi=k}}cost[i][j]=best+u;back[i][j]=bi}}
 let j=0,b=1e18;for(let k=0;k<N;k++)if(cost[T-1][k]<b){b=cost[T-1][k];j=k}
 const p=new Array(T);for(let i=T-1;i>=0;i--){p[i]=j;j=back[i][j]}return p}

// ================= PIXELS: the drawings and plates, rendered once per film from the deeds' layers =================
function composite(q,D,lt,e,st,lay,K,impossible){const carry=st.body;const order=D.layers||['bg','V','A'];const mk=D.marks?D.marks(lt,e.A,e.V,K):null;
 for(const ly of order){const c=lay[ly].getContext('2d');reset(c);c.clearRect(0,0,1920,1080);c.save();try{D.draw(c,lt,e.A,e.V,K,{layer:ly,carry})}catch(err){}c.restore()}
 reset(q);q.fillStyle='#000';q.fillRect(0,0,1920,1080);
 for(const ly of order){if(ly==='bg'||!mk){q.drawImage(lay[ly],0,0);continue}const who=ly==='A'?e.A:e.V,lv=st.levers[who],b=mk[ly];
  const f=lvScale(lv),cx=b.x+b.w/2,by=b.y+b.h;q.save();q.filter=lvFilter(lv);q.translate(cx,by);q.scale(f,f);q.translate(-cx,-by);q.drawImage(lay[ly],0,0);q.restore()}
 if(impossible){reset(q);q.fillStyle='rgba(120,220,150,.06)';for(let y=0;y<1080;y+=6)q.fillRect(0,y,1920,2)}}
function cropOf(src,box){const px=box.w*.7+50,pt=box.h*.9+60,pb=50;const x=Math.max(0,Math.floor(box.x-px)),y=Math.max(0,Math.floor(box.y-pt)),x1=Math.min(1920,Math.ceil(box.x+box.w+px)),y1=Math.min(1080,Math.ceil(box.y+box.h+pb));
 const c=off(Math.max(1,x1-x),Math.max(1,y1-y));c.getContext('2d').drawImage(src,-x,-y);return{c,x,y}}
function linesOf(src){ // the parlour as a chalk-line drawing only: a high-pass of its own backdrop
 const w=480,h=270,sm=off(w,h),sq=sm.getContext('2d');sq.filter='blur(3px)';sq.drawImage(src,0,0,w,h);
 const full=off(),fq=full.getContext('2d');fq.drawImage(src,0,0);const A=fq.getImageData(0,0,1920,1080),Bd=sq.getImageData(0,0,w,h).data,d=A.data;
 for(let y=0;y<1080;y++)for(let x=0;x<1920;x++){const i=(y*1920+x)*4,j=(((y>>2)*w)+(x>>2))*4;const l=d[i]+d[i+1]+d[i+2],b=Bd[j]+Bd[j+1]+Bd[j+2];const e=Math.max(0,Math.min(1,(l-b-12)/40));
  d[i]=lerp(14,236,e);d[i+1]=lerp(13,224,e);d[i+2]=lerp(16,196,e);d[i+3]=255}
 fq.putImageData(A,0,0);return full}
function ensure(X,K,budget){
 const L=X.ledger,key=X.film.join(',');if(C&&C.key===key&&C.done)return C;
 if(!C||C.key!==key){C={key,P:plan(L,K),jobs:[],done:false,img:{}};const P=C.P,D3=DEEDS.incitement,D4=DEEDS.knifing,s2=L.states[2],s3=L.states[3];
  C.lay={bg:off(),A:off(),V:off()};const tmp=off();
  const imp3=s3.impossible.some(q=>q.k===2),imp4=L.states[4].impossible.some(q=>q.k===3);
  C.jobs.push(()=>{C.OUT=off();composite(C.OUT.getContext('2d'),D3,5.99,P.eo,s2,C.lay,K,imp3);C.N0=off();C.N0.getContext('2d').drawImage(C.lay.bg,0,0);C.outV=off();C.outV.getContext('2d').drawImage(C.lay.V,0,0)});
  C.jobs.push(()=>{C.IN=off();composite(C.IN.getContext('2d'),D4,0,P.ei,s3,C.lay,K,imp4);C.Fb=[off(),off(),off()];C.Fb[0].getContext('2d').drawImage(C.lay.bg,0,0);
   for(let f=1;f<3;f++){const q=C.Fb[f].getContext('2d');try{D4.draw(q,f/HZ,P.ei.A,P.ei.V,K,{layer:'bg',carry:s3.body})}catch(e){}}});
  C.jobs.push(()=>{C.F0=linesOf(C.Fb[0]);C.F1=off();const q=C.F1.getContext('2d');q.drawImage(C.F0,0,0);q.save();q.globalCompositeOperation='lighter';const rg=q.createRadialGradient(960,270,10,960,520,900);rg.addColorStop(0,'rgba(255,214,150,0.34)');rg.addColorStop(.5,'rgba(255,200,130,0.08)');rg.addColorStop(1,'rgba(0,0,0,0)');q.fillStyle=rg;q.fillRect(0,0,1920,1080);q.restore();
   C.N1=off();const n=C.N1.getContext('2d');n.drawImage(C.N0,0,0);n.filter='blur(6px)';n.drawImage(C.N0,0,0);n.filter='none';for(let k=0;k<4;k++){const y=540+k*150,gr=n.createLinearGradient(0,y-220,0,y+220);gr.addColorStop(0,'rgba(140,150,172,0)');gr.addColorStop(.5,`rgba(140,150,172,${.14+.05*k})`);gr.addColorStop(1,'rgba(140,150,172,0)');n.fillStyle=gr;n.fillRect(0,y-220,1920,440)}});
  C.jobs.push(()=>{C.INSET=inset(L,P,K)});
  for(const S of P.sacks)S.bank.forEach((d,j)=>{if(!S.path.includes(j)&&!(S.body&&d.exact==='end'))return; // only drawings the path selected
   C.jobs.push(()=>{const D=DEEDS[d.deed];const st=d.exact==='end'?s2:s3;/* every harvested drawing wears the state at the join; only the outgoing end drawing keeps its own */const q=tmp.getContext('2d');reset(q);q.clearRect(0,0,1920,1080);q.save();try{D.draw(q,d.t,d.A,d.V,K,{layer:d.role,carry:st.body})}catch(e){}q.restore();d.img=cropOf(tmp,d.box)})})}
 const t0=performance.now();while(C.jobs.length){C.jobs.shift()();if(budget&&performance.now()-t0>budget)break}
 C.done=!C.jobs.length;return C}
// the fog room seen through the parlour door: the incitement room's own end picture, its dead, its evidence
function inset(L,P,K){const w=DOOR.x1-DOOR.x0,h=DOOR.y1-DOOR.y0,c=off(w,h),q=c.getContext('2d');
 const v=P.mo.V,cx=v.x+v.w/2+40,sc=.42,cw=w/sc,ch=h/sc,x0=cx-cw/2,y0=Math.min(1080-ch,v.y+v.h+120-ch);
 q.drawImage(C.N0,x0,y0,cw,ch,0,0,w,h);
 if(!L.states[3].alive[P.eo.V]){q.save();q.filter='grayscale(1) brightness(.75)';q.drawImage(C.outV,x0,y0,cw,ch,0,0,w,h);q.restore()}
 // evidence left so far in the house: each earlier deed's trace on the fog-room floor
 const ev=L.states[3].evidence;let ex=w-58;
 for(const e of ev){if(e.kind==='lamp')continue;const M=CONSEQS[e.deed];const box={x:ex,y:h-70-(ex<w/2?0:8),w:50,h:38};ex-=54;
  q.save();try{if(M&&M.trace)M.trace(q,box,3-1-e.k,K);else{q.fillStyle='rgba(230,220,200,.5)';q.fillRect(box.x+8,box.y+12,22,14)}}catch(err){}q.restore()}
 const o=off(w,h),oq=o.getContext('2d');oq.filter='brightness(1.7) saturate(.8)';oq.drawImage(c,0,0);return o}

// ================= DRAW =================
function drawDrawing(g,S,d,tr,lv,alpha){if(!d.img)return;const a=d.box;const ax=a.x+a.w/2,ay=a.y+a.h;const k=tr.sig/d.sig*lvScale(lv);
 g.save();g.globalAlpha=alpha;g.filter=lvFilter(lv);g.translate(tr.x,tr.y);g.scale(k,k);g.translate(-ax,-ay);g.drawImage(d.img.c,d.img.x,d.img.y);g.restore()}
function chalk(g,pts,i,K,w,col){g.strokeStyle=col||'rgba(225,208,176,0.55)';g.lineWidth=w||2.5;g.beginPath();pts.forEach((p,k)=>{const jx=(K.hash(i*7.3+k*1.9)-.5)*3,jy=(K.hash(i*5.1+k*2.3)-.5)*3;k?g.lineTo(p[0]+jx,p[1]+jy):g.moveTo(p[0]+jx,p[1]+jy)});g.stroke()}
function drawDoor(g,i,open,K){ // the door leaf as one of four chalk drawings (open, two-thirds, one-third, shut)
 if(open<=0)return;g.drawImage(C.INSET,DOOR.x0,DOOR.y0);const a=open*1.25,cw=Math.cos(a),sw=Math.sin(a);const w=DOOR.x1-DOOR.x0;
 const p=[[DOOR.x0,DOOR.y0],[DOOR.x0+w*cw,DOOR.y0+34*sw],[DOOR.x0+w*cw,DOOR.y1-22*sw],[DOOR.x0,DOOR.y1]];
 g.fillStyle='#1d1a20';g.beginPath();p.forEach((q,k)=>k?g.lineTo(...q):g.moveTo(...q));g.closePath();g.fill();chalk(g,[...p,p[0]],i,K);
 g.beginPath();g.arc(DOOR.x0+w*cw*.88,(DOOR.y0+DOOR.y1)/2,5,0,7);g.stroke();
 chalk(g,[[DOOR.x0,DOOR.y0],[DOOR.x1,DOOR.y0],[DOOR.x1,DOOR.y1]],i+50,K,2)}
const DOORSTEPS=[1,1,1,1,.66,.66,.33,.33,0];       // decoded door drawings after the close begins
function doorOpen(P,i){const u=H0+i/HZ;if(P.roomPath[i][0]==='N')return 0;const tc=2.45;if(u<tc)return 1;return DOORSTEPS[Math.min(DOORSTEPS.length-1,Math.round((u-tc)*HZ)+3)]}
function frame(g,u,X,K){
 const c=ensure(X,K,u<H0-.05?22:0);
 if(u<H0||!c.done){g.drawImage(c.OUT||blank(),0,0);return}
 if(u>DUR-H1){g.drawImage(c.IN,0,0);return}
 const P=c.P,i=Math.max(0,Math.min(NS-1,Math.round((u-H0)*HZ))),rp=P.roomPath[i];
 const pl=rp==='N0'?c.N0:rp==='N1'?c.N1:rp==='F0'?c.F0:rp==='F1'?c.F1:c.Fb[i%3];
 reset(g);g.drawImage(pl,0,0);
 const op=doorOpen(P,i);drawDoor(g,i,op,K);
 const lu=K.sm(H0,DUR-H1,u);
 const order=P.sacks.slice().sort((a,b)=>a.track[i].y-b.track[i].y);
 for(const S of order){const tr=S.track[i];if(tr.vis<=0)continue;
  if(S.body&&rp[0]==='F')continue;                     // the body stays in the fog room, seen through the door
  const d=S.bank[S.path[i]],lv=lvMix(S.lvA,S.lvB,S.body?0:lu);
  g.save();if(tr.inDoor>0&&rp[0]==='F'){if(op<=0){g.restore();continue}g.beginPath();g.rect(DOOR.x0,0,DOOR.x1-DOOR.x0,DOOR.y1+(1-tr.inDoor)*400);g.clip()}
  drawDrawing(g,S,d,tr,lv,tr.vis);g.restore()}
 const imp=X.ledger.states[4].impossible.some(q=>q.k===3);
 if(imp){g.fillStyle=`rgba(120,220,150,${.06*lu})`;for(let y=0;y<1080;y+=6)g.fillRect(0,y,1920,2)}}
let BL=null;const blank=()=>BL||(BL=off());

TRANSITION({k:3,scion:14,lineage:'Nora Willett — Pose2Pose: Pose Selection and Transfer for 2D Character Animation (2020)',
 op:'Each sack is re-performed by a sequence of drawings selected from a bank harvested from both deeds (fog cutouts and key contours) by a Viterbi path that scores pose distance to a written walk and the language of the room it stands in, plus a transition penalty; the room is decoded the same way through fog, chalk-line and lamp plates.',
 made:'A bank of about a dozen drawings per sack: fog-plane cutouts lifted from the incitement shot and key-contour drawings lifted from the knifing shot, plus one rare recoil drawing, each with its box, squash, motion and gait phase. The room is five plates: the fog room, thicker fog, the parlour as bare chalk lines, the lines with the lamp lit, and the boiling parlour; the fog room stays visible through the parlour door with its dead and its evidence.',
 moved:'A written performance per sack (walk downstage, walk into the door, enter from the edge or out of the door, hold to remember) is decoded at 12 drawings a second into holds and swaps; a sack changes language on the drawing whose pose fits, not by fading. The door leaf is four chalk drawings that shut the fog room away before the knife scene starts.',
 dur:DUR,
 plan:(L,K)=>plan(L,K),
 draw(g,u,X,K){frame(g,u,X,K)},
 sound(ac,out0,t0,X,K){const out=ac.createGain();out.gain.value=2.1;out.connect(out0);const L=X.ledger,P=plan(L,K),SN=K.SND,pan=x=>Math.max(-1,Math.min(1,x/960-1));let n=0;
  // the fog room's hush, thinning as the chalk room is drawn
  SN.cloud(ac,out,t0,1.3,26,{bp:500,a:.035,d:[.1,.3]},u=>1-u);
  // each room plate change: a paper/glass click (plates are swapped, not faded)
  for(let i=1;i<NS;i++)if(P.roomPath[i]!==P.roomPath[i-1]){const w=t0+H0+i/HZ,id=P.roomPath[i];
   if(id[0]==='F'&&P.roomPath[i-1][0]==='N')for(let k=0;k<10;k++)SN.grain(ac,out,w+k*.012,{bp:2400+k*300,q:2,d:.02,a:.05,pan:(k/5-1)*.6});
   else SN.grain(ac,out,w,{bp:3200,q:3,d:.025,a:.06});if(id==='F1')SN.grain(ac,out,w,{f:880,d:.18,a:.04,att:.05})}
  // sacks: a footfall in the sack's own voice on each walking drawing swap; the hesitation breathes; the ghost has no feet
  for(const S of P.sacks){for(let i=1;i<NS;i++){const tr=S.track[i];if(S.path[i]===S.path[i-1]||tr.vis<=0)continue;const w=t0+H0+i/HZ;
    if(S.ghost){if(n++<200)SN.grain(ac,out,w,{bp:SN.VOICE[S.id].bp*1.5,d:.06,a:.025,pan:pan(tr.x)});continue}
    if(tr.m>.2&&n++<200)SN.say(ac,out,S.id,w,'step',.7*(1+.4*(S.lvB.weight||0)),pan(tr.x));else SN.say(ac,out,S.id,w,'tick',.3,pan(tr.x))}
   if(S.hes){const i=S.track.findIndex(t=>t.still&&t.vis>0);if(i>=0)SN.say(ac,out,S.id,t0+H0+i/HZ,'breathe',.6,pan(S.track[i].x))}}
  // the door shuts the fog room away
  for(let i=1;i<NS;i++){const a=doorOpen(P,i-1),b=doorOpen(P,i);if(b<a){const w=t0+H0+i/HZ;if(b===0)SN.thump(ac,out,w,.8,70,.7);else SN.grain(ac,out,w,{bp:900,d:.08,a:.05,pan:.7})}}}
});
})();
