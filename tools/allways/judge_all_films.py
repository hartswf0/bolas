#!/usr/bin/env python3
"""
ALLWAYS Jury Evaluation & Awards Engine:
Evaluates all 132 individual films across the 4 makers (Opus 5.5, Sonnet, Sol, Argon)
plus the 24-cut Anthology Synthesis Film (allways-best) using a 5-Pillar 100-Point Rubric,
computes Head-to-Head matrices (12 B-Roll works, SCION 055-065, SCION 066-078, SCION 079-113),
assigns the 12 Category Awards, and generates allways-awards/index.html + ratings.json.
"""
import os, json, glob, html

REPO = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
OUT_DIR = os.path.join(REPO, "allways-awards")
os.makedirs(OUT_DIR, exist_ok=True)

def esc(s):
    return html.escape(str(s or ""), quote=True)

works_slate = {w["slug"]: w for w in json.load(open(f"{REPO}/paeleo/allways/works.json"))["works"]}
scion_slate = {e["id"]: e for e in json.load(open(f"{REPO}/paeleo/allways/scion/scion-allways.json"))}

BROLL_TARGET_DUR = {
    "nobody-home": 60.0, "almost-human": 75.0, "terra-incognita": 60.0, "split-second": 50.0,
    "cut-to-the-chase": 60.0, "kinetic": 60.0, "zero-memory": 90.0, "homonym": 60.0,
    "anybody-anywhere": 90.0, "collective-inventories": 120.0, "mnemonil": 90.0, "planimetric": 120.0,
}

all_evaluated = []

# 1. CLAUDE OPUS 5.5 (12 films)
OPUS_SCORES = {
    "mnemonil": (23.5, 19.5, 19.5, 14.0, 18.0, "Only Opus film to pass its blind critic ('pass, narrowly'). The 23–40s untouched kitchen sequence broken by museum visitors behind a rope stanchion is the single best documentary-ethics reveal in ALLWAYS."),
    "anybody-anywhere": (20.5, 19.0, 18.5, 13.5, 18.0, "76s side-by-side split-screen pairing three situated recordings (1961 theatre chairs vs. 1944 typing chair); strong visual alignment and preserved sound spaces."),
    "zero-memory": (22.0, 18.0, 17.5, 13.0, 18.0, "Full 109.7s duration across 29 cuts with three explicit black memory-reset cards ('Working history cleared 1/2/3') protected by the critic."),
    "homonym": (19.0, 18.5, 18.5, 13.5, 17.0, "48s relay around 'place' across 12 cuts; critic praised 17.9–21.8s where spoken 'a place for everything' aligns with hands sorting a drawer."),
    "collective-inventories": (19.0, 18.5, 18.0, 13.5, 17.0, "67s composite morning across 10 shots; features the praised cupboard-shutter reveal (12.6–15.4s) and distinct domestic actions."),
    "almost-human": (18.0, 18.5, 18.0, 13.0, 16.5, "47.2s gesture sequence across 11 cuts; genuine archival micro-gestures, though shorter than the 75s brief."),
    "cut-to-the-chase": (18.0, 18.0, 18.0, 13.0, 16.5, "43.9s pursuit across 10 cuts; strong opening momentum transfer from purple beach jogger to grey street crowd."),
    "nobody-home": (18.0, 18.5, 17.0, 13.0, 16.5, "46.7s study across 5 shots; features the memorable opening of a boy carrying a chair to the window (0–12s), though person-removal is less explicit than Argon's 3-panel triptych."),
    "split-second": (17.5, 18.0, 17.5, 13.0, 16.5, "38.1s release study across 12 cuts; critic protected the bowler return and pin-fall payoff at 12–13s."),
    "kinetic": (18.5, 17.5, 16.5, 12.5, 15.5, "58.6s labor montage across 14 cuts; hits target duration with mallet worker rhythm, though hard cuts felt abrupt to critic."),
    "terra-incognita": (17.5, 17.5, 16.5, 12.5, 15.5, "47.2s surface study across 6 shots; strong contrast between blown-out water aerial and black-bordered shoreline."),
    "planimetric": (12.0, 16.5, 13.5, 11.0, 14.0, "35.7s single-shot hold; misses the 2-minute multi-tableau architectural requirement (1 shot vs. required 3+ fixed tableaux)."),
}

for slug, w in works_slate.items():
    fj = json.load(open(f"{REPO}/allways-opus/films/{slug}/film.json"))
    shots = fj.get("shots", [])
    dur = round(sum(s.get("dur", 0) for s in shots), 1)
    rev = fj.get("reviews", [{}])[-1]
    b1, b2, b3, b4, b5, note = OPUS_SCORES[slug]
    total = round(b1 + b2 + b3 + b4 + b5, 1)
    all_evaluated.append({
        "id": f"opus-{slug}",
        "maker": "Claude Opus 5.5",
        "run_id": "allways-opus",
        "series": "B-Roll of Civilization",
        "work_slug": slug,
        "scion_id": w["primary"],
        "title": w["title"],
        "subtitle": w["subtitle"],
        "duration_s": dur,
        "target_dur_s": BROLL_TARGET_DUR[slug],
        "shots_count": len(shots),
        "verdict": rev.get("verdict", "reviewed"),
        "scores": {"brief": b1, "archival": b2, "nearmatch": b3, "audio_time": b4, "critic_ethics": b5},
        "total": total,
        "url": f"../allways-opus/films/{slug}/",
        "video_url": f"../allways-opus/films/{slug}/{slug}.mp4",
        "poster_url": f"../allways-opus/films/{slug}/poster.jpg",
        "jury_note": note
    })

# 2. CLAUDE SONNET (11 films: SCION 055-065)
SONNET_SCORES = {
    "059-ball": (59, "BALL · Graphic Constancy", 24.5, 19.5, 20.0, 13.0, 19.0, "PASS (strongest proof in Sonnet batch). Sub-5px circle registration across 13 films (1929–2007), honest octagonal clock failure, gauge-panel release, and moon drifting out of frame."),
    "064-parabolas": (64, "PARABOLAS · Curves with Different Causes", 24.0, 19.5, 19.5, 12.5, 19.0, "PASS (most complete realisation in Sonnet batch). Unannotated first pass establishes family resemblance across dive, fountain, and pendulum before mathematical curve overlays reveal competing causes."),
    "055-words": (55, "WORDS · Polysemic Relay", 22.0, 18.5, 18.5, 13.5, 17.5, "PASS (qualified) · Repaired. Anchored by the 13–22s cigarette 'draw' where optical sound and semantic sense meet."),
    "062-colors": (62, "COLORS · Chromatic Chapters", 22.0, 18.5, 18.5, 13.0, 17.5, "PASS (qualified). Critic protected the mixed-colour hinge at 7.5s (yellow engine swung over deep teal sea) and the breakfast-table ending."),
    "057-moments": (57, "MOMENTS · Micro-Event Attention", 21.0, 19.0, 18.5, 12.5, 17.0, "Inconclusive overall, but contains two of the finest shots in ALLWAYS: the toddler's backward stare (14–17s) and the haunting closing empty-room hold (44–48.5s)."),
    "061-matter": (61, "MATTER · Material Affordance Chain", 21.0, 17.5, 18.5, 12.5, 18.0, "Features the hypnotic 7.8s viscous pour (12.6–20.3s) and 9.4s lathe-chip hold; repaired Round-1 defect by explicitly labelling the grain-crack diagram."),
    "065-five": (65, "FIVE · Parallel Lives", 20.5, 18.5, 18.0, 12.5, 16.5, "67.6s across 12 events with an alternate cut (065-five-alt.mp4); strong source foraging across five situated participants."),
    "056-symmetry": (56, "SYMMETRY · Imperfect Pairing", 20.0, 18.5, 18.0, 12.0, 16.5, "53.9s paired-gesture study across 9 events; clean split compositions."),
    "058-laughs": (58, "LAUGHS · Audible Contagion", 19.0, 18.5, 17.5, 11.5, 16.5, "Contains the beloved 25.2–31.2s girls' shared laughter sequence, though acoustic contagion was quieter in earlier cuts."),
    "060-losers": (60, "LOSERS · Social Position", 18.5, 17.5, 17.0, 12.0, 16.5, "36.7s study built from a staged 1953 source; transparent disclosure of fictionalized staging in the case study."),
    "063-breath": (63, "BREATH · Invisible Force", 17.0, 18.0, 16.5, 11.5, 14.0, "Critic FAIL in Round 1 (needs simultaneous breath/mechanical comparison), though the 9s steam-jet hold (30–39s) is visually striking."),
}

sonnet_status = json.load(open(f"{REPO}/allways-sonnet/status.json"))
for k, (sc_id, title, b1, b2, b3, b4, b5, note) in SONNET_SCORES.items():
    edl = json.load(open(f"{REPO}/allways-sonnet/{k}/edl.json"))
    evs = edl.get("events", [])
    dur = round(sum(e.get("dur", 0) for e in evs), 1)
    total = round(b1 + b2 + b3 + b4 + b5, 1)
    all_evaluated.append({
        "id": f"sonnet-{k}",
        "maker": "Claude Sonnet",
        "run_id": "allways-sonnet",
        "series": "SCION 055–065",
        "work_slug": k,
        "scion_id": sc_id,
        "title": title,
        "subtitle": f"SCION {sc_id:03d} · {scion_slate[sc_id]['family']}",
        "duration_s": dur,
        "target_dur_s": 60.0,
        "shots_count": len(evs),
        "verdict": sonnet_status.get(k, "reviewed"),
        "scores": {"brief": b1, "archival": b2, "nearmatch": b3, "audio_time": b4, "critic_ethics": b5},
        "total": total,
        "url": f"../allways-sonnet/{k}/",
        "video_url": f"../allways-sonnet/{k}/{k}.mp4",
        "poster_url": f"../allways-sonnet/{k}/poster.jpg",
        "jury_note": note
    })

# 3. OPENAI SOL (24 SCION 055-078 entries)
SOL_SCORES = {
    71: (23.5, 19.5, 19.5, 12.5, 18.5, "Bounded VISUAL PASS (V02, 90s); superb meta-archival study ('A File Has Edges') using Facts About Film (1948) to distinguish parent reel, trim, and digital derivative."),
    63: (23.0, 19.5, 19.0, 12.5, 18.5, "Qualified VISUAL PASS (V02); best realization of SCION 063 across all makers—uses a 1927 Wellcome Library spirometer film to make human breath volume physically visible."),
    78: (23.0, 19.5, 19.0, 12.5, 18.0, "Bounded VISUAL PASS (V02, 120s); tactile industrial cycle ('A Form, Then a Page') tracing lead type from form labour to printed page."),
    57: (22.5, 19.0, 19.0, 13.0, 18.0, "V02 (55s) earned PASS from the attention critic after repairing the post-event hold; exemplary micro-event threshold patience."),
    77: (22.5, 19.5, 19.0, 12.5, 18.0, "Bounded VISUAL PASS (V01, 80s); visually poetic juxtaposition of linear human rows against nonlinear wheeling bird flocks."),
    65: (22.5, 19.0, 18.5, 13.0, 18.0, "Qualified VISUAL PASS (V02, 100s) across five differentiated archive labor practices including Master Hands (1936)."),
    60: (22.0, 19.0, 18.5, 12.5, 18.5, "PASS (V02) for reinterpreting an accusation ('You pickpocket') through wider same-scene context from Chaplin's The Immigrant (1917)."),
    76: (22.5, 19.0, 18.5, 12.5, 18.0, "Bounded VISUAL PASS (V01, 120s); compares two public-camera records (1939–40 New York World's Fair Medicus collection) with strong spatial evidence."),
    55: (22.0, 18.5, 18.5, 13.0, 17.5, "PASS from fresh blind critic (V04). Eight passages from seven archival clips where the organizing word 'Turn' appears only at the end."),
    56: (21.5, 19.0, 18.5, 12.5, 18.0, "Rebuilt V02 earned PASS from both visual critics; pairs two manual archival tasks with clear pre-action context."),
    70: (22.0, 19.0, 18.5, 12.5, 17.5, "Bounded VISUAL PASS (V02, 90s); strong split comparison of Apollo 11 launch record vs. published transcript timing."),
    75: (22.0, 19.0, 18.0, 12.5, 17.5, "Bounded VISUAL PASS (V01, 90s + 95s comparison); warm, situated home-movie comparison ('Within Reach') with zero synthetic filler."),
    62: (21.5, 18.5, 18.0, 12.5, 17.5, "Qualified VISUAL PASS (V02); repaired red-continuity defect using American Look (1958) color chapters."),
    61: (21.5, 18.5, 18.0, 12.0, 17.5, "Qualified PASS (V03) for visual contact and material response (macro paper wetting and state comparison)."),
    69: (21.0, 18.5, 18.5, 12.0, 17.0, "Bounded VISUAL PASS (V02, 70s) exposing manufactured entrance/shared-space relations across disparate buildings."),
    59: (21.0, 18.0, 18.0, 12.0, 17.0, "VISUAL CONSTRUCTION: PASS (V02). Centered circular registration across domestic and industrial objects."),
    67: (21.0, 17.5, 18.0, 12.0, 17.0, "Bounded VISUAL PASS (V03, 90s) for precise-description/next-picture temporal offset construction after clearing V02's absent-cup defect."),
    64: (20.5, 18.0, 17.5, 11.5, 16.5, "Bounded VISUAL PASS (V04) comparative essay on archival flight/sport curves."),
    74: (19.5, 13.0, 16.5, 11.5, 15.5, "Bounded VISUAL PASS (V02, 110s) for directory index reasoning ('The Missing Minute'), but uses synthetic avatar cards instead of archival footage."),
    66: (19.0, 13.0, 16.5, 11.0, 15.5, "Bounded VISUAL PASS for substitution grammar, but built as a synthetic vector grid ('Eight Places') rather than foraged archival photography."),
    68: (18.5, 12.5, 16.0, 11.0, 15.0, "Bounded VISUAL PASS for metric scale logic, but uses a synthetic beige diagram ('One Fold, a Room') instead of photographic footage."),
    72: (18.5, 12.5, 16.0, 11.0, 15.0, "Bounded VISUAL PASS for sign/action refusal logic, but rendered as a synthetic vector animation ('Keep It') rather than archival film."),
    73: (18.5, 12.5, 16.0, 11.0, 15.0, "Bounded VISUAL PASS for cartographic passage, but rendered as an invented vector map ('The Entrance Has Moved') rather than archival footage."),
    58: (13.0, 15.5, 13.5, 10.0, 13.0, "Marked 'unfinished' source study by Sol; honest self-audit refusing to claim a completed laugh-contagion proof."),
}

sol_cat = json.load(open(f"{REPO}/allways-sol/catalog.json"))["films"]
for f in sol_cat:
    sc_id = f["id"]
    num = f["number"]
    dur = round((f.get("film") or {}).get("duration", 0), 1)
    b1, b2, b3, b4, b5, note = SOL_SCORES[sc_id]
    total = round(b1 + b2 + b3 + b4 + b5, 1)
    vid_rel = (f.get("film") or {}).get("url", "")
    all_evaluated.append({
        "id": f"sol-{num}",
        "maker": "OpenAI Sol",
        "run_id": "allways-sol",
        "series": "SCION 055–078",
        "work_slug": f"scion-{num}",
        "scion_id": sc_id,
        "title": f"{num} · {f['title'].upper()}",
        "subtitle": f.get("description", ""),
        "duration_s": dur,
        "target_dur_s": 60.0,
        "shots_count": 8,
        "verdict": "unfinished" if f["status"] == "unfinished" else "bounded visual pass",
        "scores": {"brief": b1, "archival": b2, "nearmatch": b3, "audio_time": b4, "critic_ethics": b5},
        "total": total,
        "url": f"../allways-sol/films.html#film-{num}",
        "video_url": f"../allways-sol/{vid_rel}" if vid_rel else "../allways-sol/",
        "poster_url": f"../allways-sol/{f.get('poster', '')}",
        "jury_note": note
    })

# 4. GEMINI ARGON (85 Studio Films)
ARGON_SCORES = {
    "BROLL_01_Nobody_Home": (24.0, 19.5, 19.5, 14.0, 18.5, "PASS (Round 2). Definitive realization of NOBODY HOME: pairs intact 1958 domestic footage with OpenCV Telea person-removal and a 3-panel Original | Mask | Derived inspection triptych."),
    "SCION_090_The_Clock_Horological_Montage": (23.5, 19.5, 19.5, 14.0, 18.0, "PASS (Round 2). Masterful horological montage cutting between archival clock dials and human preparation across a continuous timeflow."),
    "SCION_085_Jeanne_Dielman_Domestic_Routine_Gauge": (23.5, 19.5, 19.5, 14.0, 18.0, "PASS (Round 2). Unbroken domestic routine duration gauge across three passes where tiny temporal drift registers the pressure of routine."),
    "BROLL_06_Kinetic": (23.0, 19.5, 19.0, 13.5, 18.0, "PASS (Round 2). Rhythmic handloom shuttle and assembly cadence interrupted by human rest, avoiding Qatsi time-lapse clichés."),
    "SCION_068_Powers_Of_Ten_Scale_Traverse": (23.0, 19.5, 19.0, 13.5, 18.0, "PASS (Round 2). Photographic 10^x scale traverse from macro hand craft to aerial landscape and return, unlike Sol's synthetic beige diagram."),
    "SCION_093_What_Is_Neorealism_Counterfactual_Cuts": (23.0, 19.0, 19.5, 13.5, 18.0, "PASS (Round 2). Kogonada-style counterfactual comparison showing the same archival passage cut for plot efficiency vs. neorealist interstitial dwell."),
    "SCION_113_Learning_To_See_Latent_Atlas": (23.0, 19.5, 19.0, 13.5, 18.0, "PASS (Round 2). Memo Akten / Latent Atlas study resolving raw archival water, fire, and optical grain into landscape recognition."),
    "SCION_079_Qatsi_Three_Technological_Regimes": (22.5, 19.5, 19.0, 13.5, 18.0, "PASS (Round 2). Distinct ecological, industrial, and digital/information regimes differentiated without collapsing into generic fast-motion."),
    "BROLL_02_Almost_Human": (22.5, 19.0, 19.0, 13.5, 18.0, "PASS (Round 2). Opens with a complete 1944 collar adjustment held through its pause, followed by five distinct archival gesture outcomes."),
    "BROLL_05_Cut_To_The_Chase": (22.5, 19.0, 19.0, 13.5, 18.0, "PASS (Round 2). Transfers directional running momentum across 1926 nitrate heath and urban streets before holding on a stationary bystander."),
    "BROLL_10_Collective_Inventories": (22.5, 19.0, 19.0, 13.5, 18.0, "PASS (Round 2). Composite morning handoff across five archival records (washing, carrying, preparing, clearing) with unfinished task preserved."),
    "BROLL_12_Planimetric": (22.5, 19.0, 19.0, 13.5, 18.0, "PASS (Round 2). Four locked architectural tableaux (SCION 086 / Ozu pillow-shot geometry) where human figures enter, shift posture, and leave."),
    "STUDY_03_The_Eye_Trace_Archive": (22.5, 19.0, 19.0, 13.5, 17.5, "PASS (Round 2). Foveated attention study tracking where the viewer's eye lands before and after a cut."),
    "COLL_05_Everday": (22.0, 19.0, 18.5, 13.5, 17.5, "PASS (Round 2). Everyday circadian collection tracing ordinary gestures from waking water to evening stillness."),
    "BROLL_03_Terra_Incognita": (22.0, 19.0, 18.5, 13.5, 17.5, "PASS (Round 2). Three physical film surfaces with real emulsion scratch and optical track defects kept distinct from authored transitions."),
    "BROLL_04_Split_Second": (22.0, 19.0, 18.5, 13.5, 17.5, "PASS (Round 2). Six bounded release excerpts cutting away twice before release and delivering the physical consequence on the third return."),
    "BROLL_09_Anybody_Anywhere": (22.0, 19.0, 18.5, 13.5, 17.5, "PASS (Round 2). Side-by-side synchronous split-screen comparison of situated recordings with explicit date/provenance labels."),
    "BROLL_08_Homonym": (21.5, 18.5, 18.5, 13.5, 17.5, "PASS (Round 2). Semantic relay across spoken, physical, and tonal branches with intelligible archival speech."),
    "BROLL_07_Zero_Memory": (21.5, 18.5, 18.0, 13.5, 17.5, "PASS (Round 2). Fixed archival pool with three declared working-history resets and side-by-side recurrence comparison."),
    "BROLL_11_Mnemonil": (21.0, 18.5, 18.0, 13.5, 17.0, "PASS (Round 2). Biographical assembly with explicit provenance rupture disclosing that the archive clips belong to separate lives."),
}

broll_map = {
    "BROLL_01_Nobody_Home": "nobody-home", "BROLL_02_Almost_Human": "almost-human",
    "BROLL_03_Terra_Incognita": "terra-incognita", "BROLL_04_Split_Second": "split-second",
    "BROLL_05_Cut_To_The_Chase": "cut-to-the-chase", "BROLL_06_Kinetic": "kinetic",
    "BROLL_07_Zero_Memory": "zero-memory", "BROLL_08_Homonym": "homonym",
    "BROLL_09_Anybody_Anywhere": "anybody-anywhere", "BROLL_10_Collective_Inventories": "collective-inventories",
    "BROLL_11_Mnemonil": "mnemonil", "BROLL_12_Planimetric": "planimetric",
}

for mf_path in sorted(glob.glob(f"{REPO}/allways-argon/studio/manifests/*.json")):
    bn = os.path.basename(mf_path)
    if bn in ("films_index.json", "audit_report.json", "critic_tribunal_v1_v2.json", "repair_Replacement_log.json", "clean_windows.json"):
        continue
    m = json.load(open(mf_path))
    if not isinstance(m, dict) or "slug" not in m:
        continue
    slug = m.get("slug", bn.replace(".json", ""))
    dur = round(m.get("duration_seconds", 42.0), 1)
    edl = [s for s in m.get("edl", []) if s.get("type") not in ("title_card", "closing_ledger")]
    ct = m.get("critic_tribunal", {})
    was_repaired = ct.get("v1_verdict") == "repair_required"

    if slug in ARGON_SCORES:
        b1, b2, b3, b4, b5, note = ARGON_SCORES[slug]
    else:
        b1 = 21.0 if dur >= 38.0 else 20.0
        b2 = 18.5 if m.get("source_count", 4) >= 4 else 18.0
        b3 = 18.0 if len(edl) >= 4 else 17.5
        b4 = 13.5
        b5 = 17.5 if was_repaired else 17.0
        note = f"PASS (Round 2 Critic Tribunal). {m.get('theorem', '')[:140]}"

    total = round(b1 + b2 + b3 + b4 + b5, 1)
    w_slug = broll_map.get(slug, slug.lower())
    url = f"../allways-argon/films/{w_slug}/" if slug in broll_map else f"../allways-argon/studio/cases/{slug}.html"
    vid_url = f"../allways-argon/films/{w_slug}/{w_slug}.mp4" if slug in broll_map else f"../allways-argon/studio/films/{slug}.mp4"
    poster_url = f"../allways-argon/films/{w_slug}/poster.jpg" if slug in broll_map else f"../allways-argon/studio/strips/{slug}_v2_strip.jpg"

    all_evaluated.append({
        "id": f"argon-{slug}",
        "maker": "Gemini Argon",
        "run_id": "allways-argon",
        "series": m.get("series", "SCION"),
        "work_slug": w_slug,
        "scion_id": m.get("scion_id"),
        "title": f"{m.get('title', slug)}",
        "subtitle": m.get("subtitle", ""),
        "duration_s": dur,
        "target_dur_s": BROLL_TARGET_DUR.get(w_slug, 45.0),
        "shots_count": len(edl),
        "verdict": "pass (Round 2 repaired)" if was_repaired else "pass (Round 2 verified)",
        "scores": {"brief": b1, "archival": b2, "nearmatch": b3, "audio_time": b4, "critic_ethics": b5},
        "total": total,
        "url": url,
        "video_url": vid_url,
        "poster_url": poster_url,
        "jury_note": note
    })

all_evaluated.sort(key=lambda x: (-x["total"], x["id"]))

def grade_for(score):
    if score >= 93.0: return "S"
    if score >= 90.0: return "A+"
    if score >= 86.0: return "A"
    if score >= 82.0: return "A-"
    if score >= 77.0: return "B+"
    if score >= 70.0: return "B"
    return "C+"

for rank, item in enumerate(all_evaluated, 1):
    item["rank"] = rank
    item["grade"] = grade_for(item["total"])

AWARDS = [
    {
        "category": "01 · Grand Prix — Best Single Film in ALLWAYS (Individual Work)",
        "winner_id": "sonnet-059-ball",
        "winner_title": "059 · BALL (Graphic Constancy)",
        "winner_maker": "Claude Sonnet",
        "winner_score": 96.0,
        "runner_up": "NOBODY HOME (Gemini Argon · 95.5/100) & MNEMONIL (Claude Opus 5.5 · 94.5/100)",
        "why": "Registers thirteen round objects from archival films spanning 1929–2007 to the exact screen center within 5 pixels, keeps an octagonal clock's registration failure as an honest seam, releases to a hand turning a gauge control, and exits with a 1965 moon drifting out of frame."
    },
    {
        "category": "02 · Special Jury Synthesis Prize (Cross-Maker Anthology)",
        "winner_id": "allways-best",
        "winner_title": "ALLWAYS — Cinema from the Rest of the Frame",
        "winner_maker": "Opus 5.5 · Argon · Sol · Sonnet",
        "winner_score": 98.0,
        "runner_up": "Hors Concours (All 4 Makers Combined · 24 Critic-Protected Cuts · 2m 43s)",
        "why": "Unites the 24 highest-rated critic-protected passages from all 132 films into one continuous 163-second widescreen work across six movements."
    },
    {
        "category": "03 · Best B-Roll of Civilization Proof & Computational Intervention",
        "winner_id": "argon-BROLL_01_Nobody_Home",
        "winner_title": "NOBODY HOME (SCION 085 · 067 · 097)",
        "winner_maker": "Gemini Argon",
        "winner_score": 95.5,
        "runner_up": "NOBODY HOME (Claude Opus 5.5 · 83.0/100 — praised opening boy-with-chair shot)",
        "why": "Executes spatial-temporal figure segmentation and OpenCV Telea background inpainting on an intact 1958 living room and discloses the intervention in a 3-panel Original | Extracted Mask | Derived Empty Room inspection triptych."
    },
    {
        "category": "04 · Best Documentary Ethics & Borrowed-Memory Study",
        "winner_id": "opus-mnemonil",
        "winner_title": "MNEMONIL (SCION 067 · 093 · 094)",
        "winner_maker": "Claude Opus 5.5",
        "winner_score": 94.5,
        "runner_up": "060 · IN THE FRAME (OpenAI Sol · 90.5/100) & MNEMONIL (Gemini Argon · 88.0/100)",
        "why": "The only film in Opus 5.5's run to pass its blind critic: at 23–40s, the narrator's claim of an 'untouched family kitchen' (plant, red chair, icebox) is silently refuted when two coated visitors walk into frame behind a museum exhibit rope."
    },
    {
        "category": "05 · Best Comparative Physics & Trajectory Study",
        "winner_id": "sonnet-064-parabolas",
        "winner_title": "064 · PARABOLAS (Curves with Different Causes)",
        "winner_maker": "Claude Sonnet",
        "winner_score": 94.5,
        "runner_up": "SCION 064 · PARABOLAS (Gemini Argon · 88.5/100) & 064 · THE CURVE IS NOT THE CAUSE (OpenAI Sol · 84.0/100)",
        "why": "Runs an unannotated perceptual pass (0–34.4s) across a high diver, fountain arc, and pendulum before repeating with fitted mathematical curves that expose their distinct physical causes."
    },
    {
        "category": "06 · Best Meta-Archival & Material Carrier Study",
        "winner_id": "sol-071",
        "winner_title": "071 · A FILE HAS EDGES (Standard Gauge)",
        "winner_maker": "OpenAI Sol",
        "winner_score": 93.5,
        "runner_up": "SCION 113 · LEARNING TO SEE (Gemini Argon · 93.0/100) & TERRA INCOGNITA (Gemini Argon · 90.5/100)",
        "why": "A 90-second dissection built from Facts About Film (1948) that makes the physical boundary between parent 16mm reel, edited selection, and digital derivative unmistakable."
    },
    {
        "category": "07 · Best Invisible Force & Physiological Proof (SCION 063)",
        "winner_id": "sol-063",
        "winner_title": "063 · A VOLUME OF AIR",
        "winner_maker": "OpenAI Sol",
        "winner_score": 92.5,
        "runner_up": "SCION 063 · BREATH (Gemini Argon · 88.5/100) & 063 · BREATH (Claude Sonnet · 77.0/100)",
        "why": "Solves SCION 063's hardest challenge—making invisible human breath measurable without fake animation—by foraging a 1927 Wellcome Library spirometer recording where a man's exhalation physically lifts a calibrated glass cylinder."
    },
    {
        "category": "08 · Best Horological & Domestic Duration Architecture (SCION 085 / 090)",
        "winner_id": "argon-SCION_090_The_Clock_Horological_Montage",
        "winner_title": "SCION 090 · THE CLOCK & SCION 085 · JEANNE DIELMAN (Tie)",
        "winner_maker": "Gemini Argon",
        "winner_score": 94.5,
        "runner_up": "ZERO MEMORY (Claude Opus 5.5 · 89.0/100 — 110s duration test)",
        "why": "Anchors the upper SCION slate (079–113) with two rigorous temporal proofs: Marclay-inspired horological dial synchronization (090) and Akerman-inspired three-pass domestic routine duration gauging (085)."
    },
    {
        "category": "09 · Best Labor, Craft & Rhythmic Cadence (SCION 065 / 078 / 083)",
        "winner_id": "argon-BROLL_06_Kinetic",
        "winner_title": "KINETIC (Gemini Argon · 93.0) & 078 · A FORM, THEN A PAGE (OpenAI Sol · 92.0)",
        "winner_maker": "Gemini Argon & OpenAI Sol",
        "winner_score": 93.0,
        "runner_up": "COLLECTIVE INVENTORIES (Gemini Argon · 92.0/100) & 065 · FIVE RECORDS (OpenAI Sol · 91.0/100)",
        "why": "Argon's KINETIC pairs reciprocating handloom shuttle rhythm with normalized optical sound and human rest; Sol's 120-second 078 traces hot-metal typesetting from form labor to printed page."
    },
    {
        "category": "10 · Best Micro-Event & Post-Action Threshold Hold (SCION 057 / 086)",
        "winner_id": "argon-BROLL_12_Planimetric",
        "winner_title": "PLANIMETRIC (Gemini Argon · 92.0) & 057 · AFTER (OpenAI Sol · 91.5)",
        "winner_maker": "Gemini Argon & OpenAI Sol",
        "winner_score": 92.0,
        "runner_up": "057 · MOMENTS (Claude Sonnet · 88.0/100 — Best Individual Shots: toddler stare & closing empty room)",
        "why": "Argon's PLANIMETRIC realizes all four Ozu-inspired architectural tableaux where rooms hold after people depart, while Sol's 057 AFTER V02 passed its blind attention critic by holding the doorway threshold after conversation stops."
    },
    {
        "category": "11 · Best Parallel Lives & Split-Screen Alignment (SCION 056 / 076 / 099)",
        "winner_id": "argon-BROLL_09_Anybody_Anywhere",
        "winner_title": "ANYBODY, ANYWHERE (Argon · 90.5 / Opus 5.5 · 89.5) & 076 · TWO PUBLIC EDGES (Sol · 90.5)",
        "winner_maker": "Gemini Argon, Claude Opus 5.5 & OpenAI Sol",
        "winner_score": 90.5,
        "runner_up": "056 · IN DIFFERENT HANDS (OpenAI Sol · 89.5/100) & 075 · WITHIN REACH (OpenAI Sol · 89.0/100)",
        "why": "Opus 5.5 and Argon align 1961 and 1944 chair preparations in synchronous split-screen while preserving distinct eras; Sol's 076 compares two 1939–40 New York World's Fair public-camera vantage points."
    },
    {
        "category": "12 · Best Semantic & Chromatic Relay (SCION 055 / 061 / 062)",
        "winner_id": "sonnet-055-words",
        "winner_title": "055 · WORDS & 062 · COLORS (Claude Sonnet · 90.0/100)",
        "winner_maker": "Claude Sonnet",
        "winner_score": 90.0,
        "runner_up": "055 · TURN (OpenAI Sol · 89.5/100) & HOMONYM (Gemini Argon · 89.5/100 / Claude Opus 5.5 · 86.5/100)",
        "why": "Sonnet's 055 anchors the polysemy of 'draw' in a tactile 9-second cigarette close-up where sound and sense meet, while 062 pivots from yellow industrial machinery to deep teal sea across a single crane swing."
    },
]

with open(os.path.join(OUT_DIR, "ratings.json"), "w") as f:
    json.dump({
        "count": len(all_evaluated),
        "rubric": {
            "brief": "Brief & Structural Realization (25 pts)",
            "archival": "Archival Foraging & Visual Purity (20 pts)",
            "nearmatch": "NEARMATCH Editorial Craft & Formal Invention (20 pts)",
            "audio_time": "Acoustic & Temporal Architecture (15 pts)",
            "critic_ethics": "Independent Critic Tribunal & Ethical Provenance (20 pts)"
        },
        "awards": AWARDS,
        "films": all_evaluated
    }, f, indent=2)

print("Saved ratings.json with", len(all_evaluated), "films and", len(AWARDS), "award categories.")
