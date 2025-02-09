from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
import secrets
import urllib.parse
import requests
from app.utils.spotify import refresh_token
from dotenv import load_dotenv
import os

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

router = APIRouter()

@router.get("/login")
def login():
    state = secrets.token_urlsafe(16)
    print(state)
    
    scope = "user-read-private user-read-email"
    
    authurl = (
        "https://accounts.spotify.com/authorize?" +
        urllib.parse.urlencode({
            "response_type": "code",
            "client_id": SPOTIFY_CLIENT_ID,
            "scope": scope,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "state": state
        })
    )
    
    return RedirectResponse(url=authurl)

@router.get("/callback")
def callback(code: str, response: Response):
    token_url = "https://accounts.spotify.com/api/token"
    
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    
    spotify_response = requests.post(token_url, data=payload)
    
    if spotify_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Token request failed")
    
    token_data = spotify_response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=expires_in,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    
    return {"message": "Token obtenido y almacenado en cookies"}