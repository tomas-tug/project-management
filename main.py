from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 相対インポートから絶対インポートに変更（main.pyを直接実行する場合）
import crud
import models
import schemas
from database import engine, get_db, test_connection
from fastapi.middleware.cors import CORSMiddleware
import os
import redis
from typing import Optional


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # 接続テスト
        if test_connection():
            # テーブル作成
            models.Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
        else:
            print("Warning: Could not connect to database")
    except Exception as e:
        print(f"Database startup warning: {e}")
    
    yield
    
    # Shutdown
    print("Application shutdown")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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


# ===== Users (読み取り専用 - ntb_data テーブル参照) =====
@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Note: User はマスターデータ(ntb_data)のため、作成・更新・削除エンドポイントは提供しません

# ===== Ships (読み取り専用 - ntb_data テーブル参照) =====
@app.get("/ships/", response_model=list[schemas.Ship])
def read_ships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ships = crud.get_ships(db, skip=skip, limit=limit)
    return ships

@app.get("/ships/{ship_id}", response_model=schemas.Ship)
def read_ship(ship_id: int, db: Session = Depends(get_db)):
    db_ship = crud.get_ship(db, ship_id=ship_id)
    if db_ship is None:
        raise HTTPException(status_code=404, detail="Ship not found")
    return db_ship

# Note: Ship はマスターデータ(ntb_data)のため、作成・更新・削除エンドポイントは提供しません



# http://127.0.0.1:8000/redoc （ReDoc） 
# http://127.0.0.1:8000/docs （Swagger UI）
