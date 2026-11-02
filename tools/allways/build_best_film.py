#!/usr/bin/env python3
"""
Builds the single flagship ALLWAYS synthesis film:
  ALLWAYS — Cinema from the Rest of the Frame (allways-best)
combining 24 critic-protected passages across all four makers:
  Claude Opus 5.5, Gemini Argon, OpenAI Sol, and Claude Sonnet.
"""
import os, json, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

REPO = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
OUT_DIR = os.path.join(REPO, "allways-best")
IMG_DIR = os.path.join(OUT_DIR, "img")
WORK_DIR = "/Users/gaia/.gemini/antigravity/brain/0433d372-2cf8-4c4c-9062-86fff8e7db60/scratch/build_best"

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

W, H, FPS = 1280, 720, 24

def get_font(size, mono=False):
    candidates = (
        ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Courier.dfont"]
        if mono else
        ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/System/Library/Fonts/Times.ttc"]
    )
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

CHAPTERS = [
    {
        "id": "ch1",
        "num": "I / VI",
        "title": "THE OCCASION & THE EDGE",
        "quote": "A camera points at an event. More happens than the event can contain.\nSomeone waits for a doorway to clear. Someone moves a chair.",
        "source": "ALLWAYS Statement · Record"
    },
    {
        "id": "ch2",
        "num": "II / VI",
        "title": "NEARMATCH",
        "quote": "Two gestures can resemble one another and still belong to different lives.\nWe keep the pause that interrupts the alignment.",
        "source": "ALLWAYS Statement · Machine"
    },
    {
        "id": "ch3",
        "num": "III / VI",
        "title": "THE RELAY",
        "quote": "The name joins always and all ways: recurrence through time,\nand different routes through the same material.",
        "source": "ALLWAYS Statement · Form"
    },
    {
        "id": "ch4",
        "num": "IV / VI",
        "title": "THE WORK",
        "quote": "Carrying, cleaning, preparing, repairing, waiting for access, making room.\nWe follow the activity that makes an event possible.",
        "source": "ALLWAYS Statement · Work"
    },
    {
        "id": "ch5",
        "num": "V / VI",
        "title": "THE CARRIER & THE CHASE",
        "quote": "An archive has already passed through many hands.\nOur edit enters that work and becomes answerable for what it does next.",
        "source": "ALLWAYS Statement · Archive"
    },
    {
        "id": "ch6",
        "num": "VI / VI",
        "title": "THE ROOM REMAINS",
        "quote": "A moment does not have to explain a life to be worth keeping.\nThe room remains. That does not tell us everything about who left.",
        "source": "Between Takes · The Interval & The Room"
    },
]

SHOTS = [
    # CHAPTER I
    {
        "pos": 1, "chapter": 0, "maker": "Claude Opus 5.5", "run_id": "allways-opus",
        "film_title": "NOBODY HOME", "film_url": "../allways-opus/films/nobody-home/",
        "scion": "SCION 085", "source_title": "Amateur Film New Jersey B", "source_year": "c. 1950",
        "source_url": "https://www.movingimagearchive.com/sources/amateur-film-new-jersey-b-ce960587",
        "video_path": os.path.join(REPO, "allways-opus/films/nobody-home/nobody-home.mp4"),
        "in_s": 1.0, "out_s": 7.5, "crop_mode": "full", "has_sync_audio": True,
        "action": "A boy crosses a fixed-camera domestic room, carries a chair to the window, and climbs onto it.",
        "nearmatch": "Opening domestic threshold: recorded human action before computational erasure.",
        "why_chosen": "Praised by the blind critic ('at 0:00-0:12 a boy crosses a fixed-camera room, carries a chair to the window, climbs on it'); establishes ALLWAYS's foundational proposition: someone moves a chair at the edge of the frame.",
        "critic_verdict": "Critic-noted opening passage (Opus 5.5 Round 1)"
    },
    {
        "pos": 2, "chapter": 0, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "NOBODY HOME", "film_url": "../allways-argon/films/nobody-home/",
        "scion": "SCION 085 · 067 · 097", "source_title": "Have I Told You Lately That I Love You?", "source_year": "1958",
        "source_url": "https://www.movingimagearchive.com/sources/have-i-told-you-lately-that-i-love-you-0e6a48dc?clip=058430e4-9cb9-5f36-9d45-faf15c735299",
        "video_path": os.path.join(REPO, "allways-argon/films/nobody-home/nobody-home.mp4"),
        "in_s": 38.6, "out_s": 44.6, "crop_mode": "argon_triptych", "has_sync_audio": True,
        "action": "Three-panel inspection ledger: intact source pixels on the left, extracted person silhouette mask in the center, and Telea-inpainted empty armchair on the right.",
        "nearmatch": "From Opus's occupied room to Argon's explicit disclosure of person-removal.",
        "why_chosen": "Critic Tribunal 'Strength to preserve': 'The 3-panel inspection triptych layout (Original | Extracted Mask | Derived Empty Room)'. Keeps the mask and synthesized background separate from recorded pixels.",
        "critic_verdict": "PASS · Strength to preserve (Argon Round 2)"
    },
    {
        "pos": 3, "chapter": 0, "maker": "OpenAI Sol", "run_id": "allways-sol",
        "film_title": "057 · AFTER", "film_url": "../allways-sol/",
        "scion": "SCION 057", "source_title": "Archival Threshold Study (V02)", "source_year": "1950s",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sol/films/057/media/ALLWAYS_057_AFTER_V02.mp4"),
        "in_s": 11.5, "out_s": 17.0, "crop_mode": "sol_clean", "has_sync_audio": True,
        "action": "A man and woman pause by an interior doorway as the official exchange ends and the post-action stillness takes over.",
        "nearmatch": "Doorway geometry rhymes with the domestic rooms while shifting attention to the interval after speech.",
        "why_chosen": "Cleared Sol's attention critic on V02 ('PASS from attention critic after specific 5s hold repair'): demonstrates holding a shot after the nominal action finishes.",
        "critic_verdict": "PASS · Attention Critic V02 (Sol)"
    },
    {
        "pos": 4, "chapter": 0, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "057 · MOMENTS", "film_url": "../allways-sonnet/057-moments/",
        "scion": "SCION 057", "source_title": "Home Movie Doorway Excerpt", "source_year": "c. 1955",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/057-moments/057-moments.mp4"),
        "in_s": 13.8, "out_s": 18.3, "crop_mode": "full", "has_sync_audio": False,
        "action": "A toddler stands at a screen door, hand against the frame, staring directly back at the camera.",
        "nearmatch": "From the adult doorway threshold in Sol 057 to a child's unguarded counter-gaze at the threshold.",
        "why_chosen": "Explicitly singled out by Sonnet's independent critic ('Strength to protect: the toddler's backward stare at 14–17').",
        "critic_verdict": "Strength to protect (Sonnet Round 1)"
    },

    # CHAPTER II
    {
        "pos": 5, "chapter": 1, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "ALMOST HUMAN", "film_url": "../allways-argon/films/almost-human/",
        "scion": "SCION 057 · 084 · 085", "source_title": "Basic Typing, Part I: Methods", "source_year": "1944",
        "source_url": "https://www.movingimagearchive.com/sources/basic-typing-part-i-methods-9b968a51?clip=9d763244-d729-5c73-a565-5dd1133b2f98",
        "video_path": os.path.join(REPO, "allways-argon/films/almost-human/almost-human.mp4"),
        "in_s": 3.2, "out_s": 8.7, "crop_mode": "argon_center", "has_sync_audio": True,
        "action": "A woman adjusts her collar and blouse at a desk, completing the self-preparatory gesture before settling into stillness.",
        "nearmatch": "Initiates the NEARMATCH gesture chain: a complete collar adjustment with its pause intact.",
        "why_chosen": "Verified cut-free single-shot window (max_diff < 16.0) fulfilling the ALMOST HUMAN opening requirement ('Begin with one complete collar adjustment, including the pause afterward').",
        "critic_verdict": "PASS · Verified single-shot gesture (Argon Round 2)"
    },
    {
        "pos": 6, "chapter": 1, "maker": "Claude Opus 5.5", "run_id": "allways-opus",
        "film_title": "ANYBODY, ANYWHERE", "film_url": "../allways-opus/films/anybody-anywhere/",
        "scion": "SCION 056 · 099", "source_title": "16mm Motion Picture Projector (1961) / Basic Typing (1944)", "source_year": "1944 / 1961",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-opus/films/anybody-anywhere/anybody-anywhere.mp4"),
        "in_s": 3.5, "out_s": 9.5, "crop_mode": "full", "has_sync_audio": True,
        "action": "Split-screen pairing: on the left (1961), a man bends to arrange theatre chairs; on the right (1944), a woman adjusts and sits on a typing chair.",
        "nearmatch": "Pairs two situated preparations across seventeen years without pretending they occurred simultaneously.",
        "why_chosen": "Highlighted by Opus's blind critic ('Noticed before the brief: at 0:03-0:11 a man bends to arrange theatre chairs while a woman's hands tilt and then sit on a swivel chair').",
        "critic_verdict": "Critic-highlighted parallel alignment (Opus 5.5)"
    },
    {
        "pos": 7, "chapter": 1, "maker": "OpenAI Sol", "run_id": "allways-sol",
        "film_title": "063 · A VOLUME OF AIR", "film_url": "../allways-sol/",
        "scion": "SCION 063", "source_title": "Human / Breathing (Wellcome Library)", "source_year": "1927",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sol/films/063/media/ALLWAYS_063_A_VOLUME_OF_AIR_V02.mp4"),
        "in_s": 11.0, "out_s": 16.5, "crop_mode": "sol_clean", "has_sync_audio": False,
        "action": "A subject exhales into a laboratory tube, raising the bell of a glass spirometer cylinder by the exact volume of his breath.",
        "nearmatch": "Makes invisible human breath physically measurable before cutting to audible social breath (laughter).",
        "why_chosen": "Earned a qualified VISUAL PASS in Sol's Round 2 ('The actual repair improves the mechanical demonstration substantively; no remaining visual objection').",
        "critic_verdict": "PASS · Mechanical breath proof V02 (Sol)"
    },
    {
        "pos": 8, "chapter": 1, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "058 · LAUGHS", "film_url": "../allways-sonnet/058-laughs/",
        "scion": "SCION 058", "source_title": "Archival Group Laughter Excerpt", "source_year": "c. 1950",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/058-laughs/058-laughs.mp4"),
        "in_s": 25.2, "out_s": 30.8, "crop_mode": "full", "has_sync_audio": False,
        "action": "Three young women lean into one another as genuine, unscripted laughter spreads across their shoulders and faces.",
        "nearmatch": "From solitary measured exhalation (Sol 063) to shared respiratory contagion across bodies.",
        "why_chosen": "Praised by Sonnet's blind critic ('Strength to protect: the girls' sequence 25.2–31.2 is real shared in-source laughter with physical contagion—leaning, grabbing').",
        "critic_verdict": "Strength to protect (Sonnet Round 1)"
    },

    # CHAPTER III
    {
        "pos": 9, "chapter": 2, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "055 · WORDS", "film_url": "../allways-sonnet/055-words/",
        "scion": "SCION 055", "source_title": "Archival Close-Up ('Draw')", "source_year": "c. 1958",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/055-words/055-words.mp4"),
        "in_s": 13.5, "out_s": 19.5, "crop_mode": "full", "has_sync_audio": True,
        "action": "Close-up of a young man lighting and drawing on a cigarette—activating the physical sense of the word 'draw'.",
        "nearmatch": "Inaugurates the polysemic relay where a single word pivots across physical actions.",
        "why_chosen": "Sonnet's critic passed 055-words and named this exact shot its anchor ('Strength to protect: the cigarette draw 13–22, the only shot where sound and the sense meet').",
        "critic_verdict": "PASS · Strength to protect (Sonnet Round 1)"
    },
    {
        "pos": 10, "chapter": 2, "maker": "Claude Opus 5.5", "run_id": "allways-opus",
        "film_title": "HOMONYM", "film_url": "../allways-opus/films/homonym/",
        "scion": "SCION 055 · 092", "source_title": "Archival Workshop Drawer Sorting", "source_year": "c. 1954",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-opus/films/homonym/homonym.mp4"),
        "in_s": 17.9, "out_s": 22.5, "crop_mode": "full", "has_sync_audio": True,
        "action": "Hands sort dividers inside an open wooden drawer while the soundtrack states: 'a place for everything and everything should be in its place.'",
        "nearmatch": "Pivots from 'drawing' breath/smoke (Sonnet 055) to an open 'drawer' ordered by hand (Opus Homonym).",
        "why_chosen": "Highlighted by Opus's blind critic ('Noticed before the brief: at 00:17.9-21.8 the voice says a place for everything... over hands sorting').",
        "critic_verdict": "Critic-highlighted semantic match (Opus 5.5)"
    },
    {
        "pos": 11, "chapter": 2, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "059 · BALL", "film_url": "../allways-sonnet/059-ball/",
        "scion": "SCION 059", "source_title": "Registered Circles (Globe, Moon Map, Signature Lens, Eye)", "source_year": "1929–2007",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/059-ball/059-ball.mp4"),
        "in_s": 3.5, "out_s": 11.5, "crop_mode": "full", "has_sync_audio": True,
        "action": "Graphic constancy relay: a painted Earth globe, a magnifying lens over a moon map, a lens over a signature, and an eye behind glass hold the exact center rim.",
        "nearmatch": "Shifts the relay from verbal polysemy (055) to pure geometric registration across four decades of film.",
        "why_chosen": "Rated by Sonnet's blind critic as 'PASS (strongest proof in the batch) — Strength to protect: registration that holds through the opening'.",
        "critic_verdict": "PASS · Strongest proof in batch (Sonnet)"
    },
    {
        "pos": 12, "chapter": 2, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "064 · PARABOLAS", "film_url": "../allways-sonnet/064-parabolas/",
        "scion": "SCION 064", "source_title": "Archival High Dive Trajectory", "source_year": "c. 1952",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/064-parabolas/064-parabolas.mp4"),
        "in_s": 18.0, "out_s": 24.0, "crop_mode": "full", "has_sync_audio": False,
        "action": "A high diver traces a clean gravitational parabola across open sky from tower to water.",
        "nearmatch": "Releases the centered static circle of 059 into a dynamic ballistic curve governed by gravity.",
        "why_chosen": "Rated by Sonnet's blind critic as 'PASS (most complete realisation in the batch)'.",
        "critic_verdict": "PASS · Most complete realisation (Sonnet)"
    },

    # CHAPTER IV
    {
        "pos": 13, "chapter": 3, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "062 · COLORS", "film_url": "../allways-sonnet/062-colors/",
        "scion": "SCION 062", "source_title": "Maritime Crane Loading", "source_year": "c. 1960",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/062-colors/062-colors.mp4"),
        "in_s": 5.5, "out_s": 11.0, "crop_mode": "full", "has_sync_audio": True,
        "action": "A heavy yellow industrial tractor is hoisted by crane cables out over deep teal ocean water.",
        "nearmatch": "Carries the suspended aerial arc of the diver (064) into suspended industrial tonnage and chromatic contrast.",
        "why_chosen": "Explicitly protected by Sonnet's critic ('Strength to protect: Mixed-colour hinge at 7.5: a yellow engine swung out over teal sea. This hinge works.').",
        "critic_verdict": "PASS · Strength to protect (Sonnet Round 1)"
    },
    {
        "pos": 14, "chapter": 3, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "061 · MATTER", "film_url": "../allways-sonnet/061-matter/",
        "scion": "SCION 061", "source_title": "Industrial Viscous Pour Study", "source_year": "c. 1956",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/061-matter/061-matter.mp4"),
        "in_s": 13.0, "out_s": 19.5, "crop_mode": "full", "has_sync_audio": False,
        "action": "A continuous ribbon of dark, viscous liquid pours into a white basin, expanding into a glossy concentric pool.",
        "nearmatch": "From heavy mechanical suspension to fluid material affordance held for its full physical duration.",
        "why_chosen": "Praised by Sonnet's critic ('Strength to protect: the 7.8 s pour 12.6–20.3 ... duration is earned').",
        "critic_verdict": "Strength to protect · Earned duration (Sonnet)"
    },
    {
        "pos": 15, "chapter": 3, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "COLLECTIVE INVENTORIES", "film_url": "../allways-argon/films/collective-inventories/",
        "scion": "SCION 065 · 084 · 092", "source_title": "Care of the Hair and Nails", "source_year": "1951",
        "source_url": "https://www.movingimagearchive.com/sources/care-of-the-hair-and-nails-1519c4d8?clip=d5b6b1dd-1aad-5e95-bbc5-26288aa33f63",
        "video_path": os.path.join(REPO, "allways-argon/films/collective-inventories/collective-inventories.mp4"),
        "in_s": 3.2, "out_s": 8.7, "crop_mode": "argon_center", "has_sync_audio": True,
        "action": "Hands turn porcelain basin taps and wash carefully in running water to begin a composite morning.",
        "nearmatch": "Fluid pouring into a circular white basin (061 Matter) rhymes directly with water running in a domestic porcelain sink.",
        "why_chosen": "Passed Argon Round-2 Critic Tribunal: anchors the composite morning in a concrete, situated domestic task.",
        "critic_verdict": "PASS · Situated morning handoff (Argon Round 2)"
    },
    {
        "pos": 16, "chapter": 3, "maker": "OpenAI Sol", "run_id": "allways-sol",
        "film_title": "065 · FIVE RECORDS", "film_url": "../allways-sol/",
        "scion": "SCION 065", "source_title": "Master Hands ( Chevrolet Industrial Film )", "source_year": "1936",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sol/films/065/media/ALLWAYS_065_FIVE_RECORDS_V02.mp4"),
        "in_s": 11.0, "out_s": 16.5, "crop_mode": "sol_clean", "has_sync_audio": True,
        "action": "A skilled machinist presses metal against a high-speed grinding wheel, sending a bright cascade of sparks across the workshop.",
        "nearmatch": "Hands at the domestic basin (Argon 065) hand off to skilled industrial hands at the grinding wheel (Sol 065).",
        "why_chosen": "Earned a qualified VISUAL PASS in Sol's Round 2 ('qualified VISUAL PASS for five differentiated archive practices').",
        "critic_verdict": "PASS · Differentiated archive labor V02 (Sol)"
    },

    # CHAPTER V
    {
        "pos": 17, "chapter": 4, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "KINETIC", "film_url": "../allways-argon/films/kinetic/",
        "scion": "SCION 083 · 079 · 078", "source_title": "Labor of Thy Hands (Handcraft)", "source_year": "c. 1950",
        "source_url": "https://www.movingimagearchive.com/sources/labor-of-thy-hands-handcraft-ac5c6f18?clip=6ee8ef44-caa0-5a46-ad61-8c24c17d2698",
        "video_path": os.path.join(REPO, "allways-argon/films/kinetic/kinetic.mp4"),
        "in_s": 3.5, "out_s": 9.0, "crop_mode": "argon_center", "has_sync_audio": True,
        "action": "A weaver throws and beats a wooden handloom shuttle in a crisp, reciprocating horizontal rhythm.",
        "nearmatch": "Matches rotary industrial craft (Sol 065) with reciprocating textile rhythm before releasing momentum outward.",
        "why_chosen": "Passed Argon Round-2 Critic Tribunal: preserves the human craftsperson's bodily cadence inside repetitive work.",
        "critic_verdict": "PASS · Rhythmic labor study (Argon Round 2)"
    },
    {
        "pos": 18, "chapter": 4, "maker": "Claude Opus 5.5", "run_id": "allways-opus",
        "film_title": "SPLIT SECOND", "film_url": "../allways-opus/films/split-second/",
        "scion": "SCION 084 · 069 · 082", "source_title": "Archival Championship Bowling", "source_year": "c. 1958",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-opus/films/split-second/split-second.mp4"),
        "in_s": 9.2, "out_s": 14.0, "crop_mode": "full", "has_sync_audio": True,
        "action": "After two withheld releases, the bowler's ball finally strikes the headpin and scatters all ten pins.",
        "nearmatch": "Converts repetitive back-and-forth loom motion into forward release and physical impact.",
        "why_chosen": "Explicitly protected by Opus's blind critic ('Protect: the bowler return and the pin-fall payoff at 12-13').",
        "critic_verdict": "Strength to protect · Consequence payoff (Opus 5.5)"
    },
    {
        "pos": 19, "chapter": 4, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "CUT TO THE CHASE", "film_url": "../allways-argon/films/cut-to-the-chase/",
        "scion": "SCION 082 · 084 · 069", "source_title": "Nederlandsche Heide Maatschappij", "source_year": "1926",
        "source_url": "https://www.movingimagearchive.com/sources/nederlandsche-heide-maatschappij-en-haar-werk-de0bc1aa?clip=93053686-9523-5a3e-803d-130a49d2037f",
        "video_path": os.path.join(REPO, "allways-argon/films/cut-to-the-chase/cut-to-the-chase.mp4"),
        "in_s": 11.0, "out_s": 16.5, "crop_mode": "argon_center", "has_sync_audio": True,
        "action": "A lone figure sprints across a wide open heath under nitrate-era sky, carrying directional momentum across landscapes.",
        "nearmatch": "Transfers the kinetic impact of Split Second into open-air human pursuit across a horizon line.",
        "why_chosen": "Passed Argon Round-2 Critic Tribunal: clean horizon line and unbroken directional run.",
        "critic_verdict": "PASS · Directional momentum transfer (Argon Round 2)"
    },
    {
        "pos": 20, "chapter": 4, "maker": "OpenAI Sol", "run_id": "allways-sol",
        "film_title": "077 · ROWS AND FLOCKS", "film_url": "../allways-sol/",
        "scion": "SCION 077", "source_title": "Contemplative Horizon & Flock Study", "source_year": "c. 1940",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sol/films/077/media/ALLWAYS_077_ROWS_AND_FLOCKS_V01.mp4"),
        "in_s": 11.0, "out_s": 16.5, "crop_mode": "sol_clean", "has_sync_audio": False,
        "action": "A dense flock of birds wheels across the sky above a horizontal row of silhouetted figures standing along a ridge.",
        "nearmatch": "Graphic horizon match with the lone runner on the heath (Argon 19), expanding one runner into a collective horizon and sky.",
        "why_chosen": "Passed Sol's visual critic ('bounded VISUAL PASS — Deliberately spaced human placements beside a linear guide contrast with nonlinear flock motion').",
        "critic_verdict": "PASS · Linear human row vs. flock (Sol)"
    },

    # CHAPTER VI
    {
        "pos": 21, "chapter": 5, "maker": "OpenAI Sol", "run_id": "allways-sol",
        "film_title": "071 · A FILE HAS EDGES", "film_url": "../allways-sol/",
        "scion": "SCION 071", "source_title": "Facts About Film", "source_year": "1948",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sol/films/071/media/ALLWAYS_071_A_FILE_HAS_EDGES_V02.mp4"),
        "in_s": 10.0, "out_s": 15.5, "crop_mode": "sol_clean", "has_sync_audio": False,
        "action": "An archivist's hands hold and inspect a 16mm metal film reel and celluloid strip—the physical carrier behind every image.",
        "nearmatch": "Returns from the sky to the physical 16mm spool that carried all twenty preceding fragments.",
        "why_chosen": "Passed Sol's Round 2 critic ('bounded VISUAL PASS for the truthful parent/selection/reduced-derivative relation').",
        "critic_verdict": "PASS · Material carrier proof V02 (Sol)"
    },
    {
        "pos": 22, "chapter": 5, "maker": "Claude Opus 5.5", "run_id": "allways-opus",
        "film_title": "MNEMONIL", "film_url": "../allways-opus/films/mnemonil/",
        "scion": "SCION 067 · 093 · 094", "source_title": "Historical Museum Kitchen Exhibit", "source_year": "c. 1962",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-opus/films/mnemonil/mnemonil.mp4"),
        "in_s": 24.0, "out_s": 38.0, "crop_mode": "full", "has_sync_audio": True,
        "action": "The voiceover recalls an 'untouched kitchen' (plant, red chair, icebox)—until two visitors in coats step into frame behind a museum rope stanchion, quietly exposing the borrowed memory.",
        "nearmatch": "The emotional centerpiece of ALLWAYS: picture and museum rope break the narrator's claim of private memory without a single didactic caption.",
        "why_chosen": "The ONLY film in Opus 5.5's run to pass its blind critic ('VERDICT: pass, narrowly. Protect: the kitchen sequence at 23-40s. The narration lists details that match the frames, and the exhibit rope then breaks the claim without any comment.').",
        "critic_verdict": "PASS · Highest-rated passage in Opus 5.5"
    },
    {
        "pos": 23, "chapter": 5, "maker": "Gemini Argon", "run_id": "allways-argon",
        "film_title": "SCION 090 · THE CLOCK", "film_url": "../allways-argon/studio/cases/SCION_090_The_Clock_Horological_Montage.html",
        "scion": "SCION 090", "source_title": "Horological Archival Dial", "source_year": "c. 1950",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-argon/studio/films/SCION_090_The_Clock_Horological_Montage.mp4"),
        "in_s": 3.5, "out_s": 8.5, "crop_mode": "argon_center", "has_sync_audio": True,
        "action": "Close-up of an archival clock dial as the sweep hand marks the shared minute across disparate lives.",
        "nearmatch": "Marks the time elapsed in the museum kitchen before opening the door to the final empty room.",
        "why_chosen": "Passed Argon Round-2 Critic Tribunal: anchors the horological montage in a legible, unadorned timepiece.",
        "critic_verdict": "PASS · Horological anchor (Argon Round 2)"
    },
    {
        "pos": 24, "chapter": 5, "maker": "Claude Sonnet", "run_id": "allways-sonnet",
        "film_title": "057 · MOMENTS", "film_url": "../allways-sonnet/057-moments/",
        "scion": "SCION 057 · 086", "source_title": "Empty Domestic Room Aftermath", "source_year": "c. 1955",
        "source_url": "https://www.movingimagearchive.com",
        "video_path": os.path.join(REPO, "allways-sonnet/057-moments/057-moments.mp4"),
        "in_s": 44.0, "out_s": 48.5, "crop_mode": "full", "has_sync_audio": False,
        "action": "Seen through an open white door: an unoccupied chair, a small table with a telephone, and a lit lamp held in stillness after everyone has left.",
        "nearmatch": "Completes the circle begun in Cut 01: the chair by the window gives way to the empty chair and lit lamp after the occasion is over.",
        "why_chosen": "Explicitly protected by Sonnet's blind critic ('Strength to protect: the empty-room hold at 46.25–48.5') and embodies Between Takes: 'The room remains. That does not tell us everything about who left.'",
        "critic_verdict": "Strength to protect · Closing hold (Sonnet)"
    },
]

def make_card_png(path, kicker, title, subtitle, foot=""):
    im = Image.new("RGB", (W, H), (16, 15, 13))
    draw = ImageDraw.Draw(im)
    f_kick = get_font(16, mono=True)
    f_title = get_font(44, mono=False)
    f_sub = get_font(22, mono=False)
    f_foot = get_font(15, mono=True)

    draw.line([(96, 110), (W - 96, 110)], fill=(68, 63, 55), width=1)
    draw.text((96, 78), kicker.upper(), font=f_kick, fill=(184, 152, 104))
    draw.text((96, 165), title, font=f_title, fill=(244, 241, 233))

    y = 250
    for line in subtitle.split("\n"):
        draw.text((96, y), line, font=f_sub, fill=(208, 202, 190))
        y += 36

    draw.line([(96, H - 110), (W - 96, H - 110)], fill=(68, 63, 55), width=1)
    if foot:
        draw.text((96, H - 88), foot, font=f_foot, fill=(150, 144, 132))
    im.save(path, quality=95)

def make_lower_third_overlay(path, pos, maker, film_title, scion, source_title, source_year):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    f_top = get_font(14, mono=True)
    f_bot = get_font(18, mono=False)
    # Subtle dark translucent museum pill at bottom-left
    box_w = 780
    box_h = 62
    x0, y0 = 36, H - box_h - 28
    draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=4, fill=(14, 13, 11, 195), outline=(90, 84, 72, 160), width=1)
    top_line = f"CUT {pos:02d} / 24  ·  {maker.upper()}  ·  {film_title} ({scion})"
    bot_line = f"{source_title} ({source_year})"
    draw.text((x0 + 16, y0 + 10), top_line, font=f_top, fill=(205, 175, 120, 255))
    draw.text((x0 + 16, y0 + 31), bot_line, font=f_bot, fill=(244, 241, 233, 255))
    im.save(path)

def render_card_segment(png_path, dur_s, room_tone_wav, out_mp4):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(dur_s), "-i", png_path,
        "-ss", "0", "-t", str(dur_s), "-i", room_tone_wav,
        "-vf", f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st={max(0.1, dur_s-0.35):.2f}:d=0.35",
        "-af", f"afade=t=in:st=0:d=0.25,afade=t=out:st={max(0.1, dur_s-0.25):.2f}:d=0.25",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-shortest", out_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Step 1: Extracting warm archival 16mm optical room tone bed...")
room_tone_wav = os.path.join(WORK_DIR, "room_tone.wav")
subprocess.run([
    "ffmpeg", "-y",
    "-ss", "1.0", "-t", "12.0",
    "-i", os.path.join(REPO, "allways-opus/films/nobody-home/nobody-home.mp4"),
    "-af", "lowpass=f=1800,highpass=f=60,volume=-14dB,aloop=loop=4:size=480000",
    "-t", "20.0", "-ar", "48000", "-ac", "2", room_tone_wav
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

segment_files = []
timeline_cursor = 0.0
edl_records = []

# Opening Title Card (3.2s)
open_png = os.path.join(WORK_DIR, "card_open.png")
open_mp4 = os.path.join(WORK_DIR, "seg_000_open.mp4")
make_card_png(
    open_png,
    "PAELEO / ALLWAYS · ANTHOLOGY SYNTHESIS · OPUS 5.5 · ARGON · SOL · SONNET",
    "ALLWAYS — Cinema from the Rest of the Frame",
    "Twenty-four critic-protected passages hand-cut across all four makers.\nA camera points at an event. More happens than the event can contain.",
    "131 FILMS EXAMINED  ·  4 MAKERS  ·  6 MOVEMENTS  ·  NEARMATCH PRINCIPLE"
)
render_card_segment(open_png, 3.2, room_tone_wav, open_mp4)
segment_files.append(open_mp4)
timeline_cursor += 3.2

current_chapter = -1

for s in SHOTS:
    if s["chapter"] != current_chapter:
        current_chapter = s["chapter"]
        ch = CHAPTERS[current_chapter]
        ch_png = os.path.join(WORK_DIR, f"card_ch_{current_chapter+1}.png")
        ch_mp4 = os.path.join(WORK_DIR, f"seg_ch_{current_chapter+1}.mp4")
        make_card_png(
            ch_png,
            f"MOVEMENT {ch['num']}  ·  {ch['source']}",
            ch["title"],
            ch["quote"],
            "ALLWAYS ANTHOLOGY  ·  OPUS 5.5 · ARGON · SOL · SONNET"
        )
        render_card_segment(ch_png, 2.2, room_tone_wav, ch_mp4)
        segment_files.append(ch_mp4)
        timeline_cursor += 2.2

    pos = s["pos"]
    dur_s = round(s["out_s"] - s["in_s"], 2)
    ov_png = os.path.join(WORK_DIR, f"ov_{pos:02d}.png")
    make_lower_third_overlay(ov_png, pos, s["maker"], s["film_title"], s["scion"], s["source_title"], s["source_year"])

    if s["crop_mode"] == "argon_center":
        base_vf = f"crop=608:342:176:99,scale={W}:{H}"
    elif s["crop_mode"] == "argon_triptych":
        base_vf = f"crop=960:464:0:38,scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"
    elif s["crop_mode"] == "sol_clean":
        base_vf = f"crop=960:540:0:45,scale={W}:{H}"
    else:
        base_vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"

    seg_mp4 = os.path.join(WORK_DIR, f"seg_shot_{pos:02d}.mp4")
    # Overlay lower-third for first 2.8s with smooth fade out
    filter_complex = (
        f"[0:v]{base_vf},fps={FPS},format=yuv420p,"
        f"fade=t=in:st=0:d=0.15,fade=t=out:st={max(0.1, dur_s-0.15):.2f}:d=0.15[vbase];"
        f"[1:v]format=rgba,fade=t=in:st=0.15:d=0.25:alpha=1,fade=t=out:st=2.55:d=0.45:alpha=1[vov];"
        f"[vbase][vov]overlay=0:0:shortest=1,format=yuv420p[vout]"
    )

    if s["has_sync_audio"]:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(s["in_s"]), "-t", str(dur_s), "-i", s["video_path"],
            "-loop", "1", "-t", str(dur_s), "-i", ov_png,
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "0:a:0",
            "-af", f"aresample=48000,pan=stereo|c0=c0|c1=c0,loudnorm=I=-19:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.18,afade=t=out:st={max(0.1, dur_s-0.18):.2f}:d=0.18",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            "-shortest", seg_mp4
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(s["in_s"]), "-t", str(dur_s), "-i", s["video_path"],
            "-loop", "1", "-t", str(dur_s), "-i", ov_png,
            "-ss", str((pos * 0.7) % 8.0), "-t", str(dur_s), "-i", room_tone_wav,
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "2:a:0",
            "-af", f"afade=t=in:st=0:d=0.18,afade=t=out:st={max(0.1, dur_s-0.18):.2f}:d=0.18",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            "-shortest", seg_mp4
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_files.append(seg_mp4)

    # Extract clean thumbnail & 3-frame strip for the case study
    thumb_rel = f"img/shot-{pos:02d}.jpg"
    thumb_abs = os.path.join(OUT_DIR, thumb_rel)
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(dur_s * 0.55), "-i", seg_mp4,
        "-frames:v", "1", "-q:v", "2", thumb_abs
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rec = dict(s)
    rec["timeline_in"] = round(timeline_cursor, 2)
    rec["timeline_out"] = round(timeline_cursor + dur_s, 2)
    rec["dur_s"] = dur_s
    rec["thumb"] = thumb_rel
    edl_records.append(rec)
    timeline_cursor += dur_s
    print(f"  Rendered Cut {pos:02d}/24: [{s['maker']}] {s['film_title']} ({dur_s:.1f}s)")

# Closing Card (3.4s)
close_png = os.path.join(WORK_DIR, "card_close.png")
close_mp4 = os.path.join(WORK_DIR, "seg_999_close.mp4")
make_card_png(
    close_png,
    "ALLWAYS  ·  PAELEO  ·  MANY HANDS, ONE SLATE",
    "LOOK AGAIN.",
    "The cut belongs to the editor. The lives on either side do not.\nClaude Opus 5.5  ·  Gemini Argon  ·  OpenAI Sol  ·  Claude Sonnet",
    "24 CRITIC-PROTECTED PASSAGES  ·  MOVING IMAGE ARCHIVE  ·  OCTOBER–NOVEMBER 2026"
)
render_card_segment(close_png, 3.4, room_tone_wav, close_mp4)
segment_files.append(close_mp4)
timeline_cursor += 3.4

# Concatenate all segments
concat_txt = os.path.join(WORK_DIR, "concat.txt")
with open(concat_txt, "w") as f:
    for sf in segment_files:
        f.write(f"file '{sf}'\n")

master_mp4 = os.path.join(OUT_DIR, "allways-best.mp4")
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
    "-c:v", "libx264", "-preset", "fast", "-crf", "21",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    master_mp4
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Poster image (from Cut 01 / Cut 22 composite or Cut 22 iconic kitchen + Cut 01)
shutil.copy2(os.path.join(OUT_DIR, "img/shot-22.jpg"), os.path.join(OUT_DIR, "poster.jpg"))

# Build 24-frame temporal proof strip (img/reel.jpg)
tw, th = 320, 180
reel = Image.new("RGB", (tw * 4, (th + 28) * 6), (16, 15, 13))
rdraw = ImageDraw.Draw(reel)
f_lbl = get_font(12, mono=True)
for idx, rec in enumerate(edl_records):
    im = Image.open(os.path.join(OUT_DIR, rec["thumb"])).convert("RGB").resize((tw, th))
    c = idx % 4
    r = idx // 4
    x, y = c * tw, r * (th + 28)
    reel.paste(im, (x, y))
    rdraw.text((x + 6, y + th + 6), f"{rec['pos']:02d}. {rec['maker'].split()[-1]} · {rec['film_title'][:18]} ({rec['timeline_in']:.0f}s)", font=f_lbl, fill=(235, 230, 220))
reel.save(os.path.join(IMG_DIR, "reel.jpg"), quality=88)

with open(os.path.join(OUT_DIR, "edl.json"), "w") as f:
    json.dump({
        "title": "ALLWAYS — Cinema from the Rest of the Frame",
        "subtitle": "Twenty-four critic-protected passages across Claude Opus 5.5, Gemini Argon, OpenAI Sol, and Claude Sonnet",
        "duration_seconds": round(timeline_cursor, 2),
        "makers": ["Claude Opus 5.5 (Anthropic)", "Gemini Argon (Google DeepMind)", "OpenAI Sol (OpenAI)", "Claude Sonnet (Anthropic)"],
        "chapters": CHAPTERS,
        "shots": edl_records
    }, f, indent=2)

print(f"SUCCESS: Rendered {master_mp4} ({timeline_cursor:.1f}s, {os.path.getsize(master_mp4)/1e6:.2f} MB)")
