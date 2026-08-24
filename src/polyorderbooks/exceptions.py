from __future__ import annotations

from typing import Any


class PolyOrderbooksError(Exception):
    """Base error for the PolyOrderbooks SDK."""


class APIError(PolyOrderbooksError):
    """HTTP error returned by the PolyOrderbooks API."""

    def __init__(self, status_code: int, message: str, *, body: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.body = body


class AuthenticationError(APIError):
    """Missing or invalid API key (401)."""


class NotFoundError(APIError):
    """Resource not found (404)."""


class RateLimitError(APIError):
    """Rate limit exceeded (429).

    ``retry_after`` is the number of seconds the API asked you to wait, taken from
    the Retry-After header. It is ``None`` if the header was absent or unparseable.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        body: Any | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(status_code, message, body=body)
        self.retry_after = retry_after
