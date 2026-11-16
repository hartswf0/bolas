"""Step 7 (editor): plan §9.6 numeric test on the DELIVERED pixels (decoded out/master.mp4, frame 96 = 4.0 s), using the
picture unit's region masks (picture/aesthetic.py), plus out/side-by-side.jpg (reference | 4.0 s | 21.0 s, same height)."""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SW, "picture"))
import maquette as M   # noqa: E402
import aesthetic as AE  # noqa: E402

RAW = os.path.join(SW, "..", "..", "sources", "la-cite-raymond-queneau", "editor", "master.rgb24")
MF = np.memmap(RAW, np.uint8, "r", shape=(720, 464, 960, 3))
_model_frame = M.frame
M.frame = lambda k: Image.fromarray(np.asarray(MF[k]))     # decoded master instead of the model render

res = AE.check(96)
res["source"] = "decoded out/master.mp4 (yuv420p -> rgb24 by ffmpeg), frame 96; masks from picture/aesthetic.py"
res["model_render_result"] = json.load(open(os.path.join(SW, "picture", "aesthetic-check.json"))).get("tests")
json.dump(res, open(os.path.join(SW, "out", "aesthetic-check.json"), "w"), indent=1)
print(json.dumps({k: res[k] for k in ("sky_median", "facade_cream_median", "roof_median", "roof_luma", "luma_p2_p50_p98", "mean_saturation", "passed")}))

ref = Image.open(AE.REF).convert("RGB")
h = 464
ref = ref.resize((int(ref.width * h / ref.height), h), Image.LANCZOS)
a, b = M.frame(96), M.frame(504)
gap = 12
sheet = Image.new("RGB", (ref.width + 2 * (960 + gap), h), (243, 239, 228))
sheet.paste(ref, (0, 0)); sheet.paste(a, (ref.width + gap, 0)); sheet.paste(b, (ref.width + 2 * gap + 960, 0))
sheet = sheet.resize((sheet.width // 2, h // 2), Image.LANCZOS)
sheet.save(os.path.join(SW, "out", "side-by-side.jpg"), quality=90)
