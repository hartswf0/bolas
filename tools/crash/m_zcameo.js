/* CAMEOS · short looping poses for the CRASH LAB site: the cast waves, points, sits on the edge of a film, peeks over it,
   shrugs, jumps, and watches from behind. Each world is one actor, 16 frames, last frame equal to the first so it loops. */
(function(){
  const L=16, ALLOW=['legs','feet','overreach','slide','unbalanced','clash','floor','clip','bump','balance','support'];
  const FACE={A:'happy',B:'smug',C:'grin',Cb:'deadpan',Od:'happy'};
  const W=(cid,aid,build)=>HW(cid,{title:'CAMEO '+cid,len:L,allow:ALLOW},({mk})=>{ const A=mk(aid,stance(0,0,{z:0,w:11})); build(A,FC(FACE[aid]||'calm')); });
  const pose={
    wave:(A,fc)=>{ const up=o=>({handR:SELF('head',[-34+o,20+o*.4,8]),shapeR:'open',palmR:'fwd',poleR:[-1,0,0]});
      A.k(0,Object.assign({},up(0),fc,{spine:{side:3},head:{tilt:-4}})); A.k(4,up(20),'io'); A.k(8,up(0),'io'); A.k(12,up(20),'io'); A.k(15,up(0),'io'); },
    point:(A,fc)=>{ const p=(x,y)=>({handR:SELF('chest',[x,y,18]),shapeR:'point',poleR:[0,-1,0]});
      A.k(0,Object.assign({},p(-58,22),fc,{look:[-400,150,40],spine:{side:-4}})); A.k(5,p(-66,26),'out'); A.k(10,p(-58,22),'io'); A.k(15,p(-58,22),'io'); },
    shrug:(A,fc)=>{ const s=(k,t)=>({shrug:k,handL:SELF('chest',[20,-6,20]),handR:SELF('chest',[-20,-6,20]),poleL:[0,-1,0],poleR:[0,-1,0],shapeL:'flat',shapeR:'flat',palmL:'up',palmR:'up',head:{tilt:t}});
      A.k(0,Object.assign({},s(0,0),fc)); A.k(6,s(1,14),'out'); A.k(11,s(1,14),'io'); A.k(15,s(0,0),'io'); },
    peek:(A,fc)=>{ const g=(t,n)=>({handL:SELF('chest',[17,-2,24]),handR:SELF('chest',[-17,-2,24]),shapeL:'grip',shapeR:'grip',poleL:[1,-1,0],poleR:[-1,-1,0],spine:{fwd:8},head:{tilt:t,nod:n}});
      A.k(0,Object.assign({},g(-8,4),fc)); A.k(7,g(9,0),'io'); A.k(15,g(-8,4),'io'); },
    jump:(A,fc)=>{ const r=A.cur0().root; const j=(y,o)=>({root:{y:r.y+y},handL:SELF('head',[26,28+o,6]),handR:SELF('head',[-26,28+o,6]),shapeL:'open',shapeR:'open',poleL:[1,0,0],poleR:[-1,0,0]});
      A.k(0,Object.assign({},j(-8,-10),fc)); A.k(4,Object.assign(j(16,6),{footL:[11,14,12],footR:[-11,14,12]}),'out'); A.k(8,Object.assign(j(-8,-10),{footL:[11,0,12],footR:[-11,0,12]}),'in'); A.k(15,j(-8,-10),'io'); },
    sit:(A,fc)=>{ const s=seatedK(0,0,0,{seat:56,feet:20}); const sw=(a)=>({footL:[11,0,20+a],footR:[-11,0,20-a]});
      A.k(0,Object.assign({},s,fc,sw(8),{handL:SELF('pelvis',[24,-4,4]),handR:SELF('pelvis',[-24,-4,4]),shapeL:'flat',shapeR:'flat'})); A.k(8,sw(-8),'io'); A.k(15,sw(8),'io'); },
  };
  for(const [aid,name] of [['A','bola'],['B','shim'],['C','dot'],['Cb','critic']])
    for(const k of Object.keys(pose)) W('cam_'+name+'_'+k,aid,pose[k]);
})();
