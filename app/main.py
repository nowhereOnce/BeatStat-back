from fastapi import FastAPI, HTTPException, Depends, Request, Response
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

# Inicializar FastAPI
app = FastAPI()
security = HTTPBearer()


# Función para obtener el ID de Spotify desde las cookies
def get_spotify_user_id(request: Request) -> str:
    return request.cookies.get("spotify_user_id")

global_sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        show_dialog=True,
    )


@app.get("/")
def read_root(request: Request):
    user_id = get_spotify_user_id(request)
    
    # Si no hay user_id, redirigir a la página de autenticación
    if not user_id:
        auth_url = global_sp_oauth.get_authorize_url()
        return RedirectResponse(auth_url)
    
    cache_handler = RedisCacheHandler(redis_client, key=f"spotify_token:{user_id}")
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
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
    cache_handler = RedisCacheHandler(redis_client, key=f"spotify_token:{user_id}")
    cache_handler.save_token_to_cache(token_info)
    
    # Guarda el user_id en una cookie
    response = RedirectResponse("/get_playlists")
    response.set_cookie(
        key="spotify_user_id",
        value=user_id,
        httponly=True,
        secure=False,  # Solo en HTTPS
        samesite="Lax"
    )
    
    return response

@app.get("/get_playlists")
def get_playlists(request: Request):
    user_id = request.cookies.get("spotify_user_id")
    print(user_id)

    if not user_id:
        print("No se encontró el user_id")
        return RedirectResponse("/")
    
    cache_handler = RedisCacheHandler(redis_client, key=f"spotify_token:{user_id}")
    
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_handler=cache_handler,
        show_dialog=True,
    )
    
    sp = Spotify(auth_manager=sp_oauth)
    
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return RedirectResponse("/")
    playlists = sp.current_user_playlists()
    print(playlists)
    return playlists
