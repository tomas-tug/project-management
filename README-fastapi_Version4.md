# FastAPI MSOID Reader (test harness)

This small FastAPI app reads `ms_oid` from Redis keys written by your Flask app's login flow.

Files to add:
- `fastapi_ms_oid_reader.py` — FastAPI app
- `tests/test_whoami.py` — pytest tests
- `requirements-dev.txt` — development dependencies

Environment variables:
- `REDIS_URL` OR (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)
- `SESSION_COOKIE_NAME` (default: `session`)
- `SHARED_KEY_PREFIX` (default: `shared:ms_oid_by_session:`)
- `SHARED_USER_PREFIX` (default: `shared:ms_oid_by_user:`)
- `CORS_ORIGINS` (optional; comma-separated list)

Run FastAPI locally:
1. Install dev deps:
   ```
   pip install -r requirements-dev.txt
   ```
2. Start uvicorn:
   ```
   uvicorn fastapi_ms_oid_reader:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Make sure the browser has a Flask session cookie (login via your Flask app), then call:
   - `GET /whoami` — will return `{"ms_oid": "..."}`
   - Example with `curl`:
     ```
     curl -v --cookie "session=<session_cookie_value>" http://localhost:8000/whoami
     ```

Run tests:
```
pytest -q
```

Notes:
- Tests monkeypatch `redis.from_url` and `redis.Redis` to use an in-memory fake redis.
- The FastAPI app expects the Flask login to write `shared:ms_oid_by_session:{session_id}` or `shared:ms_oid_by_user:{user_id}` keys in Redis.
- For browser-based calls from another origin, ensure CORS and cookie credentials (`fetch(..., credentials: 'include')`) are correctly set.