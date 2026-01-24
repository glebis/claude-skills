#!/usr/bin/env python3
"""
Automation Advisor - Agent SDK Server

Two modes:
1. Console interactive: Terminal-based questionnaire
2. Web server: Voice + text interface using Groq for TTS/STT

Usage:
    python server.py --mode console
    python server.py --mode server --port 8080
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse

# Agent SDK imports
try:
    from anthropic import Anthropic
    from groq import Groq
    import httpx
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install anthropic groq httpx")
    exit(1)

# Import visualization
try:
    from visualize import generate_full_report_visualization
except ImportError:
    print("Warning: visualize.py not found, visualizations will be disabled")
    def generate_full_report_visualization(data):
        return "\n[Visualization not available]\n"

# Configuration
VAULT_PATH = Path("/Users/glebkalinin/Brains/brain")
DECISIONS_DIR = VAULT_PATH / "automation-decisions"
MATRIX_FILE = VAULT_PATH / "Automation Decision Matrix.md"

# Ensure directories exist
DECISIONS_DIR.mkdir(exist_ok=True)

class AutomationAdvisor:
    """Core automation decision advisor logic"""

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.groq = None
        if os.getenv("GROQ_API_KEY"):
            self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

        self.conversation_history = []
        self.task_data = {
            "task_name": "",
            "context": "",
            "scores": {
                "frequency": 0,
                "time": 0,
                "error_cost": 1,
                "longevity": 0
            },
            "override_flags": [],
            "validation_pattern": None,
            "build_estimate": 0,
            "decision": ""
        }

    def calculate_score(self) -> int:
        """Calculate automation score"""
        scores = self.task_data["scores"]
        return scores["frequency"] * scores["time"] * scores["error_cost"] * scores["longevity"]

    def get_decision(self, score: int) -> str:
        """Determine automation decision based on score"""
        if score > 40:
            return "AUTOMATE NOW"
        elif score >= 20:
            return "AUTOMATE IF EASY"
        else:
            return "STAY MANUAL"

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report"""
        score = self.calculate_score()
        decision = self.get_decision(score)
        today = datetime.now().strftime("%Y%m%d")

        task_slug = self.task_data["task_name"].lower().replace(" ", "-")[:50]
        filename = f"{today}-{task_slug}.md"

        # Calculate break-even if we have build estimate
        break_even = ""
        if self.task_data["build_estimate"] > 0:
            # Simplified calculation
            scores = self.task_data["scores"]
            # Estimate weekly savings (rough approximation)
            freq_hours = {5: 7, 3: 4, 1: 1, 0: 0}
            time_hours = {5: 2, 3: 1, 1: 0.5, 0: 0.1}
            weekly_savings = freq_hours.get(scores["frequency"], 0) * time_hours.get(scores["time"], 0)

            if weekly_savings > 0:
                break_even_weeks = round(self.task_data["build_estimate"] / weekly_savings, 1)
                break_even = f"""
## Break-Even Analysis

- Build time: {self.task_data["build_estimate"]} hours
- Estimated time saved: {weekly_savings:.1f} hours/week
- Break-even: {break_even_weeks} weeks
- ROI after 1 year: {round(52 * weekly_savings - self.task_data["build_estimate"], 1)} hours
"""

        override_section = ""
        if self.task_data["override_flags"]:
            override_section = f"""
## Override Considerations

{chr(10).join(f"- {flag}" for flag in self.task_data["override_flags"])}
"""

        validation_section = ""
        if self.task_data["validation_pattern"]:
            validation_section = f"""
## Validation Pattern

**Recommended**: {self.task_data["validation_pattern"]}
"""

        # Generate visualization
        visualization = generate_full_report_visualization(self.task_data)

        markdown = f"""---
type: automation-decision
task: "{self.task_data["task_name"]}"
date: "[[{today}]]"
decision: "{decision}"
score: {score}
tags:
  - automation
  - decision
---

# Automation Decision: {self.task_data["task_name"]}

## Visualization

{visualization}

## Context

{self.task_data["context"]}

## Scoring

| Dimension | Score | Details |
|-----------|-------|---------|
| Frequency | {self.task_data["scores"]["frequency"]} | {self._get_score_label("frequency", self.task_data["scores"]["frequency"])} |
| Time | {self.task_data["scores"]["time"]} | {self._get_score_label("time", self.task_data["scores"]["time"])} |
| Error Cost | {self.task_data["scores"]["error_cost"]} | {self._get_score_label("error_cost", self.task_data["scores"]["error_cost"])} |
| Longevity | {self.task_data["scores"]["longevity"]} | {self._get_score_label("longevity", self.task_data["scores"]["longevity"])} |
| **Total** | **{score}** | **{self.task_data["scores"]["frequency"]} × {self.task_data["scores"]["time"]} × {self.task_data["scores"]["error_cost"]} × {self.task_data["scores"]["longevity"]} = {score}** |

## Decision: {decision}

**Reasoning**: {self._get_decision_reasoning(score, decision)}
{break_even}
{override_section}
{validation_section}

## Implementation Plan

### Next Steps
{self._generate_next_steps(decision, score)}

### Red Flags to Monitor
{self._generate_red_flags()}

## Related
- [[Automation Decision Matrix]] - Framework used

---

**Decision Date**: [[{today}]]
**Next Review**: {self._suggest_review_date()}
"""

        # Write to file
        filepath = DECISIONS_DIR / filename
        filepath.write_text(markdown)

        return str(filepath)

    def _get_score_label(self, dimension: str, score: int) -> str:
        """Get human-readable label for score"""
        labels = {
            "frequency": {5: "Multiple times per day", 3: "Weekly", 1: "Monthly", 0: "Rarely"},
            "time": {5: "Hours (2+)", 3: "30-120 minutes", 1: "5-30 minutes", 0: "Under 5 minutes"},
            "error_cost": {5: "Catastrophic", 3: "Annoying", 1: "Negligible"},
            "longevity": {5: "Years", 3: "Months", 1: "Weeks", 0: "One-time"}
        }
        return labels.get(dimension, {}).get(score, "Unknown")

    def _get_decision_reasoning(self, score: int, decision: str) -> str:
        """Generate reasoning for decision"""
        if decision == "AUTOMATE NOW":
            return f"Score of {score} indicates high ROI. Time investment in automation will pay off quickly."
        elif decision == "AUTOMATE IF EASY":
            return f"Score of {score} is borderline. Worth automating if you can build it in under 4 hours using existing tools."
        else:
            return f"Score of {score} suggests manual process is more efficient. Automation overhead not justified."

    def _generate_next_steps(self, decision: str, score: int) -> str:
        """Generate actionable next steps"""
        if decision == "AUTOMATE NOW":
            return """1. Break down task into automatable steps
2. Research tools/APIs needed
3. Build MVP in one session
4. Test with real data
5. Add validation layer if needed
6. Document for future maintenance"""
        elif decision == "AUTOMATE IF EASY":
            return """1. Time-box exploration: 1 hour
2. If solution is clear, build it (< 4 hours)
3. If not, stay manual for now
4. Revisit in 3 months"""
        else:
            return """1. Optimize manual process instead
2. Create checklist/template
3. Set reminder to re-evaluate in 6 months
4. Consider if frequency/time might change"""

    def _generate_red_flags(self) -> str:
        """Generate red flags to monitor"""
        flags = []

        if self.task_data["scores"]["error_cost"] >= 3:
            flags.append("- High error cost: Test thoroughly before production use")

        if self.task_data["override_flags"]:
            flags.append("- Override concerns present: Review mitigation strategies")

        if self.task_data["scores"]["frequency"] >= 3:
            flags.append("- High frequency: Automation failure will be immediately visible")

        if not flags:
            flags.append("- Monitor time savings vs. maintenance cost")

        return "\n".join(flags)

    def _suggest_review_date(self) -> str:
        """Suggest when to review this decision"""
        longevity = self.task_data["scores"]["longevity"]
        if longevity >= 5:
            return "Review in 1 year"
        elif longevity >= 3:
            return "Review in 6 months"
        else:
            return "Review in 3 months"

    async def speak(self, text: str):
        """Convert text to speech using Groq"""
        if not self.groq:
            print(f"\n[Would speak: {text}]\n")
            return

        try:
            # Use Groq's TTS (if available) or fallback to text display
            # Note: As of Jan 2025, Groq may not have TTS API
            # This is a placeholder for when it's available
            print(f"\n🔊 {text}\n")
            # TODO: Implement actual Groq TTS when available
        except Exception as e:
            print(f"\n[TTS Error: {e}]\n{text}\n")

    async def listen(self) -> str:
        """Listen for voice input using Groq Whisper"""
        if not self.groq:
            return input("> ")

        try:
            # TODO: Implement Groq Whisper STT
            # For now, fall back to text input
            return input("> ")
        except Exception as e:
            print(f"[STT Error: {e}]")
            return input("> ")


class ConsoleInterface:
    """Terminal-based interactive interface"""

    def __init__(self, advisor: AutomationAdvisor):
        self.advisor = advisor

    async def run(self):
        """Run console interface"""
        print("\n" + "="*60)
        print("🤖 AUTOMATION DECISION ADVISOR")
        print("="*60)
        print("\nUsing the Automation Decision Matrix framework")
        print("Let's evaluate whether to automate your task.\n")

        # Phase 1: Context gathering
        await self._phase_context()

        # Phase 2: Scoring
        await self._phase_scoring()

        # Phase 3: Calculate and present
        await self._phase_results()

        # Phase 4: Override checks
        await self._phase_overrides()

        # Phase 5: Validation (if needed)
        await self._phase_validation()

        # Phase 6: Build estimate
        await self._phase_build_estimate()

        # Phase 7: Final recommendation
        await self._phase_recommendation()

        # Phase 8: Generate outputs
        await self._phase_generate_outputs()

    async def _phase_context(self):
        """Phase 1: Gather task context"""
        print("\n--- PHASE 1: UNDERSTANDING YOUR TASK ---\n")

        task_name = input("What task are you considering automating?\n> ")
        self.advisor.task_data["task_name"] = task_name

        print("\nTell me how you currently do this manually:")
        context = input("> ")

        print("\nWhat frustrates you most about this task?")
        frustration = input("> ")

        print("\nWhat happens if this task isn't done, or is done incorrectly?")
        consequences = input("> ")

        self.advisor.task_data["context"] = f"{context}\n\nFrustrations: {frustration}\n\nConsequences if done wrong: {consequences}"

    async def _phase_scoring(self):
        """Phase 2: Score dimensions"""
        print("\n--- PHASE 2: SCORING DIMENSIONS ---\n")

        # Frequency
        print("\n1. How often do you perform this task?")
        print("   5 - Multiple times per day")
        print("   3 - Weekly")
        print("   1 - Monthly")
        print("   0 - Rarely or one-time")
        freq = int(input("Score (0-5): "))
        self.advisor.task_data["scores"]["frequency"] = freq

        # Time
        print("\n2. How long does it take each time?")
        print("   5 - Hours (2+)")
        print("   3 - 30-120 minutes")
        print("   1 - 5-30 minutes")
        print("   0 - Under 5 minutes")
        time = int(input("Score (0-5): "))
        self.advisor.task_data["scores"]["time"] = time

        # Error cost
        print("\n3. What happens if automation breaks?")
        print("   5 - Catastrophic (legal, customer loss, revenue)")
        print("   3 - Annoying (delays, manual intervention)")
        print("   1 - Negligible (easy to fix)")
        error = int(input("Score (1-5): "))
        self.advisor.task_data["scores"]["error_cost"] = error

        # Longevity
        print("\n4. How long will you do this task?")
        print("   5 - Years (core process)")
        print("   3 - Months (project-specific)")
        print("   1 - Weeks (temporary)")
        print("   0 - One-time")
        longevity = int(input("Score (0-5): "))
        self.advisor.task_data["scores"]["longevity"] = longevity

    async def _phase_results(self):
        """Phase 3: Calculate and show results"""
        score = self.advisor.calculate_score()
        decision = self.advisor.get_decision(score)

        print("\n--- PHASE 3: YOUR AUTOMATION SCORE ---\n")
        print(f"Score: {score}")
        print(f"Decision: {decision}")
        print(f"\nFormula: {self.advisor.task_data['scores']['frequency']} × {self.advisor.task_data['scores']['time']} × {self.advisor.task_data['scores']['error_cost']} × {self.advisor.task_data['scores']['longevity']} = {score}")

    async def _phase_overrides(self):
        """Phase 4: Check override conditions"""
        print("\n--- PHASE 4: RISK FACTORS ---\n")
        print("Do any of these concerns apply? (comma-separated numbers, or 0 for none)")
        print("1. High-stakes decisions without validation")
        print("2. Creative work needing authentic voice")
        print("3. Learning fundamentals")
        print("4. Regulated industry (HIPAA, GDPR, SOX)")
        print("5. Single point of failure risk")
        print("6. Rapidly changing requirements")
        print("7. Genuinely unique each time")

        choices = input("> ")
        if choices and choices != "0":
            flags = []
            flag_map = {
                "1": "High-stakes without validation",
                "2": "Creative work",
                "3": "Learning fundamentals",
                "4": "Regulated industry",
                "5": "Single point of failure",
                "6": "Rapidly changing",
                "7": "Unique each time"
            }
            for c in choices.split(","):
                c = c.strip()
                if c in flag_map:
                    flags.append(flag_map[c])
            self.advisor.task_data["override_flags"] = flags

    async def _phase_validation(self):
        """Phase 5: Validation pattern"""
        if self.advisor.task_data["scores"]["error_cost"] >= 3 or self.advisor.task_data["override_flags"]:
            print("\n--- PHASE 5: VALIDATION PATTERN ---\n")
            print("Which validation pattern fits?")
            print("1. Human-in-the-Loop (safest)")
            print("2. Confidence Threshold (auto if confident)")
            print("3. Audit Trail (periodic review)")
            print("4. Staged Rollout (gradual)")
            print("0. No validation needed")

            choice = input("> ")
            patterns = {
                "1": "Human-in-the-Loop",
                "2": "Confidence Threshold",
                "3": "Audit Trail",
                "4": "Staged Rollout"
            }
            if choice in patterns:
                self.advisor.task_data["validation_pattern"] = patterns[choice]

    async def _phase_build_estimate(self):
        """Phase 6: Build estimate"""
        print("\n--- PHASE 6: BUILD ESTIMATE ---\n")
        print("How many hours to build this automation?")
        hours = float(input("> "))
        self.advisor.task_data["build_estimate"] = hours

    async def _phase_recommendation(self):
        """Phase 7: Final recommendation"""
        score = self.advisor.calculate_score()
        decision = self.advisor.get_decision(score)

        print("\n" + "="*60)
        print(f"FINAL RECOMMENDATION: {decision}")
        print("="*60)
        print(f"\nScore: {score}")
        print(f"Reasoning: {self.advisor._get_decision_reasoning(score, decision)}")

        if self.advisor.task_data["override_flags"]:
            print(f"\nRisk factors identified: {len(self.advisor.task_data['override_flags'])}")

        if self.advisor.task_data["validation_pattern"]:
            print(f"Validation: {self.advisor.task_data['validation_pattern']}")

    async def _phase_generate_outputs(self):
        """Phase 8: Generate markdown and visualization"""
        print("\n--- GENERATING REPORT ---\n")
        filepath = self.advisor.generate_markdown_report()
        print(f"✅ Markdown report created: {filepath}")
        print("\nOpen in Obsidian to view full analysis")

        # Show visualization in console
        print("\n--- VISUALIZATION ---\n")
        viz = generate_full_report_visualization(self.advisor.task_data)
        print(viz)


async def main():
    parser = argparse.ArgumentParser(description="Automation Decision Advisor")
    parser.add_argument("--mode", choices=["console", "server"], default="console",
                      help="Interface mode")
    parser.add_argument("--port", type=int, default=8080,
                      help="Server port (server mode only)")
    parser.add_argument("--host", default="0.0.0.0",
                      help="Server host (server mode only)")

    args = parser.parse_args()

    if args.mode == "console":
        advisor = AutomationAdvisor()
        interface = ConsoleInterface(advisor)
        await interface.run()
    else:
        # Import and run web server
        print("Starting web server...")
        print(f"Importing server_web module...")

        # Import server_web and run
        import server_web
        server_web.run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main())
