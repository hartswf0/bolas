/* Shared by the level page: builds a character's animations from its drawings, and draws it.
   Every animation is a swap between whole paintings; nothing is bent. (play/index.html has its own copy.) */
'use strict';
const WY = (function(){
  const LABEL = { dance:'Dance', sit:'Sit', kneel:'Kneel', crouch:'Crouch', lean:'Lean', lunge:'Lunge', lie:'Lie down', fall:'Fall', run:'Run', fly:'Fly', float:'Float', throw:'Throw', reach:'Reach', point:'Point' };
  const GROUND_ONLY = new Set(['lie','fall','sit','kneel','crouch','float','fly']);
  const neutral = d => (d.cls==='stand'?0:2) + (d.arm>=45?2:0) + (d.spread>=20?2:0) + (d.view==='q3'?0:(d.view==='front'?0.5:3));

  function plan(ch){
    const D = ch.draws.map((d,i)=>Object.assign({i},d));
    const cands = D.filter(d=>!GROUND_ONLY.has(d.cls) && d.view!=='back' && d.view!=='back3q').sort((a,b)=>neutral(a)-neutral(b));
    const idle = cands[0] || D.filter(d=>d.view!=='back').sort((a,b)=>neutral(a)-neutral(b))[0] || D[0];
    const strides = D.filter(d=>d.spread>=25 && d.view!=='back' && d.view!=='back3q' && !GROUND_ONLY.has(d.cls));
    const walk = { frames:[], mode:'glide' };
    if (strides.length >= 2){ walk.frames = strides.map(d=>({d, hold:170})); walk.mode = 'step'; }
    else if (strides.length === 1 && strides[0] !== idle){ walk.frames = [{d:strides[0],hold:170},{d:idle,hold:170}]; walk.mode = 'step'; }
    else walk.frames = [{d:strides[0]||idle, hold:300}];
    const bestFor = v => D.filter(d=>d.view===v && !GROUND_ONLY.has(d.cls)).sort((a,b)=>neutral(a)-neutral(b))[0];
    const ring = [['q3',false],['prof',false],['back3q',false],['back',false],['back3q',true],['prof',true],['q3',true],['front',false]];
    const have = new Set(D.map(d=>d.view));
    let turn = null;
    if (have.size >= 2){ turn = []; let last = idle; for (const [v,m] of ring){ const d = bestFor(v) || last; last = d; turn.push({d, hold:150, mirror:m}); } turn.push({d:idle, hold:200}); }
    const poses = [], byCls = {};
    D.forEach(d=>{ if (d.cls!=='stand' && d.cls!=='walk') (byCls[d.cls] = byCls[d.cls]||[]).push(d); });
    for (const [c, list] of Object.entries(byCls)) poses.push({ label: LABEL[c] || ('Pose: '+c), frames: list.map(d=>({d, hold:520})) });
    const reach = D.filter(d=>d.arm>=60 && (d.cls==='stand'||d.cls==='walk'||d.cls==='dance') && !(byCls[d.cls]||[]).includes(d));
    if (reach.length) poses.push({ label:'Reach', frames: reach.map(d=>({d, hold:520})) });
    return { idle, walk, turn, poses, all: D };
  }

  /* an Actor holds one character's state: where it stands, which way, which animation is running */
  function Actor(ch, imgs){
    this.ch = ch; this.imgs = imgs; this.P = plan(ch);
    this.x = 0; this.dir = 1; this.anim = {kind:'idle'}; this.t0 = performance.now(); this.shown = this.P.idle.i; this.swapT = -1e9; this.moving = false;
  }
  Actor.prototype.set = function(a){ this.anim = a; this.t0 = performance.now(); };
  Actor.prototype.buttons = function(){
    const P = this.P, out = [{label:'Idle', fn:()=>this.set({kind:'idle'})}];
    if (P.turn) out.push({label:'Turn', fn:()=>this.set({kind:'turn'})});
    P.poses.forEach(p=>out.push({label:p.label, fn:()=>{ if (this.anim.p===p) this.set({kind:'idle'}); else this.set({kind:'pose', p}); }}));
    out.push({label:'Next painting', fn:()=>this.set({kind:'one', k:((this.anim.k===undefined?-1:this.anim.k)+1) % P.all.length})});
    return out;
  };
  /* returns {d, extra, dy, breathe} for this moment */
  Actor.prototype.pick = function(now, moving){
    const a = this.anim, P = this.P, dt = Math.max(0, now - this.t0);
    if (moving && (a.kind==='idle' || a.kind==='pose' || a.kind==='one')) { this.set({kind:'walk'}); return this.pick(now, moving); }
    if (!moving && a.kind==='walk') { this.set({kind:'idle'}); return this.pick(now, moving); }
    if (a.kind==='walk'){
      const fr = P.walk.frames, total = fr.reduce((s,f)=>s+f.hold,0); let t = dt % total, f = fr[0];
      for (const x of fr){ if (t < x.hold){ f = x; break; } t -= x.hold; }
      return { d:f.d, extra:false, dy:-Math.abs(Math.sin(dt/170*Math.PI/(P.walk.mode==='step'?2:1)))*1.6 };
    }
    if (a.kind==='turn'){
      let t = dt, f = null;
      for (const x of P.turn){ if (t < x.hold){ f = x; break; } t -= x.hold; }
      if (!f){ this.set({kind:'idle'}); return this.pick(now, moving); }
      return { d:f.d, extra:!!f.mirror, dy:0 };
    }
    if (a.kind==='pose'){ const fr = a.p.frames, k = Math.floor((dt % (fr.length*520))/520); return { d:fr[k].d, extra:false, dy:0 }; }
    if (a.kind==='one') return { d:P.all[a.k], extra:false, dy:0 };
    return { d:P.idle, extra:false, dy:0, breathe:Math.sin(dt/1100)*0.006 };
  };
  /* draw at stage pixel (sx, floorY); ppc is stage px per cm */
  Actor.prototype.draw = function(ctx, c, sx, floorY, ppc, now){
    const d = c.d, img = this.imgs[d.i]; if (!img) return;
    if (d.i !== this.shown){ this.shown = d.i; this.swapT = now; }
    const s = ((0.70*this.ch.height_cm) / d.body_px) * ppc;
    const flip = (this.dir !== (d.right ? 1 : -1)) !== !!c.extra;
    const age = now - this.swapT, dip = age < 130 ? (1 - age/130) * 0.025 * d.h * s : 0;
    ctx.save(); ctx.translate(sx, floorY + dip + (c.dy||0)*ppc);
    if (flip) ctx.scale(-1,1);
    if (c.breathe) ctx.scale(1, 1 + c.breathe);
    ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 3;
    ctx.drawImage(img, -d.ax*s, -d.h*s, d.w*s, d.h*s);
    ctx.restore();
  };
  function loadImg(src){ return new Promise(r=>{ const i = new Image(); i.onload = ()=>r(i); i.onerror = ()=>r(null); i.src = src; }); }
  return { plan, Actor, loadImg, neutral };
})();
