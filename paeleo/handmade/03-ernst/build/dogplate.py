"""SCION 03 Ernst · engraving the dog maquette: shade the solid, cut its lines along the form, outline it."""
import numpy as np
import sdf
import burin

ALB = {'coat': 0.74, 'pale': 0.9, 'muzzle': 0.6, 'nose': 0.04, 'eye': 0.0, 'ear': 0.34, 'skin': 0.85, 'cloth': 0.55,
       'cloth2': 0.6, 'hair': 0.2, 'wood': 0.5, 'shoe': 0.1, 'shirt': 0.9}
SKY = np.array([-0.35, 0.82, 0.45]); SKY /= np.linalg.norm(SKY)
SP = 0.0215          # line period on the body (m)


def shade(buf, prims, doorlight=0.0, door_pos=np.array([0.0, 1.05, -0.4]), sky=1.0, dusk=0.0, body_up=None):
    hit = buf['hit']
    N = buf['N']; P = buf['P']; ids = buf['id']
    mats = np.array([ALB.get(pr.mat, 0.6) for pr in prims] + [1.0])
    alb = mats[np.where(ids >= 0, ids, len(prims))]
    names = [pr.name for pr in prims]
    # a darker saddle along the back of the coat (the archive dog's colouring): albedo falls with the up-facing normal
    coat = np.array([pr.mat == 'coat' for pr in prims] + [False])[np.where(ids >= 0, ids, len(prims))]
    up = N[..., 1]
    alb = np.where(coat, alb - 0.34 * np.clip(up - 0.2, 0, 1) ** 0.8, alb)
    diff = np.clip(N @ SKY, 0, 1)
    rim = np.clip(-N[..., 2] * 0.0 + 0.0, 0, 1)
    L = (0.26 + 0.86 * diff) * sky
    warm = np.zeros(hit.shape)
    if doorlight > 0:
        dv = door_pos[None, None] - P
        dist = np.linalg.norm(dv, axis=-1)
        dv = dv / np.maximum(dist[..., None], 1e-6)
        lam = np.clip(np.einsum('ijk,ijk->ij', N, dv), 0, 1)
        fall = 1.0 / (1 + (dist / 1.6) ** 2)
        warm = doorlight * lam * fall * 1.25
        L = L + warm
    dark = 1 - np.clip(alb * L, 0, 1)
    dark = np.clip(dark + dusk, 0, 1)
    return np.where(hit, dark, 0.0), np.where(hit, warm, 0.0)


def engrave(buf, prims, doorlight=0.0, sky=1.0, dusk=0.0):
    hit = buf['hit']
    dark, warm = shade(buf, prims, doorlight, sky=sky, dusk=dusk)
    rad = np.maximum(buf['rad'], 0.01)
    nl = np.maximum(np.round(2 * np.pi * rad / SP), 3)
    u = buf['u'] / (2 * np.pi) * nl
    v = buf['v'] / (SP * 1.3)
    ids = buf['id']
    # per-part phase offset so the lines of neighbouring parts do not align (an engraver re-starts at each part)
    u = u + (ids % 7) * 0.137
    cov = burin.engrave(u, v, dark, knee=0.7)
    # outline: silhouette and depth breaks
    d = np.where(hit, buf['depth'], 99.0)
    gy, gx = np.gradient(d)
    brk = np.clip((np.abs(gx) + np.abs(gy) - 0.04) * 8, 0, 0.85)
    sil = burin.edge(hit, 0.9)
    line = np.maximum(sil, brk * hit)
    # dark accents: nose and eyes are solid ink
    names = np.array([pr.mat for pr in prims] + ['none'])[np.where(ids >= 0, ids, len(prims))]
    solid = (names == 'nose') | (names == 'eye')
    cov = np.where(solid, 0.92, cov)
    cov = np.maximum(cov * hit, line)
    alpha = np.clip(burin.blur(hit.astype(float), 0) * 1.0 + sil, 0, 1)
    return cov, alpha, warm
