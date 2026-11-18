# GrabCut (#29) + trimap alpha refinement (#31) of the Agence Rol visitor (man.jpg, PD).
import cv2, numpy as np
from PIL import Image
S='/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/'
O=S+'test-shot/'
im=cv2.imread(S+'man.jpg'); H,W=im.shape[:2]
sc=0.5; ims=cv2.resize(im,None,fx=sc,fy=sc)
M=np.full((H,W),cv2.GC_BGD,np.uint8)
cv2.rectangle(M,(150,150),(1230,1737),cv2.GC_PR_BGD,-1)
cv2.ellipse(M,(540,470),(260,330),0,0,360,cv2.GC_PR_FGD,-1)
cv2.fillPoly(M,[np.array([(330,700),(760,640),(1060,780),(1210,1150),(1230,1737),(160,1737),(170,1100)])],cv2.GC_PR_FGD)
for r in [(380,210,690,380),(430,380,640,700),(380,850,1050,1650),(250,1100,380,1600),(700,1500,850,1620)]:
    cv2.rectangle(M,r[:2],r[2:],cv2.GC_FGD,-1)
for r in [(800,40,1280,560),(0,0,300,700),(0,0,1280,140),(820,560,1280,640),(1230,0,1280,1737)]:
    cv2.rectangle(M,r[:2],r[2:],cv2.GC_BGD,-1)
m=cv2.resize(M,(ims.shape[1],ims.shape[0]),interpolation=cv2.INTER_NEAREST)
bg=np.zeros((1,65));fg=np.zeros((1,65))
cv2.grabCut(ims,m,None,bg,fg,8,cv2.GC_INIT_WITH_MASK)
mm=np.where((m==1)|(m==3),255,0).astype(np.uint8)
mm=cv2.resize(mm,(W,H),interpolation=cv2.INTER_LINEAR); mm=(mm>127).astype(np.uint8)*255
# hand-drawn scissor clip: coat outline (removes the flower debris along the left sleeve and right elbow)
clip=np.zeros_like(mm)
poly=np.array([(320,250),(700,150),(760,330),(700,420),(690,620),(980,760),(1090,900),(1150,1100),(1210,1350),(1220,1560),(1150,1640),(1000,1700),(560,1720),(200,1715),(180,1500),(190,1250),(240,1000),(300,840),(420,700),(430,560),(380,380)])
cv2.fillPoly(clip,[poly],255)
mm=cv2.bitwise_and(mm,clip)
n,lab,st,_=cv2.connectedComponentsWithStats(mm); i=1+np.argmax(st[1:,4]); mm=(lab==i).astype(np.uint8)*255
inv=255-mm; n,lab,st,_=cv2.connectedComponentsWithStats(inv)
for j in range(1,n):
    x,y,w,h,a=st[j]
    if x>0 and y>0 and x+w<W and y+h<H: mm[lab==j]=255
mm=cv2.morphologyEx(mm,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
mm=cv2.morphologyEx(mm,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
# trimap matte: unknown band 6px; alpha from guided smoothing of the hard mask with the luminance edge
gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
hard=mm.astype(np.float32)/255
soft=cv2.GaussianBlur(hard,(0,0),2.2)
er=cv2.erode(mm,np.ones((7,7),np.uint8)); di=cv2.dilate(mm,np.ones((7,7),np.uint8))
band=(di>0)&(er==0)
alpha=np.where(er>0,1.0,np.where(band,soft,0.0))
# decontaminate: in the band, pull the light background out of edge colour (dark subject on light ground)
rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB).astype(np.float32)
inner=cv2.inpaint(im,(255-er).astype(np.uint8)&(di),5,cv2.INPAINT_TELEA)
inner=cv2.cvtColor(inner,cv2.COLOR_BGR2RGB).astype(np.float32)
rgb=np.where(band[...,None],np.minimum(rgb,inner*0.6+rgb*0.4),rgb)
out=np.dstack([rgb.clip(0,255).astype(np.uint8),(alpha*255).astype(np.uint8)])
Image.fromarray(out).save(O+'man_rgba_full.png')
cv2.imwrite(O+'man_failmask.png',((band)*255).astype(np.uint8))
a=Image.fromarray(out);b=Image.new('RGBA',a.size,(255,0,255,255));b.alpha_composite(a);b.thumbnail((500,640));b.convert('RGB').save(O+'man_chk.jpg')
print('ok')
