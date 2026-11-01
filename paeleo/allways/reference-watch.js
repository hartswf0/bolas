/* Reference players are separate from the prompt pack's historical research claims. */
(() => {
 'use strict';
 const root=document.getElementById('reference-watch');if(!root)return;
 const labels={full_film:'Full film',trailer:'Trailer',excerpt:'Excerpt / preview',demo:'Project documentation',interactive:'Original interactive work',related:'Related context · not the reference'};
 let records=null,activeId=Number(location.hash.replace(/^#s/,''))||55;
 const make=(tag,className,text)=>{const e=document.createElement(tag);if(className)e.className=className;if(text!==undefined)e.textContent=text;return e};
 const safe=value=>{try{const u=new URL(value);return u.protocol==='https:'?u.href:null}catch{return null}};
 function link(text,url){const a=make('a','',text);a.href=safe(url)||'#';a.target='_blank';a.rel='noopener noreferrer';return a}
 function render(){
  if(!records)return;const record=records.operators.find(x=>x.id===activeId);root.replaceChildren();
  const heading=make('div','reference-heading');heading.append(make('h3','','Watch the reference'),make('span','reference-eyebrow','ORIGINAL WORK / SCION '+String(activeId).padStart(3,'0')));root.append(heading);
  if(!record){root.append(make('p','reference-note','No reference record is available for this operator.'));return}
  const available=record.media.filter(x=>x.playable!==false);const exact=available.filter(x=>x.kind!=='related');
  root.append(make('p','reference-requested',record.reference));
  const body=make('div','reference-body'),screen=make('div','reference-screen'),info=make('div','reference-info');body.append(screen,info);root.append(body);
  const choose=media=>{
   screen.replaceChildren();info.replaceChildren();screen.classList.toggle('reference-interactive',media.kind==='interactive');
   const badge=make('span','reference-kind'+(media.kind==='related'?' reference-related':''),labels[media.kind]);info.append(badge,make('h4','reference-media-title',media.title));
   if(media.kind==='related')info.append(make('p','reference-note','This is supporting context. An exact public player for the named reference was not verified.'));
   if(media.provider==='html5'){
    const video=make('video');video.controls=true;video.playsInline=true;video.preload='none';video.src=safe(media.embed_url);video.setAttribute('aria-label',media.title);video.append(link('Open the source video',media.watch_url));screen.append(video);
   }else{
    let url=new URL(media.embed_url);
    if(media.provider==='vimeo')url.searchParams.set('dnt','1');
    if(media.provider==='youtube')url.hostname='www.youtube-nocookie.com';
    const load=()=>{const frame=make('iframe');frame.src=safe(url.href);frame.title=media.title+' — '+labels[media.kind];frame.loading='lazy';frame.allow='fullscreen; picture-in-picture; encrypted-media';frame.allowFullscreen=true;frame.referrerPolicy='strict-origin-when-cross-origin';screen.replaceChildren(frame)};
    if(media.kind==='interactive'){
     const launch=make('button','reference-launch','Load the original interactive work');launch.type='button';launch.onclick=load;screen.append(make('p','',media.title),launch,make('small','','Opens the original project here. Browser compatibility varies.'));
    }else load();
   }
   const links=make('div','reference-links');links.append(link(media.kind==='interactive'?'Open original project ↗':'Open video on its host ↗',media.watch_url));if(media.source_url!==media.watch_url)links.append(link('Creator / institution source ↗',media.source_url));info.append(links);
  };
  if(available.length){
   if(available.length>1){const wrap=make('label','reference-choice','Choose a film or view');const select=make('select');select.setAttribute('aria-label','Choose reference film or view');available.forEach((m,i)=>{const option=make('option','',`${labels[m.kind]} · ${m.title}`);option.value=String(i);select.append(option)});select.onchange=()=>choose(available[Number(select.value)]);wrap.append(select);root.insertBefore(wrap,body)}
   choose(exact[0]||available[0]);
  }else{
   screen.classList.add('reference-unavailable');screen.append(make('p','reference-empty-title',record.status==='unresolved'?'Reference title unresolved':'Watch on the official platform'),make('p','',record.status==='unresolved'?'A matching film has not been established.':'An unrestricted in-page player is not available.'));
   info.append(make('span','reference-kind reference-related',record.status==='unresolved'?'Unresolved identity':'External access'));
   if(record.full_watch_url)info.append(link('Open official viewing page ↗',record.full_watch_url));
   const sources=make('div','reference-links');record.official_sources.slice(0,2).forEach(x=>sources.append(link(x.title+' ↗',x.url)));info.append(sources);
  }
  root.append(make('p','reference-note reference-availability',record.display_note||record.note));
  if(record.full_watch_url&&available.length)root.append(link('Official film / project access ↗',record.full_watch_url));
  const evidence=make('details','reference-evidence'),summary=make('summary','','Availability and source record');evidence.append(summary,make('p','reference-note','Checked '+records.checked+'. Player/source availability was inspected; this does not claim a complete-film screening or listening review.'));
  record.media.forEach(m=>{const p=make('p','reference-note');p.append(make('strong','',m.title+' — '),document.createTextNode(m.playable===false?'Source currently unavailable. '+m.verification:m.verification));evidence.append(p)});
  if(record.verification_note)evidence.append(make('p','reference-note',record.verification_note));evidence.append(link('Complete reference watch catalog ↗','https://hartswf0.github.io/bolas/paeleo/allways/reference-videos.json'));root.append(evidence);
 }
 window.AllwaysReferences={show(operator){activeId=operator.id;render()}};
 fetch('reference-videos.json').then(r=>{if(!r.ok)throw Error('reference catalog '+r.status);return r.json()}).then(d=>{records=d;render()}).catch(()=>{root.replaceChildren(make('h3','','Watch the reference'),make('p','reference-note','The video catalog could not load. The original source links remain available in the Evidence tab.'))});
})();
