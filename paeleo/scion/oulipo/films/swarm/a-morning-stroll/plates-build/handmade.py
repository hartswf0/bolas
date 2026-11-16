"""HANDMADE objects built for this film (no foraged pixels): the 2009 door chain and the 2059 7-dot sensor strip.
Run: python3 -I handmade.py   -> sources/.../plates/handmade/*

Chain: 6 steel oval links modelled as tori (per-pixel normal from the ring cross-section, one key light from the
upper right to match the 2009 plate's low winter sun), rendered 4x supersampled into RGBA. Two states are given as
link-centre lists (slack catenary and taut line) plus pre-rendered strips; the editor can re-pose links from
chain.json (each link: centre, angle, which-face).
Sensor strip: a brushed-steel bar (anisotropic noise streaks), 7 recessed lenses; sprites for lens OFF, ON (cool
white), REFUSE (amber) with a soft bloom; dot centres in strip coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

from common import PLATES, dump

OUT = f"{PLATES}/handmade"
os.makedirs(OUT, exist_ok=True)
SS = 4


def link_sprite(L=46, Wd=26, t=6.0, ang=0.0, light=(0.55, -0.6, 0.58)):
    """One oval link (stadium torus) of outer length L, width Wd, wire radius t/2 (px at 1x), rotated by ang (rad)."""
    n = int(max(L, Wd) * 1.6) * SS
    yy, xx = (np.mgrid[0:n, 0:n] - n / 2 + 0.5) / SS
    c, s = math.cos(-ang), math.sin(-ang)
    u, v = c * xx - s * yy, s * xx + c * yy
    r = t / 2
    a, b = (L - 2 * r) / 2 - (Wd - 2 * r) / 2, (Wd - 2 * r) / 2        # half straight length, centreline radius
    uc = np.clip(u, -a, a)
    du, dv = u - uc, v
    dist_c = np.hypot(du, dv)                                           # distance to the stadium's centre axis
    d = dist_c - b                                                      # signed distance to the wire centreline
    inside = np.abs(d) <= r
    h = np.sqrt(np.clip(r * r - d * d, 0, None))
    # normal: radial (in plane) * d/r + z * h/r
    nx = (du / np.maximum(dist_c, 1e-6)) * d / r
    ny = (dv / np.maximum(dist_c, 1e-6)) * d / r
    nz = h / r
    # rotate normal back to image axes
    c2, s2 = math.cos(ang), math.sin(ang)
    Nx, Ny = c2 * nx - s2 * ny, s2 * nx + c2 * ny
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lam = np.clip((Nx * lx + Ny * ly + nz * lz) / ln, 0, 1)
    hz = np.clip(nz + (Nx * lx + Ny * ly + nz * lz) / ln, 0, None)    # cheap specular
    spec = np.clip(hz / 2, 0, 1) ** 24
    base = np.array([96, 98, 104], np.float32)                          # zinc-plated steel
    col = base * (0.28 + 0.9 * lam)[..., None] + 255 * 0.85 * spec[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), inside * 255.0]).astype(np.float32)
    im = Image.fromarray(rgba.astype(np.uint8), "RGBA").resize((n // SS, n // SS), Image.LANCZOS)
    return im


def chain_strip(points, angles, size):
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    for i, ((x, y), a) in enumerate(zip(points, angles)):
        face = 0 if i % 2 == 0 else 1
        spr = link_sprite(ang=a, Wd=26 if face == 0 else 9)            # alternate links seen edge-on
        canvas.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))
    return canvas


def chain():
    n, pitch = 6, 34.0
    span = (n - 1) * pitch
    # taut: straight horizontal line; slack: catenary with the same arc length hanging between anchors 70 % as far apart
    taut = [(30 + i * pitch, 40.0) for i in range(n)]
    # slack: a catenary between anchors 70 % as far apart, solved so its arc length equals the chain length;
    # link centres placed at equal arc-length steps, each link turned to the local tangent
    sag_w = span * 0.7
    lo, hi = 1.0, 1e4
    for _ in range(80):                                                # bisection on the catenary parameter a
        a = (lo + hi) / 2
        if 2 * a * math.sinh(sag_w / (2 * a)) > span:
            lo = a
        else:
            hi = a
    xs_f = np.linspace(-sag_w / 2, sag_w / 2, 2001)
    ys_f = a * np.cosh(xs_f / a)
    ys_f = ys_f - ys_f[0]
    arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs_f), np.diff(ys_f)))])
    targets = np.linspace(0, arc[-1], n)
    xs = np.interp(targets, arc, xs_f)
    ys = np.interp(targets, arc, ys_f)
    x0 = 30 + (span - sag_w) / 2
    slack = [(x0 + sag_w / 2 + float(x), 40.0 - float(y)) for x, y in zip(xs, ys)]
    ang_s = [float(math.atan(-math.sinh(x / a))) for x in xs]          # image y down: slope sign flipped
    size = (int(span + 80), 140)
    chain_strip(taut, [0.0] * n, size).save(f"{OUT}/chain_taut.png")
    chain_strip(slack, ang_s, size).save(f"{OUT}/chain_slack.png")
    link_sprite().save(f"{OUT}/chain_link_face.png")
    link_sprite(Wd=9).save(f"{OUT}/chain_link_edge.png")
    # guard plate (slot track) for the frame side
    g = np.zeros((90, 26, 4), np.float32)
    g[..., :3] = [150, 150, 156]
    g[..., 3] = 255
    g[10:80, 10:16, :3] = 40                                           # the slot
    g[:, :2, :3] *= 0.6
    g[:, -2:, :3] *= 1.15
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA").save(f"{OUT}/chain_guard.png")
    return {"links": n, "pitch_px": pitch, "taut_centres": taut, "slack_centres": slack, "slack_angles": ang_s,
            "canvas": list(size), "files": {"taut": f"{OUT}/chain_taut.png", "slack": f"{OUT}/chain_slack.png",
                                            "link_face": f"{OUT}/chain_link_face.png", "link_edge": f"{OUT}/chain_link_edge.png",
                                            "guard": f"{OUT}/chain_guard.png"},
            "scale_note": "sprites are at B-frame scale for the 2009 door (link ~46 px = ~4 cm at the leaf); left end hooks at geometry chain_anchor_frame, right end at chain_anchor_leaf",
            "motion": "slack until E5 start (7.0 s); straightens to taut over 4 frames when the leaf reaches 25 deg (~7.6 s); 2-frame overshoot jitter"}


def sensor():
    Wb, Hb, n = 560, 46, 7
    rng = np.random.default_rng(2059)
    streak = rng.normal(0, 1, (Hb * SS, 1)) * 9 + rng.normal(0, 1, (Hb * SS, Wb * SS)) * 2.5
    streak = np.repeat(rng.normal(0, 1, (Hb * SS, Wb * SS // 64)), 64, axis=1)[:, :Wb * SS] * 4 + streak
    yy, xx = np.mgrid[0:Hb * SS, 0:Wb * SS] / SS
    shade = 150 + 40 * np.exp(-((yy - 10) / 6) ** 2) - 30 * (yy / Hb)  # top bevel highlight, falling to bottom
    bar = np.dstack([shade + streak + 2, shade + streak + 4, shade + streak + 8]).astype(np.float32)
    r = 9.0
    radius = 6.0
    corner = np.ones_like(yy, bool)
    for cx, cy in ((radius, radius), (Wb - radius, radius), (radius, Hb - radius), (Wb - radius, Hb - radius)):
        q = ((xx < radius) if cx < Wb / 2 else (xx > Wb - radius)) & ((yy < radius) if cy < Hb / 2 else (yy > Hb - radius))
        corner &= ~(q & (np.hypot(xx - cx, yy - cy) > radius))
    dots = [(Wb / 2 + (i - 3) * 64.0, Hb / 2) for i in range(n)]
    for cx, cy in dots:
        d = np.hypot(xx - cx, yy - cy)
        rim = (d > r) & (d < r + 2.5)
        bar[rim] *= 0.55                                               # recess shadow ring
        bar[d <= r] = [22, 24, 28]                                     # dark lens (OFF)
        hl = (d <= r) & (np.hypot(xx - cx + 3, yy - cy + 3) < 2.5)
        bar[hl] = [120, 124, 130]                                      # glass glint
    rgba = np.dstack([np.clip(bar, 0, 255), corner * 255.0]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").resize((Wb, Hb), Image.LANCZOS).save(f"{OUT}/sensor_bar_off.png")

    def lamp(col, name):
        s = 64
        y2, x2 = (np.mgrid[0:s * SS, 0:s * SS] / SS) - s / 2
        d = np.hypot(x2, y2)
        core = np.clip((r - d) / 1.2, 0, 1)
        bloom = np.exp(-(d / 10.0) ** 2) * 0.55
        a = np.clip(core + bloom, 0, 1)
        c = np.array(col, np.float32)
        rgb = c * (1 - core[..., None]) + np.array([255, 255, 255], np.float32) * core[..., None] * 0.6 + c * core[..., None] * 0.4
        Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA").resize((s, s), Image.LANCZOS).save(f"{OUT}/{name}")
    lamp((150, 225, 255), "sensor_dot_on.png")
    lamp((255, 170, 60), "sensor_dot_refuse.png")
    # preview states
    base = Image.open(f"{OUT}/sensor_bar_off.png")
    for name, lit in (("sensor_state_one.png", {0: "on"}), ("sensor_state_two.png", {0: "on", 1: "on"}), ("sensor_state_refuse.png", {0: "refuse"})):
        im = Image.new("RGBA", (Wb + 40, Hb + 40), (0, 0, 0, 0))
        im.alpha_composite(base, (20, 20))
        for i, k in lit.items():
            spr = Image.open(f"{OUT}/sensor_dot_{k}.png")
            im.alpha_composite(spr, (int(20 + dots[i][0] - 32), int(20 + dots[i][1] - 32)))
        im.save(f"{OUT}/{name}")
    return {"bar": f"{OUT}/sensor_bar_off.png", "size": [Wb, Hb], "dot_centres": dots, "dot_sprite_size": 64,
            "dot_on": f"{OUT}/sensor_dot_on.png", "dot_refuse": f"{OUT}/sensor_dot_refuse.png",
            "previews": [f"{OUT}/sensor_state_one.png", f"{OUT}/sensor_state_two.png", f"{OUT}/sensor_state_refuse.png"],
            "state_machine_hint": "closed: all off; strike k lights dot k-1 (on); X1 single peck: dot0 on 4 frames -> refuse 6 frames -> off; E3/E4: dots 0,1 on, held; door slides at E5",
            "mount": "centred above the sliding leaves, on the transom (see 2059 geometry)"}


if __name__ == "__main__":
    dump({"chain_2009": chain(), "sensor_2059": sensor()}, f"{OUT}/handmade.json")
    print("ok")
