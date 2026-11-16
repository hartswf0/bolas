import sys,os
from PIL import Image
D='/home/user/bolas/paeleo/scion/oulipo/films/sources/bang-bang/board'
names=sys.argv[2:]; out=sys.argv[1]
ims=[]
for n in names:
    im=Image.open(os.path.join(D,n+'.png')); bg=Image.new('RGB',im.size,(120,140,120)); bg.paste(im,(0,0),im if im.mode=='RGBA' else None); ims.append(bg)
H=300; row=[i.resize((max(1,int(i.width*H/i.height)),H)) for i in ims]
W=sum(r.width for r in row)+10*len(row)
s=Image.new('RGB',(W,H),(255,255,255));x=0
for r in row: s.paste(r,(x,0)); x+=r.width+10
s.save(out)
