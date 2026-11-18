"""Re-adopt puppets/art-layers.png as strip/strip-art.png and rebuild every U1 output
that depends on it: sheet.json (sha256 only; geometry is frozen), fixture.json,
seam-100x.png, strip-flat/folded.png, second-fold.json, the A3 page (.png/.pdf) and
the editor media in films/sources/les-caids-de-la-gaudriole/paper-engineer-writer/.
Run: python3 strip/rebuild.py
"""
import os, sys, shutil, subprocess, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "../../../sources/les-caids-de-la-gaudriole/paper-engineer-writer"))


def run(s):
    subprocess.run([sys.executable, os.path.join(HERE, s)], check=True, cwd=HERE, stdout=subprocess.DEVNULL)


def media():
    sys.path.insert(0, HERE)
    import fold as F
    art = np.asarray(Image.open(os.path.join(HERE, "strip-art.png")).convert("L"))
    pap = np.asarray(Image.open(os.path.join(SRC, "paper-front-4800x1800.png")), np.float32)
    for name, arr in [("flat", art), ("folded", F.folded_view(art))]:
        h, w = arr.shape
        big = np.asarray(Image.fromarray(arr).resize((w * 2, h * 2), Image.LANCZOS), np.float32)
        rgb = pap[:h * 2, :w * 2] * (1 - 0.92 * (1 - big / 255)[..., None])
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(SRC, f"strip-{name}-on-paper-2x.png"))
    st = F.lightbox_stack(art)
    for i, L in enumerate(st["layers"]):
        Image.fromarray(L).save(os.path.join(SRC, f"lightbox-layer{i + 1}.png"))
    np.save(os.path.join(SRC, "lightbox-masks.npy"), np.stack(st["masks"]))


if __name__ == "__main__":
    shutil.copyfile(os.path.join(HERE, "../puppets/art-layers.png"), os.path.join(HERE, "strip-art.png"))
    for s in ["sheet_build.py", "fixture.py", "second_fold.py", "page.py"]:
        run(s)
    media()
    # page strip vs art: resampled diff (B5)
    import cv2
    lay = json.load(open(os.path.join(HERE, "page-layout.json")))
    art = np.asarray(Image.open(os.path.join(HERE, "strip-art.png")).convert("L"))
    pg = Image.open(lay["page"]).convert("L")
    x, y = lay["strip_origin_px"]; w, h = lay["strip_size_px"]
    c = np.asarray(pg.crop((x, y, x + w, y + h)).resize((art.shape[1], art.shape[0]), Image.LANCZOS), float)
    inkp = np.clip(1 - c / np.percentile(c, 90), 0, 1) / 0.92
    inka = 1 - art / 255.0
    xor = (inkp > 0.5) != (inka > 0.5)
    edge = cv2.dilate(cv2.Canny((inka * 255).astype(np.uint8), 50, 150), np.ones((3, 3))) > 0
    lay["resampled_diff"] = dict(page_strip_vs_art_ink_mask_xor_fraction=float(xor.mean()), xor_off_edges=int((xor & ~edge).sum()),
                                 note="page strip resampled back to 2400x900 u, paper divided out; mismatches on 1-u anti-aliased edges are resampling")
    json.dump(lay, open(os.path.join(HERE, "page-layout.json"), "w"), indent=1)
    fx = json.load(open(os.path.join(HERE, "fixture.json")))
    print("strip-art sha256", fx["strip_art_sha256"], "fixture pass_all", fx["pass_all"])
