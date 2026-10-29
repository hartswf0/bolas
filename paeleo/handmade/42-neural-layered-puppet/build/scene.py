"""SCION 42 · the 32 s scene, frame by frame, from the score.  Renders build/cache/frames/s_XXXX.jpg (768 frames) and
measures what the dog did on screen into ../data/measure.json.

Visibility states of the dog (all one material: the template frame's pixels or the same film's frames, same tint):
  profile-L / profile-R  the learned puppet facing the door / with its back to it (placed mirrored)
  turn-learned           the puppet carried, layer by layer, from its profile pose into its *learned fit* of an archive
                         turning frame (15, or 41 mirrored), so its silhouette meets the real frame exactly
  turn-blend             cross-dissolve between that learned fit and the real archive frame (same silhouette, same place)
  view                   the real archive turning frames 16, 17, 31, 38, 40 (front of the dog toward the camera)
  head-swing             lying with its back to the door, the head and neck layers swing up and round about their learned
                         hinge until the head faces the door (7.458-7.71 s), then the dog rises
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import world as Wo
import person as Pe
from puppet import Puppet, ViewFrame, to3
from pose import Poser

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
KEYS = json.load(open(os.path.join(ROOT, '..', 'kit', 'archive-dog', 'pose_agent_v8.json')))
FPS = 24
OUT = os.path.join(HERE, 'cache', 'frames'); os.makedirs(OUT, exist_ok=True)

T_REFUSE = SCORE['choices'][2]['t']; T_WATCH2 = SCORE['choices'][3]['t']
TURN_DUR = 0.55
MID_VIEWS = [16, 17, 31, 38, 40]
SWING_DUR = 0.22                          # 7.458 -> 7.708: the head comes round while the body is still down
RISE = (T_WATCH2, T_WATCH2 + 0.54)
TB0 = RISE[1]
S_DOG = 1.55
MSRC = np.array([[-1.0, 0, 383], [0, 1, 0], [0, 0, 1]])   # mirror of a 384-px-wide source frame


def smooth(a, b, t):
    t = np.clip((t - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def door_angle(t):
    # swings through square and on, back against the inside wall
    return 0.25 + (3.08 - 0.25) * smooth(6.2, 7.1, t)


def tint_map(x_screen, lit):
    amb = np.array([0.50, 0.55, 0.80], np.float32)
    d = np.clip((x_screen - Wo.X(Wo.WALL_OUT)) / Wo.S, -1, None)
    warm = lit * np.exp(-np.clip(d, 0, None) / 2.4) * 0.75
    return amb[None, :] * 0.95 * (1 - 0.3 * warm[:, None]) + warm[:, None] * np.array([1.0, 0.72, 0.42])[None, :] * 0.55


class Views:
    """placement of an archive frame on screen (source px -> screen), shared by the real frame and the puppet's fit"""
    def __init__(self, pp):
        self.pp = pp
        self.turn = np.load(os.path.join(ROOT, 'model', 'turn.npz'))
        self.lib = np.load(os.path.join(ROOT, 'model', 'library.npz'))

    def place(self, v, X):
        vf = ViewFrame.get(v, False)
        if v in (31, 38):
            sv = S_DOG * (self.pp.bbox[3] - self.pp.bbox[1]) / max(1, vf['h']) * 0.9
        else:
            sv = S_DOG * np.sqrt(self.pp.tmask.sum() / max(1, (vf['a'] > 0.5).sum())) * 0.95
        P = np.array([[sv, 0, X - vf['cx'] * sv], [0, sv, Wo.FLOOR - vf['foot'] * sv], [0, 0, 1.0]])
        return P, sv

    def G_fit(self, v, X):
        """screen-space layer transforms of the learned fit of archive frame v (15 direct; 41 via its mirrored fit)"""
        P, _ = self.place(v, X)
        if v == 41:
            A = self.lib['walk_low'][1]                 # frame 41, fitted mirrored -> un-mirror
            return np.stack([P @ MSRC @ to3(a) for a in A])
        j = list(self.turn['frames']).index(v)
        return np.stack([P @ to3(a) for a in self.turn['learned'][j]])

    def G_norm(self, key, X, H):
        """learned fit of an archive turning frame, placed by its own fitted silhouette: height H, centre X, feet on
        the boards.  key: ('t', f) turn.npz fit of frame f; ('m', f) library fit of frame f mirrored, un-mirrored"""
        kind, f = key
        if kind == 't':
            A = self.turn['learned'][list(self.turn['frames']).index(f)]; pre = np.eye(3)
        else:
            A = self.lib['walk_low'][f - 40]; pre = MSRC
        Gs = np.stack([pre @ to3(a) for a in A])
        M = self.pp.M
        q = np.einsum('nk,kni->ni', M['w'], np.einsum('kij,nj->kni', Gs[:, :2], np.concatenate([M['p'], np.ones((len(M['p']), 1))], 1)))
        h = q[:, 1].max() - q[:, 1].min(); s = H / h
        P = np.array([[s, 0, X - s * q[:, 0].mean()], [0, s, Wo.FLOOR - s * q[:, 1].max()], [0, 0, 1.0]])
        return np.einsum('ij,kjl->kil', P, Gs)

    def draw(self, v, X, can, tint_img):
        vf = ViewFrame.get(v, False)
        P, sv = self.place(v, X)
        x0, y0, x1, y1 = vf['bbox']; pad = 4
        crop = (max(0, x0 - pad), max(0, y0 - pad), min(383, x1 + pad), min(287, y1 + pad))
        g = ndimage.gaussian_filter(vf['im'], 0.4)[crop[1]:crop[3], crop[0]:crop[2]]; al = vf['a'][crop[1]:crop[3], crop[0]:crop[2]]
        w2, h2 = int(round(g.shape[1] * sv)), int(round(g.shape[0] * sv))
        g2 = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w2, h2), Image.BICUBIC), np.float32) / 255.
        a2 = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((w2, h2), Image.BICUBIC), np.float32) / 255.
        g2 = ndimage.gaussian_filter(g2, 0.6)
        px0 = int(round(P[0, 2] + crop[0] * sv)); py0 = int(round(P[1, 2] + crop[1] * sv))
        reg = can[py0:py0 + h2, px0:px0 + w2]
        tn = tint_img[py0:py0 + h2, px0:px0 + w2]
        can[py0:py0 + h2, px0:px0 + w2] = reg * (1 - a2[..., None]) + g2[..., None] * tn * a2[..., None]
        alpha = np.zeros(can.shape[:2], np.float32); alpha[py0:py0 + h2, px0:px0 + w2] = a2
        return alpha


def lerpG(A, B, u): return A * (1 - u) + B * u


def head_piece():
    """the dog's head turned toward the camera, cut from archive frame 39 (3/4 view, muzzle and eye clear), mirrored so
    the nose points left (to the door).  It is the head's visibility state for the look back, pinned at the learned
    head-neck hinge: the one place where the layers have no pose for a head turned round."""
    im, mk = ViewFrame.get(39, False)['im'], ViewFrame.get(39, False)['a']
    x0, x1, y0, y1 = 199, 242, 103, 154
    g = ndimage.gaussian_filter(im, 0.4)[y0:y1, x0:x1][:, ::-1]
    a = mk[y0:y1, x0:x1][:, ::-1].copy()
    # soften the cut on the neck side (right after mirroring... the back of the head is now on the right)
    ramp = np.clip((np.arange(x1 - x0)[::-1] - 2) / 6.0, 0, 1)[None, :]
    a = a * np.clip(ramp + 0.0, 0, 1)
    a = a * np.clip((np.arange(y1 - y0)[::-1] - 1) / 7.0, 0, 1)[:, None]      # and on the throat side
    a = ndimage.gaussian_filter(a, 0.7)
    return g, a, np.array([x1 - x0 - 6.0, 12.0])     # attach point (back of the skull) in the piece


def main():
    t0 = time.time()
    pp = Puppet(); po = Poser(pp); n = po.n
    VW = Views(pp)
    st = Wo.build_static()
    ax, ay = pp.anchor
    frames = SCORE['frames']
    meas = []
    only = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:Wo.Ht, 0:Wo.Wd].astype(np.float32)
    vign = (1 - 0.35 * (((xx - 640) / 900) ** 2 + ((yy - 380) / 600) ** 2)).clip(0.5, 1)[..., None]
    I3 = np.eye(3)
    # head carried low: from the score's head intention, raised to 0.95 on the approach, then eased over 3 frames
    hl = np.array([float(np.clip((0.9 - f['dog']['act']['head']) / 0.45, 0, 1)) for f in frames])
    hl = np.where([f['dog']['state'] == 'approach' for f in frames], np.maximum(hl, 0.95), hl)
    HEADLOW = np.convolve(np.pad(hl, (3, 0), mode='edge'), np.ones(4) / 4, 'valid')   # eased over the 3 frames after a change
    HG, HA, HATT = head_piece()
    hsel = np.isin(pp.lab, [k for k in (n['head'], n['neck']) if k >= 0])
    for fr in frames:
        i, t = fr['i'], fr['t']
        if only and i not in only: continue
        d = fr['dog']; a = d['act']; pe = fr['person']
        lit = smooth(6.2, 6.95, t)
        img = Image.fromarray(Wo.to_u8(Wo.background(st, lit)))
        Pe.stool(img)
        step = (pe['x'] + 0.28) * 9.0
        lean = 1.0 if pe['voice'] == 'call' else 0.0
        Pe.draw(img, pe['x'], pe['sit'], pe['reach'], pe['low'], lean, step if pe['sit'] < 0.9 else 0, 0.3 + 0.7 * lit)
        Wo.door_leaf(img, door_angle(t))
        can = np.asarray(img, np.float32) / 255.
        X = Wo.X(d['x'])
        state = d['state']
        # ---- acting intentions -> puppet pose
        head_low = HEADLOW[i]
        lie = a['lie']; rest = a['rest']; look = a['look']
        phase = a['walk_phase']; moving = a['moving']; crouch = a['crouch']
        if state == 'retreat' or (1.0 <= t < 2.9 and d['v'] > 0):
            phase = -phase                         # backing away: the walk run backwards
        swing = 0.0
        if RISE[0] <= t < RISE[1]:
            swing = smooth(RISE[0], RISE[0] + SWING_DUR, t)
            lie = 1 - smooth(RISE[0] + 0.1, RISE[1], t); rest = rest * (1 - smooth(RISE[0], RISE[0] + 0.3, t))
        if TB0 <= t < 14.7:
            lie = 0.0; rest = 0.0
        breathe = 0.008 * np.sin(2 * np.pi * t / 1.7) * (1 - moving)
        pp.tail_angle = (a['wag'] * 0.35 * np.sin(2 * np.pi * 2.6 * t) + 0.3 * (a['tail'] - 0.5)) * (1 - min(1, lie)) - 0.12 * min(1, lie)
        pp.label_gain = None
        pp.head_label = n['head']
        if t >= 26.9:
            look = 1.0; rest = min(rest, 0.25)      # it keeps looking in through the lit inner door
        T_pose, info = po.pose(phase=phase, moving=moving, head_low=min(1, head_low) * (1 - min(1, lie)), lie=lie,
                               rest=rest, look=look, crouch=crouch, breathe=breathe)
        def swing_head(Gin, sw):
            # the head turns round on its learned hinge with the neck, the way a flat head turns in profile: it narrows
            # toward the camera (foreshortened to 35%), passes front-on, and opens out on the other side, nose toward
            # the door; it lifts a little as it goes
            hk = n['head']; nk = int(pp.parent[hk])
            pv = pp.pivot[(hk, nk)]
            js = (Gin[hk] @ np.array([pv[0], pv[1], 1.0]))[:2]
            w = 1 - 0.65 * np.sin(np.pi * min(sw, 1.0))
            sx = w if sw < 0.5 else -w
            Sx = np.array([[sx, 0, js[0] * (1 - sx)], [0, 1, 0], [0, 0, 1.0]])
            lift = -0.2 * np.sin(np.pi * min(sw, 1.0))
            R = np.eye(3); c_, s_ = np.cos(lift * (1 if sx > 0 else -1)), np.sin(lift * (1 if sx > 0 else -1))
            R[:2, :2] = [[c_, -s_], [s_, c_]]; R[:2, 2] = js - R[:2, :2] @ js
            Gout = Gin.copy(); Gout[hk] = R @ Sx @ Gin[hk]; return Gout
        BACK_SWITCH = TB0 + 0.25 * TURN_DUR
        facingR = T_REFUSE + TURN_DUR / 2 <= t < BACK_SWITCH
        place = np.array([[(-1 if facingR else 1) * S_DOG, 0, X + (1 if facingR else -1) * S_DOG * ax],
                          [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]])
        G = np.einsum('ij,kjl->kil', place, T_pose)
        mode = 'profile-R' if facingR else 'profile-L'
        view = None; pup_o = 1.0; vid = None
        swung = swing if RISE[0] <= t < RISE[1] else None
        split = RISE[0] <= t < TB0 + 0.16 * TURN_DUR     # head drawn as its own hard layer while it is turned
        G_head = None
        # ---- the turns, rendered with the puppet only: it is posed at its learned fits of the archive frames of the
        # dog turning (turn_fit.py; these beat the best hand-set hinge pose on 13 of 16 frames), each fit placed by its
        # own silhouette at the puppet's height.  At the front-on pose (frame 30) the fit is mirrored about the dog's
        # centre line: that is where the body changes side.
        Hn = S_DOG * (pp.bbox[3] - pp.bbox[1]) * 0.9
        Fx = np.array([[-1.0, 0, 2 * X], [0, 1, 0], [0, 0, 1]])
        def knot(k):
            if isinstance(k, str) and k.startswith('flip'):
                return np.einsum('ij,kjl->kil', Fx, VW.G_norm(('t', int(k[4:])), X, Hn))
            return VW.G_norm(k, X, Hn)
        def run(knots, u, G0, G1):
            for (ua, ka), (ub, kb) in zip(knots[:-1], knots[1:]):
                if ua <= u < ub:
                    A_ = G0 if ka == 'start' else G1 if ka == 'end' else knot(ka)
                    B_ = G0 if kb == 'start' else G1 if kb == 'end' else knot(kb)
                    return lerpG(A_, B_, smooth(ua, ub, u)), (ka if smooth(ua, ub, u) < 0.5 else kb)
            return G1, 'end'
        u = (t - T_REFUSE) / TURN_DUR
        if 0 <= u < 1:
            GL = np.einsum('ij,kjl->kil', np.array([[S_DOG, 0, X - S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]]), T_pose)
            GR = np.einsum('ij,kjl->kil', np.array([[-S_DOG, 0, X + S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]]), T_pose)
            # through the 3/4 poses only (the front-on fits read as a two-humped tangle); the body changes side at the
            # most frontal 3/4 pose (17), mirrored about the dog's centre line
            AWAY = [(0, 'start'), (0.16, ('t', 15)), (0.32, ('t', 16)), (0.48, ('t', 17)), (0.4801, 'flip17'),
                    (0.66, 'flip16'), (0.84, 'flip15'), (1.0001, 'end')]
            G, kk = run(AWAY, u, GL, GR); mode = 'turn-learned'; view = kk if isinstance(kk, tuple) else None
        u = (t - TB0) / TURN_DUR
        if 0 <= u < 1:
            GL = np.einsum('ij,kjl->kil', np.array([[S_DOG, 0, X - S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]]), T_pose)
            GR = np.einsum('ij,kjl->kil', np.array([[-S_DOG, 0, X + S_DOG * ax], [0, S_DOG, Wo.FLOOR - S_DOG * ay], [0, 0, 1.0]]), T_pose)
            BACK = [(0, 'start'), (0.16, 'flip15'), (0.32, 'flip16'), (0.48, 'flip17'), (0.4801, ('t', 17)), (0.66, ('t', 16)),
                    (0.82, ('t', 15)), (1.0001, 'end')]
            G, kk = run(BACK, u, GR, GL); mode = 'turn-learned'; view = kk if isinstance(kk, tuple) else None
            G_head, _ = run(BACK, u, swing_head(GR, 1.0), GL)
        tint_img = np.broadcast_to(tint_map(np.arange(Wo.Wd, dtype=np.float32), lit)[None], (Wo.Ht, Wo.Wd, 3))
        sh_w = 0.55 * Wo.S * (1 + 0.25 * lie); sh = np.exp(-((xx - X) / sh_w) ** 2 - ((yy - Wo.FLOOR - 3) / 7.0) ** 2)
        can *= (1 - 0.55 * sh)[..., None]
        rec = dict(i=i, t=t, state_score=state, x_score=d['x'], mode=mode, view=view, override=info['override'],
                   lie=lie, rest=rest, look=look, head_low=head_low, moving=moving, walk_phase=a['walk_phase'], swing=swing)
        alpha_v = None; r = None
        hs_ = np.concatenate([hsel, np.zeros(len(pp.lab) - len(hsel), bool)])
        if vid is not None:
            cv = can.copy(); alpha_v = VW.draw(vid, X, cv, tint_img)
        if pup_o > 0:
            cp = can.copy()
            if split:
                # the head proper (head layer above its hinge with the neck); the throat part of the layer stays
                hpv = pp.pivot[(n['head'], int(pp.parent[n['head']]))]
                hsH = (pp.lab == n['head']) & (pp.P[:, 1] < hpv[1] + 4)
                if swung is not None:
                    G_head = swing_head(G, swung)
                    if mode.startswith('profile'): mode = 'head-swing'; rec['mode'] = mode
                    info['override'] = 1.0; rec['override'] = 1.0
                saved = pp.front; pp.front = []; pp.rim = False
                if G_head is None: G_head = G
                hk_ = n['head']; pvh = pp.pivot[(hk_, int(pp.parent[hk_]))]
                js_ = (G[hk_] @ np.array([pvh[0], pvh[1], 1.0]))[:2]
                piece = (swung is not None and swung >= 0.5) or (swung is None and (t - TB0) < 0.16 * TURN_DUR)
                r0 = pp.render(G, I3, cp, tint=tint_img, sel=~(pp.lab == n['head']) if piece else ~hsH)
                pp.rim = True
                if piece:
                    # the turned-round head: archive head piece, at the hinge, nose to the door
                    sc_ = 1.25
                    hh, ww = HG.shape
                    g2 = np.asarray(Image.fromarray((HG * 255).astype(np.uint8)).resize((int(ww * sc_), int(hh * sc_)), Image.BICUBIC), np.float32) / 255.
                    a2 = np.asarray(Image.fromarray((HA * 255).astype(np.uint8)).resize((int(ww * sc_), int(hh * sc_)), Image.BICUBIC), np.float32) / 255.
                    px0 = int(round(js_[0] - HATT[0] * sc_ + 4)); py0 = int(round(js_[1] - HATT[1] * sc_ - 14))
                    h2_, w2_ = g2.shape
                    reg = cp[py0:py0 + h2_, px0:px0 + w2_]
                    tn = tint_img[py0:py0 + h2_, px0:px0 + w2_]
                    m_ = g2.mean(); g2 = np.clip(m_ + (g2 - m_) * 1.3, 0, 1)
                    cp[py0:py0 + h2_, px0:px0 + w2_] = reg * (1 - a2[..., None]) + g2[..., None] * tn * 1.1 * a2[..., None]
                    al1 = np.zeros(cp.shape[:2], np.float32); al1[py0:py0 + h2_, px0:px0 + w2_] = a2
                    r1 = dict(alpha=al1, q=r0['q'])
                    rec['head_piece'] = [px0, py0, w2_, h2_]
                else:
                    r1 = pp.render(G_head, I3, cp, tint=tint_img, sel=hsH, hard=True)
                pp.front = saved; pp.rim = True
                r = dict(alpha=np.maximum(r0['alpha'], r1['alpha']), q=np.where(hsH[:, None], r1['q'], r0['q']))
            else:
                r = pp.render(G, I3, cp, tint=tint_img)
            joints = pp.joint_screen(G, I3)
            dr = Image.fromarray((np.clip(cp, 0, 1) * 255).astype(np.uint8)); dd = ImageDraw.Draw(dr, 'RGBA')
            for k, (jx, jy) in joints.items():
                ov = abs(info['angles'].get(k, 0)) > 0.05 or (mode == 'head-swing' and k in (n['head'], n['neck']))
                c = (150, 185, 235, int(150 * pup_o)) if ov else (225, 185, 110, int(150 * pup_o))
                dd.ellipse([jx - 1.7, jy - 1.7, jx + 1.7, jy + 1.7], fill=c)
            cp = np.asarray(dr, np.float32) / 255.
        if vid is not None and pup_o > 0:
            can = cv * (1 - pup_o) + cp * pup_o
            alpha = r['alpha'] if pup_o >= 0.5 else alpha_v
        elif vid is not None:
            can = cv; alpha = alpha_v
        else:
            can = cp; alpha = r['alpha']
        if r is not None and pup_o >= 0.5:
            q = r['q']
            hk = hsH if split else (pp.lab == n['head'])
            rec['head_xy'] = q[hk].mean(0).tolist(); rec['head_top_y'] = float(q[hk][:, 1].min())
            bk = np.isin(pp.lab, [k for nm, k in n.items() if nm in ('trunk',) or nm.startswith('back')])
            rec['back_top_y'] = float(np.percentile(q[bk][:, 1], 3))
            nk = n['neck'] if n['neck'] >= 0 else n['head']
            pv = pp.pivot[(nk, int(pp.parent[nk]))]
            rec['neck_hinge_xy'] = (G[nk] @ np.array([pv[0], pv[1], 1.0]))[:2].tolist()
            hk_ = n['head']; pvh = pp.pivot[(hk_, int(pp.parent[hk_]))]
            rec['head_hinge_xy'] = (G[hk_] @ np.array([pvh[0], pvh[1], 1.0]))[:2].tolist()
            nose = KEYS[str(int(pp.M['template_frame']))]['nose']
            Gh = G_head if (split and G_head is not None) else G
            rec['nose_xy'] = (Gh[hk_] @ np.array([nose[0], nose[1], 1.0]))[:2].tolist()
            for nm in ('foreleg', 'hind'):
                kk = pp.lab == n[nm]
                lo = q[kk][np.argsort(q[kk][:, 1])[-40:]].mean(0); rec[nm + '_foot'] = lo.tolist()
            tq = q[pp.lab == pp.K][:, 0]
            rec['tail_x_range'] = [float(tq.min()), float(tq.max())]
        elif vid is not None:
            kp = KEYS.get(str(vid))
            if kp:
                ys_, xs_ = np.nonzero(ViewFrame.get(vid, False)['a'] > 0.5)
                rec['nose_rel'] = float(kp['nose'][0] - xs_.mean())
        m = alpha > 0.5
        ys, xs = np.nonzero(m)
        rec['x_screen'] = float(xs.mean()); rec['y_screen'] = float(ys.mean())
        rec['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        rec['area'] = int(m.sum())
        can = can * vign + rng.normal(0, 0.018, (Wo.Ht, Wo.Wd, 1)).astype(np.float32)
        Image.fromarray((np.clip(can, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 's_%04d.jpg' % i), quality=92)
        meas.append(rec)
        if i % 48 == 0: print(i, round(time.time() - t0, 1), mode, flush=True)
    if not only:
        json.dump(meas, open(os.path.join(ROOT, 'data', 'measure.json'), 'w'))
    else:
        json.dump(meas, open(os.path.join(HERE, 'cache', 'measure_partial.json'), 'w'))
        mp = os.path.join(ROOT, 'data', 'measure.json')
        if os.path.exists(mp) and os.environ.get('MERGE'):
            full = {r['i']: r for r in json.load(open(mp))}
            for r in meas: full[r['i']] = r
            json.dump([full[k] for k in sorted(full)], open(mp, 'w'))
    print('scene done', len(meas), round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
