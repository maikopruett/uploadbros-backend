from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, List
from ..services import file_manager
from ..utils.progress import ProgressTracker

router = APIRouter()
logger = logging.getLogger(__name__)

class SpotifyRequest(BaseModel):
    url: HttpUrl
    quality: str = "320k"
    download_artwork: bool = True
    download_lyrics: bool = False
    output_format: str = "mp3"
    playlist_items: Optional[str] = None  # Format: "1,2,3" or "1-10"

def get_spotdl_command(request: SpotifyRequest, task_id: str) -> List[str]:
    """Generate spotdl command based on request"""
    output_dir = f"temp/{task_id}"
    
    command = [
        "spotdl",
        "--output", output_dir,
        "--format", request.output_format,
        "--bitrate", request.quality
    ]
    
    if not request.download_artwork:
        command.extend(["--no-artwork"])
    
    if request.download_lyrics:
        command.extend(["--lyrics"])
    
    if request.playlist_items:
        command.extend(["--playlist-items", request.playlist_items])
    
    command.append(str(request.url))
    return command

@router.post("/download")
async def download_track(request: SpotifyRequest, background_tasks: BackgroundTasks):
    """Download track or playlist from Spotify"""
    try:
        task_id = file_manager.generate_task_id()
        temp_dir = Path(f"temp/{task_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        progress_tracker = ProgressTracker(task_id)
        command = get_spotdl_command(request, task_id)

        async def download():
            try:
                # Start spotdl process
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Monitor progress
                progress_tracker.start()
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    output = line.decode().strip()
                    logger.debug(f"spotdl output: {output}")
                    progress_tracker.update_from_spotdl(output)

                # Wait for process to complete
                await process.wait()

                if process.returncode != 0:
                    error = await process.stderr.read()
                    raise Exception(f"spotdl failed: {error.decode()}")

                # Move files to downloads directory
                files = list(temp_dir.glob("*"))
                for file in files:
                    final_path = Path("downloads") / file.name
                    file.rename(final_path)

                # Update progress to complete
                progress_tracker.complete(
                    [f.name for f in files]
                )

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