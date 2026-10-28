"""SCION 42 · the 32 s scene, frame by frame, from the score.  Renders build/cache/frames/s_XXXX.jpg (768 frames) and
measures what the dog did on screen into ../data/measure.json (centroid, head, back line, feet, facing, view state).

Visibility states of the dog:
  profile-L  the learned puppet facing the door (left)                     (learned layers + learned/override pose)
  profile-R  the same puppet placed mirrored: its back to the door          (the source's right-facing frames were in training)
  view       a whole archive frame of the dog turning (3/4 and front views) - the layers never learned a turn
  look-back  profile-R body with the head and neck layers mirrored about their learned hinge (the head comes round)
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import world as Wo
import person as Pe
from puppet import Puppet, ViewFrame
from pose import Poser

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
FPS = 24
OUT = os.path.join(HERE, 'cache', 'frames'); os.makedirs(OUT, exist_ok=True)

T_REFUSE = SCORE['choices'][2]['t']; T_WATCH2 = SCORE['choices'][3]['t']
TURN_AWAY = [(15, 0), (16, 0), (17, 0), (31, 0), (38, 0), (40, 0), (41, 0)]     # left profile -> camera -> right
TURN_DUR = 0.46
RISE = (T_WATCH2, T_WATCH2 + 0.42)        # lying, head come round, rises
TURN_BACK = [(41, 0), (40, 0), (38, 0), (31, 0), (17, 0), (16, 0), (15, 0)]
TB0 = RISE[1]; TB_DUR = 0.46

S_DOG = 1.55


def smooth(a, b, t):
    t = np.clip((t - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def door_angle(t):
    # swings through square and on, back against the inside wall
    return 0.25 + (2.85 - 0.25) * smooth(6.2, 7.1, t)


def tint_map(x_screen, lit):
    """per-column light on the dog: dusk ambient plus the warm light from the doorway"""
    amb = np.array([0.50, 0.55, 0.80], np.float32)
    d = np.clip((x_screen - Wo.X(Wo.WALL_OUT)) / Wo.S, -1, None)
    warm = lit * np.exp(-np.clip(d, 0, None) / 2.4) * 0.75
    return amb[None, :] * 0.95 * (1 - 0.3 * warm[:, None]) + warm[:, None] * np.array([1.0, 0.72, 0.42])[None, :] * 0.55


def main():
    t0 = time.time()
    pp = Puppet(); po = Poser(pp); n = po.n
    st = Wo.build_static()
    ax, ay = pp.anchor
    frames = SCORE['frames']
    meas = []
    only = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:Wo.Ht, 0:Wo.Wd].astype(np.float32)
    vign = (1 - 0.35 * (((xx - 640) / 900) ** 2 + ((yy - 380) / 600) ** 2)).clip(0.5, 1)[..., None]
    lie_hist = 0.0
    for fr in frames:
        i, t = fr['i'], fr['t']
        if only and i not in only: continue
        d = fr['dog']; a = d['act']; pe = fr['person']
        lit = smooth(6.2, 6.95, t)
        bg = Wo.background(st, lit)
        img = Image.fromarray(Wo.to_u8(bg))
        Pe.stool(img)
        # person
        step = (pe['x'] + 0.28) * 9.0
        lean = 1.0 if pe['voice'] == 'call' else 0.0
        Pe.draw(img, pe['x'], pe['sit'], pe['reach'], pe['low'], lean, step if pe['sit'] < 0.9 else 0, 0.3 + 0.7 * lit)
        Wo.door_leaf(img, door_angle(t))
        can = np.asarray(img, np.float32) / 255.
        X = Wo.X(d['x'])
        # ---- what the dog does this frame
        state = d['state']
        mode = 'profile-L'; view = None
        head_low = float(np.clip((0.9 - a['head']) / 0.45, 0, 1))
        lie = a['lie']; rest = a['rest']; look = a['look']
        phase = a['walk_phase']; moving = a['moving']
        crouch = a['crouch']
        if d['state'] == 'retreat' or (1.0 <= t < 2.9 and d['v'] > 0):
            phase = -phase                         # backing away: the learned walk run backwards
        if T_REFUSE <= t < T_REFUSE + TURN_DUR:
            mode = 'view'; view = TURN_AWAY[min(len(TURN_AWAY) - 1, int((t - T_REFUSE) / TURN_DUR * len(TURN_AWAY)))]
        elif T_REFUSE + TURN_DUR <= t < RISE[0]:
            mode = 'profile-R'
        elif RISE[0] <= t < RISE[1]:
            mode = 'look-back'
            lie = 1 - smooth(RISE[0] + 0.12, RISE[1], t); rest = 0.0; head_low = 0.3
        elif TB0 <= t < TB0 + TB_DUR:
            mode = 'view'; view = TURN_BACK[min(len(TURN_BACK) - 1, int((t - TB0) / TB_DUR * len(TURN_BACK)))]
        if mode in ('profile-R', 'look-back') or (mode == 'view'):
            pass
        if mode == 'profile-R':
            lie = a['lie']; rest = a['rest']
        if t >= TB0 + TB_DUR and t < 14.7:
            lie = 0.0; rest = 0.0
        breathe = 0.008 * np.sin(2 * np.pi * t / 1.7) * (1 - moving)
        extra_head = 0.0
        if t >= 14.708 and state == 'approach':
            head_low = max(head_low, 0.95)
        T_pose, info = po.pose(phase=phase, moving=moving, head_low=min(1, head_low) * (1 - min(1, lie)), lie=lie, rest=rest, look=look,
                               crouch=crouch, breathe=breathe,
                               wag=a['wag'] * 0.35 * np.sin(2 * np.pi * 2.6 * t) + 0.25 * (a['tail'] - 0.5))
        # tail: tuck and wag on the rump layer's hinge
        # the dog's shadow on the boards
        sh_w = 0.55 * Wo.S * (1 + 0.25 * lie); sh = np.exp(-((xx - X) / sh_w) ** 2 - ((yy - Wo.FLOOR - 3) / 7.0) ** 2)
        can *= (1 - 0.55 * sh)[..., None]
        tint_cols = tint_map(np.arange(Wo.Wd, dtype=np.float32), lit)
        tint_img = np.broadcast_to(tint_cols[None], (Wo.Ht, Wo.Wd, 3))
        rec = dict(i=i, t=t, state_score=state, x_score=d['x'], mode=mode, view=view, override=info['override'],
                   lie=lie, rest=rest, look=look, head_low=head_low, moving=moving, walk_phase=a['walk_phase'])
        if mode == 'view':
            vf = ViewFrame.get(*view)
            x0, y0, x1, y1 = vf['bbox']
            # size: a 3/4 view matches the puppet's silhouette area, a front view its height
            if view[0] in (31, 38):
                sv = S_DOG * (pp.bbox[3] - pp.bbox[1]) / max(1, vf['h']) * 0.9
            else:
                sv = S_DOG * np.sqrt(pp.tmask.sum() / max(1, (vf['a'] > 0.5).sum())) * 0.95
            pad = 4
            crop = (max(0, x0 - pad), max(0, y0 - pad), min(383, x1 + pad), min(287, y1 + pad))
            g = vf['im'][crop[1]:crop[3], crop[0]:crop[2]]; al = vf['a'][crop[1]:crop[3], crop[0]:crop[2]]
            w2, h2 = int(round(g.shape[1] * sv)), int(round(g.shape[0] * sv))
            g2 = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w2, h2), Image.LANCZOS), np.float32) / 255.
            a2 = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((w2, h2), Image.LANCZOS), np.float32) / 255.
            # feet on the boards, body centre at the dog's x
            cx = (vf['cx'] - crop[0]) * sv; fy = (vf['foot'] - crop[1]) * sv
            px0 = int(round(X - cx)); py0 = int(round(Wo.FLOOR - fy))
            reg = can[py0:py0 + h2, px0:px0 + w2]
            tn = tint_img[py0:py0 + h2, px0:px0 + w2]
            col = g2[..., None] * tn * 1.15
            can[py0:py0 + h2, px0:px0 + w2] = reg * (1 - a2[..., None]) + col * a2[..., None]
            alpha = np.zeros((Wo.Ht, Wo.Wd), np.float32); alpha[py0:py0 + h2, px0:px0 + w2] = a2
            # facing of a view, measured from the kit's nose keypoint when the frame has one
            kp = json.load(open(os.path.join(ROOT, '..', 'kit', 'archive-dog', 'pose_agent_v8.json'))).get(str(view[0]))
            if kp:
                rec['facing_src'] = 'kit nose keypoint'
                ys_, xs_ = np.nonzero(ViewFrame.get(*view)['a'] > 0.5)
                rec['nose_rel'] = float(kp['nose'][0] - xs_.mean())
            rec['view_scale'] = float(sv)
            head_xy = None; joints = {}
        else:
            if mode == 'profile-L':
                place = np.array([[S_DOG, 0, X - S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]])
                r = pp.render(T_pose, place, can, tint=tint_img)
            else:
                place = np.array([[-S_DOG, 0, X + S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]])
                if mode == 'look-back':
                    # the head comes round: head and neck layers drawn mirrored about the learned neck hinge (hard
                    # layer weights, no blend across the flip), raised a little: the look back over the shoulder
                    k_n = n['neck'] if n['neck'] >= 0 else n['head']
                    piv = pp.pivot[(k_n, int(pp.parent[k_n]))]
                    js = (place @ T_pose[k_n] @ np.array([piv[0], piv[1], 1.0]))[:2]
                    Fm = np.array([[-1, 0, 2 * js[0]], [0, 1, 0], [0, 0, 1.0]])
                    lift = smooth(RISE[0], RISE[0] + 0.1, t)
                    Rr = np.eye(3); c, s_ = np.cos(-0.35 * lift), np.sin(-0.35 * lift)
                    Rr[:2, :2] = [[c, -s_], [s_, c]]; Rr[:2, 2] = js - Rr[:2, :2] @ js
                    hsel = np.isin(pp.lab, [k for k in (n['head'], n['neck']) if k >= 0])
                    T2 = T_pose.copy()
                    for k in (n['head'], n['neck']):
                        if k >= 0: T2[k] = np.linalg.inv(place) @ (Rr @ Fm @ place @ T_pose[k])
                    r0 = pp.render(T_pose, place, can, tint=tint_img, sel=~hsel)
                    r1 = pp.render(T2, place, can, tint=tint_img, sel=hsel, hard=True)
                    info['override'] = 1.0
                    r = dict(alpha=np.maximum(r0['alpha'], r1['alpha']), q=np.where(hsel[:, None], r1['q'], r0['q']))
                    T_pose = T2
                else:
                    r = pp.render(T_pose, place, can, tint=tint_img)
            alpha = r['alpha']
            q = r['q']
            hk = pp.lab == n['head']
            head_xy = q[hk].mean(0)
            rec['head_top_y'] = float(q[hk][:, 1].min())
            # back line: the highest point of trunk + back layers (the line of the back)
            bk = np.isin(pp.lab, [k for nm, k in n.items() if nm in ('trunk',) or nm.startswith('back')])
            rec['back_top_y'] = float(np.percentile(q[bk][:, 1], 3))
            rec['head_xy'] = head_xy.tolist()
            for nm in ('foreleg', 'hind'):
                kk = pp.lab == n[nm]
                if kk.any():
                    lo = q[kk][np.argsort(q[kk][:, 1])[-40:]].mean(0); rec[nm + '_foot'] = lo.tolist()
            joints = pp.joint_screen(T_pose, place)
            rec['joints'] = {int(k): v.tolist() for k, v in joints.items()}
        # pins on the discovered hinges (brass inside the learned range, pale when the pose is an override)
        if joints:
            dr = Image.fromarray((np.clip(can, 0, 1) * 255).astype(np.uint8)); dd = ImageDraw.Draw(dr, 'RGBA')
            for k, (jx, jy) in joints.items():
                ov = abs(info['angles'].get(k, 0)) > 0.05 or (mode == 'look-back' and k in (n['head'], n['neck']))
                c = (150, 185, 235, 150) if ov else (225, 185, 110, 150)
                dd.ellipse([jx - 2.2, jy - 2.2, jx + 2.2, jy + 2.2], fill=c)
            can = np.asarray(dr, np.float32) / 255.
        m = alpha > 0.5
        ys, xs = np.nonzero(m)
        rec['x_screen'] = float(xs.mean()); rec['y_screen'] = float(ys.mean())
        rec['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        rec['area'] = int(m.sum())
        # film finish: grain and vignette
        can = can * vign + rng.normal(0, 0.018, (Wo.Ht, Wo.Wd, 1)).astype(np.float32)
        Image.fromarray((np.clip(can, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 's_%04d.jpg' % i), quality=92)
        meas.append(rec)
        if i % 48 == 0: print(i, round(time.time() - t0, 1), mode, flush=True)
    if not only:
        json.dump(meas, open(os.path.join(ROOT, 'data', 'measure.json'), 'w'))
    else:
        json.dump(meas, open(os.path.join(HERE, 'cache', 'measure_partial.json'), 'w'))
    print('scene done', len(meas), round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
