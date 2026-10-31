"""SCION 40 · title card (3 s) and end card (3 s). The end card is written from the recovered data files, so it can only
say what was measured: the recovered event stream, the measured onsets, the tracking error, and that the capture was
synthesized here. Writes cache/film/0000-0071.jpg and 0840-0911.jpg."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *


def bg():
    g = grain(H, W, 77)
    a = np.zeros((H, W, 3), np.float32) + np.array([30, 27, 30])
    a *= (1 + 0.12 * g)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def title():
    im = bg()
    d = ImageDraw.Draw(im)
    pl = Image.open(os.path.join(CACHE, 'plate', '0360.jpg')).resize((480, 270))
    im.paste(pl, (W - 480 - 80, 220))
    d.text((80, 200), 'PAE-02 · SCION 40', fill=(236, 226, 204), font=font('display', 64))
    d.text((80, 280), 'Physical Tabletop Capture', fill=(236, 200, 130), font=font('display', 52))
    d.text((80, 360), 'fingers move paper on a table;', fill=(210, 204, 190), font=font('serif', 26))
    d.text((80, 396), 'a tracker turns it into film acting.', fill=(210, 204, 190), font=font('serif', 26))
    d.text((80, 470), 'The threshold: a dog that may refuse.', fill=(170, 164, 150), font=font('serif', 22))
    d.text((W - 560, 500), 'the capture plate (synthesized here)', fill=(170, 164, 150), font=font('mono', 14))
    return im


def end():
    ev = [json.loads(l) for l in open(os.path.join(DATA, 'events.jsonl'))]
    on = json.load(open(os.path.join(DATA, 'onsets.json')))['onsets']
    te = json.load(open(os.path.join(DATA, 'tracking_error.json')))
    im = bg()
    d = ImageDraw.Draw(im)
    y = 34
    d.text((60, y), 'What this is made of', fill=(236, 200, 130), font=font('display', 40)); y += 58
    S = font('serif', 19)
    lines = [
        'The "capture" was SYNTHESIZED HERE: no camera, table or performer existed. White-card puppets with',
        'printed fiducial tabs were laid on a layout sheet and moved, frame by frame, by public-domain archive hands',
        '(The Door to Heaven, 1941, archive.org; SAM-matted) into an overhead plate (the inset).',
        'From that plate\'s pixels alone: 4 corner fiducials calibrate the camera; fiducials + Lucas-Kanade flow recover',
        'each piece\'s rigid transform and which card is down; a skin-chroma model mattes out the hands.',
        'The film replays the recovered transforms with new paper skins on a new paper set. The dog is %d body cards' % 41,
        'and 11 head cards, cut here; it moves only by those transforms and by card swaps. Sound: synthesized.',
    ]
    for l in lines:
        d.text((60, y), l, fill=(214, 208, 196), font=S); y += 27
    y += 8
    b = te['pieces']['dog.body']; h = te['pieces']['dog.head']
    d.text((60, y), 'Tracking error vs the synthesized truth: dog body %.2f px mean (card id %.1f%%), head %.2f px (id %.1f%%), hand matte IoU %.2f'
           % (b['pos_err_px_mean'], 100 * b['card_id_correct'], h['pos_err_px_mean'], 100 * h['card_id_correct'], te['hand_matte_iou']['mean']),
           fill=(180, 220, 220), font=font('mono', 14)); y += 30
    d.text((60, y), 'RECOVERED EVENT STREAM (dog), and the choices measured on the render', fill=(236, 200, 130), font=font('mono', 15)); y += 26
    M = font('mono', 13)
    sw = [e for e in ev if e['piece'] in ('dog.body', 'dog.head') and e['ev'] == 'swap' and not (e.get('to', '').startswith(('b_walk', 'b_back', 'b_step')) and e.get('frm', '').startswith(('b_walk', 'b_back', 'b_step')))]
    col_x, k = 60, 0
    for e in sw[:48]:
        d.text((col_x + (k // 16) * 330, y + (k % 16) * 17), '%6.2fs %-4s %s>%s' % (e['t'], 'body' if e['piece'] == 'dog.body' else 'head', e['frm'][2:], e['to'][2:]), fill=(200, 196, 186), font=M)
        k += 1
    x2 = 1060
    d.text((x2, y), 'choice   score  measured', fill=(180, 220, 220), font=M)
    for j, o in enumerate(on):
        d.text((x2, y + 18 * (j + 1)), '%-8s %6.2f  %s' % (o['to'][:8], o['score_t'], '%6.2f' % o['measured_t'] if o['measured_t'] is not None else '  -'), fill=(200, 196, 186), font=M)
    nst = sum(1 for e in ev if e['piece'] == 'dog.body' and e['ev'] == 'swap' and e['to'].startswith(('b_walk', 'b_back', 'b_step')))
    d.text((x2, y + 18 * 9), '+ %d walk-card steps' % nst, fill=(170, 164, 150), font=M)
    d.text((60, H - 34), 'build/, trace.json, data/events.jsonl, data/tracking_error.json in paeleo/handmade/40-tabletop-capture', fill=(140, 134, 124), font=font('mono', 12))
    return im


def main():
    od = os.path.join(CACHE, 'film')
    os_makedirs(od)
    t, e = title(), end()
    for k in range(72):
        a = min(1, k / 10, (71 - k) / 8)
        Image.blend(Image.new('RGB', (W, H)), t, max(a, 0)).save(os.path.join(od, '%04d.jpg' % k), quality=93)
        a = min(1, k / 8)
        Image.blend(Image.new('RGB', (W, H)), e, a).save(os.path.join(od, '%04d.jpg' % (840 + k)), quality=93)
    e.save(os.path.join(F, 'proof', 'end_card.jpg'), quality=90)


if __name__ == '__main__':
    main()
