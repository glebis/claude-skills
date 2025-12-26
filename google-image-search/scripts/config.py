"""Configuration and credentials handling for Google Image Search skill."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_env(path: Path) -> Dict[str, str]:
    """Load a minimal .env file, preserving keys with hyphens."""
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def resolve_credentials(
    api_key: Optional[str] = None,
    cx: Optional[str] = None,
    env_file: Optional[Path] = None,
) -> Dict[str, str]:
    """Resolve API credentials from args, environment, or .env file."""
    env_path = env_file or Path(".env")
    env = load_env(env_path)

    resolved_api_key = (
        api_key
        or os.environ.get("GOOGLE_CUSTOM_SEARCH_JSON_API_KEY")
        or os.environ.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
        or env.get("Google-Custom-Search-JSON-API-KEY")
        or env.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
    )
    resolved_cx = (
        cx
        or os.environ.get("GOOGLE_CUSTOM_SEARCH_CX")
        or env.get("Google-Custom-Search-CX")
        or env.get("GOOGLE_CUSTOM_SEARCH_CX")
    )
    return {"api_key": resolved_api_key or "", "cx": resolved_cx or ""}


def get_openrouter_key(env_file: Optional[Path] = None) -> Optional[str]:
    """Get OpenRouter API key from environment or .env file."""
    env_path = env_file or Path(".env")
    env = load_env(env_path)
    return (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENROUTER-API-KEY")
        or env.get("OPENROUTER_API_KEY")
        or env.get("OPENROUTER-API-KEY")
    )


def load_queries(config_path: Path) -> List[Dict[str, Any]]:
    """Load query entries from JSON config file."""
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Config must be a list of query entries")
    return data


def create_simple_entry(
    query: str,
    heading: Optional[str] = None,
    num_results: int = 5,
    selection_count: int = 2,
) -> Dict[str, Any]:
    """Create a config entry from a simple query string."""
    # Use query as heading if not provided
    entry_heading = heading or query.split()[0].title() if query else "Image"

    return {
        "id": query.lower().replace(" ", "-")[:40],
        "heading": entry_heading,
        "description": f"Image search for: {query}",
        "query": query,
        "numResults": num_results,
        "selectionCount": selection_count,
        "safe": "active",
    }


def create_entry_from_term(
    term: str,
    description: Optional[str] = None,
    selection_criteria: Optional[str] = None,
    required_terms: Optional[List[str]] = None,
    optional_terms: Optional[List[str]] = None,
    exclude_terms: Optional[List[str]] = None,
    preferred_hosts: Optional[List[str]] = None,
    num_results: int = 5,
    selection_count: int = 2,
) -> Dict[str, Any]:
    """Create a full config entry for a term with optional criteria."""
    entry = {
        "id": term.lower().replace(" ", "-")[:40],
        "heading": term,
        "description": description or f"Visual representation of {term}",
        "query": term,
        "numResults": num_results,
        "selectionCount": selection_count,
        "safe": "active",
    }

    if selection_criteria:
        entry["selectionCriteria"] = selection_criteria
    if required_terms:
        entry["requiredTerms"] = required_terms
    if optional_terms:
        entry["optionalTerms"] = optional_terms
    if exclude_terms:
        entry["excludeTerms"] = exclude_terms
    if preferred_hosts:
        entry["preferredHosts"] = preferred_hosts

    return entry


def save_config(entries: List[Dict[str, Any]], output_path: Path) -> None:
    """Save config entries to JSON file."""
    output_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
