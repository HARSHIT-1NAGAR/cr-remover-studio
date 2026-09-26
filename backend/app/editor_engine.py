"""
Master Rendering Engine for AI Shorts & Multi-Scene Video Editing Studio.
Compiles multi-scene video stitches, dynamic 9:16 camera zooms, word-synchronized ASS subtitles,
sidechain audio ducking, sound FX triggers, and Apple iPhone EXIF injection into a single-pass GPU FFmpeg pipeline.
"""

from pathlib import Path
import os
import re
import json
import uuid
import asyncio
import subprocess
from typing import List, Dict, Any, Optional, Callable
from app.config import HAS_NVENC, TEMP_DIR, PROCESSED_DIR, STORAGE_DIR
from app.audio_assets import SFX_DIR, BGM_DIR
from app.editor_schemas import AIShortsRenderRequest, SceneBlock
from app.tts_engine import TTSEngine


class AIShortsRenderer:
    """Renders composite 9:16 Shorts with multi-scene video, subtitles, and ducked BGM."""

    @classmethod
    async def render_shorts(
        cls,
        request: AIShortsRenderRequest,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Path:
        """
        Main entry point to render an AI Short.
        Attempts GPU NVENC first; seamlessly falls back to CPU if necessary.
        """
        try:
            return await cls._execute_render(request, use_gpu=(request.use_gpu and HAS_NVENC), progress_callback=progress_callback)
        except Exception as e:
            if request.use_gpu and HAS_NVENC:
                if progress_callback:
                    progress_callback("Retrying with High-Quality CPU encoder fallback...", 45)
                return await cls._execute_render(request, use_gpu=False, progress_callback=progress_callback)
            raise e

    @classmethod
    async def _execute_render(
        cls,
        request: AIShortsRenderRequest,
        use_gpu: bool,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Path:
        job_id = request.project_id or str(uuid.uuid4())[:8]
        output_path = PROCESSED_DIR / f"ai_short_{job_id}.mp4"

        if progress_callback:
            progress_callback("Preparing visual scenes & audio tracks...", 10)

        # 1. Prepare ASS Subtitle File
        ass_path = TEMP_DIR / f"{job_id}_subtitles.ass"
        has_subtitles = False
        if request.subtitle_style != "none" and request.word_timings:
            try:
                TTSEngine.generate_ass_subtitles(
                    [w.model_dump() for w in request.word_timings],
                    ass_path,
                    style_preset=request.subtitle_style,
                    font_family=request.subtitle_font_family,
                    font_size=request.subtitle_font_size,
                    text_case=request.subtitle_text_case,
                    active_color_hex=request.subtitle_active_color,
                    inactive_color_hex=request.subtitle_inactive_color,
                    outline_color_hex=request.subtitle_outline_color,
                    outline_width=request.subtitle_outline_width,
                    background_box=request.subtitle_background_box,
                    words_per_line=request.subtitle_words_per_line,
                    position_y=request.subtitle_position_y,
                    animation=request.subtitle_animation,
                    video_width=1080,
                    video_height=1920
                )
                has_subtitles = ass_path.exists() and ass_path.stat().st_size > 50
            except Exception as e:
                print(f"Subtitle generation warning: {e}")
                has_subtitles = False

        # 2. Check & Validate Video Inputs for each scene
        # If a scene lacks a video_source_path or file is missing, generate a dynamic animated gradient background
        scene_video_inputs: List[Path] = []
        for idx, sc in enumerate(request.scenes):
            src = Path(sc.video_source_path) if sc.video_source_path else None
            if src and src.exists():
                scene_video_inputs.append(src)
            else:
                # Generate synthetic motion background for this scene
                bg_clip = TEMP_DIR / f"{job_id}_scene_{idx}_bg.mp4"
                dur = max(2.0, sc.duration_seconds)
                hue_shift = (idx * 60) % 360
                cmd_bg = [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"mptestsrc=r=30:d={dur}",
                    "-vf", f"scale=1080:1920,boxblur=40:10,hue=h={hue_shift}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(dur),
                    str(bg_clip)
                ]
                proc = await asyncio.create_subprocess_exec(*cmd_bg, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()
                scene_video_inputs.append(bg_clip if bg_clip.exists() else Path("/dev/null"))

        # 3. Build Multi-Scene Video Filter Graph
        # Converts all scene clips to 9:16 (1080x1920), applies camera zoom FX, then concatenates them
        filter_complex = []
        input_args = []
        
        # Add scene video inputs
        for idx, v_path in enumerate(scene_video_inputs):
            input_args.extend(["-i", str(v_path)])

        # Voice input index
        voice_input_idx = len(scene_video_inputs)
        voice_path = Path(request.voice_audio_path)
        if not voice_path.exists():
            # Search in uploads or temp
            possible = list(STORAGE_DIR.glob(f"**/{voice_path.name}"))
            if possible:
                voice_path = possible[0]
        input_args.extend(["-i", str(voice_path)])

        # BGM input index
        bgm_input_idx = voice_input_idx + 1
        bgm_file = BGM_DIR / f"{request.bgm_track}.wav"
        has_bgm = (request.bgm_track != "none") and bgm_file.exists()
        if has_bgm:
            input_args.extend(["-i", str(bgm_file)])

        # Build video filter chain for each scene
        scene_v_labels = []
        total_duration = sum(sc.duration_seconds for sc in request.scenes)

        for idx, sc in enumerate(request.scenes):
            dur = max(1.5, sc.duration_seconds)
            cam_fx = sc.camera_effect
            label_out = f"v_sc_{idx}"

            # Camera zoom effects:
            # 9:16 vertical framing with blurred background + foreground center
            # Apply dynamic zoom to foreground
            if cam_fx == "punch_zoom":
                fg_zoom = "scale=1240:-2,crop=1080:1920"
            elif cam_fx == "slow_zoom_in":
                fg_zoom = f"scale=1080*1.15:-2,crop=1080:1920:'(in_w-out_w)/2 + (in_w-out_w)/2*(t/{dur})':'(in_h-out_h)/2'"
            elif cam_fx == "slow_zoom_out":
                fg_zoom = f"scale=1080*1.15:-2,crop=1080:1920:'(in_w-out_w)/2 + (in_w-out_w)/2*(1-t/{dur})':'(in_h-out_h)/2'"
            else:
                fg_zoom = "scale=1080:-2:force_original_aspect_ratio=decrease"

            sc_filter = (
                f"[{idx}:v]trim=duration={dur},setpts=PTS-STARTPTS,split[bg_{idx}][fg_{idx}];"
                f"[bg_{idx}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg_b_{idx}];"
                f"[fg_{idx}]{fg_zoom}[fg_z_{idx}];"
                f"[bg_b_{idx}][fg_z_{idx}]overlay=(W-w)/2:(H-h)/2,scale=1080:1920,setsar=1[{label_out}]"
            )
            filter_complex.append(sc_filter)
            scene_v_labels.append(f"[{label_out}]")

        # Concat all scene video streams
        n_scenes = len(request.scenes)
        concat_inputs = "".join(scene_v_labels)
        filter_complex.append(f"{concat_inputs}concat=n={n_scenes}:v=1:a=0[v_stitched]")

        # Progress bar overlay if enabled
        current_v = "v_stitched"
        if request.progress_bar:
            # Animated horizontal line expanding from left to right at the top
            bar_color = request.progress_bar_color.replace("#", "0x")
            filter_complex.append(
                f"[{current_v}]drawbox=x=0:y=0:w='(t/{total_duration})*1080':h=10:color={bar_color}:t=fill[v_with_bar]"
            )
            current_v = "v_with_bar"

        # Burn ASS subtitles if available
        if has_subtitles:
            # Escape path for FFmpeg filter
            escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")
            fonts_dir = STORAGE_DIR / "assets" / "fonts"
            escaped_fonts = str(fonts_dir).replace("\\", "/").replace(":", "\\:")
            filter_complex.append(f"[{current_v}]ass='{escaped_ass}':fontsdir='{escaped_fonts}'[v_with_sub]")
            current_v = "v_with_sub"

        # Anti-copyright subtle color grade & grain if enabled
        if request.anti_copyright_shield:
            filter_complex.append(
                f"[{current_v}]eq=contrast=1.05:brightness=0.01:saturation=1.08,noise=c1s=2:c1f=t+u[v_final]"
            )
        else:
            filter_complex.append(f"[{current_v}]null[v_final]")

        # 4. Build Audio Filter Graph (Voice + BGM Sidechain Ducking)
        if has_bgm:
            bgm_vol = request.bgm_volume
            # Loop BGM to cover total video duration and mix with voice
            # Split voice into two streams: one for sidechain trigger, one for main audio mix
            audio_filter = (
                f"[{bgm_input_idx}:a]aloop=loop=-1:size=2e+09,atrim=0:{total_duration},volume={bgm_vol}[a_bgm_raw];"
                f"[{voice_input_idx}:a]volume=1.0,asplit[a_voice_main][a_voice_sc];"
                f"[a_bgm_raw][a_voice_sc]sidechaincompress=threshold=0.1:ratio=8:attack=10:release=300[a_bgm_ducked];"
                f"[a_voice_main][a_bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2[a_final]"
            )
        else:
            audio_filter = f"[{voice_input_idx}:a]volume=1.0[a_final]"

        filter_complex.append(audio_filter)
        complex_filter_str = ";".join(filter_complex)

        # 5. Determine Encoder Parameters
        if use_gpu:
            encoder_args = [
                "-c:v", "h264_nvenc",
                "-preset", "p6",
                "-cq", "18",
                "-b:v", "12M",
                "-maxrate", "18M",
                "-bufsize", "25M",
                "-spatial-aq", "1"
            ]
        else:
            encoder_args = [
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18"
            ]

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", complex_filter_str,
            "-map", "[v_final]",
            "-map", "[a_final]",
            *encoder_args,
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-pix_fmt", "yuv420p",
            "-r", "60",
            "-movflags", "+faststart",
        ]

        # Metadata Sanitization & Authentic iPhone 15 Pro EXIF Injection
        if request.anti_copyright_shield:
            cmd.extend([
                "-map_metadata", "-1",
                "-metadata:g", "make=Apple",
                "-metadata:g", "model=iPhone 15 Pro Max",
                "-metadata:g", "software=iOS 17.5.1",
                "-metadata", "handler_name=Core Media Video"
            ])

        cmd.append(str(output_path))

        if progress_callback:
            progress_callback("Rendering 9:16 Master Short (GPU)...", 40)

        # Execute FFmpeg with progress parsing
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
        error_lines: List[str] = []

        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            line_str = line.decode(errors="ignore")
            error_lines.append(line_str)
            if len(error_lines) > 25:
                error_lines.pop(0)

            match = time_pattern.search(line_str)
            if match and total_duration > 0:
                h, m, s = map(float, match.groups())
                current_time = h * 3600 + m * 60 + s
                progress = min(98, int((current_time / total_duration) * 55) + 40)
                if progress_callback:
                    progress_callback(f"Rendering Master Short ({progress}%)...", progress)

        await proc.wait()

        if proc.returncode != 0:
            err_summary = "".join(error_lines[-6:]).strip()
            raise RuntimeError(f"FFmpeg render error: {err_summary}")

        if progress_callback:
            progress_callback("Shorts Rendering Complete!", 100)

        return output_path
