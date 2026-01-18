"""The clients that are responsible for fetching data from different sources."""

# pylint: disable=too-few-public-methods

import abc
import dataclasses
import datetime
from typing import Iterable, List, Mapping

import requests  # type: ignore[import-untyped]

from api import schemas

COINGECKO_COIN_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum",
}

COINBASE_COIN_IDS = {
    "btc": "BTC",
    "eth": "ETH",
}

BINANCE_COIN_IDS = {
    "btc": "BTC",
    "eth": "ETH",
}


@dataclasses.dataclass
class AssetMapping:
    """Dataclass representing the mapping of assets to their corresponding IDs for a service."""

    reverse_mapping: Mapping[str, str]
    asset_ids: Iterable[str]
    invalid_assets: Iterable[str]


def _map_assets(assets: Iterable[str], id_mapping: Mapping[str, str]) -> AssetMapping:
    reverse_mapping = {}
    asset_ids = []
    invalid_assets = []
    for asset in assets:
        asset_id = id_mapping[asset.lower()]
        if not asset_id:
            invalid_assets.append(asset)
        asset_ids.append(asset_id)
        reverse_mapping[asset_id] = asset.lower()

    return AssetMapping(
        reverse_mapping=reverse_mapping,
        asset_ids=asset_ids,
        invalid_assets=invalid_assets,
    )


class CryptoClient(abc.ABC):
    """The base class of clients for different crypto data sources."""

    @abc.abstractmethod
    def get_prices(self, assets: Iterable[str]) -> List[schemas.BaseCryptoPrice]:
        """Get the price of an asset.

        Arguments:
            assets: The asset symbols whose prices are to be fetched.

        """


class CoinGeckoClient(CryptoClient):
    """The client for CoinGecko."""

    def get_prices(self, assets: Iterable[str]) -> List[schemas.BaseCryptoPrice]:  # noqa: D102
        url = "https://api.coingecko.com/api/v3/simple/price"

        asset_mapping = _map_assets(assets, COINGECKO_COIN_IDS)
        if asset_mapping.invalid_assets:
            raise ValueError(
                f"Invalid assets for CoinGecko: f{', '.join(asset_mapping.invalid_assets)}."
            )

        params = {"ids": ",".join(asset_mapping.asset_ids), "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=10)
        response_contents = response.json()

        dt = datetime.datetime.now(datetime.timezone.utc)
        reverse_mapping_copy = dict(asset_mapping.reverse_mapping)
        results = [
            schemas.BaseCryptoPrice(
                asset=reverse_mapping_copy.pop(asset_id).upper(),
                quote="USD",
                price=data["usd"],
                source="coingecko",
                fetched_at=dt,
            )
            for asset_id, data in response_contents.items()
        ]

        if reverse_mapping_copy:
            raise RuntimeError(
                f"Assets with invalid Coingecko asset IDs: "
                f"{', '.join(reverse_mapping_copy.values())}"
            )
        return results


class CoinbaseClient(CryptoClient):
    """The client for Coinbase."""

    @staticmethod
    def _get_price(asset: str) -> schemas.BaseCryptoPrice:
        url = "https://api.coinbase.com/v2/prices/{}-USD/spot"
        if asset not in COINBASE_COIN_IDS:
            raise ValueError(f"{asset} is not a valid or accepted asset for Coinbase.")
        asset_id = COINBASE_COIN_IDS[asset]
        url = url.format(asset_id)
        response = requests.get(url, timeout=10)
        response_contents = response.json()
        return schemas.BaseCryptoPrice(
            asset=asset.upper(),
            quote="USD",
            price=response_contents["data"]["amount"],
            source="coinbase",
            fetched_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def get_prices(self, assets: Iterable[str]) -> List[schemas.BaseCryptoPrice]:  # noqa: D102
        return [self._get_price(asset) for asset in assets]


class BinanceClient(CryptoClient):
    """The client for Binance. The USD currency used is Binance's USDT."""

    def get_prices(self, assets: Iterable[str]) -> List[schemas.BaseCryptoPrice]:  # noqa: D102
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url, timeout=10)
        response_contents = response.json()

        asset_mapping = _map_assets(assets, BINANCE_COIN_IDS)
        if asset_mapping.invalid_assets:
            raise ValueError(
                f"Invalid assets for Binance: f{', '.join(asset_mapping.invalid_assets)}."
            )

        dt = datetime.datetime.now(datetime.timezone.utc)
        reverse_mapping_copy = dict(asset_mapping.reverse_mapping)
        results = []
        for p in response_contents:
            for asset_id in reverse_mapping_copy:
                if p["symbol"] == f"{asset_id}USDT":
                    results.append(
                        schemas.BaseCryptoPrice(
                            asset=reverse_mapping_copy.pop(asset_id).upper(),
                            quote="USD",
                            price=p["price"],
                            source="binance",
                            fetched_at=dt,
                        )
                    )
                    break
            if not reverse_mapping_copy:
                break

        if reverse_mapping_copy:
            raise RuntimeError(
                f"Assets with invalid Binance asset IDs: {', '.join(reverse_mapping_copy.values())}"
            )
        return results
