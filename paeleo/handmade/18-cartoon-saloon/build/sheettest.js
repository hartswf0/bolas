// Model sheet: renders the turnaround and expression drawings exactly as the rig uses them (proof/turnsheet.png)
function sheetTest(){
  const c=document.getElementById('c').getContext('2d');
  c.setTransform(1,0,0,1,0,0); c.fillStyle='#ece2cc';c.fillRect(0,0,1280,720);
  c.fillStyle='#3a2a20'; c.font='600 22px Literata'; c.fillText('SCION 18 · turnaround + expression sheet (as rendered by the rig)', 30, 40);
  const base={x:0,u:0,lie:0,crouch:0,h:0.9,pitch:-4,head:'prof',ear:0.85,eye:1,T:0.45,wag:0,t:0};
  const lab=(x,y,s)=>{c.fillStyle='#3a2a20';c.font='13px "JetBrains Mono"';c.fillText(s,x,y);};
  const row1=[[-1.2,{},'L stand'],[-0.2,{u:1,head:'back34'},'Q1 3/4 rear'],[0.7,{u:2,head:'rear'},'RV rear'],[1.6,{u:3,head:'back34',headFace:-1},'Q2 = mirror Q1'],[2.6,{u:3,lie:1,head:'back34',headFace:-1,h:0,pitch:20,ear:0.2,T:1},'Q2 lie (refusal)'],[3.6,{u:3,lie:1,head:'front34',headFace:1,headFront:true,headPivot:[12,33]},'Q2 lie, looks back']];
  c.save(); c.translate(0,-300); for(const [x,p,l] of row1){ drawDog(c,Object.assign({},base,{x},p)); lab(sx(x)-60,620,l);} c.restore();
  const row2=[[-1.2,{crouch:1,h:0.15,pitch:14,ear:0.05,T:1.35,eye:1.25,brow:1},'L crouch (retreat)'],[-0.1,{h:0.05,pitch:18,ear:0.4,T:0.5,crouch:0.15,eye:0.85},'L head low (approach)'],[1.1,{lie:1,h:0.6,pitch:0,ear:0.5},'L lie'],[2.3,{lie:1,h:0.85,pitch:3,head:'in34',headFront:true,ear:1},'L lie, looks in'],[3.5,{lie:1,h:0,pitch:8,eye:0,ear:0.35},'L lie, settles']];
  for(const [x,p,l] of row2){ drawDog(c,Object.assign({},base,{x},p)); lab(sx(x)-70,625,l);}
}
