from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
import httpx
import os
from dotenv import load_dotenv
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional

load_dotenv()

app = FastAPI()

# Session middleware for storing auth state
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://staging.understand.tech", "https://app.understand.tech" , "https://frontend-lovat-pi-76.vercel.app"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Microsoft OAuth configuration
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# JWT configuration for stateless auth (works with Vercel serverless)
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SESSION_SECRET", secrets.token_urlsafe(32)))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Widget API configuration (for future OTT requests)
WIDGET_API_KEY = os.getenv("WIDGET_API_KEY")
UT_API_BASE_URL = os.getenv("UT_API_BASE_URL")


def create_jwt_token(user_data: dict) -> str:
    """Create JWT token for user authentication"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user": user_data,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@app.get("/")
async def root():
    return {"message": "Parent Website Backend"}


@app.get("/auth/login")
async def login(request: Request):
    """Initiate Microsoft OAuth flow"""
    # Generate a cryptographically secure state token
    # We'll verify this on callback to prevent CSRF
    state = secrets.token_urlsafe(32)
    
    auth_url = (
        f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?"
        f"client_id={MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope=openid email profile"
        f"&state={state}"
    )
    
    return {"auth_url": auth_url, "state": state}


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None):
    """Handle Microsoft OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    # Verify state exists and is sufficiently long (basic CSRF protection)
    # In serverless, we can't store state in session, so we verify it's a valid format
    if not state or len(state) < 32:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for token
    token_url = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    # Get user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    user_data = user_response.json()
    
    # Create user info
    user_info = {
        "email": user_data.get("mail") or user_data.get("userPrincipalName"),
        "name": user_data.get("displayName"),
        "id": user_data.get("id"),
    }
    
    # Create JWT token instead of session (for serverless compatibility)
    token = create_jwt_token(user_info)
    
    # Redirect back to frontend with token
    frontend_url = os.getenv("FRONTEND_URL")
    response = RedirectResponse(url=f"{frontend_url}/home")
    
    # Set token as HTTP-only cookie
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,  # Set to True for production (HTTPS)
        samesite="none",  # Allow cross-site for Vercel deployments
        max_age=JWT_EXPIRATION_HOURS * 3600,
    )
    
    return response


@app.get("/auth/user")
async def get_user(auth_token: Optional[str] = Cookie(None)):
    """Get current user from JWT token"""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = verify_jwt_token(auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


@app.post("/auth/logout")
async def logout():
    """Logout user by clearing auth cookie"""
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie(
        key="auth_token",
        secure=True,
        samesite="none",
    )
    return response


@app.post("/widget/get-ott")
async def get_widget_ott(request: Request, auth_token: Optional[str] = Cookie(None)):
    """
    Get OTT (One-Time Token) from Understand Tech API
    This will be called by the frontend after authentication
    to obtain a token for the widget iframe
    """
    print("\n" + "="*80)
    print("🔑 [BACKEND] Widget OTT Request Started")
    print("="*80)
    
    if not auth_token:
        print("❌ [BACKEND] No auth token provided")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = verify_jwt_token(auth_token)
    if not user:
        print("❌ [BACKEND] Invalid or expired JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    print(f"✅ [BACKEND] User authenticated: {user.get('email', 'unknown')}")
    
    if not WIDGET_API_KEY:
        print("❌ [BACKEND] Widget API key not configured in environment")
        raise HTTPException(status_code=500, detail="Widget API key not configured")
    
    if not UT_API_BASE_URL:
        print("❌ [BACKEND] UT API base URL not configured in environment")
        raise HTTPException(status_code=500, detail="UT API base URL not configured")
    
    body = await request.json()
    model_id = body.get("model_id")
    origin = body.get("origin", "http://localhost:5173")
    
    print(f"📋 [BACKEND] Request params:")
    print(f"   - model_id: {model_id}")
    print(f"   - origin: {origin}")
    print(f"   - user_email: {user.get('email')}")
    
    if not model_id:
        print("❌ [BACKEND] model_id is required but not provided")
        raise HTTPException(status_code=400, detail="model_id is required")
    
    # Call UT API to get OTT
    try:
        ut_api_url = f"{UT_API_BASE_URL}/widget/ott"
        print(f"\n🌐 [BACKEND] Calling UT API: POST {ut_api_url}")
        print(f"   - Authorization: Bearer {WIDGET_API_KEY[:20]}...{WIDGET_API_KEY[-10:]}")
        print(f"   - Query params: model_id={model_id}, origin={origin}, user_email={user.get('email')}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            ott_response = await client.post(
                ut_api_url,
                headers={
                    "Authorization": f"Bearer {WIDGET_API_KEY}",
                    "Accept-Language": "en",  # UT API expects Accept-Language header
                },
                params={
                    "model_id": model_id,
                    "origin": origin,
                    "user_email": user.get("email"),
                },
            )
        
        print(f"📡 [BACKEND] UT API Response: {ott_response.status_code}")
        
        if ott_response.status_code != 200:
            error_detail = "Failed to obtain OTT from UT API"
            try:
                error_data = ott_response.json()
                error_detail = error_data.get("detail", error_detail)
                print(f"❌ [BACKEND] UT API Error: {error_detail}")
            except Exception:
                error_detail = ott_response.text or error_detail
                print(f"❌ [BACKEND] UT API Error (raw): {error_detail}")
            
            raise HTTPException(
                status_code=ott_response.status_code,
                detail=error_detail
            )
        
        ott_data = ott_response.json()
        ott_preview = ott_data.get("ott", "")[:30] + "..." if ott_data.get("ott") else "None"
        print(f"✅ [BACKEND] OTT received successfully")
        print(f"   - OTT (preview): {ott_preview}")
        print(f"   - Expires in: {ott_data.get('expires_in')} seconds")
        print("="*80 + "\n")
        
        return ott_data
    
    except httpx.TimeoutException:
        print("❌ [BACKEND] UT API request timed out (>10s)")
        print("="*80 + "\n")
        raise HTTPException(status_code=504, detail="UT API request timed out")
    except httpx.RequestError as e:
        print(f"❌ [BACKEND] Failed to connect to UT API: {str(e)}")
        print("="*80 + "\n")
        raise HTTPException(status_code=502, detail=f"Failed to connect to UT API: {str(e)}")
    except HTTPException:
        print("="*80 + "\n")
        raise
    except Exception as e:
        print(f"❌ [BACKEND] Unexpected error: {str(e)}")
        print("="*80 + "\n")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

