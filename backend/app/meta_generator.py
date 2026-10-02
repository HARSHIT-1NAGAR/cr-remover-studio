"""
YouTube Shorts & Facebook Reels SEO & Metadata Engine.
Generates high-CTR viral titles, algorithmic descriptions, pinned comment triggers,
and multi-platform hashtags with dynamic angle variation and zero repetition.
"""

from pathlib import Path
import os
import re
import json
import random
import time
import asyncio
from typing import Dict, Any, List, Optional
from app.gemini_pool import gemini_pool


# Diverse Psychological Hook Formulas for Fallback / Dynamic Seed
VIRAL_HOOK_PATTERNS = [
    # Angle 1: Curiosity Gap & Shock
    [
        "Wait For The Ending: {topic} 😱",
        "Nobody Expected This In {topic} 🤯",
        "The Dark Truth Behind {topic} ⚠️",
        "What They Hid About {topic} 🤫",
        "This {topic} Secret Changes Everything ⚡",
        "Don't Watch This Alone... 💀 ({topic})"
    ],
    # Angle 2: Urgent Warning & Insider Secret
    [
        "⚠️ Stop Scrolling: The Real Story of {topic}",
        "99% Of People Missed This In {topic} 👁️",
        "The Forbidden Breakdown: {topic} 🚨",
        "They Tried To Delete This {topic} Clip ❌",
        "What Actually Happened In {topic}? 🤐",
        "Proof That {topic} Was Planned All Along 📈"
    ],
    # Angle 3: Provocative Paradox & Psychology
    [
        "Why {topic} Is NOT What You Think 🧠",
        "The Psychological Illusion Of {topic} 🎭",
        "Why Everyone Is Wrong About {topic} ❌",
        "The 1 Rule Of {topic} You Never Knew 💡",
        "Is {topic} Actually Real? (Look Closer) 🔍",
        "The Moment Everything Changed In {topic} ⏱️"
    ],
    # Angle 4: Extreme Stakes & Climax
    [
        "He Went Too Far With {topic}... 🥶",
        "The Scariest Detail In {topic} ⚠️",
        "Watch Till 0:15 Before Judging {topic} ⏳",
        "This Explained {topic} In 30 Seconds 💥",
        "Only 1% Can Notice What Happened Here 🎯",
        "The Most Shocking {topic} Moment Ever 🎬"
    ],
    # Angle 5: Contrarian / Debunk
    [
        "The Lie You Were Told About {topic} 🛑",
        "Why Nobody Is Talking About {topic} 🤐",
        "The Untold Story Of {topic} Finally Revealed 📜",
        "How {topic} Fooled The Entire Internet 🌐",
        "The Real Cost Of {topic} Nobody Mentions 💸",
        "This Will Change How You View {topic} Forever 🔮"
    ]
]

PINNED_COMMENT_TEMPLATES = [
    "👇 What would you do in this exact situation? Let me know below! 👇",
    "👇 Be honest: Did you notice the twist at the end or did it catch you off guard? 👇",
    "👇 On a scale of 1-10, how crazy is this? Drop your rating! 👇",
    "👇 99% of people get this wrong — what's your take on this? 👇",
    "👇 Did anyone else spot the detail at the 10-second mark? 👇",
    "👇 Should there be a Part 2? Drop a 🔥 if you want more!",
    "👇 What was your immediate reaction to this? Let's discuss in the comments! 👇"
]

DESCRIPTION_TEMPLATES = [
    "The mindblowing breakdown of {topic} that has the entire internet talking. Watch until the final second and subscribe for daily viral stories! #Shorts #{niche} {tags} #Viral",
    "You won't look at {topic} the same way again. The hidden truth revealed step by step. Make sure to like & subscribe for more exclusive deep-dives! #Shorts #{niche} {tags} #Trending",
    "This shocking moment in {topic} left everyone speechless. Watch closely and let us know your thoughts below! #Shorts #{niche} {tags} #Explore",
    "The untold reality of {topic} explained in 30 seconds. Double tap if this blew your mind and follow for daily high-retention stories! #Shorts #{niche} {tags} #FYP"
]


class MetaGenerator:
    """Produces multi-platform metadata packages with high angle variety and zero repetition."""

    @classmethod
    async def generate_metadata(
        cls,
        topic: str,
        script_summary: str = "",
        niche: str = "general",
        gemini_api_key: Optional[str] = "",
        style_angle: Optional[str] = "all_angles"
    ) -> Dict[str, Any]:
        """
        Generates unique, high-CTR SEO metadata for YouTube Shorts, Instagram Reels, TikTok & Facebook.
        Injects dynamic creative seeds and high temperature so results are never repetitive.
        """
        clean_topic = topic.strip().replace("_", " ").strip()
        clean_topic = re.sub(r"\.[a-zA-Z0-9]+$", "", clean_topic)
        clean_topic = re.sub(r"^(cr_clean_|cleaned_|transformed_|voice_|output_|ai_short_)+", "", clean_topic, flags=re.I)
        clean_topic = re.sub(r"[-_]+", " ", clean_topic).strip().title()
        if not clean_topic:
            clean_topic = "Viral Video Phenomenon"

        niche_clean = re.sub(r"[^\w]", "", niche).lower()
        if not niche_clean:
            niche_clean = "viral"

        # Unique random variation token to prevent cache hits
        rand_seed = random.randint(1000, 99999)
        rand_angle = random.choice([
            "curiosity_gap_shock",
            "urgent_secret_warning",
            "psychological_paradox",
            "high_stakes_climax",
            "contrarian_debunk",
            "insider_breakdown"
        ])

        words = [re.sub(r"[^\w]", "", w).lower() for w in clean_topic.split() if len(w) > 3]
        topic_tags = [f"#{w}" for w in words[:4]] if words else [f"#{niche_clean}"]

        prompt = (
            f"You are the world's highest-paid viral YouTube Shorts & TikTok algorithm engineer.\n"
            f"Target Video Topic: \"{clean_topic}\"\n"
            f"Niche Category: {niche}\n"
            f"Context / Summary: {script_summary or clean_topic}\n"
            f"Creative Angle Focus: {style_angle or rand_angle} (Seed #{rand_seed})\n\n"
            f"CRITICAL RULES:\n"
            f"1. Generate 6 COMPLETELY UNIQUE, ultra-creative high-CTR viral titles specifically for \"{clean_topic}\".\n"
            f"2. DO NOT use generic boilerplate like 'Wait For The End' or 'Nobody Expected This'.\n"
            f"3. Craft fresh, provocative, niche-accurate hooks (Curiosity Gaps, Psychological Paradoxes, Urgency Warnings, Plot Twists).\n"
            f"4. Keep each title punchy (under 48 characters) with 1 relevant emoji.\n"
            f"5. Write a compelling 2-sentence SEO description, engaging pinned comment question, and platform hashtags.\n\n"
            f"Return STRICT JSON only matching this format:\n"
            f"{{\n"
            f'  "yt_titles": [\n'
            f'    "Unique Hook 1 with emoji (max 48 chars)",\n'
            f'    "Unique Hook 2 with emoji (max 48 chars)",\n'
            f'    "Unique Hook 3 with emoji (max 48 chars)",\n'
            f'    "Unique Hook 4 with emoji (max 48 chars)",\n'
            f'    "Unique Hook 5 with emoji (max 48 chars)",\n'
            f'    "Unique Hook 6 with emoji (max 48 chars)"\n'
            f'  ],\n'
            f'  "yt_description": "2-sentence viral SEO description with keyword loops.",\n'
            f'  "yt_tags": ["#shorts", "#viral", "#{niche_clean}", {", ".join(json.dumps(t) for t in topic_tags)}, "#trending", "#fyp"],\n'
            f'  "ig_tags": ["#reels", "#reelsinstagram", "#viralreels", "#{niche_clean}", {", ".join(json.dumps(t) for t in topic_tags)}],\n'
            f'  "tiktok_tags": ["#fyp", "#viral", "#foryou", "#{niche_clean}", {", ".join(json.dumps(t) for t in topic_tags)}],\n'
            f'  "fb_tags": ["#reels", "#viralreels", "#{niche_clean}", "#trending", "#fbreels"],\n'
            f'  "pinned_comment": "Provocative debate question to pin in comments.",\n'
            f'  "fb_caption": "Engaging Facebook Reel caption with emojis."\n'
            f"}}"
        )

        # Dynamic algorithmic fallback: randomly selects from 5 pattern pools
        pattern_set = random.choice(VIRAL_HOOK_PATTERNS)
        shuffled_titles = [p.format(topic=clean_topic) for p in pattern_set]
        random.shuffle(shuffled_titles)

        fallback_desc_tmpl = random.choice(DESCRIPTION_TEMPLATES)
        fallback_desc = fallback_desc_tmpl.format(
            topic=clean_topic,
            niche=niche_clean,
            tags=" ".join(topic_tags)
        )
        fallback_pinned = random.choice(PINNED_COMMENT_TEMPLATES)

        fallback = {
            "yt_titles": shuffled_titles,
            "yt_description": fallback_desc,
            "yt_tags": [
                "#shorts", "#viral", "#trending", f"#{niche_clean}",
                *topic_tags, "#facts", "#mindblown", "#foryou", "#explore"
            ],
            "ig_tags": [
                "#reels", "#reelsinstagram", "#viralreels", "#explorepage",
                "#trendingreels", f"#{niche_clean}", *topic_tags, "#instareels", "#fyp"
            ],
            "tiktok_tags": [
                "#fyp", "#viral", "#foryou", "#foryoupage",
                "#trending", f"#{niche_clean}", *topic_tags, "#tiktok", "#relatable"
            ],
            "fb_tags": [
                "#reels", "#viralreels", f"#{niche_clean}", *topic_tags, "#trending", "#fbreels"
            ],
            "pinned_comment": fallback_pinned,
            "fb_caption": (
                f"{shuffled_titles[0]}\n\n"
                f"What do you think about {clean_topic}? Let us know below! 👇\n\n"
                f"#reels #viralreels #{niche_clean} {' '.join(topic_tags)} #trending"
            )
        }

        try:
            # Call Gemini with higher temperature (0.85) for rich creative diversity
            res = await asyncio.to_thread(
                gemini_pool.generate_json,
                prompt=prompt,
                api_keys=gemini_api_key,
                fallback=fallback,
                temperature=0.85
            )

            if isinstance(res, dict) and res.get("yt_titles"):
                clean_titles = []
                for t in res.get("yt_titles", []):
                    clean_t = re.sub(r"^(Option \d+:|Title \d+:|\d+\.\s*)", "", str(t)).strip().strip('"')
                    if clean_t and clean_t not in clean_titles:
                        clean_titles.append(clean_t)

                # If LLM gave fewer than 6, fill with unique randomized fallbacks
                if len(clean_titles) < 6:
                    for fb_t in shuffled_titles:
                        if fb_t not in clean_titles:
                            clean_titles.append(fb_t)
                        if len(clean_titles) >= 6:
                            break

                res["yt_titles"] = clean_titles[:6]
                
                # Fill any missing tags
                for tag_key in ["yt_tags", "ig_tags", "tiktok_tags", "fb_tags"]:
                    if not res.get(tag_key):
                        res[tag_key] = fallback[tag_key]

                if not res.get("pinned_comment"):
                    res["pinned_comment"] = fallback["pinned_comment"]
                if not res.get("yt_description"):
                    res["yt_description"] = fallback["yt_description"]

                # Build combined 15 hashtag bundle
                all_tags_set = []
                for tag_list in [res.get("yt_tags", []), res.get("ig_tags", []), res.get("tiktok_tags", [])]:
                    for t in tag_list:
                        clean_t = t if t.startswith("#") else f"#{t}"
                        if clean_t not in all_tags_set:
                            all_tags_set.append(clean_t)
                res["all_tags_bundle"] = " ".join(all_tags_set[:15])

                return res

            fallback["all_tags_bundle"] = " ".join(fallback["yt_tags"][:15])
            return fallback

        except Exception as e:
            print(f"[MetaGenerator] Gemini metadata error: {e}. Returning randomized fallback...")
            fallback["all_tags_bundle"] = " ".join(fallback["yt_tags"][:15])
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
4. {titles[3] if len(titles) > 3 else 'Option 4'}
5. {titles[4] if len(titles) > 4 else 'Option 5'}
6. {titles[5] if len(titles) > 5 else 'Option 6'}

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

