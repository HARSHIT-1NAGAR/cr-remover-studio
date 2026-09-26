"""
Audio assets generator and manager for CR Remover Studio.
Generates procedural sound effects (whoosh, bass_drop, ding) and high-quality BGM tracks
so the studio works out-of-the-box with zero external network downloads.
"""

from pathlib import Path
import os
import wave
import numpy as np
from app.config import STORAGE_DIR

ASSETS_DIR = STORAGE_DIR / "assets"
SFX_DIR = ASSETS_DIR / "sfx"
BGM_DIR = ASSETS_DIR / "bgm"

for d in (ASSETS_DIR, SFX_DIR, BGM_DIR):
    d.mkdir(parents=True, exist_ok=True)


def init_default_audio_assets():
    """Generates default SFX and BGM files if they do not already exist."""
    _generate_sfx_whoosh()
    _generate_sfx_bass_drop()
    _generate_sfx_ding()
    _generate_sfx_glitch()
    _generate_bgm_lofi()
    _generate_bgm_phonk()
    _generate_bgm_tension()
    _generate_bgm_epic()
    _generate_bgm_upbeat()


def _write_wav(file_path: Path, audio_data: np.ndarray, sample_rate: int = 44100):
    """Writes a 16-bit PCM WAV file."""
    audio_data = np.clip(audio_data, -1.0, 1.0)
    int_audio = (audio_data * 32767).astype(np.int16)
    with wave.open(str(file_path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(int_audio.tobytes())


def _generate_sfx_whoosh():
    p = SFX_DIR / "whoosh.wav"
    if p.exists():
        return
    sr = 44100
    dur = 0.55
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # White noise with bandpass sweep
    noise = np.random.uniform(-1, 1, len(t))
    # Volume envelope (bell curve)
    env = np.sin(np.pi * t / dur) ** 2
    # Modulated pitch sweep
    freq = np.linspace(300, 1800, len(t))
    sweep = np.sin(2 * np.pi * freq * t)
    audio = (0.7 * noise + 0.3 * sweep) * env * 0.7
    _write_wav(p, audio, sr)


def _generate_sfx_bass_drop():
    p = SFX_DIR / "bass_drop.wav"
    if p.exists():
        return
    sr = 44100
    dur = 1.2
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Exponential pitch drop 130Hz -> 35Hz
    freq = 130.0 * np.exp(-2.2 * t / dur)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    audio = np.sin(phase) * (np.maximum(0, 1.0 - t / dur) ** 1.5) * 0.8
    _write_wav(p, audio, sr)


def _generate_sfx_ding():
    p = SFX_DIR / "ding.wav"
    if p.exists():
        return
    sr = 44100
    dur = 0.8
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Harmonic chime
    audio = (0.6 * np.sin(2 * np.pi * 1250 * t) + 0.4 * np.sin(2 * np.pi * 2500 * t)) * (np.maximum(0, 1.0 - t / dur) ** 3) * 0.6
    _write_wav(p, audio, sr)


def _generate_sfx_glitch():
    p = SFX_DIR / "glitch.wav"
    if p.exists():
        return
    sr = 44100
    dur = 0.4
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t))
    square = np.sign(np.sin(2 * np.pi * 400 * t))
    env = np.random.choice([0.0, 1.0], size=len(t), p=[0.2, 0.8]) * (np.maximum(0, 1.0 - t / dur))
    audio = (0.5 * noise + 0.5 * square) * env * 0.5
    _write_wav(p, audio, sr)


def _generate_bgm_lofi():
    p = BGM_DIR / "lofi_chill.wav"
    if p.exists():
        return
    sr = 44100
    dur = 16.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    chords = [
        [130.81, 164.81, 196.00, 246.94], # Cmaj7
        [110.00, 130.81, 164.81, 196.00], # Am7
        [87.31, 130.81, 174.61, 220.00],  # Fmaj7
        [98.00, 123.47, 146.83, 174.61]   # G7
    ]
    audio = np.zeros_like(t)
    for i, chord in enumerate(chords):
        start = i * (dur / 4)
        end = (i + 1) * (dur / 4)
        mask = (t >= start) & (t < end)
        local_t = t[mask] - start
        env = np.sin(np.pi * local_t / (dur / 4)) ** 0.5
        c_wave = np.zeros_like(local_t)
        for freq in chord:
            c_wave += 0.2 * np.sin(2 * np.pi * freq * local_t) + 0.1 * np.sin(2 * np.pi * (freq * 1.002) * local_t)
        audio[mask] += c_wave * env
    # Soft vinyl texture
    crackle = np.random.normal(0, 0.02, len(t))
    audio = (audio + crackle) * 0.7
    _write_wav(p, audio, sr)


def _generate_bgm_phonk():
    p = BGM_DIR / "phonk_drive.wav"
    if p.exists():
        return
    sr = 44100
    dur = 16.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Cowbell melody notes (E, G, A, B)
    notes = [164.81, 196.00, 220.00, 246.94, 220.00, 196.00, 164.81, 146.83]
    audio = np.zeros_like(t)
    step = dur / 16.0
    for idx in range(16):
        n_freq = notes[idx % len(notes)]
        start = idx * step
        end = (idx + 1) * step
        mask = (t >= start) & (t < end)
        lt = t[mask] - start
        env = np.exp(-6.0 * lt / step)
        wave_c = 0.3 * np.sin(2 * np.pi * n_freq * lt) + 0.2 * np.sin(2 * np.pi * n_freq * 2 * lt)
        # 808 sub bass on even beats
        if idx % 2 == 0:
            wave_c += 0.4 * np.sin(2 * np.pi * 55.0 * lt)
        audio[mask] += wave_c * env
    _write_wav(p, audio * 0.75, sr)


def _generate_bgm_tension():
    p = BGM_DIR / "deep_tension.wav"
    if p.exists():
        return
    sr = 44100
    dur = 16.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Dark drone 45Hz + 67Hz with pulsing amplitude LFO
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
    drone = (0.5 * np.sin(2 * np.pi * 45 * t) + 0.3 * np.sin(2 * np.pi * 67.5 * t)) * lfo
    hiss = np.random.normal(0, 0.015, len(t))
    audio = (drone + hiss) * 0.8
    _write_wav(p, audio, sr)


def _generate_bgm_epic():
    p = BGM_DIR / "epic_discovery.wav"
    if p.exists():
        return
    sr = 44100
    dur = 16.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Ambient string pad chord
    pad = (
        0.25 * np.sin(2 * np.pi * 220 * t) +
        0.25 * np.sin(2 * np.pi * 277.18 * t) +
        0.25 * np.sin(2 * np.pi * 329.63 * t) +
        0.25 * np.sin(2 * np.pi * 440 * t)
    )
    env = np.sin(np.pi * t / dur) ** 0.3
    _write_wav(p, pad * env * 0.7, sr)


def _generate_bgm_upbeat():
    p = BGM_DIR / "upbeat_viral.wav"
    if p.exists():
        return
    sr = 44100
    dur = 16.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Bright arpeggiator
    arp_notes = [261.63, 329.63, 392.00, 523.25]
    audio = np.zeros_like(t)
    step = 0.25
    steps_total = int(dur / step)
    for idx in range(steps_total):
        freq = arp_notes[idx % 4]
        start = idx * step
        end = (idx + 1) * step
        mask = (t >= start) & (t < end)
        lt = t[mask] - start
        env = np.exp(-8.0 * lt / step)
        audio[mask] += 0.4 * np.sin(2 * np.pi * freq * lt) * env
    _write_wav(p, audio * 0.65, sr)


# Auto initialize on module import
init_default_audio_assets()
