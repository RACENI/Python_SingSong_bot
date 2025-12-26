# app/presentation/messaging/sender.py
from __future__ import annotations

import discord


def make_embed(title: str = "", description: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=description)


def make_sender(target: discord.abc.Messageable):
    """
    target: ctx.channel, interaction.channel 등 Messageable이면 무엇이든 가능
    반환: async (title, desc) -> None
    """
    async def send(title: str, desc: str = "") -> None:
        await target.send(embed=make_embed(title, desc))
    return send
