"""
Audio Processing & AI Stem Separation Engine for CR Remover Studio.
Handles voice isolation (Demucs), pitch shifting, tempo stretching, and masking ambience.
"""

from pathlib import Path
import os
import shutil
import subprocess
import asyncio
import math
from typing import Optional, Callable
from app.config import TEMP_DIR
from app.schemas import TransformParams


class AudioEngine:
    """Handles all audio transformations and AI stem separation."""

    @staticmethod
    def is_demucs_installed() -> bool:
        """Checks if Demucs CLI is available on the system."""
        return shutil.which("demucs") is not None

    @classmethod
    async def process_audio(
        cls,
        input_audio_path: Path,
        output_audio_path: Path,
        params: TransformParams,
        duration_seconds: float,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Path:
        """
        Executes the full audio transformation pipeline:
        1. (Optional) AI Stem Separation via Demucs to isolate vocals and discard copyrighted BGM.
        2. Pitch shift & tempo time-stretching.
        3. Notch EQ filtering to disrupt harmonic peak matching.
        4. Subtle pink noise ambience injection.
        """
        # Handle missing or silent audio source
        if not input_audio_path.exists() or input_audio_path.stat().st_size < 100:
            silent_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={max(1.0, duration_seconds)}",
                "-c:a", "aac", "-b:a", "192k",
                str(output_audio_path)
            ]
            proc = await asyncio.create_subprocess_exec(
                *silent_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return output_audio_path

        working_audio = input_audio_path

        # Step 1: AI Vocal Isolation if requested
        if params.isolate_vocals:
            if progress_callback:
                progress_callback("Running AI Stem Separation (Demucs)...", 20)
            
            vocals_path = await cls._isolate_vocals(input_audio_path, progress_callback)
            if vocals_path and vocals_path.exists():
                working_audio = vocals_path

        # Step 2: Pitch, Tempo & EQ Filter Chain
        if progress_callback:
            progress_callback("Applying Audio Pitch & Acoustic Transformations...", 45)

        filter_parts = []
        
        # Pitch ratio calculation: 2^(cents / 1200)
        cents = params.pitch_cents
        speed = params.speed_factor
        pitch_ratio = math.pow(2.0, cents / 1200.0)

        # Build pitch & tempo filter (resample at 48kHz studio master)
        if abs(cents) > 0 or abs(speed - 1.0) > 0.001:
            target_sample_rate = int(48000 * pitch_ratio)
            tempo_correction = speed / pitch_ratio
            tempo_correction = max(0.5, min(2.0, tempo_correction))
            filter_parts.append(f"asetrate={target_sample_rate},aresample=48000,atempo={tempo_correction:.4f}")
        else:
            filter_parts.append("aresample=48000")

        # 4-Band Harmonic Constellation Notch Sweep (Disrupts Shazam / Content ID matching)
        if params.harmonic_notch_eq:
            filter_parts.append("equalizer=f=420:width_type=q:w=3:g=-3.5")
            filter_parts.append("equalizer=f=1250:width_type=q:w=3:g=-3.5")
            filter_parts.append("equalizer=f=3450:width_type=q:w=3:g=-3.5")
            filter_parts.append("equalizer=f=6200:width_type=q:w=3:g=-3.5")
        else:
            filter_parts.append("equalizer=f=1200:width_type=q:w=2:g=-2")
            filter_parts.append("equalizer=f=3400:width_type=q:w=2:g=-2")

        filter_parts.append("highpass=f=70")

        audio_filter_str = ",".join(filter_parts)

        # Ambience noise injection (Inaudible acoustic masking floor)
        if params.add_ambience and params.ambience_volume > 0.001:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(working_audio),
                "-f", "lavfi", "-i", f"anoisesrc=d={duration_seconds + 5}:c=pink:r=48000:a={params.ambience_volume:.4f}",
                "-filter_complex", f"[0:a]{audio_filter_str}[filtered];[filtered][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
                "-map", "[out]",
                "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                str(output_audio_path)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(working_audio),
                "-af", audio_filter_str,
                "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                str(output_audio_path)
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="ignore") if stderr else "Unknown audio error"
            raise RuntimeError(f"FFmpeg audio processing failed: {err_msg}")

        return output_audio_path

    @classmethod
    async def _isolate_vocals(
        cls,
        audio_path: Path,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Optional[Path]:
        """Runs Demucs separation to extract the isolated vocals stem."""
        if not cls.is_demucs_installed():
            # If demucs CLI not found, log warning and skip
            return None

        job_temp = TEMP_DIR / f"demucs_{audio_path.stem}"
        job_temp.mkdir(parents=True, exist_ok=True)

        cmd = [
            "demucs",
            "-n", "htdemucs",
            "--two-stems=vocals",
            "-o", str(job_temp),
            str(audio_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        # Demucs outputs to: {job_temp}/htdemucs/{audio_stem}/vocals.wav
        vocals_file = job_temp / "htdemucs" / audio_path.stem / "vocals.wav"
        if vocals_file.exists():
            return vocals_file

        return None
