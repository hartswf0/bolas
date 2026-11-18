# Proposal keyframes for la-mort-en-ce-jardin.  Usage:
#   python3 -I kf.py <sources dir> <cache thumbs dir> <cache clips dir> <out dir> <reference.webp> [123]
# Foraged: LACMA "Pair of Woman's Bar Shoes (Wedding)" 51.47.2a-b (Commons, public domain);
#   Moving Image Archive cache: Robinson Crusoe (1927, B and C reels), Indisch allerlei (1920) -- pre-1931, PD-US.
# Handmade: the paper puppets, plank, banks, silhouette jungle and water strips (all drawn by this script).
import sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, THUMBS, CLIPS, OUT, REF = sys.argv[1:6]
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PW, PH, PX = 1080, 720, 100            # 3:2 picture (the reference still is 1.48:1), pillarboxed in 1280x720
RC_C_JUNGLE = "c74f645d-34b5-52e6-933a-59fb1cee3c39.jpg"
RC_C_PALMS = "f7f9d32a-8866-51f3-b234-7b4570d0d7e1.jpg"
INDISCH_WATER = "fdb47ec9-f0f6-5e20-9af2-f697c50a2bf8.jpg"
RC_B_CLIP = "62fd3c56-ea1e-5abd-ae6e-b36198b07ea2.mp4"


# ------------------------------------------------------------------ shared helpers
def grey(im):
    return im.convert("L")


def print_grade(a):
    """Panchromatic print: lifted blacks, soft shoulder (reference highlights never clip)."""
    a = np.asarray(a, np.float32) / 255
    a = 0.05 + 0.88 * a
    a = a ** 0.95
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def frame_of(pic):
    f = Image.new("RGB", (1280, 720), (6, 6, 6)); f.paste(pic.convert("RGB"), (PX, 0)); return f


def caption(img, text, y=672, size=26):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(SERIF_I, size)
    w = d.textlength(text, font=f); x = (img.width - w) / 2
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
        d.text((x + dx, y + dy), text, font=f, fill=(10, 10, 10))
    d.text((x, y), text, font=f, fill=(238, 236, 230))


def paper_tex(size, seed, amp=0.05):
    r = np.random.default_rng(seed)
    n = cv2.resize(r.normal(0, 1, (size[1] // 5 + 1, size[0] // 5 + 1)).astype(np.float32), size,
                   interpolation=cv2.INTER_CUBIC)
    f = cv2.GaussianBlur(r.normal(0, 1, (size[1], size[0])).astype(np.float32), (0, 0), 0.8)
    return 1 + amp * n + 0.5 * amp * f


def rough(mask, seed, amt=20, blur=1.4):
    a = np.asarray(mask).astype(np.float32); H, W = a.shape
    r = np.random.default_rng(seed)
    nz = cv2.resize(r.normal(0, 1, (H // 6 + 1, W // 6 + 1)).astype(np.float32), (W, H))
    a = cv2.GaussianBlur(a, (0, 0), blur) + nz * amt
    return Image.fromarray(np.clip((a - 128) * 4 + 128, 0, 255).astype(np.uint8))


def lay(canvas, mask, tone, seed, shadow=6, sh_alpha=120, tex=0.05, smudge=None):
    """Lay one cut-paper piece (grey card) with drop shadow and fibre."""
    W, H = canvas.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(5)).point(lambda v: v * sh_alpha // 255))
    if shadow: canvas.alpha_composite(sh, (shadow, shadow))
    t = paper_tex((W, H), seed, tex)
    if smudge is not None: t = t * smudge
    col = np.clip(np.float32(tone) * t, 0, 255).astype(np.uint8)
    piece = Image.fromarray(col, "L").convert("RGBA"); piece.putalpha(mask)
    canvas.alpha_composite(piece)


def capsule(p0, p1, r0, r1, n=10):
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0); pts = []
    for k in range(n + 1):
        t = a + math.pi / 2 + math.pi * k / n; pts.append((x0 + r0 * math.cos(t), y0 + r0 * math.sin(t)))
    for k in range(n + 1):
        t = a - math.pi / 2 + math.pi * k / n; pts.append((x1 + r1 * math.cos(t), y1 + r1 * math.sin(t)))
    return pts


def ell(cx, cy, rx, ry, rot=0, n=40):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def poly_mask(size, polys, seed=None, amt=16):
    m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    for p in polys: d.polygon(p, fill=255)
    return rough(m, seed, amt) if seed is not None else m


def fk(root, chain):
    """Forward kinematics: chain = [(length, absolute-ish angle deg), ...] -> joint points."""
    pts = [root]; x, y = root; acc = 0
    for L, ang in chain:
        acc = ang
        x += L * math.cos(math.radians(acc)); y += L * math.sin(math.radians(acc)); pts.append((x, y))
    return pts


def brad(d, x, y, r=4):
    d.ellipse((x - r, y - r, x + r, y + r), fill=(150, 150, 146, 255), outline=(60, 60, 58, 255), width=1)
    d.ellipse((x - r * .5, y - r * .6, x - r * .1, y - r * .2), fill=(225, 225, 220, 255))


# --------------------------------------------------------------- puppet rig (FK, one paper piece per bone)
def puppet_parts(pose, s=1.0):
    """pose: dict with hip, torso angle, neck, limbs; returns ordered list of (name, polygon, joint)."""
    hx, hy = pose["hip"]
    parts = []
    T = 92 * s
    sh = fk((hx, hy), [(T, pose["torso"])])[1]
    neck = fk(sh, [(16 * s, pose["torso"])])[1]
    head_c = fk(neck, [(22 * s, pose.get("head", pose["torso"]))])[1]
    # far limbs first (drawn behind)
    for side in ("far", "near"):
        th, sn, ft = pose[side + "_leg"]
        k = fk((hx, hy), [(58 * s, th)])[1]; a = fk(k, [(56 * s, sn)])[1]; toe = fk(a, [(22 * s, ft)])[1]
        ua, fa, hd = pose[side + "_arm"]
        e = fk(sh, [(44 * s, ua)])[1]; w = fk(e, [(42 * s, fa)])[1]; h = fk(w, [(13 * s, hd)])[1]
        parts += [(side + "_thigh", capsule((hx, hy), k, 15 * s, 12 * s), (hx, hy)),
                  (side + "_shin", capsule(k, a, 11 * s, 8 * s), k),
                  (side + "_foot", capsule(a, toe, 8 * s, 6 * s), a),
                  (side + "_upper", capsule(sh, e, 10 * s, 8 * s), sh),
                  (side + "_fore", capsule(e, w, 8 * s, 6 * s), e),
                  (side + "_hand", capsule(w, h, 7 * s, 6 * s), w)]
    far = [p for p in parts if p[0].startswith("far")]
    near = [p for p in parts if p[0].startswith("near")]
    torso = ("torso", capsule((hx, hy), sh, 20 * s, 23 * s), (hx, hy))
    neckp = ("neck", capsule(sh, neck, 7 * s, 7 * s), sh)
    head = ("head", ell(head_c[0], head_c[1], 17 * s, 21 * s, pose.get("head", -90) + 90), neck)
    return far, [torso, neckp, head], near, dict(head=head_c, sh=sh, hip=(hx, hy), parts=parts)


def face(canvas, J, f, s, tone):
    """Profile details on the head card: nose tab, pencilled eye and brow, mouth, ear piece."""
    hx, hy = J["head"]; d = ImageDraw.Draw(canvas)
    nose = [(hx + f * 15 * s, hy - 6 * s), (hx + f * 24 * s, hy + 4 * s), (hx + f * 15 * s, hy + 6 * s)]
    lay(canvas, poly_mask(canvas.size, [nose], None), tone, 91, shadow=2, sh_alpha=90)
    d.line((hx + f * 5 * s, hy - 5 * s, hx + f * 12 * s, hy - 4 * s), fill=(25, 25, 25, 255), width=max(2, int(2 * s)))
    d.line((hx + f * 3 * s, hy - 11 * s, hx + f * 14 * s, hy - 10 * s), fill=(55, 55, 55, 230), width=max(2, int(2.5 * s)))
    d.line((hx + f * 9 * s, hy + 12 * s, hx + f * 15 * s, hy + 11 * s), fill=(45, 45, 45, 230), width=max(1, int(1.6 * s)))
    lay(canvas, poly_mask(canvas.size, [ell(hx - f * 3 * s, hy + 1 * s, 4.5 * s, 6.5 * s)], None), tone * 0.85, 92,
        shadow=1, sh_alpha=80)


def draw_puppet_paper(canvas, pose, tones, seed, s=1.0, hair=None, hat=None, prop=None, facing=1):
    far, mid, near, J = puppet_parts(pose, s)
    d = ImageDraw.Draw(canvas)
    H = canvas.size
    hx, hy = J["hip"]; sx, sy = J["sh"]
    # clothing cards laid over the bones: shirt (wider than the torso bone), trouser legs
    ta = math.atan2(sy - hy, sx - hx); nx, ny = -math.sin(ta), math.cos(ta)
    shirt = [(hx + nx * 21 * s, hy + ny * 21 * s), (sx + nx * 24 * s, sy + ny * 24 * s),
             (sx - nx * 24 * s, sy - ny * 24 * s), (hx - nx * 21 * s, hy - ny * 21 * s)]
    shirt = [(x - (sx - hx) * 0.0, y) for x, y in shirt]
    order = far + mid[:1] + [("shirt", shirt, (hx, hy))] + \
        ([("behind", prop[1], None)] if prop and prop[0] == "behind" else []) + mid[1:] + near
    for i, (name, pts, joint) in enumerate(order):
        if name == "behind":
            pts(canvas); continue
        key = name.split("_")[-1]
        if key == "upper": key = "sleeve"
        tone = tones.get(key, tones["cloth"]) * (0.78 if name.startswith("far") else 1.0)
        sm = None
        if key in ("head", "hand", "shin", "fore", "shirt", "thigh"):   # mud and sweat, charcoal rubbed on the card
            r = np.random.default_rng(seed + i)
            n = cv2.GaussianBlur(r.normal(0, 1, (H[1] // 3 + 1, H[0] // 3 + 1)).astype(np.float32), (0, 0), 2.5)
            sm = 1 - 0.13 * np.clip(cv2.resize(n, H), -1, 2)
        lay(canvas, poly_mask(H, [pts], seed + i, 10 + 4 * s), tone, seed + i, shadow=int(4 + 2 * s), smudge=sm)
        if name == "shirt":   # pencilled seams: placket, collar, pocket
            mx, my = (sx + hx) / 2, (sy + hy) / 2
            d.line((sx + nx * 2, sy + 8 * s, hx + nx * 2, hy), fill=(70, 70, 70, 160), width=max(1, int(1.5 * s)))
            d.line((sx - nx * 14 * s, sy - ny * 14 * s + 4 * s, sx, sy + 16 * s, sx + nx * 14 * s, sy + ny * 14 * s + 4 * s),
                   fill=(60, 60, 60, 200), width=max(1, int(2 * s)))
        if name == "head":
            face(canvas, J, facing, s, tones["head"])
            if hair: hair(canvas, J)
            if hat: hat(canvas, J)
    for name, pts, joint in order:
        if name in ("behind", "shirt"): continue
        if name.endswith(("shin", "fore", "upper", "thigh", "hand", "foot")) or name == "neck":
            brad(d, *joint, r=max(3, int(4 * s)))
    return J


# ------------------------------------------------------------------ the foraged wedding shoe
def shoe_rgba(width):
    im = Image.open(f"{SRC}/shoe_lacma_bar.jpg").convert("RGB")
    a = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    h, w = a.shape[:2]
    m = np.zeros((h, w), np.uint8); bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(a, m, (int(w * .30), int(h * .32), int(w * .60), int(h * .62)), bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    mm = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(mm); k = 1 + np.argmax(st[1:, 4])
    mm = np.where(lab == k, 255, 0).astype(np.uint8)
    mm = cv2.erode(mm, np.ones((5, 5), np.uint8)); mm = cv2.GaussianBlur(mm, (0, 0), 1.2)
    ys, xs = np.nonzero(mm > 20); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    g = np.asarray(im.convert("L"), np.float32)
    g = np.clip(40 + (g - 120) * 1.25 + 120, 0, 255)          # ivory satin pushed to immaculate white
    out = Image.fromarray(g.astype(np.uint8)).convert("RGBA"); out.putalpha(Image.fromarray(mm))
    out = out.crop(box)
    return out.resize((width, int(width * out.height / out.width)), Image.LANCZOS)


def float_on(canvas, shoe, cx, wl, tilt=-6, sink=0.22, ripple_tone=(235, 225), dark=70, occl=None):
    """Composite the shoe floating at waterline wl: submerged part fades, reflection below, ring ripples."""
    s = shoe.rotate(tilt, expand=True, resample=Image.BICUBIC)
    w, h = s.size; x0 = int(cx - w / 2); y0 = int(wl - h * (1 - sink))
    d = ImageDraw.Draw(canvas)
    # rings first (under the shoe)
    rings = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); rd = ImageDraw.Draw(rings)
    for k, (rx, al) in enumerate(((w * .60, 60), (w * .84, 38), (w * 1.10, 22))):
        for a0 in range(0, 360, 40):                                  # broken arcs, not perfect circles
            rd.arc((cx - rx, wl - rx * .15, cx + rx, wl + rx * .15), a0 + 6 * k, a0 + 28 + 6 * k,
                   fill=(ripple_tone[k % 2],) * 3 + (al,), width=2)
    canvas.alpha_composite(rings.filter(ImageFilter.GaussianBlur(0.8)))
    # reflection: flipped, dark, broken by ripple displacement
    refl = s.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.asarray(refl).copy(); rh = ra.shape[0]
    for yy in range(rh):
        sh = int(4 * math.sin(yy * 0.55)); ra[yy] = np.roll(ra[yy], sh, axis=0)
    ra[..., :3] = (ra[..., :3].astype(np.float32) * 0.55).astype(np.uint8)
    ra[..., 3] = (ra[..., 3].astype(np.float32) * np.linspace(0.55, 0, rh)[:, None]).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(ra), (x0, int(wl - h * sink * 0.2)))
    # the shoe, submerged rows attenuated toward water tone
    sa = np.asarray(s).astype(np.float32)
    rows = np.arange(h) + y0
    sub = np.clip((rows - wl) / (h * sink + 1), 0, 1)[:, None]
    sa[..., :3] = sa[..., :3] * (1 - 0.65 * sub[..., None]) + dark * 0.65 * sub[..., None]
    sa[..., 3] *= (1 - 0.55 * sub)
    piece = Image.fromarray(sa.astype(np.uint8), "RGBA")
    if occl is not None:                                       # #45: whatever is in front of the shoe wins
        oa = np.asarray(occl.crop((x0, y0, x0 + w, y0 + h)).convert("L"), np.float32) / 255
        pa = np.asarray(piece).copy(); pa[..., 3] = (pa[..., 3] * (1 - oa)).astype(np.uint8)
        piece = Image.fromarray(pa)
    canvas.alpha_composite(piece, (x0, y0))
    # waterline glint


# ------------------------------------------------------------------ KF1: multiplane cut-paper puppets
def kf1():
    C = Image.new("RGBA", (PW, PH), (120, 120, 120, 255))
    # plane 4 (far): foraged 1927 jungle, soft
    jung = grey(Image.open(f"{THUMBS}/{RC_C_JUNGLE}")).resize((PW, int(PW * .75)), Image.LANCZOS)
    jung = jung.crop((0, 20, PW, 20 + 470)).filter(ImageFilter.GaussianBlur(2.6))
    jung = print_grade(jung).point(lambda v: int(36 + v * 0.74))
    C.paste(jung.convert("RGBA"), (0, 0))
    # plane 3: foraged water (Indisch allerlei 1920), greyed, laid as the flooded passage
    wat = grey(Image.open(f"{THUMBS}/{INDISCH_WATER}"))
    wat = wat.crop((960, 420, 1370, 1080)).resize((PW, 330), Image.LANCZOS)
    wa = np.asarray(wat, np.float32); wa = (wa - wa.mean()) * 1.7 + 112
    grad = np.linspace(1.0, 0.66, 330)[:, None]
    wat = Image.fromarray(np.clip(wa * grad, 0, 255).astype(np.uint8))
    wm = Image.new("L", (PW, 330), 255); wmask = np.asarray(wm, np.float32)
    wmask[:18] *= np.linspace(0, 1, 18)[:, None]                       # soft far shoreline
    C.paste(wat.convert("RGBA"), (0, 390), Image.fromarray(wmask.astype(np.uint8)))
    # handmade banks: dark torn card with root fingers
    rb = [(760, 418), (900, 404), (1080, 398), (1080, 505), (960, 488), (850, 460)]
    lay(C, poly_mask((PW, PH), [rb], 12, 22), 66, 12, shadow=6, tex=0.09)
    # handmade plank (holds one person): pale card, grain scored in pencil, perspective-cut
    pl = [(360, 552), (900, 438), (906, 452), (372, 578)]
    lay(C, poly_mask((PW, PH), [pl], 13, 6), 170, 13, shadow=10, tex=0.06)
    d = ImageDraw.Draw(C)
    for k in range(6):
        d.line((380, 558 + k * 3.2, 895, 442 + k * 1.4), fill=(118, 118, 114, 90), width=1)
    lb = [(0, 512), (150, 500), (300, 518), (420, 548), (470, 720), (0, 720)]
    roots = [capsule((330 + 25 * k, 560), (300 + 60 * k, 700 - 10 * k), 10, 4) for k in range(3)]
    lay(C, poly_mask((PW, PH), [lb] + roots, 11, 26), 54, 11, shadow=8, tex=0.10)
    # A: on the plank, turned back, the dry bag on his shoulder
    def bag(canvas):
        bx, by = 676, 340
        lay(canvas, poly_mask((PW, PH), [ell(bx, by, 28, 36, 10)], 21, 8), 44, 21, shadow=6, tex=0.04)
        dd = ImageDraw.Draw(canvas)
        dd.line((bx - 20, by - 30, bx + 18, by - 28), fill=(150, 150, 146, 255), width=3)
        dd.line((bx - 18, by - 31, bx - 26, by - 46), fill=(150, 150, 146, 255), width=3)
    poseA = dict(hip=(650, 384), torso=-94, head=-100,
                 far_leg=(98, 92, 180), near_leg=(80, 95, 180),
                 far_arm=(120, 100, 100), near_arm=(140, 175, 185))
    def hatA(canvas, J):
        hx, hy = J["head"]
        lay(canvas, poly_mask((PW, PH), [ell(hx, hy - 15, 28, 6, 4), ell(hx + 1, hy - 22, 16, 11, 4)], 22, 6),
            92, 22, shadow=3, tex=0.05)
    draw_puppet_paper(C, poseA, dict(cloth=150, sleeve=146, head=126, hand=124, foot=56, shin=92, thigh=92),
                      300, s=0.95, hat=hatA, prop=("behind", bag), facing=-1)
    # C: on the near bank behind her, cropped by the frame edge, hand out (wait)
    poseC = dict(hip=(80, 410), torso=-90, head=-92,
                 far_leg=(96, 90, 0), near_leg=(84, 92, 0),
                 far_arm=(95, 80, 80), near_arm=(40, -5, -10))
    def hairC(canvas, J):
        hx, hy = J["head"]
        lay(canvas, poly_mask((PW, PH), [ell(hx - 4, hy - 10, 20, 13, 0)], 23, 6), 38, 23, shadow=0, tex=0.05)
        strip = [(hx - 19, hy - 10), (hx + 19, hy - 12), (hx + 18, hy - 2), (hx - 19, hy + 1)]   # patterned headband
        lay(canvas, poly_mask((PW, PH), [strip], 24, 4), 150, 24, shadow=2, tex=0.05)
        dd = ImageDraw.Draw(canvas)
        for k in range(6): dd.line((hx - 16 + 6 * k, hy - 9, hx - 13 + 6 * k, hy - 3), fill=(60, 60, 60, 200), width=2)
    draw_puppet_paper(C, poseC, dict(cloth=116, sleeve=112, head=134, hand=130, foot=48, shin=100, thigh=100),
                      400, s=1.6, hair=hairC)
    # B: kneeling at the plank's foot, reaching for the shoe
    poseB = dict(hip=(300, 540), torso=-22, head=2,
                 far_leg=(95, 182, 120), near_leg=(84, 176, 110),
                 far_arm=(50, 50, 60), near_arm=(42, 40, 50))
    def hairB(canvas, J):
        hx, hy = J["head"]
        strands = [capsule((hx - 20 + 6 * k, hy - 20), (hx - 34 + 7 * k + (k % 2) * 6, hy + 18 + (k % 3) * 9), 6, 2)
                   for k in range(7)]
        lay(canvas, poly_mask((PW, PH), [ell(hx - 4, hy - 16, 27, 17, 10)] + strands, 24, 10), 204, 24,
            shadow=3, tex=0.07)
    JB = draw_puppet_paper(C, poseB, dict(cloth=196, sleeve=190, head=170, hand=162, foot=70, shin=150, thigh=150),
                           500, s=1.45, hair=hairB)
    # the shoe: foraged photograph, cut out (#29), floating at her fingertips
    shoe = shoe_rgba(200)
    float_on(C, shoe, 585, 628, tilt=-4, dark=95)
    hand = [p for p in JB["parts"] if p[0] == "near_hand"][0]
    lay(C, poly_mask((PW, PH), [hand[1]], 777, 8), 162, 777, shadow=4)       # her hand in front of the shoe (#45)
    # plane 1 (near): foraged 1927 palm fronds keyed to a dark silhouette, defocused, faded at its cut edge
    palms = grey(Image.open(f"{THUMBS}/{RC_C_PALMS}")).resize((760, 570), Image.LANCZOS)
    pa = np.asarray(palms, np.float32) / 255
    alpha = np.clip((0.30 - pa) * 5, 0, 1)
    yy, xx = np.mgrid[0:570, 0:760]
    alpha *= np.clip(1.6 - np.sqrt((xx / 760) ** 2 + (yy / 380) ** 2) * 1.4, 0, 1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 6)
    fr = np.zeros((570, 760, 4), np.uint8); fr[..., :3] = 16; fr[..., 3] = (alpha * 240).astype(np.uint8)
    fr = Image.fromarray(fr)
    lay_ = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    lay_.alpha_composite(fr.crop((0, 0, 560, 330)), (-60, -50))
    lay_.alpha_composite(fr.transpose(Image.FLIP_LEFT_RIGHT).crop((200, 0, 760, 330)), (PW - 480, -40))
    la = np.asarray(lay_).copy()
    la[..., 3] = (la[..., 3] * np.clip((300 - np.arange(PH)) / 160, 0, 1)[:, None]).astype(np.uint8)
    C.alpha_composite(Image.fromarray(la))
    yy, xx = np.mgrid[0:PH, 0:PW]
    v = 1 - 0.26 * (((xx - PW / 2) / (PW / 2)) ** 2 + ((yy - PH / 2) / (PH / 2)) ** 2)
    g = np.asarray(C.convert("L"), np.float32) * v
    pic = print_grade(np.clip(g, 0, 255))
    f = frame_of(pic); caption(f, "« Elle la prend. Il faut refaire l'ordre. »")
    return f


# ------------------------------------------------------------------ KF2: silhouette shadow theatre
def fern(d, x, y, L, ang, side=1, n=16, fill=0):
    pts = []
    for k in range(n):
        t = k / n; a = math.radians(ang + side * 25 * t)
        px, py = x + L * t * math.cos(a), y + L * t * math.sin(a)
        ll = L * 0.22 * math.sin(math.pi * (0.15 + 0.85 * t)) * (1 - 0.5 * t)
        for sgn in (-1, 1):
            b = a + sgn * math.radians(60)
            d.polygon([(px, py), (px + ll * math.cos(b - 0.08), py + ll * math.sin(b - 0.08)),
                       (px + ll * 1.05 * math.cos(b), py + ll * 1.05 * math.sin(b)),
                       (px + 3 * math.cos(a), py + 3 * math.sin(a))], fill=fill)
    d.line([(x, y)] + [(x + L * t * math.cos(math.radians(ang + side * 25 * t)),
                        y + L * t * math.sin(math.radians(ang + side * 25 * t))) for t in np.linspace(0, 1, 20)],
           fill=fill, width=3)


def leaf(d, x, y, L, ang, fill=0):
    a = math.radians(ang); pts = []
    for t in np.linspace(0, 1, 30):
        w = L * 0.38 * math.sin(math.pi * t) ** 0.8
        pts.append((x + L * t * math.cos(a) - w * math.sin(a), y + L * t * math.sin(a) + w * math.cos(a)))
    for t in np.linspace(1, 0, 30):
        w = L * 0.38 * math.sin(math.pi * t) ** 0.8
        pts.append((x + L * t * math.cos(a) + w * math.sin(a), y + L * t * math.sin(a) - w * math.cos(a)))
    d.polygon(pts, fill=fill)


def liana(d, p0, p1, sag, width, fill=0):
    pts = []
    for t in np.linspace(0, 1, 40):
        x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t + sag * math.sin(math.pi * t)
        pts.append((x, y))
    d.line(pts, fill=fill, width=width)


def kf2():
    rng = np.random.default_rng(56)
    # backlight: oiled paper over a lamp, warm-neutral grey falloff (no colour; the print is b/w)
    yy, xx = np.mgrid[0:PH, 0:PW]
    r = np.sqrt(((xx - PW * .55) / PW) ** 2 + ((yy - PH * .40) / PH) ** 2)
    bg = 236 - 150 * np.clip(r, 0, 1) ** 1.3
    bg = bg * paper_tex((PW, PH), 2, 0.025)
    L = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    # far plane: pale grey cut jungle (two sheets of tracing paper behind the screen)
    far = Image.new("L", (PW, PH), 0); df = ImageDraw.Draw(far)
    for k in range(13):
        x = 20 + k * 82 + rng.integers(-35, 35); wv = rng.integers(5, 16); lean = rng.integers(-40, 40)
        df.polygon([(x - wv, 0), (x + wv, 0), (x + lean + wv * 1.4, 440), (x + lean - wv * 1.4, 440)], fill=255)
        for j in range(int(rng.integers(0, 3))):
            leaf(df, x + lean * (0.2 + 0.3 * j), int(rng.integers(40, 380)), int(rng.integers(40, 90)),
                 int(rng.integers(-180, 0)), fill=255)
    for k in range(5):
        liana(df, (int(rng.integers(0, PW)), 0), (int(rng.integers(0, PW)), int(rng.integers(150, 400))),
              int(rng.integers(-60, 60)), 3, 255)
    far = rough(far, 3, 12).filter(ImageFilter.GaussianBlur(2.5))
    L = Image.composite(Image.new("L", (PW, PH), 150), L, far.point(lambda v: v * 0.55))
    # near jungle: black card (roots, trunk, lianas, ferns, big leaves)
    blk = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(blk)
    d.polygon([(0, 0), (150, 0), (120, 210), (170, 330), (150, 420), (0, 470)], fill=255)          # great trunk L
    for k in range(6):                                                                              # buttress roots
        d.polygon([(60 + 18 * k, 300), (90 + 20 * k, 300), (40 + 70 * k, 470), (10 + 66 * k, 470)], fill=255)
    d.polygon([(930, 0), (1080, 0), (1080, 450), (1010, 440), (990, 300), (1000, 150)], fill=255)    # trunk R
    for k in range(5):
        d.polygon([(1010, 260 + 20 * k), (1030, 260 + 20 * k), (900 - 30 * k, 450), (870 - 30 * k, 450)], fill=255)
    liana(d, (140, 20), (960, 60), 150, 7, 255); liana(d, (110, 120), (700, 0), 60, 4, 255)
    liana(d, (300, 0), (330, 300), 40, 3, 255); liana(d, (760, 0), (742, 250), -30, 3, 255)
    for (x, y, Ln, a, s) in ((150, 60, 220, -10, 1), (140, 200, 180, 20, 1), (990, 90, 230, 200, -1),
                             (1000, 220, 200, 170, -1), (60, 420, 200, -40, 1), (1040, 430, 180, 220, -1)):
        fern(d, x, y, Ln, a, s, fill=255)
    for (x, y, Ln, a) in ((150, 380, 100, -20), (170, 400, 80, 10), (1040, 330, 100, 200)):
        leaf(d, x, y, Ln, a, 255)
    # water: four strips of cut card, the light slits between them are the water's glitter
    for k, (y0, amp, ph) in enumerate(((452, 6, 0.0), (500, 8, 1.3), (556, 10, 2.1), (620, 12, 0.7))):
        pts = [(0, PH)] + [(x, y0 + amp * math.sin(x / (38 + 9 * k) + ph) + 3 * math.sin(x / 9.0 + k))
                           for x in range(0, PW + 1, 6)] + [(PW, PH)]
        strip = Image.new("L", (PW, PH), 0); ImageDraw.Draw(strip).polygon(pts, fill=255)
        tone = [70, 45, 22, 0][k]
        L = Image.composite(Image.new("L", (PW, PH), tone), L, strip)
    # banks and plank (black card)
    d.polygon([(0, 440), (330, 430), (345, 450), (250, 520), (0, 560)], fill=255)
    d.polygon([(820, 436), (1080, 420), (1080, 560), (880, 520), (830, 462)], fill=255)
    d.polygon([(330, 444), (840, 438), (840, 450), (330, 457)], fill=255)
    # figures (black card, Reiniger-style fine cuts: fringes, hair, lace)
    figs = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))

    def sil(pose, s, extra=None):
        far_, mid, near_, J = puppet_parts(pose, s)
        m = Image.new("L", (PW, PH), 0); dm = ImageDraw.Draw(m)
        for _, pts, _ in far_ + mid + near_: dm.polygon(pts, fill=255)
        if extra: extra(dm, J)
        return m, J

    def bag_on(dm, J, dx, dy):
        x, y = J["hip"]; x += dx; y += dy
        dm.polygon(ell(x, y, 26, 34, 8), fill=255); dm.line((x - 4, y - 32, J["sh"][0], J["sh"][1]), fill=255, width=4)

    # C (who now goes first) steps on to the plank with the bag
    poseC = dict(hip=(500, 336), torso=-84, head=-92, far_leg=(70, 100, 0), near_leg=(115, 90, 0),
                 far_arm=(120, 80, 60), near_arm=(60, 30, 20))

    def exC(dm, J):
        hx, hy = J["head"]; dm.polygon(ell(hx, hy - 16, 30, 6, -4), fill=255); dm.polygon(ell(hx, hy - 24, 16, 11), fill=255)
        bag_on(dm, J, 28, -30)
        for k in range(7):                                          # shirt fringe, cut with a knife
            x0 = J["hip"][0] - 18 + 6 * k; dm.line((x0, J["hip"][1] - 4, x0 + 2, J["hip"][1] + 10), fill=255, width=2)
    mC, JC = sil(poseC, 0.95, exC)
    # B on the near bank: one arm high with the shoe; she cannot carry the bag any more
    poseB = dict(hip=(290, 322), torso=-88, head=-70, far_leg=(95, 92, 0), near_leg=(80, 95, -10),
                 far_arm=(-60, -80, -85), near_arm=(110, 70, 40))

    def exB(dm, J):
        hx, hy = J["head"]
        for k in range(9):                                          # loose wet hair, strand by strand
            a = math.radians(160 + 14 * k)
            dm.line((hx + 6 * math.cos(a), hy - 10 + 6 * math.sin(a),
                     hx + 26 * math.cos(a) + 4, hy - 4 + 30 * abs(math.sin(a))), fill=255, width=3)
        dm.polygon(ell(hx, hy - 8, 20, 15), fill=255)
        x, y = J["hip"]                                             # torn skirt hem
        dm.polygon([(x - 26, y - 10), (x + 26, y - 10), (x + 34, y + 64), (x - 34, y + 64)], fill=255)
    mB, JB = sil(poseB, 1.0, exB)
    # A turned back on the far bank, waiting; arms out (empty hands)
    poseA = dict(hip=(905, 326), torso=-92, head=-118, far_leg=(95, 90, 180), near_leg=(82, 92, 180),
                 far_arm=(150, 160, 170), near_arm=(120, 130, 150))

    def exA(dm, J):
        hx, hy = J["head"]; dm.polygon(ell(hx, hy - 12, 20, 12), fill=255)
        dm.line((hx - 18, hy - 6, hx + 22, hy - 10), fill=255, width=6)   # headband knot, ends flying
        dm.line((hx + 20, hy - 10, hx + 40, hy + 2), fill=255, width=3); dm.line((hx + 20, hy - 10, hx + 42, hy - 6), fill=255, width=2)
    mA, JA = sil(poseA, 0.9, exA)
    for m in (mA, mC, mB): d.bitmap((0, 0), m, fill=255)
    blk = rough(blk, 9, 6, 0.9)
    L = Image.composite(Image.new("L", (PW, PH), 8), L, blk)
    C = L.convert("RGBA")
    # lace cuts in her blouse: holes of light (Reiniger's filigree)
    dd = ImageDraw.Draw(C)
    sx, sy = JB["sh"]
    for k in range(4):
        for j in range(2):
            cx, cy = sx - 9 + 9 * j, sy + 14 + 14 * k
            dd.ellipse((cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5), fill=(150, 150, 150, 255))
    # the shoe: foraged photograph, the only lit object on the screen, held in her raised hand
    shoe = shoe_rgba(110).rotate(18, expand=True, resample=Image.BICUBIC)
    hand = [p for p in puppet_parts(poseB, 1.0)[3]["parts"] if p[0] == "far_hand"][0][1]
    hx = sum(p[0] for p in hand) / len(hand); hy = sum(p[1] for p in hand) / len(hand)
    glow = Image.new("RGBA", C.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse((hx - 90, hy - 80, hx + 90, hy + 60), fill=(255, 255, 255, 60))
    C.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    C.alpha_composite(shoe, (int(hx - shoe.width * 0.62), int(hy - shoe.height * 0.82)))
    dd.polygon(capsule((hx - 6, hy + 8), (hx + 4, hy - 8), 6, 5), fill=(8, 8, 8, 255))   # fingers over the heel
    # crossing-order ledger, scratched into the black of the bank like a cue
    f = ImageFont.truetype(SANS_B, 18)
    dd.text((22, 640), "ORDRE   1 A · 2 B · 3 C", font=f, fill=(120, 120, 120, 255))
    dd.line((22, 651, 262, 651), fill=(120, 120, 120, 255), width=2)
    dd.text((22, 668), "ORDRE   1 C · 2 A · 3 B", font=f, fill=(225, 225, 225, 255))
    pic = print_grade(C.convert("L"))
    fr = frame_of(pic); caption(fr, "« Les mains prises : le sac passe à l'autre. »", y=676, size=24)
    return fr


# ------------------------------------------------------------------ KF3: archive-led (1927 footage) + foraged shoe
def kf3():
    import subprocess, tempfile, os
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "f.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.0", "-i", f"{CLIPS}/{RC_B_CLIP}", "-frames:v", "1", p],
                   check=True)
    src = grey(Image.open(p))                                   # 320x240
    src = src.crop((6, 4, 316, 236))                            # lose the gate edge
    W43 = 960
    up = src.resize((W43, 720), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    up = print_grade(up)
    C = up.convert("RGBA")
    # occlusion matte: dark trunks/leaves in front of the bright water (#45)
    a = np.asarray(up, np.float32) / 255
    occ = np.clip((0.50 - a) * 5, 0, 1); occ = cv2.GaussianBlur(occ, (0, 0), 1.5)
    occl = Image.fromarray((occ * 255).astype(np.uint8))
    shoe = shoe_rgba(130)
    float_on(C, shoe, 880, 560, tilt=-3, ripple_tone=(250, 210), dark=170, occl=occl)
    pic = Image.new("RGB", (PW, PH), (6, 6, 6)); pic.paste(C.convert("RGB"), ((PW - W43) // 2, 0))
    f = frame_of(pic)
    caption(f, "« Sur l'eau, une chaussure de mariée. Personne ne bouge. »")
    return f


# ------------------------------------------------------------------ board
def board(frames, names):
    ref = Image.open(REF).convert("RGB")
    cw, ch = 980, 551
    refc = Image.new("RGB", (cw, ch), (6, 6, 6)); r = ref.copy(); r.thumbnail((cw, ch)); refc.paste(r, ((cw - r.width) // 2, 0))
    cells = [refc] + [fr.resize((cw, ch), Image.LANCZOS) for fr in frames]
    labels = ["REFERENCE  La Mort en ce jardin (1956), publicity still"] + names
    B = Image.new("RGB", (cw * 2 + 30, (ch + 50) * 2 + 20), (16, 16, 16)); d = ImageDraw.Draw(B)
    f = ImageFont.truetype(SANS_B, 24)
    for k, (im, lab) in enumerate(zip(cells, labels)):
        x = 10 + (k % 2) * (cw + 10); y = 10 + (k // 2) * (ch + 50)
        B.paste(im, (x, y)); d.text((x + 4, y + ch + 10), lab, font=f, fill=(235, 232, 224))
    B.save(f"{OUT}/board.jpg", quality=90)


if __name__ == "__main__":
    which = sys.argv[6] if len(sys.argv) > 6 else "123"
    names = ["1  Trois sur la planche  (cut-paper puppets, multiplane)",
             "2  Ombres de la crue  (silhouette shadow theatre)",
             "3  Le jardin trouvé  (1927 footage + foraged shoe)"]
    fr = []
    for i, fn in zip("123", (kf1, kf2, kf3)):
        if i in which:
            im = fn(); im.save(f"{OUT}/kf-{i}.png"); fr.append(im)
    if which == "123":
        board(fr, names)
