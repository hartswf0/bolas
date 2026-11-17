"""U3 · Rotate + scale the GrabCut binturong so it hangs head-down from the tail tip (no mirror, no warp).
Adds a 5 film-px white card margin (the cutout is mounted on card, cut with scissors) and stores the
original-coordinate transform. Output at 2x film resolution (S=2) in imagecue/:
  binturong_hang_rgba.png, binturong_hang_matte.png (engraving matte), binturong_hang_card.png (card matte),
  binturong_hang.json (transform: source px -> sprite px, anchor, sizes)
"""
import numpy as np, cv2, json, math
from PIL import Image
D = "/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/imagecue/"
S = 2
TAIL_TIP = (620.0, 654.0)    # end of the tail curl (source px), placed by eye on the 20 px grid
NOSE = (222.0, 1128.0)       # nose tip (source px)
TARGET_H = 300               # film px, total card height incl. margin (plan: <= 300)
MARGIN = 5                   # film px of white card around the engraving
info = json.load(open(D + "binturong_cut.json"))
ox, oy = info["crop_origin"]
crop = np.array(Image.open(D + "binturong_src_crop.png").convert("RGB"))
fg = (np.array(Image.open(D + "binturong_src_matte.png")) > 127).astype(np.uint8) * 255
tip = (TAIL_TIP[0] - ox, TAIL_TIP[1] - oy); nose = (NOSE[0] - ox, NOSE[1] - oy)
v = (nose[0] - tip[0], nose[1] - tip[1])
ang = math.degrees(math.atan2(v[1], v[0]))        # image angle (y down)
# Chosen by search (u3 log): nose-vertical (rot 40 deg) made the card 216 px wide and pushed it off the right edge.
# 24 deg CCW keeps the head lowest-left (head-down, tilted), the card inside x 770..950 and lets it be 261 px tall.
ROT_CCW = 24.0
FILM_SCALE = 0.214           # film px per source px
rot_ccw = ROT_CCW
def build(scale):
    M = cv2.getRotationMatrix2D(tip, rot_ccw, scale)
    # where does everything land?
    h, w = fg.shape
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], float) @ M.T
    pad = MARGIN * S * 3
    x0, y0 = corners[:, 0].min() - pad, corners[:, 1].min() - pad
    W2, H2 = int(corners[:, 0].max() - x0 + pad), int(corners[:, 1].max() - y0 + pad)
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    R = cv2.warpAffine(crop, M2, (W2, H2), flags=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    A = cv2.warpAffine(fg, M2, (W2, H2), flags=cv2.INTER_LINEAR)
    return M2, R, A
# scale so the card (matte + margin) is TARGET_H*S tall
scale = FILM_SCALE * S
M2, R, A = build(scale)
ys, xs = np.nonzero(A > 127)
pad = MARGIN * S * 3
x0, x1, y0, y1 = xs.min() - pad, xs.max() + pad, ys.min() - pad, ys.max() + pad
R = R[y0:y1, x0:x1]; A = A[y0:y1, x0:x1]; M2[0, 2] -= x0; M2[1, 2] -= y0
anchor = M2 @ np.array([tip[0], tip[1], 1.0])
# scissor-cut white card margin: dilate the matte by MARGIN film px, with a slight hand wobble
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * MARGIN * S + 1, 2 * MARGIN * S + 1))
card = cv2.dilate(A, k)
rs = np.random.RandomState(265)
wob = cv2.GaussianBlur(rs.randn(*card.shape).astype(np.float32), (0, 0), 9) * 40
card = (cv2.GaussianBlur(card.astype(np.float32), (0, 0), 3.0) + wob > 127).astype(np.float32)
card = cv2.GaussianBlur(card, (0, 0), 0.7)              # anti-aliased scissor edge
a_eng = cv2.GaussianBlur(A.astype(np.float32) / 255, (0, 0), 0.8)[..., None]
CARD = np.array([251, 250, 247], np.float32)             # white card stock, a hair warmer than the field
rgb = R.astype(np.float32) * a_eng + CARD * (1 - a_eng)
# lit cut edge of the card (light from upper left): brighten the up-left rim, darken the low-right rim slightly
gy, gx = np.gradient(cv2.GaussianBlur(card, (0, 0), 1.2))
lit = (-gx * 0.55 - gy * 0.83)
rgb += (np.clip(lit, 0, None) * 30)[..., None] - (np.clip(-lit, 0, None) * 55)[..., None]
out = np.dstack([np.clip(rgb, 0, 255), card * 255]).astype(np.uint8)
Image.fromarray(out, "RGBA").save(D + "binturong_hang_rgba.png")
Image.fromarray(A).save(D + "binturong_hang_matte.png")
Image.fromarray((card * 255).astype(np.uint8)).save(D + "binturong_hang_card.png")
json.dump(dict(scale_film_px_per_source_px=scale / S, sprite_scale_2x=scale, rotation_ccw_deg=rot_ccw,
               mirrored=False, warped=False, tail_tip_source_px=TAIL_TIP, nose_source_px=NOSE,
               anchor_sprite_px_2x=[float(anchor[0]), float(anchor[1])], sprite_size_2x=[out.shape[1], out.shape[0]],
               card_height_film_px=float(card.shape[0] / S), margin_film_px=MARGIN,
               affine_source_crop_to_sprite_2x=M2.tolist(), crop_origin_source_px=[ox, oy]),
          open(D + "binturong_hang.json", "w"), indent=1)
print("rot", rot_ccw, "scale", scale, "size", out.shape, "anchor", anchor)
