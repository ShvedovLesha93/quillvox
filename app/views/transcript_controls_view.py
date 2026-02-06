from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QWidget,
)

from app.translator import _, language_manager
from app.views.ui_utils.icons import IconButton

if TYPE_CHECKING:
    from app.views.main_window import MainWindow
    from app.view_model.main_vm import MainViewModel
    from app.view_model.file_selector_vm import FileSelectorViewModel


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

    def __init__(
        self,
        main_vm: MainViewModel,
        file_selector_vm: FileSelectorViewModel,
        main_window: MainWindow,
    ) -> None:
        super().__init__()
        self.main_vm = main_vm
        self.main_window = main_window
        self.file_selector_vm = file_selector_vm
        self._is_process_alive = False
        self._setup_ui()
        self._connect_signals()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_transcript_btn = SpinnerButton()
        self.start_transcript_btn.setEnabled(False)
        layout.addWidget(self.start_transcript_btn)

        self.stop_transcript_btn = IconButton("close")
        self.stop_transcript_btn.setEnabled(False)
        layout.addWidget(self.stop_transcript_btn)

    def _connect_signals(self) -> None:
        self.start_transcript_btn.clicked.connect(self._on_start_transctipt_clicked)
        self.file_selector_vm.file_opened.connect(
            lambda: self.start_transcript_btn.setEnabled(True)
        )
        self.stop_transcript_btn.clicked.connect(self._on_stop_transcript_clicked)

    def retranslate(self) -> None:
        self.start_transcript_btn.setText(_("Transcribe"))

    def _on_start_transctipt_clicked(self) -> None:
        if self.main_vm.has_transcript():
            reply = QMessageBox.question(
                self,
                _("Transcript exists"),
                _("Transcription is already exist. Do you want to rewrite it?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.main_vm.stt_worker_vm.run_stt()
            else:
                return
        else:
            self.main_vm.stt_worker_vm.run_stt()

    @Slot()
    def _on_stop_transcript_clicked(self) -> None:
        if self.main_window.is_process_alive:
            reply = QMessageBox.question(
                self,
                _("Transcription in Progress"),
                _("Transcription is currently running. Do you want to stop it?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.main_vm.stop_transcript()
            else:
                return
