from __future__ import annotations

import os
from typing import Any

import httpx

from polyorderbooks.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)

DEFAULT_BASE_URL = "https://api.polyorderbooks.com"
DEFAULT_TIMEOUT = 60.0
ENV_API_KEY = "POLYORDERBOOKS_API_KEY"


def resolve_api_key(explicit: str | None) -> str:
    api_key = explicit or os.environ.get(ENV_API_KEY)
    if not api_key:
        raise ValueError(
            "API key required. Pass api_key=... or set POLYORDERBOOKS_API_KEY."
        )
    return api_key


def build_headers(api_key: str) -> dict[str, str]:
    # Imported lazily: polyorderbooks/__init__ imports client, which imports this module.
    from polyorderbooks import __version__

    return {
        "Accept": "application/json",
        "X-API-Key": api_key,
        "User-Agent": f"polyorderbooks-python/{__version__}",
    }


def parse_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or response.reason_phrase

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail:
            return detail
        message = payload.get("message")
        if isinstance(message, str) and message:
            return message
    return response.reason_phrase


def parse_retry_after(response: httpx.Response) -> float | None:
    """Seconds to wait, from the Retry-After header the API sends on 429."""
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


def raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return

    message = parse_error_message(response)
    kwargs = {"body": None}
    try:
        kwargs["body"] = response.json()
    except ValueError:
        kwargs["body"] = response.text

    status = response.status_code
    if status == 401:
        raise AuthenticationError(status, message, **kwargs)
    if status == 404:
        raise NotFoundError(status, message, **kwargs)
    if status == 429:
        raise RateLimitError(
            status, message, retry_after=parse_retry_after(response), **kwargs
        )
    raise APIError(status, message, **kwargs)


def request_json(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.request(method, path, params=params)
    raise_for_status(response)
    payload = response.json()
    if not isinstance(payload, dict):
        raise APIError(response.status_code, "Expected JSON object response.")
    return payload
