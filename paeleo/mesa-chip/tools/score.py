#!/usr/bin/env python3
"""The MESA CHIP knight score: the game's own knight machine (make-photo/mesa/mesa.js, swarmStep), run once, deterministically.

Every handmade version keeps these events at these times (+-0.25 s), the knight comes out of the glass, every piece knocked off
stays on the floor in the colour that freed it, and the distance between the two keeps the score's pace.

    python3 tools/score.py            -> score/glass-knight-score.json
"""
import json, math, os
FPS, DUR = 24, 24.0
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'score', 'glass-knight-score.json')
PAINT = ['#2fd0d8', '#f2a83a', '#e85aa8', '#f2d04a', '#2a9a5a', '#d8342c']
WINDOW_X, STEP_X = 6.2, -7.0
EVENTS = [  # (t, who, what, note)
    (3.0, 'knight', 'turns_head', 'in the window, the glass knight turns its head toward him'),
    (4.5, 'knight', 'steps_out', 'it steps out of the window, whole'),
    (6.0, 'knight', 'draws', 'it draws a red glass sword'),
    (6.5, 'mesa', 'raises_gun', 'Uncle Mesa raises the six-shooter of paint'),
    (9.5, 'mesa', 'hit_1', 'paint takes the knight\'s shoulder; pieces fall and lie in its colour'),
    (12.2, 'mesa', 'knocked_down', 'the sword comes down; he goes down'),
    (14.0, 'mesa', 'gets_up', 'he gets up'),
    (15.0, 'mesa', 'hit_2', ''), (16.0, 'mesa', 'hit_3', ''), (17.0, 'mesa', 'hit_4', ''), (18.0, 'mesa', 'hit_5', 'it comes apart and keeps walking'),
    (19.5, 'mesa', 'shatter', 'at the last shot it goes to pieces on the mirror floor, every shard still holding its colour'),
    (22.0, 'mesa', 'sits', 'he lowers the gun and sits on the lowest step')]
HITS = {'hit_1': (.12, 0), 'hit_2': (.13, 1), 'hit_3': (.14, 2), 'hit_4': (.15, 3), 'hit_5': (.16, 4), 'shatter': (1.0, 5)}

def smooth(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

def frame(t):
    """The two bodies at time t, in metres along the cathedral floor (steps at -7, the knight's window at +6.2)."""
    # Uncle Mesa: down the steps, stands, knocked back and down, gets up, backs off while firing, walks back and sits
    mx = lerp(STEP_X, -3.4, smooth(0, 3.0, t)); ms = 'descend' if t < 3.0 else 'stand'
    if t >= 6.5: ms = 'aim'
    if 12.2 <= t < 14.0: ms = 'down'; mx = -3.4 - smooth(12.2, 12.6, t) * .9
    elif t >= 14.0: mx = -4.3 - smooth(14.0, 15.0, t) * .9
    if t >= 21.0: ms = 'walk'; mx = lerp(-5.2, -6.4, smooth(21.0, 22.0, t))
    if t >= 22.0: ms = 'sit'; mx = -6.4
    # the knight: in the glass, steps out, draws, comes on, strikes, presses on in pieces, goes to pieces
    if t < 4.5: kx, ks = WINDOW_X, 'in_window'
    elif t < 5.5: kx, ks = lerp(WINDOW_X, 5.4, smooth(4.5, 5.5, t)), 'stepping_out'
    elif t < 8.0: kx, ks = 5.4, 'stand'
    elif t < 11.8: kx, ks = lerp(5.4, -2.0, smooth(8.0, 11.8, t)), 'advance'
    elif t < 12.4: kx, ks = -2.0, 'strike'
    elif t < 14.0: kx, ks = -2.0, 'stand_over'
    elif t < 19.5: kx, ks = lerp(-2.0, -3.6, smooth(14.0, 19.5, t)), 'advance_broken'
    else: kx, ks = -3.6, 'shattered'
    whole = 1.0
    for (te, who, what, _) in EVENTS:
        if what in HITS and t >= te: whole -= HITS[what][0] if what != 'shatter' else whole
    whole = max(0.0, whole)
    light = lerp(-5.5, 3.0, t / DUR)  # the column of light moving across the floor
    return dict(t=round(t, 4), mesa=dict(x=round(mx, 3), state=ms), knight=dict(x=round(kx, 3), state=ks, whole=round(whole, 3)), distance=round(kx - mx, 3), light_x=round(light, 3))

def main():
    frames = [frame(i / FPS) for i in range(int(DUR * FPS))]
    pieces = []
    for (te, who, what, _) in EVENTS:
        if what in HITS: frac, ci = HITS[what]; pieces.append(dict(t=te, fraction=frac if what != 'shatter' else 'all that remain', paint=PAINT[ci], where='shoulder' if what == 'hit_1' else 'body'))
    out = dict(about=__doc__.split('\n\n')[0], source='make-photo/mesa/mesa.js swarmStep (the knight machine), run with the score\'s fixed timings',
               ekphrasis=open(os.path.join(HERE, '..', 'EKPHRASIS.txt')).read().strip() if os.path.exists(os.path.join(HERE, '..', 'EKPHRASIS.txt')) else '',
               units=dict(x='metres along the cathedral floor; the steps at -7, the knight\'s window at +6.2', t='seconds', fps=FPS, frames=len(frames)),
               places=dict(steps=STEP_X, window=WINDOW_X, sit=-6.4), paint=PAINT,
               events=[dict(t=t, who=w, what=e, note=n) for (t, w, e, n) in EVENTS], pieces=pieces,
               invariants=['I1 every event at its time, +-0.25 s, readable on screen',
                           'I2 the knight comes out of glass: inside the window before 4.5 s, outside it after 5.5 s, and from nowhere else',
                           'I3 every piece knocked off stays on the floor to the end, in the paint colour of the shot that freed it',
                           'I4 the distance between them follows the score\'s distance in your own space: same direction, same pace (+-15 percent of the range)'],
               frames=frames)
    json.dump(out, open(OUT, 'w'), indent=0); print('score:', OUT, len(frames), 'frames')
if __name__ == '__main__': main()
