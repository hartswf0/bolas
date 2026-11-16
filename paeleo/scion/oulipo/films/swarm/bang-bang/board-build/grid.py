import sys,os
from PIL import Image
D='/home/user/bolas/paeleo/scion/oulipo/films/sources/bang-bang/board'
out=sys.argv[1]; names=sys.argv[2:]
cell=(480,300); cols=3; rows=(len(names)+2)//3
s=Image.new('RGB',(cols*cell[0],rows*cell[1]),(255,255,255))
for k,n in enumerate(names):
    im=Image.open(os.path.join(D,n+'.png')).convert('RGBA'); im.thumbnail((cell[0]-10,cell[1]-10))
    bg=Image.new('RGB',im.size,(120,140,120)); bg.paste(im,(0,0),im)
    s.paste(bg,((k%3)*cell[0]+5,(k//3)*cell[1]+5))
s.save(out)
