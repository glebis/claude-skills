#!/usr/bin/env python3
"""
Sync Chrome browsing history from local Chrome and Chrome Sync data.

Data sources:
1. Local Chrome History SQLite (desktop browsing)
2. Chrome Sync LevelDB (synced devices: iPhone, iPad, Mac, etc.)

Run this script periodically (e.g., via cron or LaunchAgent) to keep
the browsing.db database updated with history from all devices.
"""

import sqlite3
import shutil
import struct
import datetime
import socket
from pathlib import Path
from urllib.parse import urlparse

# Paths
DB_PATH = Path.home() / "data" / "browsing.db"
CHROME_HISTORY = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
CHROME_SYNC_DB = Path.home() / "Library/Application Support/Google/Chrome/Default/Sync Data/LevelDB"

# Chrome epoch: 1601-01-01 in microseconds
CHROME_EPOCH = datetime.datetime(1601, 1, 1)


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return ""


def sync_local_chrome():
    """Sync local Chrome history to browsing.db."""

    if not CHROME_HISTORY.exists():
        print("Chrome history not found")
        return 0

    # Copy Chrome history (it may be locked)
    temp_copy = Path("/tmp/chrome_history_sync")
    try:
        shutil.copy2(CHROME_HISTORY, temp_copy)
    except Exception as e:
        print(f"Could not copy Chrome history: {e}")
        return 0

    # Connect to both databases
    chrome_conn = sqlite3.connect(temp_copy)
    chrome_conn.row_factory = sqlite3.Row
    dest_conn = sqlite3.connect(DB_PATH)

    # Get recent history from Chrome
    chrome_cursor = chrome_conn.cursor()
    chrome_cursor.execute("""
        SELECT
            urls.url,
            urls.title,
            urls.last_visit_time
        FROM urls
        WHERE urls.last_visit_time > 0
        ORDER BY urls.last_visit_time DESC
        LIMIT 10000
    """)

    hostname = socket.gethostname()
    inserted = 0

    for row in chrome_cursor.fetchall():
        url = row["url"]
        title = row["title"]

        # Convert Chrome timestamp to datetime
        chrome_time = row["last_visit_time"]
        visit_time = CHROME_EPOCH + datetime.timedelta(microseconds=chrome_time)

        domain = extract_domain(url)

        try:
            dest_conn.execute("""
                INSERT OR REPLACE INTO browsing_history
                (url, title, device_type, device_id, source_machine,
                 first_seen, source, domain, visit_time)
                VALUES (?, ?, 'desktop', 'local', ?,
                        CURRENT_TIMESTAMP, 'chrome_desktop', ?, ?)
            """, (url, title, hostname, domain, visit_time.strftime("%Y-%m-%d %H:%M:%S")))
            inserted += 1
        except Exception as e:
            pass  # Skip duplicates

    dest_conn.commit()
    chrome_conn.close()
    dest_conn.close()
    temp_copy.unlink()

    return inserted


def detect_device_type(device_name: str) -> str:
    """Detect device type from Chrome Sync device name."""
    name_lower = device_name.lower() if device_name else ""

    if "iphone" in name_lower:
        return "iPhone"
    elif "ipad" in name_lower:
        return "iPad"
    elif "android" in name_lower:
        return "Android"
    elif "tablet" in name_lower:
        return "Tablet"
    elif "mac" in name_lower or "macbook" in name_lower:
        return "Mac"
    elif "windows" in name_lower:
        return "Windows"
    else:
        return "synced"


def sync_chrome_sync():
    """
    Sync Chrome Sync data (from synced devices) to browsing.db.

    This requires parsing the LevelDB files in Chrome's Sync Data folder.
    The actual implementation depends on your Chrome Sync setup.

    For a complete implementation, you would need:
    1. Install plyvel: pip install plyvel
    2. Parse the protobuf structures in the LevelDB

    This is a placeholder - see the full implementation in:
    https://github.com/nickolay/nickolay.github.io/tree/master/AnyBrowserHistory
    """
    print("Chrome Sync parsing requires additional setup.")
    print("See: https://github.com/nickolay/nickolay.github.io/tree/master/AnyBrowserHistory")
    return 0


def main():
    """Main sync function."""
    print(f"Syncing to: {DB_PATH}")

    # Ensure database exists
    if not DB_PATH.exists():
        print("Database not found. Run init_db.py first.")
        return

    # Sync local Chrome
    local_count = sync_local_chrome()
    print(f"Synced {local_count} entries from local Chrome")

    # Sync Chrome Sync (if implemented)
    # sync_count = sync_chrome_sync()
    # print(f"Synced {sync_count} entries from Chrome Sync")

    # Show stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT device_type, COUNT(*) FROM browsing_history GROUP BY device_type")
    print("\nDatabase stats:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    conn.close()


if __name__ == "__main__":
    main()
