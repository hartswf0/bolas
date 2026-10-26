import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
const fade = (f: number, n: number) => interpolate(f, [0, 12, n - 14, n - 1], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
const base: React.CSSProperties = {background: '#0e1020', color: '#efe7d8', justifyContent: 'center', alignItems: 'center', textAlign: 'center'};
export const Title: React.FC = () => {
  const f = useCurrentFrame(); const o = fade(f, 72);
  return (
    <AbsoluteFill style={base}>
      <div style={{opacity: o}}>
        <div style={{fontFamily: 'Big Shoulders Display', fontWeight: 800, fontSize: 74, letterSpacing: 2}}>PAE-02 · SCION 27 · Remotion</div>
        <div style={{fontFamily: 'Literata', fontStyle: 'italic', fontSize: 34, marginTop: 14, color: '#e3c48f'}}>The threshold, handmade</div>
        <div style={{fontFamily: 'JetBrains Mono', fontSize: 17, marginTop: 34, color: '#9aa0b8'}}>frame = f(score, cast, time, seed 27)</div>
      </div>
    </AbsoluteFill>
  );
};
export const End: React.FC = () => {
  const f = useCurrentFrame(); const o = fade(f, 72);
  const L: React.CSSProperties = {fontFamily: 'Literata', fontSize: 21, lineHeight: 1.5, color: '#e6dccb', maxWidth: 1040, margin: '0 auto'};
  return (
    <AbsoluteFill style={base}>
      <div style={{opacity: o, padding: '0 90px'}}>
        <div style={{fontFamily: 'Big Shoulders Display', fontWeight: 800, fontSize: 40, letterSpacing: 1.5, marginBottom: 18}}>What this is made of</div>
        <div style={L}>The dog is a joint graph of 34 capsules and two ear triangles: React components drawing SVG strokes from 3-D joints,
          a pure function of the PAELEO score frame and seed 27. Its proportions are measured from the archive dog's rig keys
          (<i>Amateur Film New Jersey C</i>, Home Movies, Internet Archive, public domain); its paws are placed by a stepping solver.</div>
        <div style={{...L, marginTop: 12}}>The person, porch, door and lit room are drawn the same way. The voice, paws, door and dusk are synthesised in numpy.
          No footage and no one else's drawings appear. Compiled and rendered with Remotion 4.0.538.</div>
      </div>
    </AbsoluteFill>
  );
};
