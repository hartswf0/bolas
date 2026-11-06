// 05 · Incitement to Prostitution — CONSEQUENCE · SCION 4 · Frank Mouris, Autobiographical Image Torrent
// The money becomes an image torrent. Each coin the doer took is spent, slot by slot, on a run of drawn
// catalogue cut-outs (what this doer buys), and every cut-out flies to where this doer keeps things: the
// widow's lockbox, the wrestler's belly, through the heir and out, onto the model's head. Recurring motifs
// give the torrent its grammar: COIN (the price), the VICTIM's own silhouette in a coin frame (what was sold),
// and the remembered hatch still (where it happened). The cut rate accelerates (appetite), then the window
// strobes the other living sacks with prices on them (who next). Two deliberate holds: the coins at the start,
// the victim small and turned to the wall at the end. The sacks themselves are built of cut paper: a silhouette
// filled with clipped catalogue swatches; the victim's swatches peel off and fly to the doer as coins.
(function(){
const FY=960, SC=1.75;
const IDS=['R','B','I','O'];
// ---------- colour helpers ----------
const hx=s=>[parseInt(s.slice(1,3),16),parseInt(s.slice(3,5),16),parseInt(s.slice(5,7),16)];
const rgb=(c,a)=>a===undefined?`rgb(${c[0]|0},${c[1]|0},${c[2]|0})`:`rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
const grey=(c,k)=>{const y=c[0]*.3+c[1]*.59+c[2]*.11;return[c[0]+(y-c[0])*k,c[1]+(y-c[1])*k,c[2]+(y-c[2])*k]};
const dim=(c,k)=>[c[0]*k,c[1]*k,c[2]*k];
const mixc=(a,b,k)=>[a[0]+(b[0]-a[0])*k,a[1]+(b[1]-a[1])*k,a[2]+(b[2]-a[2])*k];
const COTTON=['#d6bf96','#e2cea5','#e8d5ae','#f0e4c8','#cdb489','#dcc79c'].map(hx);
const INK=['#2b4c7e','#b8432f','#2f6b4f','#c9962c','#7a3b8f','#1d1d22','#d97a8a','#3d8ca8'].map(hx);
const ATTR={R:hx('#6e3a33'),B:hx('#2a2622'),O:hx('#7a3b8f')};
const GOLD=hx('#e6b43c');

// ---------- the ledger-driven setup (pure function of ev, st) ----------
function setup(ev,st,K){
  const A=ev.A,V=ev.V,LA=st.levers[A]||{},LV=st.levers[V]||{};
  const mA=(st.mind[A]&&st.mind[A][V])||{},mV=(st.mind[V]&&st.mind[V][A])||{};
  const vDead=!st.alive[V], aDead=!st.alive[A];
  const others=IDS.filter(s=>s!==A&&s!==V);
  const c={A,V,LA,LV,mA,mV,vDead,aDead,others,
    guilt:mA.guilt||0, pride:mA.pride||0, fear:mV.fear||0, grudge:mV.grudge||0,
    vDrowsy:(st.body[V]||[]).includes('drowsy'), vOwes:(st.body[V]||[]).includes('coins')&&(st.know[V]||[]).length>1,
    aRich:(st.body[A]||[]).includes('coins')&&(st.know[A]||[]).some(k=>k<ev.k&&st.evidence[k]&&st.evidence[k].kind==='photograph'&&st.evidence[k].A===A)};
  c.branch=aDead?'ghost':vDead?'conceal':c.guilt>=.45?'giveback':'spend';
  c.turnBack=!vDead&&c.grudge>=.68;     // a grudge strong enough that the victim looks back
  c.tempo=1+K.cl(-.4,.6,LA.tempo||0)*.6;
  c.loom=K.cl(-.5,1.2,LA.loom||0);
  c.shadow=K.cl(0,1.4,LA.shadow||0);
  c.halo=K.cl(0,1,LA.halo||0);
  c.weight=K.cl(-.4,1,LA.weight||0);
  c.vShrink=K.cl(0,1,LV.shrink||0);
  c.vGrey=K.cl(0,1,(LV.grey||0)+.25);
  c.aGrey=K.cl(0,1,LA.grey||0);
  // slot schedule: the torrent. Durations shrink as the appetite grows.
  const slots=[];let t=.42;const N=c.branch==='ghost'?16:24+Math.round(c.loom*6);
  for(let i=0;i<N&&t<2.0;i++){const d=K.lerp(.15,.045,Math.pow(i/(N-1),.8))/c.tempo;slots.push({i,t,d,kind:slotKind(c,i,K)});t+=d}
  c.slots=slots;c.tEnd=t;
  c.appetite0=Math.max(t,1.95);c.appetite1=c.appetite0+.62;
  return c;
}
const BUY={R:['key','padlock','ledger','lockbox','candle','house','stack'],B:['loaf','sausage','bottle','drumstick','apple','cake','loaf'],
           I:['dice','card','glass','horseshoe','wheel','tophat','card'],O:['wig','perfume','mirror','shoe','lipstick','pearls','wig']};
const HIDE=['sheet','floursack','padlock','broom','floursack','sheet','key'];
function slotKind(c,i,K){
  if(i===0)return'coin';
  if(i%4===0)return'coin';                    // the price
  if(i%7===3)return'victim';                  // what was sold
  if(i%9===5)return'still';                   // where it happened
  if(c.branch==='giveback'&&i%6===1)return'flower';
  const list=c.branch==='conceal'?HIDE:BUY[c.A];
  return list[Math.floor(K.hash(i*13.7+c.A.charCodeAt(0))*list.length)];
}

// ---------- sack built of cut paper ----------
// silhouette path: bottom centre (0,0), width w, height h; ears: -1 hang, 0 corner, 1 up
function sackPath(g,w,h,earL,earR,sag){
  const hw=w/2,top=-h,ey=h*.16;
  g.beginPath();
  g.moveTo(-hw*.92,0);
  g.quadraticCurveTo(-hw*1.08,-h*.45-sag*h*.1,-hw*.9,top+ey);
  // left ear
  if(earL<0){g.lineTo(-hw*.98,top+ey+h*.05);g.quadraticCurveTo(-hw*1.25,top+h*.5,-hw*1.12,top+h*.86);g.lineTo(-hw*.98,top+h*.88);g.quadraticCurveTo(-hw*1.02,top+h*.45,-hw*.72,top+ey);}
  else{g.lineTo(-hw*(.95+.05*earL),top-h*.09*earL-4);g.lineTo(-hw*.64,top+ey*.4);}
  g.quadraticCurveTo(0,top+ey*.2+sag*h*.18,hw*.64,top+ey*.4);
  if(earR<0){g.lineTo(hw*.72,top+ey);g.quadraticCurveTo(hw*1.02,top+h*.45,hw*.98,top+h*.88);g.lineTo(hw*1.12,top+h*.86);g.quadraticCurveTo(hw*1.25,top+h*.5,hw*.98,top+ey+h*.05);}
  else{g.lineTo(hw*(.95+.05*earR),top-h*.09*earR-4);}
  g.lineTo(hw*.9,top+ey);
  g.quadraticCurveTo(hw*1.08,-h*.45-sag*h*.1,hw*.92,0);
  g.quadraticCurveTo(0,8,-hw*.92,0);
  g.closePath();
}
// one clipped catalogue swatch, local rect
function swatch(g,K,seed,w,h,gk,lit){
  const H=n=>K.hash(seed*7.31+n);
  const base=grey(COTTON[Math.floor(H(1)*COTTON.length)],gk);
  g.fillStyle=rgb(dim(base,lit));g.fillRect(-w/2,-h/2,w,h);
  const kind=Math.floor(H(2)*5),ink=grey(INK[Math.floor(H(3)*INK.length)],gk);
  g.globalAlpha=.32;g.fillStyle=rgb(dim(ink,lit));g.strokeStyle=rgb(dim(ink,lit));g.lineWidth=2;
  if(kind===0){for(let y=-h/2+4;y<h/2;y+=7){g.fillRect(-w/2+4,y,w*(.4+H(y)*.5),2.5)}}            // newsprint lines
  else if(kind===1){for(let y=-h/2+5;y<h/2;y+=9)for(let x=-w/2+5;x<w/2;x+=9){g.beginPath();g.arc(x,y,2,0,7);g.fill()}} // halftone dots
  else if(kind===2){for(let x=-w/2;x<w/2;x+=8)g.fillRect(x,-h/2,3,h)}                              // stripes
  else if(kind===3){g.beginPath();g.arc(0,0,Math.min(w,h)*.3,0,7);g.stroke()}                        // stamp
  g.globalAlpha=1;g.strokeStyle='rgba(255,252,240,.55)';g.lineWidth=1.5;g.strokeRect(-w/2,-h/2,w,h);  // white cut edge
}
// p: {x,s,rot,earL,earR,sag,gk,lit,peel,turn,wigVeil,shawlUp,bulge,belt,alpha}
function drawSack(g,id,p,K,carry){
  const C=K.CAST[id];const w=C.w*p.s*(1+(p.bulge||0))*(1+(p.flat||0)*.5),h=C.h*p.s*(1-(p.sag||0)*.25)*(1-(p.flat||0)*.62);
  g.save();g.translate(p.x,FY-(p.lift||0));g.rotate(p.rot||0);g.globalAlpha=p.alpha??1;
  // drop shadow (cut paper sits slightly above the page)
  g.save();g.translate(8,6);sackPath(g,w,h,p.earL,p.earR,p.sag||0);g.fillStyle='rgba(0,0,0,.45)';g.fill();g.restore();
  sackPath(g,w,h,p.earL,p.earR,p.sag||0);
  g.save();g.clip();
  const gk=p.gk||0,lit=p.lit??1;
  g.fillStyle=rgb(dim(grey(hx(C.fill),gk),lit));g.fillRect(-w,-h*1.2,w*2,h*1.4);
  // the swatch mosaic: identity seed per sack, ~28 pieces
  const N=22,seed0=id.charCodeAt(0)*3.1;
  for(let i=0;i<N;i++){if(i<(p.peel||0)*N)continue;const H=n=>K.hash(seed0+i*5.17+n);
    g.save();g.translate((H(1)-.5)*w*1.05,-H(2)*h*1.02);g.rotate((H(3)-.5)*.5);swatch(g,K,seed0+i,w*(.22+H(4)*.25),h*(.14+H(5)*.2),gk,lit);g.restore()}
  // attributes
  if(id==='R'){const up=p.shawlUp||0;g.fillStyle=rgb(dim(grey(ATTR.R,gk*.6),lit));g.fillRect(-w,-h*1.1,w*2,h*(.32+up*.28));
    g.strokeStyle=rgb(dim(grey([150,90,80],gk*.6),lit));g.lineWidth=3;for(let x=-w;x<w;x+=14){g.beginPath();g.moveTo(x,-h*(.78-up*.28));g.lineTo(x+7,-h*(.74-up*.28));g.stroke()}}
  if(id==='B'){g.fillStyle=rgb(dim(ATTR.B,lit));g.fillRect(-w,-h*.42-h*.05,w*2,h*.1);
    if(!p.turn||p.turn<.5){g.strokeStyle=rgb(dim(grey([120,90,40],gk),lit));g.lineWidth=4;g.beginPath();g.arc(0,-h*.7,h*.13,0,7);g.stroke();
      for(let k=-2;k<=2;k++){g.beginPath();g.moveTo(0,-h*.6);g.quadraticCurveTo(k*8,-h*.72,k*5,-h*.8);g.stroke()}}}
  if(p.turn>.5){ // turned to the wall: we see the back seam
    g.strokeStyle=`rgba(40,25,12,${(p.turn-.5)*1.8})`;g.lineWidth=5;g.setLineDash([9,7]);g.beginPath();g.moveTo(0,-h*.95);g.lineTo(0,-4);g.stroke();g.setLineDash([])}
  // carried marks
  const cr=carry||[];
  if(cr.includes('rope')){g.strokeStyle='rgba(150,110,60,.9)';g.lineWidth=6;for(const f of[.35,.55]){g.beginPath();g.moveTo(-w,-h*f);g.lineTo(w,-h*f-8);g.stroke()}}
  if(cr.includes('blot')){g.fillStyle='rgba(20,20,30,.85)';g.beginPath();g.arc(w*.15,-h*.5,h*.11,0,7);g.fill()}
  if(cr.includes('torn')){g.strokeStyle='rgba(40,25,15,.9)';g.lineWidth=3;g.beginPath();g.moveTo(-w*.3,-h*.2);g.lineTo(-w*.2,-h*.3);g.lineTo(-w*.32,-h*.38);g.lineTo(-w*.18,-h*.48);g.stroke()}
  if(cr.includes('emptied')||cr.includes('greyed')){g.fillStyle='rgba(30,30,30,.25)';g.fillRect(-w,-h*1.2,w*2,h*1.4)}
  g.restore();
  // outline (scissor edge)
  sackPath(g,w,h,p.earL,p.earR,p.sag||0);g.strokeStyle=rgb(dim(grey([250,245,230],gk),lit*.9));g.lineWidth=3;g.stroke();
  // Ogiva's wig: long cut strips; veil pulls them down over her front
  if(id==='O'){const v=p.wigVeil||0,wc=grey(ATTR.O,gk*.5);for(let k=0;k<9;k++){const x=(k/8-.5)*w*1.25;const len=h*(.34+v*.4)*(k%2?1:.85);
      g.fillStyle=rgb(dim(mixc(wc,[160,90,190],K.hash(k)*.4),lit));g.save();g.translate(x*.85,-h-4);g.rotate((k/8-.5)*(.35-v*.25));g.fillRect(-w*.06,0,w*.12,len);g.restore()}
    g.fillStyle=rgb(dim(wc,lit));g.beginPath();g.ellipse(0,-h,w*.6,h*.09,0,Math.PI,0);g.fill()}
  if(cr.includes('cinched')){g.strokeStyle='rgba(120,80,40,.95)';g.lineWidth=5;g.beginPath();g.moveTo(-w*.35,-h*.82);g.lineTo(w*.35,-h*.82);g.stroke()}
  if(cr.includes('gag')){g.fillStyle='rgba(240,235,220,.95)';g.fillRect(-w*.5,-h*.72,w,h*.07)}
  if(cr.includes('tag')){g.fillStyle='#f6f0dc';g.save();g.translate(w*.3,-h*.3);g.rotate(.3);g.fillRect(-14,-9,28,18);g.restore()}
  if(cr.includes('drowsy')){g.globalAlpha*=.25;g.translate(14,0);sackPath(g,w,h,p.earL,p.earR,p.sag||0);g.strokeStyle='#fff';g.lineWidth=2;g.stroke()}
  g.restore();
  return{w,h};
}
function sackSil(g,id,K,s,col){const C=K.CAST[id];const er=id==='I'?-1:0;sackPath(g,C.w*s,C.h*s,er,er,id==='I'?.3:0);g.fillStyle=col;g.fill();
  if(id==='O'){g.fillStyle=rgb(ATTR.O);g.fillRect(-C.w*s*.45,-C.h*s-6,C.w*s*.9,C.h*s*.5)}
  if(id==='R'){g.fillStyle=rgb(ATTR.R);g.fillRect(-C.w*s*.5,-C.h*s*1.02,C.w*s,C.h*s*.26)}
  if(id==='B'){g.fillStyle=rgb(ATTR.B);g.fillRect(-C.w*s*.55,-C.h*s*.45,C.w*s*1.1,C.h*s*.09)}}

// ---------- the catalogue: drawn cut-outs, centred at 0,0, size s ----------
function coin(g,r,spin,c){const sx=Math.abs(Math.cos(spin))*.8+.2;g.save();g.scale(sx,1);g.fillStyle=rgb(c||GOLD);g.beginPath();g.arc(0,0,r,0,7);g.fill();
  g.strokeStyle='rgba(120,80,10,.8)';g.lineWidth=r*.12;g.beginPath();g.arc(0,0,r*.72,0,7);g.stroke();g.fillStyle='rgba(255,240,180,.7)';g.beginPath();g.arc(-r*.25,-r*.3,r*.18,0,7);g.fill();g.restore()}
function icon(g,kind,s,K){
  const f=(c)=>{g.fillStyle=c},P=()=>g.beginPath();g.lineJoin='round';g.lineWidth=s*.05;
  switch(kind){
  case'coin':coin(g,s*.42,0);break;
  case'stack':for(let k=0;k<6;k++){f(k%2?'#d9a62f':'#efc24f');g.fillRect(-s*.3,s*.3-k*s*.11,s*.6,s*.09)}break;
  case'key':g.strokeStyle='#c9962c';g.lineWidth=s*.09;P();g.arc(-s*.22,0,s*.16,0,7);g.stroke();P();g.moveTo(-s*.06,0);g.lineTo(s*.38,0);g.lineTo(s*.38,s*.14);g.moveTo(s*.25,0);g.lineTo(s*.25,s*.12);g.stroke();break;
  case'padlock':g.strokeStyle='#888';g.lineWidth=s*.08;P();g.arc(0,-s*.08,s*.2,Math.PI,0);g.stroke();f('#c9962c');g.fillRect(-s*.3,-s*.08,s*.6,s*.42);f('#222');P();g.arc(0,s*.1,s*.05,0,7);g.fill();break;
  case'ledger':f('#2f6b4f');g.fillRect(-s*.32,-s*.38,s*.64,s*.76);f('#f3ead2');g.fillRect(-s*.24,-s*.3,s*.5,s*.6);f('#b8432f');for(let k=0;k<5;k++)g.fillRect(-s*.18,-s*.22+k*s*.11,s*.36,s*.03);break;
  case'lockbox':f('#4a3a2a');g.fillRect(-s*.38,-s*.2,s*.76,s*.44);f('#6e5a3a');g.fillRect(-s*.38,-s*.3,s*.76,s*.14);f('#c9962c');g.fillRect(-s*.06,-s*.08,s*.12,s*.14);break;
  case'candle':f('#f3ead2');g.fillRect(-s*.1,-s*.15,s*.2,s*.5);f('#f6c445');P();g.ellipse(0,-s*.26,s*.07,s*.12,0,0,7);g.fill();break;
  case'house':f('#b8432f');P();g.moveTo(-s*.4,-s*.02);g.lineTo(0,-s*.4);g.lineTo(s*.4,-s*.02);g.fill();f('#e8d5ae');g.fillRect(-s*.3,-s*.02,s*.6,s*.38);f('#2b4c7e');g.fillRect(-s*.2,s*.06,s*.14,s*.12);g.fillRect(s*.06,s*.06,s*.14,s*.12);break;
  case'loaf':f('#c08a3e');P();g.ellipse(0,0,s*.42,s*.24,0,0,7);g.fill();g.strokeStyle='#8a5a20';for(let k=-1;k<=1;k++){P();g.moveTo(k*s*.15-s*.06,-s*.16);g.lineTo(k*s*.15+s*.06,s*.02);g.stroke()}break;
  case'sausage':f('#a8452f');P();g.ellipse(-s*.12,0,s*.3,s*.1,.5,0,7);g.fill();P();g.ellipse(s*.14,s*.05,s*.3,s*.1,-.3,0,7);g.fill();break;
  case'bottle':f('#2f6b4f');g.fillRect(-s*.14,-s*.1,s*.28,s*.48);g.fillRect(-s*.05,-s*.36,s*.1,s*.28);f('#f3ead2');g.fillRect(-s*.14,s*.06,s*.28,s*.14);break;
  case'drumstick':f('#c07a3e');P();g.ellipse(-s*.08,-s*.06,s*.24,s*.18,-.6,0,7);g.fill();f('#f3ead2');g.fillRect(s*.06,s*.06,s*.24,s*.07);P();g.arc(s*.32,s*.06,s*.06,0,7);g.arc(s*.32,s*.14,s*.06,0,7);g.fill();break;
  case'apple':f('#c0392b');P();g.arc(-s*.1,s*.04,s*.24,0,7);g.arc(s*.1,s*.04,s*.24,0,7);g.fill();f('#2f6b4f');P();g.ellipse(s*.06,-s*.28,s*.1,s*.05,-.5,0,7);g.fill();break;
  case'cake':f('#d97a8a');g.fillRect(-s*.34,-s*.06,s*.68,s*.32);f('#f3ead2');g.fillRect(-s*.34,-s*.14,s*.68,s*.1);f('#c0392b');P();g.arc(0,-s*.22,s*.07,0,7);g.fill();break;
  case'dice':for(const[dx,r] of[[-s*.18,-.2],[s*.18,.25]]){g.save();g.translate(dx,0);g.rotate(r);f('#f3ead2');g.fillRect(-s*.16,-s*.16,s*.32,s*.32);f('#1d1d22');for(const[a,b] of[[-1,-1],[0,0],[1,1]]){P();g.arc(a*s*.08,b*s*.08,s*.03,0,7);g.fill()}g.restore()}break;
  case'card':g.save();g.rotate(-.15);f('#f3ead2');g.fillRect(-s*.22,-s*.32,s*.44,s*.64);f('#b8432f');P();g.moveTo(0,-s*.12);g.lineTo(s*.11,0);g.lineTo(0,s*.12);g.lineTo(-s*.11,0);g.fill();g.restore();break;
  case'glass':g.strokeStyle='#e8e0c8';g.lineWidth=s*.05;P();g.moveTo(-s*.18,-s*.34);g.lineTo(0,-s*.02);g.lineTo(s*.18,-s*.34);g.closePath();g.stroke();f('rgba(240,200,80,.8)');P();g.moveTo(-s*.12,-s*.26);g.lineTo(0,-s*.06);g.lineTo(s*.12,-s*.26);g.fill();P();g.moveTo(0,-s*.02);g.lineTo(0,s*.3);g.moveTo(-s*.12,s*.3);g.lineTo(s*.12,s*.3);g.stroke();break;
  case'horseshoe':g.strokeStyle='#999';g.lineWidth=s*.12;P();g.arc(0,0,s*.26,Math.PI*.85,Math.PI*2.15);g.stroke();break;
  case'wheel':f('#1d1d22');P();g.arc(0,0,s*.36,0,7);g.fill();for(let k=0;k<12;k++){f(k%2?'#b8432f':'#1d1d22');P();g.moveTo(0,0);g.arc(0,0,s*.32,k*Math.PI/6,(k+1)*Math.PI/6);g.fill()}f('#c9962c');P();g.arc(0,0,s*.08,0,7);g.fill();break;
  case'tophat':f('#1d1d22');g.fillRect(-s*.2,-s*.34,s*.4,s*.5);g.fillRect(-s*.36,s*.14,s*.72,s*.08);f('#b8432f');g.fillRect(-s*.2,s*.02,s*.4,s*.07);break;
  case'wig':f('#7a3b8f');P();g.ellipse(0,-s*.12,s*.3,s*.2,0,Math.PI,0);g.fill();for(let k=0;k<6;k++)g.fillRect(-s*.3+k*s*.1,-s*.14,s*.08,s*.5);break;
  case'perfume':f('rgba(200,140,210,.9)');P();g.ellipse(0,s*.1,s*.24,s*.22,0,0,7);g.fill();f('#c9962c');g.fillRect(-s*.06,-s*.24,s*.12,s*.14);f('#7a3b8f');P();g.arc(0,-s*.3,s*.07,0,7);g.fill();break;
  case'mirror':f('#c9962c');P();g.ellipse(0,-s*.1,s*.24,s*.28,0,0,7);g.fill();f('#cfe3ea');P();g.ellipse(0,-s*.1,s*.18,s*.22,0,0,7);g.fill();f('#c9962c');g.fillRect(-s*.04,s*.16,s*.08,s*.22);break;
  case'shoe':f('#b8432f');P();g.moveTo(-s*.34,s*.1);g.quadraticCurveTo(-s*.1,-s*.04,s*.1,-s*.24);g.lineTo(s*.32,-s*.24);g.lineTo(s*.3,s*.1);g.fill();g.fillRect(s*.26,s*.1,s*.05,s*.2);break;
  case'lipstick':f('#c9962c');g.fillRect(-s*.1,-s*.02,s*.2,s*.34);f('#c0392b');P();g.moveTo(-s*.08,-s*.02);g.lineTo(-s*.08,-s*.24);g.lineTo(s*.08,-s*.32);g.lineTo(s*.08,-s*.02);g.fill();break;
  case'pearls':f('#f3ead2');for(let k=0;k<11;k++){const a=Math.PI*.1+k*Math.PI*.08;P();g.arc(Math.cos(a)*s*.3,Math.sin(a)*s*.3-s*.1,s*.055,0,7);g.fill()}break;
  case'flower':g.strokeStyle='#2f6b4f';g.lineWidth=s*.05;P();g.moveTo(0,0);g.lineTo(0,s*.4);g.stroke();for(let k=0;k<5;k++){f('#d97a8a');P();g.arc(Math.cos(k*1.256)*s*.12,Math.sin(k*1.256)*s*.12-s*.05,s*.1,0,7);g.fill()}f('#f6c445');P();g.arc(0,-s*.05,s*.06,0,7);g.fill();break;
  case'sheet':f('#efe8d6');P();g.moveTo(-s*.4,-s*.3);g.lineTo(s*.4,-s*.3);g.quadraticCurveTo(s*.5,s*.1,s*.36,s*.36);g.lineTo(-s*.36,s*.36);g.quadraticCurveTo(-s*.5,s*.1,-s*.4,-s*.3);g.fill();g.strokeStyle='#bbb';g.lineWidth=2;P();g.moveTo(-s*.1,-s*.3);g.lineTo(-s*.16,s*.36);g.stroke();break;
  case'floursack':f('#e8d5ae');P();g.moveTo(-s*.3,s*.36);g.lineTo(-s*.26,-s*.26);g.lineTo(-s*.34,-s*.36);g.lineTo(s*.34,-s*.36);g.lineTo(s*.26,-s*.26);g.lineTo(s*.3,s*.36);g.fill();g.strokeStyle='#8a6a40';g.lineWidth=3;P();g.arc(0,0,s*.12,0,7);g.stroke();break;
  case'broom':g.strokeStyle='#8a5a20';g.lineWidth=s*.05;P();g.moveTo(-s*.3,-s*.36);g.lineTo(s*.1,s*.14);g.stroke();f('#c9962c');P();g.moveTo(s*.02,s*.06);g.lineTo(s*.34,s*.2);g.lineTo(s*.2,s*.4);g.lineTo(-s*.06,s*.2);g.fill();break;
  }
}
// a magazine cut-out card: white border, rotated, with drop shadow
function card(g,s,rot,paper){g.rotate(rot);g.fillStyle='rgba(0,0,0,.4)';g.fillRect(-s/2+7,-s/2+7,s,s);g.fillStyle='#f7f1e0';g.fillRect(-s/2,-s/2,s,s);g.fillStyle=paper;g.fillRect(-s/2+s*.06,-s/2+s*.06,s*.88,s*.88)}

// ---------- the room: a collage wall at night ----------
function room(g,K,c,t,lampK){
  g.fillStyle='#17131a';g.fillRect(0,0,1920,1080);
  // wallpaper of dark clippings
  for(let i=0;i<70;i++){const H=n=>K.hash(i*3.3+n+77);g.save();g.translate(H(1)*1920,H(2)*FY);g.rotate((H(3)-.5)*.6);
    const ink=INK[Math.floor(H(4)*INK.length)];g.fillStyle=rgb(dim(mixc(ink,[40,30,40],.75),.38));g.fillRect(-60-H(5)*60,-40-H(6)*40,120+H(5)*120,80+H(6)*80);
    g.fillStyle='rgba(255,255,255,.03)';for(let y=-30;y<30;y+=9)g.fillRect(-50,y,100*H(y+9),2);g.restore()}
  // floor
  g.fillStyle='#2a2018';g.fillRect(0,FY,1920,180);g.fillStyle='rgba(0,0,0,.35)';for(let x=0;x<1920;x+=96)g.fillRect(x,FY,3,180);
  // the right wall: door with the hatch (motif kept from the deed)
  g.fillStyle='#3a2a1e';g.fillRect(1700,330,200,FY-330);g.strokeStyle='#5a4430';g.lineWidth=6;g.strokeRect(1712,342,176,FY-352);
  g.fillStyle='#120d0a';g.fillRect(1752,520,96,56);
  // lamp, left
  const L=lampK;g.fillStyle='#3a2a1e';g.fillRect(150,560,10,FY-560);g.fillStyle=`rgba(${240*L|0},${200*L|0},${120*L|0},1)`;g.beginPath();g.moveTo(110,560);g.lineTo(200,560);g.lineTo(178,500);g.lineTo(132,500);g.fill();
  const rg=g.createRadialGradient(155,560,20,155,560,900);rg.addColorStop(0,`rgba(255,210,140,${.28*L})`);rg.addColorStop(1,'rgba(255,210,140,0)');g.fillStyle=rg;g.fillRect(0,0,1920,1080);
}

// ---------- poses: pure functions of t and the setup ----------
function doerPose(c,t,K,eaten){
  const A=c.A,base={R:400,B:430,I:400,O:420}[A];
  const app=K.sm(c.appetite0-.1,c.appetite1,t);
  const grow=1+.12*K.cl(0,1.5,c.loom+.3)*K.sm(.4,c.appetite1,t);
  const p={x:base+app*(40+c.loom*40),s:grow*SC,rot:0,earL:0,earR:0,sag:0,gk:c.aGrey,lit:1,bulge:0,alpha:1};
  if(A==='R'){p.rot=Math.sin(t*7)*.03*K.sm(.4,.8,t);p.earL=p.earR=.2+.6*app}
  if(A==='B'){p.bulge=.16*eaten;p.earL=p.earR=.1;p.lift=Math.abs(Math.sin(t*9))*6*c.weight*K.sm(.4,2,t)}
  if(A==='I'){p.earL=p.earR=-1;p.sag=.3-.15*app;p.rot=-.06*app}
  if(A==='O'){p.earL=p.earR=.3;p.rot=-.03*Math.sin(t*3)}
  // the lean toward the next one
  p.rot+=.06*app*(1+c.loom*.5);
  if(c.branch==='ghost'){p.alpha=.45+.1*Math.sin(t*11);p.gk=1}
  if(c.branch==='giveback'){const gb=K.sm(c.tEnd,c.appetite1,t);p.x+=gb*120;p.rot-=gb*.08}
  return p;
}
function victimPose(c,t,K){
  const V=c.V;const dist=K.sm(.35,2.4,t);
  const s0=1,s1=K.lerp(.72,.5,K.cl(0,1,c.fear*.6+c.vShrink));
  const p={x:K.lerp(1330,1625,dist)-(c.V==='B'?40:0),s:K.lerp(s0,s1,dist)*SC,rot:.07*K.sm(.6,2.2,t),earL:0,earR:0,sag:0,gk:c.vGrey*dist,lit:K.lerp(1,.62,dist),peel:.45*dist,turn:K.sm(.6,2.2,t)};
  if(V==='R'){p.shawlUp=K.sm(.4,1.6,t);p.rot=Math.sin(t*5)*.025;p.earL=p.earR=-.2*dist}
  if(V==='B'){p.bulge=-.12*dist;p.sag=.4*dist;p.earL=p.earR=-.6*dist;p.s*=K.lerp(1,.9,dist)}
  if(V==='I'){p.earL=p.earR=-1;p.sag=.3+.5*dist;p.x+=40*dist;p.rot=.08*dist}
  if(V==='O'){p.wigVeil=K.sm(.5,1.8,t);p.earL=p.earR=.1;p.rot=-.02*dist}
  if(c.vDrowsy){p.rot+=Math.sin(t*2.3)*.06;p.x+=Math.sin(t*1.7)*12}
  if(c.vDead){p.x=1480;p.s=.92*SC;p.rot=0;p.flat=1;p.lift=0;p.gk=1;p.lit=.6;p.peel=0;p.turn=0;p.earL=p.earR=-.4;p.wigVeil=1;p.shawlUp=0;p.sag=.3}
  if(c.turnBack){const tb=K.sm(c.appetite1-.1,c.appetite1+.35,t);p.turn*=1-.6*tb;p.earL=K.lerp(p.earL,.8,tb);p.earR=K.lerp(p.earR,.3,tb);p.rot-=.08*tb}
  return p;
}
// where each doer keeps things
function sink(c,p,K){const C=K.CAST[c.A];const h=C.h*p.s,w=C.w*p.s;
  if(c.A==='R')return{x:p.x+w*.75,y:FY-30,mode:'box'};
  if(c.A==='B')return{x:p.x,y:FY-h*.6,mode:'into'};
  if(c.A==='I')return{x:p.x,y:FY-h*.5,mode:'through'};
  return{x:p.x,y:FY-h-10,mode:'head'};}

// ---------- the beat ----------
CONSEQ({
  deed:'prostitution', n:5, scion:4, lineage:'Frank Mouris — Autobiographical Image Torrent',
  op:'The coins the doer took are spent on screen as an accelerating torrent of cut-out pictures of what it buys, which pile up where this doer keeps things, while the victim shrinks into the far corner, turned to the wall, and then the doer\'s window flashes the other sacks with prices on them.',
  made:'The sacks are silhouettes cut from paper and filled with clipped catalogue swatches (newsprint lines, halftone dots, stripes) in sack cotton, with the shawl, belt, wheat stamp and purple wig as cut strips; the room is a wall of dark clippings with the lamp left and the hatch door right. The purchases are drawn catalogue cut-outs on white-edged cards: lockbox and keys for the widow, bread and bottles for the wrestler, dice and cards for the heir, wigs and perfume for the model.',
  moved:'A slot schedule computed from the ledger (cut rate set by the doer\'s tempo and loom levers) flashes one card per slot and flies it to the doer\'s store; coin, the victim\'s silhouette and the remembered hatch still recur in fixed slots as motifs. The victim\'s distance, size, grey and peeling swatches are driven by its fear and shrink lever, the doer\'s growth, lean, shadow and halo by its loom, shadow and halo levers, and the branch (spend, give back, conceal a dead sack, ghost doer) by the state.',
  dur:3.3,
  beat(g,t,ev,st,K,X){
    const c=setup(ev,st,K),A=c.A,V=c.V;
    g.save();
    // how far into the torrent: number of slots already spent
    let cur=-1;for(const s of c.slots)if(t>=s.t)cur=s.i;
    const spent=cur+1;
    const eaten=A==='B'&&c.branch!=='ghost'?K.cl(0,1,spent/c.slots.length):0;
    const lampK=1;
    room(g,K,c,t,lampK);
    const dp=doerPose(c,t,K,eaten),vp=victimPose(c,t,K);
    // doer's shadow on the wall: lengthens with the shadow lever and the appetite
    const app=K.sm(c.appetite0-.1,c.appetite1,t);
    {const C=K.CAST[A];g.save();g.translate(dp.x+30,FY);g.transform(1,0,-.35-.4*app*c.shadow,1,0,0);g.scale(1+.25*c.shadow*app,1+(.25+.7*c.shadow)*K.sm(.4,c.appetite1,t));
      sackPath(g,C.w*dp.s*1.05,C.h*dp.s,dp.earL,dp.earR,dp.sag);g.fillStyle=`rgba(0,0,0,${.25+.3*K.cl(0,1,c.shadow)})`;g.fill();g.restore()}
    // halo lever: the lamp finds the doer
    if(c.halo>.05){const rg=g.createRadialGradient(dp.x,FY-150,10,dp.x,FY-150,360);rg.addColorStop(0,`rgba(255,220,150,${.3*c.halo})`);rg.addColorStop(1,'rgba(255,220,150,0)');g.fillStyle=rg;g.fillRect(dp.x-400,FY-560,800,700)}
    // ---- victim side ----
    if(c.vDead){ // conceal: flour sacks accumulate over the still sack, one per spent slot
      drawSack(g,V,vp,K,st.body[V]);
      const n=Math.min(9,Math.floor(spent*.45));
      for(let k=0;k<n;k++){g.save();g.translate(1250+(k%4)*100+(k>3?50:0)+(k>7?40:0),FY-80-(k>3?110:0)-(k>7?100:0));g.translate(0,80);g.rotate((K.hash(k*3.1)-.5)*.12);sackPath(g,150,150,0,0,0);g.fillStyle=rgb(COTTON[k%COTTON.length]);g.fill();g.strokeStyle='rgba(250,245,230,.8)';g.lineWidth=3;g.stroke();g.strokeStyle='rgba(120,90,40,.8)';g.lineWidth=4;g.beginPath();g.arc(0,-70,22,0,7);g.stroke();g.restore()}
    }else{
      drawSack(g,V,vp,K,st.body[V]);
      // its peeled swatches fly left and turn into coins (what was sold is its own cloth)
      for(let k=0;k<12;k++){const t0=.5+k*.13,u=K.cl(0,1,(t-t0)/.55);if(u<=0||u>=1)continue;
        const C=K.CAST[V];const sx=vp.x+(K.hash(k*2.2)-.5)*C.w*vp.s,sy=FY-K.hash(k*4.4)*C.h*vp.s;
        const tg=sink(c,dp,K);const x=K.lerp(sx,tg.x,u),y=K.lerp(sy,tg.y,u)-Math.sin(u*Math.PI)*140;
        g.save();g.translate(x,y);g.rotate(u*6+k);
        if(u<.5){swatch(g,K,V.charCodeAt(0)*3.1+k,36,26,c.vGrey*.6,1)}else coin(g,13,u*12);
        g.restore()}
    }
    // victim owes (was blackmailed): its own coins also drain toward the doer
    if(c.vOwes&&!c.vDead){for(let k=0;k<4;k++){const u=K.cl(0,1,(t-1.0-k*.18)/.6);if(u<=0||u>=1)continue;const tg=sink(c,dp,K);
      g.save();g.translate(K.lerp(vp.x,tg.x,u),K.lerp(FY-60,tg.y,u)-Math.sin(u*Math.PI)*90);coin(g,15,u*9,[200,190,170]);g.restore()}}
    // ---- the doer and what it keeps ----
    const tg=sink(c,dp,K);
    // accumulated store (behind for R box, on top for O head)
    const store=Math.max(0,spent);
    if(c.branch!=='ghost'&&A==='R'){for(let k=0;k<store;k++){const H=n=>K.hash(k*9.1+n);g.save();g.translate(tg.x+(H(1)-.5)*120,FY-12-Math.floor(k/4)*28-H(2)*6);g.rotate((H(3)-.5)*.5);
        const kd=c.slots[k]&&c.slots[k].kind;icon(g,kd==='victim'||kd==='still'||!kd?'coin':kd,58,K);g.restore()}
      icon_at(g,'lockbox',tg.x,FY-26,90,K)}
    drawSack(g,A,dp,K,st.body[A]);
    if(c.branch!=='ghost'&&A==='O'){const n=Math.min(store,10);for(let k=0;k<n;k++){g.save();g.translate(tg.x+(K.hash(k)-.5)*30,tg.y-k*16);g.rotate((K.hash(k*2)-.5)*.4);
        const kd=c.slots[k].kind;icon(g,kd==='wig'||kd==='victim'||kd==='still'?'wig':kd,66,K);g.restore()}}
    if(c.branch!=='ghost'&&A==='B'){const C=K.CAST.B;g.save();g.translate(dp.x,FY-C.h*dp.s*.42);for(let k=0;k<Math.min(store,8);k++){g.fillStyle='rgba(240,200,90,.95)';g.beginPath();g.arc(-C.w*dp.s*.42+k*C.w*dp.s*.12,0,7,0,7);g.fill()}g.restore()}
    if(A==='I'||c.branch==='ghost'){ // through him: things fall out of the bottom and roll away, spent
      for(let k=0;k<c.slots.length;k++){const s=c.slots[k];const u=(t-(s.t+.32))/.7;if(u<0||u>1)continue;
        g.save();g.translate(dp.x+(K.hash(k)-.5)*60-u*(80+K.hash(k*3)*240),FY-30+Math.pow(u,2)*0-Math.sin(u*Math.PI)*40);g.rotate(-u*8);g.globalAlpha=1-u;icon(g,s.kind==='victim'||s.kind==='still'?'coin':s.kind,46,K);g.restore()}}
    // ---- the torrent window: one card per slot, flying from the flash point to the store ----
    const FX=930,FYY=360;
    for(let k=0;k<c.slots.length;k++){const s=c.slots[k];const age=t-s.t,FL=.62;if(age<0||age>FL)continue;
      const flash=age<s.d, u=flash?0:K.cl(0,1,(age-s.d)/(FL-s.d));
      const size=flash?K.lerp(420,380,age/s.d):K.lerp(330,60,u);
      const x=K.lerp(FX,tg.x,K.eo(0,1,u)),y=K.lerp(FYY,tg.y,u*u)-Math.sin(u*Math.PI)*60;
      g.save();g.translate(x,y);
      if(c.branch==='ghost')g.globalAlpha=.5;
      const paper=s.kind==='coin'?'#1d1d22':s.kind==='victim'?'#2b2230':['#2b4c7e','#b8432f','#2f6b4f','#c9962c','#3d8ca8'][k%5];
      card(g,size,(K.hash(k*1.7)-.5)*.3,paper);
      if(s.kind==='victim'){g.save();g.beginPath();g.arc(0,0,size*.38,0,7);g.fillStyle=rgb(GOLD);g.fill();g.clip();g.translate(0,size*.32);sackSil(g,V,K,size*.0042*(V==='O'?.85:V==='B'?.62:1.05),'rgba(40,30,20,.92)');g.restore()}
      else if(s.kind==='still'&&X&&X.still){g.save();g.beginPath();g.arc(0,0,size*.4,0,7);g.clip();try{g.drawImage(X.still(ev),1180,300,600,600,-size*.4,-size*.4,size*.8,size*.8)}catch(e){}g.restore();g.strokeStyle=rgb(GOLD);g.lineWidth=size*.04;g.beginPath();g.arc(0,0,size*.4,0,7);g.stroke()}
      else icon(g,s.kind,size*.82,K);
      g.restore()}
    // ---- appetite: the window strobes the other sacks with prices ----
    if(t>c.appetite0&&t<c.appetite1+.6){const ph=(t-c.appetite0)/(c.appetite1-c.appetite0);
      const seq=c.others.slice().sort((a,b)=>(st.alive[b]?1:0)-(st.alive[a]?1:0));const i=Math.min(seq.length-1,Math.floor(ph*seq.length*1.5)%seq.length);const who=ph<1?seq[i]:seq[0];
      const hold=ph>=1;const a=hold?Math.max(0,1-(t-c.appetite1)/.6)*.9:1;
      g.save();g.globalAlpha=a*(c.branch==='ghost'?.5:1);g.translate(FX,FYY);card(g,380,hold?-.06:(K.hash(i)-.5)*.2,'#2b2230');
      const alive=st.alive[who];
      g.save();g.beginPath();g.arc(0,0,150,0,7);g.fillStyle=alive?rgb(GOLD):'#6a6a6a';g.fill();g.clip();g.translate(0,128);sackSil(g,who,K,who==='O'?.62:who==='B'?.52:.92,'rgba(40,30,20,.92)');g.restore();
      if(alive){const price={R:2,B:4,I:3,O:5}[who];for(let k=0;k<price;k++){g.save();g.translate(-(price-1)*24+k*48,-150);coin(g,20,0);g.restore()}}
      else{g.strokeStyle='#ddd';g.lineWidth=10;g.beginPath();g.moveTo(-100,-100);g.lineTo(100,100);g.stroke()}
      g.restore();
      // a cut thread from the doer's ear to the card: the appetite pointing
      if(!hold||a>.3){g.strokeStyle=`rgba(230,180,60,${.6*a})`;g.lineWidth=3;g.setLineDash([12,8]);g.beginPath();const C=K.CAST[A];g.moveTo(dp.x+C.w*dp.s*.45,FY-C.h*dp.s);g.lineTo(FX-120,FYY+90);g.stroke();g.setLineDash([])}}
    // ---- give back: the doer pushes a coin and a flower toward the victim; they stay on the floor ----
    if(c.branch==='giveback'){const u=K.sm(c.tEnd-.1,c.appetite1-.1,t);if(u>0){const x0=dp.x+150,x1=vp.x-K.CAST[V].w*vp.s*.6-70;
      g.save();g.translate(K.lerp(x0,x1,u),FY-26);coin(g,26,u*10);g.restore();g.save();g.translate(K.lerp(x0,x1,u)-70,FY-40);g.rotate(-1.3);icon(g,'flower',150,K);g.restore()}}
    // victim's back to us: a vignette that pushes it into the far corner
    {const vg=g.createRadialGradient(dp.x+200,560,300,dp.x+300,560,1500);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,`rgba(0,0,0,${.35+.25*K.sm(1,2.8,t)})`);g.fillStyle=vg;g.fillRect(0,0,1920,1080)}
    // hold 1: the coins, in the doer's top, before anything is spent
    if(t<.5&&c.branch!=='ghost'){const C=K.CAST[A];const n={R:2,B:4,I:3,O:5}[V];const a=1-K.sm(.38,.5,t);
      for(let k=0;k<n;k++){g.save();g.globalAlpha=a;g.translate(dp.x-(n-1)*16+k*32,FY-C.h*dp.s-26);coin(g,16,k);g.restore()}}
    g.restore();
  },
  sound(ac,out,t0,ev,st,K){
    const S=K.SND,c=setup(ev,st,K),A=c.A,V=c.V,at=x=>t0+x,mf=m=>440*Math.pow(2,(m-69)/12);
    const pa=-0.5,pv=c.vDead?.6:.65,pf=-.08;
    // hold 1: the coins settle
    S.say(ac,out,A,at(.05),'breathe',.5,pa);for(let k=0;k<3;k++)S.grain(ac,out,at(.08+k*.09),{f:mf(96+k*2),d:.05,a:.12,pan:pa,att:.05});
    // the torrent: a cut grain per slot (paper snap), a coin ring on coin slots, the victim's voice on its own slots
    const coinM=[91,95,98,94,96,99];
    for(const s of c.slots){const w=at(s.t);
      S.grain(ac,out,w,{bp:3200,q:1.2,d:.018,a:c.branch==='ghost'?.08:.16,pan:pf,att:.05});
      if(s.kind==='coin')S.pluck(ac,out,w,coinM[s.i%6],.32,.35,pf);
      else if(s.kind==='victim')S.say(ac,out,V,w,'tick',.8,pv);
      else if(s.kind==='still'){S.grain(ac,out,w,{bp:420,q:3,d:.05,a:.25,pan:pv,att:.05})} // the knock at the hatch, remembered
      else if(s.kind==='flower')S.grain(ac,out,w,{f:mf(84),d:.2,a:.08,pan:pf});
      else S.grain(ac,out,w,{f:mf(60+((s.i*5)%17)),d:.06,a:.07,type:'triangle',pan:pf,att:.1});
      // landing in the store: the doer's voice (B swallows thumps, R ticks the count, I lets it drop, O glass)
      const lw=w+.62;if(c.branch==='ghost')continue;
      if(A==='R')S.say(ac,out,'R',lw,'tick',.7,pa);else if(A==='B')S.say(ac,out,'B',lw,'step',.35,pa);else if(A==='O')S.say(ac,out,'O',lw,'tick',.6,pa);else S.grain(ac,out,lw,{f:2600+K.hash(s.i)*900,d:.03,a:.1,pan:pa-.2})}
    // victim: shame, distance
    if(c.vDead){S.cloud(ac,out,at(.6),1.4,30,{bp:300,a:.04,d:[.05,.12],spread:.2},u=>Math.sin(Math.PI*u));for(let k=0;k<6;k++)S.thump(ac,out,at(.7+k*.22),.25,70,pv)}
    else{S.say(ac,out,V,at(.7),'sink',1,pv);S.say(ac,out,V,at(1.6),'breathe',.6,pv+.15)}
    // appetite: breath and the price strobes
    S.say(ac,out,A,at(c.appetite0),'breathe',.6,pa+.2);
    c.others.forEach((o,k)=>{if(st.alive[o])S.grain(ac,out,at(c.appetite0+k*.2),{f:mf(100-k*3),d:.12,a:.14,pan:pf,att:.05})});
    // hold 2: the strongest sound, the hatch shutting on the victim's corner
    S.thump(ac,out,at(c.appetite1),2.2,55,.85);S.grain(ac,out,at(c.appetite1),{bp:600,q:2,d:.1,a:.75,pan:.85,att:.05});S.say(ac,out,V,at(c.appetite1+.05),'land',.8,.85);
    if(c.turnBack)S.say(ac,out,V,at(c.appetite1+.15),'react',.7,pv);
    if(c.branch==='giveback'){S.grain(ac,out,at(c.appetite1-.2),{f:mf(93),d:.4,a:.15,pan:.3});S.say(ac,out,'B',at(c.tEnd),'step',.6,pa+.1)}
  },
  trace(g,box,age,K){
    // a short stack of coins on a cut-paper card; tarnishes and thins with age
    const a=Math.max(.15,1-age*.12),n=Math.max(1,5-Math.floor(age/2)),s=Math.min(box.w,box.h);
    g.save();g.translate(box.x+box.w/2,box.y+box.h/2);g.globalAlpha=a;g.rotate(-.08);
    g.fillStyle='#f7f1e0';g.fillRect(-s*.45,-s*.45,s*.9,s*.9);g.fillStyle='#2b2230';g.fillRect(-s*.4,-s*.4,s*.8,s*.8);
    const col=mixc(GOLD,[110,100,90],K.cl(0,1,age*.12));
    for(let k=0;k<n;k++){g.save();g.translate((K.hash(k+age)-.5)*s*.06,s*.22-k*s*.1);g.scale(1,.35);coin(g,s*.22,0,col);g.restore()}
    g.restore();
  }
});
function icon_at(g,k,x,y,s,K){g.save();g.translate(x,y);icon(g,k,s,K);g.restore()}
})();
