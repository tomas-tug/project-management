import pytest
from fastapi.testclient import TestClient

# import the app module (assumes fastapi_ms_oid_reader.py placed at repo root)
import fastapi_ms_oid_reader as app_module


# Test data constants
TEST_SESSION_ID = "cookie123"
TEST_USER_ID = "42"
TEST_MS_OID_SESSION = b"ms-oid-123"
TEST_MS_OID_USER = b"ms-oid-42"


class FakeRedis:
    """A minimal in-memory Redis mock for testing."""
    def __init__(self, store=None):
        self.store = store or {}

    def get(self, key):
        # Return bytes like real redis with decode_responses=False
        val = self.store.get(key)
        if isinstance(val, str):
            return val.encode("utf-8")
        return val

    def set(self, key, value, ex=None):
        self.store[key] = value


@pytest.fixture
def fake_redis():
    store = {
        f"shared:ms_oid_by_session:{TEST_SESSION_ID}": TEST_MS_OID_SESSION,
        f"shared:ms_oid_by_user:{TEST_USER_ID}": TEST_MS_OID_USER
    }
    return FakeRedis(store=store)


def test_whoami_with_session_cookie(monkeypatch, fake_redis):
    """Test /whoami endpoint with session cookie authentication."""
    # Monkeypatch redis_client to use fake redis
    monkeypatch.setattr(app_module, "redis_client", fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": TEST_SESSION_ID})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": TEST_MS_OID_SESSION.decode("utf-8")}


def test_whoami_with_user_id_header(monkeypatch, fake_redis):
    """Test /whoami endpoint with X-User-ID header authentication."""
    monkeypatch.setattr(app_module, "redis_client", fake_redis)

    client = TestClient(app_module.app)
    response = client.get("/whoami", headers={"X-User-ID": TEST_USER_ID})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": TEST_MS_OID_USER.decode("utf-8")}


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
    response = client.get("/protected", cookies={"session": TEST_SESSION_ID})
    assert response.status_code == 200
    assert response.json() == {"message": "ok", "ms_oid": TEST_MS_OID_SESSION.decode("utf-8")}
