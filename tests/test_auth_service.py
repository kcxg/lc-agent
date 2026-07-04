import pytest
from lc_agent.core.auth import AuthService


@pytest.fixture
def auth_service():
    return AuthService(secret="test-secret-key-minimum16chars", token_expire_days=7)


def test_hash_and_verify_password(auth_service):
    hashed = auth_service.hash_password("mypassword")
    assert auth_service.verify_password("mypassword", hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token(auth_service):
    token = auth_service.create_token(user_id="u123", username="alice", role="admin")
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "u123"
    assert payload["username"] == "alice"
    assert payload["role"] == "admin"


def test_expired_token(auth_service):
    svc = AuthService(secret="test-secret-key-minimum16chars", token_expire_days=-1)
    token = svc.create_token(user_id="u1", username="bob", role="user")
    assert svc.decode_token(token) is None


def test_invalid_token(auth_service):
    assert auth_service.decode_token("garbage.token.here") is None


def test_generate_random_password(auth_service):
    pw = auth_service.generate_random_password()
    assert len(pw) >= 12
    pw2 = auth_service.generate_random_password()
    assert pw != pw2


def test_secret_too_short():
    with pytest.raises(ValueError):
        AuthService(secret="short", token_expire_days=7)
