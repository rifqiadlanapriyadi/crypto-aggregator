"""The module containing Celery tasks."""

from typing import Iterable

from ingestion import price_ingestion
from worker import celery_app


@celery_app.app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
    queue="price_ingestion",
    ignore_result=True,
)
def ingest_prices_task(_, assets: Iterable[str]) -> None:
    """Push a task to fetch crypto price data and push to the database."""
    price_ingestion.ingest_prices(assets)
