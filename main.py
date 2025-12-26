# main.py
import asyncio
import discord
from discord.ext import commands

from app.config.settings import load_settings
from app.infra.youtube_search import YoutubeSearchClient
from app.infra.ytdlp_stream import YtdlpStreamExtractor
from app.infra.playlist_repo_json import PlaylistRepoJson
from app.services.music_service import MusicService
from app.presentation.music_cog import MusicCog

def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    return commands.Bot(command_prefix="-", intents=intents)

async def main() -> None:
    settings = load_settings()
    bot = create_bot()

    search_client = YoutubeSearchClient()
    extractor = YtdlpStreamExtractor(settings.ydl_opts)
    repo = PlaylistRepoJson(settings.playlists_dir)

    service = MusicService(
        search_client=search_client,
        extractor=extractor,
        repo=repo,
        ffmpeg_exe=str(settings.ffmpeg_exe),
        ffmpeg_options=settings.ffmpeg_options,
    )

    await bot.add_cog(MusicCog(bot, service))

    @bot.event
    async def on_ready() -> None:
        print("봇 시작 완료")

    await bot.start(settings.token)

if __name__ == "__main__":
    asyncio.run(main())
