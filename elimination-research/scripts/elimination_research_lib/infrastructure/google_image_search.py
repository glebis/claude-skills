import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, parse, request


API_ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"


@dataclass(frozen=True)
class GoogleImageSearchCredentials:
    api_key: str
    cx: str

    @property
    def is_complete(self) -> bool:
        return bool(self.api_key and self.cx)


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    if path.name.endswith(".enc") or _looks_like_sops_file(path):
        return _load_sops_env_file(path)
    raise ValueError(f"Credential file must be SOPS-encrypted: {path}")


def _load_plain_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_google_image_search_credentials(
    env_files: list[Path] | None = None,
) -> GoogleImageSearchCredentials:
    env_values: dict[str, str] = {}
    for env_file in env_files or default_credential_files():
        env_values.update(load_env_file(env_file.expanduser()))

    api_key = (
        os.environ.get("GOOGLE_CUSTOM_SEARCH_JSON_API_KEY")
        or os.environ.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
        or env_values.get("Google-Custom-Search-JSON-API-KEY")
        or env_values.get("GOOGLE_CUSTOM_SEARCH_JSON_API_KEY")
        or env_values.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
        or ""
    )
    cx = (
        os.environ.get("GOOGLE_CUSTOM_SEARCH_CX")
        or env_values.get("Google-Custom-Search-CX")
        or env_values.get("GOOGLE_CUSTOM_SEARCH_CX")
        or ""
    )
    return GoogleImageSearchCredentials(api_key=api_key, cx=cx)


def default_credential_files() -> list[Path]:
    configured = os.environ.get("GOOGLE_IMAGE_SEARCH_ENV_FILE")
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.extend(
        [
            Path(__file__).resolve().parents[2] / ".env.google-image-search.enc",
        ]
    )
    return candidates


def _looks_like_sops_file(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "sops_" in text or "sops=" in text


def _load_sops_env_file(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            "sops",
            "--decrypt",
            "--input-type",
            "dotenv",
            "--output-type",
            "dotenv",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return _load_plain_env_text(result.stdout)


def build_google_image_search_url(
    *,
    credentials: GoogleImageSearchCredentials,
    query: str,
    num_results: int = 5,
    safe: str = "active",
    site_search: str | None = None,
) -> str:
    params = {
        "key": credentials.api_key,
        "cx": credentials.cx,
        "q": query,
        "searchType": "image",
        "num": max(1, min(num_results, 10)),
        "safe": safe,
    }
    if site_search:
        params["siteSearch"] = site_search
    return f"{API_ENDPOINT}?{parse.urlencode(params)}"


def fetch_google_image_results(
    *,
    query: str,
    credentials: GoogleImageSearchCredentials,
    num_results: int = 5,
    requester: Callable[[str], dict] | None = None,
) -> dict:
    if not credentials.is_complete:
        raise ValueError("Google image search credentials are incomplete")
    url = build_google_image_search_url(
        credentials=credentials,
        query=query,
        num_results=num_results,
    )
    payload = (requester or _http_get_json)(url)
    return {
        "query": query,
        "search_information": payload.get("searchInformation", {}),
        "items": [_format_result_item(item) for item in payload.get("items", [])],
    }


def search_candidate_images(
    *,
    candidates: list[dict],
    credentials: GoogleImageSearchCredentials,
    num_results: int = 5,
    observed_at: str,
    requester: Callable[[str], dict] | None = None,
) -> dict:
    searches = []
    for candidate in candidates:
        config = candidate_image_query(candidate)
        bundle = fetch_google_image_results(
            query=config["query"],
            credentials=credentials,
            num_results=num_results,
            requester=requester,
        )
        scored_items = [
            _score_image_result(item, config)
            for item in bundle["items"]
        ]
        scored_items.sort(key=lambda item: item["score"], reverse=True)
        searches.append(
            {
                "candidate_id": candidate["id"],
                "candidate_name": candidate["name"],
                "query": config["query"],
                "required_terms": config["required_terms"],
                "preferred_hosts": config["preferred_hosts"],
                "result_count": len(scored_items),
                "selected": scored_items[0] if scored_items else None,
                "results": scored_items,
                "search_information": bundle["search_information"],
            }
        )

    return {
        "enabled": True,
        "provider": "google_custom_search",
        "mode": "cached_live_api_results",
        "observed_at": observed_at,
        "num_results_per_candidate": num_results,
        "candidate_count": len(candidates),
        "search_count": len(searches),
        "searches": searches,
    }


def candidate_image_query(candidate: dict) -> dict:
    brand = candidate.get("brand") or candidate["name"].split()[0]
    model = candidate["name"]
    category = candidate.get("category") or candidate.get("product_category") or "product"
    preferred_hosts = list(candidate.get("preferred_image_hosts", []))
    preferred_hosts.extend(candidate.get("preferred_source_domains", []))
    return {
        "query": candidate.get("image_query") or f"{model} {category} product photo",
        "required_terms": [brand],
        "optional_terms": candidate.get("image_optional_terms")
        or [category, "product", "photo", candidate.get("type", "")],
        "exclude_terms": candidate.get("image_exclude_terms")
        or ["review", "youtube", "manual", "pdf", "logo", "clipart"],
        "preferred_hosts": preferred_hosts,
    }


def summarize_image_search_results(image_search: dict | None) -> list[dict]:
    if not image_search or not image_search.get("enabled"):
        return []
    rows = []
    for search in image_search.get("searches", []):
        selected = search.get("selected") or {}
        rows.append(
            {
                "candidate_id": search.get("candidate_id", ""),
                "candidate_name": search.get("candidate_name", ""),
                "query": search.get("query", ""),
                "result_count": search.get("result_count", 0),
                "selected_title": selected.get("title", ""),
                "selected_url": selected.get("link", ""),
                "context_url": selected.get("context_link", ""),
                "host": selected.get("host", ""),
                "width": selected.get("width"),
                "height": selected.get("height"),
                "score": selected.get("score"),
            }
        )
    return rows


def _http_get_json(url: str) -> dict:
    req = request.Request(url)
    try:
        with request.urlopen(req) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except error.HTTPError as http_error:
        detail = http_error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Google image search HTTP {http_error.code}: {detail}") from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Google image search request failed: {url_error}") from url_error


def _format_result_item(item: dict) -> dict:
    image_meta = item.get("image", {})
    link = item.get("link", "")
    return {
        "title": item.get("title", ""),
        "link": link,
        "display_link": item.get("displayLink", ""),
        "context_link": image_meta.get("contextLink", ""),
        "mime": item.get("mime", ""),
        "byte_size": image_meta.get("byteSize"),
        "height": image_meta.get("height"),
        "width": image_meta.get("width"),
        "thumbnail_link": image_meta.get("thumbnailLink", ""),
        "host": _extract_host(link),
    }


def _score_image_result(item: dict, config: dict) -> dict:
    text = " ".join(
        str(value)
        for value in [
            item.get("title"),
            item.get("link"),
            item.get("display_link"),
            item.get("context_link"),
        ]
        if value
    ).lower()
    score = 0
    reasons = []

    missing_required = [
        term for term in config["required_terms"]
        if term and term.lower() not in text
    ]
    if missing_required:
        score -= 80
        reasons.append(f"missing required: {', '.join(missing_required)}")
    else:
        score += 30
        reasons.append("contains required brand term")

    optional_matches = [
        term for term in config["optional_terms"]
        if term and term.lower() in text
    ]
    if optional_matches:
        score += 5 * len(optional_matches)
        reasons.append(f"optional terms: {', '.join(optional_matches)}")

    excluded = [
        term for term in config["exclude_terms"]
        if term and term.lower() in text
    ]
    if excluded:
        score -= 50 * len(excluded)
        reasons.append(f"excluded terms: {', '.join(excluded)}")

    host = item.get("host", "")
    if host:
        if any(preferred in host for preferred in config["preferred_hosts"]):
            score += 25
            reasons.append(f"preferred host: {host}")
        else:
            score -= 5
            reasons.append(f"unlisted host: {host}")

    link = item.get("link", "")
    if "walmartimages.com" in host:
        score -= 20
        reasons.append("retailer CDN packaging risk")
    if "images?url=" in link or "static.thcdn.com" in link:
        score -= 20
        reasons.append("proxy-wrapped image penalized")

    mime = (item.get("mime") or "").lower()
    if "jpeg" in mime or "png" in mime or "webp" in mime:
        score += 5
        reasons.append("preferred image mime")
    elif "gif" in mime:
        score -= 10
        reasons.append("gif penalized")

    width = item.get("width") or 0
    height = item.get("height") or 0
    if width and height:
        if width >= 600 and height >= 400:
            score += 10
            reasons.append("high resolution")
        elif width < 300 or height < 300:
            score -= 10
            reasons.append("low resolution")

    return {**item, "score": score, "score_reasons": reasons}


def _extract_host(url: str) -> str:
    return parse.urlsplit(url).netloc.lower()
