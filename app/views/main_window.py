from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.views.audio_player import AudioPlayer
from app.views.menu_bar import MenuBar
from app.views.transcript_controls import TranscriptControls
from app.views.transcript_view import TranscriptView
from app.user_message import user_msg, MessageLevel

if TYPE_CHECKING:
    from app.view_model.main_vm import MainViewModel


class MainWindow(QMainWindow):
    def __init__(self, main_vm: MainViewModel) -> None:
        super().__init__()
        self.main_vm = main_vm
        self.file_selector_vm = self.main_vm.file_selector_vm
        self.audio_player_vm = self.main_vm.audio_player_vm

        self.menu_bar = MenuBar(self)
        self.transcript_view = TranscriptView()
        self.transcript_controls = TranscriptControls()
        self.audio_player = AudioPlayer(self.audio_player_vm)
        # self.user_msg = user_msg

        self._setup_ui()
        self._setup_status_bar()
        self._connect_signals()

    def _connect_signals(self) -> None:
        user_msg.message.connect(self.set_status_message)

    def _setup_status_bar(self):
        status_bar = self.statusBar()
        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message)

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        layout.addWidget(self.transcript_controls)
        layout.addWidget(self.transcript_view)
        layout.addWidget(self.audio_player)

    def set_status_message(self, level: MessageLevel, message: str):
        palette = self.status_message.palette()

        if level == MessageLevel.ERROR:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("red"))
            self.status_message.setText(f"Error: {message}")
        elif level == MessageLevel.WARNING:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("orange"))
            self.status_message.setText(f"Warning: {message}")
        else:  # INFO
            palette.setColor(
                QPalette.ColorRole.WindowText,
                self.palette().color(QPalette.ColorRole.WindowText),
            )
            self.status_message.setText(message)

        self.status_message.setPalette(palette)

    def open_file(self):
        filter = self.file_selector_vm.filter
        last_filter = self.file_selector_vm.last_filter
        last_dir = self.file_selector_vm.last_dir

        opened_file = self._open_file_dialog(
            filter=filter, last_filter=last_filter, last_dir=str(last_dir)
        )
        self.file_selector_vm.on_file_selected(opened_file)

    def _open_file_dialog(
        self, filter: str, last_filter: str, last_dir: str
    ) -> tuple[str, str] | None:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(
            self,
            caption="Open media file",
            filter=filter,
            selectedFilter=last_filter,
            dir=last_dir,
        )
        if file:
            return file, filter
        else:
            return None
