(()=>{
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const say=(el,t)=>{const s=el&&el.querySelector('.said');if(s){s.textContent=t;clearTimeout(s._t);s._t=setTimeout(()=>s.textContent='',4000)}};
async function copy(t){try{await navigator.clipboard.writeText(t);return true}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();let ok=false;try{ok=document.execCommand('copy')}catch(_){}a.remove();return ok}}
async function shareLink(box,title,url,text){
  if(navigator.share){try{await navigator.share({title,text:text||title,url});return}catch(e){if(e.name==='AbortError')return}}
  say(box,await copy(text?text+'\n'+url:url)?'Link copied':'Copy failed: '+url)}
async function fetchFile(u,name,onp){
  const r=await fetch(u);if(!r.ok)throw new Error(r.status);const b=await r.blob();onp&&onp(b.size);return new File([b],name,{type:'video/mp4'})}
async function shareFiles(box,items,title){
  // items: [{url,name}]
  const probe=new File([new Blob(['x'])],'a.mp4',{type:'video/mp4'});
  const can=navigator.canShare&&navigator.canShare({files:[probe]});
  if(!can){ // fall back to downloading each
    say(box,items.length>1?`Downloading ${items.length} files`:'Downloading');
    for(const it of items){const a=document.createElement('a');a.href=it.url;a.download=it.name;document.body.appendChild(a);a.click();a.remove();await new Promise(r=>setTimeout(r,700))}
    return}
  const files=[];let got=0;
  for(const [k,it] of items.entries()){say(box,`Preparing ${k+1} of ${items.length}…`);files.push(await fetchFile(it.url,it.name,s=>got+=s))}
  say(box,`Ready · ${(got/1e6).toFixed(0)} MB`);
  try{await navigator.share({files,title})}catch(e){if(e.name!=='AbortError')say(box,'This app would not take the files; try fewer, or Copy links')}}

/* ---------- version page ---------- */
const tabs=$$('.tabs [role=tab]');
if(tabs.length){
  const pick=k=>{tabs.forEach(t=>{const on=t.id==='t-'+k;t.setAttribute('aria-selected',on);$('#'+t.getAttribute('aria-controls')).hidden=!on});};
  tabs.forEach(t=>t.addEventListener('click',()=>{const k=t.id.slice(2);pick(k);history.replaceState(null,'','#'+k)}));
  $('.tabs').addEventListener('keydown',e=>{const i=tabs.indexOf(document.activeElement);if(i<0)return;let j=i;if(e.key==='ArrowRight')j=(i+1)%tabs.length;else if(e.key==='ArrowLeft')j=(i-1+tabs.length)%tabs.length;else return;tabs[j].focus();tabs[j].click();e.preventDefault()});
  const h=location.hash.slice(1).split('-')[0];if(['note','process','agents','source'].includes(h))pick(h);
  const ag=location.hash.match(/^#agent-\d+$/);if(ag){pick('agents');const el=$(ag[0]);el&&el.scrollIntoView()}
}
const box=$('.share');
if(box){box.addEventListener('click',async e=>{const b=e.target.closest('button[data-act]');if(!b)return;const a=b.dataset.act,{title,url,video,file}=box.dataset;
  if(a==='share')shareLink(box,title,url,`${title} · Afterlight: the film, the note that produced it, the process and the critics.`);
  else if(a==='copy')say(box,await copy(url)?'Link copied':url);
  else if(a==='sendvideo'){b.disabled=true;try{await shareFiles(box,[{url:new URL(video,location).href,name:file}],title)}catch(err){say(box,'Could not load the video')}b.disabled=false}})}
// lightbox
const lb=$('#lb');
if(lb){document.addEventListener('click',e=>{const a=e.target.closest('a[data-lb]');if(!a||!lb.showModal)return;e.preventDefault();$('img',lb).src=a.href;$('img',lb).alt=a.dataset.cap;$('p',lb).textContent=a.dataset.cap;lb.showModal()});
  lb.addEventListener('click',e=>{if(e.target===lb)lb.close()})}

/* ---------- set page ---------- */
const set=$('main.set');
if(set){
  const A=window.AFL, root=new URL(set.dataset.root,location).href, M=root+'media/afterlight/';
  const q=new URLSearchParams(location.search).get('v');
  const scope=window.AFL_SEL||A.map((_,i)=>i);
  let chosen=new Set(window.AFL_SEL?scope:(q?q.split(',').map(n=>A.findIndex(x=>x.n===n.padStart(2,'0'))).filter(i=>i>=0):scope));
  const list=$('#plist'),vid=$('#sv'),now=$('#now'),bar=$('#sbar');let cur=-1,queue=[];
  const fmt=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`, sec=r=>/:/.test(r)?r.split(':').reduce((m,s)=>m*60+ +s,0):0;
  scope.forEach(i=>{const x=A[i];const li=document.createElement('li');li.dataset.i=i;if(!x.film)li.classList.add('nofilm');
    li.innerHTML=`<input type="checkbox" aria-label="Include AFL-${x.n} ${x.title}" ${chosen.has(i)?'checked':''}>
      <button class="th" type="button" style="background-image:url(${M}thumbs/${x.id}.jpg)" aria-label="${x.film?'Play':'Open'} ${x.title}"><b>${x.n}</b></button>
      <div class="tx"><strong>${x.title}</strong><span>AFL-${x.n} · ${x.rt}${x.film?' · '+(x.size/1e6).toFixed(1)+' MB':''}</span>
      <nav><a href="${root}afterlight/v/${x.slug}/">Trace</a>${x.film?`<a href="${M}${x.id}.mp4" download="afterlight-${x.slug}.mp4">Video</a><button type="button" data-one>Send</button>`:`<a href="${root}afterlight/${x.link}">Open</a>`}</nav></div>`;
    list.appendChild(li)});
  function upd(){const sel=[...chosen].sort((a,b)=>a-b),films=sel.filter(i=>A[i].film),t=films.reduce((s,i)=>s+sec(A[i].rt),0),mb=films.reduce((s,i)=>s+A[i].size,0)/1e6;
    $('#cnt').textContent=`${sel.length} chosen · ${films.length} films · ${fmt(t)}`;
    $('#sum').textContent=`${scope.filter(i=>A[i].film).length} films in this set`;
    const sv=bar.querySelector('[data-act=sendvideos]');sv.innerHTML=`Send the videos <small>${mb.toFixed(0)} MB</small>`;
    bar.querySelectorAll('button').forEach(b=>b.disabled=b.dataset.act!=='copylinks'&&b.dataset.act!=='sendlinks'?!films.length:!sel.length)}
  list.addEventListener('change',e=>{const li=e.target.closest('li');const i=+li.dataset.i;e.target.checked?chosen.add(i):chosen.delete(i);upd()});
  function play(i,auto){const x=A[i];if(!x.film){location.href=root+'afterlight/'+x.link;return}cur=i;vid.src=M+x.id+'.mp4';vid.poster=M+'thumbs/'+x.id+'.jpg';now.textContent=`AFL-${x.n} · ${x.title}`;
    $$('li',list).forEach(l=>l.setAttribute('aria-current',+l.dataset.i===i));if(auto)vid.play().catch(()=>{})}
  vid.addEventListener('ended',()=>{const k=queue.indexOf(cur);if(k>=0&&k<queue.length-1)play(queue[k+1],true)});
  list.addEventListener('click',async e=>{const li=e.target.closest('li');if(!li)return;const i=+li.dataset.i,x=A[i];
    if(e.target.closest('.th')){queue=[...chosen].filter(j=>A[j].film).sort((a,b)=>a-b);if(!queue.includes(i))queue=[i];play(i,true);vid.scrollIntoView({block:'nearest'})}
    else if(e.target.closest('[data-one]')){const b=e.target.closest('[data-one]');b.textContent='…';try{await shareFiles(bar,[{url:M+x.id+'.mp4',name:`afterlight-${x.slug}.mp4`}],`AFL-${x.n} ${x.title}`)}catch(_){say(bar,'Could not load the video')}b.textContent='Send'}});
  bar.addEventListener('click',async e=>{const b=e.target.closest('button[data-act]');if(!b)return;const sel=[...chosen].sort((a,b)=>a-b),films=sel.filter(i=>A[i].film);
    if(b.dataset.act==='play'){queue=films;if(queue.length){play(queue[0],true);vid.scrollIntoView({block:'nearest'})}}
    else if(b.dataset.act==='sendvideos'){b.disabled=true;try{await shareFiles(bar,films.map(i=>({url:M+A[i].id+'.mp4',name:`afterlight-${A[i].slug}.mp4`})),bar.dataset.title)}catch(_){say(bar,'Could not load the videos')}b.disabled=false}
    else if(b.dataset.act==='sendlinks'){const whole=window.AFL_SEL&&sel.length===scope.length;const url=whole?bar.dataset.url:`${root}afterlight/set/?v=${sel.map(i=>A[i].n).join(',')}`;
      shareLink(bar,bar.dataset.title,url,`Afterlight · ${sel.length} ${sel.length>1?'pieces':'piece'}: ${sel.map(i=>A[i].title).join(', ')}`)}
    else if(b.dataset.act==='copylinks'){const t=sel.map(i=>`AFL-${A[i].n} ${A[i].title} (${A[i].rt}) ${root}afterlight/v/${A[i].slug}/`).join('\n');say(bar,await copy(t)?`${sel.length} links copied`:'Copy failed')}});
  document.querySelector('.selall').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;chosen=new Set(b.hasAttribute('data-all')?scope:[]);$$('input',list).forEach(c=>c.checked=chosen.has(+c.closest('li').dataset.i));upd()});
  upd();const first=[...chosen].sort((a,b)=>a-b).find(i=>A[i].film);if(first!==undefined)play(first,false);
}
})();
