#!/usr/bin/env python3
"""
11Labs Text-to-Speech Script
Converts text to audio using ElevenLabs API
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables from .env
load_dotenv()

# Default voice IDs (popular choices)
VOICE_PRESETS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Clear, professional female
    "adam": "pNInz6obpgDQGcFmaJgB",    # Deep, male voice
    "bella": "EXAVITQu4vr4xnSDxMaL",   # Warm, female voice
    "elli": "MF3mGyEYCHffgLcfVOJA",    # Young, enthusiastic female
    "josh": "TtoZ7RTFQ8zXByXW5WwW",    # Friendly male voice
    "arnold": "pMsXgVXv3BLzUgSXRplF",  # Deep, powerful male
    "ava": "Xb7hH8MSUJpSbvtk6coT",     # Expressive female voice
}


def generate_speech(
    text: str,
    voice_id: str = "rachel",
    model: str = "eleven_monolingual_v1",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    output_path: str = "output.mp3",
) -> str:
    """
    Generate speech from text using ElevenLabs API

    Args:
        text: Text to convert to speech
        voice_id: Voice ID or preset name (see VOICE_PRESETS). Default: 'rachel'
        model: ElevenLabs model to use. Default: 'eleven_monolingual_v1'
        stability: Voice stability (0.0 - 1.0). Default: 0.5
        similarity_boost: Voice similarity (0.0 - 1.0). Default: 0.75
        output_path: Path to save the audio file. Default: 'output.mp3'

    Returns:
        Path to the generated audio file
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    # Resolve voice_id if it's a preset name
    if voice_id.lower() in VOICE_PRESETS:
        voice_id = VOICE_PRESETS[voice_id.lower()]

    client = ElevenLabs(api_key=api_key)

    # Generate audio
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model,
        text=text,
        voice_settings={
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    )

    # Save to file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return str(Path(output_path).resolve())


def list_voices() -> None:
    """List available voice presets"""
    print("Available voice presets:")
    for name, voice_id in VOICE_PRESETS.items():
        print(f"  {name}: {voice_id}")


def main():
    """CLI interface for the skill"""
    if len(sys.argv) < 2:
        print("Usage: elevenlabs_tts.py <text> [options]")
        print("\nOptions:")
        print("  --voice VOICE_ID        Voice ID or preset name (default: rachel)")
        print("  --output FILE           Output file path (default: output.mp3)")
        print("  --stability FLOAT       Stability value 0.0-1.0 (default: 0.5)")
        print("  --similarity FLOAT      Similarity boost 0.0-1.0 (default: 0.75)")
        print("  --list-voices           List available voice presets")
        return

    text = sys.argv[1]

    # Parse optional arguments
    voice_id = "rachel"
    output_path = "output.mp3"
    stability = 0.5
    similarity_boost = 0.75

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--voice":
            voice_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--output":
            output_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--stability":
            stability = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--similarity":
            similarity_boost = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--list-voices":
            list_voices()
            return
        else:
            i += 1

    try:
        path = generate_speech(
            text=text,
            voice_id=voice_id,
            stability=stability,
            similarity_boost=similarity_boost,
            output_path=output_path,
        )
        print(f"Audio generated successfully: {path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
