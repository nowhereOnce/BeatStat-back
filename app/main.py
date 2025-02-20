from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import RedisCacheHandler
from dotenv import load_dotenv
from app.dependencies import (
    get_spotify_user_id,
    get_cache_handler,
    get_user_spotify_oauth,
    get_spotify_client,
    redis_client,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SCOPE,
)

load_dotenv()

# Inicializar FastAPI
app = FastAPI()
security = HTTPBearer()


global_sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
    )


@app.get("/")
def read_root(request: Request):
    try:
        user_id = get_spotify_user_id(request)
    except Exception:
        auth_url = global_sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    cache_handler = get_cache_handler(user_id)
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=True,
    )
    
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    return RedirectResponse("/get_playlists")

@app.get("/callback")
def callback(code: str, response: Response):
    
    token_info = global_sp_oauth.get_access_token(code)
    sp = Spotify(auth=token_info["access_token"])
    
    # Obtener información del usuario para guardar en caché
    user_info = sp.current_user()
    user_id = user_info["id"]
    
    # Guardar token en caché
    cache_handler = get_cache_handler(user_id)
    cache_handler.save_token_to_cache(token_info)
    
    # Guarda el user_id en una cookie
    response = RedirectResponse("/get_playlists")
    response.set_cookie(
        key="spotify_user_id",
        value=user_id,
        httponly=True,
        secure=True,  # Solo en HTTPS
        samesite="Lax"
    )
    
    return response

@app.get("/get_playlists")
def get_playlists(sp: Spotify = Depends(get_spotify_client)):
    playlists = sp.current_user_playlists()
    return playlists

