"""Render the 32 s comp: set (corner-pinned plates) -> person -> dog (parented part layers, holdouts, matched light)
-> final grade + grain. Frames are piped to ffmpeg; per-frame matte measurements go to cache/measure.json.
usage: python3 render.py [--test i,i,...  outdir]  |  python3 render.py --film out.mp4 (title+scene+end, video only)"""
import sys, os, json, subprocess, time
import numpy as np
from PIL import Image, ImageFilter
from comp import W, H, warp, Comp, noise_level
import camera as cam
import setplates as SP
import rig
import cards

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
GRAIN_T = 0.016      # target grain (luma std of the high-pass) every layer is matched to before the common grade
rng = np.random.default_rng(7)
XS0 = float(cam.project(cam.path_point(0.0))[0][0, 0])      # screen x where the dog's path crosses the facade plane


class Renderer:
    def __init__(self):
        self.set = SP.Set()
        self.dog = rig.Dog()
        self.person = rig.Person(SP.plate)
        self.noise_cache = {}
        xs = np.arange(W, dtype=np.float32)
        self.inside_ramp = np.broadcast_to(np.clip((XS0 + 3 - xs) / 6, 0, 1)[None, :], (H, W))
        self.vign = self._vignette()
        self.grain_log = {}

    def _vignette(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((xx - W * .42) / (W * .75), (yy - H * .5) / (H * .85))
        return np.clip(1.08 - 0.55 * r ** 2, 0.45, 1.0)[..., None]

    def grain_match(self, name, piece):
        """add grain so this layer's measured high-pass noise reaches GRAIN_T (measured once per layer name)."""
        x0, y0, c, a = piece
        if name not in self.noise_cache:
            w = a > .9
            from PIL import ImageFilter as _F
            core = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(_F.MinFilter(5))) > 0
            n = noise_level(c / np.maximum(a, 1e-3)[..., None], core) if core.sum() > 400 else 0.0
            add = float(np.sqrt(max(0.0, GRAIN_T ** 2 - n ** 2)))
            self.noise_cache[name] = add
            self.grain_log[name] = dict(measured=round(n, 5), added=round(add, 5))
        add = self.noise_cache[name]
        if add > 0:
            g = rng.normal(0, add, a.shape).astype(np.float32)
            c = c + g[..., None] * a[..., None]
        return (x0, y0, c, a)

    def frame(self, i):
        t = i / 24.0
        S = self.set
        fl, cd = S.light_maps(t)
        lamp = SP.lamp_level(t)
        amb = np.array(SP.DUSK, np.float32) * 0.95
        cdc = cd / (1 + 0.6 * cd)                      # soft shoulder so the lit dog keeps its texture
        light3 = amb[None, None] + 1.5 * cdc[..., None] * SP.WARM[None, None]
        c = S.back(t)
        fac = c.mattes  # empty here
        # facade etc. drawn now; person standing inside must be held out by the facade, so draw person first when inside
        plist, pinfo = self.person.frame(i)
        inside_person = [L for L in plist if L[4] == 'silhouette' and pinfo['person'] == 'standing' and t < 5.0]
        for nm, rgb, al, M, kind in inside_person:
            pc = warp(rgb * 0.07 + np.array([.02, .015, .01], np.float32), al, M)
            c.over(pc, name='person')
        S.front(c, t, fl)
        hold_wall = np.maximum(c.mattes.get('facade', 0), c.mattes.get('sill', 0))
        for L in plist:
            if L in inside_person: continue
            nm, rgb, al, M, kind = L
            if kind == 'silhouette':
                col = rgb * 0.07
                light = None
            elif kind == 'hand':
                g = rgb @ np.array([.3, .59, .11], np.float32)
                col = (g[..., None] * .5 + rgb * .5) * 0.6; light = light3
            else:
                g = rgb @ np.array([.3, .59, .11], np.float32)
                col = np.repeat(g[..., None], 3, 2) * 0.30; light = light3
            pc = warp(col, al, M)
            if pc is None: continue
            pc = self.grain_match(nm, pc)
            c.over(pc, light=light, name='person')
        # the dog
        dl, dinfo = self.dog.frame(i)
        hold = hold_wall * self.inside_ramp
        full = np.zeros((H, W), np.float32)
        for nm, rgb, al, M in dl:
            pc = warp(rgb, al, M)
            if pc is None: continue
            x0, y0, cc, aa = pc
            sub = full[y0:y0 + aa.shape[0], x0:x0 + aa.shape[1]]; np.maximum(sub, aa, out=sub)
            pc = self.grain_match('dog', pc)
            # the back of the head faces away from the lamp: it is lit from behind (rim), darker toward us
            lt = light3 * np.array([.55, .55, .6], np.float32) if nm == 'dog:head-look' else light3
            c.over(pc, holdout=hold, light=lt, name='dog')
        # contact shadow under the dog (ambient occlusion from the dog's own full matte, squashed onto the floor)
        img = c.rgb
        # final: bloom from the lit doorway, vignette, common grain, gentle toe
        y = img @ np.array([.3, .59, .11], np.float32)
        bright = np.clip(y - .55, 0, None)
        if bright.max() > 0:
            b = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
            b = b.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
            img = img + (np.asarray(b, np.float32) / 255)[..., None] * SP.WARM * 0.5 * lamp
        img = img * self.vign
        img = img + rng.normal(0, 0.008, (H, W, 1)).astype(np.float32)
        img = np.clip(img, 0, 1) ** 0.95
        meas = self.measure(i, c.mattes.get('dog'), full, dinfo, pinfo)
        return (img * 255 + .5).astype(np.uint8), meas

    def measure(self, i, vis, full, dinfo, pinfo):
        m = dict(i=i, t=round(i / 24, 4), **{k: v for k, v in dinfo.items()})
        if vis is None or vis.sum() < 10:
            m['visible_px'] = 0; return m
        ys, xs = np.nonzero(vis > .5)
        m.update(visible_px=int(len(xs)), x_screen=round(float(xs.mean()), 1), y_screen=round(float(ys.mean()), 1),
                 left=int(xs.min()), right=int(xs.max()), top=int(ys.min()), bottom=int(ys.max()),
                 height_px=int(ys.max() - ys.min()))
        fy, fx = np.nonzero(full > .5)
        m['frac_inside_threshold'] = round(float((fx < XS0).mean()), 3)
        m['held_out_px'] = int((full > .5).sum() - (vis > .5).sum())
        m['person'] = pinfo['person']
        return m


def main():
    args = sys.argv[1:]
    R = Renderer()
    if args and args[0] == '--test':
        idx = [int(v) for v in args[1].split(',')]; out = args[2]
        os.makedirs(out, exist_ok=True)
        for i in idx:
            t0 = time.time(); im, m = R.frame(i)
            Image.fromarray(im).save(os.path.join(out, 'r%04d.jpg' % i), quality=90)
            print(i, round(time.time() - t0, 2), json.dumps(m))
        return
    if args and args[0] == '--film':
        out = args[1]
        ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                               '-r', '24', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                               '-tune', 'grain', out], stdin=subprocess.PIPE)
        n = 0
        for im in cards.title_frames():
            ff.stdin.write(im.tobytes()); n += 1
        meas = []
        stills = {86: '03.6', 216: '09.0', 456: '19.0', 672: '28.0'}
        os.makedirs(os.path.join(CACHE, 'stills'), exist_ok=True)
        t0 = time.time()
        for i in range(768):
            im, m = R.frame(i)
            ff.stdin.write(im.tobytes()); n += 1; meas.append(m)
            if i % 48 == 0: print('frame', i, round(time.time() - t0, 1), flush=True)
        for im in cards.end_frames():
            ff.stdin.write(im.tobytes()); n += 1
        ff.stdin.close(); ff.wait()
        json.dump(dict(frames_written=n, scene_frames=len(meas), xs0=XS0, grain=R.grain_log, frames=meas),
                  open(os.path.join(CACHE, 'measure.json'), 'w'))
        print('written', n)


if __name__ == '__main__':
    main()
