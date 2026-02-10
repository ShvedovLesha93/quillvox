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

    def clear_all(self) -> None:
        self.language = None
        self.segments.clear()

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "segments": [seg.to_dict() for seg in self.segments],
        }

    def from_dict(self, data: dict) -> tuple[bool, str]:
        try:
            self.language = data["language"]
            self.segments = [STTSegment.from_dict(seg) for seg in data["segments"]]
            return True, ""
        except KeyError as e:
            return False, f"Missing key: {e}"
        except TypeError as e:
            return False, f"Type error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
