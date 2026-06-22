"""Tests for the DeBank Cloud endpoint methods (sync client, respx-mocked)."""

import httpx
import pytest
import respx

from debank import (
    Chain,
    DeBankClient,
    Protocol,
    Token,
    TotalBalance,
)

BASE = "https://pro-openapi.debank.com"
WALLET = "0x5853eD4f26A3fceA565b3FBC698bb19cdF6DEB85"


@pytest.fixture
def client():
    with DeBankClient(access_key="test-key") as c:
        yield c


@respx.mock
def test_get_user_total_balance_parses_total_and_chains(client):
    route = respx.get(f"{BASE}/v1/user/total_balance").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_usd_value": 12345.67,
                "chain_list": [
                    {"id": "eth", "name": "Ethereum", "usd_value": 10000.0},
                    {"id": "bsc", "name": "BNB Chain", "usd_value": 2345.67},
                ],
            },
        )
    )
    result = client.get_user_total_balance(id=WALLET)

    assert isinstance(result, TotalBalance)
    assert result.total_usd_value == 12345.67
    assert result.chain_list[0].id == "eth"
    assert result.chain_list[1].usd_value == 2345.67
    # The wallet address is sent as the `id` query parameter.
    assert dict(route.calls.last.request.url.params)["id"] == WALLET


@respx.mock
def test_access_key_header_is_sent_on_requests(client):
    route = respx.get(f"{BASE}/v1/user/total_balance").mock(
        return_value=httpx.Response(200, json={"total_usd_value": 0.0, "chain_list": []})
    )
    client.get_user_total_balance(id=WALLET)
    assert route.calls.last.request.headers["AccessKey"] == "test-key"


@respx.mock
def test_get_user_chain_balance(client):
    route = respx.get(f"{BASE}/v1/user/chain_balance").mock(
        return_value=httpx.Response(200, json={"usd_value": 999.5})
    )
    result = client.get_user_chain_balance(id=WALLET, chain_id="eth")
    assert result.usd_value == 999.5
    params = dict(route.calls.last.request.url.params)
    assert params["id"] == WALLET
    assert params["chain_id"] == "eth"


@respx.mock
def test_get_user_used_chain_list_returns_list(client):
    respx.get(f"{BASE}/v1/user/used_chain_list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "eth", "name": "Ethereum", "born_at": 1500000000},
                {"id": "bsc", "name": "BNB Chain"},
            ],
        )
    )
    result = client.get_user_used_chain_list(id=WALLET)
    assert len(result) == 2
    assert result[0].id == "eth"
    assert result[0].born_at == 1500000000


@respx.mock
def test_get_user_all_token_list_parses_balances(client):
    respx.get(f"{BASE}/v1/user/all_token_list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "eth",
                    "chain": "eth",
                    "symbol": "ETH",
                    "decimals": 18,
                    "price": 3000.0,
                    "amount": 1.5,
                }
            ],
        )
    )
    tokens = client.get_user_all_token_list(id=WALLET)
    assert isinstance(tokens[0], Token)
    assert tokens[0].symbol == "ETH"
    assert tokens[0].amount == 1.5


@respx.mock
def test_is_all_bool_param_rendered_as_lowercase_string(client):
    route = respx.get(f"{BASE}/v1/user/all_token_list").mock(
        return_value=httpx.Response(200, json=[])
    )
    client.get_user_all_token_list(id=WALLET, is_all=True)
    assert dict(route.calls.last.request.url.params)["is_all"] == "true"


@respx.mock
def test_chain_ids_list_param_comma_joined(client):
    route = respx.get(f"{BASE}/v1/user/all_token_list").mock(
        return_value=httpx.Response(200, json=[])
    )
    client.get_user_all_token_list(id=WALLET, chain_ids=["eth", "bsc", "matic"])
    assert dict(route.calls.last.request.url.params)["chain_ids"] == "eth,bsc,matic"


@respx.mock
def test_omitted_optional_params_are_not_sent(client):
    route = respx.get(f"{BASE}/v1/user/all_token_list").mock(
        return_value=httpx.Response(200, json=[])
    )
    client.get_user_all_token_list(id=WALLET)
    params = dict(route.calls.last.request.url.params)
    assert "is_all" not in params
    assert "chain_ids" not in params


@respx.mock
def test_get_user_token(client):
    respx.get(f"{BASE}/v1/user/token").mock(
        return_value=httpx.Response(
            200, json={"id": "0xabc", "chain": "eth", "symbol": "USDC", "amount": 100.0}
        )
    )
    token = client.get_user_token(id=WALLET, chain_id="eth", token_id="0xabc")
    assert token.symbol == "USDC"
    assert token.amount == 100.0


@respx.mock
def test_get_user_all_complex_protocol_list_parses_portfolio(client):
    respx.get(f"{BASE}/v1/user/all_complex_protocol_list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "aave3",
                    "chain": "eth",
                    "name": "Aave V3",
                    "portfolio_item_list": [
                        {
                            "name": "Lending",
                            "detail_types": ["lending"],
                            "stats": {"net_usd_value": 500.0},
                        }
                    ],
                }
            ],
        )
    )
    protocols = client.get_user_all_complex_protocol_list(id=WALLET)
    assert isinstance(protocols[0], Protocol)
    assert protocols[0].id == "aave3"
    assert protocols[0].portfolio_item_list[0].name == "Lending"


@respx.mock
def test_get_user_simple_protocol_list_parses_aggregates(client):
    respx.get(f"{BASE}/v1/user/simple_protocol_list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "compound",
                    "chain": "eth",
                    "name": "Compound",
                    "net_usd_value": 1000.0,
                    "asset_usd_value": 1500.0,
                    "debt_usd_value": 500.0,
                }
            ],
        )
    )
    protocols = client.get_user_simple_protocol_list(id=WALLET, chain_id="eth")
    assert protocols[0].net_usd_value == 1000.0
    assert protocols[0].debt_usd_value == 500.0
    assert protocols[0].portfolio_item_list == []


@respx.mock
def test_get_user_history_list_parses_dicts(client):
    route = respx.get(f"{BASE}/v1/user/history_list").mock(
        return_value=httpx.Response(
            200,
            json={
                "history_list": [{"id": "0xtx", "cate_id": "send"}],
                "cate_dict": {"send": {"name": "Send"}},
                "project_dict": {},
                "token_dict": {"eth": {"symbol": "ETH"}},
                "cex_dict": {},
            },
        )
    )
    history = client.get_user_history_list(
        id=WALLET, chain_id="eth", start_time=1600000000, page_count=20
    )
    assert history.history_list[0]["id"] == "0xtx"
    assert history.token_dict["eth"]["symbol"] == "ETH"
    params = dict(route.calls.last.request.url.params)
    assert params["start_time"] == "1600000000"
    assert params["page_count"] == "20"


@respx.mock
def test_get_user_token_authorized_list(client):
    respx.get(f"{BASE}/v1/user/token_authorized_list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "0xtoken",
                    "symbol": "USDT",
                    "sum_exposure_usd": 250.0,
                    "spenders": [{"id": "0xspender", "exposure_usd": 250.0}],
                }
            ],
        )
    )
    auths = client.get_user_token_authorized_list(id=WALLET, chain_id="eth")
    assert auths[0].symbol == "USDT"
    assert auths[0].spenders[0].id == "0xspender"


@respx.mock
def test_get_user_total_net_curve(client):
    respx.get(f"{BASE}/v1/user/total_net_curve").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"timestamp": 1700000000, "usd_value": 100.0},
                {"timestamp": 1700003600, "usd_value": 105.0},
            ],
        )
    )
    curve = client.get_user_total_net_curve(id=WALLET)
    assert curve[0].timestamp == 1700000000
    assert curve[1].usd_value == 105.0


@respx.mock
def test_get_chain_list(client):
    respx.get(f"{BASE}/v1/chain/list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "eth", "community_id": 1, "name": "Ethereum", "is_support_pre_exec": True}
            ],
        )
    )
    chains = client.get_chain_list()
    assert isinstance(chains[0], Chain)
    assert chains[0].community_id == 1
    assert chains[0].is_support_pre_exec is True


@respx.mock
def test_get_chain(client):
    route = respx.get(f"{BASE}/v1/chain").mock(
        return_value=httpx.Response(200, json={"id": "bsc", "name": "BNB Chain"})
    )
    chain = client.get_chain(id="bsc")
    assert chain.name == "BNB Chain"
    assert dict(route.calls.last.request.url.params)["id"] == "bsc"


@respx.mock
def test_get_token(client):
    route = respx.get(f"{BASE}/v1/token").mock(
        return_value=httpx.Response(
            200, json={"id": "0xabc", "chain": "eth", "symbol": "USDC", "price": 1.0}
        )
    )
    token = client.get_token(chain_id="eth", id="0xabc")
    assert token.symbol == "USDC"
    params = dict(route.calls.last.request.url.params)
    assert params["chain_id"] == "eth"
    assert params["id"] == "0xabc"


@respx.mock
def test_get_token_list_by_ids_comma_joins(client):
    route = respx.get(f"{BASE}/v1/token/list_by_ids").mock(
        return_value=httpx.Response(200, json=[{"id": "0x1"}, {"id": "0x2"}])
    )
    tokens = client.get_token_list_by_ids(chain_id="eth", ids=["0x1", "0x2"])
    assert len(tokens) == 2
    assert dict(route.calls.last.request.url.params)["ids"] == "0x1,0x2"


@respx.mock
def test_get_token_history_price(client):
    route = respx.get(f"{BASE}/v1/token/history_price").mock(
        return_value=httpx.Response(200, json={"price": 42.5})
    )
    result = client.get_token_history_price(id="0xabc", chain_id="eth", date_at="2024-01-01")
    assert result.price == 42.5
    assert dict(route.calls.last.request.url.params)["date_at"] == "2024-01-01"


@respx.mock
def test_extra_fields_are_preserved(client):
    respx.get(f"{BASE}/v1/chain").mock(
        return_value=httpx.Response(
            200, json={"id": "eth", "name": "Ethereum", "some_new_field": "surprise"}
        )
    )
    chain = client.get_chain(id="eth")
    # Undocumented fields are kept thanks to extra="allow".
    assert chain.model_extra["some_new_field"] == "surprise"
