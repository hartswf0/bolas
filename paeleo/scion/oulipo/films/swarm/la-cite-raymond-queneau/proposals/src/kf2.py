import sys; sys.path.insert(0,'/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/bin')
from common import *
import cv2
rng=np.random.default_rng(7)
S=2; W,H=1280*S,720*S
def noise(scale,oct=4,seed=0):
    r=np.random.default_rng(seed); acc=np.zeros((H,W),np.float32); amp=1
    for o in range(oct):
        s=max(2,int(scale/(2**o)))
        n=r.standard_normal((H//s+2,W//s+2)).astype(np.float32)
        acc+=amp*cv2.resize(n,(W,H),interpolation=cv2.INTER_CUBIC); amp*=0.5
    return acc/acc.std()
def fibres(seed,n=900):
    r=np.random.default_rng(seed); f=np.zeros((H,W),np.float32)
    for _ in range(n):
        x,y=r.uniform(0,W),r.uniform(0,H); a=r.uniform(0,np.pi); L=r.uniform(8,40)*S
        cv2.line(f,(int(x),int(y)),(int(x+L*np.cos(a)),int(y+L*np.sin(a))),float(r.uniform(.3,1)),1)
    return cv2.GaussianBlur(f,(3,3),0)
def paper(rgb,seed,grain=6,fib=0.06,big=1.0):
    n=noise(40*S,4,seed)*grain*big + noise(3*S,1,seed+1)*grain*0.6
    base=np.ones((H,W,3),np.float32)*np.array(rgb,np.float32)
    return np.clip(base+n[...,None]-fibres(seed+2)[...,None]*255*fib,0,255)
def jag(pts,amt=1.2,seed=0):
    """hand-cut edge: resample polygon and jitter"""
    r=np.random.default_rng(seed); out=[]
    P=np.array(pts,np.float32)
    for i in range(len(P)):
        a,b=P[i],P[(i+1)%len(P)]; L=np.linalg.norm(b-a); k=max(2,int(L/(6*S)))
        for t in np.linspace(0,1,k,endpoint=False):
            out.append(a+(b-a)*t+r.normal(0,amt*S,2))
    return np.array(out,np.int32)
canvas=paper((236,233,226),1,grain=4,big=0.35)   # overcast sky sheet, faint warm white
yy=np.linspace(0,1,H)[:,None,None]; canvas=canvas*(1-0.06*yy)+np.array([200,204,210])*0.06*yy
def lay(canvas,mask,tex,shadow=(5,7),soft=9,dark=0.22,edge=True):
    m=(mask>0).astype(np.float32)
    sh=cv2.warpAffine(m,np.float32([[1,0,shadow[0]*S],[0,1,shadow[1]*S]]),(W,H)); sh=cv2.GaussianBlur(sh,(0,0),soft*S/2)
    canvas=canvas*(1-dark*sh[...,None])
    ma=cv2.GaussianBlur(m,(3,3),0)[...,None]
    canvas=canvas*(1-ma)+tex*ma
    if edge:  # bright cut edge on top-left, slightly darker bottom
        e=m-cv2.warpAffine(m,np.float32([[1,0,S],[0,1,S]]),(W,H)); canvas+= (np.clip(e,0,1)[...,None]*28)
    return np.clip(canvas,0,255)
def poly(pts,seed=0,amt=1.0):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[jag([(x*S,y*S) for x,y in pts],amt,seed)],255); return m
# --- far plane: pale distant blocks, hazy
far=poly([(0,330),(60,330),(60,300),(170,300),(170,322),(260,322),(260,290),(330,290),(330,336),(0,336)],3)
far|=poly([(980,300),(1060,300),(1060,280),(1180,280),(1180,312),(1280,312),(1280,340),(980,340)],4)
canvas=lay(canvas,far,paper((214,214,212),11,3),shadow=(2,3),soft=6,dark=0.08)
# --- main block: cream sheet, receding to the left (two volumes as in the reference)
def block(x0,x1,ybase,h0,h1,roofh,seed):
    # facade quad (top edge slants), plus curved zinc roof above
    fac=[(x0,ybase-h0),(x1,ybase-h1),(x1,ybase),(x0,ybase)]
    roof=[]
    for t in np.linspace(0,1,24):
        x=x0+(x1-x0)*t; top=ybase-(h0+(h1-h0)*t)
        roof.append((x,top))
    rh0,rh1=roofh
    # curved crown: quarter-ellipse profile at the right end (gable), flat ridge
    ridge=[(x1-30*(rh1/60),ybase-h1-rh1),(x0+8,ybase-h0-rh0)]
    curve=[(x1-30*(rh1/60)*(1-np.cos(a)) , ybase-h1-rh1*np.sin(a)) for a in np.linspace(0,np.pi/2,10)]
    roofp=[(x0,ybase-h0),(x1,ybase-h1)]+curve[1:]+ridge[1:]
    return fac,roofp
N_WIN=96
order=sorted(range(N_WIN),key=lambda i:((i*37)%N_WIN))
lit=set(order[:11])
def draw_windows(canvas,ws):
    for (bi,c,r,x,y,ww,wh) in ws:
        i=lit_score.index((bi,c,r,x,y,ww,wh))
        wm=poly([(x-ww/2,y),(x+ww/2,y),(x+ww/2,y+wh),(x-ww/2,y+wh)],1000+i,0.35)
        if i in lit:
            tex=paper((246,196,112),2000+i%5,5,0.02)
            glow=cv2.GaussianBlur((wm>0).astype(np.float32),(0,0),9*S)[...,None]
            canvas=np.clip(canvas+glow*np.array([30,18,0]),0,255)
        else:
            tex=paper((118,128,138),3000+i%5,5,0.02)
        canvas=lay(canvas,wm,tex,shadow=(-1,-1),soft=1.5,dark=0.35,edge=False)
        if r>0 and (c%3==1):
            bm=poly([(x-ww*0.8,y+wh+2),(x+ww*0.8,y+wh+2),(x+ww*0.8,y+wh+7),(x-ww*0.8,y+wh+7)],4000+i,0.3)
            canvas=lay(canvas,bm,paper((240,234,214),4100,3),shadow=(2,3),soft=3,dark=0.25)
    return canvas

blocks=[(180,560,560,150,190,(42,58),21),(520,1240,575,190,250,(58,80),22)]
lit_score=[]   # window order for the kinetic score
for bi,(x0,x1,yb,h0,h1,rh,sd) in enumerate(blocks):
    fac,roofp=block(x0,x1,yb,h0,h1,rh,sd)
    rm=poly(roofp,sd+50,0.7); canvas=lay(canvas,rm,paper((72,76,82),sd+60,7,0.03),shadow=(3,4),soft=6,dark=0.15)
    # dormers
    for k in range(6 if bi else 4):
        t=(k+0.7)/(6.6 if bi else 4.6); x=x0+(x1-x0)*t; top=yb-(h0+(h1-h0)*t)
        dm=poly([(x-9,top-rh[0]*0.45),(x+9,top-rh[0]*0.45),(x+9,top-rh[0]*0.15),(x-9,top-rh[0]*0.15)],sd+k,0.4)
        canvas=lay(canvas,dm,paper((222,224,226),sd+90+k,3),shadow=(1,2),soft=2,dark=0.2)
    fm=poly(fac,sd,0.8); canvas=lay(canvas,fm,paper((228,219,192),sd+70,5),shadow=(4,6),soft=8,dark=0.18)
    # windows grid, cut through the facade: behind each, tissue (unlit) or amber (lit)
    cols=9 if bi==0 else 15; rows=4
    for c in range(cols):
        t=(c+0.5)/cols; x=x0+(x1-x0)*t; top=yb-(h0+(h1-h0)*t); hh=(h0+(h1-h0)*t)
        ww=(x1-x0)/cols*0.38
        for r in range(rows):
            y=top+hh*(0.12+0.21*r); wh=hh*0.11
            lit_score.append((bi,c,r,x,y,ww,wh))
    canvas=draw_windows(canvas,[w for w in lit_score if w[0]==bi])
# --- hedge strip
hedge=[(0,580)]+[(x,572+6*np.sin(x/23.0)+rng.normal(0,2)) for x in range(0,1281,16)]+[(1280,600),(0,600)]
canvas=lay(canvas,poly(hedge,77,0.6),paper((92,104,72),78,8,0.05),shadow=(3,4),soft=5,dark=0.2)
# --- bare saplings: thin cut brown paper strips
tr=np.zeros((H,W),np.uint8)
for k,x in enumerate(range(120,1280,150)):
    xx=x+rng.integers(-20,20); cv2.line(tr,(xx*S,598*S),(xx*S,470*S),255,3*S)
    for b in range(5):
        a=rng.uniform(-1.1,1.1); yb=rng.uniform(480,540); L=rng.uniform(25,55)
        cv2.line(tr,(xx*S,int(yb*S)),(int((xx+L*np.sin(a))*S),int((yb-L*np.cos(a))*S)),255,2*S)
canvas=lay(canvas,tr,paper((96,84,70),88,6),shadow=(3,4),soft=4,dark=0.18,edge=False)
# --- far verge + road (grey card) + dashes
canvas=lay(canvas,poly([(0,596),(1280,596),(1280,612),(0,616)],5),paper((128,146,96),9,7),shadow=(2,3),soft=4)
road=poly([(0,614),(1280,610),(1280,672),(0,700)],6,0.5)
canvas=lay(canvas,road,paper((122,124,126),12,6,0.04),shadow=(3,5),soft=6,dark=0.15)
for k in range(0,1300,120):
    d=poly([(k,654-k*0.02),(k+56,653-k*0.02),(k+56,657-k*0.02),(k,658-k*0.02)],k,0.3)
    canvas=lay(canvas,d,paper((232,232,226),13,3),shadow=(1,1),soft=1,dark=0.1,edge=False)
# --- near grass verge (foreground plane, moves 1.0x)
canvas=lay(canvas,poly([(0,690),(1280,664),(1290,760),(-10,760)],8,1.4),paper((112,140,78),15,9,0.06),shadow=(0,-4),soft=7,dark=0.25)
# --- foreground lamp post silhouette (nearest plane, crosses frame during the track)
lp=np.zeros((H,W),np.uint8)
cv2.rectangle(lp,(1010*S,300*S),(1020*S,720*S),255,-1)
cv2.rectangle(lp,(1004*S,640*S),(1026*S,720*S),255,-1)
cv2.ellipse(lp,(990*S,300*S),(25*S,22*S),0,180,360,255,6*S)
cv2.ellipse(lp,(966*S,306*S),(20*S,8*S),0,0,360,255,-1)
canvas=lay(canvas,lp,paper((58,60,62),99,5),shadow=(6,8),soft=10,dark=0.22)
# overall paper-model light: soft vignette, very low contrast like the reference
vy,vx=np.mgrid[0:H,0:W]; v=1-0.10*(((vx/W-0.5)**2+(vy/H-0.45)**2)*2.2)
canvas=canvas*v[...,None]
out=cv2.resize(canvas,(1280,720),interpolation=cv2.INTER_AREA)
out=match(out,0.35)
img=Image.fromarray(out.astype(np.uint8)); img.save(OUT+'kf-2-picture.png')
captions(img,"« Six heures : on rentre, une fenêtre après l'autre. »","« Six heures : chaque fenêtre allumée est notée. »")
img.save(OUT+'kf-2.png')
print(len(lit_score))
