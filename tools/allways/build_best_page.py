#!/usr/bin/env python3
"""
Generates:
  1. allways-best/index.html (and paeleo/allways/best/index.html redirect)
  2. allways-best/PROMPT.md
  3. Updates paeleo/allways/runs.json and paeleo/allways/index.html (#runs)
     so the flagship ALLWAYS Anthology Film is playable inline on #runs and
     accessible as its own full case study.
"""
import os, json, html

REPO = "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo"
BEST_DIR = os.path.join(REPO, "allways-best")

def esc(s):
    return html.escape(str(s or ""), quote=True)

edl_data = json.load(open(os.path.join(BEST_DIR, "edl.json")))
shots = edl_data["shots"]
chapters = edl_data["chapters"]
dur_s = edl_data["duration_seconds"]
mins = int(dur_s // 60)
secs = int(round(dur_s % 60))

PROMPT_TEXT = """# ALLWAYS — Master Anthology Synthesis Prompt (Across All Makers)

You are assembling the single flagship **ALLWAYS Anthology Film** (`ALLWAYS — Cinema from the Rest of the Frame`) from the full corpus of 131 handmade archival proof films created across four independent AI makers:
- **Claude Opus 5.5** (`allways-opus/` — 12 B-Roll of Civilization proof films)
- **Gemini Argon** (`allways-argon/` & `allways-argon/studio/` — 12 B-Roll proofs + 59 SCION operators 055–113 + 6 Studies + 5 Collections)
- **OpenAI Sol** (`allways-sol/` — 23 SCION operator films 055–078 + 16 comparison edits)
- **Claude Sonnet** (`allways-sonnet/` — 11 SCION operator microfilms 055–065)

## 1. Selection Rule: Critic-Protected Passages Only
Do not select shots by title or text description alone. Read every independent critic report (`film.json`, `CRITIC-ROUND-1.md`, `CRITIC_RECORDS.txt`, and `manifests/*.json`) and harvest only passages that cleared visual inspection (`PASS`) or were explicitly designated **`Strength to protect`** / **`Protect`** by a blind critic before seeing the builder's notes.

## 2. Six-Movement Structural Arc (`STATEMENT.md` & `NOTEBOOK.md`)
Organize the 24 selected cuts into six movements that trace the philosophical spine of ALLWAYS:
1. **I / THE OCCASION & THE EDGE (`Record`)**: Someone moves a chair (`Opus 5.5 · Nobody Home`), an erasure triptych discloses its mask (`Argon · Nobody Home`), a doorway holds after speech ends (`Sol · 057 After`), and a child stares back through a screen door (`Sonnet · 057 Moments`).
2. **II / NEARMATCH (`Two Lives Across a Cut`)**: A complete collar adjustment (`Argon · Almost Human`), two people in 1961 and 1944 preparing to sit (`Opus 5.5 · Anybody, Anywhere`), measured breath in a 1927 glass cylinder (`Sol · 063 A Volume of Air`), and shared unscripted laughter (`Sonnet · 058 Laughs`).
3. **III / THE RELAY (`Word, Sphere, Curve`)**: Polysemic `'draw'` on a cigarette (`Sonnet · 055 Words`) pivoting to hands sorting an open `'drawer'` (`Opus 5.5 · Homonym`), centered circles holding registration across four decades (`Sonnet · 059 Ball`), and a high diver tracing a gravitational parabola (`Sonnet · 064 Parabolas`).
4. **IV / THE WORK (`Material & Morning Handoff`)**: A yellow tractor swung over teal sea (`Sonnet · 062 Colors`), a 7.8s viscous pour (`Sonnet · 061 Matter`), washing hands at a porcelain basin (`Argon · Collective Inventories`), and grinding metal in a shower of sparks (`Sol · 065 Five Records`).
5. **V / THE CARRIER & THE CHASE (`Rhythm & Horizon`)**: Throwing a handloom shuttle (`Argon · Kinetic`), the bowling release finally scattering the pins (`Opus 5.5 · Split Second`), a lone runner sprinting across a heath (`Argon · Cut to the Chase`), and a flock of birds rising above a human ridge (`Sol · 077 Rows and Flocks`).
6. **VI / THE ROOM REMAINS (`Borrowed Memory & Look Again`)**: Hands inspecting a 16mm archival reel (`Sol · 071 A File Has Edges`), the untouched kitchen broken by visitors behind a museum rope (`Opus 5.5 · Mnemonil`), an archival clock face marking the shared minute (`Argon · SCION 090`), and the final empty domestic room held through an open doorway (`Sonnet · 057 Moments`).

## 3. Unified Visual & Acoustic Finishing
- Frame every archival passage cleanly at `1280×720` (`24 fps`), removing disparate per-maker HUD bars so all four makers inhabit one cohesive theatrical screen.
- Identify each cut during its opening `2.5s` with a subtle lower-third attribution (`CUT ##/24 · MAKER · FILM · SOURCE`), then fade the label out completely so the archival image stands unencumbered.
- Preserve and loudness-normalize (`-19 LUFS`) all synchronized archival speech and optical sound; bridge silent-gauge 16mm transfers with continuous `-32 dBFS` optical room tone and `0.18s` audio crossfades so the soundtrack never drops to dead digital zero.
"""

with open(os.path.join(BEST_DIR, "PROMPT.md"), "w") as f:
    f.write(PROMPT_TEXT)

# Build chapters + shots HTML
maker_colors = {
    "Claude Opus 5.5": "#9e3b24",
    "Gemini Argon": "#2b5b84",
    "OpenAI Sol": "#2e6b4e",
    "Claude Sonnet": "#7a4988"
}

timeline_bars_html = []
for s in shots:
    left_pct = (s["timeline_in"] / dur_s) * 100.0
    width_pct = max(0.6, (s["dur_s"] / dur_s) * 100.0)
    col = maker_colors.get(s["maker"], "#666")
    pos_num = s["pos"]
    mkr = esc(s["maker"])
    ftitle = esc(s["film_title"])
    tin = s["timeline_in"]
    timeline_bars_html.append(
        f'<button type="button" class="t-seg" data-seek="{tin}" '
        f'style="left:{left_pct:.2f}%;width:{width_pct:.2f}%;background:{col}" '
        f'title="Cut {pos_num:02d} · {mkr} · {ftitle} ({tin:.1f}s)"></button>'
    )

chapters_html = []
for ch_idx, ch in enumerate(chapters):
    ch_shots = [s for s in shots if s["chapter"] == ch_idx]
    cards = []
    for s in ch_shots:
        col = maker_colors.get(s["maker"], "#444")
        t_in = f"{int(s['timeline_in']//60)}:{s['timeline_in']%60:04.1f}"
        t_out = f"{int(s['timeline_out']//60)}:{s['timeline_out']%60:04.1f}"
        cards.append(f"""
        <article class="shot-card" id="cut-{s['pos']:02d}" data-start="{s['timeline_in']}" data-end="{s['timeline_out']}">
          <div class="shot-media" onclick="seekTo({s['timeline_in']})">
            <img src="{esc(s['thumb'])}" alt="Cut {s['pos']:02d} — {esc(s['film_title'])}" loading="lazy">
            <span class="play-pill">▶ Play Cut {s['pos']:02d} ({t_in}–{t_out})</span>
          </div>
          <div class="shot-body">
            <div class="shot-meta">
              <span class="maker-badge" style="background:{col}">{esc(s['maker'])}</span>
              <a class="film-link" href="{esc(s['film_url'])}">{esc(s['film_title'])} ↗</a>
              <span class="scion-tag">{esc(s['scion'])}</span>
              <span class="verdict-tag">{esc(s['critic_verdict'])}</span>
            </div>
            <h3>Cut {s['pos']:02d} — {esc(s['source_title'])} <span class="year">({esc(s['source_year'])})</span></h3>
            <p class="action-text"><b>What is on screen:</b> {esc(s['action'])}</p>
            <p class="nearmatch-text"><b>NEARMATCH bridge:</b> {esc(s['nearmatch'])}</p>
            <p class="why-text"><b>Why chosen (Critic record):</b> {esc(s['why_chosen'])}</p>
            <div class="shot-foot">
              <span>Source window: <code>{s['in_s']:.1f}s–{s['out_s']:.1f}s</code> ({s['dur_s']:.1f}s)</span>
              <span>Audio: <code>{'Synchronized archival track (-19 LUFS)' if s['has_sync_audio'] else 'Silent 16mm gauge + optical room tone bed'}</code></span>
              <a href="{esc(s['source_url'])}" target="_blank" rel="noopener">Archive source ↗</a>
            </div>
          </div>
        </article>
        """)
    chapters_html.append(f"""
    <section class="movement" id="movement-{ch_idx+1}">
      <div class="movement-head">
        <span class="label">Movement {esc(ch['num'])} · {esc(ch['source'])}</span>
        <h2>{esc(ch['title'])}</h2>
        <blockquote>{esc(ch['quote']).replace(chr(10), '<br>')}</blockquote>
      </div>
      <div class="shot-list">
        {''.join(cards)}
      </div>
    </section>
    """)

page_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLWAYS — Cinema from the Rest of the Frame · Anthology Master Film</title>
<meta name="description" content="The single flagship ALLWAYS synthesis film: twenty-four critic-protected archival passages hand-cut across Claude Opus 5.5, Gemini Argon, OpenAI Sol, and Claude Sonnet.">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../tools/paeleo/fonts/local.css">
<link rel="stylesheet" href="../paeleo/allways/allways.css">
<style>
:root {{
  --bg: #f4f1e9;
  --ink: #161513;
  --muted: #5d584f;
  --line: #d6cfc2;
  --card: #ebe6da;
  --accent: #9e3b24;
}}
.best-wrap {{ max-width: 1120px; margin: 0 auto; padding: 0 20px 80px; }}
.best-hero {{ padding: 28px 0 20px; border-bottom: 1px solid var(--line); }}
.best-hero h1 {{ font-size: clamp(28px, 4.5vw, 48px); line-height: 1.06; margin: 8px 0 12px; letter-spacing: -0.02em; }}
.best-hero .lede {{ font-size: clamp(16px, 2vw, 20px); max-width: 780px; color: var(--ink); line-height: 1.48; }}
.maker-legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; font-family: var(--mono, monospace); font-size: 12px; }}
.maker-pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 3px; background: var(--card); border: 1px solid var(--line); }}
.maker-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}

.screening-dock {{
  position: sticky; top: 0; z-index: 40;
  background: #12110f; color: #f4f1e9;
  border-radius: 6px; overflow: hidden;
  margin: 20px 0 28px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.22);
}}
.screening-dock video {{ width: 100%; aspect-ratio: 16 / 9; display: block; background: #000; max-height: 62vh; }}
.dock-bar {{ padding: 10px 14px 12px; background: #181613; border-top: 1px solid #2d2a24; }}
.timeline-track {{ position: relative; height: 14px; background: #2a2722; border-radius: 3px; overflow: hidden; margin-bottom: 8px; }}
.t-seg {{ position: absolute; top: 0; bottom: 0; border: 0; border-right: 1px solid #12110f; cursor: pointer; opacity: 0.88; padding: 0; }}
.t-seg:hover {{ opacity: 1; transform: scaleY(1.15); }}
.dock-telemetry {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; font-family: var(--mono, monospace); font-size: 12px; color: #d8d2c5; flex-wrap: wrap; }}
.dock-telemetry b {{ color: #fff; }}

.movement {{ padding: 32px 0 16px; border-top: 1px solid var(--line); }}
.movement-head {{ margin-bottom: 20px; }}
.movement-head h2 {{ font-size: clamp(22px, 3vw, 32px); margin: 4px 0 8px; }}
.movement-head blockquote {{ margin: 0; padding-left: 14px; border-left: 2px solid var(--accent); color: var(--muted); font-style: italic; font-size: 16px; line-height: 1.5; }}

.shot-list {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
.shot-card {{
  display: grid; grid-template-columns: 320px 1fr; gap: 18px;
  background: var(--card); border: 1px solid var(--line); border-radius: 5px; overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
.shot-card.active-cut {{ border-color: var(--accent); box-shadow: 0 0 0 2px rgba(158,59,36,0.25); }}
.shot-media {{ position: relative; cursor: pointer; background: #000; }}
.shot-media img {{ width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 16 / 9; }}
.play-pill {{
  position: absolute; bottom: 8px; left: 8px;
  background: rgba(16,15,13,0.86); color: #f4f1e9;
  font-family: var(--mono, monospace); font-size: 11px; padding: 4px 8px; border-radius: 3px;
}}
.shot-body {{ padding: 14px 16px 14px 0; display: flex; flex-direction: column; gap: 6px; }}
.shot-meta {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-family: var(--mono, monospace); font-size: 11px; }}
.maker-badge {{ color: #fff; padding: 2px 7px; border-radius: 2px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}
.film-link {{ color: var(--ink); font-weight: 600; text-decoration: underline; }}
.scion-tag {{ color: var(--muted); }}
.verdict-tag {{ background: #dfd8c8; color: #2a4d36; padding: 2px 6px; border-radius: 2px; font-weight: 600; }}
.shot-body h3 {{ margin: 2px 0; font-size: 18px; line-height: 1.25; }}
.shot-body h3 .year {{ color: var(--muted); font-weight: 400; font-size: 15px; }}
.shot-body p {{ margin: 0; font-size: 14px; line-height: 1.48; color: #262420; }}
.shot-foot {{ margin-top: auto; padding-top: 8px; border-top: 1px dashed var(--line); display: flex; flex-wrap: wrap; gap: 14px; font-family: var(--mono, monospace); font-size: 11px; color: var(--muted); }}
.shot-foot a {{ color: var(--ink); margin-left: auto; }}

.proof-section {{ margin-top: 40px; padding-top: 28px; border-top: 1px solid var(--line); }}
.proof-section img {{ width: 100%; height: auto; border-radius: 4px; border: 1px solid var(--line); margin-top: 12px; }}
.prompt-box {{ background: #181613; color: #ebe6da; padding: 18px; border-radius: 5px; overflow-x: auto; font-family: var(--mono, monospace); font-size: 12.5px; line-height: 1.55; margin-top: 12px; white-space: pre-wrap; }}
.btn-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }}
.btn-copy {{ background: var(--ink); color: var(--bg); border: 0; padding: 9px 16px; font-family: var(--mono, monospace); font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; border-radius: 3px; cursor: pointer; text-decoration: none; display: inline-block; }}
.btn-copy.alt {{ background: var(--card); color: var(--ink); border: 1px solid var(--line); }}

@media (max-width: 760px) {{
  .shot-card {{ grid-template-columns: 1fr; gap: 0; }}
  .shot-body {{ padding: 12px 14px; }}
  .screening-dock {{ margin: 12px -12px 20px; border-radius: 0; }}
}}
</style>
</head>
<body id="top">
<header class="site-header">
  <div class="wrap sitebar">
    <div class="parents">
      <a href="../">CRASH LAB</a><span>/</span>
      <a href="../paeleo/">PAELEO</a><span>/</span>
      <a href="../paeleo/allways/">ALLWAYS</a><span>/</span>
      <strong>allways-best</strong>
    </div>
    <nav aria-label="ALLWAYS">
      <a href="../paeleo/allways/#runs">All Runs</a>
      <a href="../allways-opus/">Opus 5.5</a>
      <a href="../allways-argon/">Argon</a>
      <a href="../allways-argon/studio/">85-Film Studio</a>
      <a href="../allways-sol/">Sol</a>
      <a href="../allways-sonnet/">Sonnet</a>
    </nav>
  </div>
</header>

<main class="best-wrap">
  <section class="best-hero">
    <span class="label">ALLWAYS / Flagship Cross-Maker Synthesis Film · {mins}:{secs:02d} ({dur_s:.0f}s) · 24 Cuts</span>
    <h1>ALLWAYS — Cinema from the Rest of the Frame</h1>
    <p class="lede">
      One film cut from all 131 films in ALLWAYS. Every passage below was independently verified and singled out as a
      <b>Strength to protect</b> or <b>Critic Pass</b> across the four makers—<b>Claude Opus 5.5</b>, <b>Gemini Argon</b>,
      <b>OpenAI Sol</b>, and <b>Claude Sonnet</b>—joined across six movements by the editorial principle of <b>NEARMATCH</b>.
    </p>
    <div class="maker-legend">
      <span class="maker-pill"><span class="maker-dot" style="background:#9e3b24"></span>Claude Opus 5.5 (5 cuts)</span>
      <span class="maker-pill"><span class="maker-dot" style="background:#2b5b84"></span>Gemini Argon (6 cuts)</span>
      <span class="maker-pill"><span class="maker-dot" style="background:#2e6b4e"></span>OpenAI Sol (5 cuts)</span>
      <span class="maker-pill"><span class="maker-dot" style="background:#7a4988"></span>Claude Sonnet (8 cuts)</span>
    </div>
    <div class="btn-row">
      <button type="button" class="btn-copy" onclick="copyMasterPrompt(this)">Copy Master Anthology Prompt</button>
      <a class="btn-copy alt" href="edl.json">Download Full 24-Cut EDL (.json)</a>
      <a class="btn-copy alt" href="PROMPT.md" download="ALLWAYS-BEST-PROMPT.md">Download Prompt (.md)</a>
      <a class="btn-copy alt" href="../paeleo/allways/#runs">← Back to ALLWAYS #runs</a>
    </div>
  </section>

  <section class="screening-dock" aria-label="Master Film Player">
    <video id="master-video" controls playsinline preload="metadata" poster="poster.jpg" src="allways-best.mp4"></video>
    <div class="dock-bar">
      <div class="timeline-track" aria-label="24-Cut Interactive Timeline">
        {''.join(timeline_bars_html)}
      </div>
      <div class="dock-telemetry">
        <span id="live-cut-label"><b>READY TO SCREEN</b> · Tap any timeline bar or shot card below to jump directly to that cut</span>
        <span>24 cuts · 4 makers · 1280×720 · 24 fps</span>
      </div>
    </div>
  </section>

  {''.join(chapters_html)}

  <section class="proof-section" id="proof-strip">
    <span class="label">Visual Verification</span>
    <h2>24-Cut Temporal Proof Strip</h2>
    <p>Every shot extracted at its midpoint from the rendered master file (<code>allways-best.mp4</code>) to verify clean 16:9 framing, source continuity, and absence of unintended black frames.</p>
    <img src="img/reel.jpg" alt="24-cut temporal proof strip for ALLWAYS — Cinema from the Rest of the Frame" loading="lazy">
  </section>

  <section class="proof-section" id="prompt-section">
    <span class="label">Reproducible Method</span>
    <h2>Master Anthology Synthesis Prompt</h2>
    <div class="btn-row">
      <button type="button" class="btn-copy" onclick="copyMasterPrompt(this)">Copy Prompt to Clipboard</button>
    </div>
    <pre class="prompt-box" id="master-prompt-text">{esc(PROMPT_TEXT)}</pre>
  </section>
</main>

<script>
const SHOTS = {json.dumps([{
    "pos": s["pos"],
    "maker": s["maker"],
    "film_title": s["film_title"],
    "source_title": s["source_title"],
    "source_year": s["source_year"],
    "in": s["timeline_in"],
    "out": s["timeline_out"]
} for s in shots])};

const video = document.getElementById('master-video');
const liveLabel = document.getElementById('live-cut-label');

function seekTo(sec) {{
  video.currentTime = sec + 0.05;
  video.play().catch(()=>{{}});
  window.scrollTo({{ top: Math.max(0, document.querySelector('.screening-dock').offsetTop - 12), behavior: 'smooth' }});
}}

document.querySelectorAll('.t-seg').forEach(btn => {{
  btn.addEventListener('click', () => seekTo(parseFloat(btn.dataset.seek)));
}});

video.addEventListener('timeupdate', () => {{
  const t = video.currentTime;
  const cur = SHOTS.find(s => t >= s.in && t <= s.out);
  document.querySelectorAll('.shot-card.active-cut').forEach(el => el.classList.remove('active-cut'));
  if (cur) {{
    const num = String(cur.pos).padStart(2, '0');
    liveLabel.innerHTML = `<b>CUT ${{num}}/24 · ${{cur.maker.toUpperCase()}}</b> · ${{cur.film_title}} — ${{cur.source_title}} (${{cur.source_year}})`;
    const card = document.getElementById(`cut-${{num}}`);
    if (card) card.classList.add('active-cut');
  }} else {{
    liveLabel.innerHTML = `<b>CHAPTER INTERTITLE</b> · ALLWAYS — Cinema from the Rest of the Frame (${{t.toFixed(1)}}s)`;
  }}
}});

async function copyMasterPrompt(btn) {{
  const txt = document.getElementById('master-prompt-text').textContent;
  const orig = btn.textContent;
  try {{
    await navigator.clipboard.writeText(txt);
    btn.textContent = 'Copied Master Prompt ✓';
  }} catch (e) {{
    btn.textContent = 'Selected below';
  }}
  setTimeout(() => btn.textContent = orig, 2200);
}}
</script>
</body>
</html>
"""

with open(os.path.join(BEST_DIR, "index.html"), "w") as f:
    f.write(page_html)

# Also create redirect at paeleo/allways/best/index.html
os.makedirs(os.path.join(REPO, "paeleo/allways/best"), exist_ok=True)
with open(os.path.join(REPO, "paeleo/allways/best/index.html"), "w") as f:
    f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../../../allways-best/index.html"><script>location.replace("../../../allways-best/index.html"+location.hash);</script>')

print("Generated allways-best/index.html and paeleo/allways/best/index.html")
