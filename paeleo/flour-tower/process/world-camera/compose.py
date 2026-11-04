import json, subprocess, sys, functools
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
OW,OH=1920,1080
P=json.load(open('plan.json'))
BSD='/home/claude/yt/fonts/BigShouldersDisplay.ttf'
def F(sz,w):
    f=ImageFont.truetype(BSD,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
title=F(190,900); endt=F(260,900)
key=lambda t,c: '_'.join(f'{v:.5f}' for v in (t,)+tuple(c))
@functools.lru_cache(maxsize=8)
def load(f,k): return Image.open(f'cap/{f}/{k}.jpg').convert('RGB').resize((OW,OH),Image.LANCZOS)
def shadow_text(img,xy,text,fnt,fill,anchor,alpha=1.0,blur=18):
    m=Image.new('L',img.size,0); ImageDraw.Draw(m).text(xy,text,font=fnt,fill=int(170*alpha),anchor=anchor)
    m=m.filter(ImageFilter.GaussianBlur(blur)); img.paste((0,0,0),mask=m)
    t=Image.new('L',img.size,0); ImageDraw.Draw(t).text(xy,text,font=fnt,fill=int(255*alpha),anchor=anchor)
    img.paste(fill,mask=t)
def frame(fr):
    img=None
    for a,f,t,c in fr['layers']:
        im=load(f,key(t,c))
        img=im.copy() if img is None else Image.blend(img,im,a)
    if False and fr['title']:
        a=min(1,(fr['j']-24)/10)
        shadow_text(img,(90,OH-70),'FLOUR TOWER',title,(255,255,255),'ls',a)
    if fr['endtitle']:
        a=min(1,fr['j']/18); img=ImageEnhance.Brightness(img).enhance(1-0.55*a)
        shadow_text(img,(OW/2,OH/2),'FLOUR TOWER',endt,(255,255,255),'mm',a)
    if fr['i']<6: img=ImageEnhance.Brightness(img).enhance(fr['i']/6)
    if fr['i']>len(P)-12: img=ImageEnhance.Brightness(img).enhance((len(P)-fr['i'])/12)
    return img
if __name__=='__main__':
    if sys.argv[1]=='test':
        for n in map(int,sys.argv[2:]): frame(P[n]).resize((640,360)).save(f'test_{n}.jpg',quality=85)
    else:
        p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-an',sys.argv[2]],stdin=subprocess.PIPE)
        for fr in P: p.stdin.write(frame(fr).tobytes())
        p.stdin.close(); print('rc',p.wait())
