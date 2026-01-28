from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
import json
from app.models.transcript import STTSegment

if TYPE_CHECKING:
    from faster_whisper.transcribe import Segment, TranscriptionInfo
    from app.models.transcript import Transcript

import logging

logger = logging.getLogger(__name__)


class TranscriptViewModel(QObject):
    segment_str = Signal(str)

    def __init__(self, transcript: Transcript):
        super().__init__()
        self.transcript = transcript
        self.buf_text = []

    def clear_transcription(self) -> None:
        self.transcript.segments.clear()
        logger.info("transcript.json cleared")
        with open("transcript.json", "w", encoding="utf-8") as f:
            f.write("")

    def continue_transcription(
        self,
    ) -> None:  # TODO: realize this feature. 2026-01-28 11:59
        pass

    def on_info(self, info: TranscriptionInfo) -> None:
        self.transcript.language = info.language

    def on_segment(self, seg: Segment) -> None:
        segment = STTSegment(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            text=seg.text,
        )
        self.transcript.segments.append(segment)
        self.segment_str.emit(segment.text.strip())
        self._save_to_json()

    def _save_to_json(self) -> None:
        data_json = json.dumps(self.transcript.to_dict(), ensure_ascii=False, indent=2)
        with open("transcript.json", "w", encoding="utf-8") as f:
            f.write(data_json)
