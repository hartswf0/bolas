import sys, json; sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from rec56_59 import make
r = json.load(open("/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways/p58_rec.json"))
agent_tailed = {k: sum(1 for b in v if b["speaker"] == "AGENT") for k, v in r.items()}
make(58, "talks-himself-through", "He talks himself through it", "photo-cutout", "voice and language",
     "keeps E0-E5, the four lines and the outcome",
     "films/swarm/99-ways/build/p58_talks_himself.py (panels: kit/build_page01.py, 99-ways-template rest layers)",
     ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
      "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
     ["page 01's eight photo panels recomposed from films/swarm/99-ways-template/page/rest/P1..P8 with the template balloons left out",
      "P2: P1's own cut-out agent (torso, head and their paper shadows) laid risen and moved to the right edge, his head leaving the frame (P2's sleeve stub left out); P6: P4's cut-out agent laid at the window side (P6's view is P4's, 40 px on), so the agent is in all eight panels",
      "eleven HANDMADE cut-paper balloons in the shared pen hand: nine tailed to the agent's mouth (his running commentary: 'Four-fifteen, the SERVICE door. Key's in the cupboard. Right!' / 'Up we get. Cupboard, key, door. Easy as pie.' / 'Past the SERVICE door, over to the cupboard...' / 'Eh? The time? Just a moment...' / 'Let me look at the clock...' + the answer / 'There she goes. Now, the cupboard.' / 'Here's the cupboard. Open her up... there we are.' / 'Now I came over for... for...' + the forgetting line) and the stranger's two canon lines",
      "hand-ruled borders; page scaled 2550x3300 -> 2200x2850; folio by pen99.folio"],
     {"E0": "P1 memo, 'Four-fifteen, the SERVICE door. Key's in the cupboard. Right!'; P2 rising, 'Up we get...'; P3 walking past the SERVICE card",
      "E1": "P4 the stranger's question through the window; his 'Eh? The time? Just a moment...'",
      "E2": "P5 'Let me look at the clock...' then 'Ten past four, by the clock.' under the clock at 4:10",
      "E3": "P6 the thanks; his 'There she goes. Now, the cupboard.'",
      "E4": "P7 'Here's the cupboard. Open her up... there we are.' key on its hook",
      "E5": "P8 'Now I came over for... for...' then 'Well, here I am... and what for?'; key unmoved; SERVICE card on the closed door"},
     "none: the four lines verbatim; the agent's added commentary is his own, in his own balloons",
     "he talks his way across the page: panel by panel his balloons are laid; in P2 he rises (two positions) before his balloon comes; in P8 the faltering 'for... for...' comes first, then the forgetting line",
     ["b01: P1 with its balloon", "b02: + P2, the agent half risen, no balloon", "b03: P2 risen", "b04: P2 balloon",
      "b05: + P3-P5", "b06: + P6-P7", "b07: + P8 with only 'Now I came over for... for...'", "b08: the forgetting line (= the page)"],
     {"agent_tailed_balloons_per_panel": agent_tailed, "every_panel_agent_balloon": all(v >= 1 for v in agent_tailed.values()) and len(agent_tailed) == 8,
      "lines_verbatim": True, "outcome": "key on its hook, SERVICE door closed (P8 picture)"})
