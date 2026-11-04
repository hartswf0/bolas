import sys, subprocess, functools, random
from PIL import Image, ImageDraw, ImageFont
W,H=1920,1080; FPS=30
F=['02-reiniger','06-whitney','07-foldes','08-sutherland','14-pose2pose','41-soft-body']
TAG={'02-reiniger':'02 REINIGER','06-whitney':'06 WHITNEY','07-foldes':'07 FOLDÈS','08-sutherland':'08 SUTHERLAND','14-pose2pose':'14 POSE2POSE','41-soft-body':'41 SOFT BODY'}
# sack-centred crop for the late story (sack near the tower's place)
SPEC={'02-reiniger':(0.55,0.5,0.8),'06-whitney':(0.5,0.47,1.0),'07-foldes':(0.66,0.52,0.62),'08-sutherland':(0.68,0.6,0.62),'14-pose2pose':(0.55,0.55,0.62),'41-soft-body':(0.64,0.6,0.62)}
mono=ImageFont.truetype('/home/claude/yt/fonts/JetBrainsMono.ttf',22)
THREAD=(236,222,190)
@functools.lru_cache(maxsize=64)
def raw(f,i): return Image.open(f'frames/{f}/{min(959,max(0,i)):04d}.jpg').convert('RGB')
@functools.lru_cache(maxsize=24)
def norm(f,i):
    im=raw(f,i); s=min(W/im.width,H/im.height); w,h=int(im.width*s),int(im.height*s)
    bg=Image.new('RGB',(W,H),im.getpixel((2,2))); bg.paste(im.resize((w,h),Image.BILINEAR),((W-w)//2,(H-h)//2)); return bg
def sackcrop(f,i,tw,th):
    im=raw(f,i);cx,cy,w=SPEC[f];Wd,Hd=im.size;cw=w*Wd;ch=cw*th/tw
    x0=max(0,min(Wd-cw,cx*Wd-cw/2));y0=max(0,min(Hd-ch,cy*Hd-ch/2))
    return im.crop((int(x0),int(y0),int(x0+cw),int(y0+ch))).resize((tw,th),Image.BILINEAR)
def full(f,i,tw,th):
    im=raw(f,i);s=min(tw/im.width,th/im.height);w,h=int(im.width*s),int(im.height*s)
    bg=Image.new('RGB',(tw,th),im.getpixel((2,2)));bg.paste(im.resize((w,h),Image.BILINEAR),((tw-w)//2,(th-h)//2));return bg
def _unused(f,i,tw,th):
    im=raw(f,i);s=max(tw/im.width,th/im.height);w,h=int(im.width*s),int(im.height*s)
    r=im.resize((w,h),Image.BILINEAR);x=(w-tw)//2;y=(h-th)//2;return r.crop((x,y,x+tw,y+th))
def stitch(d,x0,y0,x1,y1):
    # a sewn seam: dark gap + cross-stitches in thread colour
    d.line((x0,y0,x1,y1),fill=(11,13,16),width=6)
    L=((x1-x0)**2+(y1-y0)**2)**.5; n=int(L//28)
    for k in range(n+1):
        t=k/max(1,n); x=x0+(x1-x0)*t; y=y0+(y1-y0)*t
        if x0==x1: d.line((x-9,y-7,x+9,y+7),fill=THREAD,width=3); d.line((x-9,y+7,x+9,y-7),fill=THREAD,width=3)
        else: d.line((x-7,y-9,x+7,y+9),fill=THREAD,width=3); d.line((x-7,y+9,x+7,y-9),fill=THREAD,width=3)
def label(d,text,x,y):
    tw=d.textlength(text,font=mono); d.rectangle((x-8,y-6,x+tw+8,y+30),fill=(11,13,16)); d.text((x,y),text,font=mono,fill=(231,234,238))
def grid(i,crop):
    out=Image.new('RGB',(W,H),(11,13,16)); tw,th=W//3,H//2
    for k,f in enumerate(F):
        tile=(sackcrop if crop else full)(f,i,tw,th); out.paste(tile,((k%3)*tw,(k//3)*th))
    d=ImageDraw.Draw(out)
    for c in (1,2): stitch(d,c*tw,0,c*tw,H)
    stitch(d,0,th,W,th)
    for k,f in enumerate(F): label(d,TAG[f],(k%3)*tw+20,(k//3)*th+th-44)
    return out
def strips(i,order,vertical=True,n=6):
    out=Image.new('RGB',(W,H))
    for k in range(n):
        f=F[order[k%len(order)]]; src=norm(f,i)
        if vertical: x0,x1=k*W//n,(k+1)*W//n; out.paste(src.crop((x0,0,x1,H)),(x0,0))
        else: y0,y1=k*H//n,(k+1)*H//n; out.paste(src.crop((0,y0,W,y1)),(0,y0))
    d=ImageDraw.Draw(out)
    for k in range(1,n):
        if vertical: stitch(d,k*W//n,0,k*W//n,H)
        else: stitch(d,0,k*H//n,W,k*H//n)
    return out
def single(f,i):
    out=norm(f,i).copy(); label(ImageDraw.Draw(out),TAG[f],34,H-58); return out
# --- the edit: story time t -> which treatment ---
def cycle(t,start,period,seq):
    return seq[int((t-start)//period)%len(seq)]
def frame(i):
    t=i/FPS
    if t<1.0: return grid(i,False)
    if t<2.5: return single(cycle(t,1.0,0.25,[F[0],F[3],F[1],F[5],F[2],F[4]]),i)
    if t<4.0: return single(F[0],i)
    if t<4.5: return strips(i,[0,1,2,3,4,5])
    if t<6.5: return single(F[1],i)
    if t<9.0: return single(cycle(t,6.5,0.625,[F[2],F[3]]),i)
    if t<14.5: return single(cycle(t,9.0,0.8,[F[4],F[0],F[5],F[3],F[2],F[1]]),i)
    if t<18.0: return strips(i,[4,0,5],vertical=False,n=3)
    if t<18.4: return single(F[(i//2)%6],i)
    if t<21.0: return single(F[5],i)
    if t<23.5: return single(F[(i//3)%6],i)
    if t<24.5: return single(F[4],i)
    if t<28.5: return grid(i,True)
    if t<30.0: return single(cycle(t,28.5,0.5,[F[2],F[0],F[3]]),i)
    return grid(i,True)
if __name__=='__main__':
    if sys.argv[1]=='test':
        for t in [float(x) for x in sys.argv[2:]]: frame(int(t*FPS)).resize((960,540)).save(f'fk/test_{t}.jpg',quality=85)
    else:
        out=sys.argv[2]
        p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
            '-vf','fade=t=in:st=0:d=0.3','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-an',out],stdin=subprocess.PIPE)
        for i in range(960): p.stdin.write(frame(i).tobytes())
        p.stdin.close(); p.wait(); print('rc',p.returncode)
