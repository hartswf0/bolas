"""Palette/framing targets measured on rendered mouth poses (masks come from the rig's own pieces)."""
import json, sys, numpy as np, cv2
from PIL import Image
import paper as P, mouth as M, metrics
m=M.Mouth(); W=np.full((P.CH,P.CW,3),255,np.float32)
res={}
for pid in ["rest","A","surprise","O"]:
    j=M.POSES[pid]["jaw"]; img=m.render(pid,j,W)
    up,lo=m.lib[pid]
    jaw=P.rotate_rgba(m.jaw,j,M.HINGE)[...,3]; lo_r=P.rotate_rgba(lo,j,M.HINGE)[...,3]
    lips=np.maximum(up[...,3],lo_r)
    skin=(np.maximum.reduce([m.head[...,3],jaw,m.neck[...,3]])>0.5)&(lips<0.1)
    ds=lambda a: cv2.resize(a.astype(np.float32),(960,540),interpolation=cv2.INTER_AREA)
    sk=ds(skin)>0.99; lp=ds(lips)>0.99
    fn=f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/rig_{pid}.png"
    Image.fromarray(img.clip(0,255).astype(np.uint8)).resize((960,540),Image.LANCZOS).save(fn)
    r=metrics.measure(fn,sk,lp); xs=np.nonzero(sk.any(0))[0]; r["skin_max_x_frac"]=round(xs.max()/960,3)
    r["skin_touches_top_bottom"]=bool(sk[0].any() and sk[-1].any()); r["skin_area_frac"]=round(float(sk.mean()),3)
    res[pid]=r; print(pid,json.dumps(r))
json.dump(res,open(sys.argv[1],"w"),indent=1)
