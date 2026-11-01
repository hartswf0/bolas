#!/usr/bin/env python3
"""
ALLWAYS Archive Forager (Moving Image Archive Live API + Cineosis Lab + Local Dataset)
Forages targeted micro-moments, ordinary gestures, overlooked work, material surfaces,
and polysemic actions for:
  - Series A: SCION 055–065 (11 Conceptual Microfilms)
  - Series B: B-ROLL OF CIVILIZATION (12 ALLWAYS Proposed Works)
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

STUDIO_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
FORAGE_DIR = STUDIO_DIR / "forage"
CLIPS_DIR = STUDIO_DIR / "clips"
THUMBS_DIR = STUDIO_DIR / "thumbs"
LOCAL_DATASET_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/moving_image_archive_dataset")

FORAGE_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_URL = "https://www.movingimagearchive.com/api/search"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# Targeted live archive forage queries grouped by film/operator
FORAGE_QUERIES = {
    # SCION 055: Words — Polysemic Relay ('draw')
    "s055_draw_line": "hand drawing a line with pencil or pen on paper close up",
    "s055_draw_curtain": "person drawing or pulling back a window curtain in a room",
    "s055_draw_drawer": "hand pulling open a wooden desk drawer close up",
    "s055_draw_closer": "group of people leaning in and drawing closer around a table to inspect an object",
    "s055_draw_water": "person drawing water or pulling a bucket up with a rope",
    # SCION 056: Symmetry — Imperfect Pairing & B-ROLL 09: ANYBODY, ANYWHERE
    "s056_sit_chair_a": "person pulling out a chair and sitting down at a table",
    "s056_sit_chair_b": "woman sitting down in a chair in a living room and pausing",
    "s056_tie_knot_a": "two hands tying a knot in rope or string close up",
    "s056_tie_shoe_b": "hands tying shoelaces or untangling a knot close up",
    "s056_wait_chair": "person standing and waiting beside an empty chair in a room",
    "s056_pull_chair": "person pulling a wooden chair away from a table",
    # SCION 057: Moments — Microevent Attention & B-ROLL 02: ALMOST HUMAN
    "s057_sleeve_handle": "sleeve or coat catching on a door handle close up",
    "s057_water_cup": "water pouring into a glass or cup nearly to the rim close up",
    "s057_door_latch": "hand turning a doorknob or latch clicking shut close up",
    "s057_place_key": "hand placing a key or small metal object onto a wooden table close up",
    "s057_shake_cloth": "person shaking out a tablecloth or bedsheet and letting it settle",
    "s057_empty_room": "empty room or open doorway just after a person walks out",
    "b02_adjust_collar": "man or woman adjusting shirt collar or necktie with hand",
    "b02_check_wrist": "person glancing at wristwatch and looking away in hesitation",
    "b02_hesitate_door": "person hesitating at a doorway before stepping inside",
    # SCION 058: Laughs! — Audible Contagion
    "s058_hold_laugh": "person trying to hold back a laugh with hand near mouth",
    "s058_woman_laugh": "woman laughing warmly in close up",
    "s058_man_laugh": "man laughing out loud in conversation",
    "s058_group_laugh": "people laughing together around a table and recovering",
    # SCION 059: Ball — Graphic Constancy Across Sources
    "s059_clock_face": "round clock face centered in close up",
    "s059_wheel_round": "round spinning wheel centered in close up",
    "s059_ceramic_bowl": "round bowl or plate viewed from directly above",
    "s059_play_ball": "child or athlete holding a round ball in hands",
    "s059_radar_scope": "round radar screen or circular gauge dial close up",
    # SCION 060: Losers — Social Position Through Montage
    "s060_awkward_chair": "person trying to squeeze a chair into a crowded table",
    "s060_table_group": "people working together around a shared worktable passing papers",
    "s060_isolated_worker": "one person sitting apart at the end of a long table looking on",
    "s060_pass_work": "person handing a folder or tool to another person across a desk",
    # SCION 061: Matter — Material Affordance Chain
    "s061_bend_paper": "hands pressing and bending a sheet of paper under a weight on a desk",
    "s061_crease_cloth": "hands folding and creasing a piece of cloth on a table",
    "s061_wet_paper": "water wetting paper or brush spreading liquid across a sheet",
    "s061_weathered_paint": "close up of cracked weathered paint or worn wooden surface",
    # SCION 062: Colors — Chromatic Chapters
    "s062_yellow_glove": "yellow work gloves or hands holding a bright yellow tool",
    "s062_yellow_repair": "worker repairing or painting a yellow machine part",
    "s062_blue_work": "hands working with blue cloth or a blue painted object",
    "s062_red_practical": "hands using a red tool or placing a red cup on a workbench",
    # SCION 063: Breath — Invisible Force, Visible Consequence
    "s063_blow_dust": "person gently blowing dust off an object or book page",
    "s063_paper_flutter": "thin paper strip or light curtain fluttering gently in air",
    "s063_condensation": "steam or breath condensation fogging a glass window pane",
    "s063_electric_fan": "small electric desk fan spinning and blowing air",
    # SCION 064: Parabolas (etc.) — Curves With Different Causes
    "s064_hanging_chain": "hanging metal chain or cable sagging in a catenary curve",
    "s064_thrown_arc": "ball or object tossed in a curved arc through the air",
    "s064_bent_strip": "hands bending a flexible strip of wood or metal into an arch",
    "s064_water_arc": "stream of water arcing from a hose or fountain",
    # SCION 065: Five — Parallel Lives, Unequal Details & B-ROLL 10: COLLECTIVE INVENTORIES
    "s065_wash_hands": "person washing hands with soap and water at a basin",
    "s065_sweep_floor": "person sweeping a room or porch with a broom",
    "s065_knead_bread": "hands kneading dough or preparing food on a kitchen table",
    "s065_carry_load": "worker carrying a crate or basket through a doorway",
    "s065_light_candle": "person lighting a candle or arranging objects quietly on a table",
    "b10_clear_table": "person clearing dishes and cups from a table after a meal",
    # Remaining B-ROLL OF CIVILIZATION specific queries
    "b01_enter_room_chair": "person entering a room, setting a cup on a table, and moving a chair",
    "b01_empty_room_chair": "empty living room with chairs and table in natural light",
    "b03_film_scratch": "damaged 16mm archival film frame with scratches and light leaks",
    "b03_film_leader": "film leader with sprocket holes, splice tape, and emulsion decay",
    "b04_hand_release": "close up of a hand letting go and dropping an object",
    "b04_object_impact": "dropped object or glass hitting the floor in close up",
    "b05_runner_street": "person running fast down a city street",
    "b05_runner_field": "person running across an open field or park",
    "b05_runner_stop": "runner stopping to catch breath while traffic or crowd moves past",
    "b06_factory_repeat": "factory worker repeating a mechanical hand motion at a machine",
    "b06_machine_maintenance": "worker stopping a machine to oil, wipe, or adjust a part",
    "b06_loom_weaver": "worker operating a textile loom or sewing machine in a workshop",
    "b07_archive_cards": "clerk or archivist flipping through index cards and film cans",
    "b11_home_movie_room": "1950s family home movie inside a living room",
    "b11_home_movie_yard": "amateur home movie of people in a backyard garden",
    "b12_locked_tableau": "static wide shot of an office or workshop with people working in foreground and background",
}


def fetch_query(slug: str, query: str) -> dict:
    cache_file = FORAGE_DIR / f"query_{slug}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if data.get("clips"):
                return data
        except Exception:
            pass

    payload = json.dumps({
        "query": query,
        "color": "all",
        "aspectRatio": "all",
        "offset": 0,
    }).encode("utf-8")

    for attempt in range(6):
        try:
            req = urllib.request.Request(
                SEARCH_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
            record = {
                "slug": slug,
                "query": query,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "clip_count": len(res_json.get("clips", [])),
                "clips": res_json.get("clips", []),
            }
            cache_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
            return record
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
    return {"slug": slug, "query": query, "clip_count": 0, "clips": []}


def main():
    print(f"Foraging {len(FORAGE_QUERIES)} targeted queries on Moving Image Archive...")
    results = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(fetch_query, k, q): (k, q) for k, q in FORAGE_QUERIES.items()}
        done = 0
        for fut in as_completed(futs):
            k, q = futs[fut]
            done += 1
            rec = fut.result()
            results[k] = rec
            if done % 10 == 0 or done == len(FORAGE_QUERIES):
                print(f"  [{done}/{len(FORAGE_QUERIES)}] {k}: {rec['clip_count']} clips")

    # Save master forage index
    all_foraged_clips = {}
    for k, rec in results.items():
        for rank, c in enumerate(rec.get("clips", []), 1):
            cid = c["id"]
            if cid not in all_foraged_clips:
                all_foraged_clips[cid] = {
                    **c,
                    "matched_queries": [],
                }
            all_foraged_clips[cid]["matched_queries"].append({
                "slug": k,
                "query": rec["query"],
                "rank": rank,
                "score": c.get("score"),
            })

    summary = {
        "total_queries": len(FORAGE_QUERIES),
        "total_unique_clips": len(all_foraged_clips),
        "queries": results,
    }
    (FORAGE_DIR / "live_forage_index.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved live_forage_index.json with {len(all_foraged_clips)} unique clips across {len(FORAGE_QUERIES)} queries.")


if __name__ == "__main__":
    main()
