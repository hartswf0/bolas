"""Records for pages 46 and 47 (pages 45 and 48 write their own) and the credit bookkeeping for 45-48.
Run after the four page builds: python3 -I rec45_48.py"""
import json
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import ROOT, PAGES_OUT, MASTERS, BEATS, write_record, credit_pages  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
CON = {c["id"]: c for c in CANON["constraints"]}
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SCR = "/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad"


def base(n, pid):
    c = CON[pid]
    jp = PAGES_OUT / f"{n:02d}-{pid}.jpg"
    im = Image.open(jp)
    beats = sorted((BEATS / f"{n:02d}").glob("b*.png"))
    return c, jp, {
        "n": n, "id": pid, "title": c["title"], "rule": c["rule"], "medium": c["medium"], "family": c["family"],
        "canon_revision": CANON["revision"], "declares": c["declares"],
        "file": str(jp.relative_to(ROOT)), "master": str((MASTERS / f"{n:02d}-{pid}.png").relative_to(ROOT)),
        "beats_dir": str((BEATS / f"{n:02d}").relative_to(ROOT)), "lines": LN,
    }, dict(size_px=list(im.size), jpeg_bytes=jp.stat().st_size, jpeg_quality=90,
            in_target_0_4_1_2MB=400000 <= jp.stat().st_size <= 1200000,
            beat_frames=len(beats), beat_size=list(Image.open(beats[0]).size) if beats else None)


# ------------------------------------------------------------------ 46
c, jp, r, chk = base(46, "clock-face")
rec46 = json.load(open(f"{SCR}/p46_rec.json"))
r.update({
    "build": "films/swarm/99-ways/build/p46_clock_face.py (b1m2 cut-paper model; anemic-cinema optics.render_rings)",
    "sources": ["99-ways:handmade", "anemic-cinema:o-a-engraved-ring-disc", "99-ways-template:anrc-gold-key-1922",
                "99-ways-template:loc-blank-sheet-1934"],
    "made": [
        "HANDMADE card clock dial (the LoC 1934 sheet fibre in the card), rim with minute ticks, red hour numerals XII-XI in the shared pen hand",
        "twelve round panels at the hour positions, each an upright print of the b1m2 HANDMADE cut-paper figures in ink (as page 06), the ANRC 1922 key cutout as a brass spot colour; XII the memo ... XI the forgetting",
        "the four c1 lines in cut-paper balloons (III question, V answer, VI thanks, XI forgetting); short pen captions on pasted slips in the other panels",
        "hub: the anemic-cinema O_A engraved eccentric-ring disc (procedural, reused from films/swarm/anemic-cinema/optics.py render_rings, printed in ink), pinned with a red cut-card reading hand pointing at XII",
        "a cut-card pendulum case under the dial with a brass bob; reading directions and an hour key in the pen hand",
        "folio '46 / Clock face' (pen99.folio)"],
    "panels": rec46,
    "events": {"E0": "XII memo (4:15 on the slip), I he gets up, II across the office", "E1": "III question at the window",
               "E2": "IV he looks at the clock (4:10), V 'Ten past four, by the clock.'", "E3": "VI 'Much obliged!', VII she goes",
               "E4": "VIII on to the cupboard, IX he opens it, X the key on its hook (SERVICE tag)",
               "E5": "XI 'Well, here I am... and what for?' before the open cupboard, key unmoved; next comes XII again, the memo"},
    "beat": "the reading performed as the clock: the red reading hand sweeps clockwise from XII through II, IV, VI, VIII, X to XI and on toward XII, the ring disc turning with it and the pendulum swinging; panels not yet reached lie pale",
    "beat_frames": ["b01: hand at XII, only XII read", "b02: hand at II", "b03: hand at IV", "b04: hand at VI", "b05: hand at VIII",
                    "b06: hand at X", "b07: hand at XI, the forgetting read", "b08: hand just short of XII again, all twelve read"],
    "self_check": dict(chk, panels=12, panel_order="clockwise from XII (structurally: panel h placed at angle h*30 deg)",
                       forgetting_at="XI (just before XII)", lines_verbatim=True,
                       check="A reader starts at the top panel and reads clockwise; the forgetting sits just before twelve again (maker's judgement from the full-size page; blind reading pending)",
                       evidence="structurally verified (placement) and perceptually judged (full-size page, beat frames) by the maker"),
    "weaknesses": ["the twelve panels are small (376 px across on a 2200 px page): the cut-paper figures read as silhouettes, details such as the memo slip need a close look",
                   "panels in the lower half are upright, not turned with the dial, so 'round a circle' is a layout of upright pictures, as on a picture clock",
                   "the hub's eccentric rings are decoration plus the turning in the beats; on the still page they do not tell anything"],
})
write_record(r)

# ------------------------------------------------------------------ 47
import p47_floorboard as p47  # noqa: E402
p47.HIPS.clear()
p47.build(7)
c, jp, r, chk = base(47, "floorboard")
r.update({
    "build": "films/swarm/99-ways/build/p47_floorboard.py (b1m2 cut-paper model; p05_noir screen)",
    "sources": ["99-ways:handmade", "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934"],
    "made": [
        "seven lit shadow screens (page 05's screen: lamp hotspot, the LoC 1934 sheet as paper fibre)",
        "HANDMADE floor-level cut paper: a grey floor strip with black board seams converging to a low vanishing point; desk legs and pedestal, a wooden chair from below, a ticket counter on legs open below, the cupboard plinth and its lit inside, the SERVICE door's lower panels with a line of light under it",
        "the agent only as legs: the b1m2 TROUSER outline laid at >=2.05x with HANDMADE laced boots (lace holes and welt cut through); his hip held above every panel's top edge by the rule in legs()",
        "the stranger only as hem, ankles and Louis-heel shoes (HANDMADE), held back from the screen (soft grey) beyond the counter",
        "the clock (b1m2 cut-paper clock at 4:10) high up the wall; the ANRC 1922 key cutout in brass on its hook, seen from below, SERVICE tag",
        "the four c1 lines in balloons whose tails leave the panel top (speakers above the frame); short third-person caption slips",
        "hand-ruled borders; folio '47 / Floorboard' (pen99.folio)"],
    "events": {"P1": "E0 boots and chair legs under the desk; caption: the memo up on the desk, out of sight",
               "P2": "E0 the chair scrapes back, the boots set off", "P3": "E1 beyond the counter her hem; 'Pardon me — have you the right time?' from above",
               "P4": "E2 up the wall the clock at 4:10; 'Ten past four, by the clock.'", "P5": "E3 'Much obliged!'; her shoes turn away",
               "P6": "E4 the cupboard door swings open; high up the key on its hook, seen from below",
               "P7": "E5 'Well, here I am... and what for?'; the boots stand still, the key stays, light under the shut SERVICE door"},
    "beat": "the floor-level reading performed: the seven screens laid one by one, the boots crossing the boards from desk to counter to cupboard while the hem comes and goes beyond the counter",
    "beat_frames": [f"b{i:02d}: panels P1-P{i}" for i in range(1, 8)],
    "self_check": dict(chk, panels=7, hip_y_px_in_panel=[round(h, 1) for h in p47.HIPS], max_hip_y_px=round(max(p47.HIPS), 1),
                       no_torso_or_head_laid=True, faces_on_page=0,
                       check="No figure is seen above the waist (structurally: only trousers and boots of the agent and hem/ankles/shoes of the stranger are laid, every hip y < 0); a reader still retells E0-E5 (maker's judgement from the full-size page and captions; blind reading pending)",
                       evidence="structurally verified (shape roles, hip y) and perceptually judged (full-size page) by the maker"),
    "weaknesses": ["the giant trouser legs are flat black masses; at phone width P1 reads as 'legs under a desk' only with the caption's help",
                   "the memo cannot be seen from the floor, so E0's errand is carried by the caption, not the picture",
                   "the counter, the cupboard frame and the legs are all the same black; overlaps merge where no light falls between them"],
})
write_record(r)

# ------------------------------------------------------------------ credits (locked, additive)
new = [{
    "id": "anemic-cinema:o-a-engraved-ring-disc",
    "title": "O_A engraved eccentric-ring disc (procedural)",
    "author": "anemic-cinema optics unit (made for this production in code: films/swarm/anemic-cinema/optics.py render_rings)",
    "license": "made for this work",
    "source_url": "films/swarm/anemic-cinema/optics.py",
    "used_as": "page 46: the clock dial's hub, printed in ink and turned in the beat frames (no foraged pixels: the ring disc is procedural; the CC BY-SA key cutouts of anemic-cinema are NOT used)",
    "carried_from": "films/swarm/anemic-cinema (no foraged material)",
    "pages": [],
}]
for n in (45, 46, 47, 48):
    rec = json.load(open(ROOT / f"films/swarm/99-ways/pages/{n:02d}.json"))
    credit_pages(rec["sources"], n, new_entries=new)
print("ok")
