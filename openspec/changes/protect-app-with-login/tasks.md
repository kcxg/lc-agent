## 1. Backend Authentication

- [x] 1.1 Add auth configuration fields and example config entries for administrator credentials, session secret, cookie name, and session TTL.
- [x] 1.2 Implement backend auth helpers for credential verification, signed HttpOnly session creation, session validation, and cookie clearing.
- [x] 1.3 Add login, logout, and auth-state HTTP endpoints.
- [x] 1.4 Enforce authenticated sessions on protected API routers while keeping auth-flow endpoints reachable.
- [x] 1.5 Enforce authenticated sessions during WebSocket connection setup.

## 2. Frontend Login Flow

- [x] 2.1 Add auth API methods and frontend auth state.
- [x] 2.2 Add a login view that submits credentials and handles failures without exposing sensitive details.
- [x] 2.3 Add router/app guards so unauthenticated users see login and protected stores initialize only after authentication.
- [x] 2.4 Add logout UI behavior that clears backend session state and returns to login.

## 3. Verification

- [x] 3.1 Add backend tests for valid login, invalid login, logout, protected API rejection, and authenticated API access.
- [x] 3.2 Add WebSocket authentication coverage for unauthenticated rejection and authenticated connection.
- [ ] 3.3 Add frontend contract/build coverage for login routing and auth-aware API behavior.
- [ ] 3.4 Run the relevant backend and frontend verification commands and record results.

Task 6 verification note (2026-06-27):
- `uv run --extra dev python -m pytest tests/test_auth.py tests/test_server.py -q`: passed, 13 passed and 4 dependency deprecation warnings.
- `ruff check lc_agent tests`: failed to start, `zsh:1: command not found: ruff`.
- `frontend/ npm run test:auth`: passed, `认证前端契约测试通过`.
- `frontend/ npm run build`: failed, `sh: vue-tsc: command not found`.
