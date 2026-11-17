"""U2 measurement: palette / span / field against the §7 targets (PIL + numpy). Writes nothing; returns dict."""
import numpy as np
from PIL import Image


def lab(rgb):
    c = np.asarray(rgb, np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def dE(a, b):
    return float(np.linalg.norm(lab(np.array(a, float)) - lab(np.array(b, float))))


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def measure(frame_rgb, skin_mask, lip_mask, cavity_mask=None):
    """frame_rgb: HxWx3 uint8 composite on white; masks: bool HxW (film res)."""
    f = np.asarray(frame_rgb).astype(np.float64)
    H, W = f.shape[:2]
    luma = f @ np.array([0.299, 0.587, 0.114])
    sk = f[skin_mask]; lp = f[lip_mask]
    sk_med = np.median(sk, 0); lp_med = np.median(lp, 0)
    ys, xs = np.nonzero(lip_mask)
    sx = np.nonzero(skin_mask.any(0))[0]
    right = f[:, W // 2:]
    dark = luma < 80
    out = dict(
        skin_median=[round(x, 1) for x in sk_med], skin_dE76=round(dE(sk_med, hexrgb("#CA9A8A")), 2),
        lip_median=[round(x, 1) for x in lp_med], lip_dE76=round(dE(lp_med, hexrgb("#9D565D")), 2),
        lip_span_h=round((ys.max() - ys.min() + 1) / H, 3), lip_span_w=round((xs.max() - xs.min() + 1) / W, 3),
        lip_box_frac=[round(xs.min() / W, 3), round(ys.min() / H, 3), round(xs.max() / W, 3), round(ys.max() / H, 3)],
        skin_max_x_frac=round((sx.max() + 1) / W, 3),
        skin_touches_top=bool(skin_mask[0].any()), skin_touches_bottom=bool(skin_mask[-1].any()),
        skin_area_frac=round(skin_mask.mean(), 3),
        field_mean_right_half=[round(x, 2) for x in right.reshape(-1, 3).mean(0)],
        luma_P5_P25_P50=[float(np.percentile(luma, p)) for p in (5, 25, 50)],
        frac_below80=round(dark.mean(), 4),
    )
    if cavity_mask is not None:
        out["dark_inside_cavity_frac"] = round(float((dark & cavity_mask).sum() / max(1, dark.sum())), 3)
    return out


def reference():
    im = np.asarray(Image.open("/home/user/bolas/paeleo/scion/oulipo/assets/references/maki.webp").convert("RGB"))
    luma = im.astype(float) @ np.array([0.299, 0.587, 0.114])
    return dict(luma_P5_P25_P50=[float(np.percentile(luma, p)) for p in (5, 25, 50)], frac_below80=round((luma < 80).mean(), 4))
