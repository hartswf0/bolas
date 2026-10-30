"""SCION 37 cards: the 3 s title and the 3 s end card (what the film is made of, the weight maps, LBS against DQS).
Numbers on the end card are read from the files that measured them (mesh report, proof metrics, perform audit)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, '..', '..', '..', 'tools', 'paeleo', 'fonts')
CACHE = os.path.join(HERE, 'cache'); PROOF = os.path.join(ROOT, 'proof')
W, H = 1280, 720
BG = (16, 15, 18); INK = (238, 226, 200); DIM = (170, 160, 140); ACC = (232, 160, 90)

def F(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def title():
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    big = F('f5.woff2', 72, 800); mid = F('f27.woff2', 30); mono = F('f14.woff2', 18)
    t = 'PAE-02 · SCION 37 · Weighted Skinning'
    d.text(((W - d.textlength(t, font=big)) / 2, 250), t, font=big, fill=INK)
    s = 'Mesh Attachment Laboratory'
    d.text(((W - d.textlength(s, font=mid)) / 2, 370), s, font=mid, fill=ACC)
    u = 'the threshold: one continuous skin over twenty-seven bones'
    d.text(((W - d.textlength(u, font=mono)) / 2, 430), u, font=mono, fill=DIM)
    im.save(os.path.join(CACHE, 'title.png'))


def endcard():
    mesh = json.load(open(os.path.join(ROOT, 'assets', 'mesh', 'dog.json')))
    met = json.load(open(os.path.join(PROOF, 'skinning_metrics.json')))['summary']
    st = json.load(open(os.path.join(PROOF, 'stress_twist.json')))
    coat = json.load(open(os.path.join(ROOT, 'assets', 'texture', 'coat.json')))
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    big = F('f5.woff2', 44, 800); txt = F('f34.woff2', 17); mono = F('f14.woff2', 14); small = F('f14.woff2', 12)
    d.text((48, 34), 'What it is made of', font=big, fill=INK)
    lines = [
        ('One skin.', 'a single closed triangle mesh, %d vertices, %d triangles, genus 0 — surface nets over a signed-distance '
                      'sculpture laid on the bones; nothing is cut into parts.' % (mesh['vertices'], mesh['triangles'])),
        ('Bones and weights.', '%d bones with bind matrices; every vertex carries at most 4 weights, summing to 1, found by '
                               'heat diffusion over the skin (Pinocchio bone heat).' % len(mesh['bones'])),
        ('Coat.', 'film pixels of the public-domain archive dog (Amateur Film New Jersey C): %d fur patches from %d frames, '
                  'quilted inside painted region masks and mapped by the bind-pose UVs.' % (coat['patches'], len(coat['frames']))),
        ('Motion.', 'the score drives skeletal clips: yaw, head, ears, tail, a gait clock with two-bone IK (planted paws do '
                    'not slide), a lying clip; the head leads the turn back.'),
        ('Fix.', 'skinned with dual quaternions. Linear blend with the same weights: in the stress test a neck twisted %d° '
                 'keeps %.0f%% of its girth (DQS %.0f%%); in the film\'s lie the hock keeps %.0f%% (DQS %.0f%%).' % (st['neck_twist_deg'], 100 * st['lbs_neck_ring'],
                 100 * st['dqs_neck_ring'], 100 * met['hock L']['lbs_min'], 100 * met['hock L']['dqs_at_that_frame'])),
        ('Rest.', 'a numpy rasterizer; the porch, the door and the room are plain facets; the voice, crickets, claws and '
                  'door are synthesized. A person is a skinned mesh too, faceless.'),
    ]
    y = 104
    for head, body in lines:
        d.text((48, y), head, font=F('f27.woff2', 18), fill=ACC)
        words = body.split(); line = ''; yy = y + 24
        for wd in words:
            if d.textlength(line + ' ' + wd, font=txt) > 560:
                d.text((48, yy), line.strip(), font=txt, fill=INK); yy += 22; line = ''
            line += ' ' + wd
        d.text((48, yy), line.strip(), font=txt, fill=INK)
        y = yy + 34
    # pictures: the weights, one bone's heat, LBS vs DQS
    def put(path, box, label):
        p = Image.open(path).convert('RGB'); p.thumbnail((box[2], box[3]))
        im.paste(p, (box[0], box[1])); d.text((box[0], box[1] + p.height + 4), label, font=small, fill=DIM)
        return p.height
    x0 = 650
    h1 = put(os.path.join(PROOF, 'weights_all_1.png'), (x0, 40, 300, 190), 'weights, 27 bones (colour = bone)')
    put(os.path.join(PROOF, 'weights_neck2.png'), (x0 + 310, 40, 300, 190), 'bone heat: neck2')
    put(os.path.join(PROOF, 'weights_stifleL.png'), (x0 + 310, 260, 300, 190), 'bone heat: left stifle')
    put(os.path.join(PROOF, 'weights_shoulderL.png'), (x0, 260, 300, 190), 'bone heat: left shoulder')
    s = Image.open(os.path.join(PROOF, 'stress_twist_160.png')).convert('RGB').crop((0, 140, 1280, 480)).resize((600, 160))
    im.paste(s, (x0, 535)); d.text((x0 + 6, 539), 'linear blend', font=small, fill=INK); d.text((x0 + 306, 539), 'dual quaternion', font=small, fill=INK); d.text((x0, 535 + 164), 'the neck twisted 160°: linear blend collapses (left), dual quaternions hold (right)', font=small, fill=DIM)
    im.save(os.path.join(CACHE, 'endcard.png'))


if __name__ == '__main__':
    os.makedirs(CACHE, exist_ok=True); title(); endcard(); print('cards ok')
