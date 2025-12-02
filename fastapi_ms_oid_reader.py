import os
from typing import Optional

import redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "ntb-redis.redis.cache.windows.net")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")
SHARED_KEY_PREFIX = os.getenv("SHARED_KEY_PREFIX", "shared:ms_oid_by_session:")
SHARED_USER_PREFIX = os.getenv("SHARED_USER_PREFIX", "shared:ms_oid_by_user:")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

# Initialize redis client (module-level; tests may monkeypatch redis.from_url or redis.Redis or redis_client)
if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD or None,
        ssl=True,
        decode_responses=False,
    )

app = FastAPI()

# Configure CORS
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _decode_redis_value(val: Optional[bytes]) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except Exception:
            return None
    if isinstance(val, str):
        return val
    return None


def get_ms_oid_from_request(request: Request) -> str:
    """
    Attempts to read ms_oid from Redis using:
      1. session cookie -> SHARED_KEY_PREFIX + session_id
      2. header X-User-ID or cookie user_id -> SHARED_USER_PREFIX + user_id
    Raises HTTPException(401) if not found.
    """
    # 1) try session cookie
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        key = f"{SHARED_KEY_PREFIX}{session_id}"
        try:
            val = redis_client.get(key)
        except Exception:
            val = None
        ms_oid = _decode_redis_value(val)
        if ms_oid:
            return ms_oid

    # 2) fallback to user id via header or cookie
    user_id = request.headers.get("X-User-ID") or request.cookies.get("user_id")
    if user_id:
        key = f"{SHARED_USER_PREFIX}{user_id}"
        try:
            val = redis_client.get(key)
        except Exception:
            val = None
        ms_oid = _decode_redis_value(val)
        if ms_oid:
            return ms_oid

    raise HTTPException(status_code=401, detail="Unauthorized")


def get_ms_oid_dependency(request: Request) -> str:
    return get_ms_oid_from_request(request)


@app.get("/whoami")
def whoami(ms_oid: str = Depends(get_ms_oid_dependency)):
    return {"ms_oid": ms_oid}


@app.get("/protected")
def protected(ms_oid: str = Depends(get_ms_oid_dependency)):
    return {"message": "ok", "ms_oid": ms_oid}


if __name__ == "__main__":
    uvicorn.run("fastapi_ms_oid_reader:app", host="0.0.0.0", port=8000, reload=True)
