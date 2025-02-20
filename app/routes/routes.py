from fastapi import APIRouter, Depends
from app.dependencies import get_spotify_client
from spotipy import Spotify


router = APIRouter(prefix="/me")

@router.get("/playlists")
def get_playlists(sp: Spotify = Depends(get_spotify_client)):
    playlists = sp.current_user_playlists()
    return playlists

@router.get("/top-tracks")
def get_tracks(
    sp: Spotify = Depends(get_spotify_client),
    time_range: str = "medium_term"
):
    tracks = sp.current_user_top_tracks(limit=5, time_range=time_range)
    tracks_names_dict = {
        "tracks": [track["name"] for track in tracks["items"]]
    }
    return tracks_names_dict