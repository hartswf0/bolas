"""Measure a frame against the §7 targets (ΔE76 in CIELAB, spans, white field)."""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0,"/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-maki-mococo/test-shot-build")
def lab(rgb):
    c=rgb/255.0; c=np.where(c>0.04045,((c+0.055)/1.055)**2.4,c/12.92)
    M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])
    xyz=c@M.T/np.array([0.95047,1.0,1.08883]); f=np.where(xyz>0.008856,np.cbrt(xyz),7.787*xyz+16/116)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],-1)
def dE(a,b): return float(np.linalg.norm(lab(np.array(a,float))-lab(np.array(b,float))))
def measure(path, skin_mask=None, lip_mask=None):
    im=np.asarray(Image.open(path).convert("RGB"),float); H,W=im.shape[:2]
    out={}
    if skin_mask is not None:
        out["skin_median"]=np.median(im[skin_mask],0).round(1).tolist(); out["skin_dE"]=round(dE(out["skin_median"],(202,154,138)),2)
    if lip_mask is not None:
        out["lip_median"]=np.median(im[lip_mask],0).round(1).tolist(); out["lip_dE"]=round(dE(out["lip_median"],(157,86,93)),2)
        ys,xs=np.nonzero(lip_mask); out["lip_span_h"]=round((ys.max()-ys.min())/H,3); out["lip_span_w"]=round((xs.max()-xs.min())/W,3)
    field=im[:, int(W*0.5):]; g=field.mean(-1)
    out["field_mean_excl_marks"]=round(float(field[g>235].mean()),2)
    luma=im@[0.299,0.587,0.114]; out["luma_P5_P25_P50"]=np.percentile(luma,[5,25,50]).round(0).tolist(); out["frac_below80"]=round(float((luma<80).mean()),4)
    return out
if __name__=="__main__":
    print(json.dumps(measure(sys.argv[1])))
