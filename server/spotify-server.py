import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("spotify")

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state"
))

@mcp.tool()
async def play_song(song_name: str, artist: str) -> str:
    query = f"{song_name} {artist}"
    results = sp.search(q=query, type='track', limit=1)

    if results['tracks']['items']:
        uri = results['tracks']['items'][0]['uri']
        sp.start_playback(uris=[uri])
        return f"Playing '{song_name}' by {artist} on Spotify."
    else:
        return f"Could not find '{song_name}' by {artist} on Spotify."

@mcp.tool()
async def pause_playback() -> str:
    try:
        sp.pause_playback()
        return "Playback paused."
    except Exception as e:
        return f"Failed to pause: {str(e)}"

@mcp.tool()
async def resume_playback() -> str:
    try:
        sp.start_playback()
        return "Playback resumed."
    except Exception as e:
        return f"Failed to resume: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")