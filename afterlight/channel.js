(()=>{
const $=s=>document.querySelector(s), A=window.AFL, REEL=window.REEL, SITE=window.SITE, M=(window.ROOT||'../')+'media/afterlight/';
const toast=$('#toast');const say=t=>{toast.textContent=t;toast.classList.add('on');clearTimeout(say.t);say.t=setTimeout(()=>toast.classList.remove('on'),3500)};
async function copy(t){try{await navigator.clipboard.writeText(t);return true}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();let ok=false;try{ok=document.execCommand('copy')}catch(_){}a.remove();return ok}}
const pageUrl=x=>`${SITE}afterlight/v/${x.slug}/`;
async function sendPage(x){const title=`AFL-${x.n} ${x.title} · Afterlight`,url=pageUrl(x);
  if(navigator.share){try{await navigator.share({title,text:`${title}: the film, the note that produced it, the process and the critics.`,url});return}catch(e){if(e.name==='AbortError')return}}
  say(await copy(url)?'Link copied: '+url:url)}
async function sendVideo(x,btn){const name=`afterlight-${x.slug}.mp4`,u=M+x.id+'.mp4';
  const probe=new File([new Blob(['x'])],'a.mp4',{type:'video/mp4'});
  if(!(navigator.canShare&&navigator.canShare({files:[probe]}))){const a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();say('Downloading '+name);return}
  const old=btn&&btn.textContent;if(btn)btn.textContent=`Loading ${(x.size/1e6).toFixed(0)} MB…`;
  try{const b=await (await fetch(u)).blob();await navigator.share({files:[new File([b],name,{type:'video/mp4'})],title:`AFL-${x.n} ${x.title}`})}
  catch(e){if(e.name!=='AbortError')say('Could not send the file; try Send page')}
  if(btn)btn.textContent=old}

/* reel */
const v=$('#rv');if(!v){const grid=$('#cgrid');
 grid.addEventListener('click',e=>{const b=e.target.closest('[data-play],[data-send],[data-file]');if(!b)return;
  if(b.dataset.play)location.href=`../v/${A[+b.dataset.play].slug}/`;else if(b.dataset.send)sendPage(A[+b.dataset.send]);else sendVideo(A[+b.dataset.file],b)});
 document.querySelector('.filt').addEventListener('click',e=>{const b=e.target.closest('button[data-f]');if(!b)return;const f=b.dataset.f;document.querySelectorAll('.filt button').forEach(x=>x.setAttribute('aria-pressed',x===b));grid.querySelectorAll('li').forEach(li=>li.hidden=!(f==='all'||(f==='best'?li.classList.contains('best'):li.dataset.era===f)))});
 return}
const bar=$('#rbar'),snd=$('#snd');let cur=-1,inReel=true;
const tot=REEL.reduce((s,i)=>s+sec(A[i].rt),0);function sec(r){return /:/.test(r)?r.split(':').reduce((m,s)=>m*60+ +s,0):0}
REEL.forEach((i,k)=>{const b=document.createElement('button');b.type='button';b.style.flexGrow=sec(A[i].rt);b.title=`${A[i].title} · ${A[i].rt}`;b.setAttribute('aria-label',`Play ${A[i].title}`);b.innerHTML='<span></span>';b.onclick=()=>play(i,true);bar.appendChild(b)});
function play(i,user){const x=A[i];cur=i;inReel=REEL.includes(i);v.src=M+x.id+'.mp4';v.poster=M+'thumbs/'+x.id+'.jpg';
  if(user){v.muted=false;snd.hidden=true;v.controls=true}
  v.play().catch(()=>{v.muted=true;v.play().catch(()=>{})});
  const k=REEL.indexOf(i);$('#rpos').textContent=inReel?`Reel ${k+1} of ${REEL.length} · AFL-${x.n} · ${x.rt}`:`AFL-${x.n} · ${x.rt} · not in the reel`;
  $('#rtitle').textContent=x.title;$('#rtrace').href=`v/${x.slug}/`;
  [...bar.children].forEach((b,j)=>b.classList.toggle('on',REEL[j]===i));
  document.querySelectorAll('.cgrid li').forEach(li=>li.classList.toggle('playing',li.id==='c-'+x.slug));
  history.replaceState(null,'','#'+x.slug)}
function step(d){const k=REEL.indexOf(cur);play(REEL[k<0?0:(k+d+REEL.length)%REEL.length],!v.muted)}
v.addEventListener('ended',()=>step(1));
v.addEventListener('timeupdate',()=>{const k=REEL.indexOf(cur);if(k<0)return;const s=bar.children[k].querySelector('span');s.style.width=(v.currentTime/(v.duration||1)*100)+'%'});
snd.onclick=()=>{v.muted=false;v.controls=true;snd.hidden=true;v.play().catch(()=>{})};
$('#rnext').onclick=()=>step(1);$('#rprev').onclick=()=>step(-1);
$('#rsend').onclick=()=>sendPage(A[cur]);
/* grid */
const grid=$('#cgrid');
grid.addEventListener('click',e=>{const b=e.target.closest('[data-play],[data-send],[data-file]');if(!b)return;
  if(b.dataset.play){play(+b.dataset.play,true);$('.reel').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})}
  else if(b.dataset.send)sendPage(A[+b.dataset.send]);
  else sendVideo(A[+b.dataset.file],b)});
document.querySelector('.filt').addEventListener('click',e=>{const b=e.target.closest('button[data-f]');if(!b)return;const f=b.dataset.f;
  document.querySelectorAll('.filt button').forEach(x=>x.setAttribute('aria-pressed',x===b));
  grid.querySelectorAll('li').forEach(li=>li.hidden=!(f==='all'||(f==='best'?li.classList.contains('best'):li.dataset.era===f)))});
/* start: an old link to a version (#08-warm-cave) plays that film; otherwise the reel from the first trailer */
const h=location.hash.slice(1),j=A.findIndex(x=>x.slug===h&&x.film);
if(j>=0)play(j,false);else{const k=A.findIndex(x=>x.slug===h);if(k>=0){location.replace(`v/${A[k].slug}/`);return}play(REEL[0],false)}
})();
