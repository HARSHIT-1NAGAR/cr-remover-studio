"""
2-Person Conversational Podcast & Dialogue Shorts Generator for CR Remover Studio.
Generates compelling 2-speaker dialogues (Interviewer & Expert, Skeptic & Believer),
synthesizes alternating neural voices, and compiles 9:16 split-screen videos.
"""

from pathlib import Path
import os
import re
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR
from app.tts_engine import TTSEngine
from app.broll_harvester import BRollHarvester
from app.editor_schemas import WordTiming
import google.generativeai as genai


class PodcastShortsGenerator:
    """Generates 2-person dialogue scripts, dual-voice audio, and split-screen layouts."""

    @classmethod
    async def generate_dialogue(
        cls,
        topic: str,
        style: str = "curiosity_interview",
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates structured 2-speaker conversation turns.
        """
        api_key = gemini_api_key.strip() if gemini_api_key else os.getenv("GEMINI_API_KEY", "")

        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    f"Create a high-energy 2-person podcast Shorts script about: {topic}\n"
                    f"Format: Host (interviewer asking provocative questions) & Guest (expert dropping shocking revelations).\n"
                    f"Duration: 30-45 seconds (4 to 6 total dialogue turns, fast pacing).\n\n"
                    f"Return JSON ONLY with this structure:\n"
                    f"{{\n"
                    f'  "title": "Shocking Podcast Hook Title",\n'
                    f'  "host_name": "Alex",\n'
                    f'  "guest_name": "Dr. Vance",\n'
                    f'  "turns": [\n'
                    f'    {{"speaker": "host", "text": "Is it true that modern banks don\'t actually keep our money in vaults?"}},\n'
                    f'    {{"speaker": "guest", "text": "Almost none of it. Over 90% is immediately loaned out the second you deposit it."}},\n'
                    f'    {{"speaker": "host", "text": "So what happens if everyone tries to withdraw at the same time?"}},\n'
                    f'    {{"speaker": "guest", "text": "The entire system collapses in 48 hours. That\'s the secret nobody talks about."}}\n'
                    f'  ]\n'
                    f"}}"
                )
                response = model.generate_content(prompt)
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except Exception as e:
                print(f"Gemini podcast dialogue fallback: {e}")

        # Procedural fallback podcast conversation
        return {
            "title": f"The Dark Truth Behind {topic.title()}",
            "host_name": "Host",
            "guest_name": "Expert",
            "turns": [
                {"speaker": "host", "text": f"Why is everybody talking about the hidden secret behind {topic}?"},
                {"speaker": "guest", "text": "Because what they taught us in school was completely backwards. The top one percent have known this for decades."},
                {"speaker": "host", "text": "Wait, so how does it actually work in real life?"},
                {"speaker": "guest", "text": "The moment you realize this rule, you will never look at it the same way again."}
            ]
        }

    @classmethod
    async def synthesize_dual_audio(
        cls,
        dialogue: Dict[str, Any],
        host_voice: str = "en-US-ChristopherNeural",
        guest_voice: str = "en-US-JennyNeural"
    ) -> Dict[str, Any]:
        """
        Synthesizes speech for each turn and concatenates them with global timestamps.
        """
        turns = dialogue.get("turns", [])
        turn_audio_files: List[Path] = []
        all_word_timings: List[Dict[str, Any]] = []
        current_global_time = 0.0

        for idx, turn in enumerate(turns):
            voice = host_voice if turn["speaker"] == "host" else guest_voice
            turn_out = TEMP_DIR / f"turn_{uuid.uuid4().hex[:6]}.mp3"
            
            res = await TTSEngine.generate_speech_with_timings(
                text=turn["text"],
                voice_name=voice,
                speed_factor=1.05,
                pitch_cents=0,
                output_file=turn_out
            )

            dur = res.get("duration", 2.0)
            # Offset word timings by global timeline
            for w in res.get("word_timings", []):
                all_word_timings.append({
                    "word": w["word"],
                    "start": round(w["start"] + current_global_time, 3),
                    "end": round(w["end"] + current_global_time, 3),
                    "speaker": turn["speaker"]
                })

            turn_audio_files.append(turn_out)
            current_global_time += dur + 0.15 # Small natural dialogue pause

        # Concat all audio files using FFmpeg concat
        master_audio = TEMP_DIR / f"podcast_master_{uuid.uuid4().hex[:6]}.mp3"
        concat_list_file = TEMP_DIR / f"concat_list_{uuid.uuid4().hex[:6]}.txt"
        
        with open(concat_list_file, "w") as f:
            for fpath in turn_audio_files:
                f.write(f"file '{fpath}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:a", "libmp3lame",
            "-b:a", "256k",
            str(master_audio)
        ]

        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()

        return {
            "master_audio_path": str(master_audio),
            "master_audio_url": f"/api/media/temp/{master_audio.name}",
            "total_duration": current_global_time,
            "word_timings": all_word_timings
        }
