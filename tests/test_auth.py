from datetime import datetime, timedelta, timezone

import pytest

from lc_agent.server.auth import (
    AuthConfigError,
    create_session_cookie,
    get_auth_config,
    validate_admin_credentials,
    validate_session_cookie,
)


def auth_config(**overrides):
    data = {
        "enabled": True,
        "admin_username": "admin",
        "admin_password": "secret",
        "session_secret": "test-session-secret",
        "cookie_name": "lc_agent_session",
        "session_ttl_seconds": 3600,
    }
    data.update(overrides)
    return {"auth": data}


def test_enabled_auth_requires_credentials_and_secret():
    with pytest.raises(AuthConfigError):
        get_auth_config({"auth": {"enabled": True, "admin_username": "admin"}})


def test_validate_admin_credentials_accepts_exact_configured_pair():
    settings = get_auth_config(auth_config())
    assert validate_admin_credentials(settings, "admin", "secret") is True
    assert validate_admin_credentials(settings, "admin", "wrong") is False
    assert validate_admin_credentials(settings, "other", "secret") is False


def test_signed_session_cookie_validates_until_expiry():
    settings = get_auth_config(auth_config(session_ttl_seconds=60))
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    cookie = create_session_cookie(settings, now=now)
    assert validate_session_cookie(settings, cookie, now=now + timedelta(seconds=59)) is True
    assert validate_session_cookie(settings, cookie, now=now + timedelta(seconds=61)) is False
