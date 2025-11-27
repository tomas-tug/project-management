import pytest
from fastapi.testclient import TestClient
import types

# import the app module (assumes fastapi_ms_oid_reader.py placed at repo root)
import fastapi_ms_oid_reader as app_module

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
        "shared:ms_oid_by_user:42": b"ms-oid-42"
    }
    return FakeRedis(store=store)

def test_whoami_with_session_cookie(monkeypatch, fake_redis):
    # Monkeypatch redis.from_url and redis.Redis used in the module to return fake redis
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.from_url", lambda url, decode_responses=False: fake_redis)
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.Redis", lambda *args, **kwargs: fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": "cookie123"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-123"}

def test_whoami_with_user_id_header(monkeypatch, fake_redis):
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.from_url", lambda url, decode_responses=False: fake_redis)
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.Redis", lambda *args, **kwargs: fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", headers={"X-User-ID": "42"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-42"}

def test_whoami_unauthorized(monkeypatch, fake_redis):
    # empty fake redis so no keys present
    empty_redis = FakeRedis(store={})
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.from_url", lambda url, decode_responses=False: empty_redis)
    monkeypatch.setattr("fastapi_ms_oid_reader.redis.Redis", lambda *args, **kwargs: empty_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami")
    assert response.status_code == 401