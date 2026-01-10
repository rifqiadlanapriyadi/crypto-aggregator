"""The main configuration of the crypto_aggregator API."""

import fastapi
from fastapi import status
from sqlalchemy import orm

from api import database, models, schemas

app = fastapi.FastAPI()


@app.get("/prices/{asset}", response_model=schemas.BaseCryptoPrice)
def get_crypto_price(
    asset: str,
    db: orm.Session = fastapi.Depends(database.get_db),
):
    """Get the price data of a given asset."""
    asset_upper = asset.upper()
    crypto_price = (
        db.query(models.CryptoPrice)
        .filter(models.CryptoPrice.asset == asset_upper)
        .first()
    )
    if not crypto_price:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto asset {asset} not found.",
        )
    return crypto_price
