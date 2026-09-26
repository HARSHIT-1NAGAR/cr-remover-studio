"""
Pydantic schemas and data models for CR Remover Studio.
Enforces strict validation, typing, and default presets.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PresetType(str, Enum):
    YOUTUBE_BYPASS = "youtube_bypass"
    INSTA_SHORTS = "insta_shorts"
    AI_DEEP_CLEAN = "ai_deep_clean"
    VOCAL_ONLY = "vocal_only"
    CUSTOM = "custom"


class StageType(str, Enum):
    QUEUED = "queued"
    PROBING = "probing"
    AI_SEPARATING = "ai_separating"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_RENDERING = "video_rendering"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadUrlRequest(BaseModel):
    """Schema for downloading a video from a URL (YouTube, TikTok, Insta)."""
    url: str = Field(..., description="Target video URL")


class AutoViralRequest(BaseModel):
    """Schema for automated viral hunt and export pipeline."""
    topic: str = Field(..., description="Topic, niche keyword, or @channel handle")
    count: int = Field(default=3, ge=1, le=10, description="Number of viral videos to process")
    gemini_api_key: Optional[str] = Field(default="", description="Google Gemini API Key")
    preset: PresetType = Field(default=PresetType.YOUTUBE_BYPASS, description="Preset configuration")
    min_views: int = Field(default=500_000, description="Minimum view count threshold (e.g. 500000, 1000000)")
    recency: str = Field(default="this_year", description="all_time | this_year | this_month | this_week")
    language_lock: str = Field(default="en", description="en (English only) | any")
    channel_feed: Optional[str] = Field(default="", description="Specific channel handle or curated category")


class AcceptVideoRequest(BaseModel):
    """Schema to accept and save a reviewed video to Downloads."""
    clean_id: str = Field(..., description="Internal processed video filename")
    filename: str = Field(..., description="Target clean filename")
    titles: List[str] = Field(default_factory=list, description="Viral titles")
    hook: str = Field(default="", description="Pinned comment hook")
    description: str = Field(default="", description="Description and hashtags")
    original_title: Optional[str] = ""


class RejectVideoRequest(BaseModel):
    """Schema to reject and discard a reviewed video."""
    clean_id: str = Field(..., description="Internal processed video filename to delete")


class TransformParams(BaseModel):
    """Configuration parameters for video transformation."""
    preset: PresetType = Field(default=PresetType.YOUTUBE_BYPASS, description="Preset configuration profile")
    
    # Video geometric & spatial parameters
    mirror_flip: bool = Field(default=False, description="Horizontally flip/mirror video (Default OFF)")
    ken_burns_zoom: float = Field(default=1.07, ge=1.0, le=1.3, description="Continuous dynamic zoom factor (1.0 = none)")
    color_grade: bool = Field(default=True, description="Apply color grading, saturation, and gamma shift")
    film_grain: float = Field(default=2.0, ge=0.0, le=10.0, description="Dynamic film grain noise intensity percentage")
    tilt_3d: bool = Field(default=False, description="Apply subtle 0.8-degree 3D perspective distortion")
    shorts_vertical_916: bool = Field(default=False, description="Convert 16:9 landscape to 9:16 vertical Shorts layout with blurred borders")
    
    # Advanced Risk-Reduction Video Protections
    dynamic_time_warp: bool = Field(default=True, description="Subtle non-linear time warping (1.02x-1.06x speed LFO) to break temporal frame hashes")
    watermark_blur: bool = Field(default=False, description="Apply dynamic blur mask to corner watermarks/handles")
    watermark_position: str = Field(default="bottom_right", description="bottom_right | top_right | top_left | bottom_left")
    
    # Audio parameters & Acoustic Desync
    pitch_cents: int = Field(default=-30, ge=-150, le=150, description="Pitch shift in cents (-30 cents ≈ -0.3 semitone)")
    speed_factor: float = Field(default=1.03, ge=0.8, le=1.5, description="Playback speed multiplier")
    harmonic_notch_eq: bool = Field(default=True, description="4-band parametric notch EQ sweep to disrupt audio constellation map")
    isolate_vocals: bool = Field(default=False, description="Use AI Demucs to isolate speech and remove copyrighted music")
    add_ambience: bool = Field(default=True, description="Add subtle masking acoustic ambience/pink noise")
    ambience_volume: float = Field(default=0.015, ge=0.0, le=0.1, description="Ambience overlay volume level")
    
    # Container, Metadata & Camera EXIF Injection
    strip_metadata: bool = Field(default=True, description="Completely wipe original metadata atoms and headers")
    camera_exif_injection: bool = Field(default=True, description="Injects authentic Apple iPhone 15 Pro Max camera EXIF metadata")
    use_gpu: bool = Field(default=True, description="Enable NVIDIA NVENC hardware acceleration if available")


class JobStatus(BaseModel):
    """Real-time status of a transformation job."""
    job_id: str
    filename: str
    status: StageType
    progress: int = Field(default=0, ge=0, le=100)
    current_stage: str = "Queued"
    error_message: Optional[str] = None
    output_filename: Optional[str] = None
    output_url: Optional[str] = None
    original_size_bytes: int = 0
    processed_size_bytes: int = 0
    duration_seconds: float = 0.0
    created_at: float = 0.0
