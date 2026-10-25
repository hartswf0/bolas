// SCION-27 · Remotion project root. Three compositions share one manifest: Film (38 s), Scene (32 s), DogMatte (measurement pass).
import React from 'react';
import {registerRoot, Composition, Sequence, AbsoluteFill, Audio, staticFile, delayRender, continueRender} from 'remotion';
import {Scene} from './comp/Scene.tsx';
import {Title, End} from './comp/Cards.tsx';

const FONTS: [string, string, string, string][] = [
  ['Big Shoulders Display', 'f5.woff2', '800', 'normal'], ['JetBrains Mono', 'f14.woff2', '400', 'normal'],
  ['Literata', 'f27.woff2', '400', 'italic'], ['Literata', 'f34.woff2', '400', 'normal']];
const fontHandle = delayRender('fonts');
Promise.all(FONTS.map(([fam, file, weight, style]) => new FontFace(fam, `url(${staticFile('fonts/' + file)})`, {weight, style}).load()
  .then(ff => { (document as any).fonts.add(ff); }))).then(() => continueRender(fontHandle)).catch(e => { console.error(e); continueRender(fontHandle); });

const Film: React.FC = () => (
  <AbsoluteFill style={{background: '#0e1020'}}>
    <Sequence from={0} durationInFrames={72}><Title/></Sequence>
    <Sequence from={72} durationInFrames={768}><Scene/></Sequence>
    <Sequence from={840} durationInFrames={72}><End/></Sequence>
    <Audio src={staticFile('mix.wav')}/>
  </AbsoluteFill>
);
const Root: React.FC = () => (
  <>
    <Composition id="Film" component={Film} durationInFrames={912} fps={24} width={1280} height={720}/>
    <Composition id="Scene" component={Scene} durationInFrames={768} fps={24} width={1280} height={720}/>
    <Composition id="DogMatte" component={() => <Scene matte/>} durationInFrames={768} fps={24} width={1280} height={720}/>
  </>
);
registerRoot(Root);
