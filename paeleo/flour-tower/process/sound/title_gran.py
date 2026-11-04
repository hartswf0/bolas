import json, numpy as np
from gran import Bus, rng
T=dict(pourA=0.7,pourB=3.2,pack=3.45,flipA=4.15,flipB=4.85,penny=5.25,cuts=[6.0,6.75,7.5,8.25],wobble=8.7,fall=9.75,white=10.5,clear=11.4,hopA=13.2,rise=15.6)
D=json.load(open('lands.json')); b=Bus(18.8)
SC=[45,48,50,52,55,57,60,62,64,67,69,72,74,76,79]   # A minor pentatonic, low to high
# low bed: a grain cloud on A
b.pad(0.2,[33,40,45],T['fall']-.2,a=.035,att=1.5)
# the pour: hiss of unpitched grains + each cel landing is a pitched grain, rising as the tower grows
b.cloud(T['pourA'],T['pourB']-T['pourA']+.4,1400,None,.012,(.004,.015),.9,env=lambda u:min(1,u*6)*min(1,(1-u)*4))
for t,fill in D['lands']:
    m=SC[min(len(SC)-1,int(fill*len(SC)))]; b.grain(t,None,.006,.05,rng.uniform(-.6,.6)); b.grain(t,440*2**((m+12-69)/12),.05,.07,rng.uniform(-.6,.6))
# pack: a burst of grains + thump
b.thump(T['pack'],1.2,58); b.cloud(T['pack'],.12,3000,None,.02,(.003,.01),.6)
# flip: rising whoosh of grains, slam
b.cloud(T['flipA']-.05,.75,1800,None,.02,(.01,.04),1,env=lambda u:np.sin(np.pi*u)**2)
b.thump(T['flipB'],1.5,52); b.cloud(T['flipB'],.15,3500,None,.025,(.003,.012),.8)
# penny: a bell made of grains at its partials
b.cloud(T['penny'],1.6,500,[94,101,105],.03,(.01,.04),.3,env=lambda u:(1-u)**4,detune=.001)
# the turns: blade = bright noise grains, a pitched grain chord per turn, ticks as cels hit the floor
for k,c in enumerate(T['cuts']):
    b.cloud(c-.12,.14,4000,None,.018,(.002,.006),.4)
    b.thump(c,.9,62+k*4)
    b.pluck(c,57+k*3,.22,1.0); b.pluck(c,64+k*3,.14,1.0,.3)
    for j in range(D['cutn'][k]): b.grain(c+.3+rng.random()*.35,None,.004,.05,rng.uniform(-.8,.8))
# wobble: ticking that speeds up
t=T['wobble'];gap=.16
while t<T['fall']: b.grain(t,1800,.012,.12,rng.choice([-.4,.4])); t+=gap; gap*=.9
b.cloud(T['wobble'],T['fall']-T['wobble'],600,[69,70,71,72],.02,(.05,.1),.6,env=lambda u:u*u)
# the collapse: a huge falling cloud
b.thump(T['fall'],2.0,46); b.cloud(T['fall']-.1,.16,5000,None,.02,(.002,.006),.4)
b.cloud(T['fall'],2.6,9000,None,.016,(.004,.02),1,env=lambda u:(1-u)**1.5)
b.cloud(T['fall'],2.0,1500,[45,52,57,64],.02,(.03,.12),1,env=lambda u:(1-u)**2,glide=-.4)
# silence, then the sack: a soft grain melody
for i,m in enumerate([57,60,64,60,62,65,64,60]): b.pluck(T['clear']+.4+i*.55,m,.2,1.1,(-.3,.3)[i%2])
b.cloud(T['hopA'],.3,300,None,.02,(.005,.02),.2,env=lambda u:u); b.thump(T['hopA']+1.02,.9,70); b.cloud(T['hopA']+1.02,.3,1500,None,.015,(.003,.012),.6,env=lambda u:(1-u)**2)
# the cels rise into the title: each arrival is a grain of a C major chord, then the full chord as a cloud
CM=[60,64,67,72,76,79,84]
for t in D['rise']: b.grain(t,440*2**((rng.choice(CM)-69)/12),.07,.05,rng.uniform(-.7,.7))
b.pad(T['rise']+1.2,[48,55,60,64,67,72],2.2,a=.05,att=.3); b.thump(T['rise']+1.25,.7,48)
b.write('title_gran.wav')
print('ok')
