import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Redis接続設定
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    REDIS_HOST = os.environ.get("REDIS_HOST", "ntb-redis. redis.cache.windows.net")
    REDIS_PORT = int(os. environ.get("REDIS_PORT", 6380))
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
    redis_client = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        password=REDIS_PASSWORD,
        ssl=True, 
        decode_responses=False
    )

def test_redis_connection():
    """Redis接続テスト"""
    print("=" * 50)
    print("Redis 接続テスト")
    print("=" * 50)
    
    try:
        # Ping テスト
        if redis_client.ping():
            print("✓ Redis接続成功！")
        else:
            print("✗ Redis接続失敗")
            return False
    except Exception as e:
        print(f"✗ Redis接続エラー: {e}")
        return False
    
    return True

def list_keys(pattern="*"):
    """Redisのキー一覧を表示"""
    print("\n" + "=" * 50)
    print(f"キー一覧 (パターン: {pattern})")
    print("=" * 50)
    
    try:
        keys = redis_client. keys(pattern)
        if not keys:
            print("キーが見つかりません")
            return
        
        print(f"見つかったキー数: {len(keys)}\n")
        for i, key in enumerate(keys, 1):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            ttl = redis_client.ttl(key)
            ttl_str = f"{ttl}秒" if ttl > 0 else "無期限" if ttl == -1 else "期限切れ"
            print(f"{i}. {key_str}")
            print(f"   TTL: {ttl_str}")
    except Exception as e:
        print(f"エラー: {e}")

def get_key_value(key_pattern):
    """指定したキーの値を取得"""
    print("\n" + "=" * 50)
    print(f"キーの値取得 (パターン: {key_pattern})")
    print("=" * 50)
    
    try:
        keys = redis_client.keys(key_pattern)
        if not keys:
            print("該当するキーが見つかりません")
            return
        
        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            value = redis_client.get(key)
            
            if value:
                value_str = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                print(f"\nキー: {key_str}")
                print(f"値: {value_str[:100]}..." if len(value_str) > 100 else f"値: {value_str}")
            else:
                print(f"\nキー: {key_str}")
                print("値: None")
    except Exception as e:
        print(f"エラー: {e}")

def test_write_read():
    """書き込み・読み込みテスト"""
    print("\n" + "=" * 50)
    print("書き込み・読み込みテスト")
    print("=" * 50)
    
    test_key = "test:connection"
    test_value = "Hello from Flask!"
    
    try:
        # 書き込み
        redis_client.set(test_key, test_value, ex=300)  # 5分間有効
        print(f"✓ 書き込み成功: {test_key} = {test_value}")
        
        # 読み込み
        result = redis_client.get(test_key)
        result_str = result.decode('utf-8') if isinstance(result, bytes) else str(result)
        
        if result_str == test_value:
            print(f"✓ 読み込み成功: {result_str}")
        else:
            print(f"✗ 読み込み失敗: 期待値={test_value}, 実際={result_str}")
        
        # 削除
        redis_client.delete(test_key)
        print(f"✓ テストキー削除完了")
        
    except Exception as e:
        print(f"✗ エラー: {e}")

def check_session_data():
    """セッションデータの確認"""
    print("\n" + "=" * 50)
    print("セッションデータの確認")
    print("=" * 50)
    
    # Flask-Sessionのキーを探す
    patterns = [
        "session:*",
        "flask_session:*",
        "shared:ms_oid_by_session:*",
        "shared:ms_oid_by_user:*",
        "msal_cache:*"
    ]
    
    for pattern in patterns:
        print(f"\n--- {pattern} ---")
        keys = redis_client.keys(pattern)
        if keys:
            print(f"見つかったキー: {len(keys)}個")
            for key in keys[:5]:  # 最初の5件のみ表示
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                print(f"  - {key_str}")
            if len(keys) > 5:
                print(f"  ...  他 {len(keys) - 5} 件")
        else:
            print("キーなし")

def main():
    """メイン実行"""
    if not test_redis_connection():
        return
    
    # テスト実行
    test_write_read()
    
    # 全キー一覧
    list_keys("*")
    
    # セッションデータ確認
    check_session_data()
    
    # ms_oid関連のキーを表示
    print("\n" + "=" * 50)
    print("ms_oid 関連データ")
    print("=" * 50)
    get_key_value("shared:ms_oid_by_*")
    
    # MSAL cache を表示
    print("\n" + "=" * 50)
    print("MSAL Cache データ")
    print("=" * 50)
    get_key_value("msal_cache:*")

if __name__ == "__main__":
    main()