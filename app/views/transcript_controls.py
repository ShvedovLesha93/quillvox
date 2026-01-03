from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class TranscriptControls(QWidget):
    def __init__(self, transcript_controls_vm=None) -> None:
        super().__init__()
        self.transcript_vm = transcript_controls_vm
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_transcript_btn = QPushButton("Start")
        layout.addWidget(self.start_transcript_btn)
