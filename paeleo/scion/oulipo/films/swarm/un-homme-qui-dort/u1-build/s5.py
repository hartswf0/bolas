"""S5 FLIGHT-1 (LoC 2017811447, Vachon 1940, 1024 px service JPEG) -> 132 frames; S7 reuses them.
SCION-29: climber cut out whole (cap to coat hem, coat attached) + his flash shadow on the wall as a ratio
plane; rail and balusters cut as the mid plane; wall behind him rebuilt by patch-copy of the plate's own
wallpaper (invented, mask exported). SCION-44: small lateral glide, rail 1.5x wall, figure 1.6x.
SCION-47/E4-E5: enters at 20.5, footfall dips (3 px) at 20.8 21.35 21.9 22.45 23.0, exits 23.5, along
the measured stair line (the stair rises to frame LEFT in this negative, so he enters lower right and
exits upper left)."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *

PID = "2017811447"
CROP = (60, 40, 729, 416)       # 669 x 376 -> 960 x 540 (upscale 1.435 <= 1.6)
g, curve, rec = graded_plate(PID, CROP)
G = g.copy()                    # work in full plate coords (779 x 1024)
Hp, Wp = G.shape

# ---- figure (GrabCut)
rect = (215, 35, 640, Hp)
fg = [[(335, 72), (430, 62), (440, 95), (340, 100)], [(380, 120), (450, 115), (455, 220), (395, 225)],
      [(400, 250), (540, 260), (560, 400), (430, 420)], [(320, 430), (450, 430), (460, 560), (330, 560)],
      [(300, 610), (520, 610), (540, 930), (290, 930)], [(330, 400), (420, 395), (420, 470), (330, 470)],
      [(338, 100), (390, 95), (395, 120), (345, 118)], [(455, 75), (472, 80), (470, 140), (455, 140)]]
bg = [[(48, 18), (330, 18), (330, 60), (360, 110), (360, 280), (300, 290), (48, 290)],
      [(500, 18), (740, 18), (740, 230), (600, 230), (505, 165)],
      [(615, 230), (740, 230), (740, 560), (615, 560)],
      [(48, 300), (205, 420), (205, 975), (48, 975)],
      [(575, 700), (690, 700), (690, 975), (575, 975)], [(572, 545), (690, 545), (690, 700), (585, 700)]]
hard, init = grabcut(G, rect, fg_polys=fg, bg_polys=bg, bg_lines=[[(208, 428), (300, 515)], [(560, 551), (690, 551)]], line_w=5)
fig, fail_fig, st_fig = cleanup(hard, poly_mask(G.shape, fg), max_hole=1500)
# cap brim: its dark underside touches the dark back of the head; add the dark components of the cap
# zone that touch the figure (the colour model left them as background)
cap_zone = poly_mask(G.shape, [[(320, 50), (500, 50), (500, 160), (320, 160)]])
dark = ((G < 0.33) & (cap_zone > 0)).astype(np.uint8)
n_, lab_ = cv2.connectedComponents(dark)
fd = cv2.dilate(fig, np.ones((5, 5), np.uint8))
capadd = np.isin(lab_, [i for i in range(1, n_) if ((lab_ == i) & (fd > 0)).any()]).astype(np.uint8) & (1 - fig)
fig = cv2.morphologyEx(np.clip(fig + capadd, 0, 1).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
st_fig["cap_pixels_added_by_dark_component_rule"] = int(capadd.sum())

# ---- shadow plane: wall pixels right of the figure darker than the local wall lightness
wall = (1 - cv2.dilate(fig, np.ones((5, 5), np.uint8))).astype(np.uint8)
sh_zone = poly_mask(G.shape, [[(470, 200), (620, 220), (625, 538), (470, 538)]])  # above the newel cap
lit = (wall & (1 - sh_zone)).astype(np.float32)
num = cv2.GaussianBlur(G * lit, (0, 0), 20); den = cv2.GaussianBlur(lit, (0, 0), 20)
wall_L = num / np.maximum(den, 1e-4)
ratio = np.clip(G / np.maximum(wall_L, 1e-3), 0, 1)
ratio_s = cv2.GaussianBlur(ratio, (0, 0), 2.0)                      # the flash shadow is soft; carry no pattern
shadow = (sh_zone & wall & (ratio_s < 0.86)).astype(np.uint8)
shadow = cv2.morphologyEx(shadow, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab = cv2.connectedComponents(shadow)
near_fig = cv2.dilate(fig, np.ones((9, 9), np.uint8))
shadow = np.isin(lab, [i for i in range(1, n) if ((lab == i) & near_fig).any()]).astype(np.uint8)
sh_extent = cv2.dilate(shadow, np.ones((7, 7), np.uint8)) & wall
sh_a = feather(sh_extent, 2.0)
sh_r = np.where(sh_extent > 0, ratio_s, 1.0).astype(np.float32)

# ---- mid plane: rail + balusters (GrabCut; seeds on the rail line and on each baluster)
rectR = (44, 270, 240, Hp)
rail_line = [[(44, 292), (205, 425)], [(44, 300), (200, 433)]]
balusters = [[(70, 340), (70, 975)], [(118, 385), (118, 975)], [(165, 420), (165, 975)]]
bgR = [[(48, 150), (210, 150), (210, 270), (48, 270)]]
hardR, _ = grabcut(G, rectR, fg_lines=rail_line + balusters, bg_polys=bgR, line_w=5)
railm, fail_R, st_R = cleanup(hardR, lines_mask(G.shape, rail_line + balusters, 5), max_hole=400)
railm = (railm & (1 - fig)).astype(np.uint8)
rail_a = feather(railm, 0.8)

# ---- rebuilt wall (invented): patch-copy of the plate's own wallpaper under figure + shadow
hole = (cv2.dilate(np.clip(fig + sh_extent, 0, 1).astype(np.uint8), np.ones((9, 9), np.uint8))).astype(np.uint8)
hole[460:, :] = 0                                   # never on screen below the crop (+ glide margin)
hole = (hole & (1 - railm)).astype(np.uint8)
rail_hole = railm.copy(); rail_hole[460:, :] = 0
hole = np.clip(hole + rail_hole, 0, 1).astype(np.uint8)   # wall behind the rail too (the rail plane slides 4 px)
src = np.zeros_like(fig); src[20:560, 48:645] = 1
src = (src & (1 - cv2.dilate(np.clip(fig + sh_extent, 0, 1).astype(np.uint8), np.ones((7, 7), np.uint8))) & (1 - cv2.dilate(railm, np.ones((5, 5), np.uint8)))).astype(np.uint8)
src[:, 600:] &= (G[:, 600:] < 0.93).astype(np.uint8)  # keep the white door casing out
# the damask repeats on a lattice measured by autocorrelation of the bare wall (a=(44,0), b=(68,-72) px):
# every hole pixel takes the wallpaper pixel one lattice step (smallest |offset|) away where the wall is
# visible, lightness-matched by the local wall level. Real wallpaper of this plate, moved by its own period.
LAT_A, LAT_B = np.array([44, 0]), np.array([68, -72])
offs = sorted({(int(i * LAT_A[0] + j * LAT_B[0]), int(i * LAT_A[1] + j * LAT_B[1])) for i in range(-14, 15) for j in range(-7, 8)} - {(0, 0)},
              key=lambda v: v[0] ** 2 + v[1] ** 2)
wall_img = G.copy()
todo = hole.astype(bool).copy()
yy_, xx_ = np.mgrid[0:Hp, 0:Wp]
for ox_, oy_ in offs:
    if not todo.any():
        break
    sy_, sx_ = yy_ + oy_, xx_ + ox_
    inb = (sy_ >= 0) & (sy_ < Hp) & (sx_ >= 48) & (sx_ < 650)
    ok = todo & inb
    ok[ok] = src[sy_[ok], sx_[ok]] > 0
    wall_img[ok] = G[sy_[ok], sx_[ok]] * wall_L[ok] / np.maximum(wall_L[sy_[ok], sx_[ok]], 1e-3) if False else G[sy_[ok], sx_[ok]]
    todo &= ~ok
src_full = src
# the rail plane moves 0.5x the camera relative to the wall: rebuild a thin band behind it too
behind_rail = (cv2.dilate(railm, np.ones((9, 9), np.uint8)) & (1 - railm)).astype(np.uint8)
behind_rail_fill = (railm.copy()); behind_rail_fill[460:, :] = 0


fig_a, unk = matting_band(G, fig, r=3, win=9, blend=0.7)
fig_img = decontaminate(G, fig_a)

M = U1 / "masks"; R_ = U1 / "rgba"; F = U1 / "failure_masks"; I = U1 / "fills"
save_rgba(R_ / "S5_climber_with_coat.png", fig_img, fig_a); save_rgba(R_ / "S5_climber_shadow_ratio.png", sh_r, sh_a)
save_rgba(R_ / "S5_rail_balusters_mid.png", G, rail_a); save_gray(R_ / "S5_wall_rebuilt_far.png", wall_img)
save_mask(M / "S5_climber_mask.png", fig); save_mask(M / "S5_shadow_mask.png", shadow); save_mask(M / "S5_rail_balusters_mask.png", railm)
save_mask(F / "S5_climber_cleanup_changed.png", fail_fig); save_mask(F / "S5_rail_cleanup_changed.png", fail_R)
save_mask(F / "S5_grabcut_init_fg_seeds.png", (init == cv2.GC_FGD).astype(np.uint8))
save_mask(I / "S5_wall_patchcopy_invented.png", hole); 

# ---- rig
s = W / (CROP[2] - CROP[0]); rs = s * SS
org = ((0 - CROP[0]) * s, (0 - CROP[1]) * s)
Rz = lambda a: resample(a.astype(np.float32), rs)
SLOPE = (425 - 292) / (205 - 44)     # measured rail line (plate): rises 0.826 px per px to the left
FPS_ = FPS
T0 = 19.0
F_IN, F_OUT = round(20.5 * FPS) - round(T0 * FPS), round(23.5 * FPS) - round(T0 * FPS)    # 36, 108
FOOT = [round(t * FPS) - round(T0 * FPS) for t in (20.8, 21.35, 21.9, 22.45, 23.0)]
DIP = 3.0


def cam(fi):
    u = fi / 131.0
    return (-8.0 * u, 0.0, 1.0, (0, 0))      # wall travels 8 px; rail 12 px; figure 12.8 px


fig_g, fig_al = Rz(fig_img), Rz(fig_a)
SC = (W * SS, H * SS)


def fig_cov(dxp):
    """screen coverage of the figure (alpha>0.5/255) when shifted dxp plate px along the stair line."""
    M = affine(dxp * s, dxp * SLOPE * s, 0, (0, 0), (0, 0), org)
    a = cv2.warpAffine(fig_al, M, SC, flags=cv2.INTER_LINEAR, borderValue=0)
    return float((a > 0.5 / 255).mean())


def edge(lo, hi):
    """bisection for the shift where coverage goes from 0 (at lo) to >0 (at hi)."""
    for _ in range(30):
        mid = (lo + hi) / 2
        if fig_cov(mid) > 0:
            hi = mid
        else:
            lo = mid
    return lo, hi


# entry: coming from lower right (positive shift); exit: upper left (negative shift).
# camera displacement of the figure plane (k=1.6) is folded in by solving at the actual frame.
k_fig = 1.6
cam_in, cam_out = cam(F_IN)[0] * k_fig / s, cam(F_OUT)[0] * k_fig / s     # in plate px
dx_in = edge(900, 0)[1] - cam_in       # coverage > 0 at hi side ... (searching from outside)
dx_out = edge(-1200, 0)[1] - cam_out


def path(fi):
    """plate shift along the stair line; outside [F_IN, F_OUT] the figure is held off screen."""
    u = (fi - F_IN) / (F_OUT - F_IN)
    dxp = dx_in + (dx_out - dx_in) * u
    if fi < F_IN:
        dxp = dx_in + 200
    if fi >= F_OUT:
        dxp = dx_out - 400
    dip = sum(DIP * max(0.0, 1 - abs(fi - f) / 3.0) for f in FOOT)   # 3 px down at the footfall, recovered in 3 frames
    return dxp * s, dxp * SLOPE * s + dip


def pose_fig(fi):
    dx, dy = path(fi)
    return (dx, dy, 0.0, (0, 0))


layers = [Layer("wall_far", Rz(wall_img), np.ones_like(Rz(wall_img)), 1.0, 0, org=org, role="far: wallpaper + door frame (rebuilt behind him)"),
          Layer("shadow", Rz(sh_r), Rz(sh_a), 1.0, 1, mode="multiply", pose=pose_fig, org=org, role="his flash shadow on the wall (moves with him, on the wall plane)"),
          Layer("rail_mid", Rz(G), Rz(rail_a), 1.5, 2, org=org, role="mid: rail and balusters (on the far side of the stair: he passes in front)"),
          Layer("climber", fig_g, fig_al, k_fig, 3, pose=pose_fig, org=org, role="figure: climber with plaid coat attached")]

if __name__ == "__main__":
    frames = [compose(layers, fi, cam) for fi in range(132)]
    shas, d = write_shot("S5", iter(frames))
    cov = [float((layer_alpha_on_screen(layers[3], fi, cam) > 0.5 / 255).mean()) for fi in range(132)]
    scov = [float((layer_alpha_on_screen(layers[1], fi, cam) > 0.5 / 255).mean()) for fi in range(132)]
    vis = [i for i, c in enumerate(cov) if c > 0]
    out = {"plate": PID, "crop_plate": list(CROP), "scale_plate_to_screen": round(s, 5), "upscale": round(s, 3), "dir": d, "sha1": shas,
           "curve": curve, "curve_table": curve_table(curve),
           "grabcut": {"figure": {"rect_plate": list(rect), "cleanup": st_fig}, "rail": {"rect_plate": list(rectR), "cleanup": st_R}},
           "stair_slope_measured": round(SLOPE, 4), "path_plate_shift": {"enter": round(dx_in, 2), "exit": round(dx_out, 2)},
           "figure_alpha_coverage": [round(c, 5) for c in cov], "shadow_alpha_coverage": [round(c, 5) for c in scov],
           "figure_visible_frames": [vis[0], vis[-1]] if vis else None,
           "events": {"E4_enter_frame": F_IN, "E4_exit_frame": F_OUT, "footfall_frames": FOOT, "dip_px": DIP},
           "head_height_frac": round((230 - 62) / (CROP[3] - CROP[1]), 3),
           "layers": [{"name": L.name, "k": L.k, "z": L.z, "mode": L.mode, "role": L.role} for L in layers],
           "camera_far_dx": [round(cam(fi)[0], 3) for fi in range(132)]}
    dump(U1 / "json" / "s5_render.json", out)
    print("ok visible", out["figure_visible_frames"], "path", out["path_plate_shift"], st_fig, st_R)
    print("shadow visible", [i for i, c in enumerate(scov) if c > 0][:1], [i for i, c in enumerate(scov) if c > 0][-1:])
