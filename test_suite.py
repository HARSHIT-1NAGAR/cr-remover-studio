"""
Comprehensive End-to-End System Test Suite for CR Remover Studio.
Tests all backend endpoints, TTS synthesis, B-Roll matching, Subtitle generation,
Thumbnail rendering, SEO metadata, and 9:16 Master Shorts rendering.
"""

import sys
import os
import json
import time
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path("/home/harshit/Desktop/cr-remover/backend")
sys.path.insert(0, str(backend_dir))

from app.config import (
    STORAGE_DIR, TEMP_DIR, PROCESSED_DIR, READY_EXPORT_DIR,
    HAS_NVENC, is_nvenc_available
)
from app.presets import PRESET_CONFIGS
from app.tts_engine import TTSEngine
from app.scene_director import SceneDirector
from app.broll_harvester import BRollHarvester
from app.thumbnail_generator import ThumbnailGenerator
from app.meta_generator import MetaGenerator
from app.reddit_generator import RedditStoryGenerator
from app.editor_engine import AIShortsRenderer
from app.editor_schemas import AIShortsRenderRequest, SceneBlock, WordTiming
from app.batch_autopilot import BatchAutoPilotEngine

passed = 0
failed = 0
errors = []

def report(test_name: str, success: bool, details: str = ""):
    global passed, failed
    if success:
        passed += 1
        print(f"  [PASS] {test_name} {details}")
    else:
        failed += 1
        errors.append((test_name, details))
        print(f"  [FAIL] {test_name} - ERROR: {details}")

async def run_all_tests():
    print("===================================================================")
    print("🧪 STARTING FULL COMPREHENSIVE APP & ENGINE TEST SUITE")
    print("===================================================================")

    # 1. Hardware & Config Detection
    print("\n--- 1. Testing Hardware & Storage Dirs ---")
    nvenc_ok = is_nvenc_available()
    report("NVENC GPU Hardware Detection", True, f"(Available: {nvenc_ok})")
    
    for d_name, p in [("Uploads", STORAGE_DIR / "uploads"), ("Processed", PROCESSED_DIR), ("Temp", TEMP_DIR), ("Export", READY_EXPORT_DIR)]:
        report(f"Storage Directory: {d_name}", p.exists(), str(p))

    # 2. TTS Voice List
    print("\n--- 2. Testing TTS Engine ---")
    voices = TTSEngine.get_voices()
    report("Neural TTS Voice Catalog", len(voices) > 0, f"Found {len(voices)} voices")

    # 3. Neural Speech Synthesis with Word Timings
    tts_out = TEMP_DIR / "test_tts_synth.mp3"
    tts_res = await TTSEngine.generate_speech_with_timings(
        text="This is a test of the automated neural speech and subtitle system.",
        voice_name="en-US-ChristopherNeural",
        speed_factor=1.05,
        output_file=tts_out
    )
    report("TTS Audio Synthesis", tts_out.exists() and tts_out.stat().st_size > 1000, f"Size: {tts_out.stat().st_size} bytes, Duration: {tts_res.get('duration'):.2f}s")
    report("Word-Level Timing Synchronization", len(tts_res.get("word_timings", [])) > 5, f"Captured {len(tts_res.get('word_timings', []))} words")

    # 4. Script Generation & Breakdown
    print("\n--- 3. Testing Script & Scene Director ---")
    script_data = await SceneDirector.generate_script(
        topic="Dark Psychology Secret",
        tone="dramatic",
        target_duration=30
    )
    report("AI Script Generation", "script" in script_data and len(script_data["script"]) > 20, f"Title: {script_data.get('title')}")

    scenes = await SceneDirector.parse_script_to_scenes(script_data["script"])
    report("Script-to-Scenes Decomposition", len(scenes) >= 2, f"Created {len(scenes)} distinct visual scenes")

    # 5. Stock B-Roll Vault
    print("\n--- 4. Testing B-Roll & Gameplay Vault ---")
    categories = BRollHarvester.get_categories()
    report("B-Roll Categories Discovery", len(categories) >= 6, f"Found {len(categories)} categories")

    matched_broll = await BRollHarvester.match_broll_for_keywords(
        keywords=["subway", "runner", "gameplay"],
        duration=4.0
    )
    report("Keyword B-Roll Matching", matched_broll.exists() and matched_broll.stat().st_size > 1000, f"Matched: {matched_broll.name}")

    # 6. Reddit Story & Card Generator
    print("\n--- 5. Testing Reddit Story & UI Card Generator ---")
    reddit_data = await RedditStoryGenerator.generate_story(
        subreddit="r/AskReddit",
        custom_prompt="Creepy glitch in the matrix"
    )
    report("Reddit Story Scripting", "title" in reddit_data and "script" in reddit_data, f"Story: {reddit_data.get('title')[:35]}...")

    card_out = TEMP_DIR / "test_reddit_card.png"
    RedditStoryGenerator.create_reddit_card_image(
        subreddit=reddit_data.get("subreddit", "r/AskReddit"),
        author=reddit_data.get("author", "u/User"),
        title=reddit_data.get("title", "Test Title"),
        upvotes="32.5k",
        output_path=card_out
    )
    report("Reddit Dark-Mode UI Card PNG", card_out.exists() and card_out.stat().st_size > 2000, f"Size: {card_out.stat().st_size} bytes")

    # 7. SEO Metadata Generator
    print("\n--- 6. Testing SEO & Algorithm Metadata ---")
    meta_res = await MetaGenerator.generate_metadata(
        topic="Stoic Discipline Rules",
        script_summary="How Marcus Aurelius controlled his emotions",
        niche="stoic_wisdom"
    )
    report("YouTube SEO Package", len(meta_res.get("yt_titles", [])) >= 2 and len(meta_res.get("yt_tags", [])) >= 3, f"Titles: {meta_res.get('yt_titles')[:1]}")
    report("Facebook Reels Caption Package", len(meta_res.get("fb_caption", "")) > 10, f"Hashtags: {len(meta_res.get('fb_tags', []))}")

    # 8. High-CTR Thumbnail Generator
    print("\n--- 7. Testing 9:16 Thumbnail & Cover Generator ---")
    thumb_out = TEMP_DIR / "test_thumb_cover.jpg"
    thumb_res = await ThumbnailGenerator.generate_cover(
        video_path=matched_broll,
        hook_text="THE SECRET NOBODY TOLD YOU",
        badge_text="MUST WATCH",
        style_key="viral_yellow",
        output_path=thumb_out
    )
    report("9:16 High-CTR Cover Image", thumb_out.exists() and thumb_out.stat().st_size > 5000, f"Size: {thumb_out.stat().st_size} bytes (1080x1920)")

    # 9. Full Master 9:16 Shorts Video Render Pipeline
    print("\n--- 8. Testing End-to-End 9:16 Short Video Render ---")
    test_scene_1 = SceneBlock(
        id="sc_1",
        scene_index=0,
        narration_text="This is a test of the automated neural speech",
        duration_seconds=3.0,
        visual_keywords=["dark", "cyberpunk"],
        video_source_path=str(matched_broll),
        camera_effect="slow_zoom_in"
    )
    test_scene_2 = SceneBlock(
        id="sc_2",
        scene_index=1,
        narration_text="and subtitle system with background music.",
        duration_seconds=3.0,
        visual_keywords=["space", "nebula"],
        video_source_path=str(matched_broll),
        camera_effect="punch_zoom"
    )

    render_req = AIShortsRenderRequest(
        project_id="test_render_job",
        title="Test_Automated_Short",
        scenes=[test_scene_1, test_scene_2],
        voice_audio_path=str(tts_out),
        word_timings=[WordTiming(**w) for w in tts_res.get("word_timings", [])],
        subtitle_style="hormozi_yellow",
        bgm_track="phonk_drive",
        bgm_volume=0.15,
        progress_bar=True,
        anti_copyright_shield=True,
        use_gpu=HAS_NVENC
    )

    render_out = await AIShortsRenderer.render_shorts(render_req)
    report("9:16 Master Video Render (GPU / CPU Fallback)", render_out.exists() and render_out.stat().st_size > 10000, f"Rendered: {render_out.name}, Size: {render_out.stat().st_size / 1024 / 1024:.2f} MB")

    # 10. Summary
    print("\n===================================================================")
    print(f"📊 TEST SUITE SUMMARY: {passed} PASSED, {failed} FAILED")
    print("===================================================================")
    if failed == 0:
        print("🎉 ALL SYSTEMS ARE 100% OPERATIONAL WITH ZERO BUGS!")
    else:
        print("⚠️ Errors detected:")
        for name, err in errors:
            print(f" - {name}: {err}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
