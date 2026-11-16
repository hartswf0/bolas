"""Repair 2 acceptance: box bbox centre >= 0.667H at frames 100/600/1000 (from the puppet state), and the box's
noise std and edge sharpness against the plate's own range, measured on frames decoded from the master mp4."""
import sys, json, subprocess, numpy as np, cv2
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois"
sys.path.insert(0, SW)
import present_puppets as PP
MP4 = "/home/user/bolas/paeleo/scion/oulipo/assets/films/monsieur-ripois.mp4"
def grab(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", MP4, "-vf", f"select=eq(n\\,{f})", "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(540, 960)[:, 120:840].astype(np.float32)
def edge_width(prof):
    p = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
    i10 = np.argmax(p > 0.1) if p[0] < p[-1] else np.argmax(p < 0.9)
    i90 = np.argmax(p > 0.9) if p[0] < p[-1] else np.argmax(p < 0.1)
    return abs(int(i90) - int(i10))
out = {}
for f in (100, 600, 1000):
    _, s = PP.render_twoshot(f / 24, None, return_state=True)
    x0, y0, x1, y1 = s["box_bbox_pic"]
    a = grab(f)
    hp = a - cv2.GaussianBlur(a, (0, 0), 1.5)
    bx = hp[y0 + (y1 - y0) // 3: y1 - 6, x0 + 12: x1 - 12]             # box body (inside the silhouette)
    wall = hp[60:110, 560:690]                                           # plain plate wall, upper right
    coat = hp[250:300, 40:120]                                           # her coat
    # edge: box bottom edge vs the top edge of the sofa arm (both horizontal, both on the plate key)
    cx = (x0 + x1) // 2
    pe = edge_width(cv2.GaussianBlur(a, (0, 0), 0.5)[y1 - 8:y1 + 9, cx - 10:cx + 10].mean(1))
    ps = edge_width(cv2.GaussianBlur(a, (0, 0), 0.5)[330:362, 150:190].mean(1))
    out[f] = dict(box_bbox_pic=[x0, y0, x1, y1], centre_y_over_H=round((y0 + y1) / 2 / 540, 3), passes_lower_third=(y0 + y1) / 2 / 540 >= 0.667,
                  noise_std_box=round(float(bx.std()), 2), noise_std_plate_wall=round(float(wall.std()), 2), noise_std_plate_coat=round(float(coat.std()), 2),
                  edge_10_90_px_box=pe, edge_10_90_px_sofa_arm=ps)
json.dump(out, open(SW + "/box-measure.json", "w"), indent=1)
print(json.dumps(out, indent=1))
