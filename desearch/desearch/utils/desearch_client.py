"""Minimal client for the Desearch REST API (https://api.desearch.ai).

The API key is sent as the raw value of the Authorization header. It is never
logged and never included in error messages.
"""
from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://api.desearch.ai"
AI_SOURCES = ("web", "twitter", "reddit", "hackernews", "arxiv", "wikipedia")
DATE_FILTERS = (
    "PAST_24_HOURS", "PAST_2_DAYS", "PAST_WEEK", "PAST_2_WEEKS",
    "PAST_MONTH", "PAST_2_MONTHS", "PAST_YEAR", "PAST_2_YEARS",
)
X_SORTS = ("Top", "Latest")


class DesearchError(Exception):
    """Request failed; message is safe to show to the user."""


class DesearchClient:
    def __init__(self, api_key: str, session: Any = None, timeout: int = 60):
        api_key = (api_key or "").strip()
        if not api_key:
            raise DesearchError("Desearch API key is missing. Create one at https://console.desearch.ai/api-keys")
        self._api_key = api_key
        self._session = session or requests
        self._timeout = timeout

    def _request(self, method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> Any:
        headers = {"Authorization": self._api_key, "Accept": "application/json"}
        try:
            response = self._session.request(
                method, BASE_URL + path, headers=headers, params=params, json=json, timeout=self._timeout
            )
        except requests.exceptions.Timeout:
            raise DesearchError("Desearch API request timed out") from None
        except requests.exceptions.RequestException as e:
            raise DesearchError(f"Desearch API request failed: {type(e).__name__}") from None
        if response.status_code in (401, 403):
            raise DesearchError(f"Desearch API rejected the API key (HTTP {response.status_code})")
        if response.status_code == 429:
            raise DesearchError("Desearch API rate limit reached (HTTP 429)")
        if not 200 <= response.status_code < 300:
            detail = (response.text or "")[:300].replace(self._api_key, "***")
            raise DesearchError(f"Desearch API error (HTTP {response.status_code}): {detail}")
        try:
            return response.json()
        except ValueError:
            raise DesearchError("Desearch API returned a non-JSON response") from None

    def check_key(self) -> None:
        """Free key check: GET /web without the required query parameter.

        The API checks the key before it validates parameters. A valid key gets
        HTTP 422 (validation error, no search runs, nothing is billed). An invalid
        key gets HTTP 403 and a missing key gets HTTP 401.
        """
        headers = {"Authorization": self._api_key, "Accept": "application/json"}
        try:
            response = self._session.request("GET", BASE_URL + "/web", headers=headers, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise DesearchError("Desearch API request timed out") from None
        except requests.exceptions.RequestException as e:
            raise DesearchError(f"Desearch API request failed: {type(e).__name__}") from None
        if response.status_code == 422:
            return
        if response.status_code in (401, 403):
            raise DesearchError(
                f"Desearch API rejected the API key (HTTP {response.status_code}). "
                "Create or copy a key at https://console.desearch.ai/api-keys"
            )
        raise DesearchError(f"Unexpected response while checking the API key (HTTP {response.status_code})")

    def web_search(self, query: str, start: int | None = None) -> Any:
        params: dict[str, Any] = {"query": query}
        if start:
            params["start"] = int(start)
        return self._request("GET", "/web", params=params)

    def ai_search(self, prompt: str, sources: list[str], date_filter: str | None = None) -> Any:
        body: dict[str, Any] = {"prompt": prompt, "tools": sources, "streaming": False}
        if date_filter:
            body["date_filter"] = date_filter
        return self._request("POST", "/desearch/ai/search", json=body)

    def x_search(self, query: str, count: int = 10, sort: str = "Top", **filters: Any) -> Any:
        params: dict[str, Any] = {"query": query, "count": int(count), "sort": sort}
        params.update({k: v for k, v in filters.items() if v not in (None, "")})
        return self._request("GET", "/twitter", params=params)


def parse_sources(value: str | None) -> list[str]:
    """Comma list -> validated source ids. Empty means web and twitter."""
    if not value or not str(value).strip():
        return ["web", "twitter"]
    sources = []
    for raw in str(value).split(","):
        item = raw.strip().lower()
        if not item:
            continue
        if item == "x":
            item = "twitter"
        if item not in AI_SOURCES:
            raise DesearchError(f"Unknown source '{item}'. Use: {', '.join(AI_SOURCES)}")
        if item not in sources:
            sources.append(item)
    return sources or ["web", "twitter"]


def collect_links(body: Any) -> list[dict]:
    """Find title/link pairs in any list of result objects in an AI search body."""
    links: list[dict] = []
    seen: set[str] = set()
    if not isinstance(body, dict):
        return links
    for value in body.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            url = item.get("link") or item.get("url")
            if url and url not in seen:
                seen.add(url)
                links.append({"title": item.get("title") or item.get("text") or "", "link": url})
    return links
