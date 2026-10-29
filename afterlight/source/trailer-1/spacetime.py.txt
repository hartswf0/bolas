"""SPACETIME splat renderer for the AFTERLIGHT trailer.
A clip becomes a point volume (x, y, t): every sampled pixel is a point, its depth is the moment it was filmed.
The present frame sits in front of the camera; earlier frames recede behind it and fade, so anything that moved
leaves a body of light through time. Two inks: 'paper' (pigment on fog, for day) and 'light' (emission on black, for night)."""
import numpy as np, subprocess, json, os
from scipy.ndimage import gaussian_filter
W, H = 1280, 720
RES = (448, 252)

def load_clip(path, t0=0.0, dur=3.0, fps=24, stride=1, res=RES, cache=None):
    if cache and os.path.exists(cache):
        return np.load(cache)['f']
    w, h = res
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t0), '-i', path, '-t', str(dur), '-vf',
           f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)[::stride].astype(np.float32) / 255
    lo, hi = np.percentile(f, 1), np.percentile(f, 99.5)
    f = np.clip((f - lo) / max(hi - lo, 1e-3), 0, 1)
    if cache: np.savez_compressed(cache, f=f)
    return f

class Volume:
    def __init__(self, frames, mode='paper', per=7000, seed=1, gamma=1.0, floor=0.04):
        rng = np.random.default_rng(seed)
        F, h, w, _ = frames.shape
        self.F, self.mode = F, mode
        live = (frames.std(axis=0).mean(axis=2) > 0.012) | (frames.mean(axis=(0, 3)) > 0.08)   # pillarbox / letterbox never emits
        us, vs, ss, cs = [], [], [], []
        for s in range(F):
            fr = frames[s] ** gamma
            lum = fr @ np.array([0.3, 0.59, 0.11], np.float32)
            gy, gx = np.gradient(lum)
            edge = np.sqrt(gx * gx + gy * gy)
            if mode == 'light': wgt = lum ** 2.2 + 0.6 * edge + 0.002
            else: wgt = (1 - lum) ** 1.6 + 2.0 * edge + floor
            # letterbox / pillarbox padding never emits
            pad = (frames[s].max(axis=2) < 0.012)
            wgt = np.where(pad & (mode == 'paper'), 0, wgt)
            yy, xx = np.mgrid[0:h, 0:w]
            vg = np.clip(1.25 - (((xx / w - 0.5) / 0.55) ** 2 + ((yy / h - 0.5) / 0.6) ** 2) ** 1.5, 0, 1)
            wgt = wgt * vg * live
            p = (wgt / wgt.sum()).ravel()
            idx = rng.choice(h * w, size=per, p=p)
            y, x = np.divmod(idx, w)
            us.append((x + rng.random(per)) / w); vs.append((y + rng.random(per)) / h)
            ss.append(np.full(per, s, np.float32)); cs.append(fr.reshape(-1, 3)[idx])
        self.u = np.concatenate(us).astype(np.float32); self.v = np.concatenate(vs).astype(np.float32)
        self.s = np.concatenate(ss); self.c = np.concatenate(cs).astype(np.float32)
        self.aspect = w / h
        self.jit = rng.standard_normal((len(self.u), 3)).astype(np.float32)
        self.rnd = rng.random(len(self.u)).astype(np.float32)

def rotmat(yaw, pitch, roll=0.0):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]]); Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return (Rz @ Rx @ Ry).astype(np.float32)

def splat(vol, cam, acc, S=900.0, dz=26.0, present=None, tau=18.0, assemble=1.0, opacity=1.0, size=1.0, scatter=700.0, swirl=0.0, wake=0.0):
    """Accumulate one volume into acc (dict of buckets). cam: dict yaw,pitch,roll,dist,fov,cx,cy,pz (pivot depth in slices).
    present: index of the frame being 'emitted' now (float); later frames are not yet visible; earlier ones fade with tau slices."""
    p = vol.F - 1 if present is None else present
    age = p - vol.s                                   # slices since emission
    vis = np.where(age < -0.5, 0.0, np.exp(-np.maximum(age, 0) / tau)).astype(np.float32)
    vis *= np.clip(1.0 + age * 2, 0, 1) if present is not None else 1.0   # the newest slice fades in
    X = (vol.u - 0.5) * vol.aspect * S; Y = (vol.v - 0.5) * S; Z = (age + vol.rnd - 0.5) * dz
    if assemble < 1.0:  # dust: points start scattered and settle into the picture (or leave it)
        k = (1 - assemble) ** 2
        X = X + vol.jit[:, 0] * scatter * k; Y = Y + vol.jit[:, 1] * scatter * k - scatter * 0.3 * k; Z = Z + vol.jit[:, 2] * scatter * k
        vis = vis * np.clip(assemble * 1.6 - vol.rnd * 0.6, 0, 1)
    if swirl:
        r = np.hypot(X, Y) + 1; a = swirl * 600 / r * (1 - assemble + 0.2)
        X, Y = X * np.cos(a) - Y * np.sin(a), X * np.sin(a) + Y * np.cos(a)
    P = np.stack([X - cam.get('cx', 0), Y - cam.get('cy', 0), Z - cam.get('pz', 0) * dz], 1)
    R = rotmat(cam['yaw'], cam['pitch'], cam.get('roll', 0))
    Q = P @ R.T
    z = Q[:, 2] + cam['dist']
    f = (H / 2) / np.tan(np.radians(cam.get('fov', 50)) / 2)
    ok = (z > 20) & (vis > 0.003)
    z = z[ok]; sx = Q[ok, 0] * f / z + W / 2; sy = Q[ok, 1] * f / z + H / 2
    col = vol.c[ok]; a = vis[ok] * opacity
    fog = np.exp(-np.maximum(z - cam.get('fogNear', 600), 0) / cam.get('fogLen', 2600)); a = a * fog
    rad = size * 1.15 * cam['dist'] / z                 # px radius
    inb = (sx >= 0) & (sx < W - 1) & (sy >= 0) & (sy < H - 1)
    sx, sy, col, a, rad = sx[inb], sy[inb], col[inb], a[inb], rad[inb]
    ix = sx.astype(np.int32) + W * sy.astype(np.int32)
    for b, (lo, hi) in enumerate([(0, 1.6), (1.6, 4.5), (4.5, 1e9)]):
        m = (rad >= lo) & (rad < hi)
        if not m.any(): continue
        ww = a[m] * (1.0 if b == 0 else (1.0 / (1 + 0.25 * rad[m]) if b == 1 else 1.4 / (1 + 0.15 * rad[m])))
        A = np.bincount(ix[m], ww, W * H)
        acc[b][..., 3] += A.reshape(H, W)
        for ch in range(3): acc[b][..., ch] += np.bincount(ix[m], ww * col[m, ch], W * H).reshape(H, W)

def new_acc(): return [np.zeros((H, W, 4), np.float32) for _ in range(3)]

def resolve(acc, mode, bg, gain=1.0, k=1.6):
    sig = [0.6, 1.6, 4.2]
    C = np.zeros((H, W, 3), np.float32); A = np.zeros((H, W), np.float32)
    for b in range(3):
        a = acc[b]
        if not a[..., 3].any(): continue
        bl = np.stack([gaussian_filter(a[..., ch], sig[b]) for ch in range(4)], -1)
        C += bl[..., :3]; A += bl[..., 3]
    bg = np.asarray(bg, np.float32)
    if mode == 'light':
        cov = 1 - np.exp(-A * k * gain)
        col = C / np.maximum(A, 1e-6)[..., None]
        img = bg * (1 - cov[..., None]) + col * cov[..., None]
        img = img + gaussian_filter(np.clip(img - 0.55, 0, None), 10) * 1.2
        return np.clip(img, 0, 1)
    cov = 1 - np.exp(-A * k * gain)
    col = C / np.maximum(A, 1e-6)[..., None]
    return np.clip(bg * (1 - cov[..., None]) + col * cov[..., None], 0, 1)
