"""
2-Person Conversational Podcast & Dialogue Shorts Generator for CR Remover Studio.
Generates compelling 2-speaker dialogues (Interviewer & Expert, Skeptic & Believer),
synthesizes alternating neural voices, and compiles 9:16 split-screen videos with GeminiKeyPool rotation.
"""

from pathlib import Path
import os
import re
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR, HAS_NVENC
from app.tts_engine import TTSEngine
from app.broll_harvester import BRollHarvester
from app.editor_schemas import WordTiming, AIShortsRenderRequest, SceneBlock
from app.editor_engine import AIShortsRenderer
from app.sfx_director import SFXDirector
from app.gemini_pool import gemini_pool


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
        prompt = (
            f"Create a high-energy 2-person podcast Shorts script about: {topic}\n"
            f"Format: Host (interviewer asking provocative questions) & Guest (expert dropping shocking revelations).\n"
            f"Duration: 30-45 seconds (4 to 6 total dialogue turns, fast pacing).\n\n"
            f"Return JSON ONLY with this structure:\n"
            f"{{\n"
            f'  "title": "Shocking Podcast Hook Title",\n'
            f'  "host_name": "Host",\n'
            f'  "guest_name": "Expert",\n'
            f'  "turns": [\n'
            f'    {{"speaker": "host", "text": "Is it true that modern banks don\'t actually keep our money in vaults?"}},\n'
            f'    {{"speaker": "guest", "text": "Almost none of it. Over 90% is immediately loaned out the second you deposit it."}},\n'
            f'    {{"speaker": "host", "text": "So what happens if everyone tries to withdraw at the same time?"}},\n'
            f'    {{"speaker": "guest", "text": "The entire system collapses in 48 hours. That\'s the secret nobody talks about."}}\n'
            f'  ]\n'
            f"}}"
        )

        fallback = {
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

        try:
            return gemini_pool.generate_json(
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
        except Exception as e:
            print(f"[PodcastGenerator] Gemini podcast dialogue fallback: {e}")
            return fallback

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
            for w in res.get("word_timings", []):
                all_word_timings.append({
                    "word": w["word"],
                    "start": round(w["start"] + current_global_time, 3),
                    "end": round(w["end"] + current_global_time, 3),
                    "speaker": turn["speaker"]
                })

            turn_audio_files.append(turn_out)
            current_global_time += dur + 0.15 # Small natural dialogue pause

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

    @classmethod
    async def render_split_screen_short(
        cls,
        dialogue: Dict[str, Any],
        host_voice: str = "en-US-ChristopherNeural",
        guest_voice: str = "en-US-JennyNeural",
        bgm_track: str = "phonk_drive",
        subtitle_style: str = "hormozi_yellow",
        top_broll: str = "neural_brain",
        bottom_broll: str = "minecraft_parkour"
    ) -> Path:
        """
        Renders a full 9:16 split-screen Short with top/bottom speaker streams,
        subtitles, and ducked audio.
        """
        # 1. Synthesize audio
        audio_data = await cls.synthesize_dual_audio(
            dialogue=dialogue,
            host_voice=host_voice,
            guest_voice=guest_voice
        )
        total_dur = audio_data["total_duration"]
        master_audio_path = Path(audio_data["master_audio_path"])
        word_timings = [WordTiming(**w) for w in audio_data["word_timings"]]

        # 2. Get top and bottom B-Roll clips
        top_clip = await BRollHarvester.match_broll_for_keywords(["cyber", "brain"], duration=total_dur, preferred_category=top_broll)
        bottom_clip = await BRollHarvester.match_broll_for_keywords(["gameplay", "runner"], duration=total_dur, preferred_category=bottom_broll)

        # 3. Create Scene Blocks
        turns = dialogue.get("turns", [])
        scenes: List[SceneBlock] = []
        turn_dur = max(2.0, total_dur / max(1, len(turns)))

        for idx, turn in enumerate(turns):
            scenes.append(SceneBlock(
                id=f"pod_sc_{idx}",
                scene_index=idx,
                narration_text=turn["text"],
                duration_seconds=turn_dur,
                visual_keywords=["podcast", "interview"],
                video_source_path=str(top_clip if turn["speaker"] == "host" else bottom_clip),
                camera_effect="slow_zoom_in"
            ))

        # 4. Render using AIShortsRenderer
        job_id = f"pod_{uuid.uuid4().hex[:6]}"
        render_req = AIShortsRenderRequest(
            project_id=job_id,
            title=f"Podcast_{dialogue.get('title', 'Short')[:25]}",
            scenes=scenes,
            voice_audio_path=str(master_audio_path),
            word_timings=word_timings,
            subtitle_style=subtitle_style,
            bgm_track=bgm_track,
            bgm_volume=0.15,
            progress_bar=True,
            anti_copyright_shield=True,
            use_gpu=HAS_NVENC
        )

        return await AIShortsRenderer.render_shorts(render_req)
