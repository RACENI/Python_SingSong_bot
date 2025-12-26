# app/services/guild_state.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, List

import discord

SendFunc = Callable[[str, str], Awaitable[None]]

@dataclass
class Track:
    title: str
    url: str

class GuildMusicState:
    def __init__(self, extractor, ffmpeg_exe: str, ffmpeg_options: dict) -> None:
        self.extractor = extractor
        self.ffmpeg_exe = ffmpeg_exe
        self.ffmpeg_options = ffmpeg_options

        # ✅ 인덱스 기반 재생
        self.playlist: List[Track] = []
        self.index: int = 0  # 다음에 재생할 위치
        self.current: Optional[Track] = None
        self.current_index: int = -1


        self.loop: bool = False  # True면 전체 반복(리스트 끝나면 처음으로)

        self._lock = asyncio.Lock()
        self._next_event = asyncio.Event()
        self._queue_event = asyncio.Event()

        self._task: Optional[asyncio.Task] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

        # 스킵/삭제로 현재 트랙을 “반복 재삽입” 같은 걸 할 필요는 없지만
        # stop 후 다음으로 넘어갈 때 중복 증가 방지용 플래그가 있으면 안전합니다.
        self._advance_once: bool = False  # 현재 트랙 종료 후 index를 한 번만 증가시키기 위한 안전장치

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self, voice: discord.VoiceClient, send: SendFunc) -> None:
        if self._main_loop is None:
            self._main_loop = asyncio.get_running_loop()

        # 죽은 task 정리
        if self._task is not None and self._task.done():
            self._task = None

        if self._task is not None:
            return

        self._task = asyncio.create_task(self._player_loop(voice, send))

    async def enqueue(self, track: Track) -> None:
        async with self._lock:
            self.playlist.append(track)
            self._queue_event.set()

    async def snapshot(self) -> List[Track]:
        async with self._lock:
            return list(self.playlist)

    async def get_position(self) -> tuple[int, int, Optional[Track]]:
        async with self._lock:
            return self.index, len(self.playlist), self.current

    async def remove_at(self, index_1based: int) -> tuple[Track, bool]:
        async with self._lock:
            i = index_1based - 1
            if i < 0 or i >= len(self.playlist):
                raise IndexError("범위를 벗어났습니다.")

            removed_is_current = (i == self.current_index)
            removed = self.playlist.pop(i)

            # ✅ index 보정 규칙
            # 삭제한 곡이 index보다 앞에 있으면 index를 당김
            if i < self.index:
                self.index -= 1

            # 삭제한 곡이 현재곡이면:
            if removed_is_current:
                # 👉 index는 그대로 둔다 (다음 곡이 자동으로 그 자리에 옴)
                self.current = None
                self.current_index = -1

            # 안전장치
            if self.index < 0:
                self.index = 0

            return removed, removed_is_current



    async def skip(self, voice: Optional[discord.VoiceClient]) -> bool:
        if voice is None or not voice.is_connected():
            return False
        if not (voice.is_playing() or voice.is_paused()):
            return False

        # ✅ 오직 "다음으로 넘어가라"는 신호만 설정
        async with self._lock:
            self.index += 1
            self._advance_once = True

        try:
            voice.stop()
        finally:
            # after가 안 와도 루프를 깨우는 용도
            self._next_event.set()

        return True


    async def _player_loop(self, voice: discord.VoiceClient, send: SendFunc) -> None:
        try:
            while True:
                # ✅ 재생할 트랙 선택(큐 pop 없음, index만 사용)
                async with self._lock:
                    total = len(self.playlist)
                    if total == 0 or self.index >= total:
                        self.current = None
                        self.current_index = -1
                        self._queue_event.clear()
                        need_wait = True
                    else:
                        self.current = self.playlist[self.index]
                        self.current_index = self.index
                        need_wait = False

                if need_wait:
                    await self._queue_event.wait()
                    continue

                if voice is None or not voice.is_connected():
                    break

                # 스트림 추출
                try:
                    stream_url = await self.extractor.extract_stream_url(self.current.url)
                except Exception as e:
                    await send("재생 오류", f"스트림 추출 실패: {self.current.title}\n{e}")
                    # 실패한 트랙은 다음으로 넘깁니다
                    async with self._lock:
                        self.index += 1
                    continue

                self._next_event.clear()

                def _after(_err: Optional[Exception]) -> None:
                    try:
                        if self._main_loop:
                            self._main_loop.call_soon_threadsafe(self._next_event.set)
                    except Exception:
                        pass

                try:
                    voice.play(
                        discord.FFmpegPCMAudio(stream_url, executable=self.ffmpeg_exe, **self.ffmpeg_options),
                        after=_after
                    )
                except Exception as e:
                    await send("FFmpeg 재생 오류", str(e))
                    async with self._lock:
                        self.index += 1
                    continue

                # ✅ after가 안 와도 굳지 않도록 폴백
                while True:
                    try:
                        await asyncio.wait_for(self._next_event.wait(), timeout=1.0)
                        break
                    except asyncio.TimeoutError:
                        if not (voice.is_playing() or voice.is_paused()):
                            break

                # ✅ 다음 인덱스로 이동(스킵 포함)
                async with self._lock:
                    total = len(self.playlist)
                    if total == 0:
                        self.current = None
                        self.index = 0
                        continue

                    # 정상 종료든 스킵이든 “다음”으로 이동합니다
                    if self._advance_once:
                        self._advance_once = False
                    else:
                        self.index += 1

                    if self.loop:
                        self.index %= total  # 전체 반복
                    else:
                        # loop가 아니면 끝까지 가면 대기 상태로 들어갑니다
                        if self.index > total:
                            self.index = total

        finally:
            self._task = None
