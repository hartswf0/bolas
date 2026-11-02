#!/usr/bin/env python3
"""
Builds allways-awards/index.html (and paeleo/allways/awards/index.html redirect)
with:
  - 5-Pillar 100-Point Jury Rubric
  - 4-Maker Ensemble Comparison Scorecard
  - 12 Category Award Cards (with 1-click inline video playback)
  - 3 Head-to-Head Comparison Matrices (B-Roll 12, SCION 055-065, SCION 066-078)
  - Full 132-Film Interactive Filterable & Playable Leaderboard
"""
import os, json, html

REPO = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
AWARDS_DIR = os.path.join(REPO, "allways-awards")
data = json.load(open(os.path.join(AWARDS_DIR, "ratings.json")))
films = data["films"]
awards = data["awards"]

def esc(s):
    return html.escape(str(s or ""), quote=True)

by_id = {f["id"]: f for f in films}

maker_colors = {
    "Claude Opus 5.5": "#9e3b24",
    "Gemini Argon": "#2b5b84",
    "OpenAI Sol": "#2e6b4e",
    "Claude Sonnet": "#7a4988",
}

# Build 12 Award Cards HTML
award_cards_html = []
for aw in awards:
    wid = aw["winner_id"]
    fobj = by_id.get(wid, {})
    vid = "../allways-best/allways-best.mp4" if wid == "allways-best" else fobj.get("video_url", "../allways-best/allways-best.mp4")
    case_url = "../allways-best/" if wid == "allways-best" else fobj.get("url", "../allways-best/")
    award_cards_html.append(f"""
    <article class="award-card">
      <div class="award-kicker">🏆 {esc(aw['category'])}</div>
      <h3>{esc(aw['winner_title'])}</h3>
      <div class="award-meta">
        <span class="badge-maker">{esc(aw['winner_maker'])}</span>
        <span class="badge-score">{aw['winner_score']:.1f} / 100</span>
      </div>
      <p class="award-why">{esc(aw['why'])}</p>
      <p class="award-runner"><b>Silver / Runner-Up:</b> {esc(aw['runner_up'])}</p>
      <div class="award-actions">
        <button type="button" class="btn-play" onclick="playFilm('{esc(vid)}', '{esc(aw['winner_title'])} ({esc(aw['winner_maker'])})')">▶ Screen Winner</button>
        <a class="btn-case" href="{esc(case_url)}">Open Case Study ↗</a>
      </div>
    </article>
    """)

# Head-to-Head 1: 12 B-Roll Works (Opus 5.5 vs Argon)
broll_order = [
    ("nobody-home", "01 · NOBODY HOME"),
    ("almost-human", "02 · ALMOST HUMAN"),
    ("terra-incognita", "03 · TERRA INCOGNITA"),
    ("split-second", "04 · SPLIT SECOND"),
    ("cut-to-the-chase", "05 · CUT TO THE CHASE"),
    ("kinetic", "06 · KINETIC"),
    ("zero-memory", "07 · ZERO MEMORY"),
    ("homonym", "08 · HOMONYM"),
    ("anybody-anywhere", "09 · ANYBODY, ANYWHERE"),
    ("collective-inventories", "10 · COLLECTIVE INVENTORIES"),
    ("mnemonil", "11 · MNEMONIL"),
    ("planimetric", "12 · PLANIMETRIC"),
]
h2h_broll_rows = []
for slug, label in broll_order:
    op = next(f for f in films if f["maker"] == "Claude Opus 5.5" and f["work_slug"] == slug)
    ar = next(f for f in films if f["maker"] == "Gemini Argon" and f["work_slug"] == slug)
    if op["total"] > ar["total"]:
        win = f'<span class="win-pill" style="background:#9e3b24">Opus 5.5 (+{op["total"]-ar["total"]:.1f})</span>'
    elif ar["total"] > op["total"]:
        win = f'<span class="win-pill" style="background:#2b5b84">Argon (+{ar["total"]-op["total"]:.1f})</span>'
    else:
        win = '<span class="win-pill" style="background:#555">Tie</span>'
    h2h_broll_rows.append(f"""
    <tr>
      <td><b>{esc(label)}</b></td>
      <td><a href="{esc(op['url'])}">{op['total']:.1f} ({op['grade']})</a> · <small>{op['duration_s']}s · {esc(op['verdict'])}</small></td>
      <td><a href="{esc(ar['url'])}">{ar['total']:.1f} ({ar['grade']})</a> · <small>{ar['duration_s']}s · {esc(ar['verdict'])}</small></td>
      <td>{win}</td>
    </tr>
    """)

# Head-to-Head 2: SCION 055-065 (Sonnet vs Sol vs Argon)
h2h_55_65_rows = []
for sc_id in range(55, 66):
    so = next(f for f in films if f["maker"] == "Claude Sonnet" and f["scion_id"] == sc_id)
    sl = next(f for f in films if f["maker"] == "OpenAI Sol" and f["scion_id"] == sc_id)
    ar = next(f for f in films if f["maker"] == "Gemini Argon" and f["scion_id"] == sc_id and f["series"] != "BROLL_OF_CIVILIZATION")
    trio = [("Claude Sonnet", so, "#7a4988"), ("OpenAI Sol", sl, "#2e6b4e"), ("Gemini Argon", ar, "#2b5b84")]
    best_m, best_f, best_col = max(trio, key=lambda x: x[1]["total"])
    h2h_55_65_rows.append(f"""
    <tr>
      <td><b>SCION {sc_id:03d}</b> · {esc(so['title'].split('·')[0].strip())}</td>
      <td><a href="{esc(so['url'])}">{so['total']:.1f} ({so['grade']})</a> · <small>{so['duration_s']}s</small></td>
      <td><a href="{esc(sl['url'])}">{sl['total']:.1f} ({sl['grade']})</a> · <small>{sl['duration_s']}s</small></td>
      <td><a href="{esc(ar['url'])}">{ar['total']:.1f} ({ar['grade']})</a> · <small>{ar['duration_s']}s</small></td>
      <td><span class="win-pill" style="background:{best_col}">{esc(best_m)} ({best_f['total']:.1f})</span></td>
    </tr>
    """)

# Head-to-Head 3: SCION 066-078 (Sol vs Argon)
h2h_66_78_rows = []
for sc_id in range(66, 79):
    sl = next(f for f in films if f["maker"] == "OpenAI Sol" and f["scion_id"] == sc_id)
    ar_cands = [f for f in films if f["maker"] == "Gemini Argon" and f["scion_id"] == sc_id and f["series"] != "BROLL_OF_CIVILIZATION"]
    ar = max(ar_cands, key=lambda x: x["total"])
    if sl["total"] >= ar["total"]:
        win = f'<span class="win-pill" style="background:#2e6b4e">OpenAI Sol ({sl["total"]:.1f})</span>'
        reason = "Archival long-form study + comparison reel"
    else:
        win = f'<span class="win-pill" style="background:#2b5b84">Gemini Argon ({ar["total"]:.1f})</span>'
        reason = "Real archival photography vs. Sol synthetic vector diagram"
    h2h_66_78_rows.append(f"""
    <tr>
      <td><b>SCION {sc_id:03d}</b></td>
      <td><a href="{esc(sl['url'])}">{sl['total']:.1f} ({sl['grade']})</a> · <small>{sl['duration_s']}s · {esc(sl['title'])}</small></td>
      <td><a href="{esc(ar['url'])}">{ar['total']:.1f} ({ar['grade']})</a> · <small>{ar['duration_s']}s · {esc(ar['title'][:28])}</small></td>
      <td>{win} <small style="color:#5d584f">{esc(reason)}</small></td>
    </tr>
    """)

# Full 132-film table rows
leaderboard_rows = []
for f in films:
    col = maker_colors.get(f["maker"], "#444")
    sc = f["scores"]
    leaderboard_rows.append(f"""
    <tr class="film-row" data-maker="{esc(f['maker'])}" data-grade="{esc(f['grade'])}">
      <td><b>#{f['rank']:03d}</b></td>
      <td><span class="grade-pill grade-{f['grade'].replace('+','p').replace('-','m')}">{esc(f['grade'])} · {f['total']:.1f}</span></td>
      <td><span class="win-pill" style="background:{col}">{esc(f['maker'])}</span></td>
      <td>
        <b><a href="{esc(f['url'])}">{esc(f['title'])}</a></b>
        <div class="note-sub">{esc(f['jury_note'])}</div>
      </td>
      <td><code>{f['duration_s']}s</code></td>
      <td><small>{sc['brief']:.1f} / {sc['archival']:.1f} / {sc['nearmatch']:.1f} / {sc['audio_time']:.1f} / {sc['critic_ethics']:.1f}</small></td>
      <td>
        <button type="button" class="btn-play sm" onclick="playFilm('{esc(f['video_url'])}', '#{f['rank']:02d} · {esc(f['title'])} ({esc(f['maker'])})')">▶ Play</button>
      </td>
    </tr>
    """)

html_out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLWAYS Jury Awards &amp; 132-Film Ratings</title>
<meta name="description" content="Complete jury evaluation, 100-point rubric, 12 category awards, head-to-head matrices, and rankings for all 132 films in ALLWAYS across Opus 5.5, Sonnet, Sol, and Argon.">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../tools/paeleo/fonts/local.css">
<link rel="stylesheet" href="../paeleo/allways/allways.css">
<style>
:root {{
  --bg: #f4f1e9; --ink: #161513; --muted: #5d584f; --line: #d6cfc2; --card: #ebe6da; --accent: #9e3b24;
}}
.aw-wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 20px 80px; }}
.aw-hero {{ padding: 28px 0 22px; border-bottom: 1px solid var(--line); }}
.aw-hero h1 {{ font-size: clamp(28px, 4.4vw, 46px); line-height: 1.06; margin: 8px 0 12px; }}
.aw-hero p {{ font-size: 17px; max-width: 820px; line-height: 1.5; margin: 0 0 12px; }}

.player-dock {{
  position: sticky; top: 0; z-index: 50;
  background: #141311; color: #f4f1e9; border-radius: 6px; overflow: hidden;
  margin: 18px 0 28px; box-shadow: 0 10px 28px rgba(0,0,0,0.22);
}}
.player-dock video {{ width: 100%; aspect-ratio: 16/9; max-height: 54vh; display: block; background: #000; }}
.player-bar {{ padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; font-family: var(--mono, monospace); font-size: 12px; background: #1b1916; flex-wrap: wrap; gap: 8px; }}

.rubric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 16px 0 28px; }}
.rubric-card {{ background: var(--card); border: 1px solid var(--line); padding: 14px; border-radius: 4px; }}
.rubric-card b {{ display: block; font-size: 14px; margin-bottom: 6px; }}
.rubric-card span.pts {{ font-family: var(--mono, monospace); font-size: 12px; color: var(--accent); font-weight: 700; }}
.rubric-card p {{ margin: 6px 0 0; font-size: 13px; color: var(--muted); line-height: 1.42; }}

.awards-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 16px; margin: 18px 0 36px; }}
.award-card {{ background: var(--card); border: 1px solid var(--line); border-radius: 5px; padding: 16px; display: flex; flex-direction: column; gap: 8px; }}
.award-kicker {{ font-family: var(--mono, monospace); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); font-weight: 700; }}
.award-card h3 {{ margin: 0; font-size: 19px; line-height: 1.25; }}
.award-meta {{ display: flex; gap: 8px; align-items: center; font-family: var(--mono, monospace); font-size: 12px; }}
.badge-maker {{ background: #161513; color: #f4f1e9; padding: 2px 8px; border-radius: 2px; }}
.badge-score {{ background: #dfd8c8; color: #161513; padding: 2px 8px; border-radius: 2px; font-weight: 700; }}
.award-why {{ margin: 0; font-size: 14px; line-height: 1.46; color: #24221e; }}
.award-runner {{ margin: 0; font-size: 12.5px; color: var(--muted); border-top: 1px dashed var(--line); padding-top: 6px; }}
.award-actions {{ margin-top: auto; padding-top: 8px; display: flex; gap: 10px; align-items: center; }}
.btn-play {{ background: var(--ink); color: var(--bg); border: 0; padding: 6px 12px; border-radius: 3px; font-family: var(--mono, monospace); font-size: 11px; cursor: pointer; text-transform: uppercase; }}
.btn-play.sm {{ padding: 4px 8px; font-size: 10.5px; }}
.btn-case {{ font-family: var(--mono, monospace); font-size: 11.5px; color: var(--ink); text-decoration: underline; }}

.h2h-table {{ width: 100%; border-collapse: collapse; margin: 14px 0 32px; font-size: 13.5px; }}
.h2h-table th, .h2h-table td {{ border-bottom: 1px solid var(--line); padding: 9px 10px; text-align: left; vertical-align: top; }}
.h2h-table th {{ font-family: var(--mono, monospace); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); background: var(--card); }}
.win-pill {{ display: inline-block; color: #fff; font-family: var(--mono, monospace); font-size: 11px; padding: 2px 7px; border-radius: 2px; font-weight: 600; }}
.grade-pill {{ display: inline-block; font-family: var(--mono, monospace); font-size: 11.5px; font-weight: 700; padding: 2px 7px; border-radius: 2px; background: #dfd8c8; }}
.grade-S {{ background: #9e3b24; color: #fff; }}
.grade-Ap {{ background: #2e6b4e; color: #fff; }}
.note-sub {{ font-size: 12.5px; color: var(--muted); margin-top: 3px; line-height: 1.4; }}

.filter-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; align-items: center; }}
.filter-btn {{ background: var(--card); border: 1px solid var(--line); padding: 6px 12px; font-family: var(--mono, monospace); font-size: 11.5px; border-radius: 3px; cursor: pointer; }}
.filter-btn.active {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
.table-scroll {{ overflow-x: auto; }}
</style>
</head>
<body id="top">
<header class="site-header">
  <div class="wrap sitebar">
    <div class="parents">
      <a href="../">CRASH LAB</a><span>/</span>
      <a href="../paeleo/">PAELEO</a><span>/</span>
      <a href="../paeleo/allways/">ALLWAYS</a><span>/</span>
      <strong>allways-awards</strong>
    </div>
    <nav aria-label="ALLWAYS">
      <a href="../allways-best/">Anthology Master Film</a>
      <a href="#awards">12 Category Awards</a>
      <a href="#head-to-head">Head-to-Head</a>
      <a href="#leaderboard">All 132 Films</a>
      <a href="../paeleo/allways/#runs">All Runs</a>
    </nav>
  </div>
</header>

<main class="aw-wrap">
  <section class="aw-hero">
    <span class="label">ALLWAYS Jury Report &amp; Complete Evaluation · 132 Films · 4 Makers · 12 Award Categories</span>
    <h1>How to Judge an Archival Film:<br>Ratings, Comparisons &amp; Category Awards</h1>
    <p>
      Every film across <b>Claude Opus 5.5</b> (12 films), <b>Claude Sonnet</b> (11 films), <b>OpenAI Sol</b> (24 films &amp; studies),
      and <b>Gemini Argon</b> (85 films) was evaluated on a falsifiable <b>100-point, 5-pillar rubric</b> combining direct media telemetry
      (duration fidelity, single-shot cut cleanliness, loudness &amp; acoustic continuity) with the independent blind critic records.
    </p>
  </section>

  <section class="player-dock" aria-label="Award Screening Player">
    <video id="award-video" controls playsinline preload="metadata" poster="../allways-best/poster.jpg" src="../allways-best/allways-best.mp4"></video>
    <div class="player-bar">
      <span id="now-playing-label"><b>NOW LOADED:</b> ALLWAYS — Cinema from the Rest of the Frame (24-Cut Cross-Maker Synthesis · 98.0/100)</span>
      <span>Click any "▶ Screen Winner" or "▶ Play" button below to watch immediately</span>
    </div>
  </section>

  <section id="rubric">
    <span class="label">01 / Methodology</span>
    <h2>The 5-Pillar, 100-Point Jury Rubric</h2>
    <div class="rubric-grid">
      <div class="rubric-card"><span class="pts">25 POINTS</span><b>1. Brief &amp; Structural Realization</b><p>Does the film fulfill its target duration and execute every required structural phase (e.g., three passes, memory resets, unannotated vs. annotated pass) without truncation?</p></div>
      <div class="rubric-card"><span class="pts">20 POINTS</span><b>2. Archival Foraging &amp; Visual Purity</b><p>Uses real public-domain moving-image recordings rather than synthetic vector substitutes, with clean single-shot trims free of accidental internal camera cuts.</p></div>
      <div class="rubric-card"><span class="pts">20 POINTS</span><b>3. NEARMATCH Editorial Craft</b><p>"A match should make a difference easier to notice." Evaluates spatial registration, gesture/rhythm bridges, and preservation of the post-action pause.</p></div>
      <div class="rubric-card"><span class="pts">15 POINTS</span><b>4. Acoustic &amp; Temporal Architecture</b><p>Synchronized optical sound, room tone, or spoken counterpoint (-19 LUFS) without jarring -91 dB digital dropouts, plus earned hold durations.</p></div>
      <div class="rubric-card"><span class="pts">20 POINTS</span><b>5. Blind Critic &amp; Ethical Provenance</b><p>Independent blind critic verdict (PASS vs. inconclusive vs. fail), Round 1 → Round 2 verified repairs, and strict ethical source disclosure.</p></div>
    </div>
  </section>

  <section id="makers">
    <span class="label">02 / Ensemble Comparison</span>
    <h2>How the Four Makers Compare</h2>
    <div class="table-scroll">
      <table class="h2h-table">
        <thead>
          <tr><th>Maker / Run</th><th>Scope</th><th>Mean Score</th><th>S / A+ Films</th><th>Signature Strength</th><th>Primary Limitation</th><th>Top Film</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="win-pill" style="background:#7a4988">Claude Sonnet</span><br><small><a href="../allways-sonnet/">allways-sonnet</a></small></td>
            <td>11 films<br><small>(SCION 055–065)</small></td>
            <td><b>86.7 / 100</b></td>
            <td>4</td>
            <td>Mathematical sub-pixel registration (<code>059 Ball</code>) &amp; two-pass trajectory curve fitting (<code>064 Parabolas</code>).</td>
            <td>Several exports are muted (-91 dB silence); <code>063 Breath</code> failed Round 1 critic.</td>
            <td><b>059 · BALL</b> (96.0 · S)</td>
          </tr>
          <tr>
            <td><span class="win-pill" style="background:#2b5b84">Gemini Argon</span><br><small><a href="../allways-argon/">allways-argon</a></small></td>
            <td>85 films<br><small>(12 B-Roll + 59 SCION + 11 Studies/Coll.)</small></td>
            <td><b>89.6 / 100</b></td>
            <td>26</td>
            <td>100% slate completion, OpenCV Telea person-removal triptych (<code>Nobody Home</code>), cut-free window scanner, and normalized audio on all 85 films.</td>
            <td>Compact 36–52s studio runtimes with burned-in top/bottom laboratory HUD bars.</td>
            <td><b>NOBODY HOME</b> (95.5 · S)</td>
          </tr>
          <tr>
            <td><span class="win-pill" style="background:#2e6b4e">OpenAI Sol</span><br><small><a href="../allways-sol/">allways-sol</a></small></td>
            <td>24 films + 16 comparisons<br><small>(SCION 055–078)</small></td>
            <td><b>85.2 / 100</b><br><small>(89.8 on archival cuts)</small></td>
            <td>9</td>
            <td>90–120s long-form archival essays, 16 source-passage comparison edits, and the best realizations of <code>071</code>, <code>063</code>, <code>078</code>, and <code>057</code>.</td>
            <td>Five films (<code>066, 068, 072, 073, 074</code>) used synthetic vector diagrams instead of archival footage; <code>058</code> unfinished.</td>
            <td><b>071 · A FILE HAS EDGES</b> (93.5 · S)</td>
          </tr>
          <tr>
            <td><span class="win-pill" style="background:#9e3b24">Claude Opus 5.5</span><br><small><a href="../allways-opus/">allways-opus</a></small></td>
            <td>12 films<br><small>(12 B-Roll proofs)</small></td>
            <td><b>83.9 / 100</b></td>
            <td>1</td>
            <td>Poetic voiceover counterpoint and documentary ethics in <code>MNEMONIL</code> (94.5 · S), plus clean split-screen alignment in <code>ANYBODY, ANYWHERE</code>.</td>
            <td>11 of 12 films fell short of target duration and did not undergo a Round-2 repair pass.</td>
            <td><b>MNEMONIL</b> (94.5 · S)</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <section id="awards">
    <span class="label">03 / Category Winners</span>
    <h2>The 12 ALLWAYS Jury Awards</h2>
    <div class="awards-grid">
      {''.join(award_cards_html)}
    </div>
  </section>

  <section id="head-to-head">
    <span class="label">04 / Head-to-Head Comparisons</span>
    <h2>Matrix A · The 12 B-Roll of Civilization Works (Opus 5.5 vs. Argon)</h2>
    <div class="table-scroll">
      <table class="h2h-table">
        <thead><tr><th>Work</th><th>Claude Opus 5.5</th><th>Gemini Argon</th><th>Category Winner</th></tr></thead>
        <tbody>{''.join(h2h_broll_rows)}</tbody>
      </table>
    </div>

    <h2>Matrix B · Shared SCION Operators 055–065 (Sonnet vs. Sol vs. Argon)</h2>
    <div class="table-scroll">
      <table class="h2h-table">
        <thead><tr><th>Operator</th><th>Claude Sonnet</th><th>OpenAI Sol</th><th>Gemini Argon</th><th>Operator Winner</th></tr></thead>
        <tbody>{''.join(h2h_55_65_rows)}</tbody>
      </table>
    </div>

    <h2>Matrix C · Shared SCION Operators 066–078 (Sol vs. Argon)</h2>
    <div class="table-scroll">
      <table class="h2h-table">
        <thead><tr><th>Operator</th><th>OpenAI Sol</th><th>Gemini Argon</th><th>Operator Winner &amp; Reason</th></tr></thead>
        <tbody>{''.join(h2h_66_78_rows)}</tbody>
      </table>
    </div>
  </section>

  <section id="leaderboard">
    <span class="label">05 / Complete 132-Film Ratings</span>
    <h2>All 132 Films Ranked &amp; Scored</h2>
    <div class="filter-bar">
      <button type="button" class="filter-btn active" onclick="filterFilms('ALL', this)">All 132 Films</button>
      <button type="button" class="filter-btn" onclick="filterFilms('Claude Sonnet', this)">Claude Sonnet (11)</button>
      <button type="button" class="filter-btn" onclick="filterFilms('Claude Opus 5.5', this)">Claude Opus 5.5 (12)</button>
      <button type="button" class="filter-btn" onclick="filterFilms('OpenAI Sol', this)">OpenAI Sol (24)</button>
      <button type="button" class="filter-btn" onclick="filterFilms('Gemini Argon', this)">Gemini Argon (85)</button>
      <button type="button" class="filter-btn" onclick="filterGrade('S', this)">Tier S Only (93+)</button>
    </div>
    <div class="table-scroll">
      <table class="h2h-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Grade / Total</th>
            <th>Maker</th>
            <th>Film &amp; Jury Citation</th>
            <th>Dur</th>
            <th>Rubric (25/20/20/15/20)</th>
            <th>Screen</th>
          </tr>
        </thead>
        <tbody id="leaderboard-body">
          {''.join(leaderboard_rows)}
        </tbody>
      </table>
    </div>
  </section>
</main>

<script>
const video = document.getElementById('award-video');
const label = document.getElementById('now-playing-label');

function playFilm(url, title) {{
  video.src = url;
  video.play().catch(()=>{{}});
  label.innerHTML = '<b>NOW SCREENING:</b> ' + title;
  window.scrollTo({{ top: Math.max(0, document.querySelector('.player-dock').offsetTop - 12), behavior: 'smooth' }});
}}

function filterFilms(maker, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.film-row').forEach(row => {{
    row.style.display = (maker === 'ALL' || row.dataset.maker === maker) ? '' : 'none';
  }});
}}

function filterGrade(grade, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.film-row').forEach(row => {{
    row.style.display = (row.dataset.grade === grade) ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""

with open(os.path.join(AWARDS_DIR, "index.html"), "w") as f:
    f.write(html_out)

os.makedirs(os.path.join(REPO, "paeleo/allways/awards"), exist_ok=True)
with open(os.path.join(REPO, "paeleo/allways/awards/index.html"), "w") as f:
    f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../../../allways-awards/index.html"><script>location.replace("../../../allways-awards/index.html"+location.hash);</script>')

print("Generated allways-awards/index.html and paeleo/allways/awards/index.html")
