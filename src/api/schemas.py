"""The schemas used for requests and responses."""

import datetime
import decimal

import pydantic


class BaseCryptoPrice(pydantic.BaseModel):
    """The pydantic schema for crypto price data."""

    asset: str
    quote: str
    price: decimal.Decimal
    source: str
    fetched_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)
