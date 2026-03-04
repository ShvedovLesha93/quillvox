from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from app.constants import SubtitleFormat
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
        self.open_media.triggered.connect(self.main_window.open_file_dialog)

        self.f_menu.addSeparator()
        # Export actions
        # SRT
        self.export_srt = QAction()
        self.f_menu.addAction(self.export_srt)
        self.export_srt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.SRT)
        )

        # VTT
        self.export_vtt = QAction()
        self.f_menu.addAction(self.export_vtt)
        self.export_vtt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.VTT)
        )

        # TXT
        self.export_txt = QAction()
        self.f_menu.addAction(self.export_txt)
        self.export_txt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.TXT)
        )

    def settings_menu(self) -> None:
        self.open_settings = QAction()
        self.menubar.addAction(self.open_settings)
        self.open_settings.triggered.connect(self.main_window.open_settings)

    def retranslate(self) -> None:
        self.f_menu.setTitle(_("File"))
        self.open_media.setText(_("Open Media"))
        self.open_settings.setText(_("Settings"))
        self.export_srt.setText(_("Export to SRT"))
        self.export_vtt.setText(_("Export to VTT"))
        self.export_txt.setText(_("Export to TXT"))
