# app/presentation/views/search_view.py
from __future__ import annotations

import discord
from typing import Optional, TYPE_CHECKING

from app.services.music_service import SearchSession

if TYPE_CHECKING:
    from app.presentation.music_cog import MusicCog


def make_embed(title: str = "", description: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=description)


def render_search_embed(session: SearchSession) -> discord.Embed:
    items = session.get_page_items()
    if not session.results:
        return make_embed("검색 결과 없음", session.keyword)

    lines = [f"{i}. {t.title}" for i, t in enumerate(items, start=1)]
    desc = (
        f"키워드: {session.keyword}\n"
        f"페이지: {session.page + 1}/{session.page_count}\n\n"
        + "\n".join(lines)
        + "\n\n"
        + "선택: 아래 버튼(1~3)을 누르십시오."
    )
    return make_embed("유튜브 검색 결과(상위 3개)", desc)


class SearchView(discord.ui.View):
    def __init__(self, cog: "MusicCog", guild_id: int, user_id: int, timeout: float = 180.0) -> None:
        super().__init__(timeout=timeout)
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.message: Optional[discord.Message] = None  # Search 명령에서 저장합니다

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message("이 버튼은 검색한 사용자만 사용할 수 있습니다.", ephemeral=True)
        return False

    def _sync_button_state(self) -> None:
        session = self.cog.service.get_search(self.guild_id, self.user_id)
        if not session:
            for c in self.children:
                if isinstance(c, discord.ui.Button):
                    c.disabled = True
            return

        for c in self.children:
            if isinstance(c, discord.ui.Button):
                if c.custom_id == "prev":
                    c.disabled = not session.can_prev()
                if c.custom_id == "next":
                    c.disabled = not session.can_next()

    async def on_timeout(self) -> None:
        # 세션 만료 시 버튼 비활성 + 세션 삭제(원하시면 유지로 바꿀 수 있습니다)
        self.cog.service.clear_search(self.guild_id, self.user_id)
        for c in self.children:
            if isinstance(c, discord.ui.Button):
                c.disabled = True

        if self.message:
            try:
                await self.message.edit(embed=make_embed("세션 만료", "다시 -search 하십시오."), view=self)
            except Exception:
                pass

    @discord.ui.button(label="이전", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        session = self.cog.service.get_search(self.guild_id, self.user_id)
        if not session:
            await interaction.response.edit_message(embed=make_embed("세션 만료", "다시 -search 하십시오."), view=None)
            return

        session.prev()
        self._sync_button_state()
        await interaction.response.edit_message(embed=render_search_embed(session), view=self)

    @discord.ui.button(label="다음", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        session = self.cog.service.get_search(self.guild_id, self.user_id)
        if not session:
            await interaction.response.edit_message(embed=make_embed("세션 만료", "다시 -search 하십시오."), view=None)
            return

        session.next()
        self._sync_button_state()
        await interaction.response.edit_message(embed=render_search_embed(session), view=self)

    # ---- 1/2/3 선택 버튼 ----
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, custom_id="pick1")
    async def pick1_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_pick_interaction(interaction, 1)

    @discord.ui.button(label="2", style=discord.ButtonStyle.primary, custom_id="pick2")
    async def pick2_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_pick_interaction(interaction, 2)

    @discord.ui.button(label="3", style=discord.ButtonStyle.primary, custom_id="pick3")
    async def pick3_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_pick_interaction(interaction, 3)
