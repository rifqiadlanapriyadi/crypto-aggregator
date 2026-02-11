"""The module containing the ingestion function."""

import logging
from typing import Iterable, List

from sqlalchemy.dialects import postgresql

from api import database, models, schemas
from ingestion import clients

CLIENTS_TO_CALL: Iterable[clients.CryptoClient] = {
    clients.CoinGeckoClient(),
    clients.CoinbaseClient(),
    clients.BinanceClient(),
}


def ingest_prices(assets: Iterable[str]) -> None:
    """Fetch price data by calling clients and push the data to the database."""
    logging.info("Running price ingestion for %s with %s", assets, CLIENTS_TO_CALL)

    db = next(database.get_db())
    prices: List[schemas.BaseCryptoPrice] = []

    logging.info("Fetching prices from clients.")
    for client in CLIENTS_TO_CALL:
        try:
            logging.info("Fetching prices of %s from %s", assets, client)
            prices = prices + client.get_prices(assets)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("An error occurred while calling %s: %s", client, repr(e))
            raise e

    # Cannot do bulk upsert using the ORM as the ingestion upsert needs to use
    # the model's unique constraint on asset, quote, and source
    rows = [
        {
            "asset": price.asset,
            "quote": price.quote,
            "price": price.price,
            "source": price.source,
            "fetched_at": price.fetched_at,
        }
        for price in prices
    ]

    logging.info("Upserting %s", rows)
    stmt = postgresql.insert(models.CryptoPrice).values(rows)

    stmt = stmt.on_conflict_do_update(
        index_elements=["asset", "quote", "source"],
        set_={
            "price": stmt.excluded.price,
            "fetched_at": stmt.excluded.fetched_at,
        },
    )

    db.execute(stmt)
    db.commit()
    logging.info("Changes pushed to the database.")


if __name__ == "__main__":
    ingest_prices(["btc", "eth"])
