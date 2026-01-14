from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from app.view_model.stt_vm import STTViewModel


class TranscriptVM(QObject):
    segment_str = Signal(str)

    def __init__(self, stt_vm: STTViewModel):
        super().__init__()
        self.vm = stt_vm
        self.vm.segment_sent.connect(self.add_text)

    def add_text(self, segment: str):
        self.segment_str.emit(segment)
