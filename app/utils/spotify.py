import requests
from fastapi import HTTPException

def refresh_token(refresh_token: str):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "75ad3abf75da4244ada0b84923fcb1c8",
        "client_secret": "T552821b2c12f4d03aceb71b602f9ba57",
    }
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error al refrescar el token")
    
    token_data = response.json()
    return token_data["access_token"]