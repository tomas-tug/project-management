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
from auth import get_current_user
from typing import Dict, Optional
import httpx


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

# CORS設定（Reactから呼び出す場合）
app. add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React開発環境
        "http://localhost:5000",  # Flask開発環境
        "https://your-flask-app.azurewebsites.net",
        "https://your-react-app.azurewebsites.net",
        # 本番環境のドメインを追加
    ],
    allow_credentials=True,  # Cookieを許可
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "message": "FastAPI is running",
        "auth": "Shared with Flask via Redis"
    }

@app.get("/api/protected")
async def protected_route(user: Dict = Depends(get_current_user)):
    """
    認証が必要なエンドポイントの例
    """
    return {
        "message": "認証成功！",
        "ms_oid": user["ms_oid"],
        "note": "このエンドポイントはFlaskでログインしたユーザーのみアクセス可能です"
    }

@app.get("/api/graph/me")
async def get_user_profile(user: Dict = Depends(get_current_user)):
    """
    Microsoft Graph APIを呼び出してユーザー情報を取得
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {user['access_token']}"},
            timeout=30.0
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "displayName": user_data.get("displayName"),
                "mail": user_data.get("mail"),
                "jobTitle": user_data.get("jobTitle"),
                "officeLocation": user_data.get("officeLocation"),
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )

@app.get("/api/debug/session")
async def debug_session(
    user: Dict = Depends(get_current_user)
):
    """
    デバッグ用：認証情報を確認
    """
    return {
        "ms_oid": user["ms_oid"],
        "has_access_token": bool(user. get("access_token")),
        "token_preview": user["access_token"][:50] + "..." if user. get("access_token") else None
    }


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
