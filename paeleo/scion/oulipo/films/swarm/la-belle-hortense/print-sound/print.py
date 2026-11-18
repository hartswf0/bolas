"""U4 print-sound: the handmade print objects of La belle Hortense, set in Hortense Slab (handmade, editor/typeface.py; was Courier 10 Pitch).

Every object is typeset here, character by character (a typewriter strikes one letter at a time,
so each letter gets its own small baseline offset and ink weight from a seeded generator).
Nothing is traced or copied from the reference cover. Writes PNGs to
sources/la-belle-hortense/print-sound/print/ and swarm/la-belle-hortense/print.json.
Run: python3 -I print.py
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SWARM = FILMS / "swarm/la-belle-hortense"
OUT = FILMS / "sources/la-belle-hortense/print-sound/print"
OUT.mkdir(parents=True, exist_ok=True)
BOLD = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf"
REG = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Regular.ttf"
SIGMA = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf"  # Hortense Slab has its own sigma
W, H = 960, 540
BLACK = (1, 2, 1)
RED_T = (165, 9, 23)      # title red, cover quantised
RED = (226, 1, 27)        # red top
CREAM = (225, 229, 178)   # cream highlight
CARD = (232, 228, 196)    # receipt card stock (cream, a shade warmer)
MANILA = (214, 196, 140)  # envelope paper (ochre side of the palette)
_fc = {}


def F(size, path=BOLD):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def rel(p):
    return str(p).replace(str(FILMS.parent) + "/", "")


REC = {"objects": []}


def save(img, name):
    p = OUT / f"{name}.png"
    img.save(p, optimize=True)
    return rel(p)


def typed(img, xy, text, size, color, seed=0, jitter=1.0, ink=(0.82, 1.0), path=BOLD, advance=None):
    """Strike `text` one character at a time; returns the x after the last character and per-char boxes."""
    rs = np.random.RandomState(seed)
    f = F(size, path)
    adv = advance or f.getlength("M")
    x, y = xy
    boxes = []
    for ch in text:
        if ch != " ":
            layer = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(layer)
            dy = rs.uniform(-jitter, jitter) if jitter else 0
            dx = rs.uniform(-jitter * 0.5, jitter * 0.5) if jitter else 0
            d.text((x + dx, y + dy), ch, font=f, fill=255)
            a = np.asarray(layer, np.float32) * rs.uniform(*ink)
            col = Image.new("RGBA", img.size, color + (0,))
            col.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
            img.alpha_composite(col)
        boxes.append((x, y, x + adv, y + size))
        x += adv
    return x, boxes


# ------------------------------------------------------------- 1 receipt ---
def receipt(strike=0, underline=0, rendu=False, scale=2):
    """REÇU N° 6 ticket on cream card. strike: 0..7 hyphens over 'une clé'; underline: 0..14 underscores."""
    s = scale
    w, h = 300 * s, 170 * s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=4 * s, fill=CARD + (255,))
    # perforated stub on the left: a real row of punched holes, cut through the card (transparent)
    for k in range(9):
        cy = (10 + k * 18.5) * s
        d.ellipse([34 * s - 2.2 * s, cy - 2.2 * s, 34 * s + 2.2 * s, cy + 2.2 * s], fill=(0, 0, 0, 0))
    d.rectangle([4 * s, 4 * s, w - 5 * s, h - 5 * s], outline=BLACK + (255,), width=max(1, s))
    typed(img, (10 * s, 64 * s), "6", 26 * s, RED_T, seed=60, jitter=0)  # stub number
    x, _ = typed(img, (48 * s, 14 * s), "REÇU N° 6", 24 * s, BLACK, seed=1)
    lines = ["une clé", "porte de service", "remise au banc"]
    boxes = {}
    for i, ln in enumerate(lines):
        _, b = typed(img, (48 * s, (56 + i * 30) * s), ln, 17 * s, BLACK, seed=10 + i)
        boxes[ln] = b
    # red circled number stamp, top right (a rubber number stamp: ring + numeral)
    st = Image.new("RGBA", (64 * s, 64 * s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.ellipse([3 * s, 3 * s, 61 * s, 61 * s], outline=RED + (235,), width=3 * s)
    sd.text((32 * s, 33 * s), "6", font=F(34 * s), fill=RED + (235,), anchor="mm")
    st = st.rotate(-12, resample=Image.BICUBIC)
    img.alpha_composite(st, (224 * s, 8 * s))
    if strike:
        b = boxes["une clé"]
        for k in range(min(strike, len(b))):
            x0, y0, x1, y1 = b[k]
            typed(img, (x0, y0 - 1 * s), "-", 17 * s, RED, seed=100 + k, jitter=0.6)
    if underline:
        b = boxes["remise au banc"]
        for k in range(min(underline, len(b))):
            x0, y0, x1, y1 = b[k]
            typed(img, (x0, y0 + 4 * s), "_", 17 * s, RED, seed=200 + k, jitter=0.4)
    if rendu:
        st = Image.new("RGBA", (150 * s, 56 * s), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rectangle([3 * s, 3 * s, 147 * s, 53 * s], outline=RED + (225,), width=4 * s)
        sd.rectangle([8 * s, 8 * s, 142 * s, 48 * s], outline=RED + (225,), width=max(1, s))
        sd.text((75 * s, 29 * s), "RENDU", font=F(32 * s), fill=RED + (225,), anchor="mm")
        # a rubber stamp prints unevenly where the card is not flat: thin the ink along one edge
        a = np.asarray(st.getchannel("A"), np.float32)
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        a *= (0.72 + 0.28 * (xx / a.shape[1]))
        st.putalpha(Image.fromarray(a.astype(np.uint8)))
        st = st.rotate(9, resample=Image.BICUBIC, expand=True)
        img.alpha_composite(st, (min(w - st.width, 156 * s), 40 * s))
    return img


rc = {"id": "RECEIPT", "what": "receipt ticket 'REÇU N° 6 · une clé · porte de service · remise au banc', cream card with punched perforation stub, red circled number stamp; Courier 10 Pitch Bold typed letter by letter",
      "size_px": [600, 340], "scale_note": "drawn at 2x (300x170 design px)", "states": {}}
rc["states"]["plain"] = save(receipt(), "receipt_0_plain")
rc["states"]["struck"] = save(receipt(strike=7), "receipt_1_struck")
rc["states"]["underlined"] = save(receipt(strike=7, underline=14), "receipt_2_underlined")
rc["states"]["rendu"] = save(receipt(strike=7, underline=14, rendu=True), "receipt_3_rendu")
rc["states"]["underlined_only (for II.3 / III.6 if the strike is not yet shown)"] = save(receipt(underline=14), "receipt_2b_underlined_unstruck")
rc["type_on_frames"] = {
    "strike_through (II.6, from 19.7 s, one hyphen per 0.085 s, matches sound cue type_strikethrough_7)": [save(receipt(strike=k), f"receipt_strike_{k:02d}") for k in range(1, 8)],
    "underline (III.6, from 28.7 s, one underscore per 0.07 s, matches sound cue type_underline_14)": [save(receipt(strike=7, underline=k), f"receipt_underline_{k:02d}") for k in range(1, 15)],
}
rc["slots"] = {"I.5": "plain", "II.3": "plain (line 'remise au banc' legible)", "II.6": "strike type-on -> struck", "III.6": "underline type-on -> underlined",
               "IV.1": "underlined (its N° 6 matches the door plate)", "V.2": "underlined", "VI.4": "rendu (stamp lands 52.65 s with the thud)"}
REC["objects"].append(rc)


# ------------------------------------------------------------- 2 envelope ---
def envelope_set(scale=2):
    s = scale
    w, h = 220 * s, 140 * s
    # front with typed address
    fr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(fr)
    d.rectangle([0, 0, w - 1, h - 1], fill=MANILA + (255,), outline=(120, 104, 60, 255), width=s)
    for i, ln in enumerate(["Chef de gare", "Gare de Bourré, quai", "porte de service"]):
        typed(fr, (40 * s, (62 + i * 20) * s), ln, 13 * s, BLACK, seed=300 + i)
    # postage corner: a red typed 'PAR PORTEUR' (by hand delivery), no real stamp imagery
    d.rectangle([150 * s, 10 * s, 208 * s, 46 * s], outline=RED + (230,), width=2 * s)
    typed(fr, (155 * s, 15 * s), "PAR", 11 * s, RED, seed=310, jitter=0.5)
    typed(fr, (155 * s, 29 * s), "PORTEUR", 11 * s, RED, seed=311, jitter=0.5)
    # back: body with the two side flaps and bottom flap folds, top open (pocket)
    bk = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(bk)
    d.rectangle([0, 0, w - 1, h - 1], fill=MANILA + (255,))
    shade = tuple(int(c * 0.9) for c in MANILA)
    d.polygon([(0, 0), (w * 0.5, h * 0.55), (0, h)], fill=shade + (255,))
    d.polygon([(w, 0), (w * 0.5, h * 0.55), (w, h)], fill=shade + (255,))
    d.polygon([(0, h), (w * 0.5, h * 0.45), (w, h)], fill=tuple(int(c * 0.95) for c in MANILA) + (255,))
    for seg in [[(0, 0), (w * 0.5, h * 0.55)], [(w, 0), (w * 0.5, h * 0.55)], [(0, h), (w * 0.5, h * 0.45), (w, h)]]:
        d.line(seg, fill=(120, 104, 60, 255), width=s)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 104, 60, 255), width=s)
    # inside of the pocket (dark), visible when the flap is open
    ins = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ins).polygon([(2 * s, 2 * s), (w - 2 * s, 2 * s), (w * 0.5, h * 0.5)], fill=(60, 50, 28, 255))
    # flap: triangle, hinge along its top edge (y=0); outside face and inside face
    fh = int(h * 0.62)
    flo = Image.new("RGBA", (w, fh), (0, 0, 0, 0))
    ImageDraw.Draw(flo).polygon([(0, 0), (w, 0), (w * 0.5, fh - 1)], fill=MANILA + (255,), outline=(120, 104, 60, 255))
    fli = Image.new("RGBA", (w, fh), (0, 0, 0, 0))
    ImageDraw.Draw(fli).polygon([(0, 0), (w, 0), (w * 0.5, fh - 1)], fill=tuple(int(c * 0.82) for c in MANILA) + (255,), outline=(120, 104, 60, 255))
    return fr, bk, ins, flo, fli, fh


fr, bk, ins, flo, fli, fh = envelope_set()
REC["objects"].append({
    "id": "ENVELOPE", "what": "handmade cut-paper envelope (U2 foraged none): manila front with typed address 'Chef de gare / Gare de Bourré, quai / porte de service' and a red typed PAR PORTEUR box; back with folded side/bottom flaps; separate top flap (outside and inside faces) for the hinged opening",
    "size_px": [440, 280],
    "states": {"front": save(fr, "envelope_front"), "back": save(bk, "envelope_back"), "pocket_inside": save(ins, "envelope_pocket_inside"),
               "flap_outside": save(flo, "envelope_flap_outside"), "flap_inside": save(fli, "envelope_flap_inside")},
    "rig": {"flap_hinge": "top edge of flap png (y=0) pinned to top edge of envelope_back (y=0); open by scaling flap y from +1 (closed, outside face) through 0 to -1 (open, inside face, drawn upward)",
            "pocket_inside": "composite under the flap when open; the key slides out from y~0"},
    "slots": {"I.2": "front, carried at the visitor's forearm hand pivot", "I.3": "back + flap hinge open + key slides out", "I.5": "receipt slips from it"},
})


# ------------------------------------------------------------- 3 enamel plate ---
def enamel(scale=2):
    s = scale
    w, h = 120 * s, 150 * s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14 * s, fill=(30, 28, 24, 255))            # steel rim
    d.rounded_rectangle([3 * s, 3 * s, w - 4 * s, h - 4 * s], radius=12 * s, fill=CREAM + (255,))  # enamel field
    d.rounded_rectangle([10 * s, 10 * s, w - 11 * s, h - 11 * s], radius=8 * s, outline=RED + (255,), width=4 * s)
    d.text((w / 2, h / 2 + 4 * s), "6", font=F(110 * s), fill=BLACK + (255,), anchor="mm")
    for cy in (17 * s, h - 17 * s):  # two fixing screws
        d.ellipse([w / 2 - 4 * s, cy - 4 * s, w / 2 + 4 * s, cy + 4 * s], fill=(70, 66, 60, 255))
        d.line([w / 2 - 3 * s, cy, w / 2 + 3 * s, cy], fill=(20, 20, 18, 255), width=s)
    # enamel chips at the corners (black steel showing through), a real feature of old plates
    for (cx, cy, r) in [(8 * s, h - 9 * s, 4 * s), (w - 9 * s, 10 * s, 3 * s)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 28, 24, 255))
    return img


REC["objects"].append({"id": "PLATE6", "what": "enamel door-number plate '6': cream enamel, black Courier 10 Pitch Bold numeral, red inner border, steel rim, two screws, two chipped corners",
                       "size_px": [240, 300], "states": {"plate": save(enamel(), "enamel_plate_6")},
                       "slots": {"IV.1": "laid on the goods-shed door plate (Bourré 50866795131), matched to the receipt's N° 6", "II.1/III.2/IV.4/V.5/VI.3": "stays on the door"}})


# ------------------------------------------------------------- 4 title ---
def title_card():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    typed(img, (54, 300), "Jacques", 50, BLACK, seed=400, jitter=0)
    typed(img, (84, 350), "Roubaud", 66, BLACK, seed=401, jitter=0)
    typed(img, (54, 424), "La belle Hortense", 46, RED_T, seed=402, jitter=0)
    typed(img, (56, 486), "six modules · [6,1,5,2,4,3]", 18, BLACK, seed=403, jitter=0)
    return img


REC["objects"].append({"id": "TITLE", "what": "title-card type stacked like the cover's arrangement (not traced): 'Jacques' 50 px and 'Roubaud' 66 px in black #010201, 'La belle Hortense' 46 px in red #a50917, small line 'six modules · [6,1,5,2,4,3]' 18 px; transparent RGBA over the streaked ground",
                       "size_px": [W, H], "states": {"title": save(title_card(), "title_type")}, "slots": {"title 0.0-3.0": "composited over the 420 px pan exposure of Bourré 50866798791"}})


# ------------------------------------------------------------- 5 slot type ---
ROMAN = ["I", "II", "III", "IV", "V", "VI"]
S = json.load(open(SWARM / "structure.json"))


def band_text(img, xy, text, size, fg, bg, pad=(6, 3)):
    f = F(size)
    x, y = xy
    tw = f.getlength(text)
    ImageDraw.Draw(img).rectangle([x - pad[0], y - pad[1], x + tw + pad[0], y + size + pad[1]], fill=bg + (255,))
    ImageDraw.Draw(img).text((x, y), text, font=f, fill=fg + (255,))
    return x + tw


def slot_overlay(numeral, fr_, en, slot_line):
    """Lower-left block: numeral 44 px black; FR caption 30 px red; EN gloss 18 px (60%) cream on a black band;
    slot line 18 px on a cream typed strip, the active word in red caps."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = 40
    y_slot = H - 40
    y_en = y_slot - 34
    y_fr = y_en - 40
    y_num = y_fr - 50
    d.text((x0, y_num), numeral, font=F(44), fill=BLACK + (255,))
    if fr_:
        d.text((x0, y_fr), fr_, font=F(30), fill=RED_T + (255,))
    if en:
        band_text(img, (x0, y_en), en, 18, CREAM, BLACK)
    # slot line strip
    f = F(18)
    words = slot_line.split(" · ")
    sep = " · "
    tw = f.getlength(sep.join(words))
    d.rectangle([x0 - 6, y_slot - 4, x0 + tw + 6, y_slot + 22], fill=CREAM + (255,))
    x = x0
    for i, wd in enumerate(words):
        col = RED if wd.isupper() else BLACK
        d.text((x, y_slot), wd, font=f, fill=col + (255,))
        x += f.getlength(wd)
        if i < len(words) - 1:
            d.text((x, y_slot), sep, font=f, fill=BLACK + (255,))
            x += f.getlength(sep)
    return img


slots = {}
for m in S["modules"]:
    for a in m["appearances"]:
        k = a["slot"]
        num = f"{m['module']}." if k == 1 or True else ""
        img = slot_overlay(num, a["caption_fr"], a["caption_en"], a["slot_line"])
        slots[a["id"]] = {"t": [a["start"], a["end"]], "file": save(img, f"slot_{a['id'].replace('.', '_')}"),
                          "numeral": num, "caption_fr": a["caption_fr"], "caption_en": a["caption_en"], "slot_line": a["slot_line"],
                          "active_word": [w for w in a["slot_line"].split(" · ") if w.isupper()][0]}
# a numeral-free slot line only (for frames where the editor wants the caption off)
lineonly = {}
for m in S["modules"]:
    for a in m["appearances"]:
        lineonly[a["id"]] = save(slot_overlay("", "", "", a["slot_line"]), f"slotline_only_{a['id'].replace('.', '_')}")
REC["objects"].append({"id": "SLOT-TYPE", "what": "caption and slot-line typesetting for all 36 slots: module numeral 44 px black #010201; FR caption 30 px red #a50917; EN gloss at 60% (18 px) in cream #e1e5b2 on a black #010201 band (legible over dark streak, per test-shot review); slot line 18 px black on a cream typed strip, active motif in red #e2011b caps. Full-frame 960x540 RGBA, lower-left block",
                       "size_px": [W, H], "states": slots, "slot_line_only": lineonly,
                       "check": "the red-caps word in each file equals order_i[k] (taken from structure.json slot_line)"})

# the replay tag "I·4" for IV.2 and VI.2
tag = Image.new("RGBA", (120, 52), (0, 0, 0, 0))
ImageDraw.Draw(tag).rectangle([0, 0, 119, 51], fill=CREAM + (255,), outline=BLACK + (255,), width=2)
typed(tag, (14, 8), "I·4", 34, RED, seed=500, jitter=0.6)
REC["objects"].append({"id": "REPLAY-TAG", "what": "typed slip 'I·4' marking the replay of I.4 (key on the red coat)", "size_px": [120, 52],
                       "states": {"tag": save(tag, "replay_tag_I4")}, "slots": {"IV.2": "top-left", "VI.2": "top-left"}})


# ------------------------------------------------------------- 6 end card ---
ORD = [m["order"] for m in S["modules"]]
MOT = {k: v["fr"] for k, v in S["motifs"].items()}


def end_card(rows, sigma=False, credits=False):
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    d = ImageDraw.Draw(img)
    f = F(18)
    cx0, cw, ry0, rh = 150, 118, 70, 50
    typed(img, (40, 26), "slot", 16, BLACK, seed=600, jitter=0)
    for k in range(6):
        typed(img, (cx0 + k * cw + 30, 26), str(k + 1), 16, BLACK, seed=601 + k, jitter=0)
    centers = {}
    for i in range(rows):
        y = ry0 + i * rh
        typed(img, (40, y), ROMAN[i], 22, BLACK, seed=700 + i, jitter=0.5)
        for k, c in enumerate(ORD[i]):
            word = MOT[c]
            col = RED if c == "A" else BLACK
            x = cx0 + k * cw
            typed(img, (x, y + 3), word, 18, col, seed=800 + i * 6 + k, jitter=0.5)
            centers[(i, c)] = (x + f.getlength(word) / 2, y + 12)
    # braid strands: each motif's strand from its word in row i to its word in row i+1
    for i in range(rows - 1):
        for c in "BCDEFA":  # coat (A) last so the red strand lies on top
            (xa, ya), (xb, yb) = centers[(i, c)], centers[(i + 1, c)]
            col = RED if c == "A" else BLACK
            wdt = 3 if c == "A" else 1
            pts = []
            for t in np.linspace(0, 1, 24):
                s_ = t * t * (3 - 2 * t)
                pts.append((xa + (xb - xa) * s_, ya + 12 + (yb - ya - 24) * t))
            d.line(pts, fill=col + (255,), width=wdt)
    if sigma:
        y = ry0 + 6 * rh + 8
        x, _ = typed(img, (40, y), "", 20, BLACK)
        d.text((40, y), "σ", font=F(22, SIGMA), fill=BLACK + (255,))
        typed(img, (40 + 15, y - 8), "6", 13, BLACK, seed=900, jitter=0)
        typed(img, (40 + 26, y), " = id · ABCDEF", 20, BLACK, seed=901, jitter=0.4)
    if credits:
        lines = [
            "Photographies : Jack Delano, FSA/OWI (Library of Congress, domaine public) ; Daniel Jolivet, Bourré (CC BY 2.0) ;",
            "Carol M. Highsmith (LoC, domaine public) ; Reinhard Dietrich (domaine public) ; Blenheimears (CC0).",
            "Sons : Olga Ernst (CC BY-SA 4.0) ; Pwaivers (CC BY-SA 3.0) ; stephan (domaine public) ; MKFI (domaine public) ;",
            "Gravity Sound (CC BY 4.0) ; SpaceJoe (CC0).  Caractères : Courier 10 Pitch (Bitstream).  D'après Jacques Roubaud.",
        ]
        for j, ln in enumerate(lines):
            d.text((40, 432 + j * 17), ln, font=F(12, REG), fill=BLACK + (255,))
    return img


ec = {"id": "ENDCARD", "what": "end-card motif x module matrix on cream card: six typed rows (modules I-VI) of the six motif words in slot order, braid strands drawn between each motif's positions in successive rows (coat strand red #e2011b, 3 px; others black, 1 px), then the line 'σ⁶ = id · ABCDEF', then credits in small Courier 10 Pitch Regular",
      "size_px": [W, H], "states": {}, "timing": {}}
for r in range(0, 7):
    ec["states"][f"rows_{r}"] = save(end_card(r), f"endcard_rows_{r}")
    ec["timing"][f"rows_{r}"] = 57.0 + 0.5 * r
ec["states"]["sigma"] = save(end_card(6, sigma=True), "endcard_sigma")
ec["timing"]["sigma"] = 60.5
ec["states"]["credits"] = save(end_card(6, sigma=True, credits=True), "endcard_credits")
ec["timing"]["credits"] = 61.0
ec["note"] = "each state is shown from its time until the next; credits hold to 66.0 (sound silent 63-66). Row clicks in sound_cues.json at 57.5 ... 61.0."
REC["objects"].append(ec)

REC.update({"unit": "U4 print-sound", "font": {"face": "Hortense Slab Bold / Regular (handmade for this film, editor/typeface.py; sources/la-belle-hortense/editor/type/)", "licence": "handmade for the work; released with the film under CC BY-SA 4.0", "note": "replaces Courier 10 Pitch and the DejaVu sigma (editor repair round 2): every glyph, sigma included, is drawn in typeface.py"},
            "palette": {"black": "#010201", "title_red": "#a50917", "red": "#e2011b", "cream": "#e1e5b2", "card": "#e8e4c4", "manila": "#d6c48c"},
            "script": rel(Path(__file__).resolve())})
json.dump(REC, open(SWARM / "print.json", "w"), indent=1, ensure_ascii=False)
print("objects:", [o["id"] for o in REC["objects"]])
