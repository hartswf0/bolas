"""SCION 11 · the background stage: a tabletop set of cut card, built here.

Barnes's tabletop has a background stage the puppets are laid over. This one is cut paper:
every layer is a polygon with a hand-jittered edge, a paper-fibre texture and a soft drop
shadow onto the layer beneath (cards on a table under one lamp). Nothing here is found.

Space: x along the porch maps to screen as  sx = X0 + PXM * x  (threshold x = 0 at the door's
centre line, door opening -0.46..0.46 m).  The porch floor runs from the wall base (y 500)
toward the camera; the dog walks on the line y = FEET(x).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

W, H = 1280, 720
X0, PXM = 320.0, 200.0
WALL_Y = 500
DOOR = (228, 150, 412, 500)        # opening, x -0.46..0.46 m
HOUSE_R = 610
HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(11)


def sx(x):
    return X0 + PXM * x


def feet_y(x):
    """the dog's ground line: mid-porch, then drawing in to the sill over the last metre"""
    u = np.clip((1.75 - x) / (1.75 - 0.59), 0, 1)
    u = u * u * (3 - 2 * u)
    return 612 - (612 - 530) * u


def dog_scale(y):
    return 1.36 * (0.84 + 0.16 * (y - 530) / (612 - 530))


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255. for i in (0, 2, 4))


def jitter(poly, amt=1.2, step=14):
    """a scissor edge: subdivide and wobble"""
    out = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        L = max(1, int(np.hypot(x1 - x0, y1 - y0) / step))
        for k in range(L):
            t = k / L
            out.append((x0 + (x1 - x0) * t + RNG.normal(0, amt), y0 + (y1 - y0) * t + RNG.normal(0, amt)))
    return out


def fibre(h, w, seed, amp=.05):
    r = np.random.default_rng(seed)
    a = r.normal(0, 1, (h // 8 + 2, w // 8 + 2)).astype(np.float32)
    a = np.asarray(Image.fromarray(a).resize((w, h), Image.BICUBIC))
    b = r.normal(0, 1, (h, w)).astype(np.float32)
    b = ndimage.gaussian_filter(b, .7)
    s = r.normal(0, 1, (h // 2 + 1, w // 24 + 2)).astype(np.float32)  # fibres run along the sheet
    s = np.asarray(Image.fromarray(s).resize((w, h), Image.BICUBIC))
    return 1 + amp * (.5 * a + .6 * b + .35 * s)


class Layer:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), np.float32)


def mask_of(polys, ss=2, blur=0.0):
    im = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    im = im.resize((W, H), Image.LANCZOS)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255.


def card(canvas, polys, color, seed, shadow=(4, 5, 4, .38), tex=.05, grad=None, jit=1.2):
    """lay one card on the canvas (RGB float), with its drop shadow"""
    polys = [jitter(p, jit) for p in polys]
    m = mask_of(polys)
    if shadow:
        dx, dy, bl, op = shadow
        sm = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(bl)), np.float32) / 255.
        sm = np.roll(np.roll(sm, dy, 0), dx, 1)
        canvas *= (1 - op * sm)[..., None]
    col = np.array(color, np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
    if grad is not None:
        col = col * grad[..., None] if grad.ndim == 2 else col * grad
    col = col * fibre(H, W, seed, tex)[..., None]
    canvas[:] = canvas * (1 - m[..., None]) + col * m[..., None]
    return m


def build_static():
    """returns dict of float RGB layers: back (sky..rail), wall (with the door hole), floor, front"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    back = np.zeros((H, W, 3), np.float32)
    # --- sky: three torn bands of dusk paper
    g = np.clip(yy / 440., 0, 1)
    sky = (np.array(hexc('#1d2140'))[None, None] * (1 - g[..., None]) + np.array(hexc('#5a4a6a'))[None, None] * g[..., None])
    back[:] = sky * fibre(H, W, 1, .03)[..., None]
    card(back, [[(560, 250), (1280, 236), (1280, 440), (560, 440)]], hexc('#9a6c66'), 2, shadow=(0, 3, 6, .25),
         grad=np.clip(1.15 - (yy - 250) / 600, .7, 1.2), jit=2.5)
    card(back, [[(560, 330), (1280, 318), (1280, 440), (560, 440)]], hexc('#c08a6a'), 3, shadow=(0, 3, 6, .25), jit=2.5)
    # moon, a pale cut crescent
    mo = mask_of([[(1032 + 24 * np.cos(a), 112 + 24 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)]])
    mo2 = mask_of([[(1042 + 22 * np.cos(a), 106 + 22 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)]])
    cres = np.clip(mo - mo2, 0, 1)
    back[:] = back * (1 - cres[..., None]) + np.array(hexc('#e9e0c6'))[None, None] * cres[..., None]
    # tree line: a strip of dark card with a bumpy top
    xs = np.arange(560, 1290, 18)
    top = 360 - 30 * np.abs(np.sin(xs * .021)) - 18 * np.abs(np.sin(xs * .057 + 1)) - RNG.uniform(0, 10, len(xs))
    card(back, [[(560, 440)] + list(zip(xs, top)) + [(1290, 440)]], hexc('#1c2427'), 4, shadow=(3, 4, 5, .35), jit=1.6)
    # yard beyond the deck
    card(back, [[(560, 432), (1280, 428), (1280, 505), (560, 505)]], hexc('#2b3330'), 5, shadow=(2, 3, 4, .3))
    # deck rail (behind the walking line)
    rail = [[(600, 398), (1280, 398), (1280, 408), (600, 408)], [(600, 470), (1280, 470), (1280, 476), (600, 476)]]
    for px in [760, 940, 1120]:
        rail.append([(px, 392), (px + 13, 392), (px + 13, 502), (px, 502)])
    for bx in range(628, 1280, 34):
        rail.append([(bx, 408), (bx + 6, 408), (bx + 6, 470), (bx, 470)])
    card(back, rail, hexc('#4b4440'), 6, shadow=(4, 6, 4, .4), tex=.07)
    # --- the house wall: clapboard card with the door cut out of it
    wall = np.zeros((H, W, 4), np.float32)
    wl = np.zeros((H, W, 3), np.float32)
    wpoly = [(0, 0), (HOUSE_R, 0), (HOUSE_R, WALL_Y + 4), (0, WALL_Y + 4)]
    wm = mask_of([jitter(wpoly, 1.0)])
    clap = 1 - .10 * (((yy - 6) % 26) < 2.5) - .05 * np.clip(((yy - 6) % 26) / 26, 0, 1)
    col = np.array(hexc('#56607a'))[None, None] * clap[..., None] * fibre(H, W, 7, .05)[..., None]
    col *= (1.0 - .18 * (xx / HOUSE_R))[..., None]
    wl[:] = col
    # window
    card(wl, [[(462, 196), (578, 196), (578, 338), (462, 338)]], hexc('#b9b2a0'), 8, shadow=(3, 4, 3, .35))
    card(wl, [[(472, 206), (568, 206), (568, 328), (472, 328)]], hexc('#1f2a3c'), 9, shadow=(2, 3, 3, .45),
         grad=np.clip(.8 + (yy - 206) / 300, .8, 1.3))
    card(wl, [[(517, 206), (523, 206), (523, 328), (517, 328)], [(472, 264), (568, 264), (568, 270), (472, 270)]],
         hexc('#b9b2a0'), 10, shadow=(2, 2, 2, .3))
    # eave
    card(wl, [[(0, 0), (HOUSE_R + 14, 0), (HOUSE_R + 14, 44), (0, 50)]], hexc('#262a36'), 11, shadow=(0, 6, 6, .5))
    # corner board
    card(wl, [[(HOUSE_R - 16, 40), (HOUSE_R + 2, 40), (HOUSE_R + 2, WALL_Y + 4), (HOUSE_R - 16, WALL_Y + 4)]], hexc('#8c8a86'), 12)
    # door frame trim (the hole is cut after)
    tm = card(wl, [[(208, 128), (432, 128), (432, WALL_Y + 4), (208, WALL_Y + 4)]], hexc('#bdb6a4'), 13, shadow=(3, 4, 4, .4))
    hole = mask_of([[(DOOR[0], DOOR[1]), (DOOR[2], DOOR[1]), (DOOR[2], DOOR[3] + 6), (DOOR[0], DOOR[3] + 6)]])
    wall[..., :3] = wl
    wall[..., 3] = np.clip(np.maximum(wm, tm) - hole, 0, 1)
    # --- porch floor: planks running along the porch, the sill stone at the door
    floor = np.zeros((H, W, 4), np.float32)
    fl = np.zeros((H, W, 3), np.float32)
    f = (yy - WALL_Y) / (720 - WALL_Y)
    pl = np.zeros_like(yy)
    edges = WALL_Y + (720 - WALL_Y) * (np.linspace(0, 1, 12) ** 1.35)
    for e in edges:
        pl += np.exp(-((yy - e) / 1.2) ** 2)
    joint = np.zeros_like(yy)
    for k, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        off = (k * 263) % 400
        joint += ((yy > a) & (yy < b) & (((xx + off) % 400) < 2.2)).astype(np.float32)
    base = np.array(hexc('#6a5848'))[None, None] * (0.72 + .38 * f[..., None])
    fl[:] = base * (1 - .35 * np.clip(pl + joint, 0, 1))[..., None] * fibre(H, W, 14, .06)[..., None]
    fm = mask_of([[(0, WALL_Y - 2), (1280, WALL_Y - 2), (1280, 690), (0, 690)]])
    sill = [(206, WALL_Y - 4), (434, WALL_Y - 4), (440, WALL_Y + 18), (200, WALL_Y + 18)]
    card(fl, [sill], hexc('#8e8a82'), 15, shadow=(2, 5, 4, .45))
    card(fl, [[(200, WALL_Y + 18), (440, WALL_Y + 18), (440, WALL_Y + 24), (200, WALL_Y + 24)]], hexc('#5f5c57'), 16, shadow=None)
    floor[..., :3] = fl
    floor[..., 3] = fm
    # --- foreground: porch fascia and the corner post at the steps
    front = np.zeros((H, W, 4), np.float32)
    fr = np.zeros((H, W, 3), np.float32)
    fasc = card(fr, [[(0, 688), (1250, 686), (1250, 720), (0, 720)]], hexc('#3a2f28'), 17, shadow=None)
    post = card(fr, [[(1262, 330), (1280, 330), (1280, 720), (1262, 720)]], hexc('#2c2622'), 18, shadow=None)
    step = card(fr, [[(1250, 686), (1262, 686), (1262, 720), (1250, 720)]], hexc('#4a3c32'), 19, shadow=None)
    front[..., :3] = fr
    front[..., 3] = np.clip(fasc + post + step, 0, 1)
    return dict(back=back, wall=wall, floor=floor, front=front)


def interior(light):
    """the room behind the door: warm card; light 0 (dark) .. 1 (lamp up, door wide)"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rm = np.zeros((H, W, 3), np.float32)
    x0, y0, x1, y1 = DOOR
    room = np.array(hexc('#c98f4f'))[None, None] * np.ones((H, W, 1), np.float32)
    glow = np.exp(-(((xx - 360) / 160) ** 2 + ((yy - 260) / 150) ** 2))
    rm[:] = room * (0.25 + 0.95 * glow[..., None])
    fl = (yy > 430)
    rm[fl] *= 0.75
    # a lamp on a table, cut from dark card, and its shade glowing
    lamp = mask_of([[(330, 300), (370, 300), (382, 330), (318, 330)]])
    stand = mask_of([[(347, 330), (353, 330), (353, 400), (347, 400)], [(300, 400), (400, 400), (400, 408), (300, 408)],
                     [(310, 408), (316, 408), (316, 470), (310, 470)], [(384, 408), (390, 408), (390, 470), (384, 470)]])
    rm = rm * (1 - stand[..., None] * .8)
    rm = rm * (1 - lamp[..., None]) + np.array(hexc('#ffe2a0'))[None, None] * lamp[..., None] * 1.15
    return rm, light


def door_panel(theta_deg):
    """door hinged on the left jamb, swinging inward: its card narrows and darkens"""
    x0, y0, x1, y1 = DOOR
    c = np.cos(np.radians(theta_deg))
    wpx = (x1 - x0) * c
    k = 6 * np.sin(np.radians(theta_deg))  # perspective: free edge recedes
    poly = [(x0, y0), (x0 + wpx, y0 + k), (x0 + wpx, y1 - k * .5), (x0, y1)]
    m = mask_of([poly])
    col = np.array(hexc('#33423c'))[None, None] * (0.55 + .45 * c)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # four sunk panels, drawn on the card
    pan = np.zeros((H, W), np.float32)
    for (a, b, cc, d) in [(.12, .08, .44, .45), (.56, .08, .88, .45), (.12, .55, .44, .93), (.56, .55, .88, .93)]:
        pan += mask_of([[(x0 + wpx * a, y0 + (y1 - y0) * b), (x0 + wpx * cc, y0 + (y1 - y0) * b),
                         (x0 + wpx * cc, y0 + (y1 - y0) * d), (x0 + wpx * a, y0 + (y1 - y0) * d)]])
    rgb = col * np.ones((H, W, 1), np.float32) * (1 - .18 * np.clip(pan, 0, 1))[..., None]
    knob = mask_of([[(x0 + wpx - 16 * c + 4 * np.cos(a), 330 + 4 * np.sin(a)) for a in np.linspace(0, 6.28, 12)]])
    rgb = rgb * (1 - knob[..., None]) + np.array(hexc('#b89a5a'))[None, None] * knob[..., None]
    return rgb, m


def light_pool(open_amt):
    """warm light thrown from the doorway across the sill and the porch boards"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x0, y0, x1, y1 = DOOR
    t = np.clip((yy - WALL_Y) / (720 - WALL_Y), 0, 1)
    l = x0 - 70 * t - 20
    r = x1 + 160 * t + 20
    inside = np.clip((xx - l) / 40, 0, 1) * np.clip((r - xx) / 60, 0, 1) * (yy >= WALL_Y - 6)
    fall = np.exp(-t * 1.6)
    pool = inside * fall
    pool = np.asarray(Image.fromarray((pool * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32) / 255.
    # and a soft glow on the wall around the opening
    gl = np.exp(-(((xx - 320) / 150) ** 2 + ((yy - 330) / 210) ** 2)) * (yy < WALL_Y)
    return pool * open_amt, gl * open_amt


if __name__ == '__main__':
    S = build_static()
    np.savez_compressed(os.path.join(HERE, 'cache', 'stage.npz'), **S)
    print('stage saved')
