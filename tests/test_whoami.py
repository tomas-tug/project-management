import pytest
from fastapi.testclient import TestClient

# import the app module (assumes fastapi_ms_oid_reader.py placed at repo root)
import fastapi_ms_oid_reader as app_module


class FakeRedis:
    """A simple in-memory fake Redis client for testing."""

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
    """Fixture providing a FakeRedis with pre-populated session and user data."""
    store = {
        "shared:ms_oid_by_session:cookie123": b"ms-oid-123",
        "shared:ms_oid_by_user:42": b"ms-oid-42",
    }
    return FakeRedis(store=store)


@pytest.fixture
def mock_redis(monkeypatch, fake_redis):
    """Fixture that monkeypatches redis_client and redis module to use fake_redis."""
    monkeypatch.setattr(app_module, "redis_client", fake_redis)
    monkeypatch.setattr(
        "fastapi_ms_oid_reader.redis.from_url",
        lambda url, decode_responses=False: fake_redis,
    )
    monkeypatch.setattr(
        "fastapi_ms_oid_reader.redis.Redis", lambda *args, **kwargs: fake_redis
    )
    return fake_redis


def test_whoami_with_session_cookie(mock_redis):
    """Test /whoami returns ms_oid when session cookie is present and valid."""
    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": "cookie123"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-123"}


def test_whoami_with_user_id_header(mock_redis):
    """Test /whoami returns ms_oid when X-User-ID header is present and valid."""
    client = TestClient(app_module.app)
    response = client.get("/whoami", headers={"X-User-ID": "42"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-42"}


def test_whoami_with_user_id_cookie(mock_redis):
    """Test /whoami returns ms_oid when user_id cookie is present and valid."""
    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"user_id": "42"})
    assert response.status_code == 200
    assert response.json() == {"ms_oid": "ms-oid-42"}


def test_whoami_unauthorized_no_cookie(monkeypatch):
    """Test /whoami returns 401 when no session or user identification is provided."""
    # empty fake redis so no keys present
    empty_redis = FakeRedis(store={})
    monkeypatch.setattr(app_module, "redis_client", empty_redis)
    monkeypatch.setattr(
        "fastapi_ms_oid_reader.redis.from_url",
        lambda url, decode_responses=False: empty_redis,
    )
    monkeypatch.setattr(
        "fastapi_ms_oid_reader.redis.Redis", lambda *args, **kwargs: empty_redis
    )

    client = TestClient(app_module.app)
    response = client.get("/whoami")
    assert response.status_code == 401


def test_whoami_unauthorized_invalid_session(mock_redis):
    """Test /whoami returns 401 when session cookie is invalid."""
    client = TestClient(app_module.app)
    response = client.get("/whoami", cookies={"session": "invalid_cookie"})
    assert response.status_code == 401
