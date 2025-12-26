"""Google Custom Search API wrapper."""

import json
from typing import Any, Dict, Optional
from urllib import error, parse, request

API_ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"


def build_request_url(
    *,
    api_key: str,
    cx: str,
    query: str,
    num: int,
    img_type: Optional[str] = None,
    rights: Optional[str] = None,
    safe: Optional[str] = None,
    file_type: Optional[str] = None,
    site: Optional[str] = None,
) -> str:
    """Build the Google Custom Search API request URL."""
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "searchType": "image",
        "num": max(1, min(num, 10)),
    }
    if img_type:
        params["imgType"] = img_type
    if rights:
        params["rights"] = rights
    if safe:
        params["safe"] = safe
    if file_type:
        params["fileType"] = file_type
    if site:
        params["siteSearch"] = site
    return f"{API_ENDPOINT}?{parse.urlencode(params)}"


def http_get(url: str) -> Dict[str, Any]:
    """Make HTTP GET request and return JSON response."""
    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            payload = resp.read().decode(charset)
    except error.HTTPError as http_err:
        detail = http_err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"HTTP {http_err.code} error for URL {url}: {detail}"
        ) from http_err
    except error.URLError as url_err:
        raise RuntimeError(f"Failed to reach API: {url_err}") from url_err
    return json.loads(payload)


def extract_host(url: Optional[str]) -> Optional[str]:
    """Extract hostname from URL."""
    if not url:
        return None
    netloc = parse.urlsplit(url).netloc
    return netloc.lower() if netloc else None


def format_result_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format a single search result item."""
    image_meta = item.get("image", {})
    link = item.get("link")
    return {
        "title": item.get("title"),
        "link": link,
        "displayLink": item.get("displayLink"),
        "contextLink": image_meta.get("contextLink") or item.get("image", {}).get("contextLink"),
        "mime": item.get("mime"),
        "byteSize": image_meta.get("byteSize"),
        "height": image_meta.get("height"),
        "width": image_meta.get("width"),
        "fileFormat": image_meta.get("fileFormat"),
        "thumbnailLink": image_meta.get("thumbnailLink"),
        "host": extract_host(link),
    }


def fetch_images_for_entry(
    *,
    entry: Dict[str, Any],
    api_key: str,
    cx: str,
) -> Dict[str, Any]:
    """Fetch images for a single config entry."""
    query = entry["query"]
    count = entry.get("numResults", 5)
    img_type = entry.get("imgType")
    rights = entry.get("rights")
    safe = entry.get("safe", "active")
    file_type = entry.get("fileType")
    site = entry.get("siteSearch")

    request_url = build_request_url(
        api_key=api_key,
        cx=cx,
        query=query,
        num=count,
        img_type=img_type,
        rights=rights,
        safe=safe,
        file_type=file_type,
        site=site,
    )
    data = http_get(request_url)
    items = data.get("items", [])

    formatted_items = [format_result_item(item) for item in items]
    return {
        "entry": entry,
        "results": formatted_items,
        "searchInformation": data.get("searchInformation", {}),
    }


def fetch_images_simple(
    query: str,
    api_key: str,
    cx: str,
    num_results: int = 5,
) -> Dict[str, Any]:
    """Simple image fetch without full config entry."""
    from .config import create_simple_entry
    entry = create_simple_entry(query, num_results=num_results)
    return fetch_images_for_entry(entry=entry, api_key=api_key, cx=cx)
