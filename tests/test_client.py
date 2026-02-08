# pylint: disable=protected-access

"""Test the different behaviors of the different clients from the clients module."""

import datetime
import decimal
from datetime import timezone
from urllib import parse

import pytest

from api import schemas
from ingestion import clients

PRICES = {"btc": 123.456, "eth": 111.111}
COINGECKO_REVERSE_MAPPING = clients._map_assets(
    PRICES.keys(), clients.COINGECKO_COIN_IDS
).reverse_mapping
COINBASE_REVERSE_MAPPING = clients._map_assets(
    PRICES.keys(), clients.COINBASE_COIN_IDS
).reverse_mapping
BINANCE_REVERSE_MAPPING = clients._map_assets(
    PRICES.keys(), clients.BINANCE_COIN_IDS
).reverse_mapping


def _make_mock_response(mocker, json_data, status_code=200):
    response = mocker.Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


def mock_get(mocker, url: str, params=None, **_):
    """Mock the requests.get calls used in the clients module."""
    if "coingecko" in url:
        assets = params.get("ids", "").split(",")
        coingecko_result = {
            asset: {"usd": PRICES[COINGECKO_REVERSE_MAPPING[asset]]}
            for asset in assets
            if asset in COINGECKO_REVERSE_MAPPING
        }
        return _make_mock_response(mocker, coingecko_result)
    if "coinbase" in url:
        parsed = parse.urlparse(url)
        path = parsed.path
        parts = path.strip("/").split("/")
        pair = parts[2]
        asset = pair.split("-")[0]
        if asset not in COINBASE_REVERSE_MAPPING:
            coinbase_result = {"error": "not found", "code": 5, "message": "not found"}
        else:
            coinbase_result = {
                "data": {
                    "amount": PRICES[COINBASE_REVERSE_MAPPING[asset]],
                    "base": asset,
                    "currency": "USD",
                }
            }
        return _make_mock_response(mocker, coinbase_result)
    binance_result = [
        {"symbol": "BTCUSDT", "price": PRICES["btc"]},
        {"symbol": "ETHUSDT", "price": PRICES["eth"]},
        {"symbol": "FBRUSDT", "price": "0.123"},
    ]
    return _make_mock_response(mocker, binance_result)


MOCK_TIME = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestCoinGeckoClient:
    """Tests for the CoinGeckoClient."""

    def test_coingecko_client_success(self, mocker):
        """Test calling the CoinGecko client with a success."""
        mocker.patch(
            "ingestion.clients.requests.get",
            side_effect=lambda url, **kw: mock_get(mocker, url, **kw),
        )
        mock_datetime = mocker.patch("ingestion.clients.datetime.datetime")
        mock_datetime.now.return_value = MOCK_TIME

        client = clients.CoinGeckoClient()
        result = client.get_prices(["btc", "eth"])
        assert result == [
            schemas.BaseCryptoPrice(
                asset="BTC",
                quote="USD",
                price=decimal.Decimal("123.456"),
                source="coingecko",
                fetched_at=MOCK_TIME,
            ),
            schemas.BaseCryptoPrice(
                asset="ETH",
                quote="USD",
                price=decimal.Decimal("111.111"),
                source="coingecko",
                fetched_at=MOCK_TIME,
            ),
        ]

    def test_coingecko_client_invalid_assets(self):
        """Test calling the CoinGecko client with invalid assets."""
        with pytest.raises(ValueError, match="Invalid assets for CoinGecko: foo, bar."):
            clients.CoinGeckoClient().get_prices(["foo", "bar"])


class TestCoinbaseClient:
    """Tests for the CoinbaseClient."""

    def test_coinbase_client_success(self, mocker):
        """Test calling the Coinbase client with a success."""
        mocker.patch(
            "ingestion.clients.requests.get",
            side_effect=lambda url, **kw: mock_get(mocker, url, **kw),
        )
        mock_datetime = mocker.patch("ingestion.clients.datetime.datetime")
        mock_datetime.now.return_value = MOCK_TIME

        client = clients.CoinbaseClient()
        result = client.get_prices(["btc", "eth"])
        assert result == [
            schemas.BaseCryptoPrice(
                asset="BTC",
                quote="USD",
                price=decimal.Decimal("123.456"),
                source="coinbase",
                fetched_at=MOCK_TIME,
            ),
            schemas.BaseCryptoPrice(
                asset="ETH",
                quote="USD",
                price=decimal.Decimal("111.111"),
                source="coinbase",
                fetched_at=MOCK_TIME,
            ),
        ]

    def test_coinbase_client_invalid_assets(self):
        """Test calling the Coinbase client with invalid assets."""
        with pytest.raises(ValueError, match="Invalid assets for Coinbase: foo, bar."):
            clients.CoinbaseClient().get_prices(["foo", "bar"])


class TestBinanceClient:
    """Tests for the BinanceClient."""

    def test_binance_client_success(self, mocker):
        """Test calling the Binance client with a success."""
        mocker.patch(
            "ingestion.clients.requests.get",
            side_effect=lambda url, **kw: mock_get(mocker, url, **kw),
        )
        mock_datetime = mocker.patch("ingestion.clients.datetime.datetime")
        mock_datetime.now.return_value = MOCK_TIME

        client = clients.BinanceClient()
        result = client.get_prices(["btc", "eth"])
        assert result == [
            schemas.BaseCryptoPrice(
                asset="BTC",
                quote="USD",
                price=decimal.Decimal("123.456"),
                source="binance",
                fetched_at=MOCK_TIME,
            ),
            schemas.BaseCryptoPrice(
                asset="ETH",
                quote="USD",
                price=decimal.Decimal("111.111"),
                source="binance",
                fetched_at=MOCK_TIME,
            ),
        ]

    def test_binance_client_invalid_assets(self):
        """Test calling the Binance client with invalid assets."""
        with pytest.raises(ValueError, match="Invalid assets for Binance: foo, bar."):
            clients.BinanceClient().get_prices(["foo", "bar"])
