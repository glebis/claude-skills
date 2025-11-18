---
name: elevenlabs-tts
description: This skill converts text to high-quality audio files using ElevenLabs API. Use this skill when users request text-to-speech generation, audio narration, or voice synthesis with customizable voice parameters (stability, similarity boost) and voice presets (rachel, adam, bella, elli, josh, arnold, ava).
---

# ElevenLabs Text-to-Speech

## Overview

Generate professional audio files from text using ElevenLabs' advanced text-to-speech API. The skill provides pre-configured voice presets with sensible defaults, voice parameter customization, and direct access to the `scripts/elevenlabs_tts.py` script for programmatic control.

## Quick Start

To generate audio from text:

1. Ensure the `.env` file contains a valid `ELEVENLABS_API_KEY`
2. Execute the script with text: `python scripts/elevenlabs_tts.py "Your text here"`
3. Specify voice and output: `python scripts/elevenlabs_tts.py "Text" --voice adam --output audio/output.mp3`

## Voice Presets

Seven pre-configured voices are available. See `references/api_reference.md` for complete voice descriptions:

- `rachel` (default) - Clear, professional female
- `adam` - Deep, authoritative male
- `bella` - Warm, friendly female
- `elli` - Young, enthusiastic female
- `josh` - Friendly, conversational male
- `arnold` - Deep, powerful male
- `ava` - Expressive, dynamic female

## Parameters

### Text
The text to convert to speech. Any length is supported.

### Voice Selection
Specify voice using preset name (e.g., `rachel`, `adam`) or direct ElevenLabs voice ID.

### Voice Parameters
- **stability** (0.0-1.0, default 0.5): Lower values create expressive variation; higher values ensure consistency
- **similarity_boost** (0.0-1.0, default 0.75): Higher values maintain closer adherence to voice characteristics

### Output
Specify the output file path. Default is `output.mp3`. Directories are created automatically.

## Usage Examples

### Basic Python Usage
```python
from scripts.elevenlabs_tts import generate_speech

path = generate_speech(
    text="Hello, this is a test message",
    voice_id="rachel"
)
```

### Command Line
```bash
# With default voice
python scripts/elevenlabs_tts.py "Generate this text"

# With custom voice and stability
python scripts/elevenlabs_tts.py "Different voice" --voice adam --stability 0.7

# To custom output path
python scripts/elevenlabs_tts.py "Save here" --output audio/narration.mp3

# List available voices
python scripts/elevenlabs_tts.py "" --list-voices
```

## Implementation Notes

- The script handles API communication with error reporting
- Output directories are created automatically if they don't exist
- Returns absolute path to generated audio file
- Uses `eleven_monolingual_v1` model by default (can be overridden)

## Resources

- `scripts/elevenlabs_tts.py` - Main Python script for text-to-speech generation. Can be imported as a module or executed from command line.
- `references/api_reference.md` - Detailed API documentation including voice descriptions, parameter explanations, and usage examples.
- `.env` and `.env.example` - Environment configuration for storing API credentials securely.
