"""
FastAPI Server for CR Remover Studio.
Handles upload/download endpoints, WebSockets progress streaming, and background pipeline execution.
"""

from pathlib import Path
import os
import time
import uuid
import asyncio
import shutil
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    UPLOADS_DIR, PROCESSED_DIR, TEMP_DIR, READY_EXPORT_DIR,
    EXPORTS_VIRAL_SHORTS_DIR, EXPORTS_FULL_VIDEOS_DIR, EXPORTS_REDDIT_STORIES_DIR,
    EXPORTS_PODCAST_CLIPS_DIR, EXPORTS_THUMBNAILS_DIR, EXPORTS_AUDIO_STEMS_DIR,
    EXPORTS_METADATA_DIR, EXPORTS_BATCH_DIR, ALL_EXPORT_DIRS,
    FRONTEND_DIST_DIR, HAS_NVENC, is_nvenc_available, BACKEND_DIR, STORAGE_DIR
)
from app.export_manager import ExportManager
from app.schemas import (
    TransformParams, JobStatus, StageType, PresetType,
    DownloadUrlRequest, AutoViralRequest, AcceptVideoRequest, RejectVideoRequest
)
from app.presets import PRESET_CONFIGS, get_preset_params
from app.audio_engine import AudioEngine
from app.pipeline import VideoPipeline, VideoProbe
from app.auto_viral import AutoViralEngine
from app.editor_schemas import (
    GenerateTTSRequest, ParseScriptRequest, GenerateScriptFromTopicRequest, AIShortsRenderRequest,
    BatchAutoPilotRequest, GenerateThumbnailRequest, GenerateMetadataRequest, RedditStoryRequest, StockSearchRequest,
    PodcastDialogueRequest, TrendToScriptRequest, TelegramBotRequest,
    GeminiPoolKeysRequest, GeminiTestKeysRequest, GeminiKeyRemoveRequest, ExportVideoRequest
)
from app.gemini_pool import gemini_pool, parse_raw_keys
from app.tts_engine import TTSEngine
from app.scene_director import SceneDirector
from app.editor_engine import AIShortsRenderer
from app.broll_harvester import BRollHarvester
from app.thumbnail_generator import ThumbnailGenerator
from app.meta_generator import MetaGenerator
from app.reddit_generator import RedditStoryGenerator
from app.trend_harvester import TrendHarvester
from app.podcast_generator import PodcastShortsGenerator
from app.telegram_bot import TelegramStudioBot
from app.motion_tracker import SmartMotionTracker
from app.batch_autopilot import BatchAutoPilotEngine, BATCH_JOBS
from app.audio_assets import ASSETS_DIR, BGM_DIR, SFX_DIR, init_default_audio_assets


# Initialize audio assets on startup
init_default_audio_assets()


app = FastAPI(
    title="CR Remover Studio",
    description="Automated Video Transformation & Remixing Studio",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory jobs tracking
JOBS: Dict[str, JobStatus] = {}

# Active WebSocket connections per job
WS_CONNECTIONS: Dict[str, List[WebSocket]] = {}


async def broadcast_progress(job_id: str, message: str, progress: int, stage: StageType):
    """Updates job status and broadcasts update to connected WebSockets."""
    if job_id in JOBS:
        # Do not overwrite COMPLETED or FAILED with intermediate steps
        if JOBS[job_id].status in (StageType.COMPLETED, StageType.FAILED) and stage not in (StageType.COMPLETED, StageType.FAILED):
            return
        JOBS[job_id].current_stage = message
        JOBS[job_id].progress = progress
        JOBS[job_id].status = stage

    if job_id in WS_CONNECTIONS:
        payload = {
            "job_id": job_id,
            "status": stage.value,
            "progress": progress,
            "current_stage": message
        }
        dead_sockets = []
        for ws in WS_CONNECTIONS[job_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            WS_CONNECTIONS[job_id].remove(ws)


async def execute_job(job_id: str, input_file: Path, params: TransformParams):
    """Background task executing the complete transformation pipeline."""
    try:
        await broadcast_progress(job_id, "Analyzing video format & streams...", 5, StageType.PROBING)
        
        # Probe video
        meta = await VideoProbe.probe(input_file)
        duration = meta.get("duration", 0.0)
        JOBS[job_id].duration_seconds = duration

        # Extract audio to temp file
        raw_audio_temp = TEMP_DIR / f"{job_id}_raw.wav"
        processed_audio_temp = TEMP_DIR / f"{job_id}_proc.aac"

        extract_cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(raw_audio_temp)
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *extract_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        # Step 1: Process Audio Engine
        await broadcast_progress(job_id, "Transforming audio & pitch shifts...", 15, StageType.AUDIO_PROCESSING)
        
        def audio_cb(msg: str, prog: int):
            asyncio.create_task(broadcast_progress(job_id, msg, prog, StageType.AUDIO_PROCESSING))

        await AudioEngine.process_audio(
            raw_audio_temp,
            processed_audio_temp,
            params,
            duration,
            progress_callback=audio_cb
        )

        # Step 2: Process Video Pipeline
        output_filename = f"cr_clean_{input_file.name}"
        output_path = PROCESSED_DIR / f"{job_id}_{output_filename}"

        await broadcast_progress(job_id, "Rendering Video Transformations...", 50, StageType.VIDEO_RENDERING)

        def video_cb(msg: str, prog: int):
            asyncio.create_task(broadcast_progress(job_id, msg, prog, StageType.VIDEO_RENDERING))

        await VideoPipeline.render_video(
            input_file,
            processed_audio_temp,
            output_path,
            params,
            duration,
            progress_callback=video_cb
        )

        # Finalize
        if output_path.exists():
            JOBS[job_id].processed_size_bytes = output_path.stat().st_size
            JOBS[job_id].output_filename = output_filename
            JOBS[job_id].output_url = f"/api/media/processed/{job_id}_{output_filename}"
            await broadcast_progress(job_id, "Transformation Complete!", 100, StageType.COMPLETED)
        else:
            raise FileNotFoundError("Output video file was not generated.")

    except Exception as e:
        JOBS[job_id].status = StageType.FAILED
        JOBS[job_id].error_message = str(e)
        await broadcast_progress(job_id, f"Failed: {str(e)}", 100, StageType.FAILED)
    finally:
        # Cleanup intermediate temp files
        for f in TEMP_DIR.glob(f"{job_id}*"):
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
            except Exception:
                pass


@app.get("/api/system")
async def get_system_info():
    """Returns GPU status, NVENC support, and system capabilities."""
    has_nvenc = is_nvenc_available()
    has_demucs = AudioEngine.is_demucs_installed()
    return {
        "gpu_detected": True,
        "gpu_name": "NVIDIA GeForce GTX 1650",
        "nvenc_accelerated": has_nvenc,
        "demucs_ai_available": has_demucs,
        "ffmpeg_available": shutil.which("ffmpeg") is not None
    }


@app.get("/api/presets")
async def get_presets():
    """Returns list of pre-configured transformation profiles."""
    return PRESET_CONFIGS


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Uploads a video file and returns file metadata."""
    job_id = str(uuid.uuid4())[:8]
    clean_name = file.filename.replace(" ", "_")
    saved_path = UPLOADS_DIR / f"{job_id}_{clean_name}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = saved_path.stat().st_size
    meta = await VideoProbe.probe(saved_path)

    job = JobStatus(
        job_id=job_id,
        filename=clean_name,
        status=StageType.QUEUED,
        progress=0,
        current_stage="Uploaded",
        original_size_bytes=file_size,
        duration_seconds=meta.get("duration", 0.0),
        created_at=time.time()
    )
    JOBS[job_id] = job

    return {
        "job_id": job_id,
        "filename": clean_name,
        "size_bytes": file_size,
        "duration_seconds": meta.get("duration", 0.0),
        "resolution": f"{meta.get('width', 0)}x{meta.get('height', 0)}",
        "fps": meta.get("fps", 30.0),
        "video_url": f"/api/media/uploads/{job_id}_{clean_name}"
    }


@app.post("/api/download-url")
async def download_video_from_url(payload: DownloadUrlRequest):
    """Downloads a video from YouTube / Instagram / TikTok / URL using yt-dlp and probes it."""
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    job_id = str(uuid.uuid4())[:8]
    output_template = str(UPLOADS_DIR / f"{job_id}_%(title).40s.%(ext)s")

    yt_dlp_bin = BACKEND_DIR.parent / "venv" / "bin" / "yt-dlp"
    if not yt_dlp_bin.exists():
        yt_dlp_bin = "yt-dlp"

    cmd = [
        str(yt_dlp_bin),
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        "--max-filesize", "500M",
        url
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr.decode(errors="ignore") if stderr else "Failed to download video from URL"
        raise HTTPException(status_code=400, detail=f"Download failed: {err_msg[:250]}")

    matching = list(UPLOADS_DIR.glob(f"{job_id}_*"))
    if not matching:
        raise HTTPException(status_code=500, detail="Downloaded video file not found on disk")

    downloaded_file = matching[0]
    file_size = downloaded_file.stat().st_size
    meta = await VideoProbe.probe(downloaded_file)
    clean_name = downloaded_file.name[len(job_id) + 1:]

    job = JobStatus(
        job_id=job_id,
        filename=clean_name,
        status=StageType.QUEUED,
        progress=0,
        current_stage="Downloaded & Probed",
        original_size_bytes=file_size,
        duration_seconds=meta.get("duration", 0.0),
        created_at=time.time()
    )
    JOBS[job_id] = job

    return {
        "job_id": job_id,
        "filename": clean_name,
        "size_bytes": file_size,
        "duration_seconds": meta.get("duration", 0.0),
        "resolution": f"{meta.get('width', 0)}x{meta.get('height', 0)}",
        "fps": meta.get("fps", 30.0),
        "video_url": f"/api/media/uploads/{downloaded_file.name}"
    }


# Auto-Viral Jobs Tracking
AUTO_VIRAL_JOBS: Dict[str, Dict[str, Any]] = {}


@app.post("/api/auto-viral/start")
async def start_auto_viral_pipeline(
    payload: AutoViralRequest,
    background_tasks: BackgroundTasks
):
    """Launches automated search, GPU transformation, Gemini titling, and export to ~/Downloads."""
    job_id = str(uuid.uuid4())[:8]
    AUTO_VIRAL_JOBS[job_id] = {
        "job_id": job_id,
        "status": "in_progress",
        "progress": 5,
        "current_stage": "Starting automated viral search...",
        "results": [],
        "export_dir": str(READY_EXPORT_DIR)
    }

    params = get_preset_params(payload.preset)

    async def run_bg():
        def cb(msg: str, prog: int):
            AUTO_VIRAL_JOBS[job_id]["current_stage"] = msg
            AUTO_VIRAL_JOBS[job_id]["progress"] = prog

        try:
            results = await AutoViralEngine.run_pipeline(
                topic=payload.topic,
                count=payload.count,
                params=params,
                gemini_api_key=payload.gemini_api_key or "",
                min_views=payload.min_views,
                recency=payload.recency,
                language_lock=payload.language_lock,
                channel_feed=payload.channel_feed or "",
                progress_callback=cb
            )
            AUTO_VIRAL_JOBS[job_id]["status"] = "completed"
            AUTO_VIRAL_JOBS[job_id]["progress"] = 100
            AUTO_VIRAL_JOBS[job_id]["current_stage"] = f"Processed {len(results)} viral Shorts ready for review!"
            AUTO_VIRAL_JOBS[job_id]["results"] = results
        except Exception as e:
            AUTO_VIRAL_JOBS[job_id]["status"] = "failed"
            AUTO_VIRAL_JOBS[job_id]["error_message"] = str(e)
            AUTO_VIRAL_JOBS[job_id]["current_stage"] = f"Failed: {str(e)}"

    background_tasks.add_task(run_bg)
    return {"job_id": job_id, "status": "started", "export_dir": str(READY_EXPORT_DIR)}


@app.get("/api/auto-viral/status/{job_id}")
async def get_auto_viral_status(job_id: str):
    """Returns real-time status of the automated viral pipeline."""
    job = AUTO_VIRAL_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Auto-viral job not found")
    return job


@app.post("/api/auto-viral/accept")
async def accept_viral_video(payload: AcceptVideoRequest):
    """Accepts a reviewed video, saves clean MP4 & metadata to ~/Desktop/CR_Remover_Exports/01_Viral_Shorts/."""
    source_file = PROCESSED_DIR / payload.clean_id
    if not source_file.exists():
        raise HTTPException(status_code=404, detail="Processed video file not found")

    # Build standardized descriptive filename
    title_seed = payload.original_title or (payload.titles[0] if payload.titles else payload.filename)
    descriptive_name = ExportManager.name_viral_short(title_seed, preset="AutoViral", aspect="9x16")

    meta_payload = {
        "titles": payload.titles if payload.titles else [title_seed],
        "hook": payload.hook,
        "description": payload.description,
        "tags": ["viral", "shorts", "trending", "youtube_shorts", "reels"]
    }

    # Export to categorized desktop folder
    exported = ExportManager.export_video_to_category(
        source_video_path=source_file,
        category="viral_shorts",
        descriptive_filename=descriptive_name,
        metadata_dict=meta_payload
    )

    return {
        "status": "saved",
        "video_path": exported["video_path"],
        "info_path": exported.get("metadata_path"),
        "filename": descriptive_name,
        "category": exported.get("category", "01_Viral_Shorts")
    }


@app.post("/api/auto-viral/reject")
async def reject_viral_video(payload: RejectVideoRequest):
    """Rejects and permanently deletes a candidate video to free disk space."""
    source_file = PROCESSED_DIR / payload.clean_id
    if source_file.exists():
        try:
            source_file.unlink()
        except Exception:
            pass
    return {"status": "rejected", "clean_id": payload.clean_id}


@app.post("/api/transform/{job_id}")
async def start_transform(
    job_id: str,
    params: TransformParams,
    background_tasks: BackgroundTasks
):
    """Starts transformation on an uploaded video."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    input_file = UPLOADS_DIR / f"{job_id}_{job.filename}"
    if not input_file.exists():
        raise HTTPException(status_code=404, detail="Uploaded file missing on server")

    job.status = StageType.QUEUED
    job.progress = 0
    job.current_stage = "Job started..."

    background_tasks.add_task(execute_job, job_id, input_file, params)
    return {"job_id": job_id, "status": "processing_started"}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Returns current status of a job."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# =====================================================================
# AI SHORTS CREATOR & VOICE INJECTION ENDPOINTS
# =====================================================================

@app.get("/api/ai-shorts/voices")
async def get_ai_voices():
    """Returns curated list of neural TTS voices."""
    return TTSEngine.get_voices()


@app.post("/api/ai-shorts/generate-script")
async def generate_ai_script(payload: GenerateScriptFromTopicRequest):
    """Generates a high-retention viral Shorts script from a topic."""
    return await SceneDirector.generate_script(
        topic=payload.topic,
        tone=payload.tone,
        target_duration=payload.target_duration,
        gemini_api_key=payload.gemini_api_key
    )


@app.post("/api/ai-shorts/parse-script")
async def parse_ai_script(payload: ParseScriptRequest):
    """Breaks down a script into timed scenes with visual keywords and SFX."""
    scenes = await SceneDirector.parse_script_to_scenes(
        script_text=payload.script_text,
        gemini_api_key=payload.gemini_api_key
    )
    return {"scenes": [sc.model_dump() for sc in scenes]}


@app.post("/api/ai-shorts/generate-tts")
async def generate_ai_tts(payload: GenerateTTSRequest):
    """Generates speech audio with word-level boundary synchronization."""
    file_id = str(uuid.uuid4())[:8]
    output_audio = TEMP_DIR / f"tts_{file_id}.mp3"

    result = await TTSEngine.generate_speech_with_timings(
        text=payload.text,
        voice_name=payload.voice_name,
        speed_factor=payload.speed_factor,
        pitch_cents=payload.pitch_cents,
        output_file=output_audio
    )

    audio_url = f"/api/media/temp/{output_audio.name}"
    result["audio_url"] = audio_url
    return result


@app.post("/api/ai-shorts/upload-voice")
async def upload_custom_voice(file: UploadFile = File(...)):
    """Uploads a custom voiceover audio file for voice injection."""
    file_id = str(uuid.uuid4())[:8]
    clean_name = file.filename.replace(" ", "_")
    dest_path = UPLOADS_DIR / f"voice_{file_id}_{clean_name}"

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Probe duration
    meta = await VideoProbe.probe(dest_path)
    dur = meta.get("duration", 0.0)

    return {
        "file_path": str(dest_path),
        "audio_url": f"/api/media/uploads/{dest_path.name}",
        "filename": clean_name,
        "duration": dur
    }


@app.get("/api/ai-shorts/bgm-list")
async def get_bgm_assets():
    """Returns list of curated royalty-free BGM tracks and SFX."""
    bgm_tracks = [
        {"id": "phonk_drive", "name": "Phonk Drive (Drift / High Energy)", "bpm": 140, "genre": "Phonk / Viral"},
        {"id": "lofi_chill", "name": "Lo-Fi Chill (Warm / Relaxed)", "bpm": 80, "genre": "Lo-Fi / Study"},
        {"id": "deep_tension", "name": "Deep Tension (Cinematic / Mystery)", "bpm": 95, "genre": "Suspense"},
        {"id": "epic_discovery", "name": "Epic Discovery (Harmonic Pad)", "bpm": 100, "genre": "Documentary"},
        {"id": "upbeat_viral", "name": "Upbeat Viral (Pop Arp)", "bpm": 125, "genre": "Tech / Viral"},
        {"id": "none", "name": "No Background Music", "bpm": 0, "genre": "Mute"}
    ]
    sfx_list = [
        {"id": "whoosh", "name": "Whoosh Transition"},
        {"id": "bass_drop", "name": "Sub-Bass Drop Hook"},
        {"id": "ding", "name": "Chime Ding"},
        {"id": "glitch", "name": "Glitch FX"}
    ]
    return {"bgm_tracks": bgm_tracks, "sfx_list": sfx_list}


async def execute_shorts_job(job_id: str, request: AIShortsRenderRequest):
    """Background task executing the complete AI Shorts rendering pipeline."""
    try:
        await broadcast_progress(job_id, "Compiling multi-scene storyboard...", 10, StageType.VIDEO_RENDERING)

        def progress_cb(msg: str, prog: int):
            asyncio.create_task(broadcast_progress(job_id, msg, prog, StageType.VIDEO_RENDERING))

        output_path = await AIShortsRenderer.render_shorts(request, progress_callback=progress_cb)

        if output_path.exists():
            JOBS[job_id].processed_size_bytes = output_path.stat().st_size
            JOBS[job_id].output_filename = output_path.name
            JOBS[job_id].output_url = f"/api/media/processed/{output_path.name}"
            await broadcast_progress(job_id, "AI Short Rendered Successfully!", 100, StageType.COMPLETED)
        else:
            raise FileNotFoundError("Output AI Short file was not generated.")
    except Exception as e:
        JOBS[job_id].status = StageType.FAILED
        JOBS[job_id].error_message = str(e)
        await broadcast_progress(job_id, f"Rendering Failed: {str(e)}", 100, StageType.FAILED)


@app.post("/api/ai-shorts/render")
async def render_ai_shorts(request: AIShortsRenderRequest, background_tasks: BackgroundTasks):
    """Submits an AI Shorts render job with real-time WebSocket progress."""
    job_id = request.project_id or str(uuid.uuid4())[:8]

    job = JobStatus(
        job_id=job_id,
        filename=f"{request.title}.mp4",
        status=StageType.QUEUED,
        progress=0,
        current_stage="Queued for 9:16 Shorts rendering...",
        created_at=time.time()
    )
    JOBS[job_id] = job

    background_tasks.add_task(execute_shorts_job, job_id, request)
    return {"job_id": job_id, "status": "rendering_started"}


@app.get("/api/media/{folder}/{filename}")
async def stream_media(folder: str, filename: str):
    """Streams uploaded, processed, assets, temp, or ready-exported media files."""
    import urllib.parse
    clean_name = urllib.parse.unquote(filename)

    if folder == "uploads":
        base_dir = UPLOADS_DIR
    elif folder == "processed":
        base_dir = PROCESSED_DIR
    elif folder in ("ready", "exports"):
        base_dir = READY_EXPORT_DIR
    elif folder in ("viral_shorts", "01_Viral_Shorts"):
        base_dir = EXPORTS_VIRAL_SHORTS_DIR
    elif folder in ("full_videos", "02_Full_Edited_Videos"):
        base_dir = EXPORTS_FULL_VIDEOS_DIR
    elif folder in ("reddit", "03_Reddit_Stories"):
        base_dir = EXPORTS_REDDIT_STORIES_DIR
    elif folder in ("podcast", "04_Podcast_Clips"):
        base_dir = EXPORTS_PODCAST_CLIPS_DIR
    elif folder in ("thumbnails", "05_Thumbnails_Covers"):
        base_dir = EXPORTS_THUMBNAILS_DIR
    elif folder in ("audio", "06_Audio_Stems_Voice"):
        base_dir = EXPORTS_AUDIO_STEMS_DIR
    elif folder in ("metadata", "07_Metadata_Captions"):
        base_dir = EXPORTS_METADATA_DIR
    elif folder in ("batch", "08_Batch_Campaigns"):
        base_dir = EXPORTS_BATCH_DIR
    elif folder == "temp":
        base_dir = TEMP_DIR
    elif folder == "assets":
        base_dir = STORAGE_DIR / "assets"
    else:
        raise HTTPException(status_code=400, detail="Invalid folder")

    file_path = base_dir / clean_name

    if not file_path.exists():
        # Fallback by job prefix in case of special character sanitization
        prefix = clean_name.split("_")[0] if "_" in clean_name else clean_name[:8]
        matching = list(base_dir.glob(f"*{prefix}*"))
        if matching:
            file_path = matching[0]
        else:
            raise HTTPException(status_code=404, detail=f"Media file not found: {clean_name}")

    # Determine media type
    media_type = "video/mp4"
    if file_path.suffix.lower() in (".mp3", ".wav", ".aac", ".ogg", ".m4a"):
        media_type = f"audio/{file_path.suffix[1:].lower()}"
    elif file_path.suffix.lower() == ".webm":
        media_type = "video/webm"

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name
    )


@app.get("/api/download/{job_id}")
async def download_processed(job_id: str):
    """Triggers direct download of the processed video file."""
    # Find matching file in PROCESSED_DIR by job_id prefix using iterdir (safe against special characters)
    matching = [f for f in PROCESSED_DIR.iterdir() if job_id in f.name and f.is_file()]
    if not matching:
        job = JOBS.get(job_id)
        if job and job.output_filename:
            f = PROCESSED_DIR / job.output_filename
            if f.exists():
                matching = [f]

    if not matching:
        raise HTTPException(status_code=404, detail="Processed video file not found")

    file_path = matching[0]
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=file_path.name
    )


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress events."""
    await websocket.accept()
    if job_id not in WS_CONNECTIONS:
        WS_CONNECTIONS[job_id] = []
    WS_CONNECTIONS[job_id].append(websocket)

    # Send current state immediately
    if job_id in JOBS:
        job = JOBS[job_id]
        await websocket.send_json({
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress,
            "current_stage": job.current_stage
        })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if job_id in WS_CONNECTIONS and websocket in WS_CONNECTIONS[job_id]:
            WS_CONNECTIONS[job_id].remove(websocket)


# =====================================================================
# 1-CLICK AUTO-PILOT BATCH FACTORY & CREATOR SUITE ENDPOINTS
# =====================================================================

@app.get("/api/autopilot/niches")
async def get_autopilot_niches():
    """Returns curated viral niches with sample topics and default styling."""
    return BatchAutoPilotEngine.get_niches()


@app.post("/api/autopilot/start")
async def start_batch_autopilot(
    payload: BatchAutoPilotRequest,
    background_tasks: BackgroundTasks
):
    """Starts autonomous batch generation of multiple Shorts with full assets."""
    batch_id = str(uuid.uuid4())[:8]
    BATCH_JOBS[batch_id] = {
        "batch_id": batch_id,
        "niche_id": payload.niche_id,
        "status": "in_progress",
        "progress": 5,
        "current_stage": "Starting autonomous batch rendering engine...",
        "results": [],
        "export_dir": str(READY_EXPORT_DIR)
    }

    async def run_batch_bg():
        def cb(msg: str, prog: int, extra_data: dict):
            BATCH_JOBS[batch_id]["current_stage"] = msg
            BATCH_JOBS[batch_id]["progress"] = prog
            if extra_data:
                BATCH_JOBS[batch_id]["extra"] = extra_data

        try:
            results = await BatchAutoPilotEngine.run_batch(
                batch_id=batch_id,
                niche_id=payload.niche_id,
                count=payload.count,
                voice_name=payload.voice_name,
                bgm_track=payload.bgm_track,
                subtitle_style=payload.subtitle_style,
                broll_category=payload.broll_category,
                custom_topics=payload.custom_topics,
                gemini_api_key=payload.gemini_api_key or "",
                progress_callback=cb
            )
            BATCH_JOBS[batch_id]["status"] = "completed"
            BATCH_JOBS[batch_id]["progress"] = 100
            BATCH_JOBS[batch_id]["current_stage"] = f"Generated {len(results)} viral Shorts ready in ~/Downloads!"
            BATCH_JOBS[batch_id]["results"] = results
        except Exception as e:
            BATCH_JOBS[batch_id]["status"] = "failed"
            BATCH_JOBS[batch_id]["error_message"] = str(e)
            BATCH_JOBS[batch_id]["current_stage"] = f"Auto-Pilot Failed: {str(e)}"

    background_tasks.add_task(run_batch_bg)
    return {"batch_id": batch_id, "status": "started", "export_dir": str(READY_EXPORT_DIR)}


@app.get("/api/autopilot/status/{batch_id}")
async def get_batch_status(batch_id: str):
    """Returns real-time progress and generated Shorts for a batch."""
    job = BATCH_JOBS.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return job


@app.get("/api/broll/categories")
async def get_broll_categories():
    """Returns curated stock video categories and looping clips."""
    await BRollHarvester.ensure_default_broll_assets()
    return BRollHarvester.get_categories()


@app.post("/api/broll/search")
async def search_broll_stock(payload: StockSearchRequest):
    """Searches stock video vault or Pexels API."""
    return await BRollHarvester.search_pexels_videos(
        query=payload.query,
        api_key=payload.pexels_api_key or "",
        count=payload.count
    )


@app.post("/api/thumbnail/generate")
async def generate_video_thumbnail(payload: GenerateThumbnailRequest):
    """Generates high-CTR 9:16 cover thumbnail image for a video."""
    video_p = Path(payload.video_path)
    if not video_p.exists():
        # Look in processed or uploads
        match = list(STORAGE_DIR.glob(f"**/{video_p.name}"))
        if match:
            video_p = match[0]
        else:
            raise HTTPException(status_code=404, detail="Source video not found")

    cover_path = await ThumbnailGenerator.generate_cover(
        video_path=video_p,
        hook_text=payload.hook_text,
        badge_text=payload.badge_text,
        style_key=payload.style_key,
        timestamp_sec=payload.timestamp_sec
    )
    return {
        "cover_url": f"/api/media/processed/{cover_path.name}",
        "cover_path": str(cover_path)
    }


@app.post("/api/metadata/generate")
async def generate_seo_metadata(payload: GenerateMetadataRequest):
    """Generates viral SEO titles, description, tags, and pinned comment."""
    return await MetaGenerator.generate_metadata(
        topic=payload.topic,
        script_summary=payload.script_summary,
        niche=payload.niche,
        gemini_api_key=payload.gemini_api_key
    )


@app.post("/api/reddit/generate-story")
async def generate_reddit_story(payload: RedditStoryRequest):
    """Generates a viral Reddit drama story and authentic UI card overlay."""
    story = await RedditStoryGenerator.generate_story(
        subreddit=payload.subreddit,
        custom_prompt=payload.custom_prompt,
        gemini_api_key=payload.gemini_api_key
    )
    card_path = RedditStoryGenerator.create_reddit_card_image(
        subreddit=story.get("subreddit", "r/AskReddit"),
        author=story.get("author", "u/User"),
        title=story.get("title", ""),
        upvotes=story.get("upvotes", "25.1k")
    )
    story["card_url"] = f"/api/media/temp/{card_path.name}"
    story["card_path"] = str(card_path)
    return story


@app.get("/api/trends/live")
async def get_live_trends(category: str = "all", region: str = "US"):
    """Fetches real-time viral trends from Google Trends and news feeds."""
    return await TrendHarvester.fetch_live_trends(category=category, region=region)


@app.post("/api/trends/to-script")
async def convert_trend_to_script(payload: TrendToScriptRequest):
    """Converts a live breaking news topic into a high-retention Shorts script."""
    return await TrendHarvester.trend_to_script(
        trend_title=payload.trend_title,
        summary=payload.summary,
        gemini_api_key=payload.gemini_api_key
    )


@app.post("/api/podcast/generate-dialogue")
async def generate_podcast_dialogue(payload: PodcastDialogueRequest):
    """Generates 2-person debate/interview dialogue turns."""
    return await PodcastShortsGenerator.generate_dialogue(
        topic=payload.topic,
        style=payload.style,
        gemini_api_key=payload.gemini_api_key
    )


@app.post("/api/podcast/synthesize")
async def synthesize_podcast_audio(payload: PodcastDialogueRequest):
    """Synthesizes alternating 2-voice audio with global word timestamps."""
    dialogue = await PodcastShortsGenerator.generate_dialogue(
        topic=payload.topic,
        style=payload.style,
        gemini_api_key=payload.gemini_api_key
    )
    audio_res = await PodcastShortsGenerator.synthesize_dual_audio(
        dialogue=dialogue,
        host_voice=payload.host_voice,
        guest_voice=payload.guest_voice
    )
    return {"dialogue": dialogue, "audio": audio_res}


@app.post("/api/podcast/render-short")
async def render_podcast_short_endpoint(payload: PodcastDialogueRequest):
    """Generates and fully renders a 2-person podcast split-screen Short with desktop export."""
    dialogue = await PodcastShortsGenerator.generate_dialogue(
        topic=payload.topic,
        style=payload.style,
        gemini_api_key=payload.gemini_api_key
    )
    out_video = await PodcastShortsGenerator.render_split_screen_short(
        dialogue=dialogue,
        host_voice=payload.host_voice,
        guest_voice=payload.guest_voice
    )
    
    # Export to 04_Podcast_Clips/
    descriptive_name = ExportManager.name_podcast_short(dialogue.get("title", payload.topic))
    exported = ExportManager.export_video_to_category(
        source_video_path=out_video,
        category="podcast",
        descriptive_filename=descriptive_name,
        metadata_dict={
            "titles": [dialogue.get("title", payload.topic)],
            "hook": "Wait until you hear this perspective...",
            "description": f"AI Podcast Debate on {payload.topic} #podcast #debate #shorts"
        }
    )

    return {
        "status": "completed",
        "video_url": f"/api/media/processed/{out_video.name}",
        "filename": descriptive_name,
        "title": dialogue.get("title", "Podcast Short"),
        "export_path": exported["video_path"],
        "category": "04_Podcast_Clips"
    }


@app.post("/api/reddit/render-short")
async def render_reddit_short_endpoint(payload: RedditStoryRequest):
    """Generates and fully renders a viral Reddit drama story Short over gameplay with desktop export."""
    story = await RedditStoryGenerator.generate_story(
        subreddit=payload.subreddit,
        custom_prompt=payload.custom_prompt,
        gemini_api_key=payload.gemini_api_key
    )
    out_video = await RedditStoryGenerator.render_reddit_short(
        story=story,
        voice_name="en-US-GuyNeural",
        gameplay_broll="minecraft_parkour"
    )

    # Export to 03_Reddit_Stories/
    descriptive_name = ExportManager.name_reddit_story(payload.subreddit, story.get("title", "Story"))
    exported = ExportManager.export_video_to_category(
        source_video_path=out_video,
        category="reddit",
        descriptive_filename=descriptive_name,
        metadata_dict={
            "titles": [story.get("title", "Reddit Story")],
            "hook": "This actually happened to someone...",
            "description": f"Reddit story from {payload.subreddit} #redditstories #askreddit #drama"
        }
    )

    return {
        "status": "completed",
        "video_url": f"/api/media/processed/{out_video.name}",
        "filename": descriptive_name,
        "title": story.get("title", "Reddit Story"),
        "export_path": exported["video_path"],
        "category": "03_Reddit_Stories"
    }


# =====================================================================
# ORGANIZED DESKTOP EXPORTS & ASSET EXPLORER ENDPOINTS
# =====================================================================

@app.post("/api/exports/export-video")
async def export_single_video(payload: ExportVideoRequest):
    """
    1-Click exports a processed video into the appropriate Desktop category folder
    with a crystal-clear, self-describing filename.
    """
    # 1. Locate the processed video file
    matching = [f for f in PROCESSED_DIR.iterdir() if payload.job_id in f.name and f.is_file()]
    if not matching:
        job = JOBS.get(payload.job_id)
        if job and job.output_filename:
            f = PROCESSED_DIR / job.output_filename
            if f.exists():
                matching = [f]

    if not matching:
        raise HTTPException(status_code=404, detail="Processed video file not found")

    source_video = matching[0]

    # 2. Build standardized descriptive name
    title = payload.title or source_video.name
    aspect = payload.aspect or "16x9"
    preset = payload.preset or "youtube_bypass"

    if payload.category in ("viral_shorts", "01_Viral_Shorts") or aspect == "9x16":
        descriptive_name = ExportManager.name_viral_short(title, preset=preset, aspect="9x16")
        cat_target = "viral_shorts"
    else:
        descriptive_name = ExportManager.name_full_video(title, preset=preset, aspect=aspect)
        cat_target = "full_videos"

    # 3. Export to Desktop organized folder
    exported = ExportManager.export_video_to_category(
        source_video_path=source_video,
        category=cat_target,
        descriptive_filename=descriptive_name,
        metadata_dict={
            "titles": [title],
            "description": f"Processed with CR Remover Studio ({preset}) #clean #video"
        }
    )

    return {
        "status": "exported",
        "video_path": exported["video_path"],
        "filename": descriptive_name,
        "category": exported.get("category", cat_target),
        "folder": exported.get("folder")
    }


@app.post("/api/exports/open-folder")
@app.post("/api/exports/open-desktop-folder")
async def open_desktop_exports_folder():
    """Opens ~/Desktop/CR_Remover_Exports/ in the native OS file explorer."""
    return ExportManager.open_exports_folder()


@app.get("/api/exports/summary")
async def get_desktop_exports_summary():
    """Returns a full categorized overview and file tree of all desktop exports."""
    return ExportManager.get_exports_summary()


@app.post("/api/broll/upload")
async def upload_custom_broll(file: UploadFile = File(...)):
    """Uploads a custom video clip directly into the Stock B-Roll vault."""
    from app.broll_harvester import BROLL_DIR
    clean_name = file.filename.replace(" ", "_")
    dest_path = BROLL_DIR / f"custom_{clean_name}"
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "status": "saved",
        "filename": dest_path.name,
        "video_url": f"/api/media/assets/broll/{dest_path.name}"
    }


@app.post("/api/telegram/control")
async def control_telegram_bot(
    payload: TelegramBotRequest,
    background_tasks: BackgroundTasks
):

    """Starts, stops, or sends test message through Telegram Remote Control Bot."""
    if payload.action == "test_message":
        await TelegramStudioBot.send_message(
            payload.bot_token, payload.chat_id,
            "🚀 *CR Remover Studio Test Message*\nYour Telegram remote control bot is connected and operational!"
        )
        return {"status": "test_sent"}
    elif payload.action == "start":
        if not TelegramStudioBot.is_running():
            background_tasks.add_task(TelegramStudioBot.poll_updates, payload.bot_token, payload.chat_id)
        return {"status": "bot_started"}
    else:
        return {"status": "online" if TelegramStudioBot.is_running() else "idle"}


@app.get("/api/gemini/pool-status")
async def get_gemini_pool_status():
    """Returns the current status, health, and list of Gemini API keys in the rotation pool."""
    return gemini_pool.get_status()


@app.post("/api/gemini/pool-keys")
async def update_gemini_pool_keys(payload: GeminiPoolKeysRequest):
    """Sets or registers multiple Gemini API keys in the persistent pool."""
    keys_input = payload.keys if payload.keys else payload.keys_text
    parsed = gemini_pool.set_keys(keys_input, persist=payload.persist)
    return {
        "status": "success",
        "keys_count": len(parsed),
        "pool": gemini_pool.get_status()
    }


@app.post("/api/gemini/test-keys")
async def test_gemini_keys(payload: GeminiTestKeysRequest):
    """Tests specified keys (or all configured pool keys) with live latency and health verification."""
    keys_input = payload.keys if payload.keys else payload.keys_text
    test_results = await gemini_pool.test_all_keys(keys_input)
    return {
        "results": test_results,
        "pool": gemini_pool.get_status()
    }


@app.post("/api/gemini/remove-key")
async def remove_gemini_key(payload: GeminiKeyRemoveRequest):
    """Removes a key from the persistent rotation pool."""
    removed = gemini_pool.remove_key(payload.key)
    return {
        "removed": removed,
        "pool": gemini_pool.get_status()
    }


# Mount built React frontend if dist exists
if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST_DIR), html=True), name="frontend")



