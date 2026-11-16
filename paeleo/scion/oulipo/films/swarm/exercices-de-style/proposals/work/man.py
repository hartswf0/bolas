import cv2, numpy as np
from PIL import Image
S='/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/'
im=cv2.imread(S+'man.jpg'); H,W=im.shape[:2]
sc=0.5; ims=cv2.resize(im,None,fx=sc,fy=sc)
M=np.full((H,W),cv2.GC_BGD,np.uint8)
cv2.rectangle(M,(150,150),(1230,1737),cv2.GC_PR_BGD,-1)
cv2.ellipse(M,(540,470),(260,330),0,0,360,cv2.GC_PR_FGD,-1)
cv2.fillPoly(M,[np.array([(330,700),(760,640),(1060,780),(1210,1150),(1230,1737),(160,1737),(170,1100)])],cv2.GC_PR_FGD)
for r in [(380,210,690,380),(430,380,640,700),(380,850,1050,1650)]:
    cv2.rectangle(M,r[:2],r[2:],cv2.GC_FGD,-1)
for r in [(800,40,1280,560),(0,0,300,700),(0,0,1280,140),(820,560,1280,640)]:
    cv2.rectangle(M,r[:2],r[2:],cv2.GC_BGD,-1)
m=cv2.resize(M,(ims.shape[1],ims.shape[0]),interpolation=cv2.INTER_NEAREST)
bg=np.zeros((1,65));fg=np.zeros((1,65))
cv2.grabCut(ims,m,None,bg,fg,8,cv2.GC_INIT_WITH_MASK)
mm=np.where((m==1)|(m==3),255,0).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(mm); i=1+np.argmax(st[1:,4]); mm=(lab==i).astype(np.uint8)*255
# fill holes
inv=255-mm; n,lab,st,_=cv2.connectedComponentsWithStats(inv)
for j in range(1,n):
    x,y,w,h,a=st[j]
    if x>0 and y>0 and x+w<mm.shape[1] and y+h<mm.shape[0]: mm[lab==j]=255
mm=cv2.morphologyEx(mm,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
mm=cv2.resize(mm,(W,H)); mm=cv2.GaussianBlur(mm,(5,5),0)
x,y,ww,hh=cv2.boundingRect((mm>127).astype(np.uint8))
Image.fromarray(np.dstack([cv2.cvtColor(im,cv2.COLOR_BGR2RGB),mm])[y:y+hh,x:x+ww]).save('man_cut.png'); print(x,y,ww,hh)
a=Image.open('man_cut.png');b=Image.new('RGBA',a.size,(255,0,255,255));b.alpha_composite(a);b.thumbnail((500,600));b.convert('RGB').save('man_cut_chk.jpg')
