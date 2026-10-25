// The place: dusk, a porch, a façade with a doorway, a lit room. All geometry is world data projected by the one camera.
import React from 'react';
import {random} from 'remotion';
import type {V3} from '../lib/math.ts';
import {lerp, clamp} from '../lib/math.ts';
import {project, p2, pathOf, W, H, CAM, farShift} from '../lib/camera.ts';
import {WORLD} from '../lib/world.ts';
import {spillPoly} from '../lib/light.ts';
import {mixc} from './draw.tsx';

const Z0 = -2.7, Z1 = 1.9;               // façade extent across the porch
const D = WORLD.door, X1 = WORLD.wallOut, X0 = WORLD.wallIn;
const rect = (x: number, za: number, zb: number, ya: number, yb: number): V3[] => [[x, ya, za], [x, ya, zb], [x, yb, zb], [x, yb, za]];
export const openingOuter = pathOf(rect(X1, D.z0, D.z1, 0, D.h));
export const openingInner = pathOf(rect(X0, D.z0, D.z1, 0, D.h));
export const spillPath = (angle: number) => pathOf(spillPoly(angle));

export const Defs: React.FC<{angle: number}> = ({angle}) => (
  <defs>
    <clipPath id="openIn"><path d={openingInner}/></clipPath>
    <clipPath id="opening" clipPath="url(#openIn)"><path d={openingOuter}/></clipPath>
    <clipPath id="openOut"><path d={openingOuter}/></clipPath>
    <clipPath id="spillClip"><path d={spillPath(angle)}/></clipPath>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
    <radialGradient id="glowG"><stop offset="0" stopColor="#fff2c8" stopOpacity="1"/><stop offset="0.45" stopColor="#ffe2a0" stopOpacity="0.45"/><stop offset="1" stopColor="#ffd890" stopOpacity="0"/></radialGradient>
  </defs>
);

const horizonY = () => {
  const far: V3 = [CAM.pos[0] - 400, CAM.pos[1], CAM.pos[2] - 760];
  return p2(far)[1];
};
const FarG: React.FC<{children: React.ReactNode}> = ({children}) => { const [dx, dy] = farShift(); return <g transform={`translate(${dx.toFixed(1)},${dy.toFixed(1)})`}>{children}</g>; };

export const Sky: React.FC<{t: number}> = ({t}) => {
  const k = clamp(t / 32);
  const top = mixc('#27305a', '#131733', k), mid = mixc('#5a4f78', '#2b2c52', k), low = mixc('#d08a68', '#8c5a5e', k);
  const hy = horizonY(), hyF = hy - farShift()[1];
  const stars = Array.from({length: 60}, (_, i) => ({x: random('star-x-' + i) * W * 1.3 - W * 0.15, y: random('star-y-' + i) * hyF * 0.85,
    r: 0.6 + random('star-r-' + i) * 1.1, on: random('star-on-' + i) * 26 + 3}));
  return (
    <g>
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2={hy} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor={top}/><stop offset="0.62" stopColor={mid}/><stop offset="1" stopColor={low}/>
        </linearGradient>
      </defs>
      <rect width={W} height={H} fill="url(#sky)"/>
      <FarG>{stars.map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#f4f0e0" opacity={clamp((t - s.on) / 4) * 0.8}/>)}
      {/* a low moon over the yard */}
      <circle cx={1120} cy={hyF - 175} r={17} fill="#efe6cf" opacity={0.85}/>
      <circle cx={1127} cy={hyF - 179} r={16} fill={mid} opacity={0.92}/></FarG>
    </g>
  );
};

export const Yard: React.FC<{t: number}> = ({t}) => {
  const hy = horizonY(), hyF = hy - farShift()[1];
  // tree line: seeded silhouettes on the horizon (Remotion's deterministic random)
  const crowns = Array.from({length: 60}, (_, k) => ({x: k * 29 - 300 + random('tx-' + k) * 20, r: 18 + random('tr-' + k) * 26,
    h: 18 + random('th-' + k) * 40 + 30 * Math.pow(Math.abs(Math.sin(k * 0.37 + 1.1)), 2)}));
  const ground = mixc('#262a2c', '#15181c', clamp(t / 32));
  return (
    <g>
      <FarG><g fill={mixc('#1b1e2a', '#0f101a', clamp(t / 32))}>
        {crowns.map((c, k) => <g key={k}><circle cx={c.x} cy={hyF - c.h} r={c.r}/><circle cx={c.x + c.r * 0.6} cy={hyF - c.h * 0.7} r={c.r * 0.8}/>
          <rect x={c.x - c.r} y={hyF - c.h} width={c.r * 2.2} height={c.h + 2}/></g>)}
      </g></FarG>
      <rect x={0} y={hy} width={W} height={H - hy} fill={ground}/>
    </g>
  );
};

export const Room: React.FC<{lamp: number; angle: number}> = ({lamp, angle}) => {
  const R = WORLD.room; const L = WORLD.lamp;
  const wall = mixc('#5e4330', '#e0ad6c', lamp), side = mixc('#4e3828', '#c99256', lamp), floor = mixc('#3a271b', '#8a5a36', lamp);
  const ceil = mixc('#3d2c22', '#a3784c', lamp);
  const a = angle * Math.PI / 180;
  const hx = X0, hz = WORLD.hingeZ, ex = hx - 0.96 * Math.sin(a), ez = hz - 0.96 * Math.cos(a);
  const leaf: V3[] = [[hx, 0.01, hz], [ex, 0.01, ez], [ex, 2.03, ez], [hx, 2.03, hz]];
  const inset = (u0: number, u1: number, v0: number, v1: number): V3[] => [u0, u1].flatMap(u => [v0, v1].map(v => [lerp(hx, ex, u), v, lerp(hz, ez, u)] as V3));
  const panel = (u0: number, u1: number, v0: number, v1: number) => { const q = inset(u0, u1, v0, v1); return pathOf([q[0], q[2], q[3], q[1]]); };
  const lampP = p2(L);
  return (
    <g clipPath="url(#opening)">
      <path d={pathOf([[R.x0, R.h, R.z0], [R.x0, R.h, R.z1], [X0, R.h, R.z1], [X0, R.h, R.z0]])} fill={ceil}/>
      <path d={pathOf([[R.x0, 0, R.z0], [R.x0, 0, R.z1], [R.x0, R.h, R.z1], [R.x0, R.h, R.z0]])} fill={wall}/>
      <path d={pathOf([[R.x0, 0, R.z0], [X0, 0, R.z0], [X0, R.h, R.z0], [R.x0, R.h, R.z0]])} fill={side}/>
      <path d={pathOf([[R.x0, 0, R.z0], [R.x0, 0, R.z1], [X0, 0, R.z1], [X0, 0, R.z0]])} fill={floor}/>
      {/* floorboards, a rug, a picture, a chair, a small lamp: the room the dog is invited into */}
      {Array.from({length: 14}, (_, k) => { const z = R.z0 + 0.27 * k; const a = p2([R.x0, 0.002, z]), b = p2([X0, 0.002, z]);
        return <line key={'fb' + k} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={mixc('#24170f', '#6a4228', lamp)} strokeWidth={1.2}/>; })}
      <path d={pathOf([[-2.6, 0.004, -1.2], [-2.6, 0.004, 0.6], [-0.45, 0.004, 0.6], [-0.45, 0.004, -1.2]])} fill={mixc('#3b2a2a', '#9b4a3a', lamp)}/>
      <path d={pathOf([[-2.45, 0.006, -1.05], [-2.45, 0.006, 0.45], [-0.6, 0.006, 0.45], [-0.6, 0.006, -1.05]])} fill="none" stroke={mixc('#2a1a1a', '#c9824e', lamp)} strokeWidth={2}/>
      <circle cx={p2([-1.25, 1.2, R.z0])[0]} cy={p2([-1.25, 1.2, R.z0])[1]} r={170} fill="url(#glowG)" opacity={0.35 * lamp}/>
      <path d={pathOf([[-1.65, 1.3, R.z0 + 0.01], [-1.1, 1.3, R.z0 + 0.01], [-1.1, 1.78, R.z0 + 0.01], [-1.65, 1.78, R.z0 + 0.01]])} fill={mixc('#2a2a2a', '#5b6a62', lamp)} stroke={mixc('#20160f', '#5a3a22', lamp)} strokeWidth={4}/>
      <path d={pathOf([[-1.55, 1.38, R.z0 + 0.012], [-1.2, 1.38, R.z0 + 0.012], [-1.3, 1.6, R.z0 + 0.012]])} fill={mixc('#222', '#8a9a7a', lamp)}/>
      {/* side table and small lamp */}
      {[[-1.0, -1.82], [-0.7, -1.82], [-1.0, -1.55], [-0.7, -1.55]].map(([x, z], k) =>
        <line key={'tl' + k} x1={p2([x, 0, z])[0]} y1={p2([x, 0, z])[1]} x2={p2([x, 0.62, z])[0]} y2={p2([x, 0.62, z])[1]} stroke={mixc('#20140d', '#4a2e1c', lamp)} strokeWidth={4}/>)}
      <path d={pathOf([[-1.05, 0.62, -1.86], [-0.65, 0.62, -1.86], [-0.65, 0.62, -1.5], [-1.05, 0.62, -1.5]])} fill={mixc('#24170f', '#6a4428', lamp)}/>
      <line x1={p2([-0.85, 0.62, -1.68])[0]} y1={p2([-0.85, 0.62, -1.68])[1]} x2={p2([-0.85, 0.9, -1.68])[0]} y2={p2([-0.85, 0.9, -1.68])[1]} stroke="#2a1d14" strokeWidth={3}/>
      <path d={pathOf([[-0.97, 0.88, -1.68], [-0.73, 0.88, -1.68], [-0.79, 1.06, -1.68], [-0.91, 1.06, -1.68]])} fill={mixc('#8a7050', '#ffe2a8', lamp)}/>
      <circle cx={p2([-0.85, 0.95, -1.68])[0]} cy={p2([-0.85, 0.95, -1.68])[1]} r={50} fill="url(#glowG)" opacity={0.6 * lamp}/>
      {/* a chair against the far wall */}
      {[[-1.85, -1.8], [-1.4, -1.8], [-1.85, -1.35], [-1.4, -1.35]].map(([x, z], k) =>
        <line key={'cl' + k} x1={p2([x, 0, z])[0]} y1={p2([x, 0, z])[1]} x2={p2([x, 0.45, z])[0]} y2={p2([x, 0.45, z])[1]} stroke={mixc('#20140d', '#4a2e1c', lamp)} strokeWidth={4}/>)}
      <path d={pathOf([[-1.9, 0.45, -1.85], [-1.35, 0.45, -1.85], [-1.35, 0.45, -1.3], [-1.9, 0.45, -1.3]])} fill={mixc('#24170f', '#5a3822', lamp)}/>
      <path d={pathOf([[-1.9, 0.45, -1.85], [-1.35, 0.45, -1.85], [-1.35, 1.0, -1.85], [-1.9, 1.0, -1.85]])} fill={mixc('#20140d', '#4e301d', lamp)}/>
      {/* the lamp: cord and bulb with a glow */}
      <line x1={lampP[0]} y1={p2([L[0], R.h, L[2]])[1]} x2={lampP[0]} y2={lampP[1]} stroke="#2a1d14" strokeWidth={2}/>
      <circle cx={lampP[0]} cy={lampP[1]} r={70} fill="url(#glowG)" opacity={0.4 * lamp}/>
      <circle cx={lampP[0]} cy={lampP[1] + 4} r={9} fill={mixc('#a88a5a', '#fff6dc', lamp)}/>
      <path d={`M${lampP[0] - 16},${lampP[1]}L${lampP[0] + 16},${lampP[1]}L${lampP[0] + 9},${lampP[1] - 12}L${lampP[0] - 9},${lampP[1] - 12}Z`} fill="#3a2a1e"/>
      {/* the door leaf, hung on the far jamb, swinging into the room */}
      <path d={pathOf(leaf)} fill={mixc('#1f2c27', '#3d5a4c', lamp * 0.8)} stroke="#121a17" strokeWidth={2}/>
      <path d={panel(0.15, 0.85, 1.15, 1.85)} fill="none" stroke="#16201c" strokeWidth={2.5}/>
      <path d={panel(0.15, 0.85, 0.2, 0.95)} fill="none" stroke="#16201c" strokeWidth={2.5}/>
    </g>
  );
};

export const Facade: React.FC<{t: number; lamp: number}> = ({t, lamp}) => {
  const dusk = clamp(t / 32);
  const wall = mixc('#5c6272', '#3a3f52', dusk), trim = mixc('#b9b3a4', '#7d7c80', dusk);
  const outer = pathOf(rect(X1, Z0, Z1, 0, 2.95));
  const boards: React.ReactNode[] = [];
  for (let y = 0.18; y < 2.95; y += 0.18) {
    const a = p2([X1, y, Z0]), b = p2([X1, y, Z1]);
    boards.push(<line key={y} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={mixc(wall, '#000000', 0.28)} strokeWidth={1.4}/>);
  }
  const win = rect(X1 + 0.005, 0.85, 1.55, 0.95, 1.95);
  const roof: V3[] = [[X1 + 0.3, 2.95, Z0 - 0.15], [X1 + 0.3, 2.95, Z1 + 0.2], [-1.8, 4.6, Z1 + 0.2], [-1.8, 4.6, Z0 - 0.15]];
  const tr = 0.09;
  return (
    <g>
      <path d={pathOf(roof)} fill={mixc('#2b2d38', '#191a24', dusk)}/>
      <path d={pathOf([[X1 + 0.3, 2.95, Z0 - 0.15], [X1 + 0.3, 2.95, Z1 + 0.2], [X1 + 0.3, 2.82, Z1 + 0.2], [X1 + 0.3, 2.82, Z0 - 0.15]])} fill={mixc('#40404a', '#25252f', dusk)}/>
      <path d={outer + openingOuter} fill={wall} fillRule="evenodd"/>
      <g clipPath="url(#wallClip)">{boards}</g>
      <defs><clipPath id="wallClip"><path d={outer + openingOuter} clipRule="evenodd"/></clipPath></defs>
      {/* window: the room's light, faintly, through glass */}
      <path d={pathOf(win)} fill={mixc('#3a3030', '#c48a4c', lamp * 0.8)} stroke={trim} strokeWidth={5}/>
      <line x1={p2([X1, 1.45, 0.85])[0]} y1={p2([X1, 1.45, 0.85])[1]} x2={p2([X1, 1.45, 1.55])[0]} y2={p2([X1, 1.45, 1.55])[1]} stroke={trim} strokeWidth={3}/>
      <line x1={p2([X1, 0.95, 1.2])[0]} y1={p2([X1, 0.95, 1.2])[1]} x2={p2([X1, 1.95, 1.2])[0]} y2={p2([X1, 1.95, 1.2])[1]} stroke={trim} strokeWidth={3}/>
      {/* door trim */}
      <path d={pathOf(rect(X1 + 0.01, D.z0 - tr, D.z0, 0, D.h + tr)) + pathOf(rect(X1 + 0.01, D.z1, D.z1 + tr, 0, D.h + tr)) + pathOf(rect(X1 + 0.01, D.z0 - tr, D.z1 + tr, D.h, D.h + tr))} fill={trim}/>
    </g>
  );
};

/** the inside faces of the frame you see through the opening: far jamb, lintel underside */
export const Frame: React.FC<{lamp: number}> = ({lamp}) => {
  const c = mixc('#5a5660', '#c99a64', lamp);
  return (
    <g clipPath="url(#openOut)">
      <path d={pathOf([[X0, 0, D.z0], [X1, 0, D.z0], [X1, D.h, D.z0], [X0, D.h, D.z0]])} fill={c}/>
      <path d={pathOf([[X0, D.h, D.z0], [X1, D.h, D.z0], [X1, D.h, D.z1], [X0, D.h, D.z1]])} fill={mixc(c, '#000000', 0.35)}/>
    </g>
  );
};

export const Porch: React.FC<{t: number; lamp: number; angle: number}> = ({t, lamp, angle}) => {
  const dusk = clamp(t / 32), P = WORLD.porch;
  const wood = mixc('#5b4c43', '#3b3433', dusk), seam = mixc(wood, '#000000', 0.45);
  const floor: V3[] = [[X1, 0, P.z0], [P.x1, 0, P.z0], [P.x1, 0, P.z1], [X1, 0, P.z1]];
  const seams: React.ReactNode[] = [];
  for (let z = P.z0 + 0.13; z < P.z1; z += 0.13) {
    const a = p2([X1, 0, z]), b = p2([P.x1, 0, z]);
    seams.push(<line key={z} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={seam} strokeWidth={1.1}/>);
  }
  // board ends, staggered (deterministic)
  for (let k = 0; k < 35; k++) {
    const z = P.z0 + 0.13 * k, x = 0.9 + random('end-' + k) * 3.6;
    const a = p2([x, 0, z]), b = p2([x, 0, z + 0.13]);
    seams.push(<line key={'e' + k} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={seam} strokeWidth={1}/>);
  }
  const fascia: V3[] = [[X1, 0, P.z1], [P.x1, 0, P.z1], [P.x1, -0.5, P.z1], [X1, -0.5, P.z1]];
  const endFace: V3[] = [[P.x1, 0, P.z0], [P.x1, 0, P.z1], [P.x1, -0.5, P.z1], [P.x1, -0.5, P.z0]];
  const steps: React.ReactNode[] = [];
  for (let s = 1; s <= 2; s++) {
    const y = -0.5 * s / 3, x0 = P.x1 + 0.3 * (s - 1), x1 = P.x1 + 0.3 * s;
    steps.push(<path key={'t' + s} d={pathOf([[x0, y, -0.9], [x1, y, -0.9], [x1, y, 0.7], [x0, y, 0.7]])} fill={mixc(wood, '#000000', 0.15 * s)}/>);
    steps.push(<path key={'r' + s} d={pathOf([[x1, y, -0.9], [x1, y, 0.7], [x1, y - 0.167, 0.7], [x1, y - 0.167, -0.9]])} fill={mixc(wood, '#000000', 0.35 + 0.1 * s)}/>);
  }
  const sp = spillPoly(angle);
  const g0 = p2([X1, 0, 0]), g1 = p2([P.x1, 0, -0.6]);
  const S = WORLD.sill;
  const sillTop: V3[] = [[S.x0, S.h, D.z0], [S.x1, S.h, D.z0], [S.x1, S.h, D.z1], [S.x0, S.h, D.z1]];
  const sillFront: V3[] = [[S.x1, S.h, D.z0], [S.x1, S.h, D.z1], [S.x1, 0, D.z1], [S.x1, 0, D.z0]];
  return (
    <g>
      <defs>
        <linearGradient id="spillGrad" x1={g0[0]} y1={g0[1]} x2={g1[0]} y2={g1[1]} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#ffd08a" stopOpacity={0.75 * lamp}/><stop offset="0.55" stopColor="#f0a860" stopOpacity={0.38 * lamp}/>
          <stop offset="1" stopColor="#e0904c" stopOpacity={0.16 * lamp}/>
        </linearGradient>
      </defs>
      <path d={pathOf(floor)} fill={wood}/>
      {seams}
      <path d={pathOf(sp)} fill="url(#spillGrad)" filter="url(#soft)"/>
      <path d={pathOf(fascia)} fill={mixc(wood, '#000000', 0.4)}/>
      <path d={pathOf(endFace)} fill={mixc(wood, '#000000', 0.3)}/>
      {steps}
      <path d={pathOf(sillTop)} fill={mixc(mixc('#7d776e', '#4e4a48', dusk), '#ffd08a', 0.45 * lamp)}/>
      <path d={pathOf(sillFront)} fill={mixc('#4d4844', '#2e2b2c', dusk)}/>
    </g>
  );
};

export const Railing: React.FC<{t: number; lamp: number}> = ({t}) => {
  const dusk = clamp(t / 32), c = mixc('#6b625c', '#3e3a3c', dusk), z = WORLD.porch.z0 + 0.05;
  const posts = [0.55, 1.75, 2.95, 4.15, 4.85];
  const ln = (a: V3, b: V3, w: number, k: string, col = c) => { const p = p2(a), q = p2(b); return <line key={k} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={col} strokeWidth={w} strokeLinecap="round"/>; };
  const els: React.ReactNode[] = [];
  for (let x = 0.7; x < 4.85; x += 0.22) els.push(ln([x, 0.1, z], [x, 0.88, z], 2.4, 'b' + x, mixc(c, '#000000', 0.2)));
  els.push(ln([0.55, 0.9, z], [4.85, 0.9, z], 6, 'top'), ln([0.55, 0.12, z], [4.85, 0.12, z], 4, 'bot'));
  posts.forEach((x, k) => els.push(ln([x, 0, z], [x, 1.0, z], 8, 'p' + k)));
  return <g>{els}</g>;
};
