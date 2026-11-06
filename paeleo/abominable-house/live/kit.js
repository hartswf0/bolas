window.DEEDS=window.DEEDS||{};function DEED(d){DEEDS[d.key]=d;window.LAST=d}
const K={W:1920,H:1080,hash(n){const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s)},cl:(a,b,x)=>Math.max(a,Math.min(b,x)),lerp:(a,b,u)=>a+(b-a)*u,
 sm(a,b,x){const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return u*u*(3-2*u)},eo(a,b,x){const u=Math.max(0,Math.min(1,(x-a)/(b-a)));return 1-Math.pow(1-u,3)},
 CAST:{R:{w:168,h:122,fill:'#d6bf96',attr:'shawl #6e3a33 top fifth'},B:{w:244,h:214,fill:'#e8d5ae',attr:'belt #2a2622 at 40%, wheat stencil'},I:{w:128,h:98,fill:'#e2cea5',attr:'ears hang down'},O:{w:80,h:184,fill:'#f0e4c8',attr:'purple wig #7a3b8f'}}};
// ---------- sound kit: everything is grains (one source: flour and cloth) ----------
K.SND=(function(){
 const H=K.hash;
 function noise(ac){if(!ac._nb){const n=ac.sampleRate*2,b=ac.createBuffer(1,n,ac.sampleRate),d=b.getChannelData(0);let s=12345;for(let i=0;i<n;i++){s=(s*16807)%2147483647;d[i]=s/1073741823.5-1}ac._nb=b}return ac._nb}
 function grain(ac,out,when,o={}){if(when<ac.currentTime-0.005)return;const bk=Math.floor(when*20);ac._gb=ac._gb||{};ac._gb[bk]=(ac._gb[bk]||0)+1;if(ac._gb[bk]>(K.SND_BUDGET||36))return;const d=Math.max(.004,o.d||.04),a=o.a??.2;
  const g=ac.createGain();g.gain.setValueAtTime(0,when);g.gain.linearRampToValueAtTime(a,when+d*(o.att??.5));g.gain.linearRampToValueAtTime(0,when+d);
  let node=g;if(ac.createStereoPanner){const p=ac.createStereoPanner();p.pan.value=Math.max(-1,Math.min(1,o.pan||0));g.connect(p);p.connect(out)}else g.connect(out);
  if(o.f){const os=ac.createOscillator();os.type=o.type||'sine';os.frequency.setValueAtTime(o.f,when);if(o.glide)os.frequency.linearRampToValueAtTime(Math.max(20,o.f*(1+o.glide)),when+d);const og=ac.createGain();og.gain.value=1-(o.noise||0);os.connect(og);og.connect(g);os.start(when);os.stop(when+d+.02)}
  if(!o.f||o.noise){const s=ac.createBufferSource();s.buffer=noise(ac);let nn=s;if(o.bp){const f=ac.createBiquadFilter();f.type='bandpass';f.frequency.value=o.bp;f.Q.value=o.q||1.5;s.connect(f);nn=f}const ng=ac.createGain();ng.gain.value=o.f?(o.noise||0):1;nn.connect(ng);ng.connect(g);s.start(when,H(when*997)*1.8,d+.02)}}
 function cloud(ac,out,t0,dur,rate,o={},env){const n=Math.round(rate*dur);for(let k=0;k<n;k++){const u=H(t0*31+k*1.37),t=t0+u*dur,e=env?env(u):1;if(e<.003)continue;
  const ps=o.pitches;const f=ps?440*Math.pow(2,(ps[Math.floor(H(k*7.1+t0)*ps.length)]-69)/12)*(1+(H(k*3.3)-.5)*.01):o.f;
  grain(ac,out,t,{...o,f,a:(o.a??.05)*e,d:lerp2(o.d||[.02,.08],H(k*5.7+t0)),pan:(H(k*9.1+t0)-.5)*2*(o.spread??.8)})}}
 function lerp2(r,u){return Array.isArray(r)?r[0]+(r[1]-r[0])*u:r}
 function thump(ac,out,when,a=1,f0=60,pan=0){for(let k=0;k<14;k++)grain(ac,out,when+k*.006,{f:f0*(1-k*.015),d:.16+k*.006,a:a*.14*(1-k/14),pan,att:.15})}
 function pluck(ac,out,when,m,a=.3,dur=1,pan=0){cloud(ac,out,when,dur,70,{pitches:[m,m+12],a,d:[.03,.09],spread:.15},u=>Math.pow(1-u,3));grain(ac,out,when,{f:440*Math.pow(2,(m-69)/12),d:.05,a:a*.6,pan,att:.1})}
 // the four voices: each sack's signature sound, used in every deed so the cast is recognisable by ear
 const VOICE={R:{base:45,bp:600,step:.9,color:'creak'},B:{base:33,bp:180,step:1.4,color:'thump'},I:{base:57,bp:2400,step:.5,color:'breath'},O:{base:81,bp:5200,step:.6,color:'glass'}};
 function say(ac,out,id,when,gesture,amt=1,pan=0){const v=VOICE[id],mf=m=>440*Math.pow(2,(m-69)/12);
  switch(gesture){
   case'step':if(id==='B')thump(ac,out,when,.7*amt,55,pan);else grain(ac,out,when,{bp:v.bp,d:.05,a:.18*amt*v.step,pan,att:.1});break;
   case'land':thump(ac,out,when,amt*(id==='B'?1.2:.45),id==='B'?45:90,pan);cloud(ac,out,when,.25,60,{bp:v.bp,a:.04*amt,d:[.01,.04]},u=>1-u);break;
   case'react'://the sack's cry, made of grains
    if(id==='R')cloud(ac,out,when,.45,50,{f:mf(v.base+12),glide:-.25,noise:.5,a:.06*amt,d:[.04,.09],type:'triangle'},u=>Math.sin(Math.PI*u));
    if(id==='B'){thump(ac,out,when,.6*amt,40,pan);cloud(ac,out,when,.6,40,{f:mf(v.base+12),glide:-.1,a:.07*amt,d:[.08,.18],type:'triangle'},u=>Math.sin(Math.PI*u))}
    if(id==='I')cloud(ac,out,when,.7,70,{bp:v.bp,a:.05*amt,d:[.03,.09]},u=>Math.sin(Math.PI*u)*(1-u));
    if(id==='O'){for(let k=0;k<3;k++)grain(ac,out,when+k*.07,{f:mf(v.base+[0,3,7][k]),d:.18,a:.09*amt,pan,att:.05})}break;
   case'sink':cloud(ac,out,when,1.2*amt,40,{f:mf(v.base),glide:-.4,a:.035,d:[.08,.2],noise:id==='I'?.8:.2},u=>1-u);break;
   case'tick':grain(ac,out,when,{f:mf(v.base+24),d:.02,a:.12*amt,pan,att:.05});break;
   case'breathe':cloud(ac,out,when,amt,25,{bp:v.bp*.6,a:.02,d:[.1,.3]},u=>Math.sin(Math.PI*u));break;
  }}
 return {noise,grain,cloud,thump,pluck,say,VOICE};
})();
