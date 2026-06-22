# debank-py

[![CI](https://github.com/robertruben98/debank-py/actions/workflows/ci.yml/badge.svg)](https://github.com/robertruben98/debank-py/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/debank-py.svg)](https://pypi.org/project/debank-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/debank-py.svg)](https://pypi.org/project/debank-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/robertruben98/debank-py/blob/main/LICENSE)

A typed Python client for the [DeBank Cloud Pro API](https://docs.cloud.debank.com) —
multi-chain wallet portfolio, token balances, DeFi protocol positions, NFTs and
transaction history across every chain DeBank tracks.

Synchronous (`DeBankClient`) and asynchronous (`AsyncDeBankClient`) clients built
on [`httpx`](https://www.python-httpx.org/) and [`pydantic`](https://docs.pydantic.dev/) v2,
with full type hints (`py.typed`).

## Requirements

The DeBank Cloud Pro API is a **paid** service. You need a DeBank Cloud
**AccessKey**, which is passed on every request via the `AccessKey` header.
Get one from the [DeBank Cloud console](https://cloud.debank.com). Requests
without a valid key are rejected by the API.

## Installation

```bash
pip install debank-py
```

Requires Python 3.9+.

## Quickstart

```python
from debank import DeBankClient

with DeBankClient(access_key="your-debank-access-key") as client:
    # Total USD net worth of a wallet across all chains.
    total = client.get_user_total_balance(id="0x5853 ... eb1f")
    print(total.total_usd_value)

    # Every token the wallet holds, on every chain.
    for token in client.get_user_all_token_list(id="0x5853 ... eb1f"):
        print(token.chain, token.symbol, token.amount)

    # Open DeFi positions (complex protocol portfolios).
    protocols = client.get_user_all_complex_protocol_list(id="0x5853 ... eb1f")

    # Recent transaction history.
    history = client.get_user_history_list(id="0x5853 ... eb1f", chain_id="eth")
```

### Async

```python
import asyncio
from debank import AsyncDeBankClient

async def main():
    async with AsyncDeBankClient(access_key="your-debank-access-key") as client:
        total = await client.get_user_total_balance(id="0x5853 ... eb1f")
        print(total.total_usd_value)

asyncio.run(main())
```

## Endpoints

The client mirrors the DeBank Cloud Pro reference. Every wallet query takes the
wallet address as the `id` argument.

### User

| Method | Endpoint |
| --- | --- |
| `get_user_total_balance(id)` | `GET /v1/user/total_balance` |
| `get_user_chain_balance(id, chain_id)` | `GET /v1/user/chain_balance` |
| `get_user_used_chain_list(id)` | `GET /v1/user/used_chain_list` |
| `get_user_token_list(id, chain_id, is_all=...)` | `GET /v1/user/token_list` |
| `get_user_all_token_list(id, is_all=..., chain_ids=...)` | `GET /v1/user/all_token_list` |
| `get_user_token(id, chain_id, token_id)` | `GET /v1/user/token` |
| `get_user_nft_list(id, chain_id, is_all=...)` | `GET /v1/user/nft_list` |
| `get_user_all_nft_list(id, is_all=..., chain_ids=...)` | `GET /v1/user/all_nft_list` |
| `get_user_complex_protocol_list(id, chain_id)` | `GET /v1/user/complex_protocol_list` |
| `get_user_all_complex_protocol_list(id, chain_ids=...)` | `GET /v1/user/all_complex_protocol_list` |
| `get_user_simple_protocol_list(id, chain_id)` | `GET /v1/user/simple_protocol_list` |
| `get_user_all_simple_protocol_list(id, chain_ids=...)` | `GET /v1/user/all_simple_protocol_list` |
| `get_user_protocol(id, protocol_id)` | `GET /v1/user/protocol` |
| `get_user_history_list(id, chain_id, ...)` | `GET /v1/user/history_list` |
| `get_user_all_history_list(id, ...)` | `GET /v1/user/all_history_list` |
| `get_user_token_authorized_list(id, chain_id)` | `GET /v1/user/token_authorized_list` |
| `get_user_total_net_curve(id, chain_ids=...)` | `GET /v1/user/total_net_curve` |

### Chain

| Method | Endpoint |
| --- | --- |
| `get_chain_list()` | `GET /v1/chain/list` |
| `get_chain(id)` | `GET /v1/chain` |

### Token

| Method | Endpoint |
| --- | --- |
| `get_token(chain_id, id)` | `GET /v1/token` |
| `get_token_list_by_ids(chain_id, ids)` | `GET /v1/token/list_by_ids` |
| `get_token_history_price(id, chain_id, date_at)` | `GET /v1/token/history_price` |

DeBank payloads are large and frequently extended, so the models accept and
preserve unknown fields (`extra="allow"`) — new API fields are available on the
parsed objects without a library upgrade.

## Configuration

```python
DeBankClient(
    access_key,                 # required: your DeBank Cloud AccessKey
    base_url="https://pro-openapi.debank.com",
    access_key_header="AccessKey",  # header name is configurable
    timeout=30.0,
    max_retries=2,              # retries on HTTP 429 / 5xx with backoff
    backoff_factor=0.5,
    client=None,                # supply your own httpx.Client to reuse
)
```

On HTTP 429 (rate limit; the Pro plan allows up to 100 req/s) and 5xx, the
client retries with exponential backoff, honoring any `Retry-After` header.

## Errors

```python
from debank import DeBankError, DeBankAPIError, DeBankRateLimitError

try:
    client.get_user_total_balance(id="0x...")
except DeBankRateLimitError as exc:   # HTTP 429
    print(exc.retry_after)
except DeBankAPIError as exc:         # any non-2xx
    print(exc.status_code, exc.response_body)
```

All library exceptions derive from `DeBankError`.

## License

MIT — see [LICENSE](LICENSE).
