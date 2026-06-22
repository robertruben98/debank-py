"""Shared configuration and response-handling logic for the DeBank clients.

The sync and async clients differ only in how they perform I/O. Everything that
does not touch the network — building headers, normalising query parameters,
turning an :class:`httpx.Response` into JSON or an exception, deciding whether a
response is retryable, and computing backoff delays — lives here so both clients
behave identically.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

import httpx

from .exceptions import DeBankAPIError, DeBankRateLimitError

DEFAULT_BASE_URL = "https://pro-openapi.debank.com"
DEFAULT_ACCESS_KEY_HEADER = "AccessKey"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_FACTOR = 0.5


def build_headers(access_key: str, access_key_header: str) -> dict[str, str]:
    """Build the default request headers.

    DeBank Cloud authenticates with the AccessKey sent in a request header
    (``AccessKey`` by default; the header name is configurable for proxies).

    Args:
        access_key: The DeBank Cloud Pro AccessKey.
        access_key_header: The header name to send the key under.

    Returns:
        A header dict suitable for the underlying httpx client.
    """
    return {
        "Accept": "application/json",
        "User-Agent": "debank-py",
        access_key_header: access_key,
    }


def clean_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """Normalise query parameters for the DeBank API.

    ``None`` values are dropped so optional parameters are simply omitted,
    booleans are rendered as the lowercase strings ``"true"``/``"false"`` the
    API expects, and list/tuple values are comma-joined (DeBank's ``chain_ids``
    and ``ids`` parameters take comma-separated values).

    Args:
        params: The raw parameter mapping.

    Returns:
        A cleaned parameter dict.
    """
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            cleaned[key] = ",".join(str(item) for item in value)
        else:
            cleaned[key] = value
    return cleaned


def parse_retry_after(response: httpx.Response) -> Optional[float]:
    """Parse the ``Retry-After`` header into seconds, if present and numeric."""
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def backoff_delay(attempt: int, backoff_factor: float, retry_after: Optional[float]) -> float:
    """Compute how long to sleep before the next retry.

    An explicit ``Retry-After`` from the server wins; otherwise an exponential
    backoff (``backoff_factor * 2**attempt``) is used.

    Args:
        attempt: Zero-based index of the attempt that just failed.
        backoff_factor: Base multiplier for exponential backoff.
        retry_after: Seconds requested by the server, if any.

    Returns:
        The number of seconds to wait.
    """
    if retry_after is not None:
        return retry_after
    return backoff_factor * float(2**attempt)


def is_retryable(response: httpx.Response) -> bool:
    """Return ``True`` if the response status warrants a retry (429 or 5xx)."""
    return response.status_code == 429 or 500 <= response.status_code < 600


def _extract_message(body: Any, fallback: str) -> str:
    """Pull a human-readable error message out of a decoded error body."""
    if isinstance(body, dict):
        for key in ("message", "error", "errmsg", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
    return fallback


def handle_response(response: httpx.Response) -> Any:
    """Validate an HTTP response and return its decoded JSON payload.

    Args:
        response: The HTTP response to inspect.

    Returns:
        The decoded JSON payload.

    Raises:
        DeBankRateLimitError: On HTTP 429.
        DeBankAPIError: On any other non-2xx status.
    """
    status = response.status_code
    if 200 <= status < 300:
        return response.json()

    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text or None

    if status == 429:
        raise DeBankRateLimitError(
            status,
            _extract_message(body, "Rate limit exceeded (HTTP 429)."),
            response_body=body,
            retry_after=parse_retry_after(response),
        )
    raise DeBankAPIError(
        status,
        _extract_message(body, response.reason_phrase or "DeBank API error"),
        response_body=body,
    )
