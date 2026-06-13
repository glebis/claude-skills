use rusqlite::Connection;

pub const MIGRATIONS: &[&str] = &[
    "CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );",
];

pub fn apply(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch("CREATE TABLE IF NOT EXISTS _migrations (idx INTEGER PRIMARY KEY);")?;
    let done: i64 = conn.query_row("SELECT COUNT(*) FROM _migrations", [], |r| r.get(0))?;
    for (i, sql) in MIGRATIONS.iter().enumerate().skip(done as usize) {
        conn.execute_batch(sql)?;
        conn.execute("INSERT INTO _migrations (idx) VALUES (?1)", [i as i64])?;
    }
    Ok(())
}
