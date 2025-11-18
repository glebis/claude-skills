# ElevenLabs API Reference

## Voice Presets

Pre-configured voices available through the skill with sensible defaults:

| Preset | Voice ID | Description |
|--------|----------|-------------|
| rachel | 21m00Tcm4TlvDq8ikWAM | Clear, professional female voice |
| adam | pNInz6obpgDQGcFmaJgB | Deep, authoritative male voice |
| bella | EXAVITQu4vr4xnSDxMaL | Warm, friendly female voice |
| elli | MF3mGyEYCHffgLcfVOJA | Young, enthusiastic female voice |
| josh | TtoZ7RTFQ8zXByXW5WwW | Friendly, conversational male voice |
| arnold | pMsXgVXv3BLzUgSXRplF | Deep, powerful male voice |
| ava | Xb7hH8MSUJpSbvtk6coT | Expressive, dynamic female voice |

## Voice Parameters

### stability (0.0 - 1.0)
Determines how stable/consistent the voice sounds. Default: 0.5
- Lower values (0.0-0.3): More variable, expressive
- Medium values (0.4-0.6): Balanced (recommended default)
- Higher values (0.7-1.0): Consistent, stable

### similarity_boost (0.0 - 1.0)
Controls how closely the voice matches the preset. Default: 0.75
- Lower values: More variation from original
- Higher values: Closer to original voice characteristics

## Models

- `eleven_monolingual_v1` - Standard English model (default)
- `eleven_multilingual_v1` - Supports multiple languages
- `eleven_multilingual_v2` - Latest multilingual model

## Usage Examples

### Basic Text-to-Speech
```python
from elevenlabs_tts import generate_speech

path = generate_speech(
    text="Hello, this is a test message",
    voice_id="rachel",
    output_path="output.mp3"
)
```

### Custom Voice Parameters
```python
path = generate_speech(
    text="Generate this audio",
    voice_id="adam",
    stability=0.7,
    similarity_boost=0.9,
    output_path="audio/my_file.mp3"
)
```

### Using Custom Voice ID
```python
# Use a specific 11Labs voice ID directly
path = generate_speech(
    text="Custom voice audio",
    voice_id="custom_voice_id_here"
)
```

## API Rate Limits

- Free tier: Limited calls per month
- Paid tier: Based on subscription level
- Monitor usage in ElevenLabs dashboard

## File Output

- Default format: MP3 (.mp3)
- Files are saved to specified output_path
- Directory structure is created automatically if needed

## Environment Setup

1. Create `.env` file in skill directory
2. Add your ElevenLabs API key:
   ```
   ELEVENLABS_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
