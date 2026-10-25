import json,sys
from PIL import Image,ImageDraw
cat=sys.argv[1]; n=int(sys.argv[2]); skip=int(sys.argv[3]) if len(sys.argv)>3 else 0
L=open('/home/user/hartswf0/quickdraw/%s.part'%cat).read().split('\n')[:-1]
rows=[]
for l in L:
    try: d=json.loads(l)
    except: continue
    if d.get('recognized'): rows.append(d)
rows=rows[skip:skip+n]
W=160;cols=8
im=Image.new('RGB',(W*cols,W*((len(rows)+cols-1)//cols)),'white');dr=ImageDraw.Draw(im)
for k,d in enumerate(rows):
    ox,oy=(k%cols)*W,(k//cols)*W
    for s in d['drawing']:
        pts=[(ox+10+x*140/255,oy+10+y*140/255) for x,y in zip(s[0],s[1])]
        if len(pts)>1: dr.line(pts,fill='black',width=2)
    dr.text((ox+3,oy+2),str(k+skip),fill='red')
im.save('build/cache/qd_%s.png'%cat)
print(len(rows))
