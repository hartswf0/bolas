// Render engineer's library: one bundle, one browser, one contract (Remotion 4.0.538 + Playwright's chrome-headless-shell 1243).
import {createRequire} from 'module';
import path from 'path';
import {fileURLToPath} from 'url';
export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const DEPS = path.join(HERE, 'cache/deps/node_modules');
const require = createRequire(DEPS + '/');
export const {bundle} = require('@remotion/bundler');
export const R = require('@remotion/renderer');
export const browserExecutable = process.env.SCION27_BROWSER || '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
export const chromiumOptions = {gl: 'swangle', disableWebSecurity: false};
export async function serve() {
  return bundle({entryPoint: path.join(HERE, 'src/index.tsx'), publicDir: path.join(HERE, 'cache/public'),
    webpackOverride: c => ({...c, resolve: {...c.resolve, modules: [DEPS, 'node_modules']}})});
}
export async function stills(serveUrl, id, frames, outDir, fmt = 'jpeg') {
  const composition = await R.selectComposition({serveUrl, id, browserExecutable, chromiumOptions, logLevel: 'error'});
  const out = [];
  for (const frame of frames) {
    const output = path.join(outDir, `${id}_${String(frame).padStart(4, '0')}.${fmt === 'png' ? 'png' : 'jpg'}`);
    await R.renderStill({composition, serveUrl, frame, output, imageFormat: fmt, ...(fmt === 'jpeg' ? {jpegQuality: 92} : {}), browserExecutable, chromiumOptions, logLevel: 'error'});
    out.push(output);
  }
  return out;
}
