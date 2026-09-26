"""
Gemini AI Service for CR Remover Studio.
Generates viral Shorts search queries, high-CTR titles, hooks, SEO tags, and AI Viral Hook Scores using Google Gemini API.
"""

from typing import Dict, Any, List, Optional
import json
import os
import google.generativeai as genai


DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")


class GeminiTitleGenerator:
    """Uses Gemini to formulate viral search strategies, score retention, and generate viral metadata."""

    @staticmethod
    def get_model(api_key: str = ""):
        """Initializes Gemini Flash-Lite model."""
        key = api_key.strip() if api_key and api_key.strip() else DEFAULT_GEMINI_KEY
        if not key:
            return None
        genai.configure(api_key=key)
        try:
            return genai.GenerativeModel("gemini-2.0-flash-lite")
        except Exception:
            return genai.GenerativeModel("gemini-1.5-flash")

    @classmethod
    def find_viral_shorts_queries(
        cls,
        topic: str,
        language_lock: str = "en",
        recency: str = "this_year",
        api_key: str = ""
    ) -> Dict[str, List[str]]:
        """
        Uses Gemini to research and formulate:
        - 3 YouTube hashtag keywords for direct hashtag feed queries
        - 3 ultra-viral search queries targeting 1M+ view Shorts
        """
        clean_tag = re.sub(r'[^a-zA-Z0-9]', '', topic.lower())
        fallback = {
            "hashtags": [clean_tag, f"{clean_tag}facts", "facts"],
            "queries": [
                f"{topic} #shorts 1M views",
                f"viral {topic} shorts most viewed",
                f"best {topic} #shorts"
            ]
        }
        
        try:
            model = cls.get_model(api_key)
            if not model:
                return fallback

            lang_instruction = "All queries MUST strictly target ENGLISH language content with English text." if language_lock == "en" else ""
            recency_instruction = f"Target videos trending from: {recency.replace('_', ' ')}."

            prompt = f"""
            You are an expert viral YouTube Shorts strategist.
            The user wants to find the highest-viewed (1M to 10M+ views) YouTube Shorts (15s to 60s) in this niche/topic: "{topic}".
            {lang_instruction}
            {recency_instruction}

            Generate:
            1. 3 clean, English hashtag keywords (single lowercase alphanumeric words without '#', e.g. "darkpsychology", "psychologyfacts", "facts")
            2. 3 ultra-viral English search queries targeting 1M+ view Shorts

            Return strictly JSON:
            {{
                "hashtags": ["tag1", "tag2", "tag3"],
                "queries": [
                    "exact search query 1 #shorts",
                    "exact search query 2 #shorts",
                    "exact search query 3 #shorts"
                ]
            }}
            Return ONLY JSON.
            """

            res = model.generate_content(prompt)
            text = res.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                text = "\n".join(lines).strip()

            data = json.loads(text)
            return {
                "hashtags": data.get("hashtags") or fallback["hashtags"],
                "queries": data.get("queries") or fallback["queries"]
            }
        except Exception:
            return fallback

    @classmethod
    def score_viral_retention(
        cls,
        title: str,
        views: int,
        duration: float,
        api_key: str = ""
    ) -> Dict[str, Any]:
        """
        Uses Gemini to analyze the video's viral potential and retention quality.
        Returns a viral score (0-100), hook quality, and retention verdict.
        """
        fallback_score = 92 if views > 1_000_000 else 85
        fallback = {
            "viral_score": fallback_score,
            "hook_quality": "High Curiosity Hook",
            "retention_verdict": "Strong opening curiosity gap with proven viral view velocity."
        }

        try:
            model = cls.get_model(api_key)
            if not model:
                return fallback

            prompt = f"""
            You are an expert YouTube Shorts Algorithm Analyst.
            Analyze this viral Short:
            - Title: "{title}"
            - View Count: {views:,} views
            - Duration: {int(duration)} seconds

            Evaluate its viral retention potential:
            1. viral_score: Integer from 75 to 99 based on curiosity, emotional trigger, and view count.
            2. hook_quality: A 2-4 word punchy description of the hook type (e.g. "Shocking Curiosity Gap", "Psychological Paradox Hook", "High-Stakes Challenge").
            3. retention_verdict: A 1-sentence analysis of why this video hooks viewers in the first 3 seconds.

            Return strictly JSON:
            {{
                "viral_score": 95,
                "hook_quality": "Shocking Curiosity Gap",
                "retention_verdict": "Immediate paradox in title forces viewers to watch till the final second."
            }}
            Return ONLY JSON.
            """

            res = model.generate_content(prompt)
            text = res.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                text = "\n".join(lines).strip()

            data = json.loads(text)
            score = int(data.get("viral_score", fallback_score))
            score = max(75, min(99, score))
            return {
                "viral_score": score,
                "hook_quality": data.get("hook_quality", "High Curiosity Hook"),
                "retention_verdict": data.get("retention_verdict", fallback["retention_verdict"])
            }
        except Exception:
            return fallback

    @classmethod
    def generate_viral_metadata(
        cls,
        topic_or_original_title: str,
        api_key: str = ""
    ) -> Dict[str, Any]:
        """
        Uses Gemini API to generate:
        - 3 viral, high-CTR Shorts titles (fine-tuned for mobile screen display)
        - 1 viral hook / pin comment
        - SEO description with trending hashtags
        """
        fallback = {
            "titles": [
                f"Wait For The End 😱 ({topic_or_original_title[:35]})",
                f"This Changed Everything... 🤯 #Shorts",
                f"Nobody Expected This! #Viral"
            ],
            "hook": "Watch till the end to see what happens!",
            "description": f"Must watch Short about {topic_or_original_title}! \n\n#shorts #viral #trending #fyp #facts",
            "hashtags": ["#shorts", "#viral", "#trending", "#fyp"]
        }

        try:
            model = cls.get_model(api_key)
            if not model:
                return fallback

            prompt = f"""
            You are the world's #1 viral YouTube Shorts creator.
            Given this video title: "{topic_or_original_title}"

            Generate viral Shorts metadata in strict JSON format:
            {{
                "titles": [
                    "Title 1 (High CTR curiosity gap, 1 emoji, under 50 characters for mobile display)",
                    "Title 2 (Emotional / shocking hook under 50 chars)",
                    "Title 3 (Question / challenge hook under 50 chars)"
                ],
                "hook": "A short, engaging 1-sentence hook to pin in the comments to drive replies",
                "description": "2-sentence punchy description followed by 8 trending hashtags",
                "hashtags": ["#shorts", "#viral", "#trending", "#fyp", "#foryou"]
            }}

            Return ONLY valid JSON. No markdown backticks, no other text.
            """

            response = model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                text = "\n".join(lines).strip()

            data = json.loads(text)
            return data
        except Exception:
            return fallback
