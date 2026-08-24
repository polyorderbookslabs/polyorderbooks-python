"""Official Python client for the PolyOrderbooks API."""

from importlib.metadata import PackageNotFoundError, version as _version

from polyorderbooks.client import PolyOrderbooksClient
from polyorderbooks.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    PolyOrderbooksError,
    RateLimitError,
)

__all__ = [
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "PolyOrderbooksClient",
    "PolyOrderbooksError",
    "RateLimitError",
]
try:
    __version__ = _version("polyorderbooks")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0.dev0"
