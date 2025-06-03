from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# YouTube API setup
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Spotify API setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
    scope='user-read-playback-state user-modify-playback-state user-read-currently-playing'
))

@app.get("/")
async def read_root():
    return {"message": "UploadBros Backend API"}

@app.get("/youtube/search/{query}")
async def search_youtube(query: str):
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=10
        )
        response = request.execute()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spotify/search/{query}")
async def search_spotify(query: str):
    try:
        results = sp.search(q=query, limit=10)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spotify/current-track")
async def get_current_track():
    try:
        current_track = sp.current_user_playing_track()
        return current_track
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 