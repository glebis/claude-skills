#!/usr/bin/env python3
"""
Deep Research Skill Orchestrator

This script enhances user research prompts through interactive questions,
saves the enhanced prompt, and executes deep_research.py to run the research.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# Prompt enhancement question templates by research type
ENHANCEMENT_TEMPLATES = {
    "general": {
        "scope": {
            "question": "What is the scope/timeframe for this research?",
            "options": [
                "Latest developments (2024-2025)",
                "Historical overview (all time)",
                "Specific time period (please specify)",
                "No preference"
            ]
        },
        "depth": {
            "question": "What level of detail do you need?",
            "options": [
                "Executive summary",
                "Technical deep dive",
                "Implementation guide",
                "Comparative analysis"
            ]
        },
        "focus": {
            "question": "Any specific aspects or domains to focus on?",
            "options": [
                "Performance/Benchmarks",
                "Cost/Efficiency",
                "Ease of use/Adoption",
                "Security/Privacy",
                "Multiple aspects"
            ]
        }
    },
    "technical": {
        "scope": {
            "question": "Technology scope?",
            "options": [
                "Open-source only",
                "Open-source + enterprise",
                "Language/framework specific",
                "No restriction"
            ]
        },
        "metrics": {
            "question": "What performance metrics matter most?",
            "options": [
                "Speed/Latency",
                "Accuracy/Correctness",
                "Scalability",
                "Resource usage",
                "Multiple metrics"
            ]
        },
        "use_case": {
            "question": "Any specific use cases or applications?",
            "options": [
                "Production deployment",
                "Research/Evaluation",
                "Learning/Education",
                "General exploration"
            ]
        }
    }
}


def is_prompt_too_brief(prompt: str) -> bool:
    """Check if prompt needs enhancement (too short or lacking detail)."""
    # Prompts with less than 15 words or very generic are considered brief
    word_count = len(prompt.split())
    generic_patterns = ["what is", "how to", "tell me about"]
    is_generic = any(prompt.lower().startswith(p) for p in generic_patterns)
    return word_count < 15 or is_generic


def ask_enhancement_questions(prompt: str) -> str:
    """Ask user clarifying questions to enhance the prompt."""
    # Detect if it's a technical research prompt
    technical_keywords = ["algorithm", "framework", "benchmark", "api", "architecture", "library", "tool", "system"]
    is_technical = any(kw in prompt.lower() for kw in technical_keywords)

    template_type = "technical" if is_technical else "general"
    template = ENHANCEMENT_TEMPLATES[template_type]

    print(f"\n📋 Let's refine your research prompt...")
    print(f"Original prompt: {prompt}\n")

    enhanced_parts = []

    for question_key, question_data in template.items():
        print(f"\n{question_data['question']}")
        for i, option in enumerate(question_data['options'], 1):
            print(f"  {i}. {option}")

        while True:
            response = input("Your choice (number or custom text): ").strip()
            if response.isdigit() and 1 <= int(response) <= len(question_data['options']):
                selected = question_data['options'][int(response) - 1]
                if "specify" in selected.lower() or "custom" in selected.lower():
                    custom = input("Please specify: ").strip()
                    enhanced_parts.append(custom if custom else selected)
                else:
                    enhanced_parts.append(selected)
                break
            elif response:
                # Allow custom text input
                enhanced_parts.append(response)
                break
            else:
                print("Invalid input. Please try again.")

    # Construct enhanced prompt
    enhanced_prompt = f"{prompt}\n\nResearch parameters:\n"
    enhanced_prompt += "\n".join(f"- {part}" for part in enhanced_parts)

    return enhanced_prompt


def save_research_prompt(prompt: str, output_dir: Optional[Path] = None) -> Path:
    """Save the research prompt to a file."""
    if output_dir is None:
        output_dir = Path.cwd()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = output_dir / f"research_prompt_{timestamp}.txt"

    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"\n💾 Research prompt saved to: {prompt_file}")

    return prompt_file


def get_deep_research_path() -> Path:
    """Get the path to deep_research.py."""
    # Try relative to this script first (for skill assets)
    script_dir = Path(__file__).parent
    skill_assets = script_dir.parent / "assets" / "deep_research.py"
    if skill_assets.exists():
        return skill_assets

    # Fall back to looking in common locations
    cwd = Path.cwd()
    if (cwd / "deep_research.py").exists():
        return cwd / "deep_research.py"

    if (cwd.parent / "deep_research.py").exists():
        return cwd.parent / "deep_research.py"

    raise FileNotFoundError(
        "Could not find deep_research.py. Please ensure it's in the skill assets folder or current directory."
    )


def run_deep_research(prompt_file: Path, model: str = "o4-mini-deep-research", timeout: int = 1800) -> None:
    """Execute deep_research.py with the research prompt."""
    deep_research_py = get_deep_research_path()

    print(f"\n🚀 Running Deep Research")
    print(f"   Model: {model}")
    print(f"   Timeout: {timeout} seconds ({timeout // 60} minutes)")
    print(f"   Estimated time: 10-20 minutes")
    print(f"\n⏳ Research in progress... (this may take a while)\n")

    cmd = [
        sys.executable,
        str(deep_research_py),
        "--prompt-file",
        str(prompt_file),
        "--model",
        model,
        "--timeout",
        str(timeout),
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Deep Research completed successfully!")
    except subprocess.CalledProcessError as exc:
        print(f"\n❌ Deep Research execution failed with exit code {exc.returncode}")
        raise SystemExit(f"Research execution failed") from exc
    except FileNotFoundError as exc:
        print(f"\n❌ Could not execute deep_research.py: {exc}")
        raise SystemExit("Missing deep_research.py executable") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Enhance a research prompt and run Deep Research API query"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The research question or task (can be brief, will be enhanced)",
    )
    parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Skip prompt enhancement questions",
    )
    parser.add_argument(
        "--model",
        default="o4-mini-deep-research",
        help="Model to use (default: o4-mini-deep-research)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Request timeout in seconds (default: 1800)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save the research prompt file",
    )

    args = parser.parse_args(argv)

    if not args.prompt:
        parser.error("Provide a research prompt as a positional argument.")

    # Determine if enhancement is needed
    prompt = args.prompt
    if not args.no_enhance and is_prompt_too_brief(prompt):
        prompt = ask_enhancement_questions(prompt)
    elif not args.no_enhance:
        print(f"\n✓ Prompt seems detailed enough, skipping enhancement questions.")

    # Save the prompt
    prompt_file = save_research_prompt(prompt, args.output_dir)

    # Run deep research
    run_deep_research(prompt_file, args.model, args.timeout)


if __name__ == "__main__":
    main(sys.argv[1:])
