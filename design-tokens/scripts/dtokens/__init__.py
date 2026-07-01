"""dtokens — deterministic DTCG (2025.10) subset core for the design-tokens skill."""


class TokenError(Exception):
    """Raised on malformed token files or unresolvable token graphs."""
