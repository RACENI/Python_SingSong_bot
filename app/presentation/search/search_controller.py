# app/presentation/search/search_controller.py
from __future__ import annotations

import discord
from discord.ext import commands

from app.presentation.views.search_view import SearchView, render_search_embed
from app.presentation.voice.voice_manager import VoiceManager
from app.presentation.messaging.sender import make_sender, make_embed
from app.presentation.messaging.interaction_reply import safe_reply
from app.services.music_service import MusicService


class SearchController:
    def __init__(self, service: MusicService, voice_manager: VoiceManager) -> None:
        self.service = service
        self.voice_manager = voice_manager

    async def start(self, ctx: commands.Context, keyword: str) -> None:
        self.voice_manager.ensure_guild_ctx(ctx)

        session = self.service.start_search(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            channel_id=ctx.channel.id,
            keyword=keyword,
        )

        view = SearchView(self, ctx.guild.id, ctx.author.id)
        view._sync_button_state()

        msg = await ctx.send(embed=render_search_embed(session), view=view)
        view.message = msg

    async def pick(self, interaction: discord.Interaction, n: int) -> None:
        if interaction.guild is None or interaction.user is None:
            return

        session = self.service.get_search(interaction.guild.id, interaction.user.id)
        if not session:
            await safe_reply(
                interaction,
                content="세션이 없습니다. 다시 -search 하십시오.",
                ephemeral=True,
            )
            return

        track = session.pick(n)
        voice = await self.voice_manager.ensure_connected_interaction(interaction)

        state = self.service.state(interaction.guild.id)
        await state.enqueue(track)

        await interaction.response.send_message(
            embed=make_embed("선택 재생(추가)", track.title),
            ephemeral=False,
        )

        send = make_sender(interaction.channel)
        await state.start(voice, send)
