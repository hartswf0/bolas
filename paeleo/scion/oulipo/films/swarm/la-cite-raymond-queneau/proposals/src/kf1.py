import sys; sys.path.insert(0,'/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/bin')
from common import *
import cv2
im=np.asarray(Image.open(SRC+'corbeil-leonblum-1.jpg').convert('RGB'))
# wider than frame so the track has room: keep full width, 16:9 crop
Y0=180
c=im[Y0:Y0+720].copy()  # 1280x720
H,W=c.shape[:2]
bgr=cv2.cvtColor(c,cv2.COLOR_RGB2BGR)
# --- plane 1: cars + fence + kerb (foreground) via GrabCut
mask=np.zeros((H,W),np.uint8); bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
rect=(0,585,1040,H-580)
cv2.grabCut(bgr,mask,rect,bg,fg,6,cv2.GC_INIT_WITH_RECT)
car=np.where((mask==1)|(mask==3),255,0).astype(np.uint8)
car[690:,:]=255   # pavement band under the cars belongs to the near plane
car=cv2.morphologyEx(car,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
# --- plane 2: lamp post (luminance column mask, darker than facade)
g=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY).astype(np.int16)
env=np.zeros((H,W),np.uint8)
cv2.rectangle(env,(560,512-Y0),(567,770-Y0),255,-1)
pts=np.array([[563,517],[555,511],[545,509],[535,511],[528,514]],np.int32); pts[:,1]-=Y0
cv2.polylines(env,[pts],False,255,4)
cv2.ellipse(env,(526,519-Y0),(11,6),0,0,360,255,-1)
loc=cv2.GaussianBlur(g,(41,41),0)
lamp=np.where((env>0)&(g<loc+4),255,0).astype(np.uint8)
lamp=cv2.dilate(lamp,np.ones((3,3),np.uint8))
cv2.imwrite('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/kf1_masks.png',np.dstack([car,lamp,np.zeros_like(car)]))
hole=cv2.dilate(car|lamp,np.ones((9,9),np.uint8))
back=cv2.inpaint(bgr,hole,9,cv2.INPAINT_TELEA)
back=cv2.cvtColor(back,cv2.COLOR_BGR2RGB)
# track state at t=13 s of a 12 s, 40 px lateral move: phase p=0.6
p=0.6; T=40
def shift(a,dx):
    M=np.float32([[1,0,dx],[0,1,0]]); return cv2.warpAffine(a,M,(W,H),borderMode=cv2.BORDER_REPLICATE)
out=shift(back,-0.25*T*p).astype(np.float32)
for m,k in ((lamp,0.6),(car,1.0)):
    layer=shift(c,-k*T*p).astype(np.float32); a=shift(m,-k*T*p).astype(np.float32)[...,None]/255
    a=cv2.GaussianBlur(a,(3,3),0)[...,None] if a.ndim==3 else a
    out=out*(1-a)+layer*a
# overscan: scale 1.04 to hide replicated edges
out=cv2.resize(out,None,fx=1.04,fy=1.04,interpolation=cv2.INTER_AREA)
oy=(out.shape[0]-H)//2; ox=(out.shape[1]-W)//2; out=out[oy:oy+H,ox:ox+W]
out=match(out)
img=Image.fromarray(out.astype(np.uint8))
img.save(OUT+'kf-1-picture.png')
captions(img,"« Le soir, l'avenue s'allume pour tout le monde. »","« Le lampadaire du parking est équipé depuis mars. »")
img.save(OUT+'kf-1.png')
