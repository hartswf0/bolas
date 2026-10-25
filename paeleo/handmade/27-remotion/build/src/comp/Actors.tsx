// <Dog> and <Person>: frame-pure components. Input = one manifest frame; output = SVG. No state, no effects, no clock.
import React from 'react';
import type {V3} from '../lib/math.ts';
import {add, sub, mul, clamp} from '../lib/math.ts';
import {project, p2} from '../lib/camera.ts';
import {WORLD} from '../lib/world.ts';
import {spillAt, shadowOf} from '../lib/light.ts';
import {dogParts} from '../lib/dogRig.ts';
import type {DogPose, Part, Tone, Matte} from '../lib/dogRig.ts';
import {personParts} from '../lib/personRig.ts';
import type {PersonPose, PTone} from '../lib/personRig.ts';
import {cap2, capPath, mixc} from './draw.tsx';

export const DOG_TONE: Record<Tone, string> = {coat: '#3a2c24', saddle: '#1c1512', tan: '#8c6844', dark: '#120e0c', nose: '#070606', eye: '#0a0807', ear: '#2a201b'};
export const MATTE: Record<Matte, string> = {body: '#00ff00', skull: '#0000ff', muzzle: '#ff0000'};
const PERSON_TONE: Record<PTone, string> = {cloth: '#3b4150', cloth2: '#272a33', skin: '#b98c6c', hair: '#2a1f1a', shoe: '#141414'};
const WARM = '#ffc778';

type Piece = {d: string; depth: number; inside: boolean; color: string; matte: string; mid: V3};

/** split a 3-D capsule where it crosses the façade plane, so the part behind the wall is seen only through the opening */
function splitCap(a: V3, ra: number, b: V3, rb: number): [V3, number, V3, number, boolean][] {
  const X = WORLD.wallOut;
  const ia = a[0] < X, ib = b[0] < X;
  if (ia === ib) return [[a, ra, b, rb, ia]];
  const u = (X - a[0]) / (b[0] - a[0]); const m = add(a, mul(sub(b, a), u)); const rm = ra + (rb - ra) * u;
  return [[a, ra, m, rm, ia], [m, rm, b, rb, ib]];
}

function pieces(parts: (Part | {kind: 'cap'; a: V3; ra: number; b: V3; rb: number; tone: string; matte?: string; bias?: number})[],
  tone: (p: any) => string, grow: number, angle: number, lamp: number, lightGain: number): Piece[] {
  const out: Piece[] = [];
  for (const p of parts) {
    if (p.kind === 'cap') {
      for (const [a, ra, b, rb, inside] of splitCap(p.a, p.ra, p.b, p.rb)) {
        const c = cap2(a, ra, b, rb, grow);
        const mid: V3 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
        const lit = clamp(spillAt(mid[0], mid[2], angle) * lamp) * lightGain;
        out.push({d: capPath(c), depth: c.depth + (p.bias || 0), inside, color: mixc(tone(p), WARM, lit), matte: (p as any).matte, mid});
      }
    } else {
      const pts = (p as any).pts as V3[];
      const pr = pts.map(project); const depth = pr.reduce((s, q) => s + q[2], 0) / pr.length + ((p as any).bias || 0);
      const mid: V3 = [pts[0][0], pts[0][1], pts[0][2]];
      const lit = clamp(spillAt(mid[0], mid[2], angle) * lamp) * lightGain;
      out.push({d: 'M' + pr.map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join('L') + 'Z', depth, inside: mid[0] < WORLD.wallOut,
        color: mixc(tone(p), WARM, lit), matte: (p as any).matte, mid});
    }
  }
  return out.sort((a, b) => b.depth - a.depth);
}

const Layer: React.FC<{ps: Piece[]; clip: string; fill: (p: Piece) => string; stroke?: string; sw?: number}> = ({ps, clip, fill, stroke, sw}) => (
  <>{ps.map((p, k) => <path key={k} d={p.d} fill={fill(p)} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" clipPath={p.inside ? `url(#${clip})` : undefined}/>)}</>
);

export const Dog: React.FC<{pose: DogPose; angle: number; lamp: number; clip: string; matte?: boolean; dusk: number}> = ({pose, angle, lamp, clip, matte, dusk}) => {
  const parts = dogParts(pose);
  // far-side legs read darker: compare each part's depth with the body centre
  const centre = project([pose.X, 0.45, pose.Z])[2];
  const tone = (p: Part) => {
    let c = DOG_TONE[p.tone];
    const d = p.kind === 'cap' ? (project(p.a)[2] + project(p.b)[2]) / 2 : project(p.pts[0])[2];
    if (d > centre + 0.07 && p.tone !== 'eye' && p.tone !== 'nose') c = mixc(c, '#0c0a0e', 0.38);
    return mixc(c, '#2a3048', 0.18 * dusk);
  };
  if (matte) {
    const ps = pieces(parts, () => '#000000', 0, angle, 0, 0);
    return <g><Layer ps={ps} clip={clip} fill={p => MATTE[p.matte as Matte]}/></g>;
  }
  const fills = pieces(parts, tone, 0, angle, lamp, 0.13);
  const outline = pieces(parts, () => '#0d0b0c', 1.4, angle, 0, 0);
  // cast shadow from the doorway lamp (only on the porch, only where the light falls) and a contact shadow
  const sh: string[] = [], contact: string[] = [];
  for (const p of parts) if (p.kind === 'cap' && p.tone !== 'eye' && p.tone !== 'nose') {
    if (p.a[0] > WORLD.wallOut && p.b[0] > WORLD.wallOut) {
      const a = shadowOf(p.a), b = shadowOf(p.b);
      sh.push(capPath(cap2(a, p.ra * 1.05, b, p.rb * 1.05)));
    }
    const ga: V3 = [p.a[0], 0.003, p.a[2]], gb: V3 = [p.b[0], 0.003, p.b[2]];
    if (p.a[1] < 0.7) contact.push(capPath(cap2(ga, p.ra * (1.2 - p.a[1]), gb, p.rb * (1.2 - p.b[1]))));
  }
  return (
    <g>
      <g opacity={0.5 * lamp} clipPath="url(#spillClip)" filter="url(#soft)"><path d={sh.join('')} fill="#140d0a"/></g>
      <g opacity={0.45} filter="url(#soft)"><path d={contact.join('')} fill="#07060a"/></g>
      <Layer ps={outline} clip={clip} fill={() => '#0d0b0c'}/>
      <Layer ps={fills} clip={clip} fill={p => p.color}/>
    </g>
  );
};

export const Person: React.FC<{pose: PersonPose; angle: number; lamp: number; clip: string; dusk: number}> = ({pose, angle, lamp, clip, dusk}) => {
  const parts = personParts(pose);
  const tone = (p: any) => mixc(PERSON_TONE[p.tone as PTone], '#232a40', 0.25 * dusk);
  const fills = pieces(parts, tone, 0, angle, lamp, 0.25);
  const outline = pieces(parts, () => '#0d0b0c', 1.3, angle, 0, 0);
  const sh: string[] = [];
  for (const p of parts) if (p.a[0] > WORLD.wallOut && p.b[0] > WORLD.wallOut) sh.push(capPath(cap2(shadowOf(p.a), p.ra, shadowOf(p.b), p.rb)));
  return (
    <g>
      <g opacity={0.45 * lamp} clipPath="url(#spillClip)" filter="url(#soft)"><path d={sh.join('')} fill="#140d0a"/></g>
      <Layer ps={outline} clip={clip} fill={() => '#0d0b0c'}/>
      <Layer ps={fills} clip={clip} fill={p => p.color}/>
    </g>
  );
};
