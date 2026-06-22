"""debank-py: a typed Python client for the DeBank Cloud Pro API.

DeBank Cloud exposes multi-chain wallet portfolio data — total net worth, token
balances, DeFi protocol positions, NFTs and transaction history — across every
chain DeBank tracks. This package provides synchronous (:class:`DeBankClient`)
and asynchronous (:class:`AsyncDeBankClient`) clients built on ``httpx`` and
``pydantic`` v2.

DeBank Cloud is a **paid** service: every request must carry a DeBank Cloud
``AccessKey`` (from https://cloud.debank.com), sent in the ``AccessKey`` request
header. All wallet queries take the wallet address as the ``id`` argument.
"""

from .async_client import AsyncDeBankClient
from .client import DeBankClient
from .exceptions import DeBankAPIError, DeBankError, DeBankRateLimitError
from .models import (
    Chain,
    ChainBalance,
    HistoryList,
    NetCurvePoint,
    PortfolioItem,
    Protocol,
    Token,
    TokenAuthorization,
    TokenHistoryPrice,
    TokenSpender,
    TotalBalance,
    TotalBalanceChain,
    UsedChain,
)

__version__ = "0.1.0"

__all__ = [
    "AsyncDeBankClient",
    "Chain",
    "ChainBalance",
    "DeBankAPIError",
    "DeBankClient",
    "DeBankError",
    "DeBankRateLimitError",
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
    "__version__",
]
