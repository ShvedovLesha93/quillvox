from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QPalette
from app.constants import ThemeMode
from app.views.styles import theme_palettes

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

import logging

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    theme_changed = Signal(object)

    def __init__(self, app: QApplication, initial_theme: ThemeMode):
        super().__init__()
        self.app = app
        self._user_preference = initial_theme
        self._applied_theme: ThemeMode

        app.installEventFilter(self)

        self._initialize_theme(initial_theme)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.PaletteChange:
            self.on_system_theme_change()
        return False

    def _initialize_theme(self, theme) -> None:
        if theme == ThemeMode.SYSTEM:
            resolved = self.get_system_theme_mode()
            self._applied_theme = resolved
            self._apply_theme(resolved)
        else:
            self._applied_theme = theme
            self._apply_theme(theme)

    @property
    def current_theme(self) -> ThemeMode:
        """Returns the user's theme preference (may be SYSTEM)."""
        return self._user_preference

    @property
    def applied_theme(self) -> ThemeMode:
        """Returns the currently applied theme (DARK or LIGHT only)."""
        return self._applied_theme

    def on_system_theme_change(self) -> None:
        # Only respond if user has SYSTEM mode selected
        if self._user_preference != ThemeMode.SYSTEM:
            return

        new_theme = self.get_system_theme_mode()

        if new_theme != self._applied_theme:
            self._applied_theme = new_theme
            self._apply_theme(new_theme)

    def get_system_theme_mode(self) -> ThemeMode:
        style_hints = self.app.styleHints()
        color_scheme = style_hints.colorScheme()

        if color_scheme == Qt.ColorScheme.Unknown:
            palette = self.app.palette()
            window_color = palette.color(QPalette.ColorRole.Window)
            lightness = window_color.lightness()
            is_dark = lightness < 128

            if is_dark:
                return ThemeMode.DARK
            else:
                return ThemeMode.LIGHT
        else:
            if color_scheme == Qt.ColorScheme.Dark:
                return ThemeMode.DARK
            else:
                return ThemeMode.LIGHT

    def set_theme(self, theme: ThemeMode) -> None:
        if theme == self._user_preference:
            return

        self._user_preference = theme

        if theme == ThemeMode.SYSTEM:
            resolved = self.get_system_theme_mode()
        else:
            resolved = theme

        if resolved != self._applied_theme:
            self._applied_theme = resolved
            self._apply_theme(resolved)
            self.theme_changed.emit(resolved)

    def _apply_theme(self, theme: ThemeMode) -> None:
        match theme:
            case ThemeMode.DARK:
                theme_palettes.dark_palette(self.app)
            case ThemeMode.LIGHT:
                theme_palettes.light_palette(self.app)

        logger.info("Theme selected: %s", theme)
