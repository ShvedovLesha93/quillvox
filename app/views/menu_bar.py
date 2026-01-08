from typing import TYPE_CHECKING
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.views.main_window import MainWindow


class MenuBar(QObject):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__()
        self.main_window = main_window
        self.menubar = main_window.menuBar()
        self.file_menu()
        self.settings_menu()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def file_menu(self) -> None:
        self.f_menu = self.menubar.addMenu("")

        # Open media
        self.open_media = QAction()
        self.f_menu.addAction(self.open_media)
        self.open_media.triggered.connect(self.main_window.open_file)

    def settings_menu(self) -> None:
        self.open_settings = QAction()
        self.menubar.addAction(self.open_settings)
        self.open_settings.triggered.connect(self.main_window.open_settings)

    def retranslate(self) -> None:
        self.f_menu.setTitle(_("File"))
        self.open_media.setText(_("Open Media"))
        self.open_settings.setText(_("Settings"))
