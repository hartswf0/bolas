import React from 'react';
import {registerRoot, Composition, useCurrentFrame, AbsoluteFill} from 'remotion';
const T = () => { const f = useCurrentFrame(); return <AbsoluteFill style={{background:'#123'}}><svg width={1280} height={720}><circle cx={100+f*10} cy={360} r={50} fill="orange"/></svg></AbsoluteFill>; };
registerRoot(() => <Composition id="T" component={T} durationInFrames={24} fps={24} width={1280} height={720}/>);
