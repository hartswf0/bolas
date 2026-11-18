"""boucle-la U3: exposure sheets (SCION 32 posing, SCION 1 timing), frame sequences per panel ID,
the page, the annotated page, page.json and route.json.   Run:  python3 -I build.py
"""
import copy
import hashlib
import json
import math
import os
import random
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panels as P  # noqa: E402

ROOT, SWARM, MEDIA = P.ROOT, P.SWARM, P.MEDIA
FRAMES = os.path.join(MEDIA, "frames")
CJ = P.RIG.cj
FPS, ON = 24, 2  # on 2s


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def canon(pid):
    return P.U1.pose_from(CJ["poses"][pid]["canonical"])


def entry(pid):
    return P.U1.pose_from(CJ["poses"][pid]["entry"])


def Q(base, **kw):
    """pose from base with overrides: g_lean, g_head, g_fore, o_lean, o_head, o_fore, o_note_turn, o_note_tilt."""
    p = copy.deepcopy(base)
    for k, v in kw.items():
        f, j = k.split("_", 1)
        p["gustave" if f == "g" else "odette"][j] = float(v)
    return p


def mix(a, b, t):
    out = copy.deepcopy(a)
    for f in out:
        for j in set(a[f]) | set(b[f]):
            out[f][j] = a[f].get(j, 0.0) + (b[f].get(j, 0.0) - a[f].get(j, 0.0)) * t
    return out


def between(keys, n):
    """keys: {drawing: pose}; smoothstep in-betweens.  Returns n poses."""
    ks = sorted(keys)
    out = []
    for d in range(n):
        if d <= ks[0]:
            out.append(copy.deepcopy(keys[ks[0]]))
            continue
        if d >= ks[-1]:
            out.append(copy.deepcopy(keys[ks[-1]]))
            continue
        i = max(i for i in range(len(ks)) if ks[i] <= d)
        a, b = ks[i], ks[i + 1]
        t = (d - a) / (b - a)
        t = t * t * (3 - 2 * t)
        out.append(mix(keys[a], keys[b], t))
    return out


def r1(p):
    return {f: {j: round(v, 3) for j, v in p[f].items()} for f in p}


# ---------------------------------------------------------------- exposure sheets
def sheet_A():
    C, E = canon("A"), entry("A")
    keys = {
        0: E,
        1: Q(E, o_fore=0, o_head=4, o_lean=1.2),                       # anticipation: the hand dips, she draws in
        3: Q(C, o_fore=24, o_head=-1, o_lean=-0.8, g_head=-1, g_fore=10),  # fast raise (paper jerk: few in-betweens)
        5: Q(C, o_fore=46, o_head=-6, o_lean=-2.6, g_head=-5, g_fore=16),  # overshoot at the top of the raise
        7: Q(C, o_fore=40, o_head=-11, o_lean=-2.4, g_head=-12, g_lean=-2.2, g_fore=15),  # head nod accent; his head lags back
        9: Q(C, o_fore=37, o_head=-6, g_head=-10, g_lean=-1.8),
        12: Q(C, o_fore=38.5, o_head=-7.6, g_head=-7.4),
        15: Q(C, o_head=-6.8, g_head=-8.3),
        19: C,
    }
    return between(keys, 20), 7


def sheet_B():
    C, E = canon("B"), entry("B")
    keys = {
        0: E,
        1: Q(E, g_head=7, g_lean=1.4, g_fore=12),                      # anticipation: he dips in
        2: Q(E, g_head=3, g_lean=0.2, g_fore=-14, o_fore=6),           # the flip starts (body leads)
        3: Q(C, g_head=-5, g_lean=-2.0, g_fore=-46, o_fore=0),
        4: Q(C, g_head=-14, g_lean=-3.6, g_fore=-66, o_fore=-6),       # forearm overshoot, palm out
        5: Q(C, g_head=-22, g_lean=-3.4, g_fore=-60, o_fore=-11),      # head lags one drawing: jerk back nose-up ("MOI")
        7: Q(C, g_head=-14, g_fore=-55, o_fore=-12, o_head=5),
        9: Q(C, g_head=-17.5, g_fore=-59.5),
        12: Q(C, g_head=-15.4, g_fore=-57.6),
        15: Q(C, g_head=-16.4, o_head=4.4),
        19: C,
    }
    return between(keys, 20), 5


def sheet_C():
    C, E = canon("C"), entry("C")
    keys = {
        0: E,
        1: Q(E, o_lean=2.0, o_head=3, o_fore=5),                       # anticipation: she rocks back on her heels
        3: Q(C, o_lean=-3.4, o_head=-1, o_fore=12, o_note_tilt=-9),    # the lean leads from the feet
        5: Q(C, o_lean=-6.8, o_head=-5, o_fore=22, o_note_tilt=-18, g_head=-1),  # overshoot
        6: Q(C, o_lean=-6.2, o_head=-12, o_fore=21, g_head=-6, g_lean=-1.6),     # head arrives one drawing later (accent)
        8: Q(C, o_lean=-4.6, o_head=-8.2, g_head=-3.2),
        11: Q(C, o_lean=-5.3, o_head=-9.6, g_head=-4.4),
        15: Q(C, o_lean=-4.9, o_head=-8.8),
        19: C,
    }
    return between(keys, 20), 6


def sheet_H():
    C, E = canon("H"), entry("H")
    sw = Q(E, g_lean=1.5, g_head=8.6, o_lean=-1.0, o_head=-6.0)       # heads swung in
    pt = Q(sw, g_fore=-22, g_lean=2.2, o_fore=24)                      # he points, she lifts the note
    keys = {
        0: E,
        2: Q(E, g_head=3.2, o_head=-2.0, g_lean=0.5, o_lean=-0.3),      # heads swing in over drawings 0-5
        4: Q(E, g_head=9.6, o_head=-6.8, g_lean=1.4, o_lean=-1.1),      # overshoot
        5: sw,
        6: Q(sw, g_fore=-4, o_fore=17),
        9: Q(pt, g_fore=-26, o_fore=25),                               # overshoot of the point
        11: pt,
        13: Q(pt, g_head=11, g_lean=2.6, o_note_tilt=-7),              # he jabs a nod at it; she lifts it to look
        15: Q(pt, g_head=8.4, o_note_tilt=-5),
        17: Q(pt, g_head=9.2, g_lean=2.4, o_note_tilt=-4),
        18: Q(pt, g_head=9.0, g_lean=2.5, o_note_tilt=-4),
    }
    seq = between(keys, 19)
    # the card flip: 6 drawings, substitution back -> face at edge-on (90); drawing 24 is face-out
    for k, turn in enumerate([30, 60, 90, 120, 150, 180]):
        seq.append(Q(pt, g_head=9.0, g_lean=2.5, o_note_tilt=-4, o_note_turn=turn, o_fore=24 + k * 0.33))
    FACE = len(seq) - 1
    fo = seq[-1]
    # recoil: the lean leads, the head lags a drawing (overshoot 12), settle -> canonical H; his nod accent at 30
    rec = [
        Q(fo, o_lean=0.6, o_head=-3.0),
        Q(fo, o_lean=1.8, o_head=1.0),
        Q(fo, o_lean=2.9, o_head=6.5),
        Q(fo, o_lean=2.7, o_head=12.0),
        Q(fo, o_lean=2.5, o_head=11.0, g_head=10.0),
        Q(fo, o_lean=2.5, o_head=10.4, g_head=11.2),   # 30: his head accent -> balloon
        Q(fo, o_lean=2.5, o_head=10.0, g_head=9.6),
    ]
    seq += rec
    seq.append(C)
    return seq, FACE + 6, FACE


SHEETS = {}
for pid, fn in (("A", sheet_A), ("B", sheet_B), ("C", sheet_C)):
    s, acc = fn()
    SHEETS[pid] = dict(poses=s, balloon_drawing=acc, face_out=None)
s, acc, face = sheet_H()
SHEETS["H"] = dict(poses=s, balloon_drawing=acc, face_out=face)


def jitter(pid, d, n):
    """Gilliam paper jerk: a pinned cut-out never sits still between drawings; final drawing exact."""
    if d == n - 1:
        return (0.0, 0.0), 0.0, 0.0
    rs = random.Random(1000 * "ABCH".index(pid) + d)
    k = 1.0 if d < n - 4 else 0.5
    return (rs.uniform(-0.9, 0.9) * k, rs.uniform(-0.7, 0.7) * k), rs.uniform(-0.3, 0.3) * k, rs.uniform(-0.3, 0.3) * k


# ---------------------------------------------------------------- render every drawing
def fk_check(J, J0):
    err = 0.0
    dev = 0.0
    for f in ("gustave", "odette"):
        j = J[f]
        err = max(err, math.dist(j["neck"], j["neck_on_head"]), math.dist(j["elbow"], j["elbow_on_fore"]))
        for a, b in (("neck", "elbow"), ("elbow", "hand"), ("feet", "neck"), ("neck_on_head", "mouth")):
            dev = max(dev, abs(math.dist(j[a], j[b]) - math.dist(J0[f][a], J0[f][b])))
    return err, dev


report = {}
held = {}
for pid in "ABCH":
    sh = SHEETS[pid]
    poses = sh["poses"]
    n = len(poses)
    C = canon(pid)
    d_out = os.path.join(FRAMES, pid)
    if os.path.isdir(d_out):
        shutil.rmtree(d_out)
    os.makedirs(d_out)
    _, J0, _, _ = P.figures(pid, C, black=(pid == "H"))
    drawings, worst_err, worst_dev, note_err = [], 0.0, 0.0, 0.0
    prev = None
    for d, pose in enumerate(poses):
        (jx, jy), jg, jo = jitter(pid, d, n)
        pz = copy.deepcopy(pose)
        pz["gustave"]["lean"] = pz["gustave"].get("lean", 0) + jg
        pz["odette"]["lean"] = pz["odette"].get("lean", 0) + jo
        black = pid == "H" and d >= sh["face_out"]
        show = d >= sh["balloon_drawing"]
        g, J, (note_c, hand), Ms = P.render(pid, pz, show, black=black, canon=C, jitter=(jx, jy))
        e, dv = fk_check(J, J0)
        worst_err, worst_dev = max(worst_err, e), max(worst_dev, dv)
        hx, hy = P.U1.ap(Ms["odette_fore"], P.RIG.j["odette"]["hand"])
        note_err = max(note_err, math.dist((hx, hy), J["odette"]["hand"]))
        p = os.path.join(d_out, f"d{d:03d}.png")
        Image.fromarray(g, "L").convert("RGB").save(p, optimize=False)
        h = sha_file(p)
        assert h != prev, f"{pid} drawing {d} repeats the previous drawing"
        prev = h
        drawings.append(dict(drawing=d, file=os.path.relpath(p, ROOT), sha256=h, pose=r1(pz), jitter_px=[round(jx, 3), round(jy, 3)],
                             balloon=show, ground="spot black" if (pid == "H" and black) else "page"))
    # frame sequence on 2s: hard links so paired occurrences replay the same bytes
    frames = []
    for d in range(n):
        for k in range(ON):
            fi = d * ON + k
            fp = os.path.join(d_out, f"f{fi:04d}.png")
            os.link(os.path.join(d_out, f"d{d:03d}.png"), fp)
            frames.append(dict(frame=fi, drawing=d, sha256=drawings[d]["sha256"]))
    held[pid] = np.asarray(Image.open(os.path.join(d_out, f"d{n - 1:03d}.png")).convert("RGB"))
    report[pid] = dict(n=n, drawings=drawings, frames=frames, fk_joint_err_px=round(worst_err, 4), fk_bone_dev_px=round(worst_dev, 4),
                       note_anchor_err_px=round(note_err, 4))
    print(pid, n, "drawings", "joint err", round(worst_err, 4), "bone dev", round(worst_dev, 4))

# ---------------------------------------------------------------- the page
page = np.full((P.PH, P.PW, 3), P.PAGE, np.float32)
LET = os.path.join(ROOT, "films/sources/boucle-la/dialogue-writer/lettering")


def paste_rgba(dst, path, x, y, alpha_scale=1.0):
    im = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    h, w = im.shape[:2]
    a = im[..., 3:4] / 255 * alpha_scale
    sub = dst[y:y + h, x:x + w]
    sub[:] = sub * (1 - a) + im[..., :3] * a
    return (x, y, x + w, y + h)


paste_rgba(page, os.path.join(LET, "margin-column.png"), 0, 0)
crop = {}
for slot, pid in zip(P.SLOTS, P.SEQ):
    x0, y0, x1, y1 = P.crop_rect(slot)
    page[y0:y1, x0:x1] = held[pid]
    crop[slot] = (x0, y0, x1, y1)
# panel IDs: in the right-hand gutter beside each panel's bottom-right corner (outside every crop)
id_rects = {}
for slot, pid in zip(P.SLOTS, P.SEQ):
    x0, y0, x1, y1 = P.RECT[slot]
    im = Image.open(os.path.join(LET, f"id-{pid}.png")).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    im = im.crop(bb)
    if im.width > 16:  # fit the 30 px gutter between neighbouring crops
        im = im.resize((16, max(1, round(im.height * 16 / im.width))), Image.LANCZOS)
    tmp = os.path.join(MEDIA, "lettering", f"id-{pid}-tight.png")
    im.save(tmp)
    px, py = x1 + P.PAD["r"] + 1, y1 - im.height
    r = paste_rgba(page, tmp, px, py)
    id_rects[slot] = r
    for s2, c in crop.items():
        assert not (r[0] < c[2] and c[0] < r[2] and r[1] < c[3] and c[1] < r[3]), (slot, s2)
page8 = np.clip(page + 0.5, 0, 255).astype(np.uint8)
os.makedirs(os.path.join(ROOT, "assets/pages"), exist_ok=True)
PAGE_PNG = os.path.join(ROOT, "assets/pages/boucle-la.png")
Image.fromarray(page8, "RGB").save(PAGE_PNG)

# pair identity (page crops), held drawing == page crop
pairs = [("r1c1", "r3c3"), ("r1c2", "r3c2"), ("r1c3", "r3c1")]
crop_sha = {}
for slot, pid in zip(P.SLOTS, P.SEQ):
    x0, y0, x1, y1 = crop[slot]
    c = page8[y0:y1, x0:x1]
    crop_sha[slot] = sha_bytes(c.tobytes())
    assert np.array_equal(c, held[pid]), f"page crop {slot} != held drawing {pid}"
for a, b in pairs:
    assert crop_sha[a] == crop_sha[b]

# tone stats (V1) and chroma
L = page8.mean(axis=2)
tone = {}
for slot, pid in zip(P.SLOTS, P.SEQ):
    x0, y0, x1, y1 = P.RECT[slot]
    sub = L[y0:y1, x0:x1]
    tone[slot] = dict(id=pid, black_lt60=round(float((sub < 60).mean()), 4), mid=round(float(((sub >= 60) & (sub <= 200)).mean()), 4),
                      white_gt200=round(float((sub > 200).mean()), 4))
chroma = page8.max(axis=2).astype(int) - page8.min(axis=2).astype(int)
tone["page"] = dict(black_lt60=round(float((L < 60).mean()), 4), white_gt200=round(float((L > 200).mean()), 4),
                    chroma_p99=float(np.percentile(chroma, 99)))
print("tone", json.dumps(tone))

# ---------------------------------------------------------------- annotated page (gutters only)
from PIL import ImageDraw  # noqa: E402
SS = 3
ann = Image.new("L", (P.PW * SS, P.PH * SS), 0)
dr = ImageDraw.Draw(ann)
rs = random.Random(77)


def pen(pts, w=3.0):
    q = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L_ = math.hypot(x1 - x0, y1 - y0)
        for t in np.linspace(0, 1, max(2, int(L_ / 60)), endpoint=False):
            q.append(((x0 + (x1 - x0) * t + rs.uniform(-0.8, 0.8)) * SS, (y0 + (y1 - y0) * t + rs.uniform(-0.8, 0.8)) * SS))
    q.append((pts[-1][0] * SS, pts[-1][1] * SS))
    dr.line(q, fill=255, width=int(w * SS), joint="curve")


def arrow(x, y, dx, dy, s=13):
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    dr.polygon([((x + ux * s) * SS, (y + uy * s) * SS), ((x - uy * s * 0.6) * SS, (y + ux * s * 0.6) * SS),
                ((x + uy * s * 0.6) * SS, (y - ux * s * 0.6) * SS)], fill=255)


g1, g2, g3, xr, xl = 635, 1165, 1781, 3186, 547  # gutter centre-lines: under row 1, under H, under row 3; right margin; left gutter
route_pts = [(575, g1), (xr, g1), (xr, g2), (xl, g2), (xl, g3), (3150, g3)]
pen(route_pts)
arrow(3150, g3, 1, 0)
for x in (1000, 1880, 2760):
    arrow(x, g1, 1, 0, 10)
arrow(xr, (g1 + g2) / 2, 0, 1, 10)
arrow(1865, g2, -1, 0, 10)
arrow(xl, (g2 + g3) / 2, 0, 1, 10)
for x in (1000, 1880):
    arrow(x, g3, 1, 0, 10)
annot = np.asarray(ann.resize((P.PW, P.PH), Image.LANCZOS), np.float32) / 255
# speech-act tags (U2's lettering) sitting on the route line in the gutters, scaled to fit 30 px gutters
tag_files = ["tag-o1-accuse", "tag-o2-deny", "tag-o3-press", "tag-o4-reveal", "tag-o5-deflect", "tag-o6-jab", "tag-o7-counter-accuse"]
tag_pos = []
layer = np.zeros((P.PH, P.PW), np.float32)
for i, (slot, tf) in enumerate(zip(P.SLOTS, tag_files)):
    im = Image.open(os.path.join(LET, tf + ".png")).convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    TH = 15
    sc = TH / im.height
    im = im.resize((max(1, int(im.width * sc)), TH), Image.LANCZOS)
    a = np.asarray(im.getchannel("A"), np.float32) / 255
    x0, y0, x1, y1 = P.RECT[slot]
    gy = {0: g1, 1: g1, 2: g1, 3: g2, 4: g3, 5: g3, 6: g3}[i]
    cx = (x0 + x1) // 2
    tx, ty = cx - im.width // 2, gy - TH // 2
    # a white knock-out under the tag so the route line breaks around it (still inside the gutter)
    annot[ty - 1:ty + TH + 1, tx - 8:tx + im.width + 8] = 0
    layer[ty:ty + TH, tx:tx + im.width] = np.maximum(layer[ty:ty + TH, tx:tx + im.width], a)
    tag_pos.append(dict(occurrence=i + 1, slot=slot, id=P.SEQ[i], tag=tf.split("-", 2)[2].upper(), rect=[tx, ty, tx + im.width, ty + TH]))
for r in id_rects.values():  # the route line also breaks around the gutter panel IDs
    annot[r[1] - 3:r[3] + 3, r[0] - 3:r[2] + 3] = np.minimum(annot[r[1] - 3:r[3] + 3, r[0] - 3:r[2] + 3], layer[r[1] - 3:r[3] + 3, r[0] - 3:r[2] + 3])
annot = np.maximum(annot, layer)
# gutters-only check: nothing inside any panel crop
for c in crop.values():
    assert annot[c[1]:c[3], c[0]:c[2]].max() < 0.02, c
ann_page = page * (1 - annot[..., None]) + P.INK * annot[..., None]
ANN_PNG = os.path.join(ROOT, "assets/pages/boucle-la-annotated.png")
Image.fromarray(np.clip(ann_page + 0.5, 0, 255).astype(np.uint8), "RGB").save(ANN_PNG)
a8 = np.clip(annot * 255 + 0.5, 0, 255).astype(np.uint8)
ink = np.full_like(a8, P.INK)
LAYER_PNG = os.path.join(MEDIA, "annotation-layer.png")
Image.fromarray(np.dstack([ink, ink, ink, a8]), "RGBA").save(LAYER_PNG)

# ---------------------------------------------------------------- film helper media
# ghost page: every story panel at 22 % ink over page (film only); furniture fully inked
ghost = page.copy()
for slot in P.SLOTS:
    x0, y0, x1, y1 = crop[slot]
    sub = page[y0:y1, x0:x1]
    ghost[y0:y1, x0:x1] = P.PAGE - (P.PAGE - sub) * 0.22
GHOST_PNG = os.path.join(MEDIA, "page-ghost.png")
Image.fromarray(np.clip(ghost + 0.5, 0, 255).astype(np.uint8), "RGB").save(GHOST_PNG)
shutil.copyfile(PAGE_PNG, os.path.join(MEDIA, "page.png"))

json.dump(dict(report=report, tone=tone, crop=crop, crop_sha=crop_sha, id_rects=id_rects, tags=tag_pos, route_pts=route_pts,
               sheets={k: dict(balloon_drawing=v["balloon_drawing"], face_out=v["face_out"]) for k, v in SHEETS.items()},
               balloons={k: P._BALLOON[k][3] for k in P._BALLOON},
               outputs=dict(page=PAGE_PNG, annotated=ANN_PNG, layer=LAYER_PNG, ghost=GHOST_PNG)),
          open(os.path.join(MEDIA, "build-report.json"), "w"), indent=1, ensure_ascii=False)
print("ok")
