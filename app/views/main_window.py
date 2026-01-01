from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.views.audio_player import AudioPlayer
from app.views.menu_bar import MenuBar

if TYPE_CHECKING:
    from app.view_model.main_vm import MainViewModel


class MainWindow(QMainWindow):
    def __init__(self, main_vm: MainViewModel) -> None:
        super().__init__()
        self.main_vm = main_vm
        self.file_selector_vm = self.main_vm.file_selector_vm
        self.audio_player_vm = self.main_vm.audio_player_vm

        self.menu_bar = MenuBar(self)
        self.audio_player = AudioPlayer(self.audio_player_vm)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_status_bar(self):
        status_bar = self.statusBar()
        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message)

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        layout.addWidget(self.audio_player)

    def open_file(self):
        filter = self.file_selector_vm.filter
        last_filter = self.file_selector_vm.last_filter
        last_dir = self.file_selector_vm.last_dir

        file, last_filter = self._open_file_dialog(
            filter=filter, last_filter=last_filter, last_dir=str(last_dir)
        )
        if file and last_filter:
            self.file_selector_vm.on_file_selected(file)
            self.file_selector_vm.last_filter = last_filter

    def _open_file_dialog(
        self, filter: str, last_filter: str, last_dir: str
    ) -> tuple[Path, str]:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(
            self,
            caption="Open media file",
            filter=filter,
            selectedFilter=last_filter,
            dir=last_dir,
        )

        return Path(file), filter
