from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget
from app.translator import _, language_manager


class TranscriptControls(QWidget):
    def __init__(self, transcript_controls_vm=None) -> None:
        super().__init__()
        self.transcript_vm = transcript_controls_vm
        self._setup_ui()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.transcribe_btn = QPushButton()
        layout.addWidget(self.transcribe_btn)

    def retranslate(self) -> None:
        self.transcribe_btn.setText(_("Transcribe"))
