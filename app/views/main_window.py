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

from app.views.audio_player_view import AudioPlayer
from app.views.menu_bar import MenuBar
from app.views.settings.settings_view import Settings
from app.views.transcript_controls_view import TranscriptControls
from app.views.transcript_view import TranscriptView
from app.user_message import user_msg, MessageLevel
from app.views.notifications_view import NotificationsView
from app.views.ui_utils.icons import IconButton, IconName
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager
    from app.view_model.main_vm import MainViewModel
    from PySide6.QtWidgets import QApplication


import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        app: QApplication,
        theme_manager: ThemeManager,
        main_vm: MainViewModel,
    ) -> None:
        super().__init__()
        self.app = app
        self.theme_manager = theme_manager
        self.main_vm = main_vm
        self.file_selector_vm = self.main_vm.file_selector_vm
        self.audio_player_vm = self.main_vm.audio_player_vm

        self.menu_bar = MenuBar(self)
        self.transcript_view = TranscriptView(self.main_vm.transcript_vm)
        self.transcript_controls = TranscriptControls(
            stt_vm=self.main_vm.stt_worker_vm,
            file_selector_vm=self.main_vm.file_selector_vm,
        )
        self.audio_player = AudioPlayer(
            theme_manager=self.theme_manager,
            audio_player_vm=self.audio_player_vm,
            waveform_vm=self.main_vm.waveform_vm,
        )
        self.settings = Settings(
            settings_vm=self.main_vm.settings_vm,
            theme_manager=self.theme_manager,
            main_window=self,
        )

        self.notifications_view = NotificationsView(
            main_window=self, theme_manager=self.theme_manager
        )

        self._setup_ui()
        self._setup_status_bar()
        self._connect_signals()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _connect_signals(self) -> None:
        user_msg.message.connect(self.set_status_message)
        user_msg.message.connect(self.append_status_message)
        self.main_vm.stt_worker_vm.process_active.connect(self.on_transcription_started)
        self.main_vm.stt_worker_vm.finished.connect(self.on_transcription_finished)
        self.user_logger_btn.clicked.connect(self.open_status_messages)

        # Stop transcript
        self.transcript_controls.stop_transctipt_request.connect(
            self.main_vm.stop_transcript
        )

    def _setup_status_bar(self) -> None:
        status_bar = self.statusBar()
        self.status_message = QLabel()
        self.user_logger_btn = IconButton(IconName.FORMAT_ALIGN_JUSTIFY, scale=0.8)
        status_bar.addWidget(self.user_logger_btn)
        status_bar.addWidget(self.status_message)

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        layout.addWidget(self.transcript_controls)
        layout.addWidget(self.transcript_view)
        layout.addWidget(self.audio_player)

    def retranslate(self) -> None:
        self.user_logger_btn.setToolTip(_("See all notifications"))

    def set_status_message(self, level: MessageLevel, message: str, time: str) -> None:
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

    def append_status_message(
        self, level: MessageLevel, message: str, time: str
    ) -> None:
        palette = self.status_message.palette()

        if level == MessageLevel.ERROR:
            self.notifications_view.append_message(f"{time} | Error: {message}", "red")
        elif level == MessageLevel.WARNING:
            self.notifications_view.append_message(
                f"{time} | Warning: {message}", "orange"
            )
        else:  # INFO
            self.notifications_view.append_message(
                f"{time} | {message}", QPalette.ColorRole.WindowText
            )

        self.status_message.setPalette(palette)

    def on_transcription_started(self) -> None:
        self.transcript_controls.transcribe_btn.setEnabled(False)
        self.transcript_controls.transcribe_btn.start_spinner()
        self.transcript_controls.stop_transcript_btn.setEnabled(True)
        self.settings.stt_settings.set_enabled(False)
        self.menu_bar.open_media.setEnabled(False)

    def on_transcription_finished(self) -> None:
        self.transcript_controls.transcribe_btn.setEnabled(True)
        self.transcript_controls.transcribe_btn.stop_spinner()
        self.transcript_controls.stop_transcript_btn.setEnabled(False)
        self.settings.stt_settings.set_enabled(True)
        self.menu_bar.open_media.setEnabled(True)

    def open_file(self) -> None:
        filter = self.file_selector_vm.filter
        last_filter = self.file_selector_vm.last_filter
        last_dir = self.file_selector_vm.last_dir

        opened_file = self._open_file_dialog(
            filter=filter, last_filter=last_filter, last_dir=str(last_dir)
        )
        self.file_selector_vm.on_file_selected(opened_file)

    def open_settings(self) -> None:
        if not self.settings.isVisible():
            self.settings.show()
        else:
            self.settings.raise_()
            self.settings.activateWindow()

    def open_status_messages(self) -> None:
        if not self.notifications_view.isVisible():
            self.notifications_view.show()
        else:
            self.notifications_view.raise_()
            self.notifications_view.activateWindow()

    def _open_file_dialog(
        self, filter: str, last_filter: str, last_dir: str
    ) -> tuple[str, str] | None:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(
            self,
            caption=_("Open media file"),
            filter=filter,
            selectedFilter=last_filter,
            dir=last_dir,
        )
        if file:
            return file, filter
        else:
            return None
