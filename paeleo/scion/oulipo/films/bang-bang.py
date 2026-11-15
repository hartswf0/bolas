"""Bang Bang — a pencil animatic. A pigeon on the station gutter watches a (fictional)
inventor try a paper wing, a rubber-band rotor and a glide that fails. The glide failure
is a five-board sequence. The pigeon's captions read each attempt as sensible bird behaviour."""
import math
from kit import *
from kit_anim import run, hatch_poly, hand_text

film = Film("bang-bang", seconds=30.0, boil=5, wobble=1.5, seed=11)
film.poster_at = 20.6

GR = (34, 32, 42)          # pen line
BLUE = (150, 142, 128)     # faint pencil construction line
RED = (34, 32, 42)         # arrows in the same pen
PAP = (241, 231, 203)      # yellowed paper; drawings fill with it, so they read as line
SURROUND = (247, 246, 242)
PX0, PY0, PX1, PY1 = 40, 34, 920, 430   # board panel
FLOOR = 392                              # platform line inside the board

# (start, end, id, shot, caption, fx)
BOARDS = [
    (0.0, 3.0, "00", "title", "", ""),
    (3.0, 7.0, "01", "wide · the gutter", "PIGEON:  The bell. He pins two timetables to his arms. Flat things want lifting.", "FX bell"),
    (7.0, 11.0, "02", "paper wing", "He beats them fast, as I do on take-off. Paper folds where I’d bend a feather.", "FX flap ×8"),
    (11.0, 16.0, "03", "rubber-band rotor", "He twists a band, like holding a breath — then spends it all at once. So would I.", "FX wind · buzz · snap"),
    (16.0, 18.0, "04", "glide 1/5 · run-up", "Run, open, lean on the air.", "FX steps"),
    (18.0, 19.8, "05", "glide 2/5 · launch", "Good. Level. That is all it takes.", "FX wind"),
    (19.8, 21.6, "06", "glide 3/5 · nose up", "Then he lifts his chin to see further.", "FX wind thins"),
    (21.6, 23.4, "07", "glide 4/5 · stall", "The air lets go of anyone who does that.", "FX —"),
    (23.4, 25.6, "08", "glide 5/5 · down", "He chose the ground. I choose it too, every evening.", "FX BANG"),
    (25.6, 30.0, "09", "two-shot · bench", "From up here it all looked reasonable. He only wanted the ground a little later.", "FX coo"),
]


NOTES = {
    "00": ("Bang Bang — découpage. Le narrateur : le pigeon de la gouttière.", "(the inventor is invented; so are his machines)", ""),
    "01": ("La cloche. Il s'épingle deux horaires aux bras. Les choses plates veulent qu'on les soulève.", "(The bell. He pins two timetables to his arms. Flat things want lifting.)", "ding !"),
    "02": ("Il bat vite, comme moi au départ. Le papier plie là où je plierais une plume.", "(He beats fast, as I do on take-off. Paper folds where I'd bend a feather.)", "flap flap"),
    "03": ("Il tord un élastique comme on retient son souffle, puis il dépense tout d'un coup. Moi aussi.", "(He twists a band like holding a breath, then spends it all at once. So would I.)", "tours : 120 ... crac !"),
    "04": ("Élan, ouvrir, s'appuyer sur l'air.", "(Run, open, lean on the air.)", "1/5"),
    "05": ("Bien. À plat. Il n'en faut pas plus.", "(Good. Level. That is all it takes.)", "2/5"),
    "06": ("Puis il lève le menton pour voir plus loin.", "(Then he lifts his chin to see further.)", "3/5 · nez en l'air 35°"),
    "07": ("L'air lâche tous ceux qui font ça.", "(The air lets go of anyone who does that.)", "4/5 · décroche"),
    "08": ("Il a choisi le sol. Moi aussi, chaque soir.", "(He chose the ground. I choose it too, every evening.)", "5/5 · BANG !"),
    "09": ("D'en haut, tout semblait raisonnable. Il voulait seulement le sol un peu plus tard.", "(From up here it looked reasonable. He only wanted the ground a little later.)", "coo..."),
}

_page = None


def page():
    """Yellowed sheet on a white scanner bed: warm gradient, darker edges, a soft fold,
    and faint show-through of writing on the back."""
    global _page
    if _page is None:
        rs = np.random.RandomState(4)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        img = np.zeros((H, W, 3), np.float32) + np.array(SURROUND, np.float32)
        x0, y0, x1, y1 = 20, 12, 940, 528
        inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
        edge = np.minimum.reduce([xx - x0, x1 - xx, yy - y0, y1 - yy]).clip(0, 60) / 60
        col = np.array(PAP, np.float32) * (0.93 + 0.07 * edge[..., None])
        col *= 1 - 0.035 * np.exp(-((xx - 478) / 14) ** 2)[..., None]   # the fold
        noise = Image.fromarray((rs.uniform(0, 255, (H // 6, W // 6))).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        col *= (0.985 + 0.03 * np.asarray(noise, np.float32)[..., None] / 255)
        img[inside] = col[inside]
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        d.rectangle([x0 + 3, y1, x1 + 3, y1 + 3], fill=(200, 196, 186, 255))
        back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bk = Ink(0, 0)
        bk.img = back
        bk.d = ImageDraw.Draw(back, "RGBA")
        hand_text(bk, (640, 120), "et puis encore une fois la même chose, plus haut", 22, (120, 110, 90), width=260, seed=90, alpha=0.22)
        hand_text(bk, (110, 330), "la planche 4 bis", 22, (120, 110, 90), width=260, seed=91, alpha=0.18)
        back = back.transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(1.4))
        im.paste(back, (0, 0), back)
        _page = im
    return _page


PANEL = (64, 46, 604, 286)       # main board on the sheet
THUMBS = [(64, 318, 324, 432), (344, 318, 604, 432)]
_thumb_cache = {}


def board_image(b, lt, size, index=0):
    sheet = Ink(lt, index, (W, H), 5, 1.5, 11)
    sheet.img = Image.new("RGB", (W, H), PAP)
    sheet.d = ImageDraw.Draw(sheet.img, "RGBA")
    sheet.label = lambda *a, **k: None    # notes live in the margin, in pen
    draw_board(sheet, b, lt)
    im = sheet.img.crop((PX0 + 8, PY0 + 8, PX1 - 8, PY1 - 8)).filter(ImageFilter.MinFilter(3))
    return im.resize(size, Image.LANCZOS)


def framed(ink, box, im):
    x0, y0, x1, y1 = box
    ink.paste(im, (x0, y0))
    ink.rect(x0, y0, x1, y1, color=GR, width=2.2)
    ink.circle(x0 + 14, y0 + 14, 6, fill=GR, color=GR, width=1)   # the punch hole of the reference sheet


def board_at(t):
    for b in BOARDS:
        if b[0] <= t < b[1]:
            return b
    return BOARDS[-1]


# ------------------------------------------------------------- drawings ---

def pigeon(ink, x, y, s=1.0, facing=-1, bob=0.0, color=GR):
    """A sitting pigeon, feet at (x, y)."""
    f = facing
    ink.ellipse(x, y - 22 * s, 30 * s, 19 * s, fill=PAP, color=color, width=2, angle=-0.25 * f)
    hx, hy = x + 26 * s * f, y - 44 * s + bob * 3
    ink.circle(hx, hy, 11 * s, fill=PAP, color=color, width=2)
    ink.poly([(hx + 9 * s * f, hy - 2 * s), (hx + 19 * s * f, hy + 1 * s), (hx + 9 * s * f, hy + 4 * s)], fill=PAP, color=color, width=1.5)
    ink.circle(hx + 4 * s * f, hy - 3 * s, 2.2 * s, fill=color, color=None, width=0)
    ink.poly([(x - 26 * s * f, y - 26 * s), (x - 52 * s * f, y - 18 * s), (x - 48 * s * f, y - 10 * s), (x - 22 * s * f, y - 14 * s)], fill=PAP, color=color, width=1.8)
    ink.line([(x - 6 * s * f, y - 30 * s), (x + 14 * s * f, y - 20 * s), (x - 18 * s * f, y - 16 * s)], color, 1.4)
    for dx in (-4, 6):
        ink.line([(x + dx * s, y - 6 * s), (x + dx * s + 2, y)], GR, 2)
    hatch_poly(ink, [(x - 20 * s, y - 24 * s), (x + 18 * s, y - 14 * s), (x - 10 * s, y - 6 * s)], gap=4, angle=30, color=color, alpha=90)


def inventor(ink, x, y, s=1.0, arms=(-10, -10), wings=False, hat=True, crouch=0.0, legs="stand", tilt=0.0, wing_fold=0.0):
    """Inventor in a long coat, feet at (x, y). arms are angles from horizontal (deg, + up)."""
    h = 130 * s
    hip = (x, y - h * (0.47 - 0.12 * crouch))
    neck = (x + math.sin(tilt) * h * 0.35, hip[1] - h * 0.36 * math.cos(tilt))
    head = (neck[0] + math.sin(tilt) * 14 * s, neck[1] - 13 * s)
    if legs == "stand":
        ink.line([hip, (x - 6 * s, y - h * 0.22), (x - 9 * s, y)], GR, 2.6)
        ink.line([hip, (x + 6 * s, y - h * 0.22), (x + 9 * s, y)], GR, 2.6)
    elif legs == "run":
        ink.line([hip, (x + 18 * s, y - h * 0.25), (x + 28 * s, y - 4)], GR, 2.6)
        ink.line([hip, (x - 12 * s, y - h * 0.2), (x - 34 * s, y - h * 0.08)], GR, 2.6)
    elif legs == "dangle":
        ink.line([hip, (x - 4 * s, y - h * 0.2), (x - 14 * s, y - h * 0.02)], GR, 2.6)
        ink.line([hip, (x + 10 * s, y - h * 0.22), (x + 8 * s, y)], GR, 2.6)
    elif legs == "sit":
        ink.line([hip, (x + 30 * s, hip[1] + 2), (x + 32 * s, y)], GR, 2.6)
        ink.line([hip, (x + 26 * s, hip[1] + 6), (x + 24 * s, y)], GR, 2.6)
    # coat
    ink.poly([(neck[0] - 12 * s, neck[1] + 4), (neck[0] + 12 * s, neck[1] + 4), (hip[0] + 18 * s, hip[1] + 22 * s), (hip[0] - 16 * s, hip[1] + 22 * s)],
             fill=PAP, color=GR, width=2.2)
    hatch_poly(ink, [(neck[0] + 2, neck[1] + 6), (neck[0] + 12 * s, neck[1] + 4), (hip[0] + 18 * s, hip[1] + 22 * s), (hip[0] + 2, hip[1] + 22 * s)], gap=5, angle=60, color=GR, alpha=80)
    sh = (neck[0], neck[1] + 8 * s)
    hands = []
    for k, a in enumerate(arms):
        side = 1 if k == 0 else -1
        ar = math.radians(a)
        el = (sh[0] + side * math.cos(ar) * 26 * s, sh[1] - math.sin(ar) * 26 * s)
        hd = (el[0] + side * math.cos(ar) * 24 * s, el[1] - math.sin(ar) * 24 * s)
        ink.line([sh, el, hd], GR, 2.4)
        hands.append(hd)
        if wings:
            # a timetable pinned along the forearm; folds as it flaps
            fold = wing_fold * side
            tip = (hd[0] + side * math.cos(ar) * 40 * s, hd[1] - math.sin(ar) * 40 * s)
            lo = lambda p: (p[0] - math.sin(ar) * 34 * s * 0.6 * side + fold * 6, p[1] + math.cos(ar) * 34 * s * (0.9 - abs(wing_fold) * 0.4))
            pts = [sh, tip, lo(tip), lo(sh)]
            ink.poly(pts, fill=PAP, color=GR, width=1.8)
            for q in range(1, 5):
                f = q / 5
                a_ = lerp2(sh, tip, f)
                ink.line([a_, lo(a_)], BLUE, 1, alpha=120)
    ink.circle(head[0], head[1], 12 * s, fill=PAP, color=GR, width=2.2)
    ink.line([(head[0] + 4 * s, head[1] - 2 * s), (head[0] + 7 * s, head[1] - 2 * s)], GR, 1.5)  # eye
    if hat:
        ink.line([(head[0] - 16 * s, head[1] - 8 * s), (head[0] + 16 * s, head[1] - 8 * s)], GR, 2.4)
        ink.rect(head[0] - 9 * s, head[1] - 20 * s, head[0] + 9 * s, head[1] - 8 * s, fill=GR, color=GR, width=1)
    return dict(head=head, hands=hands, neck=neck, hip=hip)


def station_bits(ink, bench_x=600, door_x=300, scale=1.0):
    ink.line([(PX0 + 10, FLOOR), (PX1 - 10, FLOOR)], GR, 2.2)
    ink.line([(PX0 + 10, FLOOR + 1), (PX1 - 10, FLOOR + 22)], BLUE, 1, alpha=110)
    door(ink, door_x, FLOOR, w=70, h=140, fill=PAP, color=GR)
    bench(ink, bench_x, FLOOR, w=180, color=GR, fill=PAP)


def arrow(ink, p, q, color=RED, width=2.5):
    ink.line([p, q], color, width)
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    for d in (2.6, -2.6):
        ink.line([q, (q[0] + 12 * math.cos(a + d), q[1] + 12 * math.sin(a + d))], color, width)


def fx(ink, xy, s, size=20, color=RED, rot=0):
    hand_text(ink, (xy[0] - size * len(s) * 0.25, xy[1] - size * 0.4), s, int(size * 1.5), GR, seed=len(s))


def gutter(ink):
    """Foreground gutter the pigeon sits on (narrator's fixed vantage)."""
    pts = [(640, 300), (PX1 - 6, 270), (PX1 - 6, 306), (640, 330)]
    ink.poly(pts, fill=PAP, color=GR, width=2.4)
    hatch_poly(ink, pts, gap=5, angle=-20, color=GR, alpha=110)
    for k in range(5):
        x = 660 + k * 52
        ink.line([(x, 330 - (x - 640) * 0.1), (x - 8, 298 - (x - 640) * 0.1)], GR, 1.2)


def glider(ink, cx, cy, pitch, span=210, crumple=0.0):
    """A big paper glider wing seen from the side-ish: long flat lozenge, pitched."""
    ca, sa = math.cos(pitch), math.sin(pitch)
    pts = []
    for px, py in [(-span / 2, 0), (-span / 2 + 30, -14), (span / 2, -8), (span / 2 - 20, 6)]:
        px += crumple * 12 * math.sin(px * 0.08)
        pts.append((cx + px * ca + py * sa, cy - px * sa + py * ca + crumple * 10 * math.cos(px * 0.06)))
    ink.poly(pts, fill=PAP, color=GR, width=2)
    for k in range(1, 6):
        f = k / 6
        a, b = lerp2(pts[0], pts[2], f), lerp2(pts[1], pts[3], f)
        ink.line([a, b], BLUE, 1, alpha=100)
    return pts


# --------------------------------------------------------------- boards ---

def b_title(ink, lt):
    hand_text(ink, (300, 120), "BANG  BANG", 64, GR, seed=5)
    hand_text(ink, (330, 230), "découpage · 10 planches · 30 s", 26, GR, seed=6)
    pigeon(ink, 480, 380, 1.4, facing=-1)


def b_wide(ink, lt):
    station_bits(ink, bench_x=330, door_x=150)
    # bell on its bracket
    sw = math.sin(lt * 16) * math.exp(-lt * 1.6) * 0.5 if lt < 3 else 0
    ink.line([(230, 150), (260, 150)], GR, 2)
    ink.poly([(250 - 12 + 8 * sw, 186), (250 + 12 + 8 * sw, 186), (250 + 7, 160), (250 - 7, 160)], fill=PAP, color=GR, width=2)
    if lt < 1.4:
        fx(ink, (300, 150), "DING", 18)
    up = 10 + 50 * ease(lt, 1.2, 2.4)
    inventor(ink, 360, FLOOR - 40, 0.72, arms=(up, up), wings=lt > 0.8)
    gutter(ink)
    pigeon(ink, 800, 288, 1.5, facing=-1, bob=math.sin(lt * 3))
    ink.line([(780, 240), (430, 300)], BLUE, 1, alpha=110)  # eyeline
    ink.label((PX0 + 16, PY1 - 22), "camera: behind the pigeon · it only sees what this frame sees", 11, BLUE)


def b_flap(ink, lt):
    station_bits(ink, bench_x=420, door_x=150)
    k = int(lt * 4)
    up = k % 2 == 0 and lt < 3.4
    a = 50 if up else -35
    p = inventor(ink, 420, FLOOR - 40, 1.0, arms=(a, a), wings=True, wing_fold=0.0 if up else 0.7, crouch=0.2 if not up else 0)
    if lt < 3.4:
        fx(ink, (250 if up else 600, 140), "flap", 24)
        for q in range(3):
            ang = (k * 1.7 + q) % 6
            ink.rect(560 + q * 40 + 12 * math.sin(ang), 150 + 30 * q + lt * 18, 574 + q * 40, 160 + 30 * q + lt * 18, fill=PAP, color=GR, width=1.3)
    else:
        fx(ink, (620, 160), "(nothing)", 18, MUTED)
    arrow(ink, (220, 200), (220, 140) if up else (220, 260))
    ink.label((PX0 + 16, PY1 - 22), "2 drawings alternating on 6s · feet never leave the bench", 11, BLUE)


def b_rotor(ink, lt):
    station_bits(ink, bench_x=470, door_x=170)
    wind = ease(lt, 0.0, 2.4)
    spin = lt >= 2.6 and lt < 3.6
    lift = 10 * math.sin(math.pi * ramp(lt, 2.7, 3.5)) if spin else 0
    p = inventor(ink, 470, FLOOR - 40 - lift, 1.0, arms=(60, 20) if lt < 2.6 else (-30, -30), hat=True)
    hx, hy = p["head"]
    top = hy - 70
    ink.line([(hx, hy - 20), (hx, top)], GR, 2.4)
    # the twisted band along the mast
    turns = int(4 + 14 * wind) if lt < 3.6 else 0
    pts = [(hx + (5 if q % 2 else -5), lerp(hy - 22, top + 4, q / max(1, turns))) for q in range(turns + 1)]
    if lt < 3.6 and len(pts) > 1:
        ink.line(pts, GR, 1.6, rough=False)
    ang = lt * 40 if spin else (wind * 6 if lt < 2.6 else 0.3)
    for sgn in (1, -1):
        L = 46 * math.cos(ang) * sgn
        ink.ellipse(hx + L / 2, top, abs(L) / 2 + 2, 5, fill=PAP, color=GR, width=1.8)
    if spin:
        ink.ellipse(hx, top, 48, 8, color=GR, width=1, alpha=110)
        fx(ink, (hx + 110, top), "bzzzz", 22)
        arrow(ink, (hx - 90, FLOOR - 30), (hx - 90, FLOOR - 60))
        ink.label((hx - 150, FLOOR - 20), "lift: 1 cm", 12, RED)
    elif lt < 2.6:
        ink.label((hx + 70, top + 30), f"winds: {int(120 * wind)}", 16, RED)
        fx(ink, (hx + 90, top - 10), "crk crk", 18)
    else:
        ink.line([(hx - 30, top - 10), (hx + 34, top + 12), (hx - 20, top + 24)], RED, 2.5)
        fx(ink, (hx + 90, top - 6), "SNAP", 26)
        ink.ellipse(hx + 60, FLOOR - 4, 20, 4, color=GR, width=1.6)  # band on the floor
    ink.label((PX0 + 16, PY1 - 22), "hold the wind-up; rotor spins 1 s; band breaks", 11, BLUE)


def b_glide(ink, lt, step):
    station_bits(ink, bench_x=330, door_x=140)
    bx = 330
    if step == 1:  # crouched on the bench, wing over head; run-up arrow
        p = inventor(ink, bx - 40 + 40 * ease(lt, 0.3, 1.8), FLOOR - 40, 0.9, arms=(80, 80), crouch=0.4, legs="run")
        glider(ink, p["head"][0], p["head"][1] - 40, 0.0)
        arrow(ink, (bx - 80, FLOOR - 140), (bx + 60, FLOOR - 140))
    elif step == 2:  # launch, level
        x = lerp(bx + 60, bx + 200, ease(lt, 0, 1.8))
        y = FLOOR - 120
        p = inventor(ink, x, y, 0.9, arms=(80, 80), legs="run", tilt=0.25)
        glider(ink, p["head"][0], p["head"][1] - 34, 0.0)
        arrow(ink, (x + 120, y - 150), (x + 230, y - 150))
        ink.line([(bx + 40, FLOOR - 80), (x - 20, y - 10)], BLUE, 1, alpha=120)
    elif step == 3:  # nose up: the readable failure
        x = bx + 210 + 20 * ease(lt, 0, 1.8)
        y = FLOOR - 140
        pitch = math.radians(lerp(5, 35, ease(lt, 0.1, 1.0)))
        p = inventor(ink, x, y, 0.9, arms=(80, 80), legs="dangle", tilt=-0.15)
        g = glider(ink, p["head"][0], p["head"][1] - 34, pitch)
        ink.line([(p["head"][0] - 130, p["head"][1] - 34), (p["head"][0] + 130, p["head"][1] - 34)], BLUE, 1.4, alpha=160)
        ink.arc(p["head"][0], p["head"][1] - 34, 90, -pitch, 0, RED, 2)
        ink.label((p["head"][0] + 120, p["head"][1] - 40), f"{int(math.degrees(pitch))}°  NOSE UP", 16, RED)
        ink.label((p["head"][0] + 120, p["head"][1] - 18), "airflow breaks off the top", 12, RED)
        for q in range(3):
            yy = p["head"][1] - 30 - q * 12
            ink.line([(x + 60, yy), (x + 120, yy - 8 + 6 * math.sin(lt * 8 + q))], RED, 1.5, alpha=180)
    elif step == 4:  # stall: drops straight
        x = bx + 230
        y = lerp(FLOOR - 140, FLOOR - 40, ease(lt, 0.1, 1.6) ** 1.6)
        p = inventor(ink, x, y, 0.9, arms=(90, 70), legs="dangle")
        glider(ink, p["head"][0] - 10, p["head"][1] - 36, math.radians(lerp(35, 70, ease(lt, 0, 1.2))), crumple=0.4)
        for q in range(4):
            ink.line([(x - 40 + q * 26, FLOOR - 170), (x - 40 + q * 26, y - 70)], RED, 1.2, alpha=150)
        arrow(ink, (x + 110, FLOOR - 170), (x + 110, FLOOR - 70))
    elif step == 5:  # down: sat on the platform under a crumpled wing
        x = bx + 230
        shake = math.sin(lt * 40) * math.exp(-lt * 5) * 6
        inventor(ink, x, FLOOR, 0.9, arms=(-20, -40), legs="sit", hat=False)
        glider(ink, x + 10 + shake, FLOOR - 120, math.radians(-20), crumple=1.0)
        ink.ellipse(x - 50, FLOOR - 2, 14, 5, fill=GR, color=GR, width=1)  # the hat
        if lt < 1.2:
            fx(ink, (x - 150, FLOOR - 170), "BANG", 46)
            for q in range(8):
                a = q * math.pi / 4
                ink.line([(x - 150 + 60 * math.cos(a), FLOOR - 170 + 34 * math.sin(a)),
                          (x - 150 + 80 * math.cos(a), FLOOR - 170 + 46 * math.sin(a))], RED, 2)
    gutter(ink)
    pigeon(ink, 830, 286, 1.2, facing=-1, bob=math.sin(lt * 4) * (1 if step < 5 else 0.2))


def b_bench(ink, lt):
    station_bits(ink, bench_x=470, door_x=200)
    inventor(ink, 430, FLOOR - 1, 1.0, arms=(-50, -60), legs="sit", hat=True)
    # the pigeon flies down and lands on the bench beside him
    f = ease(lt, 0.2, 1.6)
    px, py = lerp(820, 540, f), lerp(200, FLOOR - 78, f)
    if f < 1:
        for sgn in (1, -1):
            wa = math.sin(lt * 20) * 0.8
            ink.line([(px, py - 20), (px + 30 * sgn, py - 40 - 20 * wa * sgn)], GR, 2)
    pigeon(ink, px, py, 1.0, facing=-1)
    glider(ink, 650, FLOOR - 10, 0.0, span=160, crumple=1.0)
    ink.label((PX0 + 16, PY1 - 22), "hold 3 s · end of sequence", 11, BLUE)


def draw_board(ink, b, lt):
    bid = b[2]
    if bid == "00":
        b_title(ink, lt)
    elif bid == "01":
        b_wide(ink, lt)
    elif bid == "02":
        b_flap(ink, lt)
    elif bid == "03":
        b_rotor(ink, lt)
    elif bid in ("04", "05", "06", "07", "08"):
        b_glide(ink, lt, int(bid) - 3)
    else:
        b_bench(ink, lt)


@film.picture
def frame(t, ink):
    ink._grain = True
    ink.paste(page())
    b = board_at(t)
    lt = t - b[0]
    k = BOARDS.index(b)
    x0, y0, x1, y1 = PANEL
    framed(ink, PANEL, board_image(b, lt, (x1 - x0, y1 - y0), int(t * FPS)))
    for j, box in enumerate(THUMBS):   # the next boards wait below, as on a storyboard sheet
        if k + 1 + j < len(BOARDS):
            nb = BOARDS[k + 1 + j]
            if nb[2] not in _thumb_cache:
                _thumb_cache[nb[2]] = board_image(nb, 0.0, (box[2] - box[0], box[3] - box[1]))
            framed(ink, box, _thumb_cache[nb[2]])
            hand_text(ink, (box[0] + 30, box[1] + 4), nb[2], 16, GR, seed=k + j)
    # pen notes in the right column
    note, aside, margin = NOTES[b[2]]
    hand_text(ink, (640, 40), f"{b[2]}   {b[0]:.0f}–{b[1]:.0f} s   {b[3]}", 19, (80, 70, 60), width=290, seed=k)
    a = ease(lt, 0.05, 0.35)
    y = hand_text(ink, (640, 96), note, 25, GR, width=280, seed=10 + k, alpha=a)
    hand_text(ink, (648, y + 8), aside, 17, (86, 78, 66), width=270, seed=40 + k, alpha=a)
    if margin:
        hand_text(ink, (660, 404), margin, 26, GR, width=260, seed=70 + k, rot=4)
    # pen-ruled timing line with a tick per board and the playhead
    yl = 478
    ink.line([(64, yl), (904, yl)], GR, 1.8)
    for s_, e_, bid, *_ in BOARDS:
        xx = 64 + s_ / 30 * 840
        ink.line([(xx, yl - 7), (xx, yl + 7)], GR, 1.6)
        hand_text(ink, (xx + 6, yl + 8), bid, 14, GR if bid == b[2] else (130, 120, 100), seed=int(bid))
    ph = 64 + t / 30 * 840
    ink.circle(ph, yl, 5, fill=GR, color=GR, width=1)


@film.sound
def sound(mix):
    R = mix.rate
    mix.room(0, 30, gain=0.015)
    for s, *_ in BOARDS[1:]:
        mix.whoosh(s - 0.08, 0.18, 0.05)      # board change: a sheet slides
    # 01 bell, a few steps
    mix.bell(3.1, 587, 3.0, 0.3, -0.4)
    mix.murmur(3.4, 3.2, gain=0.05, pitch=330, pan=0.5)
    # 02 flaps: a paper burst per down-stroke
    for k in range(14):
        at = 7.0 + k * 0.25
        if k % 2 == 1:
            x = mix.band(mix.noise(0.12), 600, 5000) * np.exp(-np.linspace(0, 6, int(0.12 * R)))
            mix.add(x, at, 0.35, -0.2 if k % 4 == 1 else 0.2)
    mix.murmur(7.3, 3.4, gain=0.05, pitch=330, pan=0.5)
    # 03 rotor: ratchet clicks speeding up, buzz, snap
    t, gap = 11.0, 0.16
    while t < 13.5:
        mix.click(t, 0.12, 0.1, 5000, 0.015)
        t += gap
        gap = max(0.05, gap * 0.93)
    buzz = mix.tone(95, 1.0, "square") * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * mix.t(1.0)))
    mix.add(buzz * mix.env(len(buzz), 0.03, 0.1, 0.8, 0.2), 13.6, 0.12)
    mix.click(14.6, 0.5, 0, 7000, 0.02)
    mix.pluck(14.6, 880, 0.4, 0.15)
    mix.murmur(11.4, 4.2, gain=0.05, pitch=330, pan=0.5)
    # 04–08 glide: steps, a widening then thinning rush, silence, BANG
    mix.steps(16.3, 17.9, 0.2, 0.18, "wood")
    w = mix.band(mix.noise(5.0), 300, 3000)
    env = np.interp(np.arange(len(w)) / R, [0, 1.0, 2.6, 3.6, 5.0], [0, 1, 0.6, 0.0, 0])
    mix.add(w * env, 17.8, 0.14)
    mix.thud(23.45, 55, 0.9)
    mix.add(mix.band(mix.noise(0.4), 200, 2500) * np.exp(-np.linspace(0, 6, int(0.4 * R))), 23.45, 0.35)
    for at, dur in ((16.2, 1.6), (18.1, 1.6), (20.0, 1.5), (21.8, 1.5), (23.9, 1.6)):
        mix.murmur(at, dur, gain=0.045, pitch=330, pan=0.5)
    # 09 wingbeats down, two coos, last line
    for k in range(6):
        mix.whoosh(25.8 + k * 0.18, 0.12, 0.05, 0.4)
    for at in (27.4, 28.3):
        tt = mix.t(0.5)
        coo = np.sin(2 * np.pi * (310 + 40 * np.sin(2 * np.pi * 2 * tt)) * tt) * np.sin(np.pi * tt / 0.5) ** 2
        mix.add(coo, at, 0.12, 0.2)
    mix.murmur(25.9, 3.6, gain=0.045, pitch=330, pan=0.3)
    mix.reverb(0.12)


if __name__ == "__main__":
    run(film)
