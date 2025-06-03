# UploadBros Backend

This is the backend server for the UploadBros application, handling YouTube and Spotify downloads.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Spotify credentials:
- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Create a new application
- Copy your Client ID and Client Secret
- Create a `.env` file based on `.env.example` and add your credentials

4. Run the server:
```bash
python app.py
```

The server will start on `http://localhost:5000`.

## API Endpoints

### YouTube Download
- **POST** `/api/youtube/download`
- Body:
  ```json
  {
    "url": "YouTube URL",
    "format": "mp4|mp3|wav|m4a",
    "config": {
      "quality": "highest|1080p|720p|480p|360p",
      "downloadSubtitles": boolean,
      "downloadThumbnail": boolean,
      "audioOnly": boolean,
      "startTime": "00:00",
      "endTime": "10:00"
    }
  }
  ```

### Spotify Track Info
- **POST** `/api/spotify/download`
- Body:
  ```json
  {
    "url": "Spotify Track URL",
    "quality": "320|256|128",
    "config": {
      "downloadArtwork": boolean,
      "downloadLyrics": boolean,
      "outputFormat": "mp3|aac|ogg|wav",
      "includeMetadata": boolean
    }
  }
  ```

### Download File
- **GET** `/api/download/<filename>`
- Downloads a previously processed file

## Notes
- The Spotify endpoint currently only provides track information due to Spotify's terms of service
- YouTube downloads are handled using yt-dlp
- Files are temporarily stored in the `downloads` directory 