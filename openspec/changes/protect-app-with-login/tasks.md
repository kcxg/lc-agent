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
