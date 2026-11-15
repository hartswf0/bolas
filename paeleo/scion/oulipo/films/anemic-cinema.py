"""Anémic cinéma — two optical discs, two text discs, strict alternation, then a still pass.

Look follows the two references: monochrome 1920s film. Text discs are lit,
sphere-shaded grey plates with bold white capitals on black (spiralTextPom);
optical discs are warm grey nested rings with fine engraved grooves on black
(duchamp2). Everything is computed here; no reference pixels are used.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import *

film = Film("anemic-cinema", seconds=24, boil=0, wobble=0)
R = 215
CX, CY = W // 2, H // 2
SCORE = [(0.0, 1.8, "title", None), (1.8, 6.4, "optical", "A"), (6.4, 10.4, "text", "1"),
         (10.4, 15.2, "optical", "B"), (15.2, 20.4, "text", "2"), (20.4, 24.0, "still", None)]
PUN1 = "A KEY LEFT ON A BENCH IS A BELL THAT FORGOT TO RING · A BELL LEFT ON A BENCH IS A KEY THAT FORGOT TO TURN ·"
PUN2 = "THE DOOR STAYS SHUT SO THE STATION CAN KEEP ITS SECRET · THE SECRET STAYS SHUT SO THE STATION CAN KEEP ITS DOOR ·"
WARM = np.array([1.0, 0.95, 0.86])  # beige-grey cast of the ring plate

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def sphere_plate(size):
    """Grey plate lit from the upper right, darkening to the lower left rim."""
    n = 2 * size
    y, x = (np.mgrid[0:n, 0:n].astype(np.float32) - size) / size
    r = np.hypot(x, y)
    z = np.sqrt(np.clip(1 - r * r, 0, 1))
    lx, ly, lz = 0.45, -0.5, 0.74
    lum = np.clip(x * lx + y * ly + z * lz, 0, 1) ** 1.3
    v = 55 + 150 * lum
    alpha = np.clip((1 - r) * size * 0.9, 0, 1)
    img = np.dstack([v, v, v, alpha * 255]).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def text_disc(phrase, size=22):
    plate = sphere_plate(R)
    glyphs = Image.new("L", plate.size, 0)
    f = font("sans", size)
    c = R
    rr, a = R - 30, -math.pi / 2
    for ch in phrase:
        g = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(g).text((size, size), ch, font=f, fill=255, anchor="mm", stroke_width=1, stroke_fill=255)
        g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        glyphs.paste(255, (int(x - size), int(y - size)), g)
        step = (size * 0.74) / rr
        a += step
        rr -= (size * 1.45) * step / (2 * math.pi)
        if rr < 40:
            break
    bloom = glyphs.filter(ImageFilter.GaussianBlur(2.2))
    p = np.asarray(plate, np.float32)
    g = np.asarray(glyphs, np.float32)[..., None] / 255
    b = np.asarray(bloom, np.float32)[..., None] / 255
    shadow = np.asarray(glyphs.filter(ImageFilter.GaussianBlur(1.6)), np.float32)[..., None] / 255
    rgb = p[..., :3] * (1 - 0.45 * shadow)
    rgb = rgb * (1 - g) + 250 * g
    rgb = np.clip(rgb + 40 * b, 0, 255)
    return Image.fromarray(np.dstack([rgb, p[..., 3:]]).astype(np.uint8), "RGBA")


DISCS = {"1": text_disc(PUN1), "2": text_disc(PUN2)}


def optical(ang, sign):
    """Nested eccentric rings; centres orbit the disc centre as the disc turns."""
    out = np.zeros((H, W), np.float32)
    n = 7
    for k in range(n, 0, -1):
        f = k / n
        r_out = R * f
        r_in = r_out - R / n * 0.55
        off = sign * (1 - f) * R * 0.28
        ox, oy = CX + off * math.cos(ang), CY + off * math.sin(ang)
        d = np.hypot(xx - ox, yy - oy)
        ring = (d < r_out) & (d > r_in)
        grooves = 0.82 + 0.18 * np.cos(d * 1.9)  # fine engraved striations
        edge = np.clip(np.minimum(r_out - d, d - r_in) / 1.5, 0, 1)
        out = np.where(ring, 200 * grooves * edge + out * (1 - edge), out)
        inner = d <= r_in
        out = np.where(inner, 0, out)
    # bullseye at the innermost centre: grooved boss
    off = sign * R * 0.28
    ox, oy = CX + off * math.cos(ang), CY + off * math.sin(ang)
    d = np.hypot(xx - ox, yy - oy)
    boss = d < R / n * 0.5
    out = np.where(boss, 185 * (0.8 + 0.2 * np.cos(d * 2.4)), out)
    return out


def tone(gray, t):
    """Warm monochrome print with flicker."""
    flick = 1 + 0.035 * math.sin(t * 47.0) * math.sin(t * 13.3)
    rgb = np.clip(gray[..., None] * WARM[None, None, :] * flick, 0, 255)
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def filmstrip(frames_img, t):
    """Still pass: three frames on a strip with sprocket holes, like a clip held to light."""
    canvas = Image.new("RGB", (W, H), (8, 8, 8))
    d = ImageDraw.Draw(canvas)
    sx0, sx1 = 250, 710
    d.rectangle([sx0, 0, sx1, H], fill=(14, 14, 14))
    d.rectangle([sx0, 0, sx0 + 46, H], fill=(225, 222, 214))
    for k in range(-1, 6):
        y = k * 108 + 22
        d.rounded_rectangle([sx0 + 12, y, sx0 + 34, y + 30], 4, fill=(10, 10, 10))
    for k, img in enumerate(frames_img):
        sm = img.resize((176, 176), Image.LANCZOS)
        canvas.paste(sm, (sx0 + 90, 4 + k * 178), sm)
    return canvas


@film.picture
def frame(t, ink):
    for a, b, kind, ident in SCORE:
        if a <= t < b:
            break
    fade = min(1, (t - a) / 0.3, (b - t) / 0.3)
    weave = (round(math.sin(t * 9.1) * 1.2), round(math.sin(t * 6.7 + 1) * 1.0))
    if kind == "title":
        img = Image.new("RGB", (W, H), (6, 6, 6))
        d = ImageDraw.Draw(img)
        d.text((W / 2, H / 2 - 8), "ANÉMIC", font=font("sans", 70), fill=(232, 230, 224), anchor="mm")
        d.text((W / 2, H / 2 + 44), "CINÉMA", font=font("sans", 30), fill=(200, 198, 190), anchor="mm")
        base = img
    elif kind == "optical":
        ang = 2 * math.pi * 0.5 * t  # fixed 0.5 rev/s: angle(t+2) == angle(t) mod 2π
        base = tone(optical(ang, +1 if ident == "A" else -1), t)
    elif kind == "text":
        speed = 0.16 if ident == "1" else 0.09  # rev/s; disc 2 is the reading disc
        disc = DISCS[ident].rotate(math.degrees(2 * math.pi * speed * t), resample=Image.BICUBIC)
        base = Image.new("RGB", (W, H), (6, 6, 6))
        base.paste(disc, (CX - R, CY - R), disc)
    else:
        # three consecutive frames of the reading disc: same layout, advancing phase
        three = [DISCS["2"].rotate(-k * 25, resample=Image.BICUBIC) for k in range(3)]
        base = filmstrip(three, t)
        d = ImageDraw.Draw(base)
        d.text((740, 250), "STILL PASS", font=font("mono", 14), fill=(190, 188, 180))
        d.text((740, 272), "layout without motion", font=font("mono", 13), fill=(130, 128, 122))
    base = base.transform(base.size, Image.AFFINE, (1, 0, weave[0], 0, 1, weave[1]), fillcolor=(6, 6, 6))
    ink.img = base
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if kind in ("optical", "text"):
        lab = {"A": "OPTICAL A · pushes toward you · 0.5 rev/s", "B": "OPTICAL B · sinks away · 0.5 rev/s",
               "1": "TEXT 1 · 0.16 rev/s", "2": "TEXT 2 · 0.09 rev/s · reading speed"}[ident]
        ink.label((24, H - 30), lab, 12, (120, 118, 112))
    ink.vignette(0.55)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=(6, 6, 6, int(255 * (1 - fade))))


@film.sound
def sound(mix):
    mix.drone(0, 24, (49, 98), gain=0.05, attack=1, release=2)
    mix.room(0, 24, gain=0.012, hum=24)  # projector flutter
    for a, b, kind, ident in SCORE[1:]:
        mix.click(a, 0.35, 0, 2500)
        mix.thud(a, 55, 0.25)
    for k in range(int(1.8 * 2), int(15.2 * 2)):
        t = k / 2
        if any(a <= t < b and kind == "optical" for a, b, kind, _ in SCORE):
            mix.click(t, 0.06, 0.3, 1200)
    mix.bell(6.4, 523, 3.0, 0.18, -0.3)
    mix.bell(15.2, 392, 4.0, 0.16, 0.3)
    mix.reverb(0.2)


if __name__ == "__main__":
    film.render()
