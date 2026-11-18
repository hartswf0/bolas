import cv2,numpy as np,sys
S=sys.argv[1]
img=cv2.imread(S+'/Little_girl_laughing_with_excitement_in_France.jpg')
h,w=img.shape[:2]
m=np.zeros((h,w),np.uint8); bg=np.zeros((1,65));fg=np.zeros((1,65))
cv2.grabCut(img,m,(60,0,w-280,h-1),bg,fg,5,cv2.GC_INIT_WITH_RECT)
# sure fg: face
m[350:1100,600:1250]=cv2.GC_FGD
m[1150:h,500:1400]=cv2.GC_FGD
m[0:900,1590:w]=cv2.GC_BGD; m[:,1830:w]=cv2.GC_BGD; m[1290:h,0:330]=cv2.GC_BGD; m[1150:h,0:560][:,:0]=0
m[950:h,1450:1760]=cv2.GC_PR_FGD; m[1140:1250,490:800]=cv2.GC_BGD; m[1140:1340,490:565]=cv2.GC_BGD
cv2.grabCut(img,m,None,bg,fg,3,cv2.GC_INIT_WITH_MASK)
a=np.where((m==1)|(m==3),255,0).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(a)
k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]);a=np.where(lab==k,255,0).astype(np.uint8)
a=cv2.morphologyEx(a,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
# fill holes
pass
cv2.imwrite(sys.argv[2],a)
v=img.copy();v[a==0]=(v[a==0]*0.2).astype(np.uint8)
cv2.imwrite(sys.argv[3],cv2.resize(v,(w//3,h//3)))
