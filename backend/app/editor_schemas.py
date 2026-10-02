"""
Pydantic v2 Data Models and Schemas for AI Shorts Creator & Video Editor.
Strict typing, validation, and serialization.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class VoiceLocale(str, Enum):
    EN_US = "en-US"
    EN_GB = "en-GB"
    EN_AU = "en-AU"
    EN_IN = "en-IN"
    HI_IN = "hi-IN"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"


class TTSVoiceInfo(BaseModel):
    id: str
    name: str
    gender: Literal["Male", "Female"]
    locale: str
    description: str


class WordTiming(BaseModel):
    word: str
    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")


class SceneBlock(BaseModel):
    id: str
    scene_index: int
    narration_text: str
    duration_seconds: float = Field(default=3.0, ge=0.5, le=60.0)
    visual_keywords: List[str] = Field(default_factory=list)
    visual_image_prompt: Optional[str] = Field(default=None, description="Detailed prompt for AI scene image generation")
    video_source_path: Optional[str] = None
    camera_effect: Literal["none", "slow_zoom_in", "slow_zoom_out", "punch_zoom", "pan_left"] = "slow_zoom_in"
    transition: Literal["cut", "crossfade", "whip_pan", "zoom_blur"] = "cut"
    sfx_trigger: Optional[Literal["whoosh", "bass_drop", "ding", "glitch", "none"]] = "whoosh"


class GenerateTTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_name: str = Field(default="en-IN-NeerjaExpressiveNeural")
    speed_factor: float = Field(default=1.05, ge=0.7, le=1.5)
    pitch_cents: int = Field(default=0, ge=-100, le=100)


class ParseScriptRequest(BaseModel):
    script_text: str = Field(..., min_length=5, description="Full narration script")
    gemini_api_key: Optional[str] = Field(default="", description="Optional Gemini API key for deep analysis")


class GenerateScriptFromTopicRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="Topic or prompt for viral Shorts script")
    tone: Literal["dramatic", "educational", "storytelling", "motivational", "mystery"] = "dramatic"
    target_duration: int = Field(default=30, ge=15, le=60, description="Target duration in seconds")
    gemini_api_key: Optional[str] = Field(default="", description="Optional Gemini API key")


class AIShortsRenderRequest(BaseModel):
    project_id: str
    title: str = Field(default="AI_Viral_Short")
    scenes: List[SceneBlock] = Field(..., min_items=1)
    voice_audio_path: str = Field(..., description="Relative or absolute path to narration audio")
    word_timings: List[WordTiming] = Field(default_factory=list)
    
    # Advanced Creator Subtitle Styling
    subtitle_style: str = Field(default="hormozi_yellow") # Preset key or "custom"
    subtitle_font_family: str = Field(default="Montserrat", description="Montserrat | Bebas Neue | Impact | Liberation Sans")
    subtitle_font_size: int = Field(default=54, ge=24, le=80)
    subtitle_text_case: Literal["uppercase", "capitalize", "original"] = "uppercase"
    subtitle_active_color: str = Field(default="#FFE600", description="Hex active highlight color e.g. #FFE600, #22C55E")
    subtitle_inactive_color: str = Field(default="#FFFFFF", description="Hex inactive word color e.g. #FFFFFF, #94A3B8")
    subtitle_outline_color: str = Field(default="#000000", description="Hex stroke color")
    subtitle_outline_width: int = Field(default=5, ge=0, le=10)
    subtitle_background_box: bool = Field(default=True, description="Enable dark pill background box behind subtitles")
    subtitle_words_per_line: int = Field(default=2, ge=1, le=5, description="1 word (Hormozi flash) | 2-3 words | 4-5 words")
    subtitle_position_y: int = Field(default=420, ge=100, le=1200, description="Vertical bottom margin in 1080x1920 canvas")
    subtitle_animation: Literal["pop", "glow", "none"] = "pop"
    
    # Progress Bar & Video Extras
    progress_bar: bool = Field(default=True)
    progress_bar_color: str = Field(default="#06b6d4") # Neon Cyan
    
    # Audio & Mixing
    bgm_track: Literal["phonk_drive", "lofi_chill", "deep_tension", "epic_discovery", "upbeat_viral", "none"] = "phonk_drive"
    bgm_volume: float = Field(default=0.18, ge=0.0, le=1.0)
    ducking_intensity: float = Field(default=0.80, ge=0.0, le=1.0, description="Ducking percentage when voice is active")
    
    # Anti-Copyright & Quality
    anti_copyright_shield: bool = Field(default=True)
    use_gpu: bool = Field(default=True)


class BatchAutoPilotRequest(BaseModel):
    niche_id: str = Field(default="dark_psychology")
    count: int = Field(default=5, ge=1, le=30)
    voice_name: Optional[str] = None
    bgm_track: Optional[str] = None
    subtitle_style: Optional[str] = None
    visual_mode: str = Field(default="ai_scenes", description="ai_scenes (subtitle prompt-matched visuals) | stock_broll (gameplay / cinematic canvas)")
    broll_category: Optional[str] = None
    duration_mode: str = Field(default="auto", description="quick_30s | standard_50s | deep_75s | auto")
    target_duration: Optional[int] = Field(default=None, ge=15, le=120)
    custom_topics: Optional[List[str]] = None
    gemini_api_key: Optional[str] = ""


class GenerateThumbnailRequest(BaseModel):
    video_path: Optional[str] = Field(default="")
    topic: Optional[str] = Field(default="")
    hook_text: str = Field(default="LOOK CLOSER")
    badge_text: str = Field(default="MUST WATCH")
    style_key: str = Field(default="viral_yellow")
    timestamp_sec: float = Field(default=1.0)
    save_to_desktop: bool = Field(default=True)


class ThumbnailHooksRequest(BaseModel):
    topic: str = Field(...)
    gemini_api_key: Optional[str] = ""


class ThumbnailFramesRequest(BaseModel):
    video_path: str = Field(...)
    count: int = Field(default=6, ge=2, le=12)


class GenerateMetadataRequest(BaseModel):
    topic: str = Field(...)
    script_summary: str = Field(default="")
    niche: str = Field(default="general")
    gemini_api_key: Optional[str] = ""
    style_angle: Optional[str] = "all_angles"


class RedditStoryRequest(BaseModel):
    subreddit: str = Field(default="r/AskReddit")
    custom_prompt: str = Field(default="")
    gemini_api_key: Optional[str] = ""


class StockSearchRequest(BaseModel):
    query: str = Field(default="")
    count: int = Field(default=6, ge=1, le=20)
    pexels_api_key: Optional[str] = ""


class PodcastDialogueRequest(BaseModel):
    topic: str = Field(...)
    style: str = Field(default="curiosity_interview")
    host_voice: str = Field(default="en-US-ChristopherNeural")
    guest_voice: str = Field(default="en-US-JennyNeural")
    gemini_api_key: Optional[str] = ""


class TrendToScriptRequest(BaseModel):
    trend_title: str = Field(...)
    summary: str = Field(default="")
    gemini_api_key: Optional[str] = ""


class TelegramBotRequest(BaseModel):
    bot_token: str = Field(...)
    chat_id: str = Field(...)
    action: Literal["start", "stop", "status", "test_message"] = "status"


class GeminiPoolKeysRequest(BaseModel):
    keys: Optional[List[str]] = Field(default=None, description="List of Gemini API keys")
    keys_text: Optional[str] = Field(default="", description="Multiline or comma-separated Gemini API keys")
    persist: bool = Field(default=True, description="Save keys to storage/gemini_keys.json")


class GeminiTestKeysRequest(BaseModel):
    keys: Optional[List[str]] = Field(default=None, description="Specific keys to test (or all if omitted)")
    keys_text: Optional[str] = Field(default="", description="Multiline or comma-separated keys to test")


class GeminiKeyRemoveRequest(BaseModel):
    key: str = Field(..., description="Key or masked key identifier to remove")


class ExportVideoRequest(BaseModel):
    job_id: str = Field(..., description="The job ID of the processed video")
    title: Optional[str] = Field(default="", description="Descriptive title for the export")
    preset: Optional[str] = Field(default="youtube_bypass", description="Preset name or style")
    category: Optional[str] = Field(default="full_videos", description="Destination category (full_videos, viral_shorts, etc.)")
    aspect: Optional[str] = Field(default="16x9", description="Aspect ratio (16x9 or 9x16)")




