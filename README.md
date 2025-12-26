# 🎵 Python SingSong Bot

`discord.py` 기반 디스코드 음악 봇입니다.

- 접두사(prefix): `-`
- 유튜브 검색: `youtube-search`
- 스트림 추출: `yt-dlp`
- 재생: `FFmpegPCMAudio` (Windows용 `ffmpeg.exe` 포함)

---

## ✨ 주요 기능

- `-play <키워드>` : 검색 1개 결과를 즉시 큐에 추가하고 재생합니다.
- `-search <키워드>` : 검색 결과를 버튼 UI(이전/다음/1~3 선택)로 보여주고 선택 재생합니다.
- `-q` : 현재 큐(플레이리스트)를 출력합니다.
- `-skip` : 현재 곡을 스킵합니다.
- `-pause / -resume` : 일시정지 / 재개합니다.
- `-loop` : 전체 반복(loop) 토글입니다.
- `-remove <번호>` : 큐에서 항목을 삭제합니다.
- `-save <이름>` : 현재 큐를 JSON으로 저장합니다.
- `-open <이름>` : JSON 플레이리스트를 불러와 큐에 추가합니다.
- `-leave` : 음성 채널에서 나갑니다.

---

## ✅ 요구 사항

- Python 3.10+ 권장
- 디스코드 봇 토큰
- (Windows 기준) `ffmpeg.exe`  
  - 본 프로젝트는 `ffmpeg-4.4-full_build-shared/bin/ffmpeg.exe`를 기본 경로로 사용합니다.
- 디스코드 개발자 포털에서 “Message Content Intent”가 필요한 환경일 수 있습니다.
  - 코드에서 `intents.message_content = True`를 사용합니다.

---

## 📦 설치

의존성 설치:

```bash
pip install -r requirements.txt
```

---

## 🔐 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 토큰을 입력하십시오.

```text
DISCORD_TOKEN=여기에_봇_토큰
```

`.env.example` 파일을 참고하셔도 됩니다.

---

## ▶ 실행 방법

````bash
python main.py
````

---

## 📂 프로젝트 구조

```text
Python_SingSong_bot-main/
├─ main.py
├─ requirements.txt
├─ .env.example
├─ app/
│  ├─ config/
│  │  └─ settings.py              # 토큰/ffmpeg 경로/옵션/플레이리스트 폴더
│  ├─ domain/
│  │  └─ models.py                # Track 모델
│  ├─ infra/
│  │  ├─ youtube_search.py        # 유튜브 검색
│  │  ├─ ytdlp_stream.py          # yt-dlp로 스트림 URL 추출
│  │  └─ playlist_repo_json.py    # 플레이리스트 JSON 저장/로드
│  ├─ services/
│  │  ├─ music_service.py         # 길드별 상태/검색 세션 관리
│  │  └─ guild_state.py           # 재생 루프/큐/스킵/삭제/루프
│  └─ presentation/
│     ├─ music_cog.py             # 디스코드 명령어
│     ├─ voice/voice_manager.py   # 음성 채널 연결/이동
│     ├─ search/search_controller.py
│     ├─ views/search_view.py     # 검색 결과 버튼 UI(View)
│     └─ messaging/               # embed 전송/interaction reply 유틸
└─ ffmpeg-4.4-full_build-shared/
   └─ bin/ffmpeg.exe
```

---

## 💾 플레이리스트(JSON) 저장 위치

플레이리스트는 프로젝트 루트 기준 `playlists/` 폴더에 저장됩니다.

```text
playlists/
 ├─ mylist.json
 └─ party.json
```

---

## ⚠️ 보안 주의사항

- `.env` 파일(토큰 포함)은 절대 공개 저장소에 커밋하지 마십시오.
- 토큰이 유출되었다면 즉시 디스코드 개발자 포털에서 토큰을 재발급하십시오.

---

## 🧯 Troubleshooting

- `DISCORD_TOKEN이 설정되지 않았습니다.`  
  → `.env`에 `DISCORD_TOKEN=...`을 설정하십시오.

- `ffmpeg.exe를 찾지 못했습니다`  
  → `ffmpeg-4.4-full_build-shared/bin/ffmpeg.exe` 경로에 파일이 존재하는지 확인하십시오.  
  → Windows가 아니라면 `settings.py`에서 ffmpeg 경로를 시스템 ffmpeg로 변경하는 방식이 필요할 수 있습니다.

- 봇이 메시지를 읽지 못합니다  
  → 코드에서 `message_content` intent를 사용하므로, 디스코드 개발자 포털 설정이 필요할 수 있습니다.
