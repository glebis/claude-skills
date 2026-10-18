#!/usr/bin/env python3
"""CLI helper for OpenAI deep research via the Responses API.

Every run writes, side by side, with one timestamp stem:
  research_request_<ts>.json   what was sent (model, tools, prompt; no key)
  research_response_<ts>.json  the exact HTTP response bytes of the final poll
  research_report_<ts>.md      readable report (unless --no-save)

The raw JSON keeps the `url_citation` annotations (character spans) and the
`web_search_call` step log; the Markdown keeps neither precisely. Import the
JSON with the research-runs skill (`--adapter openai-json`).

Runs use background mode: the response ID is saved before polling starts, so
an interrupted run can be collected later with --resume instead of paying twice.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Shutdown 2026-07-23 per OpenAI's deprecation notice; gpt-5.6-sol is the named replacement.
LEGACY_MODELS = {"o3-deep-research", "o4-mini-deep-research"}
DEFAULT_MODEL = os.environ.get("DEEP_RESEARCH_MODEL", "gpt-5.6-sol")
DEFAULT_REASONING = "high"
DEFAULT_TIMEOUT_SECONDS = 60 * 60
DEFAULT_POLL_SECONDS = 15
TERMINAL = {"completed", "failed", "cancelled", "incomplete"}
ENV_KEY = "OPENAI_API_KEY"
SOPS_SECRETS = Path("~/.claude/skills/secrets.enc.yaml").expanduser()
AGE_KEY_FILE = Path("~/.config/sops/age/keys.txt").expanduser()


def load_env(path: Path = Path(".env")) -> None:
    """Populate os.environ from a .env file if the target key is missing."""
    if os.environ.get(ENV_KEY) or not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def api_key() -> str | None:
    """SOPS first (a stale OPENAI_API_KEY env var must not shadow it), then env/.env."""
    if shutil.which("sops") and SOPS_SECRETS.exists():
        env = dict(os.environ)
        if "SOPS_AGE_KEY_FILE" not in env and AGE_KEY_FILE.exists():
            env["SOPS_AGE_KEY_FILE"] = str(AGE_KEY_FILE)
        try:
            r = subprocess.run(["sops", "-d", "--extract", f'["{ENV_KEY}"]', str(SOPS_SECRETS)],
                               capture_output=True, text=True, env=env, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    load_env()
    return os.environ.get(ENV_KEY)


def get_client(timeout_seconds: float):
    from openai import OpenAI
    key = api_key()
    if not key:
        raise SystemExit(f"Missing {ENV_KEY}: not in SOPS ({SOPS_SECRETS}), the environment, or .env.")
    return OpenAI(api_key=key, timeout=min(timeout_seconds, 600))


def build_request(prompt: str, *, model: str, instructions: str | None, include_sources: bool,
                  reasoning: str | None, background: bool, unlimited_search: bool) -> dict:
    tool: dict = {"type": "web_search"}
    if unlimited_search:
        tool["return_token_budget"] = "unlimited"
    payload: dict = {"model": model, "input": prompt, "tools": [tool], "background": background}
    if instructions:
        payload["instructions"] = instructions
    if include_sources:
        payload["include"] = ["web_search_call.action.sources"]
    if reasoning and model not in LEGACY_MODELS:
        payload["reasoning"] = {"effort": reasoning}
    return payload


def save_raw(raw, path: Path) -> dict:
    """Write the exact HTTP body bytes; return the parsed JSON."""
    body = raw.http_response.content
    path.write_bytes(body)
    return json.loads(body)


def poll(client, response_id: str, raw_path: Path, timeout_seconds: float, interval: float) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        raw = client.responses.with_raw_response.retrieve(response_id)
        data = save_raw(raw, raw_path)  # always keep the latest state on disk
        status = data.get("status")
        if status in TERMINAL:
            return data
        if time.monotonic() > deadline:
            raise SystemExit(f"Still {status} after {timeout_seconds:.0f}s. Resume later with: --resume {response_id}")
        print(f"   status: {status} … next check in {interval:.0f}s", file=sys.stderr)
        time.sleep(interval)


def output_text(data: dict) -> str:
    parts = [c.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
             for c in item.get("content", []) if c.get("type") == "output_text"]
    return "\n\n".join(p for p in parts if p).strip()


def consulted_sources(data: dict) -> list[str]:
    """Unique URLs from web_search_call steps (searched or opened, cited or not)."""
    urls: list[str] = []
    for item in data.get("output", []):
        if item.get("type") != "web_search_call":
            continue
        action = item.get("action") or {}
        if action.get("type") == "search":
            urls += [s.get("url") for s in action.get("sources") or [] if s.get("url")]
        elif action.get("type") in {"find", "find_in_page", "open_page"} and action.get("url"):
            urls.append(action["url"])
    return list(dict.fromkeys(urls))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Run a deep research query with the OpenAI Responses API")
    p.add_argument("prompt", nargs="?", help="The research question or task")
    p.add_argument("--prompt-file", type=Path, help="Read the prompt from a file")
    p.add_argument("--instructions", help="Optional system instructions")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL}; env DEEP_RESEARCH_MODEL)")
    p.add_argument("--reasoning", default=DEFAULT_REASONING,
                   help="Reasoning effort for non-legacy models (default: high); 'none' omits it")
    p.add_argument("--unlimited-search", action="store_true",
                   help="web_search return_token_budget=unlimited (more pages, higher cost)")
    p.add_argument("--no-background", action="store_true", help="Wait on one blocking request instead")
    p.add_argument("--resume", metavar="RESPONSE_ID", help="Collect an earlier background run; sends no new request")
    p.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_SECONDS)
    p.add_argument("--no-sources", action="store_true", help="Do not request the consulted-sources list")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Maximum wait in seconds")
    p.add_argument("--output-dir", type=Path, default=Path("."), help="Where to write request/response/report")
    p.add_argument("--output-file", type=Path, help="Report path (default: research_report_<ts>.md)")
    p.add_argument("--no-save", action="store_true", help="Don't write the Markdown report (raw JSON is still saved)")
    args = p.parse_args(argv)

    if args.prompt_file and args.prompt:
        p.error("Specify either a positional prompt or --prompt-file, not both.")
    prompt = args.prompt
    if args.prompt_file:
        if not args.prompt_file.exists():
            p.error(f"Prompt file not found: {args.prompt_file}")
        prompt = args.prompt_file.read_text()
    if not prompt and not args.resume:
        p.error("Provide a prompt via positional argument or --prompt-file (or --resume an earlier run).")
    if args.model in LEGACY_MODELS and not args.resume:
        print(f"⚠️  {args.model} was scheduled for shutdown on 2026-07-23 (replacement: gpt-5.6-sol).", file=sys.stderr)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = out / f"research_response_{stem}.json"
    client = get_client(args.timeout)

    if args.resume:
        response_id = args.resume
        print(f"⏳ Resuming {response_id}", file=sys.stderr)
    else:
        payload = build_request(prompt, model=args.model, instructions=args.instructions,
                                include_sources=not args.no_sources,
                                reasoning=None if args.reasoning == "none" else args.reasoning,
                                background=not args.no_background, unlimited_search=args.unlimited_search)
        (out / f"research_request_{stem}.json").write_text(
            json.dumps({**payload, "submitted_at": datetime.now().astimezone().isoformat(timespec="seconds")},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        from openai import OpenAIError
        try:
            raw = client.responses.with_raw_response.create(**payload)
        except OpenAIError as exc:
            raise SystemExit(f"Deep research request failed: {exc}") from exc
        data = save_raw(raw, raw_path)  # the ID is on disk before any waiting
        response_id = data["id"]
        print(f"🆔 Response ID: {response_id} (resume with --resume {response_id})", file=sys.stderr)

    data = poll(client, response_id, raw_path, args.timeout, args.poll_interval) if args.resume or not args.no_background \
        else json.loads(raw_path.read_bytes())
    status = data.get("status")
    print(f"💾 Raw response saved to: {raw_path.absolute()}", file=sys.stderr)

    report = output_text(data)
    if status != "completed" or not report:
        reason = (data.get("error") or {}).get("message") or (data.get("incomplete_details") or {}).get("reason") or "no report text"
        raise SystemExit(f"Run ended with status '{status}': {reason}. Raw JSON kept at {raw_path}")

    sources = consulted_sources(data)
    if not args.no_save:
        report_path = args.output_file or out / f"research_report_{stem}.md"
        md = report
        if sources:
            md += "\n\n## Sources consulted (web search)\n\n" + "".join(f"{i}. {u}\n" for i, u in enumerate(sources, 1))
        md += (f"\n\n---\n\n*Research conducted on: {datetime.now().strftime('%B %d, %Y')}*  \n"
               f"*Model: {data.get('model') or args.model}*  \n*Response ID: {response_id}*  \n"
               f"*Raw response: {raw_path.name}*  \n")
        report_path.write_text(md, encoding="utf-8")
        print(f"✅ Research report saved to: {report_path.absolute()}\n")

    print("=== Deep Research Report ===\n")
    print(report)
    if sources:
        print(f"\n=== Sources consulted: {len(sources)} (see the Markdown or raw JSON) ===")


if __name__ == "__main__":
    main(sys.argv[1:])
