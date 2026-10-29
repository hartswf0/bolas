(()=>{
const C=[...document.querySelectorAll('.chap')],rail=[...document.querySelectorAll('.rail a')],prev=document.getElementById('prev'),next=document.getElementById('next'),where=document.getElementById('where');
let cur=-1;
function name(i){const c=C[i];return (c.querySelector('.kn').textContent+' · '+c.querySelector('h2').textContent)}
function show(i,user){
  if(i<0||i>=C.length)return;
  C.forEach((c,j)=>{if(j!==i){c.hidden=true;const v=c.querySelector('video');v.pause()}});
  const c=C[i],v=c.querySelector('video'),snd=c.querySelector('.snd'),af=c.querySelector('.after');cur=i;c.hidden=false;af.hidden=true;
  if(!v.src)v.src=v.dataset.src;
  v.controls=true;
  if(user){v.muted=false;snd.hidden=true;v.play().catch(()=>{})}
  else{v.muted=true;v.play().then(()=>{snd.hidden=false;v.controls=false}).catch(()=>{snd.hidden=true})}
  snd.onclick=()=>{v.muted=false;v.controls=true;snd.hidden=true;v.currentTime=0;v.play().catch(()=>{})};
  v.onended=()=>{if(i>=C.length-1)return;af.innerHTML=`<p>Next chapter</p><button type="button">${name(i+1)}</button>`;af.hidden=false;af.querySelector('button').onclick=()=>show(i+1,true)};
  rail.forEach((a,j)=>a.setAttribute('aria-current',j===i));
  const ra=rail[i],rl=ra&&ra.parentElement;if(rl)rl.scrollLeft=Math.max(0,ra.offsetLeft-rl.clientWidth/2+ra.offsetWidth/2);
  prev.disabled=i===0;next.disabled=i===C.length-1;
  next.textContent=i<C.length-1?'Next · '+C[i+1].querySelector('h2').textContent:'End';
  where.textContent=`${i+1} / ${C.length}`;
  const t=c.querySelector('.ctext');t.scrollTop=0;
  if(user&&innerWidth<1000)scrollTo({top:0,behavior:'auto'});
  history.replaceState(null,'','#'+c.id);
}
prev.onclick=()=>show(cur-1,true);next.onclick=()=>show(cur+1,true);
rail.forEach((a,j)=>a.addEventListener('click',e=>{e.preventDefault();show(j,true)}));
addEventListener('keydown',e=>{if(e.target.closest('input,textarea,video'))return;if(e.key==='ArrowRight'){show(cur+1,true);e.preventDefault()}else if(e.key==='ArrowLeft'){show(cur-1,true);e.preventDefault()}});
// old links (#08-warm-cave) go to that version's page
const h=location.hash.slice(1);const k=C.findIndex(c=>c.id===h);
if(k<0&&/^\d\d-/.test(h)){location.replace('v/'+h+'/');return}
history.scrollRestoration='manual';show(k<0?0:k,false);scrollTo(0,0);setTimeout(()=>scrollTo(0,0),60);
})();
