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

from app import theme_manager
from app.views.ui_utils.title import Title
from app.translator import _, language_manager

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsVM
    from app.view_model.settings_vm import Language, Theme


class GeneralSettings(QWidget):
    def __init__(self, settings_vm: SettingsVM):
        super().__init__()
        self.vm = settings_vm

        self._setup_ui()
        self._bind_vm()

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)

        form_layout = QFormLayout()

        # Title
        self.title = Title(self)
        main_layout.addWidget(self.title)

        main_layout.addLayout(form_layout)

        # Language
        self.lang_label = QLabel()

        self.lang_combo = QComboBox()
        form_layout.addRow(self.lang_label, self.lang_combo)

        # Theme
        self.theme_label = QLabel()
        self.theme_combo = QComboBox()

        form_layout.addRow(self.theme_label, self.theme_combo)

        main_layout.addStretch()

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)

        outer_layout.addWidget(scroll)

    def retranslate(self) -> None:
        self.title.setTitle(_("General"))
        self.lang_label.setText(_("Language"))
        self.theme_label.setText(_("Theme"))
        self.add_languages(self.vm.languages)
        self.add_themes(self.vm.themes)

    def _bind_vm(self) -> None:
        # =========== UI → ViewModel ============
        self.lang_combo.currentIndexChanged.connect(
            lambda _: self.vm.set_language(self.lang_combo.currentData())
        )
        self.theme_combo.currentIndexChanged.connect(
            lambda _: self.vm.set_theme(self.theme_combo.currentData())
        )

    def add_themes(self, data: list[Theme]) -> None:
        current_theme = self.vm.current_theme

        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()

        for theme in data:
            self.theme_combo.addItem(theme.translated, theme.data)

        self.set_current_item(self.theme_combo, current_theme)
        self.theme_combo.blockSignals(False)

    def add_languages(self, data: list[Language]) -> None:
        current_code = self.vm.current_language

        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()

        for lang in data:
            self.lang_combo.addItem(
                f"{lang.translated} ({lang.native})",
                userData=lang.code,
            )

        if current_code is not None:
            index = self.lang_combo.findData(current_code)
            if index != -1:
                self.lang_combo.setCurrentIndex(index)

        self.lang_combo.blockSignals(False)

    # TODO: Fix it. 2026-01-13 06:55
    def set_current_item(self, combo: QComboBox, data) -> None:
        index = combo.findData(data)
        if index != -1:
            combo.setCurrentIndex(index)


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from app.view_model.settings_vm import SettingsVM
    from app.theme_manager import ThemeManager
    from app.constants import ThemeMode

    app = QApplication([])
    app.setStyle("Fusion")

    theme_manager = ThemeManager(app, initial_theme=ThemeMode.SYSTEM)

    settings_vm = SettingsVM(theme_manager)
    settings_vm.language_changed.connect(language_manager.set_language)

    view = GeneralSettings(settings_vm=settings_vm)
    view.move(1020, 320)

    view.show()
    app.exec()
