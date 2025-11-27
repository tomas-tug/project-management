import pytest
from fastapi.testclient import TestClient
import importlib
import redis as real_redis

# NOTE:
# We DON'T import fastapi_ms_oid_reader here at module import time because
# that module creates a redis client at import time. We need to monkeypatch
# real_redis.from_url and real_redis.Redis BEFORE importing/reloading the app module.

class FakeRedis:
    def __init__(self, store=None):
        self.store = store or {}

    def get(self, key):
        # emulate redis returning bytes (depending on decode_responses)
        val = self.store.get(key)
        if isinstance(val, str):
            return val.encode("utf-8")
        return val

    def set(self, key, value, ex=None):
        self.store[key] = value


@pytest.fixture
def fake_redis():
    store = {
        "shared:ms_oid_by_session:cookie123": b"ms-oid-123",
        "shared:ms_oid_by_user:42": b"ms-oid-42",
    }
    return FakeRedis(store=store)


def test_whoami_with_session_cookie(monkeypatch, fake_redis):
    # Patch the redis module BEFORE importing the app so that app's module-level
    # redis_client is created from the patched functions.
    monkeypatch.setattr(real_redis, "from_url", lambda url, decode_responses=False: fake_redis)
    monkeypatch.setattr(real_redis, "Redis", lambda *args, **kwargs: fake_redis)

    # Now import (or reload) the app module so it picks up the patched redis
    import fastapi_ms_oid_reader as app_module
    importlib.reload(app_module)

    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": "cookie123"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-123"}


def test_whoami_with_user_id_header(monkeypatch, fake_redis):
    monkeypatch.setattr(real_redis, "from_url", lambda url, decode_responses=False: fake_redis)
    monkeypatch.setattr(real_redis, "Redis", lambda *args, **kwargs: fake_redis)

    import fastapi_ms_oid_reader as app_module
    importlib.reload(app_module)

    client = TestClient(app_module.app)
    response = client.get("/whoami", headers={"X-User-ID": "42"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-42"}


def test_whoami_unauthorized(monkeypatch, fake_redis):
    empty_redis = FakeRedis(store={})
    monkeypatch.setattr(real_redis, "from_url", lambda url, decode_responses=False: empty_redis)
    monkeypatch.setattr(real_redis, "Redis", lambda *args, **kwargs: empty_redis)

    import fastapi_ms_oid_reader as app_module
    importlib.reload(app_module)

    client = TestClient(app_module.app)
    response = client.get("/whoami")
    assert response.status_code == 401