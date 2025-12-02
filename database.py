from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse
from dotenv import load_dotenv
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# データベース接続情報の取得
# ntb_projects に接続すると ntb_data のテーブルも参照可能
user = os.getenv("MYSQL_USER")
password = urllib.parse.quote_plus(os.getenv("MYSQL_PASSWORD", ""))
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DATABASE")
ssl_ca = os.getenv("MYSQL_SSL_CA")

# 接続情報の確認
if not all([user, host, database]):
    raise ValueError("Database configuration is incomplete. Check your .env file.")

logger.info(f"Connecting to Azure MySQL: {database}@{host}")
logger.info("ntb_data tables are accessible from ntb_projects connection")

# Azure MySQL 用の接続URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:3306/{database}?ssl_ca={ssl_ca}&ssl_verify_identity=true"

logger.info("SSL connection enabled for Azure MySQL")

# エンジンの作成
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# セッションの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baseクラス
Base = declarative_base()

# 依存性注入用の関数
def get_db():
    """データベースセッション (ntb_projects + ntb_data 参照可能)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 接続テスト関数
def test_connection():
    """Azure MySQL データベース接続をテストする関数"""
    try:
        with engine.connect() as connection:
            logger.info("Azure MySQL connection successful!")
            return True
    except Exception as e:
        logger.error(f"Azure MySQL connection failed: {str(e)}")
        return False