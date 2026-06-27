# app-authentication Specification

## Purpose
TBD - created by archiving change protect-app-with-login. Update Purpose after archive.
## Requirements
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

