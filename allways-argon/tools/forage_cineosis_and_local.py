#!/usr/bin/env python3
"""
Harvests matching shots, spoken transcripts, and sound examples from:
1. Cineosis Lab (cineosis_lab_data.json: 15,451 shots with signs, wygwyl observations, found queries, hue/lum/sat, audio)
2. Cineosis Lab Transcripts (cineosis_transcripts.json: 2,960 word-timestamped clips)
3. Cineosis Lab Sound Table (cineosis_sound_table.json)
4. Local Moving Image Archive 345-Term Dataset (6,352 unique local MP4 clips)
"""

import json
import os
from collections import defaultdict
from pathlib import Path

STUDIO_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
FORAGE_DIR = STUDIO_DIR / "forage"
LOCAL_DATASET = Path("/Users/gaia/WORLDBUILDING-TERMS/moving_image_archive_dataset")


def main():
    lab_data = json.load(open(FORAGE_DIR / "cineosis_lab_data.json"))
    transcripts = json.load(open(FORAGE_DIR / "cineosis_transcripts.json"))
    sound_table = json.load(open(FORAGE_DIR / "cineosis_sound_table.json"))

    local_videos = set()
    local_vid_dir = LOCAL_DATASET / "media" / "videos"
    if local_vid_dir.exists():
        local_videos = {p.stem for p in local_vid_dir.glob("*.mp4")}

    # Index local dataset by term_slug
    local_by_term = defaultdict(list)
    meta_jsonl = LOCAL_DATASET / "metadata.jsonl"
    if meta_jsonl.exists():
        with open(meta_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                local_by_term[row["term_slug"]].append(row)

    shots = [s for s in lab_data["shots"] if str(s.get("video", "")).startswith("http")]
    shot_by_id = {s["id"]: s for s in shots}

    # Build text index over Cineosis shots (signs note, found query, wygwyl observed/queries, title)
    def shot_text(s):
        parts = [str(s.get("title") or "")]
        for sg in s.get("signs") or []:
            parts.append(str(sg.get("note") or ""))
            parts.append(str(sg.get("flip") or ""))
        for fd in s.get("found") or []:
            parts.append(str(fd.get("q") or ""))
        wyg = s.get("wygwyl")
        if isinstance(wyg, dict):
            parts.append(str(wyg.get("observed") or ""))
            parts.append(str(wyg.get("use") or ""))
            parts.extend(str(q) for q in (wyg.get("queries") or []))
        if s["id"] in transcripts:
            words = transcripts[s["id"]].get("words", [])
            parts.append(" ".join(w[0] for w in words))
        return " | ".join(p for p in parts if p).lower()

    annotated_shots = []
    for s in shots:
        txt = shot_text(s)
        has_rich_meta = bool(s.get("signs") or s.get("found") or s.get("wygwyl") or s["id"] in transcripts)
        if has_rich_meta:
            annotated_shots.append((s, txt))

    print(f"Total R2 shots in Cineosis Lab: {len(shots)}")
    print(f"Richly annotated / transcribed shots in Cineosis Lab: {len(annotated_shots)}")
    print(f"Local dataset clips on disk: {len(local_videos)}")

    # Find spoken word occurrences in transcripts for SCION 055 (Words) and B-ROLL 08 (HOMONYM)
    word_hits = defaultdict(list)
    for cid, tr in transcripts.items():
        words = tr.get("words", [])
        full_sentence = " ".join(w[0] for w in words)
        for w, ts in words:
            clean = w.lower().strip(".,!?;:\"'()-")
            if clean in {"draw", "line", "light", "turn", "hand", "work", "time", "play", "run", "hold", "drop", "clear", "open", "fall", "break", "rest", "point", "room", "water", "paper", "chair", "door", "laugh", "breath", "circle", "ball", "color", "yellow", "blue", "red"}:
                word_hits[clean].append({
                    "clip_id": cid,
                    "title": tr.get("title"),
                    "year": tr.get("year"),
                    "video": tr.get("video"),
                    "thumb": tr.get("thumb"),
                    "word": clean,
                    "timestamp": ts,
                    "transcript": full_sentence,
                    "in_local": cid in local_videos,
                })

    # Find chromatic shots in Cineosis Lab for SCION 062 (Colors: yellow, blue, red)
    yellow_shots = []
    blue_shots = []
    red_shots = []
    for s, txt in annotated_shots:
        hue = s.get("hue")
        sat = s.get("sat") or 0
        lum = s.get("lum") or 0.5
        if hue is not None and sat >= 0.35 and 0.2 <= lum <= 0.85:
            if 42 <= hue <= 68:
                yellow_shots.append({"id": s["id"], "title": s.get("title"), "year": s.get("year"), "hue": hue, "sat": sat, "video": s["video"], "text": txt[:180], "in_local": s["id"] in local_videos})
            elif 195 <= hue <= 245:
                blue_shots.append({"id": s["id"], "title": s.get("title"), "year": s.get("year"), "hue": hue, "sat": sat, "video": s["video"], "text": txt[:180], "in_local": s["id"] in local_videos})
            elif hue <= 18 or hue >= 345:
                red_shots.append({"id": s["id"], "title": s.get("title"), "year": s.get("year"), "hue": hue, "sat": sat, "video": s["video"], "text": txt[:180], "in_local": s["id"] in local_videos})

    yellow_shots.sort(key=lambda x: -x["sat"])
    blue_shots.sort(key=lambda x: -x["sat"])
    red_shots.sort(key=lambda x: -x["sat"])

    # Keyword search across annotated Cineosis shots
    themes = {
        "laugh": ["laugh", "giggle", "chuckle", "smiling", "grin"],
        "chair_sit": ["chair", "sitting", "bench", "seat", "sofa", "armchair"],
        "hands_gesture": ["hand", "fingers", "palm", "touch", "grasping", "holding", "picking up", "placing"],
        "door_threshold": ["door", "doorway", "threshold", "entering", "leaving", "latch", "corridor"],
        "water_pour_surface": ["water", "pouring", "cup", "glass", "ripples", "droplet", "rain", "pond"],
        "breath_wind_smoke": ["breath", "wind", "smoke", "fog", "mist", "dust", "flutter", "breeze", "fan"],
        "circle_ball_wheel": ["circle", "round", "wheel", "clock", "ball", "sphere", "globe", "ring", "coin"],
        "curve_arc_chain": ["chain", "arc", "curve", "rope", "cable", "bridge", "parabola", "swing", "throw"],
        "work_labor_machine": ["worker", "factory", "machine", "assembly", "loom", "sweeping", "washing", "hammer", "lathe", "tool"],
        "run_chase_pursuit": ["running", "runner", "chasing", "fleeing", "sprinting", "hurrying"],
        "film_decay_scratch": ["scratch", "grain", "damaged", "leader", "flicker", "blur", "abstract", "texture"],
        "tableau_room": ["wide shot", "room", "office", "table", "waiting", "crowd", "interior"],
    }

    theme_matches = {}
    for th, kws in themes.items():
        matches = []
        for s, txt in annotated_shots:
            hit_kws = [kw for kw in kws if kw in txt]
            if hit_kws:
                matches.append({
                    "id": s["id"],
                    "title": s.get("title"),
                    "year": s.get("year"),
                    "video": s.get("video"),
                    "thumb": s.get("thumb"),
                    "start": s.get("start"),
                    "end": s.get("end"),
                    "scale": s.get("scale"),
                    "audio_kind": (s.get("audio") or {}).get("kind"),
                    "hit_kws": hit_kws,
                    "text": txt[:240],
                    "in_local": s["id"] in local_videos,
                })
        matches.sort(key=lambda m: (len(m["hit_kws"]), m["in_local"]), reverse=True)
        theme_matches[th] = matches[:60]
        print(f"Theme {th:20s}: {len(matches):4d} Cineosis matches")

    out = {
        "word_hits": {k: v[:40] for k, v in word_hits.items()},
        "chromatic": {
            "yellow": yellow_shots[:40],
            "blue": blue_shots[:40],
            "red": red_shots[:40],
        },
        "theme_matches": theme_matches,
    }
    (FORAGE_DIR / "cineosis_harvest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Saved cineosis_harvest.json successfully.")


if __name__ == "__main__":
    main()
