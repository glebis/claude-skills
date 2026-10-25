#!/usr/bin/env node
// Fake headless CLI with native resume. Reads the prompt from stdin, logs argv and
// prompt to --log, and prints one JSON result line like `cmd -p --output-format json`.
// --plan works like fake-agent.mjs (ok | hang | fail), shared across calls via --state.
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";

const { values: o } = parseArgs({ strict: false, options: {
  plan: { type: "string", default: "ok" }, state: { type: "string" }, log: { type: "string" },
  resume: { type: "string" }, status: { type: "string", default: '{"stance":"converged"}' },
} });
const plan = o.plan.split(",");
const n = o.state && existsSync(o.state) ? Number(readFileSync(o.state, "utf8")) : 0;
if (o.state) writeFileSync(o.state, String(n + 1));
const step = plan[Math.min(n, plan.length - 1)];

let prompt = "";
process.stdin.on("data", (d) => (prompt += d));
process.stdin.on("end", () => {
  if (o.log) appendFileSync(o.log, JSON.stringify({ argv: process.argv.slice(2), resume: o.resume ?? null, n, step, prompt }) + "\n");
  if (step === "hang") return setInterval(() => {}, 1000);
  if (step === "fail") { console.error("fake failure"); process.exit(2); }
  const text = `headless reply ${n}\n\`\`\`roundtable-status\n${o.status}\n\`\`\`\n`;
  console.log(JSON.stringify({ type: "result", sessionId: o.resume ?? "fake-native-1", stopReason: "end_turn", finalText: text }));
});
