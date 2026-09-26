"""
AI High-CTR Thumbnail & 9:16 Cover Frame Generator for YouTube Shorts & Facebook Reels.
Extracts optimal frame from video, applies high-contrast cinematic color tuning,
and overlays viral 3D typography, badge banners, and retention hooks.
"""

from pathlib import Path
import os
import re
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR

FONTS_DIR = STORAGE_DIR / "assets" / "fonts"


THUMBNAIL_STYLES = {
    "viral_yellow": {
        "text_color": (255, 230, 0),        # #FFE600
        "stroke_color": (0, 0, 0),
        "stroke_width": 10,
        "badge_bg": (239, 68, 68),          # Red badge #ef4444
        "badge_text": (255, 255, 255),
        "overlay_tint": "dark_vignette",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "mrbeast_impact": {
        "text_color": (255, 255, 255),      # White
        "stroke_color": (0, 0, 0),
        "stroke_width": 12,
        "badge_bg": (59, 130, 246),         # Blue badge #3b82f6
        "badge_text": (255, 255, 255),
        "overlay_tint": "high_contrast",
        "font_file": "BebasNeue-Regular.ttf"
    },
    "neon_cyber": {
        "text_color": (6, 182, 212),        # Cyan #06b6d4
        "stroke_color": (15, 23, 42),
        "stroke_width": 8,
        "badge_bg": (168, 85, 247),         # Purple badge
        "badge_text": (255, 255, 255),
        "overlay_tint": "cyber_glow",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "dark_mystery": {
        "text_color": (248, 113, 113),      # Crimson
        "stroke_color": (0, 0, 0),
        "stroke_width": 10,
        "badge_bg": (17, 24, 39),
        "badge_text": (251, 191, 36),
        "overlay_tint": "shadow_gradient",
        "font_file": "Montserrat-ExtraBold.ttf"
    }
}


class ThumbnailGenerator:
    """Generates 1080x1920 high-CTR video covers for Shorts and Reels."""

    @classmethod
    async def extract_best_frame(cls, video_path: Path, timestamp_sec: float = 1.0) -> Path:
        """Extracts a clear frame from the video at specified timestamp."""
        frame_out = TEMP_DIR / f"frame_{video_path.stem}_{int(timestamp_sec*10)}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_sec),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            str(frame_out)
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return frame_out

    @classmethod
    def _wrap_text(cls, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
        """Wraps text so it fits within max_width pixels."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_str = " ".join(current_line)
            bbox = draw.textbbox((0, 0), test_str, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width and len(current_line) > 1:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    @classmethod
    async def generate_cover(
        cls,
        video_path: Path,
        hook_text: str,
        badge_text: str = "MUST WATCH",
        style_key: str = "viral_yellow",
        output_path: Optional[Path] = None,
        timestamp_sec: float = 1.2
    ) -> Path:
        """
        Builds a 1080x1920 viral thumbnail with 3D text hooks, gradient vignettes, and pill badges.
        """
        style = THUMBNAIL_STYLES.get(style_key, THUMBNAIL_STYLES["viral_yellow"])
        if not output_path:
            output_path = PROCESSED_DIR / f"cover_{video_path.stem}.jpg"

        # 1. Extract frame
        frame_path = await cls.extract_best_frame(video_path, timestamp_sec=timestamp_sec)
        
        if frame_path.exists():
            img = Image.open(frame_path).convert("RGBA")
        else:
            # Create synthetic dark background if frame extraction fails
            img = Image.new("RGBA", (1080, 1920), (15, 17, 23, 255))

        # 2. Apply Image Enhancements (Boost saturation & contrast for CTR)
        enhancer = ImageEnhance.Color(img.convert("RGB"))
        img_boosted = enhancer.enhance(1.25)
        contrast_enhancer = ImageEnhance.Contrast(img_boosted)
        img_boosted = contrast_enhancer.enhance(1.15).convert("RGBA")

        # 3. Add Gradient Overlay on top/center for text readability
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        
        # Dark top/center shadow band
        for y in range(250, 950):
            # parabolic alpha curve centered around y=600
            dist = abs(y - 600) / 350
            alpha = max(0, int((1.0 - dist) * 160))
            draw_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

        # Composite overlay
        img = Image.alpha_composite(img_boosted, overlay)
        draw = ImageDraw.Draw(img)

        # 4. Load Fonts
        font_file = FONTS_DIR / style["font_file"]
        if not font_file.exists():
            # Fallback font
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        try:
            main_font = ImageFont.truetype(str(font_file), size=86)
            badge_font = ImageFont.truetype(str(font_file), size=44)
        except Exception:
            main_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # 5. Draw Pill Badge (Top Hook Tag)
        center_y = 520
        if badge_text:
            badge_str = f"🔥 {badge_text.upper()} 🔥"
            b_bbox = draw.textbbox((0, 0), badge_str, font=badge_font)
            bw = b_bbox[2] - b_bbox[0]
            bh = b_bbox[3] - b_bbox[1]
            bx = (1080 - bw) // 2
            by = center_y - 120
            
            # Badge background pill
            padding_x = 36
            padding_y = 14
            badge_box = [bx - padding_x, by - padding_y, bx + bw + padding_x, by + bh + padding_y]
            draw.rounded_rectangle(badge_box, radius=24, fill=style["badge_bg"], outline=(255, 255, 255), width=3)
            draw.text((bx, by), badge_str, fill=style["badge_text"], font=badge_font)

        # 6. Draw Main Hook Text (Wrapped, 3D Drop Shadow + Thick Stroke)
        clean_hook = hook_text.upper().strip()
        lines = cls._wrap_text(clean_hook, main_font, max_width=920, draw=draw)

        line_height = 100
        start_y = center_y + (0 if badge_text else -60)

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=main_font)
            lw = bbox[2] - bbox[0]
            lx = (1080 - lw) // 2
            ly = start_y + (i * line_height)

            # Drop shadow (3D effect)
            shadow_offset = 8
            draw.text(
                (lx + shadow_offset, ly + shadow_offset),
                line,
                fill=(0, 0, 0, 220),
                font=main_font,
                stroke_width=style["stroke_width"] + 2,
                stroke_fill=(0, 0, 0)
            )

            # Main text with stroke
            draw.text(
                (lx, ly),
                line,
                fill=style["text_color"],
                font=main_font,
                stroke_width=style["stroke_width"],
                stroke_fill=style["stroke_color"]
            )

        # 7. Convert to RGB and Save High-Res JPEG
        final_img = img.convert("RGB")
        final_img.save(str(output_path), format="JPEG", quality=95)
        return output_path
