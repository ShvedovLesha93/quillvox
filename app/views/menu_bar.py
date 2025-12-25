from typing import TYPE_CHECKING
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from app.views.main_window import MainWindow


class MenuBar(QObject):
    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window
        self.menubar = main_window.menuBar()
        self.file_menu()

    def file_menu(self):
        file_menu = self.menubar.addMenu("File")

        # Open media
        self.open_media = QAction("Open Media")
        file_menu.addAction(self.open_media)
        self.open_media.triggered.connect(self.main_window.open_file)
