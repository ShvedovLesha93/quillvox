from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, Slot
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
        self.help_menu()

        self.enable_export(False)

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
        self.export_actions: list[QAction] = []
        # SRT
        self.export_srt = QAction()
        self.f_menu.addAction(self.export_srt)
        self.export_srt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.SRT)
        )
        self.export_actions.append(self.export_srt)

        # VTT
        self.export_vtt = QAction()
        self.f_menu.addAction(self.export_vtt)
        self.export_vtt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.VTT)
        )
        self.export_actions.append(self.export_vtt)

        # TXT
        self.export_txt = QAction()
        self.f_menu.addAction(self.export_txt)
        self.export_txt.triggered.connect(
            lambda: self.main_window.main_vm.export_request.emit(SubtitleFormat.TXT)
        )
        self.export_actions.append(self.export_txt)

    def settings_menu(self) -> None:
        self.open_settings = QAction()
        self.menubar.addAction(self.open_settings)
        self.open_settings.triggered.connect(self.main_window.open_settings)

    def help_menu(self) -> None:
        self.h_menu = self.menubar.addMenu("")
        self.check_upd = QAction()
        self.h_menu.addAction(self.check_upd)
        self.check_upd.triggered.connect(
            self.main_window.main_vm.update_checker.check_for_updates
        )

    @Slot(bool)
    def enable_export(self, state: bool) -> None:
        for act in self.export_actions:
            act.setEnabled(state)

    def retranslate(self) -> None:
        self.f_menu.setTitle(_("File"))
        self.open_media.setText(_("Open Media"))
        self.open_settings.setText(_("Settings"))
        self.h_menu.setTitle(_("Help"))
        self.check_upd.setText(_("Check for update"))
        self.export_srt.setText(_("Export to SRT"))
        self.export_vtt.setText(_("Export to VTT"))
        self.export_txt.setText(_("Export to TXT"))
