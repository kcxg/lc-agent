# Comet Design Handoff

- Change: protect-app-with-login
- Phase: design
- Mode: compact
- Context hash: 5b068822a58a151069cf0e18102451ff336d5a0f0178a44326f8998d0715c2f8

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/protect-app-with-login/proposal.md

- Source: openspec/changes/protect-app-with-login/proposal.md
- Lines: 1-30
- SHA256: 7844a29c667fe908b076c32cad0879e83bec6fd210d8e0c1de18774f366eedda

```md
## Why

lc-agent currently exposes the Web UI, API routes, and WebSocket endpoints without an application login gate. This makes local or self-hosted deployments too easy to access unintentionally when the service is shared beyond a trusted localhost-only environment.

## What Changes

- Add local administrator login using username and password.
- Load administrator credentials from configuration or environment variables.
- Issue an HttpOnly cookie-backed session after successful login.
- Require an authenticated session for the Web UI, `/api/*` routes, and WebSocket connections.
- Add logout and current-auth-state endpoints for the frontend.
- Add a frontend login view and route guard so unauthenticated users land on the login page.
- Do not add public registration, third-party OAuth, role-based permissions, or per-user data isolation in this change.

## Capabilities

### New Capabilities

- `app-authentication`: Login, logout, session persistence, and authenticated access enforcement for the lc-agent app.

### Modified Capabilities

None.

## Impact

- Backend FastAPI app setup, dependencies, middleware or route dependencies, and WebSocket handshake handling.
- Configuration schema and example configuration for administrator credentials and session settings.
- Frontend router, HTTP API wrapper, app initialization, and a new login view.
- Backend and frontend tests covering unauthenticated access, successful login, logout, and protected resource behavior.
```

## openspec/changes/protect-app-with-login/design.md

- Source: openspec/changes/protect-app-with-login/design.md
- Lines: 1-76
- SHA256: 726dfb4910524756cc23c6f691e741a0816c3474ae5e56d1d69e7c77a3069ea2

```md
## Context

The app currently creates a FastAPI application with public `/api` routers, public WebSocket entrypoints, and a Vue single-page UI without a login route or route guard. Existing data models store agent presets, chat sessions, and UI messages, but there is no user model.

The project is still in an early development stage, so this design avoids compatibility migrations and avoids building a broader user system before it is needed.

## Goals / Non-Goals

**Goals:**

- Gate the lc-agent app behind a local administrator login.
- Keep credentials configurable through config and environment-backed config values.
- Use an HttpOnly cookie session so frontend code does not store bearer tokens.
- Enforce authentication consistently for protected HTTP API routes and WebSocket connections.
- Add frontend login/logout flow and route protection.

**Non-Goals:**

- Public registration.
- OAuth or third-party identity providers.
- Role-based permissions.
- Per-user isolation of sessions, messages, tools, agents, or MCP configuration.
- Persistent user database tables.

## Decisions

### Use a single configured administrator identity

Credentials will come from the app configuration, with support for the existing environment substitution flow. The backend will validate one administrator username/password pair.

Alternative considered: add `users` and `sessions` database tables. That adds schema and migration work for a single-user access gate and conflicts with the explicit non-goal of multi-user behavior.

### Use signed HttpOnly cookie sessions

On successful login, the backend will set an HttpOnly, SameSite cookie containing a signed session value. The cookie will carry enough information to identify the administrator session and its expiry. The session secret and TTL will be configurable.

Alternative considered: JWT in localStorage or Pinia state. That exposes the token to frontend JavaScript and creates avoidable storage and refresh concerns.

### Centralize backend authentication checks

Authentication logic will live in a backend auth module and dependency/helper layer. Normal protected API routes will require the shared dependency. Login/logout and auth-state endpoints will be explicitly public. WebSocket connection setup will use the same session validation rule before accepting or processing chat traffic.

Alternative considered: add checks individually inside each route handler. That is easy to miss and makes future routers unsafe by default.

### Protect the UI through frontend route guards while allowing static assets

The backend must still serve static assets required to render the login page. The Vue router and app bootstrap will ask the backend for auth state, redirect unauthenticated users to `/login`, and prevent the main chat shell from initializing protected stores until authenticated.

Alternative considered: block every non-login static request at the server. In a single-page app this complicates asset delivery and can break the login screen itself.

### Keep logout server-authoritative

Logout will clear the session cookie server-side and the frontend will reset auth state before returning to the login page.

Alternative considered: frontend-only logout. That leaves the cookie valid and does not meet the access-control goal.

## Risks / Trade-offs

- Configured plaintext passwords can be mishandled -> encourage environment variables in examples and avoid logging credential values.
- Stateless signed sessions cannot be revoked individually before expiry -> keep TTL configurable and make logout clear the browser cookie. This is acceptable for the single-admin scope.
- Future multi-user support will require redesign -> keep auth helpers isolated so a later user database can replace credential/session validation without rewriting every route.
- Static assets remain fetchable before login -> application data and WebSocket behavior remain protected, and the UI only exposes the login flow before authentication.

## Migration Plan

1. Add auth configuration with disabled-by-default or explicit-credentials behavior that fails loudly when auth is enabled without required secrets.
2. Add backend auth endpoints and shared auth dependency/session helper.
3. Apply backend auth enforcement to protected API routers and WebSocket connection setup.
4. Add frontend auth API methods, store/state, login view, route guard, and logout control.
5. Add focused backend and frontend contract tests.

Rollback is removing the new auth config and auth enforcement changes before release; no persistent data migration is planned.

## Open Questions

None for the scoped single-admin version.
```

## openspec/changes/protect-app-with-login/tasks.md

- Source: openspec/changes/protect-app-with-login/tasks.md
- Lines: 1-21
- SHA256: b42686399edf486bb37cda6b1a23219f4d4d29d3ade9d31e8433f7fe8d88725e

```md
## 1. Backend Authentication

- [ ] 1.1 Add auth configuration fields and example config entries for administrator credentials, session secret, cookie name, and session TTL.
- [ ] 1.2 Implement backend auth helpers for credential verification, signed HttpOnly session creation, session validation, and cookie clearing.
- [ ] 1.3 Add login, logout, and auth-state HTTP endpoints.
- [ ] 1.4 Enforce authenticated sessions on protected API routers while keeping auth-flow endpoints reachable.
- [ ] 1.5 Enforce authenticated sessions during WebSocket connection setup.

## 2. Frontend Login Flow

- [ ] 2.1 Add auth API methods and frontend auth state.
- [ ] 2.2 Add a login view that submits credentials and handles failures without exposing sensitive details.
- [ ] 2.3 Add router/app guards so unauthenticated users see login and protected stores initialize only after authentication.
- [ ] 2.4 Add logout UI behavior that clears backend session state and returns to login.

## 3. Verification

- [ ] 3.1 Add backend tests for valid login, invalid login, logout, protected API rejection, and authenticated API access.
- [ ] 3.2 Add WebSocket authentication coverage for unauthenticated rejection and authenticated connection.
- [ ] 3.3 Add frontend contract/build coverage for login routing and auth-aware API behavior.
- [ ] 3.4 Run the relevant backend and frontend verification commands and record results.
```

## openspec/changes/protect-app-with-login/specs/app-authentication/spec.md

- Source: openspec/changes/protect-app-with-login/specs/app-authentication/spec.md
- Lines: 1-63
- SHA256: 830664585ee7565a83b40b05e626ded36409113b632e4942b8286d881fe740ec

```md
## ADDED Requirements

### Requirement: Configured administrator login
The system SHALL authenticate users with a configured administrator username and password before granting access to protected app functionality.

#### Scenario: Valid administrator credentials
- **WHEN** a user submits the configured administrator username and password
- **THEN** the system SHALL create an authenticated session and report login success

#### Scenario: Invalid credentials
- **WHEN** a user submits an unknown username or incorrect password
- **THEN** the system SHALL reject the login without creating an authenticated session

### Requirement: HttpOnly cookie session
The system SHALL persist successful login state using an HttpOnly cookie-backed session with a configurable expiry.

#### Scenario: Authenticated page refresh
- **WHEN** an authenticated user refreshes the browser before the session expires
- **THEN** the system SHALL keep the user authenticated without requiring credentials again

#### Scenario: Expired or missing session
- **WHEN** a request has no valid session cookie or the session is expired
- **THEN** the system SHALL treat the request as unauthenticated

### Requirement: Protected HTTP API access
The system SHALL require an authenticated session for protected `/api/*` endpoints while keeping login, logout, and auth-state endpoints reachable as needed for the login flow.

#### Scenario: Unauthenticated API request
- **WHEN** an unauthenticated client calls a protected API endpoint
- **THEN** the system SHALL reject the request with an unauthorized response

#### Scenario: Authenticated API request
- **WHEN** an authenticated client calls a protected API endpoint
- **THEN** the system SHALL process the request according to the endpoint behavior

### Requirement: Protected WebSocket access
The system SHALL require an authenticated session before accepting WebSocket chat traffic.

#### Scenario: Unauthenticated WebSocket connection
- **WHEN** an unauthenticated client attempts to connect to the WebSocket endpoint
- **THEN** the system SHALL reject or close the connection without starting a chat session

#### Scenario: Authenticated WebSocket connection
- **WHEN** an authenticated client connects to the WebSocket endpoint
- **THEN** the system SHALL allow the normal chat WebSocket flow

### Requirement: Login-gated frontend
The frontend SHALL route unauthenticated users to a login view and prevent the main chat application from initializing protected data until authentication succeeds.

#### Scenario: Opening the app without login
- **WHEN** a user opens the Web UI without a valid session
- **THEN** the frontend SHALL show the login view instead of the chat workspace

#### Scenario: Login success navigation
- **WHEN** a user logs in successfully from the login view
- **THEN** the frontend SHALL navigate to the intended chat route or the default chat route

### Requirement: Logout
The system SHALL provide logout behavior that clears the authenticated session and returns the user to the login flow.

#### Scenario: User logs out
- **WHEN** an authenticated user chooses logout
- **THEN** the backend SHALL clear the session cookie and the frontend SHALL return to the login view
```

