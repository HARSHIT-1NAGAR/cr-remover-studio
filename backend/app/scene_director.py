"""
AI Scene Director for Script-to-Scene Breakdown, Visual Keyword Matching, and B-Roll Sequencing.
Uses Google Gemini AI with resilient rule-based NLP fallbacks and multi-key pool failover.
"""

from pathlib import Path
import os
import re
import json
import uuid
from typing import List, Dict, Any, Optional
from app.editor_schemas import SceneBlock
from app.gemini_pool import gemini_pool


class SceneDirector:
    """Directs script analysis, scene timing allocation, and visual B-roll matching."""

    @classmethod
    async def generate_script(
        cls,
        topic: str,
        tone: str = "dramatic",
        target_duration: int = 30,
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates a viral, high-retention 30s-60s Shorts script using Gemini.
        """
        prompt = (
            f"You are a master viral YouTube Shorts and TikTok creator.\n"
            f"Topic: {topic}\n"
            f"Tone: {tone}\n"
            f"Target Duration: {target_duration} seconds (roughly {int(target_duration * 2.5)} words).\n\n"
            f"Create a high-retention viral script following this structure:\n"
            f"1. Hook (0-3s): Irresistible pattern interrupt.\n"
            f"2. Build/Mystery (3-15s): Fast escalating facts or story.\n"
            f"3. Climax (15-25s): The mind-blowing reveal.\n"
            f"4. Call to action / loop (25-30s).\n\n"
            f"Return JSON ONLY with this exact structure:\n"
            f"{{\n"
            f'  "title": "Viral Hook Title",\n'
            f'  "script": "The full narration text with no bracketed stage directions."\n'
            f"}}"
        )

        fallback = {
            "title": f"The Secret Truth About {topic}",
            "script": (
                f"Most people have no idea about the hidden truth behind {topic}. "
                f"Scientists and researchers recently uncovered something that completely changes how we see this. "
                f"In fact, over eighty percent of what you were taught is totally backwards. "
                f"Subscribe right now if you want to know what they discovered next."
            )
        }

        try:
            return gemini_pool.generate_json(
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
        except Exception as e:
            print(f"[SceneDirector] Gemini script generation fallback: {e}")
            return fallback

    @classmethod
    async def parse_script_to_scenes(
        cls,
        script_text: str,
        gemini_api_key: Optional[str] = ""
    ) -> List[SceneBlock]:
        """
        Splits a narration script into 3-6 distinct scene blocks with durations,
        visual keywords for B-roll matching, camera motions, and sound FX triggers.
        """
        prompt = (
            f"Analyze this viral Shorts narration script and break it down into 3 to 6 distinct visual scenes.\n\n"
            f"Script:\n\"{script_text}\"\n\n"
            f"For each scene provide:\n"
            f"- narration_text: exact slice of script spoken in this scene\n"
            f"- visual_keywords: list of 3-4 concrete B-roll stock footage search tags (e.g. ['dark ocean submarine', 'underwater dive'])\n"
            f"- camera_effect: one of 'slow_zoom_in', 'slow_zoom_out', 'punch_zoom', 'pan_left'\n"
            f"- transition: one of 'cut', 'whip_pan', 'zoom_blur', 'crossfade'\n"
            f"- sfx_trigger: one of 'whoosh', 'bass_drop', 'ding', 'glitch', 'none'\n\n"
            f"Return JSON ONLY as an array of scene objects:\n"
            f"[\n"
            f"  {{\n"
            f'    "scene_index": 1,\n'
            f'    "narration_text": "...",\n'
            f'    "visual_keywords": ["keyword1", "keyword2"],\n'
            f'    "camera_effect": "slow_zoom_in",\n'
            f'    "transition": "cut",\n'
            f'    "sfx_trigger": "bass_drop"\n'
            f"  }}\n"
            f"]"
        )

        try:
            raw_scenes = gemini_pool.generate_json(
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=None
            )

            if raw_scenes and isinstance(raw_scenes, list):
                scenes = []
                for idx, sc in enumerate(raw_scenes):
                    scenes.append(
                        SceneBlock(
                            id=f"scene_{idx+1}_{str(uuid.uuid4())[:4]}",
                            scene_index=idx + 1,
                            narration_text=sc.get("narration_text", "").strip(),
                            visual_keywords=sc.get("visual_keywords", ["cinematic 4k", "dramatic lighting"]),
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

        effects = ["slow_zoom_in", "punch_zoom", "slow_zoom_out", "pan_left"]
        sfxs = ["bass_drop", "whoosh", "ding", "whoosh"]
        transitions = ["cut", "whip_pan", "zoom_blur", "cut"]

        scenes: List[SceneBlock] = []
        for idx, sentence in enumerate(sentences):
            words = re.findall(r"\b[A-Za-z]{4,}\b", sentence)
            keywords = words[:3] if words else ["cinematic background", "4k footage"]
            keywords.append("shorts 9:16")

            scenes.append(
                SceneBlock(
                    id=f"scene_{idx+1}_{str(uuid.uuid4())[:4]}",
                    scene_index=idx + 1,
                    narration_text=sentence,
                    duration_seconds=max(2.5, len(sentence.split()) * 0.35),
                    visual_keywords=keywords,
                    camera_effect=effects[idx % len(effects)],
                    transition=transitions[idx % len(transitions)],
                    sfx_trigger=sfxs[idx % len(sfxs)]
                )
            )

        return scenes
