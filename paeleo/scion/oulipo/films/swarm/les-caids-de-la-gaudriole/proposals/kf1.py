"""KF1 - LE PLI SUR LA TABLE: stop-motion of the printed strip folding on a table.

The strip (strip.py) is printed onto a foraged paper scan and folded as a real
three-facet Z-fold: facet 3 (sheet x M..2400) lies on the table, facet 2 (A..M)
has swung up about crease M, facet 1 (0..A) rides on crease A. Orthographic
camera tilted 38 deg; each facet is an affine warp of its own sheet crop; the
back of facet 2 shows the mirrored show-through of its ink; facets cast
blurred shadows along the light; an archive hand (GrabCut matte) holds the
free edge. Monochrome, as the reference.
"""
import math, os, sys, subprocess
import numpy as np
import cv2
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strip as S

HERE = S.HERE
OUT = os.path.join(HERE, "kf-1.png")
W, H = 1280, 720
SC = 0.47                 # sheet px -> screen px
TILT = math.radians(38)
ALPHA = math.radians(152)  # facet 2 about crease M (0 = flat, 180 = folded over)
BETA = math.radians(-13)   # facet 1 direction (0 = flat leftward)
LIGHT = np.array([-0.45, 0.35, 0.82]); LIGHT /= np.linalg.norm(LIGHT)
OX, OY = 70, 250           # screen offset of sheet origin (x=0, row 0, z=0)


def paper_rgb(size):
    p = Image.open(os.path.join(S.SRC, "paper.jpg")).convert("L")
    p = p.resize((size[0], int(p.height * size[0] / p.width))).crop((0, 0, size[0], size[1]))
    a = np.asarray(p, np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    base = 236 + 7 * a                     # bright sheet, fibre and stain kept
    rgb = np.stack([base, base - 3, base - 9], -1)
    return np.clip(rgb, 0, 255)


def printed(sheet_L, paper):
    ink = 1 - np.asarray(sheet_L, np.float32) / 255.0
    return paper * (1 - 0.93 * ink[..., None])


CAM = np.array([1450.0, 2500.0, 2300.0])
TGT = np.array([1640.0, 450.0, 60.0])
FOC = 1950.0
_f = TGT - CAM; _f /= np.linalg.norm(_f)
_r = np.cross([0, 0, 1.0], _f); _r /= np.linalg.norm(_r)
_u = np.cross(_f, _r)


def proj(x, r, z):
    p = np.array([x, r, z]) - CAM
    zc = p @ _f
    return (W / 2 + FOC * (p @ _r) / zc, H / 2 - FOC * (p @ _u) / zc + 10)


def facet_pts(u0, u1, P):
    """P(u) -> (x, z); return 3D corners for sheet u0..u1, rows 0..SH."""
    (xa, za), (xb, zb) = P(u0), P(u1)
    return [(xa, 0, za), (xb, 0, zb), (xb, S.SH, zb), (xa, S.SH, za)]


def warp_facet(canvas, tex, u0, u1, P, shade, mirror=False):
    crop = tex[:, int(u0):int(u1)]
    if mirror:
        crop = crop[:, ::-1]
    h, w = crop.shape[:2]
    c = facet_pts(u0, u1, P)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]]) if not mirror else np.float32([[w, 0], [0, 0], [0, h], [w, h]])
    dst = np.float32([proj(*c[0]), proj(*c[1]), proj(*c[2]), proj(*c[3])])
    Mx = cv2.getPerspectiveTransform(src, dst)
    small = cv2.resize((crop * shade).astype(np.float32), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    Mx = Mx @ np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1.0]])
    img = cv2.warpPerspective(small, Mx, (W, H), flags=cv2.INTER_LINEAR)
    m = cv2.warpPerspective(np.ones(small.shape[:2], np.float32), Mx, (W, H), flags=cv2.INTER_LINEAR)
    canvas[:] = canvas * (1 - m[..., None]) + img * m[..., None]
    return m


def shadow_poly(c):
    L = LIGHT
    out = []
    for x, r, z in c:
        out.append(proj(x - z * L[0] / L[2], r + z * L[1] / L[2], 0))
    return np.int32(out)


def table():
    t = Image.open(os.path.join(S.SRC, "wood.jpg")).convert("L").resize((1920, 1281))
    t = t.crop((200, 150, 200 + W, 150 + H)).rotate(90, expand=False) if False else t.crop((300, 200, 300 + W, 200 + H))
    a = np.asarray(t, np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.6)
    a = 62 + 0.28 * (a - a.mean())
    # vignette, overhead lamp at upper left
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1.0 - 0.55 * (((xx - 420) / 1100) ** 2 + ((yy - 200) / 700) ** 2)
    a = a * v
    return np.stack([a * 1.04, a, a * 0.94], -1)


def hand_cutout():
    clip = "/home/user/hartswf0/cineosis-lab/lab/clips/af625567-bdef-5658-afe8-1994714524d9.mp4"
    tmp = os.path.join(HERE, "_hand.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.4", "-i", clip, "-frames:v", "1", tmp], check=True)
    f = cv2.imread(tmp)
    os.remove(tmp)
    mask = np.zeros(f.shape[:2], np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(f, mask, (150, 40, 170, 150), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 1.0, 0.0).astype(np.float32)
    m[:, 300:] = m[:, 300:]  # keep wrist
    m = cv2.GaussianBlur(m, (5, 5), 0)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
    # mirror: the archive hand reaches left; the animator's hand reaches right to the free edge
    return g[:, ::-1], m[:, ::-1]


def main():
    r = S.build()
    sheet = r["sheet"]
    paper = paper_rgb((S.SW, S.SH))
    front = printed(sheet, paper)
    back_ink = 0.10 * (1 - np.asarray(sheet, np.float32) / 255.0)  # show-through
    back = paper * (1 - back_ink[..., None]) * 0.98

    A, M = S.A, S.M
    P3 = lambda u: (u, 0.0)
    P2 = lambda u: (M + (M - u) * -math.cos(ALPHA), (M - u) * math.sin(ALPHA))
    PA = P2(A)
    P1 = lambda u: (PA[0] - (A - u) * math.cos(BETA), PA[1] + (A - u) * math.sin(BETA))

    cv = table()
    # sheet's own contact shadow on the table
    sh = np.zeros((H, W), np.float32)
    cv2.fillPoly(sh, [np.int32([proj(M, 0, 0), proj(S.SW, 0, 0), proj(S.SW, S.SH, 0), proj(M, S.SH, 0)]) + np.int32([6, 8])], 1.0)
    for c in (facet_pts(A, M, P2), facet_pts(0, A, P1)):
        cv2.fillPoly(sh, [shadow_poly(c)], 1.0)
    sh = cv2.GaussianBlur(sh, (0, 0), 14)
    cv *= (1 - 0.55 * sh[..., None])

    def lam(n):
        return 0.62 + 0.38 * max(0.0, float(np.dot(n, LIGHT)))

    # facet 3 on the table (front up)
    warp_facet(cv, front, M, S.SW, P3, lam(np.array([0, 0, 1.0])))
    # shadows of the raised facets falling onto facet 3
    sh2 = np.zeros((H, W), np.float32)
    for c in (facet_pts(A, M, P2), facet_pts(0, A, P1)):
        cv2.fillPoly(sh2, [shadow_poly(c)], 1.0)
    sh2 = cv2.GaussianBlur(sh2, (0, 0), 10)
    clipm = np.zeros((H, W), np.float32)
    cv2.fillPoly(clipm, [np.int32([proj(M, 0, 0), proj(S.SW, 0, 0), proj(S.SW, S.SH, 0), proj(M, S.SH, 0)])], 1.0)
    cv *= (1 - 0.38 * (sh2 * clipm)[..., None])

    # facet 2: tangent (cos a, -sin a), front normal (sin a, cos a): front faces away -> we see its back
    n2 = np.array([math.sin(ALPHA), 0, math.cos(ALPHA)])
    warp_facet(cv, back, A, M, P2, lam(-n2) * 0.92, mirror=False)
    # facet 1: tangent (cos b, -sin b), normal (-t_z, t_x) = (sin b, cos b)
    n1 = np.array([math.sin(BETA), 0, math.cos(BETA)])
    # crease highlight/darkening: a soft gradient along facet 1 near crease A
    m1 = warp_facet(cv, front, 0, A, P1, lam(n1))
    # crease lines
    for u, P in ((M, P3), (A, P1)):
        x, z = P(u)
        a, b = proj(x, 0, z), proj(x, S.SH, z)
        cv2.line(cv, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (60, 58, 55), 1, cv2.LINE_AA)

    # film: monochrome grade + light grain from the real paper only (no added grain)
    out = np.clip(cv, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
