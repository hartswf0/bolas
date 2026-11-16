import sys; sys.path.insert(0,'/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/bin')
from common import *
import cv2
S=2
im=np.asarray(Image.open(SRC+'noisy-cheminronde-1.jpg').convert('RGB')).astype(np.float32)
plate=im[150:870]                      # 1280x720, eye-level band
plate=match(plate,0.5)
# blur the parked car's plate (licence plate at about x 430-465, y 685-695 in source)
p=plate.copy(); y0,y1,x0,x1=680-150,700-150,420,475
p[y0:y1,x0:x1]=cv2.GaussianBlur(p[y0:y1,x0:x1],(0,0),5); plate=p
H,W=720*S,1280*S
plate=cv2.resize(plate,(W,H),interpolation=cv2.INTER_CUBIC)
r=np.random.default_rng(3)
def cardtex(rgb,seed,g=7):
    rr=np.random.default_rng(seed)
    n=cv2.resize(rr.standard_normal((H//24,W//24)).astype(np.float32),(W,H),interpolation=cv2.INTER_CUBIC)*g
    n+=rr.standard_normal((H,W)).astype(np.float32)*g*0.5
    return np.clip(np.array(rgb,np.float32)+n[...,None],0,255)
def T(pts,ang,org,off):  # FK: rotate local polygon about pivot then translate
    c,s=np.cos(ang),np.sin(ang); P=np.array(pts,np.float32)-org
    return np.stack([P[:,0]*c-P[:,1]*s,P[:,0]*s+P[:,1]*c],1)+off
def jag(P,amt=0.8,seed=0):
    rr=np.random.default_rng(seed); out=[]
    for i in range(len(P)):
        a,b=P[i],P[(i+1)%len(P)]; k=max(2,int(np.linalg.norm(b-a)/(5*S)))
        for t in np.linspace(0,1,k,endpoint=False): out.append(a+(b-a)*t+rr.normal(0,amt*S,2))
    return np.array(out,np.int32)
canvas=plate.copy()
def lay(canvas,P,tex,seed,shadow=(10,12),soft=10,dark=0.28):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[jag(P*S,0.7,seed)],255); m=m.astype(np.float32)/255
    sh=cv2.warpAffine(m,np.float32([[1,0,shadow[0]*S],[0,1,shadow[1]*S]]),(W,H)); sh=cv2.GaussianBlur(sh,(0,0),soft*S/2)
    canvas=canvas*(1-dark*sh[...,None]); a=cv2.GaussianBlur(m,(3,3),0)[...,None]
    canvas=canvas*(1-a)+tex*a
    e=m-cv2.warpAffine(m,np.float32([[1,0,1.5*S],[0,1,1.5*S]]),(W,H)); canvas+=np.clip(e,0,1)[...,None]*40
    return np.clip(canvas,0,255)
def pin(canvas,c):
    x,y=int(c[0]*S),int(c[1]*S)
    cv2.circle(canvas,(x+2*S,y+2*S),6*S,(40,38,34),-1)
    cv2.circle(canvas,(x,y),6*S,(176,142,72),-1); cv2.circle(canvas,(x-2*S,y-2*S),2*S,(236,214,150),-1)
    return canvas
# --- puppet pose at the key frame (t=19 s): arm raised -6 deg, head turned 34 deg down toward the car
base=np.array([905,720.0]); top=np.array([905,250.0])
th_arm=np.deg2rad(-6); th_head=np.deg2rad(-42)
grey=(70,74,78)
# pole (one strip, tapering) and base plinth
pole=np.array([[893,722],[917,722],[912,252],[898,252]],np.float32)
plinth=np.array([[884,722],[926,722],[922,640],[888,640]],np.float32)
collar=np.array([[892,600],[918,600],[918,588],[892,588]],np.float32)
# swan-neck arm, local coords with pivot at pole top (905,250), extends left
arc=[(905-120*(1-np.cos(a))*1.0, 250-70*np.sin(a)) for a in np.linspace(0,np.pi/2,14)]
inner=[(x+0,y+14) for x,y in arc][::-1]
arm_local=np.array(arc+[(785,190)]+[(785,201)]+inner,np.float32)
# straighten: arc goes up from pivot and turns left; end at (785,180)
arm=T(arm_local,th_arm,top,top)
arm_end=T(np.array([[785,186]],np.float32),th_arm,top,top)[0]
# head: hood + lens, local pivot at arm end
hx,hy=785,186
hood=np.array([[hx+10,hy-10],[hx-96,hy-6],[hx-116,hy+14],[hx-88,hy+28],[hx+6,hy+18]],np.float32)
lens=np.array([[hx-88,hy+24],[hx-6,hy+18],[hx-14,hy+32],[hx-80,hy+36]],np.float32)
headP=T(hood,th_head,np.array([hx,hy]),arm_end); lensP=T(lens,th_head,np.array([hx,hy]),arm_end)
# light pool from the lens onto the pavement around the parked car (soft, warm, faint)
lc=lensP.mean(0); pool=np.zeros((H,W),np.float32)
tgt=np.array([370,560.0])
cone=np.array([lensP[0],lensP[1],[tgt[0]+190,tgt[1]+30],[tgt[0]-170,tgt[1]+30]],np.float32)
cv2.fillPoly(pool,[(cone*S).astype(np.int32)],0.18); cv2.ellipse(pool,(int(tgt[0]*S),int((tgt[1]+28)*S)),(200*S,50*S),0,0,360,0.45,-1)
pool=cv2.GaussianBlur(pool,(0,0),22*S)[...,None]
canvas=np.clip(canvas*(1+1.1*pool)+pool*np.array([110,70,10]),0,255)
canvas=lay(canvas,pole,cardtex(grey,1),1)
canvas=lay(canvas,plinth,cardtex((62,66,70),2),2)
canvas=lay(canvas,collar,cardtex((84,88,92),3),3,shadow=(3,4),soft=3)
canvas=lay(canvas,arm,cardtex(grey,4),4)
canvas=lay(canvas,headP,cardtex((60,64,68),5),5)
canvas=lay(canvas,lensP,cardtex((250,226,170),6,4),6,shadow=(2,2),soft=2,dark=0.1)
g=np.zeros((H,W),np.float32); cv2.fillPoly(g,[(lensP*S).astype(np.int32)],1); g=cv2.GaussianBlur(g,(0,0),10*S)[...,None]
canvas=np.clip(canvas+g*np.array([70,52,18]),0,255)
canvas=pin(canvas,top); canvas=pin(canvas,arm_end)
out=cv2.resize(canvas,(1280,720),interpolation=cv2.INTER_AREA)
img=Image.fromarray(out.astype(np.uint8)); img.save(OUT+'kf-3-picture.png')
captions(img,"« Le réverbère se penche vers ceux qui rentrent. »","« Le réverbère suit chaque voiture qui se gare. »")
img.save(OUT+'kf-3.png')
