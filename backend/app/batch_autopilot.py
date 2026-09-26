"""
1-Click 30-Day Channel Auto-Pilot & Batch Rendering Factory.
Generates full batches of YouTube Shorts & Facebook Reels autonomously:
Script -> Neural TTS -> Matched B-Roll -> Subtitles -> Render -> 9:16 Thumbnail -> SEO Metadata -> ~/Downloads Export.
"""

from pathlib import Path
import os
import re
import json
import time
import uuid
import asyncio
import zipfile
import shutil
from typing import List, Dict, Any, Optional, Callable

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR, READY_EXPORT_DIR
from app.editor_schemas import AIShortsRenderRequest, SceneBlock, WordTiming
from app.tts_engine import TTSEngine
from app.scene_director import SceneDirector
from app.editor_engine import AIShortsRenderer
from app.broll_harvester import BRollHarvester
from app.thumbnail_generator import ThumbnailGenerator
from app.meta_generator import MetaGenerator
from app.reddit_generator import RedditStoryGenerator


AUTOPILOT_NICHES = [
    {
        "id": "dark_psychology",
        "name": "Dark Psychology & Body Language",
        "badge": "PSYCHOLOGY",
        "description": "Subtle manipulation tricks, micro-expressions, human behavior secrets",
        "default_voice": "en-US-ChristopherNeural",
        "default_bgm": "deep_tension",
        "default_broll": "neural_brain",
        "subtitle_style": "hormozi_yellow",
        "sample_topics": [
            "How to tell if someone is secretly jealous of you",
            "The 3 second eye contact trick that makes anyone trust you",
            "Psychological signs someone is lying to your face",
            "How narcissists control conversations without you noticing",
            "The silent power move that instantly earns respect"
        ]
    },
    {
        "id": "crazy_facts",
        "name": "Crazy History & Unbelievable Facts",
        "badge": "FACTS",
        "description": "Bizarre historical events, astonishing animal facts, lost civilizations",
        "default_voice": "en-US-GuyNeural",
        "default_bgm": "epic_discovery",
        "default_broll": "dark_cyberpunk",
        "subtitle_style": "beast_green",
        "sample_topics": [
            "The bizarre historical event nobody was allowed to talk about",
            "3 ancient inventions that were way too advanced for their time",
            "The deadliest mistake made by a military general in history",
            "Why ancient Roman doctors prescribed gladiators sweat",
            "The real reason why statues in Egypt have broken noses"
        ]
    },
    {
        "id": "stoic_wisdom",
        "name": "Stoic Motivation & Discipline",
        "badge": "MOTIVATION",
        "description": "Marcus Aurelius, mental toughness, ruthless self-discipline, winning mindset",
        "default_voice": "en-GB-RyanNeural",
        "default_bgm": "phonk_drive",
        "default_broll": "luxury_wealth",
        "subtitle_style": "crimson_pulse",
        "sample_topics": [
            "Marcus Aurelius rule to never get insulted again",
            "Why the 1% stay completely silent about their next moves",
            "The brutal truth about discipline that nobody wants to hear",
            "How to stop caring what other people think instantly",
            "3 harsh habits you must destroy before turning 30"
        ]
    },
    {
        "id": "scary_mysteries",
        "name": "Creepy Unsolved Mysteries & Glitches",
        "badge": "MYSTERY",
        "description": "Deep ocean creatures, unexplained radio signals, missing persons, glitch in reality",
        "default_voice": "en-US-ChristopherNeural",
        "default_bgm": "deep_tension",
        "default_broll": "dark_ocean",
        "subtitle_style": "neon_cyan",
        "sample_topics": [
            "The deepest sound ever recorded in the Pacific Ocean",
            "A radio station that has been broadcasting mysterious codes since 1970",
            "The town where every clock stopped at the exact same minute",
            "Scientists drilled 40,000 feet into the Earth and recorded this sound",
            "The creepy photograph taken by Apollo astronauts that NASA never explained"
        ]
    },
    {
        "id": "wealth_hacks",
        "name": "Money Hacks & Millionaire Mindset",
        "badge": "WEALTH",
        "description": "Passive income formulas, tax loopholes, consumer psychology, investing rules",
        "default_voice": "en-US-EricNeural",
        "default_bgm": "upbeat_viral",
        "default_broll": "luxury_wealth",
        "subtitle_style": "hormozi_yellow",
        "sample_topics": [
            "The 50 30 20 money rule that builds generational wealth",
            "How billionaires borrow against assets to pay zero taxes",
            "3 consumer psychology tricks supermarkets use to steal your money",
            "Why saving money in a standard bank is actually losing you wealth",
            "The high-income skill you can learn in 30 days for free"
        ]
    },
    {
        "id": "reddit_stories",
        "name": "Viral Reddit Drama & Revenge",
        "badge": "REDDIT",
        "description": "r/AskReddit, AITA revenge stories, landlord drama, satisfying karma",
        "default_voice": "en-US-GuyNeural",
        "default_bgm": "lofi_chill",
        "default_broll": "minecraft_parkour",
        "subtitle_style": "beast_green",
        "sample_topics": [
            "My boss took credit for my 6-month project, so I locked the source code",
            "My landlord tried to scam me for $3,000, so I reported his building to the city",
            "What is the most satisfying petty revenge you have ever witnessed?",
            "I overheard my business partner planning to steal our clients",
            "My neighbor parked on my lawn for 3 months until this happened"
        ]
    }
]


# Active Auto-Pilot batch tracking
BATCH_JOBS: Dict[str, Dict[str, Any]] = {}


class BatchAutoPilotEngine:
    """Orchestrates end-to-end multi-video batch rendering pipelines."""

    @classmethod
    def get_niches(cls) -> List[Dict[str, Any]]:
        return AUTOPILOT_NICHES

    @classmethod
    async def run_batch(
        cls,
        batch_id: str,
        niche_id: str,
        count: int = 5,
        voice_name: Optional[str] = None,
        bgm_track: Optional[str] = None,
        subtitle_style: Optional[str] = None,
        broll_category: Optional[str] = None,
        custom_topics: Optional[List[str]] = None,
        gemini_api_key: Optional[str] = "",
        progress_callback: Optional[Callable[[str, int, Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes complete batch generation sequentially with live state updates.
        """
        niche = next((n for n in AUTOPILOT_NICHES if n["id"] == niche_id), AUTOPILOT_NICHES[0])
        
        selected_voice = voice_name or niche["default_voice"]
        selected_bgm = bgm_track or niche["default_bgm"]
        selected_sub_style = subtitle_style or niche["subtitle_style"]
        selected_broll = broll_category or niche["default_broll"]

        # Determine topics
        topics_pool = list(custom_topics or [])
        if len(topics_pool) < count:
            topics_pool.extend(niche["sample_topics"])
            while len(topics_pool) < count:
                topics_pool.append(f"{niche['name']} Secret #{len(topics_pool) + 1}")

        selected_topics = topics_pool[:count]
        rendered_items: List[Dict[str, Any]] = []

        # Batch export destination folder
        timestamp_str = time.strftime("%Y%m%d_%H%M")
        batch_folder_name = f"Batch_{niche['id']}_{timestamp_str}"
        batch_export_dir = READY_EXPORT_DIR / batch_folder_name
        batch_export_dir.mkdir(parents=True, exist_ok=True)

        total_videos = len(selected_topics)

        for idx, topic in enumerate(selected_topics):
            item_id = f"{batch_id}_{idx+1}"
            overall_pct = int((idx / total_videos) * 90)

            if progress_callback:
                progress_callback(
                    f"[{idx+1}/{total_videos}] Generating AI Script & Storyboard for: {topic[:30]}...",
                    overall_pct + 2,
                    {"current_index": idx + 1, "total": total_videos, "topic": topic}
                )

            # 1. Script Generation
            if niche_id == "reddit_stories":
                story_data = await RedditStoryGenerator.generate_story(
                    subreddit="r/AskReddit",
                    custom_prompt=topic,
                    gemini_api_key=gemini_api_key
                )
                title = story_data.get("title", topic)
                script_text = story_data.get("script", topic)
            else:
                script_data = await SceneDirector.generate_script(
                    topic=topic,
                    tone="dramatic",
                    target_duration=30,
                    gemini_api_key=gemini_api_key
                )
                title = script_data.get("title", topic)
                script_text = script_data.get("script", topic)

            # 2. Neural TTS Generation with word timings
            if progress_callback:
                progress_callback(
                    f"[{idx+1}/{total_videos}] Synthesizing Neural Speech & Timings...",
                    overall_pct + 5,
                    {"current_index": idx + 1, "total": total_videos, "topic": topic}
                )

            tts_audio_path = TEMP_DIR / f"tts_batch_{item_id}.mp3"
            tts_res = await TTSEngine.generate_speech_with_timings(
                text=script_text,
                voice_name=selected_voice,
                speed_factor=1.05,
                pitch_cents=0,
                output_file=tts_audio_path
            )

            total_dur = tts_res.get("duration", 30.0)
            word_timings = [WordTiming(**w) for w in tts_res.get("word_timings", [])]

            # 3. Scene Breakdown & B-Roll Match
            scenes_raw = await SceneDirector.parse_script_to_scenes(script_text, gemini_api_key=gemini_api_key)
            
            # Allocate durations based on number of scenes
            scene_dur = max(2.0, total_dur / max(1, len(scenes_raw)))
            for sc_idx, sc in enumerate(scenes_raw):
                sc.duration_seconds = scene_dur
                # Match B-Roll clip
                broll_file = await BRollHarvester.match_broll_for_keywords(
                    keywords=sc.visual_keywords,
                    duration=scene_dur,
                    preferred_category=selected_broll
                )
                sc.video_source_path = str(broll_file)

            # 4. Render 9:16 Video
            if progress_callback:
                progress_callback(
                    f"[{idx+1}/{total_videos}] GPU Rendering 9:16 Short with Subtitles & Ducked BGM...",
                    overall_pct + 10,
                    {"current_index": idx + 1, "total": total_videos, "topic": topic}
                )

            render_req = AIShortsRenderRequest(
                project_id=item_id,
                title=f"Short_{idx+1}_{re.sub(r'[^a-zA-Z0-9]', '_', title)[:25]}",
                scenes=scenes_raw,
                voice_audio_path=str(tts_audio_path),
                word_timings=word_timings,
                subtitle_style=selected_sub_style,
                bgm_track=selected_bgm,
                bgm_volume=0.18,
                progress_bar=True,
                anti_copyright_shield=True,
                use_gpu=True
            )

            out_video = await AIShortsRenderer.render_shorts(render_req)

            # 5. Thumbnail & 9:16 Cover Generation
            if progress_callback:
                progress_callback(
                    f"[{idx+1}/{total_videos}] Generating High-CTR 9:16 Cover...",
                    overall_pct + 15,
                    {"current_index": idx + 1, "total": total_videos, "topic": topic}
                )

            cover_path = await ThumbnailGenerator.generate_cover(
                video_path=out_video,
                hook_text=title[:45],
                badge_text=niche["badge"],
                style_key="viral_yellow"
            )

            # 6. SEO Metadata Generation (YouTube & Facebook Reels)
            meta = await MetaGenerator.generate_metadata(
                topic=topic,
                script_summary=script_text[:200],
                niche=niche_id,
                gemini_api_key=gemini_api_key
            )

            # 7. Copy to ~/Downloads/CR_Remover_Ready/Batch_...
            final_vid_name = f"Short_{idx+1:02d}_{re.sub(r'[^a-zA-Z0-9]', '_', title)[:30]}.mp4"
            dest_vid = batch_export_dir / final_vid_name
            dest_cover = batch_export_dir / f"Short_{idx+1:02d}_COVER.jpg"
            dest_info = batch_export_dir / f"Short_{idx+1:02d}_METADATA_INFO.txt"

            shutil.copyfile(out_video, dest_vid)
            if cover_path.exists():
                shutil.copyfile(cover_path, dest_cover)
            MetaGenerator.save_info_file(dest_info, meta, final_vid_name)

            # Calculate publication day & schedule
            # e.g. Day 1 at 12:00 PM, Day 1 at 06:00 PM (2 posts/day)
            day_num = (idx // 2) + 1
            post_slot = "12:00 PM (Peak Lunch)" if (idx % 2 == 0) else "06:30 PM (Evening Prime)"

            item_result = {
                "index": idx + 1,
                "title": title,
                "topic": topic,
                "video_filename": final_vid_name,
                "video_url": f"/api/media/processed/{out_video.name}",
                "cover_url": f"/api/media/processed/{cover_path.name}" if cover_path.exists() else None,
                "duration": total_dur,
                "schedule_day": f"Day {day_num}",
                "schedule_time": post_slot,
                "metadata": meta,
                "export_path": str(dest_vid)
            }
            rendered_items.append(item_result)

        # Batch completed
        if progress_callback:
            progress_callback(
                f"Batch Complete! Generated {len(rendered_items)} Ready-to-Publish Shorts in Downloads.",
                100,
                {"completed": True, "count": len(rendered_items)}
            )

        return rendered_items
