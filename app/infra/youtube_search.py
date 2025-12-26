# app/infra/youtube_search.py
from __future__ import annotations

from youtube_search import YoutubeSearch
from app.domain.models import Track

class YoutubeSearchClient:
    def search_many(self, keyword: str, max_results: int = 30) -> list[Track]:
        results = YoutubeSearch(keyword, max_results=max_results).to_dict()
        tracks: list[Track] = []
        for r in results:
            title = r.get("title")
            suffix = r.get("url_suffix")
            if not title or not suffix:
                continue
            url = f"https://www.youtube.com{suffix}"
            tracks.append(Track(title=title, url=url))
        return tracks

    def search_one(self, keyword: str) -> Track | None:
        items = self.search_many(keyword, max_results=1)
        return items[0] if items else None
