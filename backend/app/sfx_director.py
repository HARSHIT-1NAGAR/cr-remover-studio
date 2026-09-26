"""
Intelligent Auto-SFX & Kinetic Sound Stager for CR Remover Studio.
Analyzes narration transcripts and word-level boundary timings to automatically stage
whoosh scene transitions, sub-bass drops on opening hooks, chime dings on power words,
and glitch audio FX.
"""

from pathlib import Path
import re
from typing import List, Dict, Any, Tuple
from app.config import STORAGE_DIR, TEMP_DIR
from app.audio_assets import SFX_DIR
from app.editor_schemas import WordTiming, SceneBlock

POWER_WORDS = {
    "shocking", "secret", "never", "million", "billion", "danger", "warning",
    "illegal", "truth", "crazy", "insane", "discovered", "mistake", "hidden",
    "exposed", "scam", "banned", "dark", "terrifying", "huge", "worst", "unbelievable"
}


class SFXDirector:
    """Calculates exact timestamp triggers for sound effects synchronized with speech and video cuts."""

    @classmethod
    def compile_sfx_timeline(
        cls,
        word_timings: List[WordTiming],
        scenes: List[SceneBlock],
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Generates a timeline of sound effect events with millisecond delays.
        """
        events: List[Dict[str, Any]] = []

        # 1. Opening Hook Sub-Bass Drop at t = 0.05s
        bass_drop_file = SFX_DIR / "bass_drop.wav"
        if bass_drop_file.exists():
            events.append({
                "type": "bass_drop",
                "timestamp": 0.05,
                "file_path": str(bass_drop_file),
                "volume": 0.35
            })

        # 2. Whoosh on Scene Transitions
        current_time = 0.0
        whoosh_file = SFX_DIR / "whoosh.wav"
        if whoosh_file.exists():
            for idx, sc in enumerate(scenes):
                if idx > 0 and current_time < (total_duration - 1.0):
                    events.append({
                        "type": "whoosh",
                        "timestamp": max(0.1, current_time - 0.15),
                        "file_path": str(whoosh_file),
                        "volume": 0.28
                    })
                current_time += sc.duration_seconds

        # 3. Power Word Emphasis SFX (Ding / Glitch)
        ding_file = SFX_DIR / "ding.wav"
        glitch_file = SFX_DIR / "glitch.wav"
        last_sfx_time = 0.5

        for wt in word_timings:
            clean_w = re.sub(r'[^a-zA-Z]', '', wt.word).lower()
            if clean_w in POWER_WORDS and (wt.start - last_sfx_time) > 2.5:
                sfx_choice = ding_file if ding_file.exists() else glitch_file
                if sfx_choice and sfx_choice.exists():
                    events.append({
                        "type": "power_word",
                        "word": clean_w,
                        "timestamp": max(0.0, wt.start),
                        "file_path": str(sfx_choice),
                        "volume": 0.25
                    })
                    last_sfx_time = wt.start

        # Sort chronologically
        events.sort(key=lambda x: x["timestamp"])
        return events

    @classmethod
    def build_sfx_filtergraph(
        cls,
        events: List[Dict[str, Any]],
        start_input_idx: int,
        total_duration: float
    ) -> Tuple[List[str], str, List[str]]:
        """
        Builds FFmpeg filter complex expressions to delay and mix all SFX triggers.
        Returns (input_args, delayed_audio_label, filter_lines).
        """
        input_args: List[str] = []
        filter_lines: List[str] = []
        delayed_labels: List[str] = []

        if not events:
            return ([], "", [])

        for i, ev in enumerate(events):
            input_idx = start_input_idx + i
            input_args.extend(["-i", ev["file_path"]])
            
            delay_ms = int(ev["timestamp"] * 1000)
            vol = ev.get("volume", 0.3)
            label = f"sfx_{i}"
            filter_lines.append(
                f"[{input_idx}:a]volume={vol},adelay={delay_ms}|{delay_ms}[{label}]"
            )
            delayed_labels.append(f"[{label}]")

        # Mix all SFX streams together into a single master SFX track
        sfx_inputs_str = "".join(delayed_labels)
        filter_lines.append(
            f"{sfx_inputs_str}amix=inputs={len(events)}:duration=first:dropout_transition=0[a_sfx_master]"
        )

        return (input_args, "[a_sfx_master]", filter_lines)
