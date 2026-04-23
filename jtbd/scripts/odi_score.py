"""Outcome-Driven Innovation (ODI) opportunity scoring."""


def score(importance, satisfaction):
    return importance + max(0, importance - satisfaction)


def tier(opportunity_score):
    if opportunity_score >= 12:
        return "prioritize"
    if opportunity_score <= 8:
        return "skip"
    return "marginal"
