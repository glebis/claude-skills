#!/usr/bin/env python3
"""Queue worker for tg-responder.

Picks pending inbox items via atomic lease, routes them:
- course_inquiry → auto-send template
- needs_classification | known_contact → spawn Claude agent
Writes results to outbox. Never sends LLM-generated text directly.
"""

import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from classify import load_config
from schema import get_db

logger = logging.getLogger(__name__)

WORKER_ID = f"worker-{uuid.uuid4().hex[:8]}"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class Worker:
    def __init__(self):
        self.config = load_config()
        self.db = get_db()
        self.running = False

        self._lease_seconds = self.config.worker.get("lease_duration_seconds", 300)
        self._max_attempts = self.config.worker.get("max_attempts", 3)
        self._retry_delay = self.config.worker.get("retry_delay_seconds", 60)
        self._claude_timeout = self.config.worker.get("claude_timeout_seconds", 300)
        self._claude_max_turns = self.config.worker.get("claude_max_turns", 15)
        self._signal_path = Path(self.config.daemon.get("signal_path", "/tmp/tg-responder-signal"))

    def claim_next(self) -> sqlite3.Row | None:
        """Atomically claim the next pending inbox item."""
        now = int(time.time())
        lease_until = now + self._lease_seconds

        cursor = self.db.execute(
            """UPDATE inbox SET
                status = 'processing',
                locked_at = ?,
                lease_until = ?,
                worker_id = ?,
                updated_at = ?
            WHERE id = (
                SELECT i.id FROM inbox i
                WHERE i.status IN ('pending', 'retrying')
                AND (i.lease_until IS NULL OR i.lease_until < ?)
                AND (i.next_retry_at IS NULL OR i.next_retry_at <= ?)
                AND i.chat_id NOT IN (
                    SELECT chat_id FROM inbox
                    WHERE status = 'processing' AND lease_until >= ?
                )
                ORDER BY i.priority ASC, i.created_at ASC
                LIMIT 1
            )
            RETURNING *""",
            (now, lease_until, WORKER_ID, now, now, now, now),
        )
        row = cursor.fetchone()
        self.db.commit()
        return row

    def handle_course_inquiry(self, row: sqlite3.Row) -> None:
        """Send course template response directly (no LLM)."""
        now = int(time.time())

        template = self.db.execute(
            "SELECT response_text FROM templates WHERE name = 'lab_signup' AND active = 1"
        ).fetchone()

        if not template:
            logger.error("No active lab_signup template found")
            self._mark_failed(row["id"], "No template found")
            return

        dedup_key = f"template-{row['chat_id']}-{row['message_id']}"

        self.db.execute(
            """INSERT OR IGNORE INTO outbox (
                inbox_id, chat_id, reply_to_message_id,
                draft_text, final_text,
                status, dedup_key, source,
                draft_created_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'approved', ?, 'template', ?, ?, ?)""",
            (
                row["id"], row["chat_id"], row["message_id"],
                template["response_text"], template["response_text"],
                dedup_key,
                now, now, now,
            ),
        )

        sent = self._send_outbox_item(dedup_key)

        if sent:
            self.db.execute(
                "UPDATE inbox SET status = 'sent', updated_at = ? WHERE id = ?",
                (int(time.time()), row["id"]),
            )
            self.db.commit()
            logger.info(f"Auto-sent course template to {row['sender_name']}")
        else:
            self._mark_failed(row["id"], "Template send failed")

    def _send_outbox_item(self, dedup_key: str) -> bool:
        """Send an outbox item via the telegram skill. Returns True on success."""
        now = int(time.time())

        item = self.db.execute(
            "SELECT * FROM outbox WHERE dedup_key = ?", (dedup_key,)
        ).fetchone()
        if not item:
            return False

        self.db.execute(
            "UPDATE outbox SET status = 'sending', sending_started_at = ?, updated_at = ? WHERE id = ?",
            (now, now, item["id"]),
        )
        self.db.commit()

        try:
            result = subprocess.run(
                [
                    "python3",
                    str(Path.home() / ".claude/skills/telegram/scripts/telegram_fetch.py"),
                    "send",
                    "--chat", str(item["chat_id"]),
                    "--text", item["final_text"] or item["draft_text"],
                ],
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode == 0:
                sent_data = json.loads(result.stdout)
                sent_msg_id = sent_data.get("message_id")

                self.db.execute(
                    "UPDATE outbox SET status = 'sent', sent_at = ?, sent_message_id = ?, updated_at = ? WHERE id = ?",
                    (int(time.time()), sent_msg_id, int(time.time()), item["id"]),
                )
                self.db.commit()
                return True
            else:
                raise RuntimeError(f"Send failed: {result.stderr}")

        except Exception as e:
            self.db.execute(
                "UPDATE outbox SET status = 'failed', send_error = ?, attempt_count = attempt_count + 1, updated_at = ? WHERE id = ?",
                (str(e), int(time.time()), item["id"]),
            )
            self.db.commit()
            logger.error(f"Send error: {e}")
            return False

    def handle_classification(self, row: sqlite3.Row) -> None:
        """Spawn Claude to classify and draft a response."""
        now = int(time.time())

        context = self._fetch_context(row["chat_id"], row["sender_name"])

        classify_prompt = PROMPTS_DIR / "classify.md"
        if not classify_prompt.exists():
            logger.error("Missing classify.md prompt")
            self._mark_failed(row["id"], "Missing classify.md prompt")
            return

        system_prompt = classify_prompt.read_text()

        user_prompt = json.dumps({
            "sender_name": row["sender_name"],
            "contact_mode": row["contact_mode"],
            "message_text": row["text"],
            "has_media": bool(row["has_media"]),
            "media_type": row["media_type"],
            "context": context,
        }, ensure_ascii=False)

        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)

        cmd = [
            "claude", "-p", user_prompt,
            "--system-prompt", system_prompt,
            "--output-format", "json",
            "--max-turns", str(self._claude_max_turns),
            "--allowedTools", "",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self._claude_timeout, env=env,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude exit {result.returncode}: {result.stderr[:500]}")

            claude_output = self._parse_claude_json(result.stdout)

            if not claude_output:
                raise RuntimeError("Could not parse Claude output as JSON")

            VALID_CATEGORIES = {"technical", "personal", "course_followup", "spam", "unknown"}
            VALID_URGENCIES = {"urgent", "normal", "low"}

            category = claude_output.get("category", "unknown")
            if category not in VALID_CATEGORIES:
                category = "unknown"
            confidence = claude_output.get("confidence", 0.0)
            draft = claude_output.get("draft")
            draft_reason = claude_output.get("draft_reason", "")
            urgency = claude_output.get("urgency", "normal")
            if urgency not in VALID_URGENCIES:
                urgency = "normal"

            self.db.execute(
                """UPDATE inbox SET
                    category = ?, classification_confidence = ?,
                    auto_decision_reason = ?, urgency = ?,
                    status = 'draft_ready', updated_at = ?
                WHERE id = ?""",
                (category, confidence, draft_reason, urgency, now, row["id"]),
            )

            if draft:
                dedup_key = f"classify-{row['id']}-{row['attempt_count']}"
                self.db.execute(
                    """INSERT OR IGNORE INTO outbox (
                        inbox_id, chat_id, reply_to_message_id,
                        draft_text, status, dedup_key, source, draft_reason,
                        draft_created_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 'draft', ?, 'classification', ?, ?, ?, ?)""",
                    (
                        row["id"], row["chat_id"], row["message_id"],
                        draft, dedup_key, draft_reason,
                        now, now, now,
                    ),
                )

            self.db.commit()
            logger.info(
                f"Classified {row['sender_name']}: {category} "
                f"(confidence={confidence:.2f}, draft={'yes' if draft else 'no'})"
            )

        except subprocess.TimeoutExpired:
            self._mark_failed(row["id"], f"Claude timeout after {self._claude_timeout}s")
        except Exception as e:
            self._mark_failed(row["id"], str(e))

    def _parse_claude_json(self, raw_output: str) -> dict | None:
        """Parse Claude CLI JSON output to extract the result."""
        try:
            data = json.loads(raw_output)
            if isinstance(data, list):
                for event in data:
                    if event.get("type") == "result" and event.get("result"):
                        try:
                            return json.loads(event["result"])
                        except json.JSONDecodeError:
                            return None
            elif isinstance(data, dict) and "result" in data:
                try:
                    return json.loads(data["result"])
                except json.JSONDecodeError:
                    return None
        except json.JSONDecodeError:
            pass
        return None

    def _fetch_context(self, chat_id: int, sender_name: str) -> str:
        """Fetch recent conversation context for a chat."""
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(Path.home() / ".claude/skills/telegram/scripts/telegram_fetch.py"),
                    "recent", "--chat", sender_name, "--limit", "5", "--json",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return result.stdout[:3000]
        except Exception as e:
            logger.warning(f"Context fetch failed: {e}")
        return ""

    def _mark_failed(self, inbox_id: int, error: str) -> None:
        """Mark an inbox item as failed, with retry logic."""
        now = int(time.time())
        row = self.db.execute("SELECT attempt_count FROM inbox WHERE id = ?", (inbox_id,)).fetchone()
        attempts = (row["attempt_count"] if row else 0) + 1

        if attempts >= self._max_attempts:
            self.db.execute(
                "UPDATE inbox SET status = 'dead', last_error = ?, attempt_count = ?, updated_at = ? WHERE id = ?",
                (error, attempts, now, inbox_id),
            )
        else:
            retry_at = now + self._retry_delay * attempts
            self.db.execute(
                """UPDATE inbox SET status = 'retrying', last_error = ?,
                   attempt_count = ?, next_retry_at = ?, lease_until = NULL, updated_at = ?
                WHERE id = ?""",
                (error, attempts, retry_at, now, inbox_id),
            )
        self.db.commit()
        logger.warning(f"Failed inbox {inbox_id} (attempt {attempts}): {error}")

    def is_stale(self, row: sqlite3.Row) -> bool:
        """Check if a row is stale (newer message exists in same chat)."""
        if not self.config.worker.get("stale_check", True):
            return False

        newer = self.db.execute(
            "SELECT 1 FROM inbox WHERE chat_id = ? AND received_at > ? AND id != ? LIMIT 1",
            (row["chat_id"], row["received_at"], row["id"]),
        ).fetchone()
        return newer is not None

    def process_one(self) -> bool:
        """Process one inbox item. Returns True if work was done."""
        row = self.claim_next()
        if not row:
            return False

        logger.info(f"Processing: {row['sender_name']} ({row['route']})")

        if self.is_stale(row):
            now = int(time.time())
            self.db.execute(
                "UPDATE inbox SET status = 'skipped', auto_decision_reason = 'stale', updated_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            self.db.commit()
            logger.info(f"Skipped stale message from {row['sender_name']}")
            return True

        if row["route"] == "course_inquiry":
            self.handle_course_inquiry(row)
        elif row["route"] in ("needs_classification", "known_contact"):
            self.handle_classification(row)
        else:
            logger.warning(f"Unknown route: {row['route']}")

        return True

    def run_once(self) -> int:
        """Process all pending items. Returns count processed."""
        count = 0
        while self.process_one():
            count += 1
        return count

    def run_loop(self) -> None:
        """Run worker loop, waiting for signals."""
        self.running = True
        logger.info(f"Worker {WORKER_ID} started")

        while self.running:
            count = self.run_once()
            if count:
                logger.info(f"Processed {count} item(s)")

            try:
                if self._signal_path.exists():
                    self._signal_path.unlink(missing_ok=True)
                    continue

                time.sleep(5)
            except KeyboardInterrupt:
                self.running = False

        logger.info("Worker stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    import argparse
    parser = argparse.ArgumentParser(description="tg-responder worker")
    parser.add_argument("--once", action="store_true", help="Process pending items and exit")
    args = parser.parse_args()

    worker = Worker()
    if args.once:
        count = worker.run_once()
        print(f"Processed {count} item(s)")
    else:
        worker.run_loop()
