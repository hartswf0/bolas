# writes films/swarm/la-mort-en-ce-jardin/interruption.json (and sound.json) from the rendered layer, cut and stems.
import os, json, math, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.abspath(os.path.join(HERE, ".."))
O = os.path.abspath(os.path.join(HERE, "..", "..", "..", "sources", "la-mort-en-ce-jardin", "object-sound"))
SRC = os.path.dirname(O)
lf = json.load(open(f"{O}/layer_frames.json"))
cues = json.load(open(f"{O}/stems/cues.json"))
cut_bar = json.load(open(f"{O}/cut/bar1280_cut.json")); cut_ox = json.load(open(f"{O}/cut/ox1280_cut.json"))
have = cues["have"]

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

# retrieval geometry against U2's traces
retr = {}
for v, off, t0 in (("L", 336, 14.0), ("E", 168, 7.0)):
    fr = json.load(open(f"{SW}/performance/trace-{v}.json"))["frames"]
    occ = []
    for k in range(115, 135):
        f = fr[off + k]; h = f["people"]["B"]["hands"]["R"]; dy = round(f["water_y"] - 408)
        c = lf["frames"][k]["centre_layer"]
        occ.append(dict(k=k, local_t=round(t0 + k / 24, 4), hand_R=h,
                        hand_card_box=[round(h[0] - 16, 1), round(h[1] - 16, 1), round(h[0] + 16, 1), round(h[1] + 16, 1)],
                        shoe_centre=[c[0], round(c[1] + dy, 2)], dist_px=round(math.dist(h, (c[0], c[1] + dy)), 1)))
    dys = [round(fr[off + k]["water_y"] - 408) for k in range(150)]
    retr[v] = dict(first_appearance_local=t0, trace_frames=[off, off + 149], paste_dy_px_per_k=dys,
                   contact_local=round(t0 + 86 / 24, 4), grasp_local=round(t0 + 135 / 24, 4),
                   hand_shoe_dist_at_retrieve_px=occ[-1]["dist_px"], occlusion=occ)

ev = lambda **k: k
foraged = [
    ev(id="FOR-SHOE-LACMA-51.47.2", title="Pair of Woman's Bar Shoes (Wedding), LACMA 51.47.2a-b (United States, 1892)",
       author="Los Angeles County Museum of Art (museum photograph; no author field on Commons)", license="Public domain",
       license_url="", source_url="https://commons.wikimedia.org/wiki/File:Pair_of_Woman%27s_Bar_Shoes_(Wedding)_LACMA_51.47.2a-b.jpg",
       file_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Pair_of_Woman%27s_Bar_Shoes_%28Wedding%29_LACMA_51.47.2a-b.jpg/1280px-Pair_of_Woman%27s_Bar_Shoes_%28Wedding%29_LACMA_51.47.2a-b.jpg",
       local_path=f"{SRC}/shoe_lacma_bar.jpg (1280x985, Commons thumbnail of the 2100x1616 original) -> cut {O}/cut/shoe_bar_white.png",
       what_it_shows="a pair of white suede/kid bar-strap wedding shoes with silk-gauze rosettes on a neutral grey museum ground; the right shoe in profile",
       verified_date_or_place="Commons extmetadata re-read live 2026-11-16 (this unit): LicenseShortName 'Public domain', License 'pd', UsageTerms 'Public domain', Copyrighted 'False'; object dated 1892 (meta/shoes.json)",
       used_as="the interruption: right shoe GrabCut-cut, strap kept, neutral 'immaculate white' curve; SHOE-DRIFT-1 layer (150 frames) and the shoe held in B's hand"),
    ev(id="FOR-SHOE-LACMA-M.83.156.1", title="Pair of Woman's Oxford Shoes (Wedding), LACMA M.83.156.1a-b (United States, c. 1890)",
       author="Los Angeles County Museum of Art (museum photograph)", license="Public domain", license_url="",
       source_url="https://commons.wikimedia.org/wiki/File:Pair_of_Woman%27s_Oxford_Shoes_(Wedding)_LACMA_M.83.156.1a-b.jpg",
       file_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Pair_of_Woman%27s_Oxford_Shoes_%28Wedding%29_LACMA_M.83.156.1a-b.jpg/1280px-Pair_of_Woman%27s_Oxford_Shoes_%28Wedding%29_LACMA_M.83.156.1a-b.jpg",
       local_path=f"{SRC}/shoe_lacma_oxford.jpg (1280x998) -> cut {O}/cut/shoe_oxford_white.png",
       what_it_shows="a pair of satin lace-up wedding oxfords with beaded floral embroidery, grey museum ground; right shoe in profile",
       verified_date_or_place="Commons extmetadata re-read live 2026-11-16: LicenseShortName 'Public domain', License 'pd', Copyrighted 'False'; object c. 1890",
       used_as="plan section 11 second-object test only: stills of the same retrieval with the oxford substituted"),
    ev(id="FOR-AUD-STREAM", title="433589 jackthemurray stream-river-water-up-close", author="jackthemurray (via Freesound)",
       license="CC0", license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
       source_url="https://commons.wikimedia.org/wiki/File:433589_jackthemurray_stream-river-water-up-close.wav",
       file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/5/54/433589_jackthemurray_stream-river-water-up-close.wav/433589_jackthemurray_stream-river-water-up-close.wav.mp3",
       local_path=f"{SRC}/test-shot/audio/stream.mp3 (reused from the test shot) -> {O}/stems/water.wav",
       what_it_shows="soft close stream flowing (field recording, 68.9 s); listened to via spectrum/periodicity check: steady broadband water, no voices",
       verified_date_or_place="Commons extmetadata re-read live 2026-11-16 (meta/aud.json): LicenseShortName 'CC0'",
       used_as="water bed for the whole film (12.0-42.0 s of the recording, looped with crossfades), louder in the late crossings"),
]
pending = dict(
    jungle=ev(id="FOR-AUD-JUNGLE", title="Jungle Sound Thailand Phuket", author="Amada44", license="CC BY-SA 3.0",
              license_url="https://creativecommons.org/licenses/by-sa/3.0", source_url="https://commons.wikimedia.org/wiki/File:Jungle_Sound_Thailand_Phuket.flac",
              file_url="https://upload.wikimedia.org/wikipedia/commons/3/3a/Jungle_Sound_Thailand_Phuket.flac", local_path=f"{O}/raw/jungle_phuket.flac",
              what_it_shows="rainforest ambience (insects, birds), Phuket, 48 s", verified_date_or_place="Commons extmetadata 2026-11-16: CC BY-SA 3.0",
              used_as="jungle/insect bed (3-43 s looped), cut to silence at film 21.4-22.0 and 51.9-52.5"),
    cicadas=ev(id="FOR-AUD-CICADAS", title="Cicadas in Greece", author="Channel R", license="Public domain", license_url="",
               source_url="https://commons.wikimedia.org/wiki/File:Cicadas_in_Greece.ogg", file_url="https://upload.wikimedia.org/wikipedia/commons/f/f4/Cicadas_in_Greece.ogg",
               local_path=f"{O}/raw/cicadas_greece.ogg", what_it_shows="a tree full of cicadas, Stavros, Ithaca, July 2008, 27.8 s",
               verified_date_or_place="Commons extmetadata 2026-11-16: Public domain", used_as="insect layer under the jungle bed"),
    tide=ev(id="FOR-AUD-TIDE", title="Water over rocks as tide recedes", author="earthcalling", license="Public domain", license_url="",
            source_url="https://commons.wikimedia.org/wiki/File:Water_over_rocks_as_tide_recedes.ogg", file_url="https://upload.wikimedia.org/wikipedia/commons/6/60/Water_over_rocks_as_tide_recedes.ogg",
            local_path=f"{O}/raw/tide_rocks.ogg", what_it_shows="water lapping and draining over rocks, 30.4 s", verified_date_or_place="Commons extmetadata 2026-11-16: Public domain",
            used_as="close lapping at the plank foot in L-S5 and E-S4"),
    splash=ev(id="FOR-AUD-SPLASH", title="Bathtub water splashes", author="gradha", license="Public domain", license_url="",
              source_url="https://commons.wikimedia.org/wiki/File:Bathtub_water_splashes.ogg", file_url="https://upload.wikimedia.org/wikipedia/commons/8/83/Bathtub_water_splashes.ogg",
              local_path=f"{O}/raw/splashes.ogg", what_it_shows="hand splashes in water, 48 s", verified_date_or_place="Commons extmetadata 2026-11-16: Public domain",
              used_as="splash on the last crosser's shins (L film 34.x, E film 66.x)"),
)
absences = [
    dict(searched="movingimagearchive cache, clips with source sound: 'water|river|stream|rapids|flood|swamp|jungle|creek|waterfall|rain|lake|splash|forest|insect|bird|frog|marsh|bayou' (title + archive queries), then every clip of audio kind 'sound' scanned for low periodicity (spectral flatness / autocorrelation)",
         result="no usable natural water or jungle ambience: hits carry narration or music (e.g. Water 1953, Blackwater NWR 2005, Shock Troops of Disaster 1938) or are 2-8 s fragments / tape hiss (The Unique Contribution 1959); none adopted"),
    dict(searched="Commons audio: 'insects night ambience', 'frogs swamp' (only spring peepers, temperate), 'cicadas', 'jungle sounds', 'rainforest ambience', 'water lapping', 'splash water'",
         result="licence-clean candidates found and verified (above). Download from upload.wikimedia.org was refused with HTTP 429 Retry-After 600 for the whole unit (also blocked the 2100 px shoe originals)" if not any(have[k] for k in ("jungle", "cicadas", "tide", "splash")) else "downloaded (see foraged)"),
    dict(searched="LACMA shoe originals at 2100 px (bar 755 KB, oxford 795 KB)", result="HTTP 429 from upload.wikimedia.org; the 1280 px Commons thumbnails already in sources/ (same files) were used; shoe renders <= 150 px wide on screen, so 1280 px (762 px shoe crop) is ample (downscale only)"),
]
for k, rec in pending.items():
    if have.get(k): foraged.append(rec)
    else: absences.append(dict(searched=f"{rec['title']} ({rec['license']}, verified)", result=f"not downloaded (HTTP 429); stand-in: {'synthesized' if k != 'tide' else 'synthesized low lap'}; rerun object-sound/sound.py once {rec['local_path']} exists"))

handmade = [
    dict(id="HM-SHOE-CUT", what="GrabCut cutout of the right bar shoe (#29): rect + chroma seeds (neutral grey ground and cast shadow = background, warm satin/kid/sole = foreground), 5 graph-cut iterations, largest component, speckle holes filled, the ground under the arch kept open, brown sole edge regrown, 1 px erosion, inpainted edge decontamination, 0.8 px feather; then one neutral monotone curve (p2/p50/p99.5 -> L105/218/246, R=G=B)",
         where=f"{O}/cut/shoe_bar_white.png (762x564), diagnostics bar1280_fail.png (red = warm pixels removed, blue = neutral kept), bar1280_cut.json", stats=cut_bar),
    dict(id="HM-SHOE-OXFORD-CUT", what="same pipeline for the oxford (all enclosed holes filled: satin highlights read as ground)", where=f"{O}/cut/shoe_oxford_white.png", stats=cut_ox),
    dict(id="HM-SHOE-DRIFT-1", what="the interruption layer: 150 RGBA frames at 24 fps rendered at 3x (layer_hi, world strip x -20..880, y 340..470) and area-downsampled to the wide 800x540 layer; Catmull-Rom drift from frame right (880,403) through (640,398) (430,406) to the grasp point x 237.34, arc-length parametrised, eased so it arrives still moving (u = 1.6s - 0.6s^2); bob +-3 px / 0.9 s; pitch rock 2.5 deg; contact at k 86 = a damped recoil (4 px, 1.6 Hz, tau 0.35 s) and pitch kick (#41: starts after the impulse, all energy decays); the hand's approach dips and stills the bob (k 115-134); reflection mirrored about the waterline, darkened, alpha-faded, re-rippled every frame by two travelling row-shift waves and broken by ripple troughs; broken ripple rings (12 dashes with seeded gaps, bright crest L205 over dark trough L40, aspect 0.13) born at bob troughs, at contact (3), at the hand entering the water (2), at the lift (2), and 3 drips; V wake while drifting; submerged 22 % tinted toward the water; above water immaculate white (no mud, ever: invariant 5)",
         where=f"{O}/layer/shoe_000..149.png, {O}/layer_hi/shoe_hi_000..149.png, {O}/layer_frames.json; code {HERE}/render_layer.py"),
    dict(id="HM-SYN-FOLEY", what="kit.Mix synthesis (declared): plank creak = stick-slip impulse train 38->85 Hz through wood modes 182/413/737/1210 Hz, scaled by plank deflection, one per plank footfall (footfalls = end of each ankle's forward swing in U2's traces); wood step thump 96/231 Hz; mud step on the banks; shoe tap = heel knock with rebound 105 ms, hollow 520 Hz body, plip; card rustle = crackle grains 1.2-7 kHz + bag landing 105 Hz; pencil writing = stroke-enveloped graphite noise 2.2-8 kHz; strike-through = one 0.33 s scratch 1.2-6.5 kHz; liana fibre creak at each grip; drips (plips) at layer k 139/143/148",
         where=f"{HERE}/sound.py -> {O}/stems/foley.wav"),
]
if not have.get("jungle") and not have.get("cicadas"):
    handmade.append(dict(id="HM-SYN-INSECTS", what="FALLBACK insect bed synthesized with kit.Mix (three AM noise-band voices 3.1/4.3/5.65 kHz + sparse chirps), -38 dBFS RMS, with the declared silences", where=f"{O}/stems/jungle.wav"))
if not have.get("tide"): handmade.append(dict(id="HM-SYN-LAP", what="fallback close lap: band-limited noise 150-900 Hz", where=f"{O}/stems/water.wav"))
if not have.get("splash"): handmade.append(dict(id="HM-SYN-SPLASH", what="fallback splash: noise 200-5000 Hz, exp decay", where=f"{O}/stems/foley.wav"))

hashes = lf["hashes"]
out = dict(
    slug="la-mort-en-ce-jardin", unit="U3 object & sound (SCION #29 GrabCut; #45 occlusion, #41 secondary dynamics as methods)", revision="os-r1", date="2026-11-16",
    shoe=dict(source="FOR-SHOE-LACMA-51.47.2", cut=f"{O}/cut/shoe_bar_white.png",
              note_for_editor="replace test-shot SHOE_FULL (old cut with a cast-shadow halo trimmed by hand) with this cut for the held shoe; draw it with the same rotation logic"),
    layer=dict(id="SHOE-DRIFT-1", frames=150, fps=24, duration_s=6.25,
               wide=f"{O}/layer/shoe_%03d.png", wide_size=[800, 540], hi=f"{O}/layer_hi/shoe_hi_%03d.png", hi_scale=3, hi_world_origin=[-20, 340], hi_size=[2700, 390],
               coords="P2 plane, wide framing, picture px, y down. Paste frame k at (0, dy) with dy = round(water_y(v, t) - 408) (per-frame list in retrieval.*.paste_dy_px_per_k); for a close at zoom Z map world->screen and scale the hi frame by Z/3 (<=1, downscale only)",
               layer_waterline_y=408, shoe_float_line_y=424, note="the shoe floats 16 px in front of the plank on the water plane (clearly separated from the plank and from B's face; never overlaps the bank card)",
               path=dict(type="Catmull-Rom, arc-length", points=[[880, 403], [850, 404], [640, 398], [430, 406], [237.34, 405]], arrive_k=86, arrive_s=3.6,
                         ease="u = 1.6 s - 0.6 s^2, s = t/3.6 (arrives with 0.4 of entry speed)"),
               bob=dict(amp_px=3, period_s=0.9), contact=dict(k=86, t_rel=3.6, L_local=17.6, E_local=10.6, L_film=19.6, E_film=50.1, response="recoil 4 px damped 1.6 Hz tau 0.35 s + 6 deg pitch kick"),
               hand_occlusion=dict(k=[115, 134], L_local=[18.79, 19.58], E_local=[11.79, 12.58],
                                   rule="#45 occlusion DAG: water < reflection < rings < shoe(submerged) < shoe(above water) < B's hand card. The editor draws B's R hand card ABOVE the layer for k 115-134; from k 135 (L 19.625 local / E 12.625) the shoe is absent from the layer and parented to B's hand (FK). No pop: the held shoe's first frame is drawn at the hand where the layer's last shoe frame was (dist <= 18.4 px).",
                                   region_world_px="per frame hand_card_box in retrieval.L/E.occlusion (hand R point +-16 px); union x 199.6-257.0, y 351.4-420.4"),
               grasp=dict(k=135, L_local=19.625, E_local=12.625), after_grasp="k 135-149: ripple burst of the lift and three drip rings (k 139, 143, 148), no shoe",
               identity=dict(rule="L uses k = round((local - 14.0)*24), E uses k = round((local - 7.0)*24): the same files; E is the L layer shifted -7.0 s (168 frames)",
                             L_trace_frames=[336, 485], E_trace_frames=[168, 317], hash_algorithm="sha256 of the PNG bytes and of the raw RGBA array",
                             all_hashes_distinct_frames=len(set(h['rgba_sha256'] for h in hashes))),
               per_frame=[dict(k=f["k"], L_local=f["L_local"], E_local=f["E_local"], shoe_visible=f["shoe_visible"], centre_layer=f["centre_layer"],
                               png_sha256=h["png_sha256"], rgba_sha256=h["rgba_sha256"], hi_rgba_sha256=h["hi_rgba_sha256"]) for f, h in zip(lf["frames"], hashes)]),
    retrieval=retr,
    second_object=dict(plan="section 11", object="FOR-SHOE-LACMA-M.83.156.1", stills=[f"{O}/stills/second-object-{n}-{t:05.2f}.png" for n in ("bar", "oxford") for t in (19.25, 19.62, 20.2)],
                       compare=f"{O}/stills/second-object-compare.jpg", method="U2's render_ls5.frame() at L local 19.25 (reach), 19.62 (grasp), 20.2 (held at chest) with only the shoe image swapped (second_object.py); same affordance (graspable, one hand), different social reading (laced, beaded: harder to wear, more ornamental)",
                       note="in these stills the floating shoe is still U2's approximate shoe_on_water (it sits on the plank line); in the film the SHOE-DRIFT-1 layer replaces it"),
    sound=dict(cue_list=f"{O}/stems/cues.json", stems={k: f"{O}/stems/{k}.wav" for k in ("water", "jungle", "foley", "mix")},
               format="44.1 kHz stereo 16-bit WAV, 73.0 s film timeline (L local + 2.0, E local + 39.5)", have_foraged=have, used=cues["used"], checks=cues["check"],
               key_cues=[c for c in cues["cues"] if c["source"] not in ("HM-SYN-CREAK", "HM-SYN-MUD")],
               footfalls=dict(n=sum(1 for c in cues["cues"] if c["source"] in ("HM-SYN-CREAK", "HM-SYN-MUD")), note="all in cues.json; derived from U2's traces (end of each ankle's forward swing), so they stay frame-locked if the traces are rebuilt: rerun sound.py"),
               declared_silence=[dict(film=[21.4, 22.0], version="L", local=[19.4, 20.0]), dict(film=[51.9, 52.5], version="E", local=[12.4, 13.0], note="the same local window in E (added for equivalence; drop it if the editor wants the silence in L only)")]),
    foraged=foraged, handmade=handmade, absences=absences,
    code=dict(cut=f"{HERE}/cut_shoe.py", whiten=f"{HERE}/whiten.py", layer=f"{HERE}/render_layer.py", sound=f"{HERE}/sound.py", second_object=f"{HERE}/second_object.py", json=f"{HERE}/build_json.py"),
)
json.dump(out, open(f"{SW}/interruption.json", "w"), indent=1, ensure_ascii=False)
json.dump(dict(cue_list=cues["cues"], stems=out["sound"]["stems"], foraged=[f for f in foraged if f["id"].startswith("FOR-AUD")], absences=absences, have=have, used=cues["used"]),
          open(f"{SW}/sound.json", "w"), indent=1, ensure_ascii=False)
print("ok", len(foraged), len(absences), out["layer"]["identity"]["all_hashes_distinct_frames"])
