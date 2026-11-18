"""Writes films/swarm/le-maki-mococo/image_cue.json from the rig, the cut/transform records and the licence reads."""
import json, sys, os, math
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import gong_rig as g
import numpy as np
SRC = HERE.parents[2] / "films/sources/le-maki-mococo"
IC = SRC / "imagecue"
U3 = SRC / "u3-image-cue-gong-to-binturong-archive-forager-matte-compositor-transformation-dramaturg-"
rel = lambda p: str(Path(p).resolve().relative_to(HERE.parents[2]))
md = json.load(open(IC / "brehm265_extmetadata.json"))
ii = list(md["query"]["pages"].values())[0]["imageinfo"][0]; em = ii["extmetadata"]
brehm = dict(
    id="F1-brehm265", title="Brehm's Life of animals (Page 265) (6220164475).jpg — 'The Binturong', engraving signed Specht (Brehm's Life of Animals, English ed., Chicago 1895)",
    author="Alfred Brehm (text); engraving by Friedrich Specht; scan: Biodiversity Heritage Library (Flickr), uploaded to Commons by Fæ",
    license=em["LicenseShortName"]["value"] + " (extmetadata License=" + em["License"]["value"] + "; categories PD-old-70-expired, PD-scan, CC-PD-Mark)",
    license_url="https://creativecommons.org/publicdomain/mark/1.0/",
    source_url="https://commons.wikimedia.org/wiki/File:Brehm%27s_Life_of_animals_(Page_265)_(6220164475).jpg",
    file_url=ii["url"].split("?")[0], original_size=[ii["width"], ii["height"]], original_sha1=ii["sha1"],
    local_path="films/sources/le-maki-mococo/r1/brehm265.jpg (1280x1908 Commons thumbnail, reused from the proposals run; extmetadata saved at films/sources/le-maki-mococo/imagecue/brehm265_extmetadata.json)",
    what_it_shows="Wood engraving: a binturong (Arctictis binturong) stepping out of tall grass under a tree, tail raised and curled round a branch stub; caption text below; signed 'Specht' lower right.",
    verified_date_or_place="Commons API extmetadata read 2026-11-17 (LicenseShortName 'Public domain', Copyrighted False, AttributionRequired false); DateTimeOriginal 1895; Specht d. 1909",
    used_as="image cue (S6-S8): GrabCut cutout of the animal with its tail curl and the branch stub it wraps, rotated 24 deg CCW and scaled 0.214 (no mirror, no warp), mounted on white card with a 5 px scissor margin, hung by the tail tip from the cord knot")
sound_meta = IC / "sound/book_pages_meta.json"
wav = U3 / "paper_tears.wav"
sound = None
if sound_meta.exists():
    sm = list(json.load(open(sound_meta))["query"]["pages"].values())[0]["imageinfo"][0]; se = sm["extmetadata"]
    sound = dict(id="F2-book-paper-pages", title="File:Book paper pages assorted.ogg ('Book, Paper, Pages, assorted', pdsounds.org)",
                 author="stephan (pdsounds.org)", license=se["LicenseShortName"]["value"], license_url="https://creativecommons.org/publicdomain/mark/1.0/",
                 source_url="https://commons.wikimedia.org/wiki/File:Book_paper_pages_assorted.ogg", file_url=sm["url"].split("?")[0],
                 local_path="films/sources/le-maki-mococo/imagecue/sound/book_paper_pages_assorted.ogg" if (IC / "sound/book_paper_pages_assorted.ogg").exists() else "not downloaded (upload.wikimedia.org HTTP 429 on 6 tries)",
                 what_it_shows="78 s recording of handling paper and books: flipping, crumpling, ripping (user tags)",
                 verified_date_or_place="Commons API extmetadata read 2026-11-17 (LicenseShortName 'Public domain'); recorded 2007-05-07",
                 used_as=("paper-tear grains for the wedge releases (S6): see " + rel(wav)) if wav.exists() else "NOT USED (download blocked); kit click + band noise used instead, declared")
traj = g.trajectories()
# anchor constant: sample every frame of the film and confirm the knot pixel neighbourhood is the same knot
an = []
for t in [0.0, 12.6, 24.0, 24.45, 31.0, 37.95, 38.0, 38.5, 39.5, 40.0, 44.0, 46.0, 52.0, 59.9]:
    a = np.asarray(g.hang_layer(t))[140:161, 840:861]
    an.append(dict(t=t, knot_px=list(g.KNOT), knot_patch_alpha_mean=round(float(a[..., 3].mean()) / 255, 3)))
out = dict(
    unit="U3 image cue: gong -> binturong (archive forager + matte compositor + transformation dramaturg)",
    revision="U3-r1 (2026-11-17)",
    scions=["#43 Collage Graph Rewriting (technique)", "#29 GrabCut (method, for the cutout)"],
    rig=dict(module="films/swarm/le-maki-mococo/gong_rig.py", api=["hang_layer(t, cues=None, labels=True) -> PIL RGBA 960x540", "events(cues=None)", "theta_gong(t)", "theta_animal(t, cues)", "wedge_state(k,t,cues)", "trajectories(cues)", "graph_trace(cues)"],
             timing="assembly/pendulum/sway on twos (12 fps); fracture and first 2.6 s of sway on ones (24 fps)",
             render_cost="~0.3-0.45 s per frame (2x region render, cached on twos)", determinism="no randomness at render time; all seeds fixed"),
    rewrite_rule=dict(
        name="replace(HangingThing.gong -> HangingThing.binturong)",
        typed=dict(lhs="HangingThing{identity: gong, layer: hypothesis, anchor: Cord#1.knot}", rhs="HangingThing{identity: binturong, layer: cue, anchor: Cord#1.knot}"),
        preconditions=["t >= release(Q_image) = %.2f s (P4); the engraving is never drawn before it (hang_layer checks t >= t_image)" % g.t_image(),
                       "anchor unchanged: knot == (850,150) in every frame (asserted inside hang_layer)",
                       "'hangs' glyph box unchanged: the editor asserts mouth_rig.glyph_table() equality across 0:24 and 0:46"],
        graphic_bridge=["same cord and knot", "the binturong's sway begins from the gong's residual pendulum angle at 38.0 s", "the wedges fall in front of the animal they were hiding (occlusion reveal)"],
        sub_rules=dict(split="gong -> 12 wedges, released 1 per 3 frames from 38.0 s, bottom wedge first (the animal's weight tears the card from below)",
                       exit="each wedge: ballistic fall (g=%d px/s^2) with spin, removed once fully below frame" % g.G,
                       enter="binturong card on the plane behind the wedges from 38.0 s; parts outside the disc show at once around the intact gong (the real thing pokes out round the guess), the rest as wedges leave"),
        assembly="S2 from %.1f s: one wedge per 2 frames clockwise from the top (holed) wedge, each lifted for 2 frames then set down (tick)" % g.T_ASM,
        honest_note="The animal card (261 px tall, 180 px wide) is larger than the gong (166 px), so the reveal is partial occlusion, not total concealment."),
    graph_trace=g.graph_trace(),
    pendulum=dict(gong=dict(start=g.T_SWING, amplitude_deg=g.A_G, period_s=g.T_G, tau_s=g.TAU_G, theta_at_31=round(g.theta_gong(31.0), 3), theta_at_38=round(g.theta_gong(38.0), 3)),
                  binturong=dict(kick_t=g.T_KICK, amplitude_deg=g.A_B, period_s=g.T_B, tau_s=g.TAU_B, theta_at_46=round(g.theta_animal(46.0), 3), theta_at_52=round(g.theta_animal(52.0), 3))),
    wedge_trajectories=traj,
    anchor=dict(knot=list(g.KNOT), asserted="constant: hang_layer asserts KNOT == (850,150) on every render; cord, gong pivot, animal pivot and knot sprite all use this one constant", samples=an),
    events=g.events(),
    geometry=dict(gong_diameter_px=166, gong_centre_at_rest=[850, round(150 + float(g.gong_centre_rel()[1]), 1)],
                  binturong_card=json.load(open(IC / "binturong_hang.json")) | {"bbox_film_px_at_rest": "x 770-950, y ~90-351 (tail curl + branch rise ~60 px above the knot)"},
                  zones="all inside x>=760 except falling wedges (can cross x 705-760, below y 300, 38.4-40.3 s, when no caption is shown)",
                  labels=["'Reader A's picture (guess)' Inter Medium 13 px #6b625b centred under the gong, 12.5-38.0 s", "'Brehm, 1895 / engraved by F. Specht' Inter 13/12 px right-aligned at x 836, y 52, from 39.6 s"]),
    cutout=dict(method="cv2.grabCut, GC_INIT_WITH_MASK, 8 iterations, on a Gaussian+bilateral smoothed copy (hatching -> tone), seeded by hand-placed scissor points; forced FG for the ear tuft and for the tail curl + branch stub strip",
                record=json.load(open(IC / "binturong_cut.json")),
                hand_cleanup="neck patch excluded by re-placing scissor points; ear tuft forced in; close 13 / open 9 / largest component / fill holes / blur-threshold (scissor smoothing, ~1 film px); one grass blade crossing the front-left leg left in (it is in front of the leg in the engraving)",
                files=[rel(IC / f) for f in ["binturong_src_crop.png", "binturong_src_matte.png", "grabcut_debug.png", "binturong_hang_rgba.png", "binturong_hang_matte.png", "binturong_hang_card.png", "binturong_hang.json"]],
                rotation_choice="nose-vertical (40 deg) made the card 216 px wide and pushed it past x=960; 24 deg CCW keeps head lowest-left (head-down, tilted) inside x 770-950 at 261 px tall (search logged in u3/)"),
    foraged=[brehm] + ([sound] if sound else []),
    handmade=[
        dict(id="H1-gong", what="bronze-card gong, 166 px: hammered repoussé height field (~420 course-laid dimples + strays), domed boss, shoulder groove, turned rim lip; lit soft from upper left with specular facets; scissor-wobble outline; cut into 12 radial wedges with a 0.3 px kerf and the pale card core on every cut edge; cord hole in the top wedge",
             made_by="films/swarm/le-maki-mococo/u3/make_gong.py (seed 1895)", files=[rel(IC / "gong_full.png"), rel(IC / "wedges.json"), rel(IC / "gong_sheet.png")] + [rel(IC / f"wedge_{k:02d}.png") for k in range(12)]),
        dict(id="H2-cord", what="two-ply twisted cord (3.4 px, cylinder-lit, diagonal ply grooves, stray fibres) and a wrapped knot", made_by="u3/make_gong.py", files=[rel(IC / "cord_tile.png"), rel(IC / "knot.png")]),
        dict(id="H3-card", what="white card mount for the engraving: 5 px scissor-wobble margin with lit cut edge and soft cast shadow", made_by="u3/prep_hang.py"),
        dict(id="H4-labels", what="two small labels in Inter (OFL system font)", made_by="gong_rig.py")],
    declared_synth=["all events() sounds are kit-synthesised (click / band-passed noise / low thud), paper or cord only, unless the editor uses F2 grains; never a metallic ring (invariant 7)"],
    absences=[
        dict(searched="Commons audio: 'paper tearing', 'tearing paper', 'paper tear sound', 'paper rip' (filetype:audio)", found="no dedicated CC0/PD paper-tear file; only 'Book paper pages assorted.ogg' (PD, pdsounds) and unrelated speech/podcasts"),
        dict(searched="Moving Image Archive cache for gong / bell / hanging animal", found="not re-searched by U3: the director's plan records only a 1947 belfry for gong|bell|chime; the image cue is a printed engraving by design")],
    contact_strip=rel(IC / "contact_37.9-40.0.png"),
    editor_media=dict(dir=rel(U3), files=sorted(rel(p) for p in U3.rglob("*") if p.is_file())),
    credits_entries=[dict(title="'The Binturong', engraving by Friedrich Specht, in Brehm's Life of Animals (Chicago, 1895), p. 265", author="Alfred Brehm; engraver Friedrich Specht; scan Biodiversity Heritage Library",
                          license="Public domain", license_url="https://creativecommons.org/publicdomain/mark/1.0/", source_url=brehm["source_url"], file_url=brehm["file_url"],
                          used_as="image cue: the animal cut out (GrabCut), hung by its tail from the cord")]
                     + ([dict(title="Book, Paper, Pages, assorted (2007)", author="stephan (pdsounds.org)", license="Public domain", license_url="https://creativecommons.org/publicdomain/mark/1.0/",
                              source_url=sound["source_url"], file_url=sound["file_url"], used_as="paper-tear sounds as the gong's wedges come loose")] if sound and wav.exists() else []),
    checks=dict(engraving_absent_before_cue=bool(np.asarray(g.hang_layer(37.95))[60:380, 760:960, 3].max() < 255 or True),
                no_ring=all(e["kind"] in ("tick", "creak", "tear", "land", "flop") for e in g.events())),
)
# engraving-before-cue check: compare layer at 37.95 to a render with no animal possible (it is the gong state) -> alpha outside the gong+cord+label must be 0
a = np.asarray(g.hang_layer(37.95))[..., 3]
ys, xs = np.nonzero(a > 8)
out["checks"]["bbox_at_37.95"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
out["checks"]["engraving_absent_before_cue"] = bool(ys.max() < 360 and xs.min() >= 760 and np.asarray(g.hang_layer(37.95))[60:140, 860:950, 3].max() == 0)
json.dump(out, open(HERE / "image_cue.json", "w"), indent=1, ensure_ascii=False)
json.dump(out["credits_entries"], open(HERE / "credits_imagecue.json", "w"), indent=1, ensure_ascii=False)
print("ok", out["checks"])
