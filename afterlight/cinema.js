(()=>{
const P=window.PROG,M='../media/afterlight/',$=id=>document.getElementById(id);
const cin=$('cin'),v=$('v'),card=$('card'),segs=$('segs'),pp=$('pp'),snd=$('snd');
let cur=-1,sound=false,hideT=0,cardT=0,startAt=0;
const setState=s=>cin.dataset.state=s;
// segments, one per film, sized by length
const sec=r=>r.split(':').reduce((m,s)=>m*60+ +s,0);
P.forEach((x,k)=>{const b=document.createElement('button');b.type='button';b.style.flexGrow=sec(x.rt);b.setAttribute('aria-label',`Play ${x.title}`);b.innerHTML='<i></i>';b.onclick=()=>load(k);segs.appendChild(b)});
function showCard(x,k){$('cn').textContent=`${k+1} / ${P.length} · ${x.title}`;$('ct').textContent=x.thesis;$('cs').textContent=x.sub;card.classList.add('on');clearTimeout(cardT)}
function hideCardSoon(ms){clearTimeout(cardT);cardT=setTimeout(()=>card.classList.remove('on'),ms)}
function playNow(){
  v.muted=!sound;
  return v.play().then(()=>{snd.hidden=!v.muted}).catch(()=>{v.muted=true;snd.hidden=false;return v.play().catch(()=>{setPP(false)})});
}
function load(k){
  if(k<0||k>=P.length)return;
  cur=k;const x=P[k];setState('gap');showCard(x,k);
  $('nt').textContent=x.title;$('ns').textContent=`${k+1} of ${P.length} · ${x.rt}`;$('how').href=`v/${x.slug}/`;
  [...segs.children].forEach((b,j)=>{b.classList.toggle('on',j===k);b.classList.toggle('done',j<k);b.firstChild.style.width=j<k?'100%':'0'});
  history.replaceState(null,'','#'+x.slug);
  setTimeout(()=>{if(cur!==k)return;v.loop=false;v.src=M+x.id+'.mp4';v.poster=M+'thumbs/'+x.id+'.jpg';setState('play');playNow();hideCardSoon(5200)},900);
  // warm the next file
  const n=P[k+1];if(n){const l=document.createElement('link');l.rel='prefetch';l.href=M+n.id+'.mp4';document.head.appendChild(l)}
}
v.addEventListener('ended',()=>{if(cin.dataset.state==='intro')return;if(cur>=P.length-1){setState('end');history.replaceState(null,'','#end');return}load(cur+1)});
v.addEventListener('timeupdate',()=>{if(cur<0||cin.dataset.state==='intro')return;const b=segs.children[cur];b&&(b.firstChild.style.width=(v.currentTime/(v.duration||1)*100)+'%')});
v.addEventListener('play',()=>setPP(true));v.addEventListener('pause',()=>setPP(false));
v.addEventListener('volumechange',()=>{if(!v.muted){sound=true;snd.hidden=true}});
function setPP(on){pp.firstChild.className='ic '+(on?'pause':'playi');pp.setAttribute('aria-label',on?'Pause':'Play')}
$('start').onclick=()=>{sound=true;load(startAt)};
$('again').onclick=()=>{sound=true;load(0)};
$('prev').onclick=()=>{if(v.currentTime>4&&cur>=0){v.currentTime=0;return}load(Math.max(0,cur-1))};
$('nx').onclick=()=>{cur<P.length-1?load(cur+1):(setState('end'))};
pp.onclick=()=>{v.paused?playNow():v.pause();poke()};
snd.onclick=()=>{sound=true;v.muted=false;snd.hidden=true;v.play().catch(()=>{})};
// controls appear on touch or mouse movement and fade while playing
function poke(){if(cin.dataset.state==='intro'||cin.dataset.state==='end')return;cin.classList.add('show');clearTimeout(hideT);hideT=setTimeout(()=>{if(!v.paused)cin.classList.remove('show')},3000)}
cin.addEventListener('pointermove',e=>{if(e.pointerType==='mouse')poke()});
cin.addEventListener('pointerdown',e=>{if(e.target.closest('a,button'))return poke();if(cin.classList.contains('show')&&e.pointerType!=='mouse'){cin.classList.remove('show');return}poke()});
addEventListener('keydown',e=>{if(cin.dataset.state==='intro'){if(e.key===' '||e.key==='Enter'){e.preventDefault();$('start').click()}return}
  if(e.key===' '){e.preventDefault();pp.click()}else if(e.key==='ArrowRight')$('nx').click();else if(e.key==='ArrowLeft')$('prev').click();else if(e.key==='Escape')cin.classList.remove('show');poke()});
// #slug: a film in the program starts there; any other version goes to its own page
const h=location.hash.slice(1);
if(h){const k=P.findIndex(x=>x.slug===h);if(k>=0)startAt=k;else if(/^\d\d-/.test(h))location.replace('v/'+h+'/')}
})();
