from common import *
P=OUT; ref=Image.open('/home/user/bolas/paeleo/scion/oulipo/assets/references/oucipo.webp').convert('RGB')
cells=[(ref,'REFERENCE · Oucipo dossier, La Machine à tuer le temps (Drouot)'),
 (Image.open(P+'kf-1.png'),'1 · LE CAHIER REBATTU — paper stop-motion of the dossier'),
 (Image.open(P+'kf-2.png'),'2 · OMBRES DE LA CONSIGNE — articulated shadow theatre'),
 (Image.open(P+'kf-3.png'),'3 · LA PERMUTATION — archive prints + edit-recipe type')]
CW,CH,LB=960,540,40
b=Image.new('RGB',(CW*2+30,(CH+LB)*2+30),(245,242,235)); d=ImageDraw.Draw(b); f=font(20)
for i,(im,lab) in enumerate(cells):
    x=10+(i%2)*(CW+10); y=10+(i//2)*(CH+LB+10)
    t=im.copy(); t.thumbnail((CW,CH)); b.paste(t,(x+(CW-t.width)//2,y+(CH-t.height)//2))
    d.text((x,y+CH+10),lab,font=f,fill=(120,20,24) if i else (40,40,40))
b.save(P+'board.jpg',quality=88); print(b.size)
