import sys, os
sys.argv=['x']
import render
rng=[]
for r in os.environ['R'].split(';'):
    a,b=r.split(':'); rng+=list(range(int(a),int(b)))
prev=None; worst=0
for i in rng:
    img,pose,m=render.render(i)
    n=(m['nose_x'],m['nose_y'])
    j=None if prev is None or prev[2]!=i-1 else round(((n[0]-prev[0])**2+(n[1]-prev[1])**2)**.5,1)
    if j is not None: worst=max(worst,j)
    print(i, pose.get('f',pose['kind']), pose.get('head_raise',''), n, 'jump',j); prev=(n[0],n[1],i)
print('worst',worst)
