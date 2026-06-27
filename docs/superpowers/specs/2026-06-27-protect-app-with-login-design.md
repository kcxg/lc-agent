---
comet_change: protect-app-with-login
role: technical-design
canonical_spec: openspec
---

# Protect App With Login Design

## Context

lc-agent currently exposes its Vue Web UI, `/api/*` routes, and `/ws/chat` WebSocket endpoints without an application-level login gate. The existing backend already centralizes FastAPI app creation in `lc_agent/server/app.py`, WebSocket route registration in `LcAgentApp._setup_websocket_route()`, and request dependencies in `lc_agent/server/dependencies.py`. The frontend has a small router with chat routes and initializes protected data stores from `App.vue`.

This change adds a single-administrator login gate. It intentionally does not introduce a user database, registration, OAuth, roles, or per-user data isolation.

## Confirmed Approach

Use a configured administrator identity with a signed HttpOnly cookie session.

Backend responsibilities:

- Add an isolated auth module for configuration parsing, credential verification, session signing, session validation, and cookie clearing.
- Add public auth endpoints under `/api/auth`: `login`, `logout`, and `me`.
- Protect existing business API routers through a shared FastAPI dependency.
- Validate the same session cookie before accepting chat WebSocket connections.
- Fail loudly when auth is enabled but required credentials or session secret are missing.

Frontend responsibilities:

- Add an auth API surface and auth state store.
- Add a `/login` route and login view.
- Add route/app guards so unauthenticated users see the login view and protected stores initialize only after authentication succeeds.
- Add logout behavior that calls the backend, clears frontend auth state, and returns to login.

## Backend Design

### Configuration

Add an `auth` configuration section to `AppConfig` and `config.example.jsonc`.

Expected fields:

- `enabled`: whether app authentication is active.
- `admin_username`: configured administrator username.
- `admin_password`: configured administrator password, intended to be supplied through environment substitution.
- `session_secret`: secret used to sign session cookies, intended to be supplied through environment substitution.
- `cookie_name`: session cookie name, with a stable default.
- `session_ttl_seconds`: session lifetime.
- `cookie_secure`: whether to mark the cookie as Secure.

When `enabled` is false, existing behavior remains public. When `enabled` is true, missing username, password, or session secret is a startup/configuration error.

### Session Format

Use a signed cookie value containing the administrator subject and expiry timestamp. The backend validates:

- signature is valid,
- subject matches the configured administrator,
- expiry has not passed.

The cookie is HttpOnly and SameSite=Lax. The frontend never reads the session value.

### HTTP Enforcement

Add an auth router separately from existing business routers. Existing routers such as tools, models, agents, sessions, skills, and MCP are included with the auth dependency when authentication is enabled. Public auth endpoints remain dependency-free so the login flow can work.

The dependency returns normally for authenticated requests and raises 401 for missing, invalid, or expired sessions.

### WebSocket Enforcement

`LcAgentApp._setup_websocket_route()` validates the incoming WebSocket request cookie before calling `ChatWebSocketHandler.connect()`. If validation fails, the route closes the WebSocket and does not start the chat loop.

This keeps `ChatWebSocketHandler` focused on chat behavior and avoids mixing authentication with streaming logic.

## Frontend Design

### Auth State

Add a small Pinia auth store that tracks:

- `initialized`,
- `authenticated`,
- optional administrator identity display value,
- login/logout actions,
- `refreshAuth()` backed by `/api/auth/me`.

HTTP calls should use same-origin credentials by default. On 401 from protected APIs, the frontend clears auth state and routes to login.

### Routing

Add `/login` to the Vue router. A global route guard checks auth state:

- unauthenticated access to `/` or `/c/:sessionId` redirects to `/login` with the intended path recorded,
- authenticated access to `/login` redirects to the intended target or home.

`App.vue` should avoid initializing tools, agents, and sessions until auth initialization succeeds and the user is authenticated. The login page is the only unauthenticated app view.

### Logout

Logout calls `/api/auth/logout`, clears frontend auth state, disconnects any active chat WebSocket, and routes to `/login`.

## Alternatives Considered

### Server-side session table

Rejected for this change. It enables revocation and auditing but introduces schema and migration work for a single-admin gate.

### Browser-stored bearer token

Rejected. It makes the token readable by frontend JavaScript and weakens logout semantics compared with an HttpOnly cookie.

### Blocking all static assets server-side

Rejected. The single-page login view needs static assets to render. The protected surface is API data, WebSocket traffic, and authenticated app navigation.

## Risks And Mitigations

- Plaintext configured passwords can be mishandled: examples should use environment substitution, and backend logs must never print credential values.
- Stateless signed sessions cannot be individually revoked before expiry: keep TTL configurable and clear the browser cookie on logout.
- Future multi-user support will need a different model: keep auth logic isolated so credential and session validation can later be replaced without changing every route.
- Existing tests may expect public API access: update tests intentionally to authenticate when exercising protected behavior.

## Test Strategy

Backend tests:

- valid login sets a session cookie,
- invalid login returns unauthorized without setting a session,
- `/api/auth/me` reports authenticated and unauthenticated states correctly,
- logout clears the session cookie,
- protected API rejects unauthenticated requests,
- protected API works with a valid session cookie,
- WebSocket connection is rejected without a valid session and succeeds with one.

Frontend checks:

- unauthenticated navigation to `/` or `/c/:sessionId` lands on `/login`,
- successful login returns to the intended route,
- protected store initialization waits for auth success,
- logout returns to login,
- 401 responses clear auth state and route to login.

## Scope Boundary

This design deliberately does not change how sessions, messages, agent presets, tools, MCP servers, or skills are owned. After login, all existing app data remains shared within the single administrator context.
