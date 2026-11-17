"""Panels P6, P7, P8 of the Template photo-comic page, built from the cut pieces, with the FK rig
(SCION #32): torso -> collar -> head; torso -> elbow -> forearm+fist+pencil; set -> jamb -> door;
set -> hook -> key -> tag. Rest poses here ARE the page; the film only animates toward them.
Run: python3 -I panels.py   (writes test-page.png + fk_test.json)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa

man = json.load(open(PIECES / "manifest.json"))


def load(name):
    im = cv2.imread(str(PIECES / f"{name}.png"), cv2.IMREAD_UNCHANGED)
    return im[..., 0].astype(np.float32), im[..., 3].copy()


PC = {n: load(n) for n in ["clerk.torso", "clerk.head", "clerk.forearm_pencil", "cupboard.door", "key"]}
PIV = {n: man["pieces"][n]["pivots_local"] for n in PC}
PLATE = cv2.imread(str(PIECES / "set.plate.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
PX0, PY0 = man["set_plate"]["bbox_src"][:2]
WIN = cv2.imread(str(PIECES / "window.plate.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
DOOR_BOX = man["set_plate"]["opening_src"]

HOOK_SRC = (1630.0, 725.0)      # hook on the cupboard's inner right wall, source (roth_H) coords
KEY_PER_H = 0.205               # key plate px -> roth_H px (a ~15 cm door key against the clerk's scale)

# poses: arm angle about the elbow (deg, + lowers the fist across his front), head roll about the collar
REST = dict(arm=0.0, head=-11.0, squash=0.955, scratch=0.0)     # P8 on the page
ARRIVE = dict(arm=45.0, head=0.0, squash=1.0, scratch=0.0)      # P7 and the first frame of P8

BALLOONS = {}


def balloons():
    if not BALLOONS:
        BALLOONS["thanks"] = balloon_piece(["Thanks!"], 70, (-390, 70), 61)
        BALLOONS["forgot"] = balloon_piece(["What the hell", "was I looking", "for, anyway?"], 68, (255, 250), 83)
        BALLOONS["tag"] = letter_lines(["SERVICE"], 22, 7, weight=0.14)
    return BALLOONS


def gray3(g):
    return np.repeat(g[..., None], 3, 2)


def set_base(w, h, k, x0, y0):
    """The set (cupboard wall, open interior) at k page-px per roth_H px, H origin (x0, y0)."""
    M = (S(k) @ T(-(x0 - PX0), -(y0 - PY0)))[:2]
    return gray3(cv2.warpAffine(PLATE, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE))


def H2P(k, x0, y0):
    return S(k) @ T(-x0, -y0)


def lay_set_pieces(c, k, x0, y0, log=None):
    W = H2P(k, x0, y0)
    # door: hinged on its left jamb, swung ~70 deg toward us; we see its inner face (mirrored), in shade
    g, a = PC["cupboard.door"]
    dh, dw = g.shape
    jx, jy0 = DOOR_BOX[0], DOOR_BOX[1]
    jt, jb = apply(W, (jx, jy0)), apply(W, (jx, jy0 + dh))
    ow = dw * k * 0.34
    grow = dh * k * 0.055
    src = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
    dst = np.float32([[jt[0] - ow, jt[1] - grow], jt, jb, [jb[0] - ow, jb[1] + grow]])
    Md = cv2.getPerspectiveTransform(src, dst)
    place(c, g[:, ::-1].copy(), a, Md, margin=8, shade=0.80)
    # handmade hook: black card J-hook with its own scissor margin
    hp = apply(W, HOOK_SRC)
    hm = np.zeros(c.shape[:2], np.uint8)
    s = k / 1.6
    cv2.rectangle(hm, (int(hp[0] - 6 * s), int(hp[1] - 20 * s)), (int(hp[0] + 6 * s), int(hp[1] - 4 * s)), 255, -1, cv2.LINE_AA)
    cv2.ellipse(hm, (int(hp[0]), int(hp[1] + 4 * s)), (int(11 * s), int(12 * s)), 0, 0, 200, 255, max(2, int(6 * s)), cv2.LINE_AA)
    pm = scissor(hm, 5)
    shadow_onto(c, pm)
    c[:] = c * (1 - pm[..., None] / 255.0) + PAPER_CUT * (pm[..., None] / 255.0)
    ink_onto(c, hm)
    # the key hangs from its ring on the hook (hook -> key: constant offset, no motion in E5)
    kg, ka = PC["key"]
    ring = PIV["key"]["ring_top"]
    ks = KEY_PER_H * k
    Mk = T(hp[0], hp[1] + 8 * s) @ R(1.5) @ S(ks) @ T(-ring[0], -ring[1])
    # paper tag on a thread from the ring, lettered SERVICE (handmade)
    tagc = apply(Mk, (ring[0] - 190, ring[1] + 400))
    ringc = apply(Mk, (ring[0] - 20, ring[1] + 60))
    tw, th = 168 * s, 58 * s
    tm = np.zeros(c.shape[:2], np.uint8)
    poly = np.array([(-tw / 2, -th / 2 + 10 * s), (-tw / 2 + 10 * s, -th / 2), (tw / 2, -th / 2), (tw / 2, th / 2), (-tw / 2, th / 2)])
    ang = math.radians(-12)
    rot = np.stack([poly[:, 0] * math.cos(ang) - poly[:, 1] * math.sin(ang), poly[:, 0] * math.sin(ang) + poly[:, 1] * math.cos(ang)], 1)
    cv2.fillPoly(tm, [np.int32((rot + tagc) * 4)], 255, cv2.LINE_AA, shift=2)
    shadow_onto(c, tm)
    c[:] = c * (1 - tm[..., None] / 255.0) + np.array([236, 232, 220], np.float32) * (tm[..., None] / 255.0)
    thread = np.zeros(c.shape[:2], np.uint8)
    hole = tagc + np.array([-tw / 2 + 14 * s, -th / 2 + 12 * s])
    brush_line(thread, [ringc, hole], max(2, 3 * s), 5, tremor=0.4)
    lt = balloons()["tag"]
    lt = cv2.resize(lt, (int(lt.shape[1] * s * 0.95), int(lt.shape[0] * s * 0.95)))
    Ml = cv2.getRotationMatrix2D((lt.shape[1] / 2, lt.shape[0] / 2), 12, 1.0)
    Ml[:, 2] += tagc - np.array([lt.shape[1] / 2, lt.shape[0] / 2]) + np.array([6 * s, 2 * s])
    ltw = cv2.warpAffine(lt, Ml, (c.shape[1], c.shape[0]))
    ink_onto(c, np.maximum(thread, ltw))
    place(c, kg, ka, Mk, margin=6)
    if log is not None:
        log["key_hook_offset"] = [float(v) for v in (apply(Mk, ring) - hp)]


def clerk_matrices(O, kc, pose):
    """FK chain. Returns world matrices for torso, head, forearm."""
    Mt = T(*O) @ S(kc)
    col = PIV["clerk.head"]["collar"]
    elb = PIV["clerk.forearm_pencil"]["elbow"]
    Mh = Mt @ about(col, R(pose["head"]) @ S(1.0, pose["squash"]))
    Mf = Mt @ about(elb, R(pose["arm"] + pose.get("scratch", 0.0)))
    return Mt, Mh, Mf


def lay_clerk(c, O, kc, pose, log=None):
    Mt, Mh, Mf = clerk_matrices(O, kc, pose)
    for name, M in [("clerk.torso", Mt), ("clerk.head", Mh), ("clerk.forearm_pencil", Mf)]:
        g, a = PC[name]
        place(c, g, a, M, margin=8)
    if log is not None:
        col = PIV["clerk.head"]["collar"]
        elb = PIV["clerk.forearm_pencil"]["elbow"]
        log.append({"pose": pose,
                    "collar_drift_px": float(np.linalg.norm(apply(Mh, col) - apply(Mt, PIV["clerk.torso"]["collar"]))),
                    "elbow_drift_px": float(np.linalg.norm(apply(Mf, elb) - apply(Mt, PIV["clerk.torso"]["elbow"])))})


P8_SET = (1.6, 1380, 300)
P8_CLERK = ((900 - 399 * 1.3, 1025 - 572 * 1.3), 1.3)
P7_SET = (1.33, 1300, 250)
P7_CLERK = ((800 - 399 * 1.0, 1020 - 572 * 1.0), 1.0)
P8_BALLOON_AT = (560, 205)
P6_BALLOON_AT = (360, 170)


def panel_P8(pose=REST, balloon=True, dy=0.0, lift=0.0, log=None, fklog=None):
    x0, y0, x1, y1 = PANELS["P8"]
    w, h = x1 - x0, y1 - y0
    c = set_base(w, h, *P8_SET)
    lay_set_pieces(c, *P8_SET, log=log)
    lay_clerk(c, P8_CLERK[0], P8_CLERK[1], pose, fklog)
    if balloon:
        lay_balloon(c, balloons()["forgot"], P8_BALLOON_AT, dy, lift)
    return c


def panel_P7():
    x0, y0, x1, y1 = PANELS["P7"]
    w, h = x1 - x0, y1 - y0
    c = set_base(w, h, *P7_SET)
    lay_set_pieces(c, *P7_SET)
    lay_clerk(c, P7_CLERK[0], P7_CLERK[1], ARRIVE)
    return c


def panel_P6(balloon=True, dy=0.0, lift=0.0):
    x0, y0, x1, y1 = PANELS["P6"]
    w, h = x1 - x0, y1 - y0
    c = gray3(cv2.resize(WIN, (w, h), interpolation=cv2.INTER_CUBIC))
    if balloon:
        lay_balloon(c, balloons()["thanks"], P6_BALLOON_AT, dy, lift)
    return c


BORDER = None


def border():
    global BORDER
    if BORDER is None:
        BORDER = border_mask((PAGE_H, PAGE_W), [PANELS[k] for k in ["P4", "P5", "P6", "P7", "P8"]], 9, 900)
    return BORDER


def page_base():
    pg = sheet()
    # pencil placeholders for panels this unit does not build (P4, P5 belong to the page unit)
    for k in ["P4", "P5"]:
        x0, y0, x1, y1 = PANELS[k]
        lm = letter_lines([k], 40, 3, weight=0.08)
        ink_onto(pg[y0 + 30:y0 + 30 + lm.shape[0], x0 + 30:x0 + 30 + lm.shape[1]], lm, np.array([140, 138, 134], np.float32), 0.6)
    return pg


def put_panel(pg, key, c):
    x0, y0, x1, y1 = PANELS[key]
    pg[y0:y1, x0:x1] = c
    return pg


def finish(pg, region=None):
    b = border()
    if region is None:
        ink_onto(pg, b)
    else:
        x0, y0, x1, y1 = region
        ink_onto(pg[y0:y1, x0:x1], b[y0:y1, x0:x1])
    return pg


def rest_page():
    pg = page_base()
    put_panel(pg, "P6", panel_P6())
    put_panel(pg, "P7", panel_P7())
    log, fk = {}, []
    put_panel(pg, "P8", panel_P8(REST, log=log, fklog=fk))
    finish(pg)
    return pg, log, fk


def tone_stats(a):
    L = a.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    return {"pct_L_gt_220": round(float((L > 220).mean() * 100), 1), "pct_L_lt_40": round(float((L < 40).mean() * 100), 1),
            "median": float(np.median(L))}


if __name__ == "__main__":
    pg, log, fk = rest_page()
    crop = pg[1110:PAGE_H].clip(0, 255).astype(np.uint8)
    Image.fromarray(crop).save(SWARM / "test-page.png", dpi=(300, 300))
    st = {"test_page": tone_stats(crop), "panels_P6_P7_P8_only": tone_stats(np.concatenate(
        [pg[PANELS[k][1]:PANELS[k][3], PANELS[k][0]:PANELS[k][2]].reshape(-1, 3) for k in ["P6", "P7", "P8"]]))}
    # FK invariants over the whole E5 pose set
    fk_all = []
    for pose in [ARRIVE, dict(arm=50, head=0, squash=1), dict(arm=28, head=0, squash=1), dict(arm=10, head=0, squash=1),
                 dict(arm=-3, head=0, squash=1), dict(arm=0, head=-4, squash=.985), dict(arm=0, head=-8, squash=.97), REST]:
        lay_clerk(np.zeros((10, 10, 3), np.float32), P8_CLERK[0], P8_CLERK[1], pose, fk_all)
    json.dump({"tone": st, "key_hook": log, "fk": fk_all,
               "max_collar_drift_px": max(f["collar_drift_px"] for f in fk_all),
               "max_elbow_drift_px": max(f["elbow_drift_px"] for f in fk_all)}, open(BUILD / "fk_test.json", "w"), indent=1)
    print(st, max(f["collar_drift_px"] for f in fk_all))
