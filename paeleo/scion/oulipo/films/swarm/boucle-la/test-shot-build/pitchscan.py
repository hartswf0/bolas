import json, subprocess, numpy as np, sys
d=json.load(open('/home/user/bolas/tools/allways-forage/index.json'))
OUT='/home/user/bolas/paeleo/scion/oulipo/films/sources/boucle-la/test-shot/audio/'
res=[]
for e in d:
    a=e.get('audio') or {}
    if a.get('kind')!='speech' or 'clip' not in e['media']: continue
    p=e['media']['clip']
    raw=subprocess.run(['ffmpeg','-loglevel','error','-i',p,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    x=np.frombuffer(raw,np.int16).astype(np.float32)/32768
    if len(x)<16000: continue
    fr=640; f0s=[]; en=[]
    for i in range(0,len(x)-fr,fr//2):
        s=x[i:i+fr]; s=s-s.mean(); E=(s**2).mean(); en.append(E)
        if E<1e-4: f0s.append(0); continue
        ac=np.correlate(s,s,'full')[fr-1:]; lo,hi=16000//300,16000//70
        k=lo+np.argmax(ac[lo:hi]); f0s.append(16000/k if ac[k]>0.4*ac[0] else 0)
    f=np.array(f0s); v=f[f>0]
    if len(v)<20: continue
    res.append((np.median(v), len(v)/len(f), e['id'], e['year'], e['title']))
res.sort()
for r in res: print('%.0f %.2f %s %s %s'%r)
