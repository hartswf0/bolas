"""KF3 'Platform 1927, inked': the page turn into page 3 at 27.6 s.
Archive-led: frames of Berlin: Symphony of a Great City (1927), The Electric House (1922) and
The Playhouse (1921), from the Moving Image Archive cache, rotoscoped frame by frame to brush ink
(solid blacks + traced contour + dot screen) inside hand-inked panels; page 2 lifts off as a leaf.
Run: python3 -I kf3.py"""
import sys, math
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/proposals")
from kf_common import *

OUT = ROOT + "/films/swarm/cercle-vicieux/proposals/"

PANELS = {   # id -> (clip, frame, crop box in the 320x240 frame)
    "E": ("play", 4, (190, 30, 320, 225)),
    "F": ("play", 9, (40, 10, 230, 230)),
    "G": ("elec", 7, (0, 0, 300, 230)),
    "H": ("berlin", 15, (0, 0, 320, 240)),
    "X": ("elec", 18, (40, 0, 172, 240)),
}
TEXT = {"E": ("This opens the service door.", "speech"), "F": ("Then I don't want it.", "speech"),
        "G": ("Nobody goes through that door.", "speech"), "H": ("Then who rang the bell?", "whisper")}


def roto(clip, idx, crop, w, h, seed=0, lo=.26, hi=.55):
    """One rotoscoped frame: the archive frame is enlarged, its contours traced as an ink line,
    its shadows filled solid, its mid-tones screened."""
    g = load_gray(CLIPF % (clip, idx))
    x0, y0, x1, y1 = crop
    g = g[y0:y1, x0:x1]
    # fit-cover into w x h
    sc = max(w / g.shape[1], h / g.shape[0])
    g = cv2.resize(g, (int(g.shape[1] * sc + 1), int(g.shape[0] * sc + 1)), interpolation=cv2.INTER_CUBIC)
    oy, ox = (g.shape[0] - h) // 2, (g.shape[1] - w) // 2
    g = g[oy:oy + h, ox:ox + w]
    g = cv2.bilateralFilter(g, 9, 40, 9)
    g = clahe(g, 2.2)
    base = ink_print(g, lo=lo, hi=hi, dot=9)
    bl = cv2.GaussianBlur(g, (0, 0), 3)
    ed = cv2.Canny(bl, 18, 46)
    ed = cv2.dilate(ed, np.ones((3, 3), np.uint8), iterations=2)
    # drop the tiny specks so the line reads as a drawn contour
    n, lab, st, _ = cv2.connectedComponentsWithStats(ed)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] > 260
    base[keep[lab]] = INK
    return base


def page(kind):
    """Render a full page (2560x1440) of either page 2 (E F / G H) or page 3 (X + H G / F E)."""
    c = Image.new("L", (W, H), PAPER)
    G_ = 40
    X0, X1, Y0, Y1 = 80, 2480, 60, 1330
    boxes = {}
    if kind == 2:
        cw = (X1 - X0 - G_) // 2; ch = (Y1 - Y0 - G_) // 2
        boxes = {"E": (X0, Y0, X0 + cw, Y0 + ch), "F": (X0 + cw + G_, Y0, X1, Y0 + ch),
                 "G": (X0, Y0 + ch + G_, X0 + cw, Y1), "H": (X0 + cw + G_, Y0 + ch + G_, X1, Y1)}
    else:
        xw = 620; gx0 = X0 + xw + G_
        cw = (X1 - gx0 - G_) // 2; ch = (Y1 - Y0 - G_) // 2
        boxes = {"X": (X0, Y0, X0 + xw, Y1), "H": (gx0, Y0, gx0 + cw, Y0 + ch), "G": (gx0 + cw + G_, Y0, X1, Y0 + ch),
                 "F": (gx0, Y0 + ch + G_, gx0 + cw, Y1), "E": (gx0 + cw + G_, Y0 + ch + G_, X1, Y1)}
    a = np.array(c)
    for k, b in boxes.items():
        clip, idx, crop = PANELS[k]
        lo, hi = (.14, .42) if clip == "play" else (.26, .55)
        a[b[1]:b[3], b[0]:b[2]] = roto(clip, idx, crop, b[2] - b[0], b[3] - b[1], ord(k), lo, hi)
    c = Image.fromarray(a)
    for k, b in boxes.items():
        if k == "X":
            c = caption_box(c, "The bell can only be rung from behind that door.", b[0] + 26, b[1] + 26, 32, maxc=15, seed=40)
        else:
            t, kd = TEXT[k]
            w = b[2] - b[0]
            c = balloon(c, t, b[0] + w * .34, b[1] + 105, 34, (b[0] + w * .48, b[1] + 230), seed=ord(k) * 3, maxc=14, kind=kd)
    d = ImageDraw.Draw(c)
    for k, b in boxes.items():
        panel_frame(d, b, seed=ord(k) + kind, width=9)
    c, _ = letter_line(c, "- %d -" % kind, W // 2, 1395, 26, 90 + kind)
    return np.array(c)


def build():
    p2 = page(2); p3 = page(3)
    out = np.full((H, W), 30, np.uint8)            # dark desk to the left of the spine
    spine = 600
    # page 3, lying flat, scaled into the spread
    sw = W - spine - 30; sh = int(H * sw / W)
    p3s = cv2.resize(p3, (sw, sh), interpolation=cv2.INTER_AREA)
    oy = (H - sh) // 2
    out[oy:oy + sh, spine:spine + sw] = p3s
    # shadow of the lifted leaf falling across page 3 near the spine (soft, darkest at the gutter)
    xx = np.arange(sw)[None, :].astype(np.float32)
    shade = 1 - 0.38 * np.exp(-xx / 120.0)
    out[oy:oy + sh, spine:spine + sw] = (out[oy:oy + sh, spine:spine + sw] * shade).astype(np.uint8)
    # page 2 as the turning leaf, at ~78 degrees: front still visible, foreshortened, its free edge near the lens
    th = math.radians(101)
    lw = sw * math.cos(th)
    near = 1.18                                       # free edge is closer to camera: taller
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    top0, bot0 = oy, oy + sh
    cy = H / 2
    dst = np.float32([[spine, top0], [spine + lw, cy - (cy - top0) * near], [spine + lw, cy + (bot0 - cy) * near], [spine, bot0]])
    back = (255 - (255 - p2[:, ::-1].astype(np.float32)) * 0.07).astype(np.uint8)   # show-through of page 2's ink
    back = cv2.GaussianBlur(back, (0, 0), 2.5)
    # the leaf's back: hinge at the spine, free edge to the left. Map back's right edge to the spine.
    src = np.float32([[W, 0], [0, 0], [0, H], [W, H]])
    M = cv2.getPerspectiveTransform(src, dst)
    leaf = cv2.warpPerspective(back, M, (W, H), flags=cv2.INTER_AREA, borderValue=0)
    lm = cv2.warpPerspective(np.full((H, W), 255, np.uint8), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    # the leaf is lit from the right: its face goes slightly grey as it turns toward vertical
    ramp = np.clip((np.arange(W)[None, :] - (spine + lw)) / max(1, -lw), 0, 1)
    leaf = (leaf.astype(np.float32) * (0.62 + 0.25 * ramp)).astype(np.uint8)   # back faces away from the light
    m = lm.astype(np.float32) / 255
    out = (out * (1 - m) + leaf * m).astype(np.uint8)
    # leaf edge line
    d_img = Image.fromarray(out); d = ImageDraw.Draw(d_img)
    brush_poly(d, [tuple(dst[1]), tuple(dst[2])], 4, 7, closed=False, fill=235)
    return finish(d_img, OUT + "kf-3.png")


if __name__ == "__main__":
    build()
