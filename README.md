# TyriaVault Backend

FastAPI-based backend service for TyriaVault, a Guild Wars 2 (GW2) companion project. It provides RESTful API endpoints,
scheduled data crawling, and persistence for semi-static and dynamic GW2 data.

## Overview

TyriaVault Backend exposes versioned APIs (`/api/v1`) to serve GW2-related data. On startup it:

- Creates database schema (SQLAlchemy)
- Seeds nearly invariable reference data (genders, races, professions, etc.)
- Initializes a GW2 API client
- Performs an initial incremental crawl of "worlds" data
- Schedules a periodic crawler job (default every 48h) via APScheduler

## Key Features

- FastAPI application with CORS configured for a single frontend origin
- Pydantic Settings for environment-based configuration (.env / .env.test)
- Async PostgreSQL access via SQLAlchemy + psycopg
- Incremental data crawler jobs (APScheduler)
- Structured logging
- Test suite (pytest + pytest-asyncio + coverage)

## Requirements

- Python 3.13+
- PostgreSQL database (reachable via `DATABASE_URL`)
- A valid GW2 API key

Core Python dependencies are pinned in `pyproject.toml`:

## Installation (Local Development)

Below are Windows (cmd.exe) examples; adapt for other shells as needed.

1. Clone the repository:

```
git clone <repo-url>
```

2. Create and activate a virtual environment:

```
python -m venv .venv
.venv\Scripts\activate
```

3. Upgrade pip (optional but recommended):

```
pip install --upgrade pip
```

4. Install dependencies (editable mode optional):

```
pip install -e .
```

If you prefer non-editable:

```
pip install .
```

5. (Optional) Verify installation:

```
python -c "import fastapi, sqlalchemy; print('Environment OK')"
```

## Configuration

The application reads settings via Pydantic Settings.
Environment variables come from a file determined by `ENV`:

- If `ENV=test` then `.env.test` is used
- Otherwise `.env` is used

## Running the Application

Activate the virtual environment first.

### Development (auto-reload)

```
uvicorn app.main:api --reload --port 8000
```

Access the interactive docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Production-Like Run

```
uvicorn app.main:api --host 0.0.0.0 --port 8000 --log-level info
```

You can set environment variables beforehand if needed:

```
set LOG_LEVEL=INFO
set ENV=prod
uvicorn app.main:api --port 8000
```

## Scheduled Jobs

A worlds crawler job runs at startup and then at an interval defined by `WORLDS_CRAWLER_INTERVAL_MINUTES` (default 2880
minutes = 48 hours) using APScheduler.

## Database Migrations

Currently the project auto-creates tables at startup using `Base.metadata.create_all`. Future migration tooling (e.g.,
Alembic) can be integrated as an enhancement.

## Testing

Set the environment so that `.env.test` is used (if you keep a separate test DB):

```
set ENV=test
```

Run tests:

```
pytest
```

Run tests with verbose output:

```
pytest -v
```

Run coverage:

```
coverage run -m pytest
coverage report -m
```

Generate HTML coverage (output goes to `htmlcov/`):

```
coverage html
```

Open coverage report:

```
start htmlcov\index.html
```

## Useful Maintenance Commands

- List outdated packages:

```
pip list --outdated
```

- Export current dependency tree:

```
pip freeze > requirements.lock.txt
```

## Project Structure (abridged)

```
app/
  main.py                # FastAPI app factory & lifespan
  api/v1/                # Versioned API routers
  core/config.py         # Settings via Pydantic
  core/logging.py        # Logging configuration
  crawlers/              # Data crawler implementations
  db/                    # Database models, sessions, seeding
  gw2/                   # GW2 client integration
tests/                   # Pytest-based test suite
pyproject.toml           # Build & dependency metadata
LICENSE                  # MIT License
```

## Logging

A timestamped log file (e.g., `tyriavault_YYYYMMDD_HHMMSS.log`) is created under `app/`. Adjust `LOG_LEVEL` for
verbosity.

## Environment Separation

- Development: `.env` + `uvicorn --reload`
- Testing: `set ENV=test` + `.env.test` + `pytest`
- Production: Provide env vars securely (without committing secrets)

## Contributing

(Placeholder) Please open issues or pull requests for improvements. Add tests for new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

Guild Wars 2 and related assets are trademarks of ArenaNet. This project is an unofficial fan-made tool and is not
endorsed by or affiliated with ArenaNet.

## Next Steps / Ideas

- Dockerfile & docker-compose for easy local stack
- Alembic migrations
- Health check endpoint
- CI workflow (lint + tests + coverage threshold)

---
Feel free to adapt and extend this README as the project evolves.
