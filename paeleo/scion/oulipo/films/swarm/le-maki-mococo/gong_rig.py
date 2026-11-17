"""le-maki-mococo · U3 image cue: gong -> binturong (SCION #43 Collage Graph Rewriting; #29 GrabCut as method).

Typed rewrite rule  replace(HangingThing.gong[hypothesis layer] -> HangingThing.binturong[cue layer])
  preconditions : t >= release(Q_image) (38.0 s); anchor == the same cord knot KNOT (asserted every frame);
                  the "hangs" glyph box unchanged (checked by the editor against mouth_rig.glyph_table()).
  graphic bridge: the same cord, the same knot, the pendulum's phase (the animal's sway starts from the gong's
                  residual angle at 38.0 s).
  method        : split (12 wedges released one per 3 frames from 38.0, bottom first) -> exit (ballistic fall
                  with spin, out of frame, per-frame physics on ones) ; enter (the engraving was already on the
                  plane behind: occlusion reveal; the wedges stay in front of it until they fall).

Materials
  HANDMADE : bronze-card gong (hammered repoussé height field, boss, rim lip), 12 scissor-cut wedges with the
             pale card core on every cut edge; two-ply twisted cord and knot  (u3/make_gong.py).
  FORAGED  : Brehm's Life of Animals (1895) p.265, "The Binturong", engraving signed Specht; Wikimedia Commons,
             Public domain (extmetadata re-read 2026-11-17).  GrabCut cutout seeded by hand-placed scissor points
             (u3/cut_binturong.py), rotated + scaled only, never mirrored or warped (u3/prep_hang.py), mounted
             on white card with a 5 px scissor-cut margin.
Planes (back -> front): field (editor) < upper cord < binturong card < attached gong wedges + cord loop < knot
  < falling wedges < labels.  Soft small cast shadows, light from the upper left (as the mouth).

Time base: film seconds, 24 fps.  Assembly, pendulum and sway are on twos (12 fps, paper stop-motion like the
mouth); the fracture runs on ones (per-frame physics).  Deterministic: no randomness at render time.

Public API
  hang_layer(t, cues=None, labels=True) -> PIL RGBA 960x540 (transparent field)
  events(cues=None)                     -> list of {t, kind, gain, pan, synth, note} for the mix (never a ring)
  theta_gong(t), theta_animal(t, cues)  -> degrees (clockwise on screen)
  wedge_state(k, t, cues)               -> dict(state, x, y, angle) (film px, gong-centre pivot)
  trajectories(cues)                    -> per-wedge release/exit + samples (for image_cue.json)
  graph_trace(cues)                     -> typed entity-graph trace (enter/swing/split/exit/enter)
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OULIPO = HERE.parents[2]
SRC = OULIPO / "films" / "sources" / "le-maki-mococo" / "imagecue"

W, H, S, FPS = 960, 540, 2, 24
KNOT = (850.0, 150.0)                 # the cord knot: the anchor of the rewrite (film px), constant
X0 = 600                              # the layer is rendered in the region x >= X0 (film px) at 2x
RW, RH = (W - X0) * S, H * S
T_ASM = 11.5                          # S2: Reader A's picture is assembled, one wedge per 2 frames
T_SWING = 24.0                        # S4: Reader B: "It hangs and swings" -> the gong is set swinging
T_IMAGE_DEFAULT = 38.0                # S6: Q_image release
LOOP = 10.0                           # cord loop from the knot to the gong's hole (film px)
G = 1500.0                            # gravity for the falling card wedges (film px / s^2)
# pendulum of the gong (S4-S5)
A_G, T_G, TAU_G = 9.0, 1.75, 4.2
# the animal's sway (S6-S8): starts from the gong's phase, kicked as its weight takes the cord
T_KICK, A_B, T_B, TAU_B = 38.5, 5.0, 2.4, 3.0
LABEL_COL = (107, 98, 91)             # muted #6b625b
INTER_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
INTER_REG = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
SHADOW_COL = np.array([62, 44, 36], np.float32)


# --------------------------------------------------------------------------------------------- cues
def t_image(cues=None):
    """Q_image release time from cues: None (cue_timeline.json or 38.0), {"Q_image": t}, or a list of cue dicts."""
    if cues is None:
        p = HERE / "cue_timeline.json"
        if p.exists():
            try:
                cues = json.loads(p.read_text()).get("cues")
            except Exception:
                cues = None
    if cues is None:
        return T_IMAGE_DEFAULT
    if isinstance(cues, dict):
        if "Q_image" in cues:
            v = cues["Q_image"]
            return float(v["t_avail"] if isinstance(v, dict) else v)
        for v in cues.values():
            if isinstance(v, dict) and v.get("cue_id") == "Q_image":
                return float(v.get("t_avail", v.get("t")))
        return T_IMAGE_DEFAULT
    for c in cues:
        if isinstance(c, dict) and c.get("cue_id") == "Q_image":
            return float(c.get("t_avail", c.get("t")))
    return T_IMAGE_DEFAULT


def twos(t):
    return math.floor(t * 12 + 1e-6) / 12.0


# --------------------------------------------------------------------------------------------- assets
@lru_cache(maxsize=1)
def assets():
    def premul(path):
        a = np.asarray(Image.open(path).convert("RGBA"), np.float32) / 255.0
        a[..., :3] *= a[..., 3:4]
        return a
    meta = json.loads((SRC / "wedges.json").read_text())
    hang = json.loads((SRC / "binturong_hang.json").read_text())
    wedges = []
    for m in meta["wedges"]:
        spr = premul(SRC / m["file"])
        pivot = (-m["offset_2x"][0], -m["offset_2x"][1])          # gong centre in sprite px
        wedges.append(dict(spr=spr, pivot=pivot, cen=np.array(m["centroid_rel_centre_2x"]) / S, mid=m["mid_angle_rad"]))
    hole = np.array(meta["hole_rel_centre_2x"]) / S                # film px, relative to the gong centre
    return dict(wedges=wedges, hole=hole, R=meta["radius_2x"] / S,
                animal=premul(SRC / "binturong_hang_rgba.png"), animal_pivot=tuple(hang["anchor_sprite_px_2x"]),
                cord=premul(SRC / "cord_tile.png"), knot=premul(SRC / "knot.png"),
                f_med=ImageFont.truetype(INTER_MED, 13 * S), f_reg=ImageFont.truetype(INTER_REG, 12 * S))


def gong_centre_rel():
    """Gong centre relative to the knot at theta=0 (film px): the hole hangs LOOP below the knot."""
    a = assets()
    return np.array([0.0, LOOP - a["hole"][1]])


def rot(deg):
    r = math.radians(deg)
    return np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])   # clockwise on screen (y down)


# --------------------------------------------------------------------------------------------- motion
def theta_gong(t):
    """Damped pendulum of the gong about the knot (deg, clockwise positive); impulse at T_SWING."""
    if t < T_SWING:
        return 0.0
    u = t - T_SWING
    return A_G * math.exp(-u / TAU_G) * math.sin(2 * math.pi * u / T_G)


def theta_animal(t, cues=None):
    """The binturong's sway about the same knot: continues the gong's residual phase, then a kick as its weight
    takes the cord (T_KICK), damped; essentially still from ~48 s (S7-S8)."""
    th = theta_gong(t)
    ti = t_image(cues)
    k = T_KICK + (ti - T_IMAGE_DEFAULT)
    if t > k:
        u = t - k
        th += A_B * (1 - math.exp(-u / 0.12)) * math.exp(-u / TAU_B) * math.sin(2 * math.pi * u / T_B)
    return th


ASM_ORDER = list(range(12))                   # clockwise from the top wedge (the one with the cord hole)


def release_order():
    """Fracture order: bottom wedges first (the animal's weight tears the card from below)."""
    a = assets()
    return sorted(range(12), key=lambda k: (-math.sin(a["wedges"][k]["mid"]), k))


def t_assembled(k):
    return T_ASM + ASM_ORDER.index(k) * 2 / FPS


def t_release(k, cues=None):
    return t_image(cues) + release_order().index(k) * 3 / FPS


def _fall_params(k):
    a = assets()
    rs = np.random.RandomState(500 + k)
    cen = a["wedges"][k]["cen"]
    u = cen / (np.linalg.norm(cen) + 1e-6)
    vr = rs.uniform(35, 70)
    v0 = u * vr + np.array([rs.uniform(-12, 12), rs.uniform(-30, 15)])
    spin = math.copysign(rs.uniform(110, 320), u[0] if abs(u[0]) > 0.15 else rs.uniform(-1, 1))
    return v0, spin


def wedge_state(k, t, cues=None):
    """Pose of wedge k: dict(state, x, y, angle) where (x,y) is where the gong-centre pivot of the sprite goes."""
    a = assets()
    knot = np.array(KNOT)
    if t < t_assembled(k):
        return dict(state="absent")
    tr = t_release(k, cues)
    if t < tr:
        th = theta_gong(twos(t))
        c = knot + rot(th) @ gong_centre_rel()
        placing = t < t_assembled(k) + 2 / FPS
        if placing:    # the piece is set down: on its first two frames it is still lifted, a little out and turned
            cen = a["wedges"][k]["cen"]
            u = cen / (np.linalg.norm(cen) + 1e-6)
            c = c + rot(th) @ (u * 4.0)
            return dict(state="placing", x=float(c[0]), y=float(c[1]), angle=th + 5.0)
        return dict(state="attached", x=float(c[0]), y=float(c[1]), angle=th)
    # ballistic exit with spin (ones)
    th0 = theta_gong(twos(tr))
    cen0 = rot(th0) @ a["wedges"][k]["cen"]
    c0 = knot + rot(th0) @ gong_centre_rel() + cen0
    v0, spin = _fall_params(k)
    v0 = rot(th0) @ v0
    u = t - tr
    c = c0 + v0 * u + np.array([0.0, 0.5 * G * u * u])
    ang = th0 + spin * u
    p = c - rot(ang) @ a["wedges"][k]["cen"]
    if c[1] - a["R"] > H + 10:
        return dict(state="gone")
    return dict(state="falling", x=float(p[0]), y=float(p[1]), angle=ang, cx=float(c[0]), cy=float(c[1]),
                lift=min(1.0, u / 0.5))


def t_exit(k, cues=None):
    """Time the wedge's centroid passes below frame + its radius (solved from the ballistic path)."""
    t = t_release(k, cues)
    while wedge_state(k, t, cues)["state"] != "gone":
        t += 1 / FPS / 4
    return t


# --------------------------------------------------------------------------------------------- compositing
def _paste(canvas, spr, pivot, x, y, ang, alpha=1.0, shadow=None):
    """Premultiplied 'over' of sprite (2x px) with its pivot at film (x,y), rotated ang deg clockwise."""
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), -ang, 1.0)
    M[0, 2] += (x - X0) * S - pivot[0]
    M[1, 2] += y * S - pivot[1]
    lay = cv2.warpAffine(spr, M, (RW, RH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if alpha < 1.0:
        lay *= alpha
    if shadow:
        dx, dy, blur, strength = shadow
        sa = cv2.GaussianBlur(lay[..., 3], (0, 0), blur * S)
        Ms = np.float32([[1, 0, dx * S], [0, 1, dy * S]])
        sa = cv2.warpAffine(sa, Ms, (RW, RH)) * strength
        canvas *= (1 - sa)[..., None]
        canvas[..., :3] += SHADOW_COL / 255.0 * sa[..., None]
        canvas[..., 3] += sa
    canvas *= (1 - lay[..., 3:4])
    canvas += lay


def _cord(canvas, y_from, y_to, x=KNOT[0], ang=0.0, alpha=1.0):
    """Vertical run of twisted cord from y_from to y_to (film px) through x, optionally rotated about its top."""
    a = assets()
    tile = a["cord"]
    n = int(max(2, (y_to - y_from) * S))
    reps = int(math.ceil(n / tile.shape[0])) + 1
    strip = np.concatenate([tile] * reps, 0)[:n]
    _paste(canvas, strip, (tile.shape[1] / 2, 0), x, y_from, ang, alpha, shadow=(1.5, 2.0, 1.2, 0.16))


def _label(canvas, lines, xy, anchor, alpha):
    if alpha <= 0:
        return
    a = assets()
    im = Image.new("L", (RW, RH), 0)
    d = ImageDraw.Draw(im)
    x, y = (xy[0] - X0) * S, xy[1] * S
    for i, (txt, f) in enumerate(lines):
        d.text((x, y + i * 17 * S), txt, font=a["f_med"] if f == "med" else a["f_reg"], fill=255, anchor=anchor)
    m = np.asarray(im, np.float32) / 255.0 * alpha
    canvas *= (1 - m)[..., None]
    canvas[..., :3] += np.array(LABEL_COL, np.float32) / 255.0 * m[..., None]
    canvas[..., 3] += m


def _key(t, cues):
    ti = t_image(cues)
    if ti - 0.01 <= t < ti + 2.6:          # fracture + first sway: ones
        return round(math.floor(t * FPS + 1e-6) / FPS, 5)
    return round(twos(t), 5)


def hang_layer(t, cues=None, labels=True):
    """RGBA 960x540 (transparent field) of the cord, the gong / binturong and their labels at film time t."""
    ti = t_image(cues)
    key = _key(t, cues)
    return _render(key, ti, bool(labels)).copy()


@lru_cache(maxsize=8)
def _render(t, ti, labels):
    cues = {"Q_image": ti}
    a = assets()
    canvas = np.zeros((RH, RW, 4), np.float32)
    # upper cord: from above the frame to the knot (static: the knot is the fixed anchor)
    _cord(canvas, -4.0, KNOT[1] + 1.0)
    # cue plane: the binturong (only once Q_image is released: precondition P4)
    if t >= ti:
        thb = theta_animal(t if t < ti + 2.6 else twos(t), cues)
        _paste(canvas, a["animal"], a["animal_pivot"], KNOT[0], KNOT[1], thb, shadow=(2.0, 3.0, 2.2, 0.20))
    # hypothesis plane: wedges still attached, and the cord loop through the hole
    attached = [k for k in range(12) if wedge_state(k, t, cues)["state"] in ("attached", "placing")]
    for k in attached:
        st = wedge_state(k, t, cues)
        w = a["wedges"][k]
        sh = (2.0, 3.0, 2.0, 0.18) if st["state"] == "attached" else (3.5, 5.0, 3.0, 0.16)
        _paste(canvas, w["spr"], w["pivot"], st["x"], st["y"], st["angle"], shadow=sh)
    holder = [k for k in attached if k in (0, 11)]
    if holder:     # the loop runs from the knot down to the hole in the top wedge(s)
        thg = theta_gong(twos(t))
        _cord(canvas, KNOT[1], KNOT[1] + LOOP + 3.0, ang=thg)
    elif t >= ti:  # after the gong has gone, the cord's free end hangs a little below the knot
        _cord(canvas, KNOT[1], KNOT[1] + 9.0, ang=theta_animal(twos(t), cues) * 1.6)
    # the knot: wrapped cord, on top (it also wraps the tail tip once the animal hangs)
    kn = a["knot"]
    _paste(canvas, kn, (kn.shape[1] / 2, kn.shape[0] / 2), KNOT[0], KNOT[1], 0.0, shadow=(1.5, 2.0, 1.2, 0.18))
    # falling wedges, in front of everything (per-frame physics)
    for k in release_order():
        st = wedge_state(k, t, cues)
        if st["state"] == "falling":
            w = a["wedges"][k]
            p = st["lift"]
            _paste(canvas, w["spr"], w["pivot"], st["x"], st["y"], st["angle"],
                   shadow=(2.0 + 4 * p, 3.0 + 6 * p, 2.0 + 3 * p, 0.18 - 0.08 * p))
    if labels:
        # "Reader A's picture (guess)": under the gong once assembled, gone as the image cue arrives
        al = min(1.0, max(0.0, (t - (T_ASM + 1.0)) / 0.5)) * (1.0 - min(1.0, max(0.0, (t - ti + 1 / FPS) / (2 / FPS))))
        _label(canvas, [("Reader A's picture (guess)", "med")], (KNOT[0], 340.0), "mt", al)
        # the engraving's own label, once the wedges are gone (upper left of the cord, clear of the poem column)
        al2 = min(1.0, max(0.0, (t - (ti + 1.6)) / 0.5))
        _label(canvas, [("Brehm, 1895", "med"), ("engraved by F. Specht", "reg")], (836.0, 52.0), "ra", al2)
    # anchor invariant: nothing moves the knot (asserted, not assumed)
    assert KNOT == (850.0, 150.0)
    out = np.zeros((RH, RW, 4), np.float32)
    alpha = np.clip(canvas[..., 3], 0, 1)
    out[..., :3] = np.where(alpha[..., None] > 1e-4, canvas[..., :3] / np.maximum(alpha[..., None], 1e-4), 0)
    out[..., 3] = alpha
    reg = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").resize((W - X0, H), Image.LANCZOS)
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.paste(reg, (X0, 0))
    return full


# --------------------------------------------------------------------------------------------- sound + ledger
def events(cues=None):
    """Sound events for the mix. All are paper or cord: kit-synthesised (declared) unless a foraged paper
    recording is supplied by the editor. There is never a metallic ring (invariant 7)."""
    ev = []
    for k in ASM_ORDER:
        ev.append(dict(t=round(t_assembled(k) + 2 / FPS, 4), kind="tick", gain=0.16, pan=0.55, synth="kit click (bright=3200)",
                       note=f"wedge {k} pinned in place (S2 assembly)"))
    first_ext = T_SWING + T_G / 4
    ev.append(dict(t=round(first_ext, 4), kind="creak", gain=0.10, pan=0.55, synth="kit band-passed noise 300-900 Hz, 0.35 s",
                   note="the cord creaks once at the first swing extreme (S4)"))
    for k in release_order():
        tr = t_release(k, cues)
        ev.append(dict(t=round(tr, 4), kind="tear", gain=0.14, pan=0.55, synth="kit click + band noise 1.5-6 kHz, 0.06 s (paper tear)",
                       note=f"wedge {k} comes loose (S6)"))
        ev.append(dict(t=round(t_exit(k, cues) + 0.12, 4), kind="land", gain=0.05, pan=0.6, synth="kit click (bright=1500), soft",
                       note=f"wedge {k} lands below frame (paper on paper)"))
    k0 = T_KICK + (t_image(cues) - T_IMAGE_DEFAULT)
    ev.append(dict(t=round(k0, 4), kind="flop", gain=0.18, pan=0.55, synth="kit thud freq=90 Hz, 0.2 s (card weight on the cord)",
                   note="the binturong's weight takes the cord"))
    ev.append(dict(t=round(k0 + T_B / 4, 4), kind="creak", gain=0.07, pan=0.55, synth="kit band-passed noise 300-900 Hz, 0.3 s",
                   note="the cord creaks softly at the animal's first sway extreme"))
    return sorted(ev, key=lambda e: e["t"])


def trajectories(cues=None, step=3):
    out = []
    for k in release_order():
        tr = t_release(k, cues)
        te = t_exit(k, cues)
        v0, spin = _fall_params(k)
        samples = []
        f = 0
        while True:
            t = tr + f / FPS
            st = wedge_state(k, t, cues)
            if st["state"] != "falling":
                break
            if f % step == 0:
                samples.append(dict(t=round(t, 4), cx=round(st["cx"], 1), cy=round(st["cy"], 1), angle=round(st["angle"], 1)))
            f += 1
        out.append(dict(wedge=k, release_rank=release_order().index(k), t_assembled=round(t_assembled(k), 4),
                        t_release=round(tr, 4), t_exit=round(te, 4), v0_local_px_s=[round(float(v), 1) for v in v0],
                        spin_deg_s=round(spin, 1), gravity_px_s2=G, samples=samples))
    return out


def graph_trace(cues=None):
    ti = t_image(cues)
    tl = max(t_release(k, cues) for k in range(12))
    te = max(t_exit(k, cues) for k in range(12))
    return [
        dict(t=0.0, op="enter", entity="Cord#1{knot=(850,150)}", layer="staging", note="empty cord + knot from the first frame"),
        dict(t=T_ASM, op="enter", entity="HangingThing#gong", layer="hypothesis", rule="assemble(12 wedges, 1 per 2 frames)",
             cites="Reader A (fictional) @0:10, cites sound", anchor=list(KNOT)),
        dict(t=round(T_ASM + 23 / FPS, 4), op="state", entity="HangingThing#gong", value="assembled"),
        dict(t=T_SWING, op="swing", entity="HangingThing#gong", value=f"damped pendulum A={A_G} deg T={T_G}s tau={TAU_G}s",
             cites="Reader B (fictional) @0:24 'It hangs and swings'", anchor=list(KNOT)),
        dict(t=ti, op="enter", entity="HangingThing#binturong", layer="cue", rule="replace(gong -> binturong)",
             preconditions=dict(t_ge_release_Q_image=True, anchor_equal=list(KNOT), hangs_glyph_box="checked by editor"),
             bridge="same cord, same knot, sway starts from the gong's residual phase", anchor=list(KNOT)),
        dict(t=ti, op="split", entity="HangingThing#gong", value="12 wedges, released 1 per 3 frames, bottom first"),
        dict(t=round(tl, 4), op="state", entity="HangingThing#gong", value="all wedges released"),
        dict(t=round(te, 4), op="exit", entity="HangingThing#gong", value="last wedge below frame"),
        dict(t=round(T_KICK + ti - T_IMAGE_DEFAULT, 4), op="swing", entity="HangingThing#binturong",
             value=f"weight kick A={A_B} deg T={T_B}s tau={TAU_B}s, settles by ~48 s", anchor=list(KNOT)),
    ]


if __name__ == "__main__":
    import sys
    t = float(sys.argv[1]) if len(sys.argv) > 1 else 38.5
    hang_layer(t).save(f"/tmp/hang_{t:.2f}.png")
