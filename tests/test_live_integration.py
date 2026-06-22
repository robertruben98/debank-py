"""Live integration tests against the real DeBank Cloud Pro API.

These tests are marked ``integration`` and are deselected by default (see
``pyproject.toml``). They run only when a real, paid ``DEBANK_ACCESS_KEY`` is
present in the environment; otherwise each test is skipped.

Run them explicitly with::

    DEBANK_ACCESS_KEY=your-key pytest -m integration
"""

import os

import pytest

from debank import AsyncDeBankClient, Chain, DeBankClient

ACCESS_KEY = os.environ.get("DEBANK_ACCESS_KEY")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not ACCESS_KEY,
        reason="DEBANK_ACCESS_KEY not set; live DeBank Cloud Pro tests skipped.",
    ),
]

# A well-known, high-activity public address (Vitalik) for read-only checks.
LIVE_WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_live_chain_list():
    with DeBankClient(access_key=ACCESS_KEY) as client:
        chains = client.get_chain_list()
    assert chains, "expected at least one supported chain"
    assert all(isinstance(c, Chain) for c in chains)
    assert any(c.id == "eth" for c in chains)


def test_live_total_balance():
    with DeBankClient(access_key=ACCESS_KEY) as client:
        total = client.get_user_total_balance(id=LIVE_WALLET)
    assert total.total_usd_value >= 0.0


def test_live_all_token_list():
    with DeBankClient(access_key=ACCESS_KEY) as client:
        tokens = client.get_user_all_token_list(id=LIVE_WALLET)
    assert isinstance(tokens, list)


@pytest.mark.asyncio
async def test_live_async_chain_list():
    async with AsyncDeBankClient(access_key=ACCESS_KEY) as client:
        chains = await client.get_chain_list()
    assert chains
