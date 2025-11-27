from fastapi import Request
import os
import importlib

# import the FastAPI app object from your app module
app_module = importlib.import_module("fastapi_ms_oid_reader")
app = getattr(app_module, "app")

# helper to obtain redis client from the app module in a robust way
def _get_redis_client():
    # prefer get_redis_client() if present (lazy-init variant)
    get_client = getattr(app_module, "get_redis_client", None)
    if callable(get_client):
        try:
            return get_client()
        except Exception as e:
            return e
    # fallback: try module-level redis_client
    rc = getattr(app_module, "redis_client", None)
    if rc is not None:
        return rc
    return None

@app.get("/debug-whoami")
async def debug_whoami(request: Request):
    """
    Debug endpoint:
    - shows which cookie name FastAPI expects
    - shows the cookie value sent by the client (if any)
    - shows the computed Redis key and value (if reachable)
    - shows a small set of headers useful for auth (X-User-ID, Origin, Host)
    """
    cookie_name = os.environ.get("SESSION_COOKIE_NAME", "session")
    session_cookie = request.cookies.get(cookie_name)

    shared_prefix = os.environ.get("SHARED_KEY_PREFIX", "shared:ms_oid_by_session:")
    shared_user_prefix = os.environ.get("SHARED_USER_PREFIX", "shared:ms_oid_by_user:")

    redis_client = _get_redis_client()
    ping = None
    session_key = None
    session_value = None
    user_key = None
    user_value = None
    redis_error = None

    try:
        if isinstance(redis_client, Exception):
            redis_error = f"redis init error: {redis_client}"
        elif redis_client is None:
            redis_error = "redis client not found in app module"
        else:
            # try ping
            try:
                ping = redis_client.ping()
            except Exception as e:
                ping = False
                redis_error = f"ping error: {e}"

            # check session-key
            if session_cookie:
                session_key = shared_prefix + session_cookie
                try:
                    blob = redis_client.get(session_key)
                    if blob is not None:
                        session_value = blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)
                except Exception as e:
                    session_value = None
                    redis_error = f"get(session_key) error: {e}"

            # check user-id header fallback if present
            user_id = request.headers.get("X-User-ID") or request.cookies.get("user_id")
            if user_id:
                user_key = shared_user_prefix + str(user_id)
                try:
                    blob = redis_client.get(user_key)
                    if blob is not None:
                        user_value = blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)
                except Exception as e:
                    user_value = None
                    redis_error = f"get(user_key) error: {e}"

    except Exception as e:
        redis_error = f"unexpected error: {e}"

    # only return limited headers
    headers = {k: v for k, v in request.headers.items() if k.lower() in ("x-user-id", "origin", "host")}

    return {
        "session_cookie_name": cookie_name,
        "session_cookie_value": session_cookie,
        "computed_session_key": session_key,
        "session_key_value": session_value,
        "computed_user_key": user_key,
        "user_key_value": user_value,
        "redis_ping": ping,
        "redis_error": redis_error,
        "seen_headers": headers,
    }