import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorldStylePass, STYLE_PRESETS} from '../world-style.js';

// The pass receives the host's Three classes. These doubles exercise its own
// lifecycle and state contract without creating a second WebGL renderer.
class Pass { constructor() { this.enabled = true; this.needsSwap = true; } }
class Vector2 { constructor(x, y) { this.set(x, y); } set(x, y) { this.x = x; this.y = y; } }
class ShaderMaterial { constructor(options) { Object.assign(this, options); } dispose() { this.disposed = true; } }
class FullScreenQuad {
  constructor(material) { this.material = material; }
  render(renderer) { renderer.draws++; }
  dispose() { this.disposed = true; }
}
const create = () => createWorldStylePass({
  THREE: {Vector2, ShaderMaterial, NoBlending: 0}, Pass, FullScreenQuad
});

test('Original bypasses treatment; fine outline settings can enable it', () => {
  const pass = create();
  assert.equal(pass.enabled, false);
  pass.configure({outline: .05});
  assert.equal(pass.enabled, true);
  pass.configure({strength: 0});
  assert.equal(pass.enabled, false);
  pass.configure({strength: .5, preset: 'ink', outline: 0});
  assert.equal(pass.enabled, true);
  pass.configure({preset: 'original'});
  assert.equal(pass.enabled, false);
});

test('Partial configuration keeps prior values and rejects invalid numbers', () => {
  const pass = create();
  pass.configure({preset: 'woodblock', strength: .61, outline: .12, lineWidth: .7, grain: .4});
  pass.configure({outline: .13, lineWidth: Infinity, grain: NaN});
  assert.equal(pass.config.strength, .61);
  assert.equal(pass.config.outline, .13);
  assert.equal(pass.config.lineWidth, .7);
  assert.equal(pass.config.grain, .4);
  pass.configure({strength: 20, outline: -1, lineWidth: .02});
  assert.equal(pass.config.strength, 1);
  assert.equal(pass.config.outline, 0);
  assert.equal(pass.config.lineWidth, .5);
  pass.configure({preset: 'unrecognized'});
  assert.equal(pass.config.preset, 'original');
  assert.equal(pass.enabled, false);
});

test('Every advertised preset has its own shader selector', () => {
  const pass = create();
  assert.equal(new Set(STYLE_PRESETS.map(p => p.id)).size, 9);
  STYLE_PRESETS.forEach((preset, index) => {
    pass.configure({preset: preset.id});
    assert.equal(pass.material.uniforms.uPreset.value, index);
  });
});

test('Reduced motion freezes shader time without discarding the shared clock', () => {
  const pass = create();
  pass.configure({time: 10, reducedMotion: true});
  assert.equal(pass.material.uniforms.uTime.value, 0);
  assert.equal(pass.config.time, 10);
  pass.configure({time: 13});
  assert.equal(pass.material.uniforms.uTime.value, 0);
  pass.configure({reducedMotion: false});
  assert.equal(pass.material.uniforms.uTime.value, 13);
});

test('Composer buffer, resize and resource ownership stay with the host', () => {
  const pass = create();
  pass.setSize(1280, 720);
  pass.setSize(NaN, 0);
  assert.deepEqual({...pass.material.uniforms.uResolution.value}, {x: 1280, y: 1});
  const renderer = {draws: 0, setRenderTarget(target) { this.target = target; }};
  const input = {texture: {}}, output = {};
  pass.render(renderer, output, input);
  assert.equal(renderer.target, output);
  assert.equal(pass.material.uniforms.tDiffuse.value, input.texture);
  assert.equal(renderer.draws, 1);
  pass.renderToScreen = true;
  pass.render(renderer, output, input);
  assert.equal(renderer.target, null);
  pass.dispose();
  assert.equal(pass.material.disposed, true);
  assert.equal(pass.quad.disposed, true);
});
