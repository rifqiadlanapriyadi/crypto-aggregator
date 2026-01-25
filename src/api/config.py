"""The configuration for environment variable loading."""

import os

import dotenv
import pydantic_settings

env = os.getenv("ENVIRONMENT", "dev")

if env == "dev":
    dotenv.load_dotenv()


class Settings(pydantic_settings.BaseSettings):
    """The settings of the environment variables."""

    environment: str
    database_url: str
    rabbitmq_url: str


settings = Settings()  # type: ignore[call-arg]
