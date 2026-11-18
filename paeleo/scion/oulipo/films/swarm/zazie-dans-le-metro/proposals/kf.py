# Round-2 keyframes for zazie-dans-le-metro.  Usage:
#   python3 -I kf.py <sources/zazie-dans-le-metro/r2> <girl_mask.png> <out_dir> <reference.webp>
# Sources (see proposals.md): Commons "Little girl laughing with excitement in France" (Basile Morin, CC BY-SA 4.0);
# LoC Photochrom prints of Paris, Detroit Publishing Co. (no known restrictions).
import sys, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S, MASK, OUT, REF = sys.argv[1:5]
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
rng = np.random.default_rng(1960)


def eastman(im, warm=1.0):
    """Warm, slightly low-contrast print grade (applied to foraged plates; no grain, no texture)."""
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    a = 0.06 + 0.9 * a                                  # lifted blacks, soft highlights
    a = a ** np.array([0.92, 0.98, 1.10])               # red lifted, blue lowered
    g = a.mean(axis=2, keepdims=True)
    a = g + (a - g) * 0.92
    a[..., 0] *= 1 + 0.05 * warm; a[..., 2] *= 1 - 0.07 * warm
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def soft_paris(name, box=None, blur=16, size=(960, 720)):
    im = Image.open(f"{S}/{name}").convert("RGB")
    if box: im = im.crop(box)
    im = im.resize(size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))
    return eastman(im, 1.1)


def pillar(pic):
    f = Image.new("RGB", (1280, 720), (8, 8, 8)); f.paste(pic, (160, 0)); return f


def caption(img, text, y=668, size=26):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(SERIF_I, size)
    w = d.textlength(text, font=f); x = (img.width - w) / 2
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
        d.text((x + dx, y + dy), text, font=f, fill=(20, 12, 8))
    d.text((x, y), text, font=f, fill=(250, 240, 220))


def paper_tex(size, seed):
    """Fibre texture for the handmade paper pieces (multiplied on to flat colour)."""
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (size[1] // 4 + 1, size[0] // 4 + 1)).astype(np.float32)
    n = cv2.resize(n, size, interpolation=cv2.INTER_CUBIC)
    f = r.normal(0, 1, (size[1], size[0])).astype(np.float32)
    f = cv2.GaussianBlur(f, (0, 0), 0.8)
    t = 1 + 0.035 * n + 0.025 * f
    return t


def paper_piece(canvas, poly, colour, seed, shadow=7, edge=True, blur_sh=6, sh_alpha=110):
    """Lay one cut-paper piece: drop shadow, fibre texture, slightly torn edge."""
    W, H = canvas.size
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    if edge:   # rough the cut edge a little (scissor wobble)
        a = np.asarray(m).astype(np.float32)
        r = np.random.default_rng(seed)
        nz = cv2.resize(r.normal(0, 1, (H // 6 + 1, W // 6 + 1)).astype(np.float32), (W, H))
        a = cv2.GaussianBlur(a, (0, 0), 1.6) + nz * 22
        m = Image.fromarray(np.clip((a - 128) * 4 + 128, 0, 255).astype(np.uint8))
    sh = Image.new("RGBA", (W, H), (30, 14, 6, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur_sh)).point(lambda v: v * sh_alpha // 255))
    canvas.alpha_composite(sh, (shadow, shadow))
    t = paper_tex((W, H), seed)
    col = np.clip(np.array(colour, np.float32)[None, None, :] * t[..., None], 0, 255).astype(np.uint8)
    piece = Image.fromarray(col, "RGB").convert("RGBA"); piece.putalpha(m)
    canvas.alpha_composite(piece)
    return m


def brad(d, x, y, r=7):
    d.ellipse((x - r, y - r, x + r, y + r), fill=(176, 138, 62), outline=(96, 70, 30), width=2)
    d.ellipse((x - r * .45, y - r * .55, x - r * .05, y - r * .15), fill=(236, 210, 140))


# ------------------------------------------------------------------ KF1: foraged laughing child
def kf1():
    img = cv2.imread(f"{S}/Little_girl_laughing_with_excitement_in_France.jpg")
    a = cv2.imread(MASK, 0)
    a = cv2.GaussianBlur(a, (0, 0), 2.2)
    x0, y0, x1, y1 = 390, 150, 1690, 1125                 # close 4:3 head-and-fists framing
    rgb = Image.fromarray(cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2RGB))
    al = Image.fromarray(a[y0:y1, x0:x1])
    rgb = eastman(rgb, 0.9).filter(ImageFilter.GaussianBlur(0.7))
    girl = rgb.convert("RGBA"); girl.putalpha(al)
    girl = girl.resize((960, 720), Image.LANCZOS)
    bg = soft_paris("loc_05184.jpg", box=(330, 190, 990, 685), blur=11)   # rue Royale, Madeleine columns
    pic = bg.convert("RGBA")
    # light wrap: bleed a little background into the matte edge
    pic.alpha_composite(girl)
    pic = pic.convert("RGB")
    f = pillar(pic)
    caption(f, "« Le métro ? En grève. »  Elle rit, et Paris saute.")
    return f


# ------------------------------------------------------------------ KF2: articulated cut-paper Zazie
def kf2():
    W, H = 1920, 1440   # drawn at 2x then reduced
    bg = soft_paris("loc_05184.jpg", box=(260, 150, 980, 690), blur=12, size=(W, H)).convert("RGBA")
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = 980, 860
    # jumper + orange collar
    paper_piece(c, [(330, 1440), (420, 1290), (640, 1225), (1320, 1225), (1560, 1300), (1650, 1440)], (92, 70, 60), 11)
    paper_piece(c, [(600, 1250), (760, 1190), (980, 1235), (1200, 1190), (1360, 1250), (1260, 1330), (980, 1300), (700, 1330)],
                (226, 104, 40), 12)
    # neck
    paper_piece(c, [(860, 1080), (1100, 1080), (1120, 1240), (980, 1270), (840, 1240)], (222, 160, 132), 13)
    # back hair (behind face) — bob, blown to the right
    back = [(560, 560), (640, 380), (820, 300), (1080, 290), (1290, 360), (1420, 500), (1480, 700), (1500, 900),
            (1560, 1080), (1430, 1060), (1330, 1000), (1300, 1120), (1180, 1020), (760, 1030), (660, 1120), (630, 990),
            (560, 1050), (600, 880), (560, 760)]
    paper_piece(c, back, (120, 62, 34), 14)
    # face
    face = []
    for k in range(64):
        t = 2 * math.pi * k / 64
        rx, ry = 305, 400
        x = cx + rx * math.sin(t) * (1 - 0.10 * max(0, math.cos(t)))
        y = cy + ry * -math.cos(t) * (0.92 if math.cos(t) > 0 else 1.0)
        face.append((x, y))
    paper_piece(c, face, (240, 194, 164), 15)
    d = ImageDraw.Draw(c)
    # cheeks (separate thin pink tissue, translucent)
    for (x, y) in ((760, 930), (1205, 930)):
        ch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ch).ellipse((x - 95, y - 62, x + 95, y + 62), fill=(232, 120, 100, 120))
        c.alpha_composite(ch.filter(ImageFilter.GaussianBlur(14)))
    # laughing eyes: closed upward arcs, cut from dark paper
    for ex, flip in ((830, 1), (1130, -1)):
        arc = []
        for k in range(21):
            u = k / 20; x = ex - 95 + 190 * u; y = 770 - 40 * math.sin(math.pi * u) + 6 * flip * (u - .5)
            arc.append((x, y))
        inner = [(x, y + 20 - 14 * abs(i - 10) / 10) for i, (x, y) in enumerate(arc)][::-1]
        paper_piece(c, arc + inner, (58, 30, 22), 16 + ex, shadow=3, blur_sh=2, edge=False)
        # lash flick
        d.line([(ex + flip * 92, 768), (ex + flip * 122, 750)], fill=(58, 30, 22), width=9)
    # brows lifted high with the laugh
    for ex in (830, 1130):
        paper_piece(c, [(ex - 90, 668), (ex - 20, 640), (ex + 80, 650), (ex + 82, 664), (ex - 20, 660), (ex - 88, 684)],
                    (104, 54, 32), 20 + ex, shadow=3, blur_sh=2, edge=False)
    # nose: a folded tab (two tones)
    paper_piece(c, [(975, 800), (1010, 940), (1050, 975), (990, 995), (935, 975)], (226, 172, 140), 24, shadow=4)
    paper_piece(c, [(990, 995), (935, 975), (955, 965), (995, 980)], (196, 128, 104), 25, shadow=0, edge=False)
    # mouth: jaw piece (replacement mouth #4 of the laugh cycle)
    mouth = []
    for k in range(41):
        u = k / 40; x = 760 + 440 * u; y = 1020 + 18 * math.sin(math.pi * u) - 10 * (u - .5) ** 2
        mouth.append((x, y))
    for k in range(41):
        u = 1 - k / 40; x = 760 + 440 * u; y = 1030 + 205 * math.sin(math.pi * u) ** 0.85
        mouth.append((x, y))
    paper_piece(c, mouth, (92, 22, 26), 26, shadow=5)
    # tongue
    paper_piece(c, [(870, 1185), (925, 1135), (1050, 1130), (1110, 1185), (1045, 1220), (925, 1220)], (196, 72, 74), 27,
                shadow=2, edge=False)
    # upper teeth with Zazie's gap: two strips
    paper_piece(c, [(815, 1034), (968, 1044), (966, 1094), (900, 1098), (825, 1080)], (246, 240, 222), 28, shadow=3, edge=False)
    paper_piece(c, [(994, 1044), (1145, 1034), (1137, 1080), (1060, 1098), (996, 1094)], (246, 240, 222), 29, shadow=3, edge=False)
    d = ImageDraw.Draw(c)
    for x in (870, 920, 1045, 1095):
        d.line([(x, 1044), (x + 2, 1092)], fill=(214, 204, 182), width=3)
    # lower lip highlight strip
    paper_piece(c, [(880, 1238), (1080, 1238), (1050, 1252), (910, 1252)], (214, 112, 106), 30, shadow=0, edge=False)
    # fringe: separate strands, each pinned at the crown, wind lifts them to the right
    roots = [(700, 470), (760, 420), (830, 385), (900, 365), (975, 355), (1050, 360), (1120, 375), (1190, 400), (1255, 440), (1310, 490)]
    for i, (rx, ry) in enumerate(roots):
        tx = rx + 170 + 22 * i + 30 * math.sin(i * 2.1)
        ty = ry + 330 - 12 * i + 25 * math.cos(i * 1.3)
        mx, my = rx + 40 + 0.35 * (tx - rx), ry + 0.55 * (ty - ry) - 20
        wdt = 78 - 4 * abs(i - 4)
        pts_l, pts_r = [], []
        for k in range(17):
            u = k / 16
            x = (1 - u) ** 2 * rx + 2 * (1 - u) * u * mx + u * u * tx
            y = (1 - u) ** 2 * ry + 2 * (1 - u) * u * my + u * u * ty
            dx = 2 * (1 - u) * (mx - rx) + 2 * u * (tx - mx); dy = 2 * (1 - u) * (my - ry) + 2 * u * (ty - my)
            n = math.hypot(dx, dy); nx, ny = -dy / n, dx / n
            w = wdt * (1 - u) ** 0.7 + 4
            pts_l.append((x + nx * w / 2, y + ny * w / 2)); pts_r.append((x - nx * w / 2, y - ny * w / 2))
        tone = [(132, 68, 36), (152, 84, 46), (112, 56, 30)][i % 3]
        paper_piece(c, pts_l + pts_r[::-1], tone, 40 + i, shadow=6, blur_sh=5)
    # stray strands flying off in the wind (thin paper slivers)
    for i, (sx, sy, ex2, ey2) in enumerate(((1330, 560, 1640, 470), (1380, 660, 1720, 640), (1270, 420, 1560, 330),
                                            (1400, 760, 1680, 820))):
        mx, my = (sx + ex2) / 2, (sy + ey2) / 2 - 40
        L, R = [], []
        for k in range(13):
            u = k / 12
            x = (1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * ex2
            y = (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ey2
            w = 16 * (1 - u) + 2
            L.append((x, y - w / 2)); R.append((x, y + w / 2))
        paper_piece(c, L + R[::-1], (146, 80, 44), 60 + i, shadow=5, blur_sh=4)
    d = ImageDraw.Draw(c)
    # split-pin pivots of the rig (crown, jaw, neck)
    for (x, y) in ((975, 357), (765, 1030), (1195, 1030), (980, 1235)):
        brad(d, x, y, 9)
    # gentle head tilt (the frame catches the rig mid-laugh, rotated about the neck pin)
    c = c.rotate(-4, resample=Image.BICUBIC, center=(980, 1235))
    k = 1.17; c = c.resize((int(W * k), int(H * k)), Image.LANCZOS)
    c = c.crop((int(W * (k - 1) / 2) + 10, int(H * (k - 1)) - 40, int(W * (k - 1) / 2) + 10 + W, int(H * (k - 1)) - 40 + H))
    bg.alpha_composite(c)
    pic = bg.convert("RGB").resize((960, 720), Image.LANCZOS)
    f = pillar(pic)
    caption(f, "« Zazie, si tu veux voir le métro… »  — le vent de la rue Royale.")
    return f


# ------------------------------------------------------------------ KF3: bouche de métro, kinetic type
def kf3():
    W, H = 1920, 1440
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # extreme close-up: one sheet of skin paper fills the frame; Paris is only seen through the mouth
    paper_piece(c, [(-20, -20), (W + 20, -20), (W + 20, H + 20), (-20, H + 20)], (236, 186, 152), 101, shadow=0, edge=False)
    for (x, y, r) in ((150, 620, 300), (1770, 620, 300)):
        ch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ch).ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=(232, 112, 92, 130))
        c.alpha_composite(ch.filter(ImageFilter.GaussianBlur(50)))
    # nose tip and nostrils (top edge), cut paper with shadow
    paper_piece(c, [(780, -40), (1140, -40), (1180, 90), (1120, 170), (960, 200), (800, 170), (740, 90)], (226, 168, 136), 105, shadow=10)
    for x in (880, 1040):
        paper_piece(c, [(x - 50, 150), (x + 40, 140), (x + 50, 170), (x - 40, 180)], (150, 84, 70), 106 + x, shadow=0, edge=False)
    def curve(f, x0=140, x1=1780, n=80):
        return [(x0 + (x1 - x0) * k / n, f(k / n)) for k in range(n + 1)]
    sn = lambda u: max(0.0, math.sin(math.pi * u))
    bow = lambda u: 58 * math.exp(-((u - .5) / .055) ** 2)
    o_top = curve(lambda u: 600 - 300 * sn(u) ** 0.6 + bow(u))
    o_bot = curve(lambda u: 600 + 700 * sn(u) ** 0.8)
    i_top = curve(lambda u: 610 - 140 * sn(u) ** 0.9, 220, 1700)
    i_bot = curve(lambda u: 610 + 560 * sn(u) ** 0.85, 220, 1700)
    paper_piece(c, o_top + o_bot[::-1], (194, 58, 54), 102, shadow=12, blur_sh=9)
    m_mask = paper_piece(c, i_top + i_bot[::-1], (36, 12, 14), 103, shadow=0)
    # through the mouth: a soft Paris (Place Clichy photochrom) seen down a tunnel, with its tram coming out
    tun = soft_paris("loc_09974.jpg", box=(180, 380, 760, 700), blur=6, size=(1100, 620)).convert("RGBA")
    tv = Image.new("RGBA", (W, H), (36, 12, 14, 255)); tv.alpha_composite(tun, (410, 560))
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((470, 600, 1450, 1150), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(70))
    tv2 = Image.new("RGBA", (W, H), (36, 12, 14, 255)); tv2.paste(tv, (0, 0), vig)
    td = ImageDraw.Draw(tv2)
    for k in range(5, 0, -1):   # tiled vault rings of a métro tunnel, cut from card
        s_ = 0.19 * k + 0.15; w2, h2 = 700 * s_, 420 * s_
        td.ellipse((960 - w2, 880 - h2, 960 + w2, 880 + h2), outline=(205, 170, 120, 255), width=int(4 + 3 * k))
    tram_src = Image.open(f"{S}/loc_09974.jpg").convert("RGB")
    tm = Image.new("L", tram_src.size, 0)
    ImageDraw.Draw(tm).polygon([(333, 520), (480, 519), (485, 531), (484, 580), (346, 584), (334, 536)], fill=255)
    tram = eastman(tram_src, 1.2).convert("RGBA"); tram.putalpha(tm.filter(ImageFilter.GaussianBlur(0.8)))
    tram = tram.crop((328, 514, 490, 588)).resize((640, 292), Image.LANCZOS)
    sh = Image.new("RGBA", tram.size, (10, 4, 2, 0)); sh.putalpha(tram.split()[3].filter(ImageFilter.GaussianBlur(8)).point(lambda v: v // 2))
    tv2.alpha_composite(sh, (652, 790)); tv2.alpha_composite(tram, (640, 772))
    tv2.putalpha(ImageChops.multiply(tv2.split()[3], m_mask))
    c.alpha_composite(tv2)
    # teeth = letter tiles. Upper row DOUK|IPU with Zazie's gap; lower row DONKTAN.
    fnt = ImageFont.truetype(SERIF_B, 104)
    def tile(ch, x, ytop, w, h, rot, seed, hang=True):
        t = Image.new("RGBA", (int(w) + 50, int(h) + 50), (0, 0, 0, 0))
        if hang: poly = [(25, 25), (25 + w, 25), (25 + w - 5, 25 + h - 14), (25 + w / 2, 25 + h), (30, 25 + h - 12)]
        else: poly = [(30, 37), (25 + w / 2, 25), (25 + w - 5, 39), (25 + w, 25 + h), (25, 25 + h)]
        paper_piece(t, poly, (248, 241, 222), seed, shadow=6, blur_sh=4)
        td = ImageDraw.Draw(t); tw = td.textlength(ch, font=fnt)
        td.text((25 + (w - tw) / 2, 25 + h * (0.06 if hang else 0.16)), ch, font=fnt, fill=(152, 44, 26))
        t = t.rotate(rot, resample=Image.BICUBIC, expand=True)
        c.alpha_composite(t, (int(x - t.width / 2), int(ytop - 25)))
    up = "DOUK IPU"; xs = np.linspace(430, 1490, len(up))
    for i, ch in enumerate(up):
        if ch == " ": continue
        u = (xs[i] - 220) / 1480
        tile(ch, xs[i], 610 - 140 * sn(u) ** 0.9 - 14, 118, 140, (i - 3.5) * -1.8, 200 + i)
    lo = "DONKTAN"; xs = np.linspace(560, 1360, len(lo))
    for i, ch in enumerate(lo):
        u = (xs[i] - 220) / 1480
        yb = 610 + 560 * sn(u) ** 0.85 + 10
        drop = 70 if i == 6 else 0          # the last tooth has come loose: it leaves to join the queue
        tile(ch, xs[i] + (30 if i == 6 else 0), yb - 132 + drop - 60 * (i == 6), 112, 132, (i - 3) * 2.4 + (22 if i == 6 else 0),
             300 + i, hang=False)
    paper_piece(c, [(640, 395), (900, 352), (960, 372), (1020, 352), (1280, 395), (960, 410)], (224, 110, 98), 104, shadow=0, edge=False)
    paper_piece(c, [(700, 1215), (1220, 1215), (1150, 1250), (770, 1250)], (220, 104, 96), 107, shadow=0, edge=False)
    # two auburn fringe strands blown in at the top corner (the wind of KF2)
    for i, (sx, sy, ex, ey) in enumerate(((1500, -40, 1900, 260), (1640, -40, 1940, 150))):
        mx, my = (sx + ex) / 2 - 40, (sy + ey) / 2 + 40
        L, R = [], []
        for k in range(15):
            u = k / 14
            x = (1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * ex; y = (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ey
            w = 70 * (1 - u) + 4; L.append((x - w / 2, y)); R.append((x + w / 2, y))
        paper_piece(c, L + R[::-1], (130, 66, 34), 400 + i, shadow=8)
    pic = c.convert("RGB").resize((960, 720), Image.LANCZOS)
    f = pillar(pic)
    caption(f, "« Doukipudonktan ! »  — la bouche de métro rit ; le tram en sort.")
    return f


def board(frames, names):
    ref = Image.open(REF).convert("RGB")
    tw, th = 960, 720
    ref = ref.resize((tw, th), Image.LANCZOS)
    cells = [pillar(ref)] + frames
    labels = ["REFERENCE  Zazie dans le métro (1960)"] + names
    cw, ch = 980, 551 + 50
    B = Image.new("RGB", (cw * 2 + 20, ch * 2 + 20), (18, 18, 18)); d = ImageDraw.Draw(B)
    f = ImageFont.truetype(SANS_B, 26)
    for k, (im, lab) in enumerate(zip(cells, labels)):
        x = 10 + (k % 2) * (cw + 0); y = 10 + (k // 2) * ch
        B.paste(im.resize((980, 551), Image.LANCZOS), (x, y))
        d.text((x + 4, y + 558), lab, font=f, fill=(240, 225, 200))
    B.save(f"{OUT}/board.jpg", quality=90)


if __name__ == "__main__":
    which = sys.argv[5] if len(sys.argv) > 5 else "123"
    names = ["1  Rire, et Paris saute  (foraged photo, jump-cut)",
             "2  Zazie en papier  (articulated cutout)",
             "3  Bouche de métro  (kinetic typography)"]
    fr = []
    for i, fn in zip("123", (kf1, kf2, kf3)):
        if i in which:
            im = fn(); im.save(f"{OUT}/kf-{i}.png"); fr.append(im)
    if which == "123":
        board(fr, names)
