"""verify_assembly.py -- editor checks on the RENDERED film assets/films/les-lieux-dune-fugue.mp4.

Decodes frames and audio with ffmpeg only, then:
  * silence: every decoded sample from 44.0 s to the end is 0 (and the longest zero run);
  * compare_P01.jpg + compare_metrics.json regenerated from final-render frames (0:03, 0:38.5)
    against assets/references/fugue1.webp, with plan sec. 9.5 acceptance;
  * I1 on the render: stone edge maps of 0:02 vs 0:29 within 1 px; P03 plate 27.9 vs 48.0;
  * I5 on the render: memory plane cold, stone warm;
  * U2's stage tests (paper_stage.task_tests) re-run, written to assembly_stage_tests.json;
  * caption timing: captions present/absent in rendered frames at window edges.
Writes assembly_checks.json.
"""
import json, os, subprocess, sys, shutil, tempfile
import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/user/bolas/paeleo/scion/oulipo"
MP4 = ROOT + "/assets/films/les-lieux-dune-fugue.mp4"
REF = ROOT + "/assets/references/fugue1.webp"
sys.path.insert(0, HERE)
import paper_stage as PS  # noqa


def frame(t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(out, np.uint8).reshape(720, 960, 3))


def audio():
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", MP4, "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "44100",
                          "-ac", "2", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).reshape(-1, 2)


res = {}
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", MP4],
                                  capture_output=True, check=True).stdout)
res["file"] = dict(duration_s=float(probe["format"]["duration"]), size_mb=round(os.path.getsize(MP4) / 1e6, 3),
                   streams=[(s["codec_type"], s.get("width"), s.get("height"), s.get("r_frame_rate")) for s in probe["streams"]])

# ---- silence
pcm = audio()
R = 44100
i0 = int(44.0 * R)
tail = pcm[i0:]
nz = np.nonzero(np.abs(pcm).max(1))[0]
last_nz = float(nz[nz < i0].max() / R) if (nz < i0).any() else None
res["silence"] = dict(window=[44.0, round(len(pcm) / R, 3)], samples=int(len(tail)), all_zero=bool(not np.any(tail)),
                      seconds=round(len(tail) / R, 3), nonzero_samples_after_44=int(np.count_nonzero(np.abs(tail).max(1))),
                      last_nonzero_before_44_s=last_nz, peak_dbfs=round(float(20 * np.log10(max(np.abs(pcm).max(), 1) / 32768)), 2))
res["silence"]["pass_ge_6s"] = res["silence"]["all_zero"] and res["silence"]["seconds"] >= 6.0
# bell window: rms in 32-41 vs 28-31
def rms(a, b):
    x = pcm[int(a * R):int(b * R)].astype(float)
    return round(float(20 * np.log10(np.sqrt((x ** 2).mean()) / 32768 + 1e-12)), 1)
res["audio_rms_db"] = {f"{a}-{b}": rms(a, b) for a, b in [(0, 8), (8, 19), (19, 28), (28, 31), (32, 41), (41, 44)]}

# ---- compare sheet from the final render
ref = Image.open(REF).convert("RGB")
f1, f4 = frame(3.0), frame(38.5)
hh = 480
ims = [ref.resize((int(ref.width * hh / ref.height), hh)), f1.resize((640, 480)), f4.resize((640, 480))]
sheet = Image.new("RGB", (sum(i.width for i in ims) + 20, hh + 28), (20, 18, 16))
d = ImageDraw.Draw(sheet); x = 0
for im, lab in zip(ims, ["REFERENCE fugue1.webp (INA still)", "FINAL RENDER 0:03  P01 prise A matin",
                         "FINAL RENDER 0:38.5  P01 prise B, open"]):
    sheet.paste(im, (x, 28)); d.text((x + 6, 8), lab, fill=(200, 190, 170), font=PS.fnt("rec")); x += im.width + 10
sheet.save(HERE + "/compare_P01.jpg", quality=90)
m1 = PS.measure(f1)
cm = dict(source="final render assets/films/les-lieux-dune-fugue.mp4 (decoded with ffmpeg; captions burnt in where on screen)",
          reference_plan_sec6=dict(frame_mean=[89, 78, 57], lum_p5=19, lum_p50=89, lum_p95=149, stone_mean=[122, 104, 69], stone_sd=12,
                                   jamb_mean=[127, 108, 72], door_mean=[21, 19, 21], door_sd=2, plinth_mean=[148, 137, 121],
                                   balcony_mean=[47, 39, 26], joint_row_min=84, stone_row_median=98),
          reference_measured_same_regions=PS.measure(ref), final_t3=m1, final_t29_closed=PS.measure(frame(29.0)),
          final_t38_5_open=PS.measure(f4),
          regions="stone x .62-.98 y .28-.80; door x .16-.50 y .40-.95; plinth x .62-.98 y .88-.99; right jamb x .565-.605; balcony y 0-.06",
          note="0:03 carries caption F1 over the plinth/door bottom; the door region y .40-.95 includes part of it")
cm["acceptance_5"] = dict(stone_within_18=bool(all(abs(a - b) <= 18 for a, b in zip(m1["stone_mean"], (122, 104, 69)))),
                          stone_R_minus_B_ge_35=m1["stone_R_minus_B"] >= 35, door_lum_le_35=m1["door_lum"] <= 35,
                          p95_le_175=m1["lum_p95"] <= 175, p5_ge_8=m1["lum_p5"] >= 8, joint_le_30=m1["joint_darkness"] <= 30)
cm["acceptance_5"]["pass"] = all(cm["acceptance_5"].values())
json.dump(cm, open(HERE + "/compare_metrics.json", "w"), indent=1)
res["tone_acceptance_5"] = cm["acceptance_5"]


# ---- I1 on the render
def edges(im):
    L = PS.lum(np.asarray(im).astype(np.float32) / 255)
    hp = L - cv2.GaussianBlur(L, (0, 0), 3)
    return cv2.Canny(PS.to8(np.clip(0.5 + hp * 4, 0, 1)), 60, 140) > 0
fa, fb = frame(2.0), frame(29.0)
ea, eb = edges(fa), edges(fb)
roi = np.zeros_like(ea); roi[int(720 * .2):int(720 * .84), int(960 * .6):] = True
dta = cv2.distanceTransform((~ea).astype(np.uint8), cv2.DIST_L2, 3)
dtb = cv2.distanceTransform((~eb).astype(np.uint8), cv2.DIST_L2, 3)
p3a, p3b = np.asarray(frame(27.9)).astype(float), np.asarray(frame(48.0)).astype(float)
crop = (slice(40, 600), slice(0, 960))   # below the slate, above the caption zone
res["I1_render"] = dict(stone_edges_A_in_B_within_1px=round(float((dtb[ea & roi] <= 1).mean()), 3),
                        stone_edges_B_in_A_within_1px=round(float((dta[eb & roi] <= 1).mean()), 3),
                        p03_plate_27_9_vs_48_0_mean_abs_diff=round(float(np.abs(p3a[crop] - p3b[crop]).mean()), 3),
                        note="mp4 (crf 28) frames; P03 diff measured on y 40-600 (slates differ, caption F3 gone by 27.9)")
# shadow direction swap A vs B: brightness just left vs right of the right jamb
st = np.asarray(fb).astype(float)
f4o = np.asarray(f4).astype(float)
mem = f4o[300:560, 290:400]; ston = f4o[200:560, 640:940]
res["I5_render"] = dict(memory_mean_rgb=mem.reshape(-1, 3).mean(0).round(1).tolist(), memory_B_ge_R=bool(mem[..., 2].mean() >= mem[..., 0].mean()),
                        stone_R_minus_B=round(float(ston[..., 0].mean() - ston[..., 2].mean()), 1))
res["I5_render"]["pass"] = res["I5_render"]["memory_B_ge_R"] and res["I5_render"]["stone_R_minus_B"] >= 35

# ---- defining beat on the render: door region darkness closed vs open, distinct leaf drawings
door_box = (slice(300, 680), slice(130, 520))
seq = [np.asarray(frame(31.0 + k / 12)).astype(np.float32)[door_box].mean() for k in range(0, 60)]
res["beat_render"] = dict(door_region_mean_31_to_36=[round(float(v), 1) for v in seq[::6]],
                          distinct_door_drawings_31_to_36=int(len(set(np.round(seq, 1)))),
                          door_mean_43_9=round(float(np.asarray(frame(43.9)).astype(np.float32)[door_box].mean()), 1),
                          door_mean_29=round(float(np.asarray(frame(29.0)).astype(np.float32)[door_box].mean()), 1))

# ---- captions visible where scheduled (bright cream pixels in the caption zone)
def cap_px(t):
    a = np.asarray(frame(t)).astype(int)[620:700, 60:900]
    return int(((a[..., 0] > 215) & (a[..., 1] > 205) & (a[..., 2] > 170)).sum())
res["captions_render"] = {f"{t}": cap_px(t) for t in (0.5, 3.0, 7.5, 12.0, 17.0, 23.0, 27.5, 29.5, 33.0, 38.5, 42.0, 48.0)}

# ---- U2 stage tests re-run (write to a scratch dir, then copy under a new name)
tmp = tempfile.mkdtemp()
PS.OUT = tmp
os.makedirs(tmp, exist_ok=True)
st_res = PS.task_tests()
shutil.copy(tmp + "/stage_tests.json", HERE + "/assembly_stage_tests.json")
res["stage_tests"] = dict(I9_pass=st_res["I9_pass"], I1=dict((k, v) for k, v in st_res["I1"].items() if k != "shadow_offset_example"),
                          I5_pass=st_res["I5"]["pass"], shot4=st_res["I9_shot4"], shot1=st_res["I9_shot1"])

json.dump(res, open(HERE + "/assembly_checks.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
