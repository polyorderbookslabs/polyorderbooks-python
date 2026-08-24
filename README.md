# PolyOrderbooks Python SDK

[![PyPI version](https://badge.fury.io/py/polyorderbooks.svg)](https://pypi.org/project/polyorderbooks/)
[![Python Versions](https://img.shields.io/pypi/pyversions/polyorderbooks)](https://pypi.org/project/polyorderbooks/)
[![CI](https://github.com/polyorderbooks/polyorderbooks-python/actions/workflows/ci.yml/badge.svg)](https://github.com/polyorderbooks/polyorderbooks-python/actions/workflows/ci.yml)

Official Python client for the [PolyOrderbooks API](https://docs.polyorderbooks.com) — historical Polymarket order books, prices, and liquidity metrics.

## What is covered

Polymarket **crypto** markets: up/down rounds (5m, 15m, 4h), price thresholds,
and related event markets. Order books are captured at 1-second resolution and
resolved markets are stored alongside their winning outcome.

Every plan queries at `1s`, including the free tier. Plans differ on history
window and request volume — see [pricing](https://polyorderbooks.com/pricing).

## Install

```bash
pip install polyorderbooks
```

Or install the latest from GitHub:

```bash
pip install git+https://github.com/polyorderbooks/polyorderbooks-python.git
```

## Quickstart

Get an API key from [polyorderbooks.com/signup](https://polyorderbooks.com/signup), then:

```python
import os
from datetime import datetime, timedelta, timezone

from polyorderbooks import PolyOrderbooksClient

client = PolyOrderbooksClient(api_key=os.environ["POLYORDERBOOKS_API_KEY"])

# Or rely on POLYORDERBOOKS_API_KEY in the environment:
# client = PolyOrderbooksClient()

markets = client.list_markets(search="bitcoin", limit=5)
slug = markets["data"][0]["slug"]

end = datetime.now(timezone.utc)
start = end - timedelta(hours=6)

books = client.get_market_books(
    slug,
    start_ts=start.isoformat().replace("+00:00", "Z"),
    end_ts=end.isoformat().replace("+00:00", "Z"),
    resolution="1s",
    limit=100,
)

for outcome, points in books["data"].items():
    for point in points[:2]:
        bids = point.get("bids") or []
        asks = point.get("asks") or []
        best_bid = bids[0][0] if bids else None
        best_ask = asks[0][0] if asks else None
        print(point["t"], outcome, "bid", best_bid, "ask", best_ask)

client.close()
```

`markets["data"]` is a list of market objects. Each item includes more fields (`public_id`, `volume`, `event_slug`, …); the essentials look like:

```json
[
    {
        "slug": "will-bitcoin-hit-150k-in-2026",
        "question": "Will Bitcoin hit $150k in 2026?",
        "status": "active"
    },
    {
        "slug": "fed-rate-cut-september-2026",
        "question": "Will the Fed cut rates in September 2026?",
        "status": "active"
    }
]
```

`books["data"]` is keyed by outcome label (`"Yes"`, `"No"`), and each snapshot is
`{"t", "bids", "asks"}`. Ladders are `[price, size]` pairs, **best price first** —
bids descend, asks ascend. Depth varies per snapshot, so do not assume a fixed
number of levels:

```json
{
    "t": "2026-08-19T02:00:00Z",
    "bids": [[0.19, 147.34], [0.18, 63.69], [0.17, 277.77]],
    "asks": [[0.20, 13.6], [0.21, 152.17]]
}
```

A snapshot list can be empty for markets with no captures in the requested
window, so guard before indexing `bids[0]` / `asks[0]`.

Context manager usage:

```python
with PolyOrderbooksClient() as client:
    usage = client.get_usage()
    print(usage["plan"], usage["limits"])
```

## Pagination

Use `metadata.next_cursor` manually, or helpers:

```python
for page in client.iter_market_books(
    slug,
    start_ts="2026-04-01T00:00:00Z",
    end_ts="2026-04-02T00:00:00Z",
    resolution="1s",
):
    process(page["data"])
```

## API coverage

| Method | Endpoint |
| --- | --- |
| `get_usage()` | `GET /v1/usage` |
| `list_series(...)` | `GET /v1/series` |
| `list_events(...)` | `GET /v1/events` |
| `list_markets(...)` | `GET /v1/markets` |
| `get_market(id_or_slug)` | `GET /v1/markets/{id_or_slug}` |
| `list_tags()` | `GET /v1/tags` |
| `get_market_metrics(...)` | `GET /v1/markets/{id_or_slug}/metrics` |
| `get_market_prices(...)` | `GET /v1/markets/{id_or_slug}/prices` |
| `get_market_books(...)` | `GET /v1/markets/{id_or_slug}/books` |
| `get_token_prices(...)` | `GET /v1/tokens/{token_id}/prices` |
| `get_token_books(...)` | `GET /v1/tokens/{token_id}/books` |

## Authentication

Send your API key via the client constructor or `POLYORDERBOOKS_API_KEY`. The SDK sets `X-API-Key` on every request (the API also accepts `Authorization: Bearer pob_…`).

## Errors

```python
from polyorderbooks import AuthenticationError, NotFoundError, RateLimitError, APIError
```

- `AuthenticationError` — 401
- `NotFoundError` — 404
- `RateLimitError` — 429
- `APIError` — other HTTP failures

Every error carries `status_code`, `message` and the parsed `body`.
`RateLimitError` also carries `retry_after`, the seconds the API asked you to
wait:

```python
import time

from polyorderbooks import RateLimitError

try:
    books = client.get_market_books(slug, start_ts=..., end_ts=..., resolution="1s")
except RateLimitError as err:
    time.sleep(err.retry_after or 1)
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Links

- Product: [polyorderbooks.com](https://polyorderbooks.com)
- Docs: [docs.polyorderbooks.com](https://docs.polyorderbooks.com)
- OpenAPI: [docs.polyorderbooks.com/openapi.json](https://docs.polyorderbooks.com/openapi.json)

## License

MIT — see [LICENSE](LICENSE).
