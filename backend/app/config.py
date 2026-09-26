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

# Automatic export folder in user's Downloads
READY_EXPORT_DIR = Path.home() / "Downloads" / "CR_Remover_Ready"

# Ensure all working directories exist
for directory in (STORAGE_DIR, UPLOADS_DIR, PROCESSED_DIR, TEMP_DIR, READY_EXPORT_DIR):
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
