"""Render 1080x1920 photorealistic Arduino/ESP32 Shorts with live HUD, Edge-TTS & SFX."""

from __future__ import annotations

import asyncio
import math
import subprocess
import urllib.parse
import wave
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

from projects import ShortProject

WIDTH, HEIGHT = 1080, 1920
FPS = 30
VOICE = "en-US-ChristopherNeural"
ASSETS_DIR = Path(__file__).parent / "assets"

BG_TOP = (8, 12, 22)
CYAN = (0, 230, 255)
EMERALD = (40, 235, 145)
RED = (255, 65, 85)
AMBER = (255, 195, 45)
WHITE = (245, 248, 255)
MUTED = (175, 190, 215)


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


FONT_HEAD = _load_font(64)
FONT_SUB = _load_font(34)
FONT_CAP = _load_font(50)
FONT_MONO = _load_font(26, mono=True)
FONT_SMALL = _load_font(26)


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

    for beat in np.arange(0.3, duration - 1.0, 1.2):
        idx = int(beat * sr)
        length = min(int(0.18 * sr), n - idx)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / sr
        freq = 880.0 if mode == "radar" else (523.25 if mode == "waveform" else 1600.0)
        buf[idx : idx + length] += 0.14 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 18.0)

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


def _get_hardware_background(project: ShortProject) -> Optional[Image.Image]:
    """Load local asset from assets/<id>.png/.jpg or fetch photorealistic hardware image."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        local = ASSETS_DIR / f"{project.id}{ext}"
        if local.exists():
            return Image.open(local).convert("RGB")

    if not project.image_prompt:
        return None

    cached = ASSETS_DIR / f"{project.id}.png"
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(project.image_prompt)
        + "?width=1080&height=1920&nologo=true"
    )
    try:
        print(f"Fetching photorealistic hardware visual for {project.id}...")
        resp = requests.get(url, timeout=45)
        resp.raise_for_status()
        cached.write_bytes(resp.content)
        return Image.open(cached).convert("RGB")
    except Exception as exc:
        print(f"Image fetch failed ({exc}); using fallback grid background.")
        return None


def _ken_burns_bg(src: Optional[Image.Image], progress: float) -> Image.Image:
    if src is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
        draw = ImageDraw.Draw(img)
        for x in range(0, WIDTH, 90):
            draw.line([(x, 0), (x, HEIGHT)], fill=(18, 26, 44), width=1)
        for y in range(0, HEIGHT, 90):
            draw.line([(0, y), (WIDTH, y)], fill=(18, 26, 44), width=1)
        return img

    # Smooth 1.0x -> 1.12x zoom + slight vertical pan
    scale = 1.0 + 0.12 * progress
    sw, sh = src.size
    target_ratio = WIDTH / HEIGHT
    if sw / sh > target_ratio:
        crop_h = sh / scale
        crop_w = crop_h * target_ratio
    else:
        crop_w = sw / scale
        crop_h = crop_w / target_ratio

    cx = sw * (0.50 + 0.02 * math.sin(progress * math.pi))
    cy = sh * (0.48 + 0.04 * progress)
    left = max(0.0, min(sw - crop_w, cx - crop_w / 2))
    top = max(0.0, min(sh - crop_h, cy - crop_h / 2))
    cropped = src.crop((left, top, left + crop_w, top + crop_h))
    return cropped.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)


def _draw_radar_hud(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, y1 - 36
    radius = 155
    phase = (math.sin(t * 2.2 - math.pi / 2) + 1.0) / 2.0
    angle = 15 + phase * 150
    rad = math.radians(angle)

    target_cm = 12 if (dur * 0.35 <= t <= dur * 0.72) else 34
    alert = target_cm <= 25

    for r in (radius, radius * 2 // 3, radius // 3):
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=(35, 130, 115), width=2)
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=(45, 145, 125), width=2)

    sx = cx + int(math.cos(rad) * radius)
    sy = cy - int(math.sin(rad) * radius)
    draw.line([(cx, cy), (sx, sy)], fill=EMERALD, width=5)

    tr = int((target_cm / 40.0) * radius)
    trad = math.radians(78.0)
    tx = cx + int(math.cos(trad) * tr)
    ty = cy - int(math.sin(trad) * tr)
    draw.ellipse([tx - 10, ty - 10, tx + 10, ty + 10], fill=RED if alert else AMBER, outline=WHITE, width=2)
    draw.text((x0 + 24, y0 + 20), f"LIVE OLED: {target_cm} CM {'ALERT!' if alert else ''}", font=FONT_SMALL, fill=RED if alert else CYAN)


def _draw_waveform_hud(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    idx = int(t * 1.8) % len(notes)
    draw.text((x0 + 24, y0 + 20), f"LIVE NOTE: {notes[idx]} ({8 + idx * 4} CM)", font=FONT_SMALL, fill=CYAN)
    base_y = y1 - 28
    for i in range(8):
        bx = x0 + 28 + i * 48
        h = 130 if i == idx else int(35 + 18 * math.sin(t * 4 + i))
        draw.rounded_rectangle([bx, base_y - h, bx + 34, base_y], radius=8, fill=EMERALD if i == idx else (45, 75, 110))


def _draw_laser_hud(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], t: float, dur: float) -> None:
    x0, y0, x1, y1 = box
    tripped = dur * 0.38 <= t <= dur * 0.72
    cy = (y0 + y1) // 2 + 15
    draw.line([(x0 + 30, cy), ((x0 + x1) // 2 if tripped else x1 - 30, cy)], fill=RED, width=8)
    draw.text((x0 + 24, y0 + 20), "BEAM BROKEN!" if tripped else "LASER LOCKED", font=FONT_SMALL, fill=RED if tripped else EMERALD)


HUD_RENDERERS = {
    "radar": _draw_radar_hud,
    "waveform": _draw_waveform_hud,
    "laser": _draw_laser_hud,
}


def _render_frame(project: ShortProject, bg_src: Optional[Image.Image], frame_idx: int, total_frames: int) -> bytes:
    t = frame_idx / FPS
    dur = total_frames / FPS
    progress = frame_idx / max(total_frames - 1, 1)

    base = _ken_burns_bg(bg_src, progress).convert("RGBA")

    # Dark translucent top/bottom scrims so text & HUD pop over real hardware photos
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle([0, 0, WIDTH, 360], fill=(8, 12, 22, 185))
    odraw.rectangle([0, 1020, WIDTH, HEIGHT], fill=(8, 12, 22, 200))

    # Compact floating OLED HUD card in upper-right corner (keeps center hardware visible)
    hud_box = (590, 380, 1020, 645)
    odraw.rounded_rectangle(hud_box, radius=24, fill=(10, 16, 30, 215), outline=(0, 230, 255, 220), width=3)

    # Code card & caption bar
    code_box = (60, 1050, 1020, 1320)
    odraw.rounded_rectangle(code_box, radius=22, fill=(10, 15, 28, 225), outline=(55, 80, 120, 220), width=3)
    odraw.rounded_rectangle([60, 1365, 1020, 1495], radius=24, fill=(14, 22, 38, 235), outline=(0, 230, 255, 240), width=4)

    img = Image.alpha_composite(base, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top hook pills & headline
    draw.rounded_rectangle([60, 95, 410, 158], radius=22, fill=(18, 45, 70), outline=CYAN, width=3)
    draw.text((88, 108), project.hook_badge, font=FONT_SUB, fill=CYAN)

    draw.rounded_rectangle([760, 95, 1020, 158], radius=22, fill=(20, 65, 45), outline=EMERALD, width=3)
    draw.text((795, 108), project.cost_label, font=FONT_SUB, fill=EMERALD)

    draw.text((60, 192), project.hook_headline, font=FONT_HEAD, fill=WHITE)

    # Live OLED/Sensor HUD
    HUD_RENDERERS.get(project.sim_mode, _draw_radar_hud)(draw, hud_box, t, dur)

    # Code snippet
    draw.text((90, 1072), f"FILE: {project.code_filename}", font=FONT_SMALL, fill=AMBER)
    for i, line in enumerate(project.code_snippet.splitlines()[:4]):
        draw.text((90, 1122 + i * 44), line, font=FONT_MONO, fill=EMERALD)

    # Synced caption
    captions = project.captions or [project.hook_headline]
    cap_idx = min(int(progress * len(captions)), len(captions) - 1)
    draw.text((95, 1400), captions[cap_idx], font=FONT_CAP, fill=WHITE)

    # Channel CTA
    draw.text((60, 1545), "Zahid Bashir Young Innovator  |  Subscribe!", font=FONT_SUB, fill=MUTED)
    return img.tobytes()


def render_short_video(project: ShortProject, out_dir: Path) -> Path:
    """Generate voiceover, SFX, photorealistic hardware background & 1080x1920 MP4."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    bg_src = _get_hardware_background(project)
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
            proc.stdin.write(_render_frame(project, bg_src, i, total_frames))
        proc.stdin.close()
    finally:
        ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {ret}")

    return final_mp4
