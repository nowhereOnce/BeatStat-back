import os
import redis
from fastapi import Request, HTTPException
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import RedisCacheHandler
from spotipy import Spotify
from dotenv import load_dotenv

load_dotenv()

# spotify connection
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "user-library-read, user-top-read"

# Redis-cloud config (local otherwise)
REDIS_URL = os.getenv("REDIS_URL")  
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  
REDIS_PORT = os.getenv("REDIS_PORT", 6379)  
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") 
REDIS_DB = os.getenv("REDIS_DB", 0) 

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL)
else:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        password=REDIS_PASSWORD,
        db=int(REDIS_DB),
        decode_responses=True,
        ssl=True,
    )

def get_spotify_user_id(request: Request) -> str:
    user_id = request.cookies.get("spotify_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No authenticated user")
    return user_id

def get_cache_handler(user_id: str) -> RedisCacheHandler:
    return RedisCacheHandler(redis_client, key=f"spotify_token:{user_id}")

def get_user_spotify_oauth(request: Request) -> SpotifyOAuth:
    user_id = get_spotify_user_id(request)
    cache_handler = get_cache_handler(user_id)
    oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=True,
    )
    token_info = cache_handler.get_cached_token()
    if not oauth.validate_token(token_info):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return oauth

def get_spotify_client(request: Request) -> Spotify:
    oauth = get_user_spotify_oauth(request)
    return Spotify(auth_manager=oauth)