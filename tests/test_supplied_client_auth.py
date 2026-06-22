"""Regression tests: the AccessKey must be sent even when a custom httpx client
is supplied via the ``client=`` argument.

DeBank requires the AccessKey header on *every* request, so the auth header must
be applied regardless of whether the client created the transport or the caller
supplied their own.
"""

import httpx
import pytest
import respx

from debank import AsyncDeBankClient, DeBankClient

BASE = "https://pro-openapi.debank.com"
WALLET = "0xabc"


@respx.mock
def test_access_key_sent_when_sync_client_supplied():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        return_value=httpx.Response(200, json=[{"id": "eth"}])
    )
    transport = httpx.Client(base_url=BASE)
    client = DeBankClient("supplied-key", client=transport)
    client.get_chain_list()
    client.close()
    transport.close()
    assert route.calls.last.request.headers["AccessKey"] == "supplied-key"


@respx.mock
def test_custom_access_key_header_name_sent_when_client_supplied():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        return_value=httpx.Response(200, json=[{"id": "eth"}])
    )
    transport = httpx.Client(base_url=BASE)
    client = DeBankClient("supplied-key", access_key_header="X-Access-Key", client=transport)
    client.get_chain_list()
    client.close()
    transport.close()
    headers = route.calls.last.request.headers
    assert headers["X-Access-Key"] == "supplied-key"


@respx.mock
@pytest.mark.asyncio
async def test_access_key_sent_when_async_client_supplied():
    route = respx.get(f"{BASE}/v1/chain/list").mock(
        return_value=httpx.Response(200, json=[{"id": "eth"}])
    )
    transport = httpx.AsyncClient(base_url=BASE)
    client = AsyncDeBankClient("supplied-key", client=transport)
    await client.get_chain_list()
    await client.aclose()
    await transport.aclose()
    assert route.calls.last.request.headers["AccessKey"] == "supplied-key"
