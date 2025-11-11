# tyriavault-backend

Backend part of TyriaVault made with FastAPI (Python)

## Features

- **RESTful API** with FastAPI
- **Database** with PostgreSQL and SQLAlchemy
- **Cache System** with Redis (optional) or InMemory fallback
- **GW2 API Integration** for game data
- **Automated Crawlers** for periodic data updates

## Cache Configuration

The application supports two cache backends:

### Redis (Recommended for production)

Add the `REDIS_URL` to your `.env` file:

```env
REDIS_URL=redis://localhost:6379/0
```

If Redis connection fails or is not configured, the application automatically falls back to InMemory cache.

### InMemory Cache (Default)

If `REDIS_URL` is not set, the application uses an InMemory cache backend automatically.

## Testing

### Unit Tests

Unit tests always use InMemory cache for speed and isolation:

```bash
pytest app/tests/unit
```

### Integration Tests

Integration tests use Redis via Docker Compose:

```bash
# Windows
run_integration_tests.bat

# Linux/Mac
./run_integration_tests.sh
```
