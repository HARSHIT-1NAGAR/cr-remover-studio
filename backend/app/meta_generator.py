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
    """Produces multi-platform metadata packages for YouTube Shorts, Instagram Reels, TikTok, and Facebook."""

    @classmethod
    async def generate_metadata(
        cls,
        topic: str,
        script_summary: str = "",
        niche: str = "general",
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates comprehensive SEO metadata for YouTube Shorts, Instagram Reels, TikTok & Facebook.
        """
        clean_topic = topic.strip().replace("_", " ").title()
        niche_clean = re.sub(r"[^\w]", "", niche).lower()
        if not niche_clean:
            niche_clean = "viral"

        prompt = (
            f"You are an elite viral content strategist and YouTube/TikTok growth specialist.\n"
            f"Video Topic: {clean_topic}\n"
            f"Niche: {niche}\n"
            f"Context: {script_summary}\n\n"
            f"Generate high-CTR, algorithm-optimized viral metadata in JSON ONLY:\n"
            f"{{\n"
            f'  "yt_titles": [\n'
            f'    "Shocking Curiosity Gap Title with emoji (max 45 chars)",\n'
            f'    "Urgent Warning / Secret Reveal Title with emoji (max 45 chars)",\n'
            f'    "Provocative Question Hook Title with emoji (max 45 chars)",\n'
            f'    "Infinite Replay Story Hook Title with emoji (max 45 chars)"\n'
            f'  ],\n'
            f'  "yt_description": "2-3 high-retention sentences with natural search keywords, curiosity hook, hashtags, and subscribe CTA.",\n'
            f'  "yt_tags": ["#shorts", "#viral", "#trending", "#{niche_clean}", "#facts", "#mindblown", "#didyouknow", "#foryou", "#explore"],\n'
            f'  "ig_tags": ["#reels", "#reelsinstagram", "#viralreels", "#explorepage", "#trendingreels", "#{niche_clean}", "#instareels", "#fyp"],\n'
            f'  "tiktok_tags": ["#fyp", "#viral", "#foryou", "#foryoupage", "#trending", "#{niche_clean}", "#tiktok", "#relatable"],\n'
            f'  "fb_tags": ["#reels", "#viralreels", "#{niche_clean}", "#trending", "#fbreels", "#fyp"],\n'
            f'  "pinned_comment": "A controversial or curiosity-inducing question that forces viewers to reply immediately.",\n'
            f'  "fb_caption": "Engaging Facebook Reel caption with emojis, curiosity hook, and 5 hashtags."\n'
            f"}}"
        )

        fallback = {
            "yt_titles": [
                f"The Bizarre Secret Behind {clean_topic[:25]} 🤫",
                f"Why Nobody Talks About This Truth ⚠️",
                f"Did You Notice What Happened Here? 🤯",
                f"The 1 Thing They Never Told You ⚡"
            ],
            "yt_description": (
                f"The shocking truth about {clean_topic} that changed everything. "
                f"Subscribe for daily viral breakdowns, hidden secrets, and fascinating stories! #Shorts #{niche_clean} #Viral #Trending"
            ),
            "yt_tags": [
                "#shorts", "#viral", "#trending", f"#{niche_clean}",
                "#facts", "#mindblown", "#didyouknow", "#foryou", "#explore", "#viralvideo"
            ],
            "ig_tags": [
                "#reels", "#reelsinstagram", "#viralreels", "#explorepage",
                "#trendingreels", f"#{niche_clean}", "#instareels", "#fyp", "#foryou"
            ],
            "tiktok_tags": [
                "#fyp", "#viral", "#foryou", "#foryoupage",
                "#trending", f"#{niche_clean}", "#tiktok", "#viralvideo", "#xyzbca"
            ],
            "fb_tags": [
                "#reels", "#viralreels", f"#{niche_clean}", "#trending", "#fbreels", "#fyp"
            ],
            "pinned_comment": "👇 What is your honest unfiltered reaction to this? Drop your thoughts below! 👇",
            "fb_caption": (
                f"Wait until you see what was revealed in {clean_topic}... 🤯\n\n"
                f"What do you think? Tell us in the comments! 👇\n\n"
                f"#reels #viralreels #{niche_clean} #trending #fbreels"
            )
        }

        try:
            res = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback
            )
            if isinstance(res, dict) and res.get("yt_titles"):
                # Clean titles of prefix artifacts like "Option 1: "
                clean_titles = []
                for t in res.get("yt_titles", []):
                    clean_t = re.sub(r"^(Option \d+:|Title \d+:|\d+\.\s*)", "", str(t)).strip().strip('"')
                    if clean_t:
                        clean_titles.append(clean_t)
                res["yt_titles"] = clean_titles or fallback["yt_titles"]
                
                # Ensure all tag lists exist
                if not res.get("ig_tags"):
                    res["ig_tags"] = fallback["ig_tags"]
                if not res.get("tiktok_tags"):
                    res["tiktok_tags"] = fallback["tiktok_tags"]
                if not res.get("fb_tags"):
                    res["fb_tags"] = fallback["fb_tags"]
                if not res.get("yt_tags"):
                    res["yt_tags"] = fallback["yt_tags"]

                # Add combined hashtags string for 1-click copy
                all_tags_set = []
                for tag_list in [res.get("yt_tags", []), res.get("ig_tags", []), res.get("tiktok_tags", [])]:
                    for t in tag_list:
                        clean_tag = t if t.startswith("#") else f"#{t}"
                        if clean_tag not in all_tags_set:
                            all_tags_set.append(clean_tag)
                res["all_tags_bundle"] = " ".join(all_tags_set[:15])

                return res
            return fallback
        except Exception as e:
            print(f"[MetaGenerator] Gemini metadata fallback: {e}")
            fallback["all_tags_bundle"] = " ".join(fallback["yt_tags"][:12])
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
