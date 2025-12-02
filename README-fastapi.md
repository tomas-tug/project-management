# FastAPI MSOID Reader

This small FastAPI app reads `ms_oid` from Redis keys written by your Flask app's login flow.

## Files

- `fastapi_ms_oid_reader.py` — FastAPI app
- `tests/test_whoami.py` — pytest tests
- `requirements-dev.txt` — development dependencies

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Full Redis connection URL | (none) |
| `REDIS_HOST` | Redis host (if `REDIS_URL` not set) | `ntb-redis.redis.cache.windows.net` |
| `REDIS_PORT` | Redis port (if `REDIS_URL` not set) | `6380` |
| `REDIS_PASSWORD` | Redis password (if `REDIS_URL` not set) | (none) |
| `SESSION_COOKIE_NAME` | Name of the session cookie | `session` |
| `SHARED_KEY_PREFIX` | Redis key prefix for session-based lookup | `shared:ms_oid_by_session:` |
| `SHARED_USER_PREFIX` | Redis key prefix for user-based lookup | `shared:ms_oid_by_user:` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000` |

## Installation

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running the Server

Start the FastAPI server with uvicorn:

```bash
uvicorn fastapi_ms_oid_reader:app --host 0.0.0.0 --port 8000 --reload
```

Or run directly:

```bash
python fastapi_ms_oid_reader.py
```

## API Endpoints

- `GET /whoami` — Returns `{"ms_oid": "..."}` for the authenticated user
- `GET /protected` — Returns `{"message": "ok", "ms_oid": "..."}` for authenticated requests

### Example Usage

```bash
# With session cookie
curl -v --cookie "session=<session_cookie_value>" http://localhost:8000/whoami

# With X-User-ID header
curl -v -H "X-User-ID: 42" http://localhost:8000/whoami
```

## Running Tests

```bash
pytest tests/
```

Or run with verbose output:

```bash
pytest -v tests/
```

## Notes

- Tests use monkeypatching to mock the Redis client with an in-memory fake implementation.
- The FastAPI app expects the Flask login to write `shared:ms_oid_by_session:{session_id}` or `shared:ms_oid_by_user:{user_id}` keys in Redis.
- For browser-based calls from another origin, ensure CORS and cookie credentials (`fetch(..., {credentials: 'include'})`) are correctly set.
