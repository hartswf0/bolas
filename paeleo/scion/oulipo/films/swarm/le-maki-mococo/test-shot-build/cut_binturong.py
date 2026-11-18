"""GrabCut cutout of the Brehm/Specht binturong (PD engraving), hand-seeded polygon."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
SRC="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/r1/brehm265.jpg"
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/"
crop_poly=[(40,415),(110,402),(180,398),(230,392),(282,393),(300,420),(380,380),(470,330),(560,310),(640,290),(660,240),
 (690,195),(740,205),(758,250),(750,310),(720,350),(712,420),(700,480),(680,540),(650,600),(620,640),(605,700),(560,712),
 (528,690),(540,640),(510,600),(450,640),(430,700),(420,745),(380,772),(330,762),(318,720),(345,690),(300,645),(260,650),
 (220,690),(190,760),(168,800),(160,834),(105,838),(98,800),(130,760),(150,700),(158,640),(120,600),(95,570),(88,520),(68,470),(36,432)]
poly=[(40+x/0.75,380+y/0.75) for x,y in crop_poly]
im=np.array(Image.open(SRC).convert("RGB"))
H,W=im.shape[:2]
m=Image.new("L",(W,H),0); ImageDraw.Draw(m).polygon(poly,fill=255)
m=np.array(m)>0
mask=np.full((H,W),cv2.GC_BGD,np.uint8)
mask[m]=cv2.GC_PR_FGD
inner=cv2.erode(m.astype(np.uint8),np.ones((41,41),np.uint8))>0
gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
dark=cv2.blur(gray,(15,15))<70
mask[inner & dark]=cv2.GC_FGD
x0,y0=int(min(p[0] for p in poly))-20,int(min(p[1] for p in poly))-20
x1,y1=int(max(p[0] for p in poly))+20,int(max(p[1] for p in poly))+20
sub=im[y0:y1,x0:x1].copy(); smask=mask[y0:y1,x0:x1].copy()
bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
cv2.grabCut(cv2.cvtColor(sub,cv2.COLOR_RGB2BGR),smask,None,bgd,fgd,6,cv2.GC_INIT_WITH_MASK)
fg=((smask==cv2.GC_FGD)|(smask==cv2.GC_PR_FGD)).astype(np.uint8)
# hand-cleaning at film scale: close fur gaps, keep largest component, smooth scissor line
fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
fg=cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(fg)
k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); fg=(lab==k).astype(np.uint8)
# fill holes
ff=fg.copy(); h,w=ff.shape; fm=np.zeros((h+2,w+2),np.uint8); cv2.floodFill(ff,fm,(0,0),1); fg=fg|(1-ff)
Image.fromarray(sub).save(OUT+"binturong_crop.png")
Image.fromarray(fg*255).save(OUT+"binturong_matte.png")
prev=sub.copy(); prev[fg==0]=(prev[fg==0]*0.25+190).astype(np.uint8)
Image.fromarray(prev).resize((sub.shape[1]//2,sub.shape[0]//2)).save("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/bint_prev.png")
print(x0,y0,x1,y1,fg.mean())
