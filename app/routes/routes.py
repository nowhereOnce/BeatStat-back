from fastapi import APIRouter, Depends
from app.dependencies import get_spotify_client
from spotipy import Spotify


router = APIRouter(prefix="/me")

@router.get("/playlists")
def get_playlists(sp: Spotify = Depends(get_spotify_client)):
    """
    Get the user's playlists
    """
    playlists = sp.current_user_playlists()
    return playlists

@router.get("/top-tracks")
def get_tracks(
    sp: Spotify = Depends(get_spotify_client),
    time_range: str = "medium_term"
):
    """
    This endpoint returns the user's top 5 tracks.
    """
    tracks = sp.current_user_top_tracks(limit=5, time_range=time_range)
    tracks_info = []
    
    for track in tracks["items"]:
        track_info = {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "image": track["album"]["images"][0]["url"]
        }
        tracks_info.append(track_info)
    
    return {"tracks": tracks_info}