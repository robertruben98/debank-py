"""Asynchronous client for the DeBank Cloud Pro API."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Optional

import httpx

from ._base import (
    DEFAULT_ACCESS_KEY_HEADER,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    backoff_delay,
    build_headers,
    clean_params,
    handle_response,
    is_retryable,
    parse_retry_after,
)
from .models import (
    Chain,
    ChainBalance,
    HistoryList,
    NetCurvePoint,
    Protocol,
    Token,
    TokenAuthorization,
    TokenHistoryPrice,
    TotalBalance,
    UsedChain,
)


class AsyncDeBankClient:
    """An asyncio client for the DeBank Cloud Pro API.

    This is the ``async``/``await`` counterpart of :class:`~debank.DeBankClient`
    and exposes the same methods and behaviour (access-key header, retry on
    429/5xx with backoff) backed by an :class:`httpx.AsyncClient`.

    DeBank Cloud is a **paid** service: every request must carry a DeBank Cloud
    ``AccessKey``. All wallet queries take the wallet address as ``id``.

    Use it as an async context manager so the connection pool is closed::

        async with AsyncDeBankClient(access_key="my-key") as client:
            total = await client.get_user_total_balance(id="0x...")

    Args:
        access_key: Your DeBank Cloud Pro AccessKey. Required.
        base_url: Base URL of the API. Defaults to
            ``https://pro-openapi.debank.com``.
        access_key_header: Name of the header the key is sent under. Defaults to
            ``AccessKey``.
        timeout: Per-request timeout in seconds.
        max_retries: Maximum retries for rate-limited / server-error responses.
        backoff_factor: Base multiplier for exponential backoff, in seconds.
        client: An existing :class:`httpx.AsyncClient` to reuse. When supplied,
            the caller owns its lifecycle and it is not closed by this client.
    """

    def __init__(
        self,
        access_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        access_key_header: str = DEFAULT_ACCESS_KEY_HEADER,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.access_key = access_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        # Built once and applied on every request so the AccessKey is sent
        # whether the transport was created here or supplied via ``client=``.
        self._headers = build_headers(access_key, access_key_header)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def __aenter__(self) -> AsyncDeBankClient:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client (only if this instance created it)."""
        if self._owns_client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, *, params: Mapping[str, Any]) -> Any:
        """Perform a request with retry/backoff and return the decoded payload."""
        cleaned = clean_params(params)
        attempt = 0
        while True:
            response = await self._client.request(
                method, path, params=cleaned, headers=self._headers
            )
            if is_retryable(response) and attempt < self.max_retries:
                delay = backoff_delay(attempt, self.backoff_factor, parse_retry_after(response))
                if delay > 0:
                    await asyncio.sleep(delay)
                attempt += 1
                continue
            return handle_response(response)

    # -- User -------------------------------------------------------------

    async def get_user_total_balance(self, *, id: str) -> TotalBalance:
        """Get a wallet's total USD net worth across all chains.

        ``GET /v1/user/total_balance``
        """
        payload = await self._request("GET", "/v1/user/total_balance", params={"id": id})
        return TotalBalance.model_validate(payload)

    async def get_user_chain_balance(self, *, id: str, chain_id: str) -> ChainBalance:
        """Get a wallet's USD balance on a single chain.

        ``GET /v1/user/chain_balance``
        """
        payload = await self._request(
            "GET", "/v1/user/chain_balance", params={"id": id, "chain_id": chain_id}
        )
        return ChainBalance.model_validate(payload)

    async def get_user_used_chain_list(self, *, id: str) -> list[UsedChain]:
        """List the chains a wallet has interacted with.

        ``GET /v1/user/used_chain_list``
        """
        payload = await self._request("GET", "/v1/user/used_chain_list", params={"id": id})
        return [UsedChain.model_validate(item) for item in payload]

    async def get_user_token_list(
        self, *, id: str, chain_id: str, is_all: Optional[bool] = None
    ) -> list[Token]:
        """List a wallet's token balances on a single chain.

        ``GET /v1/user/token_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/token_list",
            params={"id": id, "chain_id": chain_id, "is_all": is_all},
        )
        return [Token.model_validate(item) for item in payload]

    async def get_user_all_token_list(
        self,
        *,
        id: str,
        is_all: Optional[bool] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> list[Token]:
        """List a wallet's token balances across all chains.

        ``GET /v1/user/all_token_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/all_token_list",
            params={"id": id, "is_all": is_all, "chain_ids": chain_ids},
        )
        return [Token.model_validate(item) for item in payload]

    async def get_user_token(self, *, id: str, chain_id: str, token_id: str) -> Token:
        """Get a wallet's balance of a specific token.

        ``GET /v1/user/token``
        """
        payload = await self._request(
            "GET",
            "/v1/user/token",
            params={"id": id, "chain_id": chain_id, "token_id": token_id},
        )
        return Token.model_validate(payload)

    async def get_user_nft_list(
        self, *, id: str, chain_id: str, is_all: Optional[bool] = None
    ) -> list[Any]:
        """List a wallet's NFTs on a single chain.

        ``GET /v1/user/nft_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/nft_list",
            params={"id": id, "chain_id": chain_id, "is_all": is_all},
        )
        return list(payload)

    async def get_user_all_nft_list(
        self,
        *,
        id: str,
        is_all: Optional[bool] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> list[Any]:
        """List a wallet's NFTs across all chains.

        ``GET /v1/user/all_nft_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/all_nft_list",
            params={"id": id, "is_all": is_all, "chain_ids": chain_ids},
        )
        return list(payload)

    async def get_user_complex_protocol_list(self, *, id: str, chain_id: str) -> list[Protocol]:
        """List a wallet's DeFi positions on a chain with full portfolio detail.

        ``GET /v1/user/complex_protocol_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/complex_protocol_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [Protocol.model_validate(item) for item in payload]

    async def get_user_all_complex_protocol_list(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[Protocol]:
        """List a wallet's DeFi positions across all chains with full detail.

        ``GET /v1/user/all_complex_protocol_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/all_complex_protocol_list",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [Protocol.model_validate(item) for item in payload]

    async def get_user_simple_protocol_list(self, *, id: str, chain_id: str) -> list[Protocol]:
        """List a wallet's DeFi positions on a chain (aggregated USD values only).

        ``GET /v1/user/simple_protocol_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/simple_protocol_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [Protocol.model_validate(item) for item in payload]

    async def get_user_all_simple_protocol_list(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[Protocol]:
        """List a wallet's DeFi positions across all chains (aggregated values).

        ``GET /v1/user/all_simple_protocol_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/all_simple_protocol_list",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [Protocol.model_validate(item) for item in payload]

    async def get_user_protocol(self, *, id: str, protocol_id: str) -> Protocol:
        """Get a wallet's position in a single protocol.

        ``GET /v1/user/protocol``
        """
        payload = await self._request(
            "GET", "/v1/user/protocol", params={"id": id, "protocol_id": protocol_id}
        )
        return Protocol.model_validate(payload)

    async def get_user_history_list(
        self,
        *,
        id: str,
        chain_id: str,
        token_id: Optional[str] = None,
        start_time: Optional[int] = None,
        page_count: Optional[int] = None,
    ) -> HistoryList:
        """Get a wallet's transaction history on a single chain.

        ``GET /v1/user/history_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/history_list",
            params={
                "id": id,
                "chain_id": chain_id,
                "token_id": token_id,
                "start_time": start_time,
                "page_count": page_count,
            },
        )
        return HistoryList.model_validate(payload)

    async def get_user_all_history_list(
        self,
        *,
        id: str,
        start_time: Optional[int] = None,
        page_count: Optional[int] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> HistoryList:
        """Get a wallet's transaction history across all chains.

        ``GET /v1/user/all_history_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/all_history_list",
            params={
                "id": id,
                "start_time": start_time,
                "page_count": page_count,
                "chain_ids": chain_ids,
            },
        )
        return HistoryList.model_validate(payload)

    async def get_user_token_authorized_list(
        self, *, id: str, chain_id: str
    ) -> list[TokenAuthorization]:
        """List a wallet's outstanding token approvals on a chain.

        ``GET /v1/user/token_authorized_list``
        """
        payload = await self._request(
            "GET",
            "/v1/user/token_authorized_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [TokenAuthorization.model_validate(item) for item in payload]

    async def get_user_total_net_curve(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[NetCurvePoint]:
        """Get a wallet's 24-hour net-worth curve across chains.

        ``GET /v1/user/total_net_curve``
        """
        payload = await self._request(
            "GET",
            "/v1/user/total_net_curve",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [NetCurvePoint.model_validate(item) for item in payload]

    # -- Chain ------------------------------------------------------------

    async def get_chain_list(self) -> list[Chain]:
        """List every chain supported by DeBank.

        ``GET /v1/chain/list``
        """
        payload = await self._request("GET", "/v1/chain/list", params={})
        return [Chain.model_validate(item) for item in payload]

    async def get_chain(self, *, id: str) -> Chain:
        """Get information about a single chain.

        ``GET /v1/chain``
        """
        payload = await self._request("GET", "/v1/chain", params={"id": id})
        return Chain.model_validate(payload)

    # -- Token ------------------------------------------------------------

    async def get_token(self, *, chain_id: str, id: str) -> Token:
        """Get information about a single token.

        ``GET /v1/token``
        """
        payload = await self._request("GET", "/v1/token", params={"chain_id": chain_id, "id": id})
        return Token.model_validate(payload)

    async def get_token_list_by_ids(self, *, chain_id: str, ids: list[str]) -> list[Token]:
        """Get information about several tokens at once.

        ``GET /v1/token/list_by_ids``
        """
        payload = await self._request(
            "GET", "/v1/token/list_by_ids", params={"chain_id": chain_id, "ids": ids}
        )
        return [Token.model_validate(item) for item in payload]

    async def get_token_history_price(
        self, *, id: str, chain_id: str, date_at: str
    ) -> TokenHistoryPrice:
        """Get a token's USD price on a past date.

        ``GET /v1/token/history_price``
        """
        payload = await self._request(
            "GET",
            "/v1/token/history_price",
            params={"id": id, "chain_id": chain_id, "date_at": date_at},
        )
        return TokenHistoryPrice.model_validate(payload)
