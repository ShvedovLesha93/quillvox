from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class TranscriptView(QWidget):
    def __init__(self, transcript_vm=None) -> None:
        super().__init__()
        self.transcript_vm = transcript_vm
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
