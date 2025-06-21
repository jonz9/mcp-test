import os
import shutil
import subprocess
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("spotify")

# Commented out Spotipy-based implementation
# import spotipy
# from spotipy.oauth2 import SpotifyOAuth
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
#     client_id=os.getenv("SPOTIFY_CLIENT_ID"),
#     client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
#     redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
#     scope="user-read-playback-state user-modify-playback-state",
#     cache_path=".spotify_token_cache"
# ))
#
# @mcp.tool()
# async def play_song(song_name: str, artist: str) -> str:
#     query = f"{song_name} {artist}"
#     results = sp.search(q=query, type='track', limit=1)
#     if results['tracks']['items']:
#         uri = results['tracks']['items'][0]['uri']
#         sp.start_playback(uris=[uri])
#         return f"Playing '{song_name}' by {artist} on Spotify."
#     else:
#         return f"Could not find '{song_name}' by {artist} on Spotify."

@mcp.tool()
async def play_song(song_name: str, artist: str) -> str:
    subprocess.run(['open', '-a', 'Spotify'])

    safe_query = f"{song_name} {artist}".replace('"', '\\"')

    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify"',
            '-e', f'play track (first track of (search "{safe_query}"))',
            '-e', 'end tell'
        ], check=True)

        if not shutil.which("osascript"):
            return "AppleScript is not available on this system."

        return f"Playing '{song_name}' by {artist} in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to play song: {e}"

@mcp.tool()
async def next_track() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to next track'
        ], check=True)
        return "Skipped to next track in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to skip to next track: {e}"

@mcp.tool()
async def previous_track() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to previous track'
        ], check=True)
        return "Went to previous track in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to go to previous track: {e}"

@mcp.tool()
async def playpause() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to playpause'
        ], check=True)
        return "Toggled play/pause in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to toggle play/pause: {e}"

@mcp.tool()
async def pause() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to pause'
        ], check=True)
        return "Paused Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to pause: {e}"

@mcp.tool()
async def play() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to play'
        ], check=True)
        return "Resumed playback in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to resume playback: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')