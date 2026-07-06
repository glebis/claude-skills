from dataclasses import dataclass
from decimal import Decimal
import re

from domain.domain_classifier import SourceRegistryEntry


_NUMERIC_VALUE_PATTERN = re.compile(r"\d+(?:[,.]\d+)?")


@dataclass(frozen=True)
class RawEvidence:
    candidate_id: str
    source_url: str
    source_title: str
    accessed_at: str
    source: SourceRegistryEntry
    text_fields: dict[str, str]


@dataclass(frozen=True)
class SourceReference:
    url: str
    title: str
    domain: str
    accessed_at: str
    field_name: str


@dataclass(frozen=True)
class NormalizedFact:
    candidate_id: str
    metric: str
    value: Decimal
    unit: str
    is_proxy: bool
    confidence: float
    source_ref: SourceReference


def normalize_evidence(raw: RawEvidence) -> list[NormalizedFact]:
    facts: list[NormalizedFact] = []

    for field_name, text in raw.text_fields.items():
        if "price" in field_name and "€" in text:
            match = _NUMERIC_VALUE_PATTERN.search(text)
            if match:
                facts.append(_fact(raw, field_name, "price", match.group(0), "EUR"))

        if field_name == "battery_runtime" and "min" in text:
            match = _NUMERIC_VALUE_PATTERN.search(text)
            if match:
                facts.append(_fact(raw, field_name, "battery_runtime", match.group(0), "minute"))

    return facts


def _fact(raw: RawEvidence, field_name: str, metric: str, value: str, unit: str) -> NormalizedFact:
    return NormalizedFact(
        candidate_id=raw.candidate_id,
        metric=metric,
        value=Decimal(value.replace(",", ".")),
        unit=unit,
        is_proxy=False,
        confidence=raw.source.confidence,
        source_ref=SourceReference(
            url=raw.source_url,
            title=raw.source_title,
            domain=raw.source.domain,
            accessed_at=raw.accessed_at,
            field_name=field_name,
        ),
    )
