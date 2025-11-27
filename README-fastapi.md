# FastAPI MSOID Reader (Test Harness)

This minimal FastAPI app reads `ms_oid` from Redis keys written by your Flask app's login flow.

## Files

- `fastapi_ms_oid_reader.py` — FastAPI app with `/whoami` endpoint
- `tests/test_whoami.py` — pytest tests with mocked Redis
- `requirements-dev.txt` — development dependencies

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | - | Full Redis URL (takes priority) |
| `REDIS_HOST` | `ntb-redis.redis.cache.windows.net` | Redis host (if REDIS_URL not set) |
| `REDIS_PORT` | `6380` | Redis port (if REDIS_URL not set) |
| `REDIS_PASSWORD` | - | Redis password (if REDIS_URL not set) |
| `SESSION_COOKIE_NAME` | `session` | Flask session cookie name |
| `SHARED_KEY_PREFIX` | `shared:ms_oid_by_session:` | Redis key prefix for session lookup |
| `SHARED_USER_PREFIX` | `shared:ms_oid_by_user:` | Redis key prefix for user-id lookup |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed origins |

## Running FastAPI Locally

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Set environment variables (example):
   ```bash
   export REDIS_URL="redis://localhost:6379"
   # OR
   export REDIS_HOST="your-redis-host"
   export REDIS_PORT=6380
   export REDIS_PASSWORD="your-password"
   ```

3. Start the uvicorn server:
   ```bash
   uvicorn fastapi_ms_oid_reader:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Test the endpoint:
   ```bash
   # With session cookie
   curl -v --cookie "session=<session_cookie_value>" http://localhost:8000/whoami
   
   # With X-User-ID header
   curl -v -H "X-User-ID: <user_id>" http://localhost:8000/whoami
   ```

## Running Tests

```bash
pytest tests/test_whoami.py -v
```

Or simply:
```bash
pytest -q
```

## How It Works

1. The `/whoami` endpoint reads the Flask session cookie (configured via `SESSION_COOKIE_NAME`)
2. It looks up `shared:ms_oid_by_session:{session_id}` in Redis
3. If not found, it falls back to checking `X-User-ID` header or `user_id` cookie
4. For fallback, it looks up `shared:ms_oid_by_user:{user_id}` in Redis
5. Returns `{"ms_oid": "..."}` on success or HTTP 401 if not found

## Notes

- Tests use monkeypatching to mock `redis.from_url` and `redis.Redis` with an in-memory fake client
- For browser-based calls from another origin, ensure CORS and cookie credentials (`fetch(..., {credentials: 'include'})`) are correctly configured
- The Flask app must write the appropriate Redis keys during login for this service to work
