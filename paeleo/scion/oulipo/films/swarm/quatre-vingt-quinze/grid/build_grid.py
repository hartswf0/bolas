"""Build U1's outputs: page_scaffold.png, registry.json, proof sheets and editor layers."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid as G  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = G.SRC
ED = G.FILMS / "sources" / "quatre-vingt-quinze" / "story-grid-letterer"
ED.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(img, p):
    img.save(p, optimize=True)
    return {"path": str(Path(p).relative_to(G.OULIPO)), "sha256": sha(p), "size": list(img.size)}


out = {}
# 1 the scaffold (everything except figures, props and plates), neutral, both rails
page = G.compose_page()
out["page_scaffold"] = save(page, HERE / "page_scaffold.png")

# 2 editor layers
lay = {}
for c in G.CELLS:
    lay[f"ground_{c}"] = save(G.ground(c), ED / f"ground_{c}.png")
    lay[f"lettering_{c}"] = save(G.lettering(c), ED / f"lettering_{c}.png")
    lay[f"overlay_{c}"] = save(G.cell_overlay(c).resize((G.CW, G.CH), Image.LANCZOS), ED / f"overlay_{c}.png")
lay["paper"] = save(G.paper_sheet(), ED / "paper_sheet.png")
lay["page_base"] = save(G.page_base(), ED / "page_base.png")
for name, u in (("neutral", G.U_NEUTRAL), ("across", G.U_ACROSS), ("down", G.U_DOWN)):
    lay[f"marks_{name}"] = save(G.marks_layer([u] * 8), ED / f"marks_{name}.png")
for rail in ("both", "across", "down"):
    lay[f"rails_{rail}"] = save(G.rails_layer(rail), ED / f"rails_{rail}.png")
lay["title_page"] = save(G.title_layer(), ED / "title_page.png")
lay["title_upright"] = save(G.title_layer({i: 0 for i in range(40)}), ED / "title_upright.png")
lay["bottom_line"] = save(G.bottom_layer(), ED / "bottom_line.png")
f = G._furniture_layer()
lay["furniture"] = save(f.resize((G.PW, G.PH), Image.LANCZOS), ED / "furniture.png")
out["editor_layers"] = lay

# 3 proof sheets: marks in every state, turn drawings, arrow, alphabet, title turn
W = 1600
sheet = Image.new("RGB", (W, 700), G.PAPER)
d = ImageDraw.Draw(sheet, "RGBA")
big = Image.new("RGBA", (W * 2, 700 * 2), (0, 0, 0, 0))
bd = ImageDraw.Draw(big, "RGBA")
labels = [("across u=0", 0.0), ("turn 1/3", 1 / 3), ("neutral 0.5", 0.5), ("turn 2/3", 2 / 3), ("down u=1", 1.0)]
for i, (lab, u) in enumerate(labels):
    G.mark_drawing(bd, 160 + i * 300, 180, u, seed=0)
    G.letter(bd, lab.upper().replace("/", "-").replace("=", " "), 160 + i * 300, 320, 26, 4, G.INK, seed=i)
for k in (0, 1):
    G.arrow_drawing(bd, 300 + k * 400, 480, 0, k, seed=3)
    G.arrow_drawing(bd, 1100 + k * 300, 480, 90, k, seed=3)
G.letter(bd, "ARROW DRAWINGS 0 1 (RIGHT, DOWN)", 800, 640, 28, 4, G.INK, seed=9)
big = big.resize((W, 700), Image.LANCZOS)
sheet.paste(big, (0, 0), big)
out["marks_sheet"] = save(sheet, SRC / "marks_states.png")

alpha = Image.new("RGBA", (2400 * 2, 900 * 2), (0, 0, 0, 0))
ad = ImageDraw.Draw(alpha, "RGBA")
rows = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "ÉÈÊÀÇ 0123456789", "! ? . , ' - ( ) : — ·", "C'EST POUR MOI ? UNE CLÉ ? MÊME FIN : I."]
for i, r in enumerate(rows):
    G.letter(ad, r, 1200, 130 + i * 140, 80, 12, G.INK, seed=500 + i, track=0.30)
G.letter(ad, "quatre-vingt-quinze  en bas  en travers", 1200, 830, 80, 14, G.INK, seed=600, lower=True, pen=(0.42, 0.58), blob=False, dot=0.48)
a = Image.new("RGB", (2400, 900), G.PAPER)
alpha = alpha.resize((2400, 900), Image.LANCZOS)
a.paste(alpha, (0, 0), alpha)
out["alphabet_sheet"] = save(a, SRC / "alphabet.png")

tt = Image.new("RGB", (G.PW, 300 * 5), G.PAPER)
for k in range(5):
    t = G.title_layer({i: k for i in range(40)}).crop((0, 0, G.PW, 300))
    tt.paste(t, (0, 300 * k), t)
out["title_turn_sheet"] = save(tt.resize((G.PW // 2, 750), Image.LANCZOS), SRC / "title_turn.png")

json.dump(out, open(SRC / "build_manifest.json", "w"), indent=1)
print(json.dumps({k: v if k != "editor_layers" else len(v) for k, v in out.items()}, indent=1))
