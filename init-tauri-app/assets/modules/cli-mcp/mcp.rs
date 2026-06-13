// assets/modules/cli-mcp/mcp.rs
use crate::protocol::{PingRequest, PingResponse};
// NOTE: adapt the exact rmcp server boilerplate from cenno/src-tauri/src/mcp.rs.
// Expose ONE tool `ping(PingRequest) -> PingResponse`. Keep it minimal.
pub async fn run_stdio() -> anyhow::Result<()> {
    // build rmcp server with the `ping` tool, serve over stdio
    todo!("see cenno/src-tauri/src/mcp.rs for the rmcp serve-over-stdio shape")
}
pub fn ping(req: PingRequest) -> PingResponse {
    PingResponse { reply: format!("pong: {}", req.message) }
}
