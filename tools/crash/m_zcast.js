/* CAST SHEET · the crash-test family and the Critic, each in a character pose, for the model sheets on the CRASH LAB site. */
(function(){
  const one=(id,cid,pose,face)=>HW(cid,{title:'CAST '+id,len:4,allow:['legs','feet','overreach','slide','unbalanced','clash','floor','clip','bump']},({mk})=>{
    const A=mk(id,stance(0,0,{z:0,w:11})); A.k(0,Object.assign({},pose,FC(face))); });
  one('A','cast_bola',{handR:SELF('head',[-30,14,8]),shapeR:'open',palmR:'fwd',poleR:[-1,0,0],spine:{side:3}},'happy');
  one('B','cast_shim',{handL:SELF('chest',[-8,-14,16]),handR:SELF('chest',[8,-8,16]),shapeL:'flat',shapeR:'flat',poleL:[1,-.4,0],poleR:[-1,-.4,0],head:{tilt:-6}},'smug');
  one('C','cast_dot',{handL:SELF('head',[22,22,4]),handR:SELF('head',[-22,22,4]),shapeL:'open',shapeR:'open',poleL:[1,0,0],poleR:[-1,0,0]},'grin');
  one('Cb','cast_critic',{handL:SELF('pelvis',[8,6,-16]),handR:SELF('pelvis',[-8,6,-16]),poleL:[1,0,-1],poleR:[-1,0,-1],head:{nod:-6}},'deadpan');
  one('D','cast_extra',{},'calm');
})();
