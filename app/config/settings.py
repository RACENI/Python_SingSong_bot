# app/config/settings.py
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]  # app/config/settings.py -> 프로젝트 루트

@dataclass(frozen=True)
class Settings:
    token: str
    ffmpeg_exe: Path
    ydl_opts: dict
    ffmpeg_options: dict
    playlists_dir: Path

def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN이 설정되지 않았습니다.")

    ffmpeg_exe = BASE_DIR / "ffmpeg-4.4-full_build-shared" / "bin" / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        raise FileNotFoundError(f"ffmpeg.exe를 찾지 못했습니다: {ffmpeg_exe}")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
    }

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    playlists_dir = BASE_DIR / "playlists"
    playlists_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        token=token,
        ffmpeg_exe=ffmpeg_exe,
        ydl_opts=ydl_opts,
        ffmpeg_options=ffmpeg_options,
        playlists_dir=playlists_dir,
    )
