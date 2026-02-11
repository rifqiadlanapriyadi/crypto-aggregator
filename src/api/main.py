"""The main configuration of the crypto_aggregator API."""

from typing import List, Optional

import fastapi
from fastapi import status
from sqlalchemy import orm

from api import database, models, schemas

app = fastapi.FastAPI()


@app.get("/prices/{asset}", response_model=List[schemas.BaseCryptoPrice])
def get_crypto_prices(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    asset: str,
    db: orm.Session = fastapi.Depends(database.get_db),
    source: Optional[str] = None,
    quote: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
):
    """Get the price data of a given asset."""
    asset_upper = asset.upper()

    query = db.query(models.CryptoPrice).filter(models.CryptoPrice.asset == asset_upper)

    if source is not None:
        query = query.where(models.CryptoPrice.source == source)

    if quote is not None:
        query = query.where(models.CryptoPrice.quote == quote)

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    crypto_prices = db.execute(query).scalars().all()
    if not crypto_prices:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto asset {asset} with the given parameters not found.",
        )
    return crypto_prices
