from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from app.dependencies import get_spotify_user_id, get_cache_handler
from app.dependencies import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SCOPE
from app.routes.routes import router
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEFAULT_REDIRECT_ENDPOINT = os.getenv("FRONTEND_URL", "http://localhost:5173/me")

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

# Helper function to create a new SpotifyOAuth instance
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

# Get the correct domain for cookies based on environment
def get_cookie_domain():
    if ENVIRONMENT == "production":
        # Adjust this based on your actual domain
        return ".beatstat.com"  # Only if you're actually using beatstat.com
        # If using Render's domain, return None or your actual domain
        # return None  # Let the browser determine the domain
    return None  # For development

#THIS NEEDS TO BE CHANGED TO SOME ROUTE IN THE FRONTEND
default_redirect_endpoint = os.getenv("DEFAULT_REDIRECT_ENDPOINT", "http://localhost:5173/") 

@app.get("/login")
def login(request: Request):
    """
    Checks if the user is authenticated by checking the cookie.
    If not, redirects to the Spotify login page.
    """
    logger.info(f"Login attempt from: {request.client.host}")

    try:
        user_id = get_spotify_user_id(request)  
        logger.info(f"User already authenticated: {user_id}")
    except Exception as e:
        logger.info(f"User not authenticated, redirecting to Spotify: {str(e)}")
        sp_oauth = create_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    # If the user is authenticated, redirect to the default endpoint
    cache_handler = get_cache_handler(user_id)
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=True,
    )
    
    # If the token is not valid, redirect to the Spotify login page
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        logger.info(f"Token invalid for user: {user_id}")
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    return RedirectResponse(default_redirect_endpoint)


@app.get("/callback")
def callback(code: str, response: Response, request: Request):
    """
    This endpoint is called by Spotify after the user has authorized the app.
    Obtains the access token and user ID, saves the token in cache (Redis), 
    and redirects to the default endpoint.
    
    Parameters:
    - code: Authorization code provided by Spotify.
    - response: FastAPI Response object.
    """
    logger.info(f"Callback received from: {request.client.host}")
    
    # Obtain access token
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)

    if not token_info:
        logger.error("No access token was obtained")
        raise HTTPException(status_code=500, detail="No access token was obtained")
    
    sp = Spotify(auth=token_info["access_token"])
    
    # Obtain user ID
    user_info = sp.current_user()

    if user_info is None or "id" not in user_info:
        logger.error("Expected user data was not received")
        raise HTTPException(status_code=500, detail="Expected user data was not received. The object is None")

    user_id = user_info["id"]
    logger.info(f"Processing callback for user: {user_id}")
    
    # Save token in cache (Redis)
    cache_handler = get_cache_handler(user_id)
    cache_handler.save_token_to_cache(token_info)
    logger.info(f"Token saved for user: {user_id}")
    
    # Save user ID in a cookie and redirect to
    response = RedirectResponse(default_redirect_endpoint)

    # Cookie configuration based on environment
    cookie_domain = get_cookie_domain()
    cookie_secure = ENVIRONMENT == "production"

    response.set_cookie(
        key="spotify_user_id",
        value=user_id,
        httponly=True,
        secure=cookie_secure,  # HTTPS only
        domain=cookie_domain,
        samesite="lax"
    )

    logger.info(f"Cookie set for user: {user_id} with domain: {cookie_domain}")
    
    return response

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
        key="spotify_user_id",
        httponly=True,
        secure=cookie_secure,  # HTTPS only
        domain=cookie_domain,
        samesite="lax"
    )
    return response

# Debug endpoint to check current user
@app.get("/debug/current-user")
def debug_current_user(request: Request):
    """
    Debug endpoint to check which user is currently authenticated.
    Remove in production.
    """
    if ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        user_id = get_spotify_user_id(request)
        return {"user_id": user_id, "cookies": dict(request.cookies)}
    except Exception as e:
        return {"error": str(e), "cookies": dict(request.cookies)}

@app.get("/")
def read_root():
    return {"message": "BeatStat-backend"}

# Include the routers
app.include_router(router=router)
