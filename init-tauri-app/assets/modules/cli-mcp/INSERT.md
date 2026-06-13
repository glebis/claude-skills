# Insert: CLI + MCP server

1. Copy `cli.rs`, `mcp.rs`, `protocol.rs` → `src-tauri/src/`.
2. Copy `capability.json` → `src-tauri/capabilities/mcp.json`.
3. Merge `cargo-deps.toml` lines into `src-tauri/Cargo.toml` under `[dependencies]`
   (skip any key already present; keep the higher version on conflict). Add `anyhow = "1"`.
4. In `src-tauri/src/lib.rs`: add `mod cli; mod mcp; mod protocol;` near the top.
5. In `src-tauri/src/main.rs`: before building the Tauri app, parse the CLI and branch:
   ```rust
   let cli = <crate>::cli::Cli::parse();
   if let Some(<crate>::cli::Command::McpStdio) = cli.command {
       return tokio::runtime::Runtime::new()?.block_on(<crate>::mcp::run_stdio());
   }
   if let Some(<crate>::cli::Command::Ping { message }) = cli.command {
       println!("{}", <crate>::mcp::ping(<crate>::protocol::PingRequest { message }).reply);
       return Ok(());
   }
   ```
   (`<crate>` = the lib crate name from Cargo.toml.)
   **`fn main()` must return `anyhow::Result<()>`** for the `?` and `return Ok(())` above to
   compile: change its signature to `fn main() -> anyhow::Result<()>` and add `Ok(())` as the
   final expression (after the existing `<crate>::run()` call).
6. Verify: `cd src-tauri && cargo check && cargo test protocol`.
