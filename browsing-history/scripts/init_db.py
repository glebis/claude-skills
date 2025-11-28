#!/usr/bin/env python3
"""
Initialize the browsing history database.
Creates the SQLite database with proper schema for storing
Chrome history from all synced devices.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "data" / "browsing.db"


def init_database():
    """Create the browsing_history database and tables."""

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create main table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS browsing_history (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            device_type TEXT,
            device_id TEXT,
            source_machine TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            domain TEXT,
            visit_time TIMESTAMP,
            UNIQUE(url, device_id)
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON browsing_history(first_seen)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visit_time ON browsing_history(visit_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_type ON browsing_history(device_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_domain ON browsing_history(domain)")

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_database()
