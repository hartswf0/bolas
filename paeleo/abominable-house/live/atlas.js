// THE ATLAS: the possibility space of the film, seen whole.
// MAP: 6,030 films (agents in three PIE modes, random films, author films) placed by any two measures; colour is a third.
// TREE: the next three deeds from any prefix, as an icicle; height = probability under the agents, colour = how believable the deed is. Click to zoom in.
// COMPARE: two films' tableaux and audience curves on top of each other, with the cells that differ marked.
// Editing: tap a cell in the panel tableau to make that sack the doer of that deed, tap another row in the same column to make it the victim.
window.ATLAS=(function(){
 const D=window.ATLASDATA,IDSa=['R','B','I','O'],PAIRS=LEDGER.PAIRS,ORDER=LEDGER.ORDER;
 const MS=[['b','believability'],['lp','log P'],['ir','irony'],['su','suspense'],['tw','twist'],['sp','surprise'],['d','deaths'],['h','strands holding'],['wk','exactitude (weakest strand)'],['mu','multiplicity (doers)'],['vi','visibility (witnessed)'],['x','map 1: Roessler acts / Roessler is knifed'],['y','map 2: Roessler spies / Ogiva is tied']];
 const SRC=['practical','hybrid','symbolic','random','author'];const srcOf=s=>s.startsWith('author')?'author':s;
 const F=D.films.map(r=>({...r,film:r.f.split('').map(c=>parseInt(c,12)),src2:srcOf(r.src)}));
 const sorted={};for(const[m]of MS)sorted[m]=F.map(r=>r[m]).sort((a,b)=>a-b);
 const pctl=(m,v)=>{const a=sorted[m];let lo=0,hi=a.length;while(lo<hi){const mid=(lo+hi)>>1;if(a[mid]<v)lo=mid+1;else hi=mid}return lo/a.length};
 let view='map',X='x',Y='y',CO='b',show=new Set(SRC),sel=null,pinA=null,trail=[],undo=[],hover=null,pick=null,focus=[],cv,g,W=0,H=0,dpr=1;
 const cache=new Map();
 function project(film){const v=feat(film);let a=0,b=0;for(let i=0;i<v.length;i++){const c=v[i]-D.pca.mean[i];a+=c*D.pca.c1[i];b+=c*D.pca.c2[i]}return[a,b]}
 function feat(film){const v=Array(96).fill(0);film.forEach((p,k)=>{const[a,vv]=PAIRS[p];v[k*4+IDSa.indexOf(a)]=1;v[48+k*4+IDSa.indexOf(vv)]=1});return v}
 function measure(film){const key=film.join(',');if(cache.has(key))return cache.get(key);const sc=STORY.score(film),au=CROSSED.audience(film),cs=CROSSED.strands(film,au),st=sc.L.states[12];const sum=f=>au.reduce((a,x)=>a+x[f],0);const[x,y]=project(film);
  const cnt={};for(const p of film){const a=PAIRS[p][0];cnt[a]=(cnt[a]||0)+1}let Hh=0;for(const v of Object.values(cnt)){const q=v/12;Hh-=q*Math.log(q)}let wv=0;for(let k=0;k<12;k++){const[a,v]=PAIRS[film[k]];if(IDSa.some(o=>o!==a&&o!==v&&st.know[o].includes(k)))wv++}
  const r={film,mu:Math.exp(Hh),vi:wv/12,b:sc.believ,lp:sc.logp,ir:sum('irony'),su:sum('suspense'),tw:Math.max(...au.map(q=>q.twist)),sp:sum('surprise')/12,d:IDSa.filter(q=>!st.alive[q]).length,h:cs.holding,wk:cs.min,c:st.impossible.length,x,y,au,cs,sc};cache.set(key,r);return r}
 // ---- colour: dim to ember to pale, for a dark ground ----
 const STOPS=[[52,48,44],[176,74,44],[244,226,176]];const ramp=u=>{u=Math.max(0,Math.min(1,u));const s=u<.5?0:1,t=u<.5?u*2:(u-.5)*2;const a=STOPS[s],b=STOPS[s+1];return`rgb(${a.map((x,i)=>Math.round(x+(b[i]-x)*t)).join(',')})`};
 const range=m=>[sorted[m][Math.floor(sorted[m].length*.01)],sorted[m][Math.floor(sorted[m].length*.99)]];
 // ---- MAP ----
 const PAD={l:56,r:18,t:30,b:44};let RX,RY;
 const sx=v=>PAD.l+(v-RX[0])/(RX[1]-RX[0]||1)*(W-PAD.l-PAD.r),sy=v=>H-PAD.b-(v-RY[0])/(RY[1]-RY[0]||1)*(H-PAD.t-PAD.b);
 function drawMap(){const[x0,x1]=range(X),[y0,y1]=range(Y);const px=(x1-x0)*.04||1,py=(y1-y0)*.04||1;RX=[x0-px,x1+px];RY=[y0-py,y1+py];const[c0,c1]=range(CO);
  g.strokeStyle='#2e2a25';g.lineWidth=1;g.fillStyle='#958a7a';g.font='11px JetBrains Mono, monospace';g.textAlign='center';
  for(let i=0;i<=4;i++){const v=RX[0]+(RX[1]-RX[0])*i/4,xx=sx(v);g.beginPath();g.moveTo(xx,PAD.t);g.lineTo(xx,H-PAD.b);g.stroke();g.fillText(fmt(v),xx,H-PAD.b+16)}
  g.textAlign='right';for(let i=0;i<=4;i++){const v=RY[0]+(RY[1]-RY[0])*i/4,yy=sy(v);g.beginPath();g.moveTo(PAD.l,yy);g.lineTo(W-PAD.r,yy);g.stroke();g.fillText(fmt(v),PAD.l-6,yy+4)}
  g.textAlign='center';g.fillStyle='#ece3d2';g.fillText(lab(X)+' →',(PAD.l+W-PAD.r)/2,H-8);g.save();g.translate(14,(PAD.t+H-PAD.b)/2);g.rotate(-Math.PI/2);g.fillText(lab(Y)+' →',0,0);g.restore();
  g.textAlign='left';g.fillStyle='#958a7a';g.fillText(`${vis().length.toLocaleString()} films · colour: ${lab(CO)}`,PAD.l,18);
  const jit=(r,k)=>(X==='d'||X==='h'||k==='y'&&(Y==='d'||Y==='h'))?0:0;
  for(const r of vis()){const xx=sx(r[X]),yy=sy(r[Y]);g.fillStyle=ramp((r[CO]-c0)/(c1-c0||1));if(r.src2==='author'){g.save();g.translate(xx,yy);g.rotate(Math.PI/4);g.fillRect(-3.5,-3.5,7,7);g.restore()}else{g.globalAlpha=r.src2==='random'?.55:.85;g.fillRect(xx-1.6,yy-1.6,3.2,3.2);g.globalAlpha=1}}
  // the edit trail and the selected / pinned films
  if(trail.length>1){g.strokeStyle='#efe6d3';g.setLineDash([4,4]);g.lineWidth=1.5;g.beginPath();trail.forEach((r,i)=>{const xx=sx(r[X]),yy=sy(r[Y]);i?g.lineTo(xx,yy):g.moveTo(xx,yy)});g.stroke();g.setLineDash([])}
  if(pinA)ring(pinA,'#7fb3c8','A');if(sel)ring(sel,'#efe6d3','B');
  if(hover&&hover!==sel){ring(hover,'#efe6d3','');glyph(hover,Math.min(W-236,sx(hover[X])+12),Math.max(8,sy(hover[Y])-70))}
  // colour key
  const kx=W<640?PAD.l+48:W-PAD.r-190,ky=W<640?PAD.t-4:12;for(let i=0;i<70;i++){g.fillStyle=ramp(i/69);g.fillRect(kx+i*2,ky,2,8)}g.fillStyle='#958a7a';g.textAlign='right';g.fillText(fmt(c0),kx-4,ky+8);g.textAlign='left';g.fillText(fmt(c1),kx+144,ky+8)}
 function ring(r,col,t){const xx=sx(r[X]),yy=sy(r[Y]);g.strokeStyle=col;g.lineWidth=2;g.beginPath();g.arc(xx,yy,7,0,7);g.stroke();if(t){g.fillStyle=col;g.font='600 11px JetBrains Mono, monospace';g.textAlign='left';g.fillText(t,xx+9,yy-8)}}
 // a film drawn as its tableau: rows are sacks, columns deeds; filled = doer, outlined = victim
 function glyph(r,x,y,cw=15,ch=12,box=true,diff=null){const film=r.film;const w=cw*12+50,h=ch*4+30;if(box){g.fillStyle='rgba(11,10,9,.92)';g.fillRect(x,y,w,h);g.strokeStyle='#2e2a25';g.strokeRect(x,y,w,h)}
  g.font='10px JetBrains Mono, monospace';g.textAlign='left';
  IDSa.forEach((s,i)=>{g.fillStyle=COL[s];g.fillRect(x+6,y+6+i*ch+2,8,ch-4);g.fillStyle='#958a7a';g.fillText(s,x+18,y+6+i*ch+ch-3);
   for(let k=0;k<12;k++){const[a,v]=PAIRS[film[k]];const cx=x+30+k*cw,cy=y+6+i*ch;if(a===s){g.fillStyle=COL[s]==='#2a2622'?'#5a524a':COL[s];g.fillRect(cx+1,cy+1,cw-2,ch-2)}else if(v===s){g.strokeStyle=COL[a]==='#2a2622'?'#8a8278':COL[a];g.lineWidth=1.5;g.strokeRect(cx+1.5,cy+1.5,cw-3,ch-3)}else{g.fillStyle='#1d1a17';g.fillRect(cx+1,cy+1,cw-2,ch-2)}
    if(diff&&diff[k]){g.strokeStyle='#e0603f';g.lineWidth=2;g.strokeRect(cx,cy,cw,ch)}}});
  if(box){g.fillStyle='#ece3d2';g.fillText(`believ ${r.b.toFixed(2)}${r.ir!=null?' · irony '+r.ir.toFixed(2):''} · deaths ${r.d}`,x+6,y+h-6)}}
 // ---- TREE: three deeds ahead of the focus prefix ----
 let TREE=null;
 function pie(){return{P:+document.getElementById('pP').value/100,I:+document.getElementById('pI').value/100,E:+document.getElementById('pE').value/100}}
 function stateAt(prefix){let st=LEDGER.init();const mind=AGENTS.newMind();prefix.forEach((p,k)=>{st=CROSSED.agentStep(st,mind,k,p)});return{st,mind}}
 function cloneMind(m){return JSON.parse(JSON.stringify(m))}
 function nextDist(st,mind,k,P){const tau=.08+P.E*1.6;const U=PAIRS.map(([a,v])=>AGENTS.utility(st,k,a,v,mind,P));const l=U.map(u=>Math.log(Math.max(u,1e-12))/tau);const mx=Math.max(...l);const w=l.map(x=>Math.exp(x-mx));const z=w.reduce((a,b)=>a+b,0);return w.map(x=>x/z)}
 function buildTree(){const P=pie();const k0=focus.length;const root=stateAt(focus);const evs=focus.map((p,k)=>({k,deed:ORDER[k],A:PAIRS[p][0],V:PAIRS[p][1]}));
  function expand(node,depth){const k=k0+depth;if(k>=12||depth>=3)return;const p=nextDist(node.st,node.mind,k,P);node.kids=p.map((pr,i)=>{const[a,v]=PAIRS[i];const raw=STORY.rate(node.st,k,a,v,{ev:node.ev}).raw;const bad=!node.st.alive[a]||!node.st.alive[v];return{i,p:pr,raw,bad,k,path:node.path.concat([i]),node}});
   if(depth<2)for(const c of node.kids){if(c.p<.004)continue;const m=cloneMind(node.mind);const st=CROSSED.agentStep(node.st,m,k,c.i);Object.assign(c,{st,mind:m,ev:node.ev.concat([{k,deed:ORDER[k],A:PAIRS[c.i][0],V:PAIRS[c.i][1]}])});expand(c,depth+1)}}
  TREE={st:root.st,mind:root.mind,ev:evs,path:focus.slice()};expand(TREE,0)}
 let cells=[];
 function drawTree(){if(!TREE)buildTree();cells=[];const k0=focus.length;g.font='11px JetBrains Mono, monospace';g.textAlign='left';
  const trunkW=Math.min(170,W*.22),colW=(W-trunkW-24)/3,top=30,hh=H-top-14;
  g.fillStyle='#958a7a';g.fillText(k0>=12?'the film is complete':`from deed ${RN[k0]} · height = probability under the agents · colour = believability · tap to zoom in`,8,18);
  // trunk: the focus prefix as breadcrumbs
  const bh=Math.min(22,hh/Math.max(1,k0+1));for(let k=0;k<=k0;k++){const y=top+k*bh;const label=k===0?'start':`${RN[k-1]} ${PAIRS[focus[k-1]][0]}→${PAIRS[focus[k-1]][1]}`;g.fillStyle=k===k0?'#e0603f':'#ece3d2';g.fillText(label,8,y+14);cells.push({x:0,y,w:trunkW,h:bh,zoom:focus.slice(0,k)})}
  if(k0>=12)return;
  function lay(node,depth,y0,h){if(!node.kids)return;let y=y0;for(const c of node.kids){const ch=c.p*h;const x=trunkW+12+depth*colW;if(ch>=.6){g.fillStyle=c.bad?'#2a1414':ramp(c.raw);g.fillRect(x,y,colW-3,Math.max(.6,ch-1));
     if(ch>13){const[a,v]=PAIRS[c.i];g.fillStyle=c.raw>.55?'#1d1812':'#ece3d2';g.fillText(`${RN[c.k]} ${WHO[a]}→${WHO[v]}`.slice(0,Math.floor(colW/7)),x+4,y+Math.min(ch,30)/2+4);if(ch>30){g.fillStyle=c.raw>.55?'#3b3128':'#958a7a';g.fillText(`p ${c.p.toFixed(2)} · b ${c.raw.toFixed(2)}${c.bad?' · dead acts':''}`,x+4,y+Math.min(ch,30)/2+18)}}
     cells.push({x,y,w:colW-3,h:ch,zoom:c.path,c});lay(c,depth+1,y,ch)}y+=ch}}
  lay(TREE,0,top,hh);
  g.fillStyle='#958a7a';for(let d=0;d<3&&k0+d<12;d++)g.fillText(NAMES[k0+d],trunkW+12+d*colW,H-2)}
 // ---- COMPARE ----
 function drawCompare(){g.font='12px JetBrains Mono, monospace';g.textAlign='left';if(!pinA||!sel){g.fillStyle='#958a7a';g.fillText('Pin a film as A (PIN A), then select another on the map or edit it: B. They are compared here.',16,30);return}
  const a=pinA,b=sel;const diff=a.film.map((p,k)=>p!==b.film[k]);const cw=Math.max(12,Math.min(30,(W*.48-50)/12)),ch=Math.max(10,Math.min(22,H*.06));
  g.fillStyle='#7fb3c8';g.fillText('A',16,22);glyph(a,30,8,cw,ch,false,diff);g.fillStyle='#efe6d3';g.fillText('B',16+W/2,22);glyph(b,30+W/2,8,cw,ch,false,diff);
  g.fillStyle='#958a7a';g.fillText(`${diff.filter(Boolean).length} of 12 deeds differ (marked)`,30,ch*4+32);
  const ms=[['surprise','surprise'],['twist','twist'],['suspense','suspense'],['irony','irony']];const top=ch*4+48,rowH=(H-top-90)/4,x0=110,x1=W-150;
  ms.forEach(([f,l],i)=>{const y=top+i*rowH;const va=a.au.map(q=>q[f]),vb=b.au.map(q=>q[f]);const mx=Math.max(.3,...va,...vb);g.fillStyle='#ece3d2';g.fillText(l,16,y+rowH/2);
   g.strokeStyle='#2e2a25';g.lineWidth=1;g.strokeRect(x0,y+4,x1-x0,rowH-10);
   for(const[v,col,dash]of[[va,'#7fb3c8',[]],[vb,'#efe6d3',[5,4]]]){g.strokeStyle=col;g.setLineDash(dash);g.lineWidth=2;g.beginPath();v.forEach((q,k)=>{const xx=x0+k/11*(x1-x0),yy=y+rowH-8-q/mx*(rowH-16);k?g.lineTo(xx,yy):g.moveTo(xx,yy)});g.stroke()}g.setLineDash([]);
   const sa=f==='twist'?Math.max(...va):va.reduce((p,q)=>p+q,0),sb=f==='twist'?Math.max(...vb):vb.reduce((p,q)=>p+q,0);g.fillStyle='#958a7a';g.fillText(`A ${sa.toFixed(2)}  B ${sb.toFixed(2)}`,x1+10,y+rowH/2)});
  for(let k=0;k<12;k++){g.fillStyle=diff[k]?'#e0603f':'#958a7a';g.textAlign='center';g.fillText(RN[k],x0+k/11*(x1-x0),H-74)}g.textAlign='left';
  const rows=[['believability','b'],['deaths','d'],['strands holding','h'],['weakest strand','wk']];rows.forEach(([l,m],i)=>{g.fillStyle='#ece3d2';g.fillText(`${l}: A ${fmt(a[m])} · B ${fmt(b[m])} (${b[m]>=a[m]?'+':''}${fmt(b[m]-a[m])})`,16+(i%2)*W/2,H-44+Math.floor(i/2)*18)})}
 const fmt=v=>Math.abs(v)>=10?v.toFixed(0):Math.abs(v)>=1?v.toFixed(1):v.toFixed(2);const lab=m=>MS.find(q=>q[0]===m)[1];
 const vis=()=>F.filter(r=>show.has(r.src2));
 // ---- SIX MEMOS: the elite archive, one best film per cell of exactitude x multiplicity x visibility ----
 let MCELLS=[];
 function drawMemos(){const E=D.elites,B=E.bins,cnt=D.count;MCELLS=[];g.font='11px JetBrains Mono, monospace';g.textAlign='left';
  const wrap=(t,x,y)=>{const words=t.split(' ');let line='';for(const w of words){const tt=line?line+' '+w:w;if(g.measureText(tt).width>W-24&&line){g.fillText(line,x,y);y+=15;line=w}else line=tt}g.fillText(line,x,y);return y+16};let yy=18;
  const tot=BigInt(cnt.total),all=BigInt(cnt.all);g.fillStyle='#ece3d2';yy=wrap(`${Number(tot).toLocaleString()} of ${Number(all).toLocaleString()} films are consistent (${(Number(tot)/Number(all)*100).toFixed(2)}%), counted exactly`,12,yy);
  const bd=cnt.byDeaths;g.fillStyle='#958a7a';yy=wrap(`deaths: none ${(Number(bd[0])/Number(tot)*100).toFixed(1)}% · one ${(Number(bd[1])/Number(tot)*100).toFixed(1)}% · two ${(Number(bd[2]||0)/Number(tot)*100).toFixed(2)}% · tiers estimated: ${Object.entries(cnt.tiers).map(([t,v])=>t.toLowerCase()+' '+(v.share*100).toFixed(1)+'% ±'+(v.ci95*100).toFixed(1)).join(' · ')}`,12,yy);
  yy=wrap(`archive: ${E.cells.length} of 125 cells filled from ${E.evals.toLocaleString()} films · only films whose four strands hold enter · colour = believability`,12,yy);
  const by=new Map(E.cells.map(c=>[c.key,c]));const nf=5,top=yy+10,narrow=W<700;const fw=narrow?(W-24)/3:(W-24-(nf-1)*14)/nf,cw=Math.min(fw/5,narrow?Math.max(12,(H-top-112)/10):60),chh=cw;
  for(let v=0;v<nf;v++){const fx=narrow?12+(v%3)*(fw):12+v*(fw+14),fy=narrow?top+Math.floor(v/3)*(chh*5+56):top;g.fillStyle='#ece3d2';g.fillText(`${narrow?'vis':'visibility'} ${B.VI[v].toFixed(2)}-${Math.min(1,B.VI[v+1]).toFixed(2)}`,fx,fy+10);
   for(let e=0;e<5;e++)for(let m=0;m<5;m++){const x=fx+m*cw,y=fy+16+(4-e)*chh;const c=by.get([e,m,v].join(','));
    if(c){g.fillStyle=ramp((c.q-.5)/.45);g.fillRect(x+1,y+1,cw-2,chh-2);if(sel&&sel.film.join()===c.film.join()){g.strokeStyle='#efe6d3';g.lineWidth=2;g.strokeRect(x+1,y+1,cw-2,chh-2)}if(cw>34){g.fillStyle=c.q>.75?'#1d1812':'#ece3d2';g.fillText(c.q.toFixed(2),x+4,y+14)}MCELLS.push({x,y,w:cw,h:chh,c})}
    else{g.strokeStyle='#2e2a25';g.lineWidth=1;g.strokeRect(x+1.5,y+1.5,cw-3,chh-3)}}
   g.fillStyle='#958a7a';g.fillText('multiplicity →',fx,fy+16+5*chh+14)}
  g.save();g.translate(8,top+16+2.5*chh+40);g.rotate(-Math.PI/2);g.fillStyle='#958a7a';g.fillText('exactitude →',0,0);g.restore();
  const hv=hover&&hover.c;if(hv)glyph({film:hv.film,b:hv.q,ir:null,d:hv.d},Math.min(W-236,hover.x+hover.w+6),Math.max(8,hover.y-20))}
 function draw(){if(!cv)return;g.setTransform(dpr,0,0,dpr,0,0);g.fillStyle='#0b0a09';g.fillRect(0,0,W,H);if(view==='map')drawMap();else if(view==='tree')drawTree();else if(view==='memos')drawMemos();else drawCompare()}
 function resize(){if(!cv)return;const r=cv.getBoundingClientRect();dpr=Math.min(2,devicePixelRatio||1);W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;draw()}
 // ---- selection, editing, panel ----
 function select(r,{push=true}={}){if(sel&&push)undo.push(sel.film.slice());sel=measure(r.film);if(!trail.length||trail[trail.length-1].film.join()!==sel.film.join())trail.push(sel);if(trail.length>40)trail.shift();TREE=null;panelA();draw()}
 function setPair(k,a,v){const f=sel.film.slice();const i=PAIRS.findIndex(([x,y])=>x===a&&y===v);if(i<0)return;f[k]=i;select({film:f})}
 function panelA(){const el=document.getElementById('atlasP');if(!sel){el.querySelector('#asel').innerHTML='<div class=mute>tap a film on the map</div>';return}const r=sel;
  const bars=MS.filter(([m])=>!['x','y'].includes(m)).map(([m,l])=>{const p=pctl(m,r[m]);return`<div class=pl><span>${l}</span><div class=bar><i style="left:0;width:${(p*100).toFixed(0)}%"></i></div><span>${fmt(r[m])} · ${(p*100).toFixed(0)}th</span></div>`}).join('');
  let h=`<div class=mute>film ${enc(r.film).toLocaleString('en-US')} · <span class='tier T${TIERN.indexOf(r.sc.tier)}'>${r.sc.tier}</span>${r.c?' · '+r.c+' contradiction(s)':''}</div>${bars}
  <div class=mute style="margin:6px 0 2px">${pick!=null?`deed ${RN[pick]}: now tap the victim in the same column`:'tap a cell: that sack does that deed · tap again in the column: the victim'}</div><div id=etab></div>`;
  el.querySelector('#asel').innerHTML=h;const T=r.cs.per;let g2='<div></div>'+RN.map((x,k)=>`<div class="hd ${pick===k?'cur':''}">${x}</div>`).join('')+'<div class=hd>strand</div>';
  for(const id of IDSa){g2+=`<div><span class=chip style="background:${COL[id]}"></span>${WHO[id]}</div>`;for(const c of T[id].cards){const sty=c.role==='A'?`background:${COL[id]};border-color:${COL[id]}`:c.role==='V'?`border:2px solid ${COL[c.other]}`:'';
    g2+=`<div class="cell ${c.role} ${c.dead?'dead':''} ${pick===c.k?'cur':''}" data-k=${c.k} data-s=${id} style="${sty}">${c.role==='A'?'→'+c.other:c.role==='V'?'←'+c.other:''}</div>`}g2+=`<div><span class='tier T${TIERN.indexOf(T[id].tier)}'>${T[id].tier.slice(0,4)}</span></div>`}
  const et=el.querySelector('#etab');et.innerHTML=g2;et.querySelectorAll('.cell').forEach(d=>d.onclick=()=>{const k=+d.dataset.k,s=d.dataset.s;const[a,v]=PAIRS[sel.film[k]];
   if(pick===k&&s!==a){pick=null;setPair(k,a,s);return}if(s===a){pick=pick===k?null:k;panelA();return}pick=k;setPair(k,s,v===s?a:v)})}
 function nearest(mx,my){let best=null,bd=144;for(const r of vis()){const dx=sx(r[X])-mx,dy=sy(r[Y])-my,d=dx*dx+dy*dy;if(d<bd){bd=d;best=r}}return best}
 function init(){cv=document.getElementById('ac');g=cv.getContext('2d');new ResizeObserver(resize).observe(cv);
  const pt=e=>{const r=cv.getBoundingClientRect();return[e.clientX-r.left,e.clientY-r.top]};
  cv.onpointermove=e=>{if(view==='memos'){const[mx,my]=pt(e);const h=MCELLS.find(q=>mx>=q.x&&mx<=q.x+q.w&&my>=q.y&&my<=q.y+q.h)||null;if(h!==hover){hover=h;draw()}return}if(view!=='map')return;const[mx,my]=pt(e);const h=nearest(mx,my);if(h!==hover){hover=h;draw()}};
  cv.onpointerleave=()=>{hover=null;draw()};
  cv.onclick=e=>{const[mx,my]=pt(e);if(view==='memos'){const h=MCELLS.find(q=>mx>=q.x&&mx<=q.x+q.w&&my>=q.y&&my<=q.y+q.h);if(h)select({film:h.c.film})}else if(view==='map'){const h=nearest(mx,my);if(h)select(h)}else if(view==='tree'){const c=cells.filter(q=>mx>=q.x&&mx<=q.x+q.w&&my>=q.y&&my<=q.y+q.h).pop();if(c){focus=c.zoom.slice();TREE=null;draw()}}};
  const P=document.getElementById('atlasP');
  const sel3=(id,v)=>{const s=P.querySelector('#'+id);s.innerHTML=MS.map(([m,l])=>`<option value=${m} ${m===v?'selected':''}>${l}</option>`).join('');return s};
  sel3('ax',X).onchange=e=>{X=e.target.value;draw()};sel3('ay',Y).onchange=e=>{Y=e.target.value;draw()};sel3('aco',CO).onchange=e=>{CO=e.target.value;draw()};
  P.querySelector('#asrc').innerHTML=SRC.map(s=>`<button class=on data-s=${s}>${s.toUpperCase()}</button>`).join('');P.querySelectorAll('#asrc button').forEach(b=>b.onclick=()=>{const s=b.dataset.s;show.has(s)?show.delete(s):show.add(s);b.classList.toggle('on',show.has(s));draw()});
  for(const v of['map','tree','memos','compare'])P.querySelector('#v_'+v).onclick=()=>{view=v;P.querySelectorAll('.vb').forEach(b=>b.classList.toggle('on',b.id==='v_'+v));P.querySelector('#mapc').style.display=v==='map'?'':'none';if(v==='tree'&&sel&&!focus.length)focus=[];TREE=null;draw()};
  P.querySelector('#a_undo').onclick=()=>{const f=undo.pop();if(f)select({film:f},{push:false})};
  P.querySelector('#a_pin').onclick=()=>{if(sel){pinA=sel;draw()}};
  P.querySelector('#a_play').onclick=()=>{if(sel){close();setFilm(sel.film.slice())}};
  P.querySelector('#a_complete').onclick=()=>{const P2=pie();const{st:st0,mind}=stateAt(focus);let st=st0;const f=focus.slice();for(let k=f.length;k<12;k++){const p=nextDist(st,mind,k,P2);const i=p.indexOf(Math.max(...p));f.push(i);st=CROSSED.agentStep(st,mind,k,i)}select({film:f})};
  P.querySelector('#a_focus').onclick=()=>{if(sel){focus=sel.film.slice(0,pick!=null?pick:3);view='tree';P.querySelectorAll('.vb').forEach(b=>b.classList.toggle('on',b.id==='v_tree'));P.querySelector('#mapc').style.display='none';TREE=null;draw()}};
  ['pP','pI','pE'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{TREE=null;if(view==='tree')draw()}))}
 let inited=false;
 function setView(v){const P=document.getElementById('atlasP');view=v;hover=null;P.querySelectorAll('.vb').forEach(b=>b.classList.toggle('on',b.id==='v_'+v));P.querySelector('#mapc').style.display=v==='map'?'':'none';draw()}
 function open(){if(!inited){init();inited=true}document.body.classList.add('atlas');if(!sel)select({film:film.slice()},{push:false});resize()}
 function close(){document.body.classList.remove('atlas')}
 return{open,close,draw,setView,select:f=>select({film:f}),get sel(){return sel}}})();
