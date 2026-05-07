#!/usr/bin/env python3
"""Seed template responses into responder.db."""

import time
from pathlib import Path

from schema import get_db

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def seed_templates() -> None:
    conn = get_db()
    now = int(time.time())

    templates = []
    for md_file in TEMPLATES_DIR.glob("*.md"):
        name = md_file.stem
        text = md_file.read_text().strip()
        templates.append((name, text))

    for name, text in templates:
        conn.execute(
            """INSERT OR REPLACE INTO templates
               (name, trigger_pattern, response_text, language, active, created_at, updated_at)
               VALUES (?, ?, ?, 'ru', 1, ?, ?)""",
            (name, name, text, now, now),
        )

    conn.commit()
    print(f"Seeded {len(templates)} template(s)")

    for row in conn.execute("SELECT name, length(response_text) FROM templates").fetchall():
        print(f"  {row[0]}: {row[1]} chars")


if __name__ == "__main__":
    seed_templates()
