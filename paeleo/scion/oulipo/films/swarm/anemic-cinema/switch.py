"""Anemic cinema -- U3 switch: the ExposureSequence (score.json), Substitute (W1-W3), baselines.

One plate, one integer clock. theta is kept in integer TICKS, 1280 ticks per revolution
(lcm of the two periods 80 and 256), so omega_fast = 1/80 rev/frame = 16 ticks/frame and
omega_read = 1/128 rev/frame = 10 ticks/frame (repair 1; was 1/256); periodicity is exact in integer arithmetic.
theta in radians = 2 pi ticks / 1280, ccw positive on screen (shared field contract).

Substitute(D_from, D_to, window [k0, k0+18), omega) -- the central operation (plan.md s.4):
  W1 F126-143  T1 -> O_A  glyph -> squashed glyph -> dash at its own arc -> radial slide ->
               dashes on ring k's eccentric circle -> dashes close -> closed grooved ring.
               Ring k (k = 0..6, outside in) starts at F126 + 2k and takes 6 frames.
  W2 F246-263  O_A -> T2  the reverse (ring opens into dashes, slides inward/outward onto the
               T2 glyph places, dash -> squashed glyph -> glyph), outside in, 2-frame stagger.
  W3 F426-443  T2 -> O_B  discontinuous substitution (Foldes discontinuity marker): each run of
               T2 tokens is swapped, in token order, for ONE real key cutout of the run's arc
               length (GrabCut keys from optics.py), which then slides into its tangential
               bow-to-bit slot on one of 6 eccentric key rings. Key ring m starts at F426 + 2m.
Every mark is in exactly one state in every frame (no cross-blend between discs); the plate
is one continuous tone, blended between the camera-fixed plates by one global scalar.

Rendering (2x, 1920x1080, INTER_AREA down to 960x540): real 180 deg shutter integrating 8
sub-frames of the actual rotation; no grain, no vignette, no flicker. Warm grade only on the
optical discs, scaled by the same global scalar through a switch.

Run:  python3 -I switch.py score        writes score.json (do this first: glyphs.py reads it)
      python3 -I switch.py all          score + renders + fixtures + bell + ledgers
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import wave

import numpy as np

SEED = 1926
ROOT = "/home/user/bolas/paeleo/scion/oulipo"
WS = ROOT + "/films/swarm/anemic-cinema"
SRC = ROOT + "/films/sources/anemic-cinema"
MED = SRC + "/switch"
MED2 = SRC + ("/switch-switch-animator-timing-verifier-and-sound-forager-owns-score-json-"
              "exposuresequence-the-substitute-operation-for-w1-w3-all-fixtures-baselines-bell-")
FPS = 24
NFR = 576
TICKS = 1280
W_FAST = 16          # 1/80 rev/frame
W_READ = 5           # 1/256 rev/frame = 0.09375 rev/s, P = 256: the stable bar (repair 2 restores it; repair 1 had 10 = 1/128)
WIN = {"W1": (126, "T1", "O_A"), "W2": (246, "O_A", "T2"), "W3": (426, "T2", "O_B")}
WLEN = 18
STAGGER = 2
STAGES = 6
KIND = {"T1": "text", "T2": "text", "O_A": "optical", "O_B": "optical"}
READ = (288, 425)
LAST_RING = 6         # optics.NR - 1 (7 rings)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ================================================================== the score
def omega_ticks(k):
    """Integer ticks advanced from frame k to frame k+1."""
    if k < 24:
        return 0
    if k <= 264:
        return W_FAST
    if k < 288:                      # ease fast -> read over steps 265..287 (W2 + 1 frame held)
        return int(round(W_FAST + (W_READ - W_FAST) * (k - 264) / 24))
    if k <= 444:
        return W_READ
    if k < 468:                      # ease read -> fast over steps 445..467 (W3 + 1 frame held)
        return int(round(W_READ + (W_FAST - W_READ) * (k - 444) / 24))
    if k <= 515:
        return W_FAST
    return 0


def disc_of(k):
    if k < 24:
        return None, "title"
    if k < 126:
        return "T1", "body"
    if k < 144:
        return "O_A", "switch"
    if k < 246:
        return "O_A", "body"
    if k < 264:
        return "T2", "switch"
    if k < 426:
        return "T2", "body"
    if k < 444:
        return "O_B", "switch"
    if k < 516:
        return "O_B", "body"
    return "T2", "still"


def gain_of(k):
    if 126 <= k < 144:
        return 0.7
    if 144 <= k < 246:
        return 0.7 + 0.3 * smooth((k - 144) / (245 - 144))
    if 246 <= k < 264:
        return 1.0
    if 426 <= k < 444:
        return 1.0
    if 444 <= k < 516:
        return 1.0 - 0.3 * smooth((k - 444) / (515 - 444))
    return None


def window_of(k):
    for w, (k0, a, b) in WIN.items():
        if k0 <= k < k0 + WLEN:
            return w
    return None


def plate_mix(k):
    """Global plate scalar u (0 = from-plate, 1 = to-plate) inside a window."""
    w = window_of(k)
    if w is None:
        return None
    k0 = WIN[w][0]
    return smooth((k - k0 + 1) / WLEN)


def plate_front(w, k):
    """Radial plate front (repair 1): the ground transforms band by band with the marks, outer
    bands first, instead of one global crossfade. u(r) = smooth((k - k0 + 1 - 2 f(r)) / 4), with
    f(r) the continuous ring index at plate radius r (O_A rings for W1/W2, key rings for W3), so
    each band starts turning with its ring (2-frame stagger) and the innermost band completes at
    k0 + 17. Returns u at 2x (1080x1920), camera-fixed like the plates; no hard band edges."""
    G, O, cv2 = mods()
    key = ("rr2",)
    if key not in _CACHE:
        X, Y = O._grid(0, 0, O.W1X, O.H1X, 2)
        _CACHE[key] = np.hypot(X - O.CX, Y - O.CY).astype(np.float32)
    r = _CACHE[key]
    k0 = WIN[w][0]
    if w == "W3":
        R0, R1, n = O.KEY_R[0], O.KEY_R[-1], O.NKR - 1
    else:
        R0, R1, n = O.RING_R[0], O.RING_R[-1], O.NR - 1
    f = np.clip((R0 - r) / (R0 - R1) * n, 0, n)
    x = np.clip((k - k0 + 1 - STAGGER * f) / 4.0, 0, 1)
    return (x * x * (3 - 2 * x)).astype(np.float32)


def ring_stage(w, k, ring):
    """Local stage s = k - (k0 + 2 ring); <0 = not started, >= 6 = done.
    Repair 2 (W1 only): the innermost ring holds its glyphs two frames longer (starts at k0 + 14)
    and runs a 4-step metamorphosis squash -> slide -> closing -> ring, ending on the same frame
    k0 + 17. Without the hold, F138->139 changed the shape of every angular mark at once (rings
    4, 5, 6) and the rotation measured +1.8 % / -1.5 %; with it at most two rings change shape in
    any pair while the rest are rigid, and every W1 pair meets the +-1 % bar."""
    s = k - (WIN[w][0] + STAGGER * ring)
    if w == "W1" and ring == LAST_RING:
        s6 = k - (WIN[w][0] + STAGGER * ring + 2)
        return s6 if s6 < 0 else (0, 2, 4, 5)[min(s6, 3)] + max(0, s6 - 3)
    return s


def build_score(bodies=None):
    th = [0] * NFR
    for k in range(1, NFR):
        th[k] = th[k - 1] + omega_ticks(k - 1)
    th_still = th[360]
    frames = []
    for k in range(NFR):
        disc, state = disc_of(k)
        w = window_of(k)
        t = th[k] if state != "still" else th_still
        f = dict(k=k, t=round(k / FPS, 5), disc=disc, state=state, theta_ticks=t,
                 theta=2 * math.pi * (t % TICKS) / TICKS,
                 omega_ticks=omega_ticks(k), omega_rev_per_frame=omega_ticks(k) / TICKS,
                 gain=gain_of(k))
        if state == "still":
            f["shows_frame"] = 360 if k < 552 else [360, 361, 362]
        if w:
            k0, a, b = WIN[w]
            f["window"] = w
            f["from"], f["to"] = a, b
            f["plate_mix"] = round(plate_mix(k), 6)
            nr = 7 if w != "W3" else 6
            f["ring_stage"] = [ring_stage(w, k, r) for r in range(nr)]
        frames.append(f)
    return dict(
        film="anemic-cinema", unit="U3 switch", fps=FPS, frames_total=NFR, seconds=NFR / FPS,
        clock=dict(ticks_per_rev=TICKS, omega_fast=dict(ticks=W_FAST, rev_per_frame="1/80"),
                   omega_read=dict(ticks=W_READ, rev_per_frame="1/%d" % (TICKS // W_READ)), direction="ccw on screen",
                   rule="theta_{k+1} = theta_k + omega_ticks(k); theta = 2 pi theta_ticks / 1280"),
        windows={w: dict(frames=[k0, k0 + WLEN - 1], **{"from": a, "to": b},
                         stagger_frames=STAGGER, stages_per_ring=STAGES) for w, (k0, a, b) in WIN.items()},
        stage_key=dict(
            W1_W2="per ring s = k - (k0 + 2 ring). W1 forward: s<0 glyph; 0 squashed glyph; 1 dash at "
                  "glyph arc; 2 radial slide (t=0.5); 3 dashes on the ring circle (60 % arc); 4 dashes "
                  "closing (80 % of gaps); >=5 closed grooved ring. W2 reverse: s<0 ring; 0 dashes 80 %; "
                  "1 dashes 60 %; 2 slide; 3 dash at T2 glyph arc; 4 squashed glyph; >=5 glyph.",
            W3="per key ring m s = k - (k0 + 2 m); each run swaps at s = 0 (first half of the ring's "
               "runs in token order) or s = 1 (second half): glyphs -> one real key of the run's arc at "
               "the run's place (2 frames) -> slide to its slot (3 frames) -> home."),
        bodies=bodies or ["T1", "O_A", "T2", "O_B"],
        reading_interval=dict(frames=list(READ), omega="1/%d rev/frame constant" % (TICKS // W_READ)),
        theta_reading_start=2 * math.pi * (th[READ[0]] % TICKS) / TICKS,
        sound_cues=dict(bell=[126, 246, 426], elsewhere="declared digital silence"),
        frames=frames)


def write_score():
    sc = build_score()
    json.dump(sc, open(WS + "/score.json", "w"), indent=0)
    return sc


# ================================================================== rendering
_MODS = {}


def mods():
    if not _MODS:
        sys.path.insert(0, WS)
        import cv2
        import glyphs as G
        import optics as O
        _MODS.update(G=G, O=O, cv2=cv2)
    return _MODS["G"], _MODS["O"], _MODS["cv2"]


_CACHE = {}


def plates():
    if "plates" not in _CACHE:
        G, O, cv2 = mods()
        _CACHE["plates"] = {k: O.plate(k)[0] for k in ("text", "A", "B")}
        _CACHE["disc"] = O.plate("text")[1]
    return _CACHE["plates"]


def score():
    if "score" not in _CACHE:
        _CACHE["score"] = json.load(open(WS + "/score.json"))
    return _CACHE["score"]


def glyph_ring(pun):
    G, O, cv2 = mods()
    path, _ = G.glyph_path(pun)
    return [g["ring"] for g in path]


# ---- text layer (plate-texture space, N x N) with per-token drawing state
def letter_stack(pun, states):
    """states: list per token of None (absent), 'glyph', or ('squash', f)."""
    G, O, cv2 = mods()
    A = np.zeros((G.N, G.N), np.float32)
    for i, st in enumerate(states):
        if st is None:
            continue
        s = G.glyph_sprite(pun, i)
        if s["ch"] == " ":
            continue
        if st == "glyph":
            G.paste_affine(A, s["alpha"], s["ux"], s["uy"], s["vx"], s["vy"], s["cx"], s["cy"])
        else:
            f = st[1]
            G.paste_affine(A, s["alpha"], s["ux"] * 1.12, s["uy"] * 1.12, s["vx"] * f, s["vy"] * f,
                           s["cx"], s["cy"])
    return A, A * G.LETTER_L * G.LETTER_GROOVE


def text_composite(plateL, stack, theta, omega, nsub=8):
    """Exactly glyphs.render_text's model (rotate, emboss shadow down-right, letters over plate)
    but over an arbitrary camera-fixed plate. Returns full-frame L and letter alpha (2x)."""
    G, O, cv2 = mods()
    A, V = stack
    N = G.N
    x0, y0 = int(G.W2X / 2 - G.C), int(G.H2X / 2 - G.C)
    P = plateL[y0:y0 + N, x0:x0 + N]
    st = np.dstack([A, V])
    dth = 2 * math.pi * omega
    subs = [theta + dth * 0.5 * ((q + 0.5) / nsub - 0.5) for q in range(nsub)] if omega else [theta]
    accL = np.zeros((N, N), np.float32)
    accA = np.zeros((N, N), np.float32)
    for a in subs:
        rs = G._rot(st, a)
        at, vt = rs[..., 0], rs[..., 1]
        sh = cv2.GaussianBlur(np.roll(at, (3, 3), (0, 1)), (0, 0), 1.2)
        pl = P * (1 - 0.6 * sh * (1 - at))
        accL += pl * (1 - at) + vt * G.LIGHT_LET
        accA += at
    L = plateL.copy()
    L[y0:y0 + N, x0:x0 + N] = accL / len(subs)
    Af = np.zeros_like(plateL)
    Af[y0:y0 + N, x0:x0 + N] = accA / len(subs)
    return L, Af


# ---- free dashes (arcs about any plate-frame centre), same groove stock as the rings
def arcs_layer(arcs, theta, omega, nsub=8):
    """arcs: list of dict(cx, cy, rho, a, h, w, v) in 1x plate px (relative to the plate
    centre); a = centre angle about (cx, cy), h = half angle, w = thickness, v = stock L."""
    G, O, cv2 = mods()
    x0, y0, ww, hh = O.BX0, O.BY0, O.BX1 - O.BX0, O.BY1 - O.BY0
    if "grid" not in _CACHE:
        X, Y = O._grid(x0, y0, ww, hh, O.SS)
        ux, uy, uz, _ = O._sphere(X, Y)
        _CACHE["grid"] = (X, Y, (0.86 + 0.22 * O._lam(ux, uy, uz, O.L_A)).astype(np.float32))
    X, Y, light = _CACHE["grid"]
    sp = 1.0 / O.SS
    accA = np.zeros(X.shape, np.float32)
    accLA = np.zeros(X.shape, np.float32)
    angs = O._sub_angles(theta, omega, nsub)
    for th in angs:
        for q in arcs:
            mx = q["cx"] + q["rho"] * math.cos(q["a"])
            my = q["cy"] + q["rho"] * math.sin(q["a"])
            scx, scy = O._to_screen(mx, my, th)
            ext = q["rho"] * min(q["h"], math.pi) + q["w"] + 3
            i0 = max(int((scy - ext - y0) * O.SS), 0)
            i1 = min(int((scy + ext - y0) * O.SS) + 1, X.shape[0])
            j0 = max(int((scx - ext - x0) * O.SS), 0)
            j1 = min(int((scx + ext - x0) * O.SS) + 1, X.shape[1])
            if i0 >= i1 or j0 >= j1:
                continue
            sl = (slice(i0, i1), slice(j0, j1))
            px, py = O._to_plate(X[sl], Y[sl], th)
            ddx, ddy = px - q["cx"], py - q["cy"]
            d = np.sqrt(ddx * ddx + ddy * ddy)
            u = np.abs(d - q["rho"])
            a = np.clip((q["w"] / 2 - u) / sp + 0.5, 0, 1)
            dl = np.angle(np.exp(1j * (np.arctan2(ddy, ddx) - q["a"]))).astype(np.float32)
            a = a * np.clip((q["h"] - np.abs(dl)) * np.maximum(d, 1.0) / sp + 0.5, 0, 1)
            prof = 0.90 + 0.10 * np.clip(1 - (u / (q["w"] / 2)) ** 2, 0, 1)
            gr = 1.0 + O.GROOVE_DEPTH * np.cos((2 * np.pi / O.GROOVE_1X) * d)
            accA[sl] += a
            accLA[sl] += a * q["v"] * prof * gr * light[sl]
    n = len(angs)
    A = np.clip(accA / n, 0, 1)
    L = np.where(accA > 1e-6, accLA / np.maximum(accA, 1e-6), 0).astype(np.float32)
    Lf, Af = O._full(L, A.astype(np.float32))
    return dict(L=Lf, A=Af, tint="warm")


# ---- the correspondence c: glyph -> ring (W1/W2)
def dash_plan(pun, gain):
    """For each non-space token i: ring k, its glyph place (r1x, phi), its angle about ring k's
    centre, and the closing half-widths (80 % and 60 % of the neighbour gaps)."""
    G, O, cv2 = mods()
    path, _ = G.glyph_path(pun)
    rs = O.ring_set(gain)
    out = {}
    for k in range(O.NR):
        q = rs[k]
        toks = [g for g in path if g["ring"] == k and g["ch"] != " "]
        ent = []
        for g in toks:
            r1, phi = g["r"] / 2.0, g["phi"]
            gx, gy = r1 * math.cos(phi), r1 * math.sin(phi)
            ak = math.atan2(gy - q["oy"], gx - q["ox"])
            ent.append(dict(i=g["i"], r1=r1, phi=phi, ak=ak, adv1=g["adv"] / 2.0))
        n = len(ent)
        for j, e in enumerate(ent):
            nb = []
            if n > 1:
                prv = ent[(j - 1) % n]["ak"]
                nxt = ent[(j + 1) % n]["ak"]
                gp = (e["ak"] - prv) % (2 * math.pi)
                gn = (nxt - e["ak"]) % (2 * math.pi)
            else:
                gp = gn = math.pi
            e["gp"], e["gn"] = gp, gn
            e["h60"] = 0.6 * e["adv1"] / 2 / q["r"]
        out[k] = dict(ring=q, toks=ent)
    return out


def _segs_close(k, ent, frac):
    O = mods()[1]
    segs = []
    for e in ent:
        h0 = e["h60"]
        # repair 2: grow SYMMETRICALLY about the dash's own angle ak (half = frac x the mean
        # half-gap), so each closing arc keeps the dash's centroid and the frame-to-frame change
        # is a pure lengthening, not a shift (the asymmetric growth moved the centroids and read
        # as a +1.8 % rotation error at F138->139)
        hh = max(h0, frac * (e["gp"] + e["gn"]) / 4)
        a0 = e["ak"] - hh
        a1 = e["ak"] + hh
        segs.append(O.ring_segment_mask(k, a0, a1))
    return segs


def _segs_dash(k, ent):
    O = mods()[1]
    return [O.ring_segment_mask(k, e["ak"] - e["h60"], e["ak"] + e["h60"]) for e in ent]


def ring_switch_layers(w, k):
    """W1 / W2 frame k: returns (letter states for the text pun, ring_mask, free arcs, log)."""
    G, O, cv2 = mods()
    k0, a, b = WIN[w]
    pun = "T1" if w == "W1" else "T2"
    forward = (w == "W1")
    gain = 0.7 if forward else 1.0
    plan = dash_plan(pun, gain)
    path, _ = G.glyph_path(pun)
    states = [None] * len(path)
    ring_mask = [None] * (O.NR + 1)
    arcs = []
    log = {}
    cap1 = G.CAP / 2.0
    for ring in range(O.NR):
        s = ring_stage(w, k, ring)
        # map to the forward stage index e: -1 glyph, 0 squash, 1 dash@glyph, 2 slide, 3 dash@ring,
        # 4 closing, 5 closed ring
        if forward:
            e = -1 if s < 0 else min(s, 5)
        else:
            e = 5 if s < 0 else (4 - s if s <= 4 else -1)
        pr = plan[ring]
        q = pr["ring"]
        toks = pr["toks"]
        if e == -1:
            for g in path:
                if g["ring"] == ring:
                    states[g["i"]] = "glyph"
            log[ring] = "glyph"
        elif e == 0:
            for t in toks:
                states[t["i"]] = ("squash", 0.42)
            log[ring] = "squashed-glyph"
        elif e in (1, 2):
            tt = 0.0 if e == 1 else 0.5
            for t in toks:
                cx, cy = tt * q["ox"], tt * q["oy"]
                rho = (1 - tt) * t["r1"] + tt * q["r"]
                gx, gy = t["r1"] * math.cos(t["phi"]), t["r1"] * math.sin(t["phi"])
                ang = math.atan2(gy - cy, gx - cx)
                half = (0.9 * t["adv1"] / 2) / rho * (1 - tt) + tt * t["h60"] * q["r"] / rho
                wth = (1 - tt) * 0.36 * cap1 + tt * q["w"]
                v = 238.0 + (O.STOCK_A * q["b"] - 238.0) * (0.4 if e == 1 else 0.75)
                arcs.append(dict(cx=cx, cy=cy, rho=rho, a=ang, h=half, w=wth, v=v, i=t["i"]))
            log[ring] = "dash@glyph" if e == 1 else "slide"
        elif e == 3:
            ring_mask[ring] = _segs_dash(ring, toks)
            log[ring] = "dash@ring"
        elif e == 4:
            ring_mask[ring] = _segs_close(ring, toks, 0.8)
            log[ring] = "closing"
        else:
            ring_mask[ring] = 1.0
            log[ring] = "ring"
    # per-mark drawing log, read back from what is actually drawn
    drawn = {}
    for i, st in enumerate(states):
        if st is not None and path[i]["ch"] != " ":
            drawn.setdefault(i, []).append("glyph" if st == "glyph" else "squashed-glyph")
    for q_ in arcs:
        drawn.setdefault(q_["i"], []).append("free-dash")
    for ring in range(O.NR):
        if ring_mask[ring] is not None:
            for t in plan[ring]["toks"]:
                drawn.setdefault(t["i"], []).append("ring-arc" if ring_mask[ring] == 1.0 else "ring-dash")
    _CACHE["drawn"] = drawn
    # the grooved core travels with the innermost ring
    e6 = log[O.NR - 1]
    ring_mask[O.NR] = {"ring": 1.0, "closing": 0.55}.get(e6, None)
    return pun, states, ring_mask, arcs, log, gain


# ---- W3: runs of T2 tokens -> real keys -> slots
def key_plan():
    if "keyplan" in _CACHE:
        return _CACHE["keyplan"]
    G, O, cv2 = mods()
    path, _ = G.glyph_path("T2")
    slots = O.key_slots(1.0)
    runs = []
    for m in range(O.NKR):
        toks = [g for g in path if int(np.argmin([abs(g["r"] / 2 - R) for R in O.KEY_R])) == m]
        sl = [s for s in slots if s["ring"] == m]
        parts = np.array_split(np.arange(len(toks)), len(sl))
        rr = []
        for p in parts:
            gs = [toks[j] for j in p]
            ph = math.atan2(sum(math.sin(g["phi"]) for g in gs), sum(math.cos(g["phi"]) for g in gs))
            r1 = float(np.mean([g["r"] for g in gs])) / 2
            arc = sum(g["adv"] for g in gs) / 2
            rr.append(dict(tokens=[g["i"] for g in gs], phi=ph, r1=r1, arc1=arc))
        n = len(sl)
        best = None
        for c in range(n):
            cost = sum(abs(math.remainder(rr[q]["phi"] - sl[(q + c) % n]["phi"], 2 * math.pi)) for q in range(n))
            if best is None or cost < best[0]:
                best = (cost, c)
        c = best[1]
        for q, run in enumerate(rr):
            s = sl[(q + c) % n]
            run.update(ring=m, slot=s["i"], half=0 if q < (n + 1) // 2 else 1,
                       scale=float(np.clip(run["arc1"] / s["length"], 0.45, 1.25)))
            runs.append(run)
    _CACHE["keyplan"] = runs
    return runs


def key_switch_layers(k):
    G, O, cv2 = mods()
    path, _ = G.glyph_path("T2")
    slots = O.key_slots(1.0)
    states = ["glyph"] * len(path)
    placed = {}
    log = {}
    for run in key_plan():
        s = ring_stage("W3", k, run["ring"]) - run["half"]
        sl = slots[run["slot"]]
        if s < 0:
            log[run["slot"]] = "glyphs"
            continue
        for i in run["tokens"]:
            states[i] = None
        hx, hy = sl["pos"]
        hr, hphi = math.hypot(hx, hy), math.atan2(hy, hx)
        if s <= 1:
            t = 0.0
            log[run["slot"]] = "key@glyphs"
        elif s <= 4:
            t = smooth((s - 1) / 4)
            log[run["slot"]] = "slide"
        else:
            placed[run["slot"]] = {}
            log[run["slot"]] = "home"
            continue
        r = (1 - t) * run["r1"] + t * hr
        ph = run["phi"] + t * math.remainder(hphi - run["phi"], 2 * math.pi)
        ang = run["phi"] + t * math.remainder(sl["ang"] - run["phi"], 2 * math.pi)
        placed[run["slot"]] = dict(pos=[r * math.cos(ph), r * math.sin(ph)], ang=ang,
                                   scale=round((1 - t) * run["scale"] + t * 1.0, 3))
    return states, placed, log


# ---- frame compositor
def _final(L, u_warm):
    G, O, cv2 = mods()
    small = cv2.resize(L, (O.W1X, O.H1X), interpolation=cv2.INTER_AREA)
    if "disc1" not in _CACHE:
        X, Y = O._grid(0, 0, O.W1X, O.H1X, 1)
        _CACHE["disc1"] = np.clip(O.R - np.hypot(X - O.CX, Y - O.CY) + 0.5, 0, 1)[..., None]
    disc = _CACHE["disc1"]
    if isinstance(u_warm, np.ndarray):          # radial warm front (2x map) -> 1x
        u_warm = cv2.resize(u_warm, (O.W1X, O.H1X), interpolation=cv2.INTER_AREA)[..., None]
    rgb = small[..., None] * (1 + (O.WARM[None, None] - 1) * disc * u_warm)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


def _over(L, ly):
    return L * (1 - ly["A"]) + ly["L"] * ly["A"]


def render_body(disc, f, with_alpha=False):
    G, O, cv2 = mods()
    P = plates()
    th, om = f["theta"], f["omega_rev_per_frame"]
    if disc in ("T1", "T2"):
        key = ("stack", disc)
        if key not in _CACHE:
            _CACHE[key] = letter_stack(disc, ["glyph"] * len(G.glyph_path(disc)[0]))
        L, At = text_composite(P["text"], _CACHE[key], th, om)
        return (L, 0.0, At, np.zeros_like(At)) if with_alpha else (L, 0.0)
    if disc == "O_A":
        ly = O.render_rings(th, f["gain"], omega=om)
        L = _over(P["A"], ly)
        return (L, 1.0, np.zeros_like(L), ly["A"]) if with_alpha else (L, 1.0)
    if disc == "O_B":
        gr = O.render_keys(th, f["gain"], placed={}, omega=om, grooves=True)
        ky = O.render_keys(th, f["gain"], omega=om, grooves=False)
        L = _over(_over(P["B"], gr), ky)
        return (L, 1.0, np.zeros_like(L), ky["A"]) if with_alpha else (L, 1.0)
    raise ValueError(disc)


def render_frame(k, variant="film"):
    """Returns (rgb uint8 540x960x3, info). variant: film | B1 (hard cut at F126) | B2 (18-frame
    dissolve T1 -> O_A in W1). Outside W1 the baselines equal the film."""
    G, O, cv2 = mods()
    P = plates()
    f = score()["frames"][k]
    w = f.get("window")
    info = dict(k=k, variant=variant, window=w)
    if f["state"] == "title" or f["disc"] is None:
        return np.full((540, 960, 3), 2, np.uint8), info
    if w == "W1" and variant == "B1":
        L, uw, At, Ao = render_body("O_A", f, True)
        info.update(marks="O_A body (hard cut)", overlap=_overlap(At, Ao, 1.0, 1.0))
        return _final(L, uw), info
    if w == "W1" and variant == "B2":
        a = (k - 126 + 1) / (WLEN + 1)
        L1, _, At, _ = render_body("T1", f, True)
        L2, _, _, Ao = render_body("O_A", f, True)
        rgb = (1 - a) * _final(L1, 0.0).astype(np.float32) + a * _final(L2, 1.0).astype(np.float32)
        info.update(dissolve_alpha=a, marks="every T1 glyph at weight %.3f AND every O_A ring at %.3f" % (1 - a, a),
                    marks_multi_state=True, overlap=_overlap(At, Ao, 1 - a, a))
        return np.clip(rgb + 0.5, 0, 255).astype(np.uint8), info
    if w is None:
        disc = f["disc"]
        if f["state"] == "still":
            f = score()["frames"][360]
        L, uw, At, Ao = render_body(disc, f, True)
        info.update(overlap=_overlap(At, Ao, 1.0, 1.0))
        return _final(L, uw), info
    u = f["plate_mix"]
    th, om = f["theta"], f["omega_rev_per_frame"]
    if w in ("W1", "W2"):
        pun, states, ring_mask, arcs, log, gain = ring_switch_layers(w, k)
        um = plate_front(w, k)
        plateL = (1 - um) * P["text"] + um * P["A"] if w == "W1" else (1 - um) * P["A"] + um * P["text"]
        uw = um if w == "W1" else 1 - um
        stack = letter_stack(pun, states)
        L, At = text_composite(plateL, stack, th, om)
        Ao = np.zeros_like(L)
        if any(m is not None for m in ring_mask):
            ly = O.render_rings(th, gain, ring_mask=ring_mask, omega=om)
            L = _over(L, ly)
            Ao = np.maximum(Ao, ly["A"])
        if arcs:
            ly = arcs_layer(arcs, th, om)
            L = _over(L, ly)
            Ao = np.maximum(Ao, ly["A"])
        info.update(ring_states=log, glyphs=sum(1 for s in states if s == "glyph"),
                    squashed=sum(1 for s in states if isinstance(s, tuple)), dashes=len(arcs),
                    rings_closed=sum(1 for v in log.values() if v == "ring"),
                    per_mark_states=_mark_states(states, log, path_len=len(states)),
                    overlap=_overlap(At, Ao, 1.0, 1.0), plate_mix=u)
        return _final(L, uw), info
    # W3
    states, placed, log = key_switch_layers(k)
    um = plate_front("W3", k)
    plateL = (1 - um) * P["text"] + um * P["B"]
    stack = letter_stack("T2", states)
    L, At = text_composite(plateL, stack, th, om)
    gr = O.render_keys(th, 1.0, placed={}, omega=om, grooves=True)
    gr = dict(gr, A=gr["A"] * um)
    L = _over(L, gr)
    Ao = np.zeros_like(L)
    if placed:
        ky = O.render_keys(th, 1.0, placed=placed, omega=om, grooves=False)
        L = _over(L, ky)
        Ao = ky["A"]
    cnt = {}
    for v in log.values():
        cnt[v] = cnt.get(v, 0) + 1
    info.update(slot_states=cnt, glyphs=sum(1 for s in states if s == "glyph"), keys=len(placed),
                overlap=_overlap(At, Ao, 1.0, 1.0), plate_mix=u)
    return _final(L, um), info


def _mark_states(states, log, path_len):
    return dict(tokens_glyph=sum(1 for s in states if s == "glyph"),
                tokens_squashed=sum(1 for s in states if isinstance(s, tuple)),
                rings=log)


def _overlap(At, Ao, wt, wo):
    """Fraction of disc pixels (1x) where a text mark and an optical mark are both present with
    effective alpha > 0.2: a ghost of one disc over the other."""
    G, O, cv2 = mods()
    a = cv2.resize(At * wt, (960, 540), interpolation=cv2.INTER_AREA)
    b = cv2.resize(Ao * wo, (960, 540), interpolation=cv2.INTER_AREA)
    disc = _CACHE.get("disc1")
    if disc is None:
        _final(np.zeros((1080, 1920), np.float32), 0)
        disc = _CACHE["disc1"]
    d = disc[..., 0] > 0.5
    both = (a > 0.2) & (b > 0.2) & d
    return round(float(both.sum()) / float(d.sum()), 6)


# ================================================================== batch rendering
def _worker(args):
    k, variant, outdir = args
    import cv2
    rgb, info = render_frame(k, variant)
    p = f"{outdir}/{variant}_{k:03d}.png"
    cv2.imwrite(p, rgb[:, :, ::-1])
    info["sha1"] = hashlib.sha1(rgb.tobytes()).hexdigest()
    return info


def render_range(ks, variant, outdir, procs=4):
    import multiprocessing as mp
    os.makedirs(outdir, exist_ok=True)
    with mp.get_context("fork").Pool(procs) as pool:
        infos = pool.map(_worker, [(k, variant, outdir) for k in ks], chunksize=2)
    return infos


def encode(frames_dir, variant, ks, out_mp4, wav=None):
    lst = frames_dir + f"/{variant}_list.txt"
    with open(lst, "w") as fh:
        for k in ks:
            fh.write(f"file '{frames_dir}/{variant}_{k:03d}.png'\nduration {1 / FPS:.6f}\n")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if wav:
        cmd += ["-i", wav]
    cmd += ["-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
            "-tune", "animation"]
    if wav:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)



# ================================================================== measurement: polar phase correlation
def _gradmag(im):
    import cv2
    g = im.astype(np.float32).mean(axis=2) if im.ndim == 3 else im.astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return np.hypot(gx, gy)


def polar_step(img_a, img_b, nang=2880, r0=40, r1=226, refine=True):
    """Angle (deg, ccw on screen positive) by which frame b is a rotation of frame a.
    1) polar phase correlation: gradient magnitude (suppresses the smooth camera-fixed plate
       light) resampled to polar about the plate centre (2880 angle bins, r 40-226 px), cross-
       power summed over radii with partial whitening |X|^0.5, parabolic sub-bin peak;
    2) refinement: golden-section search (+-0.15 deg) of the rotation minimising the SSD of
       the gradient-magnitude images in the same annulus (cubic resampling).
    Returns (deg_refined, deg_phase_corr)."""
    import cv2
    A, B = _gradmag(img_a), _gradmag(img_b)

    def pol(g):
        return cv2.warpPolar(g, (r1, nang), (480.0, 270.0), r1,
                             cv2.WARP_POLAR_LINEAR + cv2.INTER_LINEAR)[:, r0:r1]
    Fa, Fb = np.fft.fft(pol(A), axis=0), np.fft.fft(pol(B), axis=0)
    cp = (Fb * np.conj(Fa)).sum(axis=1)
    cp /= (np.abs(cp) + 1e-9) ** 0.5
    c = np.real(np.fft.ifft(cp))
    j = int(np.argmax(c))
    y0, y1, y2 = c[(j - 1) % nang], c[j], c[(j + 1) % nang]
    den = y0 - 2 * y1 + y2
    sh = j + (0.5 * (y0 - y2) / den if den != 0 else 0.0)
    if sh > nang / 2:
        sh -= nang
    d0 = float(-sh * 360.0 / nang)
    if not refine:
        return d0, d0
    yy, xx = np.mgrid[0:A.shape[0], 0:A.shape[1]]
    rr = np.hypot(xx - 479.5, yy - 269.5)
    m = (rr > r0) & (rr < r1)

    def cost(d):
        M = cv2.getRotationMatrix2D((479.5, 269.5), d, 1.0)
        w = cv2.warpAffine(A, M, (A.shape[1], A.shape[0]), flags=cv2.INTER_CUBIC)
        return float(((w - B)[m] ** 2).mean())
    def search(c0):
        lo, hi = c0 - 0.15, c0 + 0.15
        for _ in range(36):
            m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
            if cost(m1) < cost(m2):
                hi = m2
            else:
                lo = m1
        return (lo + hi) / 2
    d1 = search(d0)
    # robust pass: marks that changed SHAPE between the two frames (hybrid frames) are outliers to
    # a rigid rotation; drop the 15 % largest residuals and search again (one reweighting step)
    M = cv2.getRotationMatrix2D((479.5, 269.5), d1, 1.0)
    res = np.abs(cv2.warpAffine(A, M, (A.shape[1], A.shape[0]), flags=cv2.INTER_CUBIC) - B)
    thr = np.percentile(res[m], 85)
    res_ok = cv2.erode((res < thr).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    m = m & res_ok
    return search(d1), d0


# ================================================================== the bell (FORAGED)
BELL_SRC = SRC + "/switch/raw/striking_bell_15cm.mp3"   # Commons PD, Wikimedia mp3 transcode
BELL_PEAK = 10 ** (-14.5 / 20)          # -14.5 dBFS in the wav, so the AAC-encoded peak stays <= -14 dBFS
BELL_LEN = 1.45
BELL_FADE = 0.35
RATE = 44100


def make_bell():
    """One real strike: the loudest, isolated strike of the recording (at about 47.4 s, preceded
    by >1 s of room tone and followed by >10 s of clean decay). Decode (ffmpeg) -> mono -> trim
    -> fade tail -> level peak to -14 dBFS. Nothing else (no EQ, no reverb, no pitch)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", BELL_SRC, "-ac", "1", "-ar", str(RATE),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    hop = RATE // 100
    env = np.array([np.abs(x[i:i + hop]).max() for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(env / env.max() + 1e-12)
    pk = int(np.argmax(env))
    j = pk
    while j > 0 and db[j] > -30 and pk - j < 30:
        j -= 1
    start = max(0, j * hop - int(0.005 * RATE))
    prev_quiet = float(db[max(0, j - 100):j].max()) if j > 0 else None
    n = int(BELL_LEN * RATE)
    seg = x[start:start + n].copy()
    fade = int(BELL_FADE * RATE)
    seg[-fade:] *= np.linspace(1, 0, fade) ** 2
    seg *= BELL_PEAK / np.abs(seg).max()
    e = np.array([np.abs(seg[i:i + hop]).max() for i in range(0, len(seg) - hop, hop)])
    p0 = int(np.argmax(e))
    rel = 20 * np.log10(e[p0:] / e[p0] + 1e-12)
    t20 = int(np.argmax(rel < -20)) / 100
    for d in (MED, MED2):
        os.makedirs(d, exist_ok=True)
        _write_wav(d + "/bell.wav", seg, 1)
    return dict(source=BELL_SRC, strike_peak_s=round(pk * hop / RATE, 3), chosen_onset_s=round(start / RATE, 4),
                loudest_level_in_1s_before_dB=prev_quiet, length_s=BELL_LEN, fade_s=BELL_FADE,
                peak_dbfs=round(20 * math.log10(np.abs(seg).max()), 2),
                decay_to_minus20dB_s=t20, audible_ring_s=round(BELL_LEN - BELL_FADE / 2, 2)), seg


def _write_wav(path, sig, ch):
    pcm = np.clip(np.round(sig * 32767), -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def sound_bed(seg, first_frame, nframes, silent=False):
    """Bell at the score's cue frames (relative to first_frame); declared digital silence elsewhere.
    Built with kit.Mix.add (pan 0 -> unity gain); kit.Mix.master() is NOT used because it boosts
    a track whose peak is < 0.25 by up to 4x (would put the bell at about -2 dBFS)."""
    sys.path.insert(0, ROOT + "/films")
    import kit
    mix = kit.Mix(nframes / FPS)
    cues = []
    if not silent:
        for c in score()["sound_cues"]["bell"]:
            if first_frame <= c < first_frame + nframes:
                mix.add(seg, (c - first_frame) / FPS, gain=1.0, pan=0.0)
                cues.append(c)
    st = np.stack([mix.L, mix.R], 1)
    return st, cues


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        sc = write_score()
        print("score.json", len(sc["frames"]), "theta_reading_start", sc["theta_reading_start"])
    elif len(sys.argv) > 1 and sys.argv[1] == "frame":
        import cv2
        for a in sys.argv[3:]:
            rgb, info = render_frame(int(a), sys.argv[2])
            cv2.imwrite(f"{MED}/probe_{sys.argv[2]}_{int(a):03d}.png", rgb[:, :, ::-1])
            print(json.dumps({k: v for k, v in info.items() if k != "per_mark_states"})[:400])
