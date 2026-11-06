/* ALLWAYS light table. Selection and comparison are local; media is never edited. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const time = n => { n = Math.max(0, Number(n) || 0); return Math.floor(n/60)+':'+String(Math.floor(n%60)).padStart(2,'0'); };
  const exact = n => (Number(n) || 0).toFixed(2)+' s';
  const link = (url, name) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(name)} ↗</a>`;
  let films = [], current, view = 'watch', visible = 24, currentShot = -1, pair = [], pairRunning = false, pairFrame = 0;
  const player = $('player'), va = $('video-a'), vb = $('video-b');
  const notify = text => { $('live-status').textContent = text; };
  const peersOf = f => films.filter(x => x.group === f.group);
  const scope = f => f.scope || 'Review scope is recorded in the case study.';
  const relation = f => f.group.startsWith('work:') ? 'B-ROLL OF CIVILIZATION / SAME WORK' : f.group.startsWith('operator:') ? 'SCION '+String(f.operator).padStart(3,'0')+' / SAME OPERATOR' : 'STUDIES & COLLECTIONS';
  function groupName(f) {
    if (f.group.startsWith('operator:')) {
      const a = films.find(x => x.maker==='Argon' && x.group===f.group);
      return a?.title || 'SCION '+String(f.operator).padStart(3,'0');
    }
    return f.group.startsWith('work:') ? f.title : f.title;
  }
  function setView(next, update=true) {
    if (next !== 'compare') pausePair();
    if (next !== 'watch') player.pause();
    view = next;
    ['watch','compare','atlas'].forEach(v => { $(v+'-view').hidden = v !== view; });
    document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view===view)));
    if (view==='atlas') renderAtlas();
    if (view==='compare') renderCompare();
    if (update) saveHash();
  }
  function saveHash() {
    if (!current) return;
    const params = new URLSearchParams({film:current.id,view});
    history.replaceState(null,'','#'+params);
  }
  function selectFilm(id, nextView='watch', update=true) {
    const f = films.find(x=>x.id===id);
    if (!f) return;
    pausePair(); player.pause(); current=f; currentShot=-1;
    $('selection-context').textContent=relation(f);
    $('selection-title').textContent=groupName(f);
    $('peers').innerHTML=peersOf(f).map(p=>`<button type="button" class="peer" data-film="${esc(p.id)}" aria-pressed="${p.id===f.id}"><img src="${esc(p.poster)}" alt=""><span><small>${esc(p.maker)} / ${time(p.duration)}</small><strong>${esc(p.title)}</strong></span></button>`).join('');
    $('peers').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>selectFilm(b.dataset.film,view==='atlas'?'watch':view)));
    player.poster=f.poster; player.src=f.video; player.load();
    $('media-error').hidden=true;
    $('film-maker').textContent=f.maker+' / '+f.version+' / '+exact(f.duration);
    $('film-title').textContent=f.title;
    $('film-description').textContent=f.description;
    $('film-verdict').textContent=f.verdict;
    $('film-scope').textContent=scope(f);
    $('direct-video').href=f.video;
    $('case-link').href=f.case;
    $('prompt-link').href='https://hartswf0.github.io/bolas/paeleo/allways/operator.html#s'+f.operator;
    $('records-content').innerHTML=f.records.map(r=>link(r.url,r.name)).join('');
    renderReview(f); renderCuts(f); setView(nextView,false);
    if (update) saveHash();
  }
  function renderReview(f) {
    $('review-details').open=false;
    let html='';
    if (f.critic) {
      const c=f.critic;
      html+=`<div class="critic-block"><b>Published round 1 / ${esc(c.v1_verdict)}</b>${(c.v1_defect_timecodes||[]).map(x=>`<p>${esc(x)}</p>`).join('')}</div>`;
      for (const [label,key] of [['Largest gap','largest_gap'],['Repair recorded','falsifiable_repair'],['Strength to preserve','strength_to_preserve']]) {
        if(c[key]) html+=`<div class="critic-block"><b>${label}</b><p>${esc(c[key])}</p></div>`;
      }
      html+=`<p class="scope">Published round 2: ${esc(c.v2_verdict)}. ${esc(scope(f))}</p>`;
    } else if(f.criticText) html=`<pre>${esc(f.criticText)}</pre>`;
    if(f.criticLinks?.length) html+=`<div class="record-links">${f.criticLinks.map(r=>link(r.url,r.name)).join('')}</div>`;
    $('review-content').innerHTML=html || `<p>${esc(scope(f))}</p>${link(f.case,'Read the actual report')}`;
  }
  function renderCuts(f) {
    const shots=f.shots||[], d=f.duration||1;
    $('cut-count').textContent=shots.length ? shots.length+' published intervals · gaps remain unannotated' : 'No cut timings imported · records remain available';
    $('mid-time').textContent=time(d/2); $('end-time').textContent=time(d);
    $('scrub').max=d; $('scrub').value=0;
    $('cut-track').innerHTML=shots.map((s,i)=>`<button type="button" aria-label="Interval ${i+1}, ${exact(s.start)} to ${exact(s.end)}: ${esc(s.title)}" data-shot="${i}" style="left:${100*s.start/d}%;width:${100*Math.min(s.end-s.start,d-s.start)/d}%">${s.end-s.start>d/32?i+1:''}</button>`).join('');
    $('shot-cards').innerHTML=shots.map((s,i)=>`<button type="button" class="shot-card" data-shot="${i}" aria-label="Inspect interval ${i+1}: ${esc(s.title)}, ${exact(s.start)} to ${exact(s.end)}">${s.thumb?`<img src="${esc(s.thumb)}" loading="lazy" alt="">`:`<div class="shot-placeholder" aria-hidden="true">${String(i+1).padStart(2,'0')}</div>`}<span>${String(i+1).padStart(2,'0')} / ${time(s.start)}–${time(s.end)}</span><small>${esc(s.action||s.title)}</small></button>`).join('');
    document.querySelectorAll('[data-shot]').forEach(b=>b.addEventListener('click',()=>inspectShot(Number(b.dataset.shot),true)));
    if(shots.length) inspectShot(0,false);
    else { $('cut-detail').classList.add('no-image'); $('cut-detail').innerHTML=`<div class="empty-visual">The published film is playable above. This catalog has no normalized timing record for it yet.<br>${link(f.case,'Inspect its full source and edit records')}</div>`; }
    updateTime(0);
  }
  function inspectShot(i, seek) {
    const s=current.shots[i]; if(!s) return;
    currentShot=i;
    if(seek) seekVideo(player,s.start);
    document.querySelectorAll('[data-shot]').forEach(b=>{const yes=Number(b.dataset.shot)===i;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',String(yes));});
    $('cut-detail').classList.toggle('no-image',!s.thumb);
    $('cut-detail').innerHTML=`${s.thumb?`<img src="${esc(s.thumb)}" alt="Published frame for interval ${i+1}">`:''}<div><p class="eyebrow">Interval ${i+1} / ${exact(s.start)}–${exact(s.end)} / ${esc(s.kind)}</p><h4>${esc(s.title)}</h4><p>${esc(s.why||s.action||'See source record for the editorial reason.')}</p>${s.source?link(s.source,/\.mp4(?:$|\?)/i.test(s.source)?'Open source clip':'Open source record'):''}${s.sourceIn!=null?`<p class="scope">Source clip interval: ${exact(s.sourceIn)}–${exact(s.sourceOut)}. Output timings appear above.</p>`:''}</div>`;
    if(seek) notify('Interval '+(i+1)+' selected at '+exact(s.start));
  }
  function updateTime(t) {
    $('media-position').textContent=time(t)+' / '+time(current.duration);
    $('scrub-value').textContent=exact(t); $('scrub').value=t;
    const i=current.shots.findIndex(s=>t>=s.start && t<s.end);
    if(i>=0 && i!==currentShot) inspectShot(i,false);
    if(i<0 && current.shots.length && currentShot!==-2){
      currentShot=-2;
      document.querySelectorAll('[data-shot]').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-pressed','false');});
      $('cut-detail').classList.add('no-image');
      $('cut-detail').innerHTML='<div><p class="eyebrow">Unannotated interval</p><p>No imported cut record covers this position. Watch the film or follow the full edit record.</p></div>';
    }
  }
  function seekVideo(v,t) {
    const seek=()=>{try{v.currentTime=Math.max(0,Math.min(t,Number.isFinite(v.duration)?v.duration:t));}catch{}};
    if(v.readyState>=1)seek();else{v.addEventListener('loadedmetadata',seek,{once:true});v.preload='metadata';v.load();}
  }
  function renderCompare(reset=false) {
    const peers=peersOf(current);
    const candidates=[...peers,...films.filter(f=>!peers.includes(f))];
    if(reset || !pair.length || !pair.some(f=>f.group===current.group)) pair=[current,peers.find(f=>f.id!==current.id)||null];
    ['a','b'].forEach((slot,i)=>{
      const select=$('select-'+slot);
      select.innerHTML=(i===1?'<option value="">Select a second film…</option>':'')+candidates.map(f=>`<option value="${esc(f.id)}">${esc(f.maker+' / '+f.title+' / '+time(f.duration))}</option>`).join('');
      select.value=pair[i]?.id||'';
      loadSlot(slot,pair[i]);
    });
    $('pair-scrub').value=0; $('pair-value').textContent='0:00'; updateRelation();audition();
  }
  function loadSlot(slot,f) {
    const v=$('video-'+slot);v.pause();v.removeAttribute('src');v.removeAttribute('poster');v.load();
    if(f){v.poster=f.poster;v.src=f.video;v.load();}
    $('meta-'+slot).innerHTML=f?`<p><b>${esc(f.maker)} / ${esc(f.version)} / ${exact(f.duration)}</b></p><p class="verdict">${esc(f.verdict)}</p><p class="scope">${esc(scope(f))}</p>${link(f.case,'Full case study')}`:'<p>Select a second film for comparison.</p>';
    $('compare-errors').hidden=true;
  }
  function updateRelation() {
    const [a,b]=pair;
    $('compare-relation').textContent=!b?'Choose another reading, or any film from the collection.':a.id===b.id?'The same published file is selected twice.':a.group===b.group?'Same proposition / separate editing decisions.':'Different propositions / exploratory juxtaposition.';
    $('play-pair').disabled=!a||!b;
    $('pair-scrub').disabled=!a||!b;
    $('pair-evidence').innerHTML=pair.map((f,i)=>f?`<div><h4>${i?'B':'A'} / What is recorded</h4><p>${esc(f.description)}</p><p class="scope">${f.shots.length?f.shots.length+' output intervals imported.':'No cut timings imported.'} ${esc(f.boundary||'Refer to the source and edit records for the boundaries of this adaptation.')}</p>${link(f.case,'Follow the evidence')}</div>`:'').join('');
  }
  function pausePair(){pairRunning=false;cancelAnimationFrame(pairFrame);va.pause();vb.pause();$('play-pair').textContent='Play both';}
  function audition(){va.muted=$('audition').value!=='a';vb.muted=$('audition').value!=='b';}
  function pairMaximum(){return Math.max(...pair.filter(Boolean).map(f=>f.duration||0),1);}
  function seekPair(value){
    pausePair();const relative=$('compare-clock').value==='progress',max=pairMaximum();
    [va,vb].forEach((v,i)=>{if(pair[i])seekVideo(v,value/1000*(relative?pair[i].duration:max));});
    $('pair-value').textContent=relative?(value/10).toFixed(1)+'%':time(value/1000*max);
  }
  function tickPair(){
    if(!pairRunning)return;
    const relative=$('compare-clock').value==='progress';
    const v=va.ended && !vb.ended?vb:va;
    const f=v===va?pair[0]:pair[1];
    const progress=relative?v.currentTime/f.duration:v.currentTime/pairMaximum();
    $('pair-scrub').value=Math.round(progress*1000);
    $('pair-value').textContent=relative?(progress*100).toFixed(1)+'%':time(v.currentTime);
    if(va.ended&&vb.ended){pausePair();return;}
    pairFrame=requestAnimationFrame(tickPair);
  }
  function renderAtlas(){
    const q=$('search').value.toLowerCase().trim(),maker=$('maker-filter').value,category=$('category-filter').value,operator=$('operator-filter').value;
    const found=films.filter(f=>(!maker||f.maker===maker)&&(!category||f.category===category)&&(!operator||f.operator===Number(operator))&&(!q||[f.title,f.description,f.maker,String(f.operator),String(f.operator).padStart(3,'0'),...f.shots.map(s=>s.title)].join(' ').toLowerCase().includes(q)));
    $('results').textContent=found.length+' matching entries / showing '+Math.min(found.length,visible);
    $('no-results').hidden=found.length>0;
    $('show-more').hidden=found.length<=visible;
    $('film-grid').innerHTML=found.slice(0,visible).map(f=>`<button type="button" class="film-card" data-card="${esc(f.id)}" aria-pressed="${f.id===current.id}"><img src="${esc(f.poster)}" loading="lazy" alt="Published preview: ${esc(f.title)}"><span class="card-heading"><span>${esc(f.maker)} / ${String(f.operator).padStart(3,'0')}</span><span>${time(f.duration)}</span></span><strong>${esc(f.title)}</strong><span class="card-status">${esc(f.verdict)}</span></button>`).join('');
    $('film-grid').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{selectFilm(b.dataset.card);$('main').scrollIntoView({block:'start',behavior:'instant'});}));
  }
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  player.addEventListener('timeupdate',()=>current&&updateTime(player.currentTime));
  player.addEventListener('error',()=>{if(!current)return;$('media-error').hidden=false;$('media-error').textContent='The media could not load. Use Open MP4 or the full case study to check the published file.';});
  $('scrub').addEventListener('input',e=>{const t=Number(e.target.value);seekVideo(player,t);updateTime(t);});
  ['search','maker-filter','category-filter','operator-filter'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>{visible=24;renderAtlas();}));
  $('clear-filters').addEventListener('click',()=>{['search','maker-filter','category-filter','operator-filter'].forEach(id=>$(id).value='');visible=24;renderAtlas();});
  $('show-more').addEventListener('click',()=>{visible+=24;renderAtlas();});
  ['a','b'].forEach((slot,i)=>{
    $('select-'+slot).addEventListener('change',e=>{pausePair();pair[i]=films.find(f=>f.id===e.target.value)||null;loadSlot(slot,pair[i]);updateRelation();audition();});
    $('video-'+slot).addEventListener('error',()=>{if(!pair[i])return;$('compare-errors').hidden=false;$('compare-errors').textContent='Film '+slot.toUpperCase()+' could not load. Its full case study and direct media link remain available.';pausePair();});
  });
  $('reset-compare').addEventListener('click',()=>{pausePair();renderCompare(true);notify('Comparison reset to the selected proposition.');});
  $('audition').addEventListener('change',audition);
  $('compare-clock').addEventListener('change',()=>{seekPair(Number($('pair-scrub').value));$('alignment-note').textContent=$('compare-clock').value==='progress'?'Shared seeking aligns percentage of each film. Playback runs at each film’s original speed; cuts and events are not synchronized.':'Shared seeking aligns elapsed time. Playback runs at original speed; cuts and historical events are not synchronized.';});
  $('pair-scrub').addEventListener('input',e=>seekPair(Number(e.target.value)));
  $('pause-pair').addEventListener('click',pausePair);
  $('play-pair').addEventListener('click',async()=>{
    if(pairRunning){pausePair();return;}if(!pair[0]||!pair[1])return;
    audition();const r=await Promise.allSettled([va.play(),vb.play()]);
    if(r.some(x=>x.status==='rejected')){pausePair();notify('Use each film’s native play control to start playback in this browser.');return;}
    pairRunning=true;$('play-pair').textContent='Pause both';tickPair();
  });
  window.addEventListener('hashchange',()=>{const p=new URLSearchParams(location.hash.slice(1));if(films.some(f=>f.id===p.get('film')))selectFilm(p.get('film'),['atlas','watch','compare'].includes(p.get('view'))?p.get('view'):'watch',false);});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){player.pause();pausePair();}});
  document.addEventListener('error',e=>{if(e.target.tagName==='IMG'){e.target.alt='Published frame unavailable';e.target.style.objectFit='contain';}},true);
  fetch('catalog.json').then(r=>{if(!r.ok)throw new Error('Catalog returned '+r.status);return r.json();}).then(data=>{
    films=data.films;
    $('catalog-state').textContent=films.length+' entries / 4 makers / '+films.filter(f=>f.preparatory).length+' unfinished source study';
    const ops=[...new Set(films.map(f=>f.operator))].sort((a,b)=>a-b);
    $('operator-filter').insertAdjacentHTML('beforeend',ops.map(n=>`<option value="${n}">${String(n).padStart(3,'0')}</option>`).join(''));
    $('desk').hidden=false;
    const params=new URLSearchParams(location.hash.slice(1));
    const f=films.find(f=>f.id===params.get('film'))||films.find(f=>f.id==='sol-055')||films[0];
    selectFilm(f.id,['atlas','watch','compare'].includes(params.get('view'))?params.get('view'):'watch');
  }).catch(error=>{$('load-error').hidden=false;$('load-error').innerHTML='The collection could not load. '+link('../#runs','Open all published runs');$('catalog-state').textContent=error.message;});
})();
