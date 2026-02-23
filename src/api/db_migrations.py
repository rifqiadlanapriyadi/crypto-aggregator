"""The file containing DB-migration-related functions to be called programmatically."""

from alembic import command
from alembic.config import Config


def run_migrations():
    """Run alembic migrations to the most recent head."""
    alembic_cfg = Config("alembic.ini")

    command.upgrade(alembic_cfg, "head")
