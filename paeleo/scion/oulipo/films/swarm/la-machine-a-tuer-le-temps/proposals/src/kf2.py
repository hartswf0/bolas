from common import *
from puppets import woman, conductor, render
W,H=1280,720
scr=paper(W,H,(240,214,160),seed=21,grain=4)
a=np.array(scr).astype(float); yy,xx=np.mgrid[0:H,0:W]
r=np.sqrt(((xx-W*0.56)/(W*0.62))**2+((yy-H*0.42)/(H*0.78))**2)
glow=np.clip(1.15-r,0,1)**1.25
dark=np.array([96,22,26.0])
a=a*glow[...,None]+dark*(1-glow[...,None])
img=Image.fromarray(a.clip(0,255).astype(np.uint8))
def layer(m,xy,color,alpha=255,blur=0.0):
    if blur: m=m.filter(ImageFilter.GaussianBlur(blur))
    if alpha<255: m=m.point(lambda v:v*alpha//255)
    img.paste(Image.new('RGB',m.size,color),xy,m)
# far plane: the Union Station waiting-room colonnade (pool shot 08), thresholded into a paper layer
far=load('08'); far=far.crop((40,40,far.width-40,int(far.height*0.66))); far=far.resize((W,int(far.height*W/far.width)))
fm=far.point(lambda v:255 if v<62 else 0).filter(ImageFilter.MedianFilter(9))
layer(fm,(0,-40),(128,76,56),alpha=60,blur=2.5)
d=ImageDraw.Draw(img); K=(14,10,10); LIT=(240,212,150)
d.rectangle([0,628,W,H],fill=K)
for x in range(-40,W,64): d.polygon([(x+10,642),(x+44,642),(x+40,652),(x+14,652)],fill=(70,40,30))
dx=1010
d.rectangle([dx,150,dx+210,630],fill=K)
d.rectangle([dx+26,232,dx+184,630],fill=(250,226,170))
d.polygon([(dx+26,232),(dx+112,250),(dx+112,612),(dx+26,630)],fill=K)
for i in range(4): d.rectangle([dx+40+i*36,170,dx+64+i*36,214],fill=LIT)
d.ellipse([dx+94,420,dx+104,430],fill=LIT)
d.text((dx+52,560),'CONSIGNE',font=font(14),fill=(180,150,110))
cx,cy,Rr=560,128,70
d.rectangle([cx-5,20,cx+5,cy-Rr+4],fill=K); d.rectangle([cx-46,14,cx+46,28],fill=K)
d.ellipse([cx-Rr,cy-Rr,cx+Rr,cy+Rr],fill=K)
for i in range(60):
    t=i/60*2*math.pi; r1=Rr-10; r2=Rr-(22 if i%5==0 else 15); w=4 if i%5==0 else 2
    d.line([(cx+r1*math.sin(t),cy-r1*math.cos(t)),(cx+r2*math.sin(t),cy-r2*math.cos(t))],fill=LIT,width=w)
def hnd(ang,l,w,col=LIT):
    t=math.radians(ang); d.line([(cx,cy),(cx+l*math.sin(t),cy-l*math.cos(t))],fill=col,width=w)
hnd(4.72/12*360,32,7); hnd(43/60*360,48,4); hnd(51/60*360,54,2,(178,40,36))
d.ellipse([cx-7,cy-7,cx+7,cy+7],fill=LIT)
# puppets (hand-cut, jointed)
cm=render(conductor(),(W,H),(250,628-12-236*1.0),1.0)
layer(cm,(0,0),K)
wm=render(woman(),(W,H),(760,628-8-208*1.05),1.05)
layer(wm,(0,0),K)
# conductor's watch and chain, punched out of his card
pass
# the dropped receipt mid-fall between them
rc=Image.new('L',(56,32),0); rd=ImageDraw.Draw(rc); rd.rectangle([0,0,55,31],fill=255)
for i in range(5): rd.ellipse([7+i*10,12,12+i*10,17],fill=0)
rc=rc.rotate(28,expand=True,resample=Image.BICUBIC)
layer(rc,(560,500),K)
d=ImageDraw.Draw(img)
import numpy as _n
ys,xs=_n.nonzero(_n.array(cm)[200:300,280:340]>128)
hx,hy=280+xs.max(),200+ys[xs.argmax()]
d.ellipse([hx-2,hy-13,hx+22,hy+11],fill=K); d.ellipse([hx+3,hy-8,hx+17,hy+6],fill=LIT)
d.line([(hx+10,hy-1),(hx+10,hy-6)],fill=K,width=2); d.line([(hx+10,hy-1),(hx+14,hy+1)],fill=K,width=1)
img.save(OUT+'kf-2.png'); print('ok')
