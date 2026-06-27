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
