from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
from dotenv import load_dotenv
import tempfile
import json
from urllib.parse import unquote
from werkzeug.utils import safe_join
import subprocess
import re
import glob

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Create downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_format_selector(format_id, config):
    """Helper function to determine the format selector based on format and config"""
    if format_id == 'mp4':
        if config.get('quality') == 'highest':
            return 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            height = config['quality'].replace('p', '')
            return f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif format_id in ['mp3', 'wav', 'm4a']:
        return 'bestaudio[ext=m4a]/bestaudio/best'
    return 'best[ext=mp4]/best'

@app.route('/api/youtube/download', methods=['POST'])
def youtube_download():
    try:
        data = request.json
        url = data.get('url')
        format_id = data.get('format', 'mp4')
        config = data.get('config', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Configure yt-dlp options
        ydl_opts = {
            'format': get_format_selector(format_id, config),
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'noplaylist': True,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'force_generic_extractor': False,
            'prefer_ffmpeg': True,
        }

        # Add format-specific options
        if format_id in ['mp3', 'wav', 'm4a']:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_id,
                    'preferredquality': '320' if format_id == 'mp3' else None,
                }],
                'keepvideo': False,
            })

        # Add config options
        if config.get('startTime') and config.get('endTime'):
            ydl_opts['download_ranges'] = lambda info: [[config['startTime'], config['endTime']]]
        
        if config.get('downloadSubtitles'):
            ydl_opts.update({
                'writesubtitles': True,
                'subtitlesformat': 'srt',
            })

        if config.get('downloadThumbnail'):
            ydl_opts['writethumbnail'] = True

        # Download the video with improved error handling
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, try to extract info without downloading
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise Exception("Could not extract video information")
                except Exception as e:
                    if "Precondition check failed" in str(e):
                        # Try with a different format selector
                        ydl_opts['format'] = 'best'
                        info = ydl.extract_info(url, download=False)

                # Then proceed with download
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Handle audio formats
                if format_id in ['mp3', 'wav', 'm4a']:
                    filename = os.path.splitext(filename)[0] + f'.{format_id}'

                if not os.path.exists(filename):
                    raise Exception("Download failed - file not created")

                return jsonify({
                    'success': True,
                    'filename': os.path.basename(filename),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                })

        except yt_dlp.utils.DownloadError as e:
            error_message = str(e)
            if "HTTP Error 429" in error_message:
                return jsonify({'error': 'Rate limited by YouTube. Please try again later.'}), 429
            elif "ERROR: Sign in to confirm your age" in error_message:
                return jsonify({'error': 'Age-restricted video. Cannot download.'}), 403
            elif "ERROR: Private video" in error_message:
                return jsonify({'error': 'This video is private.'}), 403
            elif "Precondition check failed" in error_message:
                return jsonify({'error': 'YouTube API error. Please try again or try a different video.'}), 400
            else:
                return jsonify({'error': f'Download failed: {error_message}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/download', methods=['POST'])
def spotify_download():
    try:
        data = request.json
        url = data.get('url')
        config = data.get('config', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Validate Spotify URL
        if not ('spotify.com/track/' in url or 'spotify.com/playlist/' in url):
            return jsonify({'error': 'Invalid Spotify URL'}), 400

        # Build output template with directory and naming format
        output_template = config.get('outputTemplate', '{artist} - {title}')
        output_path = os.path.join(DOWNLOAD_DIR, output_template)

        # Build spotdl command - use the full output path as the template
        cmd = ['spotdl', url, '--output', output_path]

        # Add configuration options
        if config.get('outputFormat'):
            cmd.extend(['--format', config['outputFormat']])
        
        # Handle artwork option
        if not config.get('downloadArtwork', True):
            cmd.append('--skip-album-art')
            
        if config.get('downloadLyrics'):
            cmd.append('--lyrics')

        # For playlists, handle start and end indices
        if 'spotify.com/playlist/' in url:
            if config.get('playlistStartIndex') and int(config['playlistStartIndex']) > 1:
                cmd.extend(['--playlist-start', str(config['playlistStartIndex'])])
            if config.get('playlistEndIndex'):
                cmd.extend(['--playlist-end', str(config['playlistEndIndex'])])

        print(f"Executing command: {' '.join(cmd)}")

        # Get list of files before download to compare
        files_before = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()

        # Execute spotdl command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            print(f"Command output: {result.stdout}")
            if result.stderr:
                print(f"Command stderr: {result.stderr}")
            
            # Get list of files after download
            files_after = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()
            new_files = files_after - files_before
            
            if not new_files:
                # Fallback: try to find files based on the output format
                output_format = config.get('outputFormat', 'mp3')
                pattern = os.path.join(DOWNLOAD_DIR, f"*.{output_format}")
                all_files = glob.glob(pattern)
                
                if all_files:
                    # Get the most recently created files
                    all_files.sort(key=os.path.getctime, reverse=True)
                    # Take files created in the last minute
                    import time
                    recent_files = [f for f in all_files if os.path.getctime(f) > time.time() - 60]
                    new_files = [os.path.basename(f) for f in recent_files[:10]]  # Limit to 10 files
                
                if not new_files:
                    return jsonify({'error': 'No files were downloaded. Check if the Spotify URL is valid and accessible.'}), 500

            downloaded_files = list(new_files)
            
            return jsonify({
                'success': True,
                'files': downloaded_files,
                'message': f'Download completed successfully. {len(downloaded_files)} file(s) downloaded.'
            })

        except subprocess.CalledProcessError as e:
            error_message = e.stderr if e.stderr else str(e)
            print(f"Command failed with error: {error_message}")
            
            # Handle common spotdl errors
            if "No songs found" in error_message:
                return jsonify({'error': 'No songs found. The Spotify URL might be invalid or the content might not be available.'}), 404
            elif "rate limit" in error_message.lower():
                return jsonify({'error': 'Rate limited. Please try again later.'}), 429
            elif "ffmpeg" in error_message.lower():
                return jsonify({'error': 'FFmpeg error. Please ensure FFmpeg is installed and accessible.'}), 500
            else:
                return jsonify({'error': f'Download failed: {error_message}'}), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        # Ensure the filename is properly decoded
        decoded_filename = unquote(filename)
        
        # Get the absolute path and normalize it
        file_path = os.path.join(DOWNLOAD_DIR, decoded_filename)
        file_path = os.path.abspath(file_path)
        
        # Security check: ensure the file is within DOWNLOAD_DIR
        if not file_path.startswith(os.path.abspath(DOWNLOAD_DIR)):
            return jsonify({'error': 'Invalid file path'}), 403
            
        if os.path.exists(file_path):
            # Use send_file with safe_join for added security
            safe_path = safe_join(DOWNLOAD_DIR, decoded_filename)
            
            try:
                return send_file(
                    safe_path,
                    as_attachment=True,
                    download_name=decoded_filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                print(f"Error sending file: {str(e)}")
                return jsonify({'error': 'Error sending file'}), 500
        
        print(f"File not found: {file_path}")
        print(f"Available files in {DOWNLOAD_DIR}: {os.listdir(DOWNLOAD_DIR) if os.path.exists(DOWNLOAD_DIR) else 'Directory does not exist'}")
        return jsonify({'error': f'File not found: {decoded_filename}'}), 404
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)