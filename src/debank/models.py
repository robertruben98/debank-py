"""Pydantic models for DeBank Cloud Pro API responses.

DeBank payloads are large, deeply nested and frequently extended with new
fields. Rather than model every field exhaustively, these models declare the
documented, commonly-used fields and set ``extra="allow"`` so that any
additional fields the API returns are preserved on the parsed object (accessible
via attribute access or ``model_extra``). This keeps the client forward
compatible with API changes without requiring a library upgrade.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class _DeBankModel(BaseModel):
    """Base model that tolerates and preserves undocumented extra fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Chain(_DeBankModel):
    """A blockchain supported by DeBank (``/v1/chain`` and ``/v1/chain/list``)."""

    id: str = Field(description="DeBank chain identifier, e.g. ``eth``, ``bsc``.")
    community_id: Optional[int] = Field(default=None, description="Numeric community/EVM chain id.")
    name: Optional[str] = Field(default=None, description="Human-readable chain name.")
    logo_url: Optional[str] = Field(default=None, description="URL of the chain logo.")
    native_token_id: Optional[str] = Field(
        default=None, description="Token id of the chain's native token."
    )
    wrapped_token_id: Optional[str] = Field(
        default=None, description="Token id of the wrapped native token."
    )
    is_support_pre_exec: Optional[bool] = Field(
        default=None, description="Whether the chain supports transaction pre-execution."
    )


class UsedChain(_DeBankModel):
    """A chain a wallet has interacted with (``/v1/user/used_chain_list``)."""

    id: str = Field(description="DeBank chain identifier.")
    community_id: Optional[int] = Field(default=None, description="Numeric community/EVM chain id.")
    name: Optional[str] = Field(default=None, description="Human-readable chain name.")
    logo_url: Optional[str] = Field(default=None, description="URL of the chain logo.")
    native_token_id: Optional[str] = Field(default=None, description="Native token id.")
    wrapped_token_id: Optional[str] = Field(default=None, description="Wrapped native token id.")
    born_at: Optional[int] = Field(
        default=None, description="Unix timestamp of the wallet's first activity on the chain."
    )


class ChainBalance(_DeBankModel):
    """A wallet's USD balance on a single chain (``/v1/user/chain_balance``)."""

    usd_value: float = Field(description="Total USD value held on the chain.")


class TotalBalanceChain(_DeBankModel):
    """Per-chain net worth inside a total-balance response."""

    id: Optional[str] = Field(default=None, description="DeBank chain identifier.")
    community_id: Optional[int] = Field(default=None, description="Numeric community/EVM chain id.")
    name: Optional[str] = Field(default=None, description="Human-readable chain name.")
    logo_url: Optional[str] = Field(default=None, description="URL of the chain logo.")
    usd_value: float = Field(description="USD value held on the chain.")


class TotalBalance(_DeBankModel):
    """A wallet's aggregated net worth (``/v1/user/total_balance``)."""

    total_usd_value: float = Field(description="Total USD net worth across all chains.")
    chain_list: list[TotalBalanceChain] = Field(
        default_factory=list, description="Per-chain breakdown of the net worth."
    )


class Token(_DeBankModel):
    """A token, used by the token and user-token endpoints."""

    id: str = Field(description="Token identifier (contract address or native marker).")
    chain: Optional[str] = Field(default=None, description="Chain the token belongs to.")
    name: Optional[str] = Field(default=None, description="Token name.")
    symbol: Optional[str] = Field(default=None, description="Token symbol.")
    display_symbol: Optional[str] = Field(default=None, description="Disambiguated display symbol.")
    optimized_symbol: Optional[str] = Field(default=None, description="Optimized display symbol.")
    decimals: Optional[int] = Field(default=None, description="Number of token decimals.")
    logo_url: Optional[str] = Field(default=None, description="URL of the token logo.")
    protocol_id: Optional[str] = Field(default=None, description="Owning protocol id, if any.")
    is_core: Optional[bool] = Field(default=None, description="Whether DeBank treats it as core.")
    price: Optional[float] = Field(default=None, description="USD price of the token.")
    time_at: Optional[int] = Field(
        default=None, description="Token creation Unix timestamp (seconds)."
    )
    amount: Optional[float] = Field(
        default=None, description="Decimal-adjusted wallet balance (user endpoints only)."
    )
    raw_amount: Optional[int] = Field(
        default=None,
        description=(
            "Wallet balance in the token's smallest unit (user endpoints only). "
            "Typed as int to preserve exact values beyond float64 precision."
        ),
    )


class TokenHistoryPrice(_DeBankModel):
    """Historical token price (``/v1/token/history_price``)."""

    price: float = Field(description="USD price at the requested date.")


class PortfolioItem(_DeBankModel):
    """A single position inside a protocol portfolio."""

    name: Optional[str] = Field(default=None, description="Position category, e.g. ``Lending``.")
    detail_types: list[str] = Field(
        default_factory=list, description="Detail type tags describing the position."
    )
    detail: Optional[dict[str, Any]] = Field(default=None, description="Position detail payload.")
    stats: Optional[dict[str, Any]] = Field(
        default=None, description="Aggregated USD stats for the item."
    )


class Protocol(_DeBankModel):
    """A DeFi protocol position for a wallet.

    Covers both the *complex* protocol responses (which carry
    ``portfolio_item_list``) and the *simple* ones (which carry the aggregated
    ``net_usd_value`` / ``asset_usd_value`` / ``debt_usd_value`` fields).
    Undocumented fields are preserved via ``extra="allow"``.
    """

    id: str = Field(description="Protocol identifier.")
    chain: Optional[str] = Field(default=None, description="Chain the protocol is on.")
    name: Optional[str] = Field(default=None, description="Protocol name.")
    logo_url: Optional[str] = Field(default=None, description="URL of the protocol logo.")
    site_url: Optional[str] = Field(default=None, description="Protocol website URL.")
    has_supported_portfolio: Optional[bool] = Field(
        default=None, description="Whether DeBank parses this protocol's portfolio."
    )
    net_usd_value: Optional[float] = Field(
        default=None, description="Net USD value (simple protocol list)."
    )
    asset_usd_value: Optional[float] = Field(
        default=None, description="Asset USD value (simple protocol list)."
    )
    debt_usd_value: Optional[float] = Field(
        default=None, description="Debt USD value (simple protocol list)."
    )
    portfolio_item_list: list[PortfolioItem] = Field(
        default_factory=list, description="Positions within the protocol (complex list)."
    )


class HistoryList(_DeBankModel):
    """A wallet's transaction history (``/v1/user/history_list``).

    The history endpoints return the transactions in ``history_list`` plus a set
    of lookup dictionaries (token/project/cex/category) used to decode them.
    """

    history_list: list[dict[str, Any]] = Field(
        default_factory=list, description="Decoded transactions, newest first."
    )
    cate_dict: dict[str, Any] = Field(
        default_factory=dict, description="Category id -> metadata lookup."
    )
    project_dict: dict[str, Any] = Field(
        default_factory=dict, description="Project id -> metadata lookup."
    )
    token_dict: dict[str, Any] = Field(
        default_factory=dict, description="Token id -> metadata lookup."
    )
    cex_dict: dict[str, Any] = Field(default_factory=dict, description="CEX id -> metadata lookup.")


class TokenSpender(_DeBankModel):
    """A spender approved against a token (``/v1/user/token_authorized_list``)."""

    id: Optional[str] = Field(default=None, description="Spender contract address.")
    value: Optional[float] = Field(
        default=None, description="Approved USD exposure for the spender."
    )
    exposure_usd: Optional[float] = Field(default=None, description="USD exposure for the spender.")
    protocol: Optional[dict[str, Any]] = Field(
        default=None, description="Spender protocol metadata, if known."
    )


class TokenAuthorization(_DeBankModel):
    """A token approval summary (``/v1/user/token_authorized_list``)."""

    id: str = Field(description="Token id the approvals are against.")
    name: Optional[str] = Field(default=None, description="Token name.")
    symbol: Optional[str] = Field(default=None, description="Token symbol.")
    chain: Optional[str] = Field(default=None, description="Chain the token is on.")
    sum_exposure_usd: Optional[float] = Field(
        default=None, description="Total USD exposure across all spenders."
    )
    spenders: list[TokenSpender] = Field(
        default_factory=list, description="Per-spender approval details."
    )


class NetCurvePoint(_DeBankModel):
    """A single point on a wallet's net-worth curve."""

    timestamp: int = Field(description="Unix timestamp of the sample.")
    usd_value: float = Field(description="USD net worth at the timestamp.")


__all__ = [
    "Chain",
    "ChainBalance",
    "HistoryList",
    "NetCurvePoint",
    "PortfolioItem",
    "Protocol",
    "Token",
    "TokenAuthorization",
    "TokenHistoryPrice",
    "TokenSpender",
    "TotalBalance",
    "TotalBalanceChain",
    "UsedChain",
]
