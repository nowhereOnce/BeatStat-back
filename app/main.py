from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from app.dependencies import get_spotify_user_id, get_cache_handler
from app.dependencies import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SCOPE
from app.routes.routes import router

load_dotenv()

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# Used to get the user's authorization code
sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
    )

default_redirect_endpoint = "/me/top-tracks"

@app.get("/")
def read_root(request: Request):
    """
    Checks if the user is authenticated by checking the cookie.
    If not, redirects to the Spotify login page.
    """
    try:
        user_id = get_spotify_user_id(request)
    except Exception:
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
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    return RedirectResponse(default_redirect_endpoint)


@app.get("/callback")
def callback(code: str, response: Response):
    """
    This endpoint is called by Spotify after the user has authorized the app.
    Obtains the access token and user ID, saves the token in cache (Redis), 
    and redirects to the default endpoint.
    
    Parameters:
    - code: Authorization code provided by Spotify.
    - response: FastAPI Response object.
    """
    
    # Obtain access token
    token_info = sp_oauth.get_access_token(code)
    sp = Spotify(auth=token_info["access_token"])
    
    # Obtain user ID
    user_info = sp.current_user()
    user_id = user_info["id"]
    
    # Save token in cache (Redis)
    cache_handler = get_cache_handler(user_id)
    cache_handler.save_token_to_cache(token_info)
    
    # Save user ID in a cookie and redirect to
    response = RedirectResponse(default_redirect_endpoint)
    response.set_cookie(
        key="spotify_user_id",
        value=user_id,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="Lax"
    )
    
    return response

# Include the routers
app.include_router(router=router)
