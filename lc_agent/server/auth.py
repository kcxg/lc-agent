from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request, Response, status


class AuthConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthSettings:
    enabled: bool = False
    admin_username: str = ""
    admin_password: str = ""
    session_secret: str = ""
    cookie_name: str = "lc_agent_session"
    session_ttl_seconds: int = 60 * 60 * 8
    cookie_secure: bool = False


def get_auth_config(config: dict[str, Any]) -> AuthSettings:
    raw = config.get("auth") or {}
    settings = AuthSettings(
        enabled=bool(raw.get("enabled", False)),
        admin_username=str(raw.get("admin_username", "")),
        admin_password=str(raw.get("admin_password", "")),
        session_secret=str(raw.get("session_secret", "")),
        cookie_name=str(raw.get("cookie_name", "lc_agent_session")),
        session_ttl_seconds=int(raw.get("session_ttl_seconds", 60 * 60 * 8)),
        cookie_secure=bool(raw.get("cookie_secure", False)),
    )
    if settings.enabled and (
        not settings.admin_username
        or not settings.admin_password
        or not settings.session_secret
    ):
        raise AuthConfigError("auth.enabled requires admin_username, admin_password, and session_secret")
    return settings


def validate_admin_credentials(settings: AuthSettings, username: str, password: str) -> bool:
    return secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(
        password,
        settings.admin_password,
    )


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(settings: AuthSettings, payload: str) -> str:
    digest = hmac.new(settings.session_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_session_cookie(settings: AuthSettings, *, now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    payload = {
        "sub": settings.admin_username,
        "exp": int(current.timestamp()) + settings.session_ttl_seconds,
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{encoded}.{_sign(settings, encoded)}"


def validate_session_cookie(settings: AuthSettings, value: str | None, *, now: datetime | None = None) -> bool:
    if not value:
        return False
    try:
        encoded, signature = value.split(".", 1)
        if not secrets.compare_digest(signature, _sign(settings, encoded)):
            return False
        payload = json.loads(_b64decode(encoded))
        current = now or datetime.now(timezone.utc)
        return payload.get("sub") == settings.admin_username and int(payload.get("exp", 0)) > int(
            current.timestamp()
        )
    except Exception:
        return False


def set_auth_cookie(response: Response, settings: AuthSettings) -> None:
    response.set_cookie(
        settings.cookie_name,
        create_session_cookie(settings),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response, settings: AuthSettings) -> None:
    response.delete_cookie(settings.cookie_name, path="/")


def is_request_authenticated(request: Request) -> bool:
    settings = get_auth_config(request.app.state.config)
    if not settings.enabled:
        return True
    return validate_session_cookie(settings, request.cookies.get(settings.cookie_name))


async def require_auth(request: Request) -> None:
    if not is_request_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
