"""
Configuration module for CR Remover Studio.
Handles GPU/NVENC detection, directory paths, and runtime settings.
"""

from pathlib import Path
import os
import shutil
import subprocess

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Backend storage paths
BACKEND_DIR = BASE_DIR / "backend"
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
TEMP_DIR = STORAGE_DIR / "temp"

# Organized Desktop export folder and categories
DESKTOP_DIR = Path.home() / "Desktop"
READY_EXPORT_DIR = DESKTOP_DIR / "CR_Remover_Exports" if DESKTOP_DIR.exists() else Path.home() / "Downloads" / "CR_Remover_Exports"

EXPORTS_VIRAL_SHORTS_DIR = READY_EXPORT_DIR / "01_Viral_Shorts"
EXPORTS_FULL_VIDEOS_DIR = READY_EXPORT_DIR / "02_Full_Edited_Videos"
EXPORTS_REDDIT_STORIES_DIR = READY_EXPORT_DIR / "03_Reddit_Stories"
EXPORTS_PODCAST_CLIPS_DIR = READY_EXPORT_DIR / "04_Podcast_Clips"
EXPORTS_THUMBNAILS_DIR = READY_EXPORT_DIR / "05_Thumbnails_Covers"
EXPORTS_AUDIO_STEMS_DIR = READY_EXPORT_DIR / "06_Audio_Stems_Voice"
EXPORTS_METADATA_DIR = READY_EXPORT_DIR / "07_Metadata_Captions"
EXPORTS_BATCH_DIR = READY_EXPORT_DIR / "08_Batch_Campaigns"

ALL_EXPORT_DIRS = (
    READY_EXPORT_DIR,
    EXPORTS_VIRAL_SHORTS_DIR,
    EXPORTS_FULL_VIDEOS_DIR,
    EXPORTS_REDDIT_STORIES_DIR,
    EXPORTS_PODCAST_CLIPS_DIR,
    EXPORTS_THUMBNAILS_DIR,
    EXPORTS_AUDIO_STEMS_DIR,
    EXPORTS_METADATA_DIR,
    EXPORTS_BATCH_DIR
)

# Ensure all working directories and export vaults exist
for directory in (STORAGE_DIR, UPLOADS_DIR, PROCESSED_DIR, TEMP_DIR, *ALL_EXPORT_DIRS):
    directory.mkdir(parents=True, exist_ok=True)

# Frontend static build path (when served directly by FastAPI)
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"


def is_nvenc_available() -> bool:
    """
    Checks if NVIDIA NVENC hardware encoder (h264_nvenc) is supported
    by the installed FFmpeg and GPU.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return "h264_nvenc" in result.stdout
    except Exception:
        return False


# Detect GPU status at startup
HAS_NVENC = is_nvenc_available()
