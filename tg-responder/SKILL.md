---
name: tg-responder
description: Review and send Telegram response drafts queued by the responder daemon. Use when the user says "/tg-responder review", "/tg-responder status", "check telegram drafts", "review pending messages", or "telegram inbox".
---

# tg-responder — Telegram Communications Assistant

Review pending response drafts and manage the Telegram response queue.

## Commands

### review — Approve pending drafts

Read the responder queue and present drafts for approval:

```bash
python3 ~/.claude/skills/tg-responder/scripts/schema.py  # ensure DB exists
```

Then query the database:

```sql
-- Pending drafts needing approval
SELECT o.id, o.chat_id, o.draft_text, o.draft_reason, o.source,
       i.sender_name, i.text as original_text, i.urgency, i.category,
       datetime(i.received_at, 'unixepoch') as received
FROM outbox o
JOIN inbox i ON o.inbox_id = i.id
WHERE o.status = 'draft'
ORDER BY
  CASE i.urgency WHEN 'urgent' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
  o.created_at ASC;
```

For each draft, present to the user:
1. **Original message** — who sent it, when, what they said
2. **Draft response** — the proposed reply
3. **Options**: approve (send as-is), edit (modify then send), skip

To approve and send a draft:
1. Update outbox: `UPDATE outbox SET status = 'approved', final_text = draft_text, approved_at = strftime('%s','now') WHERE id = ?`
2. Send via telegram skill: `python3 ~/.claude/skills/telegram/scripts/telegram_fetch.py send --chat-id CHAT_ID --text "THE_TEXT"`
3. Update outbox with sent status and message_id

To skip: `UPDATE outbox SET status = 'skipped', updated_at = strftime('%s','now') WHERE id = ?`

### status — Queue statistics

```sql
-- Inbox stats
SELECT status, count(*) FROM inbox GROUP BY status;

-- Outbox stats
SELECT status, count(*) FROM outbox GROUP BY status;

-- Recent activity
SELECT sender_name, route, status, datetime(created_at, 'unixepoch')
FROM inbox ORDER BY created_at DESC LIMIT 10;
```

Report: pending count, drafts waiting, sent today, failed items.

## Database

Located at `~/Brains/data/telegram/responder.db`.

## Config

Located at `~/.claude/skills/tg-responder/config.yaml`. Edit contacts, modes, and ignore lists there.

## Worker

Start: `python3 ~/.claude/skills/tg-responder/scripts/worker.py`
One-shot: `python3 ~/.claude/skills/tg-responder/scripts/worker.py --once`
