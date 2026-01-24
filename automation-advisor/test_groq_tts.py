#!/usr/bin/env python3
"""
Test Groq Orpheus TTS

Demonstrates voice synthesis with canopylabs/orpheus-v1-english model.
"""

import os
from pathlib import Path
from groq import Groq

# Set API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY environment variable not set")
    print("   Set it with: export GROQ_API_KEY='your-key'")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

# Test texts
test_cases = [
    {
        "name": "Welcome",
        "text": "Welcome to the Automation Advisor! I'll guide you through eight questions to help you make a data-driven decision about automation.",
        "filename": "welcome.wav"
    },
    {
        "name": "Question",
        "text": "What task are you considering automating?",
        "filename": "question.wav"
    },
    {
        "name": "Decision - Automate",
        "text": "Your automation decision is: Automate now. Score 225. Score of 225 indicates high ROI. Time investment in automation will pay off quickly.",
        "filename": "decision_automate.wav"
    },
    {
        "name": "Decision - Manual",
        "text": "Your automation decision is: Stay manual. Score 15. Score of 15 suggests manual process is more efficient. Automation overhead not justified.",
        "filename": "decision_manual.wav"
    },
    {
        "name": "Emotional",
        "text": "For English I highly, highly recommend using Orpheus. It can do crazy things, it can be emotional even. If you were specifically dreaming of your personal assistant, maybe it's time to go all in!",
        "filename": "emotional.wav"
    }
]

print("\n╔══════════════════════════════════════════════════════════╗")
print("║        GROQ ORPHEUS TTS TEST                             ║")
print("╚══════════════════════════════════════════════════════════╝\n")

output_dir = Path("test_audio_output")
output_dir.mkdir(exist_ok=True)

for test in test_cases:
    print(f"🎤 Generating: {test['name']}")
    print(f"   Text: {test['text'][:60]}...")

    try:
        # Synthesize speech
        response = client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="autumn",  # Options: autumn, winter, spring, summer
            response_format="wav",
            input=test['text']
        )

        # Save to file
        output_path = output_dir / test['filename']
        with open(output_path, 'wb') as f:
            # BinaryAPIResponse is iterable, read bytes
            for chunk in response.iter_bytes():
                f.write(chunk)

        print(f"   ✅ Saved: {output_path}")
        print(f"   🔊 Play with: afplay {output_path}\n")

    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("╔══════════════════════════════════════════════════════════╗")
print("║              TEST COMPLETE                               ║")
print("╚══════════════════════════════════════════════════════════╝\n")

print(f"Audio files saved to: {output_dir.absolute()}")
print("\nPlay all files:")
for test in test_cases:
    print(f"  afplay {output_dir / test['filename']}")

print("\nOr play the emotional one:")
print(f"  afplay {output_dir / 'emotional.wav'}")
