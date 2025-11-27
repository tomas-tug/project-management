import pytest
from fastapi.testclient import TestClient

# import the app module (assumes fastapi_ms_oid_reader.py placed at repo root)
import fastapi_ms_oid_reader as app_module


class FakeRedis:
    """A minimal in-memory Redis mock for testing."""
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
    """Test /whoami endpoint with session cookie authentication."""
    # Monkeypatch redis.from_url and redis.Redis used in the module to return fake redis
    monkeypatch.setattr(app_module, "redis_client", fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": "cookie123"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-123"}


def test_whoami_with_user_id_header(monkeypatch, fake_redis):
    """Test /whoami endpoint with X-User-ID header authentication."""
    monkeypatch.setattr(app_module, "redis_client", fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", headers={"X-User-ID": "42"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-42"}


def test_whoami_unauthorized(monkeypatch):
    """Test /whoami endpoint returns 401 when no auth is provided."""
    # empty fake redis so no keys present
    empty_redis = FakeRedis(store={})
    monkeypatch.setattr(app_module, "redis_client", empty_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami")
    assert response.status_code == 401


def test_protected_with_session_cookie(monkeypatch, fake_redis):
    """Test /protected endpoint with session cookie authentication."""
    monkeypatch.setattr(app_module, "redis_client", fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/protected", cookies={"session": "cookie123"})
    assert response.status_code == 200
    assert response.json() == {"message": "ok", "ms_oid": "ms-oid-123"}
