from typing import TYPE_CHECKING
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from app.views.main_window import MainWindow


class MenuBar(QObject):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__()
        self.main_window = main_window
        self.menubar = main_window.menuBar()
        self.file_menu()
        self.settings_menu()

    def file_menu(self) -> None:
        file_menu = self.menubar.addMenu("File")

        # Open media
        self.open_media = QAction("Open Media")
        file_menu.addAction(self.open_media)
        self.open_media.triggered.connect(self.main_window.open_file)

    def settings_menu(self) -> None:
        self.open_settings = QAction("Settings")
        self.menubar.addAction(self.open_settings)
        self.open_settings.triggered.connect(self.main_window.open_settings)
