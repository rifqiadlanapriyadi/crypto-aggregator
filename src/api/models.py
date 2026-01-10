# mypy: disable-error-code=valid-type

"""The sqlalchemy models for the tables in the database."""

import sqlalchemy

from api import database


class CryptoPrice(database.Base):  # pylint: disable=too-few-public-methods
    """The model used to represent crypto prices in database operations."""

    __tablename__ = "crypto_price"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    asset = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    quote = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Numeric, nullable=False)
    source = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    fetched_at = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=False)
