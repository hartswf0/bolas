#!/usr/bin/env python3
"""
Builds the super-minimal, phone-first professional ALLWAYS Screening Index
at /Users/gaia/WORLDBUILDING-TERMS/allways_studio/index.html (and watch.html).
"""
import json
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
MANIFESTS_DIR = BASE_DIR / "manifests"
FORAGE_DIR = BASE_DIR / "forage"
OUT_HTML = BASE_DIR / "index.html"
WATCH_HTML = BASE_DIR / "watch.html"


def normalize_manifest(m: dict, pool: dict) -> dict:
    slug = m.get("slug", "")
    raw_series = m.get("series", "")
    if "MICROFILMS" in raw_series or raw_series == "SERIES_A":
        cat = "series_a"
        series_short = "055–065 Microfilms"
    elif "BROLL" in raw_series or raw_series == "SERIES_B":
        cat = "series_b"
        series_short = "B-Roll of Civilization"
    elif "STRUCTURAL" in raw_series or raw_series == "SERIES_C":
        cat = "series_c"
        series_short = "066–074 Structural"
    elif "OBSERVATIONAL" in raw_series or raw_series == "SERIES_D":
        cat = "series_d"
        series_short = "075–082 Observational"
    elif "FRAMING" in raw_series or "ESSAYS" in raw_series or raw_series == "SERIES_E":
        cat = "series_e"
        series_short = "083–094 Essays & Frame"
    elif "INTERACTIVE" in raw_series or raw_series == "SERIES_F":
        cat = "series_f"
        series_short = "095–113 Interactive"
    elif "STUDIES" in raw_series or raw_series == "SERIES_G":
        cat = "studies"
        series_short = "ALLWAYS Studies"
    elif "COLLECTIONS" in raw_series or raw_series == "SERIES_H":
        cat = "collections"
        series_short = "ALLWAYS Collections"
    else:
        cat = "series_a"
        series_short = "ALLWAYS Archive"

    kicker = m.get("kicker", "")
    if slug.startswith("BROLL_"):
        code_badge = slug.split("_")[0] + " " + slug.split("_")[1]
    elif slug.startswith("STUDY_"):
        code_badge = "STUDY " + slug.split("_")[1]
    elif slug.startswith("COLL_"):
        code_badge = "COLL " + slug.split("_")[1]
    elif m.get("scion_id"):
        code_badge = f"SCION {int(m['scion_id']):03d}"
    else:
        code_badge = kicker.split("·")[0].strip()[:12]

    def make_source_entry(sub_val, fallback_title="Archival Source", fallback_year=None, fallback_page=None, fallback_in=0.0):
        if isinstance(sub_val, dict):
            cid = sub_val.get("clip_id") or sub_val.get("id") or ""
            p_meta = pool.get(cid, {})
            return {
                "clip_id": cid,
                "source_title": sub_val.get("source_title") or sub_val.get("title") or p_meta.get("title") or fallback_title,
                "source_year": sub_val.get("source_year") or sub_val.get("year") or p_meta.get("year") or fallback_year,
                "source_page_url": sub_val.get("source_page") or sub_val.get("page") or p_meta.get("page_url") or f"https://www.movingimagearchive.com/clips/{cid}",
                "trim_start_sec": sub_val.get("in_s", fallback_in),
            }
        elif isinstance(sub_val, str) and sub_val:
            cid = sub_val
            p_meta = pool.get(cid)
            if not p_meta:
                for k, v in pool.items():
                    if k.startswith(sub_val):
                        cid = k
                        p_meta = v
                        break
            p_meta = p_meta or {}
            return {
                "clip_id": cid,
                "source_title": fallback_title if fallback_title != "Archival Source" else (p_meta.get("title") or "Archival Source"),
                "source_year": fallback_year if fallback_year is not None else p_meta.get("year"),
                "source_page_url": fallback_page or p_meta.get("page_url") or f"https://www.movingimagearchive.com/clips/{cid}",
                "trim_start_sec": fallback_in,
            }
        return None

    segments = []
    t_cursor = 0.0
    edl_list = m.get("edl", [])
    has_explicit_cards = bool(edl_list and edl_list[0].get("type") == "title_card")

    if not has_explicit_cards:
        open_dur = 3.0
        segments.append({
            "idx": 1,
            "mode": "card",
            "start": round(t_cursor, 2),
            "end": round(t_cursor + open_dur, 2),
            "dur": open_dur,
            "label": "Opening Slate",
            "note": m.get("title", ""),
            "sources": [],
        })
        t_cursor += open_dur

    first_thumb_cid = ""
    for idx, e in enumerate(edl_list, start=1 if has_explicit_cards else 2):
        etype = e.get("type", "shot")
        dur = float(e.get("dur_s", 3.0))
        s_sec = float(e.get("start_sec", t_cursor))
        e_sec = float(e.get("end_sec", s_sec + dur))
        mode_map = {
            "title_card": "card",
            "closing_ledger": "card",
            "shot": "shot",
            "intertitle": "card",
            "split_shot": "split",
            "triptych_shot": "triptych",
            "reframe_shot": "reframe",
            "circle_reg_shot": "circle",
            "quad_shot": "quad",
            "curve_guide_shot": "curve",
            "erasure_shot": "erasure",
            "carrier_bridge_shot": "bridge",
        }
        mode = mode_map.get(etype, "shot")
        sources = []

        if etype in ("shot", "reframe_shot", "circle_reg_shot", "curve_guide_shot", "erasure_shot"):
            s_entry = make_source_entry(
                e.get("clip_id", ""),
                fallback_title=e.get("source_title", "Archival Source"),
                fallback_year=e.get("source_year"),
                fallback_page=e.get("source_page"),
                fallback_in=e.get("in_s", 0.0),
            )
            if s_entry:
                sources.append(s_entry)
        elif etype in ("split_shot", "carrier_bridge_shot"):
            for k in ("clip_a", "clip_b"):
                s_entry = make_source_entry(e.get(k))
                if s_entry:
                    sources.append(s_entry)
        elif etype in ("quad_shot", "triptych_shot"):
            for sub in e.get("clips", []):
                s_entry = make_source_entry(sub)
                if s_entry:
                    sources.append(s_entry)

        if not first_thumb_cid and sources:
            first_thumb_cid = sources[0]["clip_id"]

        label = e.get("phase") or e.get("title") or etype.replace("_", " ").upper()
        note = e.get("action") or ""
        nearmatch = e.get("nearmatch") or ""

        segments.append({
            "idx": idx,
            "mode": mode,
            "start": round(s_sec, 2),
            "end": round(e_sec, 2),
            "dur": round(dur, 2),
            "label": str(label),
            "note": str(note),
            "nearmatch": str(nearmatch),
            "sources": sources,
        })
        t_cursor = e_sec

    if not has_explicit_cards:
        close_dur = max(2.0, round(float(m.get("duration_seconds", t_cursor + 3.5)) - t_cursor, 2))
        segments.append({
            "idx": len(segments) + 1,
            "mode": "card",
            "start": round(t_cursor, 2),
            "end": round(t_cursor + close_dur, 2),
            "dur": close_dur,
            "label": "Closing Ledger",
            "note": m.get("boundary_note", ""),
            "nearmatch": "",
            "sources": [],
        })

    return {
        "id": slug,
        "cat": cat,
        "series_short": series_short,
        "code": code_badge,
        "scion_id": m.get("scion_id") or 55,
        "supporting": m.get("supporting_scions", []),
        "title": m.get("title", ""),
        "subtitle": m.get("subtitle", ""),
        "lineage": m.get("lineage", ""),
        "theorem": m.get("theorem", ""),
        "boundary": m.get("boundary_note", ""),
        "dur": round(float(m.get("duration_seconds", t_cursor)), 1),
        "thumb": f"thumbs/{first_thumb_cid}.jpg" if first_thumb_cid else "",
        "strip": f"forage/critic_strips/{slug}_v2_strip.jpg",
        "critic": m.get("critic_tribunal", {}),
        "segments": segments,
    }


def build():
    pool_path = FORAGE_DIR / "candidate_pool_metadata.json"
    pool = json.loads(pool_path.read_text()) if pool_path.exists() else {}

    # Order: Series A (055-065), B-Roll (01-12), Series C-F (066-113), Studies (01-06), Collections (01-05)
    manifest_paths = (
        sorted(MANIFESTS_DIR.glob("SCION_05*.json"))
        + sorted(MANIFESTS_DIR.glob("SCION_06[0-5]*.json"))
        + sorted(MANIFESTS_DIR.glob("BROLL_*.json"))
        + sorted(MANIFESTS_DIR.glob("SCION_06[6-9]*.json"))
        + sorted(MANIFESTS_DIR.glob("SCION_0[7-9]*.json"))
        + sorted(MANIFESTS_DIR.glob("SCION_1*.json"))
        + sorted(MANIFESTS_DIR.glob("STUDY_*.json"))
        + sorted(MANIFESTS_DIR.glob("COLL_*.json"))
    )
    # Deduplicate while preserving order
    seen = set()
    ordered_paths = []
    for p in manifest_paths:
        if p.name not in seen:
            seen.add(p.name)
            ordered_paths.append(p)

    raw_manifests = [json.loads(p.read_text()) for p in ordered_paths]
    (MANIFESTS_DIR / "all_films_manifest.json").write_text(json.dumps(raw_manifests, indent=2))
    films = [normalize_manifest(m, pool) for m in raw_manifests]

    data_json = json.dumps(films, ensure_ascii=False)

    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="theme-color" content="#0a0a0a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>ALLWAYS — 85 Handmade Archival Films</title>
<style>
  :root {
    --bg: #0a0a0a;
    --bg-elev: #121212;
    --bg-hover: #191919;
    --bg-active: #1f1d18;
    --ink: #f3efe6;
    --ink-muted: #9a9488;
    --ink-dim: #5e5a52;
    --accent: #d8c395;
    --mint: #8cc5a6;
    --line: rgba(255, 255, 255, 0.08);
    --line-strong: rgba(255, 255, 255, 0.16);
    --sans: -apple-system, BlinkMacSystemFont, "Inter", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    --serif: "Instrument Serif", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    --mono: "JetBrains Mono", "SF Mono", "Menlo", Consolas, monospace;
  }

  [data-theme="light"] {
    --bg: #f6f3ec;
    --bg-elev: #ffffff;
    --bg-hover: #ece7dc;
    --bg-active: #e6dfd0;
    --ink: #141311;
    --ink-muted: #625d53;
    --ink-dim: #948e82;
    --accent: #8c5a2b;
    --mint: #1d6b47;
    --line: rgba(0, 0, 0, 0.08);
    --line-strong: rgba(0, 0, 0, 0.16);
  }

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-tap-highlight-color: transparent;
  }

  html, body {
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.4;
    -webkit-font-smoothing: antialiased;
    overscroll-behavior-y: none;
  }

  /* Minimal Top Bar */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid var(--line);
    background: var(--bg);
  }
  .brand {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .brand-name {
    font-family: var(--mono);
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.14em;
  }
  .brand-meta {
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--ink-muted);
  }
  .topbar-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .pill-btn {
    background: transparent;
    color: var(--ink-muted);
    border: 1px solid var(--line-strong);
    border-radius: 999px;
    padding: 4px 9px;
    font-family: var(--mono);
    font-size: 0.66rem;
    cursor: pointer;
    transition: all 0.15s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .pill-btn:hover, .pill-btn.on {
    color: var(--bg);
    background: var(--ink);
    border-color: var(--ink);
  }

  /* App Layout: Mobile = Sticky Top Player + Scroll List; Desktop = Split Grid */
  .layout {
    display: flex;
    flex-direction: column;
    min-height: calc(100dvh - 41px);
  }

  /* Sticky Player Deck */
  .player-deck {
    position: sticky;
    top: 0;
    z-index: 60;
    background: var(--bg);
    border-bottom: 1px solid var(--line-strong);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
  }
  .video-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    overflow: hidden;
  }
  video#player {
    width: 100%;
    height: 100%;
    display: block;
    background: #000;
  }

  /* Segmented Scrubber directly under video */
  .cut-bar {
    display: flex;
    height: 10px;
    background: #050505;
    gap: 1px;
    cursor: pointer;
    user-select: none;
  }
  .cut-seg {
    height: 100%;
    background: rgba(255, 255, 255, 0.16);
    transition: background 0.12s ease;
  }
  [data-theme="light"] .cut-bar {
    background: #d8d2c5;
  }
  [data-theme="light"] .cut-seg {
    background: rgba(0, 0, 0, 0.18);
  }
  .cut-seg.is-card {
    background: rgba(255, 255, 255, 0.07);
  }
  .cut-seg.active {
    background: var(--accent);
  }

  /* Live Cut Telemetry Line */
  .live-shot-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 14px;
    background: var(--bg-elev);
    border-bottom: 1px solid var(--line);
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--ink-muted);
    white-space: nowrap;
    overflow: hidden;
  }
  .live-shot-text {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .live-shot-text strong {
    color: var(--mint);
    font-weight: 600;
  }
  .live-time {
    color: var(--ink-dim);
    flex-shrink: 0;
  }

  /* Now Playing Control Strip */
  .now-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 14px;
    background: var(--bg);
  }
  .now-info {
    min-width: 0;
    flex: 1;
  }
  .now-kicker {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--accent);
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .now-title {
    font-family: var(--serif);
    font-size: 1.18rem;
    font-weight: 400;
    line-height: 1.15;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
  }
  .now-controls {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
  }
  .icon-btn {
    background: var(--bg-elev);
    color: var(--ink);
    border: 1px solid var(--line-strong);
    border-radius: 5px;
    height: 32px;
    padding: 0 10px;
    font-family: var(--mono);
    font-size: 0.72rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  .icon-btn:active {
    transform: scale(0.96);
  }
  .icon-btn.active {
    background: var(--accent);
    color: #0a0a0a;
    border-color: var(--accent);
    font-weight: 600;
  }

  /* Expandable Info / EDL Drawer */
  .info-drawer {
    display: none;
    max-height: 44dvh;
    overflow-y: auto;
    padding: 12px 14px 16px;
    background: var(--bg-elev);
    border-top: 1px solid var(--line);
    font-size: 0.8rem;
    -webkit-overflow-scrolling: touch;
  }
  .info-drawer.open {
    display: block;
  }
  .theorem-box {
    color: var(--ink-muted);
    margin-bottom: 10px;
    line-height: 1.45;
  }
  .theorem-box strong {
    color: var(--ink);
    font-family: var(--mono);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .drawer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }
  .edl-mini-list {
    list-style: none;
    border-top: 1px solid var(--line);
  }
  .edl-mini-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding: 7px 4px;
    border-bottom: 1px solid var(--line);
    cursor: pointer;
    font-size: 0.75rem;
  }
  .edl-mini-row:hover {
    background: var(--bg-hover);
  }
  .edl-mini-row.active {
    background: var(--bg-active);
    color: var(--accent);
  }
  .edl-mini-left {
    min-width: 0;
    flex: 1;
  }
  .edl-mini-time {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--ink-dim);
    margin-right: 6px;
  }
  .edl-mini-src {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--mint);
    flex-shrink: 0;
    text-decoration: none;
  }

  /* Filter & Search Bar */
  .index-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding-bottom: env(safe-area-inset-bottom, 20px);
  }
  .filter-bar {
    position: sticky;
    top: 0;
    z-index: 30;
    background: var(--bg);
    border-bottom: 1px solid var(--line);
    padding: 8px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .cat-scroll {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .cat-scroll::-webkit-scrollbar {
    display: none;
  }
  .cat-pill {
    flex-shrink: 0;
    background: var(--bg-elev);
    color: var(--ink-muted);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 5px 11px;
    font-family: var(--mono);
    font-size: 0.68rem;
    cursor: pointer;
    white-space: nowrap;
  }
  .cat-pill.active {
    background: var(--ink);
    color: var(--bg);
    border-color: var(--ink);
    font-weight: 600;
  }
  .search-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .search-input {
    width: 100%;
    background: var(--bg-elev);
    color: var(--ink);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 6px 10px;
    font-family: var(--sans);
    font-size: 0.8rem;
    outline: none;
  }
  .search-input:focus {
    border-color: var(--accent);
  }

  /* Minimal Numbered Film List */
  .film-list {
    list-style: none;
  }
  .film-row {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--line);
    cursor: pointer;
    transition: background 0.12s ease;
  }
  .film-row:hover {
    background: var(--bg-hover);
  }
  .film-row.active {
    background: var(--bg-active);
  }
  .row-num {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--ink-dim);
    width: 22px;
    text-align: right;
    flex-shrink: 0;
  }
  .film-row.active .row-num {
    color: var(--accent);
    font-weight: 700;
  }
  .row-thumb {
    width: 56px;
    height: 32px;
    border-radius: 3px;
    object-fit: cover;
    background: #1a1a1a;
    border: 1px solid var(--line);
    flex-shrink: 0;
  }
  .row-main {
    min-width: 0;
    flex: 1;
  }
  .row-title {
    font-weight: 500;
    font-size: 0.88rem;
    color: var(--ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .film-row.active .row-title {
    color: var(--accent);
  }
  .row-sub {
    font-size: 0.73rem;
    color: var(--ink-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
  }
  .row-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    flex-shrink: 0;
  }
  .row-code {
    font-family: var(--mono);
    font-size: 0.64rem;
    color: var(--ink-muted);
    background: var(--bg-elev);
    border: 1px solid var(--line);
    padding: 1px 5px;
    border-radius: 3px;
  }
  .row-dur {
    font-family: var(--mono);
    font-size: 0.66rem;
    color: var(--ink-dim);
  }

  /* Proof Strip Lightbox Modal */
  .modal {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.92);
    flex-direction: column;
  }
  .modal.open {
    display: flex;
  }
  .modal-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    font-family: var(--mono);
    font-size: 0.75rem;
    color: #fff;
  }
  .modal-body {
    flex: 1;
    overflow: auto;
    padding: 12px;
    -webkit-overflow-scrolling: touch;
  }
  .modal-body img {
    width: 100%;
    max-width: 1200px;
    height: auto;
    display: block;
    margin: 0 auto;
    border-radius: 4px;
  }

  /* Desktop Two-Column Refinement */
  @media (min-width: 920px) {
    .layout {
      flex-direction: row;
      height: calc(100dvh - 41px);
      overflow: hidden;
    }
    .player-deck {
      position: relative;
      flex: 1;
      display: flex;
      flex-direction: column;
      border-bottom: none;
      border-right: 1px solid var(--line-strong);
      box-shadow: none;
      overflow-y: auto;
    }
    .video-wrap {
      max-height: 64dvh;
    }
    .info-drawer {
      display: block !important;
      max-height: none;
      flex: 1;
    }
    .index-pane {
      width: 430px;
      flex: none;
      height: 100%;
      overflow-y: auto;
    }
    #info-toggle-btn {
      display: none;
    }
  }
</style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <span class="brand-name">ALLWAYS</span>
    <span class="brand-meta">85 ARCHIVAL FILMS · SCION 055–113</span>
  </div>
  <div class="topbar-right">
    <button class="pill-btn on" id="auto-btn" onclick="toggleAuto()">AUTO-NEXT: ON</button>
    <button class="pill-btn" onclick="toggleTheme()">THEME</button>
  </div>
</header>

<div class="layout">
  <!-- Sticky Cinema Player Deck -->
  <section class="player-deck">
    <div class="video-wrap">
      <video id="player" controls playsinline preload="metadata"></video>
    </div>

    <div class="cut-bar" id="cut-bar" title="Tap any segment to jump to that cut"></div>

    <div class="live-shot-line">
      <div class="live-shot-text" id="live-shot-text">Select or play any film</div>
      <div class="live-time" id="live-time">0:00</div>
    </div>

    <div class="now-bar">
      <div class="now-info">
        <div class="now-kicker">
          <span id="now-idx">01 / 85</span>
          <span>·</span>
          <span id="now-code">SCION 055</span>
          <span>·</span>
          <span id="now-cat">Microfilms</span>
        </div>
        <h1 class="now-title" id="now-title">Words — Polysemic Relay</h1>
      </div>
      <div class="now-controls">
        <button class="icon-btn" onclick="stepFilm(-1)" title="Previous film">‹</button>
        <button class="icon-btn" onclick="stepFilm(1)" title="Next film">›</button>
        <button class="icon-btn" id="info-toggle-btn" onclick="toggleDrawer()">Info +</button>
      </div>
    </div>

    <div class="info-drawer" id="info-drawer">
      <div class="theorem-box" id="drawer-theorem"></div>
      <div class="drawer-links" id="drawer-links"></div>
      <ul class="edl-mini-list" id="drawer-edl"></ul>
    </div>
  </section>

  <!-- Scrollable Minimal Index -->
  <section class="index-pane">
    <div class="filter-bar">
      <div class="cat-scroll" id="cat-scroll">
        <button class="cat-pill active" data-cat="all" onclick="setCat('all')">All (85)</button>
        <button class="cat-pill" data-cat="series_a" onclick="setCat('series_a')">055–065 Microfilms (11)</button>
        <button class="cat-pill" data-cat="series_b" onclick="setCat('series_b')">B-Roll Works (12)</button>
        <button class="cat-pill" data-cat="series_c" onclick="setCat('series_c')">066–074 Structural (10)</button>
        <button class="cat-pill" data-cat="series_d" onclick="setCat('series_d')">075–082 Observational (10)</button>
        <button class="cat-pill" data-cat="series_e" onclick="setCat('series_e')">083–094 Essays (12)</button>
        <button class="cat-pill" data-cat="series_f" onclick="setCat('series_f')">095–113 Interactive (19)</button>
        <button class="cat-pill" data-cat="studies" onclick="setCat('studies')">Studies (6)</button>
        <button class="cat-pill" data-cat="collections" onclick="setCat('collections')">Collections (5)</button>
      </div>
      <div class="search-row">
        <input type="search" class="search-input" id="search-input" placeholder="Filter 85 films by title, SCION #, director, or source…" oninput="renderList()">
      </div>
    </div>

    <ul class="film-list" id="film-list"></ul>
  </section>
</div>

<!-- Proof Strip Modal -->
<div class="modal" id="strip-modal" onclick="closeStripModal()">
  <div class="modal-bar" onclick="event.stopPropagation()">
    <span id="modal-title">v2 Critic Proof Strip</span>
    <button class="pill-btn on" onclick="closeStripModal()">Close ✕</button>
  </div>
  <div class="modal-body" onclick="event.stopPropagation()">
    <img id="modal-img" src="" alt="Proof Strip">
  </div>
</div>

<script>
const FILMS = __DATA_JSON__;

let activeCat = 'all';
let currentIdx = 0;
let autoAdvance = true;
let filteredFilms = [...FILMS];

const player = document.getElementById('player');

function fmtTime(sec) {
  const s = Math.max(0, Math.round(Number(sec) || 0));
  const m = Math.floor(s / 60);
  const r = String(s % 60).padStart(2, '0');
  return `${m}:${r}`;
}

function toggleTheme() {
  const root = document.documentElement;
  if (root.getAttribute('data-theme') === 'light') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', 'light');
  }
}

function toggleAuto() {
  autoAdvance = !autoAdvance;
  const btn = document.getElementById('auto-btn');
  btn.textContent = `AUTO-NEXT: ${autoAdvance ? 'ON' : 'OFF'}`;
  btn.classList.toggle('on', autoAdvance);
}

function toggleDrawer() {
  const dr = document.getElementById('info-drawer');
  const btn = document.getElementById('info-toggle-btn');
  const open = dr.classList.toggle('open');
  btn.classList.toggle('active', open);
  btn.textContent = open ? 'Info −' : 'Info +';
}

function openStripModal(stripUrl, title) {
  document.getElementById('modal-img').src = stripUrl;
  document.getElementById('modal-title').textContent = `${title} — v2 Critic Proof Strip`;
  document.getElementById('strip-modal').classList.add('open');
}

function closeStripModal() {
  document.getElementById('strip-modal').classList.remove('open');
}

function setCat(cat) {
  activeCat = cat;
  document.querySelectorAll('.cat-pill').forEach(b => {
    b.classList.toggle('active', b.dataset.cat === cat);
  });
  renderList();
}

function renderList() {
  const q = (document.getElementById('search-input').value || '').trim().toLowerCase();
  filteredFilms = FILMS.filter(f => {
    if (activeCat !== 'all' && f.cat !== activeCat) return false;
    if (!q) return true;
    const hay = `${f.code} ${f.title} ${f.subtitle} ${f.lineage} ${f.id}`.toLowerCase();
    return hay.includes(q);
  });

  const ul = document.getElementById('film-list');
  const curFilm = FILMS[currentIdx];

  ul.innerHTML = filteredFilms.map((f) => {
    const globalIdx = FILMS.indexOf(f);
    const isAct = curFilm && curFilm.id === f.id;
    const numStr = String(globalIdx + 1).padStart(2, '0');
    return `
      <li class="film-row ${isAct ? 'active' : ''}" id="row-${f.id}" onclick="loadFilm(${globalIdx}, true)">
        <span class="row-num">${isAct ? '▶' : numStr}</span>
        <img class="row-thumb" src="${f.thumb}" loading="lazy" onerror="this.style.visibility='hidden'" alt="">
        <div class="row-main">
          <div class="row-title">${f.title}</div>
          <div class="row-sub">${f.subtitle || f.lineage}</div>
        </div>
        <div class="row-right">
          <span class="row-code">${f.code}</span>
          <span class="row-dur">${fmtTime(f.dur)}</span>
        </div>
      </li>
    `;
  }).join('');
}

function loadFilm(idx, autoplay = false) {
  if (idx < 0 || idx >= FILMS.length) return;
  currentIdx = idx;
  const f = FILMS[idx];

  // Update URL hash quietly for bookmarking/sharing
  history.replaceState(null, '', `#${f.id}`);

  player.src = `films/${f.id}.mp4`;
  if (autoplay) {
    player.play().catch(() => {});
  }

  document.getElementById('now-idx').textContent = `${String(idx + 1).padStart(2, '0')} / ${FILMS.length}`;
  document.getElementById('now-code').textContent = f.code;
  document.getElementById('now-cat').textContent = f.series_short;
  document.getElementById('now-title').textContent = f.title;
  document.getElementById('live-time').textContent = `0:00 / ${fmtTime(f.dur)}`;

  // Cut bar
  const total = f.dur || 1;
  const cutBar = document.getElementById('cut-bar');
  cutBar.innerHTML = (f.segments || []).map((s, s_i) => {
    const w = Math.max(1.5, (s.dur / total) * 100);
    return `<div class="cut-seg ${s.mode === 'card' ? 'is-card' : ''}" id="cseg-${s_i}" style="width:${w}%" onclick="seekTo(${s.start})"></div>`;
  }).join('');

  // Drawer info
  document.getElementById('drawer-theorem').innerHTML = `
    <div style="margin-bottom:4px;"><strong>${f.lineage || f.code}</strong></div>
    <div>${f.theorem || ''}</div>
  `;

  document.getElementById('drawer-links').innerHTML = `
    <button class="pill-btn" onclick="openStripModal('${f.strip}', '${f.code.replace(/'/g, "")}')">Proof Strip (v2)</button>
    <a class="pill-btn" href="films/${f.id}.mp4" download>Download MP4</a>
    <a class="pill-btn" href="manifests/${f.id}.json" target="_blank">Manifest JSON</a>
    <a class="pill-btn" href="https://hartswf0.github.io/bolas/paeleo/allways/operator.html#s${f.scion_id}" target="_blank">SCION #${f.scion_id} ↗</a>
  `;

  const edlUl = document.getElementById('drawer-edl');
  edlUl.innerHTML = (f.segments || []).map((s, s_i) => {
    const src = (s.sources && s.sources[0]) ? s.sources[0] : null;
    const srcText = src ? `${src.source_title}${src.source_year ? ' (' + src.source_year + ')' : ''}` : s.label;
    const srcLink = src ? `<a class="edl-mini-src" href="${src.source_page_url}" target="_blank" onclick="event.stopPropagation()">${src.clip_id.slice(0, 8)}↗</a>` : '';
    return `
      <li class="edl-mini-row" id="edl-row-${s_i}" onclick="seekTo(${s.start})">
        <div class="edl-mini-left">
          <span class="edl-mini-time">${fmtTime(s.start)}</span>
          <strong>${srcText}</strong>
          <span style="color:var(--ink-muted);"> — ${s.note || ''}</span>
        </div>
        ${srcLink}
      </li>
    `;
  }).join('');

  renderList();
  updateLiveShot(0.1);
}

function seekTo(sec) {
  player.currentTime = sec;
  player.play().catch(() => {});
}

function stepFilm(delta) {
  const curFilm = FILMS[currentIdx];
  const posInFiltered = filteredFilms.indexOf(curFilm);
  if (posInFiltered !== -1 && filteredFilms.length > 0) {
    const nextFiltered = filteredFilms[(posInFiltered + delta + filteredFilms.length) % filteredFilms.length];
    loadFilm(FILMS.indexOf(nextFiltered), true);
  } else {
    loadFilm((currentIdx + delta + FILMS.length) % FILMS.length, true);
  }
}

function updateLiveShot(t) {
  const f = FILMS[currentIdx];
  if (!f) return;
  document.getElementById('live-time').textContent = `${fmtTime(t)} / ${fmtTime(f.dur)}`;

  const segs = f.segments || [];
  let activeIdx = 0;
  for (let i = 0; i < segs.length; i++) {
    if (t >= segs[i].start && t <= segs[i].end + 0.15) {
      activeIdx = i;
      break;
    }
  }

  segs.forEach((_, i) => {
    const c = document.getElementById(`cseg-${i}`);
    if (c) c.classList.toggle('active', i === activeIdx);
    const r = document.getElementById(`edl-row-${i}`);
    if (r) r.classList.toggle('active', i === activeIdx);
  });

  const activeSeg = segs[activeIdx];
  if (activeSeg) {
    const src = (activeSeg.sources && activeSeg.sources[0]) ? activeSeg.sources[0] : null;
    const prefix = src ? `<strong>${src.source_title}${src.source_year ? ' (' + src.source_year + ')' : ''}</strong>` : `<strong>${activeSeg.label}</strong>`;
    const desc = activeSeg.note || activeSeg.nearmatch || '';
    document.getElementById('live-shot-text').innerHTML = `${prefix} · ${desc}`;
  }
}

player.addEventListener('timeupdate', () => {
  updateLiveShot(player.currentTime);
});

player.addEventListener('ended', () => {
  if (autoAdvance) {
    stepFilm(1);
  }
});

// Keyboard shortcuts for desktop convenience
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowRight' && e.shiftKey) {
    stepFilm(1);
  } else if (e.key === 'ArrowLeft' && e.shiftKey) {
    stepFilm(-1);
  } else if (e.key === 'Escape') {
    closeStripModal();
  }
});

// Initialize from URL hash if present
(function init() {
  const hash = (window.location.hash || '').replace('#', '').trim();
  const foundIdx = FILMS.findIndex(f => f.id === hash);
  loadFilm(foundIdx >= 0 ? foundIdx : 0, false);
})();
</script>
</body>
</html>
"""
    final_html = html.replace("__DATA_JSON__", data_json)
    OUT_HTML.write_text(final_html, encoding="utf-8")
    shutil.copyfile(OUT_HTML, WATCH_HTML)
    print(f"Built minimal mobile-first screening index at {OUT_HTML} and {WATCH_HTML} ({len(final_html) // 1024} KB, {len(films)} films).")


if __name__ == "__main__":
    build()
