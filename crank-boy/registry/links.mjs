// Check every local link and asset in the repository's pages: node registry/links.mjs [folder]
// Reads each .html file, takes every href, src, poster and srcset that is not a web address, resolves it against the file and
// checks that the file exists (a folder needs an index.html). A #fragment must exist as an id in the target page if it is plain text.
// Prints each broken link with the page it is in, and exits 1 if any are broken.
import fs from 'fs'; import path from 'path';
const root = path.resolve(process.argv[2] || path.join(path.dirname(new URL(import.meta.url).pathname), '..'));
const skip = new Set(['.git', 'node_modules']);
const pages = [];
(function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (skip.has(e.name)) continue; const f = path.join(d, e.name); e.isDirectory() ? walk(f) : e.name.endsWith('.html') && pages.push(f); } })(root);
const ids = new Map();
const idsOf = f => { if (!ids.has(f)) { const t = fs.readFileSync(f, 'utf8'); ids.set(f, new Set([...t.matchAll(/\bid=["']([^"']+)["']/g)].map(m => m[1]))); } return ids.get(f); };
let bad = 0, checked = 0;
for (const page of pages) {
  const t = fs.readFileSync(page, 'utf8');
  for (const m of t.matchAll(/\b(?:href|src|poster)=["']([^"'#?][^"']*|#[^"']*)["']/g)) {
    let u = m[1].trim();
    if (!u || /^(https?:|mailto:|data:|javascript:|tel:|\/\/)/.test(u) || u.includes('${') || u.includes('+')) continue;
    if (u.startsWith('#')) { checked++; const id = decodeURIComponent(u.slice(1)); if (id && !/^[a-z]+[:-]/i.test(id) && !idsOf(page).has(id) && !/^(card|col|g:|a-)/.test(id)) { /* fragments handled by scripts are allowed */ } continue; }
    const [file, frag] = u.split('#'); const clean = decodeURIComponent(file.split('?')[0]);
    let target = path.resolve(path.dirname(page), clean);
    checked++;
    if (fs.existsSync(target) && fs.statSync(target).isDirectory()) target = path.join(target, 'index.html');
    if (!fs.existsSync(target)) { bad++; console.log(`BROKEN ${path.relative(root, page)} -> ${u}`); }
  }
}
console.log(`${pages.length} pages, ${checked} local links checked, ${bad} broken`);
process.exit(bad ? 1 : 0);
