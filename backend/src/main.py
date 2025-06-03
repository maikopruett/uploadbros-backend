from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create required directories
Path("logs").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)
Path("downloads").mkdir(exist_ok=True)

app = FastAPI(title="UploadBros Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after FastAPI instance is created
from .routers import youtube, spotify
from .services import file_manager

# Register routers
app.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
app.include_router(spotify.router, prefix="/spotify", tags=["spotify"])

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.websocket("/ws/progress/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for progress updates"""
    await websocket.accept()
    try:
        while True:
            progress = await file_manager.get_progress(task_id)
            if progress is None:
                break
            await websocket.send_json(progress)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    logger.info("Starting up UploadBros backend")
    # Clean temporary files on startup
    await file_manager.cleanup_old_files()

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks"""
    logger.info("Shutting down UploadBros backend")
    # Cleanup any remaining temporary files
    await file_manager.cleanup_old_files() 