import cv2, numpy as np
from PIL import Image
S='/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/'
# key: colour distance from paper
k=cv2.imread(S+'key2.jpg'); h,w=k.shape[:2]
paper=np.median(k[:80,:80].reshape(-1,3),0)
d=np.linalg.norm(k.astype(float)-paper,axis=2)
m=(d>38).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(m)
big=[i for i in range(1,n) if st[i,4]>400]
m=np.isin(lab,big).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
x,y,ww,hh=cv2.boundingRect(m)
rgba=np.dstack([cv2.cvtColor(k,cv2.COLOR_BGR2RGB),cv2.GaussianBlur(m,(3,3),0)])[y:y+hh,x:x+ww]
Image.fromarray(rgba).save('key_cut.png'); print('key',ww,hh)
# man: grabcut
im=cv2.imread(S+'man.jpg'); sc=0.5; ims=cv2.resize(im,None,fx=sc,fy=sc)
mask=np.zeros(ims.shape[:2],np.uint8); rect=(int(170*sc),int(140*sc),int(1040*sc),int(1590*sc))
bg=np.zeros((1,65));fg=np.zeros((1,65))
cv2.grabCut(ims,mask,rect,bg,fg,6,cv2.GC_INIT_WITH_RECT)
mm=np.where((mask==1)|(mask==3),255,0).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(mm); i=1+np.argmax(st[1:,4]); mm=(lab==i).astype(np.uint8)*255
mm=cv2.resize(mm,(im.shape[1],im.shape[0]))
mm=cv2.GaussianBlur(mm,(5,5),0)
Image.fromarray(mm).save('man_mask.png')
x,y,ww,hh=cv2.boundingRect((mm>127).astype(np.uint8))
Image.fromarray(np.dstack([cv2.cvtColor(im,cv2.COLOR_BGR2RGB),mm])[y:y+hh,x:x+ww]).save('man_cut.png'); print('man',x,y,ww,hh)
