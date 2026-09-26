"""
Reddit Story & Viral Split-Screen Generator.
Generates viral Reddit drama, confessions, and curiosity stories,
creates authentic dark-mode Reddit post card overlays, and bundles them into 9:16 Shorts.
"""

from pathlib import Path
import os
import re
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR
from app.broll_harvester import BRollHarvester
import google.generativeai as genai

FONTS_DIR = STORAGE_DIR / "assets" / "fonts"


CURATED_SUBREDDITS = [
    {"id": "r/AskReddit", "name": "r/AskReddit", "color": "#ff4500", "theme": "crazy_questions"},
    {"id": "r/AmItheAsshole", "name": "r/AmItheAsshole", "color": "#10b981", "theme": "drama_conflict"},
    {"id": "r/confession", "name": "r/confession", "color": "#8b5cf6", "theme": "secret_confessions"},
    {"id": "r/Showerthoughts", "name": "r/Showerthoughts", "color": "#06b6d4", "theme": "mind_blowing"},
    {"id": "r/nosleep", "name": "r/nosleep", "color": "#ef4444", "theme": "scary_horror"}
]


class RedditStoryGenerator:
    """Generates viral Reddit stories and visual UI cards."""

    @classmethod
    async def generate_story(
        cls,
        subreddit: str = "r/AskReddit",
        custom_prompt: str = "",
        gemini_api_key: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Generates a compelling Reddit story with title, author, upvotes, and narration script.
        """
        api_key = gemini_api_key.strip() if gemini_api_key else os.getenv("GEMINI_API_KEY", "")

        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    f"Create a viral Reddit Shorts story for {subreddit}.\n"
                    f"Custom Prompt: {custom_prompt or 'An unbelievable true story with unexpected twist'}\n"
                    f"Target length: 120-160 words (around 35-45 seconds spoken).\n\n"
                    f"Return JSON ONLY with this format:\n"
                    f"{{\n"
                    f'  "subreddit": "{subreddit}",\n'
                    f'  "title": "Compelling Reddit Post Title (e.g. My boss fired me for doing my job, so I took his entire company down...)",\n'
                    f'  "author": "u/throwaway_{uuid.uuid4().hex[:4]}",\n'
                    f'  "upvotes": "28.4k",\n'
                    f'  "script": "The full first-person spoken story text without stage directions."\n'
                    f"}}"
                )
                response = model.generate_content(prompt)
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except Exception as e:
                print(f"Gemini Reddit story fallback: {e}")

        # Procedural fallback Reddit stories
        fallback_stories = [
            {
                "subreddit": subreddit,
                "title": "My landlord tried to keep my $3,000 security deposit for 'air wear and tear', so I investigated his tax records.",
                "author": f"u/JusticeSeeker_{uuid.uuid4().hex[:4]}",
                "upvotes": "34.1k",
                "script": (
                    "When I moved out of my apartment, my landlord sent me an email saying he was keeping my entire three thousand dollar deposit. "
                    "His excuse? 'Excessive breathing and air wear inside the unit'. I knew that was complete nonsense. "
                    "Instead of arguing with him, I pulled up the city property registry and public building permits. "
                    "Turns out, the entire third-floor unit I was renting was built illegally without any permits. "
                    "I sent one final email with the city housing violation code attached. "
                    "Within six minutes, the full three thousand dollars was wired back into my bank account."
                )
            },
            {
                "subreddit": subreddit,
                "title": "What is the creepiest glitch in reality you have ever personally experienced?",
                "author": f"u/NightWatcher_{uuid.uuid4().hex[:4]}",
                "upvotes": "41.9k",
                "script": (
                    "Back in twenty eighteen, I was driving home on an empty highway around two in the morning. "
                    "Suddenly, the radio cut out completely and every digital clock in my car reset to twelve zero zero. "
                    "Up ahead, I saw the exact same red truck pass me three different times within two minutes, with the exact same cracked taillight. "
                    "When I finally pulled into my driveway, the trip that normally takes twenty minutes had somehow taken four hours. "
                    "To this day, I have no idea where those missing hours went."
                )
            }
        ]
        import random
        return random.choice(fallback_stories)

    @classmethod
    def create_reddit_card_image(
        cls,
        subreddit: str,
        author: str,
        title: str,
        upvotes: str = "24.5k",
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Renders a pixel-perfect dark-mode Reddit post UI card overlay (1080x500 PNG with transparency).
        """
        if not output_path:
            output_path = TEMP_DIR / f"reddit_card_{uuid.uuid4().hex[:6]}.png"

        width = 980
        height = 420
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Reddit Dark Card background
        card_bg = (24, 26, 32, 240)
        draw.rounded_rectangle([0, 0, width, height], radius=28, fill=card_bg, outline=(45, 49, 66, 255), width=2)

        # Load font
        font_file = FONTS_DIR / "Montserrat-ExtraBold.ttf"
        if not font_file.exists():
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        try:
            sub_font = ImageFont.truetype(str(font_file), size=28)
            title_font = ImageFont.truetype(str(font_file), size=36)
            upvote_font = ImageFont.truetype(str(font_file), size=24)
        except Exception:
            sub_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            upvote_font = ImageFont.load_default()

        # Reddit Icon circle (Orange-Red)
        draw.ellipse([40, 35, 90, 85], fill=(255, 69, 0))
        draw.ellipse([55, 50, 75, 70], fill=(255, 255, 255))

        # Subreddit name & Author
        draw.text((110, 38), subreddit, fill=(255, 255, 255), font=sub_font)
        draw.text((110, 72), f"Posted by {author} • 4h ago", fill=(148, 163, 184), font=upvote_font)

        # Upvote pill on top right
        draw.rounded_rectangle([width - 170, 35, width - 40, 85], radius=20, fill=(35, 39, 52), outline=(55, 60, 80))
        draw.text((width - 150, 48), f"⬆ {upvotes}", fill=(255, 69, 0), font=upvote_font)

        # Wrap and Draw Title
        words = title.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            test_s = " ".join(cur_line)
            bbox = draw.textbbox((0, 0), test_s, font=title_font)
            if (bbox[2] - bbox[0]) > 880 and len(cur_line) > 1:
                cur_line.pop()
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        # Draw up to 3 lines
        for idx, line in enumerate(lines[:3]):
            draw.text((40, 130 + (idx * 50)), line, fill=(241, 245, 249), font=title_font)

        # Bottom stats bar
        draw.line([40, height - 60, width - 40, height - 60], fill=(45, 49, 66), width=1)
        draw.text((40, height - 45), "💬 1,429 Comments   ↗ Share   ⭐ Award", fill=(148, 163, 184), font=upvote_font)

        img.save(str(output_path), format="PNG")
        return output_path
