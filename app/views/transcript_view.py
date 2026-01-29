from PySide6.QtCore import Slot
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from app.view_model.transcript_vm import TranscriptViewModel


class TranscriptView(QWidget):
    def __init__(self, transcript_vm: TranscriptViewModel) -> None:
        super().__init__()
        self.vm = transcript_vm
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QPlainTextEdit()
        layout.addWidget(self.text_edit)

    def _connect_signals(self) -> None:
        self.vm.transcript_loaded.connect(self.text_edit.setPlainText)
        self.vm.segment_str.connect(self.text_edit.appendPlainText)
        self.vm.clear_requested.connect(self.text_edit.clear)

    # @Slot()
    # def _load_transcript(self) -> None:
    #     print(f"_load_transcript: self.vm.extract_text: {self.vm.extract_text()})")
    #     self.text_edit.setPlainText(self.vm.extract_text())
