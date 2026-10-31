import sys, os
sys.argv=['x']
import render
rng=[]
for r in os.environ['R'].split(';'):
    a,b=r.split(':'); rng+=list(range(int(a),int(b)))
prev=None; worst=0
for i in rng:
    img,pose,m=render.render(i)
    n=(m['head_x'],m['head_y'])
    j=None if prev is None or prev[2]!=i-1 or n[0] is None else round(((n[0]-prev[0])**2+(n[1]-prev[1])**2)**.5,1)
    if j is not None: worst=max(worst,j)
    print(i, pose.get('f',pose['kind']), round(pose.get('head_raise',0),2), n, 'jump',j, flush=True); prev=(n[0],n[1],i)
print('worst',worst)
