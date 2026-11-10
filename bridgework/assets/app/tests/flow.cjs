// Drives the real page. Needs the server on 4174 (or PORT) and Playwright. See README.
const { chromium } = require("playwright");
const out = process.env.SHOTS || "."; const URL_ = `http://127.0.0.1:${process.env.PORT || 4174}/index.html`;
let pass = 0, fail = 0; const ok = (c, m) => { c ? pass++ : fail++; console.log(`${c ? "ok  " : "FAIL"} ${m}`); };
const text = (p, s) => p.$$eval(s, n => n.map(x => x.innerText).join(" | "));
async function fresh(b, opt) { const c = await b.newContext(opt); const p = await c.newPage(); p.errs = []; p.on("pageerror", e => p.errs.push(e.message)); p.on("console", m => m.type() === "error" && p.errs.push(m.text())); await p.goto(URL_); await p.waitForSelector(".token", { state: "attached" }); await p.waitForTimeout(250); return p; }
const pair = async (p, ids) => { for (const i of ids) await p.click(`.token[data-id="${i}"]`); await p.click("#connectBtn"); await p.waitForTimeout(450); };
const idea = async (p, t = "my rough idea") => { await p.fill("#ideaText", t); await p.click("#revealBtn"); await p.waitForTimeout(350); };
(async () => {
  const b = await chromium.launch({ channel: "chrome", headless: true });
  let p = await fresh(b, { viewport: { width: 1440, height: 900 } });
  ok((await p.$$("#tokens .token")).length > 25, "first screen shows the stack");
  await p.click('.token[data-id="apple-health"]');
  ok(await p.getAttribute('.token[data-id="health-db"]', "data-fit") === "gap", "Health to SQLite shows as a gap, not a fit");
  await p.click('.token[data-id="health-db"]'); await p.click("#connectBtn"); await p.waitForTimeout(400);
  ok((await text(p, ".gapnote")).includes("No verified route"), "gap statement shown on the table");
  ok(await p.$(".hop.gap") !== null && await p.$(".rw path.gap") !== null, "gap hop drawn broken");
  await p.click('[data-act="back"]'); await p.waitForTimeout(300);

  await pair(p, ["apple-health", "elevenlabs"]);
  ok(await p.isDisabled("#revealBtn"), "reveal blocked before an idea");
  ok((await p.$$(".plank")).length === 0, "no bridges before the idea");
  await p.fill("#ideaText", "   "); ok(await p.isDisabled("#revealBtn"), "whitespace is not an idea");
  await p.screenshot({ path: out + "/a-idea.png" });
  await idea(p);
  const t1 = await text(p, ".plank h3"); ok((await p.$$(".plank")).length === 3, "three different bridges revealed"); ok(new Set(await p.$$eval(".plank", n => n.map(x => x.dataset.kind))).size === 3, "practical, playful and question");
  await p.click('.plank[data-kind="practical"] [data-act="why"]'); await p.waitForTimeout(150);
  const why = await text(p, "#panel"); ok(/Why this is suggested/.test(why) && /What remains unknown/.test(why) && /checked|, 6 Nov 2026/.test(why), "why panel shows reason, unknowns, date");
  await p.keyboard.press("Escape"); await p.waitForTimeout(150);
  const local0 = await text(p, ".plank h3"); await p.check('[name="local"]'); await p.waitForTimeout(150);
  const local1 = await text(p, ".plank h3"); ok(local0 !== local1, "keep data local changes suggestions"); ok((await text(p, "#cuts")).includes("off your machines"), "cut reason visible"); ok((await text(p, ".plank .changed")).includes("Rewritten"), "a bridge is rewritten for local");
  await p.screenshot({ path: out + "/b-local.png" });
  await p.uncheck('[name="local"]'); await p.waitForTimeout(100);
  const before = await text(p, '.plank[data-kind="practical"] .outcome');
  const third = await p.$('#tokens .token[data-id="obsidian"]'); await third.hover(); await p.waitForTimeout(200);
  ok((await p.$$(".plank.preview")).length > 0, "hover previews what a part would change"); await p.mouse.move(900, 300); await p.waitForTimeout(200);
  const box = await third.boundingBox(); const tgt = await (await p.$("#idea")).boundingBox();
  await p.mouse.move(box.x + 30, box.y + 10); await p.mouse.down(); await p.mouse.move(box.x + 120, box.y + 40, { steps: 5 }); await p.mouse.move(tgt.x + 60, tgt.y + 30, { steps: 8 }); await p.mouse.up(); await p.waitForTimeout(500);
  ok((await p.$$(".part")).length === 3, "drag a part onto the table adds it");
  const after = await text(p, '.plank[data-kind="practical"] .outcome'); ok(after !== before && /diary/.test(after), "third part changes the outcome");
  await p.screenshot({ path: out + "/c-third.png" });
  // variable shapes
  await p.click('.shapes [data-id="loop"]'); await p.waitForTimeout(250); ok((await p.$$(".hop")).length === 3, "loop adds a return hop"); ok((await text(p, ".plank .eff")).includes("next time"), "loop changes wording");
  await p.screenshot({ path: out + "/d-loop.png" });
  await p.click('.shapes [data-id="fanin"]'); await p.waitForTimeout(250); ok((await text(p, ".plank .eff")).includes("meet at"), "two into one changes wording"); await p.screenshot({ path: out + "/e-fanin.png" });
  await p.click('.shapes [data-id="fanout"]'); await p.waitForTimeout(250);
  await p.click('.shapes [data-id="hop"]'); await p.waitForTimeout(250); ok((await p.$$(".part")).length === 2, "one hop reduces the route");
  ok(await p.$(".shapes .tried") !== null, "tried shapes are marked");
  await p.click('.plank [data-act="experiment"]'); await p.waitForTimeout(150); await p.fill('[name="success"]', "I would listen twice"); await p.click("#saveExp"); await p.waitForTimeout(150);
  await p.click('[data-panel="trail"]'); await p.waitForTimeout(150);
  const tr = await text(p, "#trailList"); ok(/Assumptions:/.test(tr) && /Evidence at save:/.test(tr) && /2026-11-06/.test(tr) && /I would listen twice/.test(tr) && /my rough idea/.test(tr), "saved experiment keeps idea, assumptions, evidence, date");
  await p.reload(); await p.waitForSelector(".token", { state: "attached" }); ok((await p.textContent("#trailN")) === "1", "trail survives a reload");
  await p.evaluate(() => { location.hash = ""; }); await p.goto("about:blank"); await p.goto(URL_); await p.waitForSelector(".token", { state: "attached" }); await p.waitForTimeout(300);

  await pair(p, ["fathom", "shortcuts"]); await idea(p); const other = await text(p, ".plank h3"); ok(other !== t1, "changing the pair changes the bridges");
  const rv0 = await text(p, ".plank h3"); await p.click("#revBtn"); await p.waitForTimeout(250); const rv1 = await text(p, ".plank h3"); ok(rv0 !== rv1 && /write|End the day/i.test(rv1), "reverse changes the bridges");
  await p.click('[data-act="back"]'); await p.waitForTimeout(300);

  await pair(p, ["agent-vps", "nous"]); await idea(p);
  ok((await text(p, ".plank h3")).includes("persistent agent"), "paid bridge visible with no budget");
  await p.check('[name="spend"][value="budget"]'); await p.waitForTimeout(150);
  ok(!(await text(p, ".plank h3")).includes("persistent agent"), "USD 10 budget excludes the USD 20 addition"); ok((await text(p, "#cuts")).includes("USD 20 per month is over USD 10"), "reason names both amounts");
  await p.click('[data-panel="unlocks"]'); await p.waitForTimeout(150);
  ok(await p.getAttribute('[data-offer="nous-plus"]', "data-fits") === "false" && await p.getAttribute('[data-offer="elevenlabs-starter"]', "data-fits") === "true", "ledger separates in and out of budget");
  ok(await p.getAttribute('[data-offer="firecrawl-hobby"]', "data-fits") === "false", "annual-equivalent price not folded in");
  const led = await text(p, "#panel"); ok(/checked 6 Nov 2026/.test(led) && /New capability/.test(led) && /More quota/.test(led) && /Free grant/.test(led), "ledger shows dates and capability vs quota");
  await p.screenshot({ path: out + "/f-unlocks.png" });
  await p.fill("#ledgerBudget", "20"); await p.waitForTimeout(150); ok(await p.getAttribute('[data-offer="nous-plus"]', "data-fits") === "true", "raising the budget admits it");
  await p.keyboard.press("Escape"); await p.waitForTimeout(100);
  await p.click('[data-panel="practice"]'); await p.click('[data-act="startExercise"][data-id="transfer"]'); await p.waitForTimeout(450);
  await p.fill("#ideaText", "unaided attempt"); ok(await p.isDisabled("#revealBtn"), "transfer: no examples until saved");
  await p.click("#keepIdea"); await p.waitForTimeout(100); await p.click("#saveExp"); await p.waitForTimeout(150); ok(!(await p.isDisabled("#revealBtn")), "transfer: compare opens after saving");
  for (const id of ["distant", "middle", "swap", "shortest", "long", "fanin", "fanout", "loop"]) { await p.click('[data-panel="practice"]'); await p.click(`[data-act="startExercise"][data-id="${id}"]`); await p.waitForTimeout(350); ok((await text(p, ".exbar")).length > 10, `exercise ${id} starts`); }
  await p.click('[data-panel="practice"]'); await p.click('[data-act="startExercise"][data-id="swap"]'); await p.waitForTimeout(350); await idea(p); await p.click("#swapBtn"); await p.waitForTimeout(150); const sw = await text(p, "#panel"); ok(/You gain/.test(sw) && /You lose/.test(sw), "swap shows trade-off"); const n0 = await text(p, ".part h3"); await p.click('[data-act="applySwap"]'); await p.waitForTimeout(300); ok(n0 !== await text(p, ".part h3"), "swap replaces the part");
  await p.click('[data-act="back"]'); await p.waitForTimeout(300);
  // Draw sizes, grouping, lens
  await p.click('#handSize [data-n="4"]'); await p.click("#drawBtn"); await p.waitForTimeout(450); ok((await p.$$(".part")).length === 4, "draw honours a hand of four"); await p.screenshot({ path: out + "/g-four.png" }); await p.click('[data-act="back"]'); await p.waitForTimeout(300);
  await p.click('.token[data-id="exa"]'); await p.click('.token[data-id="firecrawl"]'); await p.click('[data-act="groupHand"]'); await p.fill("#groupName", "Things that fetch"); await p.keyboard.press("Enter"); await p.waitForTimeout(450); ok((await text(p, ".cluster")).includes("Things that fetch"), "group appears on canvas");
  await p.keyboard.press("l"); await p.waitForTimeout(100); ok(await p.isVisible("#lensRing"), "lens opens by key"); await p.keyboard.press("ArrowRight"); await p.keyboard.press("p"); await p.waitForTimeout(100); await p.screenshot({ path: out + "/h-lens.png" }); await p.keyboard.press("l");
  await p.keyboard.press("e"); await p.waitForTimeout(100); ok(await p.isVisible('#tokens .token[data-id="nous"] .f-evidence'), "evidence view floods the canvas"); await p.keyboard.press("v");
  await p.click('[data-panel="parts"]'); await p.fill("#partSearch", "nous"); await p.click('#partList li:not([hidden]) button'); await p.keyboard.press("Escape"); await p.keyboard.press("Escape"); await p.waitForTimeout(100);
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "no page errors: " + p.errs.join("; "));

  // Direct manipulation, fresh state
  p = await fresh(b, { viewport: { width: 1440, height: 900 } });
  const a0 = await (await p.$('.token[data-id="exa"] .port.out')).boundingBox(), b0 = await (await p.$('.token[data-id="shortcuts"]')).boundingBox();
  await p.mouse.move(a0.x + 8, a0.y + 8); await p.mouse.down(); await p.mouse.move(a0.x + 60, a0.y - 30, { steps: 4 }); await p.waitForTimeout(80);
  ok(await p.$('#wires .band') !== null, "dragging from a port rubber-bands a cable"); await p.mouse.move(b0.x + 60, b0.y + 20, { steps: 8 }); await p.mouse.up(); await p.waitForTimeout(450);
  ok((await text(p, ".part h3")).includes("Shortcuts"), "dropping the cable connects the parts");
  await p.click('[data-act="toggleSketch"]'); await p.waitForTimeout(80); const c0 = await (await p.$("#sketch")).boundingBox();
  await p.mouse.move(c0.x + 30, c0.y + 30); await p.mouse.down(); await p.mouse.move(c0.x + 120, c0.y + 90, { steps: 5 }); await p.mouse.up(); await p.waitForTimeout(80);
  ok(!(await p.isDisabled("#revealBtn")), "a sketch alone unlocks the reveal"); await p.click("#revealBtn"); await p.waitForTimeout(350);
  const r0 = await text(p, '.plank[data-kind="playful"] h3'); await p.click('.plank[data-kind="playful"] [data-act="reject"]'); await p.waitForTimeout(200); const r1 = await text(p, '.plank[data-kind="playful"] h3'); ok(r0 !== r1, "Not this brings an alternative");
  await p.click('[data-act="back"]'); await p.waitForTimeout(200); ok((await text(p, "#toast")).includes("Left the route"), "leaving offers a return"); await p.click("#toast button"); await p.waitForTimeout(450); ok((await p.$$(".plank")).length > 0, "return restores the route"); await p.click('[data-act="back"]'); await p.waitForTimeout(400);
  await p.keyboard.press("l"); await p.waitForTimeout(100); const inLens = await p.evaluate(() => { const L = __bw.S.lens; return [...document.querySelectorAll("#lensWorld .token")].filter(t => { const r = t.getBoundingClientRect(); return Math.hypot(r.x + r.width / 2 - L.x, r.y + r.height / 2 - 52 - L.y) < L.r; }).length; }); ok(inLens > 0, "lens sits over parts"); await p.screenshot({ path: out + "/h2-lens.png" }); await p.keyboard.press("l");
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "manipulation run has no page errors");

  // Keyboard only, fresh state
  p = await fresh(b, { viewport: { width: 1280, height: 800 } });
  await p.focus('.token[data-id="fathom"]'); await p.keyboard.press("Enter"); await p.keyboard.press("ArrowRight"); await p.keyboard.press("ArrowRight"); await p.keyboard.press("Space");
  ok((await p.evaluate(() => __bw.S.hand.length)) === 2, "keyboard: arrows move, Enter and Space pick"); await p.keyboard.press("c"); await p.waitForTimeout(450);
  ok(await p.evaluate(() => document.activeElement.id) === "ideaText", "keyboard: focus lands in the idea box"); await p.keyboard.type("typed idea");
  await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); ok(await p.evaluate(() => document.activeElement.id) === "revealBtn", "keyboard: tab reaches reveal"); await p.keyboard.press("Enter"); await p.waitForTimeout(300);
  ok((await p.$$(".plank")).length > 0, "keyboard: bridges revealed");
  await p.keyboard.press("t"); await p.waitForTimeout(150); await p.keyboard.type("obsid"); await p.waitForTimeout(100); await p.keyboard.press("Tab"); await p.keyboard.press("Enter"); await p.waitForTimeout(300);
  ok((await p.$$(".part")).length === 3, "keyboard: add a part by filter");
  await p.focus('.plank [data-act="experiment"]'); await p.keyboard.press("Enter"); await p.waitForTimeout(150); await p.focus("#saveExp"); await p.keyboard.press("Enter"); await p.waitForTimeout(150); ok((await p.textContent("#trailN")) === "1", "keyboard: experiment saved");
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "keyboard run has no page errors");

  // Panels leave the route alone, at the width where they used to crush it
  p = await fresh(b, { viewport: { width: 1000, height: 760 } });
  await p.evaluate(() => ["shazam", "ollama", "obsidian"].forEach(i => document.querySelector(`.token[data-id="${i}"]`).click())); await p.click("#connectBtn"); await p.waitForTimeout(500);
  const rects = () => p.$$eval(".part", n => n.map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height].map(Math.round).join(); }).join("|"));
  const spill = () => p.$$eval(".part", n => n.filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().width < 128).length);
  const rect0 = await rects(); await p.click(".part .more"); await p.waitForTimeout(300);
  ok(await rects() === rect0, "opening a panel leaves the route where it was"); ok(await spill() === 0, "no card spills or drops below a legible width");
  const panelLeft = await p.$eval("#panel", e => e.getBoundingClientRect().left); ok(await p.$$eval(".part", (n, l) => n.every(e => e.getBoundingClientRect().right <= l), panelLeft), "no card sits under the panel");
  await p.keyboard.press("Escape"); await p.waitForTimeout(150); await idea(p, "a diary of what I hear");
  await p.mouse.move(300, 500); await p.mouse.wheel(0, 300); await p.waitForTimeout(150);
  const top0 = await p.$eval(".plank", e => Math.round(e.getBoundingClientRect().top)); await p.click('.plank [data-act="why"]'); await p.waitForTimeout(300);
  ok(await p.$eval(".plank", e => Math.round(e.getBoundingClientRect().top)) === top0, "opening a panel keeps your scroll position"); await p.keyboard.press("Escape"); await p.waitForTimeout(150);

  // A control near the bottom edge must not move away from the pointer on press
  await p.click(`[data-act="back"]`); await p.waitForTimeout(300);
  await p.evaluate(() => ["shazam", "ollama", "obsidian"].forEach(i => document.querySelector(`.token[data-id="${i}"]`).click())); await p.click("#connectBtn"); await p.waitForTimeout(500);
  await p.click(`.shapes [data-id="fanin"]`); await p.waitForTimeout(300); await p.fill("#ideaText", "a diary of what I hear"); await p.click("#revealBtn"); await p.waitForTimeout(300);
  ok(await p.evaluate(() => __bw.S.revealed), "reveal works when its button sits near the bottom edge");
  await p.click(`.shapes [data-id="chain"]`); await p.waitForTimeout(300);

  // Agent prompt
  await p.click('.plank [data-act="experiment"]'); await p.waitForTimeout(150); await p.click("#saveExp"); await p.waitForTimeout(200);
  const pr = await p.inputValue("#promptText"); ok(/# Read the sources/.test(pr) && /a diary of what I hear/.test(pr) && /Shazam → Ollama on the home server → Obsidian/.test(pr), "saving opens an explore prompt with the idea and route");
  await p.click('[data-act="intent"][data-id="build"]'); await p.waitForTimeout(150); ok(/Build only the smallest test/.test(await p.inputValue("#promptText")), "implement prompt is different");
  await p.screenshot({ path: out + "/p-prompt.png" }); await p.context().grantPermissions(["clipboard-read", "clipboard-write"]); await p.click("#copyPrompt"); await p.waitForTimeout(150);
  ok(/Build only the smallest test/.test(await p.evaluate(() => navigator.clipboard.readText())), "copy puts the prompt on the clipboard");
  await p.click('[data-panel="trail"]'); await p.waitForTimeout(150); await p.click('[data-act="agent"][data-scope="experiment"]'); await p.waitForTimeout(150); ok(await p.$("#promptText") !== null, "the trail reopens a prompt");
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "panel run has no page errors: " + p.errs.join("; "));

  // A prompt from every step
  p = await fresh(b, { viewport: { width: 1440, height: 900 } });
  const prompt = () => p.inputValue("#promptText"), clean = t => !/undefined|\[object|NaN/.test(t);
  await p.click("#agentBtn"); await p.waitForTimeout(150); let t = await prompt(); ok(/# Read the sources: my whole stack/.test(t) && clean(t), "stack: top-bar Prompt with nothing selected");
  await p.click('[data-act="intent"][data-id="ideas"]'); await p.waitForTimeout(100); ok(/ask me for my own idea/.test(await prompt()), "ideas prompt asks for your idea first");
  await p.keyboard.press("Escape"); await p.waitForTimeout(100);
  await p.click('.token[data-id="shazam"]'); await p.click('#hand [data-act="agent"]'); await p.waitForTimeout(150); ok(/Generate ideas: Shazam/.test(await prompt()), "one selected part: prompt from the hand");
  await p.keyboard.press("Escape"); await p.click('.token[data-id="obsidian"]'); await p.click('#hand [data-act="agent"]'); await p.waitForTimeout(150); ok(/Shazam, Obsidian/.test(await prompt()) && /not connected yet/.test(await prompt()), "several parts: prompt before connecting");
  await p.keyboard.press("Escape"); await p.click("#connectBtn"); await p.waitForTimeout(450);
  await p.click("#routePrompt"); await p.waitForTimeout(150); t = await prompt(); ok(/## The route/.test(t) && /I have not named it yet/.test(t), "route prompt before the idea keeps the middle hidden");
  await p.keyboard.press("Escape"); await p.click(".hop"); await p.waitForTimeout(150); await p.click('#panel [data-act="agent"][data-scope="hop"]'); await p.waitForTimeout(150);
  ok(/## Hop in focus/.test(await prompt()), "hop prompt"); await p.click('[data-act="agentBack"]'); await p.waitForTimeout(150); ok((await text(p, "#panel h2")).includes("→"), "back returns to the hop");
  await p.keyboard.press("Escape"); await p.click('.part[data-id="shazam"] .more'); await p.waitForTimeout(150); await p.click('#panel [data-act="agent"][data-scope="part"]'); await p.waitForTimeout(150);
  ok(/Shazam/.test(await prompt()) && /reading about one part/.test(await prompt()), "part prompt from the part panel"); await p.keyboard.press("Escape");
  await idea(p, "songs into notes"); await p.click('.plank [data-act="agent"]'); await p.waitForTimeout(150); await p.click('[data-act="intent"][data-id="build"]'); await p.waitForTimeout(100);
  t = await prompt(); ok(/## Bridge in focus/.test(t) && /Build only the smallest test/.test(t) && /songs into notes/.test(t), "bridge build prompt carries your idea and the test");
  await p.keyboard.press("Escape"); await p.keyboard.press("q"); await p.waitForTimeout(150); ok(/## Already suggested to me/.test(await prompt()), "Q key prompts about the route, listing what was suggested");
  await p.keyboard.press("Escape"); await p.click('[data-panel="unlocks"]'); await p.waitForTimeout(150); await p.click('.opp [data-act="agent"]'); await p.waitForTimeout(150);
  t = await prompt(); ok(/## Opportunity/.test(t) && /Do not buy/.test(t) && clean(t), "unlock prompt never buys");
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "prompt run has no page errors: " + p.errs.join("; "));

  // Dark theme
  p = await fresh(b, { viewport: { width: 1440, height: 900 }, colorScheme: "dark" }); await pair(p, ["exa", "obsidian"]); await idea(p); await p.screenshot({ path: out + "/k-dark.png" });
  ok(await p.evaluate(() => getComputedStyle(document.body).backgroundColor) !== "rgb(232, 236, 235)", "dark theme applies");

  // Mobile
  p = await fresh(b, { viewport: { width: 375, height: 760 }, hasTouch: true, isMobile: true });
  await p.screenshot({ path: out + "/m1-field.png" });
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "mobile: no horizontal page scroll");
  await p.tap("#drawBtn"); await p.waitForTimeout(500); await p.screenshot({ path: out + "/m2-table.png" });
  await p.fill("#ideaText", "phone idea"); await p.tap("#revealBtn"); await p.waitForTimeout(400); ok((await p.$$(".plank")).length > 0, "mobile: reveal works");
  await p.tap("#addBtn"); await p.waitForTimeout(200); await p.screenshot({ path: out + "/m3-add.png" }); await p.fill("#partSearch", "obsid"); await p.tap('#partList li:not([hidden]) button'); await p.waitForTimeout(300); ok((await p.$$(".part")).length === 3, "mobile: add a part");
  await p.tap('.shapes [data-id="loop"]'); await p.waitForTimeout(250);
  await p.$eval("#viewport", v => v.scrollTop = 0); await p.screenshot({ path: out + "/m4-loop.png" });
  await p.$eval('[name="local"]', n => n.scrollIntoView()); await p.waitForTimeout(100); await p.tap('[name="local"]'); await p.waitForTimeout(150); ok((await text(p, "#cuts")).length > 0 || (await p.$("#noBridge")) !== null, "mobile: constraint applies");
  await p.screenshot({ path: out + "/m5-cons.png" });
  ok(await p.evaluate(() => document.querySelector("#viewport").scrollWidth <= innerWidth + 1), "mobile: table fits width");
  await p.tap("#agentBtn"); await p.waitForTimeout(200); ok(await p.$eval("#copyPrompt", e => e.getBoundingClientRect().bottom <= innerHeight), "mobile: Copy prompt is visible without scrolling");
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "mobile: top bar with Prompt has no horizontal scroll"); await p.screenshot({ path: out + "/m6-prompt.png" });
  ok(p.errs.filter(e => !/favicon/.test(e)).length === 0, "mobile run has no page errors: " + p.errs.join("; "));
  await b.close(); console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
