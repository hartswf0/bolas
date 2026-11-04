const {chromium}=require('playwright');const fs=require('fs');
const J=JSON.parse(fs.readFileSync('celjobs.json'));const films=process.argv.slice(2);
const N={'02':'02-reiniger','06':'06-whitney','07':'07-foldes','08':'08-sutherland','14':'14-pose2pose','41':'41-soft-body'};
const key=j=>j.map(v=>v.toFixed(5)).join('_');
(async()=>{const b=await chromium.launch();
for(const f of films){const jobs=J[f];
 const p0=await b.newPage({viewport:{width:1600,height:900}});await p0.goto('file:///home/claude/pae03/films/'+N[f]+'.html');await p0.waitForTimeout(1200);
 const bb0=await (await p0.evaluateHandle(()=>[...document.querySelectorAll('canvas')].sort((a,b)=>b.clientWidth*b.clientHeight-a.clientWidth*a.clientHeight)[0])).asElement().boundingBox();await p0.close();
 const minw=Math.min(...jobs.map(j=>j[3]));const dpr=Math.min(3,160/(minw*bb0.width));
 const p=await b.newPage({viewport:{width:1600,height:900},deviceScaleFactor:dpr});
 await p.goto('file:///home/claude/pae03/films/'+N[f]+'.html');await p.waitForTimeout(2000);
 await p.evaluate(async()=>{if(typeof window.PAE_READY==='function')await window.PAE_READY()});
 const bb=await (await p.evaluateHandle(()=>[...document.querySelectorAll('canvas')].sort((a,b)=>b.clientWidth*b.clientHeight-a.clientWidth*a.clientHeight)[0])).asElement().boundingBox();
 fs.mkdirSync('cel/'+f,{recursive:true});
 for(const j of jobs){const out=`cel/${f}/${key(j)}.jpg`;if(fs.existsSync(out))continue;
  const [t,cx,cy,w,h]=j;
  await p.evaluate(t=>window.PAE_SEEK(t),Math.min(t,31.99));
  await p.screenshot({path:out,type:'jpeg',quality:93,clip:{x:bb.x+(cx-w/2)*bb.width,y:bb.y+(cy-h/2)*bb.height,width:w*bb.width,height:h*bb.height}});}
 console.log('done',f,'dpr',dpr.toFixed(2));await p.close();}
await b.close()})().catch(e=>{console.error('ERR',e);process.exit(1)});
