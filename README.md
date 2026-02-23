# Crypto Aggregator

This project is a price ingestion and query service designed to collect asset prices from multiple sources, store them
efficiently, and expose a fast, flexible API for querying historical price data.

Currently fetching:
#### Assets
* Bitcoin (BTC)
* Ethereum (ETH)
#### Sources
* [CoinGecko](https://www.coingecko.com/)
* [Binance](https://www.binance.com)
* [Coinbase](https://www.coinbase.com)

## Features
* Distributed ingestion pipeline using RabbitMQ
* Ingestion task scheduling with Celery
* Fault-tolerant worker processing with retries and dead-lettering
* High-performance REST API with FastAPI
* Multi-dimensional query filtering (asset, quote, source)
* Pagination and efficient indexed querying
* Redis-based read-through caching
* PostgreSQL-backed time-series storage
* SQLAlchemy ORM with Alembic migrations
* Structured logging and tracing
* OpenAPI-driven API documentation

## Tech Stack
### Backend
* Python
* FastAPI – API framework
* SQLAlchemy – ORM + database modeling
* Alembic – Database migrations

### Messaging & Background Jobs
* Celery - Task scheduling
* RabbitMQ – Task queue
* Worker-based async ingestion architecture

### Cache
* Redis – High-speed in-memory cache

### Database
* PostgreSQL

### Infrastructure
* Docker

## Architecture Overview
* FastAPI serves as the public API layer and request validator
* Pydantic schemas define request and response contracts
* SQLAlchemy models define persistence and database interactions
* PostgreSQL stores normalized time-series price data
* Celery orchestrates background task execution
* RabbitMQ acts as the message broker for ingestion jobs
* Celery Beat schedules recurring ingestion tasks
* Redis provides low-latency caching for read-heavy endpoints
* External price providers are integrated through modular client adapters
* Business logic is isolated within ingestion and service layers
* Alembic manages schema migrations

## Development

### Prerequisites
* [Python 3.13](https://www.python.org/downloads/release/python-3130/)
* [uv](https://docs.astral.sh/uv/)
* [Docker](https://www.docker.com/)

### Installation
Create a virtual environment and install dependencies:
```commandline
uv venv
uv sync --all-groups
```

### Environment Variables
Create an .env file (change with your own values):
```commandline
touch .env
cat <<EOF > .env
ENVIRONMENT=dev
POSTGRES_USER=<db_username>
POSTGRES_PASSWORD=<db_password>
POSTGRES_DB=<db_name>
DATABASE_URL=postgresql://<db_username>:<db_password>@db:5432/<db_name>
RABBITMQ_USER=<rabbitmq_username>
RABBITMQ_PASSWORD=<rabbitmq_password>
RABBITMQ_URL=amqp://<rabbitmq_username>:<rabbitmq_password>@rabbitmq:5672//
REDIS_PASSWORD=<redis_password>
REDIS_URL=redis://:<redis_password>@redis:6379/0
INGESTION_INTERVAL=60
EOF
```

### Using Docker
To start the Docker containers run:
```commandline
docker compose up -d --build
```

At this point, an interactive API documentation can be accessed at http://localhost:8000/docs#/ and the RabbitMQ
dashboard can be accessed at http://localhost:15672/.

To stop the containers run:
> **_Note:_**  Be sure not to use `-v` to preserve database contents
```commandline
docker compose down
```

### Database Migrations
After making changes to the database schema, run this to create a revision:
```commandline
alembic revision --autogenerate -m "describe change"
```
Then go to the file generated in ./alembic/versions and make the changes necessary.

Be sure to add the revision to git:
```commandline
git add ./alembic/versions
```

To apply the revision, do:
```commandline
alembic upgrade head
```

To revert to a specific revision, do:
```commandline
alembic downgrade <Revision ID>
```
