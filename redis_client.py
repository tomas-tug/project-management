import os
import redis
from dotenv import load_dotenv

load_dotenv()

# Redis接続設定
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    REDIS_HOST = os.environ.get("REDIS_HOST", "ntb-redis. redis.cache.windows.net")
    REDIS_PORT = int(os. environ.get("REDIS_PORT", 6380))
    REDIS_PASSWORD = os.environ. get("REDIS_PASSWORD")
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        ssl=True,
        decode_responses=False
    )

# 起動時にRedis接続を確認
try:
    if redis_client.ping():
        print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")