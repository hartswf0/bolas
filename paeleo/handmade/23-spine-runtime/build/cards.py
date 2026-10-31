"""SCION 23 · title card and end card. The end card draws the track timeline straight from actor/dog.timeline.json
(clip bars, mix ramps) and states only what the film shows."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from fonts import font

BG = (30, 26, 34); INK = (238, 226, 206); DIM = (170, 156, 142); WARM = (214, 150, 86); COOL = (120, 140, 190)


def base():
    im = Image.new('RGB', (W, H), BG)
    a = np.asarray(im, np.float32)
    rng = np.random.default_rng(3)
    a = a * (1 + 0.05 * (rng.random((H, W, 1)) - 0.5))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def title():
    im = base(); d = ImageDraw.Draw(im)
    d.text((110, 250), 'PAE-02 · SCION 23 · Spine — Skeletal Motion Runtime', font=font('shoulders_800', 52), fill=INK)
    d.text((112, 330), 'the threshold, played by a game-ready actor in a skeletal runtime', font=font('literata_italic', 28), fill=DIM)
    at = Image.open(os.path.join(ACTOR, 'actors.png')).convert('RGBA')
    at = at.crop((0, 0, 1100, at.size[1])).resize((660, int(at.size[1] * 0.6)))
    im.paste(at, (112, 420), at)
    d.text((112, 600), 'its atlas: every part painted in code', font=font('mono', 16), fill=DIM)
    im.save(os.path.join(CACHE, 'title.png'))


def end():
    im = base(); d = ImageDraw.Draw(im)
    d.text((70, 40), 'What it is made of', font=font('shoulders_800', 44), fill=INK)
    sk = json.load(open(os.path.join(ACTOR, 'dog.skel.json')))
    nreg = len(json.load(open(os.path.join(ACTOR, 'actors.atlas.json')))['regions'])
    lines = [
        'The dog is a runtime actor: %d bones, %d slots, %d two-bone IK legs, painted atlas regions and two' % (len(sk['bones']), len(sk['slots']), len(sk['ik'])),
        'skinned meshes (torso, tail). Its 10 clips are mixed on two tracks; the head track is layered over the body.',
        'Turns swap the torso, head, neck, ear and leg attachments through body views 0/45/90/135 deg and reorder the slots.',
        'Paws are planted by a foot planner and held by IK. The person is a second actor; the porch and room are',
        'painted in code too (%d atlas regions in all). Voice, dog and room sounds are synthesized. No found footage.' % nreg,
    ]
    for k, l in enumerate(lines):
        d.text((70, 112 + k * 30), l, font=font('literata', 19), fill=INK)
    # track timeline, from the file the runtime played
    tl = json.load(open(os.path.join(ACTOR, 'dog.timeline.json')))['entries']
    x0, x1 = 120, 1210
    def X(t): return x0 + (x1 - x0) * t / 32.0
    ys = {0: 400, 1: 500}
    d.text((70, 300), 'the track timeline the film plays (actor/dog.timeline.json)', font=font('mono_600', 17), fill=WARM)
    for tr, y in ys.items():
        d.text((30, y + 8), 'body' if tr == 0 else 'head', font=font('mono', 16), fill=DIM)
        d.line([x0, y + 40, x1, y + 40], fill=(80, 72, 84), width=1)
        es = [e for e in tl if e['track'] == tr]
        for k, e in enumerate(es):
            if not e['clip']: continue
            t1 = es[k + 1]['start'] if k + 1 < len(es) else 32.0
            col = COOL if tr == 0 else WARM
            xa, xb = X(e['start']), X(t1)
            xm = X(e['start'] + e['mix'])
            d.polygon([(xa, y + 40), (xm, y + 4), (xb, y + 4), (xb, y + 40)], fill=col + (0,) if False else col)
            d.polygon([(xa, y + 40), (xm, y + 4), (xm, y + 40)], fill=tuple(int(c * 0.6) for c in col))
            lab = e['clip']
            f = font('mono', 13)
            if d.textlength(lab, font=f) < xb - xa - 4:
                d.text((xa + 4, y + 14), lab, font=f, fill=BG)
            else:
                d.text((xa, y - 14 - (k % 3) * 14), lab, font=f, fill=DIM)
    for t in range(0, 33, 4):
        d.line([X(t), 560, X(t), 566], fill=DIM); d.text((X(t) - 6, 570), '%d' % t, font=font('mono', 13), fill=DIM)
    d.text((x1 - 30, 588), 's', font=font('mono', 13), fill=DIM)
    d.text((70, 620), 'wedges = mix durations (cross-fades); bars = how long each clip holds the track',
           font=font('mono', 15), fill=DIM)
    d.text((70, 660), 'Synthesized formant voice; painted gouache in Python/numpy; runtime, IK and mixer written for this film.',
           font=font('literata_italic', 17), fill=DIM)
    im.save(os.path.join(CACHE, 'end.png'))


if __name__ == '__main__':
    title(); end()
