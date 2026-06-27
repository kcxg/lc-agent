---
change: protect-app-with-login
design-doc: docs/superpowers/specs/2026-06-27-protect-app-with-login-design.md
base-ref: efcedbd332b72dd24d3fa4d07da5fa50e801050e
---

# Protect App With Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-administrator login gate that protects lc-agent's Web UI data, HTTP API routes, and chat WebSocket endpoints.

**Architecture:** Implement a focused backend auth module with configured credentials and signed HttpOnly cookie sessions. Add public auth endpoints, protect existing business routers with a shared dependency, validate WebSocket cookies before accept, and add a Vue auth store/login route/route guard around the existing chat shell.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, httpx/pytest, Vue 3, TypeScript, Pinia, Vue Router, Element Plus, Node contract scripts.

## Global Constraints

- Do not add public registration, OAuth, RBAC, per-user data isolation, or persistent user tables.
- Do not add database migrations for this single-admin gate.
- Keep static assets loadable before login; protect app navigation, API data, and WebSocket traffic.
- Use HttpOnly cookie sessions; do not store bearer tokens in localStorage.
- Auth must fail loudly when enabled without required username, password, or session secret.
- Keep changes aligned with existing file layout and tests.

---

## File Structure

- Create `lc_agent/server/auth.py`: auth config normalization, credential verification, signed session creation/validation, cookie helpers, FastAPI dependency.
- Create `lc_agent/server/routes/auth.py`: `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`.
- Modify `lc_agent/config/schema.py`: add typed `AuthConfig`.
- Modify `lc_agent/server/app.py`: include auth router publicly and protect business routers when auth is enabled.
- Modify `lc_agent/app.py`: validate auth before accepting `/ws/chat` connections.
- Modify `config.example.jsonc`: document `auth` configuration with environment substitution.
- Create `tests/test_auth.py`: backend auth helper and route coverage.
- Modify or add WebSocket tests in `tests/test_ws_events.py` or `tests/test_auth.py`: unauthenticated rejection and authenticated connect.
- Modify existing route tests that instantiate auth-enabled apps only where needed; default auth disabled preserves current tests.
- Modify `frontend/src/api/http.ts`: credentials-aware fetch and auth methods.
- Create `frontend/src/stores/auth.ts`: auth state and login/logout/refresh actions.
- Modify `frontend/src/router/index.ts`: add `/login` route and route metadata.
- Create `frontend/src/views/LoginView.vue`: login form.
- Modify `frontend/src/App.vue`: auth-aware app initialization and login shell behavior.
- Modify `frontend/src/components/layout/AppHeader.vue`: logout control.
- Create `frontend/scripts/check-auth-contract.mjs`: static contract checks for auth routing/API behavior.
- Modify `frontend/package.json`: add `test:auth` script.

## Task 1: Backend Auth Core

**Files:**
- Create: `lc_agent/server/auth.py`
- Modify: `lc_agent/config/schema.py`
- Modify: `config.example.jsonc`
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces: `AuthConfig`, `get_auth_config(config: dict) -> AuthSettings`, `create_session_cookie(settings, now=None) -> str`, `validate_session_cookie(settings, value, now=None) -> bool`, `set_auth_cookie(response, settings) -> None`, `clear_auth_cookie(response, settings) -> None`, `require_auth(request: Request) -> None`.
- Consumes: existing `request.app.state.config`.

- [x] **Step 1: Write failing backend auth tests**

Add tests that prove enabled auth requires credentials and secrets, valid credentials create a valid cookie, wrong credentials fail, and expired cookies are invalid.

```python
# tests/test_auth.py
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
```

- [x] **Step 2: Run tests and verify they fail**

Run: `uv run --extra dev python -m pytest tests/test_auth.py -q`

Expected: import errors for `lc_agent.server.auth` or missing functions.

- [x] **Step 3: Implement minimal auth config and cookie helpers**

Create `lc_agent/server/auth.py` with:

```python
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
    if settings.enabled and (not settings.admin_username or not settings.admin_password or not settings.session_secret):
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
        return payload.get("sub") == settings.admin_username and int(payload.get("exp", 0)) > int(current.timestamp())
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
```

Modify `lc_agent/config/schema.py`:

```python
class AuthConfig(BaseModel):
    enabled: bool = False
    admin_username: str = ""
    admin_password: str = ""
    session_secret: str = ""
    cookie_name: str = "lc_agent_session"
    session_ttl_seconds: int = 60 * 60 * 8
    cookie_secure: bool = False
```

Then add this field inside the existing `AppConfig` class near the other top-level config sections:

```python
class AppConfig(BaseModel):
    auth: AuthConfig = Field(default_factory=AuthConfig)
```

Add an `auth` block to `config.example.jsonc`. Keep disabled-auth defaults loadable with empty sensitive values, and document that enabled auth can use `{env:LC_AGENT_ADMIN_PASSWORD}` and `{env:LC_AGENT_SESSION_SECRET}`.

- [x] **Step 4: Run tests and verify they pass**

Run: `uv run --extra dev python -m pytest tests/test_auth.py -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add lc_agent/server/auth.py lc_agent/config/schema.py config.example.jsonc tests/test_auth.py
git commit -m "feat: add auth session helpers"
```

## Task 2: Backend Auth Routes And HTTP Protection

**Files:**
- Create: `lc_agent/server/routes/auth.py`
- Modify: `lc_agent/server/app.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: Task 1 auth helpers.
- Produces: `router` in `lc_agent.server.routes.auth`; protected routers use `Depends(require_auth)` only when auth is enabled.

- [x] **Step 1: Write failing route tests**

Extend `tests/test_auth.py`:

```python
from httpx import ASGITransport, AsyncClient

from lc_agent.server.app import create_app


def protected_config():
    return auth_config()


async def test_login_logout_and_me_flow():
    app = create_app(protected_config())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth = await client.get("/api/auth/me")
        assert unauth.status_code == 200
        assert unauth.json()["authenticated"] is False

        bad = await client.post("/api/auth/login", json={"username": "admin", "password": "bad"})
        assert bad.status_code == 401

        login = await client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
        assert login.status_code == 200
        assert login.json()["authenticated"] is True
        assert "lc_agent_session" in client.cookies

        me = await client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["authenticated"] is True

        logout = await client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert client.cookies.get("lc_agent_session") in (None, "")


async def test_protected_api_rejects_unauthenticated_requests():
    app = create_app(protected_config())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sessions")
        assert resp.status_code == 401


async def test_protected_api_accepts_authenticated_requests():
    app = create_app(protected_config())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
        resp = await client.get("/api/tools")
        assert resp.status_code == 200
```

- [x] **Step 2: Run tests and verify they fail**

Run: `uv run --extra dev python -m pytest tests/test_auth.py -q`

Expected: failures for missing auth routes, unprotected `/api/sessions`, and missing authenticated `/api/tools` access.

- [x] **Step 3: Add auth router**

Create `lc_agent/server/routes/auth.py`:

```python
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from lc_agent.server.auth import (
    clear_auth_cookie,
    get_auth_config,
    is_request_authenticated,
    set_auth_cookie,
    validate_admin_credentials,
)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/auth/me")
async def auth_state(request: Request):
    settings = get_auth_config(request.app.state.config)
    authenticated = is_request_authenticated(request)
    return {"authenticated": authenticated, "username": settings.admin_username if authenticated and settings.enabled else ""}


@router.post("/auth/login")
async def login(body: LoginRequest, request: Request, response: Response):
    settings = get_auth_config(request.app.state.config)
    if not settings.enabled:
        return {"authenticated": True, "username": ""}
    if not validate_admin_credentials(settings, body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    set_auth_cookie(response, settings)
    return {"authenticated": True, "username": settings.admin_username}


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    settings = get_auth_config(request.app.state.config)
    clear_auth_cookie(response, settings)
    return {"authenticated": False}
```

Modify `lc_agent/server/app.py` to include auth router publicly and protected routers with dependency:

```python
from fastapi import Depends
from lc_agent.server.auth import get_auth_config, require_auth
from lc_agent.server.routes.auth import router as auth_router

auth_settings = get_auth_config(config)
protected_dependencies = [Depends(require_auth)] if auth_settings.enabled else []

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(tools_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(models_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(agents_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(sessions_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(skills_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(mcp_router, prefix="/api", dependencies=protected_dependencies)
```

Keep `/api/health` public so deployments can still perform health checks.

- [x] **Step 4: Run route tests**

Run: `uv run --extra dev python -m pytest tests/test_auth.py tests/test_server.py -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add lc_agent/server/routes/auth.py lc_agent/server/app.py tests/test_auth.py
git commit -m "feat: add auth routes and api protection"
```

## Task 3: WebSocket Authentication

**Files:**
- Modify: `lc_agent/app.py`
- Test: `tests/test_auth.py` or `tests/test_ws_events.py`

**Interfaces:**
- Consumes: `is_request_authenticated(request)` or a WebSocket-compatible cookie validator from Task 1.
- Produces: `/ws/chat` and `/ws/chat/{thread_id}` reject unauthenticated connections when auth is enabled.

- [x] **Step 1: Write failing WebSocket tests**

Add tests that connect without a cookie and expect rejection, then login and connect with the returned cookie.

```python
import pytest
from fastapi.testclient import TestClient

from lc_agent.app import LcAgentApp


def test_websocket_rejects_unauthenticated_client():
    app = LcAgentApp(protected_config()).fastapi_app
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chat"):
            pass


def test_websocket_accepts_authenticated_client():
    app = LcAgentApp(protected_config()).fastapi_app
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert login.status_code == 200
    with client.websocket_connect("/ws/chat") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connected"
        assert connected["thread_id"]
```

- [x] **Step 2: Run tests and verify unauthenticated case fails**

Run: `uv run --extra dev python -m pytest tests/test_auth.py -q`

Expected: unauthenticated WebSocket currently connects.

- [x] **Step 3: Implement WebSocket auth gate**

In `lc_agent/server/auth.py`, add:

```python
from fastapi import WebSocket


def is_websocket_authenticated(websocket: WebSocket) -> bool:
    settings = get_auth_config(websocket.app.state.config)
    if not settings.enabled:
        return True
    return validate_session_cookie(settings, websocket.cookies.get(settings.cookie_name))
```

In `lc_agent/app.py`, before each call to `self._ws_handler.connect`:

```python
from lc_agent.server.auth import is_websocket_authenticated

if not is_websocket_authenticated(websocket):
    await websocket.close(code=1008)
    return
```

Apply this to both `/ws/chat/{thread_id}` and `/ws/chat`.

- [x] **Step 4: Run WebSocket tests**

Run: `uv run --extra dev python -m pytest tests/test_auth.py -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add lc_agent/server/auth.py lc_agent/app.py tests/test_auth.py
git commit -m "feat: protect chat websocket"
```

## Task 4: Frontend Auth API, Store, And Routing

**Files:**
- Modify: `frontend/src/api/http.ts`
- Create: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/router/index.ts`
- Create: `frontend/src/views/LoginView.vue`
- Test: `frontend/scripts/check-auth-contract.mjs`
- Modify: `frontend/package.json`

**Interfaces:**
- Produces: `useAuthStore()` with `initialized`, `authenticated`, `username`, `refreshAuth()`, `login(username, password)`, `logout()`.
- Produces: `api.login`, `api.logout`, `api.getAuthState`.

- [x] **Step 1: Write failing frontend contract script**

Create `frontend/scripts/check-auth-contract.mjs`:

```javascript
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = path => readFileSync(join(root, path), 'utf8')

const files = {
  http: read('src/api/http.ts'),
  router: read('src/router/index.ts'),
  authStore: read('src/stores/auth.ts'),
  loginView: read('src/views/LoginView.vue'),
}

const failures = []
function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}
function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

expectIncludes('http.ts', files.http, "credentials: 'same-origin'")
expectIncludes('http.ts', files.http, "login:")
expectIncludes('http.ts', files.http, "logout:")
expectIncludes('http.ts', files.http, "getAuthState:")
expectIncludes('router/index.ts', files.router, "path: '/login'")
expectIncludes('router/index.ts', files.router, 'beforeEach')
expectIncludes('auth.ts', files.authStore, "defineStore('auth'")
expectIncludes('auth.ts', files.authStore, 'async function refreshAuth()')
expectIncludes('auth.ts', files.authStore, 'async function login(')
expectIncludes('auth.ts', files.authStore, 'async function logout()')
expectMatch('LoginView.vue', files.loginView, /<el-form[\s\S]*@submit\.prevent=/, '应使用表单提交登录')

if (failures.length > 0) {
  console.error('认证前端契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}
console.log('认证前端契约测试通过')
```

Add to `frontend/package.json`:

```json
"test:auth": "node scripts/check-auth-contract.mjs"
```

- [x] **Step 2: Run contract and verify it fails**

Run from `frontend/`: `npm run test:auth`

Expected: missing files or missing auth API/router/store markers.

- [x] **Step 3: Implement auth API and store**

In `frontend/src/api/http.ts`, ensure fetch includes credentials:

```typescript
const response = await fetch(`${BASE_URL}${path}`, {
  credentials: 'same-origin',
  headers: { 'Content-Type': 'application/json' },
  ...options,
})
```

Add API methods:

```typescript
getAuthState: () => fetchApi<{ authenticated: boolean; username: string }>('/auth/me'),
login: (data: { username: string; password: string }) =>
  fetchApi<{ authenticated: boolean; username: string }>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
logout: () => fetchApi<{ authenticated: boolean }>('/auth/logout', { method: 'POST' }),
```

Create `frontend/src/stores/auth.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const initialized = ref(false)
  const authenticated = ref(false)
  const username = ref('')

  async function refreshAuth() {
    try {
      const state = await api.getAuthState()
      authenticated.value = state.authenticated
      username.value = state.username || ''
    } catch {
      authenticated.value = false
      username.value = ''
    } finally {
      initialized.value = true
    }
  }

  async function login(name: string, password: string) {
    const result = await api.login({ username: name, password })
    authenticated.value = result.authenticated
    username.value = result.username || ''
    initialized.value = true
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      authenticated.value = false
      username.value = ''
      initialized.value = true
    }
  }

  function markUnauthenticated() {
    authenticated.value = false
    username.value = ''
    initialized.value = true
  }

  return { initialized, authenticated, username, refreshAuth, login, logout, markUnauthenticated }
})
```

- [x] **Step 4: Implement route guard and login view**

Add `/login` route in `frontend/src/router/index.ts`; use a dynamic import for `LoginView.vue`. Add route meta and `beforeEach` guard that calls `useAuthStore().refreshAuth()` when uninitialized, then redirects unauthenticated users to login with `redirect` query.

Create `frontend/src/views/LoginView.vue` with an Element Plus form for username/password, error message on failed login, and redirect-after-login behavior.

- [x] **Step 5: Run frontend contract**

Run from `frontend/`: `npm run test:auth`

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add frontend/src/api/http.ts frontend/src/stores/auth.ts frontend/src/router/index.ts frontend/src/views/LoginView.vue frontend/scripts/check-auth-contract.mjs frontend/package.json
git commit -m "feat: add frontend login flow"
```

## Task 5: Auth-Aware App Shell And Logout UI

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/layout/AppHeader.vue`
- Modify: `frontend/scripts/check-auth-contract.mjs`

**Interfaces:**
- Consumes: `useAuthStore()`.
- Produces: app store initialization only after authenticated state; `logout` event from `AppHeader.vue`.

- [x] **Step 1: Extend frontend contract**

Add checks to `frontend/scripts/check-auth-contract.mjs`:

```javascript
files.app = read('src/App.vue')
files.header = read('src/components/layout/AppHeader.vue')

expectIncludes('App.vue', files.app, 'useAuthStore')
expectIncludes('App.vue', files.app, 'authStore.authenticated')
expectIncludes('App.vue', files.app, 'async function handleLogout()')
expectIncludes('AppHeader.vue', files.header, 'logout: []')
expectIncludes('AppHeader.vue', files.header, "@click=\"$emit('logout')\"")
```

- [x] **Step 2: Run contract and verify it fails**

Run from `frontend/`: `npm run test:auth`

Expected: failures for missing app/header auth behavior.

- [x] **Step 3: Gate app initialization**

In `frontend/src/App.vue`:

- import `useAuthStore`,
- initialize `authStore`,
- call protected store initialization only when `authStore.authenticated` is true,
- skip chat shell rendering for `/login`,
- add `handleLogout()` that disconnects chat, calls `authStore.logout()`, and routes to login.

Keep existing session restore behavior intact inside the authenticated branch.

- [x] **Step 4: Add logout control**

In `frontend/src/components/layout/AppHeader.vue`, add a compact icon or text button in the right header area that emits `logout`. Prefer an Element Plus icon button with a tooltip if an existing icon is available.

- [x] **Step 5: Run frontend verification**

Run from `frontend/`:

```bash
npm run test:auth
npm run build
```

Expected: both PASS.

- [x] **Step 6: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/layout/AppHeader.vue frontend/scripts/check-auth-contract.mjs
git commit -m "feat: gate app shell behind login"
```

## Task 6: Final Integration Verification

**Files:**
- Modify: `openspec/changes/protect-app-with-login/tasks.md`
- Modify only if required by findings: files touched in earlier tasks.

**Interfaces:**
- Consumes: all tasks.
- Produces: checked OpenSpec task list and verification evidence.

- [x] **Step 1: Run focused backend tests**

Run:

```bash
uv run --extra dev python -m pytest tests/test_auth.py tests/test_server.py -q
```

Expected: PASS.

- [x] **Step 2: Run Python lint**

Run:

```bash
ruff check lc_agent tests
```

Expected: PASS.

- [x] **Step 3: Run frontend auth checks**

Run from `frontend/`:

```bash
npm run test:auth
npm run build
```

Expected: PASS.

- [x] **Step 4: Update OpenSpec task checklist**

Mark completed items in `openspec/changes/protect-app-with-login/tasks.md` only after the relevant tests pass. If automatic code review is skipped by user choice later, record the skip reason in a durable comment in `tasks.md`.

- [x] **Step 5: Commit final checklist update**

```bash
git add openspec/changes/protect-app-with-login/tasks.md
git commit -m "chore: record auth implementation verification"
```

## Self-Review

- Spec coverage: configured admin login, HttpOnly session, protected HTTP API, protected WebSocket, login-gated frontend, and logout are each covered by tasks.
- Placeholder scan: no incomplete placeholder steps are intentionally left.
- Type consistency: backend helper names and frontend store/API names are introduced before consumers rely on them.
