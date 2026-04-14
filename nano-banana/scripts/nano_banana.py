#!/usr/bin/env python3
"""Nano Banana - Gemini Image Generation Tool

A CLI wrapper around Google's Gemini image generation models (Nano Banana family).
Supports style presets, platform-specific sizing, variants, image editing, and
organized output with metadata.

Usage:
    nano_banana.py [flags] "prompt" [output.png]
    nano_banana.py init                    # onboarding wizard
    nano_banana.py again                   # regenerate last
    nano_banana.py history [-n 10]         # show history
    nano_banana.py list-presets
    nano_banana.py list-platforms
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

SKILL_DIR = Path(__file__).resolve().parent.parent
PRESETS_FILE = SKILL_DIR / "presets.yaml"
PLATFORMS_FILE = SKILL_DIR / "platforms.yaml"
CENTRAL_SECRETS = SKILL_DIR.parent / "secrets.enc.yaml"
LOCAL_SECRETS = SKILL_DIR / "secrets.enc.yaml"
CONFIG_DIR = Path.home() / ".config" / "nano-banana"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
HISTORY_FILE = CONFIG_DIR / "history.jsonl"
LAST_RUN_FILE = CONFIG_DIR / "last.json"

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
MODELS = {
    "flash": "gemini-3.1-flash-image-preview",
    "pro": "gemini-3-pro-image-preview",
    "flash-2.5": "gemini-2.5-flash-image",
}

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# ---------- Config & secrets ----------


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def get_api_key() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    if shutil.which("sops") is None:
        return None
    for secrets_path in (LOCAL_SECRETS, CENTRAL_SECRETS):
        if secrets_path.exists():
            try:
                result = subprocess.run(
                    ["sops", "--decrypt", "--extract", '["GEMINI_API_KEY"]', str(secrets_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                key = result.stdout.strip()
                if key:
                    return key
            except subprocess.CalledProcessError:
                continue
    return None


def load_presets() -> dict[str, dict[str, str]]:
    if not PRESETS_FILE.exists():
        return {}
    with PRESETS_FILE.open() as f:
        return yaml.safe_load(f) or {}


def load_platforms() -> dict[str, dict[str, Any]]:
    if not PLATFORMS_FILE.exists():
        return {}
    with PLATFORMS_FILE.open() as f:
        return yaml.safe_load(f) or {}


# ---------- API calls ----------


@dataclass
class GenerationResult:
    output_path: Path
    prompt: str
    model: str
    preset: str | None
    platform: str | None
    edit_source: str | None
    timestamp: str
    duration_s: float


def _image_part(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return {"inlineData": {"mimeType": mime, "data": b64}}


# HTTP status codes that are worth retrying (transient)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 4
_BASE_BACKOFF_S = 2.0


class TransientAPIError(RuntimeError):
    """Retryable API failure."""


class PermanentAPIError(RuntimeError):
    """Non-retryable API failure (4xx, content safety, etc.)."""


def _call_gemini_once(
    prompt: str,
    model: str,
    api_key: str,
    edit_source: Path | None,
    reference_images: list[Path] | None,
) -> bytes:
    parts: list[dict[str, Any]] = [{"text": prompt}]
    if edit_source:
        parts.append(_image_part(edit_source))
    for ref in reference_images or []:
        parts.append(_image_part(ref))

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    req = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if e.code in _RETRYABLE_STATUS:
            raise TransientAPIError(f"HTTP {e.code}: {body[:400]}") from e
        raise PermanentAPIError(f"HTTP {e.code}: {body[:400]}") from e
    except urllib.error.URLError as e:
        raise TransientAPIError(f"Network error: {e}") from e

    candidates = data.get("candidates", [])
    if not candidates:
        # Body may contain promptFeedback about safety blocks
        feedback = data.get("promptFeedback", {})
        raise PermanentAPIError(f"No candidates. Feedback: {feedback}")

    candidate = candidates[0]
    # Check finishReason for transient vs permanent issues
    finish_reason = candidate.get("finishReason", "")
    for part in candidate.get("content", {}).get("parts", []):
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])

    # No image returned
    text_parts = [p.get("text", "") for p in candidate.get("content", {}).get("parts", [])]
    msg = f"No image. finishReason={finish_reason}. Text: {' '.join(text_parts)[:300]}"
    # Treat "other" / "internal" / empty as transient; SAFETY / RECITATION as permanent
    if finish_reason in {"SAFETY", "RECITATION", "PROHIBITED_CONTENT"}:
        raise PermanentAPIError(msg)
    raise TransientAPIError(msg)


def _call_gemini(
    prompt: str,
    model: str,
    api_key: str,
    edit_source: Path | None = None,
    reference_images: list[Path] | None = None,
) -> bytes:
    """Call Gemini image API with retry on transient failures."""
    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return _call_gemini_once(prompt, model, api_key, edit_source, reference_images)
        except TransientAPIError as e:
            last_err = e
            if attempt == _MAX_RETRIES - 1:
                break
            delay = _BASE_BACKOFF_S * (2 ** attempt)
            print(
                f"  ⚠ transient error (attempt {attempt + 1}/{_MAX_RETRIES}): {str(e)[:120]}\n"
                f"    retrying in {delay:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(delay)
        except PermanentAPIError:
            raise  # no point retrying
    raise RuntimeError(f"Gave up after {_MAX_RETRIES} retries. Last error: {last_err}")


# ---------- Post-processing ----------


def apply_platform_fit(
    image_path: Path, platform: dict[str, Any], output_path: Path | None = None
) -> Path:
    """Resize/crop image to platform target dimensions using ImageMagick."""
    width = platform["width"]
    height = platform["height"]
    dest = output_path or image_path
    cmd = [
        "magick",
        str(image_path),
        "-resize",
        f"{width}x{height}^",
        "-gravity",
        "center",
        "-extent",
        f"{width}x{height}",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return dest


def make_contact_sheet(image_paths: list[Path], output_path: Path, cols: int = 2) -> Path:
    """Assemble contact sheet using ImageMagick montage."""
    if not image_paths:
        raise ValueError("No images for contact sheet")
    cmd = [
        "magick",
        "montage",
        *[str(p) for p in image_paths],
        "-tile",
        f"{cols}x",
        "-geometry",
        "600x+10+10",
        "-background",
        "#0f0f0f",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


# ---------- Metadata ----------


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "image"


def resolve_output_path(
    output_arg: str | None,
    subject: str,
    project: str | None,
    config: dict[str, Any],
) -> Path:
    if output_arg:
        return Path(output_arg).expanduser().resolve()
    base = Path(config.get("output_dir", "~/nano-banana/outputs")).expanduser()
    if project:
        base = base / project
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return base / f"{ts}-{slugify(subject)}.png"


def write_sidecar(image_path: Path, metadata: dict[str, Any]) -> Path:
    sidecar = image_path.with_suffix(".json")
    with sidecar.open("w") as f:
        json.dump(metadata, f, indent=2, default=str)
    return sidecar


def append_history(entry: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def save_last_run(entry: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with LAST_RUN_FILE.open("w") as f:
        json.dump(entry, f, indent=2, default=str)


def load_last_run() -> dict[str, Any] | None:
    if not LAST_RUN_FILE.exists():
        return None
    with LAST_RUN_FILE.open() as f:
        return json.load(f)


# ---------- Core generation ----------


def compose_prompt(subject: str, preset_name: str | None, presets: dict) -> str:
    if not preset_name:
        return subject
    if preset_name not in presets:
        raise SystemExit(
            f"Error: preset '{preset_name}' not found. Available: {list(presets.keys())}"
        )
    template = presets[preset_name]["prompt"]
    return template.replace("{subject}", subject)


def generate_once(
    prompt: str,
    output_path: Path,
    model: str,
    api_key: str,
    edit_source: Path | None = None,
    reference_images: list[Path] | None = None,
    platform: dict[str, Any] | None = None,
) -> GenerationResult:
    start = time.time()
    img_bytes = _call_gemini(prompt, model, api_key, edit_source, reference_images)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(img_bytes)
    if platform:
        apply_platform_fit(output_path, platform)
    return GenerationResult(
        output_path=output_path,
        prompt=prompt,
        model=model,
        preset=None,
        platform=None,
        edit_source=str(edit_source) if edit_source else None,
        timestamp=datetime.now().isoformat(),
        duration_s=round(time.time() - start, 2),
    )


def generate(args: argparse.Namespace, config: dict[str, Any]) -> None:
    api_key = get_api_key()
    if not api_key:
        print(
            "Error: GEMINI_API_KEY not set and could not decrypt from secrets.enc.yaml.\n"
            "Run: nano_banana.py init",
            file=sys.stderr,
        )
        sys.exit(1)

    presets = load_presets()
    platforms = load_platforms()

    edit_source = Path(args.edit).expanduser().resolve() if args.edit else None
    if edit_source and not edit_source.exists():
        sys.exit(f"Error: edit source not found: {edit_source}")

    reference_paths: list[Path] = []
    for ref in args.reference or []:
        p = Path(ref).expanduser().resolve()
        if not p.exists():
            sys.exit(f"Error: reference image not found: {p}")
        reference_paths.append(p)

    # Subject / prompt composition
    if edit_source:
        if not args.prompt:
            sys.exit("Error: edit mode requires a prompt (the instruction)")
        prompt = args.prompt
        preset_name = None
    else:
        if not args.prompt:
            sys.exit("Error: prompt is required")
        preset_name = args.preset or config.get("default_preset")
        prompt = compose_prompt(args.prompt, preset_name, presets)

    platform_conf = None
    platform_name = args.platform or config.get("default_platform")
    if platform_name:
        if platform_name not in platforms:
            sys.exit(
                f"Error: platform '{platform_name}' not found. Available: {list(platforms.keys())}"
            )
        platform_conf = platforms[platform_name]

    model = args.model or config.get("default_model", DEFAULT_MODEL)
    # Resolve model aliases
    model = MODELS.get(model, model)

    if args.dry_run:
        print(f"Model: {model}")
        print(f"Preset: {preset_name or '(none)'}")
        print(f"Platform: {platform_name or '(none)'}")
        if edit_source:
            print(f"Edit source: {edit_source}")
        if reference_paths:
            print(f"References: {', '.join(str(r) for r in reference_paths)}")
        print(f"Prompt:\n  {prompt}")
        return

    # Resolve output path(s)
    project = args.project or config.get("default_project")
    primary_output = resolve_output_path(args.output, args.prompt, project, config)

    n = max(1, args.n)
    outputs: list[GenerationResult] = []

    def _job(i: int) -> GenerationResult | None:
        if n == 1:
            out = primary_output
        else:
            out = primary_output.with_name(f"{primary_output.stem}-{i+1:02d}{primary_output.suffix}")
        print(f"[{i+1}/{n}] Generating → {out.name}")
        try:
            result = generate_once(
                prompt, out, model, api_key, edit_source, reference_paths, platform_conf
            )
        except Exception as e:
            print(f"  ✗ variant {i+1} failed: {e}", file=sys.stderr)
            return None
        result.preset = preset_name
        result.platform = platform_name
        return result

    if n == 1:
        one = _job(0)
        if one is None:
            sys.exit(1)
        outputs.append(one)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(n, 4)) as pool:
            outputs = [r for r in pool.map(_job, range(n)) if r is not None]
        if not outputs:
            sys.exit("All variants failed.")

    # Contact sheet for variants
    if n > 1:
        contact_path = primary_output.with_name(f"{primary_output.stem}-contact.png")
        make_contact_sheet([o.output_path for o in outputs], contact_path)
        print(f"Contact sheet: {contact_path}")

    # Metadata
    for result in outputs:
        entry = asdict(result)
        entry["output_path"] = str(result.output_path)
        if not args.no_metadata:
            write_sidecar(result.output_path, entry)
        append_history({**entry, "subject": args.prompt, "project": project})

    # Save last run for --again
    save_last_run({
        "subject": args.prompt,
        "prompt": prompt,
        "preset": preset_name,
        "platform": platform_name,
        "model": model,
        "edit_source": str(edit_source) if edit_source else None,
        "reference": [str(r) for r in reference_paths],
        "project": project,
        "n": n,
        "output": str(primary_output),
    })

    for result in outputs:
        print(f"✓ {result.output_path} ({result.duration_s}s)")


# ---------- Subcommands ----------


def cmd_list_presets(_args: argparse.Namespace) -> None:
    presets = load_presets()
    for name, conf in presets.items():
        print(f"  {name:16s} {conf.get('description', '')}")


def cmd_list_platforms(_args: argparse.Namespace) -> None:
    platforms = load_platforms()
    for name, conf in platforms.items():
        desc = conf.get("description", "")
        size = f"{conf.get('width', '?')}x{conf.get('height', '?')}"
        print(f"  {name:16s} {size:12s} {desc}")


def cmd_again(args: argparse.Namespace) -> None:
    last = load_last_run()
    if not last:
        sys.exit("Error: no previous run found. Generate an image first.")
    # Reconstruct args
    ns = argparse.Namespace(
        prompt=last["subject"],
        output=None,  # force new output path
        preset=last.get("preset"),
        platform=last.get("platform"),
        model=last.get("model"),
        edit=last.get("edit_source"),
        reference=last.get("reference", []),
        project=last.get("project"),
        n=args.n if args.n else last.get("n", 1),
        no_metadata=False,
        dry_run=False,
    )
    print(f"↻ Regenerating: {last['subject']}")
    generate(ns, load_config())


def cmd_history(args: argparse.Namespace) -> None:
    if not HISTORY_FILE.exists():
        print("No history yet.")
        return
    with HISTORY_FILE.open() as f:
        lines = f.readlines()
    entries = [json.loads(ln) for ln in lines]
    if args.project:
        entries = [e for e in entries if e.get("project") == args.project]
    entries = entries[-args.n :]
    for e in entries:
        ts = e.get("timestamp", "?")[:19].replace("T", " ")
        preset = e.get("preset") or "-"
        subject = e.get("subject", "")[:60]
        print(f"{ts}  {preset:14s}  {subject}")
        print(f"              → {e.get('output_path', '?')}")


def cmd_init(_args: argparse.Namespace) -> None:
    print("Nano Banana — Onboarding\n")
    # Check deps
    deps = {
        "sops": "brew install sops",
        "age": "brew install age",
        "magick": "brew install imagemagick",
    }
    missing = [d for d in deps if shutil.which(d) is None]
    if missing:
        print("Missing dependencies:")
        for d in missing:
            print(f"  {d}  — install with: {deps[d]}")
        print()
    else:
        print("✓ Dependencies (sops, age, magick) installed\n")

    # Check API key
    key = get_api_key()
    if key:
        print(f"✓ GEMINI_API_KEY accessible (via SOPS or env)")
    else:
        print("✗ GEMINI_API_KEY not found.")
        print("  Set it by editing secrets.enc.yaml with: sops secrets.enc.yaml")
        print("  Or: export GEMINI_API_KEY=AIza... in your shell rc")
    print()

    # Config wizard
    config = load_config()

    def ask(key: str, prompt: str, default: str = "") -> str:
        current = config.get(key, default)
        shown = f" [{current}]" if current else ""
        val = input(f"{prompt}{shown}: ").strip()
        return val or current

    config["default_model"] = ask(
        "default_model",
        "Default model (flash / pro / flash-2.5)",
        "flash",
    )
    config["default_platform"] = ask(
        "default_platform",
        "Default platform (youtube / slides / blog / square / none)",
        "",
    )
    config["default_project"] = ask(
        "default_project",
        "Default project name (optional, e.g. 'blog')",
        "",
    )
    out_dir = ask(
        "output_dir",
        "Default output directory",
        "~/nano-banana/outputs",
    )
    config["output_dir"] = out_dir

    # Clean empty values
    config = {k: v for k, v in config.items() if v}

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    print(f"\n✓ Config saved to {CONFIG_FILE}")
    print("\nTry: nano_banana.py --preset editorial 'a robot' out.png")


# ---------- CLI parsing ----------


SUBCOMMANDS = {
    "init": cmd_init,
    "again": cmd_again,
    "history": cmd_history,
    "list-presets": cmd_list_presets,
    "list-platforms": cmd_list_platforms,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nano_banana",
        description="Nano Banana - Gemini image generation with presets, variants, edit, metadata",
        epilog=(
            "Subcommands: init | again | history | list-presets | list-platforms\n"
            "Run 'nano_banana.py <subcommand> --help' for details."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("prompt", nargs="?", help="Prompt / subject / edit instruction")
    p.add_argument("output", nargs="?", help="Output path (auto-generated if omitted)")
    p.add_argument("--preset", help="Style preset name (see list-presets)")
    p.add_argument("--platform", help="Platform preset (see list-platforms)")
    p.add_argument("--model", help="Model: flash | pro | flash-2.5 or full ID")
    p.add_argument("--edit", help="Edit mode: path to source image to modify")
    p.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Reference image for style/aesthetic anchor (repeatable)",
    )
    p.add_argument("--n", type=int, default=1, help="Number of variants (default 1)")
    p.add_argument("--project", help="Project name (groups outputs in subfolder)")
    p.add_argument("--no-metadata", action="store_true", help="Skip sidecar JSON")
    p.add_argument("--dry-run", action="store_true", help="Show composed prompt, don't call API")
    return p


def build_subparser(name: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=f"nano_banana {name}")
    if name == "again":
        p.add_argument("--n", type=int, default=0, help="Override variant count")
    elif name == "history":
        p.add_argument("-n", type=int, default=20, help="Number of entries to show")
        p.add_argument("--project", help="Filter by project")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Peek for subcommand as first arg
    if argv and argv[0] in SUBCOMMANDS:
        sub_name = argv[0]
        sub_parser = build_subparser(sub_name)
        sub_args = sub_parser.parse_args(argv[1:])
        SUBCOMMANDS[sub_name](sub_args)
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    if not args.prompt:
        parser.print_help()
        return 1

    try:
        generate(args, config)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
