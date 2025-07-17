from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
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
    time_range: str = "short_term"
):
    """
    This endpoint returns the user's top 5 tracks.
    """
    tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)
    tracks_info = []
    
    if tracks and "items"  in tracks:
        for track in tracks["items"]:
            track_artist_info = sp.artist(track["artists"][0]["id"]) # image of the artist for every track
            track_info = {
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "artist_image": track_artist_info["images"][0]["url"] if track_artist_info else "",
                "image": track["album"]["images"][0]["url"]
            }
            # print(track)
            tracks_info.append(track_info)
    else:
        raise HTTPException(status_code=500, detail="Expected tracks data was not received. The object is None")
    
    return {"tracks": tracks_info}