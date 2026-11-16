import cv2, numpy as np
SRC='/home/user/bolas/paeleo/scion/oulipo/films/sources/la-machine-a-tuer-le-temps/'
OUT='/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/m/'
def cut(name, rect, fgpts, out):
    img=cv2.imread(SRC+name)
    mask=np.zeros(img.shape[:2],np.uint8)
    x,y,w,h=rect; mask[y:y+h,x:x+w]=cv2.GC_PR_FGD
    for p,q in fgpts: cv2.line(mask,p,q,cv2.GC_FGD,14)
    bg=np.zeros((1,65)); fg=np.zeros((1,65))
    cv2.grabCut(img,mask,None,bg,fg,10,cv2.GC_INIT_WITH_MASK)
    m=np.where((mask==1)|(mask==3),255,0).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); m=np.where(lab==k,255,0).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    cv2.imwrite(OUT+out,m)
    vis=img.copy(); vis[m==0]=(vis[m==0]*0.2).astype(np.uint8); cv2.rectangle(vis,(x,y),(x+w,y+h),(0,0,255),2)
    cv2.imwrite(OUT+'vis_'+out.replace('png','jpg'),vis)
cut('loc_2017844115.jpg',(320,240,330,770),[((560,330),(560,900)),((520,300),(600,300)),((470,450),(470,850))],'m_cond.png')
cut('loc_2017844121.jpg',(240,190,440,580),[((330,230),(330,700)),((420,330),(640,300)),((300,400),(380,560))],'m_woman.png')
