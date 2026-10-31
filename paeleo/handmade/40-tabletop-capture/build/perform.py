"""SCION 40 · the performers' sheet. Turns the score into what four hands do to paper on the table, frame by frame:
which card lies where (stage px, radians), and which hand holds what. This is the GROUND TRUTH of the synthesized
capture. It is used for two things only: to synthesize the plate (plate.py), and to measure the tracker's error
afterwards (track.py --eval). The film is never rendered from it. Writes cache/perform.json."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))
Q = 12.5                      # px the dog card advances per walk card: stride 0.5 m = 100 px over 8 cards


def act(i):
    return FR[i]['dog']['act']


def seq(t, keys):
    """keys: list of (t0, value): last key with t0 <= t"""
    v = keys[0][1]
    for t0, val in keys:
        if t >= t0 - 1e-9:
            v = val
    return v


def dog_cards(i):
    t = i / FPS
    f = FR[i]
    x = f['dog']['x']
    a = act(i)
    X = x_stage(x)
    # --- body card and its position
    if t < 1.0:
        body, X = 'b_stand_L', x_stage(3.0)
    elif t < 2.333:                                  # backing away: crouched walk cards run backwards, feet planted
        n = int(round((X - x_stage(3.0)) / Q))
        body, X = 'b_back_%d' % ((-n) % 8), x_stage(3.0) + n * Q
    elif t < 3.417:                                  # watching, the last steps back upright, then still
        n = int(round((X - x_stage(3.0)) / Q))
        Xq = x_stage(3.0) + n * Q
        body = 'b_step_%d' % ((-n) % 8) if t < 2.9 else 'b_stand_L'
        X = Xq
    else:
        X0 = x_stage(4.0)
        body = seq(t, [(3.417, 'b_turn45'), (3.583, 'b_turn90'), (3.75, 'b_turn135'), (3.917, 'b_stand_R'),
                       (4.375, 'b_settle_R'), (4.75, 'b_lie_R'), (7.80, 'b_settle_R'), (7.96, 'b_stand_R'),
                       (8.125, 'b_turn225'), (8.29, 'b_turn270'), (8.46, 'b_turn315'), (8.625, 'b_stand_L')])
        X = X0
        if t >= 14.708 and t < 23.792:              # coming, head low: walk cards, one per 12.5 px of travel
            d = x_stage(4.0) - x_stage(x)
            n = int(math.floor(d / Q + 0.5)) + 1      # the first card goes down at the moment of the choice
            body, X = 'b_walk_%d' % (n % 8), x_stage(4.0) - n * Q
            X = max(X, x_stage(0.59))
        elif t >= 23.792:
            body = 'b_settle_L' if t < 24.2 else 'b_lie_L'
            X = x_stage(0.59)
    # --- head card and pitch (radians; + turns a left-facing muzzle down)
    head_up = a['head']
    if t < 1.0:
        head, pitch = 'h_L', (0.9 - head_up) * 0.5 - 0.05
    elif t < 2.333:
        head, pitch = 'h_L_flat', 0.25 + (0.9 - head_up) * 0.25
    elif t < 3.417:
        head, pitch = 'h_L', (0.9 - head_up) * 0.5 - 0.05
    elif t < 7.458:
        head = seq(t, [(3.417, 'h_45'), (3.583, 'h_90'), (3.75, 'h_135'), (3.917, 'h_R')])
        rest = a['rest']
        pitch = -(0.15 + 0.35 * (1 - head_up) + 0.25 * rest) if head == 'h_R' else 0.0
        if t > 7.2:                                  # lifts the head a moment before it comes round
            pitch = -(0.15 + 0.35 * (1 - head_up) + 0.25 * rest) * (1 - smooth((t - 7.2) / 0.12))
            head = seq(t, [(7.2, 'h_R'), (7.33, 'h_135'), (7.40, 'h_90')])
    elif t < 14.708:
        head = 'h_L'
        pitch = -0.05 + 0.08 * math.sin((t - 9.5) * 1.3) * smooth((t - 9.0) / 1.0)   # small looking tilts
        if t < 8.62:
            head = seq(t, [(7.458, 'h_L'), (8.125, 'h_L'), (8.29, 'h_315'), (8.46, 'h_315'), (8.625, 'h_L')])
            pitch = 0.0
    elif t < 23.792:
        head, pitch = 'h_L_low', 0.32 + 0.05 * math.sin(t * 2.2)
    else:
        look, rest = a['look'], a['rest']
        if t < 26.55:
            head, pitch = 'h_L_low', 0.15 + 0.25 * (1 - head_up)
        elif t < 28.4:
            head, pitch = ('h_in', -0.12 * a['look']) if a['look'] > 0.35 else ('h_L', 0.0)
        else:
            head, pitch = 'h_L_flat', 0.15 + 0.35 * rest
        if t < 26.55 and t > 26.4:
            head = 'h_L'
    return body, X, head, pitch


def person_cards(i):
    t = i / FPS
    p = FR[i]['person']
    PX = 268 + (p['x'] + 0.28) / (-0.97) * (-190)
    card = seq(t, [(0, 'p_stand'), (1.0, 'p_call'), (2.3, 'p_stand'), (3.4, 'p_reach'), (4.6, 'p_stand'),
                   (5.4, 'p_step'), (5.62, 'p_stand'), (5.8, 'p_step'), (6.0, 'p_down'), (6.3, 'p_sit'), (6.8, 'p_sit_low')])
    if t >= 6.3:
        PX = 268 - 190
    return card, PX


def main():
    rng = np.random.default_rng(40)
    frames = []
    # hands: (name, mirrored?, arm direction from the grip toward the frame edge, engagements)
    HANDS = {
        'A': dict(mirror=False, ang=math.radians(-14), eng=[('dog.body', 0.8, 3.1), ('dog.body', 3.3, 5.0), ('dog.body', 7.7, 8.95), ('dog.body', 14.5, 24.6)]),
        'B': dict(mirror=True, ang=math.radians(-128), eng=[('dog.head', 0.85, 2.6), ('dog.head', 3.3, 6.8), ('dog.head', 7.1, 9.0), ('dog.head', 9.8, 13.2), ('dog.head', 14.55, 24.7), ('dog.head', 25.9, 29.0)]),
        'C': dict(mirror=True, ang=math.radians(-150), eng=[('person', 0.85, 2.45), ('person', 3.25, 4.75), ('person', 5.25, 7.0)]),
        'D': dict(mirror=False, ang=math.radians(-35), eng=[('door', 6.0, 6.55), ('light', 6.15, 7.0)]),
    }
    for i in range(N):
        t = i / FPS
        body, X, head, pitch = dog_cards(i)
        bm = CARDS[body]
        pieces = {}
        pieces['dog.body'] = dict(card=body, X=X, Y=GROUND, th=0.0)
        nx, ny = to_stage(bm['neck'], bm['anchor'], X, GROUND, 0.0)
        hm = CARDS[head]
        # a right-facing head turns its muzzle down with negative rotation
        th = pitch if hm['yaw'] in (0, 315, 45, 40) or head in ('h_L', 'h_L_low', 'h_L_flat') else pitch
        pieces['dog.head'] = dict(card=head, X=nx, Y=ny, th=th)
        pc, PX = person_cards(i)
        pieces['person'] = dict(card=pc, X=PX, Y=GROUND, th=0.0)
        door = seq(t, [(0, 'd_ajar'), (6.2, 'd_mid'), (6.38, 'd_open')])
        pieces['door'] = dict(card=door, X=WALL[0], Y=GROUND, th=0.0)
        u = smooth((t - 6.25) / 0.55)
        pieces['light'] = dict(card='light', X=8 + u * (WALL[0] - 8), Y=GROUND + 4, th=0.0)
        hands = []
        for hn, hd in HANDS.items():
            pres, piece = 0.0, None
            for (pn, t0, t1) in hd['eng']:
                if t0 - 0.35 <= t <= t1 + 0.35:
                    pres = smooth((t - (t0 - 0.35)) / 0.35) * (1 - smooth((t - t1) / 0.35))
                    piece = pn
            if piece is None or pres <= 0:
                continue
            pp = pieces[piece]
            cm = CARDS[pp['card']]
            gx, gy = to_stage(cm['tab']['grip'], cm['anchor'], pp['X'], pp['Y'], pp['th'])
            hands.append(dict(hand=hn, piece=piece, grip=[gx, gy], ang=hd['ang'], mirror=hd['mirror'], presence=round(pres, 4), held=pres > 0.999))
        # a held piece trembles a little with the fingers
        for h in hands:
            if h['held']:
                p = pieces[h['piece']]
                p['X'] += float(rng.normal(0, 0.25)); p['Y'] += float(rng.normal(0, 0.25))
        frames.append(dict(i=i, t=round(t, 4), pieces=pieces, hands=hands))
    json.dump(dict(about=__doc__, frames=frames), open(os.path.join(CACHE, 'perform.json'), 'w'))
    print('perform', len(frames))


if __name__ == '__main__':
    main()
