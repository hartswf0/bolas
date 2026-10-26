import sys, time, os
sys.argv=['x']
import render
from PIL import Image
fr=[int(a) for a in os.environ['FR'].split(',')]
ims=[]
for i in fr:
    t0=time.time(); img,pose,meas=render.render(i); print(i, round(time.time()-t0,2), pose.get('posture'), meas)
    ims.append(Image.fromarray(img))
n=len(ims); cols=2; rows=(n+1)//2
sh=Image.new('RGB',(640*cols,360*rows))
for k,im in enumerate(ims): sh.paste(im.resize((640,360)),((k%cols)*640,(k//cols)*360))
sh.save('/tmp/claude-0/-home-user-bolas/3bf170de-e051-51c1-84f3-a27a68c230c5/scratchpad/test.jpg')
if len(ims)==1: ims[0].save('/tmp/claude-0/-home-user-bolas/3bf170de-e051-51c1-84f3-a27a68c230c5/scratchpad/one.jpg')
