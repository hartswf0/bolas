"""99 ways, page 10 "One room, one picture" (photo-cutout).
The whole incident in ONE picture: the Rothstein 1937 Randolph office (the clerk-removed set plate of 99-ways-template,
FORAGED, PD) mounted as a single photographic print on the LoC 1934 sheet, with the agent cut out and laid FIVE times
along his path (desk -> ticket window -> under the clock -> open cupboard), the stranger (Bubley 1943, PD) behind the
glass, the clock (Rothstein 1937, PD) set to 4:10, the key (ANRC 1922, PD) on its hook. A dotted pencil track joins his
appearances. The four canon lines are cut-paper balloons pasted over the print's edges in reading order.
Reuses the 99-ways-template rig (page/build_page.py: FK clerk, door/key, memo slip, sign card, balloons).
Run: python3 -I p10_one_room.py"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
sys.path.insert(0, str(pen99.TPL / "page"))
import build_page as bp  # noqa: E402  (99-ways-template rig; importing only loads pieces)

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
T, S, R, about, apply = bp.T, bp.S, bp.R, bp.about, bp.apply

# the print: plate 4360x3100 -> photo area
PX0, PY0 = 134, 720
K = 1932 / 4360.0
PW, PH = 1932, int(round(3100 * K))
BORDER = 24

BUBLEY = cv2.imread(str(ROOT / "films/sources/99-ways-template/cutout-surgeon/pieces/bubley.visitor.png"), cv2.IMREAD_UNCHANGED)
GLASS = (110, 810, 1230, 1850)          # ticket-window glass, plate px (checked on the plate)
CLOCK_AT = (2790, 560)                  # clock arbor on the wall, plate px
CLOCK_K = 1.0
COUNTER_Y = 1905
STRANGER_AT, STRANGER_S = (470, 930), 2.25
STRANGER_MOUTH = (470 + 2.25 * (97 - 101.5), 930 + 2.25 * 45)      # plate px, from the Bubley piece (mouth ~ (97, 45))
DESK_POLY = [(1430, 2790), (4360, 2560), (4360, 3100), (1430, 3100)]   # desk top, back edge in perspective

# agent appearances: (event, root plate px, plate scale, mirrored (faces left), pose)
SC = 0.60            # standing figures: plate scale
# standing roots: the shirt's bottom edge (src y 2786) lies just below the counter top, the fist rests on it
ROOT_L = 1945 - (2786 - 2680) * SC          # left counter run (top ~1915)
ROOT_R = 2005 - (2786 - 2680) * SC          # right counter run (top ~1975)
APPEAR = [
    ("E0", (2300, 2930), 0.80, True, dict(bp.POSE_ARRIVE, head=2.0)),
    # E1: mirrored, so he turns toward the glass on his left; head turned to the pane, forearm lowered toward it
    ("E1", (1100, ROOT_L), SC, True, dict(arm=-44.0, pencil=18.0, head=16.0)),
    # E2: head tipped right back on the collar hinge toward the clock (upper right), pencil at his temple as photographed
    ("E2", (2300, ROOT_L), SC, False, dict(bp.POSE_SOURCE, head=-14.0)),
    # E4-E5: in front of the open cupboard, right of the swung leaf, turned (mirrored) to the key on the leaf's inner
    # face, pencil at his chin (FK solve)
    ("E4-E5", (3620, ROOT_R), SC, True, bp.POSE_CHIN),
]
# the torso piece's own left forearm and fist (source px): kept in front of the counter top (he leans on it), so the
# counter covers only the shirt between his arms; no straight occlusion edge then runs the full width of the figure
FIST_SRC = [(2090, 2150), (2400, 2150), (2400, 2900), (2090, 2900)]


POSES = {e: pose for (e, _, _, _, pose) in APPEAR}


def counter_top(x_plate):
    """plate y of the counter's top edge (read off the set plate: left run ~1915, right run ~1975)"""
    return 1915.0 if x_plate < 2550 else 1975.0


def P2(p):
    """plate px -> page px"""
    return (PX0 + p[0] * K, PY0 + p[1] * K)


def Mplate():
    return T(PX0, PY0) @ S(K)


def clerk_M(root, s, mir):
    M = Mplate() @ T(root[0], root[1]) @ S(s) @ T(-bp.CX, -bp.ROOT_[1])
    if mir:
        M = M @ bp.MIR()
    return M


def mouth_of(M, pose):
    return apply(M @ about(bp.COLLAR, R(pose.get("head", 0.0))), (2992, 2018))


def stranger(P, at, s, alpha_mul=1.0):
    """Bubley 1943 figure behind the ticket-window glass, clipped to the glass, glass tone laid back over her."""
    g = BUBLEY[..., 0].astype(np.float32)
    a = BUBLEY[..., 3].copy()
    a[BUBLEY.shape[0] * 55 // 100:] = 0          # below the sill line: hidden by the counter
    M = Mplate() @ T(at[0], at[1]) @ S(s) @ T(-BUBLEY.shape[1] / 2, 0)
    h, w = P.c.shape[:2]
    gw = cv2.warpPerspective(g, M, (w, h), flags=cv2.INTER_CUBIC)
    aw = cv2.warpPerspective(a, M, (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
    clip = np.zeros((h, w), np.float32)
    x0, y0 = P2(GLASS[:2])
    x1, y1 = P2(GLASS[2:])
    clip[int(y0):int(y1), int(x0):int(x1)] = 1
    aw *= clip * alpha_mul
    before = P.c.copy()
    P.over("stranger", np.repeat(np.clip(gw * 0.92, 0, 255)[..., None], 3, 2), aw)
    # the glass in front of her: 30% of the pane's own tone back over the figure (no filter: the plate's pixels)
    P.over("stranger.glass", before, aw * 0.30)
    return M


def clock(P):
    cc = bp.PC["clock.case"]
    arb = cc["piv"]["arbor"]
    Mc = Mplate() @ T(*CLOCK_AT) @ S(CLOCK_K) @ T(-arb[0], -arb[1])
    P.piece("clock.case", cc["g"], cc["a"], Mc @ T(*cc["o"]), margin=6)
    h, w = P.c.shape[:2]
    for n, ang in [("clock.hour", 4 * 30 + 10 * 0.5), ("clock.minute", 10 * 6)]:
        pc = bp.PC[n]
        rot = ang - bp.man["pieces"][n]["source_angle_deg"]
        Mh = Mc @ about(arb, R(rot)) @ T(*pc["o"])
        hg = cv2.warpAffine(pc["g"], Mh[:2], (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(pc["a"], Mh[:2], (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        P.over(n, np.repeat(hg[..., None], 3, 2), ha)


def catmull(pts, n=24):
    p = np.array(pts, np.float64)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(p[-2])
    return np.array(out)


TRACK = [[(1950, 2470), (1600, 2290), (1250, 2130)],                     # desk -> window
         [(1330, 2115), (1700, 2130), (2080, 2115)],                     # window -> clock
         [(2520, 2115), (2900, 2140), (3230, 2125)]]                     # clock -> cupboard


def track(P, upto, seed=5):
    """dotted pencil track on the print, with an arrowhead at the end of each leg"""
    m = np.zeros(P.c.shape[:2], np.uint8)
    for leg in TRACK[:upto]:
        c = catmull([P2(p) for p in leg])
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        for s in np.arange(10, d[-1] - 30, 26):
            i = np.searchsorted(d, s)
            cv2.circle(m, (int(c[i][0] * 4), int(c[i][1] * 4)), 22, 255, -1, cv2.LINE_AA, shift=2)
        tip, back = c[-1], c[-4]
        v = (tip - back) / (np.linalg.norm(tip - back) + 1e-6)
        nrm = np.array([-v[1], v[0]])
        for sgn in (1, -1):
            bp.brush_line(m, [tip - v * 34 + nrm * 20 * sgn, tip], 7, seed + sgn, tremor=0.3)
    P.ink("track.halo", cv2.dilate(m, np.ones((7, 7), np.uint8)), np.array([25, 24, 22], np.float32))
    P.ink("track", m, np.array([244, 240, 228], np.float32))


def photo_corners(P):
    x0, y0, x1, y1 = PX0 - BORDER, PY0 - BORDER, PX0 + PW + BORDER, PY0 + PH + BORDER
    sz = 92
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        pts = [(cx - 14 * sx, cy - 14 * sy), (cx + sz * sx, cy - 14 * sy), (cx - 14 * sx, cy + sz * sy)]
        m = bp.fillmask(P.c.shape[:2], pts)
        P.paper("corner", m, (30, 29, 28))


CUT = {}


def build(stage=99):
    """stage: 0 empty room, 1 +E0, 2 +E1, 3 +E2, 4 +E3, 5 cupboard open, 6 +E4-E5 (= page)"""
    pg = pen99.sheet99().astype(np.float32)
    P = bp.Panel("P10", pg)
    plate = bp.SETP if stage >= 5 else bp.OFFICE
    view = bp.view_plate(plate, K, 0, 0, PW, PH)
    pm = np.zeros((H, W), np.uint8)
    pm[PY0 - BORDER:PY0 + PH + BORDER, PX0 - BORDER:PX0 + PW + BORDER] = 255
    P.paper("print", pm, (244, 242, 236))
    P.c[PY0:PY0 + PH, PX0:PX0 + PW] = view
    # fixed furniture of the one room
    clock(P)
    Mp = Mplate()
    bp.sign_card(P, apply(Mp, (4040, 800)), 330 * K * 1.15, -2)
    if stage >= 5:
        bp.lay_door_key(P, K, -PX0 / K, -PY0 / K, swing=0.34)
    speech = {}
    # the stranger: at the glass for E1-E2, turned away and further along for E3
    if stage >= 2:
        stranger(P, (470, 930), 2.25)
    figs = {}
    full = P.c.copy()
    full[PY0:PY0 + PH, PX0:PX0 + PW] = view

    def relay(name, x0, y0, x1, y1, poly=None):
        m = np.zeros((H, W), np.float32)
        if poly is None:
            m[int(PY0 + y0 * K):int(PY0 + y1 * K), int(PX0 + x0 * K):int(PX0 + x1 * K)] = 1
        else:
            m = bp.fillmask((H, W), [P2(q) for q in poly]).astype(np.float32) / 255
        P.over(name, full, m)

    figm = {}

    def lay(ev):
        for (e, root, s_, mir, pose) in APPEAR:
            if e == ev:
                M = clerk_M(root, s_, mir)
                before = P.c.copy()
                bp.lay_clerk(P, M, pose)
                figm[ev] = (np.abs(P.c - before).max(2) > 1.0, M)
                figs[ev] = mouth_of(M, pose)
    need = {"E0": 1, "E1": 2, "E2": 3, "E4-E5": 6}
    standing = [e for e in ("E1", "E2", "E4-E5") if stage >= need[e]]
    yy, xx = np.mgrid[0:H, 0:W]
    below = (yy - PY0) / K > np.where((xx - PX0) / K < 2550, 1915.0, 1975.0)

    def occlude(ev, occ_mask, name):
        fig, M = figm[ev]
        fist = bp.fillmask((H, W), [apply(M, q) for q in FIST_SRC]) > 0
        Mf = bp.clerk_mats(M, POSES[ev])["clerk.forearm"]      # the pencil forearm lies in front of the counter too
        fx0, fy0, fx1, fy1 = bp.man["pieces"]["clerk.forearm"]["bbox_src"]
        fist |= bp.fillmask((H, W), [apply(Mf, q) for q in ((fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1))]) > 0
        m = fig & occ_mask & ~fist
        P.over(name, full, m.astype(np.float32))
        vis = fig & ~m
        # longest straight horizontal run of the occlusion edge on this figure (3-row band, page px)
        cut = np.zeros((H, W), bool)
        cut[:-1] = vis[:-1] & m[1:]
        band = cut[:-2] | cut[1:-1] | cut[2:]
        best = 0
        for row in band[np.any(band, axis=1)]:
            r = np.r_[0, row.astype(np.int8), 0]
            d = np.diff(r)
            st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
            if len(st):
                best = max(best, int((en - st).max()))
        CUT[ev] = best
    for e in standing:
        lay(e)
        occlude(e, below, "counter." + e)
    track(P, {0: 0, 1: 0, 2: 1, 3: 2, 4: 2, 5: 2}.get(stage, 3))
    if stage >= 1:
        lay("E0")
        occlude("E0", bp.fillmask((H, W), [P2(q) for q in DESK_POLY]) > 0, "desk.front")   # E0 sits behind the desk
        bp.memo_slip(P, apply(Mp, (2330, 2830)), 210, 4)
    # balloons, pasted over the print's edges; reading order: top band Q, A; bottom band T, F
    sm = P2(STRANGER_MOUTH)
    q_tip, t_tip = (sm[0] + 30, sm[1]), (sm[0] - 30, sm[1] + 2)   # her mouth corners, outside the cheeks
    if stage >= 2:
        speech["E1"] = bp.balloon(P, "q", ["Pardon me —", "have you the", "right time?"], 58, (720, 560), q_tip, 21, tail_w=0.20, bend=0.0)
    if stage >= 3:
        speech["E2"] = bp.balloon(P, "a", ["Ten past four,", "by the clock."], 58, (1520, 520), (figs["E2"][0] + 62, figs["E2"][1]), 33, tail_w=0.20, bend=0.0)
    if stage >= 4:
        speech["E3"] = bp.balloon(P, "t", ["Much", "obliged!"], 62, (250, 1720), t_tip, 61, tail_w=0.22, bend=0.0)
    if stage >= 6:
        speech["E5"] = bp.balloon(P, "f", ["Well, here I am...", "and what for?"], 58, (1700, 2230), (figs["E4-E5"][0] + 64, figs["E4-E5"][1] + 4), 83, tail_w=0.18, bend=0.0)
    photo_corners(P)
    cap = np.zeros((H, W), np.uint8)
    pen99.penlib.ink_onto  # noqa
    m = pen99.letter(["Randolph station, the office: one afternoon, one picture."], 40, 1010)
    y = 2470
    cap[y:y + m.shape[0], (W - m.shape[1]) // 2:(W - m.shape[1]) // 2 + m.shape[1]] = m
    if stage >= 99 or stage >= 6:
        P.ink("caption", cap)
    out = P.c.copy()
    pen99.folio(out, 10, "One room, one picture")
    return np.clip(np.round(out), 0, 255).astype(np.uint8), speech


def main():
    from b1m2 import credit_pages
    out_jpg = ROOT / "assets/pages/99-ways/10-one-room-one-picture.jpg"
    out_png = ROOT / "films/sources/99-ways/masters/10-one-room-one-picture.png"
    beats = ROOT / "films/sources/99-ways/beats/10"
    beats.mkdir(parents=True, exist_ok=True)
    page, speech = build(99)
    cut_page = dict(CUT)
    Image.fromarray(page).save(out_png, compress_level=6)
    Image.fromarray(page).save(out_jpg, quality=90, dpi=(300, 300))
    size = out_jpg.stat().st_size
    desc = ["b01: the empty office on the print (cupboard shut, clock at 4:10, SERVICE card)",
            "b02: + the agent at the desk with the memo (E0)",
            "b03: + the agent at the ticket window, the stranger behind the glass, her question; first leg of the track (E1)",
            "b04: + the agent under the clock, his answer; second leg (E2)",
            "b05: + her thanks (E3)",
            "b06: the cupboard opened, the key on its hook; third leg (E4)",
            "b07: + the agent at the open cupboard, pencil to chin, the forgetting line (E5) = the page"]
    for j, st in enumerate([0, 1, 2, 3, 4, 5, 6], 1):
        im = page if st == 6 else build(st)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(beats / f"b{j:02d}.png")
    tpl = {e.get("title"): e for e in json.load(open(ROOT / "films/credits/99-ways-template.json"))}
    bub = dict(tpl["Cincinnati (vicinity), Ohio. The ticket agent at a small town station (1943 Sept.)"])
    bub.update(id="99-ways-template:bubley-stranger-1943", carried_from="films/credits/99-ways-template.json",
               used_as_99_ways="the stranger (cutout-surgeon/pieces/bubley.visitor.png) behind the ticket-window glass")
    src = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
           "99-ways-template:anrc-gold-key-1922", "99-ways-template:bubley-stranger-1943",
           "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, 10, new_entries=[bub])
    rec = {
        "n": 10, "id": "one-room-one-picture", "title": "One room, one picture", "family": "layout and page grammar",
        "medium": "photo-cutout", "canon_revision": "c1",
        "rule": "The whole incident in a single panel: the agent appears several times along his path through one continuous office.",
        "declares": "keeps E0-E5, the four lines and the outcome",
        "file": str(out_jpg.relative_to(ROOT)), "master": str(out_png.relative_to(ROOT)),
        "beats_dir": str(beats.relative_to(ROOT)), "build": "films/swarm/99-ways/build/p10_one_room.py",
        "sources": src,
        "made": [
            "one print: the 99-ways-template clerk-removed Rothstein set plate (editor/set.plate.r1.png, cupboard opened) whole, "
            "mounted with a white print border and four black paper photo corners on the LoC 1934 sheet",
            "the agent laid four times with the 99-ways-template FK rig (build_page.lay_clerk), each with its own pose: seated behind "
            "the desk with the memo (E0); at the ticket window, mirrored to turn toward the glass, head turned to the pane, forearm "
            "lowered (E1); under the clock, head tipped back on the collar hinge toward it, pencil at his temple (E2); in the open "
            "cupboard right of the swung leaf, mirrored to face the key on the leaf, pencil at his chin by the FK solve (E4-E5)",
            "occlusion by real plate objects only: each standing figure is laid so his shirt's lower edge falls just below the "
            "counter top and the plate's counter is re-laid over that strip only within the figure's own footprint (no "
            "rectangle, so the open leaf is untouched); his own left forearm and fist and his pencil forearm stay in front, "
            "resting on the counter, so the counter edge never runs across a whole figure; E0 is occluded the same way by the desk",
            "the Bubley 1943 figure behind the glass (clipped to the pane, 30% of the pane's own pixels laid back over her): "
            "at the glass for both her lines",
            "the Rothstein clock case and its own hands re-set to 4:10; the cupboard door on its jamb with hook, ANRC key and SERVICE tag "
            "(build_page.lay_door_key); the SERVICE card on the closed right-hand door",
            "a dotted pencil track with arrowheads joining his appearances (handmade)",
            "four cut-paper balloons lettered with the canon lines in the shared pen hand, pasted over the print's top and bottom edges "
            "in reading order; caption and folio in the pen hand"],
        "events": {"E0": "agent behind the desk, memo slip on it (centre foreground)",
                   "E1": "agent at the ticket window, turned toward the glass; stranger behind it; question balloon (top left) tailed from the upper right to her mouth's right corner",
                   "E2": "agent under the wall clock (4:10), head tipped back toward it, pencil at his temple; answer balloon (top centre) tailed to his mouth's right",
                   "E3": "thanks balloon (left, below) tailed from below-left to her mouth's left corner; her face left clear",
                   "E4": "cupboard open, key on its hook with its SERVICE tag",
                   "E5": "agent before the open cupboard, pencil to chin, forgetting balloon (bottom right); SERVICE door shut"},
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "beat": "on one unchanging print the agent is laid down again and again along a dotted track: desk, window, clock, "
                "then the cupboard is opened and he stands before it",
        "beat_frames": desc,
        "self_check": {"size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000, "panels": 1, "agent_appearances": 4,
                       "balloon_cap_px": 58,
                       "longest_horizontal_occlusion_edge_px_per_figure": cut_page,
                       "occlusion": "counter/desk re-laid only inside each figure's footprint; fist and pencil forearm kept in front",
                       "check": "A reader finds the agent more than once in one frame and orders his appearances E0 to E5 "
                                "(maker's judgement from the full-size page; blind reading pending)",
                       "evidence": "measured (size, bytes, appearance count) and perceptually judged (from frames) by the maker"},
        "weaknesses": ["the agent source is one frontal, downcast Rothstein photograph: the FK rig can mirror, turn the head in the picture plane and move the pencil forearm, but cannot give a true profile (E1) or raise his eyes (E2: the head tips back, the eyelids stay down)", "the three standing appearances still share one torso cut-out, scaled alike behind the same counter"],
    }
    json.dump(rec, open(ROOT / "films/swarm/99-ways/pages/10.json", "w"), indent=1, ensure_ascii=False)
    print(size)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        Image.fromarray(build(int(sys.argv[1]))[0]).save(sys.argv[2])
    else:
        main()
