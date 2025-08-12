import os
import redis
from fastapi import Request, HTTPException
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from spotipy import Spotify
from typing import cast


load_dotenv()

# spotify connection
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "user-library-read, user-top-read"

# Session configuration
SESSION_EXPIRE_MINUTES = 60 * 24  # 24 hours

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

# Helper function to create a new SpotifyOAuth instance
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

def get_session_id(request: Request) -> str:
    """Get or create session ID from cookie"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="No session found. Please login first.")
    
    return session_token

def get_user_session(session_id: str) -> dict:
    """Get user session data from Redis"""
    session_data = redis_client.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")

    return json.loads(cast(str, session_data))

def save_user_session(session_id: str, token_info: dict, user_info: dict):
    """Save user session in Redis"""
    session_data = {
        "token_info": token_info,
        "user_info": user_info,
        "created_at": datetime.now().isoformat()
    }
    
    # Save in Redis with expiration
    redis_client.setex(
        f"session:{session_id}",
        timedelta(minutes=SESSION_EXPIRE_MINUTES),
        json.dumps(session_data)
    )

def get_spotify_client(session_data: dict, session_id: str) -> Spotify:
    """Create Spotify client with session token"""
    token_info = session_data["token_info"]
    
    # Check if token needs renewal
    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        # Update token in session
        session_data["token_info"] = token_info
        # Update session in Redis
        redis_client.setex(
            f"session:{session_id}",
            timedelta(minutes=SESSION_EXPIRE_MINUTES),
            json.dumps(session_data)
        )

    sp = Spotify(oauth_manager=sp_oauth)
        
    return sp