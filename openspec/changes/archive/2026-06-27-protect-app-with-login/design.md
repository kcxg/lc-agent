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
