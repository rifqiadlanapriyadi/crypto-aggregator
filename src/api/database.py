"""The database configuration of the app."""

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative

from api import config

SQLALCHEMY_DATABASE_URL = config.settings.database_url

engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL)

session_local = orm.sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative.declarative_base()


def get_db():
    """Get the database."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()
