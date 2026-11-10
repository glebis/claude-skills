import test from "node:test"; import assert from "node:assert/strict"; import fs from "node:fs";
import { createEngine } from "../src/engine.js";
const j = f => JSON.parse(fs.readFileSync(new URL(`../data/${f}.json`, import.meta.url)));
const E = createEngine({ facts: j("facts"), bridges: j("bridges"), costs: j("costs"), rules: j("rules") });
const R = (parts, mode = "chain") => ({ parts, mode });
const titles = v => v.shown.map(p => p.title).join("|");

test("agent prompts carry the route and stay honest", () => {
  const x = { parts: ["shazam", "obsidian"], mode: "chain", idea: "my words", outcome: "a music diary", test: "one track by hand", success: "I read it twice", constraints: { local: true, spend: "none" } };
  const ex = E.agentPrompt(x, "explore"), im = E.agentPrompt(x, "implement");
  for (const p of [ex, im]) { assert.match(p, /my words/); assert.match(p, /Shazam → Obsidian/); assert.match(p, /Keep data on my machines/); assert.match(p, /Ask me before using credentials/); assert.doesNotMatch(p, /undefined|null|\[object/); }
  assert.match(ex, /do not build/i); assert.match(ex, /documented, tested or inferred/); assert.match(im, /Build only the smallest test/); assert.match(im, /one track by hand/); assert.notEqual(ex, im);
  const gap = E.agentPrompt({ parts: ["apple-health", "health-db"], mode: "chain", constraints: {} }, "implement");
  assert.match(gap, /BLOCKED/); assert.match(gap, /Do not fake it/); assert.match(gap, /Not stated yet/);
});

test("every step can become a sources, ideas or build prompt", () => {
  const ctxs = [{ focus: "stack", parts: E.facts.resources.map(r => r.id) }, { focus: "part", parts: ["exa"] }, { focus: "parts", parts: ["exa", "obsidian"] },
    { focus: "route", parts: ["shazam", "ollama", "obsidian"], mode: "chain", hideMiddles: true }, { focus: "hop", parts: ["shazam", "ollama"], mode: "chain", hopIndex: 0 },
    { focus: "opportunity", parts: ["exa"], opportunity: { goal: "g", outcome: "o", missing: "m", change: "c" }, offer: E.costs.offers[0].id }];
  for (const c of ctxs) for (const i of ["sources", "ideas", "build"]) { const t = E.promptFor({ constraints: {}, ...c }, i);
    assert.doesNotMatch(t, /undefined|null|NaN|\[object/, `${c.focus} ${i}`); assert.match(t, /## Limits/); assert.doesNotMatch(t, /score:|\b\d+\/10\b/i); }
  assert.match(E.promptFor({ focus: "route", parts: ["shazam", "obsidian"], mode: "chain", constraints: {} }, "ideas"), /ask me for my own idea/);
  assert.match(E.promptFor({ focus: "route", parts: ["shazam", "obsidian"], mode: "chain", idea: "mine", constraints: {} }, "ideas"), /Start from my idea/);
  const hidden = E.promptFor({ focus: "route", parts: ["shazam", "obsidian"], mode: "chain", hideMiddles: true, constraints: {} }, "sources");
  assert.match(hidden, /I have not named it yet/); assert.doesNotMatch(hidden, /missing middle:/);
  assert.match(E.promptFor({ focus: "parts", parts: ["exa", "obsidian"], constraints: {} }, "build"), /wait for my go-ahead/);
  assert.match(E.promptFor({ focus: "opportunity", parts: ["exa"], opportunity: { goal: "g", outcome: "o", missing: "m", change: "c" }, offer: E.costs.offers[0].id, constraints: {} }, "sources"), /Do not buy/);
});

test("all ids referenced by seeds, swaps and opportunities exist", () => {
  for (const s of E.bridges.seeds) { assert.ok(E.res(s.from), s.from); assert.ok(E.res(s.to), s.to); if (s.offer) assert.ok(E.offer(s.offer));
    Object.keys(s.thirds || {}).forEach(k => assert.ok(E.res(k), k)); (s.variants?.local?.parts || []).forEach(k => assert.ok(E.res(k), k)); }
  for (const w of E.bridges.swaps) { assert.ok(E.res(w.from)); assert.ok(E.res(w.to)); }
  for (const o of E.costs.opportunities) { assert.ok(E.offer(o.offer)); o.existing.forEach(k => assert.ok(E.res(k), k)); if (o.bridge) assert.ok(E.bridges.seeds.find(s => s.id === o.bridge), o.bridge); }
  for (const o of E.costs.offers) if (o.prices.some(p => p.amount > 0 || p.basis === "usage")) { assert.ok(o.url?.startsWith("https://"), o.id); assert.ok(o.checked); }
});
test("changing the pair changes the bridges", () => {
  assert.notEqual(titles(E.view(R(["apple-health", "elevenlabs"]))), titles(E.view(R(["fathom", "shortcuts"]))));
});
test("adding a part changes the outcome, at any length", () => {
  const a = E.view(R(["exa", "obsidian"])).shown[0], b = E.view(R(["exa", "obsidian", "elevenlabs"])).shown[0];
  assert.notEqual(a.outcome, b.outcome); assert.match(b.outcome, /audio field guide/);
  const c = E.view(R(["exa", "obsidian", "elevenlabs", "telegram"]));
  assert.equal(c.hops.length, 3); assert.equal(c.shown[0].effects.length, 2);
});
test("shapes change hops and wording", () => {
  const p = ["fathom", "exa", "obsidian"];
  assert.equal(E.hopsOf(R(p)).length, 2); assert.equal(E.hopsOf(R(p, "fanin")).every(h => h.to === "obsidian"), true);
  assert.equal(E.hopsOf(R(p, "fanout")).every(h => h.from === "fathom"), true); assert.equal(E.hopsOf(R(p, "loop")).length, 3);
  assert.equal(E.shapeOf(R(p.slice(0, 2))), "hop"); assert.equal(E.shapeOf(R(p)), "chain");
  assert.match(E.view(R(p, "fanin")).shown[0].shapeNote, /meet at Obsidian/);
  assert.match(E.view(R(p, "loop")).shown[0].unknown.join(), /running away/);
});
test("local-only removes or rewrites incompatible proposals", () => {
  const v = E.view(R(["apple-health", "elevenlabs"]), { constraints: { local: true } });
  assert.ok(v.shown.every(p => p.parts.every(x => E.boundaryOf(x).local)), titles(v)); assert.ok(v.shown.some(p => p.changed)); assert.ok(v.cut.length);
  const w = E.view(R(["exa", "gmail"]), { constraints: { local: true } }); assert.equal(w.shown.length, 0); assert.ok(w.cut.length);
});
test("budget excludes unaffordable additions, without folding in USD 20 or annual billing", () => {
  const r = R(["agent-vps", "nous"]), free = E.view(r);
  assert.ok(free.shown.some(p => p.seedId === "agent-paid"));
  const v = E.view(r, { constraints: { spend: "budget", budget: 10 } });
  assert.ok(!v.shown.some(p => p.seedId === "agent-paid")); assert.match(v.cut[0].why[0].text, /USD 20 per month is over USD 10/);
  assert.ok(E.view(r, { constraints: { spend: "budget", budget: 20 } }).shown.some(p => p.seedId === "agent-paid"));
  const hobby = E.offer("firecrawl-hobby");
  assert.equal(E.offerFit(hobby, 10).fits, false); assert.equal(E.offerFit(hobby, 16).fits, false); assert.equal(E.offerFit(hobby, 19).fits, true);
  assert.equal(E.offerFit(E.offer("nous-api"), 1000).fits, false);
  assert.equal(E.offerFit(E.offer("elevenlabs-starter"), 10).fits, true); assert.equal(E.offerFit(E.offer("exa-free"), 0).fits, true);
});
test("use what I have cuts new purchases", () => {
  const v = E.view(R(["fathom", "elevenlabs"]), { constraints: { spend: "none" }, prefer: "client-recap" });
  assert.ok(!v.shown.some(p => p.seedId === "client-recap")); assert.ok(v.cut.some(c => c.why[0].rule === "have"));
});
test("the Health route is a gap, never a fit", () => {
  assert.equal(E.fit("apple-health", "health-db").kind, "gap");
  const v = E.view(R(["apple-health", "health-db"]));
  assert.equal(v.middles[0].state, "gap"); assert.ok(v.shown.every(p => p.origin === "seed" ? p.seedId === "health-export" : true));
});
test("reverse uses authored text where it exists", () => {
  assert.match(E.view(R(["elevenlabs", "apple-health"])).shown.map(p => p.title).join(), /Say it first/);
});
test("rejection yields an alternative or an honest end", () => {
  const r = R(["firecrawl", "obsidian"]); const first = E.view(r).shown[0];
  const next = E.view(r, { rejected: [first.id] }).shown[0]; assert.notEqual(first.id, next.id);
});
test("not every pair gets a practical bridge", () => {
  const ids = E.facts.resources.map(r => r.id); let none = 0;
  for (const a of ids) for (const b of ids) if (a !== b && !E.view(R([a, b])).shown.some(p => p.kind === "practical")) none++;
  assert.ok(none > 0); 
});
test("draw respects hand size, is deterministic and never crashes", () => {
  for (const n of [2, 3, 4, 5]) for (let s = 0; s < 40; s++) { const h = E.drawHand(n, s); assert.equal(new Set(h).size, n); assert.deepEqual(h, E.drawHand(n, s)); E.view(R(h)); E.view(R(h, "loop")); }
});
test("no generated text leaks a placeholder for any pair", () => {
  const ids = E.facts.resources.map(r => r.id);
  for (const a of ids) for (const b of ids) if (a !== b) for (const p of E.view(R([a, b])).shown) assert.doesNotMatch(p.title + p.outcome + p.test, /undefined|\{|\}/);
});
test("nudge invites an untried shape and does not count volume", () => {
  const n = E.nudge(["hop", "hop", "hop"]); assert.equal(n.next.id, "chain"); assert.equal(n.shapes.find(s => s.id === "hop").tried, true);
});
