"""Source image restorer: a clean background plate of the archive dog shot.
The home-movie camera pans (kit camera.json: per-frame offset, frame-i pixel x maps to plate u = x - cam[i]).
For every plate pixel we take the median of the frames that see it with the dog (SAM mask dilated 10 px) excluded.
The plate gives the cut a cue SAM does not: |frame - plate| (the dog is what is not the porch).
Writes build/cache/plate/plate.npz (plate, count, offset)."""
import os, json
import numpy as np
from PIL import Image
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphcut import poly_mask, dilate

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.abspath(os.path.join(HERE, '../../kit/archive-dog'))
OUT = os.path.join(HERE, 'cache/plate')


def build():
    cam = json.load(open(os.path.join(D, 'camera.json')))
    masks = json.load(open(os.path.join(D, 'masks.json')))
    cam = np.round(np.array(cam)).astype(int)
    H, W = 288, 384
    ox = -cam[:, 0].min() if False else 0
    umin = int((0 - cam[:, 0]).min()); umax = int((W - cam[:, 0]).max())
    vmin = int((0 - cam[:, 1]).min()); vmax = int((H - cam[:, 1]).max())
    PW, PH = umax - umin, vmax - vmin
    stack = np.full((50, PH, PW), np.nan, np.float32)
    for i in range(50):
        f = np.array(Image.open(os.path.join(D, 'frames/f%03d.jpg' % i)).convert('L')).astype(np.float32)
        dogm = dilate(poly_mask(masks[str(i)], H, W), 10)
        f[dogm] = np.nan
        u0 = -cam[i, 0] - umin; v0 = -cam[i, 1] - vmin
        stack[i, v0:v0 + H, u0:u0 + W] = f
    plate = np.nanmedian(stack, 0)
    count = np.isfinite(stack).sum(0)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, 'plate.npz'), plate=np.nan_to_num(plate, nan=0).astype(np.float32), count=count,
                        umin=umin, vmin=vmin, cam=cam)
    Image.fromarray(np.nan_to_num(plate, nan=0).clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, 'plate.png'))
    print('plate', PW, PH, 'unseen px', int((count == 0).sum()))


def plate_for(i):
    z = np.load(os.path.join(OUT, 'plate.npz'))
    cam = z['cam']; umin = int(z['umin']); vmin = int(z['vmin'])
    u0 = -cam[i, 0] - umin; v0 = -cam[i, 1] - vmin
    return z['plate'][v0:v0 + 288, u0:u0 + 384], z['count'][v0:v0 + 288, u0:u0 + 384]


if __name__ == '__main__':
    build()
