import os
import json
from typing import Optional, Dict
from fastapi import Cookie, HTTPException, Request, Header
from msal import ConfidentialClientApplication, SerializableTokenCache
from redis_client import redis_client

# Azure AD設定
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
AUTHORITY = os.environ.get("AUTHORITY")
SCOPE = ["https://graph.microsoft.com/.default"]

def get_ms_oid_from_session_cookie(session_cookie: str) -> Optional[str]:
    """
    Flaskのsession cookieからms_oidを取得
    """
    if not session_cookie:
        return None
    
    try:
        key = f"shared:ms_oid_by_session:{session_cookie}"
        blob = redis_client.get(key)
        if blob:
            ms_oid = blob.decode("utf-8") if isinstance(blob, bytes) else str(blob)
            print(f"✓ Found ms_oid from session: {ms_oid}")
            return ms_oid
    except Exception as e:
        print(f"Failed to get ms_oid from session cookie: {e}")
    
    return None

def get_ms_oid_from_user_id(user_id: int) -> Optional[str]:
    """
    user_idからms_oidを取得（フォールバック）
    """
    try:
        key = f"shared:ms_oid_by_user:{user_id}"
        blob = redis_client.get(key)
        if blob:
            ms_oid = blob. decode("utf-8") if isinstance(blob, bytes) else str(blob)
            print(f"✓ Found ms_oid from user_id: {ms_oid}")
            return ms_oid
    except Exception as e:
        print(f"Failed to get ms_oid from user_id: {e}")
    
    return None

def get_token_info_from_redis(ms_oid: str) -> Optional[Dict]:
    """
    Redisからtoken_infoを取得（簡易版）
    """
    try:
        key = f"token_info:{ms_oid}"
        blob = redis_client.get(key)
        
        if blob:
            if isinstance(blob, bytes):
                blob = blob.decode("utf-8")
            token_info = json.loads(blob)
            print(f"✓ Found token_info for ms_oid: {ms_oid}")
            return token_info
    except Exception as e:
        print(f"Failed to get token_info from Redis: {e}")
    
    return None

def get_msal_token_cache(ms_oid: str) -> Optional[SerializableTokenCache]:
    """
    RedisからMSAL token cacheを取得
    """
    try:
        key = f"msal_cache:{ms_oid}"
        cache_blob = redis_client.get(key)
        
        if cache_blob:
            cache = SerializableTokenCache()
            if isinstance(cache_blob, bytes):
                cache_blob = cache_blob.decode("utf-8")
            cache. deserialize(cache_blob)
            print(f"✓ Found MSAL cache for ms_oid: {ms_oid}")
            return cache
    except Exception as e:
        print(f"Failed to get MSAL cache from Redis: {e}")
    
    return None

def get_access_token_for_user(ms_oid: str) -> Optional[str]:
    """
    ms_oidを使ってMicrosoft Graph APIのアクセストークンを取得
    
    優先順位:
    1. token_info から直接取得（シンプル・高速）
    2. MSAL cacheから取得（トークン更新対応）
    """
    
    # 方法1: token_infoから直接取得
    token_info = get_token_info_from_redis(ms_oid)
    if token_info and token_info.get("access_token"):
        print("✓ Using access token from token_info")
        return token_info["access_token"]
    
    # 方法2: MSAL cacheから取得
    token_cache = get_msal_token_cache(ms_oid)
    if not token_cache:
        print(f"✗ No token cache found for ms_oid: {ms_oid}")
        return None
    
    # MSALアプリを初期化
    msal_app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
        token_cache=token_cache
    )
    
    # キャッシュからアカウントを取得
    accounts = msal_app.get_accounts()
    account = None
    for acc in accounts:
        # home_account_idは "oid. tid" 形式
        if acc.get("home_account_id", "").startswith(ms_oid):
            account = acc
            break
    
    if not account:
        print(f"✗ No account found in cache for ms_oid: {ms_oid}")
        return None
    
    # Silent token取得を試みる
    result = msal_app.acquire_token_silent(
        scopes=SCOPE,
        account=account
    )
    
    if result and "access_token" in result:
        # キャッシュが更新された場合はRedisに保存
        if token_cache. has_state_changed:
            try:
                cache_blob = token_cache.serialize()
                redis_client.set(f"msal_cache:{ms_oid}", cache_blob, ex=60 * 60 * 8)
                print(f"✓ Updated MSAL cache in Redis for ms_oid: {ms_oid}")
            except Exception as e:
                print(f"Failed to update MSAL cache: {e}")
        
        print("✓ Successfully acquired token from MSAL cache")
        return result["access_token"]
    
    print(f"✗ Failed to acquire token: {result. get('error_description', 'Unknown error')}")
    return None

async def get_current_user(
    request: Request,
    session: Optional[str] = Cookie(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict:
    """
    FastAPIの依存性注入で使う認証ヘルパー
    
    使い方:
        @app.get("/api/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": "Success", "ms_oid": user["ms_oid"]}
    """
    # 1. session cookieからms_oidを取得
    ms_oid = get_ms_oid_from_session_cookie(session)
    
    # 2. フォールバック: X-User-IDヘッダーから取得
    if not ms_oid and x_user_id:
        try:
            user_id = int(x_user_id)
            ms_oid = get_ms_oid_from_user_id(user_id)
        except ValueError:
            pass
    
    if not ms_oid:
        raise HTTPException(
            status_code=401,
            detail="認証情報が見つかりません。Flaskアプリでログインしてください。"
        )
    
    # 3.  アクセストークンを取得
    access_token = get_access_token_for_user(ms_oid)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="トークンの取得に失敗しました。再ログインが必要です。"
        )
    
    return {
        "ms_oid": ms_oid,
        "access_token": access_token
    }