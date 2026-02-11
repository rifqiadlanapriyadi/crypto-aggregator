"""The main configuration of the crypto_aggregator API."""

import json
from typing import List, Optional

import fastapi
import redis
from fastapi import encoders, status
from sqlalchemy import orm

from api import database, models, schemas
from cache import redis as redis_cache

CACHE_TTL = 30

app = fastapi.FastAPI()


@app.get("/prices/{asset}", response_model=List[schemas.BaseCryptoPrice])
def get_crypto_prices(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    asset: str,
    db: orm.Session = fastapi.Depends(database.get_db),
    cache: redis.Redis = fastapi.Depends(redis_cache.get_redis_client),
    source: Optional[str] = None,
    quote: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
):
    """Get the price data of a given asset by trying the cache first."""
    asset_upper = asset.upper()
    cache_key = f"prices:{asset_upper}"

    cached = cache.get(cache_key)

    if cached:
        rows = json.loads(cached)  # type: ignore[arg-type]
    else:
        query = db.query(models.CryptoPrice).filter(models.CryptoPrice.asset == asset_upper)
        rows = [schemas.BaseCryptoPrice.model_validate(row).model_dump() for row in query.all()]
        encoded = encoders.jsonable_encoder(rows)
        cache.setex(cache_key, CACHE_TTL, json.dumps(encoded))

    if source:
        rows = [r for r in rows if r["source"] == source]

    if quote:
        rows = [r for r in rows if r["quote"] == quote]

    start = offset or 0
    end = start + limit if limit else None
    result = rows[start:end]

    if not result:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto asset {asset} with the given parameters not found.",
        )

    return result
