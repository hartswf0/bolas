/**
 * A shared, renderer-independent art treatment for the archive rooms.
 * Add the returned pass after the existing LookPass. It never owns a renderer,
 * scene, clock or media element. Widths are in drawing-buffer pixels.
 *
 * These are screen-space pigment/print approximations. Contours come from
 * luminance differences, not geometry normals; grain belongs to the picture
 * plane. The pass deliberately does not claim to simulate wet paint or cloth.
 */
export const STYLE_PRESETS = Object.freeze([
  {id: 'original', label: 'Room original'},
  {id: 'woodblock', label: 'Woodblock print'},
  {id: 'ink', label: 'Ink landscape'},
  {id: 'doodle', label: 'Pen doodle'},
  {id: 'watercolor', label: 'Watercolor'},
  {id: 'graffiti', label: 'Spray / graffiti'},
  {id: 'thread', label: 'Embroidered thread'},
  {id: 'cyanotype', label: 'Cyanotype / X-ray'},
  {id: 'glass', label: 'Stained glass'}
].map(Object.freeze));

export const DEFAULT_STYLE = Object.freeze({
  preset: 'original', strength: .8, outline: 0, lineWidth: 1.25,
  grain: .35, wobble: .15, time: 0, reducedMotion: false
});

const finite = (value, previous, low, high) => Number.isFinite(value)
  ? Math.min(high, Math.max(low, value)) : previous;

const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

const fragmentShader = `
uniform sampler2D tDiffuse;
uniform vec2 uResolution;
uniform int uPreset;
uniform float uStrength, uOutline, uLineWidth, uGrain, uWobble, uTime;
varying vec2 vUv;

float luminance(vec3 c) { return dot(c, vec3(.299, .587, .114)); }
float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}
float noise2(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash21(i), hash21(i + vec2(1., 0.)), f.x),
             mix(hash21(i + vec2(0., 1.)), hash21(i + vec2(1.)), f.x), f.y);
}
vec3 samplePicture(vec2 p) {
  return texture2D(tDiffuse, clamp(p, vec2(0.), vec2(1.))).rgb;
}
vec3 saturateColor(vec3 c, float amount) {
  return clamp(mix(vec3(luminance(c)), c, amount), 0., 1.);
}

void main() {
  vec4 source = texture2D(tDiffuse, vUv);
  if (uStrength <= 0. || (uPreset == 0 && uOutline <= 0.)) {
    gl_FragColor = source;
    return;
  }
  vec2 px = vUv * uResolution;
  vec2 texel = 1. / uResolution;
  // The field is stable. Time introduces a slow subpixel breathing of the pen,
  // never a random seed per frame. Reduced motion freezes uTime on the CPU.
  vec2 drift = vec2(
    sin(px.y * .025 + noise2(px / 71.) * 3. + uTime * .32),
    cos(px.x * .021 + noise2(px / 83. + 4.) * 3. + uTime * .27)
  ) * uWobble * .8 * texel;
  vec2 uv = vUv + drift, stepSize = texel * uLineWidth;
  vec3 tl = samplePicture(uv + stepSize * vec2(-1., 1.));
  vec3 tc = samplePicture(uv + stepSize * vec2(0., 1.));
  vec3 tr = samplePicture(uv + stepSize * vec2(1., 1.));
  vec3 ml = samplePicture(uv + stepSize * vec2(-1., 0.));
  vec3 mr = samplePicture(uv + stepSize * vec2(1., 0.));
  vec3 bl = samplePicture(uv + stepSize * vec2(-1., -1.));
  vec3 bc = samplePicture(uv + stepSize * vec2(0., -1.));
  vec3 br = samplePicture(uv + stepSize * vec2(1., -1.));
  // Nine source samples are shared by every treatment and its Sobel outline.
  vec3 blur = (tl + tc * 2. + tr + ml * 2. + source.rgb * 4.
    + mr * 2. + bl + bc * 2. + br) / 16.;
  float gx = luminance(tr + mr * 2. + br - tl - ml * 2. - bl) * .25;
  float gy = luminance(tl + tc * 2. + tr - bl - bc * 2. - br) * .25;
  float edge = smoothstep(.035, .2, length(vec2(gx, gy)));
  float l = luminance(source.rgb), lb = luminance(blur);
  float tooth = noise2(px / 2.7) * .6 + noise2(px / 13.) * .4;
  float fine = hash21(floor(px)) - .5;
  float broad = noise2(px / 90.);
  vec3 paper = vec3(.965, .947, .89) * (1. + uGrain * (tooth - .5) * .13);
  vec3 color = source.rgb;
  vec3 lineColor = vec3(.045, .055, .075);
  float outline = edge * uOutline;

  if (uPreset == 1) {
    // Separate printing plates and thin carved gouges; a pale paper ground
    // allows the existing luminous animals to read as ink impressions.
    float level = l + (tooth - .5) * uGrain * .055;
    color = paper;
    color = mix(color, vec3(.48, .66, .63), smoothstep(.075, .1, level));
    color = mix(color, vec3(.12, .34, .39), smoothstep(.21, .24, level));
    color = mix(color, vec3(.055, .13, .24), smoothstep(.43, .46, level));
    color = mix(color, vec3(.86, .48, .24), smoothstep(.68, .72, level));
    color = mix(color, paper, smoothstep(.9, 1., level));
    float cut = smoothstep(.84, .98, sin(px.y * .85 + noise2(px / 42.) * 9.) * .5 + .5);
    cut *= smoothstep(.1, .3, level) * (1. - smoothstep(.6, .9, level));
    color = mix(color, paper, cut * (.2 + uGrain * .55));
    color *= 1. + fine * uGrain * .09;
    lineColor = vec3(.04, .1, .19);
  } else if (uPreset == 2) {
    // Diluted washes, fibrous brush skips and darker pooled contour ink.
    float fibers = noise2(vec2(px.x / 3., px.y / 64.));
    float ink = smoothstep(.035, .2, lb) * .32
      + smoothstep(.17, .5, lb) * .48 + smoothstep(.53, .88, l) * .14;
    float dry = mix(1., smoothstep(.15, .65, fibers + lb), uGrain * (1. - lb) * .6);
    color = paper * (1. - ink * dry);
    color = mix(color, paper * vec3(.83, .88, .92),
      smoothstep(.02, .07, lb) * (1. - smoothstep(.07, .15, lb)) * .3);
    lineColor = vec3(.06, .055, .06);
    outline *= .45 + .55 * smoothstep(.12, .75, fibers + .15);
  } else if (uPreset == 3) {
    // Open pen contours with irregular dry gaps and a faint colored wash.
    float gap = smoothstep(.12, .48, noise2(px / 8. + 2.));
    float pen = edge * mix(1., gap, .28 + uGrain * .4);
    color = mix(paper, saturateColor(source.rgb, .65) * .6 + .35, .08 * smoothstep(.04, .6, l));
    lineColor = vec3(.13, .1, .18);
    color = mix(color, lineColor, pen * .76);
    outline *= .6;
  } else if (uPreset == 4) {
    // A wash on paper: shared neighboring taps soften edges, while pigment
    // concentration increases at the contour and in the paper's tooth.
    vec3 hue = saturateColor(blur / max(max(blur.r, max(blur.g, blur.b)), .09), 1.35);
    vec3 dye = mix(vec3(.73, .79, .84), hue, .7);
    float pigment = smoothstep(.025, .3, lb) * (.45 + tooth * .34);
    color = paper * mix(vec3(1.), dye * .8, pigment);
    color *= 1. - edge * (.08 + uGrain * .14);
    float tide = smoothstep(.56, .66, broad) * (1. - smoothstep(.66, .76, broad));
    color = mix(color, paper, tide * pigment * uGrain * .22);
    lineColor = vec3(.24, .27, .31);
    outline *= .52;
  } else if (uPreset == 5) {
    // Solid paint, a spray halo and a pale tag outline on rough charcoal.
    vec3 wall = vec3(.115, .12, .14) * (1. + (tooth - .5) * uGrain * .5);
    vec3 hue = saturateColor(source.rgb / max(max(source.r, max(source.g, source.b)), .08), 1.8);
    vec3 accent = mix(vec3(.97, .38, .2), vec3(.22, .77, .84), smoothstep(.2, .8, noise2(px / 160.)));
    hue = mix(hue, accent, .45);
    float mist = smoothstep(.025, .15, lb) * (1. - smoothstep(.05, .24, l));
    float spray = smoothstep(.35, .72, hash21(floor(px / 1.4)));
    color = mix(wall, hue * .72, mist * spray * (.3 + uGrain * .5));
    float paint = smoothstep(.065, .12, l + fine * uGrain * .08);
    color = mix(color, hue * (.68 + .28 * floor(clamp(l, 0., .999) * 3.) / 2.), paint);
    color = mix(color, vec3(.98, .93, .8), smoothstep(.86, 1., l));
    lineColor = vec3(.97, .94, .82);
  } else if (uPreset == 6) {
    // Small diagonal stitches have a raised central filament, over a weave.
    vec2 cell = floor(px / 6.), local = fract(px / 6.) - .5;
    float flip = mod(cell.x + cell.y, 2.) * 2. - 1.;
    float stitch = 1. - smoothstep(.06, .22, abs(local.y - local.x * flip));
    stitch *= 1. - smoothstep(.3, .49, max(abs(local.x), abs(local.y)));
    float filament = 1. - smoothstep(.015, .07, abs(local.y - local.x * flip + .05));
    float weave = sin(px.x * 1.57) * sin(px.y * 1.57);
    vec3 cloth = vec3(.045, .075, .13) * (1. + weave * uGrain * .24);
    vec3 yarn = saturateColor(blur, 1.25) * .8 + vec3(.16, .13, .17);
    yarn += filament * .16;
    color = mix(cloth, yarn, stitch * smoothstep(.025, .3, lb));
    color += edge * vec3(.15, .16, .2) * .25;
    lineColor = vec3(.82, .79, .66);
    outline *= .55 + .45 * stitch;
  } else if (uPreset == 7) {
    // A deep blue photographic print with white radiographic contours.
    float exposure = clamp(pow(max(l, 0.), .76) + edge * .18, 0., 1.);
    vec3 blue = mix(vec3(.015, .1, .28), vec3(.025, .32, .52), broad * .36);
    color = mix(blue, paper * vec3(.94, .98, 1.), exposure);
    color *= 1. + (tooth - .5) * uGrain * .13;
    lineColor = vec3(.91, .98, 1.);
  } else if (uPreset == 8) {
    // A lightly irregular rectangular glass leading, with one extra tap for
    // its pane color. This is mosaic glass, not a ray-traced refractive model.
    vec2 lattice = px / 24. + vec2(noise2(px / 120.), noise2(px / 130. + 7.)) * .32;
    vec2 cell = floor(lattice), f = fract(lattice);
    vec3 pane = samplePicture((cell + .5) * 24. / uResolution);
    vec3 hue = saturateColor(pane / max(max(pane.r, max(pane.g, pane.b)), .12), 1.8);
    float choice = hash21(cell);
    vec3 jewel = choice < .33 ? vec3(.27, .43, .82) : choice < .66 ? vec3(.87, .43, .17) : vec3(.38, .67, .56);
    hue = mix(hue, jewel, .44);
    float lead = 1. - smoothstep(.025, .065, min(min(f.x, 1. - f.x), min(f.y, 1. - f.y)));
    color = hue * (.2 + .85 * luminance(pane));
    color += vec3(.1, .12, .13) * smoothstep(.56, 1., l);
    color *= 1. + (tooth - .5) * uGrain * .19;
    color = mix(color, vec3(.025, .03, .04), lead * .82);
    lineColor = vec3(.025, .03, .04);
  }
  color = mix(color, lineColor, clamp(outline, 0., 1.));
  gl_FragColor = vec4(mix(source.rgb, clamp(color, 0., 1.), uStrength), source.a);
}`;

/** Inject the same THREE/Pass classes already used by the host composer. */
export function createWorldStylePass({THREE, Pass, FullScreenQuad}) {
  return new (class WorldStylePass extends Pass {
    constructor() {
      super();
      this.name = 'ArchiveWorldStyle';
      this.config = {...DEFAULT_STYLE};
      this.material = new THREE.ShaderMaterial({
        name: 'ArchiveWorldStyleMaterial',
        uniforms: {
          tDiffuse: {value: null}, uResolution: {value: new THREE.Vector2(1, 1)},
          uPreset: {value: 0}, uStrength: {value: .8}, uOutline: {value: 0},
          uLineWidth: {value: 1.25}, uGrain: {value: .35},
          uWobble: {value: .15}, uTime: {value: 0}
        },
        vertexShader, fragmentShader, depthTest: false, depthWrite: false,
        // The existing OutputPass has already encoded the picture.
        toneMapped: false, blending: THREE.NoBlending
      });
      this.quad = new FullScreenQuad(this.material);
      this.configure(this.config);
    }

    configure(next = {}) {
      const c = this.config;
      if (Object.hasOwn(next, 'preset')) {
        c.preset = STYLE_PRESETS.some(p => p.id === next.preset) ? next.preset : 'original';
      }
      for (const key of ['strength', 'outline', 'grain', 'wobble']) {
        c[key] = finite(next[key], c[key], 0, 1);
      }
      c.lineWidth = finite(next.lineWidth, c.lineWidth, .5, 4);
      c.time = finite(next.time, c.time, 0, 1e9);
      if (typeof next.reducedMotion === 'boolean') c.reducedMotion = next.reducedMotion;
      const u = this.material.uniforms;
      u.uPreset.value = STYLE_PRESETS.findIndex(p => p.id === c.preset);
      u.uStrength.value = c.strength;
      u.uOutline.value = c.outline;
      u.uLineWidth.value = c.lineWidth;
      u.uGrain.value = c.grain;
      u.uWobble.value = c.wobble;
      u.uTime.value = c.reducedMotion ? 0 : c.time;
      this.enabled = c.strength > 0 && (c.preset !== 'original' || c.outline > 0);
      return this;
    }

    setSize(width, height) {
      const size = this.material.uniforms.uResolution.value;
      size.set(finite(width, size.x, 1, 32768), finite(height, size.y, 1, 32768));
    }

    render(renderer, writeBuffer, readBuffer) {
      this.material.uniforms.tDiffuse.value = readBuffer.texture;
      renderer.setRenderTarget(this.renderToScreen ? null : writeBuffer);
      if (this.clear) renderer.clear();
      this.quad.render(renderer);
    }

    dispose() {
      this.material.dispose();
      this.quad.dispose();
    }
  })();
}
