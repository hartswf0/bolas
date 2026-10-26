import sys, os
sys.argv=['x']
import render
from PIL import Image
spec=os.environ['Z'].split(';')   # i:x0,y0,x1,y1
ims=[]
for s in spec:
    i,b=s.split(':'); x0,y0,x1,y1=[int(v) for v in b.split(',')]
    img,pose,meas=render.render(int(i))
    im=Image.fromarray(img).crop((x0,y0,x1,y1)); sc=min(2.0, 900/im.width)
    ims.append(im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS))
Wt=max(i.width for i in ims); Ht=sum(i.height for i in ims)
sh=Image.new('RGB',(Wt,Ht)); y=0
for im in ims: sh.paste(im,(0,y)); y+=im.height
sh.save('/tmp/claude-0/-home-user-bolas/3bf170de-e051-51c1-84f3-a27a68c230c5/scratchpad/zoom.jpg')
