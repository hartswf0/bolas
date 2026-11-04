import numpy as np, wave, json
from film import SH, FPS
SR=48000; rng=np.random.default_rng(11)
starts=[];o=0
for s in SH: starts.append(o); o+=round(s['d']*FPS)/FPS
TOT=o; N=int(TOT*SR)+SR; L=np.zeros(N); R=np.zeros(N)
def add(t,x,g=1.,pan=0.):
    i=int(t*SR); n=min(len(x),N-i)
    if n>0 and i>=0: L[i:i+n]+=g*x[:n]*(1-max(0,pan)); R[i:i+n]+=g*x[:n]*(1+min(0,pan))
def lp(x,k):
    y=np.empty_like(x);s=0.
    for i in range(len(x)): s+=k*(x[i]-s); y[i]=s
    return y
def mtof(m): return 440*2**((m-69)/12)
def ks(m,dur=1.5,damp=.497):
    f=mtof(m);p=max(2,int(SR/f));n=int(dur*SR);y=np.zeros(n+p);y[:p]=rng.uniform(-1,1,p)
    for i in range(p,n+p): y[i]=damp*(y[i-p]+y[i-p+1])
    return y[p:]
def pad(ms,dur,g=.12,att=.5):
    n=int(dur*SR);t=np.arange(n)/SR;x=np.zeros(n)
    for m in ms:
        for d in (-.08,.08): x+=np.sin(2*np.pi*mtof(m)*(1+d/100)*t)+.25*np.sin(4*np.pi*mtof(m)*t)
    return x*np.minimum(1,t/att)*np.clip((dur-t)/.5,0,1)*g/len(ms)
def kick(g=1): n=int(.4*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*(100*np.exp(-t*16)+42)*t)*np.exp(-t/.13)*g
def bell(m,dur=2.5):
    n=int(dur*SR);t=np.arange(n)/SR;f=mtof(m)
    return sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t/(dur*d)) for r,a,d in [(1,.6,.5),(2.76,.3,.25),(5.4,.15,.12)])
def noise(d,k=.3): n=int(d*SR);x=rng.standard_normal(n);return x-lp(x,k)
def cut(): n=int(.4*SR);t=np.arange(n)/SR;return noise(.4,.2)*np.exp(-t/.025)*.7+np.sin(2*np.pi*(95-40*t)*t)*np.exp(-t/.1)
def thud(): n=int(.6*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*(65-25*t)*t)*np.exp(-t/.16)*1.3+lp(noise(.6,.05),.3)*np.exp(-t/.1)*.8
def rumble(d): n=int(d*SR);t=np.arange(n)/SR;return lp(rng.standard_normal(n),.015)*4*np.exp(-t/(d*.4))
def sift(d): t=np.arange(int(d*SR))/SR;return lp(noise(d,.08),.5)*np.sin(np.pi*t/d)**2*.35
def whoosh(d): t=np.arange(int(d*SR))/SR;return lp(noise(d,.15),.6)*np.sin(np.pi*t/d)**2*.6

import sys; sys.path.insert(0,'/home/claude/title')
from gran import Bus
GB=Bus(TOT+1)
def _render(fn):
    import numpy as _np
    b=Bus(4.0); fn(b); x=b.L[:b.N]; return x
def ks(m,dur=1.5,damp=.497): return _render(lambda b:b.pluck(0,m,.3,dur))
def pad(ms,dur,g=.12,att=.5):
    b=Bus(dur+.1); b.pad(0,ms,dur,a=g*.35,att=att); return b.L[:int(dur*SR)]
def kick(g=1): b=Bus(.5); b.thump(0,g,55); return b.L[:int(.45*SR)]
def bell(m,dur=2.5): b=Bus(dur+.1); b.cloud(0,dur,500,[m,m+16,m+29],.03,(.01,.04),.2,env=lambda u:(1-u)**4,detune=.001); return b.L[:int(dur*SR)]
def cut(): b=Bus(.5); b.cloud(0,.12,4000,None,.02,(.002,.006),.2); b.thump(0,.8,64); return b.L[:int(.4*SR)]
def thud(): b=Bus(.7); b.thump(0,1.3,48); b.cloud(0,.3,1500,None,.02,(.003,.012),.4,env=lambda u:(1-u)**2); return b.L[:int(.6*SR)]
def rumble(d): b=Bus(d+.1); b.cloud(0,d,4000,None,.02,(.005,.03),.5,env=lambda u:(1-u)**1.5); b.cloud(0,d,600,[33,40],.03,(.08,.2),.5,env=lambda u:(1-u)); return b.L[:int(d*SR)]
def sift(d): b=Bus(d+.1); b.cloud(0,d,2500,None,.012,(.003,.01),.6,env=lambda u:__import__('math').sin(3.1416*u)**2); return b.L[:int(d*SR)]
def whoosh(d): b=Bus(d+.1); b.cloud(0,d,1500,None,.02,(.01,.04),.6,env=lambda u:__import__('math').sin(3.1416*u)**2); return b.L[:int(d*SR)]
EV=[(1.0,cut,1),(4.0,cut,.8),(18.0,cut,1),(21.0,cut,1),(21.02,lambda:rumble(1.4),.7),(22.4,lambda:bell(91,1.6),.32),(23.0,thud,1),(31.15,lambda:whoosh(.7),.8)]
for k,s in enumerate(SH):
    if s['t1']<=s['t0']: continue
    for te,fn,g in EV:
        if s['t0']<=te<s['t1']:
            sp=(s['t1']-s['t0'])/s['d']; ot=starts[k]+(te-s['t0'])/sp
            x=fn()
            if sp<0.8: x=np.interp(np.arange(0,len(x),sp),np.arange(len(x)),x)  # slowed sound for slow motion
            add(ot,x,g)
st=starts
# 0 cold open: deep swell + slow heartbeat
add(0,pad([33,40,45],2.7,.22,1.2)); [add(t,kick(.55)) for t in (.35,1.25,2.15)]
n=int(2.6*SR);tt=np.arange(n)/SR;add(0,sum(np.sin(2*np.pi*mtof(m)*tt) for m in (81,88))*np.minimum(1,tt/2)*.025)
# 1-5 act one: sparse plucks in A minor, pad
a,b=st[1],st[6]; add(a,pad([45,52,60],b-a,.09,1))
mel=[69,72,76,72,67,69,64,67,69,71]
for i,t in enumerate(np.arange(a+.15,b,0.55)): add(t,ks(mel[i%len(mel)]-12,1.4),.33,pan=(-.3,.3)[i%2])
add(st[4],ks(81,1.6),.25); add(st[4]+.3,ks(84,1.6),.2)        # notice: high answer
add(st[5],ks(45,1.4),.5)                                         # decision crouch: low note
# 6 the walk: one rising note per new body + soft pulse
sc=[57,60,62,64,67,69]; seg=SH[6]['d']/6
add(st[6],pad([45,52,57,60],SH[6]['d'],.08,.6))
for j in range(6):
    t=st[6]+j*seg; add(t,ks(sc[j]+12,1.3),.5); add(t,ks(sc[j],1.3),.28); add(t,kick(.35)); add(t+seg/2,kick(.2))
# 7-9 prop, brace, collapse: low drone, tension
add(st[7],pad([41,48,53],st[10]-st[7],.16,.4))
for t in np.arange(st[7],st[10],0.42): add(t,ks(41,.8),.18)
# 10 strobe slow-mo: heartbeat + rising shimmer
for t in np.arange(st[10]+.1,st[11],0.5): add(t,kick(.5))
n=int((st[11]-st[10])*SR);tt=np.arange(n)/SR
add(st[10],sum(np.sin(2*np.pi*mtof(m)*tt*(1+tt*.025)) for m in (81,88,93))*np.minimum(1,tt/1.2)*.03)
# 11-12 land + gather: warm C major
add(st[11],pad([48,55,60,64],st[13]-st[11],.12,.3))
arp=[60,64,67,72,76,79,84,79]
for i,t in enumerate(np.arange(st[12],st[13],0.25)): add(t,ks(arp[i%8],1.2),.28,pan=(i%3-1)*.4)
add(st[12],sift(SH[12]['d']),1)
# 13 knife hover: hush, one held high tone
n=int((st[14]-st[13])*SR);tt=np.arange(n)/SR;add(st[13],np.sin(2*np.pi*mtof(88)*tt)*np.minimum(1,tt/.6)*np.clip((len(tt)/SR-tt)/.3,0,1)*.035)
# 14-15 resolve
add(st[14],pad([36,48,55,60,64,67],TOT-st[14],.2,.4)); add(st[14],bell(84,3),.3); add(st[14],ks(48,3),.5); add(st[14],kick(.6))
add(st[15],bell(79,2.2),.22)
mx=max(np.abs(L).max(),np.abs(R).max()); L/=mx/.8; R/=mx/.8
n=int(TOT*SR); f=np.ones(n); f[-int(.6*SR):]=np.linspace(1,0,int(.6*SR))
pcm=(np.stack([L[:n]*f,R[:n]*f],1)*32767).astype('<i2')
with wave.open('score_gran.wav','wb') as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print('total',round(TOT,2),[round(x,2) for x in starts])
