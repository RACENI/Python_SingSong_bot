# app/services/music_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import discord

from app.domain.models import Track
from app.services.guild_state import GuildMusicState, SendFunc
from app.infra.youtube_search import YoutubeSearchClient
from app.infra.playlist_repo_json import PlaylistRepoJson
from app.infra.ytdlp_stream import YtdlpStreamExtractor


@dataclass
class SearchSession:
    keyword: str
    results: list[Track]
    page: int = 0
    page_size: int = 3
    channel_id: int = 0  # 번호 입력을 이 채널에서만 받기 위해 저장합니다

    @property
    def page_count(self) -> int:
        if not self.results:
            return 0
        return (len(self.results) + self.page_size - 1) // self.page_size

    def get_page_items(self) -> list[Track]:
        start = self.page * self.page_size
        end = start + self.page_size
        return self.results[start:end]

    def can_prev(self) -> bool:
        return self.page > 0

    def can_next(self) -> bool:
        return self.page + 1 < self.page_count

    def prev(self) -> None:
        if self.can_prev():
            self.page -= 1

    def next(self) -> None:
        if self.can_next():
            self.page += 1

    def pick(self, one_based_index_on_page: int) -> Track:
        if one_based_index_on_page < 1 or one_based_index_on_page > self.page_size:
            raise IndexError("선택 번호는 1~3 범위입니다.")
        items = self.get_page_items()
        idx = one_based_index_on_page - 1
        if idx >= len(items):
            raise IndexError("해당 번호의 항목이 없습니다.")
        return items[idx]


class MusicService:
    def __init__(
        self,
        search_client: YoutubeSearchClient,
        extractor: YtdlpStreamExtractor,
        repo: PlaylistRepoJson,
        ffmpeg_exe: str,
        ffmpeg_options: dict,
    ) -> None:
        self.search_client = search_client
        self.repo = repo
        self.states: Dict[int, GuildMusicState] = {}
        self.ffmpeg_exe = ffmpeg_exe
        self.ffmpeg_options = ffmpeg_options
        self.extractor = extractor

        # (guild_id, user_id) -> SearchSession
        self.search_sessions: Dict[Tuple[int, int], SearchSession] = {}

    def state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState(
                extractor=self.extractor,
                ffmpeg_exe=self.ffmpeg_exe,
                ffmpeg_options=self.ffmpeg_options,
            )
        return self.states[guild_id]

    # ---------- 검색 세션 ----------
    def start_search(self, guild_id: int, user_id: int, channel_id: int, keyword: str) -> SearchSession:
        results = self.search_client.search_many(keyword, max_results=30)
        session = SearchSession(keyword=keyword, results=results, page=0, page_size=3, channel_id=channel_id)
        self.search_sessions[(guild_id, user_id)] = session
        return session

    def get_search(self, guild_id: int, user_id: int) -> SearchSession | None:
        return self.search_sessions.get((guild_id, user_id))

    def clear_search(self, guild_id: int, user_id: int) -> None:
        self.search_sessions.pop((guild_id, user_id), None)

    # ---------- 기존 기능 ----------
    def search_one(self, keyword: str) -> Track | None:
        return self.search_client.search_one(keyword)

    def save_queue(self, guild_id: int, name: str, tracks: list[Track]) -> None:
        self.repo.save(name, tracks)

    def load_queue(self, name: str) -> list[Track]:
        return self.repo.load(name)
