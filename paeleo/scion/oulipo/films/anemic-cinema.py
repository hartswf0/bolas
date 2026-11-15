"""Anémic cinéma — two optical discs, two text discs, strict alternation, then a still pass."""
import math
from PIL import Image, ImageDraw
from kit import *

film = Film("anemic-cinema", seconds=24, boil=0, wobble=0)
R = 220
CX, CY = W // 2, H // 2 - 6
# exposure score: (start, end, kind, id)
SCORE = [(0.0, 1.6, "title", None), (1.6, 6.4, "optical", "A"), (6.4, 10.4, "text", "1"),
         (10.4, 15.2, "optical", "B"), (15.2, 20.4, "text", "2"), (20.4, 24.0, "still", None)]
PUN1 = "A KEY LEFT ON A BENCH IS A BELL THAT FORGOT TO RING ·  "
PUN2 = "THE DOOR STAYS SHUT SO THE STATION CAN KEEP ITS SECRET ·  "


def text_disc(phrase, turns=3.1, size=22):
    img = Image.new("RGBA", (2 * R + 8, 2 * R + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = R + 4
    d.ellipse([4, 4, 2 * R + 4, 2 * R + 4], fill=PAGE + (255,), outline=INK + (255,), width=3)
    f = font("mono", size)
    # glyph path: archimedean spiral inward, order preserved
    rr, a = R - 26, -math.pi / 2
    chars = (phrase * 2)
    for ch in chars:
        if rr < 34:
            break
        g = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((size, size), ch, font=f, fill=INK + (255,), anchor="mm")
        g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        img.paste(g, (int(x - size), int(y - size)), g)
        step = (size * 0.66) / rr
        a += step
        rr -= (size * 1.9) * step / (2 * math.pi)
    d.ellipse([c - 6, c - 6, c + 6, c + 6], fill=ACCENT + (255,))
    return img


DISCS = {"1": text_disc(PUN1), "2": text_disc(PUN2, size=24)}


def optical(ink, ang, sign, motif):
    ink.circle(CX, CY, R, fill=PAGE, color=INK, width=3, rough=False)
    n = 13
    for k in range(n, 0, -1):
        f = k / n
        r = R * f * 0.97
        off = sign * (1 - f) * R * 0.34
        ox, oy = CX + off * math.cos(ang), CY + off * math.sin(ang)
        col = INK if k % 2 else ACCENT
        ink.circle(ox, oy, r, fill=PAGE if k % 2 == 0 else WASH, color=col, width=4 if k % 2 else 2, rough=False, steps=120)
    # motif sits at the innermost centre: bench key (A) or the closed service door (B)
    off = sign * R * 0.34
    mx, my = CX + off * math.cos(ang), CY + off * math.sin(ang)
    if motif == "key":
        key_shape(ink, mx - 18, my, 0.9, angle=ang)
    else:
        ink.rect(mx - 12, my - 20, mx + 12, my + 20, fill=(120, 96, 80), color=INK, width=2, rough=False)
        ink.circle(mx + 6, my, 2.5, fill=BRASS, color=INK, width=1, rough=False)


def turntable(ink):
    ink.fill(NIGHT)
    ink.circle(CX, CY, R + 14, fill=(40, 38, 42), color=(70, 66, 70), width=2, rough=False)


@film.picture
def frame(t, ink):
    ink.vignette(0.5)
    for a, b, kind, ident in SCORE:
        if a <= t < b:
            break
    local = t - a
    fade = min(1, local / 0.25, (b - t) / 0.25)
    if kind == "title":
        ink.fill(NIGHT)
        ink.text((W / 2, H / 2 - 10), "ANÉMIC", "serif", 64, PAGE, anchor="mm")
        ink.label((W / 2, H / 2 + 40), "two optical discs · two text discs · one still pass", 14, RULE, anchor="mm")
        return
    if kind != "still":
        turntable(ink)
    else:
        ink.fill(NIGHT)
    if kind == "optical":
        # 0.5 turns per second, fixed speed -> angle(t+2) == angle(t) mod 2pi
        ang = 2 * math.pi * 0.5 * t
        optical(ink, ang, +1 if ident == "A" else -1, "key" if ident == "A" else "door")
        ink.label((24, H - 30), f"OPTICAL {ident} · {'expands toward you' if ident == 'A' else 'recedes'} · 0.5 rev/s", 13, RULE)
    elif kind == "text":
        speed = 0.16 if ident == "1" else 0.09  # rev/s; the second is the reading disc
        disc = DISCS[ident].rotate(math.degrees(2 * math.pi * speed * t), resample=Image.BICUBIC)
        ink.paste(disc, (CX - R - 4, CY - R - 4))
        ink.label((24, H - 30), f"TEXT {ident} · {speed:.2f} rev/s" + (" · reading speed" if ident == "2" else ""), 13, RULE)
    else:  # still pass: both text discs side by side, unmoving
        for k, ident in enumerate(("1", "2")):
            sm = DISCS[ident].resize((300, 300), Image.LANCZOS)
            ink.paste(sm, (W / 2 - 330 + k * 360, H / 2 - 160))
        ink.label((W / 2, H - 34), "STILL PASS · layout without motion", 13, RULE, anchor="mm")
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=NIGHT + (int(255 * (1 - fade)),))


@film.sound
def sound(mix):
    # a soft pulse cues each switch; turntable hum underneath; the bell from the seed
    mix.drone(0, 24, (49, 98), gain=0.05, attack=1, release=2)
    for a, b, kind, ident in SCORE[1:]:
        mix.click(a, 0.35, 0, 2500)
        mix.thud(a, 55, 0.25)
    for k in range(int(1.6 * 2), int(15.2 * 2)):
        t = k / 2
        if any(a <= t < b and kind == "optical" for a, b, kind, _ in SCORE):
            mix.click(t, 0.06, 0.3, 1200)  # one tick per half turn
    mix.bell(6.4, 523, 3.0, 0.18, -0.3)
    mix.bell(15.2, 392, 4.0, 0.16, 0.3)
    mix.reverb(0.2)


if __name__ == "__main__":
    film.render()
