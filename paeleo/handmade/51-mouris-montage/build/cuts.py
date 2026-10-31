"""SCION 51 · the cutting score (shot rhythm as a first-class object) and the narrated-word layer.
A cut is a whole-image substitution, held for a measured number of frames. At each cut the dog's coat, eyes and paws,
the facade, the door leaf and the lit interior each take a new whole image from the imagery class that matches the moment.
Holds accelerate on the calls (2 frames) and slow on the soft voice and the light (16-36 frames). On the approach the cuts
fall on the dog's footfalls (every 0.275 m of travel), so the rhythm is the walk.
Writes cutting-score.json and words.json at the folder root."""
import json, math, os
from lib import OUT, FPS, SCORE

N = 768
inv = {r['id']: r for r in json.load(open(os.path.join(OUT, 'inventory.json')))['records']}


def pool(layer, temps):
    return [r['id'] for r in inv.values() if layer in r['layers'] and r['temperature'] in temps]


# sections: (t0, t1, hold frames (list = decelerating sequence), temperature, why)
SECTIONS = [
    (0.0, 1.0, [12], 'neutral', 'dusk, waiting: slow'),
    (1.0, 2.333, [2], 'cold', 'call 1 (come here): the cut accelerates to 2 frames, hard cold images'),
    (2.333, 3.417, [3, 4, 5, 6, 8, 10], 'neutral', 'the call ends: the rhythm decelerates'),
    (3.417, 4.6, [2], 'cold', 'call 2 + reach: 2-frame cuts, hard images'),
    (4.6, 6.2, [6, 8, 10, 12], 'neutral', 'the person steps aside and sits: slowing'),
    (6.2, 7.4, [12, 12], 'warm', 'the door opens, light comes out, the hand is offered low'),
    (7.4, 9.4, [16], 'warm', 'soft voice (it\'s all right): long holds, soft warm images'),
    (9.4, 10.4, [12], 'warm', 'silence, watching'),
    (10.4, 11.6, [28], 'warm', 'soft voice again: one long hold'),
    (11.6, 14.708, [14], 'warm', 'waiting in its own time'),
    (14.708, 23.792, 'steps', 'warm', 'the approach: one cut per footfall (0.275 m of travel)'),
    (23.792, 26.4, [20], 'warm', 'lies down across the sill'),
    (26.4, 27.4, [24], 'warm', 'come in (soft): a single hold, lamps'),
    (27.4, 32.01, [24, 30, 36, 46], 'warm', 'stays: the rhythm slows to stillness'),
]

COAT = {'cold': pool('coat', ['cold']), 'neutral': pool('coat', ['neutral']), 'warm': pool('coat', ['warm'])}
EYE = {'cold': pool('eye', ['cold']), 'neutral': pool('eye', ['neutral']), 'warm': pool('eye', ['warm'])}
PAW = {'cold': pool('paw', ['cold']), 'neutral': pool('paw', ['neutral']), 'warm': pool('paw', ['warm'])}
ROOM = {'cold': pool('room', ['cold']), 'neutral': pool('room', ['neutral']), 'warm': pool('room', ['warm', 'neutral'])}
DOOR = {'cold': pool('door', ['cold', 'neutral']), 'neutral': pool('door', ['neutral']), 'warm': pool('door', ['neutral'])}
INTERIOR = pool('interior', ['warm'])
HAND = {'cold': pool('hand', ['neutral']), 'neutral': pool('hand', ['neutral', 'warm']), 'warm': pool('hand', ['warm'])}


def build():
    poses = json.load(open(os.path.join(OUT, 'build/cache/poses.json')))
    walk = [p['dog']['walk'] for p in poses]
    starts = []
    for (t0, t1, holds, temp, why) in SECTIONS:
        f0, f1 = round(t0 * FPS), min(N, round(t1 * FPS))
        if holds == 'steps':
            f = f0; starts.append((f, temp, why))
            for k in range(f0 + 1, f1):
                if math.floor(walk[k] / 0.275) != math.floor(walk[k - 1] / 0.275) and k - starts[-1][0] >= 4:
                    starts.append((k, temp, why))
            continue
        f = f0; j = 0
        while f < f1:
            starts.append((f, temp, why)); f += holds[min(j, len(holds) - 1)]; j += 1
    cuts = []; ctr = {}
    def pick(d, temp, key):
        L = d[temp] if isinstance(d, dict) else d
        n = ctr.get(key, 0); ctr[key] = n + 1
        return L[(n * 5 + 1) % len(L)] if len(L) > 2 else L[n % len(L)]
    for k, (f, temp, why) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else N
        if end <= f:
            continue
        t = f / FPS
        door_open = t >= 6.2
        cuts.append({'n': len(cuts), 'frame': f, 'hold': end - f, 't': round(t, 3), 'temperature': temp, 'why': why,
                     'coat': pick(COAT, temp, 'coat' + temp), 'eye': pick(EYE, temp, 'eye' + temp), 'paw': pick(PAW, temp, 'paw' + temp),
                     'room': pick(ROOM, temp, 'room' + temp), 'door': pick(DOOR, temp, 'door' + temp),
                     'interior': pick(INTERIOR, 'warm', 'int') if door_open else 'lamps.bulb.halo',
                     'hand': pick(HAND, temp, 'hand' + temp)})
    # 26.4 come in: lamps only in the interior and on the facade
    for c in cuts:
        if 26.4 <= c['t'] < 27.4:
            c['room'] = 'lamps.lantern.brass'; c['interior'] = 'lamps.bulb.glow'
    tot = sum(c['hold'] for c in cuts); assert tot == N, tot
    rhythm = []
    for (t0, t1, holds, temp, why) in SECTIONS:
        cs = [c for c in cuts if t0 <= c['t'] < t1]
        if cs:
            hs = [c['hold'] for c in cs]
            rhythm.append({'t0': t0, 't1': t1, 'temperature': temp, 'why': why, 'cuts': len(cs),
                           'cuts_per_s': round(len(cs) / (t1 - t0), 2), 'mean_hold_frames': round(sum(hs) / len(hs), 2), 'holds': hs})
    json.dump({'about': 'The cutting score. Every cut is a whole-image substitution of the dog\'s coat/eyes/paws and of the room, '
               'held for `hold` frames at 24 fps; images are inventory ids (inventory.json). The dog\'s silhouette, pose and '
               'shading never cut: only what it is made of.', 'fps': FPS, 'n_frames': N, 'n_cuts': len(cuts),
               'rhythm_by_section': rhythm, 'cuts': cuts}, open(os.path.join(OUT, 'cutting-score.json'), 'w'), indent=1)
    # ---------------- the narrated words, an image layer of cut letters
    words = [
        {'text': 'COME HERE', 'voice': 'call', 'spoken': [1.0, 2.3], 'syll': [1.0, 1.32], 'temperature': 'cold', 'size': 92,
         'letters_from': ['hard.clock.bell', 'voices.trumpet', 'hard.train.front', 'hard.traffic.signal', 'hard.wheel.spokes', 'hard.ladder.rungs'],
         'anchor': 'above_person', 'exit': 'drop'},
        {'text': 'COME HERE', 'voice': 'call', 'spoken': [3.4, 4.6], 'syll': [3.4, 3.7], 'temperature': 'cold', 'size': 110,
         'letters_from': ['hard.traffic.signal', 'hard.wheel.spokes', 'voices.trumpet', 'hard.clock.bell', 'hard.ladder.rungs', 'hard.train.front'],
         'anchor': 'above_person', 'exit': 'drop'},
        {'text': "it's all right", 'voice': 'soft', 'spoken': [7.4, 9.4], 'syll': [7.4, 7.85, 8.3], 'temperature': 'warm', 'size': 70,
         'letters_from': ['soft.sleepingbag', 'soft.flower', 'soft.basket.weave', 'lamps.lantern.brass', 'voices.cello', 'lamps.bulb.glow'],
         'anchor': 'by_hand', 'exit': 'fade'},
        {'text': "it's all right", 'voice': 'soft', 'spoken': [10.4, 11.6], 'syll': [10.4, 10.8, 11.15], 'temperature': 'warm', 'size': 60,
         'letters_from': ['soft.flower', 'soft.basket.weave', 'soft.sleepingbag', 'voices.cello', 'lamps.bulb.glow', 'lamps.lantern.brass'],
         'anchor': 'by_hand2', 'exit': 'fade'},
        {'text': 'come in', 'voice': 'soft', 'spoken': [26.4, 27.4], 'syll': [26.4, 26.8], 'temperature': 'warm', 'size': 72,
         'letters_from': ['lamps.bulb.glow', 'lamps.lantern.brass', 'soft.flower', 'soft.sleepingbag', 'lamps.bulb.halo', 'soft.basket.weave'],
         'anchor': 'in_doorway', 'exit': 'fade_late'},
    ]
    json.dump({'about': 'Narrated words as an image layer: each spoken phrase appears as cut-out letters (glyph-shaped cuts from '
               'inventory images, class matched to the voice) at the moment it is spoken; one word per syllable onset. '
               'The voice in the soundtrack starts at the same frame.', 'words': words},
              open(os.path.join(OUT, 'words.json'), 'w'), indent=1)
    return cuts


if __name__ == '__main__':
    c = build(); print(len(c), 'cuts')
