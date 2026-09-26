"""
Preset definitions for CR Remover Studio.
Provides pre-tuned audio/video parameter profiles for maximum quality and risk-reduction.
"""

from typing import Dict, Any
from app.schemas import PresetType, TransformParams

PRESET_CONFIGS: Dict[PresetType, Dict[str, Any]] = {
    PresetType.YOUTUBE_BYPASS: {
        "name": "⚡ YouTube Content ID Bypass (Pro)",
        "description": "Maximum quality bypass using dynamic time-warping, Ken Burns zoom, harmonic notch EQ, and synthetic iPhone 15 EXIF.",
        "icon": "youtube",
        "params": {
            "mirror_flip": False,  # Default OFF as requested
            "ken_burns_zoom": 1.07,
            "color_grade": True,
            "film_grain": 2.0,
            "tilt_3d": False,
            "shorts_vertical_916": False,
            "dynamic_time_warp": True,
            "watermark_blur": False,
            "watermark_position": "bottom_right",
            "pitch_cents": -30,
            "speed_factor": 1.03,
            "harmonic_notch_eq": True,
            "isolate_vocals": False,
            "add_ambience": True,
            "ambience_volume": 0.015,
            "strip_metadata": True,
            "camera_exif_injection": True,
            "use_gpu": True,
        }
    },
    PresetType.INSTA_SHORTS: {
        "name": "📱 Instagram & TikTok Shorts Maker",
        "description": "Converts landscape 16:9 videos to 9:16 vertical Reels/Shorts with aesthetic blurred borders & voice boost.",
        "icon": "smartphone",
        "params": {
            "mirror_flip": False,
            "ken_burns_zoom": 1.05,
            "color_grade": True,
            "film_grain": 1.5,
            "tilt_3d": False,
            "shorts_vertical_916": True,
            "dynamic_time_warp": True,
            "watermark_blur": False,
            "watermark_position": "bottom_right",
            "pitch_cents": -25,
            "speed_factor": 1.04,
            "harmonic_notch_eq": True,
            "isolate_vocals": False,
            "add_ambience": True,
            "ambience_volume": 0.015,
            "strip_metadata": True,
            "camera_exif_injection": True,
            "use_gpu": True,
        }
    },
    PresetType.AI_DEEP_CLEAN: {
        "name": "🤖 AI Deep Clean (BGM Remover)",
        "description": "Runs Meta Demucs AI to separate human speech from copyrighted songs + applies time-warp & film grain.",
        "icon": "sparkles",
        "params": {
            "mirror_flip": False,
            "ken_burns_zoom": 1.08,
            "color_grade": True,
            "film_grain": 2.5,
            "tilt_3d": False,
            "shorts_vertical_916": False,
            "dynamic_time_warp": True,
            "watermark_blur": False,
            "watermark_position": "bottom_right",
            "pitch_cents": -40,
            "speed_factor": 1.04,
            "harmonic_notch_eq": True,
            "isolate_vocals": True,
            "add_ambience": True,
            "ambience_volume": 0.02,
            "strip_metadata": True,
            "camera_exif_injection": True,
            "use_gpu": True,
        }
    },
    PresetType.VOCAL_ONLY: {
        "name": "🎙️ Vocal & Speech Isolation Only",
        "description": "Strips 100% of background music and audio noise, leaving pure human dialogue without altering video.",
        "icon": "mic",
        "params": {
            "mirror_flip": False,
            "ken_burns_zoom": 1.0,
            "color_grade": False,
            "film_grain": 0.0,
            "tilt_3d": False,
            "shorts_vertical_916": False,
            "dynamic_time_warp": False,
            "watermark_blur": False,
            "watermark_position": "bottom_right",
            "pitch_cents": 0,
            "speed_factor": 1.0,
            "harmonic_notch_eq": False,
            "isolate_vocals": True,
            "add_ambience": False,
            "ambience_volume": 0.0,
            "strip_metadata": True,
            "camera_exif_injection": False,
            "use_gpu": True,
        }
    }
}


def get_preset_params(preset_type: PresetType) -> TransformParams:
    """Returns TransformParams populated with preset defaults."""
    if preset_type in PRESET_CONFIGS:
        return TransformParams(
            preset=preset_type,
            **PRESET_CONFIGS[preset_type]["params"]
        )
    return TransformParams(preset=PresetType.CUSTOM)
