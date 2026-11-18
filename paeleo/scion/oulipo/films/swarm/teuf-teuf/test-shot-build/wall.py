"""Layout plate for the teuf-teuf rollers test shot.

The wall is the real Cueva de las Manos photograph (Suzko, CC BY-SA 3.0,
films/sources/teuf-teuf/hands_cueva.jpg, decoded with PIL only), re-toned
toward the reference's cream wash:
  * rock grain: high-pass kept at 0.30 and low-passed (smooth wash, not grit)
  * median lifted to ~210 and mapped onto the reference's greenish sepia ramp
  * pigment (red/ochre stencil spray, grey guanacos) found by chroma/darkness
    against the local rock colour and printed dark, so the real negative
    stencils read as pale hands in dark blown halos.
Then handmade layers: rubbed charcoal bands, ground line, scratched ticks,
the drag beat's ghost outline, a dot cluster.

World space = layout A, 1280x720, ground y=566, 100 px/m. A plate is rendered
for any camera (scale s, world offset ox, oy) so the wide and the close-up
show the same wall.
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/teuf-teuf/hands_cueva.jpg"
WW, WH = 1280, 720
GROUND = 566

# reference ramp (sampled from teuf.webp: darkest, charcoal, mid, wash, cream, highlight)
RAMP_L = np.array([0.00, 0.12, 0.33, 0.68, 0.87, 0.94, 1.00], np.float32)
RAMP_C = np.array([[15, 17, 9], [43, 44, 31], [89, 90, 73], [179, 176, 152],
                   [223, 217, 188], [239, 232, 202], [251, 243, 213]], np.float32)


def ramp(l):
    l = np.clip(l, 0, 1)
    out = np.empty(l.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(l, RAMP_L, RAMP_C[:, c])
    return out


def wall_lum():
    """toned wall luminance (0..1) in world space 1280x720 at 1 px/world px,
    plus a 2x version for the close-up."""
    a = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32) / 255.0  # 960x720
    lab = cv2.cvtColor(a, cv2.COLOR_RGB2LAB)
    L, A, B = lab[..., 0] / 100.0, lab[..., 1], lab[..., 2]
    # local rock colour (large blur), pigment = chroma / darkness away from it
    Lb = cv2.GaussianBlur(L, (0, 0), 30)
    Ab = cv2.GaussianBlur(A, (0, 0), 60); Bb = cv2.GaussianBlur(B, (0, 0), 60)
    red = np.clip((A - Ab - 4) / 22.0, 0, 1)                    # red ochre spray, red hands, spiral
    yel = np.clip((B - Bb - 6) / 25.0, 0, 1) * (1 - red)        # yellow ochre figures (lighter)
    Ls = cv2.GaussianBlur(L, (0, 0), 1.4)
    grey = np.clip((Lb - Ls - 0.06) / 0.12, 0, 1)               # grey guanacos (rock pits mostly below threshold)
    grey = cv2.morphologyEx(grey, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    # keep only the large painted marks (guanacos); drop rock pits and small shadows
    n, lab, st, _ = cv2.connectedComponentsWithStats((grey > 0.25).astype(np.uint8))
    big = np.zeros(n, np.float32); big[1:] = (st[1:, cv2.CC_STAT_AREA] > 900)
    keep = cv2.dilate(big[lab], np.ones((5, 5), np.uint8))
    grey = grey * keep
    red = cv2.GaussianBlur(red, (0, 0), 1.2) ** 0.85            # blown spray kept as a graded density
    pig = np.clip(red * 1.35 + grey * 0.95 + yel * 0.35, 0, 1)
    pig = cv2.GaussianBlur(pig, (0, 0), 1.0)
    pig = np.clip((pig - 0.06) / 0.94, 0, 1)
    # rock: high-pass 0.30, low-passed so it is a soft wash, not grit
    base = cv2.GaussianBlur(L, (0, 0), 45)
    hp = cv2.GaussianBlur(L - base, (0, 0), 4.0)
    broad = (base - base.mean())
    l = 0.885 + 0.30 * hp * 1.6 + 0.30 * broad - 0.82 * pig
    return l


def build_world(scale=1.0):
    """world-space lum plate (H*scale, W*scale)."""
    l = wall_lum()                                   # 720 x 960
    # cover 1280 wide: scale 1280/960, crop vertically (oy chooses the frieze height)
    s = WW / l.shape[1]
    big = cv2.resize(l, (int(l.shape[1] * s * scale), int(l.shape[0] * s * scale)), interpolation=cv2.INTER_CUBIC)
    oy = int(150 * scale)
    plate = big[oy:oy + int(WH * scale), :int(WW * scale)]
    if plate.shape[0] < int(WH * scale):
        plate = np.pad(plate, ((0, int(WH * scale) - plate.shape[0]), (0, 0)), mode="edge")
    return plate


def band(l, scale, top, seed):
    """rubbed charcoal band: wavy edge, horizontal streaks, rubbed pale gaps."""
    rng = np.random.default_rng(seed)
    h, w = l.shape
    xs = np.arange(w, dtype=np.float32) / scale
    if top:
        edge = (64 + 20 * np.sin(xs / 230 + 0.6) + 8 * np.sin(xs / 71 + 2) + 3 * np.sin(xs / 23)) * scale
    else:
        edge = (GROUND + 34 + 12 * np.sin(xs / 270 + 1.3) + 5 * np.sin(xs / 47) + 2 * np.sin(xs / 19)) * scale
    yy = np.arange(h, dtype=np.float32)[:, None]
    soft = 6 * scale
    m = np.clip((edge[None, :] - yy) / soft + 0.5, 0, 1) if top else np.clip((yy - edge[None, :]) / soft + 0.5, 0, 1)
    st = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), sigmaX=22 * scale, sigmaY=2.2 * scale)
    st = (st - st.mean()) / (st.std() + 1e-6)
    patch = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), sigmaX=60 * scale, sigmaY=20 * scale)
    patch = (patch - patch.mean()) / (patch.std() + 1e-6)
    st = st * np.clip(0.5 + 0.6 * patch, 0.1, 1.4)             # streaks come and go, like rubbed charcoal
    st2 = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), sigmaX=160 * scale, sigmaY=12 * scale)
    st2 = (st2 - st2.mean()) / (st2.std() + 1e-6)
    tone = (0.30 if top else 0.36) + 0.07 * st + 0.06 * st2
    # darker toward the edge of the band (charcoal pressed along the line), paler rubbed inside
    dist = np.abs(yy - edge[None, :]) / scale
    tone = tone - 0.10 * np.exp(-dist / 10.0)
    return l * (1 - m) + tone * m


def scratch_layer(shape, scale, ox, oy, strokes, width=1.6, seed=0, keep=0.75):
    """white scratched lines (engraved ghosts); strokes in world coords."""
    h, w = shape
    ss = 2
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    for pts in strokes:
        pp = [((x - ox) * scale * ss + rng.normal(0, 0.6), (y - oy) * scale * ss + rng.normal(0, 0.6)) for x, y in pts]
        d.line(pp, fill=255, width=max(1, int(width * scale * ss)), joint="curve")
    a = np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    br = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.2 * scale)
    a = a * (br > np.quantile(br, 1 - keep))
    return a


def wobble(p0, p1, n, amp, rng):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((p0[0] + (p1[0] - p0[0]) * t + rng.normal(0, amp), p0[1] + (p1[1] - p0[1]) * t + rng.normal(0, amp)))
    return pts


def plate(scale, ox, oy, out_w, out_h, ghost_front=450, stone_w=250, stone_h=150):
    """Final camera plate as lum array (out_h, out_w) for a camera that maps
    world (x,y) -> ((x-ox)*scale, (y-oy)*scale)."""
    world = build_world(scale)
    world = band(world, scale, True, 3)
    world = band(world, scale, False, 4)
    h, w = world.shape
    rng = np.random.default_rng(7)
    # ground line: a pressed charcoal stroke, slightly uneven
    xs = np.arange(w, dtype=np.float32) / scale
    gy = (GROUND + 1.2 * np.sin(xs / 37) + 0.8 * np.sin(xs / 11)) * scale
    yy = np.arange(h, dtype=np.float32)[:, None]
    gl = np.exp(-((yy - gy[None, :]) / (1.6 * scale)) ** 2)
    gl *= 0.75 + 0.25 * cv2.GaussianBlur(rng.random((1, w)).astype(np.float32), (0, 0), 6)[0][None, :]
    world = world * (1 - gl) + 0.07 * gl
    # scratches in world coords: ghost of the stone where the drag stopped (1.2 m),
    # ticks at 0 / 1.2 / 3 m on the ground band, a few ghost animal contours
    gx1 = ghost_front; gx0 = gx1 - stone_w
    ghost = [wobble((gx0 + 4, GROUND - 3), (gx0 + 10, GROUND - stone_h + 12), 6, 1.2, rng),
             wobble((gx0 + 10, GROUND - stone_h + 12), (gx1 - 30, GROUND - stone_h - 2), 9, 1.5, rng),
             wobble((gx1 - 30, GROUND - stone_h - 2), (gx1 + 6, GROUND - 40), 6, 1.2, rng),
             wobble((gx1 + 6, GROUND - 40), (gx1 - 4, GROUND - 3), 3, 1.0, rng)]
    ticks = []
    for m in (0.0, 1.2, 3.0, 8.0):
        x = 330 + 100 * m
        ticks.append(wobble((x - 1, GROUND + 10), (x + 2, GROUND + 26), 3, 0.6, rng))
    # drag grooves left by the sledge runner earlier in the film
    grooves = [wobble((90, GROUND + 6 + i * 5), (452, GROUND + 5 + i * 5), 20, 0.5, rng) for i in range(2)]
    # ghost animal (a large faint bovid contour, the reference's engraved ghosts)
    ga = [[(700 + 330 * t, 170 - 40 * math.sin(math.pi * t) + 6 * math.sin(9 * t)) for t in np.linspace(0, 1, 30)],
          [(700, 170), (690, 230), (705, 300)], [(1030, 170), (1060, 215), (1050, 290)],
          [(760, 300), (850, 286), (960, 296), (1010, 290)]]
    a = scratch_layer(world.shape, scale, 0, 0, ghost + ticks, width=1.8, seed=11, keep=0.8)
    a = np.maximum(a, 0.55 * scratch_layer(world.shape, scale, 0, 0, grooves, width=1.0, seed=12, keep=0.6))
    a = np.maximum(a, 0.45 * scratch_layer(world.shape, scale, 0, 0, ga, width=1.4, seed=13, keep=0.7))
    world = world * (1 - a) + 1.0 * a
    # dot cluster upper right (handmade, like the reference's)
    dots = np.zeros_like(world)
    for i in range(90):
        x = rng.normal(1120, 60); y = rng.normal(150, 30)
        r = rng.uniform(1.2, 2.4) * scale
        cv2.ellipse(dots, (int(x * scale), int(y * scale)), (int(r * 1.3) + 1, int(r) + 1), rng.uniform(0, 180), 0, 360, 1.0, -1)
    dots = cv2.GaussianBlur(dots, (0, 0), 0.6 * scale)
    world = world * (1 - 0.8 * dots) + 0.12 * dots * 0.8
    # crop to camera
    x0, y0 = int(round(ox * scale)), int(round(oy * scale))
    pad = np.pad(world, ((max(0, -y0), max(0, y0 + out_h - h)), (max(0, -x0), max(0, x0 + out_w - w))), mode="edge")
    return pad[max(0, y0):max(0, y0) + out_h, max(0, x0):max(0, x0) + out_w]


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    p = plate(0.75, 0, 0, 960, 540)
    Image.fromarray(np.clip(ramp(p), 0, 255).astype(np.uint8)).save(out)
    print("ok")
