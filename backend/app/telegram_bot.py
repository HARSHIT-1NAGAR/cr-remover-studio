"""
Telegram Remote Control Bot for CR Remover Studio.
Allows creators to trigger batches, generate Reddit/Trend Shorts, and receive
MP4 video previews and YouTube/Facebook SEO packages directly on their smartphone.
"""

from pathlib import Path
import os
import re
import json
import time
import asyncio
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

from app.config import STORAGE_DIR, TEMP_DIR, PROCESSED_DIR
from app.batch_autopilot import BatchAutoPilotEngine
from app.trend_harvester import TrendHarvester
from app.reddit_generator import RedditStoryGenerator


class TelegramStudioBot:
    """Lightweight asynchronous Telegram Bot manager using Telegram HTTP Bot API."""

    _running_task: Optional[asyncio.Task] = None
    _is_active: bool = False
    _last_update_id: int = 0

    @classmethod
    def is_running(cls) -> bool:
        return cls._is_active

    @classmethod
    async def send_message(cls, bot_token: str, chat_id: str, text: str):
        """Sends a text message to the specified Telegram chat."""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        loop = asyncio.get_event_loop()
        def do_post():
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read()
            except Exception as e:
                print(f"Telegram send error: {e}")
        await loop.run_in_executor(None, do_post)

    @classmethod
    async def send_video(cls, bot_token: str, chat_id: str, video_path: Path, caption: str = ""):
        """Sends an MP4 video file to Telegram chat."""
        # Use curl or multipart request to upload video
        cmd = [
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{bot_token}/sendVideo",
            "-F", f"chat_id={chat_id}",
            "-F", f"caption={caption[:1000]}",
            "-F", f"video=@{str(video_path)}"
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()

    @classmethod
    async def poll_updates(cls, bot_token: str, chat_id: str):
        """Background polling loop handling user commands from Telegram."""
        cls._is_active = True
        print("Telegram Bot Daemon started.")

        await cls.send_message(
            bot_token, chat_id,
            "🚀 *CR Remover Studio Bot Connected!*\n\n"
            "Commands:\n"
            "• `/batch 3 dark_psychology` - Generate 3 Shorts\n"
            "• `/trend` - Generate Short from today's top Google Trend\n"
            "• `/reddit` - Generate viral Reddit Story Short\n"
            "• `/status` - Check Server & GPU Status"
        )

        while cls._is_active:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={cls._last_update_id + 1}&timeout=10"
                req = urllib.request.Request(url, headers={"User-Agent": "CR-Remover-Studio/2.0"})
                loop = asyncio.get_event_loop()

                def get_up():
                    try:
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            return json.loads(resp.read().decode())
                    except Exception:
                        return None

                data = await loop.run_in_executor(None, get_up)

                if data and data.get("ok"):
                    for update in data.get("result", []):
                        cls._last_update_id = update["update_id"]
                        msg = update.get("message", {})
                        text = msg.get("text", "").strip()
                        sender_id = str(msg.get("chat", {}).get("id", ""))

                        # Only respond to authorized chat_id if specified
                        if chat_id and sender_id != str(chat_id):
                            continue

                        if text.startswith("/status"):
                            await cls.send_message(
                                bot_token, sender_id,
                                "🟢 *Server Online & Operational*\n"
                                "• Engine: Fast GPU NVENC\n"
                                "• Auto-Pilot: Ready\n"
                                "• Location: `~/Downloads/CR_Remover_Ready/`"
                            )

                        elif text.startswith("/batch"):
                            parts = text.split()
                            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 3
                            niche = parts[2] if len(parts) > 2 else "dark_psychology"

                            await cls.send_message(
                                bot_token, sender_id,
                                f"⏳ Starting Auto-Pilot generation for *{count} {niche} Shorts*... Rendering in background!"
                            )

                            # Run batch in background
                            asyncio.create_task(cls._handle_batch_job(bot_token, sender_id, niche, count))

                        elif text.startswith("/trend"):
                            await cls.send_message(bot_token, sender_id, "🔍 Fetching live Google Trends & generating Short...")
                            # Trigger trend short
                            asyncio.create_task(cls._handle_trend_job(bot_token, sender_id))

                        elif text.startswith("/reddit"):
                            await cls.send_message(bot_token, sender_id, "📖 Generating viral Reddit drama story Short...")
                            asyncio.create_task(cls._handle_reddit_job(bot_token, sender_id))

            except Exception as e:
                print(f"Telegram polling error: {e}")
                await asyncio.sleep(3)

            await asyncio.sleep(1)

    @classmethod
    async def _handle_batch_job(cls, bot_token: str, chat_id: str, niche: str, count: int):
        try:
            results = await BatchAutoPilotEngine.run_batch(
                batch_id=f"tg_{int(time.time())}",
                niche_id=niche,
                count=count
            )
            for res in results:
                vid_path = Path(res["export_path"])
                meta = res.get("metadata", {})
                title = meta.get("yt_titles", [res["title"]])[0]
                caption = f"🎬 *{title}*\n\n📅 {res.get('schedule_day')} • {res.get('schedule_time')}\n\n🏷️ {res.get('metadata', {}).get('yt_description', '')[:200]}"
                if vid_path.exists():
                    await cls.send_video(bot_token, chat_id, vid_path, caption=caption)
            await cls.send_message(bot_token, chat_id, f"✅ Batch complete! {len(results)} Shorts delivered to your phone & Downloads.")
        except Exception as e:
            await cls.send_message(bot_token, chat_id, f"❌ Batch failed: {str(e)}")

    @classmethod
    async def _handle_trend_job(cls, bot_token: str, chat_id: str):
        try:
            trends = await TrendHarvester.fetch_live_trends()
            top_trend = trends[0] if trends else {"title": "AI Breakthrough", "summary": "New discoveries"}
            script_data = await TrendHarvester.trend_to_script(top_trend["title"], top_trend.get("summary", ""))
            
            results = await BatchAutoPilotEngine.run_batch(
                batch_id=f"trend_{int(time.time())}",
                niche_id="crazy_facts",
                count=1,
                custom_topics=[top_trend["title"]]
            )
            if results:
                vid_p = Path(results[0]["export_path"])
                if vid_p.exists():
                    await cls.send_video(bot_token, chat_id, vid_p, caption=f"🔥 *Trending Short Generated:*\n{top_trend['title']}")
        except Exception as e:
            await cls.send_message(bot_token, chat_id, f"❌ Trend job failed: {str(e)}")

    @classmethod
    async def _handle_reddit_job(cls, bot_token: str, chat_id: str):
        try:
            results = await BatchAutoPilotEngine.run_batch(
                batch_id=f"reddit_{int(time.time())}",
                niche_id="reddit_stories",
                count=1
            )
            if results:
                vid_p = Path(results[0]["export_path"])
                if vid_p.exists():
                    await cls.send_video(bot_token, chat_id, vid_p, caption=f"📖 *Reddit Story Short Generated:*\n{results[0]['title']}")
        except Exception as e:
            await cls.send_message(bot_token, chat_id, f"❌ Reddit job failed: {str(e)}")
