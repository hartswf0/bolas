"use strict";

const get = id => document.getElementById(id);
const data = JSON.parse(get("catalogue-data").textContent);
const entries = new Map(data.entries.map(entry => [entry.id, entry]));
const standalone = Number(document.body.dataset.start);
const root = standalone ? "../../" : "./";
const families = ["Cinema", "Comics", "Animation", "Variations", "Literature", "Compiler"];
const search = get("query");
const panel = get("panel");
const list = get("catalogue-list");
let selected = entries.get(standalone) ?? data.entries[0];
let activeFamily = "All";
let activeTab = 0;

get("home").href = root;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function comparable(text) {
  return text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

function pageLink(entry) {
  return root + "s/" + entry.slug + "/index.html";
}

function renderList() {
  const needle = comparable(search.value.trim());
  const matches = data.catalogue.filter(entry => {
    const haystack = comparable(
      [entry.work, entry.title, entry.family, entry.byline, entry.line, entry.slug].join(" ")
    );
    return (activeFamily === "All" || activeFamily === entry.family) && haystack.includes(needle);
  });
  get("catalogue-count").textContent = matches.length + " of " + data.catalogue.length + " prompts";
  const previousScroll = list.scrollTop;
  list.replaceChildren();
  for (const family of families) {
    const group = matches.filter(entry => entry.family === family);
    if (!group.length) continue;
    list.append(element("p", family, "list-group"));
    for (const entry of group) {
      const item = element("a", null, "catalogue-item");
      item.href = pageLink(entry);
      item.dataset.id = entry.id;
      if (entry.id === selected.id) item.setAttribute("aria-current", "page");
      item.append(element("span", entry.work, "item-name"), element("span", entry.title, "item-rule"));
      if (!standalone) {
        item.addEventListener("click", event => {
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
          event.preventDefault();
          const hash = "#s" + entry.id;
          if (location.hash !== hash) history.pushState(null, "", hash);
          select(entry.id);
          if (matchMedia("(max-width: 760px)").matches) {
            showCatalogue(false);
          }
          get("work-name").focus({preventScroll: true});
          get("selection").scrollIntoView({block: "start"});
        });
      }
      list.append(item);
    }
  }
  list.scrollTop = previousScroll;
}

const filters = new Map();
for (const family of ["All", ...families]) {
  const button = element("button", family, "filter");
  button.type = "button";
  button.setAttribute("aria-pressed", String(family === activeFamily));
  button.addEventListener("click", () => {
    activeFamily = family;
    for (const [name, control] of filters) {
      control.setAttribute("aria-pressed", String(name === activeFamily));
    }
    renderList();
  });
  filters.set(family, button);
  get("filters").append(button);
}
search.addEventListener("input", renderList);

function showCatalogue(open) {
  get("catalogue-controls").closest(".catalogue").dataset.open = String(open);
  get("browse").setAttribute("aria-expanded", String(open));
  get("browse").textContent = open ? "Close catalog" : "Browse prompts";
}

get("browse").addEventListener("click", () => {
  const open = get("browse").getAttribute("aria-expanded") !== "true";
  showCatalogue(open);
  if (open) search.focus();
});

const tabButtons = data.tabs.map((label, index) => {
  const tab = element("button", label, "tab");
  tab.type = "button";
  tab.setAttribute("aria-controls", "panel");
  tab.addEventListener("click", () => showTab(index));
  get("tabs").append(tab);
  return tab;
});

function addText(parent, heading, body) {
  parent.append(element("h3", heading));
  for (const part of body.split("\n\n")) parent.append(element("p", part));
}

function renderReference(reference) {
  const [key, alt, credit] = reference;
  const figure = element("figure");
  const button = element("button", null, "image-button");
  button.type = "button";
  button.setAttribute("aria-label", "Enlarge reference image. " + alt);
  const image = element("img");
  image.src = root + data.images[key];
  image.alt = alt;
  button.append(image);
  button.addEventListener("click", () => openImage(reference));
  figure.append(button, element("figcaption", credit));
  return figure;
}

function openImage([key, alt, credit]) {
  const dialog = element("dialog", null, "lightbox");
  dialog.setAttribute("aria-label", "Reference image");
  const head = element("header");
  const close = element("button", "Close", "action");
  close.type = "button";
  close.addEventListener("click", () => dialog.close());
  head.append(element("p", credit), close);
  const image = element("img");
  image.src = root + data.images[key];
  image.alt = alt;
  dialog.append(head, image);
  dialog.addEventListener("close", () => dialog.remove(), {once: true});
  document.body.append(dialog);
  dialog.showModal();
}

function renderOverview(entry) {
  if (entry.family === "Compiler") {
    for (const index of [0, 8, 9]) {
      const section = entry.sections[index];
      addText(panel, section.heading, section.body);
    }
    return;
  }

  const layout = element("div", null, "proof-layout");
  if (entry.id === 1) layout.classList.add("archive");
  const copy = element("div", null, "proof-copy");
  addText(copy, "What stays fixed", entry.invariant);
  addText(copy, "First proof to build", entry.proof);
  addText(copy, "What the critic checks", entry.critic);
  const references = element("div", null, "reference-images");
  references.append(renderReference(entry.image));
  if (entry.gallery) {
    const pair = element("div", null, "image-pair");
    for (const reference of entry.gallery) pair.append(renderReference(reference));
    references.append(pair);
  }
  layout.append(copy, references);
  panel.append(layout);

  const seed = element("details", null, "seed");
  seed.append(element("summary", "Try the same station incident"));
  seed.append(element("p", data.station));
  const events = element("ol");
  for (const [id, description] of data.events) {
    const row = element("li");
    row.append(element("code", id), document.createTextNode("  " + description));
    events.append(row);
  }
  seed.append(events, element("p", entry.shared));
  panel.append(seed);
}

function renderSources(entry) {
  const sources = element("ul", null, "source-list");
  for (const [label, href, evidence] of entry.sources) {
    const row = element("li");
    const link = element(href ? "a" : "strong", label);
    if (href) {
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener";
    }
    row.append(link, element("p", evidence));
    sources.append(row);
  }
  panel.append(sources);
}

function showTab(index) {
  activeTab = index;
  tabButtons.forEach((button, tabIndex) => {
    button.setAttribute("aria-pressed", String(tabIndex === activeTab));
  });
  panel.replaceChildren();
  if (activeTab === 0) renderOverview(selected);
  if (activeTab === 1) panel.append(element("pre", selected.markdown, "prompt"));
  if (activeTab === 2) renderSources(selected);
}

function select(id) {
  selected = entries.get(id) ?? data.entries[0];
  const heading = selected.family === "Compiler" ? selected.title : selected.work;
  get("work-name").textContent = heading;
  get("work-name").tabIndex = -1;
  get("byline").textContent = selected.byline;
  get("work-description").textContent = selected.line;
  get("status").textContent = "";
  document.title = heading + " · Oulipo SCION";
  renderList();
  showTab(activeTab);
}

function selectFromLocation() {
  if (standalone) return;
  const match = /^#s(\d+)$/.exec(location.hash);
  if (match) select(Number(match[1]));
  else select(location.hash ? selected.id : data.entries[0].id);
}

function fallbackCopy(value) {
  const control = element("textarea");
  control.value = value;
  control.setAttribute("aria-label", "Text to copy");
  control.className = "sr";
  const before = document.activeElement;
  document.body.append(control);
  control.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } finally {
    control.remove();
    before?.focus();
  }
  return copied;
}

async function copy(value, kind) {
  const status = get("status");
  try {
    if (!navigator.clipboard) throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(value);
    status.textContent = kind + " copied.";
  } catch {
    try {
      if (fallbackCopy(value)) {
        status.textContent = kind + " copied.";
        return;
      }
    } catch {
      // Use a visible selection if the browser declines programmatic copying.
    }
    if (kind === "Prompt") {
      showTab(1);
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(panel.firstChild);
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = "Prompt selected. Use your device’s copy command.";
    } else {
      if (!standalone) history.replaceState(null, "", "#s" + selected.id);
      status.textContent = "Copy the link from your address bar.";
    }
  }
}

function download(extension, content) {
  const mime = extension === "md" ? "text/markdown" : "application/xml";
  const href = URL.createObjectURL(new Blob([content], {type: mime + ";charset=utf-8"}));
  const link = element("a");
  link.href = href;
  link.download = selected.slug + "." + extension;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(href), 2000);
  get("status").textContent = link.download + " download requested.";
}

get("copy").addEventListener("click", () => copy(selected.markdown, "Prompt"));
get("poml").addEventListener("click", () => download("poml", selected.poml));
get("markdown").addEventListener("click", () => download("md", selected.markdown));
get("link").addEventListener("click", () => {
  const address = new URL(standalone ? location.href : pageLink(selected), location.href);
  address.hash = "";
  copy(address.href, "Link");
});
window.addEventListener("hashchange", selectFromLocation);
window.addEventListener("popstate", selectFromLocation);
if (standalone) select(standalone);
else selectFromLocation();
