from common import *
W,H=1280,720
bg=paper(W,H,(206,200,190),seed=3,grain=5)   # table / backing board
img=bg.copy(); d=ImageDraw.Draw(img)
# two pages of the spiral notebook
L=(28,22,630,706); R=(650,22,1252,706)
for i,(x0,y0,x1,y1) in enumerate([L,R]):
    pg=paper(x1-x0,y1-y0,(238,232,216),seed=10+i,grain=6)
    a=np.array(pg).astype(float); yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]]
    edge=np.minimum.reduce([xx,yy,a.shape[1]-xx,a.shape[0]-yy]).astype(float)
    a*= (0.93+0.07*np.clip(edge/40,0,1))[...,None]
    gut = (a.shape[1]-xx) if i==0 else xx
    a*= (0.86+0.14*np.clip(gut/70,0,1))[...,None]
    shadow_paste(img,Image.fromarray(a.clip(0,255).astype(np.uint8)),(x0,y0),blur=6,off=(3,5),alpha=90)
d=ImageDraw.Draw(img)
# spiral wire
for y in range(40,700,17):
    d.arc([626,y-2,654,y+12],200,520,fill=(60,58,56),width=3)
    d.arc([627,y-1,653,y+11],210,330,fill=(170,168,165),width=1)
    d.ellipse([628,y+3,632,y+7],fill=(70,62,52)); d.ellipse([648,y+3,652,y+7],fill=(70,62,52))
# prints: left = 05 regard, right = 02 main au colis (cut B order: ... 04 porte, 02 main)
p1=print_photo('05',box_h=330); p2=print_photo('02',box_h=330)
shadow_paste(img,p1,(330-p1.width//2,100),blur=4,off=(2,3),alpha=80)
shadow_paste(img,p2,(952-p2.width//2,100),blur=4,off=(2,3),alpha=80)
tape(img,330,100+330+26,"05.- Le porteur regarde hors du\n      champ, vers la consigne.",sz=15,seed=1)
tape(img,952,100+330+26,"02.- Une femme emporte le colis\n      et se retourne.",sz=15,seed=2)
d=ImageDraw.Draw(img)
ink=(40,38,44); red=(178,32,36)
# hand-written shot numbers (old positions in cut A) and red-pencil renumbering for cut B
hand(d,'5',300,520,44,ink,3,seed=4); hand(d,'2',924,520,44,ink,3,seed=5)
d.line([(918,526),(966,560)],fill=red,width=3); d.line([(920,560),(962,528)],fill=red,width=2)
hand(d,'3',980,516,46,red,3,seed=7)
d.line([(294,528),(342,562)],fill=red,width=3); d.line([(296,562),(338,530)],fill=red,width=2)
hand(d,'1',350,516,40,red,3,seed=8)
hand(d,'16',1190,34,26,red,2,seed=9)
d.text((52,40),'B',font=font(22),fill=red)
# the third print, 01 horloge, lifted and sliding toward the right page (translation only)
p3=print_photo('01',box_w=250)
shadow_paste(img,p3,(540,588),blur=14,off=(14,18),alpha=120)
img=img.filter(ImageFilter.UnsharpMask(1,40,2))
img.save(OUT+'kf-1.png'); print(img.size)
