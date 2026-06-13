use rusqlite::Connection;
use std::path::Path;
use crate::migrations;

pub fn open(path: &Path) -> rusqlite::Result<Connection> {
    let conn = Connection::open(path)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600));
    }
    migrations::apply(&conn)?;
    Ok(conn)
}

pub fn insert_item(conn: &Connection, name: &str) -> rusqlite::Result<i64> {
    conn.execute("INSERT INTO items (name) VALUES (?1)", [name])?;
    Ok(conn.last_insert_rowid())
}

pub fn list_items(conn: &Connection) -> rusqlite::Result<Vec<(i64, String)>> {
    let mut stmt = conn.prepare("SELECT id, name FROM items ORDER BY id")?;
    let rows = stmt.query_map([], |r| Ok((r.get(0)?, r.get(1)?)))?;
    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn insert_and_list() {
        let conn = Connection::open_in_memory().unwrap();
        migrations::apply(&conn).unwrap();
        insert_item(&conn, "a").unwrap();
        insert_item(&conn, "b").unwrap();
        let items = list_items(&conn).unwrap();
        assert_eq!(items.len(), 2);
        assert_eq!(items[0].1, "a");
    }
}
