import re
import time
from typing import Optional, Union, List
from ..services import file_manager

class ProgressTracker:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.start_time = None
        self.update_progress({
            "status": "initializing",
            "progress": 0,
            "speed": None,
            "eta": None,
            "filename": None,
            "error": None
        })

    def start(self):
        """Mark the download as started"""
        self.start_time = time.time()
        self.update_progress({
            "status": "downloading",
            "progress": 0
        })

    def complete(self, filename: Union[str, List[str]]):
        """Mark the download as complete"""
        self.update_progress({
            "status": "complete",
            "progress": 100,
            "filename": filename,
            "time_taken": round(time.time() - self.start_time, 2) if self.start_time else None
        })

    def error(self, error_message: str):
        """Mark the download as failed"""
        self.update_progress({
            "status": "error",
            "error": error_message
        })

    def update_progress(self, data: dict):
        """Update progress in the store"""
        file_manager.update_progress(self.task_id, data)

    def yt_dlp_hook(self, d: dict):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                progress = (downloaded / total) * 100
            else:
                progress = 0

            self.update_progress({
                "status": "downloading",
                "progress": round(progress, 2),
                "speed": d.get('speed', 0),
                "eta": d.get('eta', 0),
                "filename": d.get('filename'),
                "total_size": total,
                "downloaded_size": downloaded
            })
        
        elif d['status'] == 'finished':
            self.update_progress({
                "status": "processing",
                "progress": 100,
                "filename": d.get('filename')
            })

    def update_from_spotdl(self, output: str):
        """Parse and update progress from spotdl output"""
        # Example patterns to match spotdl output
        download_pattern = r"Downloaded (\d+)%"
        processing_pattern = r"Processing (\d+)%"
        error_pattern = r"Error: (.*)"
        
        if match := re.search(download_pattern, output):
            progress = int(match.group(1))
            self.update_progress({
                "status": "downloading",
                "progress": progress
            })
        
        elif match := re.search(processing_pattern, output):
            progress = int(match.group(1))
            self.update_progress({
                "status": "processing",
                "progress": progress
            })
        
        elif match := re.search(error_pattern, output):
            error_msg = match.group(1)
            self.error(error_msg)
        
        elif "Download completed" in output:
            self.update_progress({
                "status": "processing",
                "progress": 100
            }) 