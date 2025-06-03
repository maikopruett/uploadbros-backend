from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
import yt_dlp
import asyncio
import logging
from pathlib import Path
from typing import Optional
from ..services import file_manager
from ..utils.progress import ProgressTracker

router = APIRouter()
logger = logging.getLogger(__name__)

class VideoRequest(BaseModel):
    url: HttpUrl
    format: str = "mp4"
    quality: str = "best"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: bool = False

def get_yt_dlp_opts(request: VideoRequest, task_id: str, progress_tracker: ProgressTracker):
    """Configure yt-dlp options based on request"""
    output_template = f"temp/{task_id}/%(title)s.%(ext)s"
    
    format_selection = {
        "mp4": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "mp3": "bestaudio/best",
        "wav": "bestaudio/best",
        "m4a": "bestaudio[ext=m4a]/bestaudio/best"
    }

    opts = {
        'format': format_selection.get(request.format, 'best'),
        'outtmpl': output_template,
        'progress_hooks': [progress_tracker.yt_dlp_hook],
        'quiet': True,
        'no_warnings': True,
    }

    if request.audio_only or request.format in ['mp3', 'wav', 'm4a']:
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': request.format,
            'preferredquality': '320' if request.format == 'mp3' else None,
        }]

    if request.start_time or request.end_time:
        opts['download_ranges'] = lambda info: [[
            request.start_time or '0',
            request.end_time or None
        ]]

    return opts

@router.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Download video from YouTube"""
    try:
        task_id = file_manager.generate_task_id()
        temp_dir = Path(f"temp/{task_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        progress_tracker = ProgressTracker(task_id)
        yt_opts = get_yt_dlp_opts(request, task_id, progress_tracker)

        async def download():
            try:
                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    await asyncio.to_thread(ydl.download, [str(request.url)])
                    
                # Get the downloaded file
                files = list(temp_dir.glob("*"))
                if not files:
                    raise HTTPException(status_code=404, message="Download failed")
                
                downloaded_file = files[0]
                final_path = Path("downloads") / downloaded_file.name
                downloaded_file.rename(final_path)
                
                # Update progress to complete
                progress_tracker.complete(final_path.name)
                
                # Schedule cleanup
                background_tasks.add_task(file_manager.cleanup_task, task_id)
                
            except Exception as e:
                logger.error(f"Download error: {e}")
                progress_tracker.error(str(e))
                raise

        # Start download in background
        background_tasks.add_task(download)
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Download started"
        }

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get download status"""
    progress = await file_manager.get_progress(task_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return progress 