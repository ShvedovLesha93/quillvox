from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFrame,
    QMessageBox,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
)

from app.constants import SettingsCategory, ThemeMode
from app.views.settings.general_settings_view import GeneralSettingsView
from app.views.settings.stt_settings_view import STTSettingsView
from app.translator import _, language_manager
from app.views.ui_utils.style_loader import StyleLoader

if TYPE_CHECKING:
    from app.view_model.settings_vm import SettingsViewModel
    from app.theme_manager import ThemeManager
    from app.views.main_window import MainWindow


class SettingsCategoryWidget(QPushButton):
    def __init__(
        self, parent: QWidget | None = None, theme_manager: ThemeManager | None = None
    ) -> None:
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setCheckable(True)
        self._connect_signals()

        if self.theme_manager:
            self.update_theme(self.theme_manager.applied_theme)

    def _connect_signals(self) -> None:
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_theme)

    def set_highlighted(self, highlighted: bool):
        self.setProperty("highlighted", highlighted)
        self.style().unpolish(self)
        self.style().polish(self)
        if highlighted:
            self.setToolTip(_("Settings was changed"))
        else:
            self.setToolTip("")

    def update_theme(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.dark_theme()
        else:
            self.light_theme()

    def dark_theme(self) -> None:
        self.setStyleSheet(StyleLoader.load(ThemeMode.DARK, style="setting_category"))

    def light_theme(self) -> None:
        self.setStyleSheet(StyleLoader.load(ThemeMode.LIGHT, style="setting_category"))


class Settings(QWidget):

    def __init__(
        self,
        settings_vm: SettingsViewModel,
        theme_manager: ThemeManager,
        main_window: MainWindow | None = None,
    ):
        super().__init__(main_window)

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        self.main_window = main_window
        self.theme_manager = theme_manager
        self.settings_vm = settings_vm
        self.general_settings = GeneralSettingsView(
            self.settings_vm.general_settings_vm
        )
        self.stt_settings = STTSettingsView(self.settings_vm.stt_settings_vm)

        self._setup_ui()
        self.retranslate()
        self._connect_signals()

        self.update_theme(self.theme_manager.applied_theme)

    def _connect_signals(self) -> None:
        language_manager.language_changed.connect(self.retranslate)
        self.theme_manager.theme_changed.connect(self.update_theme)
        self.settings_vm.settings_changed.connect(self._on_settings_changed)

        # Connect buttons
        self.general_btn.clicked.connect(lambda: self.switch_page(0))
        self.stt_btn.clicked.connect(lambda: self.switch_page(1))

        self.btn_reset.clicked.connect(self._on_reset_clicked)
        self.btn_apply.clicked.connect(self.settings_vm.save_requested.emit)
        self.btn_apply.clicked.connect(self._reset_ui)
        self.btn_ok.clicked.connect(self._on_ok_clicked)

    def _setup_ui(self):
        self.resize(500, 350)
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
        self.general_btn = SettingsCategoryWidget(
            self, theme_manager=self.theme_manager
        )
        self.stt_btn = SettingsCategoryWidget(self, theme_manager=self.theme_manager)

        self.categories_btn = (self.general_btn, self.stt_btn)

        for btn in self.categories_btn:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Right content area
        self.content_stack = QStackedWidget()

        # Add pages
        self.content_stack.addWidget(self.general_settings)
        self.content_stack.addWidget(self.stt_settings)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(5, 5, 5, 5)

        # Reset button
        self.btn_reset = QPushButton()
        self.btn_reset.setEnabled(False)
        self.btn_reset.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        btn_layout.addStretch()

        # Apply button
        self.btn_apply = QPushButton()
        self.btn_apply.setEnabled(False)
        self.btn_apply.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )

        # Ok button
        self.btn_ok = QPushButton()
        self.btn_ok.setEnabled(False)
        self.btn_ok.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        btn_layout.addWidget(self.btn_reset)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_ok)

        # Vertical separator
        self.v_separator = QFrame()
        self.v_separator.setFrameShape(QFrame.Shape.VLine)
        self.v_separator.setFixedWidth(2)

        # Gorizontal seaparator
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

    @Slot()
    def _reset_ui(self) -> None:
        self.stt_btn.set_highlighted(False)
        self.general_btn.set_highlighted(False)
        self.btn_apply.setEnabled(False)
        self.btn_reset.setEnabled(False)

    @Slot()
    def _on_settings_changed(self) -> None:

        has_changes = self.settings_vm.has_any_changes()
        self.btn_apply.setEnabled(has_changes)
        self.btn_reset.setEnabled(has_changes)
        self.btn_ok.setEnabled(has_changes)

        self.stt_btn.set_highlighted(
            self.settings_vm.has_category_changes(SettingsCategory.STT)
        )
        self.general_btn.set_highlighted(
            self.settings_vm.has_category_changes(SettingsCategory.GENERAL)
        )

    @Slot(object)
    def update_theme(self, theme: ThemeMode) -> None:
        if theme == ThemeMode.DARK:
            self.v_separator.setStyleSheet("background-color: #404040; border: none")
            self.h_separator.setStyleSheet("background-color: #404040; border: none")
        else:
            self.v_separator.setStyleSheet("background-color: #b7b6b6; border: none")
            self.h_separator.setStyleSheet("background-color: #b6b6b6; border: none")

    @Slot()
    def retranslate(self) -> None:
        self.general_btn.setText(_("General"))
        self.stt_btn.setText(_("Transcription"))
        self.btn_reset.setText(_("Reset"))
        self.btn_apply.setText(_("Apply"))
        self.btn_ok.setText(_("Ok"))

    def switch_page(self, index):
        # Uncheck all buttons
        for btn in self.categories_btn:
            btn.setChecked(False)

        # Check clicked button and switch page
        self.categories_btn[index].setChecked(True)
        self.content_stack.setCurrentIndex(index)

    @Slot()
    def _on_reset_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            _("Reset all settings"),
            _("Are you sure you want to reset the changed settings?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_vm.restore_requested.emit()
        else:
            return

    @Slot()
    def _on_ok_clicked(self) -> None:
        self.settings_vm.save_requested.emit()
        self._reset_ui
        self.close()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.main_window is not None:
            main_center = self.main_window.frameGeometry().center()
            geom = self.frameGeometry()
            geom.moveCenter(main_center)
            self.move(geom.topLeft())

    def closeEvent(self, event) -> None:
        if self.settings_vm.has_any_changes():
            reply = QMessageBox.question(
                self,
                _("Exit Confirmation"),
                _("Settings not saved. Save changes?"),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.settings_vm.save_requested.emit()
                event.accept()

            elif reply == QMessageBox.StandardButton.No:
                self.settings_vm.restore_requested.emit()
                event.accept()

            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()


# ============ TEST ============
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from app.theme_manager import ThemeManager
    from app.view_model.settings_vm import SettingsViewModel
    from app.utils.logging_config import configure_logging
    from app.config.stt_config import STTConfig
    from app.config.general_config import GeneralConfig

    app = QApplication([])
    app.setStyle("Fusion")

    configure_logging()

    theme_manager = ThemeManager(app, initial_theme=ThemeMode.LIGHT)

    stt_config = STTConfig()
    general_config = GeneralConfig()
    settings_vm = SettingsViewModel(
        general_config=general_config,
        stt_config=stt_config,
        theme_manager=theme_manager,
    )

    view = Settings(
        settings_vm=settings_vm,
        theme_manager=theme_manager,
    )

    view.resize(500, 400)
    view.move(1020, 320)

    view.show()
    app.exec()
