# Backend API

FastAPI service that powers Microsoft SSO and the Understand Tech widget OTT exchange.

## Quick Start

```bash
# from widget-sso/backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# copy the sample env (see list below) and fill in secrets
cp env.example .env
${EDITOR:-nano} .env

# run in development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# or run the script entry point (no autoreload)
python main.py
```

Server listens on `http://localhost:8000`. Update `FRONTEND_URL` in `.env` if your frontend uses a different origin.

## Required Environment Variables

Create `.env` using the keys below. Everything marked **(required)** must be set for Microsoft SSO + widget OTT to work.

| Variable | Required | Description |
| --- | --- | --- |
| `MICROSOFT_CLIENT_ID` | Yes | App registration client ID from Azure AD |
| `MICROSOFT_CLIENT_SECRET` | Yes | Client secret value for the Azure app |
| `MICROSOFT_TENANT_ID` | Yes | Tenant ID (`common` works for multi-tenant) |
| `REDIRECT_URI` | Yes | Must match the redirect configured in Azure (e.g. `http://localhost:8000/auth/callback`) |
| `FRONTEND_URL` | Yes | URL the backend should redirect to after login (e.g. `http://localhost:5173`) |
| `SESSION_SECRET` | Yes | Random string used by FastAPI session middleware fallback |
| `JWT_SECRET` | Optional | Override for the JWT signing secret (defaults to `SESSION_SECRET`) |
| `WIDGET_API_KEY` | Yes | Understand Tech Widget API key (kept server-side) |
| `UT_API_BASE_URL` | Yes | Understand Tech API base (`https://staging.understand.tech` or `https://app.understand.tech`) |

> Tip: Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Authentication & Tokens

- The backend issues an `auth_token` cookie (JWT) after the Microsoft OAuth callback. Cookies are `HttpOnly`, `SameSite=None`, and `Secure` (for HTTPS).
- Every authenticated request calls `verify_jwt_token` to decode the token and pull user details.
- When the frontend hits `/widget/get-ott`, the backend validates the cookie, calls the Understand Tech API with the Widget API key, and returns the OTT payload (`ott`, `expires_in`) to the browser.

## API Endpoints

### Authentication

- `GET /auth/login` – Generate Microsoft OAuth URL + CSRF state token.
- `GET /auth/callback` – Exchange auth code, mint JWT, and redirect to `FRONTEND_URL`.
- `GET /auth/user` – Read user profile data from the JWT cookie.
- `POST /auth/logout` – Expire the auth cookie.

### Widget Integration

- `POST /widget/get-ott` – Authenticated OTT broker. Expects JSON `{ "model_id": "...", "origin": "https://..." }`.

## Additional Notes

- CORS `allow_origins` defaults to local dev + staging + production widget domains; edit `main.py` if you need more.
- Session state lives entirely in the JWT cookie—no external store required for the demo. For production, plan on rotating secrets and using persistent storage.
- The OTT request prints verbose logs (with masked key previews) to help during integration testing. Reduce logging once you move beyond sandbox environments.
# Backend API

FastAPI service that powers Microsoft SSO and the Understand Tech widget OTT exchange.

## Quick Start

```bash
# from widget-sso/backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# copy the sample env (see list below) and fill in secrets
cp env.example .env
${EDITOR:-nano} .env

# run in development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# or run the script entry point (no autoreload)
python main.py
```

Server listens on `http://localhost:8000`. Update `FRONTEND_URL` in `.env` if your frontend uses a different origin.

## Required Environment Variables

Create `.env` using the keys below. Everything marked **(required)** must be set for Microsoft SSO + widget OTT to work.

| Variable | Required | Description |
| --- | --- | --- |
| `MICROSOFT_CLIENT_ID` | Yes | App registration client ID from Azure AD |
| `MICROSOFT_CLIENT_SECRET` | Yes | Client secret value for the Azure app |
| `MICROSOFT_TENANT_ID` | Yes | Tenant ID (`common` works for multi-tenant) |
| `REDIRECT_URI` | Yes | Must match the redirect configured in Azure (e.g. `http://localhost:8000/auth/callback`) |
| `FRONTEND_URL` | Yes | URL the backend should redirect to after login (e.g. `http://localhost:5173`) |
| `SESSION_SECRET` | Yes | Random string used by FastAPI session middleware fallback |
| `JWT_SECRET` | Optional | Override for the JWT signing secret (defaults to `SESSION_SECRET`) |
| `WIDGET_API_KEY` | Yes | Understand Tech Widget API key (kept server-side) |
| `UT_API_BASE_URL` | Yes | Understand Tech API base (`https://staging.understand.tech` or `https://app.understand.tech`) |

> Tip: Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Authentication & Tokens

- The backend issues an `auth_token` cookie (JWT) after the Microsoft OAuth callback. Cookies are `HttpOnly`, `SameSite=None`, and `Secure` (for HTTPS).
- Every authenticated request calls `verify_jwt_token` to decode the token and pull user details.
- When the frontend hits `/widget/get-ott`, the backend validates the cookie, calls the Understand Tech API with the Widget API key, and returns the OTT payload (`ott`, `expires_in`) to the browser.

## API Endpoints

### Authentication

- `GET /auth/login` – Generate Microsoft OAuth URL + CSRF state token.
- `GET /auth/callback` – Exchange auth code, mint JWT, and redirect to `FRONTEND_URL`.
- `GET /auth/user` – Read user profile data from the JWT cookie.
- `POST /auth/logout` – Expire the auth cookie.

### Widget Integration

- `POST /widget/get-ott` – Authenticated OTT broker. Expects JSON `{ "model_id": "...", "origin": "https://..." }`.

## Additional Notes

- CORS `allow_origins` defaults to local dev + staging + production widget domains; edit `main.py` if you need more.
- Session state lives entirely in the JWT cookie—no external store required for the demo. For production, plan on rotating secrets and using persistent storage.
- The OTT request prints verbose logs (with masked key previews) to help during integration testing. Reduce logging once you move beyond sandbox environments.
# Backend API

FastAPI backend for Widget SSO parent website.

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your credentials

# Run server
python main.py
```

Server runs at `http://localhost:8080`

## API Endpoints

### Authentication

- `GET /auth/login` - Get Microsoft OAuth URL
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/user` - Get current user info
- `POST /auth/logout` - Logout current user

### Widget Integration

- `POST /widget/get-ott` - Get One-Time Token for widget (requires authentication)

## Environment Variables

See `env.example` for all required configuration.

