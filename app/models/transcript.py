from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class STTSegment:
    id: int
    start: float
    end: float
    text: str
    words: list[dict] | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "words": self.words,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "STTSegment":
        return cls(
            id=data["id"],
            start=data["start"],
            end=data["end"],
            text=data["text"],
            words=data.get("words"),
        )


@dataclass
class Transcript:
    language: str | None = None
    segments: List[STTSegment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "segments": [seg.to_dict() for seg in self.segments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        return cls(
            language=data.get("language"),
            segments=[STTSegment.from_dict(seg) for seg in data.get("segments", [])],
        )
