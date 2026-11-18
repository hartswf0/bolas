"""Shared photo-cutout helpers for pages 45 and 48 (batch 5): the 99-ways-template rig (build_page.py: Rothstein 1937
clerk pieces with FK, clerk-removed set plates, cupboard door + ANRC key on its hook, Rothstein clock case with its
own hands re-set on the arbor), plus a HANDMADE seconds hand for the clock and a door/key variant whose tag can swing.
Importing build_page only loads its pieces; nothing foraged is executed."""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
sys.path.insert(0, str(pen99.TPL / "page"))
import build_page as bp  # noqa: E402

T, S, R, about, apply = bp.T, bp.S, bp.R, bp.about, bp.apply


def clock_on(P, at, kk, hh, mm, ss=None, name="clock"):
    """Lay the Rothstein clock case (cut-out, scissor margin) with its own hands set to hh:mm(:ss) on the arbor.
    ss: a HANDMADE seconds hand (a thin inked needle with a counterweight, cut paper) is added at ss seconds."""
    h, w = P.c.shape[:2]
    cc = bp.PC["clock.case"]
    arb = cc["piv"]["arbor"]
    Mclk = T(at[0], at[1]) @ S(kk) @ T(-arb[0], -arb[1])
    P.piece(name + ".case", cc["g"], cc["a"], Mclk @ T(*cc["o"]), margin=7, meta={"piece": "clock.case"})
    t_min = mm + (ss or 0) / 60.0
    for n, ang in [("clock.hour", (hh % 12) * 30 + t_min * 0.5), ("clock.minute", t_min * 6)]:
        pc = bp.PC[n]
        rot = ang - bp.man["pieces"][n]["source_angle_deg"]
        Mh = Mclk @ about(arb, R(rot)) @ T(*pc["o"])
        hg = cv2.warpAffine(pc["g"], Mh[:2], (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(pc["a"], Mh[:2], (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        P.over(name + "." + n.split(".")[1], np.repeat(hg[..., None], 3, 2), ha, {"piece": n, "set_to_deg": ang})
    centre = apply(Mclk, arb)
    if ss is not None:
        a = math.radians(ss * 6)
        L = 118 * kk                        # source dial radius ~140 px
        u = np.array([math.sin(a), -math.cos(a)])
        p1 = centre + u * L
        p0 = centre - u * 34 * kk
        m = np.zeros((h, w), np.uint8)
        cv2.line(m, tuple(int(v) for v in p0 * 4), tuple(int(v) for v in p1 * 4), 255, max(2, int(round(5 * kk))),
                 cv2.LINE_AA, shift=2)
        cw = p0 + u * 6 * kk
        cv2.circle(m, (int(cw[0] * 4), int(cw[1] * 4)), int(13 * kk * 4), 255, -1, cv2.LINE_AA, shift=2)
        cv2.circle(m, (int(centre[0] * 4), int(centre[1] * 4)), int(9 * kk * 4), 255, -1, cv2.LINE_AA, shift=2)
        P.over(name + ".seconds", np.array([150, 34, 20], np.float32), m.astype(np.float32) / 255,
               {"made": "HANDMADE seconds hand", "set_to_deg": ss * 6})
    return centre


def door_key(P, k, x0, y0, swing=0.34, key_deg=1.5, tag_deg=12.0):
    """bp.lay_door_key with the key's hang angle and the tag's angle free (a swinging tag)."""
    Wm = bp.W2P(k, x0, y0)
    dh, dw = bp.DOOR.shape
    jx, jy = bp.DOOR_BOX[0], bp.DOOR_BOX[1]
    jt, jb = apply(Wm, (jx, jy)), apply(Wm, (jx, jy + dh))
    ow = dw * k * swing
    grow = dh * k * 0.05
    src = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
    dst = np.float32([[jt[0] - ow, jt[1] - grow], jt, jb, [jb[0] - ow, jb[1] + grow]])
    Md = cv2.getPerspectiveTransform(src, dst).astype(np.float64)
    P.piece("cupboard.door", bp.DOOR[:, ::-1].copy(), np.full(bp.DOOR.shape, 255, np.uint8), Md, margin=8, shade=0.78,
            meta={"piece": "cupboard.door", "swing_scaleX": swing})
    hp = apply(Md, (dw * 0.52, dh * 0.40))
    s = k / 0.8
    shp = P.c.shape[:2]
    hm = np.zeros(shp, np.uint8)
    cv2.rectangle(hm, (int(hp[0] - 6 * s), int(hp[1] - 22 * s)), (int(hp[0] + 6 * s), int(hp[1] - 4 * s)), 255, -1, cv2.LINE_AA)
    cv2.ellipse(hm, (int(hp[0]), int(hp[1] + 4 * s)), (int(11 * s), int(12 * s)), 0, 0, 200, 255, max(2, int(6 * s)), cv2.LINE_AA)
    P.paper("hook.paper", bp.scissor(hm, 5), bp.PAPER_CUT)
    P.ink("hook", hm)
    kp = bp.PC["key"]
    ring = kp["piv"]["ring_top"]
    ks = 0.41 * k * 0.92
    Mk = T(hp[0], hp[1] + 8 * s) @ R(key_deg) @ S(ks) @ T(-ring[0], -ring[1])
    ringc = apply(Mk, (ring[0] + 20, ring[1] + 60))
    # the tag hangs from the ring on its thread; tag_deg swings the thread about the ring
    rest = apply(Mk, (ring[0] + 190, ring[1] + 420)) - ringc
    a = math.radians(tag_deg - 12.0)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    tagc = ringc + rot @ rest
    tw, th = 168 * s, 58 * s
    tm = bp.fillmask(shp, bp.rect_poly(tagc, tw, th, tag_deg, notch=10 * s))
    P.paper("tag", tm, (236, 232, 220))
    thread = np.zeros(shp, np.uint8)
    ta = math.radians(tag_deg)
    off = np.array([-tw / 2 + 16 * s, -th / 2 + 10 * s])
    corner = tagc + np.array([off[0] * math.cos(ta) - off[1] * math.sin(ta), off[0] * math.sin(ta) + off[1] * math.cos(ta)])
    bp.brush_line(thread, [ringc, corner], max(2, 3 * s), 5, tremor=0.4)
    thread = bp.lettering_onto(thread, ["SERVICE"], 22 * s, tagc + rot @ np.array([4 * s, 2 * s]), -tag_deg, 7, weight=0.15)
    P.ink("tag.ink", thread)
    P.piece("key", kp["g"], kp["a"], Mk, margin=6, meta={"piece": "key", "hook_px": list(hp)})
    return dict(hook=hp, tag=tagc, jamb_top=jt, jamb_bottom=jb, door_free_x=float(jt[0] - ow))


def clerk(P, Mc, pose, order=("clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil")):
    rec = {}
    Ms = bp.lay_clerk(P, Mc, pose, order=order, rec=rec)
    r = rec[P.key]
    r["mouth_px"] = list(apply(Ms["clerk.head"], (2992, 2018)))
    r["head_top_px"] = list(apply(Ms["clerk.head"], (2990, 1560)))
    return r
