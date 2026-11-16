"""Hortense Slab: a handmade monospaced slab-serif typewriter face, drawn for this film (editor repair round 2).

Every glyph is drawn here, in code, as pen strokes (lines, elliptical arcs, dots) and slab serifs on a 600-unit
monospaced grid; the strokes are rasterised at 2x, traced with cv2.findContours and written as TrueType outlines with
fontTools.  No existing typeface is copied, traced or used: the face is handmade for the work and released with the
film (CC BY-SA 4.0).  Two weights: Bold (stroke 118) and Regular (stroke 80).

    python3 -I films/swarm/la-belle-hortense/editor/typeface.py
Writes films/sources/la-belle-hortense/editor/type/HortenseSlab-{Bold,Regular}.ttf and a specimen PNG.
"""
import math, os
import numpy as np, cv2
from PIL import Image, ImageDraw
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/type')
os.makedirs(OUT, exist_ok=True)
ADV, ASC, DSC = 600, 900, 260
C, X = 680, 480

def l(*a): return ('l',) + a
def a(*a_): return ('a',) + a_
def d(*a_): return ('d',) + a_
def s(*a_): return ('s',) + a_
def E(cx, cy, rx, ry): return a(cx, cy, rx, ry, 0, 360)

ACUTE = [l(250, 570, 390, 710)]; GRAVE = [l(210, 710, 350, 570)]
CIRC = [l(170, 570, 300, 700), l(300, 700, 430, 570)]; DIAER = [d(200, 640, 58), d(400, 640, 58)]
CED = [l(300, 10, 300, -60), a(290, -125, 85, 65, 90, -170)]
def up(ops, dy=200): return [(o[0], o[1], o[2] + dy) + o[3:] if o[0] in 'ds' else
                             ((o[0], o[1], o[2] + dy, o[3], o[4] + dy) if o[0] == 'l' else (o[0], o[1], o[2] + dy) + o[3:]) for o in ops]

G = {
 ' ': [],
 'A': [l(300, 680, 90, 0), l(300, 680, 510, 0), l(170, 230, 430, 230), s(90, 0, 190), s(510, 0, 190), s(250, 680, 120)],
 'B': [l(110, 0, 110, 680), l(110, 680, 330, 680), a(330, 520, 150, 160, 90, -90), l(110, 360, 340, 360),
       a(340, 180, 175, 180, 90, -90), l(110, 0, 340, 0), s(80, 680, 110), s(80, 0, 110)],
 'C': [a(320, 340, 220, 340, 38, 322), l(492, 560, 492, 680), s(492, 680, 60)],
 'D': [l(110, 0, 110, 680), l(110, 680, 270, 680), l(110, 0, 270, 0), a(270, 340, 240, 340, 90, -90), s(80, 680, 110), s(80, 0, 110)],
 'E': [l(120, 0, 120, 680), l(120, 680, 500, 680), l(120, 350, 410, 350), l(120, 0, 510, 0), l(500, 680, 500, 570),
       l(510, 0, 510, 120), l(410, 290, 410, 410), s(90, 680, 120), s(90, 0, 120)],
 'F': [l(130, 0, 130, 680), l(130, 680, 510, 680), l(130, 350, 420, 350), l(510, 680, 510, 570), l(420, 290, 420, 410),
       s(100, 680, 120), s(160, 0, 260)],
 'G': [a(320, 340, 220, 340, 38, 322), l(500, 110, 500, 300), l(360, 300, 550, 300), l(492, 560, 492, 680)],
 'H': [l(110, 0, 110, 680), l(490, 0, 490, 680), l(110, 350, 490, 350)] + [s(x, y, 180) for x in (110, 490) for y in (0, 680)],
 'I': [l(300, 0, 300, 680), s(300, 680, 320), s(300, 0, 320)],
 'J': [l(430, 680, 430, 220), a(270, 220, 160, 220, 0, -180), s(410, 680, 260)],
 'K': [l(110, 0, 110, 680), l(480, 680, 130, 300), l(250, 420, 500, 0)] + [s(x, y, 170) for x, y in ((110, 0), (110, 680), (480, 680), (510, 0))],
 'L': [l(120, 0, 120, 680), l(120, 0, 510, 0), l(510, 0, 510, 130), s(140, 680, 240), s(90, 0, 110)],
 'M': [l(80, 0, 80, 680), l(520, 0, 520, 680), l(80, 680, 300, 230), l(520, 680, 300, 230), s(70, 0, 150), s(530, 0, 150), s(60, 680, 90), s(540, 680, 90)],
 'N': [l(100, 0, 100, 680), l(500, 0, 500, 680), l(100, 680, 500, 0), s(100, 0, 180), s(500, 680, 180), s(70, 680, 90)],
 'O': [E(300, 340, 220, 340)],
 'P': [l(110, 0, 110, 680), l(110, 680, 310, 680), a(310, 510, 185, 170, 90, -90), l(110, 340, 310, 340), s(150, 0, 260), s(80, 680, 110)],
 'Q': [E(300, 340, 220, 340), l(320, 40, 510, -130)],
 'R': [l(110, 0, 110, 680), l(110, 680, 310, 680), a(310, 510, 185, 170, 90, -90), l(110, 340, 310, 340), l(290, 340, 500, 0),
       s(150, 0, 240), s(80, 680, 110), s(520, 0, 110)],
 'S': [a(300, 515, 185, 165, 25, 270), a(300, 175, 205, 175, 90, -155), l(470, 680, 470, 560), l(120, 0, 120, 130)],
 'T': [l(60, 680, 540, 680), l(300, 0, 300, 680), l(60, 680, 60, 560), l(540, 680, 540, 560), s(300, 0, 280)],
 'U': [l(110, 680, 110, 230), l(490, 680, 490, 230), a(300, 230, 190, 230, 180, 360), s(110, 680, 180), s(490, 680, 180)],
 'V': [l(70, 680, 300, 0), l(530, 680, 300, 0), s(70, 680, 170), s(530, 680, 170)],
 'W': [l(50, 680, 170, 0), l(170, 0, 300, 450), l(300, 450, 430, 0), l(430, 0, 550, 680), s(50, 680, 110), s(550, 680, 110)],
 'X': [l(90, 680, 510, 0), l(510, 680, 90, 0)] + [s(x, y, 170) for x in (90, 510) for y in (0, 680)],
 'Y': [l(80, 680, 300, 330), l(520, 680, 300, 330), l(300, 330, 300, 0), s(300, 0, 280), s(80, 680, 160), s(520, 680, 160)],
 'Z': [l(90, 680, 510, 680), l(510, 680, 90, 0), l(90, 0, 510, 0), l(90, 680, 90, 570), l(510, 0, 510, 110)],
 'a': [l(460, 0, 460, 320), a(300, 320, 160, 160, 0, 150), E(285, 135, 165, 135), s(500, 0, 100)],
 'b': [l(110, 0, 110, 720), E(320, 240, 195, 240), s(80, 720, 110), s(90, 0, 70)],
 'c': [a(310, 240, 200, 240, 40, 320), l(463, 360, 463, 480)],
 'd': [E(280, 240, 195, 240), l(490, 0, 490, 720), s(460, 720, 120), s(520, 0, 90)],
 'e': [l(110, 250, 500, 250), a(300, 240, 200, 240, 0, 320)],
 'f': [l(250, 0, 250, 560), a(390, 560, 140, 150, 180, 20), l(110, 480, 430, 480), s(250, 0, 290)],
 'g': [E(290, 280, 185, 200), l(475, 480, 475, -60), a(300, -60, 175, 150, 0, -165), s(510, 480, 90)],
 'h': [l(110, 0, 110, 720), a(300, 300, 190, 180, 180, 0), l(490, 300, 490, 0), s(110, 0, 180), s(490, 0, 180), s(80, 720, 110)],
 'i': [l(300, 0, 300, 480), d(300, 650, 72), s(300, 0, 320), s(240, 480, 130)],
 'j': [l(380, 480, 380, -60), a(230, -60, 150, 150, 0, -165), d(380, 650, 72), s(320, 480, 130)],
 'k': [l(110, 0, 110, 720), l(450, 480, 130, 200), l(230, 290, 480, 0), s(80, 720, 110), s(110, 0, 170), s(450, 480, 160), s(500, 0, 120)],
 'l': [l(300, 0, 300, 720), s(300, 0, 320), s(240, 720, 130)],
 'm': [l(70, 0, 70, 480), a(185, 330, 115, 150, 180, 0), l(300, 330, 300, 0), a(415, 330, 115, 150, 180, 0), l(530, 330, 530, 0),
       s(70, 0, 110), s(300, 0, 100), s(530, 0, 110)],
 'n': [l(110, 0, 110, 480), a(300, 300, 190, 180, 180, 0), l(490, 300, 490, 0), s(110, 0, 180), s(490, 0, 180), s(80, 480, 90)],
 'o': [E(300, 240, 205, 240)],
 'p': [l(110, 480, 110, -210), E(320, 240, 195, 240), s(130, -210, 230), s(80, 480, 90)],
 'q': [E(280, 240, 195, 240), l(490, 480, 490, -210), s(470, -210, 230)],
 'r': [l(150, 0, 150, 480), a(360, 290, 210, 190, 180, 55), s(190, 0, 300), s(120, 480, 90)],
 's': [a(300, 360, 165, 120, 25, 270), a(300, 120, 180, 120, 90, -155), l(455, 480, 455, 400), l(130, 0, 130, 80)],
 't': [l(240, 640, 240, 120), a(380, 120, 140, 120, 180, 300), l(100, 480, 450, 480)],
 'u': [l(110, 480, 110, 180), a(300, 180, 190, 180, 180, 360), l(490, 480, 490, 0), s(80, 480, 90), s(460, 480, 90), s(520, 0, 80)],
 'v': [l(80, 480, 300, 0), l(520, 480, 300, 0), s(80, 480, 170), s(520, 480, 170)],
 'w': [l(50, 480, 170, 0), l(170, 0, 300, 330), l(300, 330, 430, 0), l(430, 0, 550, 480), s(50, 480, 110), s(550, 480, 110)],
 'x': [l(100, 480, 500, 0), l(500, 480, 100, 0)] + [s(x, y, 160) for x in (100, 500) for y in (0, 480)],
 'y': [l(80, 480, 300, 0), l(520, 480, 200, -210), s(80, 480, 170), s(520, 480, 170), s(170, -210, 220)],
 'z': [l(110, 480, 490, 480), l(490, 480, 110, 0), l(110, 0, 500, 0), l(110, 480, 110, 390), l(500, 0, 500, 90)],
 '0': [E(300, 340, 200, 340), l(230, 200, 370, 480)],
 '1': [l(300, 0, 300, 680), l(300, 680, 150, 560), s(300, 0, 320)],
 '2': [a(300, 480, 190, 200, 160, -30), l(465, 380, 100, 0), l(100, 0, 510, 0), l(510, 0, 510, 110)],
 '3': [a(290, 515, 180, 165, 150, -90), a(300, 180, 205, 180, 90, -150)],
 '4': [l(400, 0, 400, 680), l(400, 680, 70, 200), l(70, 200, 530, 200), s(400, 0, 260)],
 '5': [l(140, 680, 480, 680), l(140, 680, 120, 390), l(120, 390, 230, 410), a(300, 215, 205, 210, 110, -150)],
 '6': [E(300, 215, 200, 215), l(130, 270, 380, 680)],
 '7': [l(90, 680, 510, 680), l(510, 680, 240, 0), l(90, 680, 90, 570), s(240, 0, 200)],
 '8': [E(300, 520, 170, 160), E(300, 180, 205, 180)],
 '9': [E(300, 465, 200, 215), l(470, 410, 220, 0)],
 '.': [d(300, 55, 68)], ',': [d(300, 60, 66), l(325, 40, 230, -150)],
 ':': [d(300, 55, 68), d(300, 410, 68)], ';': [d(300, 410, 68), d(300, 60, 66), l(325, 40, 230, -150)],
 "'": [l(300, 720, 300, 490)], '’': [d(300, 650, 62), l(325, 640, 240, 470)], '`': [l(240, 720, 360, 590)],
 '"': [l(210, 720, 210, 490), l(390, 720, 390, 490)],
 '-': [l(150, 290, 450, 290)], '–': [l(50, 290, 550, 290)], '—': [l(0, 290, 600, 290)], '_': [l(0, -150, 600, -150)],
 '(': [a(500, 260, 270, 470, 125, 235)], ')': [a(100, 260, 270, 470, 55, -55)],
 '[': [l(250, 730, 250, -160), l(250, 730, 440, 730), l(250, -160, 440, -160)],
 ']': [l(350, 730, 350, -160), l(350, 730, 160, 730), l(350, -160, 160, -160)],
 '{': [a(420, 560, 120, 170, 90, 180), a(180, 390, 120, 170, 0, -90), a(180, 130, 120, 170, 90, 0), a(420, -40, 120, 120, 180, 270)],
 '}': [a(180, 560, 120, 170, 90, 0), a(420, 390, 120, 170, 180, 270), a(420, 130, 120, 170, 90, 180), a(180, -40, 120, 120, 0, -90)],
 '/': [l(470, 730, 130, -110)], '\\': [l(130, 730, 470, -110)], '|': [l(300, 740, 300, -200)],
 '·': [d(300, 330, 70)], '×': [l(170, 140, 430, 500), l(430, 140, 170, 500)],
 '=': [l(110, 210, 490, 210), l(110, 410, 490, 410)], '+': [l(110, 320, 490, 320), l(300, 130, 300, 510)],
 '<': [l(490, 560, 120, 320), l(120, 320, 490, 80)], '>': [l(110, 560, 480, 320), l(480, 320, 110, 80)],
 '~': [a(200, 300, 100, 80, 180, 0), a(400, 300, 100, 80, 180, 360)],
 '^': [l(150, 480, 300, 700), l(300, 700, 450, 480)],
 '?': [a(300, 530, 170, 160, 160, -60), l(385, 391, 300, 260), l(300, 260, 300, 200), d(300, 55, 68)],
 '!': [l(300, 720, 300, 230), d(300, 55, 68)],
 '«': [l(270, 410, 120, 250), l(120, 250, 270, 90), l(450, 410, 300, 250), l(300, 250, 450, 90)],
 '»': [l(150, 410, 300, 250), l(300, 250, 150, 90), l(330, 410, 480, 250), l(480, 250, 330, 90)],
 '°': [('e', 300, 590, 95, 95, 0.55)], '⁶': [('e', 300, 520, 95, 110, 0.6), l(225, 545, 330, 760)],
 '#': [l(230, 700, 190, 0), l(420, 700, 380, 0), l(90, 470, 520, 470), l(80, 230, 510, 230)],
 '%': [('e', 170, 560, 90, 110, 0.7), ('e', 430, 120, 90, 110, 0.7), l(500, 680, 100, 0)],
 '&': [a(260, 545, 125, 140, -40, 230), l(180, 440, 520, 0), a(250, 190, 150, 190, 60, 300), l(250, 0, 470, 260)],
 '*': [l(300, 720, 300, 380), l(160, 640, 440, 460), l(440, 640, 160, 460)],
 '@': [E(300, 300, 240, 300), E(310, 290, 100, 140), l(410, 430, 410, 170)],
 '$': [a(300, 515, 185, 165, 25, 270), a(300, 175, 205, 175, 90, -155), l(300, 780, 300, -100)],
 'σ': [E(270, 240, 190, 240), l(270, 480, 545, 480), l(545, 480, 545, 400)],
 '§': [a(300, 560, 150, 120, 20, 260), a(300, 330, 150, 130, 90, -90), a(300, 330, 150, 130, 90, 270), a(300, 100, 150, 120, 100, -160)],
}
G['é'] = G['e'] + ACUTE; G['è'] = G['e'] + GRAVE; G['ê'] = G['e'] + CIRC; G['ë'] = G['e'] + DIAER
G['à'] = G['a'] + GRAVE; G['â'] = G['a'] + CIRC; G['ç'] = G['c'] + CED; G['ô'] = G['o'] + CIRC
G['ù'] = G['u'] + GRAVE; G['û'] = G['u'] + CIRC; G['î'] = [o for o in G['i'] if o[0] != 'd'] + CIRC
G['ï'] = [o for o in G['i'] if o[0] != 'd'] + DIAER
G['É'] = G['E'] + up(ACUTE, 210); G['È'] = G['E'] + up(GRAVE, 210); G['À'] = G['A'] + up(GRAVE, 210)
G['Ç'] = G['C'] + CED; G['Ê'] = G['E'] + up(CIRC, 210); G['Ô'] = G['O'] + up(CIRC, 210)

K = 2                                     # raster scale
TOP = ASC + 100                           # raster row 0 = font y TOP

def raster(ops, stroke):
    im = Image.new('L', (ADV * K, (TOP + DSC + 100) * K), 0)
    dr = ImageDraw.Draw(im)
    w = stroke * K
    def P(x, y): return (x * K, (TOP - y) * K)
    def dot(x, y, r): px, py = P(x, y); dr.ellipse((px - r * K, py - r * K, px + r * K, py + r * K), fill=255)
    def seg(pts, wd):
        for p, q in zip(pts[:-1], pts[1:]):
            dr.line([P(*p), P(*q)], fill=255, width=int(round(wd * K)))
        for p in pts: dot(p[0], p[1], wd / 2)
    for o in ops:
        if o[0] == 'l':
            seg([(o[1], o[2]), (o[3], o[4])], stroke)
        elif o[0] == 'a':
            cx, cy, rx, ry, a0, a1 = o[1:]
            n = max(8, int(abs(a1 - a0) / 4))
            pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                    cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
            seg(pts, stroke)
        elif o[0] == 'e':                 # thin ellipse (degree sign etc.): stroke scaled by o[5]
            cx, cy, rx, ry, k = o[1:]
            pts = [(cx + rx * math.cos(math.radians(t)), cy + ry * math.sin(math.radians(t))) for t in range(0, 365, 5)]
            seg(pts, stroke * k)
        elif o[0] == 'd':
            dot(o[1], o[2], o[3] * stroke / 118)
        elif o[0] == 's':                 # slab serif: a bar centred on (x, y), height 0.72 stroke
            x, y, wd = o[1:]
            hh = 0.72 * stroke
            yc = y + hh / 2 if y <= 0 + 1e-6 and y > -1 else (y - hh / 2 if y >= X - 1 else y)
            if y == 0: yc = hh / 2
            elif y > 0: yc = y - hh / 2 + 0.0
            else: yc = y + hh / 2
            x0, y0 = P(x - wd / 2, yc + hh / 2); x1, y1 = P(x + wd / 2, yc - hh / 2)
            dr.rectangle((x0, y0, x1, y1), fill=255)
    return np.asarray(im)

def glyph_from(ops, stroke):
    m = raster(ops, stroke)
    pen = TTGlyphPen(None)
    if m.max() == 0:
        return pen.glyph()
    cs, hier = cv2.findContours((m > 127).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    for i, c in enumerate(cs):
        c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :].astype(np.float64)
        if len(c) < 3: continue
        pts = [(int(round(px / K)), int(round(TOP - py / K))) for px, py in c]
        dedup = [p for j, p in enumerate(pts) if p != pts[j - 1]]
        if len(dedup) < 3: continue
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(dedup, dedup[1:] + dedup[:1])) / 2
        outer = hier[0][i][3] < 0
        if (outer and area > 0) or ((not outer) and area < 0):    # TrueType: outer clockwise, holes counter-clockwise
            dedup = dedup[::-1]
        pen.moveTo(dedup[0])
        for p in dedup[1:]: pen.lineTo(p)
        pen.closePath()
    return pen.glyph()

def build(style, stroke):
    names = ['.notdef'] + ['u%04X' % ord(ch) for ch in G]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(ch): 'u%04X' % ord(ch) for ch in G})
    glyphs = {'.notdef': glyph_from([l(100, 0, 100, 680), l(500, 0, 500, 680), l(100, 0, 500, 0), l(100, 680, 500, 680)], 40)}
    for ch, ops in G.items():
        glyphs['u%04X' % ord(ch)] = glyph_from(ops, stroke)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (ADV, 0) for n in names})
    fb.setupHorizontalHeader(ascent=ASC, descent=-DSC)
    fb.setupNameTable(dict(familyName='Hortense Slab', styleName=style, uniqueFontIdentifier='HortenseSlab-' + style,
                           fullName='Hortense Slab ' + style, psName='HortenseSlab-' + style, version='1.0',
                           copyright='Handmade for the film La belle Hortense (sextine exercise), 2026; CC BY-SA 4.0',
                           licenseDescription='Creative Commons Attribution-ShareAlike 4.0'))
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=-DSC, usWinAscent=ASC, usWinDescent=DSC, sxHeight=X, sCapHeight=C,
                usWeightClass=700 if style == 'Bold' else 400)
    fb.setupPost(isFixedPitch=1)
    p = os.path.join(OUT, 'HortenseSlab-%s.ttf' % style)
    fb.save(p)
    return p

if __name__ == '__main__':
    from PIL import ImageFont
    pb = build('Bold', 118); pr = build('Regular', 80)
    im = Image.new('RGB', (1200, 520), (225, 229, 178)); dr = ImageDraw.Draw(im)
    lines = ['ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz', '0123456789 .,:;\'’"-–—()[]/·×=+?!«»°σ',
             'é è ê à ç ù ô É Ç  REÇU · CLÉ · MANTEAU', 'Jacques Roubaud', 'La belle Hortense']
    for j, s_ in enumerate(lines):
        dr.text((20, 10 + j * 62), s_, font=ImageFont.truetype(pb, 40), fill=(1, 2, 1) if j != 5 else (165, 9, 23))
    dr.text((20, 400), 'Regular: une clé remise au banc — porte de service, quai (σ = [6,1,5,2,4,3])', font=ImageFont.truetype(pr, 26), fill=(1, 2, 1))
    dr.text((20, 450), 'small 12 px: Photographies : Jack Delano, FSA/OWI (Library of Congress, domaine public)', font=ImageFont.truetype(pr, 14), fill=(1, 2, 1))
    im.save(os.path.join(OUT, 'specimen.png'))
    print(pb, pr)
