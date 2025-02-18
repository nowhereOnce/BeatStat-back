from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import RedisCacheHandler
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Spotify
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
scope = "user-library-read"

# Configuración de Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)

cache_handler = RedisCacheHandler(redis_client)

# Inicializar FastAPI
app = FastAPI()
security = HTTPBearer()

# OAuth de Spotify
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True,
)

sp = Spotify(auth_manager=sp_oauth)

app = FastAPI()

@app.get("/")
def read_root():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    return RedirectResponse("/get_playlists")

@app.get("/callback")
def callback(code: str):
    token_info = sp_oauth.get_access_token(code)
    cache_handler.save_token_to_cache(token_info)
    return RedirectResponse("/get_playlists")

@app.get("/get_playlists")
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return RedirectResponse("/")
    playlists = sp.current_user_playlists()
    print(playlists)
    return playlists
