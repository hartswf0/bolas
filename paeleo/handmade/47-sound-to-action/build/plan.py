"""Sound dramaturg. Place the spoken lines and the world's sounds on the scene clock (0..32 s, 24 fps), as typed
audio events. The dog is driven from these events (build/xsheet.py): it reacts to the vowel that carries each cue,
after a fixed hearing latency, so the voice is the measurable cause of its choices.

Placement rule: a cue line is placed so that cue vowel onset + LAT lands on the score's choice time. The lines that
do not cause a choice are placed by the score's timeline (voice/hand/door) and by acting needs.
Output: build/audio_timeline.json
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
LINES = {l['id']: l for l in json.load(open(os.path.join(HERE, 'voice_lines.json')))}
LAT = 0.17            # s, from the onset of the cue vowel to the first frame of the dog's answer (hearing latency)
CH = {c['to'] + ('' if c['to'] != 'watch' else '@%.2f' % c['t']): c['t'] for c in SCORE['choices']}


def place_by_cue(lid, t_choice):
    L = LINES[lid]
    return round(t_choice - LAT - L['cue_vowel_onset'], 3)


def main():
    ev = []

    def voice(lid, t0, causes=None, src='person'):
        L = LINES[lid]
        ev.append({'id': lid, 'kind': 'voice', 'style': L['kind'], 'src': src, 't0': t0, 't1': round(t0 + L['dur'], 3),
                   'text': L['text'], 'cue_t': round(t0 + L['cue_vowel_onset'], 3), 'cue_word': L['cue_word'],
                   'words': [{'w': w['w'], 't0': round(t0 + w['t0'], 3), 't1': round(t0 + w['t1'], 3)} for w in L['words']],
                   'phones': [{'p': p['p'], 't0': round(t0 + p['t0'], 3), 't1': round(t0 + p['t1'], 3)} for p in L['phones']],
                   'causes': causes, 'file': f'build/cache/voice/{lid}.wav'})

    t_retreat = CH['retreat']; t_refuse = CH['refuse']; t_look = [c['t'] for c in SCORE['choices'] if c['from'] == 'refuse'][0]
    voice('call1', place_by_cue('call1', t_retreat), causes='retreat')           # "Come here!"  -> backs away
    voice('call4', 1.30, causes='retreat continues while the call sounds')       # "Come on!"    -> keeps backing
    voice('call3', place_by_cue('call3', t_refuse), causes='refuse')             # "Come here!" + reach -> turns its back
    ev[-1]['id'] = 'call3'
    voice('call4', 3.92, causes='refusal deepens: lies down, back turned')       # "Come on!"
    ev[-1]['id'] = 'call4b'
    voice('soft1', place_by_cue('soft1', t_look), causes='watch: turns back to look')   # "It's all right."
    voice('soft2', 10.45, causes='ears and tail answer; no step yet')            # "It's okay."
    voice('soft3', 26.4 - LAT - LINES['soft3']['cue_vowel_onset'] + 0.08, causes='looks in through the door, then settles')  # "Come in."
    # the world
    ev += [
        {'id': 'room', 'kind': 'room', 'src': 'yard', 't0': 0, 't1': 32, 'desc': 'dusk room tone: air and crickets'},
        {'id': 'pstep1', 'kind': 'step', 'src': 'person', 't0': 4.98, 'x': -0.45},
        {'id': 'pstep2', 'kind': 'step', 'src': 'person', 't0': 5.22, 'x': -0.75},
        {'id': 'pstep3', 'kind': 'step', 'src': 'person', 't0': 5.46, 'x': -1.05},
        {'id': 'sit', 'kind': 'sit', 'src': 'person', 't0': 5.80, 't1': 6.35, 'x': -1.25, 'desc': 'cloth and a board taking weight'},
        {'id': 'push', 'kind': 'touch', 'src': 'person', 't0': 6.18, 'x': -0.45, 'desc': 'palm on the door'},
        {'id': 'door', 'kind': 'creak', 'src': 'door', 't0': 6.22, 't1': 6.95, 'x': -0.46, 'desc': 'hinge creak as the door swings in',
         'causes': 'gesture accent only: one ear turns to the sound; the dog does not answer'},
        {'id': 'hand', 'kind': 'cloth', 'src': 'person', 't0': 6.80, 't1': 7.15, 'x': -0.9},
        {'id': 'sniff', 'kind': 'sniff', 'src': 'dog', 't0': 13.86, 'n': 3, 'gap': 0.16, 'causes': 'approach: the dog reads the air, then comes'},
        {'id': 'hand_rest', 'kind': 'cloth', 'src': 'person', 't0': 29.6, 't1': 29.9, 'x': -1.0},
    ]
    ev.sort(key=lambda e: e['t0'])
    out = {'about': 'Typed audio events on the scene clock (s). voice events carry words and phones from the synthesizer; '
                    'cue_t is the onset of the vowel the dog answers. LAT is the hearing latency used by the exposure sheet.',
           'LAT': LAT, 'fps': 24, 'events': ev}
    json.dump(out, open(os.path.join(HERE, 'audio_timeline.json'), 'w'), indent=1)
    for e in ev:
        if e['kind'] == 'voice':
            print(f"{e['id']:7s} {e['t0']:6.2f}-{e['t1']:6.2f} cue {e['cue_t']:6.2f} -> {e['causes']}  {e['text']}")


if __name__ == '__main__':
    main()
