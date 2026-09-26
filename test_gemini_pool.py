"""
Comprehensive Test Suite for Gemini Multi-Key Pool & Failover Manager.
Tests:
1. Key parsing (commas, newlines, spaces, quotes, deduplication)
2. Masking for secure display
3. Candidate priority and load balancing
4. 429 / ResourceExhausted rotation & automatic failover simulation
5. Multi-model fallback sequence
6. FastAPI endpoints (/api/gemini/pool-status, /api/gemini/pool-keys, /api/gemini/test-keys, /api/gemini/remove-key)
7. Integration with SceneDirector, PodcastGenerator, MetaGenerator, TrendHarvester, RedditStoryGenerator
"""

import sys
import os
import json
import time
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.gemini_pool import (
    GeminiKeyPool, KeyHealth, parse_raw_keys, mask_key, gemini_pool, POOL_STORAGE_FILE
)
from app.scene_director import SceneDirector
from app.podcast_generator import PodcastShortsGenerator
from app.meta_generator import MetaGenerator
from app.reddit_generator import RedditStoryGenerator
from app.trend_harvester import TrendHarvester
from app.gemini_service import GeminiTitleGenerator
from fastapi.testclient import TestClient
from app.main import app

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


def test_key_parsing_and_masking():
    print("\n--- 1. Testing Key Parsing & Masking ---")
    
    # Comma, newline, space, quotes mixed input
    raw_input = """
    AIzaSyDummyKeyNumberOne111, AIzaSyDummyKeyNumberTwo222
    'AIzaSyDummyKeyNumberThree333'  "AIzaSyDummyKeyNumberFour444"
    AIzaSyDummyKeyNumberOne111
    """
    keys = parse_raw_keys(raw_input)
    report("Parse multiple keys with mixed separators", len(keys) == 4, f"Found {len(keys)} keys")
    report("Deduplicate keys preserving order", keys[0] == "AIzaSyDummyKeyNumberOne111" and len(keys) == 4)
    
    # Masking test
    masked = mask_key("AIzaSyB1234567890XYZ")
    report("Key Masking", masked == "AIzaSyB1...0XYZ", f"Masked: {masked}")


def test_pool_management():
    print("\n--- 2. Testing Pool Registration, Cooldown & Priority ---")
    pool = GeminiKeyPool()
    
    test_keys = [
        "AIzaSyAlphaKey123456789",
        "AIzaSyBetaKey1234567890",
        "AIzaSyGammaKey123456789"
    ]
    pool.set_keys(test_keys, persist=True)
    status = pool.get_status()
    report("Pool Key Count", status["total_keys"] == 3, f"Total: {status['total_keys']}")
    report("All Keys Active initially", status["active_keys"] == 3)
    
    # Rate limit key 1
    health1 = pool._keys_map["AIzaSyAlphaKey123456789"]
    health1.mark_rate_limited("429 ResourceExhausted: Quota exceeded", cooldown_seconds=60)
    
    status_after = pool.get_status()
    report("Rate Limited State Tracked", status_after["rate_limited_keys"] == 1 and status_after["active_keys"] == 2)
    report("Key 1 Not Available during cooldown", not health1.is_available())
    
    # Candidate order should put healthy keys (Beta, Gamma) before limited key (Alpha)
    candidates = pool.get_candidate_keys()
    report("Healthy keys prioritized over rate-limited keys", candidates[0] != "AIzaSyAlphaKey123456789" and candidates[-1] == "AIzaSyAlphaKey123456789")
    
    # Remove key
    removed = pool.remove_key("AIzaSyGammaKey123456789")
    report("Remove Key from Pool", removed and len(pool._keys_map) == 2)


def test_automatic_failover_simulation():
    print("\n--- 3. Testing Automatic Failover on 429 Quota Exhaustion ---")
    pool = GeminiKeyPool()
    pool.set_keys(["AIzaSyKeyA_RateLimited", "AIzaSyKeyB_WorkingFine"], persist=False)
    
    current_key_holder = {"key": None}

    def mock_configure(api_key=None, **kwargs):
        current_key_holder["key"] = api_key

    with patch("google.generativeai.configure", side_effect=mock_configure), \
         patch("google.generativeai.GenerativeModel") as MockModel:
        
        instance_a = MagicMock()
        instance_a.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded for model")
        
        instance_b = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = '{"viral_hook": "Shocking reveal", "status": "ok"}'
        instance_b.generate_content.return_value = mock_resp
        
        def model_factory(model_name, **kwargs):
            if current_key_holder["key"] == "AIzaSyKeyA_RateLimited":
                return instance_a
            return instance_b
        
        MockModel.side_effect = model_factory
        
        result = pool.generate_json(
            prompt="Generate viral hook",
            api_keys=["AIzaSyKeyA_RateLimited", "AIzaSyKeyB_WorkingFine"],
            fallback={"fallback": True}
        )
        
        report("Automatic Failover succeeded", result.get("status") == "ok")
        report("Key A was marked as rate_limited", pool._keys_map["AIzaSyKeyA_RateLimited"].status == "rate_limited")
        report("Key B was marked as active with success", pool._keys_map["AIzaSyKeyB_WorkingFine"].success_count > 0)


def test_fastapi_endpoints():
    print("\n--- 4. Testing FastAPI Gemini Pool Endpoints ---")
    client = TestClient(app)
    
    # 1. GET /api/gemini/pool-status
    res = client.get("/api/gemini/pool-status")
    report("GET /api/gemini/pool-status status code 200", res.status_code == 200)
    data = res.json()
    report("Pool status returns structured health dict", "total_keys" in data and "keys" in data)
    
    # 2. POST /api/gemini/pool-keys
    post_res = client.post("/api/gemini/pool-keys", json={
        "keys_text": "AIzaSyEndpointTest1_AAA\nAIzaSyEndpointTest2_BBB",
        "persist": False
    })
    report("POST /api/gemini/pool-keys registers keys", post_res.status_code == 200 and post_res.json()["keys_count"] == 2)
    
    # 3. POST /api/gemini/remove-key
    del_res = client.post("/api/gemini/remove-key", json={"key": "AIzaSyEndpointTest1_AAA"})
    report("POST /api/gemini/remove-key removes key", del_res.status_code == 200 and del_res.json()["removed"] is True)


async def test_generator_modules_integration():
    print("\n--- 5. Testing Generator Modules with Gemini Pool & Fallback ---")
    
    # Test SceneDirector fallback & structure
    script = await SceneDirector.generate_script(topic="Quantum Physics", target_duration=30)
    report("SceneDirector.generate_script returns valid script object", "script" in script and "title" in script)
    
    scenes = await SceneDirector.parse_script_to_scenes(script["script"])
    report("SceneDirector.parse_script_to_scenes returns SceneBlock list", len(scenes) >= 1)
    
    # Test PodcastShortsGenerator
    podcast = await PodcastShortsGenerator.generate_dialogue(topic="Real Estate Wealth")
    report("PodcastShortsGenerator returns turns and speakers", "turns" in podcast and len(podcast["turns"]) >= 2)
    
    # Test MetaGenerator
    meta = await MetaGenerator.generate_metadata(topic="Black Hole Paradox", niche="science")
    report("MetaGenerator returns multi-platform metadata", "yt_titles" in meta and len(meta["yt_titles"]) >= 2)
    
    # Test RedditStoryGenerator
    reddit = await RedditStoryGenerator.generate_story(subreddit="r/AskReddit")
    report("RedditStoryGenerator returns story and title", "title" in reddit and "script" in reddit)
    
    # Test TrendHarvester
    trend_script = await TrendHarvester.trend_to_script(trend_title="New Space Discovery")
    report("TrendHarvester.trend_to_script returns script and title", "script" in trend_script)


async def main():
    test_key_parsing_and_masking()
    test_pool_management()
    test_automatic_failover_simulation()
    test_fastapi_endpoints()
    await test_generator_modules_integration()
    
    print("\n===================================================================")
    print(f"📊 GEMINI POOL TEST SUMMARY: {passed} PASSED, {failed} FAILED")
    print("===================================================================")
    if failed > 0:
        for name, err in errors:
            print(f"  - {name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
