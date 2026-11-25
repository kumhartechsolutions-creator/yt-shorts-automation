"""Render 1080x1920 animated Arduino/ESP32 YouTube Shorts with Edge-TTS voiceover & SFX."""

from __future__ import annotations

import asyncio
import math
import subprocess
import wave
from pathlib import Path
from typing import Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from projects import ShortProject

WIDTH, HEIGHT = 1080, 1920
FPS = 30
VOICE = "en-US-ChristopherNeural"

BG_TOP = (8, 12, 22)
CYAN = (0, 230, 255)
EMERALD = (40, 235, 145)
RED = (255, 65, 85)
AMBER = (255, 195, 45)
WHITE = (245, 248, 255)
MUTED = (150, 165, 190)
CARD_BG = (16, 22, 36)


def _load_font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["consolab.ttf", "consola.ttf", "DejaVuSansMono.ttf"]
        if mono
        else ["arialbd.ttf", "seguisb.ttf", "DejaVuSans-Bold.ttf"]
    )
    for name in candidates:
        for base in [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype")]:
            p = base / name
            if p.exists():
                return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


FONT_HEAD = _load_font(68)
FONT_SUB = _load_font(36)
FONT_CAP = _load_font(52)
FONT_MONO = _load_font(28, mono=True)
FONT_SMALL = _load_font(28)


async def _synthesize_tts(text: str, out_mp3: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE, rate="+8%")
    await communicate.save(str(out_mp3))


def _get_duration_seconds(ffmpeg_exe: str, media_path: Path) -> float:
    proc = subprocess.run(
        [ffmpeg_exe, "-i", str(media_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in proc.stderr.splitlines():
        if "Duration:" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 15.0


def _write_sfx_wav(out_wav: Path, duration: float, mode: str) -> None:
    sr = 44100
    n = int(sr * duration)
    buf = np.zeros(n, dtype=np.float32)

    # Subtle periodic tech pulse/sonar ping every 1.2s + alert chirps near mid-video
    t_all = np.arange(n, dtype=np.float32) / sr
    for beat in np.arange(0.3, duration - 1.0, 1.2):
        idx = int(beat * sr)
        length = min(int(0.18 * sr), n - idx)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / sr
        freq = 880.0 if mode == "radar" else (523.25 if mode == "waveform" else 1600.0)
        env = np.exp(-t * 18.0)
        buf[idx : idx + length] += 0.14 * np.sin(2 * np.pi * freq * t) * env

    # Alert burst between 45% and 65% of clip
    for beat in np.arange(duration * 0.45, duration * 0.65, 0.22):
        idx = int(beat * sr)
        length = min(int(0.09 * sr), n - idx)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / sr
        buf[idx : idx + length] += 0.18 * np.sin(2 * np.pi * 1950.0 * t) * np.exp(-t * 14.0)

    pcm = np.clip(buf * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _draw_grid_bg(draw: ImageDraw.ImageDraw) -> None:
    for x in range(0, WIDTH, 90):
        draw.line([(x, 0), (x, HEIGHT)], fill=(18, 26, 44), width=1)
    for y in range(0, HEIGHT, 90):
        draw.line([(0, y), (WIDTH, y)], fill=(18, 26, 44), width=1)


def _draw_radar_sim(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, y1 - 95
    radius = 340

    # Sweep 15..165 deg back and forth
    phase = (math.sin(t * 2.1 - math.pi / 2) + 1.0) / 2.0
    angle = 15 + phase * 150
    rad = math.radians(angle)

    # Target active in middle portion of video
    target_angle = 78.0
    target_cm = 12 if (dur * 0.35 <= t <= dur * 0.72) else 34
    alert = target_cm <= 25

    for r in (radius, radius * 2 // 3, radius // 3):
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=(25, 95, 85), width=3)
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=(35, 115, 100), width=3)

    # Sweep beam
    sx = cx + int(math.cos(rad) * radius)
    sy = cy - int(math.sin(rad) * radius)
    draw.line([(cx, cy), (sx, sy)], fill=EMERALD, width=6)

    # Target blip
    tr = int((target_cm / 40.0) * radius)
    trad = math.radians(target_angle)
    tx = cx + int(math.cos(trad) * tr)
    ty = cy - int(math.sin(trad) * tr)
    blip_color = RED if alert else AMBER
    draw.ellipse([tx - 16, ty - 16, tx + 16, ty + 16], fill=blip_color, outline=WHITE, width=3)

    status = f"ANG: {int(angle)}°   DIST: {target_cm} CM {'ALERT!' if alert else 'OK'}"
    draw.text((x0 + 42, y0 + 36), status, font=FONT_SUB, fill=RED if alert else CYAN)


def _draw_waveform_sim(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    idx = int((t * 1.8)) % len(notes)
    dist = 8 + idx * 4
    draw.text((x0 + 42, y0 + 36), f"HAND: {dist} CM   NOTE: {notes[idx]}", font=FONT_SUB, fill=CYAN)

    bar_w = 68
    gap = 26
    start_x = x0 + 65
    base_y = y1 - 80
    for i in range(8):
        bx = start_x + i * (bar_w + gap)
        h = 340 if i == idx else int(80 + 40 * math.sin(t * 4 + i))
        color = EMERALD if i == idx else (35, 65, 95)
        draw.rounded_rectangle([bx, base_y - h, bx + bar_w, base_y], radius=12, fill=color)
        draw.text((bx + 12, base_y + 18), notes[i], font=FONT_SMALL, fill=WHITE if i == idx else MUTED)


def _draw_laser_sim(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    tripped = dur * 0.38 <= t <= dur * 0.72
    cy = (y0 + y1) // 2 + 20

    draw.rounded_rectangle([x0 + 50, cy - 45, x0 + 160, cy + 45], radius=12, fill=(45, 55, 75), outline=CYAN, width=3)
    draw.rounded_rectangle([x1 - 160, cy - 45, x1 - 50, cy + 45], radius=12, fill=(45, 55, 75), outline=AMBER, width=3)
    draw.text((x0 + 62, cy + 60), "LASER", font=FONT_SMALL, fill=MUTED)
    draw.text((x1 - 140, cy + 60), "LDR", font=FONT_SMALL, fill=MUTED)

    beam_end = (x0 + x1) // 2 if tripped else (x1 - 160)
    draw.line([(x0 + 160, cy), (beam_end, cy)], fill=RED, width=10)
    if tripped:
        draw.rounded_rectangle([(x0 + x1) // 2 - 22, cy - 110, (x0 + x1) // 2 + 22, cy + 110], radius=14, fill=AMBER)
    status = "BEAM BROKEN - ALARM ON!" if tripped else "LASER LOCKED - SECURE"
    draw.text((x0 + 42, y0 + 36), status, font=FONT_SUB, fill=RED if tripped else EMERALD)


SIM_RENDERERS = {
    "radar": _draw_radar_sim,
    "waveform": _draw_waveform_sim,
    "laser": _draw_laser_sim,
}


def _render_frame(project: ShortProject, frame_idx: int, total_frames: int) -> bytes:
    t = frame_idx / FPS
    dur = total_frames / FPS
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
    draw = ImageDraw.Draw(img)
    _draw_grid_bg(draw)

    # Top hook pills & headline
    draw.rounded_rectangle([70, 110, 420, 175], radius=24, fill=(18, 45, 70), outline=CYAN, width=3)
    draw.text((98, 124), project.hook_badge, font=FONT_SUB, fill=CYAN)

    draw.rounded_rectangle([760, 110, 1010, 175], radius=24, fill=(20, 65, 45), outline=EMERALD, width=3)
    draw.text((795, 124), project.cost_label, font=FONT_SUB, fill=EMERALD)

    draw.text((70, 215), project.hook_headline, font=FONT_HEAD, fill=WHITE)

    # Central simulation card
    sim_box = (70, 350, 1010, 960)
    draw.rounded_rectangle(sim_box, radius=32, fill=CARD_BG, outline=(45, 70, 105), width=4)
    SIM_RENDERERS.get(project.sim_mode, _draw_radar_sim)(draw, sim_box, t, dur)

    # Code card
    code_box = (70, 1005, 1010, 1310)
    draw.rounded_rectangle(code_box, radius=24, fill=(12, 16, 28), outline=(45, 60, 90), width=3)
    draw.text((100, 1025), f"FILE: {project.code_filename}", font=FONT_SMALL, fill=AMBER)
    for i, line in enumerate(project.code_snippet.splitlines()[:4]):
        draw.text((100, 1080 + i * 48), line, font=FONT_MONO, fill=EMERALD)

    # Phrase-synced caption in safe lower-third
    captions = project.captions or [project.hook_headline]
    cap_idx = min(int((frame_idx / total_frames) * len(captions)), len(captions) - 1)
    cap = captions[cap_idx]
    draw.rounded_rectangle([70, 1380, 1010, 1510], radius=26, fill=(18, 25, 42), outline=CYAN, width=4)
    draw.text((105, 1418), cap, font=FONT_CAP, fill=WHITE)

    # Bottom channel branding
    draw.text((70, 1575), "Zahid Bashir Young Innovator  |  Subscribe!", font=FONT_SUB, fill=MUTED)
    return img.tobytes()


def render_short_video(project: ShortProject, out_dir: Path) -> Path:
    """Generate voiceover, SFX, and animated 1080x1920 MP4 for a project."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    voice_mp3 = out_dir / f"{project.id}_voice.mp3"
    sfx_wav = out_dir / f"{project.id}_sfx.wav"
    final_mp4 = out_dir / f"{project.id}.mp4"

    asyncio.run(_synthesize_tts(project.voiceover, voice_mp3))
    duration = max(_get_duration_seconds(ffmpeg_exe, voice_mp3) + 0.6, 12.0)
    _write_sfx_wav(sfx_wav, duration, project.sim_mode)

    total_frames = int(duration * FPS)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-i", str(voice_mp3),
        "-i", str(sfx_wav),
        "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=0.35[s];[v][s]amix=inputs=2:duration=longest[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i in range(total_frames):
            proc.stdin.write(_render_frame(project, i, total_frames))
        proc.stdin.close()
    finally:
        ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {ret}")

    return final_mp4
