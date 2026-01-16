from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.file_selector import FileSelectorVM
    from app.view_model.stt_vm import STTViewModel


class SpinnerButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self._original_text = text
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._frame_index = 0

        self._anim = QPropertyAnimation(self, b"frameIndex", self)
        self._anim.setStartValue(0)
        self._anim.setEndValue(len(self._frames))
        self._anim.setDuration(1000)  # one full cycle
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)

    def getFrameIndex(self) -> int:
        return self._frame_index

    def setFrameIndex(self, value: int):
        self._frame_index = value % len(self._frames)
        self.setText(f"{self._frames[self._frame_index]} {self._original_text}")

    frameIndex = Property(int, getFrameIndex, setFrameIndex)

    def start_spinner(self):
        self._original_text = self.text()
        self.setEnabled(False)
        self._anim.start()

    def stop_spinner(self):
        self._anim.stop()
        self.setText(self._original_text)
        self.setEnabled(True)


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

        self.transcribe_btn = SpinnerButton()
        self.transcribe_btn.setEnabled(False)
        layout.addWidget(self.transcribe_btn)

    def _bind_vm(self) -> None:
        self.transcribe_btn.clicked.connect(self.stt_vm.run_stt)
        self.file_selector_vm.file_opened.connect(
            lambda: self.transcribe_btn.setEnabled(True)
        )

    def retranslate(self) -> None:
        self.transcribe_btn.setText(_("Transcribe"))
