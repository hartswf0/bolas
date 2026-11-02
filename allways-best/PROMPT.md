# ALLWAYS — Master Anthology Synthesis Prompt (Across All Makers)

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
