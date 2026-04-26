#!/usr/bin/env python3
"""GPT Image 2 — OpenAI Image Generation Tool

A CLI wrapper around OpenAI's GPT Image 2 model.
Supports style presets, platform-specific sizing, thinking mode, variants,
image editing, seed locking, cost controls, and OpenRouter routing.

Usage:
    gpt_image_2.py [flags] "prompt" [output.png]
    gpt_image_2.py init                    # onboarding wizard
    gpt_image_2.py again                   # regenerate last
    gpt_image_2.py history [-n 10]         # show history
    gpt_image_2.py list-presets
    gpt_image_2.py list-platforms
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
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
CONFIG_DIR = Path.home() / ".config" / "gpt-image-2"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
HISTORY_FILE = CONFIG_DIR / "history.jsonl"
LAST_RUN_FILE = CONFIG_DIR / "last.json"

MODEL = "gpt-image-2"
THINKING_LEVELS = ("off", "low", "medium", "high")

PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/images/generations",
        "edit_url": "https://api.openai.com/v1/images/edits",
        "key_env": "OPENAI_API_KEY",
        "key_sops": "OPENAI_API_KEY",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/images/generations",
        "edit_url": "https://openrouter.ai/api/v1/images/edits",
        "key_env": "OPENROUTER_API_KEY",
        "key_sops": "OPENROUTER_API_KEY",
    },
}

# Cost per image by quality and thinking level (April 2026 pricing)
COST_PER_IMAGE = {
    "high":   {"off": 0.21, "low": 0.25, "medium": 0.32, "high": 0.42},
    "medium": {"off": 0.05, "low": 0.07, "medium": 0.09, "high": 0.14},
    "low":    {"off": 0.006, "low": 0.01, "medium": 0.015, "high": 0.025},
}

CONFIRM_THRESHOLD = 0.50


def estimate_cost(quality: str, thinking: str, n: int) -> float:
    return COST_PER_IMAGE.get(quality, COST_PER_IMAGE["high"]).get(thinking, 0.21) * n


def cost_per_unit(quality: str, thinking: str) -> float:
    return COST_PER_IMAGE.get(quality, COST_PER_IMAGE["high"]).get(thinking, 0.21)


# ---------- Config & secrets ----------


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def get_api_key(provider: str) -> str | None:
    prov = PROVIDERS[provider]
    if os.environ.get(prov["key_env"]):
        return os.environ[prov["key_env"]]
    if shutil.which("sops") is None:
        return None
    for secrets_path in (LOCAL_SECRETS, CENTRAL_SECRETS):
        if secrets_path.exists():
            try:
                result = subprocess.run(
                    ["sops", "--decrypt", "--extract", f'["{prov["key_sops"]}"]', str(secrets_path)],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    return None


# ---------- Presets ----------


def load_presets() -> dict[str, dict]:
    if PRESETS_FILE.exists():
        with PRESETS_FILE.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def load_platforms() -> dict[str, dict]:
    if PLATFORMS_FILE.exists():
        with PLATFORMS_FILE.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def compose_prompt(user_prompt: str, preset_name: str | None) -> tuple[str, str | None]:
    """Return (final_prompt, preset_thinking_level)."""
    if not preset_name:
        return user_prompt, None
    presets = load_presets()
    if preset_name not in presets:
        print(f"Error: unknown preset '{preset_name}'. Available: {', '.join(presets.keys())}", file=sys.stderr)
        sys.exit(1)
    preset = presets[preset_name]
    prompt = preset["prompt"].replace("{subject}", user_prompt)
    return prompt, preset.get("thinking")


# ---------- Image I/O ----------


def encode_image(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def save_image(b64_data: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64_data))


def platform_fit(image_path: Path, width: int, height: int) -> None:
    if not shutil.which("magick"):
        print("Warning: ImageMagick not found, skipping platform resize", file=sys.stderr)
        return
    subprocess.run(
        ["magick", str(image_path), "-resize", f"{width}x{height}^",
         "-gravity", "center", "-extent", f"{width}x{height}", str(image_path)],
        check=True, capture_output=True,
    )


def make_contact_sheet(images: list[Path], output: Path, cols: int = 3) -> None:
    if not shutil.which("magick"):
        print("Warning: ImageMagick not found, skipping contact sheet", file=sys.stderr)
        return
    subprocess.run(
        ["magick", "montage"] + [str(p) for p in images] +
        ["-geometry", "+4+4", "-tile", f"{cols}x", str(output)],
        check=True, capture_output=True,
    )


# ---------- API ----------


MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _build_multipart(fields: list[tuple[str, str | bytes, str | None]]) -> tuple[bytes, str]:
    """Build multipart/form-data body. Each field is (name, value, filename_or_None)."""
    import uuid
    boundary = uuid.uuid4().hex
    lines: list[bytes] = []
    for name, value, filename in fields:
        lines.append(f"--{boundary}".encode())
        if filename:
            ext = Path(filename).suffix.lower()
            mime = MIME_TYPES.get(ext, "image/png")
            lines.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode())
            lines.append(f"Content-Type: {mime}".encode())
        else:
            lines.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        lines.append(b"")
        lines.append(value if isinstance(value, bytes) else value.encode())
    lines.append(f"--{boundary}--".encode())
    body = b"\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def api_request(
    prompt: str,
    provider: str,
    api_key: str,
    thinking: str = "off",
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
    seed: int | None = None,
    edit_image: str | None = None,
    reference_images: list[str] | None = None,
) -> list[str]:
    """Call the OpenAI/OpenRouter image generation API. Returns list of base64 images."""
    prov = PROVIDERS[provider]
    is_edit = bool(edit_image or reference_images)

    if is_edit:
        url = prov["edit_url"]
        fields: list[tuple[str, str | bytes, str | None]] = [
            ("model", MODEL, None),
            ("prompt", prompt, None),
            ("n", str(n), None),
            ("size", size, None),
            ("quality", quality, None),
        ]
        # seed parameter reserved for future API support
        if edit_image:
            with open(edit_image, "rb") as f:
                fields.append(("image[]", f.read(), Path(edit_image).name))
        if reference_images:
            for ref in reference_images:
                with open(ref, "rb") as f:
                    fields.append(("image[]", f.read(), Path(ref).name))
        data, content_type = _build_multipart(fields)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        }
    else:
        url = prov["url"]
        body: dict[str, Any] = {
            "model": MODEL,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "output_format": "png",
        }
        # thinking parameter reserved for future API support
        # (not yet accepted on /v1/images/generations endpoint)
        # seed parameter reserved for future API support
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/glebis/claude-skills"
        headers["X-Title"] = "gpt-image-2-skill"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    max_retries = 4
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                resp_data = result.get("data")
                if not resp_data:
                    print("Error: API returned no image data.", file=sys.stderr)
                    sys.exit(1)
                images = []
                for item in resp_data:
                    b64 = item.get("b64_json")
                    if b64:
                        images.append(b64)
                if not images:
                    print("Error: API response missing b64_json fields.", file=sys.stderr)
                    sys.exit(1)
                return images
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            if e.code == 429 or e.code >= 500:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    label = "Rate limited" if e.code == 429 else f"Server error {e.code}"
                    print(f"{label}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...", file=sys.stderr)
                    time.sleep(wait)
                else:
                    print(f"Failed after {max_retries} attempts. Last error {e.code}: {error_body}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Error {e.code}: {error_body}", file=sys.stderr)
                sys.exit(1)
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"Network error: {e.reason}, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"Failed after {max_retries} attempts: {e.reason}", file=sys.stderr)
                sys.exit(1)
    return []


# ---------- History ----------


@dataclass
class HistoryEntry:
    timestamp: str
    prompt: str
    preset: str | None
    platform: str | None
    thinking: str
    quality: str
    provider: str
    n: int
    seed: int | None
    output: str
    project: str | None
    estimated_cost: float | None


def save_history(entry: HistoryEntry) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps(asdict(entry)) + "\n")
    with LAST_RUN_FILE.open("w") as f:
        json.dump(asdict(entry), f, indent=2)


def load_history(n: int = 20, project: str | None = None) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    entries = []
    with HISTORY_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if project and entry.get("project") != project:
                continue
            entries.append(entry)
    return entries[-n:]


def load_last_run() -> dict | None:
    if not LAST_RUN_FILE.exists():
        return None
    with LAST_RUN_FILE.open() as f:
        return json.load(f)


# ---------- Metadata ----------


def save_metadata(output_path: Path, entry: HistoryEntry) -> None:
    meta_path = output_path.with_suffix(".json")
    with meta_path.open("w") as f:
        json.dump(asdict(entry), f, indent=2)


# ---------- Init wizard ----------


def cmd_init():
    print("🔧 GPT Image 2 — Setup Wizard\n")

    deps = {"sops": shutil.which("sops"), "age": shutil.which("age"), "magick": shutil.which("magick")}
    for name, path in deps.items():
        status = f"✅ {path}" if path else "❌ not found"
        print(f"  {name}: {status}")

    if not deps["magick"]:
        print("\n⚠  ImageMagick not found. Platform resizing and contact sheets will be unavailable.")
        print("  Install: brew install imagemagick")

    print()
    for provider_name in PROVIDERS:
        key = get_api_key(provider_name)
        if key:
            masked = key[:8] + "..." + key[-4:]
            print(f"  {provider_name} key: ✅ {masked}")
        else:
            print(f"  {provider_name} key: ❌ not found")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    defaults = load_config()
    if not defaults:
        defaults = {
            "provider": "openai",
            "thinking": "off",
            "quality": "high",
            "size": "1024x1024",
        }
        with CONFIG_FILE.open("w") as f:
            yaml.dump(defaults, f, default_flow_style=False)
        print(f"\n✅ Config saved to {CONFIG_FILE}")
    else:
        print(f"\n✅ Config already exists at {CONFIG_FILE}")

    print("\n📊 Pricing (per image):")
    print("  quality=low:    $0.006 (draft)  — fast iteration")
    print("  quality=medium: $0.05           — good for review")
    print("  quality=high:   $0.21 (default) — production")
    print("  + thinking adds 20-100% on top")

    print("\nReady! Try: scripts/gpt_image_2.py \"a cat astronaut\" ./cat.png")


# ---------- List commands ----------


def cmd_list_presets():
    presets = load_presets()
    if not presets:
        print("No presets found.")
        return
    print("Available presets:\n")
    for name, info in presets.items():
        thinking = f" [thinking: {info['thinking']}]" if info.get("thinking") else ""
        print(f"  {name:16s} {info['description']}{thinking}")


def cmd_list_platforms():
    platforms = load_platforms()
    if not platforms:
        print("No platforms found.")
        return
    print("Available platforms:\n")
    for name, info in platforms.items():
        print(f"  {name:16s} {info['width']}×{info['height']}  ({info['description']})")


# ---------- Main generate ----------


def cmd_generate(args):
    config = load_config()
    provider = args.provider or config.get("provider", "openai")
    api_key = get_api_key(provider)
    if not api_key:
        print(f"Error: No API key found for {provider}.", file=sys.stderr)
        print(f"Set {PROVIDERS[provider]['key_env']} or run: scripts/gpt_image_2.py init", file=sys.stderr)
        sys.exit(1)

    prompt, preset_thinking = compose_prompt(args.prompt, args.preset)

    thinking = args.thinking or preset_thinking or config.get("thinking", "off")
    quality = args.quality or config.get("quality", "high")
    size = args.size or config.get("size", "1024x1024")
    n = args.n or 1
    seed = getattr(args, "seed", None)
    is_draft = getattr(args, "draft", False)

    if is_draft:
        quality = "low"
        size = "1024x1024"

    output_path = Path(args.output) if args.output else Path(f"./gpt-image-2-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png")

    if args.project:
        base_dir = Path.home() / "gpt-image-2" / "outputs" / args.project
        slug = re.sub(r'[^a-z0-9]+', '-', args.prompt.lower()[:40]).strip('-')
        output_path = base_dir / f"{datetime.now().strftime('%Y%m%d')}-{slug}.png"

    cost = estimate_cost(quality, thinking, n)
    per = cost_per_unit(quality, thinking)
    mode_label = "DRAFT" if is_draft else quality.upper()

    if args.dry_run:
        print(f"Mode:      {mode_label}")
        print(f"Prompt:    {prompt}")
        print(f"Provider:  {provider}")
        print(f"Thinking:  {thinking}")
        print(f"Quality:   {quality}")
        print(f"Size:      {size}")
        print(f"N:         {n}")
        if seed is not None:
            print(f"Seed:      {seed}")
        print(f"Output:    {output_path}")
        print(f"Est. cost: ${cost:.3f}")
        return

    if args.estimate:
        print(f"Estimated cost ({mode_label}): ${cost:.3f} ({n} image{'s' if n > 1 else ''} × ~${per:.3f}/image, quality={quality}, thinking={thinking})")
        return

    no_confirm = getattr(args, "yes", False)
    if not no_confirm and cost >= CONFIRM_THRESHOLD:
        print(f"⚠  Estimated cost: ${cost:.2f} ({n} × ~${per:.3f}/image, {mode_label})")
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer not in ("y", "yes"):
            print("Cancelled.", file=sys.stderr)
            sys.exit(0)

    print(f"Generating {mode_label} with {provider} (thinking: {thinking}, quality: {quality}, size: {size}{f', seed: {seed}' if seed else ''})...", file=sys.stderr)

    images = api_request(
        prompt=prompt,
        provider=provider,
        api_key=api_key,
        thinking=thinking,
        size=size,
        quality=quality,
        n=n,
        seed=seed,
        edit_image=args.edit,
        reference_images=args.reference,
    )

    if not images:
        print("Error: No images returned.", file=sys.stderr)
        sys.exit(1)

    saved_paths = []
    if len(images) == 1:
        save_image(images[0], output_path)
        saved_paths.append(output_path)
        print(f"✅ {output_path}")
    else:
        stem = output_path.stem
        suffix = output_path.suffix
        parent = output_path.parent
        for i, img_data in enumerate(images, 1):
            p = parent / f"{stem}-{i:02d}{suffix}"
            save_image(img_data, p)
            saved_paths.append(p)
            print(f"✅ {p}")
        contact = parent / f"{stem}-contact{suffix}"
        make_contact_sheet(saved_paths, contact)
        if contact.exists():
            print(f"✅ {contact} (contact sheet)")

    platform = None
    if args.platform:
        platforms = load_platforms()
        if args.platform not in platforms:
            print(f"Warning: unknown platform '{args.platform}', skipping resize", file=sys.stderr)
        else:
            plat = platforms[args.platform]
            platform = args.platform
            for p in saved_paths:
                platform_fit(p, plat["width"], plat["height"])
            print(f"  Resized to {plat['width']}×{plat['height']} ({args.platform})")

    actual_cost = estimate_cost(quality, thinking, len(images))
    entry = HistoryEntry(
        timestamp=datetime.now().isoformat(),
        prompt=args.prompt,
        preset=args.preset,
        platform=platform,
        thinking=thinking,
        quality=quality,
        provider=provider,
        n=len(images),
        seed=seed,
        output=str(saved_paths[0] if len(saved_paths) == 1 else saved_paths[0].parent),
        project=args.project,
        estimated_cost=actual_cost,
    )
    save_history(entry)
    for p in saved_paths:
        save_metadata(p, entry)

    print(f"  Est. cost: ${actual_cost:.3f}")


# ---------- Again ----------


def cmd_again(args):
    last = load_last_run()
    if not last:
        print("No previous run found.", file=sys.stderr)
        sys.exit(1)
    print(f"Re-running: \"{last['prompt']}\"")
    args.prompt = last["prompt"]
    args.preset = last.get("preset")
    args.platform = last.get("platform")
    args.thinking = last.get("thinking", "off")
    args.provider = last.get("provider", "openai")
    args.n = last.get("n", 1)
    args.quality = last.get("quality", "high")
    args.size = "1024x1024"
    args.seed = last.get("seed")
    args.edit = None
    args.reference = None
    args.project = last.get("project")
    args.dry_run = False
    args.estimate = False
    args.draft = False
    args.yes = False
    args.output = None
    cmd_generate(args)


# ---------- History ----------


def cmd_history(args):
    entries = load_history(n=args.n, project=args.history_project)
    if not entries:
        print("No history found.")
        return
    for e in entries:
        ts = e["timestamp"][:19]
        prompt = e["prompt"][:50]
        cost = f"${e.get('estimated_cost', 0):.3f}" if e.get("estimated_cost") else "?"
        preset = f" [{e['preset']}]" if e.get("preset") else ""
        q = e.get("quality", "high")
        thinking = f" t:{e['thinking']}" if e.get("thinking", "off") != "off" else ""
        seed_str = f" s:{e['seed']}" if e.get("seed") else ""
        print(f"  {ts}  {cost:>7s}  q:{q:<6s}{thinking}{seed_str}  {prompt}{preset}")


# ---------- CLI ----------


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        cmd_init()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "list-presets":
        cmd_list_presets()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "list-platforms":
        cmd_list_platforms()
        return

    parser = argparse.ArgumentParser(
        description="GPT Image 2 — OpenAI Image Generation",
        epilog="Commands: init, list-presets, list-platforms, again, history",
    )
    sub = parser.add_subparsers(dest="command")

    gen_parser = argparse.ArgumentParser(
        prog="gpt_image_2.py",
        description="GPT Image 2 — Generate images from text prompts",
    )
    gen_parser.add_argument("prompt", nargs="?", help="Text prompt for image generation")
    gen_parser.add_argument("output", nargs="?", help="Output file path (default: auto-named)")
    gen_parser.add_argument("--preset", help="Style preset name")
    gen_parser.add_argument("--platform", help="Platform preset for auto-sizing")
    gen_parser.add_argument("--thinking", choices=THINKING_LEVELS, help="Thinking level (off/low/medium/high)")
    gen_parser.add_argument("--provider", choices=list(PROVIDERS.keys()), help="API provider")
    gen_parser.add_argument("--quality", choices=("low", "medium", "high"), help="Image quality")
    gen_parser.add_argument("--size", help="Image size (e.g., 1024x1024, 1536x1024, 2000x1024)")
    gen_parser.add_argument("--n", type=int, help="Number of variants (1-10)")
    gen_parser.add_argument("--seed", type=int, help="Seed for reproducible output")
    gen_parser.add_argument("--edit", help="Path to image to edit")
    gen_parser.add_argument("--reference", action="append", help="Reference image for style (repeatable)")
    gen_parser.add_argument("--project", help="Project name for organized output")
    gen_parser.add_argument("--dry-run", action="store_true", help="Preview prompt without API call")
    gen_parser.add_argument("--estimate", action="store_true", help="Show cost estimate only")
    gen_parser.add_argument("--draft", action="store_true", help="Draft mode: low quality, ~$0.006/image")
    gen_parser.add_argument("-y", "--yes", action="store_true", help="Skip cost confirmation prompt")

    sub_again = sub.add_parser("again", help="Re-run last generation")

    sub_history = sub.add_parser("history", help="Show generation history")
    sub_history.add_argument("-n", type=int, default=20, help="Number of entries to show")
    sub_history.add_argument("--project", dest="history_project", help="Filter by project")

    if len(sys.argv) <= 1 or sys.argv[1] in ("-h", "--help"):
        parser.print_help()
        return

    if sys.argv[1] not in ("again", "history"):
        args = gen_parser.parse_args()
        if not args.prompt:
            gen_parser.print_help()
            sys.exit(1)
        if args.n is not None and (args.n < 1 or args.n > 10):
            print("Error: --n must be between 1 and 10", file=sys.stderr)
            sys.exit(1)
        cmd_generate(args)
    else:
        args = parser.parse_args()
        if args.command == "again":
            cmd_again(args)
        elif args.command == "history":
            cmd_history(args)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
