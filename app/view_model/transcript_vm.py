from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, Slot
import json
from app.user_message import user_msg
from app.models.transcript import STTSegment
from app.translator import _
from bisect import bisect_right

if TYPE_CHECKING:
    from app.view_model.main_vm import MainViewModel
    from app.config.stt_config import STTConfig
    from faster_whisper.transcribe import Segment, TranscriptionInfo
    from app.models.transcript import Transcript

import logging

logger = logging.getLogger(__name__)


class TranscriptViewModel(QObject):
    segment_str = Signal(str)
    clear_requested = Signal()
    transcript_loaded = Signal(str)
    block_index_changed = Signal(int)

    def __init__(
        self, main_vm: MainViewModel, transcript: Transcript, stt_config: STTConfig
    ) -> None:
        super().__init__()
        self.main_vm = main_vm
        self.transcript = transcript
        self.stt_config = stt_config

        self.json_path: Path

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.main_vm.file_selector_vm.file_opened.connect(self._on_file_opened)
        self.main_vm.audio_player_vm.position_changed.connect(self._on_position_changed)

    @Slot(int)
    def _on_position_changed(self, pos: int) -> None:
        pos_seconds = pos / 1000.0
        idx = self.find_block_at_position(pos_seconds)
        self.block_index_changed.emit(idx)

    @Slot()
    def _on_file_opened(self) -> None:
        self.create_json_path()

        if self.transcript.segments:
            self.clear_transcription()
            self.clear_requested.emit()

        if self._check_existing_json():
            if self.load_json():
                self.transcript_loaded.emit(self.extract_text())

    def on_start_transcription(self) -> None:
        audio = self.stt_config.audio
        if audio:
            self.create_json_path()
            self.clear_requested.emit()
            self.clear_transcription()
            self._clear_json()
        else:
            raise FileNotFoundError("Cannot find audio file")

    def find_block_at_position(self, position: float) -> int:
        """Find which block contains the given character position using binary search."""
        idx = bisect_right(
            self.transcript.segments, position, key=lambda seg: seg.start
        )

        if idx == 0:
            return -1  # Position is before the first segment

        # Check if position falls within the previous segment
        seg = self.transcript.segments[idx - 1]
        if seg.start <= position <= seg.end:
            return idx - 1

        return -1  # Position is in a gap between segments

    def _on_info(self, info: TranscriptionInfo) -> None:
        """Transcription information"""
        self.transcript.language = info.language

    def _on_segment(self, seg: Segment) -> None:
        segment = STTSegment(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            text=seg.text,
        )
        self.transcript.segments.append(segment)
        self.segment_str.emit(segment.text.strip())
        self._save_to_json()

    def clear_transcription(self) -> None:
        if self.transcript.segments:
            self.transcript.segments.clear()

            logger.info("cleared transcript from memory")

    def create_json_path(self) -> None:
        """To create a JSON file next to the transcribed audio file"""
        audio = self.stt_config.audio
        if audio:
            self.json_path = audio.with_suffix(".json")

    def _save_to_json(self) -> None:
        data_json = json.dumps(self.transcript.to_dict(), ensure_ascii=False, indent=2)
        if self.json_path:
            with open(self.json_path, "w", encoding="utf-8") as f:
                f.write(data_json)
        else:
            raise FileNotFoundError("Cannot find audio file")

    def load_json(self) -> bool:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                json_data = f.read()
                data = json.loads(json_data)

            state, msg = self.transcript.from_dict(data)
            if state:
                return True
            else:
                user_msg.error(_("The JSON file is corrupted: {e}").format(e=msg))
                return False

        except (json.JSONDecodeError, OSError) as e:
            user_msg.error(
                _("Failed to load JSON file: {file}").format(file=self.json_path)
            )
            logger.error("Failed to load json: %s", e)
            return False

    def extract_text(self) -> str:
        segments = [segment.text.strip() for segment in self.transcript.segments]
        return "\n".join(segments)

    def _clear_json(self) -> None:
        if self.json_path.exists():
            with open(self.json_path, "w", encoding="utf-8") as f:
                f.write("")

            logger.info("Cleared JSON transcipt file: %s", self.json_path.name)

        else:
            logger.warning("JSON file not exists: %s", self.json_path)

    def _check_existing_json(self) -> bool:
        if self.json_path.exists():  # pyright: ignore
            logger.info("JSON transcipt file found: %s", self.json_path)
            return True
        else:
            logger.info("JSON transcript file not found")
            return False
