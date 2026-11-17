"""Editor: side-by-side frames (0:06, 0:46) beside maki.webp and acceptance conditions 6-7 (+3 diff).
Run: python3 -I films/swarm/le-maki-mococo/editor_measure.py   (from the oulipo root). Writes editor_measure.json."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SW = Path(__file__).resolve().parent
OUL = SW.parents[2]
sys.path.insert(0, str(SW / "u2"))
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("film_lmm", OUL / "films" / "le-maki-mococo.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
M, G = F.M, F.G
import measure as Q  # noqa: E402  (U2's PIL measure)

OUT = OUL / "films" / "sources" / "le-maki-mococo" / "editor"
REF = OUL / "assets" / "references" / "maki.webp"


def masks(pose, lip_set, jaw):
    R = M.rig()
    L = R.lip(pose, lip_set)

    def img(a):
        return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L")

    def rot(a):
        return np.asarray(img(a).rotate(-jaw, resample=Image.BICUBIC, center=(M.HINGE[0] * M.S, M.HINGE[1] * M.S)),
                          np.float32) / 255 if jaw > 1e-3 else a

    def film(a):    # E3: same ZOOM framing as mouth_rig.mouth_image
        z = M.ZOOM
        big = img(a).resize((int(round(M.W * z)), int(round(M.H * z))), Image.BILINEAR)
        ox, oy = int(round(M.ZOOM_C[0] * (z - 1))), int(round(M.ZOOM_C[1] * (z - 1)))
        return np.asarray(big.crop((ox, oy, ox + M.W, oy + M.H)), np.float32) / 255 > 0.5
    up, lo = L["up_a"], rot(L["lo_a"])
    head, jawa, neck = R.a_head, rot(R.a_jaw), R.a_neck
    lip = (up > 0.5) | ((lo > 0.5) & (head < 0.5))
    skin = ((head > 0.5) | (jawa > 0.5) | (neck > 0.5)) & ~lip
    cav = np.asarray(R._cavity_for(pose).getchannel("A"), np.float32) / 255 > 0.5
    cav = cav & ~lip & ~(head > 0.5) & ~(jawa > 0.5)
    return film(skin), film(lip), film(cav)


def field_mask(t):
    """Right 50% excluding type, cord/animal, captions, strip (every drawn layer's alpha, dilated 2 px)."""
    a = np.zeros((540, 960), bool)
    for lay in (M.type_layer(t, F.ONSETS, darken=F.darken(t)), G.hang_layer(t, F.HANG_CUES)):
        a |= np.asarray(lay)[..., 3] > 0
    from PIL import ImageFilter
    a = np.asarray(Image.fromarray(a.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    a[:40, :] = True          # cue strip band
    a[380:, 440:] = True      # caption band
    m = ~a
    m[:, :480] = False
    return m


res = {}
ref = Image.open(REF).convert("RGB").resize((960, 540), Image.LANCZOS)
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 16)
for t in (6.0, 46.0):
    fr = F.film.frame(int(round(t * 24)))
    fa = np.asarray(fr)
    pose, jaw = F.TRACK.frame(t)
    sk, lp, cv = masks(pose, F.lip_set(t), round(jaw / 0.25) * 0.25)
    m = Q.measure(fa, sk, lp, cv)
    fm = field_mask(t)
    m["pose"], m["jaw_deg"] = pose, round(jaw, 2)
    m["field_mean_right_half_excl_layers"] = [round(float(x), 2) for x in fa[fm].mean(0)]
    m["field_pixels"] = int(fm.sum())
    luma = fa.astype(float) @ np.array([0.299, 0.587, 0.114])
    m["dark_frac_frame"] = round(float((luma < 80).mean()), 4)
    m["dark_frac_mouth_region_left_half"] = round(float((luma[:, :480] < 80).sum() / luma.size), 4)
    m["face_area_frac_skin_lips_cavity"] = round(float((sk | lp | cv).mean()), 3)
    m["dark_in_mouth_region_frac"] = round(float(((luma < 80) & (sk | lp | cv)).sum() / max(1, (luma < 80).sum())), 3)
    res[f"{t:.0f}s"] = m
    sbs = Image.new("RGB", (1920, 580), "white")
    sbs.paste(fr, (0, 40)); sbs.paste(ref, (960, 40))
    d = ImageDraw.Draw(sbs)
    d.text((10, 12), f"le-maki-mococo film frame {t:.0f} s (handmade paper mouth)", font=font, fill=(90, 80, 75))
    d.text((970, 12), "reference maki.webp (measured only; never pasted or traced)", font=font, fill=(90, 80, 75))
    sbs.save(OUT / f"compare_{t:04.1f}.png")
res["reference"] = Q.reference()
# E4: the framing bar, settled.  Reference flesh mass (all non-white pixels) and an upper-bound skin-only share
# (non-white minus lip-coloured, cavity and teeth pixels; colour segmentation under-counts the upper lip).
_r = np.asarray(Image.open(REF).convert("RGB")).astype(float)
_nw = ~(_r.min(2) > 240)
_lip = _nw & ((_r[..., 1] / (_r[..., 0] + 1)) < 0.72) & (_r[..., 2] > _r[..., 1] * 0.97)
_dk = _nw & (_r.mean(2) < 80)
_th = _nw & (_r.min(2) > 200)
res["reference_framing"] = dict(flesh_mass_frac=round(float(_nw.mean()), 3),
                                skin_only_frac_upper_bound=round(float((_nw & ~_lip & ~_dk & ~_th).mean()), 3),
                                note="maki.webp: non-white = skin + lips + cavity + teeth; skin-only by colour segmentation")
# acceptance 3: 'hangs' box at 0:24 vs 0:46 (alpha identical) and the knot constant
x0, y0, x1, y1 = [int(round(v)) for v in M.HANGS_BOX]
box = (slice(y0 - 26, y1 + 8), slice(x0 - 4, x1 + 4))
a24 = np.asarray(M.type_layer(24.0, F.ONSETS, cursor=False))[..., 3][box]
a46 = np.asarray(M.type_layer(46.0, F.ONSETS, cursor=False))[..., 3][box]
res["acc3_hangs_alpha_diff_24_vs_46"] = int(np.abs(a24.astype(int) - a46.astype(int)).sum())
res["acc3_knot"] = list(G.KNOT)
targets = dict(skin_dE76="<12", lip_dE76="<15", lip_span_h=">=0.35", lip_span_w=">=0.22", skin_max_x_frac="<0.45",
               field=">=250 every channel", flesh_area="0.35-0.50 (E4 amended bar: skin + lips + cavity; reference 0.386)",
               skin_only_area="reported, declared deviation: no 35% skin-only target (reference itself ~0.31)",
               dark_frac="<=0.04, cavity only")
res["targets"] = targets
res["framing_declaration"] = ("E4: plan §9 bar 7 said 'skin occupies 35-50%'. Measured on maki.webp, skin alone is at most "
    "~31% and the whole flesh mass 38.6%, so the bar is amended (plan.md, editor amendment E4) to the flesh mass "
    "(skin + lips + cavity) 35-50%. Skin alone is reported as skin_area_frac and is BELOW 35% (declared deviation): "
    "with the skin confined to x < 45% and lips >= 35% of frame height, skin alone cannot reach 35%.")
for k in ("6s", "46s"):
    m = res[k]
    m["pass"] = dict(skin=m["skin_dE76"] < 12, lip=m["lip_dE76"] < 15, field=min(m["field_mean_right_half_excl_layers"]) >= 250,
                     dark=m["dark_frac_mouth_region_left_half"] <= 0.04, skin_x=m["skin_max_x_frac"] < 0.45,
                     flesh_area=0.35 <= m["face_area_frac_skin_lips_cavity"] <= 0.50, cut_top_bottom=m["skin_touches_top"] and m["skin_touches_bottom"],
                     lip_span=m["lip_span_h"] >= 0.35 and m["lip_span_w"] >= 0.22)
json.dump(res, open(SW / "editor_measure.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
