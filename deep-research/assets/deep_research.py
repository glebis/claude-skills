#!/usr/bin/env python3
"""Simple CLI helper for the OpenAI Deep Research API."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from openai import OpenAI
from openai._exceptions import OpenAIError
from openai.types.responses.response import Response

try:
    from openai.types.responses.response_function_web_search import (
        Action,
        ActionFind,
        ActionOpenPage,
        ActionSearch,
    )
except ImportError:  # pragma: no cover - SDK drift safety net
    Action = ActionFind = ActionOpenPage = ActionSearch = None  # type: ignore

DEFAULT_MODEL = "o4-mini-deep-research"
DEFAULT_TOOLS = [{"type": "web_search"}]
DEFAULT_TIMEOUT_SECONDS = 30 * 60  # 30 minutes runtime window
DEFAULT_ENV_PATH = Path(".env")
ENV_KEY = "OPENAI_API_KEY"


def load_env(path: Path = DEFAULT_ENV_PATH) -> None:
    """Populate os.environ from a .env file if the target key is missing."""
    if os.environ.get(ENV_KEY) or not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        cleaned = value.strip().strip('"').strip("'")
        os.environ[key] = cleaned


def extract_web_sources(response: Response) -> List[str]:
    """Extract unique URLs referenced by web search tool calls."""
    urls: List[str] = []

    for item in response.output:
        item_type = getattr(item, "type", None)
        if item_type != "web_search_call":
            continue

        action: Action | None = getattr(item, "action", None)  # type: ignore[assignment]
        if action is None:
            continue

        action_type = getattr(action, "type", "")
        if action_type == "search":
            sources: Iterable | None = getattr(action, "sources", None)  # type: ignore[assignment]
            for source in sources or []:
                url = getattr(source, "url", None)
                if url:
                    urls.append(url)
        elif action_type in {"find", "open_page"}:
            url = getattr(action, "url", None)
            if url:
                urls.append(url)

    unique_urls: List[str] = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def run_research(
    prompt: str,
    *,
    instructions: str | None,
    model: str,
    include_sources: bool,
    timeout_seconds: float,
) -> Response:
    load_env()

    api_key = os.environ.get(ENV_KEY)
    if not api_key:
        raise SystemExit(
            "Missing OPENAI_API_KEY. Set it via environment or .env file before running the script."
        )

    client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    request_payload: dict = {
        "model": model,
        "input": prompt,
        "tools": DEFAULT_TOOLS,
    }
    if instructions:
        request_payload["instructions"] = instructions
    if include_sources:
        request_payload["include"] = ["web_search_call.action.sources"]

    try:
        return client.responses.create(**request_payload)
    except OpenAIError as exc:
        raise SystemExit(f"Deep Research request failed: {exc}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a Deep Research query using the OpenAI API")
    parser.add_argument("prompt", nargs="?", help="The research question or task you want to run")
    parser.add_argument(
        "--instructions",
        help="Optional system instructions to steer the researcher",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Read the prompt text from a file instead of positional argument",
    )
    parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Disable best-effort extraction of web sources",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Request timeout in seconds (default: 1800)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Save research report to this markdown file (default: auto-generated timestamp)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save the research report to a file",
    )

    args = parser.parse_args(argv)

    if args.prompt_file and args.prompt:
        parser.error("Specify either a positional prompt or --prompt-file, not both.")

    prompt_text = args.prompt
    if args.prompt_file:
        if not args.prompt_file.exists():
            parser.error(f"Prompt file not found: {args.prompt_file}")
        prompt_text = args.prompt_file.read_text()

    if not prompt_text:
        parser.error("Provide a prompt via positional argument or --prompt-file.")

    response = run_research(
        prompt_text,
        instructions=args.instructions,
        model=args.model,
        include_sources=not args.no_sources,
        timeout_seconds=args.timeout,
    )

    report = (response.output_text or "").strip()
    if not report:
        print("No textual report returned. Full response follows:\n")
        print(response.model_dump_json(indent=2))
        return

    # Extract sources
    sources = extract_web_sources(response) if not args.no_sources else []

    # Save to markdown file (unless --no-save is specified)
    if not args.no_save:
        output_file = args.output_file
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"research_report_{timestamp}.md")

        # Build markdown content
        markdown_content = report

        # Append sources if available
        if sources:
            markdown_content += "\n\n## Sources\n\n"
            for idx, url in enumerate(sources, start=1):
                markdown_content += f"{idx}. {url}\n"

        # Add metadata footer
        markdown_content += f"\n\n---\n\n*Research conducted on: {datetime.now().strftime('%B %d, %Y')}*  \n"
        markdown_content += f"*Model: {args.model}*  \n"

        # Save file
        output_file.write_text(markdown_content, encoding="utf-8")
        print(f"✅ Research report saved to: {output_file.absolute()}\n")

    # Print to terminal
    print("=== Deep Research Report ===\n")
    print(report)

    if args.no_sources or not sources:
        return

    print("\n=== Sources ===")
    for idx, url in enumerate(sources, start=1):
        print(f"{idx}. {url}")


if __name__ == "__main__":
    main(sys.argv[1:])
