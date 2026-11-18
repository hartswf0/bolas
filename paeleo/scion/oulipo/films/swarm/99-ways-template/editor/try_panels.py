import sys; sys.path.insert(0,'/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-template/page')
import build_page as bp, numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/'
keys=sys.argv[1:]
ims=[]
for k in keys:
    P=getattr(bp,k)(); a=np.clip(P.c,0,255).astype(np.uint8); ims.append(Image.fromarray(a))
H=700; W=sum(int(i.width*H/i.height) for i in ims); c=Image.new('RGB',(W,H),'gray'); x=0
for i in ims:
    j=i.resize((int(i.width*H/i.height),H)); c.paste(j,(x,0)); x+=j.width
c.save(S+'try.jpg'); print(bp.POSE_CHIN, bp.FK.get('P8'))
