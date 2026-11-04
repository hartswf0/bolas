import numpy as np, wave
SR=48000
rng=np.random.default_rng(7)
def env(n,a,d): t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def lp(x,k):  # one-pole lowpass, k in (0,1)
    y=np.empty_like(x);s=0.0
    for i in range(len(x)): s+=k*(x[i]-s); y[i]=s
    return y
def cut():
    n=int(.35*SR); t=np.arange(n)/SR
    hiss=rng.standard_normal(n)*env(n,.001,.03)*.5
    thud=np.sin(2*np.pi*(90-40*t)*t)*env(n,.002,.09)
    return hiss-lp(hiss,.2)+thud*.9
def clink():
    n=int(.9*SR); t=np.arange(n)/SR
    return sum(a*np.sin(2*np.pi*f*t) for f,a in [(2390,.5),(3710,.3),(5230,.15)])*env(n,.001,.18)
def thud(): 
    n=int(.5*SR);t=np.arange(n)/SR; return (np.sin(2*np.pi*(70-25*t)*t)*env(n,.003,.14)+lp(rng.standard_normal(n),.05)*env(n,.002,.12)*2)
def sift(dur):
    n=int(dur*SR);t=np.arange(n)/SR; x=rng.standard_normal(n); x=x-lp(x,.08); x=lp(x,.5)
    return x*np.sin(np.pi*t/dur)**2*.25
def rumble(dur):
    n=int(dur*SR);x=lp(rng.standard_normal(n),.02)*3;return x*env(n,.02,.35)
def whoosh(dur):
    n=int(dur*SR);t=np.arange(n)/SR;x=rng.standard_normal(n);x=x-lp(x,.15);return x*np.sin(np.pi*t/dur)**2*.18
def add(buf,t,x,g=1.0):
    i=int(t*SR); buf[i:i+len(x)]+=g*x[:max(0,len(buf)-i)]
film=np.zeros(int(32*SR))
for t,g in [(1.0,1),(4.0,.8),(18.0,.9),(21.0,1)]: add(film,t,cut(),g)
add(film,21.05,rumble(1.2),.8); add(film,22.4,clink(),.5); add(film,23.0,thud(),.9)
add(film,24.5,sift(4.0),1); add(film,31.15,whoosh(.6),1)
OPEN,STORY,CARD,END=6,9,4,10
total=OPEN+STORY+6*(CARD+32)+END
buf=np.zeros(int(total*SR))
room=lp(rng.standard_normal(len(buf)),.03)*.004; buf+=room
t0=OPEN+STORY
for k in range(6):
    add(buf,t0+CARD,film); t0+=CARD+32
buf=buf/np.max(np.abs(buf))*0.7
st=np.stack([buf,buf],1); pcm=(st*32767).astype('<i2')
with wave.open('score.wav','wb') as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print('total',total)
