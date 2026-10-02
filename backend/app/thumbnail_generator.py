"""
AI High-CTR Thumbnail & 9:16 Cover Frame Generator for YouTube Shorts & Facebook Reels.
Extracts optimal frame from video, applies high-contrast cinematic color tuning,
and overlays viral 3D typography, badge banners, and retention hooks.
"""

from pathlib import Path
import os
import re
import random
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR, EXPORTS_THUMBNAILS_DIR
from app.gemini_pool import gemini_pool

FONTS_DIR = STORAGE_DIR / "assets" / "fonts"


THUMBNAIL_STYLES = {
    "viral_yellow": {
        "name": "🔥 Viral Yellow (MrBeast)",
        "text_color": (255, 230, 0),        # #FFE600
        "stroke_color": (0, 0, 0),
        "stroke_width": 12,
        "badge_bg": (239, 68, 68),          # Red badge #ef4444
        "badge_text": (255, 255, 255),
        "overlay_tint": "dark_vignette",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "mrbeast_impact": {
        "name": "⚡ Bold Impact White",
        "text_color": (255, 255, 255),      # White
        "stroke_color": (0, 0, 0),
        "stroke_width": 14,
        "badge_bg": (59, 130, 246),         # Blue badge #3b82f6
        "badge_text": (255, 255, 255),
        "overlay_tint": "high_contrast",
        "font_file": "BebasNeue-Regular.ttf"
    },
    "neon_cyber": {
        "name": "💎 Cyberpunk Neon Glow",
        "text_color": (6, 182, 212),        # Cyan #06b6d4
        "stroke_color": (15, 23, 42),
        "stroke_width": 10,
        "badge_bg": (168, 85, 247),         # Purple badge
        "badge_text": (255, 255, 255),
        "overlay_tint": "cyber_glow",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "crimson_shock": {
        "name": "🩸 Crimson Shock (Warning)",
        "text_color": (248, 113, 113),      # Crimson
        "stroke_color": (0, 0, 0),
        "stroke_width": 12,
        "badge_bg": (220, 38, 38),          # Blood red
        "badge_text": (255, 255, 255),
        "overlay_tint": "shadow_gradient",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "golden_luxury": {
        "name": "👑 Golden Luxury (Wealth)",
        "text_color": (250, 204, 21),       # Gold #facc15
        "stroke_color": (20, 20, 20),
        "stroke_width": 10,
        "badge_bg": (16, 185, 129),         # Emerald green #10b981
        "badge_text": (255, 255, 255),
        "overlay_tint": "dark_vignette",
        "font_file": "Montserrat-ExtraBold.ttf"
    },
    "dark_mystery": {
        "name": "👻 Dark Mystery (Secrets)",
        "text_color": (251, 191, 36),       # Amber
        "stroke_color": (17, 24, 39),
        "stroke_width": 11,
        "badge_bg": (31, 41, 55),
        "badge_text": (251, 191, 36),
        "overlay_tint": "shadow_gradient",
        "font_file": "Montserrat-ExtraBold.ttf"
    }
}

FALLBACK_HOOK_BANK = [
    "LOOK CLOSER 😱",
    "THEY LIED TO YOU ⚠️",
    "DON'T DO THIS 🛑",
    "99% FAILED THIS 🧠",
    "NOBODY NOTICED THIS 👁️",
    "THIS CHANGED EVERYTHING ⚡",
    "THE SECRET REVEALED 🤫",
    "IS THIS REAL? 🤯",
    "ONLY 1% KNOWS THIS 🎯",
    "NEVER SEARCH THIS 💀"
]


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
    async def extract_candidate_frames(cls, video_path: Path, count: int = 6) -> List[Dict[str, Any]]:
        """Extracts candidate frames spaced evenly across the video for quick selection."""
        if not video_path.exists():
            return []

        # Probe duration
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
        proc = await asyncio.create_subprocess_exec(*dur_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        try:
            total_dur = float(stdout.decode().strip())
        except Exception:
            total_dur = 15.0

        timestamps = [round((total_dur / (count + 1)) * (i + 1), 2) for i in range(count)]
        frames = []

        for ts in timestamps:
            frame_file = await cls.extract_best_frame(video_path, timestamp_sec=ts)
            if frame_file.exists():
                frames.append({
                    "timestamp": ts,
                    "frame_url": f"/api/media/temp/{frame_file.name}",
                    "frame_path": str(frame_file)
                })

        return frames

    @classmethod
    async def generate_ai_hooks(cls, topic: str, gemini_api_key: str = "") -> List[str]:
        """Generates 5 punchy 2-4 word high-CTR 3D thumbnail hook phrases."""
        clean_topic = topic.strip().replace("_", " ")
        prompt = (
            f"You are a master YouTube Shorts Thumbnail designer.\n"
            f"Video Topic: \"{clean_topic}\"\n\n"
            f"Generate 6 ultra-short, punchy (2 to 4 words MAX) high-CTR 3D thumbnail text hooks.\n"
            f"Examples: 'LOOK CLOSER', 'THEY LIED', '99% FAILED', 'NEVER DO THIS', 'HIDDEN TRUTH', 'WATCH THE END'.\n"
            f"Make them provocative, curiosity-inducing, and all-caps.\n\n"
            f"Return JSON strictly: {{\"hooks\": [\"HOOK 1\", \"HOOK 2\", \"HOOK 3\", \"HOOK 4\", \"HOOK 5\", \"HOOK 6\"]}}"
        )

        fallback_hooks = random.sample(FALLBACK_HOOK_BANK, min(6, len(FALLBACK_HOOK_BANK)))

        try:
            res = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback={"hooks": fallback_hooks},
                temperature=0.85
            )
            hooks = res.get("hooks", fallback_hooks)
            return [h.upper().strip() for h in hooks if len(h) <= 30][:6] or fallback_hooks
        except Exception:
            return fallback_hooks

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
        video_path: Optional[Path],
        hook_text: str,
        badge_text: str = "MUST WATCH",
        style_key: str = "viral_yellow",
        output_path: Optional[Path] = None,
        timestamp_sec: float = 1.2,
        save_to_desktop: bool = True
    ) -> Path:
        """
        Builds a 1080x1920 viral thumbnail with 3D text hooks, gradient vignettes, and pill badges.
        """
        style = THUMBNAIL_STYLES.get(style_key, THUMBNAIL_STYLES["viral_yellow"])
        if not output_path:
            stem = video_path.stem if video_path else "custom"
            output_path = PROCESSED_DIR / f"cover_{stem}_{int(time.time())}.jpg"

        # 1. Extract frame or generate procedural backdrop
        img = None
        if video_path and Path(video_path).exists():
            frame_path = await cls.extract_best_frame(Path(video_path), timestamp_sec=timestamp_sec)
            if frame_path.exists():
                try:
                    img = Image.open(frame_path).convert("RGBA")
                except Exception:
                    pass

        if img is None:
            # Create synthetic dark cyber cinematic background
            img = Image.new("RGBA", (1080, 1920), (15, 18, 28, 255))
            draw_bg = ImageDraw.Draw(img)
            # Add subtle radial background glow
            for r in range(600, 0, -20):
                alpha = int((1.0 - r / 600) * 80)
                draw_bg.ellipse([(540 - r, 700 - r), (540 + r, 700 + r)], fill=(30, 41, 59, alpha))

        # 2. Apply Image Enhancements (Boost saturation & contrast for CTR)
        enhancer = ImageEnhance.Color(img.convert("RGB"))
        img_boosted = enhancer.enhance(1.30)
        contrast_enhancer = ImageEnhance.Contrast(img_boosted)
        img_boosted = contrast_enhancer.enhance(1.20).convert("RGBA")

        # 3. Add Gradient Overlay on top/center for text readability
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        
        # Dark top/center shadow band
        for y in range(200, 1050):
            dist = abs(y - 620) / 420
            alpha = max(0, int((1.0 - dist) * 175))
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
            main_font = ImageFont.truetype(str(font_file), size=92)
            badge_font = ImageFont.truetype(str(font_file), size=46)
        except Exception:
            main_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # 5. Draw Pill Badge (Top Hook Tag)
        center_y = 530
        if badge_text:
            badge_str = f"🔥 {badge_text.upper().strip()} 🔥"
            b_bbox = draw.textbbox((0, 0), badge_str, font=badge_font)
            bw = b_bbox[2] - b_bbox[0]
            bh = b_bbox[3] - b_bbox[1]
            bx = (1080 - bw) // 2
            by = center_y - 130
            
            # Badge background pill
            padding_x = 38
            padding_y = 15
            badge_box = [bx - padding_x, by - padding_y, bx + bw + padding_x, by + bh + padding_y]
            draw.rounded_rectangle(badge_box, radius=24, fill=style["badge_bg"], outline=(255, 255, 255), width=3)
            draw.text((bx, by), badge_str, fill=style["badge_text"], font=badge_font)

        # 6. Draw Main Hook Text (Wrapped, 3D Drop Shadow + Thick Stroke)
        clean_hook = (hook_text or "MUST WATCH").upper().strip()
        lines = cls._wrap_text(clean_hook, main_font, max_width=940, draw=draw)

        line_height = 105
        start_y = center_y + (0 if badge_text else -60)

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=main_font)
            lw = bbox[2] - bbox[0]
            lx = (1080 - lw) // 2
            ly = start_y + (i * line_height)

            # Drop shadow (3D effect)
            shadow_offset = 10
            draw.text(
                (lx + shadow_offset, ly + shadow_offset),
                line,
                fill=(0, 0, 0, 240),
                font=main_font,
                stroke_width=style["stroke_width"] + 3,
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
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_img.save(str(output_path), format="JPEG", quality=96)

        # Also copy to Desktop Exports Vault
        if save_to_desktop and EXPORTS_THUMBNAILS_DIR.exists():
            try:
                import shutil
                desktop_thumb = EXPORTS_THUMBNAILS_DIR / output_path.name
                shutil.copy2(output_path, desktop_thumb)
            except Exception:
                pass

        return output_path

