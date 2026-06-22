"""Exception hierarchy raised by the DeBank client.

All errors raised by this library derive from :class:`DeBankError`, so callers
can catch every library-originated failure with a single ``except`` clause.
"""

from __future__ import annotations

from typing import Any, Optional


class DeBankError(Exception):
    """Base class for every error raised by ``debank-py``."""


class DeBankAPIError(DeBankError):
    """Raised when the DeBank Cloud API returns an unsuccessful HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the API.
        message: A human-readable error message, extracted from the response
            body when possible.
        response_body: The decoded JSON body of the error response, or the raw
            text when the body is not valid JSON.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        response_body: Optional[Any] = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"[{status_code}] {message}")


class DeBankRateLimitError(DeBankAPIError):
    """Raised when the DeBank Cloud API responds with HTTP 429 (rate limited).

    The Pro plan allows up to 100 requests per second; exceeding that returns
    ``429``. The client retries such responses with backoff before giving up
    and raising this error.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` response header when present.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        response_body: Optional[Any] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(status_code, message, response_body=response_body)
        self.retry_after = retry_after
