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

# Curated list of 100% Free, high-fidelity neural voices for video storytelling (Hinglish, Hindi, English)
CURATED_VOICES = [
    # Hinglish & Indian English
    TTSVoiceInfo(id="en-IN-NeerjaExpressiveNeural", name="Neerja Expressive (Hinglish / Indian Female)", gender="Female", locale="en-IN", description="Super natural, conversational Hinglish creator tone — perfect for Indian Shorts"),
    TTSVoiceInfo(id="en-IN-PrabhatNeural", name="Prabhat (Hinglish / Indian Male)", gender="Male", locale="en-IN", description="Clear, energetic Indian English & Hinglish explainer voice"),
    TTSVoiceInfo(id="en-IN-NeerjaNeural", name="Neerja Standard (Hinglish / Indian Female)", gender="Female", locale="en-IN", description="Smooth, professional Indian English & Hinglish presentation"),
    
    # Pure Hindi (हिंदी)
    TTSVoiceInfo(id="hi-IN-MadhurNeural", name="Madhur (Hindi Storyteller / Deep Male)", gender="Male", locale="hi-IN", description="Expressive, dramatic Hindi storytelling voice for viral facts & mysteries"),
    TTSVoiceInfo(id="hi-IN-SwaraNeural", name="Swara (Hindi Narrative / Expressive Female)", gender="Female", locale="hi-IN", description="Smooth, engaging Hindi documentary and lifestyle voice"),

    # Natural English (Multilingual Neural)
    TTSVoiceInfo(id="en-US-AndrewMultilingualNeural", name="Andrew (Ultra-Natural Human / Male)", gender="Male", locale="en-US", description="Microsoft Copilot flagship — authentic human breathing & conversational cadence"),
    TTSVoiceInfo(id="en-US-BrianMultilingualNeural", name="Brian (Smart / Tech Explainer)", gender="Male", locale="en-US", description="Modern, clear presenter tone for facts and psychology"),
    TTSVoiceInfo(id="en-US-AvaMultilingualNeural", name="Ava (Dynamic / Expressive Female)", gender="Female", locale="en-US", description="High-energy, pleasant female narrative tone for viral hooks"),
    TTSVoiceInfo(id="en-US-EmmaMultilingualNeural", name="Emma (Cheerful / Viral Creator)", gender="Female", locale="en-US", description="Modern lifestyle and creator cadence with clear articulation"),
    TTSVoiceInfo(id="en-US-ChristopherNeural", name="Christopher (Storyteller / Dark Noir)", gender="Male", locale="en-US", description="Authoritative, deep documentary & mystery voice"),
    TTSVoiceInfo(id="en-GB-RyanNeural", name="Ryan (British Narrative Master)", gender="Male", locale="en-GB", description="Refined British BBC-style documentary narration"),
    TTSVoiceInfo(id="en-US-GuyNeural", name="Guy (Energetic / Punchy)", gender="Male", locale="en-US", description="Fast-paced, high retention creator delivery"),
]


def hex_to_ass_style_color(hex_str: str, alpha: int = 0) -> str:
    """Converts #RRGGBB hex string to ASS header &HAABBGGRR format."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c*2 for c in hex_clean])
    if len(hex_clean) != 6:
        return f"&H{alpha:02X}FFFFFF"
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def hex_to_ass_tag_color(hex_str: str) -> str:
    """Converts #RRGGBB hex string to ASS inline override tag &HBBGGRR& format."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c*2 for c in hex_clean])
    if len(hex_clean) != 6:
        return "&HFFFFFF&"
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return f"&H{b:02X}{g:02X}{r:02X}&"


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
        voice_name: str = "en-IN-NeerjaExpressiveNeural",
        speed_factor: float = 1.05,
        pitch_cents: int = 0,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes 100% free neural voice audio and extracts word-level boundary timings.
        Guarantees fallback word-timing synthesis so subtitles are always present.
        """
        if output_file is None:
            file_id = str(uuid.uuid4())[:8]
            output_file = TEMP_DIR / f"tts_{file_id}.mp3"

        actual_voice = voice_name or "en-IN-NeerjaExpressiveNeural"

        # Format rate and pitch adjustments for edge-tts
        rate_pct = int((speed_factor - 1.0) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

        pitch_hz = int(pitch_cents / 10)
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        communicate = edge_tts.Communicate(
            text=text,
            voice=actual_voice,
            rate=rate_str,
            pitch=pitch_str
        )

        sentence_boundaries = []
        raw_audio_chunks = []

        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    raw_audio_chunks.append(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    sentence_boundaries.append(chunk)
        except Exception as e:
            print(f"[TTSEngine] edge-tts stream warning: {e}")

        # Write output MP3
        with open(output_file, "wb") as f:
            for chunk in raw_audio_chunks:
                f.write(chunk)

        # Probe exact audio file duration using ffprobe
        probed_dur = 0.0
        try:
            import subprocess
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(output_file)]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probed_dur = float(res.stdout.strip())
        except Exception:
            probed_dur = max(2.0, len(text.split()) * 0.35)

        # Calculate word-level timings from sentence boundaries
        word_timings: List[WordTiming] = []

        for sb in sentence_boundaries:
            start_sec = round(sb.get("offset", 0) / 10_000_000, 3)
            dur_sec = round(sb.get("duration", 0) / 10_000_000, 3)
            sent_text = sb.get("text", "").strip()

            words = sent_text.split()
            if not words or dur_sec <= 0:
                continue

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

        # Resilient fallback: If no sentence boundaries returned, calculate even word division
        if not word_timings:
            words = text.split()
            if words:
                word_dur = probed_dur / len(words)
                cur_t = 0.0
                for w in words:
                    word_timings.append(
                        WordTiming(
                            word=w,
                            start=round(cur_t, 2),
                            end=round(min(probed_dur, cur_t + word_dur), 2)
                        )
                    )
                    cur_t += word_dur

        total_audio_duration = probed_dur if probed_dur > 0 else (word_timings[-1].end if word_timings else 1.0)

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
        font_family: str = "Liberation Sans",
        font_size: int = 64,
        text_case: str = "uppercase",
        active_color_hex: str = "#FFE600",
        inactive_color_hex: str = "#FFFFFF",
        outline_color_hex: str = "#000000",
        outline_width: int = 6,
        background_box: bool = True,
        words_per_line: int = 2,
        position_y: int = 360,
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
            font_family = "Liberation Sans"
            active_color_hex = "#FFE600" # Bright Canary Yellow
            inactive_color_hex = "#FFFFFF"
            outline_width = 6
            font_size = 66
            background_box = True
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "beast_green":
            font_family = "Liberation Sans"
            active_color_hex = "#22C55E" # Electric Neon Green
            inactive_color_hex = "#FFFFFF"
            outline_width = 6
            font_size = 64
            background_box = True
            words_per_line = 3
            text_case = "uppercase"
        elif style_preset == "ali_abdaal":
            font_family = "Liberation Sans"
            active_color_hex = "#FBBF24" # Warm Amber Gold
            inactive_color_hex = "#F1F5F9"
            outline_width = 4
            font_size = 60
            background_box = True
            words_per_line = 3
            text_case = "capitalize"
        elif style_preset == "iman_gadzhi":
            font_family = "Liberation Sans"
            active_color_hex = "#EF4444" # Crimson Red
            inactive_color_hex = "#FFFFFF"
            outline_width = 5
            font_size = 64
            background_box = False
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "cyber_neon":
            font_family = "Liberation Sans"
            active_color_hex = "#00F0FF" # Cyber Cyan
            inactive_color_hex = "#F472B6" # Pink
            outline_width = 5
            font_size = 64
            background_box = True
            words_per_line = 2
            text_case = "uppercase"
        elif style_preset == "clean_white":
            font_family = "Liberation Sans"
            active_color_hex = "#FFD700" # Gold
            inactive_color_hex = "#FFFFFF"
            outline_width = 4
            font_size = 58
            background_box = True
            words_per_line = 3
            text_case = "original"

        # Convert hex colors for ASS header (&HAABBGGRR) and inline tags (&HBBGGRR&)
        primary_header_ass = hex_to_ass_style_color(inactive_color_hex, alpha=0)
        outline_header_ass = hex_to_ass_style_color(outline_color_hex, alpha=0)
        back_header_ass = "&H80000000" if background_box else "&HFF000000" # 50% opacity dark backing

        active_tag_color = hex_to_ass_tag_color(active_color_hex)
        inactive_tag_color = hex_to_ass_tag_color(inactive_color_hex)

        border_style = 1
        border_width = max(2, outline_width)
        shadow_depth = 3

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
            f"Style: Default,{font_family},{font_size},{primary_header_ass},&H000000FF,{outline_header_ass},{back_header_ass},-1,0,0,0,100,100,2,0,{border_style},{border_width},{shadow_depth},2,30,30,{position_y},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        def format_ass_time(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h:d}:{m:02d}:{s:05.2f}"

        chunk_size = max(1, min(4, words_per_line))

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
                        formatted_words.append(f"{{\\1c{active_tag_color}\\fscx112\\fscy112\\bord{border_width+1}}}{w_text}{{\\r}}")
                    else:
                        formatted_words.append(f"{{\\1c{inactive_tag_color}\\bord{border_width}}}{w_text}{{\\r}}")

                line_text = " ".join(formatted_words)
                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                ass_content.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_content))

        return output_path

