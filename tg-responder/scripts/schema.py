#!/usr/bin/env python3
"""Initialize and migrate responder.db."""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / "Brains" / "data" / "telegram" / "responder.db"

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inbox (
    id                        INTEGER PRIMARY KEY,
    chat_id                   INTEGER NOT NULL,
    message_id                INTEGER NOT NULL,
    sender_id                 INTEGER,
    sender_name               TEXT,
    text                      TEXT,
    has_media                 INTEGER DEFAULT 0,
    media_type                TEXT,
    received_at               INTEGER NOT NULL,
    route                     TEXT NOT NULL CHECK(route IN ('course_inquiry','needs_classification','known_contact','ignored')),
    contact_mode              TEXT CHECK(contact_mode IN ('auto','auto_respond','draft_only') OR contact_mode IS NULL),
    category                  TEXT CHECK(category IN ('technical','personal','course_followup','spam','unknown') OR category IS NULL),
    classification_confidence REAL,
    auto_decision_reason      TEXT,
    status                    TEXT DEFAULT 'pending' CHECK(status IN ('pending','processing','draft_ready','sent','failed','retrying','dead','cancelled','skipped')),
    priority                  INTEGER DEFAULT 50,
    urgency                   TEXT DEFAULT 'normal' CHECK(urgency IN ('urgent','normal','low')),
    locked_at                 INTEGER,
    lease_until               INTEGER,
    worker_id                 TEXT,
    attempt_count             INTEGER DEFAULT 0,
    last_error                TEXT,
    next_retry_at             INTEGER,
    context_json              TEXT,
    created_at                INTEGER NOT NULL,
    updated_at                INTEGER NOT NULL,
    UNIQUE(chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_inbox_status_priority ON inbox(status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_inbox_chat_date ON inbox(chat_id, received_at);
CREATE INDEX IF NOT EXISTS idx_inbox_lease ON inbox(lease_until);

CREATE TABLE IF NOT EXISTS outbox (
    id                        INTEGER PRIMARY KEY,
    inbox_id                  INTEGER REFERENCES inbox(id),
    chat_id                   INTEGER NOT NULL,
    reply_to_message_id       INTEGER,
    draft_text                TEXT,
    final_text                TEXT,
    media_paths               TEXT,
    status                    TEXT DEFAULT 'draft' CHECK(status IN ('draft','approved','sending','sent','skipped','failed')),
    dedup_key                 TEXT UNIQUE,
    send_error                TEXT,
    attempt_count             INTEGER DEFAULT 0,
    next_retry_at             INTEGER,
    sending_started_at        INTEGER,
    draft_reason              TEXT,
    source                    TEXT CHECK(source IN ('classification','template','proactive','manual')),
    is_proactive              INTEGER DEFAULT 0,
    draft_created_at          INTEGER,
    approved_at               INTEGER,
    sent_at                   INTEGER,
    sent_message_id           INTEGER,
    created_at                INTEGER NOT NULL,
    updated_at                INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox(status);
CREATE INDEX IF NOT EXISTS idx_outbox_inbox ON outbox(inbox_id);

CREATE TABLE IF NOT EXISTS contacts_state (
    chat_id                   INTEGER PRIMARY KEY,
    sender_id                 INTEGER,
    display_name              TEXT,
    contact_mode              TEXT DEFAULT 'draft_only',
    last_inbound_at           INTEGER,
    last_outbound_at          INTEGER,
    last_meaningful_at        INTEGER,
    last_proactive_at         INTEGER,
    cadence_days              INTEGER DEFAULT 7,
    snoozed_until             INTEGER,
    do_not_contact            INTEGER DEFAULT 0,
    relationship_tags         TEXT,
    timezone                  TEXT,
    notes                     TEXT,
    config_version            INTEGER DEFAULT 1,
    created_at                INTEGER NOT NULL,
    updated_at                INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS templates (
    id                        INTEGER PRIMARY KEY,
    name                      TEXT NOT NULL UNIQUE,
    trigger_pattern           TEXT NOT NULL,
    response_text             TEXT NOT NULL,
    language                  TEXT DEFAULT 'ru',
    active                    INTEGER DEFAULT 1,
    created_at                INTEGER NOT NULL,
    updated_at                INTEGER NOT NULL
);
"""


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize database, create tables if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    now = int(time.time())
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
        ("version", str(SCHEMA_VERSION)),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_meta (key, value) VALUES (?, ?)",
        ("created_at", str(now)),
    )
    conn.commit()
    return conn


def get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get database connection, initializing if needed."""
    return init_db(db_path)


if __name__ == "__main__":
    conn = init_db()
    version = conn.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f"responder.db initialized (v{version[0]})")
    print(f"Tables: {', '.join(r[0] for r in tables)}")
    conn.close()
