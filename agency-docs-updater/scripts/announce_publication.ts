// One-shot publication announcement (SKILL Step 10). First used for GDA 01 #02 (2026-10-17, message 40).
// Usage (from ~/ai_projects/pibot, age key in env):
//   npx tsx announce_publication.ts --meeting 02 --recording <youtube url> --lead "<one-sentence what we did>"
//     [--cohort goal-driven-ai-01] [--chat <id>, default $LAB_ANNOUNCE_CHAT_ID] [--bot agency_lab_companion_bot] [--published-at ISO]
// Per agency-docs-updater references/bot-announcement.md: PiBot lab transport, SecretStore-encrypted
// credential (read-only decrypt), getMe verification, durable receipt BEFORE the external call,
// no polling, never print the token.
import * as fs from "node:fs";
import * as path from "node:path";
import { createHash } from "node:crypto";
import { decryptJsonWithSops } from "/Users/glebkalinin/ai_projects/pibot/src/core/secrets.ts";
import { TelegramTransport } from "/Users/glebkalinin/ai_projects/pibot/src/transports/telegram.ts";

const arg = (k: string, d?: string) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const DATA = process.env.PIBOT_DATA_DIR || "/Users/glebkalinin/ai_projects/pibot/data";
const BOT_USERNAME = arg("bot", "agency_lab_companion_bot")!;
const CHAT_ID = arg("chat", process.env.LAB_ANNOUNCE_CHAT_ID) ?? "";
if (!/^-?\d+$/.test(CHAT_ID)) { console.log("missing --chat (or LAB_ANNOUNCE_CHAT_ID in the skill .env)"); process.exit(64); }
const COHORT = arg("cohort", "goal-driven-ai-01")!;
const MEETING = (arg("meeting") ?? "").padStart(2, "0");
const RECORDING = arg("recording") ?? "";
const LEAD = arg("lead") ?? "";
const PUBLISHED_AT = arg("published-at") ?? "";
if (!/^\d{2}$/.test(MEETING) || !/^https:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}/.test(RECORDING) || !LEAD) {
  console.log("usage: --meeting NN --recording <youtube url> --lead <sentence>"); process.exit(64);
}
// --feed: curriculum feed cohort (also the receipt key). A second track in one cohort has its
// own feed and page path, e.g. --feed goal-driven-ai-01-advanced --page /goal-driven-ai-01/advanced/01
const FEED = arg("feed", COHORT)!;
const PAGE = arg("page", `/${COHORT}/meetings/${MEETING}`)!;
const HEADING = arg("heading", `Запись встречи ${MEETING} и материалы готовы`)!;
const MATERIALS = `https://agency-lab.glebkalinin.com${PAGE}`;
const START = `https://t.me/${BOT_USERNAME}?start=lesson${MEETING}`;

const text = [
  `**${HEADING}**`,
  "",
  LEAD,
  "",
  `[Смотреть запись →](${RECORDING})`,
  `[Открыть конспект и материалы →](${MATERIALS})`,
  "",
  "В личном чате я помогу выбрать следующий шаг с учётом вашей задачи, найти записи занятий, подобрать упражнение, промпт или навыки и установить плагин курса. Если нет доступа к модели — подскажу, где искать бесплатные и открытые варианты.",
  "",
  "Напишите мне напрямую и нажмите Start. Расскажите, над чем работаете и где нужна помощь. Обратную связь о курсе или боте можно начать словами «У меня есть обратная связь» или “I have feedback”.",
].join("\n");
const reply_markup = { inline_keyboard: [[{ text: "Открыть личный чат →", url: START }]] };

const receiptDir = path.join(DATA, "publication-receipts");
const receiptPath = path.join(receiptDir, `${FEED}--${MEETING}--${CHAT_ID}.json`);
const contentHash = createHash("sha256").update(text + JSON.stringify(reply_markup)).digest("hex");

async function main() {
  if (fs.existsSync(receiptPath)) {
    const r = JSON.parse(fs.readFileSync(receiptPath, "utf8"));
    console.log(`STOP: receipt exists (status=${r.status}, message_id=${r.message_id ?? "-"}) — reconcile, never resend`);
    process.exit(2);
  }
  // Publication gate, checked on the LIVE feed (not the local file): the meeting must be published.
  if (!process.env.ANNOUNCE_SKIP_FEED_CHECK) {
    const feed: any = await fetch(`https://agency-lab.glebkalinin.com/api/curriculum/${FEED}?ts=${Date.now()}`, { signal: AbortSignal.timeout(15000) }).then(r => r.json());
    const m = (feed?.meetings ?? []).find((x: any) => x.number === MEETING);
    if (!m || m.publication_status !== "published") {
      console.log(`STOP: live feed ${FEED} shows meeting ${MEETING} as ${m?.publication_status ?? "missing"} — publication gate not met`);
      process.exit(5);
    }
  }
  const settings: any = await decryptJsonWithSops(path.join(DATA, "settings.enc.json"));
  const subBots: Record<string, { token: string; username?: string }> = settings?.telegram?.subBots ?? {};
  let transport: TelegramTransport | undefined;
  let agent = "";
  for (const [id, sb] of Object.entries(subBots)) {
    if (sb.username && sb.username.replace(/^@/, "") !== BOT_USERNAME) continue;
    const t = new TelegramTransport(sb.token, [CHAT_ID], { boundAgentId: id }); // no start(): no polling
    const who = await t.verify().catch(() => "");
    if (who.includes(BOT_USERNAME)) { transport = t; agent = id; break; }
  }
  if (!transport) { console.log(`STOP: no sub-bot verified as @${BOT_USERNAME}`); process.exit(3); }
  console.log(`verified @${BOT_USERNAME} (agent ${agent})`);

  fs.mkdirSync(receiptDir, { recursive: true, mode: 0o700 });
  const base = { cohort: COHORT, feed: FEED, page: PAGE, meeting: MEETING, chat_id: CHAT_ID, bot: BOT_USERNAME, content_sha256: contentHash,
    recording_url: RECORDING, materials_url: MATERIALS, published_at: PUBLISHED_AT || null };
  fs.writeFileSync(receiptPath, JSON.stringify({ ...base, status: "pending", attempted_at: new Date().toISOString() }, null, 2), { mode: 0o600, flag: "wx" });

  const api = (transport as any).bot.api;
  let sent: any; let format = "rich";
  try {
    sent = await api.sendRichMessage(CHAT_ID, { markdown: text }, { reply_markup });
  } catch (e: any) {
    // Only an unsupported method (404) may fall back; anything else stays pending for reconciliation.
    if (e?.error_code !== 404) { console.log(`STOP: send failed (${e?.error_code ?? "?"} ${String(e?.description ?? e).slice(0, 120)}) — receipt left pending`); process.exit(4); }
    format = "html-fallback";
    const html = text.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    sent = await api.sendMessage(CHAT_ID, html, { parse_mode: "HTML", reply_markup, link_preview_options: { is_disabled: true } });
  }
  const messageId = sent?.message_id;
  const link = `https://t.me/c/${CHAT_ID.replace(/^-100/, "")}/${messageId}`;
  fs.writeFileSync(receiptPath, JSON.stringify({ ...base, status: "sent", format, message_id: messageId, link, sent_at: new Date().toISOString() }, null, 2), { mode: 0o600 });
  console.log(`SENT format=${format} message_id=${messageId} link=${link}`);
}
main().catch(e => { console.log(`ERROR ${String(e?.message ?? e).slice(0, 200)}`); process.exit(1); });
