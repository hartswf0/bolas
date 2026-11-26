// The full flow: one fixed order through every page of the Abominable House. Each page loads this file; it adds a small control at the bottom left (previous, the list, next). A page hosted elsewhere can set window.FLOW_MAP (file name to URL) and window.FLOW_HERE (its own file name).
(function(){
const FLOW=[
 ['mentalfilm.html','The Mental Film','The frame. What does an index of twelve crimes leave open?'],
 ['rerereorder.html','The List Has No Names','The case in ten lines. Why can nobody say who did what?'],
 ['abom.html','The Story, Drawn in Code','The first film. What does the story itself say happened?'],
 ['player.html','The Deed Bank','Each of the twelve deeds, by every pair. What does one crime look like?'],
 ['film.html','The Film Bank','Any of the 8,916,100,448,256 films. What does one whole story look like?'],
 ['guide.html','Film Bank Guide','Waldemar on each part of the panel. How is a film rated?'],
 ['numbers.html','Twelve to the Twelfth','The count and the rules. How many stories are left?'],
 ['policies.html','The Policies','The four insurance policies. What does the insurer pay in each story?'],
 ['reorder.html','Re:Order in Crime','Nine episodes. What does each part of the program do, and leave out?'],
 ['rereorder.html','Six Readings','Six theories staged on the deed films. Does any of them pick one story?'],
 ['array.html','The Array','The workstation. Compare deeds, tenants and films side by side.']];
window.FLOW=FLOW;const M=window.FLOW_MAP||{},url=f=>M[f]||f,here=window.FLOW_HERE||(location.pathname.split('/').pop()||'index.html'),i=FLOW.findIndex(s=>s[0]===here);
const css='#flw{position:fixed;left:6px;bottom:6px;z-index:9999;font:600 11px "JetBrains Mono",ui-monospace,Menlo,monospace;display:flex;gap:1px}#flw a,#flw button{background:#1d1812;color:#f4eedd;border:1px solid #6f6456;padding:6px 8px;text-decoration:none;cursor:pointer;font:inherit;letter-spacing:.04em}#flw button{background:#ffdc00;color:#1d1812;border-color:#1d1812}'+
 '#flp{position:fixed;left:6px;bottom:38px;z-index:9999;width:min(420px,calc(100vw - 12px));max-height:70vh;overflow:auto;background:#faf6ee;color:#1d1812;border:1.5px solid #1d1812;padding:8px 10px;font:13px/1.35 Georgia,serif;display:none}#flp.on{display:block}#flp h3{font:800 15px ui-monospace,Menlo,monospace;margin:0 0 6px;letter-spacing:.04em}#flp a{display:grid;grid-template-columns:1.8em 1fr;gap:4px;padding:5px 2px;border-top:1px solid #d3c8b4;color:inherit;text-decoration:none}#flp a b{font:600 12px ui-monospace,Menlo,monospace}#flp .pn{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}#flp .pn a{display:block;background:#1d1812;color:#f4eedd;border:0;padding:8px 10px;font:600 12px ui-monospace,Menlo,monospace}#flh{margin-top:8px;font:600 11px ui-monospace,Menlo,monospace;background:none;border:1px solid #6f6456;padding:5px 8px;cursor:pointer;color:#1d1812}#flp a[aria-current="page"]{background:#ffdc00}#flp a span{display:block;color:#6f6456;font-size:12px}';
const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
const bar=document.createElement('nav');bar.id='flw';bar.setAttribute('aria-label','Full flow');const pan=document.createElement('div');pan.id='flp';
const prev=i>0?FLOW[i-1]:null,next=i>=0&&i<FLOW.length-1?FLOW[i+1]:i<0?FLOW[0]:null;
bar.innerHTML='<button type="button" aria-expanded="false">FLOW '+(i>=0?(i+1)+'/'+FLOW.length:'')+'</button>';
pan.innerHTML='<h3>THE ABOMINABLE HOUSE · FULL FLOW</h3><div class="pn">'+(prev?'<a href="'+url(prev[0])+'">&lsaquo; BACK: '+prev[1]+'</a>':'')+(next?'<a href="'+url(next[0])+'">NEXT: '+next[1]+' &rsaquo;</a>':'')+'</div>'+FLOW.map((s,k)=>'<a href="'+url(s[0])+'"'+(k===i?' aria-current="page"':'')+'><b>'+(k+1)+'</b><div>'+s[1]+'<span>'+s[2]+'</span></div></a>').join('')+'<a href="'+url('../flow.html')+'"><b></b><div>The flow on one page</div></a><a href="'+url('../watch.html')+'"><b></b><div>Watch all four films back to back</div></a><button type="button" id="flh">HIDE THIS CONTROL</button>';
document.body.appendChild(pan);document.body.appendChild(bar);const btn=bar.querySelector('button');btn.onclick=()=>{const on=pan.classList.toggle('on');btn.setAttribute('aria-expanded',on)};pan.querySelector('#flh').onclick=()=>{bar.remove();pan.remove()};
})();
// Watch mode: when a film page is running inside watch.html, the control above is hidden, the voice is switched on, and the page tells watch.html when its last line has finished.
(function(){let P=null;try{if(window.parent!==window&&window.parent.WATCH)P=window.parent}catch(e){}if(!P)return;
 const hide=document.createElement('style');hide.textContent='#flw,#flp{display:none!important}header{display:none!important}';document.head.appendChild(hide);
 setTimeout(()=>{const v=document.getElementById('vo'),p=document.getElementById('pp');if(v&&P.WATCH.voice&&v.getAttribute('aria-pressed')!=='true')v.click();else if(p&&p.textContent.trim()==='PLAY')p.click()},700);
 let seen=0;setInterval(()=>{const p=document.getElementById('pp'),bar=document.querySelector('#prog i');if(!p||!bar)return;const w=parseFloat(bar.style.width)||0;if(p.textContent.trim()==='PAUSE')seen++;if(seen>4&&p.textContent.trim()==='PLAY'&&w>=99){seen=-1e9;P.postMessage('film:end','*')}},500)})();
