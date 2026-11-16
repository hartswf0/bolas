# Split the GrabCut visitor into articulated RGBA pieces (#1 cutout, #32 FK), cut the hand, and
# cut trouser/shoe pieces from the photograph's own cloth and felt (flagged inventions: shapes are ours,
# the material is the real silver print).
import cv2, numpy as np, json
from PIL import Image, ImageDraw, ImageFilter
S='/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/'
O=S+'test-shot/'
src=np.array(Image.open(S+'man.jpg').convert('RGB'))
cut=np.array(Image.open(O+'man_rgba_full.png'))
H,W=src.shape[:2]
def polymask(pts,blur=1.5):
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon(pts,fill=255)
    return np.array(m.filter(ImageFilter.GaussianBlur(blur)),np.float32)/255
def save(name,rgb,alpha,pivot):
    a=(alpha*255).clip(0,255).astype(np.uint8)
    ys,xs=np.where(a>8); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    Image.fromarray(np.dstack([rgb[y0:y1,x0:x1],a[y0:y1,x0:x1]])).save(O+f'pc_{name}.png')
    rig[name]={'file':f'pc_{name}.png','pivot':[pivot[0]-int(x0),pivot[1]-int(y0)],'origin':[int(x0),int(y0)]}
rig={}
A=cut[...,3].astype(np.float32)/255; RGB=cut[...,:3]
A=A*polymask([(300,100),(760,100),(760,620),(1000,740),(1110,880),(1180,1050),(1205,1250),(1212,1570),(1010,1585),(995,1720),(235,1720),(225,1420),(245,1300),(250,950),(330,820),(420,720),(300,450)],1.0)
headpoly=[(250,120),(640,120),(690,250),(745,330),(745,560),(720,600),(650,700),(470,712),(420,620),(250,470)]
hm=polymask(headpoly)
save('head',RGB,A*hm,(560,700))
y=np.arange(H)[:,None]*np.ones((1,W))
torso_m=A*(1-hm)*(y<1505)
save('torso',RGB,torso_m,(650,1490))
hem_m=A*(y>=1460)
save('hem',RGB,hem_m,(650,1470))
# hand (+gloves): light flesh/glove pixels inside a box, seeded GrabCut on the full-res crop
x0,y0,x1,y1=600,1440,880,1650
crop=cv2.cvtColor(src[y0:y1,x0:x1],cv2.COLOR_RGB2BGR)
L=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
gm=np.full(L.shape,cv2.GC_PR_BGD,np.uint8); gm[L>120]=cv2.GC_PR_FGD; gm[L>175]=cv2.GC_FGD; gm[L<55]=cv2.GC_BGD
bg=np.zeros((1,65));fg=np.zeros((1,65)); cv2.grabCut(crop,gm,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
hmk=np.where((gm==1)|(gm==3),255,0).astype(np.uint8)
hmk=cv2.morphologyEx(hmk,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(hmk); keep=np.zeros_like(hmk)
for j in range(1,n):
    if st[j,4]>600: keep[lab==j]=255
keep=cv2.morphologyEx(keep,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
full=np.zeros((H,W),np.float32); full[y0:y1,x0:x1]=cv2.GaussianBlur(keep,(3,3),0)/255
save('hand',src,full,(860,1500))
# sleeve: the visitor's real right sleeve (x 980-1215, y 1180-1560)
slv=A*polymask([(985,1180),(1185,1150),(1210,1470),(1005,1480)],2)
save('sleeve',RGB,slv,(1095,1170))
# trouser segments and shoe: shapes cut by us from the photograph's own wool (x 860-1000, y 1040-1360)
# and from the bowler's felt crown (x 420-640, y 190-300)
def cloth(name,box,shape,pivot):
    pass
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon(shape,fill=255)
    m=np.array(m.filter(ImageFilter.GaussianBlur(1.2)),np.float32)/255
    save(name,src,m,pivot)
cloth('thigh',None,[(725,885),(855,885),(840,1235),(740,1235)],(790,895))
cloth('shin',None,[(880,1000),(975,1000),(965,1290),(890,1290)],(927,1010))
cloth('shoe',(420,190,640,300),[(430,215),(520,200),(560,205),(600,225),(610,290),(420,292),(415,250)],(585,215))
json.dump(rig,open(O+'rig_pieces.json','w'),indent=1)
# check sheet
sheet=Image.new('RGB',(1900,640),(255,0,255)); x=10
for k in rig:
    p=Image.open(O+rig[k]['file']); p.thumbnail((260,600)); sheet.paste(p,(x,10),p); x+=p.size[0]+10
sheet.save(O+'pieces_chk.jpg'); print(rig)
