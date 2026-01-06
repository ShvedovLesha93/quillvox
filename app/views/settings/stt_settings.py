from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
)

from app.views.ui_utils.title import Title

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsVM


class STTSettings(QWidget):
    def __init__(self, settings_vm: SettingsVM):
        super().__init__()
        self.vm = settings_vm

        self._setup_ui()
        self._bind_vm()

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)

        form_layout = QFormLayout()

        # Title
        title = Title(self)
        title.setTitle("Transcription")
        main_layout.addWidget(title)

        main_layout.addLayout(form_layout)

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def _bind_vm(self) -> None:
        pass
