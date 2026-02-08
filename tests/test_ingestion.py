# pylint: disable=redefined-outer-name,unused-argument,duplicate-code

"""Test the price_ingestion module while mocking client results and using a test database."""

import datetime
import decimal
from datetime import timezone
from typing import Generator, Iterable

import pytest
import sqlalchemy
from fastapi import testclient
from sqlalchemy import orm

from api import database, main, models, schemas
from ingestion import price_ingestion

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
testing_session_local = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db() -> Generator[orm.Session, None, None]:
    try:
        db = testing_session_local()
        yield db
    finally:
        db.close()


@pytest.fixture
def tdb():
    """Properly create and drop testing database and yield the test session."""
    database.Base.metadata.create_all(bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        database.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> testclient.TestClient:
    """Override the database with the testing database and return the testing client."""
    main.app.dependency_overrides[database.get_db] = _override_get_db
    return testclient.TestClient(main.app)


@pytest.fixture
def setup(client: testclient.TestClient, tdb: orm.Session) -> None:
    """Set up users and tasks before tests."""
    tdb.add(
        models.CryptoPrice(
            asset="BTC",
            quote="USD",
            price=decimal.Decimal("150.5"),
            source="coingecko",
            fetched_at=datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    )
    tdb.commit()


MOCK_TIME = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_price(asset: str, price: decimal.Decimal, source: str) -> schemas.BaseCryptoPrice:
    return schemas.BaseCryptoPrice(
        asset=asset,
        quote="USD",
        price=decimal.Decimal(price),
        source=source,
        fetched_at=MOCK_TIME,
    )


COINGECKO_MOCK_RESULTS = {
    "btc": _make_price("BTC", decimal.Decimal("123.456"), "coingecko"),
    "eth": _make_price("ETH", decimal.Decimal("111.111"), "coingecko"),
}

BINANCE_MOCK_RESULTS = {
    "btc": _make_price("BTC", decimal.Decimal("130.3"), "binance"),
    "eth": _make_price("ETH", decimal.Decimal("120"), "binance"),
}

COINBASE_MOCK_RESULTS = {
    "btc": _make_price("BTC", decimal.Decimal("115.511"), "coinbase"),
    "eth": _make_price("ETH", decimal.Decimal("135.246"), "coinbase"),
}


def _mock_get_prices_factory(data):
    def _mock(_, assets: Iterable[str]):
        return [data[a] for a in assets if a in data]

    return _mock


def test_ingestion(client: testclient.TestClient, tdb: orm.Session, setup, mocker):
    """Test that the ingestion calls clients and upserts to the database"""
    mocker.patch(
        "ingestion.clients.CoinGeckoClient.get_prices",
        _mock_get_prices_factory(COINGECKO_MOCK_RESULTS),
    )
    mocker.patch(
        "ingestion.clients.CoinbaseClient.get_prices",
        _mock_get_prices_factory(COINBASE_MOCK_RESULTS),
    )
    mocker.patch(
        "ingestion.clients.BinanceClient.get_prices", _mock_get_prices_factory(BINANCE_MOCK_RESULTS)
    )
    mocker.patch("api.database.get_db", _override_get_db)

    expected = [
        {
            "asset": "BTC",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("123.456"),
            "quote": "USD",
            "source": "coingecko",
        },
        {
            "asset": "BTC",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("130.3"),
            "quote": "USD",
            "source": "binance",
        },
        {
            "asset": "ETH",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("1.2E+2"),
            "quote": "USD",
            "source": "binance",
        },
        {
            "asset": "ETH",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("111.111"),
            "quote": "USD",
            "source": "coingecko",
        },
        {
            "asset": "BTC",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("115.511"),
            "quote": "USD",
            "source": "coinbase",
        },
        {
            "asset": "ETH",
            "fetched_at": datetime.datetime(2026, 1, 1, 12, 0),
            "price": decimal.Decimal("135.246"),
            "quote": "USD",
            "source": "coinbase",
        },
    ]

    price_ingestion.ingest_prices(["btc", "eth"])

    rows = tdb.query(models.CryptoPrice).all()
    actual = [
        {
            "asset": row.asset,
            "price": row.price,
            "quote": row.quote,
            "source": row.source,
            "fetched_at": row.fetched_at,
        }
        for row in rows
    ]

    assert len(actual) == len(expected)
    assert all(item in actual for item in expected)
