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

load_dotenv()

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# List of allowed origins for CORS
# Only include the frontend domains
# THIS MIGHT NEED TO BE CHANGED!!!
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Used to get the user's authorization code
global_sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
    )

#THIS NEEDS TO BE CHANGED TO SOME ROUTE IN THE FRONTEND
default_redirect_endpoint = "http://localhost:5173/me" 

@app.get("/")
def read_root(request: Request):
    """
    Checks if the user is authenticated by checking the cookie.
    If not, redirects to the Spotify login page.
    """
    try:
        user_id = get_spotify_user_id(request)
    except Exception:
        auth_url = global_sp_oauth.get_authorize_url()
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
    token_info = global_sp_oauth.get_access_token(code)
    if token_info:
        sp = Spotify(auth=token_info["access_token"])
    else:
        raise HTTPException(status_code=500, detail="No access token was obtained")
    
    # Obtain user ID
    user_info = sp.current_user()

    if user_info is None or "id" not in user_info:
        raise HTTPException(status_code=500, detail="Expected user data was not received. The object is None")

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
        samesite="lax"
    )
    
    return response

@app.post("/logout")
def logout(response: Response):
    """
    Deletes the authentication cookie.
    """
    response = Response(status_code=200)
    response.delete_cookie(
        key="spotify_user_id",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response

# Include the routers
app.include_router(router=router)
