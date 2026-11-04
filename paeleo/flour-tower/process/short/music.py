import numpy as np, wave
from shots import S, FPS
SR=48000; rng=np.random.default_rng(3)
# shot start times in output
starts=[];o=0
for sh in S: starts.append(o); o+=round(sh[2]*FPS)/FPS
TOTAL=o; N=int(TOTAL*SR)+SR
L=np.zeros(N); R=np.zeros(N)
def add(t,x,g=1.0,pan=0.0):
    i=int(t*SR); n=min(len(x),N-i)
    if n<=0: return
    L[i:i+n]+=g*x[:n]*(1-max(0,pan)); R[i:i+n]+=g*x[:n]*(1+min(0,pan))
def lp(x,k):
    y=np.empty_like(x);s=0.
    for i in range(len(x)): s+=k*(x[i]-s); y[i]=s
    return y
def mtof(m): return 440*2**((m-69)/12)
def pluck(m,dur=1.6,bright=.5):
    f=mtof(m); p=int(SR/f); n=int(dur*SR); buf=rng.uniform(-1,1,p); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%p]; buf[i%p]=bright*buf[i%p]+(1-bright)*0.5*(buf[i%p]+buf[(i+1)%p])*0.996/ (1 if bright<1 else 1)
    return out*np.exp(-np.arange(n)/SR/dur*2)
def kspluck(m,dur=1.5):
    f=mtof(m); p=max(2,int(SR/f)); n=int(dur*SR); y=np.zeros(n+p); y[:p]=rng.uniform(-1,1,p)
    for i in range(p,n+p): y[i]=0.497*(y[i-p]+y[i-p+1])
    return y[p:]
def pad(ms,dur,g=.12):
    n=int(dur*SR); t=np.arange(n)/SR; x=np.zeros(n)
    for m in ms:
        for d in (-.06,.06): x+=np.sin(2*np.pi*mtof(m)*(1+d/100)*t)+.3*np.sin(4*np.pi*mtof(m)*t)
    env=np.minimum(1,t/.4)*np.minimum(1,(dur-t)/.5).clip(0,1)
    return x*env*g/len(ms)
def kick(): n=int(.35*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*(110*np.exp(-t*18)+45)*t)*np.exp(-t/.12)
def bell(m,dur=2.5):
    n=int(dur*SR);t=np.arange(n)/SR;f=mtof(m)
    return sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t/(dur*d)) for r,a,d in [(1,.6,.5),(2.76,.3,.25),(5.4,.15,.12)])
def noise(dur,k=.3): n=int(dur*SR);x=rng.standard_normal(n);return x-lp(x,k)
def cut():
    n=int(.35*SR);t=np.arange(n)/SR;e=np.exp(-t/.03)
    return (noise(.35,.2)*e*.6+np.sin(2*np.pi*(95-40*t)*t)*np.exp(-t/.09))
def thud(): n=int(.5*SR);t=np.arange(n)/SR;return np.sin(2*np.pi*(70-25*t)*t)*np.exp(-t/.15)*1.2
def sift(d): t=np.arange(int(d*SR))/SR;return lp(noise(d,.08),.5)*np.sin(np.pi*t/d)**2*.35
# --- map story events into each shot ---
EV=[(1.0,'cut'),(4.0,'cut'),(18.0,'cut'),(21.0,'cut'),(22.4,'clink'),(23.0,'thud'),(31.15,'whoosh')]
for k,(film,t0,d,s,crop) in enumerate(S):
    if film=='GRID': continue
    t1=t0+d*s
    for te,kind in EV:
        if t0<=te<t1:
            ot=starts[k]+(te-t0)/s
            if kind=='cut': add(ot,cut(),.9)
            if kind=='clink': add(ot,bell(91 if s==1 else 84,1.4),.35)
            if kind=='thud': add(ot,thud(),1)
            if kind=='whoosh': add(ot,lp(noise(.6,.15),.6)*np.sin(np.pi*np.arange(int(.6*SR))/SR/.6)**2,.5)
    if film in('07','41') and t0>=24 and t0<29: add(starts[k],sift(d),1)
# --- music ---
st=dict(enumerate(starts))
# cold open: low pad + slow-mo heartbeat
add(0,pad([45,52,57],2.6,.18)); add(.2,kick(),.5); add(1.2,kick(),.5)
# act 1 (shots 1-7): sparse minor plucks, A minor
a1,a1e=st[1],st[8]
notes=[69,72,76,72,67,69,64,67]
for i,t in enumerate(np.arange(a1,a1e,0.6)): add(t,kspluck(notes[i%len(notes)]-12,1.4),.35,pan=-.3 if i%2 else .3)
add(a1,pad([45,52,60],a1e-a1,.10))
# approach (shots 8-13): one rising note per body change + pulse
scale=[57,60,62,64,67,69]
for j in range(6):
    t=st[8+j]; add(t,kspluck(scale[j]+12,1.2),.55); add(t,kspluck(scale[j],1.2),.3); add(t,kick(),.35)
    add(t+.3,kick(),.2)
add(st[8],pad([45,52,57,60],st[14]-st[8],.08))
# prop + brace (14,15): low drone tension
add(st[14],pad([41,48,53],st[16]-st[14]+.2,.16))
for t in np.arange(st[14],st[16],0.4): add(t,kspluck(41,0.8),.2)
# collapse (16): drop out; strobe (17): shimmer rising + heartbeat
for t in np.arange(st[17],st[18],0.4): add(t,kick(),.45)
n=int((st[18]-st[17])*SR);tt=np.arange(n)/SR
sh=sum(np.sin(2*np.pi*mtof(m)*tt*(1+tt*.02)) for m in (81,88,93))*np.minimum(1,tt/1.5)*.03
add(st[17],sh)
# landing (18) + gather (19,20): warm C major arpeggio rising
add(st[18],pad([48,55,60,64],st[21]-st[18],.12))
arp=[60,64,67,72,76,79,84,88]
for i,t in enumerate(np.arange(st[19],st[21],0.25)): add(t,kspluck(arp[i%len(arp)],1.2),.3,pan=(i%3-1)*.4)
# knife hover (21): hush, high held tone
n=int((st[22]-st[21])*SR);tt=np.arange(n)/SR;add(st[21],np.sin(2*np.pi*mtof(88)*tt)*np.minimum(1,tt/.5)*np.minimum(1,(len(tt)/SR-tt)/.3)*.04)
# reveal (22): full resolve chord + bell
add(st[22],pad([36,48,55,60,64,67],3.4,.2)); add(st[22],bell(84,3),.3); add(st[22],kspluck(48,3),.5); add(st[22],kick(),.6)
mx=max(np.abs(L).max(),np.abs(R).max()); L/=mx/.8; R/=mx/.8
L=L[:int(TOTAL*SR)];R=R[:int(TOTAL*SR)]
pcm=(np.stack([L,R],1)*32767).astype('<i2')
with wave.open('music.wav','wb') as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print('total',TOTAL,[round(x,2) for x in starts])
