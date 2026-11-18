import sys, numpy as np, time
from PIL import Image
import render_shots as R
OUT = "/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/"
rend = R.Renderer()
ims = []
t0 = time.time()
for p in (0.0, 0.3, 0.5, 0.7, 0.9):
    st = R.fold_state(p); cs = R.section(*st)
    print(p, "minz", cs["z"].min().round(2), "maxz", cs["z"].max().round(0))
    ims.append(rend.frame(R.Cam(*R.R_cam(p)) if hasattr(R, "R_cam") else R.Cam(*R.cam_mix(R.CAM_WIDE, R.CAM_PACKET, R.ease((p - .25) / .75))), cs))
cs = R.section(*R.FLAT); ims.append(rend.frame(R.Cam(*R.CAM_PACKET), cs))
print("t/frame", (time.time() - t0) / 6)
cs = R.section(*R.OPEN)
ims.append(rend.frame(R.Cam(*R.CAM_WIDE), cs, rigid=(170, -120, 26, -3.0), lift=R.corner_lift(34), ny=4))
ims.append(rend.frame(R.Cam(*R.CAM_P1), cs))
ims.append(R.lightbox_frame(R.ART, 1.0, 0.4)[0])
ims.append(R.lightbox_frame(R.ART, 0.0, 1.0)[0])
rows = [np.concatenate(ims[i:i + 2], 1) for i in range(0, 10, 2)]
Image.fromarray(np.clip(np.concatenate(rows, 0), 0, 255).astype(np.uint8)).resize((960, 1350)).save(OUT + "probe.jpg")
for i, im in enumerate(ims): Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(OUT + f"probe{i}.png")
