from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
)

from app.constants import ThemeMode
from app.view_model import settings_vm
from app.views.settings.general_settings_view import GeneralSettings
from app.views.settings.stt_settings_view import STTSettings
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.stt_settings_vm import STTSettingsViewModel
    from app.theme_manager import ThemeManager
    from app.view_model.settings_vm import SettingsViewModel
    from app.views.main_window import MainWindow


class SettingsCategory(QPushButton):
    def __init__(
        self, parent: QWidget | None = None, theme_manager: ThemeManager | None = None
    ) -> None:
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setCheckable(True)

        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_theme)
            self.update_theme(self.theme_manager.applied_theme)

    def set_highlighted(self, highlighted: bool):
        self.setProperty("highlighted", highlighted)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_theme(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.dark_theme()
        else:
            self.light_theme()

    def dark_theme(self) -> None:
        self.setStyleSheet(
            """
            QPushButton {
                font: bold;
                text-align: left;
                padding: 10px 10px;
                border: 2px solid #272727;
                background-color: #272727;
                color: #ffffff;
                font-size: 14px;
                border-radius: 8px;
                margin: 2px 5px;
            }

            QPushButton:hover {
                background-color: #424242;
                border: 2px solid #424242;
            }

            QPushButton:pressed {
                background-color: #565656;
                border: 2px solid #565656;
            }

            QPushButton:checked {
                background-color: #424242;
                border: 2px solid #424242;
            }

            QPushButton[highlighted="true"] {
                border: 2px solid #ffa500;
            }
            """
        )

    def light_theme(self) -> None:
        self.setStyleSheet(
            """
            QPushButton {
                font: bold;
                text-align: left;
                padding: 10px 10px;
                border: 2px solid #e6e6e6;
                background-color: #f2f2f2;
                color: #1a1a1a;
                font-size: 14px;
                border-radius: 8px;
                margin: 2px 5px;
            }

            QPushButton:hover {
                background-color: #e5e5e5;
            }

            QPushButton:pressed {
                border: 2px solid #cecece;
                background-color: #cecece;
            }

            QPushButton:checked {
                border: 2px solid #dadada;
                background-color: #dadada;
                color: #000000;
            }

            QPushButton[highlighted="true"] {
                border: 2px solid #ffa500;
            }
            """
        )


class Settings(QWidget):
    restore_settings_request = Signal()
    save_settings_request = Signal()

    def __init__(
        self,
        settings_vm: SettingsViewModel,
        stt_settings_vm: STTSettingsViewModel,
        theme_manager: ThemeManager,
        main_window: MainWindow | None = None,
    ):
        super().__init__()
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.settings_vm = settings_vm
        self.stt_settings_vm = stt_settings_vm
        self.general_settings = GeneralSettings(self.settings_vm)
        self.stt_settings = STTSettings(self.stt_settings_vm)
        self._setup_ui()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

        self.theme_manager.theme_changed.connect(self.update_theme)

        self.update_theme(self.theme_manager.applied_theme)

    def _setup_ui(self):
        self.resize(500, 200)
        # Central widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main part
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left sidebar
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 0)
        sidebar_layout.setSpacing(0)

        # Category buttons
        self.general_btn = SettingsCategory(self, theme_manager=self.theme_manager)
        self.stt_btn = SettingsCategory(self, theme_manager=self.theme_manager)

        self.categories_btn = (self.general_btn, self.stt_btn)

        for btn in self.categories_btn:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Right content area
        self.content_stack = QStackedWidget()

        # Add pages
        self.content_stack.addWidget(self.general_settings)
        self.content_stack.addWidget(self.stt_settings)

        # Connect buttons
        self.general_btn.clicked.connect(lambda: self.switch_page(0))
        self.stt_btn.clicked.connect(lambda: self.switch_page(1))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(5, 5, 5, 5)

        self.btn_save = QPushButton()
        self.btn_save.setEnabled(False)
        self.btn_save.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self.btn_save.clicked.connect(self.save_settings_request.emit)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)

        # Vertical separator
        self.v_separator = QFrame()
        self.v_separator.setFrameShape(QFrame.Shape.VLine)
        self.v_separator.setFixedWidth(2)

        # Gorizontal separator
        self.h_separator = QFrame()
        self.h_separator.setFrameShape(QFrame.Shape.HLine)
        self.h_separator.setFixedHeight(2)

        # Add to main layout
        layout.addWidget(sidebar)
        layout.addWidget(self.v_separator)
        layout.addWidget(self.content_stack)

        main_layout.addLayout(layout)
        main_layout.addWidget(self.h_separator)
        main_layout.addLayout(btn_layout)

        # Set initial state
        self.general_btn.setChecked(True)
        self.content_stack.setCurrentIndex(0)

    def update_theme(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.v_separator.setStyleSheet("background-color: #404040; border: none")
            self.h_separator.setStyleSheet("background-color: #404040; border: none")
        else:
            self.v_separator.setStyleSheet("background-color: #b7b6b6; border: none")
            self.h_separator.setStyleSheet("background-color: #b6b6b6; border: none")

    def retranslate(self) -> None:
        self.general_btn.setText(_("General"))
        self.stt_btn.setText(_("Transcription"))
        self.btn_save.setText(_("Save"))

    def switch_page(self, index):
        # Uncheck all buttons
        for btn in self.categories_btn:
            btn.setChecked(False)

        # Check clicked button and switch page
        self.categories_btn[index].setChecked(True)
        self.content_stack.setCurrentIndex(index)

    def on_main_closing(self):
        """Called when main window is closing."""
        self.force_close = True
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        if self.main_window is not None:
            main_center = self.main_window.frameGeometry().center()
            geom = self.frameGeometry()
            geom.moveCenter(main_center)
            self.move(geom.topLeft())


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from app.view_model.settings_vm import SettingsViewModel
    from app.theme_manager import ThemeManager
    from app.view_model.stt_settings_vm import STTSettingsViewModel
    from app.utils.logging_config import configure_logging

    app = QApplication([])
    app.setStyle("Fusion")

    configure_logging()

    theme_manager = ThemeManager(app, initial_theme=ThemeMode.LIGHT)

    settings_vm = SettingsViewModel(theme_manager)
    from app.models.stt_config import STTConfig

    stt_config = STTConfig()
    stt_settings_vm = STTSettingsViewModel(stt_config)

    view = Settings(
        settings_vm=settings_vm,
        stt_settings_vm=stt_settings_vm,
        theme_manager=theme_manager,
    )

    view.resize(500, 200)
    view.move(1020, 320)

    view.show()
    app.exec()
