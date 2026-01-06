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

from app.views.settings.general_settings import GeneralSettings
from app.views.settings.stt_settings import STTSettings

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsVM
    from app.views.main_window import MainWindow


class SettingsCategory(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setCheckable(True)
        self.setStyleSheet(
            """
            QPushButton {
                font: bold;
                text-align: left;
                padding: 10px 10px;
                border: 2px solid transparent;
                background-color: #404040;
                color: #FFFFFF;
                font-size: 14px;
                border-radius: 8px;
                margin: 2px 5px;
            }

            QPushButton:hover {
                background-color: #5A5A5A;
            }

            QPushButton:pressed {
                background-color: #707070;
            }

            QPushButton:checked {
                background-color: #B4B4B4;
                color: #1A1A1A;
            }

            QPushButton:checked:hover {
                background-color: #C8C8C8;
            }

            QPushButton[highlighted="true"] {
                border: 2px solid #ffa500;
            }
            """
        )

    def set_highlighted(self, highlighted: bool):
        self.setProperty("highlighted", highlighted)
        self.style().unpolish(self)
        self.style().polish(self)


class Settings(QWidget):
    restore_settings_request = Signal()
    save_settings_request = Signal()

    def __init__(self, main_window: MainWindow, settings_vm: SettingsVM):
        super().__init__()
        self.main_window = main_window
        self.settings_vm = settings_vm
        self.general_settings = GeneralSettings(self.settings_vm)
        self.stt_settings = STTSettings(self.settings_vm)
        self._setup_ui()

    def _setup_ui(self):
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
        self.general_btn = SettingsCategory()
        self.general_btn.setText("General")
        self.stt_btn = SettingsCategory()
        self.stt_btn.setText("Transcription")

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

        self.btn_save = QPushButton("Save")
        self.btn_save.setEnabled(False)
        self.btn_save.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self.btn_save.clicked.connect(self.save_settings_request.emit)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)

        # Vertical separator
        v_separator = QFrame()
        v_separator.setFrameShape(QFrame.Shape.VLine)
        v_separator.setFixedWidth(2)
        v_separator.setStyleSheet("background-color: #404040; border: none")

        # Gorizontal separator
        h_separator = QFrame()
        h_separator.setFrameShape(QFrame.Shape.HLine)
        h_separator.setFixedHeight(2)
        h_separator.setStyleSheet("background-color: #404040; border: none")

        # Add to main layout
        layout.addWidget(sidebar)
        layout.addWidget(v_separator)
        layout.addWidget(self.content_stack)

        main_layout.addLayout(layout)
        main_layout.addWidget(h_separator)
        main_layout.addLayout(btn_layout)

        # Set initial state
        self.general_btn.setChecked(True)
        self.content_stack.setCurrentIndex(0)

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
