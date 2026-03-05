from dataclasses import dataclass, field
from datetime import timedelta
from typing import List

from app.constants import SubtitleFormat


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

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        timestamp = timedelta(seconds=seconds)
        return str(timestamp)[:-3].replace(".", ",")

    @staticmethod
    def _format_vtt_timestamp(seconds: float) -> str:
        timestamp = timedelta(seconds=seconds)
        return str(timestamp)[:-3]

    def convert(self, format: SubtitleFormat) -> str:
        """Convert the transcript to the specified subtitle format.

        Args:
            format: The target subtitle format (SRT, VTT, or TXT).

        Returns:
            The transcript as a formatted string in the requested format.

        Raises:
            KeyError: If the format is not supported.
        """
        funcs = {
            SubtitleFormat.SRT: self._to_srt,
            SubtitleFormat.VTT: self._to_vtt,
            SubtitleFormat.TXT: self._to_txt,
        }

        return funcs[format]()

    def _to_srt(self) -> str:
        """Convert transcript to SRT string."""
        lines = []
        for i, segment in enumerate(self.segments, start=1):
            start = self._format_srt_timestamp(segment.start)
            end = self._format_srt_timestamp(segment.end)
            lines.extend([str(i), f"{start} --> {end}", segment.text.strip(), ""])
        return "\n".join(lines)

    def _to_vtt(self) -> str:
        """Convert transcript to VTT string."""
        lines = []
        for segment in self.segments:
            start = self._format_vtt_timestamp(segment.start)
            end = self._format_vtt_timestamp(segment.end)
            lines.extend([f"{start} --> {end}", segment.text.strip(), ""])
        return "\n".join(lines)

    def _to_txt(self) -> str:
        """Convert transcript to TXT string."""
        lines = []
        for segment in self.segments:
            lines.extend([segment.text.strip(), ""])
        return "\n".join(lines)
