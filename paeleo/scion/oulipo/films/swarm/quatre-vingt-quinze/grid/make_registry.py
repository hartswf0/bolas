import json, hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid as G
man = json.load(open(G.SRC / "build_manifest.json"))
CELL = {
 "A": dict(props=["sealed cream envelope (in visitor's front hand)", "service door, shut, small lit EMPTY window", "FSA waiting-room stencil (pale salmon, U3)"],
           cue="footsteps on stone, room tone", outgoing=["lit empty door window (answered in D by the man's profile)", "the envelope (opened in D)", "the shut door (knocked at in C, closed to the end in I)"]),
 "B": dict(props=["bell on wall bracket (close-up)", "red pull-cord off the left edge"], cue="two bell strokes, tail ~2.5 s",
           outgoing=["red cord leaving left (the same cord G hauls)", "bell hangs directly above E on the page: E's up-turned head looks at it"]),
 "C": dict(props=["service door, shut", "visitor's raised fist"], cue="three knocks on wood, then silence", outgoing=["the door never moves"]),
 "D": dict(props=["bench", "envelope torn open", "brass key (CC0 cutout) with red thread through the bow", "capped man's profile in the lit door window"],
           cue="paper tear", outgoing=["the key in her hand (lifted in E)", "the watcher in the window (pulls the cord in G; gone in H)"]),
 "E": dict(props=["brass key raised HIGH at arm's length, glint", "visitor's head turned up toward the panel top"], cue="small key click at the top of the lift",
           outgoing=["the question, answered by F's TANT PIS. (across) / by H's emptiness (down)"]),
 "F": dict(props=["key lying on the bench, red thread trailing off the right edge", "visitor walking out left"], cue="key set down on wood; receding steps",
           outgoing=["red thread off right edge (taut into the door gap in I)"]),
 "G": dict(props=["capped man in a lit salmon interior behind the service door", "red cord rising out of the top-right, clear of his hands and head"],
           cue="rope creak, hand slaps", outgoing=["cord rising top-right (to B's bell, down route next cell)"]),
 "H": dict(props=["empty bench (FSA stencil, mid salmon, U3)", "door window, light going out"], cue="room tone only", outgoing=["dark window: the watcher has gone"]),
 "I": dict(props=["service door, shut", "brass key half drawn under the door, red thread taut into the gap", "balloon tail from behind the door"],
           cue="key scraping on stone", outgoing=["end of both routes"]),
}
PE = {  # (route, cell): (precondition, effect) -- path-local narrative context
 ("across","A"): ("none (first cell)", "she arrives at an empty station with a sealed envelope; the service door is shut"),
 ("across","B"): ("she is waiting, alone", "a bell rings; no one is seen ringing it"),
 ("across","C"): ("a bell rang, a door is there", "she knocks at the service door: no answer"),
 ("across","D"): ("no one answers", "on the bench she opens the envelope: a key (a shadow in the window, unremarked)"),
 ("across","E"): ("a key has just come out of an envelope that is not obviously hers", "'C'EST POUR MOI ?' = is this key meant for me?"),
 ("across","F"): ("the key may not be hers", "TANT PIS: she leaves the key on the bench and goes"),
 ("across","G"): ("the key lies abandoned", "IL (someone) pulls a cord behind the door"),
 ("across","H"): ("someone acted behind the door", "no one left, and the key is gone from the bench"),
 ("across","I"): ("the key is gone from the bench", "the key slides home under the shut door: MERCI = the owner has it back"),
 ("down","A"): ("none (first cell)", "she arrives with a sealed envelope; the door window is lit and empty"),
 ("down","D"): ("the lit window above the door", "she opens the envelope, a key; the capped man watches from the window"),
 ("down","G"): ("the man has seen the key", "he pulls the cord"),
 ("down","B"): ("he has pulled a cord", "the bell rings: his signal"),
 ("down","E"): ("the bell has just rung (its tail still sounding)", "'C'EST POUR MOI ?' = was that bell rung for me? am I called?"),
 ("down","H"): ("she wonders whether she is called", "PLUS PERSONNE: the window is dark, the watcher gone"),
 ("down","C"): ("the man has withdrawn behind the door", "she knocks at his door, answering the call: no answer"),
 ("down","F"): ("the door stays shut to her", "TANT PIS: she gives up and leaves the key on the bench"),
 ("down","I"): ("the key is left on the bench", "he draws it in under the shut door: MERCI = she played her part"),
}
def entry(route, c, i):
    r = G.ROUTES[route]
    pred = r[i-1] if i else None
    if pred is None: side = "pull-in (first cell)"
    else:
        (ra,ca),(rb,cb) = G.cell_rc(pred), G.cell_rc(c)
        side = "from left" if ra==rb else "from above" if ca==cb else ("diagonal return from upper right" if route=="across" else "diagonal return from lower left")
    return side
cells = []
for c in G.CELLS:
    r, col = G.cell_rc(c)
    occ = []
    for route in ("across","down"):
        i = G.ROUTES[route].index(c)
        pre, eff = PE[(route,c)]
        occ.append({"route": route, "index": i+1, "film_window_s": [3+3*i, 6+3*i] if route=="across" else [32+3*i, 35+3*i],
                    "predecessor": G.ROUTES[route][i-1] if i else None, "successor": G.ROUTES[route][i+1] if i<8 else None,
                    "camera_entry": entry(route,c,i), "precondition": pre, "effect": eff,
                    "arrow": (lambda a: None if a is None else {"edge": f"{a}->{c}", "at_page_px": [round(v) for v in G.gutter_point(a,c)[0]], "angle_deg": round(G.gutter_point(a,c)[1],1)})(G.ROUTES[route][i-1] if i else None)})
    cells.append({"id": c, "row": r, "col": col, "page_origin_px": list(G.cell_origin(c)), "size_px": [G.CW, G.CH],
                  "ground": "salmon (painted pool, light at %s)" % (list(G.POOL[c][:2]),) if c in G.SALMON else "white (paper)",
                  "chamfered_corners": [k for k,v in G._chamfered(c).items() if v],
                  "lettering": G.LETTERING[c], "props": CELL[c]["props"], "sound_cue": CELL[c]["cue"],
                  "outgoing_cues": CELL[c]["outgoing"], "occurrences": occ,
                  "layers": {k: man["editor_layers"][f"{k}_{c}"] for k in ("ground","lettering","overlay")}})
reg = {
 "unit": "U1 story-grid-letterer", "plan_revision": "r0", "built": "2026-11-17",
 "routes": G.ROUTES, "shared_final": "I", "fixed_points_of_transpose": ["A","E","I"],
 "contract_check": G.contract_check(),
 "cells": cells,
 "page": {"size": [G.PW, G.PH], "col_x": G.COLX, "row_y": G.ROWY, "gutter": G.GUT, "title": G.TITLE,
          "title_flips": "every second glyph (index 1,3,5,...) turned 180 deg about the x-band centre; film turn drawings 0..4 via title_layer(turn)",
          "bottom_line": G.BOTTOM_LINE, "marks_px": G.MARKS, "mark_turn_order": G.MARK_TURN_ORDER,
          "mark_states": {"across": G.U_ACROSS, "neutral": G.U_NEUTRAL, "down": G.U_DOWN, "turn": "turn_states(u_from,u_to,k), k=0..3 (3 drawings per mark)"},
          "rails": {"left": "II en bas: A D G B E H C F I vertical", "right": "I en travers: 3x3"},
          "scaffold": man["page_scaffold"]},
 "api": {"module": "films/swarm/quatre-vingt-quinze/grid/grid.py",
         "functions": ["ground(c)", "lettering(c, tail_to=None)", "cell_overlay(c)", "marks_layer(states[8])", "turn_states(u_from,u_to,k)",
                       "rails_layer(rail)", "title_layer(turn=None)", "bottom_layer()", "arrow_layer(a,b,k)", "gutter_point(a,b)",
                       "scaffold_layer(marks,rail,title_turn)", "compose_page(cells,marks,rail)", "page_base()", "paper_sheet()", "contract_check()"],
         "rule": "no function takes a route; marks take u, rails take a display state, arrows take an edge; the editor maps route -> state",
         "compositing": "page = page_base (paper + grounds) <- cell content (U2 figures/props, U3 stencils) <- lettering(c) <- scaffold_layer (chamfer paper, borders, tabs, marks, rails, title, bottom line); film adds arrow_layer"},
 "editor_media_dir": "films/sources/quatre-vingt-quinze/story-grid-letterer/", "editor_layers": man["editor_layers"],
 "proof_sheets": {k: man[k] for k in ("marks_sheet","alphabet_sheet","title_turn_sheet")},
 "foraged": [{
   "id": "PAPER", "title": "[Unidentified Production: Sketch no. 27, Blank Sheet of Paper]", "author": "Federal Theatre Project (U.S.); Nels Astner",
   "license": "Public domain (US government work; LoC Federal Theatre Project restriction statement: not aware of any copyright)",
   "license_url": "https://www.loc.gov/item/musftpsets.200218222/", "source_url": "https://www.loc.gov/item/musftpsets.200218222/",
   "file_url": "https://tile.loc.gov/storage-services/public/music/musftpsets-200218222/musftpsets-200218222.0001.jp2",
   "local_path": "films/sources/quatre-vingt-quinze/grid/loc_blank_0001.jpg (copied from films/sources/la-cite-raymond-queneau/picture/, sha256 f96ca0949a00d8705286996562aa70d877f6d84c216ea54b795acbdbf1d44530)",
   "what_it_shows": "a blank cream sheet of drawing paper on a grey ground, taped at the edges; fine fibre and laid texture",
   "verified_date_or_place": "rights field re-read from loc.gov item JSON 2026-11-17 (grid/loc_blank_meta.json); item date 1934 (predates FTP 1935 founding; low risk, blank sheet carries no expression)",
   "used_as": "the paper of the page and every cell: crop (260,300,2940,2214) of the scan, fibre relief only (scan / own 40 px blur, ^1.4) on palette white; salmon pigment settles into the same relief"}],
 "handmade": [
   "broad-nib single-stroke capital alphabet A-Z, 0-9, É È Ê À Ç, ! ? . , ' - ( ) : — · (grid.py CAPS + pen_stroke; sheet grid/alphabet.png)",
   "bold lowercase title hand (q u a t r e v i n g z, wavy hyphen) and rail lowercase (b s), rounder nib (title_layer; title_turn.png shows drawings 0..4)",
   "balloons (irregular hand ovals, curved pointed tails), corner caption boxes ruled on two sides, red SFX with darker edge pass: lettering_A..I.png",
   "hand-ruled 7 px borders with bow, pressure drift and overshoot; corners meeting a crossing mark chamfered as on Lécroart's page; id tabs",
   "painted salmon pools in D E G I: first coat plus 150 broad brush strokes per cell, density graded to the light (ground_D/E/G/I.png)",
   "eight red barbed crossing marks: fletched arrows on both axes plus fletched diagonals, two ink passes; states across/neutral/down and 3 turn drawings (marks_states.png)",
   "margin rails (II en bas vertical list with arrowed links; I en travers 3x3), bottom line",
   "red cut-paper gutter arrow, scissor facets and small cast shadow, drawings 0 (entering) and 1 (laid)"],
 "absences": [
   "Commons API returned HTTP 429 on a paper-texture search (2026-11-17); no new Commons download made; the LoC paper scan already in the repository was re-verified and used instead",
   "No figures, props, bell, key or stencil plates here (U2 / U3 own them); page_scaffold.png is therefore grounds + lettering + furniture only",
   "Title colour follows plan.md section 6 (ink #2b2021); the reference title is rust-red: title_layer(color=G.RED) is available if the operator prefers"],
 "notes_for_editor": [
   "Balloon tails point at the test shot's page-pose mouths; if U2 moves a mouth, call lettering(c, tail_to=(x,y)) and use the SAME value for page and film",
   "E's balloon sits top-left so a camera framing B's bottom edge with E's top half holds the bell and 'C'EST POUR MOI ?' together (test-shot note)",
   "Marks: across u=0, down u=1, page/end neutral u=0.5; turn at 30-32 s: for mark MARK_TURN_ORDER[j], drawings k=1..3 of turn_states(0,1,k)",
   "G: keep the red cord rising to the top-right clear of hands and head (registry prop text) -- U2 draws it"],
}
json.dump(reg, open(Path(__file__).resolve().parent / "registry.json", "w"), indent=1, ensure_ascii=False)
print(reg["contract_check"]["ok"])
