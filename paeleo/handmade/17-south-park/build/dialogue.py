"""SCION 17 // dialogue v1: one phoneme chart drives both the person's mouth atlas and the synthesized voice.

Each line: start time (s, scene clock), loudness register (call | soft), caption text, and phonemes with durations (ms).
The mouth shape for every frame is looked up from the phoneme sounding at that frame (PHONEME_TO_MOUTH); the voice is
synthesized from the same list (sound.py), so lips and sound cannot drift apart.
"""
VERSION = 'dialogue-v1'

LINES = [
    dict(t=1.00, reg='call', text='Come here.', speed=1.0,
         ph=[('k', 60), ('AH', 170), ('m', 110), ('_', 50), ('h', 70), ('IH', 170), ('ER', 260)]),
    dict(t=3.40, reg='call', text='Hey! Come here!', speed=1.0,
         ph=[('h', 50), ('EY', 210), ('_', 90), ('k', 50), ('AH', 150), ('m', 90), ('_', 30), ('h', 60), ('IH', 190), ('ER', 300)]),
    dict(t=7.40, reg='soft', text="it's all right.", speed=1.3,
         ph=[('IH', 90), ('t', 50), ('s', 110), ('AO', 190), ('l', 110), ('r', 80), ('AY', 300), ('t', 60)]),
    dict(t=10.40, reg='soft', text="it's all right.", speed=1.25,
         ph=[('IH', 90), ('t', 50), ('s', 110), ('AO', 190), ('l', 110), ('r', 80), ('AY', 300), ('t', 60)]),
    dict(t=26.40, reg='soft', text='come in.', speed=1.25,
         ph=[('k', 60), ('AH', 170), ('m', 100), ('IH', 150), ('n', 220)]),
]

# the phoneme chart: phoneme -> mouth drawing in the atlas
PHONEME_TO_MOUTH = {
    'k': 'CONS', 't': 'CONS', 's': 'S', 'h': 'CONS', 'n': 'CONS', '_': 'REST',
    'm': 'MBP', 'AH': 'AA', 'IH': 'EE', 'ER': 'OO', 'EY': 'EE', 'AO': 'OH', 'l': 'L', 'r': 'OO', 'AY': 'AA',
}


def timeline():
    """[(t0, t1, phoneme, line_index)] in scene seconds"""
    out = []
    for li, L in enumerate(LINES):
        t = L['t']
        for p, ms in L['ph']:
            d = ms / 1000.0 * L['speed']
            out.append((t, t + d, p, li)); t += d
    return out


def line_span(li):
    tl = [x for x in timeline() if x[3] == li]
    return tl[0][0], tl[-1][1]


def mouth_at(t):
    """mouth drawing and the line it belongs to (or REST, None). AY glides to EE in its second half."""
    for t0, t1, p, li in timeline():
        if t0 <= t < t1:
            m = PHONEME_TO_MOUTH[p]
            if p == 'AY' and t > (t0 + t1) / 2: m = 'EE'
            if p == 'EY' and t > (t0 + t1) / 2: m = 'EE'
            return m, li
    return 'REST', None
