"""SCION 18 painted-texture library. Every texture is synthesized here from a fixed seed (numpy + Pillow): nothing is fetched.
Outputs (build/cache/): paper.png (screen-space grain, multiply), wash0..2.png (tileable pigment washes for fills),
wood.png (porch plank grain, tileable), speck.png (granulation flecks). Rebuild: python3 build/textures.py"""
import numpy as np, os
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(OUT, exist_ok=True)


def fnoise(h, w, beta, seed):
    """Periodic 1/f^beta noise via FFT, normalised to 0..1 (tileable by construction)."""
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    spec = (r.normal(size=(h, w)) + 1j * r.normal(size=(h, w))) / f ** beta
    spec[0, 0] = 0
    n = np.real(np.fft.ifft2(spec))
    n -= n.min(); n /= n.max()
    return n


def save(a, name):
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name))


# paper: cold-press grain, mostly light, used as a multiply layer over the whole frame (screen space, never scaled)
g = 0.55 * fnoise(720, 1280, 0.6, 1) + 0.45 * fnoise(720, 1280, 1.4, 2)
paper = 1 - 0.10 * (g - g.mean()) / g.std() * 0.5
save(np.clip(paper, 0.80, 1.0), 'paper.png')

# pigment washes: low-frequency blooms + mid granulation; value around 1 (multiply), darker pools
for k in range(3):
    a = fnoise(512, 512, 2.0, 10 + k); b = fnoise(512, 512, 1.1, 20 + k); c = fnoise(512, 512, 0.3, 30 + k)
    w = 1 - (0.30 * a + 0.12 * b + 0.06 * (c > 0.62))
    w = (w - w.min()) / (w.max() - w.min())
    save(0.70 + 0.30 * w, f'wash{k}.png')

# wood: stretched noise along x for plank grain
h, w = 256, 1024
n = fnoise(h * 4, w // 4, 1.6, 40)
n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
rings = 0.5 + 0.5 * np.sin(n * 38)
save(0.72 + 0.28 * (0.6 * rings + 0.4 * n), 'wood.png')

# speck: sparse granulation flecks (alpha)
r = np.random.default_rng(50)
s = (r.random((512, 512)) > 0.996).astype(float)
s = np.maximum(s, np.roll(s, 1, 0) * 0.5)
save(1 - 0.6 * s, 'speck.png')
print('textures ->', OUT)
