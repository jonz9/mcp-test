# Terminal MCP

Terminal MCP is a command-line assistant that communicates with a local Gemini 2.5 Flash model using the FastMCP protocol. It is built in Python and integrates modular tools for controlling system features, Spotify, and Google Workspace.

## Features

- Gemini 2.5 Flash integration via FastMCP
- Modular tool system with native tool calling
- System control: volume, brightness, screenshot
- Spotify search and playback (AppleScript-based)
- Gmail and Google Calendar access

## Requirements

- Python 3.10+
- macOS (for system and Spotify AppleScript tools)
- Virtual environment (recommended)

## Installation

```bash
git clone https://github.com/jonz9/terminal-mcp-gemini.git
cd terminal-mcp-gemini
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ENV file

Further ensure you have spotify and google developer accounts activated to obtain the keys list below.

```bash
GEMINI_API_KEY
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

## Running locally 

Ensure Docker Desktop is installed and opened.

```bash
cd client
python client.py
```
