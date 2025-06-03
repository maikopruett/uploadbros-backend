import asyncio
import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# In-memory storage for progress tracking
_progress_store: Dict[str, Dict[str, Any]] = {}

def generate_task_id() -> str:
    """Generate a unique task ID"""
    return str(uuid.uuid4())

async def get_progress(task_id: str) -> Optional[Dict[str, Any]]:
    """Get progress for a task"""
    return _progress_store.get(task_id)

def update_progress(task_id: str, progress: Dict[str, Any]):
    """Update progress for a task"""
    _progress_store[task_id] = progress

def remove_progress(task_id: str):
    """Remove progress for a task"""
    _progress_store.pop(task_id, None)

async def cleanup_task(task_id: str):
    """Clean up temporary files for a task"""
    try:
        temp_dir = Path(f"temp/{task_id}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        remove_progress(task_id)
    except Exception as e:
        logger.error(f"Error cleaning up task {task_id}: {e}")

async def cleanup_old_files(max_age_hours: int = 24):
    """Clean up old temporary files and downloads"""
    try:
        # Clean up temp directory
        temp_dir = Path("temp")
        if temp_dir.exists():
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            for item in temp_dir.glob("*"):
                if item.stat().st_mtime < cutoff.timestamp():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

        # Clean up old downloads
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            cutoff = datetime.now() - timedelta(hours=max_age_hours * 2)  # Keep downloads longer
            for item in downloads_dir.glob("*"):
                if item.stat().st_mtime < cutoff.timestamp():
                    item.unlink()

    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

async def ensure_disk_space(required_mb: int = 1000):
    """Ensure there's enough disk space available"""
    try:
        downloads_dir = Path("downloads")
        temp_dir = Path("temp")
        
        # Get disk usage
        total, used, free = shutil.disk_usage(downloads_dir if downloads_dir.exists() else ".")
        free_mb = free // (1024 * 1024)  # Convert to MB
        
        if free_mb < required_mb:
            logger.warning(f"Low disk space: {free_mb}MB free")
            # Clean up old files first
            await cleanup_old_files(max_age_hours=1)
            
            # Check again
            _, _, free = shutil.disk_usage(downloads_dir if downloads_dir.exists() else ".")
            free_mb = free // (1024 * 1024)
            
            if free_mb < required_mb:
                raise Exception(f"Insufficient disk space: {free_mb}MB free, {required_mb}MB required")
    
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        raise 