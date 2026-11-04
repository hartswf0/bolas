import subprocess, functools, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shots import *
W,H=1080,1920
BSD='/home/claude/yt/fonts/BigShouldersDisplay.ttf'; JBM='/home/claude/yt/fonts/JetBrainsMono.ttf'
def font(p,s,w=None):
    f=ImageFont.truetype(p,s)
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
big=font(BSD,150,900); mid=font(BSD,96,800); lab=font(JBM,46,600); small=font(JBM,30,500)
def path(f,t,crop,out):
    js=lambda v: str(int(v)) if float(v).is_integer() else repr(v)
    cx,cy,hf=crop; return f'cap/{f}/{t:.4f}_{js(cx)}_{js(cy)}_{js(hf)}_{out[0]}x{out[1]}.jpg'
@functools.lru_cache(maxsize=16)
def load(p,size): return Image.open(p).convert('RGB').resize(size,Image.LANCZOS)
def shadowed(img,xy,text,fnt,fill=(255,255,255),anchor='mm',blur=10):
    sh=Image.new('L',img.size,0); ImageDraw.Draw(sh).text(xy,text,font=fnt,fill=200,anchor=anchor)
    sh=sh.filter(ImageFilter.GaussianBlur(blur)); img.paste((0,0,0),mask=sh)
    ImageDraw.Draw(img).text(xy,text,font=fnt,fill=fill,anchor=anchor)
def pill(img,text,y):
    d=ImageDraw.Draw(img); w=d.textlength(text,font=lab)
    d.rounded_rectangle((W/2-w/2-26,y-38,W/2+w/2+26,y+38),radius=38,fill=(11,13,16))
    d.text((W/2,y),text,font=lab,fill=(236,230,214),anchor='mm')
def grid_frame(t,k,n):
    out=Image.new('RGB',(W,H),(11,13,16)); tw,th=540,560; top=H-3*th
    for j,f in enumerate(['02','06','07','08','14','41']):
        out.paste(load(path(f,t,GRID_CROP[f],(540,560)),(tw,th)),((j%2)*tw,top+(j//2)*th))
    d=ImageDraw.Draw(out)
    d.line((tw,top,tw,H),fill=(11,13,16),width=8)
    for r in (1,2): d.line((0,top+r*th,W,top+r*th),fill=(11,13,16),width=8)
    for j,f in enumerate(['02','06','07','08','14','41']):
        x=(j%2)*tw+tw/2; y=top+(j//2)*th+th-46; tl=d.textlength(LABEL[f],font=small)
        d.rounded_rectangle((x-tl/2-14,y-22,x+tl/2+14,y+22),radius=22,fill=(11,13,16)); d.text((x,y),LABEL[f],font=small,fill=(236,230,214),anchor='mm')
    a=min(1,k/12)
    if a>0:
        d.text((W/2,95),'SAME SACK. SAME STORY.',font=mid,fill=(255,255,255),anchor='mm')
        d.text((W/2,195),'SIX WAYS.',font=mid,fill=(242,196,106),anchor='mm')
    return out
def frames():
    for i,f,t,crop,kind in plan():
        if f=='GRID':
            k=i-[x[0] for x in plan() if x[1]=='GRID'][0]; yield grid_frame(t,k,0); continue
        img=load(path(f,round(t,4),crop,(1080,1920)),(W,H)).copy()
        if i<72 and i>=8:
            shadowed(img,(W/2,300),'ONE FLOUR SACK.',big)
            shadowed(img,(W/2,440),'SIX WAYS TO ANIMATE IT.',mid,fill=(242,196,106))
        elif kind not in('STROBE',) and i>=72:
            pill(img,LABEL[f],H-150)
        yield img
if __name__=='__main__':
    if sys.argv[1]=='test':
        P=plan(); want=[int(x) for x in sys.argv[2:]]
        for n,img in enumerate(frames()):
            if n in want: img.resize((360,640)).save(f'test_{n}.jpg',quality=85)
            if n>max(want): break
    else:
        p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-an',sys.argv[2]],stdin=subprocess.PIPE)
        for img in frames(): p.stdin.write(img.tobytes())
        p.stdin.close(); print('rc',p.wait())
