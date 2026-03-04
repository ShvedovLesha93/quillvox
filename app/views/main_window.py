from __future__ import annotations
import os
import sys
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QToolButton,
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
from app.views.ui_utils.icons import IconButton
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager
    from app.view_model.main_vm import MainViewModel
    from PySide6.QtWidgets import QApplication


class TerminationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Transcription in Progress"))
        self.setModal(True)
        self.setMinimumWidth(300)

        # Prevent closing with X button
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        layout = QVBoxLayout()

        self.label = QLabel(_("Terminating transcription process..."))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(
        self,
        app: QApplication,
        theme_manager: ThemeManager,
        main_vm: MainViewModel,
        dev_restart: bool,
    ) -> None:
        super().__init__()
        self._is_dev_restarting = False
        self.app = app
        self.theme_manager = theme_manager
        self.main_vm = main_vm
        self.file_selector_vm = self.main_vm.file_selector_vm
        self.audio_player_vm = self.main_vm.audio_player_vm

        self.is_process_alive = False
        self._skip_exit_confirmation = False

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.menu_bar = MenuBar(self)
        self.transcript_view = TranscriptView(
            transcript_vm=self.main_vm.transcript_vm, theme_manager=self.theme_manager
        )
        self.transcript_controls = TranscriptControls(
            main_vm=self.main_vm,
            file_selector_vm=self.main_vm.file_selector_vm,
            main_window=self,
        )
        self.audio_player = AudioPlayer(
            theme_manager=self.theme_manager,
            audio_player_vm=self.audio_player_vm,
            waveform_vm=self.main_vm.waveform_vm,
        )
        self.settings = Settings(
            settings_vm=self.main_vm.settings_vm,
            main_window=self,
        )
        self.notifications_view = NotificationsView(
            main_window=self, theme_manager=self.theme_manager
        )

        self._setup_ui()
        self._set_no_focus_recursive(self)

        self._setup_status_bar()
        self._connect_signals()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

        if dev_restart:
            self.setup_shortcuts()

    def _connect_signals(self) -> None:
        user_msg.message.connect(self.set_status_message)
        user_msg.message.connect(self.append_status_message)
        self.main_vm.stt_worker_vm.started.connect(self.on_transcription_started)
        self.main_vm.stt_worker_vm.finished.connect(self.on_transcription_finished)
        self.main_vm.stt_worker_vm.progress_updated.connect(self.progress_bar.setValue)
        self.user_logger_btn.clicked.connect(self.open_status_messages)

    def _setup_status_bar(self) -> None:
        status_bar = self.statusBar()

        self.status_stack = QStackedWidget()

        self.status_message = QLabel()

        progress_container = QWidget()
        container_layout = QHBoxLayout(progress_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        container_layout.addWidget(
            self.progress_bar, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self.status_stack.addWidget(self.status_message)
        self.status_stack.addWidget(progress_container)

        self.user_logger_btn = IconButton("format_align_justify", scale=0.8)
        self.user_logger_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        status_bar.addWidget(self.user_logger_btn)
        status_bar.addWidget(self.status_stack, 1)

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        layout.addWidget(self.transcript_controls)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.splitter.addWidget(self.transcript_view)
        self.splitter.addWidget(self.audio_player)

        self.splitter.setSizes([400, 200])
        self.splitter.setChildrenCollapsible(False)

        layout.addWidget(self.splitter)

    def retranslate(self) -> None:
        self.user_logger_btn.setToolTip(_("See all notifications"))

    def set_status_message(self, level: MessageLevel, message: str, time: str) -> None:
        palette = self.status_message.palette()

        if level == MessageLevel.ERROR:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("red"))
            self.status_message.setText(message)
        elif level == MessageLevel.WARNING:
            palette.setColor(QPalette.ColorRole.WindowText, QColor("orange"))
            self.status_message.setText(message)
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
                # fmt: off
                f"{time} | {message}",
                "orange",
                # fmt: on
            )
        else:  # INFO
            self.notifications_view.append_message(
                f"{time} | {message}", QPalette.ColorRole.WindowText
            )

        self.status_message.setPalette(palette)

    def on_transcription_started(self) -> None:
        self.status_stack.setCurrentIndex(1)
        self.is_process_alive = True
        self.transcript_controls.start_transcript_btn.setEnabled(False)
        self.transcript_controls.start_transcript_btn.start_spinner()
        self.transcript_controls.stop_transcript_btn.setEnabled(True)
        self.transcript_view.text_edit.setReadOnly(True)
        self.settings.stt_settings.set_enabled(False)
        self.menu_bar.open_media.setEnabled(False)

    def on_transcription_finished(self) -> None:
        self.progress_bar.setValue(0)
        self.status_stack.setCurrentIndex(0)
        self.is_process_alive = False
        self.transcript_controls.start_transcript_btn.setEnabled(True)
        self.transcript_controls.start_transcript_btn.stop_spinner()
        self.transcript_controls.stop_transcript_btn.setEnabled(False)
        self.transcript_view.text_edit.setReadOnly(False)
        self.settings.stt_settings.set_enabled(True)
        self.menu_bar.open_media.setEnabled(True)

        if hasattr(self, "termination_dialog") and self.termination_dialog:
            self.termination_dialog.close()
            self._skip_exit_confirmation = True
            self.close()

    def open_file_dialog(self) -> None:
        file_dialog = QFileDialog()
        file, filter = file_dialog.getOpenFileName(
            self,
            caption=_("Open media file"),
            **self.file_selector_vm.get_open_file_kwargs(),
        )
        if file:
            self.file_selector_vm.open_selected_file(file, filter)

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

    def _set_no_focus_recursive(self, widget: QWidget) -> None:
        """Recursively set NoFocus on all buttons and sliders"""
        if isinstance(widget, (QPushButton, QSlider, QToolButton)):
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        for child in widget.findChildren(QWidget):
            self._set_no_focus_recursive(child)

    def closeEvent(self, event):
        if self._is_dev_restarting:
            event.accept()
            return

        # If transcription is running, prevent immediate close
        if self.is_process_alive:
            reply = QMessageBox.question(
                self,
                _("Transcription in Progress"),
                _(
                    "Transcription is currently running. Do you want to stop it and exit?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.termination_dialog = TerminationDialog(self)
                self.termination_dialog.show()
                self.main_vm.stop_transcript()
                event.ignore()  # Temporarily ignore until process actually stops
            else:
                event.ignore()

        else:
            if self._skip_exit_confirmation:
                event.accept()
                return

            # Normal close confirmation when no transcription is running
            reply = QMessageBox.question(
                self,
                _("Exit Confirmation"),
                _("Are you sure you want to exit?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

    def keyPressEvent(self, event) -> None:
        """Handle global keyboard shortcuts"""
        key = event.key()

        if key == Qt.Key.Key_Space:
            if self.audio_player_vm.is_file_loaded:
                self.audio_player_vm.toggle_play()
                event.accept()
                return
        elif key == Qt.Key.Key_Left:
            if self.audio_player_vm.is_file_loaded:
                self.audio_player_vm.rewind()
        elif key == Qt.Key.Key_Right:
            if self.audio_player_vm.is_file_loaded:
                self.audio_player_vm.forward()

        super().keyPressEvent(event)

    def setup_shortcuts(self) -> None:
        restart_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        restart_shortcut.activated.connect(self.run_dev_restart)

    def run_dev_restart(self) -> None:
        self._is_dev_restarting = True
        self.main_vm.restart_application()
