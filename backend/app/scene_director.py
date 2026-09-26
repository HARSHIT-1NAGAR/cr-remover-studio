"""
AI Scene Director for Script-to-Scene Breakdown, Visual Keyword Matching, and B-Roll Sequencing.
Uses Google Gemini AI with resilient rule-based NLP fallbacks and multi-key pool failover.
Engineered for multi-million view YouTube Shorts, TikTok, and Instagram Reels retention.
"""

from pathlib import Path
import os
import re
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from app.editor_schemas import SceneBlock
from app.gemini_pool import gemini_pool


class SceneDirector:
    """Directs script analysis, scene timing allocation, and visual B-roll matching."""

    @classmethod
    async def generate_script(
        cls,
        topic: str,
        niche: str = "general",
        tone: str = "dramatic",
        duration_mode: str = "auto",
        target_duration: Optional[int] = None,
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates a viral, high-retention Shorts script using Gemini.
        Supports full-depth storytelling (30s, 50s, 75s, or adaptive auto duration).
        """
        # Calculate target word count and duration
        if target_duration:
            dur_sec = max(25, min(90, target_duration))
        elif duration_mode == "quick_30s":
            dur_sec = 30
        elif duration_mode == "standard_50s":
            dur_sec = 50
        elif duration_mode == "deep_75s":
            dur_sec = 75
        else: # auto / full depth
            dur_sec = 55

        # ~3.0 words per second is the ideal punchy Shorts voiceover tempo
        min_words = int(dur_sec * 2.6)
        max_words = int(dur_sec * 3.2)

        prompt = (
            f"You are an elite, multi-million view YouTube Shorts, TikTok, and Instagram Reels content director.\n"
            f"Your job is to write a deeply engaging, professional viral narration script that hooks viewers instantly and retains them for over 100% of the duration.\n\n"
            f"TOPIC: {topic}\n"
            f"NICHE: {niche}\n"
            f"TONE: {tone}\n"
            f"TARGET DURATION: {dur_sec} seconds (STRICT WORD COUNT: {min_words} to {max_words} words).\n\n"
            f"MANDATORY VIRAL RETENTION RULES:\n"
            f"1. PATTERN-INTERRUPT HOOK (0-2s): Start IMMEDIATELY with the most shocking, counter-intuitive statement, bizarre fact, or psychological hook. NEVER use generic intros like 'Did you know', 'Most people have no idea', 'In this video', or 'Welcome back'.\n"
            f"2. NARRATIVE ESCALATION (2s to {dur_sec-8}s): Deliver rapid, high-information density storytelling. Include specific real names, numbers, historical dates, physiological mechanisms, or psychological tension. Every sentence must raise the stakes or open a curiosity loop.\n"
            f"3. THE CLIMAX ({dur_sec-8}s to {dur_sec-3}s): Deliver the astonishing revelation, secret, or twist that completely pays off the hook.\n"
            f"4. SEAMLESS INFINITE LOOP ENDING ({dur_sec-3}s to {dur_sec}s): Craft the very last line so that it flows grammatically and conceptually right back into the opening hook line without a pause, creating an infinite replay loop.\n\n"
            f"Return valid JSON ONLY with this exact schema:\n"
            f"{{\n"
            f'  "title": "Shocking High-CTR Title with emojis (max 50 chars)",\n'
            f'  "hook_badge": "SHOCKING TRUTH",\n'
            f'  "script": "Full spoken voiceover text with zero stage directions, brackets, sound cues, or timestamps.",\n'
            f'  "target_duration_sec": {dur_sec}\n'
            f"}}"
        )

        clean_topic = topic.strip().rstrip(".!?")
        fallback = {
            "title": f"The Bizarre Secret Behind {clean_topic[:35]} 🤯",
            "hook_badge": "VIRAL FACT",
            "script": (
                f"In 1968, researchers made an astonishing discovery about {clean_topic} that was immediately classified. "
                f"For decades, the public was told a completely sanitized version of what actually happened. "
                f"When independent investigators finally cross-referenced the declassified archives, they uncovered something terrifying: "
                f"over seventy percent of the documented records showed an outcome nobody could explain. "
                f"The reason authorities refused to release the full report is because once you understand how this works, you realize that"
            ),
            "target_duration_sec": dur_sec
        }

        try:
            res = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
            if isinstance(res, dict) and res.get("script"):
                return res
            return fallback
        except Exception as e:
            print(f"[SceneDirector] Gemini script generation error: {e}")
            return fallback

    @classmethod
    async def parse_script_to_scenes(
        cls,
        script_text: str,
        gemini_api_key: Optional[str] = ""
    ) -> List[SceneBlock]:
        """
        Splits a narration script into 4-8 distinct scene blocks with durations,
        visual keywords for B-roll matching, camera motions, and sound FX triggers.
        """
        prompt = (
            f"Analyze this viral Shorts narration script and break it down into 4 to 8 visual cinematic scenes.\n\n"
            f"Script:\n\"{script_text}\"\n\n"
            f"For each scene provide:\n"
            f"- scene_index: integer starting at 1\n"
            f"- narration_text: exact slice of script spoken in this scene\n"
            f"- visual_keywords: list of 3-4 concrete stock footage search tags (e.g. ['cyberpunk neon city', 'dark hallway', 'ancient colosseum'])\n"
            f"- visual_image_prompt: highly detailed photorealistic AI image generation prompt matching this exact line of narration (e.g. 'hyperrealistic 8k cinematic vertical shot of an ancient Egyptian golden sarcophagus opening in a dark tomb with volumetric light rays, dramatic depth of field, Octane render, 9:16 portrait')\n"
            f"- camera_effect: one of 'slow_zoom_in', 'slow_zoom_out', 'punch_zoom', 'pan_left'\n"
            f"- transition: one of 'cut', 'whip_pan', 'zoom_blur', 'crossfade'\n"
            f"- sfx_trigger: one of 'whoosh', 'bass_drop', 'ding', 'glitch', 'none'\n\n"
            f"Return JSON ONLY as an array of scene objects:\n"
            f"[\n"
            f"  {{\n"
            f'    "scene_index": 1,\n'
            f'    "narration_text": "...",\n'
            f'    "visual_keywords": ["keyword1", "keyword2", "keyword3"],\n'
            f'    "visual_image_prompt": "cinematic hyperrealistic 8k vertical shot of...",\n'
            f'    "camera_effect": "punch_zoom",\n'
            f'    "transition": "cut",\n'
            f'    "sfx_trigger": "bass_drop"\n'
            f"  }}\n"
            f"]"
        )

        try:
            raw_scenes = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=None
            )

            if raw_scenes and isinstance(raw_scenes, list):
                scenes = []
                for idx, sc in enumerate(raw_scenes):
                    if isinstance(sc, dict) and sc.get("narration_text"):
                        narr = sc.get("narration_text", "").strip()
                        kw = sc.get("visual_keywords", ["cinematic 4k", "dramatic lighting"])
                        img_p = sc.get("visual_image_prompt") or f"cinematic 8k vertical shot of {' '.join(kw[:3])}, dramatic lighting, 9:16 portrait, masterpiece"
                        scenes.append(
                            SceneBlock(
                                id=f"scene_{idx+1}_{str(uuid.uuid4())[:4]}",
                                scene_index=idx + 1,
                                narration_text=narr,
                                visual_keywords=kw,
                                visual_image_prompt=img_p,
                                camera_effect=sc.get("camera_effect", "slow_zoom_in"),
                                transition=sc.get("transition", "cut"),
                                sfx_trigger=sc.get("sfx_trigger", "whoosh")
                            )
                        )
                if scenes:
                    return scenes
        except Exception as e:
            print(f"[SceneDirector] Gemini scene parsing fallback: {e}")

        # Smart rule-based sentence chunking fallback
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script_text) if s.strip()]
        if not sentences:
            sentences = [script_text]

        effects = ["punch_zoom", "slow_zoom_in", "slow_zoom_out", "pan_left"]
        sfxs = ["bass_drop", "whoosh", "ding", "whoosh"]
        transitions = ["cut", "whip_pan", "zoom_blur", "cut"]

        scenes: List[SceneBlock] = []
        for idx, sentence in enumerate(sentences):
            words = re.findall(r"\b[A-Za-z]{4,}\b", sentence)
            keywords = words[:3] if words else ["cinematic dark background", "4k footage"]
            keywords.append("shorts 9:16")
            img_prompt = f"hyperrealistic 8k cinematic vertical shot of {sentence[:80]}, dramatic atmospheric lighting, 9:16 portrait"

            scenes.append(
                SceneBlock(
                    id=f"scene_{idx+1}_{str(uuid.uuid4())[:4]}",
                    scene_index=idx + 1,
                    narration_text=sentence,
                    duration_seconds=max(2.5, len(sentence.split()) * 0.35),
                    visual_keywords=keywords,
                    visual_image_prompt=img_prompt,
                    camera_effect=effects[idx % len(effects)],
                    transition=transitions[idx % len(transitions)],
                    sfx_trigger=sfxs[idx % len(sfxs)]
                )
            )

        return scenes
