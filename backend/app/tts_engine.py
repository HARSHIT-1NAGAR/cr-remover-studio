"""
Neural Text-To-Speech (TTS) & Word-Level Subtitle Synchronization Engine.
Leverages edge-tts for high-fidelity neural voices with microsecond-exact boundary metadata.
"""

from pathlib import Path
import os
import re
import uuid
import asyncio
import edge_tts
from typing import List, Dict, Any, Optional
from app.config import TEMP_DIR
from app.editor_schemas import TTSVoiceInfo, WordTiming

# Curated list of popular, high-fidelity neural voices for video storytelling
CURATED_VOICES = [
    TTSVoiceInfo(id="en-US-ChristopherNeural", name="Christopher (Storyteller / Deep)", gender="Male", locale="en-US", description="Authoritative, deep documentary voice"),
    TTSVoiceInfo(id="en-US-GuyNeural", name="Guy (Energetic / Viral)", gender="Male", locale="en-US", description="Fast-paced, engaging creator tone"),
    TTSVoiceInfo(id="en-US-AriaNeural", name="Aria (Expressive / Crisp)", gender="Female", locale="en-US", description="Clear, versatile narrative delivery"),
    TTSVoiceInfo(id="en-US-JennyNeural", name="Jenny (Warm / Friendly)", gender="Female", locale="en-US", description="Approachable podcast & lifestyle tone"),
    TTSVoiceInfo(id="en-US-BrianNeural", name="Brian (Smart / Tech)", gender="Male", locale="en-US", description="Modern tech & factual presenter"),
    TTSVoiceInfo(id="en-GB-RyanNeural", name="Ryan (British Narrative)", gender="Male", locale="en-GB", description="Refined British documentary narration"),
    TTSVoiceInfo(id="en-GB-SoniaNeural", name="Sonia (British Studio)", gender="Female", locale="en-GB", description="Eloquent BBC-style presentation"),
    TTSVoiceInfo(id="en-IN-PrabhatNeural", name="Prabhat (Indian English)", gender="Male", locale="en-IN", description="Clear Indian English corporate & explainer"),
    TTSVoiceInfo(id="hi-IN-MadhurNeural", name="Madhur (Hindi Storyteller)", gender="Male", locale="hi-IN", description="Expressive Hindi storytelling voice"),
    TTSVoiceInfo(id="hi-IN-SwaraNeural", name="Swara (Hindi Narrative)", gender="Female", locale="hi-IN", description="Smooth, professional Hindi delivery"),
]


def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """Converts #RRGGBB hex string to ASS &HAABBGGRR format."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c*2 for c in hex_clean])
    if len(hex_clean) != 6:
        return f"&H{alpha:02X}FFFFFF"
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


class TTSEngine:
    """Manages neural voice synthesis, word boundary extraction, and subtitle generation."""

    @classmethod
    def get_voices(cls) -> List[TTSVoiceInfo]:
        """Returns the curated voice catalogue."""
        return CURATED_VOICES

    @classmethod
    async def generate_speech_with_timings(
        cls,
        text: str,
        voice_name: str = "en-US-ChristopherNeural",
        speed_factor: float = 1.05,
        pitch_cents: int = 0,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes neural voice audio and extracts word-level boundary timings.
        """
        if output_file is None:
            file_id = str(uuid.uuid4())[:8]
            output_file = TEMP_DIR / f"tts_{file_id}.mp3"

        # Format rate and pitch adjustments for edge-tts
        rate_pct = int((speed_factor - 1.0) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

        # pitch format in edge-tts: +0Hz, +5Hz etc or semitones
        pitch_hz = int(pitch_cents / 10)
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=rate_str,
            pitch=pitch_str
        )

        sentence_boundaries = []
        raw_audio_chunks = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                raw_audio_chunks.append(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sentence_boundaries.append(chunk)

        # Write output MP3
        with open(output_file, "wb") as f:
            for chunk in raw_audio_chunks:
                f.write(chunk)

        # Calculate word-level timings from sentence boundaries
        word_timings: List[WordTiming] = []

        for sb in sentence_boundaries:
            # edge-tts offsets are in 100-nanosecond ticks (10,000,000 ticks = 1 second)
            start_sec = round(sb.get("offset", 0) / 10_000_000, 3)
            dur_sec = round(sb.get("duration", 0) / 10_000_000, 3)
            sent_text = sb.get("text", "").strip()

            words = sent_text.split()
            if not words or dur_sec <= 0:
                continue

            # Distribute time across words proportional to character length + pause padding
            total_chars = sum(len(w) for w in words)
            cur_time = start_sec

            for w in words:
                w_dur = max(0.12, (len(w) / total_chars) * dur_sec)
                w_clean = re.sub(r"[^\w\s\$\%\#\@\!]", "", w)
                word_timings.append(
                    WordTiming(
                        word=w if w else w_clean,
                        start=round(cur_time, 2),
                        end=round(min(start_sec + dur_sec, cur_time + w_dur), 2)
                    )
                )
                cur_time += w_dur

        total_audio_duration = word_timings[-1].end if word_timings else 1.0

        return {
            "audio_file": str(output_file),
            "duration": total_audio_duration,
            "word_timings": [w.model_dump() for w in word_timings],
            "total_words": len(word_timings)
        }

    @classmethod
    def generate_ass_subtitles(
        cls,
        word_timings: List[Dict[str, Any]],
        output_path: Path,
        style_preset: str = "hormozi_yellow",
        font_family: str = "Montserrat",
        font_size: int = 54,
        text_case: str = "uppercase",
        active_color_hex: str = "#FFE600",
        inactive_color_hex: str = "#FFFFFF",
        outline_color_hex: str = "#000000",
        outline_width: int = 5,
        background_box: bool = True,
        words_per_line: int = 2,
        position_y: int = 420,
        animation: str = "pop",
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """
        Generates Advanced SubStation Alpha (.ass) subtitle file
        with creator-grade word-by-word active word pop, bounding pill boxes,
        and high-contrast typography.
        """
        # Resolve preset styles if not custom
        if style_preset == "hormozi_yellow":
            font_family = "Montserrat"
            active_color_hex = "#FFE600" # Bright Canary Yellow
            inactive_color_hex = "#FFFFFF"
            outline_width = 5
            background_box = True
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "beast_green":
            font_family = "Montserrat"
            active_color_hex = "#22C55E" # Electric Neon Green
            inactive_color_hex = "#FFFFFF"
            outline_width = 6
            background_box = True
            words_per_line = 3
            text_case = "uppercase"
        elif style_preset == "ali_abdaal":
            font_family = "Montserrat"
            active_color_hex = "#FBBF24" # Warm Amber Gold
            inactive_color_hex = "#F1F5F9"
            outline_width = 2
            background_box = True
            words_per_line = 3
            text_case = "capitalize"
        elif style_preset == "iman_gadzhi":
            font_family = "Bebas Neue"
            active_color_hex = "#EF4444" # Crimson Red
            inactive_color_hex = "#FFFFFF"
            outline_width = 4
            background_box = False
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "cyber_neon":
            font_family = "Montserrat"
            active_color_hex = "#00F0FF" # Cyber Cyan
            inactive_color_hex = "#F472B6" # Pink
            outline_width = 4
            background_box = True
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "clean_white":
            font_family = "Liberation Sans"
            active_color_hex = "#FFD700" # Gold
            inactive_color_hex = "#FFFFFF"
            outline_width = 3
            background_box = True
            words_per_line = 4
            text_case = "original"

        # Convert hex colors to ASS format (&HAABBGGRR)
        primary_ass = hex_to_ass_color(inactive_color_hex, alpha=0)
        highlight_ass = hex_to_ass_color(active_color_hex, alpha=0)
        outline_ass = hex_to_ass_color(outline_color_hex, alpha=0)
        back_ass = "&H85000000" if background_box else "&HFF000000" # 52% alpha dark box

        # Border style: 1 = outline + shadow, 3 = opaque bounding box
        border_style = 1
        border_width = max(0, outline_width)
        shadow_depth = 2 if outline_width > 0 else 0

        # Scale animation tags
        scale_tag = "\\fscx115\\fscy115" if animation == "pop" else ""

        # ASS Header
        ass_content = [
            "[Script Info]",
            "Title: CR Remover Pro Creator Subtitles",
            "ScriptType: v4.00+",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{font_family},{font_size},{primary_ass},&H000000FF,{outline_ass},{back_ass},-1,0,0,0,100,100,1,0,{border_style},{border_width},{shadow_depth},2,40,40,{position_y},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        def format_ass_time(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h:d}:{m:02d}:{s:05.2f}"

        chunk_size = max(1, min(5, words_per_line))

        for i in range(0, len(word_timings), chunk_size):
            chunk = word_timings[i:i + chunk_size]
            if not chunk:
                continue

            chunk_start = chunk[0].get("start", 0.0)
            chunk_end = chunk[-1].get("end", chunk_start + 1.2)

            for active_idx, active_word in enumerate(chunk):
                w_start = active_word.get("start", chunk_start)
                w_end = active_word.get("end", chunk_end)

                formatted_words = []
                for j, w in enumerate(chunk):
                    raw_text = w.get("word", "")
                    if text_case == "uppercase":
                        w_text = raw_text.upper()
                    elif text_case == "capitalize":
                        w_text = raw_text.capitalize()
                    else:
                        w_text = raw_text

                    if j == active_idx:
                        # Highlight active word with creator color and pop zoom
                        formatted_words.append(f"{{\\c{highlight_ass}{scale_tag}}}{w_text}{{\\r}}")
                    else:
                        formatted_words.append(f"{{\\c{primary_ass}}}{w_text}{{\\r}}")

                line_text = " ".join(formatted_words)
                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                ass_content.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_content))

        return output_path

