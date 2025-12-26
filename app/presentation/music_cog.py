# app/presentation/music_cog.py
from __future__ import annotations

import discord
from discord.ext import commands

from app.presentation.views.search_view import SearchView, render_search_embed
from app.services.music_service import MusicService, SearchSession
from app.presentation.voice.voice_manager import VoiceManager
from app.presentation.messaging.sender import make_sender, make_embed
from app.presentation.search.search_controller import SearchController
from app.presentation.messaging.interaction_reply import safe_reply



class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: MusicService) -> None:
        self.bot = bot
        self.service = service
        self.voice_manager = VoiceManager()
        self.search_controller = SearchController(service, self.voice_manager)


    # -------------------------
    # Search + UI
    # -------------------------
    @commands.command(aliases=["search", "srch", "find"])
    async def Search(self, ctx: commands.Context, *, keyword: str) -> None:
        send = make_sender(ctx.channel)
        try:
            await self.search_controller.start(ctx, keyword)
        except Exception as e:
            await send("Search Error", str(e))

    # -------------------------
    # 기존 Play는 유지(원하시면 Search 기반으로 완전 통합도 가능합니다)
    # -------------------------
    @commands.command(aliases=["play", "p", "ㅔ"])
    async def Play(self, ctx: commands.Context, *, keyword: str) -> None:
        send = make_sender(ctx.channel)
        try:
            voice = await self.voice_manager.ensure_connected_ctx(ctx)

            track = self.service.search_one(keyword)
            if not track:
                await send("검색 결과 없음", keyword)
                return

            state = self.service.state(ctx.guild.id)
            await state.enqueue(track)
            await send("노래 추가", track.title)

            await state.start(voice, send)

        except Exception as e:
            await send("Play Error", str(e))

    @commands.command(aliases=["q", "ㅂ", "queue"])
    async def Que(self, ctx: commands.Context) -> None:
        """
        -q
        현재 큐 목록을 출력합니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            state = self.service.state(ctx.guild.id)
            items = await state.snapshot()

            if not items:
                await send("플레이리스트", "현재 큐가 비어 있습니다.")
                return

            lines = [f"{idx + 1}. {t.title}" for idx, t in enumerate(items)]
            await send("플레이리스트", "\n".join(lines))

        except Exception as e:
            await send("Que Error", str(e))

    @commands.command(aliases=["skip", "s"])
    async def Skip(self, ctx: commands.Context) -> None:
        """
        -skip
        현재 곡을 중지하고 다음 곡으로 넘어갑니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            voice = ctx.guild.voice_client
            state = self.service.state(ctx.guild.id)

            # Try to trigger skip via the state (stops voice and sets next event)
            skipped = await state.skip(voice)
            if skipped:
                await send("스킵", "다음 곡으로 넘어갑니다.")
                return

            # If nothing was playing but there are queued items, start playback
            items = await state.snapshot()
            if items:
                # Ensure we are connected to a voice channel
                if voice is None or not (voice.is_connected()):
                    try:
                        voice = await self.voice_manager.ensure_connected_ctx(ctx)
                    except Exception as e:
                        await send("스킵 실패", str(e))
                        return

                await state.start(voice, send)
                await send("스킵", "다음 곡을 재생합니다.")
                return

            await send("스킵", "재생 중인 곡이 없습니다.")

        except Exception as e:
            await send("Skip Error", str(e))

    @commands.command(aliases=["pause"])
    async def Pause(self, ctx: commands.Context) -> None:
        """
        -pause
        재생 중이면 일시정지합니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            voice = ctx.guild.voice_client
            if voice and voice.is_playing():
                voice.pause()
                await send("일시정지", "정지하였습니다.")
            else:
                await send("일시정지", "재생 중이 아닙니다.")

        except Exception as e:
            await send("Pause Error", str(e))

    @commands.command(aliases=["resume"])
    async def Resume(self, ctx: commands.Context) -> None:
        """
        -resume
        일시정지 상태면 재개합니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            voice = ctx.guild.voice_client
            if voice and voice.is_paused():
                voice.resume()
                await send("재개", "다시 재생합니다.")
            else:
                await send("재개", "일시정지 상태가 아닙니다.")

        except Exception as e:
            await send("Resume Error", str(e))

    @commands.command(aliases=["loop", "l", "ㅣ"])
    async def Loop(self, ctx: commands.Context) -> None:
        """
        -loop
        루프 토글입니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            state = self.service.state(ctx.guild.id)
            state.loop = not state.loop
            await send("루프 상태", f"현재 LOOP 상태: {state.loop}")

        except Exception as e:
            await send("Loop Error", str(e))

    @commands.command(aliases=["remove"])
    async def Remove(self, ctx: commands.Context, arg: str) -> None:
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)
            idx = int(arg)

            state = self.service.state(ctx.guild.id)
            removed, removed_is_current = await state.remove_at(idx)

            # ✅ 현재 재생곡을 삭제했다면 즉시 skip(=stop)해서 다음으로 진행
            if removed_is_current:
                voice = ctx.guild.voice_client
                await state.skip(voice)
            await send("노래 삭제", removed.title)

        except ValueError:
            await send("노래 제거중 오류", "번호는 정수로 입력하셔야 합니다.")
        except Exception as e:
            await send("노래 제거중 오류", str(e))

    @commands.command(aliases=["save"])
    async def Save(self, ctx: commands.Context, *, name: str) -> None:
        """
        -save <이름>
        현재 큐를 JSON으로 저장합니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            state = self.service.state(ctx.guild.id)
            items = await state.snapshot()
            self.service.save_queue(ctx.guild.id, name, items)

            await send("저장 완료", name)

        except Exception as e:
            await send("Save Error", str(e))

    @commands.command(aliases=["open"])
    async def Open(self, ctx: commands.Context, *, name: str) -> None:
        """
        -open <이름>
        JSON 플레이리스트를 불러와 큐에 추가하고, 재생 루프를 시작합니다.
        """
        send = make_sender(ctx.channel)
        try:
            voice = await self.voice_manager.ensure_connected_ctx(ctx)

            tracks = self.service.load_queue(name)
            if not tracks:
                await send("Open Error", "불러올 항목이 없습니다.")
                return

            state = self.service.state(ctx.guild.id)
            for t in tracks:
                await state.enqueue(t)

            await send("플레이리스트 추가 완료", name)

            await state.start(voice, send)

        except Exception as e:
            await send("Open Error", str(e))

    @commands.command(aliases=["leave"])
    async def Leave(self, ctx: commands.Context) -> None:
        """
        -leave
        음성 채널에서 나갑니다.
        """
        send = make_sender(ctx.channel)
        try:
            self.voice_manager.ensure_guild_ctx(ctx)

            voice = ctx.guild.voice_client
            if voice and voice.is_connected():
                await voice.disconnect()
                await send("퇴장", "음성 채널에서 나갔습니다.")
            else:
                await send("퇴장", "이미 연결되어 있지 않습니다.")

        except Exception as e:
            await send("Leave Error", str(e))