# Media Downloader Backend Integration Guide

This document provides structured information about integrating with the Media Downloader backend API.

## API Endpoints

### 1. YouTube Download
- **Endpoint**: `POST /api/download/youtube`
- **Request Body**:
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```
- **Response**: MP3 file download
- **Error Response**:
```json
{
  "error": "error message"
}
```

### 2. Spotify Download
- **Endpoint**: `POST /api/download/spotify`
- **Request Body**:
```json
{
  "url": "https://open.spotify.com/track/..."
}
```
- **Response**: MP3 file download
- **Error Response**:
```json
{
  "error": "error message"
}
```

### 3. Health Check
- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "status": "ok"
}
```

## Frontend Integration Steps

1. Configure the backend URL in your frontend environment:
```javascript
const API_BASE_URL = 'http://localhost:3000/api';
```

2. Create utility functions for making API calls:
```javascript
async function downloadYouTube(url) {
  const response = await fetch(`${API_BASE_URL}/download/youtube`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }

  return response.blob();
}

async function downloadSpotify(url) {
  const response = await fetch(`${API_BASE_URL}/download/spotify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }

  return response.blob();
}
```

3. Example usage in a frontend component:
```javascript
// Download and trigger file download in browser
async function handleDownload(url, type) {
  try {
    const blob = await (type === 'youtube' ? downloadYouTube(url) : downloadSpotify(url));
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `download.mp3`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  } catch (error) {
    console.error('Download failed:', error);
    // Handle error in UI
  }
}
```

## Error Handling

The backend returns standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid or missing URL)
- 500: Server Error (download or conversion failed)

Always wrap API calls in try-catch blocks and handle errors appropriately in the UI.

## CORS Configuration

The backend accepts requests from the origin specified in the `ALLOWED_ORIGIN` environment variable. Make sure this matches your frontend's URL.

## File Handling

Downloaded files are automatically:
1. Saved to a temporary directory
2. Sent to the client
3. Deleted from the server after download

No action is required from the frontend regarding file cleanup.

## Environment Variables

Backend environment variables that may affect integration:
- `PORT`: Server port (default: 3000)
- `ALLOWED_ORIGIN`: Allowed CORS origin (default: *)

## Health Checking

Use the health check endpoint to verify the backend is running:
```javascript
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    return false;
  }
}
``` 