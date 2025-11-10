# Widget SSO Parent Website Setup Guide

This is a full-stack web application that serves as a parent website for embedding the Understand Tech widget with SSO authentication.

## Architecture

- **Frontend**: React + Vite (Port 5173)
- **Backend**: FastAPI + Python (Port 8000)
- **Authentication**: Microsoft OAuth 2.0

## Prerequisites

- Node.js (v16 or higher)
- Python 3.8 or higher
- Microsoft Azure account for OAuth app registration

## Step 1: Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Configure your app:
   - **Name**: Widget SSO Demo (or your preferred name)
   - **Supported account types**: Choose based on your needs (e.g., "Accounts in any organizational directory")
   - **Redirect URI**: 
     - Type: Web
     - URI: `http://localhost:8000/auth/callback`
4. After registration, note down:
   - **Application (client) ID**
   - **Directory (tenant) ID**
5. Create a client secret:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Add a description and choose expiry
   - **Copy the secret value immediately** (you won't be able to see it again)

## Step 2: Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from the example:
```bash
cp env.example .env
```

5. Edit `.env` and fill in your configuration:
```env
MICROSOFT_CLIENT_ID=your_application_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret_value
MICROSOFT_TENANT_ID=your_tenant_id_or_common
REDIRECT_URI=http://localhost:8000/auth/callback

# Generate a random secret for sessions (you can use: python -c "import secrets; print(secrets.token_urlsafe(32))")
SESSION_SECRET=your_random_secret_here
# Optional: override if you want a different signing key than SESSION_SECRET
JWT_SECRET=

# Widget API Configuration (Required for widget OTT exchange)
WIDGET_API_KEY=your_widget_api_key_from_understand_tech
UT_API_BASE_URL=https://staging.understand.tech  # or https://app.understand.tech for production

# Frontend URL (for CORS and redirects)
FRONTEND_URL=http://localhost:5173
```

6. Run the backend server:
```bash
python main.py
```

The backend should now be running at `http://localhost:8000`

## Step 3: Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend should now be running at `http://localhost:5173`

## Step 4: Test the Application

1. Open your browser and go to `http://localhost:5173`
2. You should see the login page
3. Click **"Sign in with Microsoft"**
4. You'll be redirected to Microsoft's login page
5. After successful authentication, you'll be redirected back to the home page
6. Open DevTools → Application → Cookies and confirm an `auth_token` cookie appears for the frontend origin
7. The home page displays:
   - Your name and email from Microsoft
   - A welcome message
   - A placeholder for the widget iframe (to be configured later)

## Step 5: Widget Integration

The widget OTT exchange is now fully implemented! To use it:

1. **Obtain your Widget API Key** from Understand Tech
2. **Add it to your backend `.env` file**:
   ```env
   WIDGET_API_KEY=your_actual_widget_api_key
   UT_API_BASE_URL=https://staging.understand.tech  # or production URL
   ```
3. **Update widget configuration** in `frontend/src/pages/Home.jsx`:
   - Change `WIDGET_URL` if needed
   - Change `MODEL_ID` to your assistant's model ID
4. **Restart both backend and frontend servers**
5. After login, the home page will:
   - Automatically fetch an OTT from your backend
   - Send it to the widget iframe via postMessage
   - The widget (UT side) exchanges the OTT for a session cookie
   - The widget is ready for authenticated chat interactions

## Architecture Flow

1. **Login Flow**:
   - User clicks "Sign in with Microsoft"
   - Frontend calls backend `/auth/login` to retrieve the Microsoft OAuth URL + CSRF state
   - User is redirected to Microsoft
   - After auth, Microsoft redirects to `/auth/callback`
   - Backend exchanges the code for tokens, builds a profile, and sets an `auth_token` JWT cookie (HttpOnly) for the frontend
   - User is redirected back to frontend home page

2. **Session Management**:
   - Backend stores auth state in the JWT cookie (no server database required for the demo)
   - Frontend makes authenticated requests with `credentials: 'include'` so the cookie is sent
   - Session persists until logout or until the JWT expires

3. **Widget OTT Exchange Flow** (fully implemented):
   - User authenticates via Microsoft SSO
   - Home page loads with widget iframe
   - Frontend calls backend `/widget/get-ott` with model_id and origin
   - Backend validates auth token and calls UT API `/widget/ott` with Widget API Key
   - UT API validates key, team, assistant, origin and returns signed OTT (60s TTL)
   - Frontend receives OTT and sends it to iframe via postMessage `{ type: 'UT_OTT', ott }`
   - Widget iframe (UT code) calls `/widget/exchange-ott` with credentials
   - UT API verifies OTT (signature, expiry, replay, origin) and sets HttpOnly session cookie
   - Widget is now authenticated and ready for chat interactions

## Project Structure

```
widget-sso/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── env.example         # Environment variables template
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx    # Login page component
│   │   │   ├── Login.css
│   │   │   ├── Home.jsx     # Home page component
│   │   │   └── Home.css
│   │   ├── App.jsx          # Main app component with routing
│   │   ├── App.css
│   │   ├── main.jsx         # Entry point
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .gitignore
├── README.md               # Widget SSO concept documentation
└── SETUP.md               # This file
```

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure virtual environment is activated and dependencies are installed
- **OAuth errors**: Verify your Microsoft app credentials in `.env`
- **CORS errors**: Check that `allow_origins` in `main.py` matches your frontend URL

### Frontend Issues

- **Can't connect to backend**: Ensure backend is running on port 8000
- **Login redirect fails**: Check that `REDIRECT_URI` in backend `.env` matches Azure app registration
- **Build errors**: Delete `node_modules` and run `npm install` again

### Authentication Issues

- **Redirect URI mismatch**: Make sure the redirect URI in Azure portal exactly matches the one in your `.env`
- **Tenant issues**: Try using "common" as `MICROSOFT_TENANT_ID` for multi-tenant support

## Development Notes

- Both servers must be running simultaneously
- Backend handles authentication and will handle widget OTT requests
- Frontend is a SPA with React Router
- Sessions are stored in-memory (use Redis or database for production)

## Production Deployment

For production:
1. Use proper session storage (Redis, database)
2. Set secure session secrets
3. Update CORS origins to production domains
4. Use HTTPS for all endpoints
5. Update Microsoft OAuth redirect URIs to production URLs
6. Enable secure cookies in production

## Next Steps

- Configure your Widget API Key when ready
- Customize the UI to match your brand
- Add error handling and user feedback
- Implement session persistence with Redis/database
- Add logging and monitoring

