"""Tests for error handling and retry/backoff behaviour."""

import httpx
import pytest
import respx

from debank import (
    AsyncDeBankClient,
    DeBankAPIError,
    DeBankClient,
    DeBankError,
    DeBankRateLimitError,
)
from debank._base import backoff_delay, is_retryable

BASE = "https://pro-openapi.debank.com"
WALLET = "0xabc"


@respx.mock
def test_non_2xx_raises_debank_api_error():
    respx.get(f"{BASE}/v1/chain").mock(
        return_value=httpx.Response(400, json={"message": "bad chain id"})
    )
    with DeBankClient(access_key="k") as client, pytest.raises(DeBankAPIError) as excinfo:
        client.get_chain(id="nope")
    assert excinfo.value.status_code == 400
    assert "bad chain id" in str(excinfo.value)
    assert excinfo.value.response_body == {"message": "bad chain id"}


@respx.mock
def test_403_capacity_limit_raises_api_error():
    respx.get(f"{BASE}/v1/chain").mock(return_value=httpx.Response(403, text="capacity exceeded"))
    with DeBankClient(access_key="k") as client, pytest.raises(DeBankAPIError) as excinfo:
        client.get_chain(id="eth")
    assert excinfo.value.status_code == 403
    # A non-JSON body is preserved as raw text.
    assert excinfo.value.response_body == "capacity exceeded"


def test_rate_limit_error_is_an_api_error_is_a_debank_error():
    # Exception hierarchy: DeBankRateLimitError -> DeBankAPIError -> DeBankError.
    assert issubclass(DeBankRateLimitError, DeBankAPIError)
    assert issubclass(DeBankAPIError, DeBankError)


@respx.mock
def test_429_is_retried_then_succeeds():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=[{"id": "eth"}]),
        ]
    )
    with DeBankClient(access_key="k", backoff_factor=0.0) as client:
        chains = client.get_chain_list()
    assert chains[0].id == "eth"
    assert route.call_count == 2


@respx.mock
def test_429_exhausts_retries_and_raises_rate_limit_error():
    respx.get(f"{BASE}/v1/chain/list").mock(
        return_value=httpx.Response(
            429, headers={"Retry-After": "0"}, json={"message": "slow down"}
        )
    )
    client = DeBankClient(access_key="k", max_retries=1, backoff_factor=0.0)
    with pytest.raises(DeBankRateLimitError) as excinfo:
        client.get_chain_list()
    client.close()
    assert excinfo.value.status_code == 429
    assert excinfo.value.retry_after == 0.0


@respx.mock
def test_5xx_is_retried():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json=[{"id": "eth"}]),
        ]
    )
    with DeBankClient(access_key="k", backoff_factor=0.0) as client:
        client.get_chain_list()
    assert route.call_count == 2


def test_is_retryable_classifies_statuses():
    assert is_retryable(httpx.Response(429))
    assert is_retryable(httpx.Response(500))
    assert is_retryable(httpx.Response(503))
    assert not is_retryable(httpx.Response(200))
    assert not is_retryable(httpx.Response(400))
    assert not is_retryable(httpx.Response(404))


def test_backoff_delay_prefers_retry_after():
    assert backoff_delay(0, 0.5, retry_after=7.0) == 7.0


def test_backoff_delay_is_exponential_without_retry_after():
    assert backoff_delay(0, 0.5, retry_after=None) == 0.5
    assert backoff_delay(1, 0.5, retry_after=None) == 1.0
    assert backoff_delay(2, 0.5, retry_after=None) == 2.0


@respx.mock
@pytest.mark.asyncio
async def test_async_429_is_retried_then_succeeds():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=[{"id": "eth"}]),
        ]
    )
    async with AsyncDeBankClient(access_key="k", backoff_factor=0.0) as client:
        chains = await client.get_chain_list()
    assert chains[0].id == "eth"
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_async_error_raises():
    respx.get(f"{BASE}/v1/user/total_balance").mock(
        return_value=httpx.Response(401, json={"message": "invalid AccessKey"})
    )
    client = AsyncDeBankClient(access_key="bad")
    with pytest.raises(DeBankAPIError) as excinfo:
        await client.get_user_total_balance(id=WALLET)
    await client.aclose()
    assert excinfo.value.status_code == 401
