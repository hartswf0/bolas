"""Rotate the GrabCut binturong so it hangs head-down from its tail; add a white paper margin. Rotation+scale only."""
import numpy as np, cv2, math, json
from PIL import Image
D="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/"
sub=np.array(Image.open(D+"binturong_crop.png").convert("RGB")); fg=np.array(Image.open(D+"binturong_matte.png"))>127
ys,xs=np.nonzero(fg)
# tail tip = topmost matte point in the right third
sel=xs>fg.shape[1]*0.7; i=np.argmin(ys[sel]); tail=(float(xs[sel][i]),float(ys[sel][i]))
head=(170.0,480.0)
v=(head[0]-tail[0],head[1]-tail[1]); phi=math.degrees(math.atan2(v[1],v[0])); rot=phi-90   # CCW degrees for cv2
pad=400
big=cv2.copyMakeBorder(sub,pad,pad,pad,pad,cv2.BORDER_CONSTANT,value=(255,255,255))
bm=cv2.copyMakeBorder(fg.astype(np.uint8)*255,pad,pad,pad,pad,cv2.BORDER_CONSTANT,value=0)
c=(tail[0]+pad,tail[1]+pad)
M=cv2.getRotationMatrix2D(c,rot,1.0)
R=cv2.warpAffine(big,M,(big.shape[1],big.shape[0]),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
A=cv2.warpAffine(bm,M,(bm.shape[1],bm.shape[0]),flags=cv2.INTER_LINEAR)
ys,xs=np.nonzero(A>127); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
m=40
R=R[y0-m:y1+m,x0-m:x1+m]; A=A[y0-m:y1+m,x0-m:x1+m]
tail_r=(c[0]-(x0-m),c[1]-(y0-m))
# white paper margin ~ 10 source px (≈ 3 film px at final scale): the engraving is printed on a cut card
marg=cv2.dilate(A,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21)))
out=np.dstack([R,marg]); 
rgb=out[...,:3].copy(); rgb[A<128]=(250,247,240)   # margin is the page's own paper colour lifted (handmade card backing)
# keep the engraving pixels exactly as scanned inside the matte (soft edge)
a=cv2.GaussianBlur(A.astype(np.float32)/255,(0,0),1.0)[...,None]
rgb=(R*a+np.array([250,247,240])*(1-a)).astype(np.uint8)
Image.fromarray(np.dstack([rgb,marg])).save(D+"binturong_hang.png")
json.dump(dict(rotation_ccw_deg=rot,tail_tip=tail_r,size=R.shape[:2][::-1]),open(D+"binturong_hang.json","w"))
print(rot,tail_r,R.shape)
