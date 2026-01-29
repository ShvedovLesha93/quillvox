from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
import json
from app.models.transcript import STTSegment

if TYPE_CHECKING:
    from app.config.stt_config import STTConfig
    from faster_whisper.transcribe import Segment, TranscriptionInfo
    from app.models.transcript import Transcript

import logging

logger = logging.getLogger(__name__)


class TranscriptViewModel(QObject):
    segment_str = Signal(str)
    clear_requested = Signal()

    def __init__(self, transcript: Transcript, stt_config: STTConfig) -> None:
        super().__init__()
        self.transcript = transcript
        self.stt_config = stt_config

        self.json_path: Path

    def continue_transcription(
        self,
    ) -> None:  # TODO: realize this feature. 2026-01-28 11:59
        pass

    def on_start_transcription(self) -> None:
        audio = self.stt_config.audio
        if audio:
            self.generate_json_path(audio)
            self.clear_requested.emit()
            self.clear_transcription()
            self.clear_json()
        else:
            raise FileNotFoundError("Cannot find audio file")

    def generate_json_path(self, audio: Path) -> None:
        """To create a JSON file next to the transcribed audio file"""
        self.json_path = audio.with_suffix(".json")

    def on_info(self, info: TranscriptionInfo) -> None:
        """Transcription information"""
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
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write(data_json)

    def clear_transcription(self) -> None:
        if self.transcript.segments:
            self.transcript.segments.clear()

            logger.info("cleared transcript from memory")

    def clear_json(self) -> None:
        if self.json_path.exists():
            with open(self.json_path, "w", encoding="utf-8") as f:
                f.write("")

            logger.info("Cleared JSON transcipt file: %s", self.json_path.name)
