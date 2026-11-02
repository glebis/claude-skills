# Bot publication announcement

## Trigger and destination

Send once after the actual agency-docs publication is verified on the live site, including the final aggregation deployment. Resolve the materials URL through `labs.json`; verify the recording matches this meeting and plays, and the materials page is accessible to the intended cohort. For Goal-Driven AI, also check the deployed curriculum feed's explicit `publication_status: published` and ISO `published_at`. A draft with an embedded recording does not satisfy this trigger. Do not change publication status merely to make notification run; report a blocked announcement if publication is incomplete.

Current verified mapping for **Goal-Driven AI 01**:
- Bot: `@agency_lab_companion_bot`
- Destination: `Goal-Driven AI 01 — Чат`, chat ID `-1004311316115`
- Private-chat link: `https://t.me/agency_lab_companion_bot?start=lesson{meeting}` (zero-padded meeting number)
- Do not additionally post to the announcements channel or send participant DMs. Personalized publication notifications are a separate PiBot workflow.

An explicit user override can authorize a one-time destination or draft announcement; record that exception without changing the normal publication gate. Follow the session's external-send authorization and approval rules. If destination or authorization is missing, prepare the complete draft first and request only the missing decision through Cenno.

## Message

Use the lab bot's native Telegram rich article rendering: heading, short paragraphs, bold feature labels, clickable links, inline code for skill names, and a URL button to the bot. Never post raw Markdown as plain text or expose a relative site URL. Example (replace links and content with verified values):

> **Запись встречи и материалы готовы**
>
> [Смотреть запись →](VERIFIED_RECORDING_URL)
> [Открыть конспект и материалы →](VERIFIED_MEETING_URL)
>
> В личном чате я помогу выбрать следующий шаг с учётом вашей задачи, найти записи занятий, подобрать упражнение, промпт или навыки и установить плагин курса. Если нет доступа к модели — подскажу, где искать бесплатные и открытые варианты.
>
> Напишите мне напрямую и нажмите Start. Расскажите, над чем работаете и где нужна помощь. Обратную связь о курсе или боте можно начать словами «У меня есть обратная связь» или “I have feedback”.
>
> [Открыть личный чат →](VERIFIED_BOT_START_URL)

Mention only deployed, verified features; describe features as new only when this release introduced them. Say the recording is ready/available, without claiming the bot uploaded it. Every “Напишите Глебу” reference must link to `https://t.me/glebkalinin`.

## Send and verify

Use PiBot's existing lab Telegram transport in `/Users/glebkalinin/ai_projects/pibot`, not the operator's Telegram account. Inspect the current transport API before using it. Load the lab sub-bot credential through PiBot's encrypted `SecretStore`; never print, persist in scripts, or log the token. Verify bot identity via `getMe`/transport `verify()` before sending. For a one-shot transport send, do not start polling or restart the running service.

Keep a durable private publication receipt keyed by cohort + meeting + destination, with content hash, publication timestamp, status, and returned message ID/link. Check it before sending. Write a pending receipt before the external call; mark sent only after confirmation. A transport instance's in-memory dedupe key is insufficient across retries. If a request times out or a pending receipt already exists, inspect recent bot messages and reconcile; never blindly resend. New deployment commits alone do not justify a duplicate announcement.

Verify the resulting message's sender, chat, links, button, and rich formatting in Telegram. Native rich articles can appear as `MessageMediaUnsupported` with empty text in older Telethon readers; inspect visually instead of treating this as send failure. Save the message ID and permalink in the receipt and Pipeline Report. If blocked, report the exact failed gate and retain the draft; do not claim the announcement was sent.
