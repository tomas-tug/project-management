from fastapi import  Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 相対インポートから絶対インポートに変更（main.pyを直接実行する場合）
import crud
import models
import schemas
from database import engine, get_db, test_connection


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

# Users
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

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

# Ships
@app.post("/ships/", response_model=schemas.Ship)
def create_ship(ship: schemas.ShipCreate, db: Session = Depends(get_db)):
    return crud.create_ship(db=db, ship=ship)

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

# Note: Ship は読み取り専用モデルのため、更新・削除エンドポイントは提供しません



# http://127.0.0.1:8000/redoc （ReDoc） 
# http://127.0.0.1:8000/docs （Swagger UI）
