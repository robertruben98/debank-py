"""Synchronous client for the DeBank Cloud Pro API."""

from __future__ import annotations

import time
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


class DeBankClient:
    """A synchronous client for the DeBank Cloud Pro API.

    DeBank Cloud is a **paid** service: every request must carry a DeBank Cloud
    ``AccessKey`` (obtained from https://cloud.debank.com), sent in the
    ``AccessKey`` request header by default. All wallet queries take the wallet
    address as the ``id`` argument.

    The client wraps an :class:`httpx.Client`, attaches the access-key header,
    and retries on HTTP 429 (rate limit) and 5xx responses with exponential
    backoff, honoring any ``Retry-After`` header.

    Use it as a context manager so the connection pool is closed::

        with DeBankClient(access_key="my-key") as client:
            total = client.get_user_total_balance(id="0x...")

    Args:
        access_key: Your DeBank Cloud Pro AccessKey. Required.
        base_url: Base URL of the API. Defaults to
            ``https://pro-openapi.debank.com``.
        access_key_header: Name of the header the key is sent under. Defaults to
            ``AccessKey``.
        timeout: Per-request timeout in seconds.
        max_retries: Maximum retries for rate-limited / server-error responses.
        backoff_factor: Base multiplier for exponential backoff, in seconds.
        client: An existing :class:`httpx.Client` to reuse. When supplied, the
            caller owns its lifecycle and it is not closed by this client.
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
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.access_key = access_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        # Built once and applied on every request so the AccessKey is sent
        # whether the transport was created here or supplied via ``client=``.
        self._headers = build_headers(access_key, access_key_header)
        self._owns_client = client is None
        self._client = client or httpx.Client(base_url=self.base_url, timeout=timeout)

    def __enter__(self) -> DeBankClient:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client (only if this instance created it)."""
        if self._owns_client:
            self._client.close()

    def _request(self, method: str, path: str, *, params: Mapping[str, Any]) -> Any:
        """Perform a request with retry/backoff and return the decoded payload."""
        cleaned = clean_params(params)
        attempt = 0
        while True:
            response = self._client.request(method, path, params=cleaned, headers=self._headers)
            if is_retryable(response) and attempt < self.max_retries:
                delay = backoff_delay(attempt, self.backoff_factor, parse_retry_after(response))
                if delay > 0:
                    time.sleep(delay)
                attempt += 1
                continue
            return handle_response(response)

    # -- User -------------------------------------------------------------

    def get_user_total_balance(self, *, id: str) -> TotalBalance:
        """Get a wallet's total USD net worth across all chains.

        ``GET /v1/user/total_balance``

        Args:
            id: The wallet address to query.

        Returns:
            A :class:`~debank.models.TotalBalance` with the total and a per-chain
            breakdown.
        """
        payload = self._request("GET", "/v1/user/total_balance", params={"id": id})
        return TotalBalance.model_validate(payload)

    def get_user_chain_balance(self, *, id: str, chain_id: str) -> ChainBalance:
        """Get a wallet's USD balance on a single chain.

        ``GET /v1/user/chain_balance``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier (e.g. ``eth``).

        Returns:
            A :class:`~debank.models.ChainBalance`.
        """
        payload = self._request(
            "GET", "/v1/user/chain_balance", params={"id": id, "chain_id": chain_id}
        )
        return ChainBalance.model_validate(payload)

    def get_user_used_chain_list(self, *, id: str) -> list[UsedChain]:
        """List the chains a wallet has interacted with.

        ``GET /v1/user/used_chain_list``

        Args:
            id: The wallet address to query.

        Returns:
            A list of :class:`~debank.models.UsedChain`.
        """
        payload = self._request("GET", "/v1/user/used_chain_list", params={"id": id})
        return [UsedChain.model_validate(item) for item in payload]

    def get_user_token_list(
        self, *, id: str, chain_id: str, is_all: Optional[bool] = None
    ) -> list[Token]:
        """List a wallet's token balances on a single chain.

        ``GET /v1/user/token_list``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.
            is_all: When ``True``, include all tokens (not just verified ones).

        Returns:
            A list of :class:`~debank.models.Token` with balances populated.
        """
        payload = self._request(
            "GET",
            "/v1/user/token_list",
            params={"id": id, "chain_id": chain_id, "is_all": is_all},
        )
        return [Token.model_validate(item) for item in payload]

    def get_user_all_token_list(
        self,
        *,
        id: str,
        is_all: Optional[bool] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> list[Token]:
        """List a wallet's token balances across all chains.

        ``GET /v1/user/all_token_list``

        Args:
            id: The wallet address to query.
            is_all: When ``True``, include all tokens (not just verified ones).
            chain_ids: Optional list of chain ids to restrict the query to (sent
                comma-separated).

        Returns:
            A list of :class:`~debank.models.Token` with balances populated.
        """
        payload = self._request(
            "GET",
            "/v1/user/all_token_list",
            params={"id": id, "is_all": is_all, "chain_ids": chain_ids},
        )
        return [Token.model_validate(item) for item in payload]

    def get_user_token(self, *, id: str, chain_id: str, token_id: str) -> Token:
        """Get a wallet's balance of a specific token.

        ``GET /v1/user/token``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.
            token_id: Token identifier (contract address or native marker).

        Returns:
            A :class:`~debank.models.Token`.
        """
        payload = self._request(
            "GET",
            "/v1/user/token",
            params={"id": id, "chain_id": chain_id, "token_id": token_id},
        )
        return Token.model_validate(payload)

    def get_user_nft_list(
        self, *, id: str, chain_id: str, is_all: Optional[bool] = None
    ) -> list[Any]:
        """List a wallet's NFTs on a single chain.

        ``GET /v1/user/nft_list``

        NFT payloads vary widely by collection, so each item is returned as a raw
        ``dict`` rather than a fixed model.

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.
            is_all: When ``True``, include all NFTs.

        Returns:
            A list of raw NFT dictionaries.
        """
        payload = self._request(
            "GET",
            "/v1/user/nft_list",
            params={"id": id, "chain_id": chain_id, "is_all": is_all},
        )
        return list(payload)

    def get_user_all_nft_list(
        self,
        *,
        id: str,
        is_all: Optional[bool] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> list[Any]:
        """List a wallet's NFTs across all chains.

        ``GET /v1/user/all_nft_list``

        Args:
            id: The wallet address to query.
            is_all: When ``True``, include all NFTs.
            chain_ids: Optional list of chain ids (sent comma-separated).

        Returns:
            A list of raw NFT dictionaries.
        """
        payload = self._request(
            "GET",
            "/v1/user/all_nft_list",
            params={"id": id, "is_all": is_all, "chain_ids": chain_ids},
        )
        return list(payload)

    def get_user_complex_protocol_list(self, *, id: str, chain_id: str) -> list[Protocol]:
        """List a wallet's DeFi positions on a chain with full portfolio detail.

        ``GET /v1/user/complex_protocol_list``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.

        Returns:
            A list of :class:`~debank.models.Protocol` with ``portfolio_item_list``.
        """
        payload = self._request(
            "GET",
            "/v1/user/complex_protocol_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [Protocol.model_validate(item) for item in payload]

    def get_user_all_complex_protocol_list(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[Protocol]:
        """List a wallet's DeFi positions across all chains with full detail.

        ``GET /v1/user/all_complex_protocol_list``

        Args:
            id: The wallet address to query.
            chain_ids: Optional list of chain ids (sent comma-separated).

        Returns:
            A list of :class:`~debank.models.Protocol` with ``portfolio_item_list``.
        """
        payload = self._request(
            "GET",
            "/v1/user/all_complex_protocol_list",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [Protocol.model_validate(item) for item in payload]

    def get_user_simple_protocol_list(self, *, id: str, chain_id: str) -> list[Protocol]:
        """List a wallet's DeFi positions on a chain (aggregated USD values only).

        ``GET /v1/user/simple_protocol_list``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.

        Returns:
            A list of :class:`~debank.models.Protocol` with net/asset/debt values.
        """
        payload = self._request(
            "GET",
            "/v1/user/simple_protocol_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [Protocol.model_validate(item) for item in payload]

    def get_user_all_simple_protocol_list(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[Protocol]:
        """List a wallet's DeFi positions across all chains (aggregated values).

        ``GET /v1/user/all_simple_protocol_list``

        Args:
            id: The wallet address to query.
            chain_ids: Optional list of chain ids (sent comma-separated).

        Returns:
            A list of :class:`~debank.models.Protocol` with net/asset/debt values.
        """
        payload = self._request(
            "GET",
            "/v1/user/all_simple_protocol_list",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [Protocol.model_validate(item) for item in payload]

    def get_user_protocol(self, *, id: str, protocol_id: str) -> Protocol:
        """Get a wallet's position in a single protocol.

        ``GET /v1/user/protocol``

        Args:
            id: The wallet address to query.
            protocol_id: DeBank protocol identifier.

        Returns:
            A :class:`~debank.models.Protocol`.
        """
        payload = self._request(
            "GET", "/v1/user/protocol", params={"id": id, "protocol_id": protocol_id}
        )
        return Protocol.model_validate(payload)

    def get_user_history_list(
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

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.
            token_id: Restrict history to a single token, if given.
            start_time: Page backwards from this Unix timestamp (exclusive).
            page_count: Number of transactions to return (max per the API).

        Returns:
            A :class:`~debank.models.HistoryList`.
        """
        payload = self._request(
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

    def get_user_all_history_list(
        self,
        *,
        id: str,
        start_time: Optional[int] = None,
        page_count: Optional[int] = None,
        chain_ids: Optional[list[str]] = None,
    ) -> HistoryList:
        """Get a wallet's transaction history across all chains.

        ``GET /v1/user/all_history_list``

        Args:
            id: The wallet address to query.
            start_time: Page backwards from this Unix timestamp (exclusive).
            page_count: Number of transactions to return.
            chain_ids: Optional list of chain ids (sent comma-separated).

        Returns:
            A :class:`~debank.models.HistoryList`.
        """
        payload = self._request(
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

    def get_user_token_authorized_list(self, *, id: str, chain_id: str) -> list[TokenAuthorization]:
        """List a wallet's outstanding token approvals on a chain.

        ``GET /v1/user/token_authorized_list``

        Args:
            id: The wallet address to query.
            chain_id: DeBank chain identifier.

        Returns:
            A list of :class:`~debank.models.TokenAuthorization`.
        """
        payload = self._request(
            "GET",
            "/v1/user/token_authorized_list",
            params={"id": id, "chain_id": chain_id},
        )
        return [TokenAuthorization.model_validate(item) for item in payload]

    def get_user_total_net_curve(
        self, *, id: str, chain_ids: Optional[list[str]] = None
    ) -> list[NetCurvePoint]:
        """Get a wallet's 24-hour net-worth curve across chains.

        ``GET /v1/user/total_net_curve``

        Args:
            id: The wallet address to query.
            chain_ids: Optional list of chain ids (sent comma-separated).

        Returns:
            A list of :class:`~debank.models.NetCurvePoint`.
        """
        payload = self._request(
            "GET",
            "/v1/user/total_net_curve",
            params={"id": id, "chain_ids": chain_ids},
        )
        return [NetCurvePoint.model_validate(item) for item in payload]

    # -- Chain ------------------------------------------------------------

    def get_chain_list(self) -> list[Chain]:
        """List every chain supported by DeBank.

        ``GET /v1/chain/list``

        Returns:
            A list of :class:`~debank.models.Chain`.
        """
        payload = self._request("GET", "/v1/chain/list", params={})
        return [Chain.model_validate(item) for item in payload]

    def get_chain(self, *, id: str) -> Chain:
        """Get information about a single chain.

        ``GET /v1/chain``

        Args:
            id: DeBank chain identifier (e.g. ``eth``).

        Returns:
            A :class:`~debank.models.Chain`.
        """
        payload = self._request("GET", "/v1/chain", params={"id": id})
        return Chain.model_validate(payload)

    # -- Token ------------------------------------------------------------

    def get_token(self, *, chain_id: str, id: str) -> Token:
        """Get information about a single token.

        ``GET /v1/token``

        Args:
            chain_id: DeBank chain identifier.
            id: Token identifier (contract address or native marker).

        Returns:
            A :class:`~debank.models.Token`.
        """
        payload = self._request("GET", "/v1/token", params={"chain_id": chain_id, "id": id})
        return Token.model_validate(payload)

    def get_token_list_by_ids(self, *, chain_id: str, ids: list[str]) -> list[Token]:
        """Get information about several tokens at once.

        ``GET /v1/token/list_by_ids``

        Args:
            chain_id: DeBank chain identifier.
            ids: Token identifiers (sent comma-separated).

        Returns:
            A list of :class:`~debank.models.Token`.
        """
        payload = self._request(
            "GET", "/v1/token/list_by_ids", params={"chain_id": chain_id, "ids": ids}
        )
        return [Token.model_validate(item) for item in payload]

    def get_token_history_price(self, *, id: str, chain_id: str, date_at: str) -> TokenHistoryPrice:
        """Get a token's USD price on a past date.

        ``GET /v1/token/history_price``

        Args:
            id: Token identifier.
            chain_id: DeBank chain identifier.
            date_at: Date in ``YYYY-MM-DD`` form.

        Returns:
            A :class:`~debank.models.TokenHistoryPrice`.
        """
        payload = self._request(
            "GET",
            "/v1/token/history_price",
            params={"id": id, "chain_id": chain_id, "date_at": date_at},
        )
        return TokenHistoryPrice.model_validate(payload)
