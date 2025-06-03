# Media Downloader Backend

A simple Node.js backend service that downloads and converts YouTube videos and Spotify tracks to MP3 format.

## Prerequisites

- Node.js >= 18.0.0
- Python 3.x
- ffmpeg

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd media-downloader-backend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Create Python virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install spotdl
```

4. Install system dependencies:
```bash
# On macOS
brew install ffmpeg yt-dlp

# On Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg python3-pip
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

5. Create environment configuration:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
PORT=3000
ALLOWED_ORIGIN=http://localhost:5173
```

## Development

Start the development server with hot reload:
```bash
npm run dev
```

## Production

Start the production server:
```bash
npm start
```

## API Documentation

See [INTEGRATION.md](./INTEGRATION.md) for detailed API documentation and frontend integration guide.

## Features

- Download YouTube videos and convert to MP3
- Download Spotify tracks as MP3
- Automatic file cleanup
- CORS support
- Health check endpoint
- Error handling
- Rate limiting

## Security Considerations

- The server automatically deletes downloaded files after sending
- CORS is configured to accept requests only from allowed origins
- Input validation for URLs
- No files are stored permanently on the server

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT 