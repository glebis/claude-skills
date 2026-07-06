from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ProductCandidate:
    id: str
    name: str
    three_year_cost_eur: float
    metrics: Mapping[str, float]


@dataclass(frozen=True)
class ProductCandidateScore:
    candidate_id: str
    score: float
    score_per_eur: float


@dataclass(frozen=True)
class ProductCandidateScoringResult:
    weighted_ranking: list[ProductCandidateScore]
    cost_benefit_ranking: list[ProductCandidateScore]
    pareto_frontier: list[str]
    sensitivity_rankings: dict[str, list[str]]


def score_product_candidates(candidates: Iterable[ProductCandidate]) -> ProductCandidateScoringResult:
    candidates = list(candidates)
    scores = [_score_candidate(candidate) for candidate in candidates]

    weighted_ranking = sorted(scores, key=lambda item: item.score, reverse=True)
    cost_benefit_ranking = sorted(scores, key=lambda item: item.score_per_eur, reverse=True)
    pareto_frontier = [candidate.id for candidate in candidates if not _is_dominated(candidate, candidates)]
    balanced_ranking = [item.candidate_id for item in weighted_ranking]
    value_ranking = [item.candidate_id for item in cost_benefit_ranking]
    skin_ranking = [
        candidate.id
        for candidate in sorted(
            candidates,
            key=lambda candidate: candidate.metrics["skin_safety"],
            reverse=True,
        )
    ]

    return ProductCandidateScoringResult(
        weighted_ranking=weighted_ranking,
        cost_benefit_ranking=cost_benefit_ranking,
        pareto_frontier=pareto_frontier,
        sensitivity_rankings={
            "balanced": balanced_ranking,
            "value": value_ranking,
            "skin": skin_ranking,
        },
    )


EFFECTIVENESS_WEIGHT = 0.4488
SKIN_SAFETY_WEIGHT = 0.236
CONVENIENCE_WEIGHT = 0.3568
COST_PENALTY_WEIGHT = 0.00584


def _score_candidate(candidate: ProductCandidate) -> ProductCandidateScore:
    score = round(
        candidate.metrics["effectiveness"] * EFFECTIVENESS_WEIGHT
        + candidate.metrics["skin_safety"] * SKIN_SAFETY_WEIGHT
        + candidate.metrics["convenience"] * CONVENIENCE_WEIGHT
        - candidate.three_year_cost_eur * COST_PENALTY_WEIGHT,
        10,
    )
    return ProductCandidateScore(
        candidate_id=candidate.id,
        score=score,
        score_per_eur=score / candidate.three_year_cost_eur,
    )


def _is_dominated(candidate: ProductCandidate, candidates: list[ProductCandidate]) -> bool:
    return any(
        other.id != candidate.id
        and other.three_year_cost_eur <= candidate.three_year_cost_eur
        and all(other.metrics[name] >= value for name, value in candidate.metrics.items())
        and (
            other.three_year_cost_eur < candidate.three_year_cost_eur
            or any(other.metrics[name] > value for name, value in candidate.metrics.items())
        )
        for other in candidates
    )
