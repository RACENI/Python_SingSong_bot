# app/infra/ytdlp_stream.py
import asyncio
import yt_dlp

class YtdlpStreamExtractor:
    def __init__(self, ydl_opts: dict) -> None:
        self.ydl_opts = ydl_opts

    async def extract_stream_url(self, youtube_url: str) -> str:
        loop = asyncio.get_running_loop()

        def _blocking() -> str:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info["url"]

        return await loop.run_in_executor(None, _blocking)
