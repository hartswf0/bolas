"""S2 TELEPHONE (LoC 2017735081, Russell Lee 1936, archival TIFF 8a21346a.tif, 16-bit, on disk from r1).
SCION-29: coats cut as the near plane (GrabCut + matting band on the fur collar).
SCION-44: push 1.00 -> 1.04 on the wall/phone, coats scale twice as much (k = 2). Nothing touches the phone."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *

PID = "2017735081"
CROP = (230, 560, 3530, 2416)    # 3300 x 1856 -> 960 x 540 (scale 0.2909)
REG = (150, 480, 3620, 2500)
TH = 4.309                        # thumbnail (1000 px) -> plate
g, curve, rec = graded_plate(PID, CROP)
x0, y0, x1, y1 = REG
G = g[y0:y1, x0:x1].copy(); o = (x0, y0)
def T(pts):   # thumbnail coords -> region coords
    return [(x * TH - x0, y * TH - y0) for x, y in pts]

rect = (int(262 * TH - x0), int(200 * TH - y0), x1 - x0, y1 - y0)
fg = [T([(310, 320), (420, 300), (430, 600), (320, 620)]), T([(450, 300), (540, 290), (550, 620), (460, 620)]),
      T([(580, 230), (700, 230), (710, 370), (590, 380)]), T([(600, 420), (720, 420), (720, 600), (600, 600)]),
      T([(745, 240), (820, 240), (820, 400), (745, 400)]), T([(760, 450), (819, 450), (819, 560), (760, 560)])]
bg = [T([(300, 188), (835, 188), (835, 205), (300, 205)]),              # rack board top edge
      T([(80, 175), (300, 175), (300, 535), (80, 535)]),                # phone box and its shelf
      T([(35, 540), (262, 540), (262, 665), (35, 665)]),                # wall under the phone
      T([(300, 205), (345, 205), (345, 235), (300, 235)]),
      T([(545, 205), (565, 205), (565, 225), (545, 225)])]
hard, init = grabcut(G, rect, fg_polys=fg, bg_polys=bg)
coats, fail, st = cleanup(hard, poly_mask(G.shape, fg), max_hole=5000)
fur_band = T([(550, 195), (745, 195), (745, 430), (550, 430)])
alpha, unk = matting_band(G, coats, band_poly=fur_band, r=7, blend=0.85)
alpha = np.where(poly_mask(G.shape, fur_band) > 0, alpha, feather(coats, 1.0))
coat_img = decontaminate(G, alpha)
far = G  # coats only grow over the wall during the push: nothing behind them is revealed, no fill needed

save_rgba(U1 / "rgba" / "S2_coats_near.png", coat_img, alpha, o)
save_gray(U1 / "rgba" / "S2_far_wall_phone.png", far)
save_mask(U1 / "masks" / "S2_coats_mask.png", coats); save_mask(U1 / "masks" / "S2_fur_matting_band.png", unk)
save_mask(U1 / "failure_masks" / "S2_coats_cleanup_changed.png", fail)
save_mask(U1 / "failure_masks" / "S2_grabcut_init_fg_seeds.png", (init == cv2.GC_FGD).astype(np.uint8))

s = W / (CROP[2] - CROP[0]); rs = s * SS
org = ((x0 - CROP[0]) * s, (y0 - CROP[1]) * s)
R = lambda a: resample(a.astype(np.float32), rs)
ZC = (W / 2, H / 2)
layers = [Layer("wall_phone_far", R(far), np.ones_like(R(far)), 1.0, 0, org=org, role="far: wall, crank telephone, directory"),
          Layer("coats_near", R(coat_img), R(alpha), 2.0, 1, org=org, role="near: hanging coats (shield; drift 2x the wall)")]


def cam(fi):
    u = fi / 71.0
    u = u * u * (3 - 2 * u)
    return (0.0, 0.0, 1.0 + 0.04 * u, ZC)


if __name__ == "__main__":
    shas, d = write_shot("S2", (compose(layers, fi, cam) for fi in range(72)))
    phone_h = (530 - 175) * TH
    out = {"plate": PID, "crop_plate": list(CROP), "region_plate": list(REG), "scale_plate_to_screen": round(s, 5), "dir": d, "sha1": shas,
           "curve": curve, "curve_table": curve_table(curve), "grabcut": {"rect_plate": [rect[0] + x0, rect[1] + y0, rect[2] + x0, rect[3] + y0], "cleanup": st},
           "phone_box_height_frac": round(phone_h / (CROP[3] - CROP[1]), 3),
           "layers": [{"name": L.name, "k": L.k, "z": L.z, "role": L.role} for L in layers],
           "push": {"far_scale": [1.0, 1.04], "near_scale": [1.0, 1.08], "zoom_center_screen": ZC, "ease": "smoothstep over 72 frames"},
           "invented_fill": "none (the coats only expand over the wall)"}
    dump(U1 / "json" / "s2_render.json", out)
    print("ok", out["phone_box_height_frac"], st)
