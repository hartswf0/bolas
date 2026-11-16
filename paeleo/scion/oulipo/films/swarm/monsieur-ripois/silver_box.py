"""HANDMADE silver box (U2 full build; derived from the test-shot box.py with the review fixes:
crisp V-groove engraving rendered at high texture resolution and area-filtered (no moire), a tarnished, slightly wavy
mirror lid, specular highlights reaching paper white, and a receipt-in-slot state).
, built from its geometry (plan §7 box spec), not drawn as a picture.
Units of box width w=1: depth 0.62, body height 0.30, lid 0.08 hinged on the back top edge,
velvet insert with a pressed ring hollow centred at (0.50w, 0.45 depth), slit 0.18w x 0.025w.
Each face is made as a texture in its own (u,v) space (guilloche computed from concentric/wave geometry,
Lambert + specular from V0's key direction, environment = blurred plate crop), then projected by a
pinhole camera with cv2.warpPerspective. Returns float gray image + alpha."""
import numpy as np, cv2, math, json
SPEC = json.load(open(__file__.rsplit('/', 1)[0] + '/box-spec.json'))
W_, D_, H_, LID = 1.0, 0.62, 0.30, 0.08
SLOT = dict(cx=0.50, cy=0.45, len=0.18, wid=0.025)
WALL = SPEC['wall']
KEY = np.array([0.50, -0.62, 0.80]); KEY = KEY / np.linalg.norm(KEY)   # V0s real key: high camera-RIGHT, front (his head casts its shadow to the left on the wall)

def spec_json(path):
    json.dump({"units": "box width w", "w": W_, "depth": D_, "body_h": H_, "lid_h": LID, "hinge": "back top edge",
               "slot": SLOT, "wall": WALL, "key_dir": KEY.round(3).tolist()}, open(path, "w"), indent=1)

class Cam:
    def __init__(s, yaw, pitch, dist, f, cx, cy, target=(0.5, 0.31, 0.15)):
        s.f, s.cx, s.cy = f, cx, cy
        t = np.array(target, float)
        y, p = math.radians(yaw), math.radians(pitch)
        eye = t + dist * np.array([-math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)])
        fwd = (t - eye); fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        s.eye, s.R = eye, np.stack([right, -up, fwd])
    def P(s, X):
        c = s.R @ (np.asarray(X, float) - s.eye)
        return (s.cx + s.f * c[0] / c[2], s.cy + s.f * c[1] / c[2])
    def facing(s, centre, n):
        return np.dot(np.asarray(n), s.eye - np.asarray(centre)) > 0

def shade(n, base, spec_amt, uvx, uvy, cam_dir):
    n = np.asarray(n, float); n /= np.linalg.norm(n)
    lam = max(0.0, float(n @ KEY))
    h = KEY + cam_dir; h /= np.linalg.norm(h)
    sp = max(0.0, float(n @ h)) ** 30
    return 0.16 + 0.78 * lam * base, sp * spec_amt

def guilloche(tw, th, seed, freq=38):
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
    u = xx / tw - 0.5; v = (yy / th - 0.5) * th / tw
    r = np.sqrt(u * u + v * v); a = np.arctan2(v, u)
    g = np.sin(2 * np.pi * (r * freq + 0.18 * np.sin(a * 14 + r * 30)))          # engine-turned rose
    g2 = np.sin(2 * np.pi * (u * freq * 0.5 + 0.12 * np.sin(v * 90)))           # wave band
    # engine-turned cut: thin V-grooves (dark) between polished lands; a groove's two facets catch the key differently
    ph = (r * freq + 0.18 * np.sin(a * 14 + r * 30)) % 1.0
    ph2 = (u * freq * 0.5 + 0.12 * np.sin(v * 90)) % 1.0
    gro = np.clip(1 - np.abs(ph - 0.5) / 0.16, 0, 1) ** 1.5
    gro2 = np.clip(1 - np.abs(ph2 - 0.5) / 0.14, 0, 1) ** 1.5
    band = (np.abs(v) < 0.08 * th / tw * 4).astype(np.float32)
    pat = -np.maximum(gro * (1 - band), gro2 * band) + 0.35 * np.sign(ph - 0.5) * np.maximum(gro, gro2 * band)
    rng = np.random.default_rng(seed)
    wear = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), tw / 40)
    return pat, wear

def env_strip(env, tw, th, x0, y0, x1, y1, blur):
    """reflection: blurred crop of the room plate (fractional coords), flipped as a mirror would"""
    H, W = env.shape
    crop = env[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
    crop = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA)[::-1]
    return cv2.GaussianBlur(crop.astype(np.float32) / 255, (0, 0), blur)

def face_tex(kind, tw, th, n, cam, centre, env, seed):
    cam_dir = cam.eye - np.asarray(centre); cam_dir /= np.linalg.norm(cam_dir)
    dif, sp = shade(n, 1.0, 1.0, 0, 0, cam_dir)
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
    if kind == "metal":
        pat, wear = guilloche(tw, th, seed)
        e = env_strip(env, tw, th, 0.15, 0.25, 0.85, 0.85, 4)
        grad = 1 - 0.35 * (xx / tw) if n[0] >= 0 else 0.85 + 0.15 * (yy / th)       # falloff away from key
        val = (0.45 * dif * grad + 0.42 * e * (0.7 + 0.3 * dif)) * (1 + 0.32 * pat) + 0.05 * wear
        streak = np.exp(-((xx / tw - 0.62) ** 2) / 0.012)
        val += (sp * 0.9 + 0.35) * streak * (1 + 0.25 * pat)                        # key's specular streak, up to paper white
        # bevelled border: a bright edge on the key side, darker on the far side
        b = max(2, tw // 60)
        val[:b, :] += 0.35; val[-b:, :] *= 0.55; val[:, :b] += 0.2; val[:, -b:] *= 0.6
        return np.clip(val, 0, 1.2)
    if kind == "mirror":
        # an old silvered mirror: the room, slightly wavy glass, tarnish blooms, a wiped smudge, desilvering at the edge
        rng = np.random.default_rng(seed)
        H0, W0 = env.shape
        dx = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), tw / 14) * tw * 0.35
        dy = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), tw / 14) * tw * 0.35
        e = env_strip(env, tw, th, 0.05, 0.0, 0.95, 0.7, 2.2)
        e = cv2.remap(e, (xx + dx).astype(np.float32), (yy + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        tarn = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), tw / 25)
        tarn = np.clip(tarn / (tarn.std() + 1e-6), -2, 2)
        smudge = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), 1.5) * np.exp(-(((xx / tw - 0.3) / 0.18) ** 2 + ((yy / th - 0.6) / 0.25) ** 2))
        edge = np.minimum.reduce([xx / tw, 1 - xx / tw, yy / th, 1 - yy / th])
        desil = np.clip(1 - edge / 0.06, 0, 1) * (0.5 + 0.5 * np.clip(tarn, 0, 2))
        val = 0.07 + 0.85 * (e ** 1.6) * (0.6 + 0.4 * (1 - yy / th))
        val = val * (1 - 0.18 * np.clip(tarn, 0, 2)) + 0.05 * smudge + 0.10 * np.clip(-tarn, 0, 2) * val
        val = val * (1 - 0.6 * desil) + 0.10 * desil
        b = max(2, tw // 50); val[:b] += 0.4; val[:, :b] += 0.2; val[:, -b:] *= 0.5
        return val
    if kind == "inner":
        val = np.full((th, tw), 0.22 + 0.25 * dif, np.float32)
        val *= 0.6 + 0.4 * (yy / th)                                                 # darker toward the velvet
        return val
    if kind == "velvet":
        rng = np.random.default_rng(seed)
        fib = cv2.GaussianBlur(rng.normal(0, 1, (th, tw)).astype(np.float32), (0, 0), 0.7)
        u = xx / tw; v = yy / th                                                    # v: 0 = front, 1 = back
        edge = np.minimum.reduce([u, 1 - u, v, 1 - v])
        val = 0.15 + 0.04 * fib + 0.06 * np.clip(edge * 8, 0, 1) * dif               # pile sheen
        # pressed ring hollow (empty): a soft elliptical depression around the slit
        du = (u - SLOT["cx"]) / 0.16; dv = (v - SLOT["cy"]) / 0.20
        rr = np.sqrt(du * du + dv * dv)
        val -= 0.07 * np.exp(-(rr ** 2) * 3)
        val += 0.09 * np.exp(-((rr - 1.0) ** 2) * 30) * (dv > -0.3)                    # lit lip on the near side
        # the slit: a dark cut with a lit far lip (key from the front lights the back wall of the cut)
        su = np.abs(u - SLOT["cx"]) / (SLOT["len"] / 2); sv = (v - SLOT["cy"]) / (SLOT["wid"] / D_ / 2)
        inside = (su < 1) & (np.abs(sv) < 1)
        val[inside] = 0.02
        lip = (su < 1) & (sv > 1) & (sv < 2.4)
        val[lip] += 0.22
        return val
    if kind == "metal_flat":       # rim top
        val = np.full((th, tw), 0.5 + 0.5 * dif, np.float32) + sp * 0.6
        return val
    raise ValueError(kind)

def quad(cam, pts):
    return np.array([cam.P(p) for p in pts], np.float32)

def put(canvas, alpha, tex, dst, ss):
    th, tw = tex.shape
    src = np.array([[0, 0], [tw, 0], [tw, th], [0, th]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst * ss)
    H, W = canvas.shape
    t = cv2.warpPerspective(tex.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    m = cv2.warpPerspective(np.ones_like(tex, np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    poly = np.zeros_like(m); cv2.fillPoly(poly, [np.round(dst * ss).astype(np.int32)], 1.0)
    m = m * cv2.GaussianBlur(poly, (0, 0), 0.6)   # clip: a near-degenerate homography folds space outside the quad
    canvas[:] = canvas * (1 - m) + t * m
    alpha[:] = np.maximum(alpha, m)

def render(cam, size, lid_deg, env, ss=3, ring=False, seed=7, receipt=0.0):
    """lid_deg: 0 closed, ~105 open. returns (gray float 0..1, alpha float, shadow float) at `size`"""
    Wp, Hp = size
    C = np.zeros((Hp * ss, Wp * ss), np.float32); A = np.zeros_like(C)
    w, d, h, t = W_, D_, H_, WALL
    # lid geometry: rotate about hinge line (y=d, z=h) by lid_deg (opening toward the back)
    th_ = math.radians(lid_deg)
    def lidp(x, y, z):  # lid point in closed pose -> rotated
        dy, dz = y - d, z - h
        return (x, d + dy * math.cos(th_) + dz * math.sin(th_) * -1 * -1 if False else d + dy * math.cos(th_) - dz * math.sin(th_) * -1, h + dy * math.sin(th_) * -1 * -1 + dz * math.cos(th_)) if False else \
               (x, d + dy * math.cos(th_) + dz * math.sin(th_), h - dy * math.sin(th_) + dz * math.cos(th_))
    T = 900
    faces = []
    if lid_deg > 2:
        # lid inner face (underside in closed pose, z=h) -> becomes the mirror facing the camera when open
        Lq = [lidp(0, 0, h), lidp(w, 0, h), lidp(w, d, h), lidp(0, d, h)]
        Lq_draw = [Lq[3], Lq[2], Lq[1], Lq[0]][::-1]
        # inner walls + velvet + rim
        zv = h * 0.82
        faces.append(("mirror", [lidp(0, 0, h), lidp(w, 0, h), lidp(w, d, h), lidp(0, d, h)], (0, 0.3, 0.95), (T, int(T * d))))
        faces.append(("inner", [(t, d - t, h), (w - t, d - t, h), (w - t, d - t, zv), (t, d - t, zv)], (0, -1, 0), (T, int(T * 0.2))))
        faces.append(("inner", [(w - t, t, h), (w - t, d - t, h), (w - t, d - t, zv), (w - t, t, zv)], (-1, 0, 0), (int(T * d), int(T * 0.2))))
        faces.append(("velvet", [(t, t, zv), (w - t, t, zv), (w - t, d - t, zv), (t, d - t, zv)], (0, 0, 1), (T, int(T * d))))
        faces.append(("rimfront", None, None, None))
        if lid_deg < 80:   # partly open: the lid's engraved outer top and its front edge still face the camera
            sn, cs = math.sin(th_), math.cos(th_)
            faces.append(("metal", [lidp(0, 0, h + LID), lidp(w, 0, h + LID), lidp(w, d, h + LID), lidp(0, d, h + LID)], (0, sn, cs), (T, int(T * d))))
            faces.append(("metal", [lidp(0, 0, h + LID), lidp(w, 0, h + LID), lidp(w, 0, h), lidp(0, 0, h)], (0, -cs, sn), (T, int(T * LID))))
    else:
        faces.append(("metal", [(0, 0, h + LID), (w, 0, h + LID), (w, d, h + LID), (0, d, h + LID)], (0, 0, 1), (T, int(T * d))))
    faces.append(("metal", [(0, 0, h), (w, 0, h), (w, 0, 0), (0, 0, 0)], (0, -1, 0), (T, int(T * h))))
    faces.append(("metal", [(0, d, h), (0, 0, h), (0, 0, 0), (0, d, 0)], (-1, 0, 0), (int(T * d), int(T * h))))
    if lid_deg <= 2:
        faces.append(("metal", [(0, 0, h + LID), (w, 0, h + LID), (w, 0, h), (0, 0, h)], (0, -1, 0), (T, int(T * LID))))
        faces.append(("metal", [(0, d, h + LID), (0, 0, h + LID), (0, 0, h), (0, d, h)], (-1, 0, 0), (int(T * d), int(T * LID))))
    # painter's order: mirror lid (behind), inner walls, velvet, rim, outside faces
    for k, (kind, pts, n, ts) in enumerate(faces):
        if kind == "rimfront":
            # top rim: thin bright metal frame around the opening
            for q, nn in [([(0, 0, h), (w, 0, h), (w - t, t, h), (t, t, h)], (0, 0, 1)), ([(0, 0, h), (t, t, h), (t, d - t, h), (0, d, h)], (0, 0, 1)),
                          ([(w, 0, h), (w, d, h), (w - t, d - t, h), (w - t, t, h)], (0, 0, 1)), ([(0, d, h), (t, d - t, h), (w - t, d - t, h), (w, d, h)], (0, 0, 1))]:
                put(C, A, face_tex("metal_flat", 40, 8, nn, cam, (0.5, 0.3, h), env, seed), quad(cam, q), ss)
            continue
        centre = np.mean(np.array(pts, float), 0)
        if kind in ("metal",) and not cam.facing(centre, n):
            continue
        tex = face_tex(kind, ts[0], ts[1], n, cam, centre, env, seed + k)
        put(C, A, tex, quad(cam, pts), ss)
    if receipt > 0:
        # the folded pawn slip laid into the slit: a pale card standing up out of the cut, leaning back
        zv = h * 0.82; cy = t + SLOT["cy"] * (d - 2 * t); hl = SLOT["len"] * 0.55
        hgt = 0.11 * receipt
        q = [(0.5 - hl, cy, zv + hgt), (0.5 + hl, cy + 0.01, zv + hgt), (0.5 + hl, cy, zv - 0.01), (0.5 - hl, cy, zv - 0.01)]
        q = [(x, y + (z - zv) * 0.35, z) for x, y, z in q]
        yy_, xx_ = np.mgrid[0:60, 0:200].astype(np.float32)
        paper = 0.78 + 0.04 * np.random.default_rng(3).normal(0, 1, (60, 200)).astype(np.float32)
        paper[(xx_ > 20) & (xx_ < 180) & ((yy_ % 9) < 1.2) & (yy_ > 10)] -= 0.25     # typed lines seen edge-on
        paper *= 0.7 + 0.3 * (1 - yy_ / 60)
        put(C, A, paper, quad(cam, q), ss)
    # contact shadow: footprint projected away from the key, blurred
    foot = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0)]
    off = -KEY[:2] / KEY[2] * (h + LID) * 0.5
    sh = np.zeros_like(C)
    fq = quad(cam, [(x + off[0] * 0.6, y + off[1] * 0.6, 0) for x, y, _ in foot]) * ss
    cv2.fillPoly(sh, [fq.astype(np.int32)], 1.0)
    cv2.fillPoly(sh, [(quad(cam, foot) * ss).astype(np.int32)], 1.0)
    sh = cv2.GaussianBlur(sh, (0, 0), 6 * ss)
    sh2 = cv2.GaussianBlur(cv2.fillPoly(np.zeros_like(C), [(quad(cam, foot) * ss).astype(np.int32)], 1.0), (0, 0), 1.5 * ss)
    Cs = cv2.resize(C, (Wp, Hp), interpolation=cv2.INTER_AREA)
    As = cv2.resize(A, (Wp, Hp), interpolation=cv2.INTER_AREA)
    Ss = cv2.resize(np.maximum(sh * 0.65, sh2 * 0.9), (Wp, Hp), interpolation=cv2.INTER_AREA)
    return Cs, As, Ss

def slot_screen(cam):
    """screen position of the slit centre and box width endpoints (for the cross-media match test)"""
    zv = H_ * 0.82
    c = cam.P((SLOT["cx"] * W_, WALL + SLOT["cy"] * (D_ - 2 * WALL), zv))
    l = cam.P((0, WALL, zv)); r = cam.P((W_, WALL, zv))
    return c, l, r
