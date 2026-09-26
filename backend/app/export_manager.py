"""
Export & Asset Organization Manager for CR Remover Studio.
Manages structured desktop export directory ~/Desktop/CR_Remover_Exports/
with dedicated category subfolders and standardized, self-describing file naming.
"""

from pathlib import Path
import os
import re
import time
import shutil
import subprocess
import platform
from typing import Dict, Any, List, Optional

from app.config import (
    READY_EXPORT_DIR,
    EXPORTS_VIRAL_SHORTS_DIR,
    EXPORTS_FULL_VIDEOS_DIR,
    EXPORTS_REDDIT_STORIES_DIR,
    EXPORTS_PODCAST_CLIPS_DIR,
    EXPORTS_THUMBNAILS_DIR,
    EXPORTS_AUDIO_STEMS_DIR,
    EXPORTS_METADATA_DIR,
    EXPORTS_BATCH_DIR,
    ALL_EXPORT_DIRS
)


class ExportManager:
    """Handles automated directory categorization, descriptive file naming, and export staging."""

    @staticmethod
    def init_export_structure() -> None:
        """Ensures all export directories and folder guide exist on Desktop."""
        for directory in ALL_EXPORT_DIRS:
            directory.mkdir(parents=True, exist_ok=True)

        guide_file = READY_EXPORT_DIR / "00_FOLDER_GUIDE.txt"
        if not guide_file.exists():
            guide_content = """================================================================================
🎬 CR REMOVER STUDIO — ORGANIZED DESKTOP EXPORTS VAULT
================================================================================
Location: ~/Desktop/CR_Remover_Exports/

All videos, thumbnails, audio tracks, and SEO metadata are automatically organized
into dedicated folders with self-describing filenames so you can identify content
instantly without opening every single file.

📁 DIRECTORY STRUCTURE:
--------------------------------------------------------------------------------
├── 01_Viral_Shorts/
│   └── 9:16 vertical viral shorts ready for YouTube Shorts, TikTok & IG Reels
│       Format: VIRAL_SHORT_[Topic]_[Preset]_[Aspect]_[Timestamp].mp4
│
├── 02_Full_Edited_Videos/
│   └── Full-length copyright-free transformed videos (16:9 & horizontal)
│       Format: EDITED_VIDEO_[Title]_[Preset]_[Aspect]_[Timestamp].mp4
│
├── 03_Reddit_Stories/
│   └── Reddit drama & confession story shorts with authentic UI cards
│       Format: REDDIT_STORY_[Subreddit]_[Title]_[Timestamp].mp4
│
├── 04_Podcast_Clips/
│   └── 2-Person AI debate and split-screen conversation shorts
│       Format: PODCAST_DEBATE_[Topic]_[Style]_[Timestamp].mp4
│
├── 05_Thumbnails_Covers/
│   └── High-CTR 9:16 cover images and video thumbnails (.jpg / .png)
│       Format: THUMBNAIL_COVER_[Title]_[Style]_[Resolution]_[Timestamp].jpg
│
├── 06_Audio_Stems_Voice/
│   └── Extracted vocals, instrumental stems, neural TTS voiceovers, BGM
│       Format: AUDIO_TTS_[Voice]_[Title]_[Timestamp].mp3
│       Format: AUDIO_VOCALS_[Title]_[Timestamp].wav
│
├── 07_Metadata_Captions/
│   └── Viral titles, pinned comment hooks, hashtags, and .srt subtitle files
│       Format: METADATA_SEO_[Title]_[Timestamp].txt
│       Format: CAPTIONS_SUBTITLES_[Title]_[Timestamp].srt
│
└── 08_Batch_Campaigns/
    └── Complete multi-video batch folders organized by campaign date
--------------------------------------------------------------------------------
⚡ Transformed with CR Remover Studio — AI Anti-Fingerprint & Copyright Shield
================================================================================
"""
            try:
                with open(guide_file, "w", encoding="utf-8") as f:
                    f.write(guide_content)
            except Exception as e:
                print(f"[ExportManager] Warning: could not write guide file: {e}")

    @staticmethod
    def clean_name(text: str, max_chars: int = 40) -> str:
        """
        Sanitizes and formats a title into a clean, human-readable file slug.
        Example: "My Landlord Kept $3,000 Deposit! (Crazy Story)" -> "My_Landlord_Kept_3000_Deposit_Crazy_Story"
        """
        if not text:
            return "Untitled"
        # Remove file extensions if present
        text = re.sub(r'\.(mp4|mov|avi|mkv|webm|mp3|wav|jpg|png|txt|srt)$', '', text, flags=re.IGNORECASE)
        # Strip out special characters, keeping alphanumeric and spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s_-]', '', text)
        # Replace spaces or multiple underscores with single underscore
        cleaned = re.sub(r'[\s-]+', '_', cleaned)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        if not cleaned:
            cleaned = "Item"
        return cleaned[:max_chars].rstrip('_')

    @staticmethod
    def get_timestamp() -> str:
        """Returns standard timestamp string YYYYMMDD_HHMMSS."""
        return time.strftime("%Y%m%d_%H%M%S")

    # =========================================================================
    # STANDARDIZED DESCRIPTIVE FILENAME BUILDERS
    # =========================================================================

    @classmethod
    def name_viral_short(
        cls,
        topic_or_title: str,
        preset: str = "Bypass",
        aspect: str = "9x16",
        ext: str = "mp4"
    ) -> str:
        """
        Returns: VIRAL_SHORT_[Topic]_[Preset]_[Aspect]_[Timestamp].mp4
        Example: VIRAL_SHORT_How_To_Manipulate_Time_Bypass_9x16_20260926_214530.mp4
        """
        c_title = cls.clean_name(topic_or_title, max_chars=35)
        c_preset = cls.clean_name(preset, max_chars=16)
        ts = cls.get_timestamp()
        return f"VIRAL_SHORT_{c_title}_{c_preset}_{aspect}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_full_video(
        cls,
        title: str,
        preset: str = "CleanEdit",
        aspect: str = "16x9",
        ext: str = "mp4"
    ) -> str:
        """
        Returns: EDITED_VIDEO_[Title]_[Preset]_[Aspect]_[Timestamp].mp4
        Example: EDITED_VIDEO_Tesla_Optimus_Review_Aggressive_16x9_20260926_214530.mp4
        """
        c_title = cls.clean_name(title, max_chars=40)
        c_preset = cls.clean_name(preset, max_chars=16)
        ts = cls.get_timestamp()
        return f"EDITED_VIDEO_{c_title}_{c_preset}_{aspect}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_reddit_story(
        cls,
        subreddit: str,
        title: str,
        aspect: str = "9x16",
        ext: str = "mp4"
    ) -> str:
        """
        Returns: REDDIT_STORY_[Subreddit]_[Title]_[Aspect]_[Timestamp].mp4
        Example: REDDIT_STORY_rAskReddit_LandlordDepositScam_9x16_20260926_214530.mp4
        """
        c_sub = cls.clean_name(subreddit.replace("r/", ""), max_chars=15)
        c_title = cls.clean_name(title, max_chars=35)
        ts = cls.get_timestamp()
        return f"REDDIT_STORY_r{c_sub}_{c_title}_{aspect}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_podcast_short(
        cls,
        topic: str,
        style: str = "SplitScreen",
        aspect: str = "9x16",
        ext: str = "mp4"
    ) -> str:
        """
        Returns: PODCAST_DEBATE_[Topic]_[Style]_[Aspect]_[Timestamp].mp4
        Example: PODCAST_DEBATE_AI_Taking_Jobs_SplitScreen_9x16_20260926_214530.mp4
        """
        c_topic = cls.clean_name(topic, max_chars=35)
        c_style = cls.clean_name(style, max_chars=16)
        ts = cls.get_timestamp()
        return f"PODCAST_DEBATE_{c_topic}_{c_style}_{aspect}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_thumbnail_cover(
        cls,
        title: str,
        style: str = "ViralYellow",
        resolution: str = "1080x1920",
        ext: str = "jpg"
    ) -> str:
        """
        Returns: THUMBNAIL_COVER_[Title]_[Style]_[Resolution]_[Timestamp].jpg
        Example: THUMBNAIL_COVER_Psychology_Facts_ViralYellow_1080x1920_20260926_214530.jpg
        """
        c_title = cls.clean_name(title, max_chars=35)
        c_style = cls.clean_name(style, max_chars=16)
        ts = cls.get_timestamp()
        return f"THUMBNAIL_COVER_{c_title}_{c_style}_{resolution}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_audio_stem(
        cls,
        stem_type: str,
        title: str,
        voice_or_extra: str = "",
        ext: str = "mp3"
    ) -> str:
        """
        Returns: AUDIO_[TYPE]_[Extra]_[Title]_[Timestamp].mp3
        Example: AUDIO_TTS_VOICE_GuyNeural_Mind_Blowing_Facts_20260926_214530.mp3
        Example: AUDIO_VOCALS_EXTRACTED_Original_Car_Review_20260926_214530.wav
        """
        c_type = cls.clean_name(stem_type, max_chars=15).upper()
        c_extra = f"{cls.clean_name(voice_or_extra, max_chars=15)}_" if voice_or_extra else ""
        c_title = cls.clean_name(title, max_chars=30)
        ts = cls.get_timestamp()
        return f"AUDIO_{c_type}_{c_extra}{c_title}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_metadata_file(
        cls,
        title: str,
        info_type: str = "SEO_TAGS",
        ext: str = "txt"
    ) -> str:
        """
        Returns: METADATA_[TYPE]_[Title]_[Timestamp].txt
        Example: METADATA_SEO_TAGS_How_To_Manipulate_Time_20260926_214530.txt
        """
        c_type = cls.clean_name(info_type, max_chars=15).upper()
        c_title = cls.clean_name(title, max_chars=35)
        ts = cls.get_timestamp()
        return f"METADATA_{c_type}_{c_title}_{ts}.{ext.lstrip('.')}"

    @classmethod
    def name_captions_file(
        cls,
        title: str,
        sync_type: str = "WordSync",
        ext: str = "srt"
    ) -> str:
        """
        Returns: CAPTIONS_SUBTITLES_[Title]_[SyncType]_[Timestamp].srt
        Example: CAPTIONS_SUBTITLES_How_To_Manipulate_Time_WordSync_20260926_214530.srt
        """
        c_title = cls.clean_name(title, max_chars=35)
        c_sync = cls.clean_name(sync_type, max_chars=15)
        ts = cls.get_timestamp()
        return f"CAPTIONS_SUBTITLES_{c_title}_{c_sync}_{ts}.{ext.lstrip('.')}"

    # =========================================================================
    # EXPORTING METHODS & ACTIONS
    # =========================================================================

    @classmethod
    def export_video_to_category(
        cls,
        source_video_path: Path,
        category: str,  # 'viral_shorts', 'full_videos', 'reddit', 'podcast'
        descriptive_filename: str,
        metadata_dict: Optional[Dict[str, Any]] = None,
        cover_image_path: Optional[Path] = None,
        captions_srt_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exports a video and any associated metadata, cover image, or subtitles
        into the organized category folders on Desktop.
        """
        cls.init_export_structure()

        if not source_video_path.exists():
            raise FileNotFoundError(f"Source video file not found: {source_video_path}")

        # Choose destination folder
        cat_lower = category.lower()
        if "viral" in cat_lower or "short" in cat_lower:
            target_dir = EXPORTS_VIRAL_SHORTS_DIR
        elif "reddit" in cat_lower:
            target_dir = EXPORTS_REDDIT_STORIES_DIR
        elif "podcast" in cat_lower:
            target_dir = EXPORTS_PODCAST_CLIPS_DIR
        elif "full" in cat_lower or "edit" in cat_lower or "video" in cat_lower:
            target_dir = EXPORTS_FULL_VIDEOS_DIR
        else:
            target_dir = READY_EXPORT_DIR

        dest_video = target_dir / descriptive_filename
        shutil.copyfile(source_video_path, dest_video)

        exported_items = {
            "video_path": str(dest_video),
            "video_filename": dest_video.name,
            "folder": str(target_dir),
            "category": target_dir.name
        }

        # Export Cover Image to 05_Thumbnails_Covers/
        if cover_image_path and cover_image_path.exists():
            cover_name = descriptive_filename.rsplit('.', 1)[0] + "_COVER.jpg"
            dest_cover = EXPORTS_THUMBNAILS_DIR / cover_name
            shutil.copyfile(cover_image_path, dest_cover)
            exported_items["cover_path"] = str(dest_cover)

        # Export Metadata to 07_Metadata_Captions/
        if metadata_dict:
            meta_name = descriptive_filename.rsplit('.', 1)[0] + "_METADATA.txt"
            dest_meta = EXPORTS_METADATA_DIR / meta_name
            title_opts = metadata_dict.get("titles", [metadata_dict.get("title", "")])
            if isinstance(title_opts, str):
                title_opts = [title_opts]

            titles_formatted = "\n".join([f"{i+1}. {t}" for i, t in enumerate(title_opts[:3])]) if title_opts else "1. Ready Video"

            info_text = f"""================================================================================
🎬 CR REMOVER STUDIO — CONTENT METADATA & SEO PACK
================================================================================
Video File: {dest_video.name}
Full Path:  {dest_video}
Category:   {target_dir.name}
Exported:   {time.strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

🔥 HIGH-CTR VIRAL TITLE OPTIONS (Choose one):
{titles_formatted}

📌 PINNED COMMENT ENGAGEMENT HOOK:
{metadata_dict.get('hook', 'Drop your thoughts in the comments below! 👇')}

📝 OPTIMIZED DESCRIPTION & VIRAL HASHTAGS:
{metadata_dict.get('description', '#viral #shorts #trending')}

🏷️ SEARCH TAGS / KEYWORDS:
{', '.join(metadata_dict.get('tags', ['viral', 'shorts', 'trending', 'cr_remover']))}

================================================================================
⚡ Transformed with CR Remover Studio (Anti-Fingerprint Applied)
================================================================================
"""
            with open(dest_meta, "w", encoding="utf-8") as f:
                f.write(info_text)
            exported_items["metadata_path"] = str(dest_meta)

        # Export Subtitles to 07_Metadata_Captions/
        if captions_srt_content:
            captions_name = descriptive_filename.rsplit('.', 1)[0] + "_CAPTIONS.srt"
            dest_srt = EXPORTS_METADATA_DIR / captions_name
            with open(dest_srt, "w", encoding="utf-8") as f:
                f.write(captions_srt_content)
            exported_items["captions_path"] = str(dest_srt)

        return exported_items

    @classmethod
    def open_exports_folder(cls) -> Dict[str, Any]:
        """Opens the desktop export folder in the native OS file explorer."""
        cls.init_export_structure()
        path_str = str(READY_EXPORT_DIR)
        current_os = platform.system().lower()

        try:
            if "linux" in current_os:
                subprocess.Popen(["xdg-open", path_str])
            elif "darwin" in current_os:
                subprocess.Popen(["open", path_str])
            elif "windows" in current_os:
                os.startfile(path_str)
            else:
                subprocess.Popen(["xdg-open", path_str])
            return {"status": "success", "message": f"Opened {path_str} in file explorer", "path": path_str}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open explorer: {e}", "path": path_str}

    @classmethod
    def get_exports_summary(cls) -> Dict[str, Any]:
        """
        Returns structured statistics and file listings for all organized folders
        so the frontend UI can show interactive stats and instant links.
        """
        cls.init_export_structure()
        folders_data = []
        total_files = 0
        total_bytes = 0

        categories = [
            {"id": "01_Viral_Shorts", "dir": EXPORTS_VIRAL_SHORTS_DIR, "label": "Viral Shorts (9:16)", "icon": "Sparkles"},
            {"id": "02_Full_Edited_Videos", "dir": EXPORTS_FULL_VIDEOS_DIR, "label": "Full Edited Videos", "icon": "Video"},
            {"id": "03_Reddit_Stories", "dir": EXPORTS_REDDIT_STORIES_DIR, "label": "Reddit Stories", "icon": "MessageSquare"},
            {"id": "04_Podcast_Clips", "dir": EXPORTS_PODCAST_CLIPS_DIR, "label": "Podcast Clips", "icon": "Mic"},
            {"id": "05_Thumbnails_Covers", "dir": EXPORTS_THUMBNAILS_DIR, "label": "Thumbnails & Covers", "icon": "Image"},
            {"id": "06_Audio_Stems_Voice", "dir": EXPORTS_AUDIO_STEMS_DIR, "label": "Audio & Stems", "icon": "Music"},
            {"id": "07_Metadata_Captions", "dir": EXPORTS_METADATA_DIR, "label": "Metadata & Subtitles", "icon": "FileText"},
            {"id": "08_Batch_Campaigns", "dir": EXPORTS_BATCH_DIR, "label": "Batch Campaigns", "icon": "Layers"},
        ]

        recent_files: List[Dict[str, Any]] = []

        for cat in categories:
            d: Path = cat["dir"]
            files_list = []
            dir_bytes = 0

            if d.exists():
                for f in sorted(d.glob("**/*"), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
                    if f.is_file() and not f.name.startswith("."):
                        f_stat = f.stat()
                        size = f_stat.st_size
                        mtime = f_stat.st_mtime
                        dir_bytes += size
                        total_bytes += size
                        total_files += 1

                        file_info = {
                            "filename": f.name,
                            "relative_path": str(f.relative_to(READY_EXPORT_DIR)),
                            "size_bytes": size,
                            "modified_at": mtime,
                            "modified_formatted": time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)),
                            "category": cat["id"],
                            "extension": f.suffix.lower()
                        }
                        files_list.append(file_info)
                        if len(recent_files) < 25:
                            recent_files.append(file_info)

            folders_data.append({
                "id": cat["id"],
                "label": cat["label"],
                "icon": cat["icon"],
                "path": str(d),
                "file_count": len(files_list),
                "total_bytes": dir_bytes,
                "files": files_list[:15]  # Top 15 in summary
            })

        # Sort recent files globally
        recent_files.sort(key=lambda x: x["modified_at"], reverse=True)

        return {
            "root_path": str(READY_EXPORT_DIR),
            "total_files": total_files,
            "total_bytes": total_bytes,
            "folders": folders_data,
            "recent_files": recent_files[:20]
        }
