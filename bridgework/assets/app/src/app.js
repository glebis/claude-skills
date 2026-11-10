import { createEngine, KIND_LABEL } from "./engine.js";

/* ---------- small helpers ---------- */
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const calm = matchMedia("(prefers-reduced-motion: reduce)");
const isNarrow = () => innerWidth <= 760;
const STORE = "bridgework.v1";
const load = () => { try { return JSON.parse(localStorage.getItem(STORE)) || {}; } catch { return {}; } };
const fmtDate = d => new Date(d + "T12:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
const GLYPH = {
  square: '<rect x="2" y="2" width="8" height="8"/>', diamond: '<path d="M6 .8 11.2 6 6 11.2.8 6z"/>', circle: '<circle cx="6" cy="6" r="4.6"/>',
  triangle: '<path d="M6 1.2 11 10.6H1z"/>', half: '<path d="M1.4 6a4.6 4.6 0 0 1 9.2 0z"/>', hexagon: '<path d="M3.2 1.2h5.6L11.6 6 8.8 10.8H3.2L.4 6z"/>',
  bars: '<path d="M1 11V7h2.4v4zM4.8 11V1h2.4v10zM8.6 11V4H11v7z"/>', chevron: '<path d="M2 1.4 9 6l-7 4.6z"/>', ring: '<circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="2.2"/>',
};
const glyph = t => { const y = E.facts.types.find(x => x.id === t); return `<svg viewBox="0 0 12 12" fill="currentColor" role="img" aria-label="${esc(y?.label || t)}">${GLYPH[y?.shape] || GLYPH.circle}</svg>`; };
const SHAPE_ICON = {
  hop: '<path d="M3 9h20"/><circle cx="3" cy="9" r="2"/><circle cx="23" cy="9" r="2"/>',
  chain: '<path d="M3 9h20"/><circle cx="3" cy="9" r="2"/><circle cx="13" cy="9" r="2"/><circle cx="23" cy="9" r="2"/>',
  fanin: '<path d="M3 3c10 0 10 6 20 6M3 15c10 0 10-6 20-6"/><circle cx="3" cy="3" r="2"/><circle cx="3" cy="15" r="2"/><circle cx="23" cy="9" r="2"/>',
  fanout: '<path d="M23 3C13 3 13 9 3 9M23 15C13 15 13 9 3 9"/><circle cx="23" cy="3" r="2"/><circle cx="23" cy="15" r="2"/><circle cx="3" cy="9" r="2"/>',
  loop: '<path d="M4 6h18M22 6c4 0 4 9 0 9H4C0 15 0 6 4 6"/><circle cx="4" cy="6" r="2"/><circle cx="22" cy="6" r="2"/>',
};

/* ---------- state ---------- */
let E, base;
const saved = load();
const S = {
  mode: "field", hand: [], route: null, revealed: false, idea: { text: "", sketch: null }, sketching: false,
  constraints: { local: false, spend: "any", budget: 10 }, rejected: [], prefer: null, preview: null, insertAt: null,
  exercise: null, transferSaved: false, why: null, arrange: "domain", view: "plain", handSize: 2, seq: saved.seq || 0,
  lens: { on: false, x: 0, y: 0, r: 120, spec: "evidence" }, panel: null, panelArg: null, returnFocus: null,
  experiments: saved.experiments || [], tried: saved.tried || [], seen: saved.seen || [], avoid: saved.avoid || [],
  groups: saved.groups || [], userParts: saved.userParts || [], importedStack: saved.importedStack || null, highlight: null,
};
const persist = () => { try { localStorage.setItem(STORE, JSON.stringify({ experiments: S.experiments, tried: S.tried, seen: S.seen, avoid: S.avoid, groups: S.groups, userParts: S.userParts, importedStack: S.importedStack, seq: S.seq })); } catch { /* the page still works without storage */ } };
const cam = { x: 0, y: 0, k: 1, tx: 0, ty: 0, tk: 1 };
const P = new Map();
const TW = 190, TH = 58, GX = 18, GY = 14, MH = 28;

const normal = r => ({ takes: [], gives: [], does: [], gates: [], unknown: [], sources: [], constraints: {}, evidence: "unknown", place: "mac", boundary: "local", domain: "memory", act: "", ...r,
  asThird: r.asThird || { adds: `what ${r.name} does`, then: r.act || "it changes the result" } });
function boot(firstTime) {
  const facts = { ...base.facts, resources: (S.importedStack || base.facts.resources).concat(S.userParts).map(normal) };
  E = createEngine({ ...base, facts });
  buildTokens();
  if (!firstTime) { layoutField(true); }
}

/* ---------- tokens ---------- */
function tokenHTML(r) {
  const ev = E.facts.evidence.find(x => x.id === r.evidence), bd = E.boundaryOf(r.id), pl = E.placeOf(r.id);
  return `<span class="port in ${r.takes.length ? "" : "none"}">${r.takes[0] ? glyph(r.takes[0].type) : ""}</span>
  <span class="t-name">${esc(r.name)}</span><span class="t-sub">${esc(r.does.slice(0, 3).join(" · "))}</span>
  <span class="fitnote">No verified route</span>
  <span class="t-face f-evidence">${esc(ev?.label || r.evidence)}</span><span class="t-face f-place">${esc(pl.label)}</span>
  <span class="t-face f-data">${esc(bd.label)}</span><span class="t-face f-cost">${esc(r.constraints.cost || "No cost on record")}</span>
  <span class="port out ${r.gives.length ? "" : "none"}">${r.gives[0] ? glyph(r.gives[0].type) : ""}</span>`;
}
function buildTokens() {
  const host = $("#tokens"), lens = $("#lensWorld");
  host.innerHTML = ""; lens.innerHTML = "";
  for (const r of E.facts.resources) {
    const b = document.createElement("button");
    b.className = "token"; b.dataset.id = r.id; b.dataset.ev = r.evidence; b.dataset.away = String(!E.boundaryOf(r.id).local);
    b.innerHTML = tokenHTML(r);
    b.setAttribute("aria-label", `${r.name}. ${r.act}.`);
    host.append(b);
    const c = b.cloneNode(true); c.tabIndex = -1; lens.append(c);
    const p = P.get(r.id) || { x: 0, y: 0, tx: 0, ty: 0 };
    p.el = b; p.clone = c; P.set(r.id, p);
  }
}
function clusterKey(r) {
  switch (S.arrange) {
    case "place": return E.placeOf(r.id).label;
    case "gives": return E.facts.types.find(t => t.id === r.gives[0]?.type)?.label || "Gives nothing yet";
    case "evidence": return E.facts.evidence.find(e => e.id === r.evidence)?.label || r.evidence;
    case "groups": return S.groups.find(g => g.members.includes(r.id))?.name || "Not grouped";
    default: return E.facts.domains.find(d => d.id === r.domain)?.label || r.domain;
  }
}
function clusters() {
  const m = new Map();
  for (const r of E.facts.resources) { const k = clusterKey(r); (m.get(k) || m.set(k, []).get(k)).push(r.id); }
  return [...m].map(([label, ids]) => ({ label, ids }));
}
// One side column: the stack rail and the panels share it, so opening a panel never takes width from the route.
const sideW = () => innerWidth >= 1180 ? 372 : 320;
function usableWidth() { return innerWidth - (S.panel && !isNarrow() ? sideW() : 0); }
function syncSide() {
  const side = sideW(), open = !!S.panel && !isNarrow(), st = document.documentElement.style;
  st.setProperty("--side", side + "px"); st.setProperty("--mw", (side - 30) / 2 + "px");
  document.body.classList.toggle("side-open", open); $("#tokens").inert = open && S.mode === "table";
}
function layoutField(jump) {
  syncSide();
  const W = Math.max(usableWidth() - 48, TW * 2 + GX), top = isNarrow() ? 112 : 120;
  const host = $("#clusters"); host.innerHTML = "";
  let x = 24, y = top, rowH = 0, right = 0;
  for (const c of clusters()) {
    const maxCols = Math.max(1, Math.floor(W / (TW + GX))), cols = Math.min(maxCols, Math.ceil(c.ids.length / 4)), rows = Math.ceil(c.ids.length / cols);
    const w = cols * (TW + GX), h = 26 + rows * (TH + GY) + 22;
    if (x + w > W + 24 && x > 24) { x = 24; y += rowH; rowH = 0; }
    const label = document.createElement("div"); label.className = "cluster"; label.textContent = c.label; label.style.transform = `translate(${x + 10}px,${y}px)`; host.append(label);
    c.ids.forEach((id, i) => { const p = P.get(id); p.tx = x + 10 + (i % cols) * (TW + GX); p.ty = y + 26 + Math.floor(i / cols) * (TH + GY); });
    x += w + 14; rowH = Math.max(rowH, h); right = Math.max(right, x);
  }
  const bottom = y + rowH + 90, vh = innerHeight - 52;
  let k = Math.min(1, W / Math.max(right, 1));
  if (!isNarrow()) k = Math.min(k, Math.max(.62, vh / bottom));
  cam.tk = k; cam.tx = 0; cam.ty = 0;
  if (jump) { for (const p of P.values()) { p.x = p.tx; p.y = p.ty; } cam.k = cam.tk; cam.x = cam.tx; cam.y = cam.ty; }
  kick();
}
function layoutRail(toTop) {
  syncSide();
  const inUse = new Set(S.route?.parts), side = sideW(), mw = (side - 30) / 2, x0 = innerWidth - side + 12, ids = clusters().flatMap(c => c.ids).filter(i => !inUse.has(i));
  ids.forEach((id, i) => { const p = P.get(id); p.tx = x0 + (i % 2) * (mw + 6); p.ty = 14 + Math.floor(i / 2) * (MH + 5); });
  $("#clusters").innerHTML = "";
  const t = $("#table");
  if (isNarrow()) { t.style.width = ""; t.style.transform = ""; }
  else { t.style.width = innerWidth - side - 28 + "px"; t.style.transform = "translate(14px,14px)"; }
  cam.tk = 1; cam.tx = 0; if (toTop) { cam.ty = 0; cam.k = 1; cam.x = 0; cam.y = 0; paint(); } kick();
}

/* ---------- animation loop ---------- */
let running = false, dirtyWires = true;
function kick() { dirtyWires = true; if (!running) { running = true; requestAnimationFrame(tick); } }
function tick() {
  const f = calm.matches ? 1 : .24; let moving = false;
  for (const p of P.values()) {
    if (p.drag) continue;
    const dx = p.tx - p.x, dy = p.ty - p.y;
    if (Math.abs(dx) + Math.abs(dy) > .4) { p.x += dx * f; p.y += dy * f; moving = true; } else { p.x = p.tx; p.y = p.ty; }
  }
  for (const k of ["x", "y", "k"]) { const t = cam["t" + k], d = t - cam[k]; if (Math.abs(d) > (k === "k" ? .001 : .4)) { cam[k] += d * f; moving = true; } else cam[k] = t; }
  paint(); if (moving) requestAnimationFrame(tick); else running = false;
}
function paint() {
  const vp = $("#viewport"), tf = `translate(${cam.x}px,${cam.y}px) scale(${cam.k})`;
  $("#world").style.transform = tf; $("#lensWorld").style.transform = tf;
  vp.style.backgroundPosition = `${cam.x}px ${cam.y}px`; vp.style.backgroundSize = `${24 * cam.k}px ${24 * cam.k}px`;
  $("#tokens").classList.toggle("far", cam.k < .72); $("#lensWorld").classList.toggle("far", cam.k < .72);
  $("#tokens").style.transform = S.mode === "table" ? `translateY(${-cam.y}px)` : "";
  for (const p of P.values()) { const t = `translate(${p.x}px,${p.y}px)`; p.el.style.transform = t; p.clone.style.transform = t; }
  if (dirtyWires) drawFieldWires();
}
function center(id) { const p = P.get(id); return p ? { x: p.x + TW / 2, y: p.y + TH / 2 } : null; }
function drawFieldWires() {
  const svg = $("#wires"); let html = "";
  if (S.mode === "field") {
    for (const ex of S.experiments) {
      const pts = ex.parts.map(center).filter(Boolean); if (pts.length < 2) continue;
      html += `<path class="trail ${S.highlight === ex.id ? "on" : ""}" d="M${pts.map(p => `${p.x} ${p.y}`).join("L")}"/>`;
    }
    if (S.arrange === "groups") for (const g of S.groups) {
      const ps = g.members.map(id => P.get(id)).filter(Boolean); if (!ps.length) continue;
      const x0 = Math.min(...ps.map(p => p.x)) - 12, y0 = Math.min(...ps.map(p => p.y)) - 36, x1 = Math.max(...ps.map(p => p.x)) + TW + 12, y1 = Math.max(...ps.map(p => p.y)) + TH + 12;
      html += `<rect class="hull" fill="none" stroke="currentColor" rx="14" x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" style="color:var(--muted)"/>`;
    }
    if (band) html += `<path class="band" d="M${band.x0} ${band.y0}C${band.x0 + 60} ${band.y0} ${band.x1 - 60} ${band.y1} ${band.x1} ${band.y1}"/>`;
    if (marquee) html += `<rect fill="none" stroke="currentColor" stroke-dasharray="4 4" style="color:var(--accent)" x="${Math.min(marquee.x0, marquee.x1)}" y="${Math.min(marquee.y0, marquee.y1)}" width="${Math.abs(marquee.x1 - marquee.x0)}" height="${Math.abs(marquee.y1 - marquee.y0)}"/>`;
  }
  svg.innerHTML = html;
}

/* ---------- hand and fit overlay ---------- */
function showFit(fromId) {
  for (const [id, p] of P) {
    if (!fromId || id === fromId || S.hand.includes(id) || S.mode !== "field") { delete p.el.dataset.fit; continue; }
    p.el.dataset.fit = E.fit(fromId, id).kind;
  }
}
function renderHand() {
  const el = $("#hand"), h = S.hand;
  for (const [id, p] of P) { const on = h.includes(id); p.el.classList.toggle("picked", on); p.el.setAttribute("aria-pressed", on); p.clone.classList.toggle("picked", on); }
  showFit(h[h.length - 1]);
  if (S.mode !== "field" || !h.length) { el.hidden = true; return; }
  el.hidden = false;
  if (S.naming) {
    el.innerHTML = `<label>Name this group <input id="groupName" class="search" style="width:190px" placeholder="For example: things that listen"></label><button class="primary" data-act="saveGroup">Keep group</button><button data-act="cancelGroup">Cancel</button>`;
    $("#groupName").focus(); return;
  }
  const names = h.map(id => `<span class="chip">${esc(E.res(id).name)}</span>`).join('<span class="sep">→</span>');
  el.innerHTML = h.length === 1
    ? `${names}<span class="sep">Rings show a shape fit. Pick any number more.</span><button data-act="agent" data-scope="part" data-id="${h[0]}">Prompt</button><button data-act="clearHand">Clear</button>`
    : `${names}<button class="primary" id="connectBtn" data-act="connectHand">Connect ${h.length} parts</button><button data-act="groupHand">Group</button><button data-act="agent" data-scope="parts">Prompt</button><button data-act="clearHand">Clear</button>`;
}
function togglePick(id) {
  const i = S.hand.indexOf(id);
  if (i >= 0) S.hand.splice(i, 1); else if (S.hand.length < 5) S.hand.push(id); else toast("Five parts is the limit here. A longer route may be two routes.");
  renderHand();
}

/* ---------- route lifecycle ---------- */
function connect(parts, { mode = "chain", exercise = null, keepIdea = false } = {}) {
  const from = parts.map(id => P.get(id)?.el.getBoundingClientRect());
  S.route = { parts: [...parts], mode }; S.hand = []; S.revealed = false; S.rejected = []; S.prefer = null; S.preview = null;
  S.exercise = exercise; S.transferSaved = false; S.why = S.why && exercise ? S.why : null; S.sketching = false;
  if (!keepIdea) S.idea = { text: "", sketch: null };
  const key = E.handKey(parts); if (!S.seen.includes(key)) S.seen.push(key);
  persist(); setMode("table"); renderHand();
  if (!calm.matches) $$(".part").forEach(el => { const r = from[S.route.parts.indexOf(el.dataset.id)]; if (!r || !r.width) return; const t = el.getBoundingClientRect();
    el.animate([{ transform: `translate(${r.left - t.left}px,${r.top - t.top}px)`, opacity: .4 }, { transform: "none", opacity: 1 }], { duration: 320, easing: "cubic-bezier(.2,.7,.2,1)" }).finished.then(drawRoute, () => {}); });
  $("#ideaText")?.focus({ preventScroll: true });
  syncHash();
}
function setMode(m) {
  S.mode = m; document.body.dataset.mode = m; const inTable = m === "table";
  $("#table").hidden = !inTable; $("#backBtn").hidden = !inTable;
  for (const [id, p] of P) { p.el.classList.toggle("mini", inTable); p.clone.classList.toggle("mini", inTable); const used = inTable && S.route.parts.includes(id); p.el.classList.toggle("used", used); p.clone.classList.toggle("used", used); }
  if (inTable) { renderTable(); layoutRail(true); fitRoute($("#route")); } else { $("#table").innerHTML = ""; layoutField(false); }
  kick();
}
function backToField() {
  const was = { route: S.route, idea: S.idea, revealed: S.revealed, exercise: S.exercise };
  S.route = null; S.exercise = null; setMode("field"); syncHash();
  if (was.idea.text.trim() || was.idea.sketch) toast("Left the route.", "Return to it", () => { connect(was.route.parts, { mode: was.route.mode, exercise: was.exercise, keepIdea: true }); S.idea = was.idea; S.revealed = was.revealed; renderTable(); });
}
function syncHash() {
  const h = S.route ? `#r=${S.route.parts.join(",")}&m=${S.route.mode}` : " ";
  try { history.replaceState(null, "", h === " " ? location.pathname : h); } catch { /* file preview */ }
}
function markTried() { if (!S.revealed) return; const s = E.shapeOf(S.route); const need = E.rules.shapes.find(x => x.id === s)?.needs || 2; if (S.route.parts.length >= need && !S.tried.includes(s)) { S.tried.push(s); persist(); } }
function routeChanged(msg) {
  S.rejected = []; S.preview = null; markTried(); renderTable(); layoutRail();
  for (const [id, p] of P) { const used = S.route.parts.includes(id); p.el.classList.toggle("used", used); p.clone.classList.toggle("used", used); }
  if (msg) toast(msg); syncHash();
}
function addPart(id, at = S.insertAt) {
  if (!S.route) return;
  if (S.route.parts.includes(id)) return toast(`${E.res(id).name} is already in this route.`);
  if (S.route.parts.length >= 5) return toast("Five parts is the limit here. A longer route may be two routes.");
  const p = S.route.parts; p.splice(at ?? p.length, 0, id); S.insertAt = null;
  routeChanged(`${E.res(id).name} added. Compare what changed in each bridge.`);
}

/* ---------- table ---------- */
function exerciseBar() {
  if (!S.exercise) return "";
  const x = E.rules.exercises.find(e => e.id === S.exercise);
  const rule = S.exercise === "distant" ? `<button data-act="notDistant">These aren’t distant to me</button>` : "";
  return `<div class="exbar"><b>${esc(x.name)}</b><span>${esc(x.ask)}</span>${rule}<button data-act="startExercise" data-id="${x.id}">Another one</button><button data-act="endExercise">End practice</button></div>`;
}
function partCard(id, removable) {
  const r = E.res(id), ev = E.facts.evidence.find(e => e.id === r.evidence);
  const list = a => a.length ? a.map(x => esc(x.label)).join("; ") : "nothing; it only observes";
  return `<article class="part" data-id="${id}"><h3>${esc(r.name)}</h3>
    ${removable ? `<button class="x" data-act="removePart" data-id="${id}" aria-label="Remove ${esc(r.name)} from the route" title="Remove">×</button>` : ""}
    <dl><dt>Takes</dt><dd>${list(r.takes)}</dd><dt>Does</dt><dd>${esc(r.act)}</dd><dt>Gives</dt><dd>${r.gives.length ? list(r.gives) : "nothing yet"}</dd></dl>
    <div class="meta">${esc(E.placeOf(id).label)} · ${esc(ev?.label || r.evidence)}</div>
    <button class="more" data-act="openPart" data-id="${id}">Evidence and limits</button></article>`;
}
function renderTable() {
  const t = $("#table"), { parts, mode } = S.route, rm = parts.length > 2;
  let cards;
  if (mode === "fanin" && parts.length > 2) cards = `<div class="col">${parts.slice(0, -1).map(p => partCard(p, rm)).join("")}</div>${partCard(parts[parts.length - 1], rm)}`;
  else if (mode === "fanout" && parts.length > 2) cards = `${partCard(parts[0], rm)}<div class="col">${parts.slice(1).map(p => partCard(p, rm)).join("")}</div>`;
  else cards = parts.map(p => partCard(p, rm)).join("");
  const v = E.view(S.route), gaps = v.hops.filter(h => h.fit.kind === "gap");
  const head = parts.length === 2 ? "What could these two do together?" : `What could these ${parts.length} do together?`;
  t.innerHTML = `${exerciseBar()}
    <div class="tb-head"><h2>${esc(head)}</h2></div>
    <div class="route" id="route" data-mode="${mode}" data-n="${parts.length}"><svg class="rw" id="rw" aria-hidden="true"></svg>${cards}</div>
    ${gaps.map(g => `<p class="gapnote">${esc(g.fit.statement)}</p>`).join("")}
    <div class="tools" id="tools"></div>
    <div class="idea ${S.revealed ? "done" : ""}" id="idea"></div>
    <div id="bridges"></div>`;
  renderTools(); renderIdea(); renderBridges();
  requestAnimationFrame(drawRoute);
}
function renderTools() {
  const nud = E.nudge(S.tried), cur = E.shapeOf(S.route), n = S.route.parts.length;
  const shapes = nud.shapes.map(s => `<button data-act="setShape" data-id="${s.id}" aria-pressed="${cur === s.id}" class="${s.tried ? "tried" : ""}" title="${esc(s.invite)}" aria-label="${esc(s.name)}${s.tried ? ", tried" : ""}"><svg viewBox="-1 0 28 18" aria-hidden="true">${SHAPE_ICON[s.id]}</svg>${esc(s.name)}</button>`).join("");
  const next = nud.next && nud.next.id !== cur ? nud.next : null;
  const canSwap = E.swapsFor(S.route.parts).length > 0;
  $("#tools").innerHTML = `<div class="shapes" role="group" aria-label="Shape of this route">${shapes}</div>
    <button class="ghost" id="addBtn" data-act="openAdder" ${n >= 5 ? "disabled" : ""} title="Add a part (T)">Add a part</button>
    <button class="ghost" id="revBtn" data-act="reverse" title="Reverse (R)">Reverse</button>
    <button class="ghost" id="swapBtn" data-act="openSwaps" ${canSwap ? "" : "disabled"}>Swap a part</button>
    <button class="ghost" id="routePrompt" data-act="agent" data-scope="route" title="Prompt for an agent (Q)">Prompt an agent</button>
    ${next ? `<p class="nudge" id="nudge">Not tried yet: <button data-act="setShape" data-id="${next.id}">${esc(next.name)}</button>. ${esc(next.invite)}</p>` : ""}`;
}
function renderIdea() {
  const el = $("#idea"), tr = S.exercise === "transfer", mid = S.exercise === "middle";
  const label = mid ? "What transformation is missing in the middle?" : tr ? "Your bridge, unaided" : "Your idea first";
  const has = S.idea.text.trim() || S.idea.sketch;
  el.classList.toggle("done", S.revealed);
  el.innerHTML = `<label for="ideaText">${esc(label)}</label>
    <textarea id="ideaText" placeholder="${tr ? "No examples here. What would you build?" : "One rough sentence is enough."}"${S.sketching ? " hidden" : ""}>${esc(S.idea.text)}</textarea>
    <canvas id="sketch" width="520" height="150" aria-label="Sketch area"${S.sketching ? "" : " hidden"}></canvas>
    <div class="row"><button class="ghost" data-act="toggleSketch">${S.sketching ? "Write instead" : "Sketch instead"}</button>
      ${S.sketching ? `<button class="ghost" data-act="clearSketch">Clear sketch</button>` : ""}
      <button class="ghost" id="keepIdea" data-act="experimentMine" ${has ? "" : "disabled"}>${tr ? "Save my bridge" : "Keep my idea"}</button>
      ${S.revealed ? "" : `<button class="primary" id="revealBtn" data-act="reveal" ${has && (!tr || S.transferSaved) ? "" : "disabled"}>${tr ? "Compare with examples" : "Show other bridges"}</button>`}</div>
    ${S.revealed ? "" : `<p class="note" id="ideaNote">${tr ? (S.transferSaved ? "Saved. Now you can compare." : "Save your bridge first. Examples stay hidden until then.") : "Nothing here is graded. Examples stay hidden until you have put something down."}</p>`}`;
  $("#ideaText").addEventListener("input", e => { S.idea.text = e.target.value; refreshIdeaButtons(); });
  if (S.sketching) setupSketch();
}
function refreshIdeaButtons() {
  const has = !!(S.idea.text.trim() || S.idea.sketch), tr = S.exercise === "transfer";
  const r = $("#revealBtn"); if (r) r.disabled = !has || (tr && !S.transferSaved);
  const k = $("#keepIdea"); if (k) k.disabled = !has;
}
function setupSketch() {
  const c = $("#sketch"), g = c.getContext("2d"); c.width = c.clientWidth || 520; c.height = 150;
  const ink = getComputedStyle(document.body).color; g.lineWidth = 2; g.lineCap = "round"; g.strokeStyle = ink;
  if (S.idea.sketch) { const i = new Image(); i.onload = () => g.drawImage(i, 0, 0); i.src = S.idea.sketch; }
  let on = false; const at = e => { const r = c.getBoundingClientRect(); return [(e.clientX - r.left) * c.width / r.width, (e.clientY - r.top) * c.height / r.height]; };
  c.onpointerdown = e => { on = true; c.setPointerCapture(e.pointerId); g.beginPath(); g.moveTo(...at(e)); e.stopPropagation(); };
  c.onpointermove = e => { if (on) { g.lineTo(...at(e)); g.stroke(); } };
  c.onpointerup = () => { if (on) { on = false; S.idea.sketch = c.toDataURL(); refreshIdeaButtons(); } };
}
// Density follows the width the route has, so no card drops below a legible size.
function fitRoute(host) {
  const { parts, mode } = S.route, n = parts.length, cols = (mode === "fanin" || mode === "fanout") && n > 2 ? 2 : n;
  const gap = cols === 2 ? 120 : cols === 3 ? 88 : 56, per = g => (host.clientWidth - (cols - 1) * g) / cols;
  host.dataset.fit = isNarrow() ? "stack" : per(gap) >= 210 ? "full" : per(56) >= 128 ? "compact" : "stack";
  host.style.setProperty("--gap", (host.dataset.fit === "full" ? gap : 56) + "px");
}
function drawRoute() {
  const host = $("#route"); if (!host) return;
  $$(".hop,.slot", host).forEach(n => n.remove());
  fitRoute(host);
  const vertical = host.dataset.fit === "stack", fan = vertical && S.route.parts.length > 2 && (S.route.mode === "fanin" || S.route.mode === "fanout");
  const box = id => { let el = $(`.part[data-id="${id}"]`, host), l = 0, t = 0; const w = el.offsetWidth, h = el.offsetHeight; while (el && el !== host) { l += el.offsetLeft; t += el.offsetTop; el = el.offsetParent; } return { l, t, r: l + w, b: t + h }; };
  const hops = E.hopsOf(S.route); let svg = "";
  hops.forEach((h, i) => {
    const a = box(h.from), b = box(h.to), m = E.middleOf(h); let d, mx, my;
    if (h.role === "return") {
      if (vertical) { const x = a.r + 22; d = `M${a.r} ${(a.t + a.b) / 2}C${x} ${(a.t + a.b) / 2} ${x} ${(b.t + b.b) / 2} ${b.r} ${(b.t + b.b) / 2}`; mx = x - 5; my = (a.t + a.b + b.t + b.b) / 4; }
      else { const y = Math.max(a.b, b.b) + 40, ax = (a.l + a.r) / 2, bx = (b.l + b.r) / 2; d = `M${ax} ${a.b}C${ax} ${y} ${bx} ${y} ${bx} ${b.b}`; mx = (ax + bx) / 2; my = Math.max(a.b, b.b) + 30; }
    } else if (fan) {
      // Stacked fans run down a side gutter, so a hop never sits on a neighbouring card.
      const ya = (a.t + a.b) / 2, yb = (b.t + b.b) / 2, x = Math.max(a.r, b.r) + 26; d = `M${a.r} ${ya}C${x} ${ya} ${x} ${yb} ${b.r} ${yb}`; mx = x - 6; my = S.route.mode === "fanin" ? ya : yb;
    } else if (vertical) {
      const x0 = (a.l + a.r) / 2, x1 = (b.l + b.r) / 2; d = `M${x0} ${a.b}C${x0} ${a.b + 20} ${x1} ${b.t - 20} ${x1} ${b.t}`; mx = (x0 + x1) / 2; my = (a.b + b.t) / 2;
    } else {
      const y0 = (a.t + a.b) / 2, y1 = (b.t + b.b) / 2, c = Math.max(24, (b.l - a.r) / 2); d = `M${a.r} ${y0}C${a.r + c} ${y0} ${b.l - c} ${y1} ${b.l} ${y1}`; mx = (a.r + b.l) / 2; my = (y0 + y1) / 2;
    }
    svg += `<path class="${m.state}" d="${d}"/>`;
    const btn = document.createElement("button");
    btn.className = `hop ${m.state}`; btn.style.left = mx + "px"; btn.style.top = my + "px"; btn.dataset.act = "openHop"; btn.dataset.i = i;
    btn.textContent = { direct: "=", gap: "×" }[m.state] || "?";
    btn.setAttribute("aria-label", `Hop from ${E.res(h.from).name} to ${E.res(h.to).name}: ${m.state === "direct" ? "shapes match" : m.state === "gap" ? "no verified route" : "a middle is missing"}`);
    host.append(btn);
    if (S.route.mode === "chain" || S.route.mode === "loop") if (h.role !== "return" && S.route.parts.length < 5) {
      const s = document.createElement("button"); s.className = "slot"; s.textContent = "+"; s.dataset.act = "openAdder"; s.dataset.at = i + 1;
      s.style.left = (vertical ? mx + 34 : mx) + "px"; s.style.top = (vertical ? my : my - 30) + "px";
      s.setAttribute("aria-label", `Add a part between ${E.res(h.from).name} and ${E.res(h.to).name}`); host.append(s);
    }
  });
  $("#rw").innerHTML = svg;
}
function currentView() {
  const route = S.preview ? { ...S.route, parts: [...S.route.parts, S.preview] } : S.route;
  return E.view(route, { constraints: S.constraints, rejected: S.rejected, prefer: S.prefer });
}
function plankHTML(p) {
  const o = p.offer && E.offer(p.offer), missing = p.middles.filter(m => m.state === "missing").length, hops = p.middles.length;
  const sym = { direct: "=", missing: "?", gap: "×", none: "·" };
  const steps = p.middles.map(m => `<li><span class="st" aria-hidden="true">${sym[m.state]}</span><span>${esc(m.label)}</span></li>`).join("");
  const effects = p.effects.map(e => `<p class="eff ${e.inert ? "inert" : ""}">${esc(e.authored ? `${E.res(e.id).name} adds ${e.adds}.` : e.text)}</p>`).join("");
  const showBefore = p.effects.some(e => e.authored) && p.base !== p.outcome;
  return `<article class="plank ${S.preview ? "preview" : ""}" data-id="${esc(p.id)}" data-kind="${p.kind}">
    <div class="kind"><span>${KIND_LABEL[p.kind]}</span><span>${esc(p.goal)}</span></div>
    <h3>${esc(p.title)}</h3><p class="outcome">${esc(p.outcome)}</p>
    ${showBefore ? `<p class="before">Before: ${esc(p.base)}</p>` : ""}${effects}
    ${p.shapeNote ? `<p class="eff">${esc(p.shapeNote)}</p>` : ""}
    ${p.changed ? `<p class="changed">${esc(p.changed)}</p>` : ""}
    <ul class="steps" aria-label="The middle">${steps}</ul>
    ${o ? `<p class="price">${esc(o.prices[0].label)}, ${esc(o.name)}</p>` : ""}
    <div class="tag">${hops} ${hops === 1 ? "hop" : "hops"}, ${missing} to build. ${p.origin === "seed" ? "Authored example" : "Rule-made example"}. Proposal, not run.</div>
    ${S.preview ? "" : `<div class="acts"><button class="ghost" data-act="why" data-id="${esc(p.id)}">Why this?</button><button class="ghost" data-act="agent" data-scope="bridge" data-id="${esc(p.id)}">Prompt</button><button class="ghost" data-act="reject" data-id="${esc(p.id)}">Not this</button><button class="primary" data-act="experiment" data-id="${esc(p.id)}">Make it an experiment</button></div>`}
  </article>`;
}
function renderBridges() {
  const host = $("#bridges"); if (!host) return;
  if (!S.revealed) { host.innerHTML = ""; return; }
  const v = currentView(), c = S.constraints;
  const emptyLine = v.shown.length ? "" : `<p class="gapnote" id="noBridge">No example survives here. That may be the honest answer, or the bridge may be yours alone. Your idea above still counts.</p>`;
  const noRule = v.empty.includes("practical") && v.shown.length ? `<p class="tag">No practical route from the rules: ${esc(E.rules.fit.none)}</p>` : "";
  host.innerHTML = `<div style="display:grid;gap:12px">
    <form class="cons" id="cons" aria-label="Constraints"><label><input type="checkbox" name="local" ${c.local ? "checked" : ""}> Keep data local</label>
      <fieldset><legend>Spending</legend>
      <label><input type="radio" name="spend" value="any" ${c.spend === "any" ? "checked" : ""}> Show everything</label>
      <label><input type="radio" name="spend" value="none" ${c.spend === "none" ? "checked" : ""}> Use what I already have</label>
      <label><input type="radio" name="spend" value="budget" ${c.spend === "budget" ? "checked" : ""}> One small purchase up to USD <input type="number" name="budget" min="0" max="100" step="1" value="${c.budget}" aria-label="Monthly budget in USD"> a month</label></fieldset></form>
    ${S.preview ? `<p class="tag">If you add ${esc(E.res(S.preview).name)}:</p>` : ""}
    <div class="planks" id="planks">${v.shown.map(plankHTML).join("")}</div>${emptyLine}${noRule}
    <div class="cuts" id="cuts">${v.cut.length ? `<h3>Removed by your constraints</h3><ul>${v.cut.map(x => `<li><b>${esc(x.plank.title)}</b> ${esc(x.why.map(w => w.text).join(" "))}</li>`).join("")}</ul>` : ""}
      ${S.rejected.length ? `<button class="ghost" data-act="restore">Bring back what I set aside</button>` : ""}</div></div>`;
  $("#cons").addEventListener("change", onCons); $("#cons").addEventListener("submit", e => e.preventDefault());
}
function onCons(e) {
  const f = new FormData($("#cons"));
  S.constraints = { local: f.get("local") === "on", spend: f.get("spend"), budget: Math.max(0, Number(f.get("budget")) || 0) };
  const n = e.target.name; renderBridges(); $(`#cons [name="${n}"]${n === "spend" ? ":checked" : ""}`)?.focus();
}

/* ---------- panels ---------- */
function openPanel(name, arg) {
  if (!S.panel) S.returnFocus = document.activeElement;
  S.panel = name; S.panelArg = arg; const el = $("#panel"); el.hidden = false;
  el.innerHTML = `<button class="close" data-act="closePanel" aria-label="Close panel">×</button>` + PANELS[name](arg);
  el.scrollTop = 0; el.focus({ preventScroll: true });
  if (name === "parts") { $("#partSearch")?.focus(); filterParts(); }
  relayout();
}
function closePanel() { S.panel = null; S.insertAt = null; $("#panel").hidden = true; relayout(); if (S.returnFocus?.isConnected) S.returnFocus.focus({ preventScroll: true }); S.highlight = null; kick(); }
function relayout() { if (S.mode === "table") { layoutRail(); requestAnimationFrame(drawRoute); } else layoutField(false); }
const sourceLine = id => { const s = E.facts.sources[id]; if (!s) return ""; return `<li class="src">${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}, checked ${fmtDate(s.checked)}<br>${esc(s.where)}</li>`; };
const gatesHTML = r => r.gates.map(g => `<div class="gate"><span class="s ${g.state}">${{ pass: "seen", fail: "absent", partial: "partly", unknown: "unknown" }[g.state]}</span><span><b>${esc(g.label)}</b><br>${esc(g.detail)}</span></div>`).join("") || "<p>No access evidence recorded.</p>";
const PANELS = {
  part(id) {
    const r = E.res(id), ev = E.facts.evidence.find(e => e.id === r.evidence), c = r.constraints;
    const row = (k, v) => v ? `<li><b>${k}:</b> ${esc(v)}</li>` : "";
    const canAdd = S.mode === "table" && !S.route.parts.includes(id);
    return `<h2>${esc(r.name)}</h2><p>It ${esc(r.act)}.</p>
      <p class="acts">${canAdd ? `<button class="primary" id="addThis" data-act="addPart" data-id="${id}">Add to this route</button>` : ""}<button class="ghost" data-act="agent" data-scope="part" data-id="${id}">Prompt an agent</button></p>
      <h3>Takes, does, gives</h3><ul><li>Takes: ${r.takes.map(t => esc(t.label)).join("; ") || "nothing; it only observes"}</li><li>Does: ${esc(r.does.join(", "))}</li><li>Gives: ${r.gives.map(t => esc(t.label)).join("; ") || "nothing yet"}</li></ul>
      <h3>Runs here</h3><p>${esc(E.placeOf(id).label)}. ${esc(E.boundaryOf(id).label)}.</p>
      <h3>Access evidence: ${esc(ev?.label || r.evidence)}</h3><p class="src">${esc(ev?.meaning)}</p>${gatesHTML(r)}
      ${id === "nous" ? catalogNous() : id === "nvidia" ? catalogNvidia() : ""}
      <h3>Constraints</h3><ul>${row("Authentication", c.auth)}${row("Data", c.data)}${row("Dependencies", c.deps)}${row("Freshness", c.freshness)}${row("Latency", c.latency || "Not measured")}${row("Cost and limits", c.cost)}</ul>
      <h3>Still unknown</h3><ul>${r.unknown.map(u => `<li>${esc(u)}</li>`).join("") || "<li>Nothing recorded</li>"}</ul>
      <h3>Sources</h3><ul class="list">${r.sources.map(sourceLine).join("")}</ul>`;
  },
  hop(i) {
    const h = E.hopsOf(S.route)[i], m = E.middleOf(h), a = E.res(h.from), b = E.res(h.to), f = h.fit;
    const showMiddle = S.revealed && m.state === "missing";
    return `<h2>${esc(a.name)} → ${esc(b.name)}</h2>
      ${f.kind === "gap" ? `<p class="gapnote">${esc(f.statement)}</p>` : ""}
      <p>${esc(a.name)} gives ${esc(f.give?.label || "nothing yet")}. ${esc(b.name)} takes ${esc(f.take?.label || "nothing here")}.</p>
      <p>${esc(E.rules.fit[f.kind] || "")}</p>
      ${showMiddle ? `<h3>The rule’s middle</h3><p>${esc(m.label)} (${esc(m.kind)}).</p>` : m.state === "missing" ? `<p class="src">The rule’s suggestion stays hidden until you have put your idea down.</p>` : ""}
      <p class="src">This is a type rule. It says nothing about whether the hop is worth making, and nothing here has been run.</p>
      <p><button class="ghost" data-act="agent" data-scope="hop" data-id="${i}">Prompt an agent about this hop</button></p>`;
  },
  why(id) {
    const p = findPlank(id); if (!p) return "<h2>No longer shown</h2>";
    const s = E.facts.sources[p.source];
    return `<h2>${esc(p.title)}</h2>
      <h3>Why this is suggested</h3><ul>${p.why.map(w => `<li>${esc(w)}</li>`).join("")}</ul>
      <p class="src">${p.origin === "seed" ? `Authored example${s ? ` from ${esc(s.title)}, ${fmtDate(s.checked)}` : ""}.` : "Made by a local rule from the two parts’ shapes. It is deterministic and does not know you."} It could be wrong for you.</p>
      <h3>What it needs</h3><p>${esc(p.dependency)}</p>
      <h3>The parts, as evidenced</h3><ul>${p.parts.map(id => { const r = E.res(id); return `<li><button class="more" data-act="openPart" data-id="${id}">${esc(r.name)}</button>: ${esc(E.facts.evidence.find(e => e.id === r.evidence)?.label)}, ${esc(E.placeOf(id).label)}</li>`; }).join("")}</ul>
      <h3>What remains unknown</h3><ul>${p.unknown.map(u => `<li>${esc(u)}</li>`).join("")}</ul>
      <h3>Smallest test</h3><p>${esc(p.test)}</p>
      <p class="src">No bridge in this stack has been run. ${esc(E.facts.meta.note)}</p>
      <p><button class="ghost" data-act="agent" data-scope="bridge" data-id="${esc(id)}">Prompt an agent about this bridge</button></p>`;
  },
  agent() {
    const c = S.agentDesc && agentCtx(S.agentDesc), from = S.agentFrom;
    const back = from ? `<button class="ghost backlink" data-act="agentBack">← ${esc(PANEL_BACK[from.name] || "Back")}</button>` : "";
    if (!c) return `${back}<h2>Prompt for an agent</h2><p>That is no longer on screen. Pick something and try again.</p>`;
    const intent = S.intent ||= "sources", tab = (k, l) => `<button role="radio" aria-checked="${intent === k}" data-act="intent" data-id="${k}">${l}</button>`;
    const blocked = c.mode && c.parts.length > 1 && E.hopsOf(c).some(h => h.fit.kind === "gap");
    return `${back}<h2>Prompt for an agent</h2><p class="src">About ${esc(E.promptSubject(c))}. Paste it into any agent. Bridgework sends nothing.</p>
      <div class="seg" role="radiogroup" aria-label="What the agent should do">${tab("sources", "Sources")}${tab("ideas", "Ideas")}${tab("build", "Build")}</div>
      <p class="src" id="intentNote">${INTENT_NOTE[intent]}</p>
      ${blocked ? `<p class="gapnote">This route has a blocked hop. The prompt says so, and a build prompt tells the agent to stop there.</p>` : ""}
      <div class="acts"><button class="primary" id="copyPrompt" data-act="copyPrompt">Copy prompt</button><button class="ghost" data-act="downloadPrompt">Download .md</button></div>
      <textarea id="promptText" aria-label="Prompt for the agent. You can edit it." spellcheck="false">${esc(E.promptFor(c, intent))}</textarea>
      <p class="src">You can edit this. Changing the tab starts it fresh.</p>`;
  },
  experiment(id) {
    const mine = id === "mine", p = mine ? null : findPlank(id), tr = S.exercise === "transfer";
    const mids = p ? p.middles.map(m => m.label).join("; then ") : "";
    const unknown = p ? p.unknown : [...new Set(S.route.parts.flatMap(x => E.res(x).unknown))];
    const parts = S.route.parts.map(x => E.res(x).name).join(" → ");
    const ta = (n, l, v, ph = "") => `<label>${l}<textarea name="${n}" rows="2" placeholder="${esc(ph)}">${esc(v)}</textarea></label>`;
    return `<h2>${mine ? "Keep your bridge" : "Make it an experiment"}</h2><p class="src">${esc(parts)}. Shape: ${esc(E.rules.shapes.find(s => s.id === E.shapeOf(S.route))?.name)}.</p>
      <form class="exp" id="expForm" data-id="${esc(id)}">
      ${ta("outcome", "Intended outcome", p ? p.outcome : S.idea.text, "What would be different?")}
      ${ta("bridge", "Bridge", mids, "What happens in the middle?")}
      ${ta("dependency", "Missing dependency", p ? p.dependency : "", "What has to exist first?")}
      ${ta("test", "Smallest test", p ? p.test : "", "The least you could do to find out")}
      ${ta("success", "What success would look like", p ? p.success : "", "How you would know")}
      ${ta("assumptions", "Assumptions to keep", unknown.join("\n"))}
      <p class="src">Evidence is saved as it stands today: ${S.route.parts.map(x => `${esc(E.res(x).name)} (${esc(E.res(x).evidence)})`).join(", ")}; observed ${fmtDate(E.facts.meta.observed_date)}.</p>
      <button class="primary" id="saveExp" type="submit">${tr && mine ? "Save my bridge" : "Save experiment"}</button></form>`;
  },
  practice() {
    return `<h2>Practice</h2><p class="src">These are proposed formats, not measured creativity training. Nothing is scored.</p>
      <ul class="list">${E.rules.exercises.map(x => `<li><button class="row" data-act="startExercise" data-id="${x.id}"><b>${esc(x.name)}</b><br><span class="src">${esc(x.ask)}</span></button></li>`).join("")}</ul>
      <h3>How pairs are drawn</h3><p class="src">${esc(E.rules.distance.rule)}</p>`;
  },
  parts() {
    const at = S.insertAt, adding = S.mode === "table";
    return `<h2>${adding ? (at != null && S.route.parts[at] ? `Add between ${esc(E.res(S.route.parts[at - 1]).name)} and ${esc(E.res(S.route.parts[at]).name)}` : "Add a part") : "Parts"}</h2>
      <input id="partSearch" class="search" type="search" placeholder="Filter by name or verb" aria-label="Filter parts">
      <ul class="list" id="partList">${E.facts.resources.map(r => `<li data-name="${esc((r.name + " " + r.does.join(" ") + " " + r.act).toLowerCase())}"><button class="row" data-act="${adding ? "addPart" : "pickFromList"}" data-id="${r.id}"><b>${esc(r.name)}</b><br><span class="src">${esc(r.act)}</span></button></li>`).join("")}</ul>
      <h3>Use your own stack</h3>
      <form class="addform" id="addForm"><input name="name" required placeholder="Name" aria-label="Name">
        <input name="act" required placeholder="What it does, in plain words" aria-label="What it does">
        <label class="src">Takes <select name="takes"><option value="">Nothing</option>${E.facts.types.map(t => `<option value="${t.id}">${esc(t.label)}</option>`).join("")}</select></label>
        <label class="src">Gives <select name="gives">${E.facts.types.map(t => `<option value="${t.id}">${esc(t.label)}</option>`).join("")}</select></label>
        <label class="src">Runs <select name="place">${E.facts.places.map(t => `<option value="${t.id}">${esc(t.label)}</option>`).join("")}</select></label>
        <label class="src">Evidence <select name="evidence">${E.facts.evidence.map(t => `<option value="${t.id}">${esc(t.label)}</option>`).join("")}</select></label>
        <button class="ghost" type="submit">Add this part</button></form>
      <p><label class="src">Replace this stack with a stack file (.json, same shape as data/facts.json resources) <input type="file" id="stackFile" accept="application/json"></label></p>
      ${S.importedStack || S.userParts.length ? `<button class="ghost" data-act="resetStack">Return to the original stack</button>` : ""}`;
  },
  swaps() {
    const list = E.swapsFor(S.route.parts);
    return `<h2>Swap a part</h2><p class="src">A trade-off, not an upgrade.</p>
      ${list.map((s, i) => `<div class="opp"><h3>${esc(E.res(s.from).name)} → ${esc(E.res(s.to).name)}</h3><p>${esc(s.label)}</p>
      <div class="chain"><div><span>You gain</span><b>${esc(s.gain)}</b></div><div><span>You lose</span><b>${esc(s.loss)}</b></div><div><span>Unknown</span><b>${esc(s.unknown)}</b></div></div>
      <div class="acts"><button class="ghost" data-act="applySwap" data-i="${i}">Swap it in</button><button class="ghost" data-act="agent" data-scope="swap" data-id="${i}">Prompt</button></div></div>`).join("")}`;
  },
  unlocks() {
    const b = S.constraints.budget, led = E.ledger(b), name = id => esc(E.res(id)?.name || id);
    const KIND = { "new-capability": "New capability", "more-quota": "More quota", grant: "Free grant", glue: "Glue, no new fee" };
    const card = o => { const d = o.offerData; return `<div class="opp ${o.fits ? "" : "out"}" data-offer="${d.id}" data-fits="${o.fits}"><h3>${esc(o.outcome)}</h3>
      <p class="src">${KIND[d.kind]}. ${esc(o.change)}</p>
      <div class="chain"><div><span>Goal</span><b>${esc(o.goal)}</b></div><div><span>Useful outcome</span><b>${esc(o.outcome)}</b></div><div><span>Existing pieces</span><b>${o.existing.map(name).join(", ")}</b></div><div><span>Missing</span><b>${esc(o.missing)}</b></div><div><span>Candidate</span><b>${esc(d.name)}</b></div><div><span>Smallest test</span><b>${esc(o.test)}</b></div><div><span>Setup</span><b>${esc(d.setup)}</b></div><div><span>Depends on</span><b>${esc(d.dependencies.join("; "))}</b></div></div>
      <ul>${d.prices.map(p => `<li>${esc(p.label)} <span class="tag">${esc(p.basis)}</span></li>`).join("")}</ul>
      <p class="src">${esc(d.conditions)}</p>${o.fits ? "" : `<p>${esc(o.rejected.map(r => r.why).join(" "))}</p>`}
      <p class="src">${d.url ? `<a href="${esc(d.url)}" target="_blank" rel="noopener">Official pricing</a>, checked ${fmtDate(d.checked)}` : `From ${esc(E.facts.sources[d.source]?.title)}, ${fmtDate(d.checked)}`}</p>
      <div class="acts">${o.bridge ? `<button class="ghost" data-act="loadOpp" data-id="${o.id}">Try this on the canvas</button>` : ""}<button class="ghost" data-act="agent" data-scope="opportunity" data-id="${o.id}">Prompt</button></div></div>`; };
    return `<h2>What a small addition unlocks</h2>
      <p><label>Monthly budget, USD <input id="ledgerBudget" type="number" min="0" max="100" value="${b}" style="width:70px"></label></p>
      <p class="src">${esc(E.costs.meta.note)} One-time candidates appear here when the stack has them.</p>
      <h3>Within USD ${b} a month</h3>${led.filter(o => o.fits).map(card).join("")}
      <h3>Outside it</h3>${led.filter(o => !o.fits).map(card).join("") || "<p>Nothing.</p>"}`;
  },
  trail() {
    const nud = E.nudge(S.tried);
    return `<h2>Your trail</h2><p class="src">Saved experiments keep their assumptions and the evidence as it stood. On the stack they appear as dotted proposals, not connections.</p>
      <p class="src">Shapes you have tried: ${nud.shapes.filter(s => s.tried).map(s => esc(s.name)).join(", ") || "none yet"}.${nud.next ? ` Next invitation: ${esc(nud.next.name)}.` : ""}</p>
      ${S.experiments.length ? `<ul class="list" id="trailList">${S.experiments.map(x => `<li data-exp="${x.id}"><b>${esc(x.outcome || "Untitled")}</b>
        <p class="src">${esc(x.names.join(" → "))}. ${esc(x.shapeName)}. ${esc(x.origin)}.</p>
        <p class="src"><b>Bridge:</b> ${esc(x.bridge || "not stated")}<br><b>Missing:</b> ${esc(x.dependency || "not stated")}<br><b>Smallest test:</b> ${esc(x.test || "not stated")}<br><b>Success:</b> ${esc(x.success || "not stated")}<br><b>Assumptions:</b> ${esc(x.assumptions || "none recorded")}<br><b>Evidence at save:</b> ${esc(x.evidence.map(e => `${e.name}: ${e.state}`).join("; "))}, observed ${esc(x.observed)}<br><b>Constraints:</b> ${esc(x.constraintText)}</p>
        ${x.idea ? `<p class="src"><b>Your idea:</b> ${esc(x.idea)}</p>` : ""}${x.sketch ? `<img src="${x.sketch}" alt="Your sketch" style="max-width:100%">` : ""}
        <div class="acts"><button class="primary" data-act="agent" data-scope="experiment" data-id="${x.id}">Prompt</button><button class="ghost" data-act="reopen" data-id="${x.id}">Reopen</button><button class="ghost" data-act="showTrail" data-id="${x.id}">Show on stack</button><button class="ghost" data-act="dropExp" data-id="${x.id}">Remove</button></div></li>`).join("")}</ul>
        <p><button class="ghost" data-act="export" data-kind="md">Download Markdown</button> <button class="ghost" data-act="export" data-kind="json">Download JSON</button></p>`
        : `<p>Nothing saved yet. Press <span class="kbd">D</span> to draw, write one rough idea, and keep it.</p>`}`;
  },
  about() {
    const keys = [["D", "Draw parts"], ["/", "Parts list"], ["C", "Connect selected parts"], ["G", "Group selected parts"], ["T", "Add a part to the route"], ["R", "Reverse the route"], ["L", "Lens on or off"], ["Q", "Prompt for an agent about what you are looking at"], ["V E P B K", "View: plain, evidence, place, data boundary, cost"], ["A", "Next arrangement"], ["Arrow keys", "Move between parts, or move the lens"], ["+ − 0", "Zoom and fit"], ["Esc", "Close panel, then leave the route"]];
    const c = base.catalogs;
    return `<h2>About this stack</h2><p>${esc(E.facts.meta.note)}</p>
      <p>Suggestions come from authored seeds and local rules. No model is called and no service is contacted. Pick a seed or a rule’s example apart: it may simply be wrong for you.</p>
      <h3>What the shapes mean</h3><ul class="list">${E.facts.types.map(t => `<li style="display:flex;gap:8px;align-items:center;padding:2px 0;border:0"><span style="width:12px;height:12px;display:inline-block">${glyph(t.id)}</span>${esc(t.label)}</li>`).join("")}</ul>
      <h3>Evidence states</h3><ul>${E.facts.evidence.map(e => `<li><b>${esc(e.label)}:</b> ${esc(e.meaning)}</li>`).join("")}</ul>
      <h3>Catalogs are not access</h3><p class="src">Nous: ${c.nous.entries} catalog entries, ${c.nous.zero_price_candidates.length} zero-price candidates. NVIDIA: ${c.nvidia.public_ids} public IDs and ${c.nvidia.free_endpoint_cards} Free Endpoint cards, ${c.nvidia.free_also_in_public_ids} in both lists.</p>
      <h3>Keys</h3><ul class="list">${keys.map(([k, d]) => `<li style="border:0;padding:2px 0"><span class="kbd">${k}</span> ${esc(d)}</li>`).join("")}</ul>
      <h3>Sources</h3><ul class="list">${Object.keys(E.facts.sources).map(sourceLine).join("")}</ul>`;
  },
};
const catalogNous = () => { const c = base.catalogs.nous; return `<h3>Catalog, not access</h3><p class="src">${c.entries} entries. Accept audio: ${c.input_modalities.audio}. Output audio: ${c.output_modalities.audio}. Zero-price candidates:</p><ul>${c.zero_price_candidates.map(m => `<li class="src">${esc(m)}</li>`).join("")}</ul>`; };
const catalogNvidia = () => { const c = base.catalogs.nvidia, voice = c.free_endpoint_cards_list.filter(m => /tts|voice/i.test(m.name)); return `<h3>Catalog, not access</h3><p class="src">${c.public_ids} public IDs; ${c.free_endpoint_cards} Free Endpoint cards of ${c.site_total_models} site models; ${c.free_also_in_public_ids} cards match the ID list. Voice-related cards: ${voice.map(v => esc(v.name)).join(", ")}.</p>`; };
function findPlank(id) {
  const v = currentView(); const hit = v.shown.find(p => p.id === id) || v.cut.map(c => c.plank).find(p => p.id === id);
  return hit || null;
}
function filterParts() { const q = ($("#partSearch")?.value || "").toLowerCase(); $$("#partList li").forEach(li => { li.hidden = !li.dataset.name.includes(q); }); }

/* ---------- agent prompts ---------- */
const INTENT_NOTE = { sources: "Reads documentation and other primary sources, and answers the open questions. It builds nothing.",
  ideas: "Generates varied ideas from these parts, starting from yours. Nothing is scored.",
  build: "Builds the smallest test one hop at a time, or proposes one and waits for your go-ahead." };
const PANEL_BACK = { part: "Back to the part", hop: "Back to the hop", why: "Back to why", unlocks: "Back to unlocks", trail: "Back to your trail", swaps: "Back to swaps", experiment: "Back to the experiment", parts: "Back to parts", practice: "Back to practice", about: "Back" };
// What the agent needs to know about the step you are on. Returns null when that thing is gone.
function agentCtx(d) {
  const c = { focus: d.scope, constraints: { ...S.constraints }, observed: E.facts.meta.observed_date };
  const route = () => { Object.assign(c, { parts: [...S.route.parts], mode: S.route.mode, idea: S.idea.text, hideMiddles: !S.revealed });
    const ex = S.exercise && E.rules.exercises.find(e => e.id === S.exercise); if (ex) c.exercise = { name: ex.name, ask: ex.ask };
    if (S.revealed) c.shown = currentView().shown.map(p => p.title); };
  switch (d.scope) {
    case "stack": c.parts = E.facts.resources.map(r => r.id); break;
    case "parts": c.parts = d.ids ? String(d.ids).split(",") : [...S.hand]; break;
    case "part": if (!E.res(d.id)) return null; c.parts = [d.id]; break;
    case "route": if (!S.route) return null; route(); break;
    case "hop": if (!S.route || !E.hopsOf(S.route)[Number(d.id)]) return null; route(); c.hopIndex = Number(d.id); break;
    case "bridge": { const p = S.route && findPlank(d.id); if (!p) return null; route();
      c.bridge = { title: p.title, outcome: p.outcome, steps: p.middles.map(m => m.label), dependency: p.dependency, test: p.test, success: p.success, unknown: p.unknown, origin: p.origin === "seed" ? "an authored example" : "made by a local rule" };
      if (p.offer) c.offer = p.offer; break; }
    case "experiment": { const x = S.experiments.find(e => e.id === d.id); if (!x) return null;
      Object.assign(c, { parts: x.parts, mode: x.mode, idea: x.idea, experiment: x, constraints: x.constraints || c.constraints, observed: x.observed, offer: x.offer || null }); break; }
    case "opportunity": { const o = E.ledger(S.constraints.budget).find(o => o.id === d.id); if (!o) return null;
      c.parts = o.existing; c.opportunity = { goal: o.goal, outcome: o.outcome, missing: o.missing, change: o.change }; c.offer = o.offerData.id; break; }
    case "swap": { const s = S.route && E.swapsFor(S.route.parts)[Number(d.id)]; if (!s) return null; route(); c.swap = s; break; }
    default: return null;
  }
  return c;
}
// The most specific thing on screen, for the top-bar Prompt button and the Q key.
function hereDesc() {
  const a = S.panelArg;
  if (S.panel === "part") return { scope: "part", id: a };
  if (S.panel === "hop") return { scope: "hop", id: a };
  if (S.panel === "why" || (S.panel === "experiment" && a !== "mine")) return { scope: "bridge", id: a };
  if (S.mode === "table") return { scope: "route" };
  if (S.hand.length === 1) return { scope: "part", id: S.hand[0] };
  if (S.hand.length > 1) return { scope: "parts" };
  return { scope: "stack" };
}
function openAgent(desc, from) {
  if (desc.scope === "parts" && !desc.ids) desc = { ...desc, ids: S.hand.join(",") };
  S.agentFrom = from !== undefined ? from : S.panel && S.panel !== "agent" ? { name: S.panel, arg: S.panelArg } : S.panel === "agent" ? S.agentFrom : null;
  S.agentDesc = desc; openPanel("agent");
}

/* ---------- exercises ---------- */
function draw(opts = {}) {
  const sizes = [2, 3, 4, 5];
  const n = opts.n || (S.handSize === "any" ? sizes[S.seq % 4] : S.handSize);
  const pools = S.groups.length > 1 && !opts.where ? S.groups.map(g => g.members) : null;
  const hand = E.drawHand(n, S.seq, { seen: S.seen, avoid: S.avoid, pools, where: opts.where });
  S.seq++; persist();
  connect(hand, { mode: opts.mode || "chain", exercise: opts.exercise || null });
}
const EX = {
  distant: () => draw({ n: 2, exercise: "distant", where: h => ["body", "time"].includes(E.res(h[0]).domain) && E.distant(h[0], h[1]) }),
  middle: () => draw({ n: 2, exercise: "middle", where: h => E.fit(h[0], h[1]).kind === "adapter" }),
  third: () => S.route && S.revealed ? (S.exercise = "third", renderTable()) : draw({ n: 2, exercise: "third" }),
  reverse: () => S.route && S.revealed ? (S.exercise = "reverse", renderTable()) : draw({ n: 2, exercise: "reverse" }),
  swap: () => draw({ n: 2, exercise: "swap", where: h => E.swapsFor(h).length > 0 }),
  purchase: () => openPanel("unlocks"),
  transfer: () => draw({ n: 2, exercise: "transfer", where: h => !E.hasSeed(h) }),
  shortest: () => draw({ n: 4, exercise: "shortest" }),
  long: () => draw({ n: 4, exercise: "long" }),
  fanin: () => draw({ n: 3, mode: "fanin", exercise: "fanin" }),
  fanout: () => draw({ n: 3, mode: "fanout", exercise: "fanout" }),
  loop: () => draw({ n: 2, mode: "loop", exercise: "loop" }),
};

/* ---------- actions ---------- */
function constraintText() { const c = S.constraints; return [c.local ? "keep data local" : "", c.spend === "none" ? "use what I already have" : c.spend === "budget" ? `one purchase up to USD ${c.budget} a month` : ""].filter(Boolean).join("; ") || "none"; }
const A = {
  back: backToField, closePanel,
  connectHand: () => connect(S.hand),
  clearHand: () => { S.hand = []; renderHand(); },
  groupHand: () => { S.naming = true; renderHand(); },
  cancelGroup: () => { S.naming = false; renderHand(); },
  saveGroup: () => {
    const name = $("#groupName").value.trim() || `Group ${S.groups.length + 1}`;
    S.groups.forEach(g => { g.members = g.members.filter(m => !S.hand.includes(m)); });
    S.groups = S.groups.filter(g => g.members.length);
    S.groups.push({ id: "g" + Date.now(), name, members: [...S.hand] }); S.naming = false; S.hand = []; S.arrange = "groups"; $("#arrange").value = "groups";
    persist(); renderHand(); layoutField(false); toast(`${name} kept. With two groups, Draw picks one part from each.`);
  },
  reveal: () => { S.revealed = true; markTried(); renderIdea(); renderTools(); renderBridges(); requestAnimationFrame(drawRoute); $("#planks .plank h3")?.scrollIntoView?.({ block: "nearest" }); $("#planks button, #noBridge")?.focus?.({ preventScroll: true }); },
  toggleSketch: () => { S.sketching = !S.sketching; renderIdea(); },
  clearSketch: () => { S.idea.sketch = null; renderIdea(); refreshIdeaButtons(); },
  openPart: d => openPanel("part", d.id),
  openHop: d => openPanel("hop", Number(d.i)),
  why: d => openPanel("why", d.id),
  openAdder: d => { S.insertAt = d.at != null ? Number(d.at) : null; openPanel("parts"); },
  addPart: d => { const at = S.insertAt; S.panel && closePanel(); addPart(d.id, at); },
  pickFromList: d => { togglePick(d.id); toast(`${E.res(d.id).name} ${S.hand.includes(d.id) ? "selected" : "removed"}.`); },
  removePart: d => { if (S.route.parts.length <= 2) return; S.route.parts = S.route.parts.filter(p => p !== d.id); routeChanged(`${E.res(d.id).name} removed. Did the idea survive?`); },
  reverse: () => { const r = S.route; r.parts.reverse(); if (r.mode === "fanin") r.mode = "fanout"; else if (r.mode === "fanout") r.mode = "fanin"; routeChanged("Reversed. Read the bridges again."); },
  setShape: d => {
    const r = S.route;
    if (d.id === "hop") { r.mode = "chain"; if (r.parts.length > 2) r.parts = [r.parts[0], r.parts[r.parts.length - 1]]; routeChanged("Down to one hop. What did you lose?"); return; }
    if (d.id === "chain") { r.mode = "chain"; if (r.parts.length < 3) { routeChanged(); S.insertAt = 1; openPanel("parts"); toast("A chain needs a stop along the way. Pick one."); return; } routeChanged(); return; }
    r.mode = d.id;
    if (r.parts.length < 3 && d.id !== "loop") { routeChanged(); openPanel("parts"); toast("This shape needs a third part. Pick one."); return; }
    routeChanged();
  },
  reject: d => { S.rejected.push(d.id); renderBridges(); toast("Set aside. Here is another, if the rules have one."); },
  restore: () => { S.rejected = []; renderBridges(); },
  experiment: d => openPanel("experiment", d.id),
  agent: d => openAgent({ scope: d.scope, id: d.id }),
  agentHere: () => S.panel === "agent" ? closePanel() : openAgent(hereDesc()),
  agentBack: () => { const f = S.agentFrom; S.agentFrom = null; f ? openPanel(f.name, f.arg) : closePanel(); },
  intent: d => { S.intent = d.id; openPanel("agent"); $(`[data-act="intent"][data-id="${d.id}"]`)?.focus(); },
  copyPrompt: async () => { const t = $("#promptText");
    try { await navigator.clipboard.writeText(t.value); toast("Copied. Nothing has been sent."); }
    catch { t.select(); toast("Selected. Press Cmd or Ctrl and C to copy."); } },
  downloadPrompt: () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([$("#promptText").value], { type: "text/markdown" })); a.download = `bridgework-${S.intent}.md`; a.click(); URL.revokeObjectURL(a.href); },
  experimentMine: () => openPanel("experiment", "mine"),
  openSwaps: () => openPanel("swaps"),
  applySwap: d => { const s = E.swapsFor(S.route.parts)[Number(d.i)]; S.route.parts = S.route.parts.map(p => p === s.from ? s.to : p); closePanel(); routeChanged(`${E.res(s.to).name} swapped in. You gain: ${s.gain}. You lose: ${s.loss}.`); },
  startExercise: d => { if (S.panel) closePanel(); EX[d.id](); },
  endExercise: () => { S.exercise = null; renderTable(); },
  notDistant: () => { S.avoid.push(E.handKey(S.route.parts)); persist(); toast("Noted. The rule was wrong for this pair; it will not be drawn again."); EX.distant(); },
  loadOpp: d => {
    const op = E.costs.opportunities.find(o => o.id === d.id), seed = E.bridges.seeds.find(s => s.id === op.bridge);
    closePanel(); connect([seed.from, seed.to]); S.prefer = seed.id; S.constraints.spend = "budget"; renderIdea(); toast("Your idea first, then the bridge.");
  },
  reopen: d => {
    const x = S.experiments.find(e => e.id === d.id); if (!x.parts.every(p => E.res(p))) return toast("A part of this experiment is not in the current stack.");
    closePanel(); connect(x.parts, { mode: x.mode }); S.idea = { text: x.idea || "", sketch: x.sketch || null }; S.revealed = !!x.revealed; renderTable();
  },
  showTrail: d => { S.highlight = d.id; if (S.mode !== "field") backToField(); kick(); },
  dropExp: d => { const i = S.experiments.findIndex(e => e.id === d.id), x = S.experiments[i]; S.experiments.splice(i, 1); persist(); updateTrailN(); openPanel("trail"); kick();
    toast("Removed.", "Undo", () => { S.experiments.splice(i, 0, x); persist(); updateTrailN(); openPanel("trail"); kick(); }); },
  export: d => {
    const body = d.kind === "json" ? JSON.stringify(S.experiments, null, 2) : S.experiments.map(x => `## ${x.outcome}\n\n- Parts: ${x.names.join(" → ")} (${x.shapeName})\n- Bridge: ${x.bridge}\n- Missing: ${x.dependency}\n- Smallest test: ${x.test}\n- Success: ${x.success}\n- Assumptions: ${x.assumptions}\n- Evidence at save: ${x.evidence.map(e => `${e.name}: ${e.state}`).join("; ")} (observed ${x.observed})\n- Constraints: ${x.constraintText}\n- Status: proposal, not run\n`).join("\n");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([body], { type: "text/plain" })); a.download = `bridgework-trail.${d.kind}`; a.click(); URL.revokeObjectURL(a.href);
  },
  resetStack: () => { S.importedStack = null; S.userParts = []; persist(); S.hand = []; boot(); closePanel(); toast("Back to the original stack."); },
};
function saveExperiment(form) {
  const f = new FormData(form), id = form.dataset.id, mine = id === "mine", p = mine ? null : findPlank(id);
  const shape = E.shapeOf(S.route), get = k => String(f.get(k) || "").trim();
  S.experiments.unshift({
    id: "x" + Date.now(), parts: [...S.route.parts], names: S.route.parts.map(x => E.res(x).name), mode: S.route.mode, shape, shapeName: E.rules.shapes.find(s => s.id === shape)?.name,
    outcome: get("outcome"), bridge: get("bridge"), dependency: get("dependency"), test: get("test"), success: get("success"), assumptions: get("assumptions"),
    idea: S.idea.text, sketch: S.idea.sketch, revealed: S.revealed, bridgeId: p?.id || null, origin: mine ? "Your own bridge" : p?.origin === "seed" ? "Seeded example, proposal" : "Rule-made example, proposal",
    evidence: S.route.parts.map(x => ({ id: x, name: E.res(x).name, state: E.res(x).evidence, gates: E.res(x).gates })), observed: E.facts.meta.observed_date,
    constraints: { ...S.constraints }, constraintText: constraintText(), offer: p?.offer || null, savedAt: new Date().toISOString(), status: "proposal, not run",
  });
  if (!S.tried.includes(shape)) S.tried.push(shape);
  if (S.exercise === "transfer") S.transferSaved = true;
  persist(); updateTrailN(); renderTools(); renderIdea(); openAgent({ scope: "experiment", id: S.experiments[0].id }, { name: "trail" }); toast("Saved to your trail.");
}
const updateTrailN = () => { $("#trailN").textContent = S.experiments.length || ""; };
let toastTimer;
function toast(msg, label, fn) {
  const t = $("#toast"); t.textContent = msg;
  if (label) { const b = document.createElement("button"); b.textContent = label; b.onclick = () => { fn(); t.classList.remove("on"); }; t.append(b); }
  t.classList.add("on"); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("on"), label ? 6000 : 3200);
}

/* ---------- view specs and lens ---------- */
const VIEWS = [["plain", "Plain", "V"], ["evidence", "Evidence", "E"], ["place", "Place", "P"], ["data", "Data", "B"], ["cost", "Cost", "K"]];
function setView(v) {
  if (S.lens.on) { S.lens.spec = v === "plain" ? "evidence" : v; $("#lensWorld").dataset.view = S.lens.spec; } else { S.view = v; $("#world").dataset.view = v; }
  const cur = S.lens.on ? S.lens.spec : S.view; $$("#views button").forEach(b => b.setAttribute("aria-checked", b.dataset.v === cur)); paintLens();
}
function toggleLens(on = !S.lens.on) {
  const L = S.lens; L.on = on; if (on && !L.x) { L.x = usableWidth() * .34; L.y = (innerHeight - 52) * .42; L.r = isNarrow() ? 90 : 130; }
  if (on) { S.view = "plain"; $("#world").dataset.view = "plain"; }
  $("#lensBtn").setAttribute("aria-pressed", on); $("#lensClip").hidden = !on; $("#lensRing").hidden = !on; setView(L.spec); if (on) $("#lensRing").focus({ preventScroll: true });
}
function paintLens() {
  const L = S.lens; if (!L.on) return;
  $("#lensClip").style.clipPath = `circle(${L.r}px at ${L.x}px ${L.y}px)`;
  const r = $("#lensRing"); r.style.left = L.x - L.r + "px"; r.style.top = L.y - L.r + "px"; r.style.width = r.style.height = L.r * 2 + "px";
  r.firstElementChild.textContent = VIEWS.find(v => v[0] === L.spec)?.[1] + " lens";
}

/* ---------- pointer ---------- */
let band = null, marquee = null, gesture = null, suppressClick = false;
const pointers = new Map();
const toWorld = (cx, cy) => { const r = $("#viewport").getBoundingClientRect(); return { x: (cx - r.left - cam.x) / cam.k, y: (cy - r.top - cam.y) / cam.k }; };
const tokWorld = e => { const w = toWorld(e.clientX, e.clientY); if (S.mode === "table") w.y += cam.y; return w; };
const setCam = (x, y, k = cam.k) => { if (S.mode === "table") { x = 0; y = Math.min(0, y); k = 1; } cam.x = cam.tx = x; cam.y = cam.ty = y; cam.k = cam.tk = k; dirtyWires = true; paint(); };
function zoomAt(cx, cy, f) { const r = $("#viewport").getBoundingClientRect(), px = cx - r.left, py = cy - r.top, k = Math.min(2.2, Math.max(.35, cam.k * f)); setCam(px - (px - cam.x) * k / cam.k, py - (py - cam.y) * k / cam.k, k); }
function onDown(e) {
  if (S.mode === "table" && isNarrow()) return;
  const lensH = e.target.closest("#lensRing span");
  if (lensH) { gesture = { kind: "lens", ox: e.clientX - S.lens.x, oy: e.clientY - S.lens.y }; capture(e); return; }
  if (e.target.closest("#table") ) { if (e.target.closest("button,textarea,input,select,a,canvas,label,.part,.plank,.idea,.cons")) return; }
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (pointers.size === 2) { const [a, b] = [...pointers.values()]; gesture = { kind: "pinch", d: Math.hypot(a.x - b.x, a.y - b.y) }; return; }
  const tok = e.target.closest(".token");
  if (tok) {
    const id = tok.dataset.id, port = e.target.closest(".port.out"), w = tokWorld(e), p = P.get(id);
    gesture = { kind: port ? "band" : "token", id, ox: w.x - p.x, oy: w.y - p.y, sx: e.clientX, sy: e.clientY, moved: false };
  } else if (e.shiftKey && S.mode === "field") { const w = toWorld(e.clientX, e.clientY); marquee = { x0: w.x, y0: w.y, x1: w.x, y1: w.y }; gesture = { kind: "marquee" }; }
  else { gesture = { kind: "pan", ox: e.clientX - cam.x, oy: e.clientY - cam.y }; $("#viewport").classList.add("panning"); capture(e); }
}
const capture = e => { try { $("#viewport").setPointerCapture(e.pointerId); } catch { /* synthetic pointer */ } };
function onMove(e) {
  if (pointers.has(e.pointerId)) pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (!gesture) return;
  const g = gesture;
  if (g.kind === "lens") { S.lens.x = e.clientX - g.ox; S.lens.y = e.clientY - g.oy; paintLens(); }
  else if (g.kind === "pinch") { const [a, b] = [...pointers.values()]; if (!b) return; const d = Math.hypot(a.x - b.x, a.y - b.y); zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, d / g.d); g.d = d; }
  else if (g.kind === "pan") setCam(e.clientX - g.ox, e.clientY - g.oy);
  else if (g.kind === "marquee") { const w = toWorld(e.clientX, e.clientY); marquee.x1 = w.x; marquee.y1 = w.y; dirtyWires = true; paint(); }
  else if (g.kind === "token" || g.kind === "band") {
    if (!g.moved && Math.hypot(e.clientX - g.sx, e.clientY - g.sy) < 6) return;
    const w = tokWorld(e);
    if (g.kind === "band" && S.mode === "field") {
      if (!g.moved) showFit(g.id);
      g.moved = true; const p = P.get(g.id); band = { x0: p.x + TW, y0: p.y + TH / 2, x1: w.x, y1: w.y }; dirtyWires = true; paint();
    } else {
      g.moved = true; const p = P.get(g.id); p.drag = true; p.x = p.tx = w.x - g.ox; p.y = p.ty = w.y - g.oy; p.el.style.zIndex = 5; dirtyWires = true; paint();
      if (S.mode === "table") { $$(".slot").forEach(s => s.classList.toggle("over", s === document.elementsFromPoint(e.clientX, e.clientY).find(n => n.classList?.contains("slot")))); }
    }
  }
}
function onUp(e) {
  pointers.delete(e.pointerId); const g = gesture; if (!g) return;
  if (pointers.size > 0 && g.kind === "pinch") return;
  gesture = null; $("#viewport").classList.remove("panning");
  if (g.kind === "marquee") {
    const x0 = Math.min(marquee.x0, marquee.x1), x1 = Math.max(marquee.x0, marquee.x1), y0 = Math.min(marquee.y0, marquee.y1), y1 = Math.max(marquee.y0, marquee.y1);
    for (const [id, p] of P) { const c = { x: p.x + TW / 2, y: p.y + TH / 2 }; if (c.x > x0 && c.x < x1 && c.y > y0 && c.y < y1 && !S.hand.includes(id) && S.hand.length < 5) S.hand.push(id); }
    marquee = null; renderHand(); kick();
  } else if (g.moved && g.kind === "band") {
    suppressClick = true; band = null; kick();
    const hit = document.elementsFromPoint(e.clientX, e.clientY).find(n => n.classList?.contains("token"));
    if (hit && hit.dataset.id !== g.id) connect([...S.hand.filter(h => h !== g.id && h !== hit.dataset.id), g.id, hit.dataset.id]); else showFit(S.hand[S.hand.length - 1]);
  } else if (g.moved && g.kind === "token") {
    suppressClick = true; const p = P.get(g.id); p.drag = false; p.el.style.zIndex = "";
    if (S.mode === "table") {
      const under = document.elementsFromPoint(e.clientX, e.clientY), slot = under.find(n => n.classList?.contains("slot")), onTable = under.some(n => n.id === "table" || n.closest?.("#table"));
      layoutRail();
      if (onTable) {
        if (!S.revealed) toast("Put your idea down first. Then parts can join.");
        else addPart(g.id, slot ? Number(slot.dataset.at) : null);
      }
    }
    kick();
  }
}
function onClick(e) {
  const act = e.target.closest("[data-act]");
  if (act) { A[act.dataset.act]?.(act.dataset, act); return; }
  const pn = e.target.closest("[data-panel]");
  if (pn) { const name = pn.dataset.panel; if (S.panel === name) closePanel(); else openPanel(name); return; }
  const tok = e.target.closest("#tokens .token");
  if (tok) { if (suppressClick) { suppressClick = false; return; } if (S.mode === "field") togglePick(tok.dataset.id); else openPanel("part", tok.dataset.id); return; }
  suppressClick = false;
}

/* ---------- keyboard ---------- */
function moveFocus(dir, from) {
  const a = P.get(from); let best = null, bd = 1e9;
  for (const [id, p] of P) {
    if (id === from || p.el.classList.contains("used")) continue;
    const dx = p.x - a.x, dy = p.y - a.y, along = { ArrowRight: dx, ArrowLeft: -dx, ArrowDown: dy, ArrowUp: -dy }[dir], across = dir === "ArrowLeft" || dir === "ArrowRight" ? Math.abs(dy) : Math.abs(dx);
    if (along <= 4) continue; const s = along + across * 2.2; if (s < bd) { bd = s; best = p; }
  }
  best?.el.focus();
}
function onKey(e) {
  const tag = e.target.tagName, typing = /INPUT|TEXTAREA|SELECT/.test(tag);
  if (e.key === "Escape") {
    if (S.naming) { S.naming = false; renderHand(); return; }
    if (S.panel) { closePanel(); return; }
    if (typing) { e.target.blur(); return; }
    if (S.mode === "table") { backToField(); return; }
    if (S.lens.on) { toggleLens(false); return; }
    if (S.hand.length) A.clearHand();
    return;
  }
  if (S.naming && e.key === "Enter" && e.target.id === "groupName") { A.saveGroup(); return; }
  if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target.id === "lensRing" && e.key.startsWith("Arrow")) { const d = 24; S.lens.x += { ArrowLeft: -d, ArrowRight: d }[e.key] || 0; S.lens.y += { ArrowUp: -d, ArrowDown: d }[e.key] || 0; paintLens(); e.preventDefault(); return; }
  if (e.key.startsWith("Arrow")) {
    const t = e.target.closest?.("#tokens .token");
    if (t) { moveFocus(e.key, t.dataset.id); e.preventDefault(); return; }
    if (S.mode === "field") { const d = 60; setCam(cam.x + ({ ArrowLeft: d, ArrowRight: -d }[e.key] || 0), cam.y + ({ ArrowUp: d, ArrowDown: -d }[e.key] || 0)); e.preventDefault(); }
    return;
  }
  const k = e.key.toLowerCase(), v = VIEWS.find(x => x[2].toLowerCase() === k);
  if (v) { setView(v[0]); return; }
  const map = {
    d: () => draw(), q: () => A.agentHere(), "/": () => openPanel("parts"), "?": () => openPanel("about"), l: () => toggleLens(),
    c: () => S.hand.length > 1 && connect(S.hand), g: () => S.hand.length > 1 && A.groupHand(),
    t: () => S.route && S.revealed && A.openAdder({}), r: () => S.route && A.reverse(),
    a: () => { const s = $("#arrange"); s.selectedIndex = (s.selectedIndex + 1) % s.options.length; s.dispatchEvent(new Event("change")); },
    "+": () => zoomAt(innerWidth / 2, innerHeight / 2, 1.2), "=": () => zoomAt(innerWidth / 2, innerHeight / 2, 1.2), "-": () => zoomAt(innerWidth / 2, innerHeight / 2, 1 / 1.2), 0: () => S.mode === "field" ? layoutField(false) : layoutRail(),
  };
  if (map[k]) { map[k](); e.preventDefault(); }
}

/* ---------- wiring ---------- */
function bind() {
  const vp = $("#viewport");
  vp.addEventListener("pointerdown", onDown); addEventListener("pointermove", onMove); addEventListener("pointerup", onUp); addEventListener("pointercancel", onUp);
  document.addEventListener("click", onClick); document.addEventListener("keydown", onKey);
  vp.addEventListener("wheel", e => {
    if (S.mode === "table" && isNarrow()) return;
    if (e.target.closest("textarea")) return;
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * .01)); else setCam(cam.x - e.deltaX, cam.y - e.deltaY);
  }, { passive: false });
  // Browsers scroll overflow:hidden parents to reveal focus; the camera owns position instead.
  vp.addEventListener("scroll", () => { if (!(S.mode === "table" && isNarrow())) { vp.scrollTop = 0; vp.scrollLeft = 0; } });
  document.addEventListener("focusin", e => {
    if (!vp.contains(e.target) || !e.target.matches(":focus-visible") || (S.mode === "table" && isNarrow())) return;
    const r = e.target.getBoundingClientRect(), v = vp.getBoundingClientRect(), right = v.right - (S.panel && !isNarrow() ? sideW() : 0); let dx = 0, dy = 0;
    if (r.bottom > v.bottom - 60) dy = v.bottom - 60 - r.bottom; if (r.top < v.top + 10) dy = v.top + 10 - r.top;
    if (r.right > right - 10) dx = right - 10 - r.right; if (r.left < v.left + 10) dx = v.left + 10 - r.left;
    if (dx || dy) setCam(cam.x + dx, cam.y + dy);
  });
  // Previewing a part shows what changes before committing to it.
  const prev = e => { const t = e.target.closest?.("#tokens .token"); if (!t || S.mode !== "table" || !S.revealed || S.route.parts.length >= 5 || gesture) return; if (S.preview !== t.dataset.id) { S.preview = t.dataset.id; renderBridges(); } };
  const unprev = e => { if (e.target.closest?.("#tokens .token") && S.preview) { S.preview = null; renderBridges(); } };
  $("#tokens").addEventListener("pointerover", prev); $("#tokens").addEventListener("pointerout", unprev); $("#tokens").addEventListener("focusin", prev); $("#tokens").addEventListener("focusout", unprev);
  $("#panel").addEventListener("submit", e => {
    e.preventDefault();
    if (e.target.id === "expForm") saveExperiment(e.target);
    if (e.target.id === "addForm") {
      const f = new FormData(e.target), name = String(f.get("name")).trim(), place = f.get("place");
      const boundary = { device: "device", mac: "local", home: "lan", vps: "own-cloud", hosted: "vendor" }[place];
      S.userParts.push({ id: "my-" + name.toLowerCase().replace(/\W+/g, "-") + "-" + S.userParts.length, name, act: String(f.get("act")).trim(), does: [String(f.get("act")).trim().split(" ")[0]], place, boundary, domain: "memory", evidence: f.get("evidence"),
        takes: f.get("takes") ? [{ type: f.get("takes"), label: `${E.facts.types.find(t => t.id === f.get("takes")).label.toLowerCase()}` }] : [], gives: [{ type: f.get("gives"), label: `${E.facts.types.find(t => t.id === f.get("gives")).label.toLowerCase()}` }],
        unknown: ["Whether it works in a route"], gates: [{ label: "Added by you", state: f.get("evidence") === "unknown" ? "unknown" : "partial", detail: "Your own statement", src: "" }] });
      persist(); boot(); relayoutSoon(); openPanel("parts"); toast(`${name} added.`);
    }
  });
  $("#panel").addEventListener("input", e => {
    if (e.target.id === "partSearch") filterParts();
    if (e.target.id === "ledgerBudget") { S.constraints.budget = Math.max(0, Number(e.target.value) || 0); const v = e.target.value; openPanel("unlocks"); const b = $("#ledgerBudget"); b.value = v; b.focus(); if (S.mode === "table") renderBridges(); }
  });
  $("#panel").addEventListener("change", async e => {
    if (e.target.id !== "stackFile") return;
    try {
      const j = JSON.parse(await e.target.files[0].text()), list = Array.isArray(j) ? j : j.resources;
      if (!Array.isArray(list) || !list.every(r => r.id && r.name)) throw 0;
      S.importedStack = list; S.userParts = []; S.hand = []; persist(); boot(); relayoutSoon(); closePanel(); toast(`${list.length} parts loaded. Rule-made examples work on any stack; seeds need the sample’s ids.`);
    } catch { toast("That file has no list of parts with id and name."); }
  });
  $("#handSize").innerHTML = [[2, "2"], [3, "3"], [4, "4"], ["any", "?"]].map(([v, l]) => `<button role="radio" data-n="${v}" aria-checked="${S.handSize === v}" aria-label="${v === "any" ? "A surprise number of" : v} parts">${l}</button>`).join("");
  $("#handSize").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; S.handSize = b.dataset.n === "any" ? "any" : Number(b.dataset.n); $$("#handSize button").forEach(x => x.setAttribute("aria-checked", x === b)); });
  $("#drawBtn").addEventListener("click", () => draw());
  $("#views").innerHTML = VIEWS.map(([v, l, k]) => `<button role="radio" data-v="${v}" aria-checked="${v === "plain"}" title="${l} (${k})">${l}</button>`).join("");
  $("#views").addEventListener("click", e => { const b = e.target.closest("button"); if (b) setView(b.dataset.v); });
  $("#lensBtn").addEventListener("click", () => toggleLens());
  $("#arrange").addEventListener("change", e => { S.arrange = e.target.value; if (S.arrange === "groups" && !S.groups.length) toast("No groups yet. Select parts, then press Group."); layoutField(false); });
  $("#zIn").onclick = () => zoomAt(innerWidth / 2, innerHeight / 2, 1.2); $("#zOut").onclick = () => zoomAt(innerWidth / 2, innerHeight / 2, 1 / 1.2); $("#zFit").onclick = () => layoutField(false);
  new ResizeObserver(() => { if (S.mode === "table") drawRoute(); }).observe($("#table"));
  addEventListener("resize", () => { if (S.mode === "table") { layoutRail(); requestAnimationFrame(drawRoute); } else layoutField(true); });
}
const relayoutSoon = () => { if (S.mode === "table") { setMode("table"); } else layoutField(true); };

async function main() {
  const get = n => fetch(`data/${n}.json`, { cache: "no-store" }).then(r => r.json());
  const [facts, bridges, costs, rules, catalogs] = await Promise.all(["facts", "bridges", "costs", "rules", "catalogs"].map(get));
  base = { facts, bridges, costs, rules, catalogs };
  $("#sampleNote").textContent = `${facts.meta.stack_name}, observed ${fmtDate(facts.meta.observed_date)}. Nothing is connected and no bridge has been run. Suggestions are local rules, not AI.`;
  boot(true); bind(); layoutField(true); updateTrailN(); renderHand();
  const m = location.hash.match(/r=([^&]+)&m=(\w+)/);
  if (m) { const ids = m[1].split(",").filter(E.res); if (ids.length > 1) connect(ids, { mode: m[2] }); }
  window.__bw = { S, cam, get E() { return E; } };
}
main();
