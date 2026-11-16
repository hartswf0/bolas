import time, numpy as np, sys
from PIL import Image
import paper as P, mouth as M
t0=time.time(); m=M.Mouth(); print("lib",time.time()-t0)
bg=np.full((P.CH,P.CW,3),255,np.float32)
tiles=[]
for pid in M.POSE_IDS:
    t1=time.time(); img=m.render(pid, M.POSES[pid]["jaw"], bg)
    im=Image.fromarray(img.clip(0,255).astype(np.uint8)).resize((960,540),Image.LANCZOS)
    if pid=="A": im.save(sys.argv[1]+"/pose_A.png")
    if pid=="rest": im.save(sys.argv[1]+"/pose_rest.png")
    tiles.append((pid,im)); print(pid,time.time()-t1)
sheet=Image.new("RGB",(5*480,2*270),"white")
from PIL import ImageDraw
d=ImageDraw.Draw(sheet)
for k,(pid,im) in enumerate(tiles):
    x,y=(k%5)*480,(k//5)*270
    sheet.paste(im.resize((480,270)),(x,y)); d.text((x+300,y+240),pid,fill=(0,0,0))
sheet.save(sys.argv[1]+"/pose_sheet.png")
