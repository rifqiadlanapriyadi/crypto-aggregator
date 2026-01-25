"""The definition of the Celery app."""

import celery  # type: ignore[import-untyped]

from api import config

app = celery.Celery(
    "worker",
    broker=config.settings.rabbitmq_url,
    backend="rpc://",
)

app.autodiscover_tasks(["worker"])  # File name needs to be tasks.py
