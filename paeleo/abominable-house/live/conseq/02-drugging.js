// CONSEQUENCE 02 · Drugging — the waking. SCION 31 · Alpha Matting (hair, lace and smoke).
// The drug is written as matte contamination: every edge in the sleeper's sight carries a green spill halo and the
// world sits under a smoke matte. Waking is a matte solve run forward in time:
//   trimap   : known foreground = the victim itself (its own body is clear first), unknown band = the room, which
//              thins from the victim outward; the corners stay unknown longest (residual haze = 'drowsy').
//   alpha    : the smoke is a fractional-alpha field (two octaves of value noise, low-res, bilinear upsampled),
//              threshold rising with the waking progress p(t).
//   decontam : the green spill halo on each edge decays with p (foreground colour recovery), except on the victim and
//              in the cup: residue edges keep their contamination.
//   edges    : sacks are polygons with fibre edge texture (short strands along the outward normal at partial alpha);
//              Ogiva's wig and Inigo's ears are strand bundles; Roessler's shawl and the guilt veil are lace (holes punched
//              evenodd); burnt photograph smoke is premultiplied soft puffs; absences are drawn as a residue edge
//              (a clean patch outlined where an object was lifted out of the matte).
// Invariant (numeric): the haze alpha is monotone non-increasing in t at every pixel of the grid except the noise
// drift term (amplitude bounded by .12), and the victim's spill c_V(t) >= .25 for all t (the residue never fully clears).
(function(){
const FY=800,S=1.25,TX0=818,TX1=1102,TY=FY-132,CUPX=960;
const clamp=(a,b,x)=>Math.max(a,Math.min(b,x));
const sm=(a,b,x)=>{const u=clamp(0,1,(x-a)/(b-a));return u*u*(3-2*u)};
const eo=(a,b,x)=>{const u=clamp(0,1,(x-a)/(b-a));return 1-Math.pow(1-u,3)};
const lerp=(a,b,u)=>a+(b-a)*u;
const H=n=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)};
const vn=(x,y)=>{const xi=Math.floor(x),yi=Math.floor(y),xf=x-xi,yf=y-yi,u=xf*xf*(3-2*xf),v=yf*yf*(3-2*yf);
 const h=(a,b)=>H(a*57.3+b*131.7);return lerp(lerp(h(xi,yi),h(xi+1,yi),u),lerp(h(xi,yi+1),h(xi+1,yi+1),u),v)};
const MAT={R:{w:168,h:122,col:[214,191,150]},B:{w:244,h:214,col:[232,213,174]},I:{w:128,h:98,col:[226,206,165]},O:{w:80,h:184,col:[240,228,200]}};
const GREEN=[143,208,94];
const rgba=(c,a)=>`rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
const mix=(a,b,u)=>[lerp(a[0],b[0],u),lerp(a[1],b[1],u),lerp(a[2],b[2],u)];
const DUR=3.2;
// waking schedule per victim: start, end of rise
const WAKE={R:[.45,1.6],B:[.85,1.95],I:[.75,1.5],O:[.35,1.45]};

// ---------- reading the ledger: which branch, who saw ----------
function plan(ev,st){const A=ev.A,V=ev.V;const bm=(st.evidence||[]).find(e=>e.deed==='blackmail')||null;
 const guilt=((st.mind[A]||{})[V]||{}).guilt||0;let br='rinse';
 if(bm&&bm.A===V&&bm.V===A)br='photo';               // the sleeper holds a photograph of the doer: the doer burns it
 else if(guilt>.3)br='veil';                         // guilt (Belindo): he stays and covers the sleeper with lace
 else if((st.body[V]||[]).includes('coins'))br='coins'; // the sleeper's coins are lifted and counted
 // who saw: the third party of the house's other secret looks in at the door
 let wit=null;if(bm){for(const c of[bm.A,bm.V])if(c!==A&&c!==V&&st.alive[c]){wit=c;break}}
 const dead=!st.alive[V],deadA=!st.alive[A];
 return{br,wit,dead,deadA,guilt}}
function lev(st,id){const l=(st.levers||{})[id]||{};return{loom:l.loom||0,weight:l.weight||0,tempo:l.tempo||0,halo:l.halo||0,shadow:l.shadow||0,shrink:l.shrink||0,grey:l.grey||0}}

// ---------- sack geometry: polygon in local coords (origin base centre, y up negative) ----------
function poly(id,w,h,ear){const P=[],N=18;
 const ex=id==='I'||id==='O'?0:w*.035,ey=id==='I'?-h*.02:id==='O'?h*.01:h*(.02+.07*ear);
 for(let i=0;i<=N;i++){const u=i/N;P.push([lerp(-w/2,w/2,u),2*Math.sin(Math.PI*u)])}               // bottom
 for(let i=1;i<=N;i++){const u=i/N;P.push([w/2*(1+.05*Math.sin(Math.PI*u)-.05*u*u*u),-h*u*.96])}   // right side
 P.push([w/2+ex,-h-ey]);                                                                           // right ear
 for(let i=1;i<N;i++){const u=i/N;P.push([lerp(w/2*.92,-w/2*.92,u),-h*.97+h*.04*Math.sin(Math.PI*u)])} // top (dip)
 P.push([-w/2-ex,-h-ey]);                                                                          // left ear
 for(let i=N;i>=1;i--){const u=i/N;P.push([-w/2*(1+.05*Math.sin(Math.PI*u)-.05*u*u*u),-h*u*.96])}  // left side
 return P}
function pathOf(g,P){g.beginPath();g.moveTo(P[0][0],P[0][1]);for(let i=1;i<P.length;i++)g.lineTo(P[i][0],P[i][1]);g.closePath()}
// pose -> transform on g; returns local w,h actually used
function enter(g,s){const M=MAT[s.id];const k=s.k;const w=M.w*(1+(1-s.sq)*.5),h=M.h*s.sq;
 g.translate(s.x,FY);g.scale(k,k);
 if(s.lie>0){g.translate(w/2,0);g.rotate(s.lie*Math.PI/2);g.translate(-w/2,0)}
 g.rotate(s.lean||0);return{w,h}}
// local -> world (same maths as enter), for strands that obey world gravity
function l2w(s,lx,ly){const M=MAT[s.id];const k=s.k;const w=M.w*(1+(1-s.sq)*.5);let x=lx,y=ly;
 const c0=Math.cos(s.lean||0),s0=Math.sin(s.lean||0);[x,y]=[x*c0-y*s0,x*s0+y*c0];
 if(s.lie>0){const a=s.lie*Math.PI/2,c=Math.cos(a),sn=Math.sin(a);x-=w/2;[x,y]=[x*c-y*sn,x*sn+y*c];x+=w/2}
 return[s.x+x*k,FY+y*k]}

// the matte-native sack: spill halo, premultiplied body fill, attribute, fibre edge texture
function drawSack(g,s,o){const M=MAT[s.id];const lv=o.lv;
 let col=mix(M.col,[138,136,130],lv.grey*.8);col=mix(col,GREEN,o.tint||0);if(o.back)col=mix(col,[30,24,22],.72);
 const al=o.alpha??1;
 g.save();const{w,h}=enter(g,s);const P=poly(s.id,w,h,s.ear);
 // floor shadow (in local frame, only when upright-ish)
 // spill halo: the drug's colour contamination at the edge
 if(o.spill>0.01){g.save();g.lineJoin='round';pathOf(g,P);for(const[lw,a]of[[34,.07],[20,.11],[9,.18]]){g.strokeStyle=rgba(GREEN,a*o.spill*al*1.4);g.lineWidth=lw*o.spill/s.k*1.6;g.stroke()}g.restore()}
 pathOf(g,P);
 const gr=g.createLinearGradient(-w/2,-h,w/2,0);gr.addColorStop(0,rgba(mix(col,[255,240,210],.25),al));gr.addColorStop(1,rgba(mix(col,[60,40,30],.28),al));
 g.fillStyle=gr;g.fill();
 g.save();pathOf(g,P);g.clip();
 if(s.id==='R'){// lace shawl: band with punched holes (evenodd) and a scalloped lace edge
  g.beginPath();g.rect(-w,-h*1.2,w*2,h*.2+h*.2);const r=3.2;for(let yy=-h*.93;yy<-h*.8;yy+=9)for(let xx=-w/2;xx<w/2;xx+=10){const ox=((yy/9|0)&1)*5;g.moveTo(xx+ox+r,yy);g.arc(xx+ox,yy,r,0,7)}
  g.fillStyle=rgba(mix([110,58,51],GREEN,(o.tint||0)*.5),.92*al);g.fill('evenodd');
  g.beginPath();for(let xx=-w/2;xx<w/2;xx+=12){g.moveTo(xx,-h*.8);g.arc(xx+6,-h*.8,6,Math.PI,0,true)}g.fillStyle=rgba([110,58,51],.55*al);g.fill()}
 if(s.id==='B'){g.fillStyle=rgba([42,38,34],al);g.fillRect(-w,-h*.44,w*2,h*.08);
  g.strokeStyle=rgba([120,90,60],.8*al);g.lineWidth=4;g.beginPath();g.arc(0,-h*.68,h*.13,0,7);g.stroke();
  g.beginPath();g.moveTo(0,-h*.58);g.lineTo(0,-h*.78);for(let k=0;k<3;k++){const yy=-h*(.63+k*.05);g.moveTo(0,yy);g.lineTo(-10,yy-9);g.moveTo(0,yy);g.lineTo(10,yy-9)}g.stroke()}
 if(o.patch){// residue edge of something lifted from the body (the photograph): a clean patch with a fringe
  g.fillStyle=rgba([255,250,236],.35*al);g.fillRect(-w*.18,-h*.6,w*.36,h*.26);g.setLineDash([3,3]);g.strokeStyle=rgba([90,70,50],.5*al);g.lineWidth=1.5;g.strokeRect(-w*.18,-h*.6,w*.36,h*.26);g.setLineDash([])}
 g.restore();
 // fibre edge texture: short strands along the outward normal at partial alpha
 const fc=o.back?[255,214,150]:mix(col,GREEN,clamp(0,1,o.spill*.8));g.strokeStyle=rgba(fc,(o.back?.85:.45)*al);g.lineWidth=o.back?1.6:1.1;g.beginPath();
 for(let i=1;i<P.length-1;i+=1){const a=P[i-1],b=P[i+1],p=P[i];let nx=b[1]-a[1],ny=-(b[0]-a[0]);const L=Math.hypot(nx,ny)||1;nx/=L;ny/=L;
  if(nx*p[0]+ny*(p[1]+h/2)<0){nx=-nx;ny=-ny}
  for(let j=0;j<2;j++){const r=H(i*7.1+j*3.3+s.seed),ln=1.5+4*r,ox=(H(i*1.9+j)-.5)*4;g.moveTo(p[0]+ox*ny,p[1]-ox*nx);g.lineTo(p[0]+ox*ny+nx*ln+(r-.5)*2,p[1]-ox*nx+ny*ln)}}
 g.stroke();
 g.restore();
 // strands in world space: Inigo's hanging ears, Ogiva's wig
 if(s.id==='I')earLobes(g,s,o,col,w,h);
 if(s.id==='O')wig(g,s,o,w,h);
 if(o.lvHalo>0.02){const c=l2w(s,0,-h*.9);const hg=g.createRadialGradient(c[0],c[1],4,c[0],c[1],M.h*s.k*.9);hg.addColorStop(0,`rgba(255,230,180,${.32*o.lvHalo*al})`);hg.addColorStop(1,'rgba(255,230,180,0)');g.fillStyle=hg;g.fillRect(c[0]-400,c[1]-400,800,800)}
}
// Inigo's ears: two cloth lobes hanging beside him to the floor like long unwashed hair; their tips fray into strands
function earLobes(g,s,o,col,w,h){const al=o.alpha??1;const c=mix(col,[110,92,64],.3);const lift=s.earLift||0;
 for(const side of[-1,1]){const r0=l2w(s,side*w*.47,-h*.96);const L=h*s.k*(.95-.55*lift),ww=w*.2*s.k;const sw=Math.sin((o.t||0)*1.4+side)*3;
  const tip=[r0[0]+side*(ww*.9+lift*30*s.k)+sw,Math.min(FY-2,r0[1]+L)];
  g.fillStyle=rgba(mix(c,GREEN,(o.spill||0)*.3),.97*al);g.beginPath();g.moveTo(r0[0]-side*ww*.15,r0[1]);g.quadraticCurveTo(r0[0]+side*ww*1.4,r0[1]+L*.2,tip[0]+side*ww*.5,tip[1]);
  g.lineTo(tip[0]-side*ww*.5,tip[1]);g.quadraticCurveTo(r0[0]+side*ww*.2,r0[1]+L*.5,r0[0]-side*ww*.15,r0[1]);g.fill();
  g.strokeStyle=rgba(mix(c,[60,48,34],.3),.55*al);g.lineWidth=1.2;g.beginPath();
  for(let i=0;i<14;i++){const u=i/13-.5,x=tip[0]+u*ww,r=H(i*3.1+side*7),Lh=(6+16*r)*s.k;g.moveTo(x,tip[1]-4);g.lineTo(x+(r-.5)*8+sw,Math.min(FY+1,tip[1]+Lh-6*lift))}
  for(let i=0;i<10;i++){const u=i/9,x=lerp(r0[0],tip[0],u)+side*ww*(.6+.5*Math.sin(Math.PI*u)),y=lerp(r0[1],tip[1],u);g.moveTo(x,y);g.lineTo(x+side*(3+5*H(i+side)),y+6)}g.stroke()}}
// a hanging strand bundle from each top corner, falling under world gravity (fractional alpha per strand)
function strands(g,s,o,sides,n,len,col,lw,w,h){const al=o.alpha??1;
 for(const[side]of sides){const root=l2w(s,side*w*.46,-h*.95);
  for(let i=0;i<n;i++){const r=H(i*3.7+side*11+s.seed),r2=H(i*9.1+side*5);const sp=(r-.5)*14*s.k;
   const sway=Math.sin((o.t||0)*1.7+i*.6)*3;const L=len*s.k*(.75+.35*r2);
   const x0=root[0]+sp*.4,y0=root[1];const out=side*(10+18*r)*s.k*(1-s.earLift*.3);
   const x1=x0+out+sway,y1=y0+L*.5-s.earLift*L*.6,x2=x0+out*.6+sway*2,y2=Math.min(FY+2,y0+L-s.earLift*L*.9);
   g.strokeStyle=rgba(mix(col,GREEN,clamp(0,1,o.spill*.6)),(.25+.5*r2)*al);g.lineWidth=lw*(.6+r);
   g.beginPath();g.moveTo(x0,y0);g.quadraticCurveTo(x1,y1,x2,y2);g.stroke()}}}
function wig(g,s,o,w,h){const al=o.alpha??1;const ask=o.wigAsk||0;const P=o.back?[60,30,70]:[122,59,143];const pc=c=>mix(c,GREEN,(o.spill||0)*.35);
 const tilt=(s.lean||0)+s.lie*Math.PI/2+ask*.45;const lie=s.lie>.5;const k=s.k;
 const root=u=>l2w(s,u*w*.62+ask*w*.3,-h*1.0+Math.abs(u)*h*.06);
 // long side curtains: strands rooted along the cap rim, falling in world space just outside the body edge
 for(let i=0;i<40;i++){const side=i<20?-1:1,j=i%20,r=H(i*5.3+1),r2=H(i*2.1+7);const u=side*(.72+.42*j/19);
  const R0=root(u);const L=(lie?50:h*.66*k)*(.75+.4*r);const out=lie?0:side*(4+10*r)*k;const sway=Math.sin((o.t||0)*1.3+i)*2.2;const fly=j%7===3;
  g.strokeStyle=rgba(pc(fly?[176,120,196]:P),(fly?.35:.6+.35*r2)*al);g.lineWidth=fly?.8:1.4+1.2*r;
  g.beginPath();g.moveTo(R0[0],R0[1]);g.quadraticCurveTo(R0[0]+out*1.6+sway,R0[1]+L*.45,R0[0]+out+sway*1.6+(fly?side*12:0),Math.min(FY+1,R0[1]+L));g.stroke()}
 // the cap: a soft dome wider than the head
 const C=root(0);g.save();g.translate(C[0],C[1]);g.rotate(tilt);g.fillStyle=rgba(pc(P),.97*al);g.beginPath();g.ellipse(0,6*k,w*.66*k,h*.13*k,0,Math.PI,0);g.quadraticCurveTo(w*.6*k,h*.09*k,w*.5*k,h*.1*k);g.lineTo(-w*.5*k,h*.1*k);g.quadraticCurveTo(-w*.6*k,h*.09*k,-w*.66*k,6*k);g.fill();
 // fringe: short strands at fractional alpha over the brow
 g.strokeStyle=rgba(pc(P),.55*al);g.lineWidth=1.1;g.beginPath();for(let i=0;i<22;i++){const x=(i/21-.5)*w*1.1*k,L=(6+10*H(i*3.7))*k;g.moveTo(x,h*.08*k);g.lineTo(x+(H(i)-.5)*3,h*.08*k+L)}g.stroke();g.restore()}

// floor shadow + the lamp-cast wall shadow (the shadow lever lengthens and darkens it)
function shadow(g,s,lv,al){const M=MAT[s.id];const w=M.w*s.k*(1+(1-s.sq)*.5)*(s.lie>.5?M.h/M.w*.9:1);const cx=s.x+(s.lie>.5?w*.35:0);
 g.fillStyle=`rgba(0,0,0,${(.32+.3*lv.shadow)*al})`;g.beginPath();g.ellipse(cx,FY+4,w*.6*(1+.5*lv.shadow),10+6*lv.shadow,0,0,7);g.fill();
 if(lv.shadow>.05){const dir=s.x<960?-1:1;const hh=M.h*s.k*s.sq*(1+1.6*lv.shadow);g.fillStyle=`rgba(0,0,0,${.18*lv.shadow*al})`;
  g.beginPath();g.moveTo(s.x-w*.45,FY-118);g.lineTo(s.x+w*.45,FY-118);g.lineTo(s.x+w*.45+dir*hh*.35,FY-118-hh);g.lineTo(s.x-w*.45+dir*hh*.35,FY-118-hh);g.fill()}}

function room(g,t,pl,doorOpen){
 let gr=g.createLinearGradient(0,0,0,FY);gr.addColorStop(0,'#14131a');gr.addColorStop(1,'#272029');g.fillStyle=gr;g.fillRect(0,0,1920,FY);
 g.fillStyle='rgba(255,255,255,.025)';for(let x=0;x<1920;x+=48)g.fillRect(x,0,18,FY-120);
 // the door (back right): ajar while someone looks in
 const dx=1590,dw=150,dt=FY-370;g.fillStyle='#1a1412';g.fillRect(dx-8,dt-8,dw+16,370+8);g.fillStyle='#2e2420';g.fillRect(dx,dt,dw,370);
 if(doorOpen>0.01){const gap=dw*.75*doorOpen;const lg=g.createLinearGradient(dx,0,dx+gap,0);lg.addColorStop(0,'rgba(255,214,150,.75)');lg.addColorStop(1,'rgba(255,190,120,.35)');g.fillStyle=lg;g.fillRect(dx,dt,gap,370);
  g.fillStyle='rgba(255,205,140,.12)';g.beginPath();g.moveTo(dx,FY);g.lineTo(dx+gap,FY);g.lineTo(dx+gap*3-200,1080);g.lineTo(dx-260,1080);g.fill()}
 g.fillStyle='#3a2c26';g.fillRect(dx+(doorOpen>0.01?dw*.75*doorOpen:0),dt,6,370);
 g.fillStyle='#1d1715';g.fillRect(0,FY-120,dx-8,120);g.fillRect(dx+dw+8,FY-120,1920,120);g.fillStyle='#2b211c';g.fillRect(0,FY-124,dx-8,6);g.fillRect(dx+dw+8,FY-124,1920,6);
 gr=g.createLinearGradient(0,FY,0,1080);gr.addColorStop(0,'#3a2a1f');gr.addColorStop(1,'#1c1510');g.fillStyle=gr;g.fillRect(0,FY,1920,280);
 g.strokeStyle='rgba(0,0,0,.35)';g.lineWidth=2;for(let k=-12;k<14;k++){g.beginPath();g.moveTo(960+k*60,FY);g.lineTo(960+k*190,1080);g.stroke()}
 const lg=g.createRadialGradient(960,370,10,960,640,780);lg.addColorStop(0,'rgba(255,214,150,.40)');lg.addColorStop(.5,'rgba(255,190,120,.13)');lg.addColorStop(1,'rgba(255,190,120,0)');g.fillStyle=lg;g.fillRect(0,0,1920,1080);
 g.strokeStyle='#0c0b0d';g.lineWidth=3;g.beginPath();g.moveTo(960,0);g.lineTo(960,320);g.stroke();
 g.fillStyle='#17151a';g.beginPath();g.moveTo(930,320);g.lineTo(990,320);g.lineTo(1012,350);g.lineTo(908,350);g.fill();g.fillStyle='rgba(255,226,170,.95)';g.beginPath();g.ellipse(960,350,40,7,0,0,7);g.fill();
 // table
 g.fillStyle='#4a2f1e';g.fillRect(TX0+20,TY+12,15,FY-TY-12);g.fillRect(TX1-35,TY+12,15,FY-TY-12);
 g.fillStyle='#6a4428';g.fillRect(TX0-8,TY,TX1-TX0+16,16);g.fillStyle='#8a5c36';g.fillRect(TX0-8,TY,TX1-TX0+16,4);g.fillStyle='#3b2618';g.fillRect(TX0+5,TY+16,TX1-TX0-10,12)}

// the cup and its residue: a residue edge never fully decontaminates
function cup(g,x,y,rinsed,t,al=1){const w=56,h=66;
 // ring stain on the table under it
 g.fillStyle=`rgba(110,160,70,${(rinsed?.25:.5)*al})`;g.beginPath();g.ellipse(x+(rinsed?40:0),y+2,w*.62,6,0,0,7);g.fill();
 g.fillStyle=`rgba(235,232,220,${.92*al})`;g.beginPath();g.moveTo(x-w/2,y-h);g.lineTo(x+w/2,y-h);g.lineTo(x+w*.4,y);g.lineTo(x-w*.4,y);g.closePath();g.fill();
 g.strokeStyle=`rgba(235,232,220,${.92*al})`;g.lineWidth=7;g.beginPath();g.arc(x+w*.5,y-h*.55,13,-1.2,1.2);g.stroke();
 // dregs + residue line inside the rim (a soft-edged green band); after rinsing only the edge remains
 const rg=g.createLinearGradient(0,y-h,0,y-h*.55);rg.addColorStop(0,`rgba(143,208,94,${(rinsed?.55:.85)*al})`);rg.addColorStop(1,'rgba(143,208,94,0)');
 g.fillStyle=rg;g.fillRect(x-w/2+4,y-h+2,w-8,h*.45);
 if(!rinsed){g.fillStyle=`rgba(120,180,70,${.9*al})`;g.beginPath();g.ellipse(x,y-h+5,w*.42,5,0,0,7);g.fill();
  g.fillStyle=`rgba(143,208,94,${.7*al})`;g.beginPath();g.moveTo(x+w*.3,y-h+4);g.quadraticCurveTo(x+w*.36,y-h*.5,x+w*.33,y-h*.3+3*Math.sin(t*2));g.lineTo(x+w*.27,y-h*.3);g.quadraticCurveTo(x+w*.3,y-h*.6,x+w*.24,y-h+4);g.fill()}
 g.strokeStyle=`rgba(160,220,110,${(.45+.15*Math.sin(t*5))*al})`;g.lineWidth=2;g.beginPath();g.moveTo(x-w/2,y-h);g.lineTo(x+w/2,y-h);g.stroke()}

// lace veil (guilt branch): a draped cloth with punched holes and a strand fringe
function veil(g,cx,top,wd,ht,off,drop,al){g.save();g.translate(cx+off,top+drop);g.rotate(off*.0015);
 g.beginPath();g.moveTo(-wd/2,0);g.quadraticCurveTo(0,-ht*.18,wd/2,0);g.lineTo(wd/2+10,ht);for(let x=wd/2+10;x>-wd/2-10;x-=16)g.arc(x-8,ht,8,0,Math.PI);g.lineTo(-wd/2-10,ht);g.closePath();
 for(let yy=8;yy<ht-6;yy+=14)for(let xx=-wd/2+6;xx<wd/2;xx+=14){const ox=((yy/14|0)&1)*7,r=3.4+1.2*Math.sin(xx*.3+yy*.2);g.moveTo(xx+ox+r,yy);g.arc(xx+ox,yy,r,0,7)}
 g.fillStyle=`rgba(244,240,228,${.62*al})`;g.fill('evenodd');
 g.strokeStyle=`rgba(244,240,228,${.35*al})`;g.lineWidth=1;g.beginPath();for(let x=-wd/2-10;x<wd/2+10;x+=5){const L=8+10*H(x);g.moveTo(x,ht+6);g.lineTo(x+(H(x*3)-.5)*4,ht+6+L)}g.stroke();g.restore()}

function coinAt(g,x,y,al,a=1){g.fillStyle=`rgba(170,130,40,${al*a})`;g.beginPath();g.ellipse(x,y,22,7,0,0,7);g.fill();g.fillStyle=`rgba(245,210,110,${al*a})`;g.beginPath();g.ellipse(x,y-3,22,7,0,0,7);g.fill()}

// ---------- the smoke matte: fractional alpha field, low-res, upsampled ----------
let HZ=null,BIG=null,MID=null;
function up(src){if(!MID){MID=document.createElement('canvas');MID.width=240;MID.height=135}const q=MID.getContext('2d');q.clearRect(0,0,240,135);q.imageSmoothingEnabled=true;q.filter='blur(3.5px)';q.drawImage(src,-6,-6,252,147);q.filter='none';return MID}
function hazeField(t,p,vx,vy,thr){if(!HZ){HZ=document.createElement('canvas');HZ.width=96;HZ.height=54}
 const q=HZ.getContext('2d'),im=q.createImageData(96,54),d=im.data;
 for(let y=0;y<54;y++)for(let x=0;x<96;x++){const n=.65*vn(x*.1+t*.32,y*.14-t*.1)+.35*vn(x*.24-t*.45,y*.28+t*.18);
  const X=x*20,Y=y*20;const vg=Math.pow((x/96-.5)*2,2)*.7+Math.pow((y/54-.5)*2,2)*.5;
  const known=Math.exp(-((X-vx)*(X-vx)+(Y-vy)*(Y-vy))/(2*300*300));
  let a;if(thr){a=clamp(0,1,(n-thr)*5)}else{const f=1-p;a=clamp(0,1,f*1.3*(.45+.9*n)-known*f*.95+vg*.32*(.6+.7*n)*(.55+.45*f))}
  const i=(y*96+x)*4;d[i]=226+n*20;d[i+1]=238;d[i+2]=204-known*20;d[i+3]=a*255}
 q.putImageData(im,0,0);return HZ}

// ---------- the beat ----------
const MK={};// cache of the deed's end marks per pair (a pure function of A,V)
function scene(ev,st,X,K){const A=ev.A,V=ev.V;let mA=null,mV=null;
 try{const D=(window.DEEDS||{}).drugging;if(D&&D.marks){const m=MK[A+V]||(MK[A+V]=D.marks(5.95,A,V,K));mA=m.A;mV=m.V}}catch(e){}
 let ax=mA?mA.x+mA.w/2:640,vx=mV?mV.x+mV.w/2:1300;ax=clamp(380,TX0-MAT[A].w*S*.5-6,ax);vx=clamp(TX1+MAT[V].w*S*.55,1460,vx);
 return{ax,vx}}

function poseV(V,t,pl,lvV,vx){const[w0,w1]=WAKE[V];const u=eo(w0,w1,t);const sh=lvV.shrink;
 const s={id:V,x:vx,sq:1,lean:0,lie:0,ear:0,earLift:0,k:S*(1+.12*clamp(-1,1,lvV.loom)-.16*sh),seed:7};
 if(V==='R'){s.sq=lerp(.55,.93,u);s.lean=.07*Math.sin(t*5.5)*u*(1-sm(2.3,2.9,t));s.ear=(.15+.55*u)*(1-.5*sh)}
 if(V==='B'){s.sq=lerp(.6,.9,u);s.lean=.06*Math.sin((t-w0)*10)*sm(w0,w0+.2,t)*(1-sm(w1,w1+.7,t));s.ear=(.1+.4*u)*(1-.5*sh)}
 if(V==='I'){s.sq=lerp(.45,.78,u)-.2*sm(2.2,3.0,t);s.earLift=.6*Math.sin(Math.PI*sm(.8,2.1,t))*(1-.4*sh)}
 if(V==='O'){s.lie=1-u;s.ear=.5*u*(1-.5*sh);s.x=vx-(1-u)*MAT.O.h*S*.3}
 // branch gestures after waking
 if(pl.br==='coins')s.lean+=-.13*sm(1.8,2.3,t)*(V==='O'?.5:1);
 if(pl.br==='photo'){s.sq*=1-.05*Math.max(0,Math.sin((t-1.9)*22))*sm(1.85,1.95,t)*(1-sm(2.45,2.6,t))}
 if(pl.br==='rinse')s.lean+=-.06*sm(2.0,2.5,t);
 if(pl.wit)s.lean+=.09*sm(1.4,1.7,t)*(1-sm(2.3,2.7,t));
 if(pl.dead){s.sq=V==='O'?1:.55;s.lie=V==='O'?1:0;s.lean=0;s.ear=0;s.earLift=0}
 return s}

function poseA(A,t,pl,lvA,ax,vx){const tm=1+.35*clamp(-1,1,lvA.tempo);const T=t*tm;const M=MAT[A];
 const s={id:A,x:ax,sq:1-.02*lvA.weight,lean:.05*clamp(-1,1,lvA.loom),lie:0,ear:.5,earLift:0,k:S*(1+.12*clamp(-1,1,lvA.loom)-.16*lvA.shrink),seed:3};
 if(pl.br==='photo'){s.ear=.8*(1-sm(1.9,2.4,T));s.lean+=-.05*sm(.2,.6,T)*(1-sm(1.8,2.3,T))}
 if(pl.br==='coins'){s.lean+=.02*Math.sin(T*9)*sm(.2,.4,T)*(1-sm(2.1,2.3,T));s.ear=.6+.3*sm(1.9,2.4,T)}
 if(pl.br==='veil'){const near=vx-(MAT[pl.V].w*.5+M.w*.5)*S-75;s.x=lerp(near,ax,eo(1.5,2.6,T));s.lean+=.08*(1-sm(1.4,1.9,T));s.ear=.1;s.sq*=1-.04*(1-sm(1.4,2.2,T))}
 if(pl.br==='rinse'){s.lean+=.06*sm(1.5,1.8,T)*(1-sm(1.9,2.2,T))-.08*sm(2.2,2.7,T);s.x=ax-120*eo(2.1,3.0,T)}
 if(A==='I'){s.sq=.85;s.earLift=.1}
 return{s,T}}

function beat(g,t,ev,st,K,X){const pl=plan(ev,st);pl.V=ev.V;const A=ev.A,V=ev.V;const lvA=lev(st,A),lvV=lev(st,V);
 const{ax,vx}=scene(ev,st,X,K);
 const[w0,w1]=WAKE[V];const p=pl.dead?0:sm(.1,w1+.15,t);              // waking progress (matte solve)
 const spillW=pl.dead?1:lerp(1,.0,sm(.2,w1+.6,t));                       // the room decontaminates
 const spillV=Math.max(.42,lerp(1,.42,sm(.3,w1+.8,t)));                  // the sleeper keeps its residue
 const doorOpen=pl.wit?(sm(.4,.7,t)*(1-sm(2.0,2.4,t))):0;
 room(g,t,pl,doorOpen);
 // witness at the door: only its edge is known (unknown region of the trimap)
 if(pl.wit&&doorOpen>.02){const wl=lev(st,pl.wit);const ws={id:pl.wit,x:1590+30+MAT[pl.wit].w*.5*.95-MAT[pl.wit].w*.95*sm(1.6,2.1,t),sq:1,lean:-.04,lie:0,ear:.7,earLift:.2,k:.95*(1+.1*wl.loom),seed:11};
  g.save();g.beginPath();g.rect(1590,FY-370,150*.75*doorOpen+2,370);g.clip();
  drawSack(g,ws,{lv:wl,alpha:.9*doorOpen,spill:0,tint:0,t,lvHalo:0,back:1});g.restore()}
 const{s:sA,T}=poseA(A,t,pl,lvA,ax,vx);const sV=poseV(V,t,pl,lvV,vx);
 const ghost=sm(.0,.3,t);
 // the cup: rinse branch -> the doer holds it, wipes it, sets it down
 let cupX=CUPX,cupY=TY,held=false;
 if(pl.br==='rinse'&&T<1.7){held=true;const hx=sA.x+MAT[A].w*sA.k*.5+30,hy=FY-MAT[A].h*sA.k*.55;cupX=lerp(hx,CUPX-70,sm(1.4,1.7,T));cupY=lerp(hy,TY,sm(1.4,1.7,T))}
 if(pl.br==='rinse'&&T>=1.7)cupX=CUPX-70;
 shadow(g,sA,lvA,1);shadow(g,sV,lvV,1);
 if(!held)cup(g,cupX,cupY,pl.br==='rinse'&&T>1.5,t);
 // coins branch: the clean patch where the sleeper's coins were (a residue edge on the dusty boards)
 if(pl.br==='coins'){const px=sV.x-MAT[V].w*S*.62-26;g.fillStyle='rgba(120,95,70,.35)';g.beginPath();g.ellipse(px,FY+14,44,13,0,0,7);g.fill();
  g.strokeStyle='rgba(251,247,238,.35)';g.setLineDash([4,4]);g.lineWidth=2;g.beginPath();g.ellipse(px,FY+14,44,13,0,0,7);g.stroke();g.setLineDash([])}
 // the victim
 if(pl.br==='veil'&&t<w0+.5){}
 drawSack(g,sV,{lv:lvV,spill:spillV,tint:.22*spillV,t,patch:pl.br==='photo'&&t>1.7,wigAsk:V==='O'?.7*(1-sm(1.8,2.5,t)):0,lvHalo:lvV.halo,alpha:1});
 if(pl.br==='veil'){const M=MAT[V];const top=FY-M.h*S*sV.sq*(sV.lie>.5?.45:1)-14;const wd=(sV.lie>.5?M.h:M.w)*S*1.15;
  const off=180*eo(w0+.2,w0+1.0,t),drop=(FY-top-40)*sm(w0+.5,w0+1.1,t);veil(g,sV.x+(sV.lie>.5?M.h*S*.35:0),top,wd,lerp(M.h*S*sV.sq*.6,34,sm(w0+.5,w0+1.1,t)),off,drop,1)}
 // the doer
 drawSack(g,sA,{lv:lvA,spill:spillW*.8,tint:0,t,lvHalo:lvA.halo,alpha:1,wigAsk:0});
 if(held)cup(g,cupX,cupY,T>1.0,t);
 if(pl.br==='rinse'&&T>=1.6){// the rag keeps the green: it hangs from the doer's side, stained
  const r0=l2w(sA,MAT[A].w*.5,-MAT[A].h*.55);g.fillStyle='rgba(236,226,200,.85)';g.beginPath();g.moveTo(r0[0],r0[1]);g.lineTo(r0[0]+22,r0[1]+4);g.lineTo(r0[0]+18,r0[1]+44);g.lineTo(r0[0]+2,r0[1]+40);g.fill();
  g.fillStyle='rgba(143,208,94,.6)';g.beginPath();g.ellipse(r0[0]+11,r0[1]+26,7,9,0,0,7);g.fill()}
 if(pl.br==='rinse'&&T<1.6){// cloth wiping in circles over the held cup
  const a=T*11;const cx=cupX+14*Math.cos(a),cy=cupY-40+9*Math.sin(a);g.fillStyle='rgba(236,226,200,.8)';g.beginPath();g.ellipse(cx,cy,26,14,a*.2,0,7);g.fill();
  g.strokeStyle='rgba(236,226,200,.4)';g.lineWidth=1;g.beginPath();for(let k=0;k<10;k++){const xx=cx-22+k*5;g.moveTo(xx,cy+10);g.lineTo(xx+(H(k)-.5)*5,cy+18+6*H(k*3))}g.stroke()}
 if(pl.br==='coins'){// coins set down one by one on the table edge in front of the doer; pride counts them
  const n=5,base=TX0+40;for(let i=0;i<n;i++){const td=.35+i*.36;const u=sm(td,td+.12,T);if(u<=0){continue}
   const hx=sA.x+MAT[A].w*sA.k*.45,hy=FY-MAT[A].h*sA.k*.6;coinAt(g,lerp(hx,base,u),lerp(hy,TY-3-i*7,u),1)}
  if(T<.35+4*.36){coinAt(g,sA.x+MAT[A].w*sA.k*.45,FY-MAT[A].h*sA.k*.6,1)}}
 if(pl.br==='photo'){// the photograph held to the lamp: it curls, burns along its edge and goes to smoke
  const top=l2w(sA,MAT[A].w*.5,-MAT[A].h*.95);const px=lerp(top[0]+20,Math.min(900,top[0]+160),sm(.1,.6,T)),py=lerp(top[1]-10,Math.max(380,top[1]-140),sm(.1,.6,T));
  const burn=sm(.6,1.9,T);if(burn<1){g.save();g.translate(px,py);g.rotate(-.2+.5*burn);const w=96*(1-burn*.8),h=72*(1-burn*.6);
   g.fillStyle='rgba(240,236,224,.95)';g.fillRect(-w/2,-h/2,w,h);g.fillStyle='rgba(60,50,48,.9)';g.fillRect(-w/2+5,-h/2+5,w-10,h-14);
   if(burn>0){g.shadowColor='rgba(255,140,40,.9)';g.shadowBlur=18;g.strokeStyle='rgba(255,150,60,.95)';g.lineWidth=3;g.beginPath();g.moveTo(-w/2,h/2);g.lineTo(w/2,h/2);g.lineTo(w/2,h/2-h*burn*.6);g.stroke()}
   g.restore()}
  // smoke puffs: premultiplied soft discs drifting up (translucency intended)
  for(let i=0;i<34;i++){const t0=.6+i*.05;if(T<t0)continue;const a=T-t0;if(a>2.4)continue;const r=H(i*4.1);
   const sx=px+(r-.5)*30+Math.sin(a*2+i)*18*a,sy=py-a*110-r*20,rad=10+a*36;const al=.34*(1-a/2.4)*(1-.3*r);
   const sg=g.createRadialGradient(sx,sy,0,sx,sy,rad);sg.addColorStop(0,`rgba(200,196,190,${al})`);sg.addColorStop(.6,`rgba(180,176,170,${al*.5})`);sg.addColorStop(1,'rgba(180,176,170,0)');g.fillStyle=sg;g.fillRect(sx-rad,sy-rad,rad*2,rad*2)}
  // ash flakes
  for(let i=0;i<8;i++){const t0=1.0+i*.12;if(T<t0)continue;const a=T-t0;g.fillStyle=`rgba(40,36,34,${.7})`;g.fillRect(px+(H(i)-.5)*40+Math.sin(a*4+i)*8,Math.min(FY-2,py+a*a*120+a*30),4,3)}}
 // continuity: the deed's last frame fades out under the thick early haze
 if(X&&X.still&&t<.8){try{const st0=X.still(ev,5.95);g.save();g.globalAlpha=1-sm(.0,.8,t);g.drawImage(st0,0,0);g.restore()}catch(e){}}
 // the haze of the sleeper's sight
 const vyc=FY-MAT[V].h*S*.5;
 const hz=hazeField(t,p,sV.x,vyc,0);g.save();g.imageSmoothingEnabled=true;g.globalAlpha=pl.dead?.9:1;g.drawImage(up(hz),0,0,1920,1080);g.restore();
}

// ---------- sound: grains ----------
function sound(ac,out0,t0,ev,st,K){const S2=K.SND;const out=ac.createGain();out.gain.value=3;out.connect(out0);const pl=plan(ev,st);const A=ev.A,V=ev.V;const at=x=>t0+x;
 const lvA=lev(st,A);const tm=1+.35*clamp(-1,1,lvA.tempo);const pA=-.45,pV=.4;
 // the haze: a noise bed whose band rises as the sight clears (low and smothered -> airy)
 for(let i=0;i<6;i++)S2.cloud(ac,out,at(i*.28),.4,40,{bp:300*Math.pow(1.45,i),q:1.2,a:.03*(1-i/8),d:[.08,.2],spread:.9},u=>Math.sin(Math.PI*u));
 const[w0,w1]=WAKE[V];
 S2.say(ac,out,V,at(.1),'breathe',.9,pV);
 if(!pl.dead){S2.say(ac,out,V,at(w0+.25),'react',V==='I'?.5:.9,pV);if(V==='B')S2.say(ac,out,V,at(w1),'land',.8,pV);else S2.say(ac,out,V,at(w1),'step',.6,pV);
  // the strongest grain: the waking edge clears — a high glass shimmer resolving to one tone
  S2.cloud(ac,out,at(w0+.2),.6,90,{pitches:[88,95,100],a:.03,d:[.03,.08],spread:.3},u=>u*(1-u)*4);S2.grain(ac,out,at(w1+.1),{f:1760,d:.5,a:.2,pan:pV,att:.1});S2.grain(ac,out,at(w1+.1),{f:880,d:.7,a:.12,pan:pV,att:.1})}
 if(pl.br==='coins'){for(let i=0;i<5;i++){const td=(.35+i*.36+.12)/tm;S2.grain(ac,out,at(td),{f:2900+i*120,d:.06,a:.16,pan:pA+.2,att:.05});S2.grain(ac,out,at(td+.012),{f:1400,d:.05,a:.06,pan:pA+.2})}
  S2.say(ac,out,A,at(2.0/tm),'tick',.7,pA);S2.say(ac,out,V,at(1.9),'sink',.5,pV)}
 if(pl.br==='photo'){S2.cloud(ac,out,at(.6/tm),1.3/tm,110,{bp:3200,q:2,a:.05,d:[.004,.02],spread:.2},u=>Math.sin(Math.PI*u));S2.cloud(ac,out,at(.9/tm),1.6,30,{bp:700,a:.02,d:[.1,.3],spread:.3},u=>1-u);
  for(let i=0;i<4;i++)S2.grain(ac,out,at(1.92+i*.14),{bp:500,q:2,d:.05,a:.1,pan:pV})}
 if(pl.br==='veil'){S2.cloud(ac,out,at(w0+.2),.9,60,{bp:1400,q:.8,a:.03,d:[.04,.12],spread:.4},u=>Math.sin(Math.PI*u));S2.say(ac,out,A,at(1.6/tm),'step',.7,pA);S2.say(ac,out,A,at(2.1/tm),'step',.6,pA)}
 if(pl.br==='rinse'){for(let i=0;i<5;i++)S2.cloud(ac,out,at((.15+i*.28)/tm),.18,90,{bp:2200,q:1.5,a:.03,d:[.01,.04],spread:.15},u=>Math.sin(Math.PI*u));
  S2.grain(ac,out,at(1.7/tm),{f:1900,d:.12,a:.12,pan:0,att:.05});S2.say(ac,out,A,at(2.3/tm),'step',.6,pA);S2.say(ac,out,A,at(2.7/tm),'step',.5,pA)}
 if(pl.wit){S2.grain(ac,out,at(.45),{f:150,glide:.5,d:.45,a:.06,type:'sawtooth',noise:.4,pan:.75});S2.say(ac,out,pl.wit,at(1.75),'step',.5,.8);S2.grain(ac,out,at(2.35),{bp:400,q:2,d:.06,a:.14,pan:.75})}
}

// ---------- trace: the cup's residue ring, aging ----------
function trace(g,box,age,K){const a=Math.exp(-(age||0)*.22);const cx=box.x+box.w/2,cy=box.y+box.h*.6,r=Math.min(box.w,box.h*2.4)*.38;
 g.save();g.globalAlpha=1;g.strokeStyle=`rgba(130,190,80,${.55*a})`;g.lineWidth=Math.max(1.5,r*.12);g.beginPath();g.ellipse(cx,cy,r,r*.34,0,0,7);g.stroke();
 g.strokeStyle=`rgba(170,225,120,${.22*a})`;g.lineWidth=Math.max(3,r*.3);g.beginPath();g.ellipse(cx,cy,r*1.05,r*.36,0,0,7);g.stroke();
 g.fillStyle=`rgba(120,175,70,${.25*a})`;g.beginPath();g.ellipse(cx+r*.3,cy+r*.04,r*.25,r*.08,0,0,7);g.fill();g.restore()}

CONSEQ({deed:'drugging',n:2,scion:31,lineage:'Alpha Matting — Hair, Lace and Smoke',
 op:'The sleeper\'s sight is a smoke matte over the room with a green spill halo on every edge; waking solves the matte from the sleeper outward and decontaminates the edges, except the residue in the cup and on the sleeper, and shows what was lifted out of the picture while it slept and who looked in at the door.',
 made:'Sacks are polygons filled premultiplied with fibre-strand edges; Ogiva\'s wig and Inigo\'s ears are strand bundles hanging under world gravity, Roessler\'s shawl and the guilt veil are lace with punched holes. The haze is a low-resolution fractional-alpha noise field upsampled over the frame, and every absence (coins, photograph) is drawn as a clean patch with a residue edge.',
 moved:'A waking progress p(t) raises the matte threshold and lowers each edge\'s green spill; the victim\'s own rise, rock or doze follows its identity, and the doer\'s action is picked from the ledger (burn the photograph, lay a veil and back away, count the lifted coins, or rinse the cup). The archetype levers scale the sacks (loom, shrink), stretch their wall shadows (shadow), light them (halo), drain them (grey) and change the doer\'s timing (tempo).',
 dur:DUR,beat,sound,trace});
})();
