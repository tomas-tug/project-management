from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import redis
from typing import Optional

app = FastAPI(title="MSOID Reader")

# CORS 設定（フロントエンドが別ホストにある場合は調整）
origins = os.environ.get("CORS_ORIGINS", "")
allow_origins = origins.split(",") if origins else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,   # cookie を許可するなら True にする
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 接続（REDIS_URL を優先）
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    REDIS_HOST = os.getenv("REDIS_HOST", "ntb-redis.redis.cache.windows.net")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6380))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    redis_client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, ssl=True, decode_responses=False
    )

# 設定：Flask と同じ SESSION_COOKIE 名を使うこと
SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "session")
SHARED_KEY_PREFIX = os.environ.get("SHARED_KEY_PREFIX", "shared:ms_oid_by_session:")
SHARED_USER_PREFIX = os.environ.get("SHARED_USER_PREFIX", "shared:ms_oid_by_user:")


def get_ms_oid_from_request(request: Request) -> str:
    """
    リクエストの cookie から session id を取り、Redis の専用キーを読み出して ms_oid を返す。
    見つからなければ HTTPException(401) を投げる。
    """
    # 1) session cookie ベース
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        key = SHARED_KEY_PREFIX + session_cookie
        blob = redis_client.get(key)
        if blob:
            return blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)

    # 2) fallback: user_id ベース（例：ヘッダや別 cookie で伝えてくる場合）
    user_id = request.headers.get("X-User-ID") or request.cookies.get("user_id")
    if user_id:
        key = SHARED_USER_PREFIX + str(user_id)
        blob = redis_client.get(key)
        if blob:
            return blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)

    raise HTTPException(status_code=401, detail="ms_oid not found")


# 依存関数（ルートで使う）
def require_ms_oid(request: Request) -> str:
    return get_ms_oid_from_request(request)


@app.get("/whoami")
async def whoami(ms_oid: str = Depends(require_ms_oid)):
    # ここで ms_oid を使ってユーザや権限を引くなど実装可能
    return {"ms_oid": ms_oid}


@app.get("/protected")
async def protected(ms_oid: str = Depends(require_ms_oid)):
    # 実運用なら ms_oid から DB lookup して権限チェックなど行う
    return {"message": "ok", "ms_oid": ms_oid}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_ms_oid_reader:app", host="0.0.0.0", port=8000, reload=True)