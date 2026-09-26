"""
YouTube Shorts & Facebook Reels SEO & Metadata Engine.
Generates high-CTR viral titles, algorithmic descriptions, pinned comment triggers,
and multi-platform hashtags formatted for 1-click publishing with GeminiKeyPool.
"""

from pathlib import Path
import os
import re
import json
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
        prompt = (
            f"You are the #1 algorithmic growth strategist for YouTube Shorts and Facebook Reels.\n"
            f"Topic: {topic}\n"
            f"Niche: {niche}\n"
            f"Script/Context: {script_summary}\n\n"
            f"Generate viral metadata formatted in JSON ONLY with this structure:\n"
            f"{{\n"
            f'  "yt_titles": ["Title 1 (<50 chars, high curiosity)", "Title 2 (shock value)", "Title 3 (question hook)"],\n'
            f'  "yt_description": "2-3 sentences with high search volume keywords, #shorts, and subscribe CTA.",\n'
            f'  "yt_tags": ["#shorts", "#viral", "#trending", ...],\n'
            f'  "pinned_comment": "Controversial/engaging question to make viewers comment immediately.",\n'
            f'  "fb_caption": "Short emotional Facebook Reel caption with emojis, question, and 5 hashtags.",\n'
            f'  "fb_tags": ["#reels", "#viralreels", "#fyp", ...]\n'
            f"}}"
        )

        clean_topic = topic.title()
        niche_tag = niche.replace("_", "").lower()
        fallback = {
            "yt_titles": [
                f"The Secret Truth About {clean_topic} 😱",
                f"Never Do This With {clean_topic}...",
                f"Scientists Shocked By {clean_topic} 🤯"
            ],
            "yt_description": (
                f"Discover the hidden facts about {clean_topic} that most people ignore. "
                f"Subscribe for daily mind-blowing facts and psychological breakdowns! #Shorts #{niche_tag} #Viral"
            ),
            "yt_tags": [
                "#shorts", "#viral", "#trending", f"#{niche_tag}",
                "#facts", "#mindblown", "#didyouknow", "#psychology", "#foryou"
            ],
            "pinned_comment": f"👇 Did you already know about this, or is this your first time hearing it? Let me know below!",
            "fb_caption": (
                f"Wait until you see what happens with {clean_topic}... 🤯\n\n"
                f"Have you ever noticed this before? Drop your thoughts below! 👇\n\n"
                f"#reels #viralreels #{niche_tag} #trending #fbreels"
            ),
            "fb_tags": ["#reels", "#viralreels", f"#{niche_tag}", "#trending", "#fyp"]
        }

        try:
            return gemini_pool.generate_json(
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
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

🔴 YOUTUBE SHORTS (Choose 1 Title):
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
