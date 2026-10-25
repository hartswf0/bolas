"""The person's voice as timed syllables (shared by the sound and by the face's mouth control, so the mouth source frame
is chosen by what is being said). Times in scene seconds. Calls are loud; the soft voice is about 12 dB quieter."""
import math

CALL, SOFT = 1.0, 0.25
SYL = [
    # (start, end, amplitude, pitch Hz start, pitch Hz end, vowel)   'Come here.'
    (1.00, 1.27, CALL, 210, 230, 'uh'), (1.36, 1.86, CALL, 250, 205, 'ee'),
    # 'Come HERE!' again, reaching
    (3.42, 3.66, CALL * 1.05, 225, 245, 'uh'), (3.73, 4.30, CALL * 1.1, 275, 215, 'ee'),
    # 'It's all right' softly (7.4) and again (10.4)
    (7.45, 7.58, SOFT, 175, 170, 'ih'), (7.66, 7.98, SOFT, 172, 160, 'aw'), (8.08, 8.55, SOFT, 165, 140, 'ai'),
    (10.45, 10.58, SOFT * 0.95, 170, 166, 'ih'), (10.66, 10.98, SOFT * 0.95, 168, 156, 'aw'), (11.08, 11.55, SOFT * 0.95, 160, 136, 'ai'),
    # 'Come in' softly (26.4)
    (26.42, 26.66, SOFT, 168, 172, 'uh'), (26.76, 27.25, SOFT, 175, 140, 'ih'),
]


def envelope(t):
    """0..1 loudness-shaped mouth opening at time t, and the amplitude class"""
    for s, e, a, *_ in SYL:
        if s - 0.03 <= t <= e + 0.04:
            u = (t - s) / (e - s)
            env = math.sin(math.pi * min(1, max(0, u))) ** 0.6
            return env, a
    return 0.0, 0.0


def mouth_state(t):
    env, a = envelope(t)
    if env < 0.2: return 'closed'
    if a >= 0.9 and env > 0.55: return 'open'
    return 'half'
