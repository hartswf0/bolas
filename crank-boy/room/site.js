/* The Crank Boy site bar: one navigation for every reading page (see DESIGN.md, page contract).
   <script src="../room/site.js" data-root="../" data-here="films"></script>   placed just after <body>.
   data-root is the path from the page back to the repository root; data-here is one of album, futuretown, films, kit. */
(function () {
  var s = document.currentScript, root = s.getAttribute('data-root') || '', here = s.getAttribute('data-here') || '';
  /* When this site is mirrored inside Bolas (shorts/tools/to_bolas.py), every page carries <meta name="crank-mirror">, the album is
     album.html (index.html is the Bolas landing page) and Bolas itself is one folder up. */
  var mirror = !!document.querySelector('meta[name="crank-mirror"]');
  window.CRANK_SITE = { root: root, mirror: mirror, album: root + (mirror ? 'album.html' : 'index.html'), bolas: mirror ? root + '../' : 'https://hartswf0.github.io/bolas/' };
  var css = '.sitebar{display:flex;align-items:center;gap:6px 18px;flex-wrap:wrap;max-width:1100px;margin:0 auto;padding:10px 16px 6px;font-family:var(--display,"IM Fell English SC",Georgia,serif);color:var(--ink,#2B2320)}' +
    '.sitebar .sb-mark{display:flex;align-items:center;gap:8px;margin-right:auto;font-size:19px;letter-spacing:.02em;text-decoration:none;color:inherit}' +
    '.sitebar a.sb{font-size:14.5px;letter-spacing:.06em;text-decoration:none;color:var(--muted,#6E5F4F);padding:3px 0;border-bottom:2px solid transparent}' +
    '.sitebar a.sb:hover{color:var(--ink,#2B2320)}.sitebar a.sb[aria-current=page]{color:var(--ink,#2B2320);border-bottom-color:var(--red,#B44A3C)}' +
    '.sitebar a:focus-visible{outline:2px solid var(--red,#B44A3C);outline-offset:2px}' +
    '@media (max-width:560px){.sitebar{padding:8px 12px 4px;gap:4px 12px}.sitebar .sb-mark{font-size:17px;width:100%}.sitebar a.sb{font-size:13.5px}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  var items = [['album', 'Album', mirror ? 'album.html' : 'index.html'], ['futuretown', 'Futuretown', 'shorts/index.html'], ['films', 'Films', 'films.html'], ['kit', 'Kit', 'kit.html']];
  var nav = document.createElement('nav'); nav.className = 'sitebar'; nav.setAttribute('aria-label', 'The Crank Boy');
  nav.innerHTML = '<a class="sb-mark" href="' + CRANK_SITE.album + '"><svg width="26" height="26" viewBox="-12 -12 24 24" aria-hidden="true"><g fill="none" stroke="#C0573A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M-9 0 L0 -8.5 L9 0 M-7 0 V8.5 M7 0 V8.5 M0 -8.5 V-5"/></g><circle cx="-2.8" cy="2.6" r="1.1" fill="#C0573A"/><circle cx="2.8" cy="2.6" r="1.1" fill="#C0573A"/></svg>The Crank Boy</a>' +
    items.map(function (i) { return '<a class="sb" href="' + root + i[2] + '"' + (i[0] === here ? ' aria-current="page"' : '') + '>' + i[1] + '</a>'; }).join('');
  s.parentNode.insertBefore(nav, s.nextSibling);
})();
