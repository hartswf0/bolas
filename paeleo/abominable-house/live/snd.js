// node snd.js deeds/x.js A V  -> proof/<nn>/snd_A_V.wav + snd_A_V.png (spectrogram + loudness, contact marked)
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');const {execSync}=require('child_process');
const [file,A,V]=process.argv.slice(2);const nn=path.basename(file).slice(0,2);const out=`/home/claude/ah/proof/${nn}`;fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch();const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file:///home/claude/ah/view.html?m='+path.resolve(file));await p.waitForFunction(()=>window.READY);
const r=await p.evaluate(async([A,V])=>{if(!LAST.sound)return{err:'no sound()'};const ac=new OfflineAudioContext(2,48000*6,48000);LAST.sound(ac,ac.destination,0,A,V,K);const buf=await ac.startRendering();
 const L=buf.getChannelData(0),R=buf.getChannelData(1);const toB=a=>{const i=new Int16Array(a.length);let m=0;for(const x of a)m=Math.max(m,Math.abs(x));for(let k=0;k<a.length;k++)i[k]=Math.max(-32767,Math.min(32767,a[k]*32767));return[btoa(String.fromCharCode(...new Uint8Array(i.buffer).slice(0,0)))||'',m]};
 let peak=0;const out=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){peak=Math.max(peak,Math.abs(L[k]),Math.abs(R[k]));out[2*k]=Math.max(-32767,Math.min(32767,L[k]*32767));out[2*k+1]=Math.max(-32767,Math.min(32767,R[k]*32767))}
 let s='';const u8=new Uint8Array(out.buffer);for(let i=0;i<u8.length;i+=8192)s+=String.fromCharCode.apply(null,u8.subarray(i,i+8192));return{b64:btoa(s),peak,contact:LAST.contact}},[A,V]);
if(r.err){console.log(r.err,errs);await b.close();return}
const raw=Buffer.from(r.b64,'base64');const hdr=Buffer.alloc(44);hdr.write('RIFF',0);hdr.writeUInt32LE(36+raw.length,4);hdr.write('WAVE',8);hdr.write('fmt ',12);hdr.writeUInt32LE(16,16);hdr.writeUInt16LE(1,20);hdr.writeUInt16LE(2,22);hdr.writeUInt32LE(48000,24);hdr.writeUInt32LE(48000*4,28);hdr.writeUInt16LE(4,32);hdr.writeUInt16LE(16,34);hdr.write('data',36);hdr.writeUInt32LE(raw.length,40);
const wav=`${out}/snd_${A}_${V}.wav`;fs.writeFileSync(wav,Buffer.concat([hdr,raw]));
execSync(`python3 /home/claude/ah/spec.py ${wav} ${r.contact}`);console.log('wrote',wav,'and .png  peak',r.peak.toFixed(3),'(keep peak 0.3-0.9; clipping above 1)','errors',JSON.stringify(errs));await b.close()})();
