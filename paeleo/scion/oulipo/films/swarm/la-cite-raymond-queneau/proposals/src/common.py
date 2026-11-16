import numpy as np
from PIL import Image, ImageDraw, ImageFont
REF='/home/user/bolas/paeleo/scion/oulipo/assets/references/citefilm.webp'
SRC='/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/'
OUT='/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-cite-raymond-queneau/proposals/'
def ref_stats():
    r=np.asarray(Image.open(REF).convert('L'),dtype=np.float32); return r.mean(), r.std()
def match(a, k=0.5):
    """half-strength luminance mean/spread match to reference, no hue grade"""
    m,s=ref_stats(); a=a.astype(np.float32)
    L=a.mean(2,keepdims=True); lm,ls=L.mean(),L.std()
    L2=(L-lm)*(1+k*(s/ls-1))+lm+k*(m-lm)
    return np.clip(a+(L2-L),0,255)
def captions(img, a, b):
    d=ImageDraw.Draw(img); f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',26)
    fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    W,H=img.size
    for i,(tag,t,col) in enumerate([('A',a,(255,240,200)),('B',b,(215,228,240))]):
        y=H-92+i*40; w=d.textlength(t,font=f); x=(W-w)/2
        for dx in(-2,-1,0,1,2):
            for dy in(-2,-1,0,1,2): d.text((x+dx,y+dy),t,font=f,fill=(20,20,20))
        d.text((x,y),t,font=f,fill=col); d.text((x-24,y+8),tag,font=fs,fill=col)
    return img
