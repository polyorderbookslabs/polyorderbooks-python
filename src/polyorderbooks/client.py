from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

import httpx

from polyorderbooks._http import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    build_headers,
    request_json,
    resolve_api_key,
)

Resolution = Literal["1s", "60s", "1m", "5m", "10m", "15m", "1h", "6h", "1d"]
SortField = Literal["updated_at", "created_at", "start_date", "end_date", "title"]
SortOrder = Literal["asc", "desc"]
TagsMatch = Literal["any", "all"]


class PolyOrderbooksClient:
    """Sync client for the PolyOrderbooks read API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = resolve_api_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=build_headers(self._api_key),
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PolyOrderbooksClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # --- Utility ---

    def get_usage(self) -> dict[str, Any]:
        """Return plan, limits, and quota usage for the authenticated API key."""
        return request_json(self._client, "GET", "/v1/usage")

    # --- Discovery ---

    def list_series(
        self,
        *,
        search: str | None = None,
        tags: list[str] | str | None = None,
        tags_match: TagsMatch = "any",
        start_date_min: str | None = None,
        start_date_max: str | None = None,
        end_date_min: str | None = None,
        end_date_max: str | None = None,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = self._discovery_params(
            search=search,
            tags=tags,
            tags_match=tags_match,
            start_date_min=start_date_min,
            start_date_max=start_date_max,
            end_date_min=end_date_min,
            end_date_max=end_date_max,
            sort=sort,
            order=order,
            limit=limit,
            cursor=cursor,
        )
        return request_json(self._client, "GET", "/v1/series", params=params)

    def list_events(
        self,
        *,
        search: str | None = None,
        series_id: str | None = None,
        series_slug: str | None = None,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = self._discovery_params(
            search=search,
            series_id=series_id,
            series_slug=series_slug,
            sort=sort,
            order=order,
            limit=limit,
            cursor=cursor,
        )
        return request_json(self._client, "GET", "/v1/events", params=params)

    def list_markets(
        self,
        *,
        search: str | None = None,
        event_id: str | None = None,
        event_slug: str | None = None,
        include_closed: bool = False,
        sort: SortField = "updated_at",
        order: SortOrder = "desc",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = self._discovery_params(
            search=search,
            event_id=event_id,
            event_slug=event_slug,
            include_closed=include_closed,
            sort=sort,
            order=order,
            limit=limit,
            cursor=cursor,
        )
        return request_json(self._client, "GET", "/v1/markets", params=params)

    def get_market(self, id_or_slug: str) -> dict[str, Any]:
        return request_json(
            self._client, "GET", f"/v1/markets/{id_or_slug}"
        )

    def list_tags(self) -> dict[str, Any]:
        return request_json(self._client, "GET", "/v1/tags")

    # --- History ---

    def get_market_metrics(
        self,
        id_or_slug: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._history_request(
            f"/v1/markets/{id_or_slug}/metrics",
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )

    def get_market_prices(
        self,
        id_or_slug: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._history_request(
            f"/v1/markets/{id_or_slug}/prices",
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )

    def get_market_books(
        self,
        id_or_slug: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._history_request(
            f"/v1/markets/{id_or_slug}/books",
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )

    def get_token_prices(
        self,
        token_id: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._history_request(
            f"/v1/tokens/{token_id}/prices",
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )

    def get_token_books(
        self,
        token_id: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._history_request(
            f"/v1/tokens/{token_id}/books",
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )

    # --- Pagination helpers ---

    def iter_markets(
        self,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        """Yield each page from ``list_markets`` until ``next_cursor`` is exhausted."""
        yield from self._iter_pages(self.list_markets, params)

    def iter_market_books(
        self,
        id_or_slug: str,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        """Yield each page from ``get_market_books`` until ``next_cursor`` is exhausted."""
        yield from self._iter_pages(
            lambda **kw: self.get_market_books(id_or_slug, **kw),
            params,
        )

    def _history_request(
        self,
        path: str,
        *,
        start_ts: str,
        end_ts: str,
        resolution: Resolution,
        limit: int | None,
        cursor: str | None,
    ) -> dict[str, Any]:
        params = self._compact(
            start_ts=start_ts,
            end_ts=end_ts,
            resolution=resolution,
            limit=limit,
            cursor=cursor,
        )
        return request_json(self._client, "GET", path, params=params)

    def _discovery_params(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        tags = params.pop("tags", None)
        if tags is not None:
            if isinstance(tags, list):
                params["tags"] = ",".join(tags)
            else:
                params["tags"] = tags
        include_closed = params.pop("include_closed", None)
        if include_closed is not None:
            params["include_closed"] = str(include_closed).lower()
        return self._compact(**params)

    @staticmethod
    def _compact(**kwargs: Any) -> dict[str, Any]:
        return {key: value for key, value in kwargs.items() if value is not None}

    @staticmethod
    def _iter_pages(
        fetch_page: Any,
        params: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        while True:
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            page = fetch_page(**page_params)
            yield page
            metadata = page.get("metadata") or {}
            cursor = metadata.get("next_cursor")
            if not cursor:
                break
