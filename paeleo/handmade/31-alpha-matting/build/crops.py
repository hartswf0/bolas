import sys, os, json
sys.argv=['x']
import render
from PIL import Image, ImageDraw
fr=[int(a) for a in os.environ['FR'].split(',')]
box=[int(v) for v in os.environ['BOX'].split(',')]
sc=float(os.environ.get('SC','1'))
ims=[]
for i in fr:
    img,pose,meas=render.render(i)
    im=Image.fromarray(img).crop(box); im=im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS)
    ImageDraw.Draw(im).text((4,4),'%d %.2fs %s %s'%(i,i/24,pose.get('f',''),pose['posture']),fill=(255,255,0)); ims.append(im)
cols=int(os.environ.get('COLS','4')); w,h=ims[0].size; rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(w*cols,h*rows))
for k,im in enumerate(ims): s.paste(im,((k%cols)*w,(k//cols)*h))
s.save(os.environ['OUT'])
