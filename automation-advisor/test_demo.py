#!/usr/bin/env python3
"""
Demo script showing automation-advisor visualizations

Run this to see example outputs before using the full interactive tool.
"""

from visualize import (
    generate_score_breakdown,
    generate_decision_tree,
    generate_threshold_gauge,
    generate_break_even_timeline,
    generate_risk_matrix,
    generate_full_report_visualization
)


def demo_high_score():
    """Example: Invoice Generation (Score 225)"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Invoice Generation (HIGH SCORE)")
    print("="*60)

    data = {
        "task_name": "Invoice Generation",
        "scores": {
            "frequency": 3,  # Weekly
            "time": 3,  # 30-120 min
            "error_cost": 5,  # Catastrophic
            "longevity": 5  # Years
        },
        "override_flags": ["High-stakes without validation"],
        "build_estimate": 8.0
    }

    score = 3 * 3 * 5 * 5  # 225

    print(generate_score_breakdown(data["scores"], score))
    print(generate_threshold_gauge(score))
    print(generate_decision_tree(score, "AUTOMATE NOW"))
    print(generate_break_even_timeline(8.0, 1.7, score))
    print(generate_risk_matrix(data["override_flags"], 5))


def demo_low_score():
    """Example: Monthly Report (Score 15)"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Monthly Internal Report (LOW SCORE)")
    print("="*60)

    data = {
        "task_name": "Monthly Internal Report",
        "scores": {
            "frequency": 1,  # Monthly
            "time": 5,  # 2+ hours
            "error_cost": 1,  # Negligible
            "longevity": 3  # Months
        },
        "override_flags": [],
        "build_estimate": 8.0
    }

    score = 1 * 5 * 1 * 3  # 15

    print(generate_score_breakdown(data["scores"], score))
    print(generate_threshold_gauge(score))
    print(generate_decision_tree(score, "STAY MANUAL"))
    print(generate_break_even_timeline(8.0, 0.4, score))
    print(generate_risk_matrix(data["override_flags"], 1))


def demo_borderline():
    """Example: Social Media Posting (Score 27)"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Social Media Posting (BORDERLINE)")
    print("="*60)

    data = {
        "task_name": "Social Media Posting",
        "scores": {
            "frequency": 3,  # Weekly
            "time": 1,  # 5-30 min
            "error_cost": 3,  # Annoying
            "longevity": 3  # Months
        },
        "override_flags": ["Creative work needing authentic voice"],
        "build_estimate": 4.0
    }

    score = 3 * 1 * 3 * 3  # 27

    print(generate_score_breakdown(data["scores"], score))
    print(generate_threshold_gauge(score))
    print(generate_decision_tree(score, "AUTOMATE IF EASY"))
    print(generate_break_even_timeline(4.0, 0.3, score))
    print(generate_risk_matrix(data["override_flags"], 3))


def demo_full_visualization():
    """Example: Full report visualization"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Full Report (as appears in markdown)")
    print("="*60)

    data = {
        "task_name": "Client Onboarding",
        "scores": {
            "frequency": 5,  # Daily
            "time": 5,  # 2+ hours
            "error_cost": 5,  # Catastrophic
            "longevity": 5  # Years
        },
        "override_flags": ["High-stakes without validation", "Regulated industry"],
        "build_estimate": 40.0
    }

    print(generate_full_report_visualization(data))


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# AUTOMATION ADVISOR - VISUALIZATION DEMOS")
    print("#"*60)

    demo_high_score()
    demo_low_score()
    demo_borderline()
    demo_full_visualization()

    print("\n" + "="*60)
    print("✅ All demos complete!")
    print("="*60)
    print("\nTo use the interactive advisor:")
    print("  python server.py --mode console")
    print("\nOr via Claude Code:")
    print("  /automation-advisor")
    print()
