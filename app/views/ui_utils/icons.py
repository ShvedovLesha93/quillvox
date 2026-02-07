from typing import Literal
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QPushButton,
)

from app.constants import ThemeMode
import app.resources.resources_rc as _  # noqa: F401

Icon = Literal[
    "close",
    "format_align_justify",
    "format_text_overflow",
    "format_text_wrap",
    "pause",
    "play_arrow",
    "replay",
    "speed",
    "stop",
    "volume_off",
    "volume_up",
]


def get_icon(theme: ThemeMode, icon: str) -> QIcon:
    """Get icon from resources"""
    if theme == ThemeMode.DARK:
        return QIcon(f":/icons/icons/dark_theme/{icon}.svg")
    else:
        return QIcon(f":/icons/icons/light_theme/{icon}.svg")


class IconButton(QPushButton):
    BASE_ICON_SIZE = 28
    BASE_BUTTON_PADDING = 4

    _current_theme: ThemeMode

    def __init__(self, name: Icon, scale: float = 1.0, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("iconButton")
        self.name: Icon = name
        self.scale = scale

        self.setIcon(get_icon(self._current_theme, self.name))
        self.setFlat(True)

        # Setup opacity effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._update_opacity()

        self.set_scale(self.scale)

    @classmethod
    def set_theme(cls, theme: ThemeMode) -> None:
        """Class method to update theme for all IconButton instances.
        This should be called by ThemeManager when theme changes.
        """
        cls._current_theme = theme

    def update_icon_theme(self) -> None:
        """Update this button's icon to match current theme."""
        self.setIcon(get_icon(self._current_theme, self.name))

    def set_scale(self, scale: float) -> None:
        """Set the button scale factor."""
        self.scale = scale
        icon_size = int(self.BASE_ICON_SIZE * scale)
        button_size = icon_size + (self.BASE_BUTTON_PADDING * 2)

        self.setIconSize(QSize(icon_size, icon_size))
        self.setFixedSize(button_size, button_size)

    def set_icon(self, icon: Icon) -> None:
        self.name = icon
        self.setIcon(get_icon(self._current_theme, icon))

    def _update_opacity(self) -> None:
        """Update opacity based on enabled state."""
        self._opacity_effect.setOpacity(1.0 if self.isEnabled() else 0.3)

    def changeEvent(self, event: QEvent) -> None:
        """Automatically update opacity when enabled state changes."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self._update_opacity()


class IconLabel(QLabel):
    BASE_ICON_SIZE = 28
    BASE_PADDING = 4

    _current_theme: ThemeMode

    def __init__(
        self,
        name: Icon,
        scale: float = 1.0,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.name = name
        self.scale = scale

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.set_icon(name)
        self.set_scale(scale)

    @classmethod
    def set_theme(cls, theme: ThemeMode) -> None:
        """Class method to update theme for all IconLabel instances.

        This should be called by ThemeManager when theme changes.
        """
        cls._current_theme = theme

    def update_icon_theme(self) -> None:
        """Update this label's icon to match current theme."""
        self._update_pixmap()

    def set_scale(self, scale: float) -> None:
        """Set the label scale factor."""
        self.scale = scale

        icon = int(self.BASE_ICON_SIZE * scale)
        size = icon + self.BASE_PADDING * 2

        self.setFixedSize(size, size)
        self._update_pixmap(icon)

    def set_icon(self, name: Icon) -> None:
        """Change the icon to a different one."""
        self.name = name
        self._update_pixmap()

    def _update_pixmap(self, icon_size: int | None = None) -> None:
        """Update the pixmap with current theme and icon."""
        icon_size = icon_size or int(self.BASE_ICON_SIZE * self.scale)

        pixmap = get_icon(self._current_theme, self.name).pixmap(
            icon_size,
            icon_size,
        )
        self.setPixmap(pixmap)
