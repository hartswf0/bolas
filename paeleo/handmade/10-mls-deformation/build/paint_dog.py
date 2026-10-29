"""SCION-10 · paint the ONE image the dog is made of: a hide, laid flat.

It is a dog's coat opened out like a pelt and painted in numpy: the back (dark saddle) down the middle, both flanks to either
side, the four legs reaching out from the flank edges, the head with its ears at the front, the tail behind. Nothing else of the
dog exists: no skeleton, no pieces. Every frame of the film is this one image moved by MLS from a few handles; the handles
lift the flanks down into sides and the legs down to the floor.

Coordinates: u forward along the body (nose at +0.86 m), v across (+ = the dog's left), metres. 400 px per metre.
Writes ../assets/dog_hide.png (RGBA), ../assets/dog_labels.png (semantic part per pixel), ../assets/dog_hide_meta.json."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, '..', 'assets'); os.makedirs(A, exist_ok=True)
PPM = 400; U0, U1, V0, V1 = -0.98, 0.92, -0.66, 0.66
W, Hh = int((U1 - U0) * PPM), int((V1 - V0) * PPM)
SS = 4
rng = np.random.default_rng(1010)


def px(u, v):
    return ((u - U0) * PPM * SS, (v - V0) * PPM * SS)


def poly(pts):
    return [px(u, v) for u, v in pts]


def hw_trunk(u):
    base = 0.255 + 0.035 * np.exp(-((u - 0.17) / 0.12) ** 2) + 0.025 * np.exp(-((u + 0.27) / 0.1) ** 2) - 0.02 * np.exp(-((u + 0.06) / 0.1) ** 2)
    uc, L = -0.03, 0.40
    return base * np.clip(1 - np.abs((u - uc) / L) ** 5, 0, 1) ** 0.5


def outline(f, ua, ub, n=120):
    us = np.linspace(ua, ub, n)
    return [(u, f(u)) for u in us] + [(u, -f(u)) for u in us[::-1]]


def shapes():
    S = {}
    S['trunk'] = [outline(hw_trunk, -0.43, 0.37)]
    S['neck'] = [outline(lambda u: 0.22 - 0.11 * np.clip((u - 0.28) / 0.24, 0, 1) ** 1.1, 0.27, 0.56)]
    th = np.linspace(0, 2 * np.pi, 80)
    skull = [(0.60 + 0.12 * np.cos(t), 0.165 * np.sin(t)) for t in th]
    muzzle = outline(lambda u: 0.105 - 0.045 * np.clip((u - 0.66) / 0.22, 0, 1) ** 1.1 - 0.03 * np.clip((u - 0.875) / 0.035, 0, 1) ** 2, 0.62, 0.91)
    S['head'] = [skull, muzzle]
    ears = []
    for s in (1, -1):
        ears.append([(0.50, s * 0.095), (0.60, s * 0.15), (0.575, s * 0.215), (0.47, s * 0.275), (0.445, s * 0.20), (0.475, s * 0.12)])
    S['ear'] = ears
    legs = []
    for s in (1, -1):   # front legs: from flank edge outwards, a paw at the end
        legs.append(('legF', [(0.13, s * 0.25), (0.285, s * 0.25), (0.262, s * 0.40), (0.258, s * 0.53), (0.18, s * 0.53), (0.172, s * 0.40)]))
        legs.append(('legH', [(-0.40, s * 0.22), (-0.13, s * 0.24), (-0.20, s * 0.40), (-0.225, s * 0.53), (-0.305, s * 0.53), (-0.33, s * 0.40)]))
    S['legs'] = legs
    paws = []
    for s in (1, -1):
        for uc in (0.218, -0.265):
            paws.append([(uc + 0.052 * np.cos(t), s * 0.548 + 0.04 * np.sin(t)) for t in th])
    S['paws'] = paws
    S['tail'] = [outline(lambda u: 0.026 + 0.05 * np.clip((u + 0.87) / 0.45, 0, 1) ** 0.7 * (1 - 0.3 * np.clip((u + 0.45) / 0.07, 0, 1)), -0.87, -0.36)]
    return S


def mask(polys):
    im = Image.new('L', (W * SS, Hh * SS), 0); d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon(poly(p), fill=255)
    return np.asarray(im.resize((W, Hh), Image.LANCZOS), float) / 255


def main():
    S = shapes()
    M = {k: mask(v) for k, v in S.items() if k not in ('legs',)}
    legF = mask([p for n, p in S['legs'] if n == 'legF']); legH = mask([p for n, p in S['legs'] if n == 'legH'])
    M['legs'] = np.maximum(np.maximum(legF, legH), M['paws'])
    uu, vv = np.meshgrid(U0 + (np.arange(W) + .5) / PPM, V0 + (np.arange(Hh) + .5) / PPM)
    av = np.abs(vv)
    alpha = np.clip(sum(M[k] for k in ('trunk', 'neck', 'head', 'ear', 'legs', 'tail')), 0, 1)
    # fur fringe: the outline breaks into hair
    n1 = ndi.gaussian_filter(rng.normal(0, 1, alpha.shape), (0.8, 2.5)); n1 /= n1.std()
    edge = ndi.gaussian_filter(alpha, 1.2)
    fringe = np.clip((edge - 0.5) * 3 + 0.5 + 0.22 * n1 * (1 + 1.5 * M['tail']), 0, 1)
    alpha = np.where((alpha > 0.02) & (alpha < 0.98), np.minimum(fringe, ndi.maximum_filter(alpha, 3)), alpha)

    # coat colour (sRGB 0..1)
    tan = np.array([0.66, 0.47, 0.28]); cream = np.array([0.80, 0.68, 0.50]); black = np.array([0.15, 0.11, 0.08])
    brown = np.array([0.36, 0.24, 0.14]); dark = np.array([0.20, 0.14, 0.10])
    col = np.ones(alpha.shape + (3,)) * tan
    # saddle along the back of trunk and neck, fading at the edges, onto the top of the tail
    hw = np.maximum(hw_trunk(uu), 0.05)
    sad_w = np.where(uu < 0.3, 0.165 + 0.012 * np.sin(uu * 9), 0.165 - 0.3 * (uu - 0.3))
    sad = np.clip((sad_w - av) / 0.04, 0, 1) * np.clip((uu + 0.47) / 0.05, 0, 1) * np.clip((0.50 - uu) / 0.08, 0, 1)
    sad = np.maximum(sad, M['tail'] * np.clip((0.035 - av) / 0.02, 0, 1) * np.clip((-uu - 0.42) / 0.1, 0, 1) * 0.85 * np.clip((uu + 0.84) / 0.06, 0, 1))
    col = col * (1 - sad[..., None]) + black * sad[..., None]
    # lighter belly line at the flank edges, cream legs, darker paws' toes
    belly = np.clip((av / hw - 0.78) / 0.2, 0, 1) * M['trunk'] * (1 - M['legs'])
    col = col * (1 - 0.6 * belly[..., None]) + cream * 0.6 * belly[..., None]
    legmix = M['legs'] * (1 - M['trunk'])
    col = col * (1 - 0.55 * legmix[..., None]) + np.array([0.74, 0.58, 0.38]) * 0.55 * legmix[..., None]
    # head: tan cheeks, dark mask over the muzzle top and between the eyes, dark ears
    hm = M['head'] * (1 - M['neck'] * (uu < 0.5))
    mask_dark = hm * np.clip((uu - 0.70) / 0.05, 0, 1) * np.clip((0.07 - av) / 0.03 + 0.5, 0, 1)
    brow = hm * np.clip((0.05 - av) / 0.03, 0, 1) * np.clip((uu - 0.5) / 0.05, 0, 1) * 0.6
    col = col * (1 - mask_dark[..., None]) + dark * mask_dark[..., None]
    col = col * (1 - brow[..., None]) + brown * brow[..., None]
    ear = M['ear'] * (1 - M['head'])
    inner = ear * np.clip(1 - np.abs(av - 0.19) / 0.045, 0, 1) * 0.55
    col = col * (1 - ear[..., None]) + dark * ear[..., None]
    col = col * (1 - inner[..., None]) + np.array([0.55, 0.38, 0.30]) * inner[..., None]
    # nose and eyes
    nose = ((uu - 0.872) / 0.034) ** 2 + (vv / 0.04) ** 2 < 1
    col[nose] = [0.05, 0.04, 0.04]
    for s in (1, -1):
        e = ((uu - 0.675) / 0.022) ** 2 + ((vv - s * 0.082) / 0.014) ** 2
        col[e < 1] = [0.06, 0.04, 0.03]
        col[e < 1.6] = col[e < 1.6] * 0.7
        c = ((uu - 0.681) / 0.006) ** 2 + ((vv - s * 0.079) / 0.005) ** 2 < 1
        col[c] = [0.85, 0.80, 0.70]
        lip = hm * np.clip(1 - np.abs(av - (0.085 - 0.03 * np.clip((uu - 0.70) / 0.2, 0, 1))) / 0.007, 0, 1) * (uu > 0.70)
        col = col * (1 - 0.6 * lip[..., None])

    # fur: streaks that flow back along the body and down the flanks (anisotropic noise), plus fine grain
    g = rng.normal(0, 1, alpha.shape)
    along = ndi.gaussian_filter(g, (0.7, 5.0)); along /= along.std()
    down = ndi.gaussian_filter(g, (4.0, 0.7)); down /= down.std()
    side = np.clip((av / hw - 0.35) / 0.4, 0, 1) * M['trunk']
    side = np.maximum(side, legmix)
    fur = along * (1 - side) + down * side
    grain = ndi.gaussian_filter(rng.normal(0, 1, alpha.shape), 0.6); grain /= grain.std()
    col *= (1 + 0.11 * fur + 0.05 * grain)[..., None]
    # baked form shading: the spine catches the sky; flanks and legs fall away into shadow toward the belly
    form = 1 - 0.30 * np.clip(av / hw, 0, 1.2) ** 2 * M['trunk'] - 0.15 * legmix
    form = np.where(M['head'] > 0.5, 1 - 0.22 * np.clip(av / 0.16, 0, 1) ** 2, form)
    col *= form[..., None]
    col = np.clip(col, 0, 1)

    # semantic labels (for feature protection measurements and painter bias): 1 trunk, 2 neck, 3 head, 4 ear, 5 leg, 6 tail
    lab = np.zeros(alpha.shape, np.uint8)
    for k, i in (('trunk', 1), ('neck', 2), ('legs', 5), ('tail', 6), ('head', 3), ('ear', 4)):
        lab[M[k] > 0.5] = i
    lab[(M['ear'] > 0.5) & (M['head'] > 0.5)] = 3
    lab[(lab == 0) & (alpha > 0.05)] = 1
    rgba = np.dstack([col * 255, alpha * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(A, 'dog_hide.png'))
    Image.fromarray(lab).save(os.path.join(A, 'dog_labels.png'))
    json.dump({'ppm': PPM, 'u0': U0, 'u1': U1, 'v0': V0, 'v1': V1, 'W': W, 'H': Hh,
               'about': 'image x = (u - u0) * ppm (nose to the right), image y = (v - v0) * ppm; labels 1 trunk 2 neck 3 head 4 ear 5 leg 6 tail'},
              open(os.path.join(A, 'dog_hide_meta.json'), 'w'), indent=1)
    # a viewing copy on a mid-grey ground
    bg = Image.new('RGBA', (W, Hh), (120, 124, 130, 255)); bg.alpha_composite(Image.fromarray(rgba, 'RGBA'))
    bg.convert('RGB').save(os.path.join(H, '..', 'proof', 'dog_hide_view.jpg'), quality=90)


if __name__ == '__main__':
    main()
