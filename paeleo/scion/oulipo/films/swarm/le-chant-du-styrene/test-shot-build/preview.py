import sys, time
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/test-shot-build")
t0=time.time()
import melt, cv2, numpy as np
print("precompute", time.time()-t0, "gateT", melt.gate_T, "cavTmax", melt.cav_Tmax, "order", melt.order_empty)
print(melt.iou_report())
out=sys.argv[1]
rows=[]
for t in [float(x) for x in sys.argv[2:]]:
    t1=time.time(); im=melt.band(t,int(t*24)); print(t, time.time()-t1)
    rows.append(im)
cv2.imwrite(out, np.vstack(rows)[..., ::-1])
