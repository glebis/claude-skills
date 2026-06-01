---
type: source
created: 2026-04-30
tags:
  - cli
  - agents
  - ndjson
  - mcp
  - polar-h10
  - architecture
---

# CLI Design for AI Agents

Practical patterns for building CLIs that are consumed by AI agents, not just humans. Compiled for the [[polar-h10-ribbon]] HRV biofeedback project.

Core principle: **Human DX optimizes for discoverability and forgiveness. Agent DX optimizes for predictability and defense-in-depth.** Design for both simultaneously.

---

## 1. Key Principles

- **stdout is your API.** Structured (machine-readable) output goes to stdout. Human messages, progress, and diagnostics go to stderr.
- **TTY detection.** When stdout is not a TTY, default to JSON. When it is a TTY, show human-friendly output. The `--json` flag forces JSON regardless.
- **Output formats are API contracts.** Treat them with the same discipline as REST APIs: semver, CI schema checks, no silent breakage.
- **Meaningful exit codes.** Agents branch on failure modes. 0 = success, 1 = generic error, 2 = bad usage, 3-125 = application-specific.
- **Idempotent operations.** Agents retry. Design commands so re-running them produces the same result.
- **Non-interactive by default.** Never block on stdin. Provide `--no-prompt`, `--no-interactive`, or detect non-TTY and skip prompts automatically.

---

## 2. Pattern Catalog

### 2.1 NDJSON Event Envelope

Every line is a self-contained JSON object with a standard envelope:

```json
{"event": "ready", "ts": "2026-04-30T14:00:00Z", "pid": 1234, "port": 8765}
{"event": "hr", "ts": "2026-04-30T14:00:01Z", "bpm": 72, "rr_ms": [831, 845]}
{"event": "metric", "ts": "2026-04-30T14:00:05Z", "rmssd": 42.3, "sdnn": 55.1}
{"event": "error", "ts": "2026-04-30T14:00:10Z", "message": "BLE disconnected", "code": "ble_disconnect", "retry": true}
```

**Required fields in every line:**
- `event` -- the event type (string, snake_case)
- `ts` -- ISO 8601 UTC timestamp

**Why NDJSON over JSON arrays:**
- Can be processed incrementally (one line at a time)
- One corrupted line does not break the stream
- Easily appendable (log files, streaming)
- Works with line-oriented tools (grep, jq, wc)
- Low memory footprint for long-running processes

### 2.2 Daemon Readiness Signal

The first JSON line a daemon emits is its readiness announcement. The orchestrating agent reads this line to confirm the process started successfully.

```json
{"event": "ready", "ts": "...", "pid": 1234, "port": 8765, "version": "0.3.0"}
```

**Pattern:** The agent starts the subprocess, reads the first line of stdout, parses it, and confirms `event == "ready"`. If it does not arrive within a timeout (e.g. 10s), the agent treats the process as failed.

**Alternatives considered:**
- Pidfiles: race-prone, stale files cause confusion
- Health endpoints: require HTTP, adds complexity
- systemd-notify: Linux-only, requires sd_notify()
- **First-line JSON: cross-platform, zero dependencies, works with any language**

### 2.3 Structured Error Reporting

Errors are NDJSON lines with `event: "error"`, not unstructured stderr text.

```json
{"event": "error", "ts": "...", "message": "Device not found", "code": "device_not_found", "detail": "No Polar H10 in range after 30s scan", "retry": true}
```

**Fields:**
- `message` -- human-readable summary
- `code` -- machine-parseable error type (snake_case string, not a number)
- `detail` -- optional longer explanation
- `retry` -- hint to the agent whether retrying makes sense
- `exit_code` -- if the process is about to exit, include it

**Exit code conventions for this project:**

| Code | Meaning |
|------|---------|
| 0 | Success / clean shutdown |
| 1 | Generic runtime error |
| 2 | Bad arguments / usage error |
| 10 | BLE device not found |
| 11 | BLE connection lost |
| 12 | BLE permission denied |
| 20 | Database error |
| 21 | Database locked |
| 30 | WebSocket error |
| 40 | Sensor data quality issue |

### 2.4 Streaming Status for Long-Running Processes

Daemons like `bridge.py` and `hrv_lights.py` run indefinitely. They stream status as periodic NDJSON heartbeats:

```json
{"event": "heartbeat", "ts": "...", "uptime_s": 120, "samples": 1500, "bpm": 68, "connected": true}
```

**Rules:**
- Emit a heartbeat every 10-30 seconds even when nothing changes
- Include a monotonically increasing counter or uptime for liveness detection
- The agent can kill the process if heartbeats stop for > 2x the interval
- State transitions (connected/disconnected) get their own events immediately, not batched into heartbeats

### 2.5 Schema Introspection

Agents should not need to parse `--help` text. Provide:

```bash
python bridge.py --schema
```

Returns:
```json
{
  "name": "bridge",
  "version": "0.3.0",
  "description": "Polar H10 BLE to WebSocket bridge",
  "args": {
    "--json": {"type": "bool", "default": false, "help": "NDJSON output"},
    "--port": {"type": "int", "default": 8765, "help": "WebSocket port"},
    "--device": {"type": "str", "help": "BLE device serial"}
  },
  "events": ["ready", "hr", "ecg", "acc", "error", "heartbeat"],
  "exit_codes": {"0": "success", "10": "device_not_found", "11": "connection_lost"}
}
```

This lets agents discover capabilities without wasting tokens on help text parsing.

### 2.6 CLI Orchestrator Pattern

For managing multiple services (bridge + lights + metrics + relay), use a parent process that:

1. Starts each child with `--json`
2. Reads the first `ready` line from each
3. Multiplexes all NDJSON streams into a single output, adding a `source` field
4. Forwards signals (SIGTERM) to all children
5. Restarts children on unexpected exit

```json
{"event": "ready", "ts": "...", "source": "bridge", "pid": 1234, "port": 8765}
{"event": "ready", "ts": "...", "source": "lights", "pid": 1235}
{"event": "hr", "ts": "...", "source": "bridge", "bpm": 72}
{"event": "color", "ts": "...", "source": "lights", "hue": 120, "brightness": 80}
```

The orchestrator itself emits:
```json
{"event": "orchestra_ready", "ts": "...", "services": ["bridge", "lights", "metrics", "relay"]}
```

### 2.7 CLI vs MCP: When to Use Each

Per RudderStack's pattern:

| Operation | Interface | Reason |
|-----------|-----------|--------|
| Start/stop recording | CLI | State-changing, needs explicit control |
| Query HRV history | MCP or CLI `query` | Read-only, safe to explore |
| Change light preset | CLI | State-changing mutation |
| Get current session status | MCP or CLI `status` | Read-only |
| Configure protocol | CLI + config file | Agent generates config, human reviews |

**Rule of thumb:** Write operations go through CLI with explicit flags. Read operations can go through either CLI or MCP.

---

## 3. Implementation Checklist for polar-h10-ribbon

Current state: `cli_utils.py` already implements the basic envelope (`json_log`, `json_error`, `add_json_flag`). The existing envelope uses `event` + `ts` fields -- this is solid.

### What to add:

- [ ] **Readiness signal**: Every daemon (`bridge.py`, `relay.py`, `hrv_lights.py`) should emit `{"event": "ready", ...}` as its first JSON line after initialization
- [ ] **Heartbeats**: Bridge should emit periodic heartbeats with connection status, sample count, current BPM
- [ ] **Exit codes**: Define project-wide exit code constants in `cli_utils.py`
- [ ] **Error codes**: Add string error codes to `json_error()` -- e.g., `json_error("BLE scan failed", code="ble_scan_timeout")`
- [ ] **Schema command**: Add `--schema` flag to each script that dumps args and event types as JSON
- [ ] **Orchestrator**: Build a `run_all.py` that starts bridge + lights + metrics, reads readiness, and multiplexes output
- [ ] **stderr for human output**: When `--json` is active, redirect `log()` calls to stderr so stdout stays clean NDJSON
- [ ] **Non-interactive guards**: Ensure no script ever blocks on stdin input

### Current `cli_utils.py` improvements:

```python
# Add to cli_utils.py:

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_BLE_NOT_FOUND = 10
EXIT_BLE_DISCONNECTED = 11
EXIT_BLE_PERMISSION = 12
EXIT_DB_ERROR = 20
EXIT_DB_LOCKED = 21
EXIT_WS_ERROR = 30
EXIT_DATA_QUALITY = 40

def json_ready(**kwargs):
    """Emit the readiness signal. Must be the first JSON line."""
    json_log("ready", pid=os.getpid(), **kwargs)

def json_heartbeat(**kwargs):
    """Emit a periodic liveness signal."""
    json_log("heartbeat", **kwargs)
```

---

## 4. MCP Stdio Transport Reference

MCP uses JSON-RPC 2.0 over stdio. The pattern is similar to our NDJSON approach but with a formal request/response protocol:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_hrv", "arguments": {"window": 60}}}
{"jsonrpc": "2.0", "id": 1, "result": {"rmssd": 42.3, "sdnn": 55.1, "hr": 68}}
```

**Key differences from our NDJSON pattern:**
- MCP is request/response; our pattern is event-streaming
- MCP has formal method registration; we use ad-hoc event types
- MCP requires a JSON-RPC envelope with `id` and `jsonrpc` fields

**When to consider MCP:** If we want Claude Code or other agents to interact with live HRV data through tool calls rather than stream parsing, we could wrap the bridge as an MCP server. For now, NDJSON streaming is simpler and sufficient.

---

## 5. Token Efficiency

CLIs are 10-32x cheaper on tokens than MCP for most tasks. Agents chain commands in quick sequences where one output pipes to the next. Key optimizations:

- **Field masks**: `--fields bpm,rmssd,ts` to limit output to what the agent needs
- **Compact output**: No pretty-printing in JSON mode (no indentation)
- **Pagination as NDJSON**: Stream one object per page instead of buffering arrays
- **Short error codes**: `"ble_scan_timeout"` not `"Bluetooth Low Energy scan timed out after 30 seconds while searching for compatible heart rate monitors"`

---

## References

- [You Need to Rewrite Your CLI for AI Agents](https://justin.poehnelt.com/posts/rewrite-your-cli-for-ai-agents/) -- Most comprehensive guide; covers schema introspection, input hardening, skill files
- [Keep the Terminal Relevant: Patterns for AI Agent Driven CLIs](https://www.infoq.com/articles/ai-agent-cli/) -- InfoQ article on exit codes, structured output as API contracts, MCP integration
- [AI agents need two interfaces: CLI and MCP](https://www.rudderstack.com/blog/ai-agents-cli-mcp-design-pattern/) -- RudderStack on write-via-CLI, read-via-MCP separation
- [Rewrite Your CLI for Agents (Or Get Replaced)](https://dev.to/meimakes/rewrite-your-cli-for-agents-or-get-replaced-2a2h) -- DEV Community overview of agent-friendly patterns
- [Command Line Interface Guidelines](https://clig.dev/) -- The canonical CLI design guide; stdout/stderr separation, `--json` flag, output as API
- [NDJSON Specification](https://ndjson.com/) -- Newline Delimited JSON format reference
- [JSON Lines](https://jsonlines.org/) -- Alternative name for the same spec
- [MCP Transports](https://modelcontextprotocol.io/docs/concepts/transports/) -- stdio transport for JSON-RPC 2.0
- [Structured CLI Output as Pipeline Glue](https://stevekinney.com/courses/self-testing-ai-agents/structured-cli-output-as-pipeline-glue) -- Steve Kinney on CLI output for agent pipelines
- [Designing CLIs for AI Agents](https://medium.com/@dminhk/designing-clis-for-ai-agents-patterns-that-work-in-2026-29ac725850de) -- 2026 patterns overview
- [10 Must-have CLIs for your AI Agents](https://medium.com/@unicodeveloper/10-must-have-clis-for-your-ai-agents-in-2026-51ba0d0881df) -- Practical agent CLI tools
