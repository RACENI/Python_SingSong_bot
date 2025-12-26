# app/domain/models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Track:
    title: str
    url: str  # https://www.youtube.com/watch?v=...
