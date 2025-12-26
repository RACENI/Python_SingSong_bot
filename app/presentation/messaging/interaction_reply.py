# app/presentation/messaging/interaction_reply.py
from __future__ import annotations

import discord


async def safe_reply(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
) -> None:
    """
    interaction 응답을 안전하게 보냅니다.
    - 이미 응답했으면 followup
    - 아직이면 response
    """
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
    except Exception:
        # 로그를 붙이고 싶으면 여기에 logger를 연결하십시오.
        pass
