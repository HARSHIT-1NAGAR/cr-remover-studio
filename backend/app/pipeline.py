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
        # 0. Probe source video resolution & aspect ratio
        meta = await VideoProbe.probe(input_video)
        src_w = int(meta.get("width", 1920)) or 1920
        src_h = int(meta.get("height", 1080)) or 1080
        is_source_vertical = src_h > src_w

        # Calculate target dimensions
        target_res = getattr(params, "render_resolution", "original") or "original"
        
        if target_res == "4k":
            if params.shorts_vertical_916 or is_source_vertical:
                target_w, target_h = 2160, 3840
            else:
                target_w, target_h = 3840, 2160
        elif target_res == "2k":
            if params.shorts_vertical_916 or is_source_vertical:
                target_w, target_h = 1440, 2560
            else:
                target_w, target_h = 2560, 1440
        elif target_res == "1080p":
            if params.shorts_vertical_916 or is_source_vertical:
                target_w, target_h = 1080, 1920
            else:
                target_w, target_h = 1920, 1080
        else:
            # "original" / source match
            if params.shorts_vertical_916:
                if is_source_vertical:
                    target_w, target_h = (src_w // 2) * 2, (src_h // 2) * 2
                else:
                    target_h = max(src_h, 1920)
                    target_w = int(target_h * 9 / 16 / 2) * 2
            else:
                target_w, target_h = (src_w // 2) * 2, (src_h // 2) * 2

        video_filters = []

        # 1. Horizontal Mirror Flip (Only if enabled, Default is False)
        if params.mirror_flip:
            video_filters.append("hflip")

        # 2. Dynamic Ken Burns Pan & Zoom (Smooth imperceptible pan with high-quality lanczos)
        zoom = params.ken_burns_zoom
        if zoom > 1.001:
            zoom_str = (
                f"scale=trunc(iw*{zoom:.3f}/2)*2:trunc(ih*{zoom:.3f}/2)*2:flags=lanczos,"
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
            video_filters.append("eq=contrast=1.03:brightness=0.003:saturation=1.06:gamma=1.01")
            video_filters.append("hue=h=1.0")

        # 6. Optional Clarity & Sharpness Boost
        if getattr(params, "clarity_boost", False):
            video_filters.append("unsharp=5:5:0.6:5:5:0.0")

        # 7. Procedural Film Grain (Default 0.0 = Crystal Clean / Zero Grain)
        if params.film_grain > 0.05:
            grain_int = max(1, min(10, int(round(params.film_grain))))
            # Subtle luminance-only micro-dither, no ugly chroma artifacts
            video_filters.append(f"noise=c0s={grain_int}:c0f=t:c1s=0:c2s=0")

        # 8. Dynamic Non-Linear Time Warping (Breaks Temporal Frame Hash)
        if params.dynamic_time_warp:
            base_factor = round(1.0 / params.speed_factor, 4)
            video_filters.append(f"setpts=({base_factor}+0.02*sin(N/30))*PTS")
        elif abs(params.speed_factor - 1.0) > 0.001:
            pts_factor = round(1.0 / params.speed_factor, 4)
            video_filters.append(f"setpts={pts_factor}*PTS")

        # 9. Shorts / Reels Vertical 9:16 Layout Mode vs Direct Master Output
        if params.shorts_vertical_916:
            filter_chain = ",".join(video_filters) if video_filters else "null"
            complex_filter = (
                f"[0:v]{filter_chain}[v_processed];"
                f"[v_processed]split[main][bg];"
                f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase:flags=lanczos,crop={target_w}:{target_h},boxblur=25:5[bg_blur];"
                f"[main]scale={target_w}:-2:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
                f"[bg_blur][fg]overlay=(W-w)/2:(H-h)/2,scale={target_w}:{target_h}:flags=lanczos[v_final]"
            )
        else:
            # Guarantee full master resolution with high-fidelity Lanczos resampling
            video_filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1")
            video_filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
            filter_chain = ",".join(video_filters)
            complex_filter = f"[0:v]{filter_chain}[v_final]"

        # Determine High-Quality Video Encoder Parameters based on target resolution
        is_4k = target_w >= 3840 or target_h >= 2160 or target_res == "4k"
        is_2k = target_w >= 2560 or target_h >= 1440 or target_res == "2k"

        if use_gpu:
            if is_4k:
                bitrate_args = ["-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "16", "-b:v", "40M", "-maxrate", "55M", "-bufsize", "75M"]
            elif is_2k:
                bitrate_args = ["-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "17", "-b:v", "26M", "-maxrate", "36M", "-bufsize", "48M"]
            else:
                bitrate_args = ["-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "18", "-b:v", "18M", "-maxrate", "28M", "-bufsize", "36M"]
            
            encoder_args = [
                "-c:v", "h264_nvenc",
                *bitrate_args,
                "-spatial-aq", "1",
                "-temporal-aq", "1"
            ]
        else:
            crf_val = "18" if is_4k else "19"
            encoder_args = [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", crf_val,
                "-threads", "0"
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
                    res_label = "4K UHD Master" if is_4k else ("2K QHD" if is_2k else "Master Studio")
                    progress_callback(f"Rendering {res_label} Video ({progress}%)...", progress)

        await proc.wait()

        if proc.returncode != 0:
            err_summary = "".join(error_lines[-5:]).strip()
            raise RuntimeError(f"FFmpeg error: {err_summary}")

        if progress_callback:
            progress_callback("Finalizing pristine master & injecting iPhone EXIF...", 100)

        return output_video
