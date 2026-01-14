from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.file_selector import FileSelectorVM
    from app.view_model.stt_vm import STTViewModel


class TranscriptControls(QWidget):
    def __init__(self, stt_vm: STTViewModel, file_selector_vm: FileSelectorVM) -> None:
        super().__init__()
        self.stt_vm = stt_vm
        self.file_selector_vm = file_selector_vm
        self._setup_ui()
        self._bind_vm()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.transcribe_btn = QPushButton()
        self.transcribe_btn.setEnabled(False)
        layout.addWidget(self.transcribe_btn)

    def _bind_vm(self) -> None:
        self.transcribe_btn.clicked.connect(self.stt_vm.run_stt)
        self.file_selector_vm.file_opened.connect(
            lambda: self.transcribe_btn.setEnabled(True)
        )

    def retranslate(self) -> None:
        self.transcribe_btn.setText(_("Transcribe"))
