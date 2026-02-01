# mypy: disable-error-code=valid-type

"""The sqlalchemy models for the tables in the database."""

import decimal
from typing import Optional

import sqlalchemy
from sqlalchemy import Dialect, types

from api import database


class NonTrailingDecimal(types.TypeDecorator):
    """Decimal without trailing zeroes."""

    # pylint: disable=abstract-method,too-many-ancestors
    impl = sqlalchemy.Numeric
    cache_ok = True

    def process_bind_param(
        self, value: Optional[decimal.Decimal], dialect: Dialect
    ) -> Optional[decimal.Decimal]:
        """Normalize the decimal in before writing."""
        if value is None:
            return None
        return decimal.Decimal(value).normalize()

    def process_result_value(
        self, value: Optional[decimal.Decimal], dialect: Dialect
    ) -> Optional[decimal.Decimal]:
        """Normalize the decimal after reding."""
        if value is None:
            return None
        return value.normalize()


class CryptoPrice(database.Base):  # pylint: disable=too-few-public-methods
    """The model used to represent crypto prices in database operations."""

    __tablename__ = "crypto_price"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    asset = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    quote = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(NonTrailingDecimal, nullable=False)
    source = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    fetched_at = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        sqlalchemy.UniqueConstraint("asset", "quote", "source", name="uq_asset_quote_source"),
    )
