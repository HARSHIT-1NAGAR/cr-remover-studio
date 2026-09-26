"""
Video Processing Pipeline for CR Remover Studio.
Builds and executes high-fidelity dynamic FFmpeg filter matrices (GPU/CPU)
with dynamic time-warping, watermark blurring, and authentic iPhone 15 Pro EXIF injection.
"""

from pathlib import Path
import os
import re
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional, Callable, List
from app.config import HAS_NVENC, TEMP_DIR
from app.schemas import TransformParams


class VideoProbe:
    """Probes media files using ffprobe to extract video metadata."""

    @staticmethod
    async def probe(file_path: Path) -> Dict[str, Any]:
        """Returns metadata dictionary for a media file."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return {"duration": 0.0, "width": 1080, "height": 1920, "fps": 30.0, "has_audio": False}

        try:
            data = json.loads(stdout.decode(errors="ignore"))
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))

            video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

            width = int(video_stream.get("width", 0)) if video_stream else 0
            height = int(video_stream.get("height", 0)) if video_stream else 0

            fps = 30.0
            if video_stream:
                r_frame_rate = video_stream.get("r_frame_rate", "30/1")
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / float(den) if float(den) > 0 else 30.0

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": audio_stream is not None,
                "video_codec": video_stream.get("codec_name", "") if video_stream else "",
                "audio_codec": audio_stream.get("codec_name", "") if audio_stream else "",
            }
        except Exception:
            return {"duration": 0.0, "width": 1080, "height": 1920, "fps": 30.0, "has_audio": False}


class VideoPipeline:
    """Builds and executes video transformation filter graphs with maximum quality."""

    @classmethod
    async def render_video(
        cls,
        input_video: Path,
        processed_audio: Path,
        output_video: Path,
        params: TransformParams,
        duration: float,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Path:
        """
        Executes the video transformation matrix and muxes with processed audio.
        Attempts GPU NVENC first; falls back to CPU libx264 on error.
        """
        try:
            return await cls._run_ffmpeg_render(
                input_video, processed_audio, output_video, params, duration,
                use_gpu=(params.use_gpu and HAS_NVENC),
                progress_callback=progress_callback
            )
        except Exception as e:
            if params.use_gpu and HAS_NVENC:
                if progress_callback:
                    progress_callback("Retrying with High-Quality CPU encoder fallback...", 55)
                return await cls._run_ffmpeg_render(
                    input_video, processed_audio, output_video, params, duration,
                    use_gpu=False,
                    progress_callback=progress_callback
                )
            raise e

    @classmethod
    async def _run_ffmpeg_render(
        cls,
        input_video: Path,
        processed_audio: Path,
        output_video: Path,
        params: TransformParams,
        duration: float,
        use_gpu: bool,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Path:
        video_filters = []

        # 1. Horizontal Mirror Flip (Only if enabled, Default is False)
        if params.mirror_flip:
            video_filters.append("hflip")

        # 2. Dynamic Ken Burns Pan & Zoom (Smooth imperceptible pan)
        zoom = params.ken_burns_zoom
        if zoom > 1.001:
            zoom_str = (
                f"scale=trunc(iw*{zoom:.3f}/2)*2:trunc(ih*{zoom:.3f}/2)*2,"
                f"crop=trunc(iw/{zoom:.3f}/2)*2:trunc(ih/{zoom:.3f}/2)*2:"
                f"'(in_w-out_w)/2 + (in_w-out_w)/4*sin(t*0.5)':"
                f"'(in_h-out_h)/2 + (in_h-out_h)/4*cos(t*0.5)'"
            )
            video_filters.append(zoom_str)

        # 3. Watermark / On-Screen Text Eraser
        if params.watermark_blur:
            pos = params.watermark_position
            if pos == "top_right":
                video_filters.append("delogo=x=W-260:y=20:w=240:h=140")
            elif pos == "top_left":
                video_filters.append("delogo=x=20:y=20:w=240:h=140")
            elif pos == "bottom_left":
                video_filters.append("delogo=x=20:y=H-160:w=240:h=140")
            else: # bottom_right default
                video_filters.append("delogo=x=W-260:y=H-160:w=240:h=140")

        # 4. 3D Perspective Tilt (Subtle 0.8 degree)
        if params.tilt_3d:
            video_filters.append("perspective=x0=0:y0=0:x1=W:y1=0.008*H:x2=0:y2=H:x3=W:y3=0.992*H:interpolation=cubic")

        # 5. High-Fidelity Color Grading & Vibrance
        if params.color_grade:
            video_filters.append("eq=contrast=1.04:brightness=0.005:saturation=1.08:gamma=1.02")
            video_filters.append("hue=h=1.5")

        # 6. Procedural Dynamic Film Grain (Subtle micro-texture)
        if params.film_grain > 0.1:
            grain_int = max(1, int(params.film_grain))
            video_filters.append(f"noise=c1s={grain_int}:c1f=t+u:c2s={max(0, grain_int-1)}:c2f=t+u")

        # 7. Dynamic Non-Linear Time Warping (Breaks Temporal Frame Hash)
        if params.dynamic_time_warp:
            base_factor = round(1.0 / params.speed_factor, 4)
            # Smooth sine wave time warp (using frame index N)
            video_filters.append(f"setpts=({base_factor}+0.02*sin(N/30))*PTS")
        elif abs(params.speed_factor - 1.0) > 0.001:
            pts_factor = round(1.0 / params.speed_factor, 4)
            video_filters.append(f"setpts={pts_factor}*PTS")

        # Guarantee even width and height for YUV420p encoder compatibility
        video_filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")

        # 8. Shorts / Reels Vertical 9:16 Layout Mode
        if params.shorts_vertical_916:
            filter_chain = ",".join(video_filters)
            complex_filter = (
                f"[0:v]{filter_chain}[v_processed];"
                f"[v_processed]split[main][bg];"
                f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg_blur];"
                f"[main]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
                f"[bg_blur][fg]overlay=(W-w)/2:(H-h)/2,scale=1080:1920[v_final]"
            )
        else:
            filter_chain = ",".join(video_filters)
            complex_filter = f"[0:v]{filter_chain}[v_final]"

        # Determine High-Quality Video Encoder Parameters (Preserve 100% Quality)
        if use_gpu:
            encoder_args = [
                "-c:v", "h264_nvenc",
                "-preset", "p6",
                "-cq", "17",
                "-b:v", "14M",
                "-maxrate", "20M",
                "-bufsize", "30M",
                "-spatial-aq", "1",
                "-temporal-aq", "1"
            ]
        else:
            encoder_args = [
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "17"
            ]

        # Check if processed audio exists and is valid
        has_valid_audio = processed_audio.exists() and processed_audio.stat().st_size > 500

        cmd = ["ffmpeg", "-y", "-i", str(input_video)]
        
        if has_valid_audio:
            cmd.extend(["-i", str(processed_audio)])
            cmd.extend(["-filter_complex", complex_filter])
            cmd.extend(["-map", "[v_final]", "-map", "1:a"])
        else:
            cmd.extend(["-filter_complex", complex_filter])
            cmd.extend(["-map", "[v_final]"])

        cmd.extend([
            *encoder_args,
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-pix_fmt", "yuv420p",
            "-g", "30",
            "-movflags", "+faststart",
        ])

        # Metadata Sanitization & Synthetic Apple iPhone 15 Pro EXIF Injection
        if params.strip_metadata:
            cmd.extend(["-map_metadata", "-1"])

        if params.camera_exif_injection:
            cmd.extend([
                "-metadata:g", "make=Apple",
                "-metadata:g", "model=iPhone 15 Pro Max",
                "-metadata:g", "software=iOS 17.5.1",
                "-metadata", "handler_name=Core Media Video",
                "-metadata", "encoder=Apple H.264 High"
            ])

        cmd.append(str(output_video))

        # Execute and parse real-time progress
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
        effective_duration = duration / params.speed_factor if duration > 0 else 1.0
        error_lines: List[str] = []

        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            line_str = line.decode(errors="ignore")
            error_lines.append(line_str)
            if len(error_lines) > 20:
                error_lines.pop(0)

            match = time_pattern.search(line_str)
            if match and effective_duration > 0:
                h, m, s = map(float, match.groups())
                current_time = h * 3600 + m * 60 + s
                progress = min(99, int((current_time / effective_duration) * 50) + 50)
                if progress_callback:
                    progress_callback(f"Rendering Master Quality Video ({progress}%)...", progress)

        await proc.wait()

        if proc.returncode != 0:
            err_summary = "".join(error_lines[-5:]).strip()
            raise RuntimeError(f"FFmpeg error: {err_summary}")

        if progress_callback:
            progress_callback("Finalizing high-quality master & injecting iPhone EXIF...", 100)

        return output_video
