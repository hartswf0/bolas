import numpy as np, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC='/home/user/bolas/paeleo/scion/oulipo/films/sources/la-machine-a-tuer-le-temps/'
M='/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/m/'
OUT='/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-machine-a-tuer-le-temps/proposals/'
COUR='/usr/share/fonts/X11/Type1/c0419bt_.pfb'
POOL={ '01':('horloge','loc_2017844012.jpg'), '02':('main au colis','loc_2017844121.jpg'),
 '03':('trotteuse','loc_2017844115.jpg'), '04':('porte','loc_2017843935.jpg'),
 '05':('regard','loc_2017843923.jpg'), '06':('reçu tombé','loc_2017843913.jpg'),
 '07':('sortie','loc_2017843870.jpg'), '08':('seuil vide','loc_2017843779.jpg')}
A=['01','02','03','04','05','06','07','08']
B=['05','04','02','06','03','01','07','08']
def font(sz):
    try: return ImageFont.truetype(COUR,sz)
    except Exception: return ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',sz)
def load(k): return Image.open(SRC+POOL[k][1]).convert('L')
def paper(w,h,base=(236,229,212),seed=1,grain=7):
    rng=np.random.default_rng(seed)
    n=rng.normal(0,1,(h//4+1,w//4+1)); n=np.array(Image.fromarray(((n*30)+128).clip(0,255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(float)-128
    f=rng.normal(0,grain,(h,w))
    a=np.zeros((h,w,3))
    for i,c in enumerate(base): a[...,i]=c+n*0.12+f
    return Image.fromarray(a.clip(0,255).astype(np.uint8))
# single-stroke hand digits in a 0..1 box (x right, y down)
DIG={'0':[[(.5,0),(.15,.2),(.1,.6),(.35,1),(.75,.9),(.9,.45),(.7,.05),(.45,0)]],
 '1':[[(.25,.25),(.55,0),(.5,1)]],
 '2':[[(.1,.25),(.4,0),(.8,.1),(.8,.4),(.1,1),(.95,.98)]],
 '3':[[(.1,.1),(.5,0),(.85,.2),(.45,.48),(.9,.7),(.6,1),(.1,.9)]],
 '4':[[(.7,1),(.65,0),(.05,.7),(.95,.68)]],
 '5':[[(.85,0),(.2,0),(.15,.45),(.6,.4),(.9,.7),(.55,1),(.1,.9)]],
 '6':[[(.75,0),(.25,.35),(.12,.75),(.45,1),(.85,.75),(.6,.5),(.15,.65)]],
 '7':[[(.05,.02),(.95,0),(.4,1)]],
 '8':[[(.5,.48),(.15,.25),(.45,0),(.85,.2),(.5,.48),(.1,.75),(.45,1),(.9,.75),(.5,.48)]],
 '9':[[(.85,.3),(.5,.5),(.15,.3),(.45,0),(.85,.2),(.8,.6),(.6,1)]]}
def smooth(pts,n=8):
    out=[]
    P=[pts[0]]+pts+[pts[-1]]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        for t in np.linspace(0,1,n,endpoint=False):
            t2,t3=t*t,t*t*t
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in range(2)))
    out.append(pts[-1]); return out
def hand(draw,s,x,y,h,color,width,seed=0,slant=0.12):
    rng=random.Random(seed); cx=x
    for ch in s:
        if ch==' ': cx+=h*0.5; continue
        for stroke in DIG[ch]:
            pts=[(cx+(px+rng.uniform(-.04,.04))*h*0.62+ (1-py)*h*slant, y+(py+rng.uniform(-.03,.03))*h) for px,py in stroke]
            sp=smooth(pts)
            for i in range(len(sp)-1):
                w=max(1,int(width*(0.75+0.35*math.sin(i*0.3+seed))))
                draw.line([sp[i],sp[i+1]],fill=color,width=w)
                draw.ellipse([sp[i][0]-w/2,sp[i][1]-w/2,sp[i][0]+w/2,sp[i][1]+w/2],fill=color)
        cx+=h*0.72
def tape(img,x,y,text,sz=15,pad=10,seed=0):
    f=font(sz); d=ImageDraw.Draw(img)
    lines=text.split('\n'); tw=max(d.textlength(l,font=f) for l in lines); th=len(lines)*sz*1.25
    W,H=int(tw+2*pad),int(th+2*pad*0.7)
    strip=paper(W,H,(246,242,230),seed=seed+9,grain=4)
    # yellowed tape band through middle like the reference
    sa=np.array(strip).astype(float); band=np.zeros((H,W)); band[int(H*0.18):int(H*0.82)]=1
    band=np.array(Image.fromarray((band*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(float)/255
    tint=np.array([238,206,120.0]); sa=sa*(1-band[...,None]*0.55)+tint*band[...,None]*0.55
    strip=Image.fromarray(sa.clip(0,255).astype(np.uint8)); sd=ImageDraw.Draw(strip)
    for i,l in enumerate(lines): sd.text((pad,pad*0.7+i*sz*1.25),l,font=f,fill=(48,40,36))
    img.paste(strip,(int(x-W/2),int(y)))
    return W,H
def shadow_paste(base,im,xy,blur=8,off=(4,6),alpha=110):
    sh=Image.new('L',base.size,0); ImageDraw.Draw(sh).rectangle([xy[0]+off[0],xy[1]+off[1],xy[0]+im.width+off[0],xy[1]+im.height+off[1]],fill=alpha)
    sh=sh.filter(ImageFilter.GaussianBlur(blur))
    dark=Image.new('RGB',base.size,(20,16,12)); base.paste(dark,(0,0),sh); base.paste(im.convert('RGB'),xy)
def print_photo(k,box_w=None,box_h=None,crop_border=0.035,tone=(0,0)):
    im=load(k)
    if k=='05': im=im.crop((156,40,890,768))
    w,h=im.size; c=int(min(w,h)*crop_border)
    im=im.crop((c,c,w-c,h-c))   # trim the negative's black rebate only, picture untouched
    a=np.array(im); thr=215; cols=np.where(a.mean(0)<thr)[0]; rows=np.where(a.mean(1)<thr)[0]
    im=im.crop((cols[0]+4,rows[0]+4,cols[-1]-4,rows[-1]-4))   # and any white print margin
    if box_w: s=box_w/im.width
    else: s=box_h/im.height
    im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    # silver-gelatin print: neutral-warm black, paper-white highlights
    a=np.array(im).astype(float)/255; lo=np.array([22,20,19.0]); hi=np.array([238,234,224.0])
    rgb=lo+(hi-lo)*a[...,None]
    return Image.fromarray(rgb.clip(0,255).astype(np.uint8))
