"""2059 plate (Commons: "Automatische Schiebetüre mit Schlüsselsäule", Plennert, 28 March 2022, CC BY-SA 4.0).
Run: python3 -I prep_2059.py   -> sources/.../plates/2059/*
Input: plates/raw/commons/schiebetuer.jpg (the Commons 1920 px thumbnail of the 4624 x 2084 original; the original
URL returned HTTP 429 repeatedly). Coordinates are in this 1920 x 865 image.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

from common import PLATES, dump, push_rects, render_crop, rgba_piece

OUT = f"{PLATES}/2059"
os.makedirs(OUT, exist_ok=True)
SHOTS = {"A": (200, 10, 1720, 865), "C": (200, 10, 1720, 865), "B": (450, 170, 1410, 710)}
LEAF_L = (695, 930)        # left sliding leaf x (slides left behind the fixed side light, rail at y 185..700)
LEAF_R = (930, 1170)       # right sliding leaf x (slides right)
LEAF_Y = (190, 700)
RAIL_Y_TOP, RAIL_Y_BOT = 186, 702
POSTS = [(680, 698), (1165, 1182)]  # dark aluminium posts at the leaf pockets (hard holdouts)
PILLAR = (1180, 1226, 365, 732)     # key pillar (Schlüsselsäule), in front of the right side light
STRIP_MOUNT = (930, 205)            # centre of the handmade 7-dot strip, on the leaves' head rail


def unify(rgb):
    """One cold unify grade toward the AK17 ladder: saturation x0.40 about luma, a highlight-compressing curve
    (no clipping; scaled to 0.68 so <5 % lands above 200 and the median sits near AK17), +4 green / -2 red on the result. Applied identically to every 2059 pixel."""
    a = rgb.astype(np.float32)
    L = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = L[..., None] + (a - L[..., None]) * 0.40
    t = np.clip(a / 255.0, 0, 1)
    t = 0.80 * t ** 1.15 / (0.80 * t ** 1.15 + 0.20 * (1 - t) ** 1.3 + 1e-6) * 0.68 + 0.02
    out = t * 255 + np.array([-2, 4, 0], np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    P = np.asarray(Image.open(f"{PLATES}/raw/commons/schiebetuer.jpg").convert("RGB"))
    G = unify(P)
    Image.fromarray(G).save(f"{OUT}/plate_graded.png")
    gimg = Image.fromarray(G)
    crops = {}
    for k, r in SHOTS.items():
        pr = push_rects(r)
        render_crop(gimg, pr[0], f"{OUT}/crop_{k}_start.png")
        render_crop(gimg, pr[1], f"{OUT}/crop_{k}_end.png")
        crops[k] = {"rect": list(r), "push_start": pr[0], "push_end": pr[1], "scale_px_per_src": 960 / (r[2] - r[0]),
                    "start_png": f"{OUT}/crop_{k}_start.png"}
    h, w = G.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    box = lambda x0, x1, y0, y1: ((xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)).astype(np.float32) * 255
    pieces = {
        "leaf_left": box(*LEAF_L, *LEAF_Y), "leaf_right": box(*LEAF_R, *LEAF_Y),
        "post_left": box(*POSTS[0], 140, 705), "post_right": box(*POSTS[1], 140, 705),
        "pillar": box(PILLAR[0], PILLAR[1], PILLAR[2], PILLAR[3]),
        "head_rail": box(530, 1180, 170, RAIL_Y_TOP + 6), "threshold": box(540, 1180, RAIL_Y_BOT - 4, 712),
    }
    st = {k: rgba_piece(G, v, f"{OUT}/piece_{k}.png", f"{OUT}/piece_{k}_contour.png") for k, v in pieces.items()}
    # interior seen through the opening (HANDMADE from the plate): the view through the glass with the surface
    # reflection lifted out (local minimum over a small window = what the glass adds least) and slightly darker
    from PIL import ImageFilter
    inner = np.asarray(gimg.filter(ImageFilter.MinFilter(5)), np.float32) * 0.82
    op = box(LEAF_L[0], LEAF_R[1], *LEAF_Y)
    Image.fromarray(np.dstack([inner.clip(0, 255).astype(np.uint8), op.astype(np.uint8)]), "RGBA").save(f"{OUT}/interior_opening.png")
    ov = G.copy()
    for k, v in pieces.items():
        col = {"leaf_left": [0, 0, 90], "leaf_right": [0, 60, 90], "pillar": [90, 0, 0]}.get(k, [0, 90, 0])
        m = v > 0
        ov[m] = (0.6 * ov[m] + col).astype(np.uint8)
    ov[STRIP_MOUNT[1] - 3:STRIP_MOUNT[1] + 3, STRIP_MOUNT[0] - 140:STRIP_MOUNT[0] + 140] = [255, 255, 0]
    Image.fromarray(ov).resize((960, 432)).save(f"{OUT}/check.png")
    geom = {"plate": "commons-schiebetuer", "image_size": [w, h], "unify_grade": unify.__doc__.strip(), "crops": crops,
            "slide_rails": {"y_top": RAIL_Y_TOP, "y_bottom": RAIL_Y_BOT, "left_leaf_x": list(LEAF_L), "right_leaf_x": list(LEAF_R),
                            "travel_px": 235, "direction": "left leaf -x, right leaf +x, in front of the fixed side lights; ease-in-out over E5 (7.0-8.5 s); close after E6"},
            "posts": POSTS, "pillar": list(PILLAR), "threshold_y": RAIL_Y_BOT, "floor_y_range": [702, 865],
            "sensor_strip_mount_centre": list(STRIP_MOUNT), "sensor_strip_scale": 0.5,
            "light": {"plate": "soft overcast daylight from the open front (camera side); no hard shadows in the plate",
                      "computed_long_shadow_dir_img": [0.30, -0.95], "note": "AK17's very long low-sun shadow: cast from behind the camera-left, raking up the floor and onto the glass; length >= 40 % of frame height"},
            "pieces": {k: {"rgba": f"{OUT}/piece_{k}.png", "contour": f"{OUT}/piece_{k}_contour.png", **st[k]} for k in pieces},
            "interior_opening": f"{OUT}/interior_opening.png", "check": f"{OUT}/check.png",
            "bird_height_src_px": [170, 200], "bird_note": "in B (1.0x) 170-200 px = 31-37 %; beak meets the glass at y ~540-570 just left of the meeting stile x 930",
            "dag": {"B": ["plate_B", "interior_opening (where leaves have slid)", "bird (once inside)", "leaf_left/leaf_right (glass: composite the bird behind at 45 % visibility)",
                          "threshold", "bird (outside)", "posts", "pillar", "sensor strip (HANDMADE)", "grain"],
                    "A": ["plate_A", "watcher long cast shadow", "bird_contact_shadow", "bird", "pillar", "grain"]},
            "gaps": ["no steps: the entrance is at grade with a threshold rail; the climb in V3 A becomes a walk-up across the forecourt and a hop over the threshold"]}
    dump(geom, f"{OUT}/geometry.json")
    print(st)


if __name__ == "__main__":
    main()
