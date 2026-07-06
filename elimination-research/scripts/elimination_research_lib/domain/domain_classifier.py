from dataclasses import dataclass
from enum import Enum, auto
from urllib.parse import urlparse


class SourceRole(Enum):
    DISCOVERY = auto()
    EVIDENCE = auto()
    PRICE_REFERENCE = auto()
    PURCHASE_RECOMMENDATION = auto()


class TrustTier(Enum):
    LOW = auto()
    HIGH = auto()


class SourceType(Enum):
    AFFILIATE = auto()
    RETAILER = auto()


class HumanApprovalStatus(Enum):
    APPROVED = auto()
    REQUIRES_REVIEW = auto()


@dataclass(frozen=True)
class SourceRegistryEntry:
    domain: str
    allowed_roles: set[SourceRole]
    blocked_roles: set[SourceRole]
    trust_tier: TrustTier
    source_type: SourceType
    human_approval_status: HumanApprovalStatus
    confidence: float


class DomainClassifier:
    def __init__(self, registry_entries=None):
        self._registry_entries = {
            entry.domain: entry for entry in (registry_entries or [])
        }

    def classify(self, url: str) -> SourceRegistryEntry:
        parsed = urlparse(url)
        domain = parsed.hostname or parsed.path

        if domain in self._registry_entries:
            return self._registry_entries[domain]

        return SourceRegistryEntry(
            domain=domain,
            allowed_roles={SourceRole.DISCOVERY},
            blocked_roles={
                SourceRole.EVIDENCE,
                SourceRole.PRICE_REFERENCE,
                SourceRole.PURCHASE_RECOMMENDATION,
            },
            trust_tier=TrustTier.LOW,
            source_type=SourceType.AFFILIATE,
            human_approval_status=HumanApprovalStatus.REQUIRES_REVIEW,
            confidence=0.6,
        )

