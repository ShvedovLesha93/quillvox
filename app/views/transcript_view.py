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
        self.vm.segment_str.connect(self.text_edit.appendPlainText)
        self.vm.clear_requested.connect(self.text_edit.clear)
