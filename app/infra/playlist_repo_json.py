# app/infra/playlist_repo_json.py
import json
from pathlib import Path
from app.domain.models import Track

class PlaylistRepoJson:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def save(self, name: str, tracks: list[Track]) -> Path:
        path = self.base_dir / f"{name}.json"
        data = [{"title": t.title, "url": t.url} for t in tracks]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load(self, name: str) -> list[Track]:
        path = self.base_dir / f"{name}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Track(title=item["title"], url=item["url"]) for item in data]
