# pylint: disable=redefined-outer-name,unused-argument

"""Test file for API operations."""

import datetime
from datetime import timezone
from typing import Generator

import pytest
import sqlalchemy
from fastapi import testclient
from sqlalchemy import orm

from api import database, main, models

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
            asset="FBR",
            quote="USD",
            price=123.123,
            source="barbaz_source",
            fetched_at=datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    )
    tdb.add(
        models.CryptoPrice(
            asset="FBR",
            quote="USD",
            price=123.456,
            source="foobar_source",
            fetched_at=datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    )
    tdb.commit()


class TestAPI:
    """Test different task requests."""

    def test_get_crypto_price_success(
        self, client: testclient.TestClient, tdb: orm.Session, setup
    ) -> None:
        """Test a successful get of a crypto prices."""
        response = client.get("/prices/fbr")
        data = response.json()
        assert response.status_code == 200
        assert data == [
            {
                "asset": "FBR",
                "quote": "USD",
                "price": "123.123",
                "source": "barbaz_source",
                "fetched_at": "2026-01-01T12:00:00",
            },
            {
                "asset": "FBR",
                "quote": "USD",
                "price": "123.456",
                "source": "foobar_source",
                "fetched_at": "2026-01-01T12:00:00",
            },
        ]

    def test_get_crypto_price_fail(
        self, client: testclient.TestClient, tdb: orm.Session, setup
    ) -> None:
        """Test a get of a crypto prices with an unknown asset."""
        response = client.get("/prices/asd")
        data = response.json()
        assert response.status_code == 404
        assert data["detail"] == "Crypto asset asd not found."
