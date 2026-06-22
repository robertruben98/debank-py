"""Tests for DeBank client construction and configuration."""

import httpx
import pytest

from debank import AsyncDeBankClient, DeBankClient


def test_access_key_is_required_positional():
    client = DeBankClient("my-access-key")
    assert client.access_key == "my-access-key"
    client.close()


def test_default_base_url():
    client = DeBankClient("k")
    assert client.base_url == "https://pro-openapi.debank.com"
    client.close()


def test_base_url_is_configurable_and_trailing_slash_stripped():
    client = DeBankClient("k", base_url="https://example.test/")
    assert client.base_url == "https://example.test"
    client.close()


def test_access_key_sent_under_default_header_name():
    client = DeBankClient("secret-key")
    # The auth header is applied on every request (see _request); it is built once.
    assert client._headers["AccessKey"] == "secret-key"
    client.close()


def test_access_key_header_name_is_configurable():
    client = DeBankClient("secret-key", access_key_header="X-Access-Key")
    assert client._headers["X-Access-Key"] == "secret-key"
    assert "AccessKey" not in client._headers
    client.close()


def test_sync_client_is_a_context_manager():
    with DeBankClient("k") as client:
        assert isinstance(client, DeBankClient)


def test_client_can_reuse_supplied_httpx_client():
    transport = httpx.Client(base_url="https://pro-openapi.debank.com")
    client = DeBankClient("k", client=transport)
    assert client._client is transport
    # A supplied client is owned by the caller and not closed by us.
    client.close()
    assert not transport.is_closed
    transport.close()


@pytest.mark.asyncio
async def test_async_client_construction_and_header():
    client = AsyncDeBankClient("secret-key")
    assert client.access_key == "secret-key"
    assert client.base_url == "https://pro-openapi.debank.com"
    assert client._headers["AccessKey"] == "secret-key"
    await client.aclose()
