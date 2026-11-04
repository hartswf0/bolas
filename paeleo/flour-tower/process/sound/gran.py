import numpy as np
SR=48000
rng=np.random.default_rng(21)
def mtof(m): return 440*2**((m-69)/12)
_win={}
def win(n):
    if n not in _win: _win[n]=np.hanning(n)
    return _win[n]
class Bus:
    def __init__(s,dur): s.N=int(dur*SR); s.L=np.zeros(s.N+SR); s.R=np.zeros(s.N+SR)
    def grain(s,t,f=None,d=.04,a=.2,pan=0.,noise=0.,glide=0.):
        n=max(16,int(d*SR)); i=int(t*SR)
        if i<0 or i+n>=len(s.L): return
        w=win(n)
        if f is None: x=rng.standard_normal(n)
        else:
            tt=np.arange(n)/SR; ff=f*(1+glide*tt/d); ph=2*np.pi*np.cumsum(ff)/SR+rng.uniform(0,6.28)
            x=np.sin(ph)*(1-noise)+(rng.standard_normal(n)*noise if noise else 0)
        x=x*w*a; s.L[i:i+n]+=x*(1-max(0,pan)); s.R[i:i+n]+=x*(1+min(0,pan))
    def cloud(s,t0,dur,rate,pitches=None,a=.05,d=(.02,.08),spread=.8,env=None,noise=0.,detune=.006,glide=0.):
        n=int(rate*dur)
        for k in range(n):
            u=rng.random(); t=t0+u*dur
            e=1 if env is None else env(u)
            if e<=0.002: continue
            f=None if pitches is None else mtof(rng.choice(pitches))*(1+rng.normal(0,detune))
            s.grain(t,f,rng.uniform(*d),a*e,rng.uniform(-spread,spread),noise,glide)
    def thump(s,t,a=1.,f0=60):  # low thump made of overlapped long grains
        for k in range(24): s.grain(t+k*.004,f0*(1-k*.012),.16+k*.004,a*.12*(1-k/24),0)
    def pluck(s,t,m,a=.3,dur=1.2,pan=0.):  # a note = a decaying stream of grains at one pitch
        s.cloud(t,dur,90,[m,m+12],a,(.03,.09),.15+abs(pan),env=lambda u:(1-u)**3,detune=.002)
    def pad(s,t,ms,dur,a=.03,att=.4):
        s.cloud(t,dur,140*len(ms)/3,ms,a,(.08,.22),.9,env=lambda u:min(1,u*dur/att)*min(1,(1-u)*dur/.6))
    def write(s,path,fade=.5):
        L,R=s.L[:s.N],s.R[:s.N]; mx=max(abs(L).max(),abs(R).max())+1e-9; L=L/mx*.8; R=R/mx*.8
        f=np.ones(s.N); k=int(fade*SR); f[-k:]=np.linspace(1,0,k)
        import wave
        pcm=(np.stack([L*f,R*f],1)*32767).astype('<i2')
        w=wave.open(path,'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes());w.close()
