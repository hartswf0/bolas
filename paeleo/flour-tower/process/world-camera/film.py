import json, math
FPS=30; OW,OH=1920,1080
T=json.load(open('traces.json'))
N={'02':'02-reiniger','06':'06-whitney','07':'07-foldes','08':'08-sutherland','14':'14-pose2pose','41':'41-soft-body'}
MAP={'02':(.5288,.2942,.855,.518),'07':(.499,.2322,.6396,.3142),'08':(.5,.2405,.7589,.3211),'14':(.499,.2222,.803,.395),'41':(.5,.2267,.824,.402)}
def tr(f,t,key):
    tr_=T[N[f]]; u=max(0,min(767,t*24)); i=int(u); j=min(767,i+1); a=u-i
    def g(r):
        if key=='x': return r.get('x',r.get('sackX'))
        if key=='top': return r.get('top',r.get('sackTop'))
        return r[key]
    return g(tr_[i])*(1-a)+g(tr_[j])*a
def mapping(f,t):
    if f=='06':
        cx,cw=tr(f,t,'camX'),tr(f,t,'camW'); return (.5-cx/cw,1/cw,.778,1.32/cw)
    return MAP[f]
def crop(f,t,cx,cy,wm):
    fx0,kx,fy0,ky=mapping(f,t); hm=wm*9/16
    w=wm*kx; h=hm*ky
    s=min(1,1/w,1/h); w*=s; h*=s
    x=fx0+kx*cx; y=fy0-ky*cy
    x=min(max(x,w/2),1-w/2); y=min(max(y,h/2),1-h/2)
    return (round(x,5),round(y,5),round(w,5),round(h,5))
def ease(a): a=max(0,min(1,a)); return a*a*(3-2*a)
def lerp(a,b,u): return a+(b-a)*u
# ---- shots: (out_dur, t0, t1, mats, cam, extra) ----
# cam: ('path',(cx,cy,wm),(cx,cy,wm))  or ('lock',dy,wm0,wm1)  (follow current material's sack)
# mats: list of (fraction_start, material) ; 'xfade':seconds for dissolves between materials
SH=[
 dict(d=2.6,t0=21.5,t1=22.6,mats=[(0,'41')],cam=('path',(0.78,0.72,1.75),(0.80,0.80,1.30)),title=True),
 dict(d=1.7,t0=0.25,t1=1.95,mats=[(0,'02')],cam=('path',(-0.25,0.80,2.80),(-0.30,0.76,2.55))),
 dict(d=0.9,t0=3.65,t1=4.55,mats=[(0,'14')],cam=('path',(-1.40,0.44,1.80),(-1.42,0.44,1.62))),
 dict(d=0.75,t0=6.15,t1=6.90,mats=[(0,'41')],cam=('path',(0.78,0.64,1.80),(0.78,0.62,1.60))),
 dict(d=1.35,t0=6.45,t1=7.80,mats=[(0,'14')],cam=('path',(-1.42,0.47,1.90),(-1.45,0.47,1.50))),
 dict(d=0.85,t0=8.25,t1=9.10,mats=[(0,'02')],cam=('path',(-1.36,0.47,1.80),(-1.34,0.45,1.62))),
 dict(d=4.25,t0=9.10,t1=14.35,mats=[(0,'06'),(1/6,'08'),(2/6,'07'),(3/6,'41'),(4/6,'14'),(5/6,'02')],cam=('lock',0.14,1.85,1.85,0.10)),
 dict(d=1.75,t0=14.30,t1=16.05,mats=[(0,'02')],cam=('path',(0.47,0.62,1.95),(0.50,0.60,1.65))),
 dict(d=1.10,t0=17.65,t1=18.75,mats=[(0,'08')],cam=('path',(0.45,0.60,1.85),(0.47,0.58,1.70)),shake=[18.0]),
 dict(d=0.75,t0=20.70,t1=21.45,mats=[(0,'07')],cam=('path',(0.60,0.66,2.05),(0.65,0.66,1.95)),shake=[21.0]),
 dict(d=3.00,t0=21.45,t1=22.65,strobe=['41','02','07','14','06','08'],cam=('locktop',-0.42,2.05,1.80,0.0)),
 dict(d=0.75,t0=22.65,t1=23.40,mats=[(0,'14')],cam=('path',(0.80,0.56,1.95),(0.80,0.55,1.85)),shake=[23.0]),
 dict(d=3.45,t0=24.45,t1=28.60,mats=[(0,'07'),(1/6,'06'),(2/6,'41'),(3/6,'08'),(4/6,'02'),(5/6,'14')],xfade=0.25,cam=('path',(0.80,0.64,2.10),(0.80,0.64,1.90))),
 dict(d=2.10,t0=29.55,t1=31.65,mats=[(0,'02')],cam=('path',(0.80,0.85,1.60),(0.80,0.88,1.35))),
 dict(d=2.40,t0=31.90,t1=31.90,mats=[(0,'41'),(1/6,'06'),(2/6,'07'),(3/6,'08'),(4/6,'14'),(5/6,'02')],xfade=0.18,cam=('path',(0.80,0.60,1.85),(0.80,0.58,1.95))),
 dict(d=2.20,t0=31.95,t1=31.95,mats=[(0,'02')],cam=('path',(0.78,0.56,1.95),(0.78,0.56,2.05)),endtitle=True),
]
def frames():
    out=[]; o0=0.0; k=0
    for si,s in enumerate(SH):
        n=round(s['d']*FPS)
        for j in range(n):
            u=j/max(1,n-1); t=lerp(s['t0'],s['t1'],j/n)
            layers=[]
            if 'strobe' in s: mats=[(1.0,s['strobe'][(j//5)%len(s['strobe'])])]
            else:
                ms=s['mats']; idx=max(i for i,(fs,_) in enumerate(ms) if fs<=j/n+1e-9)
                mats=[(1.0,ms[idx][1])]
                xf=s.get('xfade',0)
                if xf and idx+1<len(ms):
                    tnext=ms[idx+1][0]*s['d']; tnow=j/FPS
                    if tnow>tnext-xf: a=ease((tnow-(tnext-xf))/xf); mats=[(1-a,ms[idx][1]),(a,ms[idx+1][1])]
            for a,f in mats:
                cam=s['cam']
                if cam[0]=='path': cx,cy,wm=[lerp(p,q,ease(u)) for p,q in zip(cam[1],cam[2])]
                else:
                    mode,dy,w0,w1,lead=cam; wm=lerp(w0,w1,ease(u))
                    cx=tr(f,t,'x')+lead
                    cy=tr(f,t,'top')+dy if mode=='locktop' else tr(f,t,'top')*0.5+dy
                for st in s.get('shake',[]):
                    if st<=t<st+0.35:
                        e=math.exp(-(t-st)*12); cx+=0.025*e*math.sin(t*90); cy+=0.02*e*math.cos(t*77)
                layers.append((a,f,round(t,4),crop(f,t,cx,cy,wm)))
            out.append(dict(i=k,si=si,o=k/FPS,t=t,layers=layers,title=s.get('title') and j>=24,endtitle=s.get('endtitle'),j=j,n=n))
            k+=1
    return out
if __name__=='__main__':
    F=frames(); jobs={}
    for fr in F:
        for a,f,t,c in fr['layers']: jobs.setdefault(f,set()).add((t,)+c)
    J={f:[list(x) for x in sorted(v)] for f,v in jobs.items()}
    json.dump(J,open('jobs.json','w')); json.dump(F,open('plan.json','w'))
    print(len(F),'frames',round(len(F)/FPS,2),'s',{f:len(v) for f,v in J.items()})
    for f,v in J.items(): print(f,'min crop w',min(x[3] for x in v))
