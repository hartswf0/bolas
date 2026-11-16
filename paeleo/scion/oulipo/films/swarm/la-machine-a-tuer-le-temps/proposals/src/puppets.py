# hand-cut articulated card puppets (FK chains), drawn as filled polygons
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import smooth
def R(p,a):
    c,s=math.cos(a),math.sin(a); return (p[0]*c-p[1]*s, p[0]*s+p[1]*c)
class Part:
    def __init__(s,poly,pivot=(0,0),angle=0,kids=(),closed_smooth=True,holes=()):
        s.poly=poly; s.pivot=pivot; s.angle=math.radians(angle); s.kids=list(kids); s.sm=closed_smooth; s.holes=holes
def csmooth(pts,n=6):
    P=pts[-1:]+pts+pts[:2]; out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        for t in np.linspace(0,1,n,endpoint=False):
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t**3) for j in range(2)))
    return out
def draw(d,part,origin,ang,scale,fill=255,hole=0):
    o=origin; a=ang+part.angle
    pts=csmooth(part.poly) if part.sm else part.poly
    d.polygon([(o[0]+scale*q[0],o[1]+scale*q[1]) for q in (R(p,a) for p in pts)],fill=fill)
    for h in part.holes:
        d.polygon([(o[0]+scale*q[0],o[1]+scale*q[1]) for q in (R(p,a) for p in csmooth(h))],fill=hole)
    for k in part.kids:
        pv=R(k.pivot,a); draw(d,k,(o[0]+scale*pv[0],o[1]+scale*pv[1]),a,scale,fill,hole)
def limb(L,w0,w1): return [(-w0/2,0),(w0/2,0),(w1/2,L),(-w1/2,L)]
def shoe(L,w,toe=34,fwd=1): return [(-w/2,0),(w/2,0),(w/2+2,L-10),(fwd*toe,L-6),(fwd*toe+2,L),(-w/2-4,L)]
def woman():
    head=Part([(8,0),(12,-20),(22,-40),(20,-62),(6,-77),(-14,-75),(-26,-62),(-28,-50),(-36,-40),(-28,-36),(-30,-30),(-26,-26),(-27,-20),(-18,-15),(-8,-4),(-6,0)],(-4,-160),-4)
    knot=Part([(-6,0),(6,0),(8,-10),(0,-16),(-8,-10)],(0,0),0)
    head.kids.append(Part([(-7,-74),(7,-76),(9,-86),(0,-92),(-9,-86)],(0,0),0))
    fore=Part(limb(64,19,16)+[(-10,64),(-12,76),(6,80),(10,64)][::-1][:0],(0,70),-78,closed_smooth=True)
    fore.poly=[(-9.5,0),(9.5,0),(9,58),(14,64),(10,78),(-4,80),(-10,66)]
    upper=Part(limb(70,24,20),(6,-146),-22,[fore])
    back_up=Part(limb(70,22,18),(-14,-146),-10,[Part([(-9,0),(9,0),(8,58),(4,72),(-8,70),(-9,58)],(0,70),-70)])
    box=Part([(0,0),(124,-10),(128,76),(4,86)],(24,-154),0,closed_smooth=False,holes=())
    torso=Part([(-28,0),(-24,-80),(-34,-138),(-20,-162),(12,-164),(34,-140),(32,-90),(24,-40),(30,0)],(0,0),-4,[back_up,head,upper,box])
    def leg(a,ka,fwd):
        shin=Part(limb(98,26,19),(0,110),ka,[Part(shoe(20,20,30,fwd),(0,96),-ka-a)])
        return Part(limb(112,36,26),(0,0),a,[shin])
    root=Part([(-20,-2),(20,-2),(16,8),(-16,8)],(0,0),0,[leg(14,0,1),leg(-18,6,1),torso])
    return root
def conductor():
    head=Part([(-8,0),(-12,-22),(-22,-42),(-24,-56),(-30,-70),(-22,-84),(14,-88),(28,-76),(23,-66),(46,-63),(46,-58),(19,-57),(21,-50),(29,-40),(21,-35),(23,-29),(19,-23),(10,-15),(5,0)],(2,-168),3)
    watch_hand=Part([(-8,0),(8,0),(9,52),(14,60),(8,72),(-6,70),(-9,56)],(0,74),-128)
    upper=Part(limb(76,26,22),(4,-150),-6,[watch_hand])
    back=Part(limb(78,24,20),(-16,-150),12,[Part([(-10,0),(10,0),(9,64),(4,78),(-8,74),(-10,60)],(0,76),6)])
    coat=Part([(-36,-142),(-30,-60),(-46,64),(44,68),(32,-60),(30,-142),(14,-170),(-22,-170)],(0,0),0,[back,head,upper])
    def leg(a,ka):
        shin=Part(limb(118,28,22),(0,118),ka,[Part(shoe(20,22,32,1),(0,114),-ka-a)])
        return Part(limb(120,34,28),(0,0),a,[shin])
    return Part([(-20,0),(20,0),(20,10),(-20,10)],(0,0),0,[leg(6,0),leg(-8,4),coat])
def render(fig,size,origin,scale,ss=3):
    W,H=size; m=Image.new('L',(W*ss,H*ss),0); d=ImageDraw.Draw(m)
    draw(d,fig,(origin[0]*ss,origin[1]*ss),0,scale*ss)
    return m.resize((W,H),Image.LANCZOS)
