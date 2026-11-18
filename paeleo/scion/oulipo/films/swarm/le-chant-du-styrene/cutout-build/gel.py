"""Declared thickness-based gel ramp (colour substitution: the only open runner photograph is teal).

Keeps the photograph's own V channel as the record of light through the part, reads it as optical
thickness (Beer-Lambert: V = exp(-k th)), and re-lights the cutout from behind through a warm polystyrene
gel with per-channel absorption (red absorbed least): thin -> amber (#DB9924..#F7BC5F), thick -> deep red
(#711D1D..#A2514E). Hue of the photograph is discarded; shape, shading, moulding irregularities, gate stubs are kept.
Specular catches (white, unsaturated highlights on the rims in the photo) stay as warm catches.
"""
import cv2, numpy as np

ALPHA = np.array([0.20, 1.45, 3.6], np.float32)   # absorption per unit thickness (R, G, B)
L0 = np.array([1.00, 0.86, 0.66], np.float32)     # warm backlight (tungsten-like)

def gel(bgra, gain=1.0, edge_dark=0.55, wall=1.0):
    a = bgra[..., 3].astype(np.float32) / 255
    m = (a > 0.5).astype(np.uint8)
    hsv = cv2.cvtColor(bgra[..., :3], cv2.COLOR_BGR2HSV).astype(np.float32)
    V, S = hsv[..., 2] / 255, hsv[..., 1] / 255
    dt = cv2.distanceTransform(np.pad(m, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    # edge band: GrabCut edge pixels carry the white table; replace their V by the interior's
    inner = (dt >= 3).astype(np.float32)
    vb = cv2.GaussianBlur(V * inner, (0, 0), 3) / (cv2.GaussianBlur(inner, (0, 0), 3) + 1e-4)
    Vu = np.where(dt < 3, np.minimum(V, vb), V)
    vals = Vu[m > 0]
    vref = np.percentile(vals, 98) if vals.size else 1
    Vn = np.clip(Vu / vref, 0.02, 1)
    dtn = np.clip(dt / max(dt.max(), 1), 0, 1)
    th = wall * (0.08 + 2.9 * (-np.log(Vn)) + 0.45 * dtn)   # optical thickness: photo shading x declared wall factor (thin arms < 1, thick discs > 1)
    T = np.exp(-ALPHA[None, None, :] * th[..., None])
    rgb = 1.22 * L0 * T * (0.22 + 0.78 * Vn[..., None] ** 1.6) * gain    # brighter where the photo lets more light through
    # real specular catches: unsaturated, very bright source pixels well inside the part
    spec = np.clip((V - 0.82) / 0.15, 0, 1) * np.clip((0.35 - S) / 0.25, 0, 1) * (dt >= 2.5)
    rgb = rgb * (1 - 0.6 * spec[..., None]) + spec[..., None] * np.array([0.97, 0.74, 0.40]) * 0.6
    # grazing edges pass less light (no constant-width glow outline)
    ef = 1 - edge_dark * np.clip(1 - dt / 3.0, 0, 1)
    rgb *= ef[..., None]
    # alpha: GrabCut mask with a 1 px soft edge
    al = np.clip(dt / 1.5, 0, 1).astype(np.float32)
    return np.dstack([np.clip(rgb, 0, 1) * al[..., None], al]).astype(np.float32)   # premultiplied RGBA, RGB order
