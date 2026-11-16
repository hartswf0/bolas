from common import *
import hashlib
W,H=1280,720
h=hashlib.sha256()
for k in sorted(POOL): h.update(open(SRC+POOL[k][1],'rb').read())
PH=h.hexdigest()
img=Image.new('RGB',(W,H),(12,11,10)); d=ImageDraw.Draw(img)
cur='03'; pos=B.index(cur)
p=print_photo(cur,box_h=600)
img.paste(p,(40,40))
tape(img,40+p.width//2,40+p.height-78,"03.- Il regarde l'heure, puis\n      la porte de la consigne.",sz=16,seed=4)
f=font(15); fs=font(13); red=(196,46,44); cream=(232,226,210); grey=(120,114,106)
d=ImageDraw.Draw(img)
d.text((40,652),f"B {pos+1:02d}/08 · {cur} trotteuse · in 0 out 72 · 120f · +",font=f,fill=cream)
d.text((40,676),"00:00:17:08",font=f,fill=red)
X0=40+p.width+60; colA=X0+40; colB=W-150; tw,th=86,64
d.text((X0,40),"POOL  sha256 "+PH[:12]+"  (gelé)",font=f,fill=cream)
d.text((X0,62),"8 tirages · Jack Delano, Union Station, Chicago, 1943",font=fs,fill=grey)
d.text((colA,98),"A  ordinaire",font=f,fill=grey); d.text((colB,98),"B  illicite",font=f,fill=red)
thumbs={k:print_photo(k,box_w=tw).resize((tw,th)) if False else None for k in POOL}
def thumb(k):
    t=print_photo(k,box_h=th); 
    if t.width>tw: t=t.crop(((t.width-tw)//2,0,(t.width-tw)//2+tw,th))
    return t
ya=lambda i:126+i*68
for i,k in enumerate(A):
    j=B.index(k); col=red if k==cur else (90,86,80)
    d.line([(colA+tw+92,ya(i)+th//2),(colB-8,ya(j)+th//2)],fill=col,width=3 if k==cur else 1)
for i,k in enumerate(A):
    img.paste(thumb(k),(colA,ya(i))); d.text((colA+tw+6,ya(i)+6),k,font=fs,fill=grey); d.text((colA+tw+6,ya(i)+24),POOL[k][0][:10],font=font(11),fill=grey)
for j,k in enumerate(B):
    t=thumb(k); img.paste(t,(colB,ya(j)))
    if k==cur: d.rectangle([colB-3,ya(j)-3,colB+t.width+2,ya(j)+th+2],outline=red,width=3)
    d.text((colB+tw+6,ya(j)+6),k,font=fs,fill=red if k==cur else grey)
img.save(OUT+'kf-3.png'); print(PH)
