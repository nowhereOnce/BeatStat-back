from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import requests
from app.utils.spotify import refresh_token

router = APIRouter()

@router.get("/playlists")
def get_playlists(request: Request):
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse("/")
    
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    spotify_response = requests.get(url, headers=headers)

    
    if spotify_response.status_code != 200:
        raise HTTPException(status_code=spotify_response.status_code, detail="Error al obtener las playlists")
    
    return spotify_response.json()