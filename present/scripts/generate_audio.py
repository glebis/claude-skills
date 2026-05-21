#!/usr/bin/env python3
"""
Generate narration audio for presentation slides using ElevenLabs API.
Also generates a Rhodes chord transition sound.

Usage:
    python3 generate_audio.py slides.json output_dir/ [--voice daniel]

slides.json format:
[
  {"id": "slide-title", "narration": "Text to speak for this slide"},
  {"id": "slide-exec", "narration": "Another slide's narration"},
  ...
]

Output: MP3 files in output_dir/ named <id>.mp3, plus transition.mp3
Also writes durations.json with timing data for the HTML template.
"""

import argparse
import json
import os
import subprocess
import sys
import time

VOICE_MAP = {
    "daniel": "onwK4e9ZLuTAKqWW03F9",
    "alice": "Xb7hH8MSUJpSbSDYk0k2",
    "matilda": "XrExE9yKIg1WjnnlVkGX",
    "brian": "nPczCjzI2devNBz1zQrb",
    "george": "JBFqnCBsd6RMkjVDRZzb",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "eric": "cjVigY5qzO86Huf0OWal",
    "bella": "hpp4J3VqNfWAUOO0d1Us",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
}


def get_api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key
    env_path = os.path.expanduser("~/claude-skills/elevenlabs-tts/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    raise ValueError("ELEVENLABS_API_KEY not found in environment or ~/claude-skills/elevenlabs-tts/.env")


def generate_tts(text, voice_id, output_path, api_key):
    import requests
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.65, "similarity_boost": 0.75, "style": 0.15},
        },
    )
    if r.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(r.content)
        return len(r.content)
    else:
        print(f"  ERROR: {r.status_code} {r.text[:200]}", file=sys.stderr)
        return 0


def generate_transition(output_path, api_key):
    import requests
    r = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": "A warm Rhodes electric piano chord with gentle reverb, smooth and professional, two seconds",
            "duration_seconds": 2.0,
        },
    )
    if r.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(r.content)
        return len(r.content)
    return 0


def get_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True,
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 20.0


def main():
    parser = argparse.ArgumentParser(description="Generate presentation narration audio")
    parser.add_argument("slides_json", help="Path to slides JSON file")
    parser.add_argument("output_dir", help="Output directory for audio files")
    parser.add_argument("--voice", default="daniel", help="Voice name (default: daniel)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip slides that already have audio")
    args = parser.parse_args()

    api_key = get_api_key()
    voice_id = VOICE_MAP.get(args.voice.lower())
    if not voice_id:
        print(f"Unknown voice '{args.voice}'. Available: {', '.join(VOICE_MAP.keys())}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.slides_json) as f:
        slides = json.load(f)

    print(f"Generating {len(slides)} narration tracks with voice '{args.voice}'...")
    for i, slide in enumerate(slides):
        outpath = os.path.join(args.output_dir, f"{slide['id']}.mp3")
        if args.skip_existing and os.path.exists(outpath):
            print(f"  [{i+1}/{len(slides)}] skip {slide['id']} (exists)")
            continue
        print(f"  [{i+1}/{len(slides)}] {slide['id']}...")
        size = generate_tts(slide["narration"], voice_id, outpath, api_key)
        if size:
            print(f"    -> {size} bytes")
        time.sleep(0.3)

    # Transition sound
    transition_path = os.path.join(args.output_dir, "transition.mp3")
    if not os.path.exists(transition_path):
        print("Generating transition sound...")
        generate_transition(transition_path, api_key)

    # Get durations
    print("Getting durations...")
    durations = {}
    for slide in slides:
        path = os.path.join(args.output_dir, f"{slide['id']}.mp3")
        if os.path.exists(path):
            durations[slide["id"]] = round(get_duration(path), 1)

    dur_path = os.path.join(args.output_dir, "durations.json")
    with open(dur_path, "w") as f:
        json.dump(durations, f, indent=2)
    print(f"Durations saved to {dur_path}")

    total = sum(durations.values())
    print(f"\nTotal narration: {total:.0f}s ({total/60:.1f}m)")


if __name__ == "__main__":
    main()
