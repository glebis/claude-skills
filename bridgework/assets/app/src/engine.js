// Pure logic: no DOM, no network. Facts, suggestions and costs arrive as separate data.
const cap = s => (s ? s[0].toUpperCase() + s.slice(1) : s);
const hash = s => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
const listNames = a => a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1];
const fill = (t, v) => t.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? "");

export const KINDS = ["practical", "playful", "question"];
export const KIND_LABEL = { practical: "A practical route", playful: "A playful use", question: "A question to follow" };

export function createEngine({ facts, bridges, costs, rules }) {
  const byId = new Map(facts.resources.map(r => [r.id, r]));
  const res = id => byId.get(id);
  const lookup = (list, id) => list.find(x => x.id === id);
  const boundaryOf = id => lookup(facts.boundaries, res(id).boundary) || { local: false, label: "Unknown boundary" };
  const placeOf = id => lookup(facts.places, res(id).place) || { label: "Unknown place" };
  const offer = id => costs.offers.find(o => o.id === id);

  /** How A's output could reach B's input. Direct beats adapter; a recorded gap beats both. */
  function fit(a, b) {
    const gap = facts.gaps.find(g => g.from === a && g.to === b);
    if (gap) return { kind: "gap", statement: gap.statement, source: gap.source };
    const A = res(a), B = res(b);
    for (const give of A.gives) for (const take of B.takes)
      if (give.type === take.type) return { kind: "direct", give, take };
    for (const give of A.gives) for (const take of B.takes) {
      const adapter = rules.adapters[`${give.type}>${take.type}`];
      if (adapter) return { kind: "adapter", give, take, adapter };
    }
    return { kind: "none", give: A.gives[0], take: B.takes[0] };
  }

  /** The exposed sorting rule. Deliberately a boolean: no score. */
  const distant = (a, b) => res(a).domain !== res(b).domain && res(a).place !== res(b).place;

  /** Which hops a route has. A route is ordered parts plus a shape. */
  function hopsOf({ parts, mode = "chain" }) {
    const pairs = [];
    if (mode === "fanin") parts.slice(0, -1).forEach(p => pairs.push([p, parts[parts.length - 1]]));
    else if (mode === "fanout") parts.slice(1).forEach(p => pairs.push([parts[0], p]));
    else {
      for (let i = 0; i < parts.length - 1; i++) pairs.push([parts[i], parts[i + 1]]);
      if (mode === "loop" && parts.length > 1) pairs.push([parts[parts.length - 1], parts[0], "return"]);
    }
    return pairs.map(([from, to, role]) => ({ from, to, role, fit: fit(from, to) }));
  }

  const shapeOf = ({ parts, mode = "chain" }) => (mode === "chain" ? (parts.length > 2 ? "chain" : "hop") : mode);

  function middleOf(hop) {
    const f = hop.fit, base = { from: hop.from, to: hop.to, role: hop.role };
    if (f.kind === "direct") return { ...base, state: "direct", label: "fits with nothing in between", kind: "none" };
    if (f.kind === "adapter") return { ...base, state: "missing", label: f.adapter.label, kind: f.adapter.kind };
    if (f.kind === "gap") return { ...base, state: "gap", label: "no verified route", kind: "gap" };
    if (hop.role === "return") return { ...base, state: "missing", label: "you close the loop by hand", kind: "human" };
    return { ...base, state: "none", label: "no rule names a middle here", kind: "unknown" };
  }

  function shapeSentence(route) {
    const { parts, mode } = route, names = parts.map(p => res(p).name);
    if (mode === "fanin") return `${listNames(names.slice(0, -1))} meet at ${names[names.length - 1]}. Look for what neither shows alone.`;
    if (mode === "fanout") return `The same thing goes to ${listNames(names.slice(1))}. The difference between the results is the point.`;
    if (mode === "loop") return `What comes out of ${names[names.length - 1]} changes what ${names[0]} starts from next time.`;
    return "";
  }

  /** Effect of a part beyond the core of a plank. Authored text wins; otherwise the rule uses its position. */
  function extraEffect(seed, id, route) {
    if (seed?.thirds?.[id]) return { id, text: seed.thirds[id].outcome, adds: seed.thirds[id].adds, authored: true };
    const r = res(id), hops = hopsOf(route).filter(h => h.from === id || h.to === id);
    const open = hops.some(h => h.fit.kind === "direct" || h.fit.kind === "adapter");
    if (!open) return { id, inert: true, adds: r.asThird.adds, text: `${r.name} has no rule connecting it here. Say why it belongs, or remove it.` };
    return { id, adds: r.asThird.adds, text: `${cap(r.name)} adds ${r.asThird.adds}: ${r.asThird.then}.` };
  }

  function seedPlank(seed, route, reversed) {
    const ov = reversed ? seed.reverse : null;
    const core = [seed.from, seed.to], extras = route.parts.filter(p => !core.includes(p));
    const hops = hopsOf(route), mid = ov?.middle || seed.middle;
    const f = reversed ? seed.to : seed.from, t = reversed ? seed.from : seed.to;
    let placed = false;
    const middles = hops.map(h => {
      const m = middleOf(h);
      if (h.from === f && h.to === t) { placed = true; return { ...m, state: "missing", label: mid.label, kind: mid.kind }; }
      return m;
    });
    if (!placed) middles.unshift({ from: f, to: t, state: "missing", label: mid.label, kind: mid.kind });
    const effects = extras.map(id => extraEffect(seed, id, route));
    const base = ov?.outcome || seed.outcome, note = shapeSentence(route);
    const live = effects.filter(e => !e.inert);
    const outcome = live.some(e => e.authored) ? live.filter(e => e.authored).map(e => e.text).join(" ") : base;
    return {
      id: seed.id + (reversed ? ":rev" : ""), seedId: seed.id, origin: "seed", kind: seed.kind, goal: seed.goal,
      title: ov?.title || seed.title, base, outcome, effects, shapeNote: note, middles, parts: [...route.parts], offer: seed.offer || null,
      dependency: seed.dependency, why: ov?.why || seed.why, unknown: seed.unknown.concat(extras.flatMap(p => res(p).unknown.slice(0, 1))).concat(route.mode === "loop" ? ["What stops the loop running away"] : []),
      test: seed.test, success: seed.success, source: seed.source, variants: seed.variants,
    };
  }

  function rulePlank(route, kind, i) {
    const { parts } = route, hops = hopsOf(route);
    const first = res(parts[0]), last = res(parts[parts.length - 1]);
    const middles = hops.map(middleOf);
    const broken = middles.filter(m => m.state === "none" || m.state === "gap");
    const open = hops.find(h => h.fit.give) || {};
    const give = open.fit?.give?.label || first.gives[0]?.label || `what ${first.name} holds`;
    const v = { give, A: first.name, B: last.name };
    const common = {
      origin: "rule", kind, middles, parts: [...parts], offer: null, effects: [], shapeNote: shapeSentence(route),
      goal: rules.goals[last.domain] || "Discover ideas",
      unknown: [...new Set(parts.flatMap(p => res(p).unknown.slice(0, 1)))].concat(route.mode === "loop" ? ["What stops the loop running away"] : []),
      dependency: middles.filter(m => m.state === "missing").map(m => cap(m.label)).join("; ") || "Nothing named by the rules. Check that the parts work at all.",
    };
    const id = `rule:${route.mode}:${parts.join(">")}:${kind}:${i}`;
    if (kind === "practical") {
      if (broken.length || i > 0) return null;
      const steps = hops.filter(h => h.role !== "return").map(h => `${res(h.to).name} ${res(h.to).act}`);
      const outcome = hops.length === 1
        ? `${last.name} receives ${give} and ${last.act}. You decide whether the result is worth keeping.`
        : `${first.name} hands over ${give}. ${cap(steps.join("; then "))}. You decide whether the result is worth keeping.`;
      return { ...common, id, title: parts.length > 2 ? `${first.name} to ${last.name}, by way of ${listNames(parts.slice(1, -1).map(p => res(p).name))}` : `${cap(give)} into ${last.name}`,
        base: outcome, outcome, why: [`Rule: ${rules.fit[hops.every(h => h.fit.kind === "direct") ? "direct" : "adapter"]}`],
        test: "Do each hop by hand once, with a made-up example, before automating any of it.", success: "You would do it again without being asked." };
    }
    const pool = kind === "playful" ? rules.playful : rules.questions;
    const pick = pool[(hash(parts.join()) + i) % pool.length];
    if (i >= pool.length) return null;
    if (kind === "playful" && broken.length === middles.length) return null;
    const outcome = fill(pick.outcome, v);
    return { ...common, id, title: fill(pick.title, v), base: outcome, outcome,
      why: [`Rule: a ${kind === "playful" ? "playful" : "question"} template filled from these parts. It knows nothing about whether this matters to you.`],
      test: pick.test ? fill(pick.test, v) : "Write down what you expect before you look.", success: pick.success ? fill(pick.success, v) : "You have a question you did not have before." };
  }

  /** Ordered candidates for one kind: seeds that fit the route, then generated examples. */
  function candidates(route, kind, prefer) {
    const idx = id => route.parts.indexOf(id), out = [];
    for (const s of bridges.seeds) {
      if (s.kind !== kind) continue;
      const a = idx(s.from), b = idx(s.to);
      if (a < 0 || b < 0) continue;
      if (a < b) out.push(seedPlank(s, route, false));
      else if (s.reverse) out.push(seedPlank(s, route, true));
    }
    // A reversed seed may be authored under another kind; keep it reachable as the practical option.
    if (kind === "practical") for (const s of bridges.seeds) {
      if (s.kind === kind) continue;
      const a = idx(s.from), b = idx(s.to);
      if (a >= 0 && b >= 0 && a > b && s.reverse) out.push(seedPlank(s, route, true));
    }
    for (let i = 0; i < 3; i++) { const p = rulePlank(route, kind, i); if (p) out.push(p); }
    if (prefer) out.sort((x, y) => (y.seedId === prefer) - (x.seedId === prefer));
    return out;
  }

  /** One offer against a monthly budget. Annual billing and usage pricing are never folded in quietly. */
  function offerFit(o, budget) {
    const ok = [], no = [];
    for (const p of o.prices) {
      if (p.basis === "none" || p.basis === "free-allowance") ok.push(p);
      else if (p.basis === "usage") no.push({ p, why: "Billed by use, with no rate on record, so it cannot be placed inside a fixed budget." });
      else if (p.basis === "annual-equivalent") {
        const yearly = p.amount * 12;
        no.push({ p, why: `Billed yearly: about ${p.currency} ${yearly} at once, by arithmetic, which is not a USD ${budget} monthly budget.` });
      } else if (p.basis === "one-time") (p.amount <= budget ? ok : no).push(p.amount <= budget ? p : { p, why: `${p.label} is over USD ${budget}.` });
      else if (p.amount <= budget) ok.push(p);
      else no.push({ p, why: `${p.label} is over USD ${budget} per month.` });
    }
    return { fits: ok.length > 0, price: ok[0] || null, rejected: no };
  }
  const isPriced = o => o.prices.every(p => p.basis !== "none" && p.basis !== "free-allowance");

  function judge(plank, c) {
    const cut = [];
    if (c.local) {
      const away = plank.parts.filter(p => !boundaryOf(p).local);
      if (away.length) cut.push({ rule: "local", text: `${listNames(away.map(p => res(p).name))} ${away.length > 1 ? "take" : "takes"} data off your machines.` });
    }
    const o = plank.offer && offer(plank.offer);
    if (o && isPriced(o)) {
      if (c.spend === "none") cut.push({ rule: "have", text: `Needs ${o.name}, which is a new purchase.` });
      if (c.spend === "budget") {
        const f = offerFit(o, c.budget);
        if (!f.fits) cut.push({ rule: "budget", text: f.rejected.map(r => r.why).join(" ") });
      }
    }
    return cut;
  }

  function localVariant(plank) {
    const v = plank.variants?.local;
    if (!v) return null;
    const parts = [...new Set(v.parts)];
    const away = plank.parts.filter(p => !boundaryOf(p).local);
    const keep = plank.parts.filter(p => boundaryOf(p).local && !parts.includes(p));
    return { ...plank, id: plank.id + ":local", title: v.title, base: v.outcome, outcome: v.outcome, effects: [], parts: [...parts, ...keep],
      middles: [{ from: parts[0], to: parts[parts.length - 1], state: "missing", label: v.middle.label, kind: v.middle.kind }],
      unknown: v.unknown, changed: `Rewritten for “keep data local”: ${listNames(away.map(p => res(p).name))} left out.`, variants: null };
  }

  /** What the person sees: one plank per kind, plus what constraints cut and why. */
  function view(route, { constraints = {}, rejected = [], prefer = null } = {}) {
    const c = { local: false, spend: "any", budget: 10, ...constraints };
    const shown = [], cut = [], empty = [];
    for (const kind of KINDS) {
      let placed = false;
      for (const raw of candidates(route, kind, prefer)) {
        if (rejected.includes(raw.id)) continue;
        let p = raw, why = judge(p, c);
        if (why.length && c.local && why.every(w => w.rule === "local")) {
          const v = localVariant(p);
          if (v && !judge(v, c).length) { p = v; why = []; }
        }
        if (why.length) { if (!cut.some(x => x.plank.id === p.id)) cut.push({ plank: p, why }); continue; }
        if (rejected.includes(p.id)) continue;
        if (!placed) { shown.push(p); placed = true; }
      }
      if (!placed) empty.push(kind);
    }
    const hops = hopsOf(route);
    return { shown, cut, empty, hops, middles: hops.map(middleOf), shape: shapeOf(route) };
  }

  function ledger(budget) {
    return costs.opportunities.map(op => {
      const o = offer(op.offer), f = offerFit(o, budget);
      return { ...op, offerData: o, fits: f.fits, price: f.price, rejected: f.rejected };
    });
  }

  const swapsFor = parts => bridges.swaps.filter(s => parts.includes(s.from) && !parts.includes(s.to) && byId.has(s.to));

  /** A deterministic hand of n parts: distant from each other, preferring pairs not yet seen. */
  function drawHand(n, seq, { seen = [], pools = null, avoid = [], where = () => true } = {}) {
    const ids = facts.resources.map(r => r.id);
    if (seq === 0 && n === 2 && !pools && byId.has("apple-health") && byId.has("elevenlabs")) return ["apple-health", "elevenlabs"];
    const key = h => [...h].sort().join("+");
    let best = null;
    for (let t = 0; t < 400; t++) {
      const rnd = k => hash(`${seq}:${t}:${k}`);
      const hand = [];
      for (let k = 0; k < n; k++) {
        const pool = (pools ? pools[k % pools.length] : ids).filter(id => byId.has(id) && !hand.includes(id));
        const near = pool.filter(id => hand.every(h => distant(h, id)));
        const from = near.length ? near : pool;
        if (!from.length) break;
        hand.push(from[rnd(k) % from.length]);
      }
      if (hand.length < Math.min(n, ids.length)) continue;
      const pairKey = key(hand), bad = avoid.includes(pairKey) || !where(hand);
      const dead = hopsOf({ parts: hand }).filter(h => ["none", "gap"].includes(h.fit.kind)).length;
      if (!bad && !seen.includes(pairKey) && dead <= (n > 2 ? 1 : 0)) return hand;
      best ||= bad ? null : hand;
    }
    return best || ids.slice(0, n);
  }
  const handKey = h => [...h].sort().join("+");
  const hasSeed = h => bridges.seeds.some(s => h.includes(s.from) && h.includes(s.to));

  /** Variety, not volume: which shapes have been tried, and one invitation to an untried one. */
  function nudge(history) {
    const tried = new Set(history);
    const shapes = rules.shapes.map(s => ({ ...s, tried: tried.has(s.id) }));
    const next = shapes.find(s => !s.tried) || null;
    return { shapes, next };
  }


  // Turns whatever you are looking at into text for an agent. Plain template: nothing is sent, and nothing here has been run.
  // Intents: "sources" reads documentation, "ideas" generates options, "build" makes the smallest test.
  function promptSubject(c) {
    const name = id => res(id)?.name || id, ps = c.parts || [];
    if (c.focus === "stack") return "my whole stack";
    if (c.focus === "hop") { const h = hopsOf(c)[c.hopIndex]; return h ? `${name(h.from)} → ${name(h.to)}` : "one hop"; }
    if (c.focus === "bridge") return c.bridge.title;
    if (c.focus === "opportunity") return c.opportunity.outcome;
    if (c.focus === "swap") return `${name(c.swap.from)} or ${name(c.swap.to)}`;
    return ps.map(name).join(c.mode && ps.length > 1 ? " → " : ", ");
  }
  function promptFor(c, intent = "sources") {
    const said = s => String(s || "").trim(), name = id => res(id)?.name || id, cons = c.constraints || {}, x = c.experiment;
    const parts = (c.parts || []).filter(id => res(id)), isRoute = !!c.mode && parts.length > 1, subject = promptSubject(c);
    const hops = isRoute ? hopsOf({ parts, mode: c.mode }) : [], blocked = hops.filter(h => h.fit.kind === "gap");
    const hopText = h => { const m = middleOf(h), hidden = c.hideMiddles && m.state === "missing";
      return `${name(h.from)} → ${name(h.to)}: ${hidden ? "a middle is missing; I have not named it yet" : {
        direct: "shapes match, so nothing should be needed in between", missing: `missing middle: ${m.label}`,
        gap: `BLOCKED, no verified route. ${h.fit.statement || ""}`.trim(), none: "unknown, no rule names a middle" }[m.state]}`; };
    const list = a => (a || []).map(t => t.label).join("; ") || "nothing recorded";
    const lineParts = c.focus === "swap" ? [...parts, c.swap.to] : parts, compact = lineParts.length > 6;
    const partLine = id => { const r = res(id), ev = facts.evidence.find(e => e.id === r.evidence)?.label || r.evidence;
      if (compact) return `- ${r.name} (${placeOf(id).label}; ${ev}): ${r.act}.`;
      const src = [...(r.sources || []).map(s => facts.sources[s]).filter(s => s?.url).map(s => s.url), ...(r.docs ? [r.docs] : [])];
      return [`- ${r.name}: takes ${list(r.takes)}; ${r.act}; gives ${list(r.gives)}.`, `  Runs: ${placeOf(id).label}. Evidence: ${ev}, observed ${c.observed || facts.meta.observed_date}.`,
        r.unknown?.length ? `  Unknown: ${r.unknown.join("; ")}.` : "", src.length ? `  Starting points: ${src.join(", ")}` : ""].filter(Boolean).join("\n"); };
    const o = c.offer && offer(c.offer), test = said(c.bridge?.test || x?.test), success = said(c.bridge?.success || x?.success), dep = said(c.bridge?.dependency || x?.dependency);
    const WHERE = { stack: "I am looking at a map of my whole tech stack. Nothing is selected.", parts: "I picked these parts on my stack map. They are not connected yet.",
      part: "I am reading about one part of my stack.", route: `I connected these parts as a route${c.idea ? "" : ". I have not written my own idea yet"}.`,
      hop: "I am looking at one hop inside a route.", bridge: `I am looking at one suggested bridge, ${c.bridge?.origin || "a proposal"}. It has not been run.`,
      experiment: "I saved this as an experiment. It has not been run.", opportunity: "I am weighing whether one small addition would unlock something. I have not bought anything.",
      swap: "I am weighing swapping one part of a route for another." };
    const hop = c.focus === "hop" ? hops[c.hopIndex] : null;
    const ctx = [
      `## Where I am\n${WHERE[c.focus] || WHERE.parts}`,
      c.idea ? `## My own idea\n${said(c.idea)}` : "",
      c.exercise ? `## Practice I am doing\n${c.exercise.name}: ${c.exercise.ask}` : "",
      isRoute ? `## The route (${x?.shapeName || rules.shapes.find(s => s.id === shapeOf({ parts, mode: c.mode }))?.name || c.mode})\n${parts.map(name).join(" → ")}\n${hops.map(h => `- ${hopText(h)}`).join("\n")}` : "",
      hop ? `## Hop in focus\n${hopText(hop)}\n${name(hop.from)} gives ${hop.fit.give?.label || "nothing yet"}. ${name(hop.to)} takes ${hop.fit.take?.label || "nothing here"}.` : "",
      c.bridge ? `## Bridge in focus\n${c.bridge.title}\nOutcome: ${c.bridge.outcome}\nThe middle: ${c.bridge.steps.join("; then ")}\nNeeds: ${dep || "Not stated"}\nStill unknown: ${(c.bridge.unknown || []).join("; ") || "nothing recorded"}` : "",
      x ? `## Experiment\nIntended outcome: ${said(x.outcome) || "Not stated yet"}\nProposed bridge: ${said(x.bridge) || "Not stated yet"}\nMissing dependency: ${dep || "Not stated yet"}\nAssumptions to check: ${said(x.assumptions) || "none recorded"}\nOrigin: ${x.origin || "proposal"}.` : "",
      c.opportunity ? `## Opportunity\nGoal: ${c.opportunity.goal}\nUseful outcome: ${c.opportunity.outcome}\nMissing capability: ${c.opportunity.missing}\nWhat changes: ${c.opportunity.change}` : "",
      c.swap ? `## Swap\n${name(c.swap.from)} → ${name(c.swap.to)}: ${c.swap.label}\nGain: ${c.swap.gain}. Loss: ${c.swap.loss}. Unknown: ${c.swap.unknown}.` : "",
      o ? `## Possible purchase\n${o.name}: ${o.prices.map(p => p.label).join("; ")}. Recheck at ${o.url || "the official pricing page"} (last checked ${o.checked}). Do not buy or activate it.` : "",
      c.shown?.length ? `## Already suggested to me\n${c.shown.map(t => `- ${t}`).join("\n")}` : "",
      lineParts.length ? `## Parts, as evidenced\n${lineParts.map(partLine).join("\n")}` : "",
    ];
    const open = hops.filter(h => middleOf(h).state !== "direct");
    let tail;
    if (intent === "ideas") {
      const hopState = hop && middleOf(hop).state;
      const ask = c.focus === "hop" ? (hopState === "direct" ? "The shapes already match, so nothing is needed in between. Give three ideas for what this hop could carry: one useful every week, one playful, and one that only works because these two parts meet."
          : hopState === "gap" ? "This hop has no verified route. Give three ways to reach the same outcome without it: a different part, a manual step, or a different shape."
          : "Give three different ways to fill this hop: one using only what I already have, one done by hand, and one that surprises me.")
        : c.focus === "bridge" ? "Give four variations of this bridge: a smaller one, a reversed one, one with a part swapped for another from my stack, and one that loops back."
        : c.focus === "opportunity" ? "Give three things this addition would make possible, and one way to get most of the benefit without buying anything."
        : c.focus === "swap" ? "Give two ideas that only work with the original part and two that only work with the replacement."
        : c.focus === "part" ? "Give five ideas that pair this part with other parts of my stack, each with a different partner. Include one pairing that looks unlikely."
        : `Give five ideas, each a different shape: one hop, a chain through a third part, two sources into one, one source into two, and a loop.${parts.length > 2 ? " At least one should drop a part." : ""}`;
      tail = [`## Your task\nHelp me think about what ${subject} could do. This is for ideas: do not build anything, and keep research to what you need to stay honest.`,
        `## Start from me\n${c.idea ? "Start from my idea above and build on it. Do not replace it." : "Before you offer any ideas, ask me for my own idea in one sentence, then start from it."}`,
        `## What I want\n${ask}${c.shown?.length ? " Do not repeat what was already suggested to me." : ""}\nMake at least one practical, one playful, and one a question worth asking.\nFor each idea: the outcome in one sentence, the route through my parts, what is missing in the middle, the smallest test, and what it assumes. Use only parts listed here, unless you mark an addition as new.`,
        `## Report back\nNo scores, ratings or rankings for novelty, value or feasibility. Mark which ideas rest on assumptions nobody has checked.`];
    } else if (intent === "build") {
      tail = [test ? `## Your task\nBuild only the smallest test, then stop.\nSmallest test: ${test}\nSuccess looks like: ${success || "Not stated yet"}`
          : `## Your task\nPropose the smallest test that would show whether ${subject} can work${c.focus === "stack" || c.focus === "part" ? " with another part of my stack" : " together"}. Write it in three lines: what you would build, with what sample data, and what success looks like. Then wait for my go-ahead before building anything.`,
        `## How to work\n1. Before writing code, read the official documentation for each part involved and confirm the assumptions above. Trust what you find over this brief.\n2. Work in a new folder or branch. Start with made-up sample data.\n3. Build one hop at a time and run each hop before starting the next.${blocked.length ? `\n4. This route has a blocked hop (${blocked.map(h => `${name(h.from)} → ${name(h.to)}`).join(", ")}). Do not fake it or work around it silently. Stop there and report.` : ""}`,
        `## Stop and ask me if\n- A step needs a credential, a paid plan or real personal data.\n- The documentation contradicts this brief.\n- The test grows beyond what is written above.`,
        `## Report back\nWhat ran, with the commands. What was verified and what was not. What surprised you.${test ? " Whether the success condition was met." : ""}`];
    } else {
      const qs = [
        ...open.map(h => middleOf(h).state === "gap" ? `Is there any documented route from ${name(h.from)} to ${name(h.to)}? My notes say none is verified.` : `How, according to the official documentation, can ${name(h.from)} hand its output to ${name(h.to)}?`),
        ...(!isRoute && lineParts.length <= 6 ? lineParts.map(id => `What programmatic ways in and out does ${name(id)} offer (API, command line, export, automation hooks), and what does each need?`) : []),
        ...(lineParts.length > 6 ? ["For each part, find its official documentation and its programmatic ways in and out (API, command line, export, automation hooks)."] : []),
        ...(lineParts.length <= 3 ? lineParts.flatMap(id => (res(id).unknown || []).map(u => `${name(id)}: ${u}?`)) : []),
        ...(dep ? [`What would it take to provide this: ${dep}?`] : []),
        ...(c.opportunity && o ? [`Does ${o.name} actually provide this: ${c.opportunity.missing}? Confirm the current price, limits and conditions on the official page.`] : []),
        ...(c.swap ? [`Is the trade-off right? Check what ${name(c.swap.to)} gains and loses compared with ${name(c.swap.from)}.`] : []),
        "Which of my assumptions here are wrong or out of date?",
      ].slice(0, 12);
      tail = [`## Your task\nRead primary sources about ${subject} and tell me what is actually possible. This is research only: do not build, install, configure or sign in to anything.`,
        `## Questions to answer\n${qs.map((q, i) => `${i + 1}. ${q}`).join("\n")}`,
        `## How to work\nRead primary sources first: official documentation, API references, changelogs and pricing pages. Give the URL and the date you read it for every claim. Mark each claim as documented, tested or inferred. Note anything that has changed since ${c.observed || facts.meta.observed_date}.`,
        `## Report back\nFor each question: the answer, the source, and how sure you are. Then what I should read or try next. Do not score anything.`];
    }
    const limits = ["Ask me before using credentials, logging in to any account, or spending money.", "Do not send messages, publish, deploy, or change permissions or devices.", "Treat my personal data and notes as read-only.",
      cons.local ? "Keep data on my machines. Flag any step that would send it to a hosted service." : "", cons.spend === "none" ? "Use only what I already have. Do not propose a purchase." : "",
      cons.spend === "budget" ? `At most one purchase, up to USD ${cons.budget} a month, and only as a recommendation.` : ""].filter(Boolean);
    const HEAD = { sources: "Read the sources", ideas: "Generate ideas", build: "Build a small test" };
    return [`# ${HEAD[intent] || HEAD.sources}: ${subject}`, ...ctx, ...tail, `## Limits\n${limits.map(l => `- ${l}`).join("\n")}`].filter(Boolean).join("\n\n") + "\n";
  }
  const agentPrompt = (x, kind = "explore") => promptFor({ focus: "experiment", parts: x.parts, mode: x.mode, idea: x.idea, experiment: x, constraints: x.constraints, observed: x.observed, offer: x.offer }, kind === "implement" ? "build" : kind === "explore" ? "sources" : kind);

  return { agentPrompt, promptFor, promptSubject, res, facts, costs, rules, bridges, boundaryOf, placeOf, offer, fit, distant, hopsOf, shapeOf, middleOf, view, candidates, offerFit, ledger, swapsFor, drawHand, handKey, hasSeed, nudge, isPriced };
}
