from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from spotipy import Spotify
from dotenv import load_dotenv
from app.routes.routes import router
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import uuid
from app.dependencies import get_spotify_oauth, save_user_session, get_user_session, get_session_id, get_spotify_client

load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Session configuration
SESSION_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# List of allowed origins for CORS
# Only include the frontend domains
# THIS MIGHT NEED TO BE CHANGED!!!
origins = [
    "https://app.beatstat.com",
    "https://www.app.beatstat.com",
]

# Middleware to handle CORS
if ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # Use specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Get the correct domain for cookies based on environment
def get_cookie_domain():
    if ENVIRONMENT == "production":
        return ".beatstat.com"
    return None  # For development

DEFAULT_REDIRECT_ENDPOINT = os.getenv("DEFAULT_REDIRECT_ENDPOINT", "http://localhost:8000/status")
logger.info(f"Default redirect endpoint: {DEFAULT_REDIRECT_ENDPOINT}")


@app.get("/login")
async def login():
    """Start Spotify authentication process"""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(url=auth_url)


@app.get("/callback")
async def callback(request: Request, response: Response):
    """Callback after Spotify authentication"""
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    try:
        # Get access token
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.get_access_token(code=code, check_cache=False) # VERY IMPORTANT: check_cache=False (Otherwise it might return a cached token)
        
        # Create Spotify client
        sp = Spotify(auth=token_info['access_token'])
        
        # Get user information
        user_info = sp.current_user()
        if not user_info:
            raise HTTPException(status_code=401, detail="Failed to retrieve user information from Spotify")
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Save session in Redis
        save_user_session(session_id, token_info, user_info)
        
        # Set session cookie
        response = RedirectResponse(url=DEFAULT_REDIRECT_ENDPOINT)
        response.set_cookie(
            key="session_token",
            value=session_id,
            max_age=SESSION_EXPIRE_MINUTES * 60,  # in seconds
            httponly=True,
            secure=ENVIRONMENT == "production",  # Change to True in production with HTTPS
            domain=get_cookie_domain(),  # Configure cookie domain
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.post("/logout")
def logout(response: Response):
    """
    Deletes the authentication cookie.
    """
    response = Response(status_code=200)

    # Cookie configuration based on environment
    cookie_domain = get_cookie_domain()
    cookie_secure = ENVIRONMENT == "production"

    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=cookie_secure,  # HTTPS only
        domain=cookie_domain,
        samesite="lax"
    )
    return response

@app.get("/status")
async def get_status(session_id: str = Depends(get_session_id)):
    """Get current session status"""
    try:
        session_data = get_user_session(session_id)
        
        # Verify token is valid and get updated user information
        sp = get_spotify_client(session_data, session_id)
        current_user = sp.current_user()
        if not current_user:
            raise HTTPException(status_code=401, detail="Failed to retrieve user information from Spotify")
        
        return {
            "authenticated": True,
            "user": {
                "id": current_user["id"],
                "display_name": current_user["display_name"],
                "email": current_user.get("email")
            },
            "session_created": session_data["created_at"]
        }
        
    except HTTPException:
        return {"authenticated": False}


@app.get("/")
def read_root():
    return {"message": "BeatStat-backend"}

# Include the routers
app.include_router(router=router)
