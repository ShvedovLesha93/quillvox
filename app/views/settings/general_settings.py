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


class GeneralSettings(QWidget):
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
        title.setTitle("General")
        main_layout.addWidget(title)

        main_layout.addLayout(form_layout)

        # Language
        lang_label = QLabel("Language")

        self.lang_combo = QComboBox()
        form_layout.addRow(lang_label, self.lang_combo)

        # Theme
        theme_label = QLabel("Theme")
        theme_combo = QComboBox()

        form_layout.addRow(theme_label, theme_combo)

        main_layout.addStretch()

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def _bind_vm(self) -> None:
        # =========== UI → ViewModel ============
        self.lang_combo.currentIndexChanged.connect(
            lambda _: self.vm.set_language(self.lang_combo.currentData())
        )

        # =========== ViewModel → UI ===========
        self.add_languages(self.vm.languages())

    def add_languages(self, data: list[tuple[str, str]]) -> None:
        for code, label in data:
            self.lang_combo.addItem(label, userData=code)


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from app.view_model.settings_vm import SettingsVM

    app = QApplication([])
    app.setStyle("Fusion")

    settings_vm = SettingsVM()

    view = GeneralSettings(settings_vm=settings_vm)
    view.move(1020, 320)

    view.show()
    app.exec()
