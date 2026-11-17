# B3 reader cuts (r1)

Two single-route cuts, rendered from the same composite as the film by `QVQ_CUT=across|down python3 films/quatre-vingt-quinze.py`. Every frame in them is a frame of the master film, time-mapped:

- `quatre-vingt-quinze-across-only.mp4`, 35 s:
  - 0–30 s are master 0–30 (title, then the across route A B C D E F G H I);
  - 30–35 s are master 59–64 (the end on the page).
  
  At the end the marks return from across-long to neutral. Rail I stays lit until 59.5 s.
- `quatre-vingt-quinze-down-only.mp4`, 35 s:
  - 0–3 s are master 0–3 (title, with rail II lit from 1.5 s);
  - 3–35 s are master 32–64 (the down route A D G B E H C F I, then the end).
  
  E is at 15–18 s in this cut, and the beat is at 15.5 s.

Sound: each cell's own cue, at its master offset, plus the room. The 30–32 s turn clicks are absent because the turn is not in either cut.

Protocol:
1. Reader 1 sees only the across cut. Reader 2, who is a fresh reader, sees only the down cut.
2. Each reader writes `reader-across.md` or `reader-down.md` before seeing anything else.
3. Only after that may either reader see the other cut or the full film.

The printed page itself, with both rails and the bottom line, appears in both cuts because it is the page.
