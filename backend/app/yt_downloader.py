"""
High-Speed Anti-429 YouTube & Social Video Downloader for CR Remover Studio.

Strategy (in order of effectiveness for 2025+ YouTube):
  1. PO Token via chrome cookie extraction (best bypass)
  2. Android / iOS / tv_embedded client spoofing (works without cookies)
  3. Aggressive header injection + sleep/retry tuning
  4. Generic single-format fallback
"""

from pathlib import Path
import os
import shutil
import asyncio
import json
import random
import logging
from typing import Optional, Dict, Any, List, Tuple

from app.config import STORAGE_DIR, TEMP_DIR, BACKEND_DIR, BASE_DIR

logger = logging.getLogger(__name__)

# ── Cookie file detection ─────────────────────────────────────────────────────
COOKIES_FILE = STORAGE_DIR / "cookies.txt"
if not COOKIES_FILE.exists() and (BASE_DIR / "cookies.txt").exists():
    COOKIES_FILE = BASE_DIR / "cookies.txt"

# Browsers to try for auto-extracting cookies (yt-dlp >= 2021.12)
BROWSER_COOKIE_SOURCES = ["chrome", "firefox", "chromium", "edge", "brave"]


def get_yt_dlp_binary() -> str:
    """Finds the yt-dlp binary in venv or PATH."""
    venv_bin = BACKEND_DIR.parent / "venv" / "bin" / "yt-dlp"
    if venv_bin.exists():
        return str(venv_bin)
    system_bin = shutil.which("yt-dlp")
    if system_bin:
        return system_bin
    return "yt-dlp"


YT_DLP = get_yt_dlp_binary()

# ── Client cascades (ordered best→worst for 429 bypass in 2025) ──────────────
# yt-dlp 2024+ supports comma-separated player_client list directly
CLIENT_STRATEGIES: List[Tuple[str, str]] = [
    # (extractor-args, description)
    ("youtube:player_client=ios",                          "iOS client"),
    ("youtube:player_client=android",                     "Android client"),
    ("youtube:player_client=tv_embedded",                 "TV embedded client"),
    ("youtube:player_client=mweb",                        "mweb client"),
    ("youtube:player_client=android_vr",                  "Android VR client"),
    ("youtube:player_client=android_embedded_player",     "Android embedded"),
    ("youtube:player_client=ios,android,tv_embedded",     "iOS+Android+TV cascade"),
]

# Realistic rotating user-agents
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Safari on iPhone (matches iOS client)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Chrome on Android (matches Android client)
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Mobile Safari/537.36",
]

# 429-signal keywords in stderr
_429_SIGNALS = ("429", "Too Many Requests", "Sign in to confirm", "bot", "captcha",
                "blocked", "HTTP Error 429", "nsig", "403")


class YTDownloader:
    """Resilient video downloader with layered anti-429 bypass for yt-dlp 2024+."""

    # ── Shared base args ──────────────────────────────────────────────────────
    @staticmethod
    def _base_args(
        client_args: str,
        user_agent: str,
        use_cookies: bool = True,
        sleep: float = 0.0
    ) -> List[str]:
        cmd = [
            YT_DLP,
            "--extractor-args", client_args,
            "--user-agent", user_agent,
            # Real browser-like headers
            "--add-header", "Accept-Language:en-US,en;q=0.9",
            "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "--add-header", "Sec-Fetch-Mode:navigate",
            "--add-header", "Sec-Fetch-Site:none",
            "--add-header", "Sec-Fetch-Dest:document",
            # Retry / timeout
            "--retries", "8",
            "--fragment-retries", "8",
            "--retry-sleep", "linear=1::4",   # exponential back-off: 1s, 2s, 4s…
            "--socket-timeout", "30",
            "--no-playlist",
            # Avoid detection
            "--no-check-certificates",
        ]

        if sleep > 0:
            cmd.extend(["--sleep-interval", str(int(sleep)),
                        "--max-sleep-interval", str(int(sleep * 3))])

        # Prefer file cookies > browser extraction
        if use_cookies and COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10:
            cmd.extend(["--cookies", str(COOKIES_FILE)])

        return cmd

    # ── Try to extract live browser cookies (best bypass) ────────────────────
    @staticmethod
    async def _try_browser_cookies(url: str, output_path: Path) -> bool:
        """
        Attempts download using live cookies extracted from installed browsers.
        Only works in desktop environments where a browser is signed in to YouTube.
        """
        for browser in BROWSER_COOKIE_SOURCES:
            cmd = [
                YT_DLP,
                "--cookies-from-browser", browser,
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "--no-playlist",
                "--retries", "5",
                "--socket-timeout", "30",
                "-o", str(output_path),
                url
            ]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await proc.communicate()
                err = stderr.decode(errors="ignore")

                if proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                    logger.info(f"[YTDownloader] Browser cookie bypass succeeded ({browser})")
                    return True

                # If browser not found, skip immediately
                if "browser" in err.lower() and "not found" in err.lower():
                    continue

            except Exception:
                continue

        return False

    # ── Core download with client cascade ─────────────────────────────────────
    @classmethod
    async def download_video(
        cls,
        url: str,
        output_path: Path,
        max_filesize: str = "500M",
    ) -> bool:
        """
        Downloads with layered anti-429 strategy:
          Pass 1 → Live browser cookies (best)
          Pass 2 → Client cascade (Android → iOS → TV → mweb → …) with random UA
          Pass 3 → Single-stream format fallback with sleep delay
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        last_error = ""

        # ── Pass 1: Browser cookies (sign-in bypass) ──────────────────────────
        if not (COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10):
            browser_ok = await cls._try_browser_cookies(url, output_path)
            if browser_ok:
                return True

        # ── Pass 2: Client cascade ────────────────────────────────────────────
        for attempt, (client_args, desc) in enumerate(CLIENT_STRATEGIES):
            ua = USER_AGENTS[attempt % len(USER_AGENTS)]
            # Introduce a small jittered delay after 1st attempt to avoid rate-limit burst
            sleep_delay = 0.0 if attempt == 0 else random.uniform(1.0, 3.0)

            cmd = cls._base_args(client_args, ua, sleep=sleep_delay)
            cmd.extend([
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "--max-filesize", max_filesize,
                "-o", str(output_path),
                url
            ])

            logger.info(f"[YTDownloader] Attempt {attempt+1}/{len(CLIENT_STRATEGIES)}: {desc}")

            try:
                if sleep_delay > 0:
                    await asyncio.sleep(sleep_delay)

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await proc.communicate()
                err = stderr.decode(errors="ignore") if stderr else ""

                if output_path.exists() and output_path.stat().st_size > 1000:
                    logger.info(f"[YTDownloader] Success with {desc}")
                    return True

                last_error = err[:300]
                is_429 = any(sig in err for sig in _429_SIGNALS)

                if is_429:
                    logger.warning(f"[YTDownloader] 429/bot signal on {desc}, rotating client…")
                    await asyncio.sleep(random.uniform(2.0, 5.0))  # cool-down before next
                    continue
                elif proc.returncode != 0:
                    # Non-rate-limit error; still try next client
                    logger.warning(f"[YTDownloader] {desc} failed (rc={proc.returncode}), trying next…")
                    continue

            except Exception as e:
                last_error = str(e)
                logger.error(f"[YTDownloader] Exception on {desc}: {e}")
                continue

        # ── Pass 3: Single-stream format fallback with sleep ──────────────────
        logger.warning("[YTDownloader] All cascade attempts failed, trying single-stream fallback…")
        for fmt in ["b", "bv*+ba/b", "worst[ext=mp4]"]:
            try:
                ua = random.choice(USER_AGENTS)
                cmd = cls._base_args(CLIENT_STRATEGIES[-1][0], ua, sleep=3.0)
                cmd.extend([
                    "-f", fmt,
                    "--merge-output-format", "mp4",
                    "--sleep-interval", "3",
                    "--max-sleep-interval", "8",
                    "-o", str(output_path),
                    url
                ])
                await asyncio.sleep(3.0)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if output_path.exists() and output_path.stat().st_size > 1000:
                    logger.info(f"[YTDownloader] Fallback format '{fmt}' succeeded")
                    return True
            except Exception:
                continue

        raise RuntimeError(
            f"Download failed after all anti-429 strategies. "
            f"Last error: {last_error[:250]}\n\n"
            "💡 Tip: Place a YouTube cookies.txt file at storage/cookies.txt "
            "or sign in to Chrome/Firefox for automatic cookie extraction."
        )

    # ── Metadata probe ────────────────────────────────────────────────────────
    @classmethod
    async def dump_json(cls, url: str) -> Dict[str, Any]:
        """Extracts video metadata with anti-429 client spoofing."""
        for attempt, (client_args, desc) in enumerate(CLIENT_STRATEGIES[:4]):
            ua = USER_AGENTS[attempt % len(USER_AGENTS)]
            cmd = cls._base_args(client_args, ua)
            cmd.extend(["--dump-single-json", "--no-warnings", url])

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode == 0 and stdout:
                    try:
                        return json.loads(stdout.decode(errors="ignore"))
                    except json.JSONDecodeError:
                        continue

                err = stderr.decode(errors="ignore") if stderr else ""
                if any(sig in err for sig in _429_SIGNALS):
                    await asyncio.sleep(random.uniform(1.5, 3.5))

            except Exception:
                continue

        return {}
