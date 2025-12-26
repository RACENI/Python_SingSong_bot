# app/presentation/voice/voice_manager.py
from __future__ import annotations

import discord
from discord.ext import commands


class VoiceManager:
    """
    Discord 음성 채널 연결/이동 책임만 담당합니다.
    - ctx 기반(Command)
    - interaction 기반(UI 버튼/슬래시 등)
    """

    def ensure_guild_ctx(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            raise RuntimeError("DM에서는 사용할 수 없습니다. 서버에서 사용하십시오.")

    async def ensure_connected_ctx(self, ctx: commands.Context) -> discord.VoiceClient:
        self.ensure_guild_ctx(ctx)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise RuntimeError("음성 채널에 먼저 들어가셔야 합니다.")

        channel = ctx.author.voice.channel
        voice = ctx.guild.voice_client

        if voice is None:
            voice = await channel.connect()
        elif voice.channel != channel:
            await voice.move_to(channel)

        return voice

    async def ensure_connected_interaction(
        self,
        interaction: discord.Interaction,
    ) -> discord.VoiceClient:
        if interaction.guild is None:
            raise RuntimeError("서버에서만 사용할 수 있습니다.")
        if interaction.user is None or not isinstance(interaction.user, discord.Member):
            raise RuntimeError("사용자 정보를 확인할 수 없습니다.")
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise RuntimeError("음성 채널에 먼저 들어가셔야 합니다.")

        channel = interaction.user.voice.channel
        voice = interaction.guild.voice_client

        if voice is None:
            voice = await channel.connect()
        elif voice.channel != channel:
            await voice.move_to(channel)

        return voice
