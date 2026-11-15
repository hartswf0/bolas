"""La Machine à tuer le temps — eight drawn shots frozen in one pool, two cuts.

CUT A reads as an ordinary parcel handoff, CUT B as an illicit one. Every
picture frame on screen is a frame of one of the eight pooled clips (rendered
once, hashed), placed by an explicit edit recipe: asset, in/out, integer
output frames, direction. Screening 1 plays both cuts side by side over one
shared sound bed; screening 2 plays each cut with its own final mix.
"""
import json
import hashlib
import math
from PIL import Image
from kit_cinema_a import *

SW, SH = 800, 450
N = 24  # source frames per pooled clip
COAT1 = (70, 82, 98)
COAT2 = (58, 52, 50)
WOOD = (150, 110, 70)
SKIN = (224, 196, 170)


# ---------------------------------------------------------------- shots ---

def wall(ink, color=WASH):
    ink.fill(color)
    for x in range(0, SW + 1, 50):
        ink.line([(x, 0), (x, SH)], RULE, 1, alpha=140)
    for y in range(0, SH + 1, 25):
        ink.line([(0, y), (SW, y)], RULE, 1, alpha=110)


def s_clock(k, u, ink):
    wall(ink)
    ink.rect(380, 0, 420, 70, fill=(80, 70, 60), color=INK, width=2)
    clock(ink, 400, 215, 150, hours=3 + 58 / 60)
    sec = 8 + 14 * u
    a = 2 * math.pi * sec / 60 - math.pi / 2
    ink.line([(400 - math.cos(a) * 30, 215 - math.sin(a) * 30), (400 + math.cos(a) * 132, 215 + math.sin(a) * 132)], ACCENT, 2, rough=False)
    ink.circle(400, 215, 5, fill=ACCENT, color=ACCENT, width=1, rough=False)
    ink.text((400, 290), "GARE", "serif", 26, MUTED, anchor="mm")


def counter(ink):
    ink.fill((214, 205, 190))
    ink.hatch(0, 0, SW, 270, gap=14, angle=90, color=RULE, width=1, alpha=120)
    ink.rect(-10, 280, SW + 10, SH + 10, fill=WOOD, color=INK, width=3)
    for y in (320, 372, 418):
        ink.line([(0, y), (SW, y + 4)], (120, 85, 50), 1.5, alpha=160)


def hand(ink, hx, hy, side, sleeve, cuff=PAGE, ring=False, open_=False):
    """A forearm from the left (side=1) or right (side=-1) ending at (hx, hy)."""
    edge = -40 if side == 1 else SW + 40
    ink.poly([(edge, hy - 34), (hx - side * 70, hy - 30), (hx - side * 70, hy + 30), (edge, hy + 36)], fill=sleeve, color=INK, width=2.5)
    ink.rect(min(hx - side * 70, hx - side * 82), hy - 30, max(hx - side * 70, hx - side * 82), hy + 30, fill=cuff, color=INK, width=2)
    ink.ellipse(hx - side * 32, hy, 46, 30, fill=SKIN, color=INK, width=2.5)
    if open_:
        for f in range(4):
            fy = hy - 22 + f * 14
            ink.line([(hx - side * 8, fy), (hx + side * 34, fy - 4 + f * 2)], INK, 7)
            ink.line([(hx - side * 8, fy), (hx + side * 34, fy - 4 + f * 2)], SKIN, 4)
        ink.line([(hx - side * 40, hy - 26), (hx - side * 10, hy - 44)], INK, 9)
        ink.line([(hx - side * 40, hy - 26), (hx - side * 10, hy - 44)], SKIN, 6)
        if ring:
            ink.ellipse(hx + side * 8, hy - 8, 5, 9, fill=BRASS, color=INK, width=1.5)
    else:
        for f in range(4):
            ink.arc(hx + side * 2, hy - 18 + f * 12, 9, -math.pi / 2, math.pi / 2, INK, 2)


def s_parcel(k, u, ink):
    counter(ink)
    hx = lerp(150, 420, ease(u, 0, 1))
    hy = 250
    # parcel under the hand
    px = hx + 40
    ink.rect(px - 80, hy - 40, px + 80, hy + 56, fill=(190, 152, 104), color=INK, width=2.5)
    ink.line([(px, hy - 40), (px, hy + 56)], (90, 70, 50), 2)
    ink.line([(px - 80, hy + 8), (px + 80, hy + 8)], (90, 70, 50), 2)
    ink.circle(px, hy + 8, 10, fill=ACCENT, color=INK, width=1.5)
    ink.label((px - 72, hy + 30), "No 0417", 12, (80, 60, 40))
    hand(ink, hx - 30, hy - 36, 1, COAT1)


def s_hand2(k, u, ink):
    counter(ink)
    hx = lerp(SW + 40, 480, ease(u, 0, 1))
    hand(ink, hx, 232, -1, COAT2, cuff=(200, 190, 175), ring=True, open_=True)


def s_door(k, u, ink):
    wall(ink, (226, 216, 200))
    ink.d.rectangle([0, 420, SW, SH], fill=(160, 150, 136))
    # light under the door
    ink.d.rectangle([318, 416, 482, 421], fill=(245, 215, 140, 220))
    door(ink, 400, 418, 160, 320, sign="SERVICE")
    a = 0.55 * math.sin(math.pi * u)  # the handle dips and returns
    kx, ky = 400 - 80 + 160 - 12, 418 - 160
    ink.line([(kx, ky), (kx - math.cos(a) * 34, ky + math.sin(a) * 34)], INK, 7, rough=False)
    ink.line([(kx, ky), (kx - math.cos(a) * 34, ky + math.sin(a) * 34)], BRASS, 4, rough=False)


def s_glance(k, u, ink):
    ink.fill(SKIN)
    ink.d.rectangle([0, 0, SW, 70], fill=COAT2)  # hat brim
    ink.line([(0, 70), (SW, 74)], INK, 3)
    look = -ease(u, 0.15, 0.85)
    for cx in (250, 550):
        ink.stroke([(cx - 110, 150), (cx - 20, 128), (cx + 100, 146)], INK, 9)  # brow
        ink.ellipse(cx, 230, 105, 46, fill=PAGE, color=INK, width=3)
        ix = cx + look * 52
        ink.circle(ix, 232, 34, fill=(96, 74, 52), color=INK, width=2)
        ink.circle(ix, 232, 15, fill=INK, color=INK, width=1)
        ink.circle(ix + 9, 222, 5, fill=PAGE, color=PAGE, width=1)
        ink.arc(cx, 262, 110, math.pi * 1.15, math.pi * 1.85, INK, 3)  # lid
        ink.line([(cx - 95, 300), (cx + 80, 305)], (180, 150, 125), 2)
    ink.line([(400, 200), (392, 330), (412, 345)], (170, 135, 110), 3)


SLIP = None


def slip():
    global SLIP
    if SLIP is None:
        i = Ink(0, 0, (150, 90), boil=0, wobble=0.6)
        i.img = Image.new("RGBA", (150, 90), (0, 0, 0, 0))
        from PIL import ImageDraw
        i.d = ImageDraw.Draw(i.img, "RGBA")
        i.rect(2, 2, 147, 87, fill=PAGE, color=INK, width=2)
        i.text((75, 20), "RECEIPT", "mono", 13, INK, anchor="mm")
        i.text((75, 42), "No 0417", "mono", 15, ACCENT, anchor="mm")
        i.text((75, 64), "1 parcel · 15:58", "mono", 11, MUTED, anchor="mm")
        SLIP = i.img
    return SLIP


def s_receipt(k, u, ink):
    ink.fill((150, 144, 134))
    for y in range(0, SH, 60):
        ink.line([(0, y), (SW, y)], (120, 114, 104), 2, alpha=200)
    for x in range(-400, SW + 400, 90):
        ink.line([(x, 0), (SW / 2 + (x - SW / 2) * 1.4, SH)], (120, 114, 104), 2, alpha=200)
    f = ease(u, 0, 0.85)
    y = lerp(-60, 300, f)
    x = 400 + 60 * math.sin(u * 7) * (1 - f)
    ang = 35 * math.sin(u * 9) * (1 - f) + 12
    if f > 0.98:
        ink.ellipse(400, 330, 90, 14, fill=(0, 0, 0, 50), color=None)
    rot_paste(ink, slip(), x, y, ang)


def arch(ink):
    ink.fill((206, 196, 180))
    ink.d.rectangle([0, 330, SW, SH], fill=(170, 160, 146))
    ink.line([(0, 330), (SW, 330)], INK, 2)
    ink.d.rectangle([450, 70, 650, 330], fill=(250, 238, 205))
    ink.d.pieslice([450, -30, 650, 170], 180, 360, fill=(250, 238, 205))
    ink.arc(550, 70, 100, math.pi, 2 * math.pi, INK, 4)
    ink.line([(450, 70), (450, 330)], INK, 4)
    ink.line([(650, 70), (650, 330)], INK, 4)
    ink.poly([(450, 330), (650, 330), (720, SH), (380, SH)], fill=(240, 226, 190, 160), color=None)
    bench(ink, 200, 380, 220)


def s_exit(k, u, ink):
    arch(ink)
    f = ease(u, 0, 1)
    figure(ink, lerp(330, 560, f), lerp(420, 326, f), lerp(1.55, 0.95, f), "walk", phase=u * 2.2, facing=1, coat=COAT1, hat=True)


def s_threshold(k, u, ink):
    arch(ink)
    for m in range(14):
        x = 470 + (m * 53 % 170) + 12 * math.sin(u * 3 + m)
        y = 120 + (m * 97 % 200) - u * 30
        ink.circle(x, y, 2, fill=(255, 250, 230), color=None)


SHOTS = [("clock", s_clock), ("parcel", s_parcel), ("hand2", s_hand2), ("door", s_door),
         ("glance", s_glance), ("receipt", s_receipt), ("exit", s_exit), ("threshold", s_threshold)]
LABEL = {"clock": "clock", "parcel": "hand + parcel", "hand2": "second hand", "door": "door",
         "glance": "glance", "receipt": "dropped receipt", "exit": "person exiting", "threshold": "empty threshold"}
POOL = {}
for i, (name, fn) in enumerate(SHOTS):
    POOL[name] = build_clip(fn, N, (SW, SH), boil=6, wobble=1.1, seed=31 + i)
POOL_HASH = hashlib.sha1("".join(frames_hash(POOL[n]) for n, _ in SHOTS).encode()).hexdigest()[:12]
SMALL = {n: [f.resize((456, 256), Image.LANCZOS) for f in fr] for n, fr in POOL.items()}
THUMB = {n: [f.resize((208, 117), Image.LANCZOS) for f in fr] for n, fr in POOL.items()}
ASSET_ID = {n: i + 1 for i, (n, _) in enumerate(SHOTS)}
HUE = {"clock": (176, 138, 62), "parcel": (190, 152, 104), "hand2": (120, 110, 100), "door": (120, 96, 80),
       "glance": (200, 160, 130), "receipt": (230, 226, 214), "exit": (70, 82, 98), "threshold": (240, 226, 190)}

# ---------------------------------------------------------- edit recipes ---
# (asset, in, out, output_frames, direction)
CUT_A = [("threshold", 0, 23, 48, 1), ("clock", 0, 23, 60, 1), ("parcel", 0, 23, 72, 1), ("hand2", 0, 23, 60, 1),
         ("glance", 0, 23, 36, 1), ("receipt", 0, 23, 72, 1), ("exit", 0, 23, 84, 1), ("door", 0, 0, 48, 1)]
CUT_B = [("glance", 0, 23, 72, 1), ("door", 0, 23, 48, 1), ("parcel", 0, 23, 36, 1), ("hand2", 0, 23, 24, 1),
         ("glance", 0, 23, 36, -1), ("receipt", 0, 23, 96, 1), ("clock", 0, 23, 36, 1), ("exit", 0, 23, 36, 1),
         ("threshold", 0, 23, 96, 1)]
for cut in (CUT_A, CUT_B):
    assert sum(e[3] for e in cut) == 480
    for a, i0, i1, n, d in cut:  # validator: every edit resolves inside the pool
        assert a in POOL and 0 <= i0 <= i1 < N
CUT_LEN = 20.0
RECIPE_HASH = {k: hashlib.sha1(json.dumps(c).encode()).hexdigest()[:8] for k, c in (("A", CUT_A), ("B", CUT_B))}


def edit_starts(cut):
    out, a = [], 0
    for e in cut:
        out.append(a / FPS)
        a += e[3]
    return out


def resolve(cut, k):
    """Output frame k of a cut -> (edit index, asset, source frame)."""
    a = 0
    for idx, (asset, i0, i1, n, d) in enumerate(cut):
        if k < a + n:
            j = k - a
            src = i0 + (i1 - i0) * j / max(1, n - 1)
            if d < 0:
                src = i1 - (src - i0)
            return idx, asset, int(round(src))
        a += n
    asset, i0, i1, n, d = cut[-1]
    return len(cut) - 1, asset, i1 if d > 0 else i0


def strip(ink, cut, k, x0, y0, w, h, label, short=False):
    total = sum(e[3] for e in cut)
    idx, _, src = resolve(cut, k)
    a = 0
    for j, (asset, i0, i1, n, d) in enumerate(cut):
        xa, xb = x0 + w * a / total, x0 + w * (a + n) / total
        on = j == idx
        ink.d.rectangle([xa + 1, y0, xb - 1, y0 + h], fill=HUE[asset] + (255 if on else 90,))
        if xb - xa > 26:
            ink.text(((xa + xb) / 2, y0 + h / 2), f"{ASSET_ID[asset]:02d}{'' if d > 0 else 'r'}", "mono", 11,
                     INK if on else RULE, anchor="mm")
        a += n
    px = x0 + w * min(k, total) / total
    ink.line([(px, y0 - 4), (px, y0 + h + 4)], ACCENT, 2, rough=False)
    asset, i0, i1, n, d = cut[idx]
    if short:
        ink.text((x0, y0 + h + 8), f"edit {idx + 1}/{len(cut)} · {ASSET_ID[asset]:02d} {LABEL[asset]} · src {src:02d} · {'fwd' if d > 0 else 'rev'}", "mono", 11, RULE)
        return
    ink.text((x0, y0 + h + 8), f"{label} · edit {idx + 1}/{len(cut)} · asset {ASSET_ID[asset]:02d} {LABEL[asset]} · src {src:02d} of {i0}–{i1} · "
             f"{n} fr {'fwd' if d > 0 else 'rev'}", "mono", 11, RULE)


SEGS = [("title", 2.4), ("pool", 4.4), ("card1", 1.6), ("split", CUT_LEN), ("cardA", 1.6), ("A", CUT_LEN),
        ("cardB", 1.6), ("B", CUT_LEN), ("report", 3.2)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)
film = Film("la-machine-a-tuer-le-temps", seconds=TOTAL, boil=0, wobble=0)
film.poster_at = ST["B"] + 10.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    ink.fill(NIGHT)
    if seg == "title":
        title_card(ink, "La Machine à tuer le temps", "eight drawn shots · one frozen pool · two cuts")
    elif seg == "pool":
        ink.text((W / 2, 28), "THE POOL", "mono", 15, PAGE, anchor="mm")
        for i, (name, _) in enumerate(SHOTS):
            cx, cy = 26 + (i % 4) * 230, 62 + (i // 4) * 196
            k = int(lt * FPS) % N
            ink.paste(THUMB[name][k], (cx, cy))
            ink.d.rectangle([cx, cy, cx + 207, cy + 116], outline=RULE + (255,), width=1)
            ink.text((cx, cy + 126), f"{i + 1:02d} {LABEL[name]}", "mono", 12, PAGE)
            ink.text((cx, cy + 144), f"{N} fr · sha {frames_hash(POOL[name])[:8]}" if i == 0 or lt > 0.2 else "", "mono", 10, MUTED)
        ink.text((W / 2, H - 22), f"pool hash {POOL_HASH} · frozen before cutting · no frame outside these {8 * N}", "mono", 12, BRASS, anchor="mm")
    elif seg in ("card1", "cardA", "cardB"):
        t1 = {"card1": ("Screening 1", "CUT A and CUT B side by side · one shared sound bed"),
              "cardA": ("CUT A · ordinary handoff", f"final mix A · recipe {RECIPE_HASH['A']}"),
              "cardB": ("CUT B · illicit", f"final mix B · recipe {RECIPE_HASH['B']}")}[seg]
        title_card(ink, *t1, size=44)
    elif seg == "split":
        k = min(479, int(lt * FPS))
        ink.text((W / 2, 30), "SCREENING 1 · shared bed", "mono", 14, BRASS, anchor="mm")
        for j, (cut, nm) in enumerate(((CUT_A, "CUT A"), (CUT_B, "CUT B"))):
            x0 = 16 + j * 472
            _, asset, src = resolve(cut, k)
            ink.paste(SMALL[asset][src], (x0, 92))
            ink.text((x0, 70), nm + (" · ordinary" if j == 0 else " · illicit"), "mono", 13, PAGE)
            strip(ink, cut, k, x0, 366, 456, 22, nm, short=True)
    elif seg in ("A", "B"):
        cut = CUT_A if seg == "A" else CUT_B
        k = min(479, int(lt * FPS))
        _, asset, src = resolve(cut, k)
        ink.paste(POOL[asset][src], (80, 12))
        strip(ink, cut, k, 80, 478, 800, 20, "CUT " + seg)
    elif seg == "report":
        ink.text((W / 2, 70), "picture-reuse report", "serif", 40, PAGE, anchor="mm")
        rows = [f"pool {POOL_HASH} · 8 assets · {8 * N} source frames",
                f"CUT A  recipe {RECIPE_HASH['A']} · 8 edits · 480 fr · assets 8 1 2 3 5 6 7 4",
                f"CUT B  recipe {RECIPE_HASH['B']} · 9 edits · 480 fr · assets 5 4 2 3 5(rev) 6 1 7 8",
                "out-of-pool frames: 0 · generated inserts: 0 · geometry/colour untouched",
                "fixture  A=[clock, hand, door, exit]  B=[exit, door, hand, clock]  in pool: pass",
                "audio swap (screening 1 to 2) leaves both picture recipes unchanged"]
        for i, r in enumerate(rows):
            ink.text((W / 2, 150 + i * 44), r, "mono", 15, PAGE if i else BRASS, anchor="mm")
    if seg in ("A", "B", "split"):
        return
    fade_edges(ink, lt, dur, 0.25)


@film.sound
def sound(mix):
    s = ST["split"]
    # ---- shared bed (screening 1): room tone, a wall-clock tick, distant platform air
    mix.room(s, CUT_LEN, 0.03)
    for k in range(int(CUT_LEN)):
        mix.click(s + k + 0.5, 0.12, 0.1, 3000, 0.02)
    mix.wind(s, CUT_LEN, 0.03)
    mix.bell(s + 0.3, 587, 3.0, 0.08, -0.4)

    # ---- final mix A: ordinary
    a = ST["A"]
    ea = [a + x for x in edit_starts(CUT_A)]
    mix.room(a, CUT_LEN, 0.03)
    mix.bell(a + 0.2, 659, 3.0, 0.14, -0.3)
    for k in range(int(CUT_LEN)):
        mix.click(a + k + 0.5, 0.06, 0.1, 3000, 0.02)
    for i, f in enumerate((392, 494, 587, 494)):  # a small friendly figure as the parcel crosses
        mix.pluck(ea[2] + 0.4 + i * 0.35, f, 1.2, 0.12, -0.2)
    mix.murmur(ea[3] + 0.6, 1.4, 0.08, 150, 0.2, seed=4)   # "thank you"
    mix.murmur(ea[4] + 0.1, 0.9, 0.06, 115, -0.2, seed=8)
    paper_flutter(mix, ea[5] + 0.3, 1.8, 0.06)
    mix.steps(ea[6] + 0.2, ea[7], 0.48, 0.18, "stone", -0.1, 0.5)
    mix.pluck(ea[7] + 0.3, 784, 1.5, 0.08)

    # ---- final mix B: illicit
    b = ST["B"]
    eb = [b + x for x in edit_starts(CUT_B)]
    mix.room(b, CUT_LEN, 0.02)
    mix.drone(b, CUT_LEN, (41.2, 58.3, 82.4), 0.09, attack=2, release=1.5)
    mix.add(mix.tone(1975, 3.0) * mix.env(int(3.0 * mix.rate), 1.2, 0.1, 1.0, 1.0) * 0.4, b, 0.05, 0.3)  # thin held whistle on the glance
    heartbeat(mix, b + 1.0, eb[5] + 3.5, 66, accel=1.6, gain=0.28)
    mix.click(eb[1] + 0.9, 0.35, 0.4, 2000, 0.06)  # the handle
    mix.thud(eb[3] + 0.2, 60, 0.3)
    paper_flutter(mix, eb[5] + 0.2, 2.6, 0.05)
    mix.thud(eb[5] + 3.4, 38, 0.6, 0, 0.8)
    mix.note(eb[5] + 3.4, 69.3, 2.4, 0.12, 0, "saw", 0.01, 1.5, 0.2)
    mix.note(eb[5] + 3.4, 73.4, 2.4, 0.1, 0, "saw", 0.01, 1.5, 0.2)
    for k in range(6):
        mix.click(eb[6] + k * 0.25, 0.25, 0.1, 3500, 0.02)
    mix.steps(eb[7], eb[8], 0.26, 0.25, "stone", 0, 0.7)
    mix.bell(eb[8] + 1.0, 330, 4.0, 0.06, 0.5)


if __name__ == "__main__":
    film.render()
