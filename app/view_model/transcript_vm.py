from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from app.view_model.stt_runner_vm import STTRunnerViewModel


class TranscriptViewModel(QObject):
    segment_str = Signal(str)

    def __init__(self, stt_vm: STTRunnerViewModel):
        super().__init__()
        self.vm = stt_vm
        self.buf_text = []
        self.vm.segment_sent.connect(self.get_segment)

    def get_segment(self, segment: str) -> None:
        self.segment_str.emit(segment)
