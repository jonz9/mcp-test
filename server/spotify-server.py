import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from fastmcp.server import ToolServer, tool
from pydantic import BaseModel, Field

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state",
    cache_path=".spotify_token_cache"
))

class PlaySongArgs(BaseModel):
    song_name: str = Field(..., description="The name of the song to play")
    artist: str = Field(..., description="The artist who performed the song")

@tool
async def play_song(args: PlaySongArgs) -> str:
    query = f"{args.song_name} {args.artist}"
    results = sp.search(q=query, type='track', limit=1)

    if results['tracks']['items']:
        uri = results['tracks']['items'][0]['uri']
        sp.start_playback(uris=[uri])
        return f"Playing '{args.song_name}' by {args.artist} on Spotify."
    else:
        return f"Could not find '{args.song_name}' by {args.artist} on Spotify."

server = ToolServer("spotify")
server.add_tool(play_song)

if __name__ == "__main__":
    server.run(transport='stdio')