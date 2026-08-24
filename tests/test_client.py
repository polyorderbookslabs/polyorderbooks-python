import pytest

from polyorderbooks import (
    AuthenticationError,
    PolyOrderbooksClient,
    RateLimitError,
)
from polyorderbooks._http import resolve_api_key


def test_resolve_api_key_from_argument():
    assert resolve_api_key("pob_test") == "pob_test"


def test_resolve_api_key_missing(monkeypatch):
    monkeypatch.delenv("POLYORDERBOOKS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key required"):
        resolve_api_key(None)


def test_list_markets_builds_query(httpx_mock):
    httpx_mock.add_response(
        json={"data": [{"slug": "btc-100k"}], "metadata": {"next_cursor": None}},
    )
    with PolyOrderbooksClient(api_key="pob_test") as client:
        payload = client.list_markets(search="bitcoin", limit=5)

    assert payload["data"][0]["slug"] == "btc-100k"
    request = httpx_mock.get_request()
    assert request.url.path == "/v1/markets"
    assert request.headers["X-API-Key"] == "pob_test"
    assert "search=bitcoin" in str(request.url)
    assert "limit=5" in str(request.url)


def test_get_market_books(httpx_mock):
    httpx_mock.add_response(
        json={"data": {"Yes": []}, "metadata": {"next_cursor": None}},
    )
    with PolyOrderbooksClient(api_key="pob_test") as client:
        payload = client.get_market_books(
            "will-btc-hit-100k",
            start_ts="2026-04-01T00:00:00Z",
            end_ts="2026-04-01T06:00:00Z",
            resolution="60s",
            limit=100,
        )

    assert "Yes" in payload["data"]
    request = httpx_mock.get_request()
    assert request.url.path == "/v1/markets/will-btc-hit-100k/books"


def test_authentication_error(httpx_mock):
    httpx_mock.add_response(status_code=401, json={"detail": "Invalid API key."})
    with PolyOrderbooksClient(api_key="pob_bad") as client:
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            client.get_usage()


def test_rate_limit_error(httpx_mock):
    httpx_mock.add_response(
        status_code=429,
        json={"detail": "Rate limit exceeded. Please try again later."},
    )
    with PolyOrderbooksClient(api_key="pob_test") as client:
        with pytest.raises(RateLimitError):
            client.list_tags()


def test_iter_market_books_pagination(httpx_mock):
    httpx_mock.add_response(
        json={"data": {"Yes": [{"t": "1"}]}, "metadata": {"next_cursor": "abc"}},
    )
    httpx_mock.add_response(
        json={"data": {"Yes": [{"t": "2"}]}, "metadata": {"next_cursor": None}},
    )
    with PolyOrderbooksClient(api_key="pob_test") as client:
        pages = list(
            client.iter_market_books(
                "sample-market",
                start_ts="2026-04-01T00:00:00Z",
                end_ts="2026-04-02T00:00:00Z",
                resolution="60s",
            )
        )

    assert len(pages) == 2
    assert httpx_mock.get_requests()[1].url.params.get("cursor") == "abc"


def test_rate_limit_error_exposes_retry_after():
    """The API sends Retry-After on 429; it is the only thing a caller can act on."""
    import httpx
    import pytest

    from polyorderbooks import RateLimitError
    from polyorderbooks._http import raise_for_status

    response = httpx.Response(
        429,
        headers={"Retry-After": "30"},
        json={"error": "rate_limited", "message": "Too many requests"},
        request=httpx.Request("GET", "https://api.polyorderbooks.com/v1/markets"),
    )
    with pytest.raises(RateLimitError) as err:
        raise_for_status(response)
    assert err.value.retry_after == 30.0
    assert err.value.status_code == 429


def test_rate_limit_error_without_retry_after():
    import httpx
    import pytest

    from polyorderbooks import RateLimitError
    from polyorderbooks._http import raise_for_status

    response = httpx.Response(
        429,
        json={"error": "rate_limited"},
        request=httpx.Request("GET", "https://api.polyorderbooks.com/v1/markets"),
    )
    with pytest.raises(RateLimitError) as err:
        raise_for_status(response)
    assert err.value.retry_after is None


def test_user_agent_tracks_the_package_version():
    """It was hardcoded to 0.1.0, so every release reported the same version."""
    import polyorderbooks
    from polyorderbooks._http import build_headers

    assert build_headers("k")["User-Agent"] == f"polyorderbooks-python/{polyorderbooks.__version__}"
