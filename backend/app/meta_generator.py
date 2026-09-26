"""
YouTube Shorts & Facebook Reels SEO & Metadata Engine.
Generates high-CTR viral titles, algorithmic descriptions, pinned comment triggers,
and multi-platform hashtags formatted for 1-click publishing with GeminiKeyPool.
"""

from pathlib import Path
import os
import re
import json
import asyncio
from typing import Dict, Any, List, Optional
from app.gemini_pool import gemini_pool


class MetaGenerator:
    """Produces multi-platform metadata packages for YouTube Shorts and Facebook Reels."""

    @classmethod
    async def generate_metadata(
        cls,
        topic: str,
        script_summary: str = "",
        niche: str = "general",
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates comprehensive SEO metadata for YouTube Shorts & Facebook Reels.
        """
        clean_topic = topic.strip().title()
        niche_tag = niche.replace("_", "").lower()
        prompt = (
            f"You are the top YouTube Shorts and TikTok algorithmic growth consultant for 10M+ subscriber creators.\n"
            f"Topic: {topic}\n"
            f"Niche: {niche}\n"
            f"Script Context: {script_summary}\n\n"
            f"Create a high-CTR, algorithm-optimized metadata package in JSON ONLY:\n"
            f"{{\n"
            f'  "yt_titles": [\n'
            f'    "Option 1: Extreme Curiosity Gap (under 50 chars with emoji)",\n'
            f'    "Option 2: Shocking Revelation / Warning (under 50 chars with emoji)",\n'
            f'    "Option 3: Provocative Question Hook (under 50 chars with emoji)"\n'
            f'  ],\n'
            f'  "yt_description": "2-3 punchy sentences with natural high-volume search keywords, clear curiosity hook, #Shorts #{niche_tag}, and subscribe CTA.",\n'
            f'  "yt_tags": ["#shorts", "#viral", "#trending", "#{niche_tag}", "#facts", "#mindblown", "#didyouknow", "#psychology", "#mystery"],\n'
            f'  "pinned_comment": "A controversial, polarizing, or curiosity-inducing question that forces viewers to reply immediately (boosting algorithmic engagement).",\n'
            f'  "fb_caption": "Engaging Facebook Reel caption with emojis, curiosity hook, and 5 hashtags.",\n'
            f'  "fb_tags": ["#reels", "#viralreels", "#{niche_tag}", "#trending", "#fyp"]\n'
            f"}}"
        )

        clean_topic = topic.strip().title()
        niche_tag = niche.replace("_", "").lower()
        fallback = {
            "yt_titles": [
                f"The Forbidden Truth About {clean_topic[:30]} 🤫",
                f"Why Nobody Is Allowed To Talk About This ⚠️",
                f"Did You Notice The Hidden Detail In {clean_topic[:25]}? 🤯"
            ],
            "yt_description": (
                f"The hidden facts about {clean_topic} that will completely change how you see this. "
                f"Subscribe for daily mind-blowing facts, psychology secrets, and historical breakdowns! #Shorts #{niche_tag} #Viral"
            ),
            "yt_tags": [
                "#shorts", "#viral", "#trending", f"#{niche_tag}",
                "#facts", "#mindblown", "#didyouknow", "#psychology", "#mystery", "#foryou"
            ],
            "pinned_comment": f"👇 What would you have done in this exact situation? Drop your unfiltered reaction below! 👇",
            "fb_caption": (
                f"Wait until you see what was hidden in {clean_topic}... 🤯\n\n"
                f"Have you ever heard of this before? Tell us below! 👇\n\n"
                f"#reels #viralreels #{niche_tag} #trending #fbreels"
            ),
            "fb_tags": ["#reels", "#viralreels", f"#{niche_tag}", "#trending", "#fyp"]
        }

        try:
            res = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
            if isinstance(res, dict) and res.get("yt_titles"):
                return res
            return fallback
        except Exception as e:
            print(f"[MetaGenerator] Gemini metadata fallback: {e}")
            return fallback

    @classmethod
    def save_info_file(cls, dest_file: Path, meta: Dict[str, Any], video_filename: str):
        """Writes a clean human-readable text file ready for copy-pasting into uploaders."""
        titles = meta.get("yt_titles", ["Viral Short"])
        desc = meta.get("yt_description", "")
        tags = " ".join(meta.get("yt_tags", ["#shorts"]))
        pinned = meta.get("pinned_comment", "")
        fb_cap = meta.get("fb_caption", "")

        content = f"""===================================================================
🎬 READY-TO-PUBLISH VIRAL SHORT
Video File: {video_filename}
===================================================================

🔴 YOUTUBE SHORTS (Choose 1 High-CTR Title):
1. {titles[0] if len(titles) > 0 else 'Option 1'}
2. {titles[1] if len(titles) > 1 else 'Option 2'}
3. {titles[2] if len(titles) > 2 else 'Option 3'}

📝 YOUTUBE DESCRIPTION:
{desc}

🏷️ YOUTUBE TAGS:
{tags}

📌 PINNED COMMENT (Post immediately after uploading to boost algorithm):
{pinned}

===================================================================
🔵 FACEBOOK REELS POST TEXT:
{fb_cap}

===================================================================
⚡ Generated automatically by CR Remover Studio Auto-Pilot
"""
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(content)
