const {chromium}=require('playwright');const fs=require('fs');const mode=process.argv[2];
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file:///home/claude/title/title2.html');await p.waitForFunction(()=>window.READY);
if(mode==='test'){for(const t of process.argv.slice(3).map(Number)){await p.evaluate(t=>DRAW(t),t);await p.screenshot({path:`t_${t}.jpg`,type:'jpeg',quality:82});}}
else{fs.writeFileSync('lands.json',JSON.stringify(await p.evaluate(()=>({lands:LANDS,rise:RISE,cutn:CUTN}))));fs.mkdirSync('fr2',{recursive:true});const dur=await p.evaluate(()=>DUR);const n=Math.round(dur*30);for(let i=0;i<n;i++){await p.evaluate(t=>DRAW(t),i/30);await p.screenshot({path:`fr2/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92});}console.log('frames',n)}
await b.close()})();
